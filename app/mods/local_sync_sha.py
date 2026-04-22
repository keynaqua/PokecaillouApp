from __future__ import annotations

import hashlib
from pathlib import Path

from utils.http import get_json, download_file  # ✅ IMPORTANT


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

    # ⚠️ on stream le download via download_file temporaire ? NON
    # ici on stream direct via urllib interne de get_json / download_file
    # MAIS comme on n'a pas accès au stream interne, on fallback simple :

    import urllib.request

    with urllib.request.urlopen(url) as response:
        while True:
            chunk = response.read(8192)
            if not chunk:
                break
            h.update(chunk)

    return h.hexdigest()


# =========================
# GitHub
# =========================

def _list_github_mods(owner: str, repo: str, path: str, branch: str) -> list[RemoteMod]:
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"

    data = get_json(api_url)  # ✅ robuste

    if not isinstance(data, list):
        raise RuntimeError(f"Réponse GitHub invalide pour {api_url}")

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
# Sync
# =========================

def sync_remote_repo_mods(
    instance_mods_dir: str | Path,
    owner: str,
    repo: str,
    repo_mods_path: str = "mods",
    branch: str = "mods",  # ✅ PAR DÉFAUT ta branche
):
    instance_path = Path(instance_mods_dir)
    instance_path.mkdir(parents=True, exist_ok=True)

    print("[LOCAL SHA] Fetch repo mods...")
    remote_mods = _list_github_mods(owner, repo, repo_mods_path, branch)

    # =========================
    # Hash local
    # =========================

    local_hashes: dict[str, tuple[Path, str]] = {}

    for file in instance_path.glob("*.jar"):
        try:
            sha = _sha1_file(file)
            local_hashes[file.name] = (file, sha)
        except Exception:
            print(f"[LOCAL SHA] Ignored local file: {file.name}")
            continue

    # =========================
    # Compare
    # =========================

    for mod in remote_mods:
        local = local_hashes.get(mod.name)
        target_file = instance_path / mod.name

        # 🆕 INSTALL
        if not local:
            print(f"[LOCAL SHA] Install {mod.name}")
            download_file(mod.download_url, target_file)
            continue

        local_file, local_sha = local

        # 🔁 UPDATE
        if local_sha != mod.sha1:
            print(f"[LOCAL SHA] Update {mod.name}")
            try:
                local_file.unlink()
            except OSError:
                pass

            download_file(mod.download_url, target_file)
            continue

        # ✅ OK
        print(f"[LOCAL SHA] OK {mod.name}")