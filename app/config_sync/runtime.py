from __future__ import annotations

from pathlib import Path

from config import get_minecraft_dir
from logger import info, success
from utils.http import get_json, download_file


class ConfigSyncError(RuntimeError):
    pass


def _github_root_url(owner: str, repo: str, branch: str) -> str:
    return f"https://api.github.com/repos/{owner}/{repo}/contents?ref={branch}"


def _walk_repo(owner: str, repo: str, path: str | None, branch: str) -> list[dict]:
    """
    Liste récursivement tous les fichiers d'une branche GitHub.
    """
    if path:
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
    else:
        url = _github_root_url(owner, repo, branch)

    data = get_json(url)

    if isinstance(data, dict):
        if data.get("type") == "file":
            return [data]
        raise ConfigSyncError(f"Réponse GitHub invalide pour '{path or '/'}'")

    if not isinstance(data, list):
        raise ConfigSyncError(f"Réponse GitHub invalide pour '{path or '/'}'")

    files: list[dict] = []

    for entry in data:
        if not isinstance(entry, dict):
            continue

        entry_type = entry.get("type")
        entry_path = entry.get("path")

        if entry_type == "file":
            files.append(entry)

        elif entry_type == "dir":
            if not isinstance(entry_path, str) or not entry_path.strip():
                continue
            files.extend(_walk_repo(owner, repo, entry_path, branch))

    return files


def sync_config_branch(
    owner: str,
    repo: str,
    branch: str = "config",
    installation_name: str = "pokecaillou",
) -> Path:
    game_dir = get_minecraft_dir() / ".installations" / installation_name
    target_root = game_dir / "config"
    target_root.mkdir(parents=True, exist_ok=True)

    info(f" - [CONFIG] Source GitHub: {owner}/{repo}@{branch}")
    info(f" - [CONFIG] Dossier cible: {target_root}")

    try:
        files = _walk_repo(owner, repo, None, branch)
    except Exception as e:
        info(f" - [CONFIG] Impossible de récupérer la branche ({e}), étape ignorée.")
        return target_root

    # ✅ NOUVEAU COMPORTEMENT
    if not files:
        info(" - [CONFIG] Aucun fichier trouvé dans la branche, étape ignorée.")
        return target_root

    for entry in files:
        file_path = entry.get("path")
        download_url = entry.get("download_url")

        if not isinstance(file_path, str) or not file_path.strip():
            continue

        if not isinstance(download_url, str) or not download_url.strip():
            raise ConfigSyncError(f"download_url manquant pour '{file_path}'")

        relative_path = Path(file_path)
        destination = target_root / relative_path

        info(f" - [CONFIG] Download: {relative_path}")
        download_file(download_url, destination)

    success("Config synchronisée avec succès.")
    return target_root
