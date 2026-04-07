# TikTok 视频拆解网站 — 开发计划

> Sprint: sprint-2026-04-06-01
> 类型: Full Sprint
> 状态: PLANNING

---

## 1. 系统架构

```
┌──────────────────────────────────────────────────────────────────┐
│                        用户浏览器                                 │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────┐ │
│  │ 上传页面 │  │ 分析 Dashboard│  │ 结果详情页   │  │ 导出页  │ │
│  └─────┬────┘  └──────┬───────┘  └──────┬───────┘  └────┬────┘ │
└────────┼──────────────┼─────────────────┼───────────────┼───────┘
         │              │                 │               │
┌────────┴──────────────┴─────────────────┴───────────────┴───────┐
│                     Next.js API Routes                          │
│                    (BFF / 反向代理)                              │
└────────┬──────────────┬─────────────────┬───────────────┬───────┘
         │              │                 │               │
┌────────┴──────────────┴─────────────────┴───────────────┴───────┐
│                     Python FastAPI 后端                          │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────────┐ │
│  │ Upload      │  │ Video       │  │ Analysis Engine          │ │
│  │ Handler     │  │ Processor   │  │                          │ │
│  │             │  │             │  │ ┌──────────────────────┐ │ │
│  │ - 接收文件  │  │ - 分段切割  │  │ │ Segment Analyzer     │ │ │
│  │ - 存储本地  │  │ - 抽帧     │  │ │ (多模态LLM 分析片段) │ │ │
│  │ - 元数据    │  │ - 提取音频  │  │ ├──────────────────────┤ │ │
│  │             │  │             │  │ │ Prompt Reverser      │ │ │
│  └─────────────┘  └─────────────┘  │ │ (逆向提示词)         │ │ │
│                                     │ ├──────────────────────┤ │ │
│  ┌─────────────┐                    │ │ Pattern Extractor    │ │ │
│  │ Task Queue  │                    │ │ (爆款模式提炼)       │ │ │
│  │ (异步处理)  │                    │ └──────────────────────┘ │ │
│  └─────────────┘                    └──────────────────────────┘ │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Storage Layer                                               │ │
│  │ - 本地文件系统 (视频/帧/音频)                               │ │
│  │ - SQLite / PostgreSQL (分析结果)                            │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                      外部 AI 服务                                │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │ Gemini 2.5   │  │ gpt-4o-mini-     │  │ PySceneDetect    │   │
│  │ Flash (视频) │  │ transcribe (字幕)│  │ (场景检测/本地)   │   │
│  ├──────────────┤  └──────────────────┘  └──────────────────┘   │
│  │ Claude/GPT   │  ┌──────────────────┐                        │
│  │ (文本推理)   │  │ ffmpeg           │                        │
│  └──────────────┘  │ (分段/音频提取)  │                        │
│                    └──────────────────┘                        │
└──────────────────────────────────────────────────────────────────┘
```

## 2. 核心数据流

```
用户上传视频
     │
     ▼
[1] 视频接收 & 存储
     │ video_id, file_path
     ▼
[2] 视频预处理（异步）
     ├── 2a. ffmpeg → 提取元数据（时长/分辨率）
     ├── 2b. PySceneDetect → 场景切割点
     ├── 2c. ffmpeg → 按场景切割片段
     └── 2d. ffmpeg → 提取音频
              │
              ▼
[3] 双轨分析（并行）
     ├── 3a. Gemini 2.5 Flash ← 视频文件（原生视频输入）
     │        → 画面理解 + 画面描述 + 视觉风格分析
     └── 3b. gpt-4o-mini-transcribe ← 音频
              → 字幕/台词文本
              │
              ▼
[4] 片段级分析（Gemini 按片段分别上传）
     ├── 4a. 每个片段 → Gemini → 画面+内容综合描述
     └── 4b. 合并画面+字幕 → Claude/GPT → 片段综合分析
              │
              ▼
[5] 提示词逆向（Claude/GPT 文本推理）
     └── 将综合分析 → LLM → 反推可能的提示词/创作指令
              │
              ▼
[6] 爆款模式提炼（Claude/GPT 文本推理）
     ├── 6a. 分析视频结构（开头/Hook/高潮/结尾）
     ├── 6b. 提取节奏模式（时长/转场/配乐）
     └── 6c. 生成可复用模板
              │
              ▼
[7] 结果汇总 & 展示
     └── 前端 Dashboard 展示所有分析结果
```

## 3. 技术选型

