from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path
from datetime import datetime, timedelta


def default_output(input_path: Path) -> Path:
    return input_path.with_name(f"{input_path.stem}.fixed{input_path.suffix}")


def temporary_output(final_path: Path, *, test: bool = False) -> Path:
    marker = "paladin-test" if test else "paladin-tmp"
    return final_path.with_name(f".{final_path.stem}.{marker}-{uuid.uuid4().hex}.mkv")


def valid_file(path: Path) -> bool:
    try:
        return path.is_file() and path.stat().st_size > 0
    except OSError:
        return False


def available_bytes(path: Path) -> int:
    return shutil.disk_usage(path).free


def atomic_install(temp_path: Path, final_path: Path) -> None:
    os.replace(temp_path, final_path)


def backup_path(input_path: Path) -> Path:
    return input_path.with_name(input_path.name + ".paladin-backup")


def stale_temp_files(directory: Path, *, older_than_hours: int = 24) -> list[Path]:
    cutoff = datetime.now().timestamp() - timedelta(hours=older_than_hours).total_seconds()
    result: list[Path] = []
    for path in directory.glob(".*.paladin-*.mkv"):
        try:
            if path.stat().st_mtime < cutoff:
                result.append(path)
        except OSError:
            continue
    return sorted(result)
