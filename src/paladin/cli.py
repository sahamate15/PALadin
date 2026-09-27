from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import shutil
import sys
from pathlib import Path

from . import AUTHOR, RELEASE_DATE, __version__
from .detection import detect
from .discovery import discover
from .errors import DependencyError, PaladinError
from .models import CorrectionPlan, MediaInfo
from .players import launch
from .processing import make_plan, process
from .probing import probe
from .progress import BatchProgress
from .safety import default_output, stale_temp_files


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="paladin", description="Correct PAL-speedup-style MKV media safely.")
    p.add_argument("inputs", nargs="+", type=Path)
    p.add_argument("--recursive", action="store_true", help="Search directories recursively.")
    p.add_argument("--output", type=Path, help="Output path for a single input file.")
    p.add_argument("--test-duration", type=int, default=20, help="Preview duration in seconds (default: 20).")
    p.add_argument("--audio-track", type=int, action="append", default=[], help="Audio stream index to correct; repeatable.")
    p.add_argument("--jobs", default="auto", help="Concurrent files; auto is conservative sequential mode.")
    p.add_argument("--existing", choices=("ask", "skip", "new", "abort"), default="ask", help="Policy for existing outputs.")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--replace", action="store_true", help="Safely replace sources after validation; keeps a backup.")
    p.add_argument("--yes", action="store_true", help="Approve without interactive preview.")
    p.add_argument("--no-player", action="store_true", help="Do not launch a media player for the preview.")
    p.add_argument("--keep-test", action="store_true", help="Keep the preview file for troubleshooting.")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--debug", action="store_true")
    p.add_argument("--version", action="version", version=f"PALadin {__version__} ({RELEASE_DATE}) by {AUTHOR}")
    return p


def _new_output(path: Path) -> Path:
    number = 2
    while True:
        candidate = path.with_name(f"{path.stem}-{number}{path.suffix}")
        if not candidate.exists():
            return candidate
        number += 1


def _existing_policy(args: argparse.Namespace, collisions: list[Path]) -> str:
    if not collisions:
        return "skip"
    if args.existing != "ask":
        return args.existing
    print("\n[WARNING] Existing outputs were found:")
    for path in collisions:
        print(f"  {path}")
    print("[INPUT] Choose: [S]kip all, [N]ew output names, or [A]bort.")
    answer = input("[INPUT] Existing-output policy [S/N/A]: ").strip().lower()
    return {"s": "skip", "n": "new", "a": "abort"}.get(answer, "abort")


def _show_analysis(path: Path, media: MediaInfo) -> None:
    detection = detect(media)
    print(f"[ANALYZE] {path.name}")
    print(f"[INFO] Video: {detection.source_rate or 'unknown'} fps")
    print(f"[INFO] Audio tracks: {len(media.audio)} | Subtitles: {len(media.subtitles)} | Attachments: {media.attachments}")
    print(f"[INFO] Detection: {detection.status} ({detection.confidence}) — {detection.reason}")


def _review_test(plan: CorrectionPlan, media: MediaInfo, args: argparse.Namespace) -> None:
    test_path = plan.output_path.with_name(f".{plan.output_path.stem}.paladin-test.mkv")
    test_plan = CorrectionPlan(plan.input_path, test_path, plan.selected_audio, plan.copied_audio, plan.subtitle_assessments, plan.detection, True)
    try:
        process(test_plan, media, duration=args.test_duration, debug=args.debug)
        print(f"[TEST] Created: {test_path}")
        launched = None if args.no_player else launch(test_path)
        if launched:
            print(f"[TEST] Opened in {launched[0]}.")
        else:
            print("[INFO] No player was detected; open the test manually.")
        print("[WAITING] Check pitch, audio/video sync, subtitles, and gaps/mutes.")
        input("[INPUT] Close the player when finished, then press Enter: ")
        if input("[INPUT] Type Y only to approve full processing: ").strip().lower() not in {"y", "yes"}:
            raise PaladinError("Test declined. No original files were modified.")
    finally:
        if not args.keep_test:
            test_path.unlink(missing_ok=True)
        else:
            print(f"[INFO] Keeping test clip: {test_path}")


