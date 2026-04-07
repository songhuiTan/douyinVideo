"""智谱 GLM-4.6V 视觉分析服务（通过截帧 + base64 图片调用）"""

import base64
import json
import subprocess

import httpx


def _extract_frames(
    video_path: str,
    time_start: float,
    time_end: float,
    count: int = 3,
) -> list[str]:
    """截取视频帧，返回 base64 编码 PNG 列表"""
    duration = time_end - time_start
    frames = []
    for i in range(count):
        t = time_start + duration * (i + 1) / (count + 1)
        result = subprocess.run(
            [
                "ffmpeg", "-ss", str(t), "-i", video_path,
                "-frames:v", "1", "-f", "image2pipe",
                "-vcodec", "png", "pipe:1",
            ],
            capture_output=True,
            timeout=30,
        )
        if result.stdout:
            frames.append(base64.b64encode(result.stdout).decode())
    return frames


def _extract_frames_full(
    video_path: str,
    duration: float,
    count: int = 5,
) -> list[str]:
    """从全片中均匀截取帧"""
    return _extract_frames(video_path, 0.0, duration, count)


def _call_glm4v(
    api_key: str,
    model: str,
    prompt: str,
    frames: list[str],
) -> str:
    """调用智谱 GLM-4.6V，返回原始文本"""
    content: list[dict] = [{"type": "text", "text": prompt}]
    for frame_b64 in frames:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{frame_b64}"},
        })

    resp = httpx.post(
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "temperature": 0.3,
            "max_tokens": 2000,
        },
        timeout=60.0,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


# ── 分段分析 prompt ──────────────────────────────────────

_SEGMENT_PROMPT = """你是一个专业的短视频分析师。分析这个视频片段（第 {seg_num} 段，时间 {start:.1f}s - {end:.1f}s）的截图帧。

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


# ── 全片分析 prompt ──────────────────────────────────────

_FULL_PROMPT = """你是一个专业的 TikTok/抖音爆款视频分析师。分析这个完整的短视频（时长 {duration:.1f} 秒）的截图帧。

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


def _parse_json_response(text: str) -> dict | None:
    """尝试从响应文本中提取 JSON"""
    text = text.strip()
    # 去掉可能的 markdown 代码块包裹
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _segment_fallback(
    segment_index: int,
    time_start: float,
    time_end: float,
    raw_text: str,
) -> dict:
    """分段分析降级结果"""
    return {
        "segment_index": segment_index,
        "time_range": [time_start, time_end],
        "visual_description": raw_text,
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
        "_raw_response": raw_text,
    }


def analyze_video_segment(
    video_path: str,
    segment_index: int,
    time_start: float,
    time_end: float,
    api_key: str,
    model: str = "glm-4.6v-flashx",
) -> dict:
    """用智谱 GLM-4.6V 分析单个视频片段"""
    frames = _extract_frames(video_path, time_start, time_end, count=3)
    if not frames:
        return _segment_fallback(segment_index, time_start, time_end, "截帧失败")

    prompt = _SEGMENT_PROMPT.format(
        seg_num=segment_index + 1, start=time_start, end=time_end,
    )

    try:
        text = _call_glm4v(api_key, model, prompt, frames)
    except Exception as e:
        return _segment_fallback(
            segment_index, time_start, time_end,
            f"智谱 API 调用失败: {e}",
        )

    result = _parse_json_response(text)
    if result is None:
        return _segment_fallback(segment_index, time_start, time_end, text)

    result["segment_index"] = segment_index
    result["time_range"] = [time_start, time_end]
    return result


def analyze_full_video(
    video_path: str,
    duration: float,
    api_key: str,
    model: str = "glm-4.6v-flashx",
) -> dict:
    """用智谱 GLM-4.6V 分析完整视频"""
    frames = _extract_frames_full(video_path, duration, count=5)
    if not frames:
        return {"overall_summary": "截帧失败", "_raw": True}

    prompt = _FULL_PROMPT.format(duration=duration)

    try:
        text = _call_glm4v(api_key, model, prompt, frames)
    except Exception as e:
        return {"overall_summary": f"智谱 API 调用失败: {e}", "_raw": True}

    result = _parse_json_response(text)
    if result is None:
        return {"overall_summary": text, "_raw": True}

    return result
