"""分析管线编排：场景检测 → 并行 AI 分析 → 生成复刻指南"""

import asyncio
import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional

from backend.config import settings
from backend.models.schemas import (
    AnalysisStatus,
    ReplicationGuide,
    SegmentAnalysis,
    ReversedPrompt,
    ViralPatterns,
)
from backend.services import gemini_analyzer, zhipu_analyzer, transcriber, claude_reasoner
from backend.services.video_processor import (
    detect_scenes,
    extract_audio,
    get_video_metadata,
    split_video,
)


# ── 分段合并逻辑 ──────────────────────────────────────────
# 短于 MIN_SEGMENT_DURATION 秒的段合并到相邻段
# 上限 MAX_SEGMENTS 段
MIN_SEGMENT_DURATION = 2.0
MAX_SEGMENTS = 12


def merge_short_segments(
    segments: list[tuple[float, float]],
) -> list[tuple[float, float]]:
    """合并过短的分段"""
    if not segments:
        return segments

    merged = [segments[0]]
    for start, end in segments[1:]:
        prev_start, prev_end = merged[-1]
        if (end - start) < MIN_SEGMENT_DURATION:
            # 合并到前一段
            merged[-1] = (prev_start, end)
        else:
            merged.append((start, end))

    # 如果合并后仍超过上限，均匀合并
    while len(merged) > MAX_SEGMENTS:
        # 找最短的相邻对合并
        min_gap = float("inf")
        min_idx = 0
        for i in range(len(merged) - 1):
            gap = merged[i + 1][1] - merged[i][0]
            if gap < min_gap:
                min_gap = gap
                min_idx = i
        merged[min_idx] = (merged[min_idx][0], merged[min_idx + 1][1])
        del merged[min_idx + 1]

    return merged


# ── 异步包装 ──────────────────────────────────────────────

def _get_vision_analyzer():
    """根据配置返回对应的视觉分析模块"""
    if settings.vision_provider == "gemini":
        return gemini_analyzer
    return zhipu_analyzer


def _get_vision_api_key() -> str:
    """根据配置返回对应的 API key"""
    if settings.vision_provider == "gemini":
        return settings.gemini_api_key
    return settings.zhipu_api_key


def _get_vision_model() -> str:
    """返回视觉模型名称（智谱专用）"""
    return settings.zhipu_vision_model


async def async_analyze_segment(
    segment_path: str,
    segment_index: int,
    time_start: float,
    time_end: float,
) -> dict:
    """异步包装分段视觉分析"""
    analyzer = _get_vision_analyzer()
    api_key = _get_vision_api_key()
    kwargs = {}
    if analyzer is zhipu_analyzer:
        kwargs["model"] = _get_vision_model()
    return await asyncio.to_thread(
        analyzer.analyze_video_segment,
        segment_path,
        segment_index,
        time_start,
        time_end,
        api_key,
        **kwargs,
    )


async def async_analyze_full_video(
    video_path: str,
    duration: float,
) -> dict:
    """异步包装全片视觉分析"""
    analyzer = _get_vision_analyzer()
    api_key = _get_vision_api_key()
    kwargs = {}
    if analyzer is zhipu_analyzer:
        kwargs["model"] = _get_vision_model()
    return await asyncio.to_thread(
        analyzer.analyze_full_video,
        video_path,
        duration,
        api_key,
        **kwargs,
    )


async def async_transcribe(
    audio_path: str,
) -> str:
    """异步包装转写"""
    return await asyncio.to_thread(
        transcriber.transcribe_audio,
        audio_path,
        settings.openai_api_key,
    )


async def async_reverse_prompts(
    segments: list[dict],
    summary: dict,
) -> list[dict]:
    """异步包装提示词逆向"""
    return await asyncio.to_thread(
        claude_reasoner.reverse_prompts,
        segments,
        summary,
        settings.anthropic_api_key,
    )


async def async_extract_patterns(
    segments: list[dict],
    summary: dict,
    transcription: str,
) -> dict:
    """异步包装爆款模式提炼"""
    return await asyncio.to_thread(
        claude_reasoner.extract_patterns,
        segments,
        summary,
        transcription,
        settings.anthropic_api_key,
    )


# ── 管线主流程 ────────────────────────────────────────────

