from pathlib import Path

from paladin.discovery import discover


def test_discovery_is_mkv_only_and_recursive_is_opt_in(tmp_path: Path):
    (tmp_path / "a.mkv").touch()
    (tmp_path / "b.mp4").touch()
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "c.mkv").touch()
    assert [p.name for p in discover([tmp_path])] == ["a.mkv"]
    assert [p.name for p in discover([tmp_path], recursive=True)] == ["a.mkv", "c.mkv"]
