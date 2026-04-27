from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from urllib.request import urlopen

from config import GITHUB_API_URL
from logger import extra, info, missing, mods, outdated, uptodate
from utils.http import download_file, get_json

from .detect import detect_mods, parse_installed_mod_bytes


@dataclass
class RemoteMod:
    name: str
    download_url: str
    sha1: str
    mod_id: str
    version: str


def _sha1_bytes(raw_bytes: bytes) -> str:
    return hashlib.sha1(raw_bytes).hexdigest()


def _sha1_file(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as file:
        while True:
            chunk = file.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _download_bytes(url: str) -> bytes:
    with urlopen(url) as response:
        return response.read()


def _fetch_remote_mods() -> list[RemoteMod]:
    mods("Lecture des mods distants depuis la branche repo...")
    data = get_json(GITHUB_API_URL)

    if not isinstance(data, list):
        raise RuntimeError("Reponse GitHub invalide")

    remote_mods: list[RemoteMod] = []
    seen_mod_ids: dict[str, str] = {}

    for entry in data:
        if not isinstance(entry, dict) or entry.get("type") != "file":
            continue

        name = entry.get("name")
        download_url = entry.get("download_url")
        if not isinstance(name, str) or not name.endswith(".jar"):
            continue
        if not isinstance(download_url, str) or not download_url.strip():
            continue

        mods(f"Analyse du mod distant: {name}")
        raw_bytes = _download_bytes(download_url)
        remote_meta = parse_installed_mod_bytes(raw_bytes, name)
        remote = RemoteMod(
            name=name,
            download_url=download_url,
            sha1=_sha1_bytes(raw_bytes),
            mod_id=remote_meta.mod_id,
            version=remote_meta.version,
        )

        previous_name = seen_mod_ids.get(remote.mod_id)
        if previous_name is not None:
            raise RuntimeError(
                f"Deux mods distants ont le meme id '{remote.mod_id}': "
                f"{previous_name} et {remote.name}"
            )

        seen_mod_ids[remote.mod_id] = remote.name
        remote_mods.append(remote)

    return remote_mods


def sync_remote_repo_mods(instance_mods_dir: str | Path):
    instance_path = Path(instance_mods_dir)
    instance_path.mkdir(parents=True, exist_ok=True)

    remote_mods = _fetch_remote_mods()
    detected = detect_mods(instance_path)

    if detected.broken_files:
        mods("Fichiers locaux ignores pendant la synchro repo:")
        for file_path, reason in detected.broken_files:
            extra(f"{file_path.name}: {reason}")

    local_hashes: dict[str, tuple[Path, str]] = {}
    local_by_mod_id: dict[str, list] = {}

    for mod in detected.mods:
        local_by_mod_id.setdefault(mod.mod_id, []).append(mod)
        try:
            local_hashes[mod.file_path.name] = (mod.file_path, _sha1_file(mod.file_path))
        except Exception as exc:
            extra(f"Hash local ignore pour {mod.file_path.name}: {exc}")

    for remote in remote_mods:
        target_file = instance_path / remote.name
        local_same_name = local_hashes.get(remote.name)
        same_mods = local_by_mod_id.get(remote.mod_id, [])

        remove_candidates = {
            mod.file_path
            for mod in same_mods
            if mod.file_path.name != remote.name or mod.version != remote.version
        }

        for old_file in sorted(remove_candidates, key=lambda path: path.name):
            if old_file.exists():
                outdated(
                    f"Repo cleanup {remote.mod_id}: suppression de {old_file.name}"
                )
                old_file.unlink()

        if not local_same_name:
            missing(f"Repo install {remote.mod_id} ({remote.version})")
            info(f" - [MODS][REPO] Download: {remote.name}")
            download_file(remote.download_url, target_file)
            continue

        local_file, local_sha = local_same_name
        if local_sha != remote.sha1:
            outdated(f"Repo update {remote.mod_id}: {local_file.name} -> {remote.name}")

            if local_file.exists():
                info(f" - [MODS][REPO] Remove: {local_file.name}")
                local_file.unlink()

            info(f" - [MODS][REPO] Download: {remote.name}")
            download_file(remote.download_url, target_file)
            continue

        uptodate(f"Repo OK {remote.mod_id} ({remote.version})")
