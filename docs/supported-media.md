# Supported media

PALadin currently targets MKV files with a stable 25/1 video stream and one or
more audio streams. It is deliberately conservative about variable frame
rates, broken timestamps, unusual time bases, and subtitle formats.

The default audio policy corrects every audio stream. Explicit
`--audio-track` options correct only the selected streams and copy unselected
streams unchanged.

Subtitle preservation is fail-closed. Safe-copy support is limited to formats
validated by the current FFmpeg/MKV integration tests. Unknown or unsafe
subtitle formats are rejected rather than silently dropped.
