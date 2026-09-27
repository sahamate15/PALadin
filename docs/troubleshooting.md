# Troubleshooting

## FFmpeg was not found

Install FFmpeg and confirm both commands work:

```text
ffmpeg -version
ffprobe -version
```

## PALadin says the file is ambiguous

25 fps alone cannot prove PAL speedup. Review the generated test clip and
approve only if pitch, timing, subtitles, and audio continuity are correct.

## A subtitle format is rejected

PALadin fails closed when it cannot guarantee subtitle timestamp correctness.
The original remains untouched. Use a separately validated subtitle conversion
workflow rather than accepting potentially mis-timed subtitles.

## An output already exists

Use an interactive policy or select one explicitly:

```text
paladin input.mkv --existing skip
paladin input.mkv --existing new
```

## A run is interrupted

PALadin attempts to terminate FFmpeg and removes its own temporary output. The
source remains protected unless the user explicitly enabled `--replace` and a
validated replacement had already completed.
