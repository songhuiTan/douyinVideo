"""Gemini 2.5 Flash 视频理解服务"""

import json
import time
import threading

import google.generativeai as genai
from typing import Optional

# 模块级锁，防止并发 configure 竞争
_configure_lock = threading.Lock()
_configured_key: Optional[str] = None


def configure_gemini(api_key: str):
    """线程安全的 Gemini 配置"""
    global _configured_key
    with _configure_lock:
        if _configured_key != api_key:
            genai.configure(api_key=api_key)
            _configured_key = api_key


# PROCESSING 状态最大等待时间（秒）
_MAX_PROCESSING_WAIT = 300  # 5 分钟


def analyze_video_segment(
    video_path: str,
    segment_index: int,
    time_start: float,
    time_end: float,
    api_key: str,
) -> dict:
    """用 Gemini 分析单个视频片段"""
    configure_gemini(api_key)

    model = genai.GenerativeModel("gemini-2.5-flash")

    # 上传视频文件
    video_file = genai.upload_file(video_path)
    # 等待处理完成（带超时）
    elapsed = 0
    while video_file.state.name == "PROCESSING":
        if elapsed >= _MAX_PROCESSING_WAIT:
            try:
                genai.delete_file(video_file.name)
            except Exception:
                pass
            raise RuntimeError(f"Gemini video processing timed out after {_MAX_PROCESSING_WAIT}s for segment {segment_index}")
        time.sleep(2)
        elapsed += 2
        video_file = genai.get_file(video_file.name)

    if video_file.state.name == "FAILED":
        raise RuntimeError(f"Gemini video processing failed for segment {segment_index}")

    prompt = f"""你是一个专业的短视频分析师。分析这个视频片段（第 {segment_index + 1} 段，时间 {time_start:.1f}s - {time_end:.1f}s）。

请严格按以下 JSON 格式输出分析结果（不要输出 JSON 之外的内容）：

{{
    "visual_description": "画面内容的详细描述（3-5句话）",
    "shot_type": "特写/中景/远景/全景",
    "camera_movement": "固定/推拉/摇移/跟拍/航拍/手持",
    "technique": "这段使用了什么拍摄技巧和创意手法",
    "rhythm": "快/中/慢",
    "on_screen_text": "画面中出现的文字（标题、字幕等）",
    "color_tone": "暖色调/冷色调/高饱和/低饱和/黑白",
    "transition_type": "硬切/溶解/缩放/滑动/特效转场",
    "key_elements": ["画面中的关键视觉元素1", "元素2"],
    "emotion": "这段画面传递的情绪",
    "notes": "复刻这段视频需要注意的要点"
}}"""

    response = model.generate_content(
        [prompt, video_file],
        generation_config=genai.GenerationConfig(
            temperature=0.3,
            response_mime_type="application/json",
        ),
    )

    # 清理上传的文件
    try:
        genai.delete_file(video_file.name)
    except Exception:
        pass

    try:
        result = json.loads(response.text)
        result["segment_index"] = segment_index
        result["time_range"] = [time_start, time_end]
        return result
    except json.JSONDecodeError:
        return {
            "segment_index": segment_index,
            "time_range": [time_start, time_end],
            "visual_description": response.text,
            "shot_type": "未知",
            "camera_movement": "未知",
            "technique": "",
            "rhythm": "中",
            "on_screen_text": "",
            "color_tone": "",
            "transition_type": "",
            "key_elements": [],
            "emotion": "",
            "notes": "",
            "_raw_response": response.text,
        }


def analyze_full_video(
    video_path: str,
    duration: float,
    api_key: str,
) -> dict:
    """用 Gemini 分析完整视频（用于整体概览）"""
    configure_gemini(api_key)

    model = genai.GenerativeModel("gemini-2.5-flash")

    video_file = genai.upload_file(video_path)
    elapsed = 0
    while video_file.state.name == "PROCESSING":
        if elapsed >= _MAX_PROCESSING_WAIT:
            try:
                genai.delete_file(video_file.name)
            except Exception:
                pass
            raise RuntimeError(f"Gemini full video processing timed out after {_MAX_PROCESSING_WAIT}s")
        time.sleep(2)
        elapsed += 2
        video_file = genai.get_file(video_file.name)

    if video_file.state.name == "FAILED":
        raise RuntimeError("Gemini full video processing failed")

    prompt = f"""你是一个专业的 TikTok/抖音爆款视频分析师。分析这个完整的短视频（时长 {duration:.1f} 秒）。

请严格按以下 JSON 格式输出（不要输出 JSON 之外的内容）：

{{
    "overall_summary": "视频整体内容概述（2-3句话）",
    "video_type": "教程/剧情/Vlog/挑战/测评/日常/其他",
    "target_audience": "目标受众描述",
    "hook_technique": "开头使用的吸引注意力的技巧",
    "viral_elements": ["可能让它成为爆款的元素1", "元素2", "元素3"],
    "structure": ["视频结构各阶段，如：开头hook", "正文setup", "高潮climax", "结尾cta"],
    "visual_style": "整体视觉风格描述",
    "pacing": "整体节奏：快/中/慢/快慢交替",
    "music_style": "配乐风格和情绪",
    "engagement_triggers": ["驱动互动（点赞/评论/分享）的元素"],
    "replication_difficulty": "简单/中等/困难",
    "replication_notes": "复刻这个视频的主要注意事项"
}}"""

    response = model.generate_content(
        [prompt, video_file],
        generation_config=genai.GenerationConfig(
            temperature=0.3,
            response_mime_type="application/json",
        ),
    )

    try:
        genai.delete_file(video_file.name)
    except Exception:
        pass

    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        return {"overall_summary": response.text, "_raw": True}
