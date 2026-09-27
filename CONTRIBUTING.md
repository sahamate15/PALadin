# Contributing to PALadin

PALadin is maintained by Shubham Sahamate.

Before opening a pull request:

```text
python -m pip install -e ".[dev]"
ruff check src tests
python -m pytest -q
```

Media fixtures must be synthetic or freely redistributable. Do not add
copyrighted episodes, films, or personal media to the repository.

Changes to the FFmpeg command architecture should include an integration test
covering video, audio, subtitles, and output stream preservation.
