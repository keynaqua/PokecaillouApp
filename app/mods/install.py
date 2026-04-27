from __future__ import annotations

from pathlib import Path
from urllib.request import urlopen

from logger import info
from .models import CompareResult


def _download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(url) as response, target.open("wb") as file:
        file.write(response.read())


def apply_actions(result: CompareResult) -> None:
    for action in result.actions:
        for old_file in action.remove_files:
            if old_file.exists():
                info(f" - [MODS] Remove: {old_file.name}")
                old_file.unlink()

        if action.download_url and action.target_file:
            if action.kind == "install":
                info(f" - [MODS] Install: {action.mod_id} -> {action.target_file.name}")
            else:
                info(
                    f" - [MODS] Download: {action.mod_id} "
                    f"{action.from_version or 'unknown'} -> {action.to_version}"
                )
            _download(action.download_url, action.target_file)
