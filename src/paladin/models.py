from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class StreamInfo:
    index: int
    kind: str
    codec: str | None = None
    codec_long_name: str | None = None
    duration: float | None = None
    rate: Fraction | None = None
    sample_rate: int | None = None
    channels: int | None = None
    channel_layout: str | None = None
    language: str | None = None
    title: str | None = None
    disposition: dict[str, Any] = field(default_factory=dict)
    tags: dict[str, Any] = field(default_factory=dict)
    time_base: str | None = None
    profile: str | None = None


@dataclass(frozen=True)
class SubtitleAssessment:
    stream_index: int
    format_name: str | None
    category: str
    reason: str


@dataclass(frozen=True)
class MediaInfo:
    path: Path
    format_name: str | None
    duration: float | None
    streams: tuple[StreamInfo, ...]
    chapters: int
    attachments: int
    metadata: dict[str, Any]

    @property
    def video(self) -> tuple[StreamInfo, ...]:
        return tuple(s for s in self.streams if s.kind == "video")

    @property
    def audio(self) -> tuple[StreamInfo, ...]:
        return tuple(s for s in self.streams if s.kind == "audio")

    @property
    def subtitles(self) -> tuple[StreamInfo, ...]:
        return tuple(s for s in self.streams if s.kind == "subtitle")


@dataclass(frozen=True)
class Detection:
    status: str
    confidence: str
    reason: str
    source_rate: Fraction | None
    target_rate: Fraction = Fraction(24000, 1001)
    video_scale: Fraction = Fraction(25025, 24000)
    audio_speed: Fraction = Fraction(24000, 25025)

    @property
    def candidate(self) -> bool:
        return self.status == "candidate"


@dataclass(frozen=True)
class CorrectionPlan:
    input_path: Path
    output_path: Path
    selected_audio: tuple[int, ...]
    copied_audio: tuple[int, ...]
    subtitle_assessments: tuple[SubtitleAssessment, ...]
    detection: Detection
    test: bool = False
