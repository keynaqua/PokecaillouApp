from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .models import CompareResult, DesiredMod, DetectionReport, InstalledMod, ModAction


class DuplicateModError(RuntimeError):
    pass


def _index_mods(mods: list[InstalledMod]) -> dict[str, list[InstalledMod]]:
    index: dict[str, list[InstalledMod]] = {}
    for mod in mods:
        index.setdefault(mod.mod_id, []).append(mod)
    return index


def compare_mods(
    detected: DetectionReport,
    desired_mods: Iterable[DesiredMod],
    mods_dir: str | Path,
) -> CompareResult:
    mods_path = Path(mods_dir)
    installed = _index_mods(detected.mods)
    result = CompareResult()
    used_files: set[Path] = set()

    for desired in desired_mods:
        matches = installed.get(desired.mod_id, [])

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

        if len(matches) > 1:
            names = ", ".join(sorted(mod.file_path.name for mod in matches))
            raise DuplicateModError(f"Multiple JARs found for '{desired.mod_id}': {names}")

        current = matches[0]
        used_files.add(current.file_path)

        if current.version == desired.version:
            result.up_to_date.append(current)
            continue

        result.actions.append(
            ModAction(
                kind="update",
                mod_id=desired.mod_id,
                from_version=current.version,
                to_version=desired.version,
                download_url=desired.download_url,
                target_file=mods_path / (desired.file_name or f"{desired.mod_id}-{desired.version}.jar"),
                remove_files=[current.file_path],
            )
        )

    for mod in detected.mods:
        if mod.file_path not in used_files:
            result.extra_mods.append(mod)

    return result
