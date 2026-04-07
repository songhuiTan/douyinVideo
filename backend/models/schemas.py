from pydantic import BaseModel, field_validator
from typing import Optional


class VideoUploadResponse(BaseModel):
    video_id: str
    filename: str
    status: str


class Segment(BaseModel):
    index: int
    time_start: float
    time_end: float
    duration: float


class AnalysisStatus(BaseModel):
    video_id: str
    status: str  # uploaded | processing | analyzing | completed | failed
    progress: float  # 0.0 - 1.0
    message: str = ""


class SegmentAnalysis(BaseModel):
    index: int
    time_range: list[float]

    @field_validator("time_range")
    @classmethod
    def validate_time_range(cls, v):
        if len(v) != 2:
            raise ValueError("time_range must have exactly 2 elements [start, end]")
        if v[0] < 0 or v[1] < 0:
            raise ValueError("time values must be non-negative")
        if v[1] <= v[0]:
            raise ValueError("time_range end must be greater than start")
        return v

    shot_type: str
    camera_movement: str
    visual_description: str
    transcription: str = ""
    technique: str
    rhythm: str
    notes: str


class ReversedPrompt(BaseModel):
    type: str  # visual | narrative | style
    prompt: str
    confidence: float

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v


class ViralPatterns(BaseModel):
    structure: list[str]
    pacing: str
    visual_style: str
    music_suggestion: str
    reusable_template: str


class ReplicationGuide(BaseModel):
    video_id: str
    title: str
    summary: str
    segments: list[SegmentAnalysis]
    prompts: list[ReversedPrompt]
    patterns: ViralPatterns
    export_markdown: str = ""
