from pathlib import Path


def has_any_shader(shaders_dir) -> bool:
    path = Path(shaders_dir)

    if not path.exists():
        return False

    if not path.is_dir():
        raise NotADirectoryError(f"Invalid shaders directory: {path}")

    for file in path.iterdir():
        if file.is_file() and file.suffix.lower() in {".zip", ".jar"}:
            return True

    return False
