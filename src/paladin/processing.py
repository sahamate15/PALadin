from __future__ import annotations

from pathlib import Path
from collections.abc import Callable

from .detection import assess_subtitles, detect
from .errors import ProcessingError, UnsafeSubtitleError
from .ffmpeg import build_command, run
from .models import CorrectionPlan, MediaInfo
from .probing import probe
from .safety import atomic_install, default_output, temporary_output, valid_file
from .safety import backup_path


def make_plan(media: MediaInfo, output: Path | None = None, audio_tracks: tuple[int, ...] = ()) -> CorrectionPlan:
    detection = detect(media)
    assessments = assess_subtitles(media)
    unsafe = [item for item in assessments if item.category != "safe-copy"]
    if unsafe:
        raise UnsafeSubtitleError("Subtitle timing cannot be guaranteed for: " + ", ".join(str(i.stream_index) for i in unsafe))
    selected = audio_tracks or tuple(stream.index for stream in media.audio)
    available = {stream.index for stream in media.audio}
    invalid = set(selected) - available
    if invalid:
        raise ProcessingError(f"Unknown audio stream index/indices: {sorted(invalid)}")
    copied = tuple(stream.index for stream in media.audio if stream.index not in selected)
    return CorrectionPlan(media.path, output or default_output(media.path), tuple(selected), copied, assessments, detection)


def process(plan: CorrectionPlan, media: MediaInfo, *, duration: int | None = None, debug: bool = False, replace: bool = False, on_progress: Callable[[dict[str, str]], None] | None = None) -> Path:
    if replace and plan.output_path != plan.input_path:
        raise ProcessingError("Safe replacement requires the output path to be the original input path.")
    if not replace and plan.output_path == plan.input_path:
        raise ProcessingError("Refusing to overwrite the input without replacement mode.")
    temp = temporary_output(plan.output_path, test=plan.test)
    temp_plan = CorrectionPlan(plan.input_path, temp, plan.selected_audio, plan.copied_audio, plan.subtitle_assessments, plan.detection, plan.test)
    try:
        run(build_command(temp_plan, media, duration=duration), debug=debug, on_progress=on_progress)
        if not valid_file(temp):
            raise ProcessingError("FFmpeg completed but produced an empty or missing output.")
        output_media = probe(temp, debug=debug)
        if len(output_media.video) != len(media.video) or len(output_media.audio) != len(media.audio):
            raise ProcessingError("Output validation failed: stream counts changed unexpectedly.")
        if len(output_media.subtitles) != len(media.subtitles):
            raise ProcessingError("Output validation failed: subtitle streams were not preserved.")
        if replace:
            backup = backup_path(plan.input_path)
            if backup.exists():
                raise ProcessingError(f"Replacement backup already exists: {backup}")
            atomic_install(plan.input_path, backup)
            try:
                atomic_install(temp, plan.output_path)
            except Exception:
                atomic_install(backup, plan.input_path)
                raise
        else:
            atomic_install(temp, plan.output_path)
        return plan.output_path
    finally:
        if temp.exists():
            temp.unlink(missing_ok=True)
