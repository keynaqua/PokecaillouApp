from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from config import (
    INSTALLATIONS_DIR_NAME,
    MODS_DIR_NAME,
    RESOURCEPACKS_DIR_NAME,
    SHADERPACKS_DIR_NAME,
    SHORT_HTTP_RETRIES,
    SHORT_HTTP_TIMEOUT,
    get_installation_dir,
    get_launcher_profiles_path,
    get_minecraft_dir,
    get_modpack_manifest_url,
    get_modpack_resourcepacks_url,
    get_modpack_shaderpacks_url,
)
from logger import info, progress, success
from modpack import ModpackInfo, load_modpack_info
from utils.http import DownloadError, get_json


class UninstallMode(str, Enum):
    CLASSIC = "classic"
    FULL = "full"


@dataclass(frozen=True)
class ManifestFile:
    file_name: str


def _required_file_name(entry: dict, label: str) -> str:
    value = entry.get("file_name")
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"{label}: champ 'file_name' invalide")
    return value.strip()


def _load_named_files(url: str, section: str, *fallback_sections: str) -> list[ManifestFile]:
    data = get_json(url, timeout=SHORT_HTTP_TIMEOUT, retries=SHORT_HTTP_RETRIES)
    if not isinstance(data, dict):
        raise RuntimeError(f"Le manifest {section} doit etre un objet JSON")

    raw_items = data.get(section)
    selected_section = section
    for fallback in fallback_sections:
        if isinstance(raw_items, list):
            break
        raw_items = data.get(fallback)
        selected_section = fallback

    if not isinstance(raw_items, list):
        sections = "', '".join((section, *fallback_sections))
        raise RuntimeError(f"Le manifest doit contenir une liste '{sections}'")

    files: list[ManifestFile] = []
    for index, entry in enumerate(raw_items, start=1):
        if not isinstance(entry, dict):
            raise RuntimeError(f"{selected_section}[{index}] doit etre un objet")
        files.append(ManifestFile(_required_file_name(entry, f"{selected_section}[{index}]")))
    return files


def _load_mod_files(modpack_key: str) -> list[ManifestFile]:
    return _load_named_files(get_modpack_manifest_url(modpack_key), "mods")


def _load_optional_named_files(url: str, section: str, *fallback_sections: str) -> list[ManifestFile]:
    try:
        return _load_named_files(url, section, *fallback_sections)
    except DownloadError as exc:
        text = str(exc)
        if "404" in text or "Expecting value" in text:
            return []
        raise


def _safe_child(base: Path, file_name: str) -> Path:
    target = (base / file_name).resolve()
    base_resolved = base.resolve()
    try:
        target.relative_to(base_resolved)
    except ValueError as exc:
        raise RuntimeError(f"Chemin manifest hors dossier autorise: {file_name}") from exc
    return target


def _remove_manifest_files(base: Path, files: list[ManifestFile], label: str) -> int:
    removed = 0
    if not base.exists():
        info(f"{label}: dossier absent, rien a supprimer.")
        return removed

    for item in files:
        target = _safe_child(base, item.file_name)
        if not target.exists():
            continue
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        removed += 1
        info(f"{label}: supprime {item.file_name}")

    success(f"{label}: {removed} fichier(s) supprime(s).")
    return removed


def _installation_path(modpack_info: ModpackInfo) -> Path:
    root = get_installation_dir(modpack_info.installation_dir).resolve()
    installations_root = (get_minecraft_dir() / INSTALLATIONS_DIR_NAME).resolve()
    try:
        root.relative_to(installations_root)
    except ValueError as exc:
        raise RuntimeError(f"Dossier d'installation invalide: {root}") from exc
    return root


def _remove_launcher_profile(profile_name: str) -> None:
    launcher_file = get_launcher_profiles_path()
    if not launcher_file.exists():
        return

    data = json.loads(launcher_file.read_text(encoding="utf-8"))
    profiles = data.get("profiles")
    if not isinstance(profiles, dict) or profile_name not in profiles:
        return

    del profiles[profile_name]
    launcher_file.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")
    info(f"Profil launcher supprime: {profile_name}")


def _classic_uninstall(modpack_info: ModpackInfo) -> None:
    game_dir = _installation_path(modpack_info)
    if not game_dir.exists():
        info(f"Dossier absent: {game_dir}")
        return

    progress(25)
    info("Chargement des manifests du modpack...")
    mod_files = _load_mod_files(modpack_info.key)
    resourcepacks = _load_optional_named_files(get_modpack_resourcepacks_url(modpack_info.key), "packs")
    shaderpacks = _load_optional_named_files(
        get_modpack_shaderpacks_url(modpack_info.key),
        "packs",
        "shaders",
    )

    progress(45)
    _remove_manifest_files(game_dir / MODS_DIR_NAME, mod_files, "Mods")

    progress(65)
    _remove_manifest_files(game_dir / RESOURCEPACKS_DIR_NAME, resourcepacks, "Resourcepacks")

    progress(85)
    _remove_manifest_files(game_dir / SHADERPACKS_DIR_NAME, shaderpacks, "Shaderpacks")

    success("Desinstallation classique terminee. Saves, options et configs conservees.")


def _full_uninstall(modpack_info: ModpackInfo) -> None:
    game_dir = _installation_path(modpack_info)
    if game_dir.exists():
        shutil.rmtree(game_dir)
        success(f"Dossier du modpack supprime: {game_dir}")
    else:
        info(f"Dossier deja absent: {game_dir}")

    _remove_launcher_profile(modpack_info.name)
    success("Desinstallation complete terminee.")


def uninstall_modpack(modpack_name: str, mode: UninstallMode | str) -> None:
    selected_mode = UninstallMode(mode)
    progress(5)
    info(f"Recuperation de modpack.json pour {modpack_name}...")
    info_data = load_modpack_info(modpack_name)

    progress(15)
    if selected_mode == UninstallMode.CLASSIC:
        _classic_uninstall(info_data)
    elif selected_mode == UninstallMode.FULL:
        _full_uninstall(info_data)

    progress(100)
