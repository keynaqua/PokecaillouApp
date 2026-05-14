from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from config import HASH_CHUNK_SIZE, RESOURCEPACKS_DIR_NAME, get_modpack_resourcepacks_url
from logger import success, txtp
from utils.http import download_file, get_json


@dataclass
class ResourcePack:
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


def _load_manifest(modpack_key: str) -> list[ResourcePack]:
    data = get_json(get_modpack_resourcepacks_url(modpack_key))
    if not isinstance(data, dict):
        raise RuntimeError("Le manifest resourcepacks doit etre un objet JSON")

    raw_packs = data.get("packs")
    if not isinstance(raw_packs, list):
        raise RuntimeError("Le manifest resourcepacks doit contenir une liste 'packs'")

    packs: list[ResourcePack] = []
    for index, entry in enumerate(raw_packs, start=1):
        if not isinstance(entry, dict):
            raise RuntimeError(f"packs[{index}] doit etre un objet")
        label = f"packs[{index}]"
        packs.append(
            ResourcePack(
                file_name=_required_string(entry, "file_name", label),
                download_url=_required_string(entry, "download_url", label),
                sha256=_required_string(entry, "sha256", label).lower(),
            )
        )

    return packs


def _sync_resourcepacks(resourcepacks_dir: Path, packs: list[ResourcePack]) -> None:
    resourcepacks_dir.mkdir(parents=True, exist_ok=True)

    for pack in packs:
        target = resourcepacks_dir / pack.file_name

        if target.exists() and _sha256(target) == pack.sha256:
            txtp(f"OK {pack.file_name}")
            continue

        if target.exists():
            txtp(f"Update {pack.file_name}")
            target.unlink()
        else:
            txtp(f"Install {pack.file_name}")

        download_file(pack.download_url, target)


def _quote_pack(file_name: str) -> str:
    return f"file/{file_name}"


def _parse_resourcepacks_value(value: str) -> list[str]:
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return []

    if not isinstance(parsed, list):
        return []

    return [item for item in parsed if isinstance(item, str)]


def _activate_resourcepacks(game_dir: Path, packs: list[ResourcePack]) -> None:
    options_path = game_dir / "options.txt"
    lines = options_path.read_text(encoding="utf-8").splitlines() if options_path.exists() else []

    wanted = [_quote_pack(pack.file_name) for pack in packs]
    found = False
    output: list[str] = []

    for line in lines:
        if not line.startswith("resourcePacks:"):
            output.append(line)
            continue

        current = _parse_resourcepacks_value(line.split(":", 1)[1])
        merged = [pack for pack in current if pack not in wanted]
        merged.extend(wanted)
        output.append(f"resourcePacks:{json.dumps(merged, ensure_ascii=False)}")
        found = True

    if not found:
        output.append(f"resourcePacks:{json.dumps(wanted, ensure_ascii=False)}")

    options_path.write_text("\n".join(output) + "\n", encoding="utf-8")


def update_txt_packs(game_dir: str | Path, modpack_key: str) -> None:
    game_path = Path(game_dir)

    txtp("Chargement du manifest resourcepacks...")
    packs = _load_manifest(modpack_key)

    txtp("Synchronisation des resourcepacks...")
    _sync_resourcepacks(game_path / RESOURCEPACKS_DIR_NAME, packs)

    txtp("Activation des resourcepacks...")
    _activate_resourcepacks(game_path, packs)

    success("Resourcepacks synchronises avec succes !")
