from pathlib import Path


def discover(inputs: list[Path], recursive: bool = False) -> list[Path]:
    result: list[Path] = []
    for item in inputs:
        if item.is_file():
            if item.suffix.lower() == ".mkv":
                result.append(item)
        elif item.is_dir():
            pattern = "**/*.mkv" if recursive else "*.mkv"
            result.extend(path for path in item.glob(pattern) if path.is_file())
    return sorted(set(path.resolve() for path in result))
