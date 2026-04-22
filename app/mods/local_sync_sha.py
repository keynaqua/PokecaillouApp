from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import urlopen

from utils.http import get_json, download_file

from config import GITHUB_API_URL

# =========================
# MODELS
# =========================

class RemoteMod:
    def __init__(self, name: str, download_url: str, sha1: str):
        self.name = name
        self.download_url = download_url
        self.sha1 = sha1


# =========================
# SHA
# =========================

def _sha1_file(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _sha1_url(url: str) -> str:
    h = hashlib.sha1()

    with urlopen(url) as response:
        while True:
            chunk = response.read(8192)
            if not chunk:
                break
            h.update(chunk)

    return h.hexdigest()


# =========================
# GITHUB
# =========================

def _fetch_remote_mods() -> list[RemoteMod]:
    print("[LOCAL SHA] Fetch repo mods...")

    data = get_json(GITHUB_API_URL)

    if not isinstance(data, list):
        raise RuntimeError("Réponse GitHub invalide")

    mods: list[RemoteMod] = []

    for entry in data:
        if not isinstance(entry, dict):
            continue

        if entry.get("type") != "file":
            continue

        name = entry.get("name")
        if not isinstance(name, str) or not name.endswith(".jar"):
            continue

        download_url = entry.get("download_url")
        if not isinstance(download_url, str):
            continue

        print(f"[LOCAL SHA] Hash remote: {name}")
        sha1 = _sha1_url(download_url)

        mods.append(RemoteMod(name, download_url, sha1))

    return mods


# =========================
# SYNC
# =========================

def sync_remote_repo_mods(instance_mods_dir: str | Path):
    instance_path = Path(instance_mods_dir)
    instance_path.mkdir(parents=True, exist_ok=True)

    remote_mods = _fetch_remote_mods()

    # =========================
    # HASH LOCAL
    # =========================

    local_hashes: dict[str, tuple[Path, str]] = {}

    for file in instance_path.glob("*.jar"):
        try:
            sha = _sha1_file(file)
            local_hashes[file.name] = (file, sha)
        except Exception:
            print(f"[LOCAL SHA] Ignored local file: {file.name}")

    # =========================
    # COMPARE
    # =========================

    for mod in remote_mods:
        local = local_hashes.get(mod.name)
        target_file = instance_path / mod.name

        # INSTALL
        if not local:
            print(f"[LOCAL SHA] Install {mod.name}")
            download_file(mod.download_url, target_file)
            continue

        local_file, local_sha = local

        # UPDATE
        if local_sha != mod.sha1:
            print(f"[LOCAL SHA] Update {mod.name}")
            try:
                local_file.unlink()
            except OSError:
                pass

            download_file(mod.download_url, target_file)
            continue

        # OK
        print(f"[LOCAL SHA] OK {mod.name}")