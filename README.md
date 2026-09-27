# PALadin

## PALadin by Shubham Sahamate

PALadin is a test-first command-line utility for correcting MKV files that
may have been accelerated from 23.976 fps-style material to 25 fps, causing
voices and music to sound slightly too high-pitched.

PALadin uses FFmpeg to correct the timeline toward the exact target rate
`24000/1001` and naturally lowers audio pitch while slowing it. It does not
claim that every 25 fps file is PAL speedup: native 25 fps productions exist,
so the test clip is an important human validation step.

## Safety model

The default is non-destructive:

```text
episode.mkv -> episode.fixed.mkv
```

Original media is not overwritten. PALadin writes temporary output, checks that
FFmpeg succeeded, and installs the final output only after validation. Existing
outputs are skipped by default. `--replace` is opt-in.

## Requirements and installation

- Python 3.10 or newer
- FFmpeg and ffprobe available on `PATH`

macOS: `brew install ffmpeg`
Debian/Ubuntu: `sudo apt install ffmpeg`
Windows: install a trusted FFmpeg distribution and add its `bin` directory to `PATH`.

For the initial GitHub release, install from the repository:

```text
git clone <repository-url>
cd PALadin
python -m pip install .
```

Or:

```text
pipx install .
```

Development install:

```text
python -m pip install -e ".[dev]"
```

PyPI publication is optional and future-facing; do not assume `pipx install
paladin` works until PALadin is published there.

## Usage

```text
paladin episode.mkv
paladin ./Season3
paladin ./Season3 --recursive
```

PALadin analyzes the files, creates a 20-second preview, opens it in an
available player when possible, waits for review, and accepts only `y` or
`yes` as approval.

Useful options include `--test-duration`, `--dry-run`, `--jobs auto`,
`--audio-track`, `--no-player`, `--verbose`, `--debug`, and `--version`.

PALadin shows persistent batch progress when Rich is installed, including
completed files, current status, elapsed time, and an approximate ETA. Explicit
`--jobs N` enables conservative process-level parallelism; `--jobs auto`
defaults to sequential processing for maximum predictability.

If an output already exists, PALadin asks once for a batch policy: skip,
create new numbered outputs, or abort. Use `--existing skip|new|abort` for
non-interactive runs. `--replace` is separate: it replaces source files only
after validation and keeps a `.paladin-backup` beside the original.

With no `--audio-track`, all audio streams are corrected. When one or more
tracks are selected, those tracks are corrected and unselected tracks are
copied unchanged. PALadin reports this distinction before processing.

Subtitle handling is conservative: PALadin only claims preservation when the
subtitle codec is in its validated safe-copy set. Unsafe or unknown subtitle
timing fails closed rather than silently producing mis-timed subtitles.

## Technical correction

```text
target video rate:  24000/1001
video scale:        25025/24000
audio speed:        24000/25025
```

Video, audio, and subtitles use role-isolated FFmpeg input views. Video and
subtitle timestamps are scaled only in their respective mapped input views;
audio is read unscaled and corrected with an `asetrate`/`aresample` pipeline.

The mathematically transformed 48 kHz intermediate rate is approximately
46033.97 Hz (`48000 * 24000/25025`), represented by the nearest supported
integer sample rate where required by FFmpeg.

## Development

```text
python -m pytest -q
python -m pytest -q -m integration
```

The integration test generates synthetic media with FFmpeg. No copyrighted
media is stored in the repository.

## Limitations

Metadata cannot prove a file's historical source. Variable-frame-rate media,
broken timestamps, unusual subtitle formats, and unsupported stream layouts
may be rejected. FFmpeg builds and codecs can differ, so PALadin validates
outputs rather than promising universal preservation.

## License

Apache-2.0. See `LICENSE`.
