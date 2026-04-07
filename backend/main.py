"""FastAPI 后端入口"""

import asyncio
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.models.schemas import AnalysisStatus, ReplicationGuide, VideoUploadResponse
from backend.services.pipeline import run_analysis


# ── 内存状态存储（MVP 单用户）──────────────────────────────

class AnalysisStore:
    def __init__(self):
        self.videos: dict[str, dict] = {}  # video_id -> {path, filename, status, progress, message, guide}
        self._tasks: dict[str, asyncio.Task] = {}  # video_id -> background task

    def create(self, video_id: str, path: str, filename: str):
        self.videos[video_id] = {
            "path": path,
            "filename": filename,
            "status": "uploaded",
            "progress": 0.0,
            "message": "上传完成",
            "guide": None,
        }

    def get(self, video_id: str) -> Optional[dict]:
        return self.videos.get(video_id)

    def update(self, video_id: str, status: str, progress: float, message: str):
        if video_id in self.videos:
            self.videos[video_id]["status"] = status
            self.videos[video_id]["progress"] = progress
            self.videos[video_id]["message"] = message

    def set_guide(self, video_id: str, guide: ReplicationGuide):
        if video_id in self.videos:
            self.videos[video_id]["guide"] = guide
            self.videos[video_id]["status"] = "completed"
            self.videos[video_id]["progress"] = 1.0
            self.videos[video_id]["message"] = "分析完成"

    def set_error(self, video_id: str, error: str):
        if video_id in self.videos:
            self.videos[video_id]["status"] = "failed"
            self.videos[video_id]["message"] = error


store = AnalysisStore()


# ── 后台分析任务 ────────────────────────────────────────

async def background_analyze(video_id: str):
    """后台运行分析管线"""
    entry = store.get(video_id)
    if not entry:
        return

    video_path = entry["path"]
    work_dir = os.path.dirname(video_path)

    def status_cb(vid, status, progress, message):
        store.update(vid, status, progress, message)

    try:
        guide = await run_analysis(video_path, video_id, work_dir, status_callback=status_cb)
        store.set_guide(video_id, guide)
    except Exception as e:
        store.set_error(video_id, str(e))
    finally:
        store._tasks.pop(video_id, None)


# ── FastAPI App ─────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时校验 API keys
    try:
        settings.validate_api_keys()
    except ValueError as e:
        print(f"WARNING: {e}")
        print("Server will start but analysis will fail without valid API keys.")

    # 确保上传目录存在
    settings.upload_dir.mkdir(parents=True, exist_ok=True)

    yield


app = FastAPI(
    title="TikTok 视频拆解 — 爆款复刻指南生成器",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── API 路由 ────────────────────────────────────────────

MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # 500MB

@app.post("/api/upload", response_model=VideoUploadResponse)
async def upload_video(file: UploadFile = File(...)):
    """上传视频文件 — 流式写入磁盘，避免内存溢出"""
    # 校验文件类型
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in (".mp4", ".mov", ".avi", ".mkv", ".webm"):
        raise HTTPException(status_code=400, detail=f"Unsupported format: {ext}. Supported: mp4, mov, avi, mkv, webm")

    # 生成 video_id 和保存路径
    video_id = str(uuid.uuid4())[:8]
    save_dir = settings.upload_dir / video_id
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / f"original{ext}"

    # 流式写入文件，同时检查大小
    total_size = 0
    try:
        with open(save_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                total_size += len(chunk)
                if total_size > MAX_UPLOAD_SIZE:
                    # 清理已写入的文件
                    f.close()
                    save_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=400,
                        detail=f"File too large. Max: {settings.max_video_size_mb}MB",
                    )
                f.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        save_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    if total_size < 1024:  # < 1KB
        save_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="File appears empty")

    store.create(video_id, str(save_path), file.filename)

    return VideoUploadResponse(
        video_id=video_id,
        filename=file.filename,
        status="uploaded",
    )


@app.post("/api/analyze/{video_id}")
async def start_analysis(video_id: str):
    """触发视频分析"""
    entry = store.get(video_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Video not found: {video_id}")

    if entry["status"] in ("processing", "analyzing"):
        raise HTTPException(status_code=409, detail="Analysis already in progress")

    if entry["status"] == "completed":
        raise HTTPException(status_code=409, detail="Analysis already completed. GET /api/result/{video_id}")

    store.update(video_id, "processing", 0.01, "开始分析...")

    # 启动后台任务并保存引用
    task = asyncio.create_task(background_analyze(video_id))
    store._tasks[video_id] = task

    return {"video_id": video_id, "status": "processing", "message": "分析已启动"}


@app.get("/api/status/{video_id}", response_model=AnalysisStatus)
async def get_status(video_id: str):
    """查询分析进度"""
    entry = store.get(video_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Video not found: {video_id}")

    return AnalysisStatus(
        video_id=video_id,
        status=entry["status"],
        progress=entry["progress"],
        message=entry["message"],
    )


@app.get("/api/result/{video_id}")
async def get_result(video_id: str):
    """获取分析结果"""
    entry = store.get(video_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Video not found: {video_id}")

    if entry["status"] != "completed":
        raise HTTPException(
            status_code=404,
            detail=f"Analysis not ready. Current status: {entry['status']}",
        )

    return entry["guide"].model_dump()


@app.get("/api/result/{video_id}/export")
async def export_markdown(video_id: str):
    """导出 Markdown 格式复刻指南"""
    entry = store.get(video_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Video not found: {video_id}")

    if entry["status"] != "completed" or not entry["guide"]:
        raise HTTPException(status_code=404, detail="Analysis not ready")

    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content=entry["guide"].export_markdown,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=replication-guide-{video_id}.md"},
    )


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