async def run_analysis(
    video_path: str,
    video_id: str,
    work_dir: str,
    status_callback=None,
) -> ReplicationGuide:
    """
    执行完整分析管线。

    Args:
        video_path: 上传的视频文件路径
        video_id: 唯一标识
        work_dir: 工作目录（分段文件、音频等）
        status_callback: 可选的进度回调 fn(video_id, status, progress, message)
    """

    def update_status(status: str, progress: float, message: str):
        if status_callback:
            status_callback(video_id, status, progress, message)

    # ── Step 1: 获取元数据 ──────────────────────────
    update_status("processing", 0.05, "获取视频元数据...")
    metadata = get_video_metadata(video_path)

    # 校验时长
    if metadata["duration"] < 15:
        raise ValueError(f"视频太短 ({metadata['duration']:.1f}s)，至少需要 15 秒")
    if metadata["duration"] > 120:
        raise ValueError(f"视频太长 ({metadata['duration']:.1f}s)，最长 120 秒")

    # ── Step 2: 场景检测 + 分段 ─────────────────────
    update_status("processing", 0.1, "检测场景切换点...")
    raw_segments = detect_scenes(video_path)
    segments = merge_short_segments(raw_segments)

    update_status("processing", 0.15, f"检测到 {len(segments)} 个场景片段")

    # ── Step 3: 切割分段文件 ─────────────────────────
    seg_dir = os.path.join(work_dir, "segments")
    update_status("processing", 0.2, "切割视频分段...")
    segment_paths = split_video(video_path, segments, seg_dir)

    if not segment_paths:
        raise RuntimeError("视频分段切割失败，所有段均无法生成")

    # ── Step 4: 并行 AI 分析 ────────────────────────
    update_status("analyzing", 0.25, "启动 AI 分析管线...")

    # split_video returns (original_index, path) tuples for correct alignment
    seg_info = []  # [(path, seg_index, start, end)]
    for orig_idx, seg_path in segment_paths:
        start, end = segments[orig_idx]
        seg_info.append((seg_path, orig_idx, start, end))

    # 并行任务 1: 各段 Gemini 分析
    seg_tasks = []
    for seg_path, seg_idx, start, end in seg_info:
        seg_tasks.append(async_analyze_segment(seg_path, seg_idx, start, end))

    # 并行任务 2: 全片 Gemini 分析
    full_task = async_analyze_full_video(video_path, metadata["duration"])

    # 并行任务 3: 音频转写（如果有音轨）
    audio_path = os.path.join(work_dir, "audio.mp3")
    transcription = ""

    # 音频提取也要异步化（ffmpeg 可能耗时）
    async def async_extract_and_transcribe():
        audio_file = await asyncio.to_thread(extract_audio, video_path, audio_path)
        if audio_file:
            return await async_transcribe(audio_file)
        return ""

    # 启动所有并行任务
    tasks = seg_tasks + [full_task]
    transcribe_task = None
    if metadata["has_audio"]:
        transcribe_task = async_extract_and_transcribe()
        tasks.append(transcribe_task)

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 解析分段分析结果
    seg_results = []
    for i, r in enumerate(results[:len(seg_tasks)]):
        if isinstance(r, Exception):
            seg_results.append({
                "segment_index": i,
                "time_range": list(segments[i]),
                "visual_description": f"分析失败: {str(r)}",
                "shot_type": "未知",
                "camera_movement": "未知",
                "technique": "",
                "rhythm": "中",
                "notes": "",
            })
        else:
            seg_results.append(r)

    # 解析全片分析结果
    full_summary = {}
    full_idx = len(seg_tasks)
    if full_idx < len(results) and not isinstance(results[full_idx], Exception):
        full_summary = results[full_idx]

    # 解析转写结果
    if transcribe_task is not None:
        trans_idx = len(seg_tasks) + 1
        if trans_idx < len(results) and not isinstance(results[trans_idx], Exception):
            transcription = results[trans_idx]

    update_status("analyzing", 0.6, f"AI 视觉分析完成，开始推理...")

    # ── Step 5: Claude 推理（并行） ─────────────────
    prompts_task = async_reverse_prompts(seg_results, full_summary)
    patterns_task = async_extract_patterns(seg_results, full_summary, transcription)

    prompts_result, patterns_result = await asyncio.gather(
        prompts_task, patterns_task, return_exceptions=True
    )

    if isinstance(prompts_result, Exception):
        prompts_result = [{"type": "error", "prompt": str(prompts_result), "confidence": 0.0}]
    if isinstance(patterns_result, Exception):
        patterns_result = {
            "structure": [], "pacing": "分析失败",
            "visual_style": "", "music_suggestion": "",
            "reusable_template": str(patterns_result),
        }

    update_status("analyzing", 0.85, "生成复刻指南...")

    # ── Step 6: 组装复刻指南 ────────────────────────
    # 把转写文本填入各段
    segment_analyses = []
    for seg in seg_results:
        segment_analyses.append(SegmentAnalysis(
            index=seg.get("segment_index", 0),
            time_range=seg.get("time_range", [0, 0]),
            shot_type=seg.get("shot_type", "未知"),
            camera_movement=seg.get("camera_movement", "未知"),
            visual_description=seg.get("visual_description", ""),
            transcription=seg.get("on_screen_text", ""),
            technique=seg.get("technique", ""),
            rhythm=seg.get("rhythm", "中"),
            notes=seg.get("notes", ""),
        ))

    reversed_prompts = [
        ReversedPrompt(type=p["type"], prompt=p["prompt"], confidence=p["confidence"])
        for p in prompts_result
    ]

    patterns = ViralPatterns(
        structure=patterns_result.get("structure", []),
        pacing=patterns_result.get("pacing", "未知"),
        visual_style=patterns_result.get("visual_style", ""),
        music_suggestion=patterns_result.get("music_suggestion", ""),
        reusable_template=patterns_result.get("reusable_template", ""),
    )

    title = full_summary.get("video_type", "视频分析") + "复刻指南"

    guide = ReplicationGuide(
        video_id=video_id,
        title=title,
        summary=full_summary.get("overall_summary", ""),
        segments=segment_analyses,
        prompts=reversed_prompts,
        patterns=patterns,
    )

    # 生成 Markdown 导出
    guide.export_markdown = generate_markdown(guide, transcription)

    update_status("completed", 1.0, "分析完成")

    # ── Step 7: 清理临时文件 ────────────────────────
    try:
        if os.path.isdir(seg_dir):
            shutil.rmtree(seg_dir)
        if os.path.exists(audio_path):
            os.remove(audio_path)
    except Exception:
        pass

    return guide


