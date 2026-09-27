from __future__ import annotations

import time
from collections import deque

try:
    from rich.console import Console
    from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn, TimeRemainingColumn
except ImportError:  # pragma: no cover - exercised when the optional UI dependency is absent
    Console = None  # type: ignore[assignment,misc]
    Progress = None  # type: ignore[assignment,misc]


class Eta:
    def __init__(self) -> None:
        self.samples: deque[float] = deque(maxlen=5)
        self.started = time.monotonic()

    def add(self, seconds: float) -> None:
        self.samples.append(seconds)

    def estimate(self, remaining: int) -> str:
        if not self.samples:
            return "Calculating..."
        rate = sum(self.samples) / len(self.samples)
        total = max(0, round(rate * remaining))
        return f"~{total // 60:02d}:{total % 60:02d}"


class BatchProgress:
    """Persistent Rich progress with a readable plain-text fallback."""

    def __init__(self, total: int) -> None:
        self.total = total
        self.completed = 0
        self.current = ""
        self._eta = Eta()
        self._started = time.monotonic()
        self._rich = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
        ) if Progress else None
        self._task = None

    def __enter__(self) -> "BatchProgress":
        if self._rich:
            self._rich.start()
            self._task = self._rich.add_task("Processing media", total=self.total)
        else:
            print(f"Processing media: 0 / {self.total} | ETA: Calculating... | Originals: SAFE")
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self._rich:
            self._rich.stop()

    def set_current(self, name: str, status: str = "working") -> None:
        self.current = name
        if self._rich and self._task is not None:
            self._rich.update(self._task, description=f"{status}: {name}")
        else:
            print(f"[PROCESS] {name} — {status} | Originals: SAFE")

    def file_progress(self, fraction: float) -> None:
        if self._rich and self._task is not None:
            self._rich.update(self._task, refresh=True)

    def complete(self, success: bool) -> None:
        elapsed = max(0.001, time.monotonic() - self._started)
        self._eta.add(elapsed)
        self.completed += 1
        if self._rich and self._task is not None:
            self._rich.advance(self._task)
        else:
            print(f"[{'OK' if success else 'ERROR'}] {self.current} | {self.completed}/{self.total} | ETA: {self._eta.estimate(self.total - self.completed)} | Originals: SAFE")
