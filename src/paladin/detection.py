from __future__ import annotations

from .models import Detection, MediaInfo, SubtitleAssessment
from .rationals import SOURCE_RATE, TARGET_RATE, AUDIO_SPEED


SAFE_SUBTITLE_CODECS = {"subrip", "ass", "ssa", "webvtt", "hdmv_pgs_subtitle", "dvd_subtitle"}
CONVERTIBLE_SUBTITLE_CODECS = {"mov_text", "tx3g"}


def detect(media: MediaInfo) -> Detection:
    if not media.video:
        return Detection("unsupported", "none", "No video stream was found.", None)
    rate = media.video[0].rate
    if rate is None:
        return Detection("ambiguous", "low", "Video frame rate could not be determined.", None)
    if rate == TARGET_RATE or abs(float(rate - TARGET_RATE)) < 0.0005:
        return Detection("already-correct", "high", "Video already appears to use 24000/1001 fps.", rate)
    if rate == SOURCE_RATE:
        return Detection("candidate", "medium", "Stable 25 fps is consistent with PAL speedup, but does not prove it.", rate)
    return Detection("unsupported", "high", f"Video rate is {rate}, not the canonical 25 fps candidate.", rate)


def assess_subtitles(media: MediaInfo) -> tuple[SubtitleAssessment, ...]:
    result: list[SubtitleAssessment] = []
    for stream in media.subtitles:
        codec = stream.codec
        if codec in SAFE_SUBTITLE_CODECS:
            category = "safe-copy"
            reason = "Packet timestamps can be scaled in the subtitle-purpose input view."
        elif codec in CONVERTIBLE_SUBTITLE_CODECS:
            category = "conversion-required"
            reason = "Direct timestamp-preserving copy is not guaranteed for this codec."
        else:
            category = "unsupported-unsafe"
            reason = "PALadin cannot guarantee correct timestamp preservation for this format."
        result.append(SubtitleAssessment(stream.index, codec, category, reason))
    return tuple(result)


def corrected_rate_for_audio(sample_rate: int | None) -> int | None:
    return round(sample_rate * AUDIO_SPEED) if sample_rate else None
