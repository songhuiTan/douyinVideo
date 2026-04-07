"""OpenAI Whisper 转写服务"""

import json
from pathlib import Path
from typing import Optional

from openai import OpenAI


def transcribe_audio(
    audio_path: str,
    api_key: str,
    language: str = "zh",
) -> str:
    """用 gpt-4o-mini-transcribe 转写音频文件"""
    client = OpenAI(api_key=api_key)
    audio = Path(audio_path)

    if not audio.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    with open(audio, "rb") as f:
        result = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=f,
            language=language,
            response_format="text",
        )

    return result if isinstance(result, str) else result.text


def transcribe_with_timestamps(
    audio_path: str,
    api_key: str,
    language: str = "zh",
) -> str:
    """带时间戳的转写（用于字幕对齐）"""
    client = OpenAI(api_key=api_key)
    audio = Path(audio_path)

    if not audio.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    with open(audio, "rb") as f:
        result = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=f,
            language=language,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )

    if hasattr(result, "segments"):
        parts = []
        for seg in result.segments:
            # OpenAI SDK returns Pydantic-like objects with attribute access
            start = getattr(seg, "start", 0)
            text = getattr(seg, "text", "")
            parts.append(f"[{start:.1f}s] {text}")
        return "\n".join(parts)

    return getattr(result, "text", str(result))