| 层级 | 技术 | 理由 |
|------|------|------|
| 前端框架 | Next.js 14+ (App Router) | SSR + API Routes，生态成熟 |
| UI 组件 | Tailwind CSS + shadcn/ui | 快速开发，美观 |
| 视频播放 | video.js / plyr | 支持分段标记 |
| 后端框架 | FastAPI (Python) | 异步支持好，ML 生态友好 |
| 视频处理 | ffmpeg + PySceneDetect | 场景检测标准方案 |
| 音频转写 | gpt-4o-mini-transcribe | $0.003/分钟，成本极低 |
| 视频理解 | Gemini 2.5 Flash | 原生视频输入，$0.01-0.05/视频，免费层可用 |
| 文本推理 | Claude Sonnet 4 / GPT-4o | 提示词逆向 + 模式提炼（文本任务更强） |
| 数据库 | SQLite (MVP) → PostgreSQL | MVP 用 SQLite 简化部署 |
| 任务队列 | Celery + Redis / arq | 异步处理耗时分析任务 |
| 文件存储 | 本地文件系统 (MVP) | 后续可切换 S3 |

### AI 服务成本估算（每个 60s 视频）

| 服务 | 调用 | 成本 |
|------|------|------|
| Gemini 2.5 Flash（视频理解） | 1 次全片 + N 次分段 | ~$0.01-0.05 |
| gpt-4o-mini-transcribe（字幕） | 1 次 | ~$0.003 |
| Claude Sonnet 4（文本推理） | 2-3 次（提示词+模式） | ~$0.05-0.10 |
| **合计** | | **~$0.06-0.15 / 视频** |

## 4. 目录结构

```
tiktok-video-analyzer/
├── frontend/                    # Next.js 前端
│   ├── app/
│   │   ├── page.tsx            # 首页（上传入口）
│   │   ├── analyze/
│   │   │   └── [id]/page.tsx   # 分析结果页
│   │   └── api/                # API Routes (BFF)
│   │       ├── upload/route.ts
│   │       ├── analyze/[id]/route.ts
│   │       └── status/[id]/route.ts
│   ├── components/
│   │   ├── VideoUploader.tsx
│   │   ├── AnalysisDashboard.tsx
│   │   ├── SegmentPlayer.tsx
│   │   ├── PromptCard.tsx
│   │   ├── PatternCard.tsx
│   │   └── ExportPanel.tsx
│   └── lib/
│       └── api.ts              # 后端 API 客户端
│
├── backend/                     # FastAPI 后端
│   ├── main.py                 # FastAPI 入口
│   ├── api/
│   │   ├── upload.py           # 上传接口
│   │   ├── analysis.py         # 分析接口
│   │   └── status.py           # 状态查询接口
│   ├── services/
│   │   ├── video_processor.py  # 视频预处理（分段、音频提取）
│   │   ├── transcription.py    # gpt-4o-mini-transcribe 转写
│   │   ├── gemini_analyzer.py  # Gemini 视频理解（原生视频输入）
│   │   ├── prompt_reverser.py  # 提示词逆向（Claude/GPT 文本推理）
│   │   └── pattern_extractor.py # 爆款模式提取（Claude/GPT 文本推理）
│   ├── models/
│   │   └── schemas.py          # Pydantic 数据模型
│   └── config.py               # 配置管理
│
├── docker-compose.yml           # 本地开发环境
├── .env.example                 # 环境变量模板
└── README.md
```

## 5. 数据模型

### Video (视频)

```python
{
    "id": "uuid",
    "filename": "original.mp4",
    "file_path": "/data/videos/uuid/original.mp4",
    "duration": 60.5,           # 秒
    "resolution": "1080x1920",
    "status": "uploaded | processing | analyzing | completed | failed",
    "created_at": "2026-04-06T10:00:00Z"
}
```

### Segment (视频片段)

```python
{
    "id": "uuid",
    "video_id": "uuid",
    "index": 0,                  # 片段序号
    "start_time": 0.0,
    "end_time": 5.2,
    "duration": 5.2,
    "file_path": "/data/videos/uuid/segments/seg_0.mp4",
    "frames": [                  # 关键帧
        {"time": 0.0, "path": "/data/videos/uuid/frames/seg_0_f0.jpg"},
        {"time": 1.0, "path": "/data/videos/uuid/frames/seg_0_f1.jpg"}
    ],
    "transcription": "字幕文本...",
    "visual_description": "画面描述...",
    "combined_analysis": "综合分析..."
}
```

### AnalysisResult (分析结果)

