from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from config import (
    get_modpack_manifest_url,
)
from logger import error, extra, info, missing, mods, outdated, success, uptodate
from utils.http import download_file, get_json
from utils.progress import ProgressCallback, RangedProgress

from .detect import DetectionReport, InstalledMod, detect_mods, ensure_sha1

MOD_PROGRESS_START = 30
MOD_PROGRESS_END = 70


@dataclass
class ManifestMod:
    mod_id: str
    version: str
    download_url: str
    file_name: str
    sha1: str


def _ensure_windows_10_or_11() -> None:
    if sys.platform != "win32":
        raise RuntimeError("KayouInstaller ne supporte que Windows.")


def _required_string(entry: dict, field: str, label: str) -> str:
    value = entry.get(field)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"{label}: champ '{field}' invalide")
    return value.strip()


def _load_manifest(modpack_key: str) -> tuple[list[ManifestMod], set[str], set[str]]:
    data = get_json(get_modpack_manifest_url(modpack_key))
    if not isinstance(data, dict):
        raise RuntimeError("Le manifest des mods doit etre un objet JSON")

    raw_mods = data.get("mods")
    if not isinstance(raw_mods, list):
        raise RuntimeError("Le manifest doit contenir une liste 'mods'")

    manifest_mods: list[ManifestMod] = []
    for index, entry in enumerate(raw_mods, start=1):
        if not isinstance(entry, dict):
            raise RuntimeError(f"mods[{index}] doit etre un objet")
        label = f"mods[{index}]"
        manifest_mods.append(
            ManifestMod(
                mod_id=_required_string(entry, "id", label),
                version=_required_string(entry, "version", label),
                download_url=_required_string(entry, "download_url", label),
                file_name=_required_string(entry, "file_name", label),
                sha1=_required_string(entry, "sha1", label).lower(),
            )
        )

    return (
        manifest_mods,
        _load_rule_ids(data, "blacklist"),
        _load_rule_ids(data, "safe_mode"),
    )


def _load_rule_ids(data: dict, section: str) -> set[str]:
    raw_rules = data.get(section, [])
    if not isinstance(raw_rules, list):
        raise RuntimeError(f"'{section}' doit etre une liste")

    ids: set[str] = set()
    for index, entry in enumerate(raw_rules, start=1):
        if isinstance(entry, str) and entry.strip():
            ids.add(entry.strip())
            continue
        if isinstance(entry, dict):
            ids.add(_required_string(entry, "id", f"{section}[{index}]"))
            continue
        raise RuntimeError(f"{section}[{index}] doit etre une chaine ou un objet")
    return ids


def _remove_mod_ids(mods_dir: Path, mod_ids: set[str], label: str) -> None:
    if not mod_ids:
        return

    removed = 0
    for mod in detect_mods(mods_dir).mods:
        if mod.mod_id not in mod_ids:
            continue
        if mod.file_path.exists():
            info(f" - [MODS] Remove {label}: {mod.file_path.name}")
            mod.file_path.unlink()
            removed += 1

    if removed:
        success(f"{label}: {removed} mod(s) supprime(s)")


def _report_broken_files(report: DetectionReport) -> None:
    if not report.broken_files:
        return
    error("Fichiers .jar invalides detectes:")
    for file_path, reason in report.broken_files:
        extra(f"{file_path.name}: {reason}")


def _index_by_mod_id(mods_list: list[InstalledMod]) -> dict[str, list[InstalledMod]]:
    index: dict[str, list[InstalledMod]] = {}
    for mod in mods_list:
        index.setdefault(mod.mod_id, []).append(mod)
    return index


def _sync_manifest_mods(
    mods_dir: Path,
    desired_mods: list[ManifestMod],
    progress_callback: ProgressCallback | None = None,
    progress_start: int = MOD_PROGRESS_START,
    progress_end: int = MOD_PROGRESS_END,
) -> None:
    installed = _index_by_mod_id(detect_mods(mods_dir).mods)
    ranged_progress = RangedProgress(progress_callback, progress_start, progress_end, len(desired_mods))

    for desired in desired_mods:
        matches = installed.get(desired.mod_id, [])
        up_to_date = next(
            (
                mod
                for mod in matches
                if mod.version == desired.version and ensure_sha1(mod) == desired.sha1
            ),
            None,
        )

        if up_to_date:
            uptodate(f"{desired.mod_id} ({desired.version})")
            for duplicate in matches:
                if duplicate.file_path != up_to_date.file_path and duplicate.file_path.exists():
                    info(f" - [MODS] Remove duplicate: {duplicate.file_path.name}")
                    duplicate.file_path.unlink()
            ranged_progress.advance()
            continue

        for old_mod in matches:
            if old_mod.file_path.exists():
                outdated(f"UPDATE {desired.mod_id}: {old_mod.version} -> {desired.version}")
                old_mod.file_path.unlink()

        if not matches:
            missing(f"INSTALL {desired.mod_id} -> {desired.version}")

        download_file(desired.download_url, mods_dir / desired.file_name)
        ranged_progress.advance()

    ranged_progress.finish()


def update_mods(
    mods_dir: str | Path,
    modpack_key: str,
    safe_mode: bool = False,
    progress_callback: ProgressCallback | None = None,
) -> None:
    _ensure_windows_10_or_11()

    mods_path = Path(mods_dir)
    mods_path.mkdir(parents=True, exist_ok=True)

    mods("Chargement du manifest des mods...")
    manifest_mods, blacklist_ids, safe_mode_ids = _load_manifest(modpack_key)

    mods("Suppression des mods blacklistes...")
    _remove_mod_ids(mods_path, blacklist_ids, "blacklist")

    safe_mode_enabled = safe_mode and bool(safe_mode_ids)
    if safe_mode_enabled:
        mods("Application du safe mode...")
        _remove_mod_ids(mods_path, safe_mode_ids, "safe mode")

    excluded_ids = safe_mode_ids if safe_mode_enabled else set()
    wanted = [mod for mod in manifest_mods if mod.mod_id not in excluded_ids]

    report = detect_mods(mods_path)
    _report_broken_files(report)

    mods("Synchronisation des mods du manifest...")
    _sync_manifest_mods(mods_path, wanted, progress_callback=progress_callback)

    success("Mods synchronises avec succes !")
