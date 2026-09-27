from pathlib import Path
from fractions import Fraction

import pytest

from paladin.errors import UnsafeSubtitleError
from paladin.models import MediaInfo, StreamInfo
from paladin.processing import make_plan


def test_audio_track_semantics(tmp_path: Path):
    media = MediaInfo(tmp_path / "in.mkv", "matroska", 10, (
        StreamInfo(0, "video", rate=Fraction(25)),
        StreamInfo(1, "audio", codec="aac", sample_rate=48000),
        StreamInfo(2, "audio", codec="aac", sample_rate=48000),
        StreamInfo(3, "subtitle", codec="subrip"),
    ), 0, 0, {})
    all_plan = make_plan(media)
    assert all_plan.selected_audio == (1, 2)
    assert all_plan.copied_audio == ()
    selected_plan = make_plan(media, audio_tracks=(1,))
    assert selected_plan.selected_audio == (1,)
    assert selected_plan.copied_audio == (2,)


def test_unsafe_subtitles_fail_closed(tmp_path: Path):
    media = MediaInfo(tmp_path / "in.mkv", "matroska", 10, (
        StreamInfo(0, "video", rate=Fraction(25)),
        StreamInfo(1, "audio", codec="aac", sample_rate=48000),
        StreamInfo(2, "subtitle", codec="unknown"),
    ), 0, 0, {})
    with pytest.raises(UnsafeSubtitleError):
        make_plan(media)
