import os
import time
from pathlib import Path

from paladin.safety import default_output, stale_temp_files, temporary_output


def test_output_and_temp_names_are_unambiguous(tmp_path: Path):
    source = tmp_path / "Episode 06.mkv"
    output = default_output(source)
    assert output.name == "Episode 06.fixed.mkv"
    assert temporary_output(output).name.startswith(".Episode 06.fixed.paladin-tmp-")


def test_stale_temp_discovery_is_narrow(tmp_path: Path):
    stale = tmp_path / ".episode.paladin-tmp-old.mkv"
    stale.touch()
    old = time.time() - 48 * 60 * 60
    os.utime(stale, (old, old))
    (tmp_path / "not-paladin.mkv").touch()
    assert stale_temp_files(tmp_path, older_than_hours=24) == [stale]
