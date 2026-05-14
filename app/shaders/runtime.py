from __future__ import annotations

import ctypes
import hashlib
from dataclasses import dataclass
from pathlib import Path

from config import (
    GUI_SHADER_MESSAGEBOX_FLAGS,
    HASH_CHUNK_SIZE,
    SHADERPACKS_DIR_NAME,
    SHADERPACK_SUFFIXES,
    SHORT_HTTP_RETRIES,
    SHORT_HTTP_TIMEOUT,
    get_modpack_shaderpacks_url,
)
from logger import shader, success
from utils.http import DownloadError, download_file, get_json


@dataclass
class ShaderPack:
    file_name: str
    download_url: str
    sha256: str


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as file:
        while chunk := file.read(HASH_CHUNK_SIZE):
            h.update(chunk)
    return h.hexdigest()


def _required_string(entry: dict, field: str, label: str) -> str:
    value = entry.get(field)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"{label}: champ '{field}' invalide")
    return value.strip()


def _load_manifest(modpack_key: str) -> list[ShaderPack]:
    try:
        data = get_json(
            get_modpack_shaderpacks_url(modpack_key),
            timeout=SHORT_HTTP_TIMEOUT,
            retries=SHORT_HTTP_RETRIES,
        )
    except DownloadError as exc:
        text = str(exc)
        if "404" in text or "Expecting value" in text:
            shader("Aucun manifest shaderpacks exploitable.")
            return []
        raise

    if not isinstance(data, dict):
        raise RuntimeError("Le manifest shaderpacks doit etre un objet JSON")

    raw_packs = data.get("packs", data.get("shaders", []))
    if not isinstance(raw_packs, list):
        raise RuntimeError("Le manifest shaderpacks doit contenir une liste 'packs'")

    packs: list[ShaderPack] = []
    for index, entry in enumerate(raw_packs, start=1):
        if not isinstance(entry, dict):
            raise RuntimeError(f"packs[{index}] doit etre un objet")
        label = f"packs[{index}]"
        packs.append(
            ShaderPack(
                file_name=_required_string(entry, "file_name", label),
                download_url=_required_string(entry, "download_url", label),
                sha256=_required_string(entry, "sha256", label).lower(),
            )
        )
    return packs


def _local_shaderpacks(shaderpacks_dir: Path) -> dict[str, Path]:
    shaderpacks_dir.mkdir(parents=True, exist_ok=True)
    return {
        path.name.lower(): path
        for path in shaderpacks_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SHADERPACK_SUFFIXES
    }


def _ask_install_defaults() -> bool:
    result = ctypes.windll.user32.MessageBoxW(
        None,
        "Des shaders sont deja presents.\n\n"
        "Installer les shaders par defaut du modpack a cote de ceux deja presents ?",
        "KayouInstaller - Shaders",
        GUI_SHADER_MESSAGEBOX_FLAGS,
    )
    return result == 6


def ensure_shaders_installed(game_dir: str | Path, modpack_key: str) -> None:
    game_path = Path(game_dir)
    shaderpacks_dir = game_path / SHADERPACKS_DIR_NAME

    shader("Chargement du manifest shaderpacks...")
    packs = _load_manifest(modpack_key)
    if not packs:
        success("Configuration des shaderpacks terminee !")
        return

    local = _local_shaderpacks(shaderpacks_dir)
    wanted_names = {pack.file_name.lower() for pack in packs}
    missing_defaults = [pack for pack in packs if pack.file_name.lower() not in local]
    other_shaders = [path for name, path in local.items() if name not in wanted_names]

    if missing_defaults and other_shaders and not _ask_install_defaults():
        shader("Shaders par defaut ignores.")
        success("Configuration des shaderpacks terminee !")
        return

    for pack in packs:
        target = shaderpacks_dir / pack.file_name

        if target.exists() and _sha256(target) == pack.sha256:
            shader(f"OK {pack.file_name}")
            continue

        if target.exists():
            shader(f"Update {pack.file_name}")
            target.unlink()
        else:
            shader(f"Install {pack.file_name}")

        download_file(pack.download_url, target)

    success("Configuration des shaderpacks terminee !")
