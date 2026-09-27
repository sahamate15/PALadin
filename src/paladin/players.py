from __future__ import annotations

import platform
import shutil
import subprocess
from pathlib import Path


def find_player() -> tuple[str, list[str]] | None:
    candidates = ["vlc", "iina", "mpv"]
    for name in candidates:
        path = shutil.which(name)
        if path:
            return name, [path]
    if platform.system() == "Darwin":
        return "default macOS player", ["open"]
    if platform.system() == "Linux" and shutil.which("xdg-open"):
        return "default Linux player", ["xdg-open"]
    if platform.system() == "Windows":
        return "default Windows player", ["cmd", "/c", "start", ""]
    return None


def launch(path: Path) -> tuple[str, subprocess.Popen[bytes]] | None:
    found = find_player()
    if not found:
        return None
    name, command = found
    process = subprocess.Popen(command + [str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return name, process