```python
{
    "id": "uuid",
    "video_id": "uuid",
    "reversed_prompts": [        # 逆向提示词
        {
            "type": "visual" | "narrative" | "style",
            "prompt": "一段高质量的...",
            "confidence": 0.85
        }
    ],
    "viral_patterns": {          # 爆款模式
        "hook": {"time_range": [0, 3], "technique": "悬念开头"},
        "structure": ["hook", "setup", "climax", "cta"],
        "pacing": "fast",
        "visual_style": "高饱和度 + 快速剪辑",
        "reusable_template": "# 可复用模板\n..."
    },
    "overall_summary": "这是一个...",
    "created_at": "2026-04-06T10:05:00Z"
}
```

## 6. 开发步骤（按优先级）

### Wave 1: 基础框架 + 视频处理 (Day 1)

| 步骤 | 内容 | 预计产出 |
|------|------|---------|
| W1-1 | 搭建 Next.js + FastAPI 项目骨架 | 可运行的空项目 |
| W1-2 | 实现视频上传接口（前端 + 后端） | 视频能上传并保存 |
| W1-3 | 实现视频预处理（场景检测 + 分段 + 抽帧 + 提取音频） | 视频自动分段 |

### Wave 2: AI 分析引擎 (Day 2)

| 步骤 | 内容 | 预计产出 |
|------|------|---------|
| W2-1 | 集成 Whisper API（音频转写） | 每个片段有字幕 |
| W2-2 | 集成多模态 LLM（关键帧分析） | 每个片段有画面描述 |
| W2-3 | 实现提示词逆向引擎 | 生成逆向提示词 |
| W2-4 | 实现爆款模式提取器 | 生成可复用模板 |

### Wave 3: 前端展示 + 打通 (Day 3)

| 步骤 | 内容 | 预计产出 |
|------|------|---------|
| W3-1 | 分析 Dashboard（整体视图） | 展示分析结果总览 |
| W3-2 | 片段播放器（带时间轴标记） | 可按片段查看 |
| W3-3 | 提示词卡片 + 爆款模式展示 | 结构化展示分析结果 |
| W3-4 | 导出功能 | 可导出提示词和模板 |

### Wave 4: 完善 + 部署 (Day 4)

| 步骤 | 内容 | 预计产出 |
|------|------|---------|
| W4-1 | 异步任务队列（处理耗时分析） | 大视频不阻塞 |
| W4-2 | 错误处理 + 进度反馈 | 用户看到处理进度 |
| W4-3 | UI 打磨 + 响应式 | 移动端可用 |
| W4-4 | Docker 部署 | 一键启动 |

## 7. API 设计

### 后端 API (FastAPI)

```
POST   /api/videos/upload          # 上传视频
GET    /api/videos/{id}            # 获取视频信息
GET    /api/videos/{id}/status     # 获取处理状态
POST   /api/videos/{id}/analyze    # 触发分析
GET    /api/videos/{id}/segments   # 获取片段列表
GET    /api/videos/{id}/result     # 获取分析结果
GET    /api/videos/{id}/export     # 导出结果
GET    /api/videos                 # 视频列表
```

### 前端 API Routes (Next.js BFF)

```
POST   /api/upload                 # 代理上传
GET    /api/analyze/[id]           # 代理获取结果
GET    /api/status/[id]            # SSE 状态推送
```

## 8. 环境变量

```env
# AI Services
GEMINI_API_KEY=AIza...                          # 视频理解（主要）
OPENAI_API_KEY=sk-...                           # 音频转写 + 文本推理备选
ANTHROPIC_API_KEY=sk-ant-...                    # 文本推理（提示词逆向+模式提炼）

# Storage
UPLOAD_DIR=/data/videos
MAX_VIDEO_SIZE_MB=500

# Database
DATABASE_URL=sqlite:///./data/analyzer.db

# Server
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

## 9. 风险与应对

| 风险 | 概率 | 应对 |
|------|------|------|
| 场景检测不准 | 中 | 提供手动调整分段功能 |
| LLM API 成本高 | 中 | 控制抽帧频率，批量调用 |
| 长视频处理慢 | 高 | 异步队列 + 进度反馈 |
| 视频格式兼容 | 中 | ffmpeg 统一转码 |

## 10. 验收标准

1. 用户能上传 TikTok 视频（mp4 格式）
2. 系统自动将视频切割为场景片段
3. 每个片段展示字幕 + 画面分析
4. 生成至少 3 条逆向提示词
5. 输出爆款模式分析报告（含结构/节奏/风格）
6. 前端界面清晰美观，操作流畅
7. 导出功能可用（复制/下载）
