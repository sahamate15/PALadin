from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .errors import DependencyError, ProbeError
from .models import MediaInfo, StreamInfo
from .rationals import parse_rate


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise DependencyError(f"{name} was not found on PATH.")
    return path


def probe(path: Path, *, debug: bool = False) -> MediaInfo:
    executable = require_tool("ffprobe")
    command = [executable, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", "-show_chapters", str(path)]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        data: dict[str, Any] = json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        detail = result.stderr.strip() if "result" in locals() else str(exc)
        raise ProbeError(f"Could not inspect {path}: {detail}") from exc

    streams = tuple(_stream(item) for item in data.get("streams", []))
    fmt = data.get("format", {})
    duration = _float(fmt.get("duration"))
    attachments = sum(1 for item in data.get("streams", []) if item.get("codec_type") == "attachment")
    return MediaInfo(path, fmt.get("format_name"), duration, streams, len(data.get("chapters", [])), attachments, fmt.get("tags", {}))


def _float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _stream(item: dict[str, Any]) -> StreamInfo:
    tags = item.get("tags", {})
    return StreamInfo(
        index=int(item.get("index", -1)),
        kind=str(item.get("codec_type", "unknown")),
        codec=item.get("codec_name"),
        codec_long_name=item.get("codec_long_name"),
        duration=_float(item.get("duration")),
        rate=parse_rate(item.get("avg_frame_rate") or item.get("r_frame_rate")),
        sample_rate=int(item["sample_rate"]) if item.get("sample_rate", "").isdigit() else None,
        channels=item.get("channels"),
        channel_layout=item.get("channel_layout"),
        language=tags.get("language"),
        title=tags.get("title"),
        disposition=item.get("disposition", {}),
        tags=tags,
        time_base=item.get("time_base"),
        profile=item.get("profile"),
    )
