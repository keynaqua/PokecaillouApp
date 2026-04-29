from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from urllib.request import urlopen

from config import GITHUB_API_URL
from logger import extra, missing, mods, outdated
from utils.http import download_file, get_json

from .detect import detect_mods, parse_installed_mod_bytes
from .models import InstalledMod


@dataclass
class RemoteMod:
    name: str
    download_url: str
    sha1: str
    mod_id: str
    version: str


@dataclass
class RepoSyncAction:
    remote: RemoteMod
    remove_files: list[Path]


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


def _index_local_mods(mods: list[InstalledMod]) -> dict[str, list[InstalledMod]]:
    index: dict[str, list[InstalledMod]] = {}

    for mod in mods:
        index.setdefault(mod.mod_id, []).append(mod)

    return index


def _build_sync_actions(
    remote_mods: list[RemoteMod],
    local_mods: list[InstalledMod],
) -> tuple[list[RepoSyncAction], list[RepoSyncAction]]:
    local_by_mod_id = _index_local_mods(local_mods)

    missing_actions: list[RepoSyncAction] = []
    outdated_actions: list[RepoSyncAction] = []

    for remote in remote_mods:
        local_matches = local_by_mod_id.get(remote.mod_id, [])
        exact_match = next((mod for mod in local_matches if mod.version == remote.version), None)

        if exact_match is None:
            remove_files = [mod.file_path for mod in local_matches]
            missing_actions.append(RepoSyncAction(remote=remote, remove_files=remove_files))
            continue

        try:
            local_sha = _sha1_file(exact_match.file_path)
        except Exception as exc:
            raise RuntimeError(
                f"Impossible de calculer le hash de {exact_match.file_path.name}: {exc}"
            ) from exc

        stale_duplicates = [
            mod.file_path
            for mod in local_matches
            if mod.file_path != exact_match.file_path
        ]

        if local_sha != remote.sha1 or stale_duplicates:
            remove_files = [exact_match.file_path, *stale_duplicates] if local_sha != remote.sha1 else stale_duplicates
            outdated_actions.append(RepoSyncAction(remote=remote, remove_files=remove_files))

    return missing_actions, outdated_actions


def _apply_sync_actions(instance_path: Path, actions: list[RepoSyncAction]) -> None:
    for action in actions:
        for file_path in action.remove_files:
            if file_path.exists():
                file_path.unlink()

        target_file = instance_path / action.remote.name
        download_file(action.remote.download_url, target_file)


def sync_remote_repo_mods(instance_mods_dir: str | Path):
    instance_path = Path(instance_mods_dir)
    instance_path.mkdir(parents=True, exist_ok=True)

    remote_mods = _fetch_remote_mods()
    detected = detect_mods(instance_path)

    if detected.broken_files:
        mods("Ignored local files during distant mod folder synchronisation:")
        for file_path, reason in detected.broken_files:
            extra(f"{file_path.name}: {reason}")

    mods("Comparaison du dossier avec le repo distant")
    missing_actions, outdated_actions = _build_sync_actions(remote_mods, detected.mods)

    if missing_actions:
        mods("Mods manquants")
        for action in missing_actions:
            missing(f"INSTALL {action.remote.mod_id} -> {action.remote.version}")

    if outdated_actions:
        mods("Outdated")
        for action in outdated_actions:
            outdated(f"UPDATE {action.remote.mod_id} -> {action.remote.version}")

    _apply_sync_actions(instance_path, missing_actions)
    _apply_sync_actions(instance_path, outdated_actions)
