from pathlib import Path
from fractions import Fraction

from paladin.detection import assess_subtitles, detect
from paladin.models import MediaInfo, StreamInfo


def media(rate: Fraction, subtitle_codec: str = "subrip") -> MediaInfo:
    return MediaInfo(
        Path("input.mkv"), "matroska", 10.0,
        (StreamInfo(0, "video", rate=rate), StreamInfo(1, "audio", codec="aac", sample_rate=48000), StreamInfo(2, "subtitle", codec=subtitle_codec)),
        0, 0, {},
    )


def test_25_fps_is_candidate_not_proof():
    result = detect(media(Fraction(25, 1)))
    assert result.status == "candidate"
    assert result.confidence == "medium"


def test_already_correct_is_not_processed():
    assert detect(media(Fraction(24000, 1001))).status == "already-correct"


def test_subtitle_safety_categories_are_explicit():
    assert assess_subtitles(media(Fraction(25), "subrip"))[0].category == "safe-copy"
    assert assess_subtitles(media(Fraction(25), "mov_text"))[0].category == "conversion-required"
    assert assess_subtitles(media(Fraction(25), "unknown"))[0].category == "unsupported-unsafe"
