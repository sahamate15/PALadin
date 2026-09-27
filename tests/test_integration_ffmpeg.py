import shutil
import subprocess
from pathlib import Path

import pytest

from paladin.processing import make_plan, process
from paladin.probing import probe


@pytest.mark.integration
def test_synthetic_video_audio_subtitles_stay_synchronized(tmp_path: Path):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("FFmpeg is not installed")
    subtitle = tmp_path / "markers.srt"
    subtitle.write_text("1\n00:00:02,000 --> 00:00:03,000\nSYNC MARKER\n", encoding="utf-8")
    source = tmp_path / "fixture.mkv"
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=320x180:rate=25:duration=8",
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=8",
        "-f", "lavfi", "-i", "sine=frequency=880:sample_rate=48000:duration=8",
        "-i", str(subtitle), "-map", "0:v", "-map", "1:a", "-map", "2:a", "-map", "3:0",
        "-c:v", "ffv1", "-c:a", "pcm_s16le", "-c:s", "srt", "-t", "8", str(source), "-y",
    ]
    subprocess.run(command, check=True, capture_output=True)
    media = probe(source)
    plan = make_plan(media, tmp_path / "fixture.fixed.mkv")
    output = process(plan, media)
    result = probe(output)
    assert len(result.video) == 1
    assert len(result.audio) == 2
    assert len(result.subtitles) == 1
    assert result.duration and result.duration > 8
    assert result.audio[0].duration is None or result.audio[0].duration > 0
    assert result.subtitles[0].codec == "subrip"
