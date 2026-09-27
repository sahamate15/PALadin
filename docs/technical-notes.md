# PALadin technical notes

PALadin keeps exact correction ratios as Python `Fraction` values. FFmpeg
options are serialized only at the command boundary when an option requires a
decimal or integer.

The processing command intentionally uses three input views: a video-purpose
timestamp-scaled input mapped only for video, an unscaled audio-purpose input,
and an independently timestamp-scaled subtitle-purpose input. The synthetic
integration fixture verifies two audio tracks and subtitle preservation.

Subtitle support is fail-closed. A format is not called preserved unless its
timestamps have been validated in the target FFmpeg/MKV pipeline.

The default job policy is sequential. Explicit `--jobs N` uses independent
worker processes at the orchestration layer, while each FFmpeg process retains
its own codec/filter threading. This is intentionally conservative because
audio filtering/encoding and disk throughput, rather than video encoding, are
the likely bottlenecks.
