"""Claude Sonnet 4 推理服务：提示词逆向 + 爆款模式提炼"""

import json
from typing import Optional

import anthropic

from backend.config import settings


def _get_client(api_key: str) -> anthropic.Anthropic:
    """创建 Anthropic 客户端，支持自定义 base_url"""
    kwargs = {"api_key": api_key}
    if settings.anthropic_base_url:
        kwargs["base_url"] = settings.anthropic_base_url
    return anthropic.Anthropic(**kwargs)


def reverse_prompts(
    segment_analyses: list[dict],
    full_video_summary: dict,
    api_key: str,
) -> list[dict]:
    """从分析结果反推创作提示词"""
    client = _get_client(api_key)

    segments_text = json.dumps(segment_analyses, ensure_ascii=False, indent=2)
    summary_text = json.dumps(full_video_summary, ensure_ascii=False, indent=2)

    prompt = f"""你是一个专业的 TikTok/抖音创意逆向工程师。

给定以下视频分析数据，反推出创作者可能使用的创意简报和 AI 提示词。

## 视频整体分析
{summary_text}

## 各段分析
{segments_text}

请输出三类提示词，严格按 JSON 格式：
{{
    "visual": {{
        "prompt": "画面相关的提示词，描述这个视频的视觉风格、构图、色调等",
        "confidence": 0.0-1.0
    }},
    "narrative": {{
        "prompt": "叙事相关的提示词，描述内容策略、情感曲线、结构设计",
        "confidence": 0.0-1.0
    }},
    "style": {{
        "prompt": "风格相关的提示词，描述剪辑风格、配乐选择、整体调性",
        "confidence": 0.0-1.0
    }}
}}

只输出 JSON，不要其他内容。"""

    text = ""
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text
        result = json.loads(text)
        prompts = []
        for ptype in ["visual", "narrative", "style"]:
            if ptype in result:
                prompts.append({
                    "type": ptype,
                    "prompt": result[ptype]["prompt"],
                    "confidence": result[ptype].get("confidence", 0.7),
                })
        return prompts
    except json.JSONDecodeError:
        return [{
            "type": "combined",
            "prompt": text or "JSON 解析失败",
            "confidence": 0.5,
        }]
    except Exception as e:
        return [{
            "type": "error",
            "prompt": f"提示词逆向失败: {str(e)}",
            "confidence": 0.0,
        }]


def extract_patterns(
    segment_analyses: list[dict],
    full_video_summary: dict,
    transcription: str,
    api_key: str,
) -> dict:
    """提炼爆款模式和可复用模板"""
    client = _get_client(api_key)

    segments_text = json.dumps(segment_analyses, ensure_ascii=False, indent=2)
    summary_text = json.dumps(full_video_summary, ensure_ascii=False, indent=2)

    prompt = f"""你是一个专业的短视频爆款分析师。

给定以下视频分析数据，提炼爆款模式并生成可复用的拍摄模板。

## 视频整体分析
{summary_text}

## 各段分析
{segments_text}

## 字幕/台词
{transcription}

请严格按以下 JSON 格式输出：
{{
    "structure": ["视频结构各阶段，如 hook", "setup", "climax", "cta"],
    "pacing": "整体节奏描述",
    "visual_style": "视觉风格描述",
    "music_suggestion": "推荐配乐风格或具体曲目",
    "reusable_template": "可复用的拍摄模板，用 Markdown 格式，包含分镜、台词、拍摄技巧"
}}

只输出 JSON，不要其他内容。"""

    text = ""
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "structure": [],
            "pacing": "未知",
            "visual_style": (text or "")[:200],
            "music_suggestion": "",
            "reusable_template": text or "",
        }
    except Exception as e:
        return {
            "structure": [],
            "pacing": "分析失败",
            "visual_style": "",
            "music_suggestion": "",
            "reusable_template": f"模式提炼失败: {str(e)}",
        }