def generate_markdown(guide: ReplicationGuide, transcription: str = "") -> str:
    """生成可导出的 Markdown 格式复刻指南"""
    lines = []
    lines.append(f"# {guide.title}\n")
    lines.append(f"## 概述\n\n{guide.summary}\n")

    # 分镜表
    lines.append("## 分镜表\n")
    lines.append("| # | 时间 | 景别 | 运镜 | 节奏 | 拍摄技巧 |")
    lines.append("|---|------|------|------|------|----------|")
    for seg in guide.segments:
        time_range = f"{seg.time_range[0]:.1f}s-{seg.time_range[1]:.1f}s"
        lines.append(
            f"| {seg.index} | {time_range} | {seg.shot_type} | "
            f"{seg.camera_movement} | {seg.rhythm} | {seg.technique[:30]} |"
        )

    # 各段详情
    lines.append("\n## 各段详情\n")
    for seg in guide.segments:
        lines.append(f"### 段 {seg.index} ({seg.time_range[0]:.1f}s - {seg.time_range[1]:.1f}s)\n")
        lines.append(f"- **景别**: {seg.shot_type}")
        lines.append(f"- **运镜**: {seg.camera_movement}")
        lines.append(f"- **节奏**: {seg.rhythm}")
        lines.append(f"- **画面**: {seg.visual_description}")
        if seg.transcription:
            lines.append(f"- **文字/字幕**: {seg.transcription}")
        lines.append(f"- **拍摄技巧**: {seg.technique}")
        lines.append(f"- **复刻要点**: {seg.notes}")
        lines.append("")

    # 提示词
    lines.append("## 逆向提示词\n")
    for p in guide.prompts:
        lines.append(f"### {p.type} (置信度 {p.confidence:.0%})\n")
        lines.append(f"```\n{p.prompt}\n```\n")

    # 爆款模式
    lines.append("## 爆款模式\n")
    lines.append(f"- **结构**: {' → '.join(guide.patterns.structure)}")
    lines.append(f"- **节奏**: {guide.patterns.pacing}")
    lines.append(f"- **视觉风格**: {guide.patterns.visual_style}")
    lines.append(f"- **配乐建议**: {guide.patterns.music_suggestion}")

    # 可复用模板
    if guide.patterns.reusable_template:
        lines.append("\n## 可复用拍摄模板\n")
        lines.append(guide.patterns.reusable_template)

    return "\n".join(lines)