def _resolve_jobs(value: str, count: int) -> int:
    if value == "auto":
        return 1
    try:
        jobs = int(value)
    except ValueError as exc:
        raise PaladinError("--jobs must be a positive integer or auto.") from exc
    if jobs < 1:
        raise PaladinError("--jobs must be at least 1.")
    return min(jobs, count, max(1, os.cpu_count() or 1))


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    print(f"PALadin v{__version__}\nby {AUTHOR}\nReleased {RELEASE_DATE}\n")
    try:
        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            raise DependencyError("FFmpeg and ffprobe are required and must be available on PATH.")
        files = discover(args.inputs, args.recursive)
        if not files:
            raise PaladinError("No MKV files were found in the supplied inputs.")
        if args.output and len(files) != 1:
            raise PaladinError("--output requires exactly one input file.")
        stale = stale_temp_files(files[0].parent)
        if stale:
            print(f"[WARNING] Found {len(stale)} stale PALadin temporary file(s); they were not removed automatically.")

        analyzed: list[tuple[MediaInfo, CorrectionPlan]] = []
        for path in files:
            media = probe(path, debug=args.debug)
            _show_analysis(path, media)
            if detect(media).status != "candidate":
                print(f"[SKIP] {path.name}\n")
                continue
            output = path if args.replace else (args.output or default_output(path))
            try:
                plan = make_plan(media, output, tuple(args.audio_track))
            except PaladinError as exc:
                print(f"[ERROR] {path.name}: {exc}\n[SAFE] Original was not modified.")
                continue
            analyzed.append((media, plan))

        collisions = [plan.output_path for _, plan in analyzed if plan.output_path.exists() and not args.replace]
        policy = _existing_policy(args, collisions)
        if policy == "abort":
            print("[STOP] Existing-output decision aborted the run. Originals remain safe.")
            return 2
        if policy == "skip":
            analyzed = [(media, plan) for media, plan in analyzed if not plan.output_path.exists()]
        elif policy == "new":
            analyzed = [(media, CorrectionPlan(plan.input_path, _new_output(plan.output_path), plan.selected_audio, plan.copied_audio, plan.subtitle_assessments, plan.detection, plan.test)) if plan.output_path.exists() else (media, plan) for media, plan in analyzed]

        if args.dry_run:
            print(f"[DRY-RUN] {len(analyzed)} file(s) would be processed.")
            print("[SAFE] No files were created or modified.")
            return 0
        if not analyzed:
            print("[INFO] Nothing to process.")
            return 0
        if args.replace and not args.yes:
            if input("[WARNING] Type YES to enable source replacement: ").strip() != "YES":
                print("[STOP] Replacement not enabled. Originals remain safe.")
                return 2
        if not args.yes:
            _review_test(analyzed[0][1], analyzed[0][0], args)

        completed = failed = 0
        jobs = _resolve_jobs(args.jobs, len(analyzed))
        print(f"[INFO] Concurrency: {jobs} job(s). Originals: SAFE")

        def run_one(item: tuple[MediaInfo, CorrectionPlan]) -> tuple[MediaInfo, CorrectionPlan, Exception | None]:
            media, plan = item
            try:
                process(plan, media, debug=args.debug, replace=args.replace)
                return media, plan, None
            except Exception as exc:  # surfaced as a per-file result below
                return media, plan, exc

        with BatchProgress(len(analyzed)) as progress:
            if jobs == 1:
                results = (run_one(item) for item in analyzed)
                for media, plan, error in results:
                    progress.set_current(media.path.name, "processing")
                    if error is None:
                        print(f"[OK] {media.path.name} complete.\n[SAFE] Original {'backed up and replaced' if args.replace else 'preserved'}.\n[OUTPUT] {plan.output_path}")
                        completed += 1
                        progress.complete(True)
                    else:
                        if isinstance(error, KeyboardInterrupt):
                            raise error
                        print(f"[ERROR] {media.path.name}: {error}\n[SAFE] Original was not modified.")
                        failed += 1
                        progress.complete(False)
            else:
                with ThreadPoolExecutor(max_workers=jobs, thread_name_prefix="paladin") as executor:
                    futures = [executor.submit(run_one, item) for item in analyzed]
                    for future in as_completed(futures):
                        media, plan, error = future.result()
                        progress.set_current(media.path.name, "processing")
                        if error is None:
                            print(f"[OK] {media.path.name} complete.\n[SAFE] Original {'backed up and replaced' if args.replace else 'preserved'}.\n[OUTPUT] {plan.output_path}")
                            completed += 1
                            progress.complete(True)
                        else:
                            print(f"[ERROR] {media.path.name}: {error}\n[SAFE] Original was not modified.")
                            failed += 1
                            progress.complete(False)
        print(f"\nPALadin COMPLETE\n{len(files)} files discovered\n{completed} successfully processed\n{failed} failed\nPALadin by {AUTHOR}")
        return 1 if failed else 0
    except KeyboardInterrupt:
        print("\n[INTERRUPTED]\nPALadin stopped by user.\n[SAFE] Original media has not been replaced.\n[CLEANUP] PALadin temporary files were cleaned where possible.")
        return 130
    except PaladinError as exc:
        print(f"[ERROR] {exc}\n[SAFE] Original media remains untouched.", file=sys.stderr)
        return 2
