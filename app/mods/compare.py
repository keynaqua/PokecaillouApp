from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from .models import CompareResult, DesiredMod, DetectionReport, InstalledMod, ModAction


def _index_mods(mods: list[InstalledMod]) -> dict[str, list[InstalledMod]]:
    index: dict[str, list[InstalledMod]] = {}
    for mod in mods:
        index.setdefault(mod.mod_id, []).append(mod)
    return index


def _version_key(version: str) -> tuple:
    parts: list[tuple[int, int | str]] = []

    for token in re.findall(r"\d+|[A-Za-z]+", version):
        if token.isdigit():
            parts.append((0, int(token)))
        else:
            parts.append((1, token.lower()))

    return tuple(parts)


def _sort_matches(matches: list[InstalledMod]) -> list[InstalledMod]:
    return sorted(matches, key=lambda mod: (_version_key(mod.version), mod.file_path.name))


def compare_mods(detected: DetectionReport, desired_mods: Iterable[DesiredMod], mods_dir: str | Path) -> CompareResult:
    mods_path = Path(mods_dir)
    installed = _index_mods(detected.mods)
    result = CompareResult()
    used_files: set[Path] = set()

    for desired in desired_mods:
        matches = _sort_matches(installed.get(desired.mod_id, []))

        if not matches:
            result.actions.append(
                ModAction(
                    kind="install",
                    mod_id=desired.mod_id,
                    from_version=None,
                    to_version=desired.version,
                    download_url=desired.download_url,
                    target_file=mods_path / (desired.file_name or f"{desired.mod_id}-{desired.version}.jar"),
                )
            )
            continue

        matching_version = [mod for mod in matches if mod.version == desired.version]
        duplicates_to_remove: list[Path] = []

        if matching_version:
            current = matching_version[-1]
            duplicates_to_remove = [
                mod.file_path for mod in matches if mod.file_path != current.file_path
            ]
            used_files.add(current.file_path)
            result.up_to_date.append(current)

            if duplicates_to_remove:
                result.actions.append(
                    ModAction(
                        kind="cleanup",
                        mod_id=desired.mod_id,
                        from_version=current.version,
                        to_version=desired.version,
                        remove_files=duplicates_to_remove,
                    )
                )

            continue

        current = matches[-1]
        remove_files = [mod.file_path for mod in matches]

        result.actions.append(
            ModAction(
                kind="update",
                mod_id=desired.mod_id,
                from_version=current.version,
                to_version=desired.version,
                download_url=desired.download_url,
                target_file=mods_path / (desired.file_name or f"{desired.mod_id}-{desired.version}.jar"),
                remove_files=remove_files,
            )
        )

    planned_removals = {
        file_path
        for action in result.actions
        for file_path in action.remove_files
    }

    for mod in detected.mods:
        if mod.file_path not in used_files and mod.file_path not in planned_removals:
            result.extra_mods.append(mod)

    return result
