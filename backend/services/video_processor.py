"""视频预处理：场景检测 + 分段切割 + 音频提取"""

import subprocess
import json
from pathlib import Path
from typing import Optional


def get_video_metadata(video_path: str) -> dict:
    """用 ffprobe 获取视频元数据"""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", str(video_path)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        raise RuntimeError("ffprobe timed out after 60s")

    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")

    info = json.loads(result.stdout)
    duration = float(info["format"]["duration"])

    # 找视频流
    video_stream = next(
        (s for s in info["streams"] if s["codec_type"] == "video"), None
    )
    if video_stream is None:
        raise ValueError(f"No video stream found in {video_path}")

    has_audio = any(s["codec_type"] == "audio" for s in info["streams"])

    width = int(video_stream["width"])
    height = int(video_stream["height"])

    return {
        "duration": duration,
        "width": width,
        "height": height,
        "has_audio": has_audio,
        "format": info["format"]["format_name"],
    }


def detect_scenes(video_path: str, threshold: float = 0.3) -> list[tuple[float, float]]:
    """用 PySceneDetect 检测场景切割点"""
    from scenedetect import detect, ContentDetector

    scene_list = detect(video_path, ContentDetector(threshold=threshold))

    if not scene_list:
        # 未检测到场景切换，整片作为一段
        meta = get_video_metadata(video_path)
        return [(0.0, meta["duration"])]

    segments = []
    for i, (start, end) in enumerate(scene_list):
        segments.append((
            start.get_seconds(),
            end.get_seconds()
        ))

    return segments


def split_video(video_path: str, segments: list[tuple[float, float]],
                output_dir: str) -> list[tuple[int, str]]:
    """用 ffmpeg 按场景分段切割视频。

    Returns list of (original_segment_index, path) to maintain alignment
    even when some segments fail to split.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    segment_paths = []
    for i, (start, end) in enumerate(segments):
        duration = end - start
        output_path = out / f"seg_{i:03d}.mp4"

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-ss", str(start),
            "-t", str(duration),
            "-c", "copy",
            "-movflags", "+faststart",
            str(output_path)
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                print(f"Warning: segment {i} split failed: {result.stderr}")
                continue
        except subprocess.TimeoutExpired:
            print(f"Warning: segment {i} split timed out after 120s")
            continue

        segment_paths.append((i, str(output_path)))

    return segment_paths


def extract_audio(video_path: str, output_path: str) -> Optional[str]:
    """用 ffmpeg 提取音频为 mp3"""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vn",
        "-acodec", "libmp3lame",
        "-q:a", "2",
        str(out)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        print("Warning: audio extraction timed out after 60s")
        return None

    if result.returncode != 0:
        print(f"Warning: audio extraction failed: {result.stderr}")
        return None

    return str(out)


def extract_segment_audio(segment_path: str, output_path: str) -> Optional[str]:
    """提取单个分段的音频"""
    return extract_audio(segment_path, output_path)
