from fractions import Fraction
from pathlib import Path

from paladin.ffmpeg import build_command
from paladin.models import CorrectionPlan, MediaInfo, StreamInfo
from paladin.detection import assess_subtitles, detect


def test_command_has_role_isolated_inputs_and_explicit_maps():
    media = MediaInfo(Path("input.mkv"), "matroska", 8, (
        StreamInfo(0, "video", codec="ffv1", rate=Fraction(25)),
        StreamInfo(1, "audio", codec="aac", sample_rate=48000),
        StreamInfo(2, "audio", codec="aac", sample_rate=48000),
        StreamInfo(3, "subtitle", codec="subrip"),
    ), 0, 0, {})
    plan = CorrectionPlan(Path("input.mkv"), Path("out.mkv"), (1,), (2,), assess_subtitles(media), detect(media))
    command = build_command(plan, media)
    assert command.count("-i") == 3
    assert "-map" in command
    assert "0:v:0" in command
    assert "1:a:0" in command and "1:a:1" in command
    assert "2:s:0" in command
    assert "asetrate=46034,aresample=48000" in command
