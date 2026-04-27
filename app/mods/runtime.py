from __future__ import annotations

import json
from pathlib import Path
from urllib.request import urlopen

from .models import DesiredMod
from .detect import detect_mods
from .compare import compare_mods
from .install import apply_actions
from logger import mods, uptodate, outdated, missing, extra, success

from .local_sync_sha import sync_remote_repo_mods

class ManifestError(RuntimeError):
    pass


def _load_json(url: str) -> dict:
    with urlopen(url) as response:
        data = json.loads(response.read().decode("utf-8"))
    if not isinstance(data, dict):
        raise ManifestError("Manifest must be a JSON object")
    return data


def _parse_mod(entry: dict, index: int) -> DesiredMod:
    mod_id = entry.get("id")
    version = entry.get("version")
    url = entry.get("download_url")
    file_name = entry.get("file_name")

    if not isinstance(mod_id, str) or not mod_id.strip():
        raise ManifestError(f"Mod #{index} has an invalid 'id'")
    if not isinstance(version, str) or not version.strip():
        raise ManifestError(f"Mod '{mod_id}' has an invalid 'version'")
    if not isinstance(url, str) or not url.strip():
        raise ManifestError(f"Mod '{mod_id}' has an invalid 'download_url'")
    if file_name is not None:
        if not isinstance(file_name, str) or not file_name.strip():
            raise ManifestError(f"Mod '{mod_id}' has an invalid 'file_name'")
        file_name = file_name.strip()

    return DesiredMod(
        mod_id=mod_id.strip(),
        version=version.strip(),
        download_url=url.strip(),
        file_name=file_name,
    )


def _load_manifest(url: str) -> list[DesiredMod]:
    data = _load_json(url)
    raw_mods = data.get("mods")

    if not isinstance(raw_mods, list):
        raise ManifestError("Manifest must contain a 'mods' list")

    mods: list[DesiredMod] = []
    for index, entry in enumerate(raw_mods, start=1):
        if not isinstance(entry, dict):
            raise ManifestError(f"Mod #{index} must be a JSON object")
        mods.append(_parse_mod(entry, index))
    return mods


def _print_report(result) -> None:
    if result.up_to_date:
        mods("Up to date:")
        for mod in result.up_to_date:
            uptodate(f"{mod.mod_id} ({mod.version})")

    if result.actions:
        mods("Planned actions:")
        for action in result.actions:
            if action.kind == "install":
                missing(f"INSTALL {action.mod_id} -> {action.to_version}")
            elif action.kind == "cleanup":
                outdated(
                    f"CLEANUP {action.mod_id}: remove {len(action.remove_files)} old file(s)"
                )
            else:
                outdated(f"UPDATE {action.mod_id}: {action.from_version} -> {action.to_version}")

    if result.extra_mods:
        mods("Extra mods kept:")
        for mod in result.extra_mods:
            extra(f"{mod.mod_id} ({mod.version}) [{mod.file_path.name}]")


def update_mods(mods_dir: str | Path, manifest_url: str, apply: bool = True):
    mods_path = Path(mods_dir)
    mods_path.mkdir(parents=True, exist_ok=True)

    mods(f"Load manifest: {manifest_url}")
    desired_mods = _load_manifest(manifest_url)

    mods(f"Scan mods: {mods_path}")
    detected = detect_mods(mods_path)
    # mods("Detected installed mods:")
    # for mod in detected.mods:
    #     print(f"  - id={mod.mod_id!r}, version={mod.version!r}, file={mod.file_path.name}")

    if detected.broken_files:
        mods("Ignored invalid files:")
        for file_path, reason in detected.broken_files:
            extra(f"{file_path.name}: {reason}")

    mods("Compare with manifest...")
    # mods("Desired mods from manifest:")
    # for mod in desired_mods:
    #     print(f"  - id={mod.mod_id!r}, version={mod.version!r}")
    result = compare_mods(detected, desired_mods, mods_path)
    _print_report(result)

    if not apply:
        mods("Dry-run mode, nothing applied.")
        return result

    mods("Apply changes...")
    apply_actions(result)

    sync_remote_repo_mods(mods_path)

    success("Mods synchronisés avec succes !")
    return result
