from __future__ import annotations

import subprocess
from collections.abc import Callable

from .errors import ProcessingError
from .models import CorrectionPlan, MediaInfo
from .probing import require_tool
from .rationals import VIDEO_SCALE


def build_command(plan: CorrectionPlan, media: MediaInfo, *, duration: int | None = None) -> list[str]:
    """Build role-isolated FFmpeg inputs.

    Input 0 is timestamp-scaled and maps video only.
    Input 1 is unscaled and maps audio only.
    Input 2 is independently timestamp-scaled and maps subtitles/attachments.
    """
    ffmpeg = require_tool("ffmpeg")
    # FFmpeg's -itsscale parser accepts a decimal here, not a rational string.
    # The Fraction remains exact internally; this is only serialization at the
    # external command boundary.
    scale = f"{float(VIDEO_SCALE):.15f}"
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-progress", "pipe:1", "-nostats"]
    cmd += ["-itsscale", scale, "-i", str(plan.input_path)]
    cmd += ["-i", str(plan.input_path)]
    cmd += ["-itsscale", scale, "-i", str(plan.input_path)]

    cmd += ["-map", "0:v:0", "-c:v", "copy"]
    for position, stream_index in enumerate(plan.selected_audio):
        cmd += ["-map", f"1:a:{_relative_index(media, stream_index, 'audio')}", f"-c:a:{position}", "aac"]
        stream = next(s for s in media.audio if s.index == stream_index)
        intermediate = round((stream.sample_rate or 48000) * 24000 / 25025)
        cmd += [f"-filter:a:{position}", f"asetrate={intermediate},aresample={stream.sample_rate or 48000}"]
        if stream.sample_rate:
            cmd += [f"-ar:a:{position}", str(stream.sample_rate)]

    for position, stream_index in enumerate(plan.copied_audio, start=len(plan.selected_audio)):
        cmd += ["-map", f"1:a:{_relative_index(media, stream_index, 'audio')}", f"-c:a:{position}", "copy"]

    safe_subs = [a.stream_index for a in plan.subtitle_assessments if a.category == "safe-copy"]
    for stream_index in safe_subs:
        cmd += ["-map", f"2:s:{_relative_index(media, stream_index, 'subtitle')}", "-c:s", "copy"]

    # Attachments are mapped from the scaled subtitle-purpose input but are not
    # timestamped media. They remain byte-for-byte copied where supported.
    if media.attachments:
        cmd += ["-map", "2:t?", "-c:t", "copy"]
    cmd += ["-map_metadata", "0", "-map_chapters", "0", "-copy_unknown"]
    if duration is not None:
        cmd += ["-t", str(duration)]
    cmd += ["-y", str(plan.output_path)]
    return cmd


def _relative_index(media: MediaInfo, stream_index: int, kind: str) -> int:
    streams = [stream for stream in media.streams if stream.kind == kind]
    return next(i for i, stream in enumerate(streams) if stream.index == stream_index)


def run(command: list[str], *, debug: bool = False, on_progress: Callable[[dict[str, str]], None] | None = None) -> None:
    process: subprocess.Popen[str] | None = None
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        assert process.stdout is not None
        progress: dict[str, str] = {}
        for line in process.stdout:
            line = line.strip()
            if "=" in line:
                key, value = line.split("=", 1)
                progress[key] = value
                if on_progress and key in {"out_time_ms", "progress"}:
                    on_progress(dict(progress))
        stderr = process.stderr.read() if process.stderr else ""
        return_code = process.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, command, stderr=stderr)
    except KeyboardInterrupt:
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        raise
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "FFmpeg returned a failure status.").strip()
        raise ProcessingError(detail if debug else "FFmpeg failed while processing the media.") from exc
