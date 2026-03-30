import os
import re
import sys
import time
import subprocess
from pathlib import Path

from config import VERSION, GITHUB_OWNER, GITHUB_REPO, APP_BASENAME
from utils.http import get_json, download_file


def parse_version(version: str) -> tuple[int, ...]:
    version = version.strip().lstrip("vV")
    parts = []
    for p in version.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def is_newer_version(local: str, remote: str) -> bool:
    return parse_version(remote) > parse_version(local)


def current_exe_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    return Path(sys.argv[0]).resolve()


def app_dir() -> Path:
    return current_exe_path().parent


def build_versioned_exe_name(version: str) -> str:
    return f"{APP_BASENAME}-{version}.exe"


def get_latest_release_info() -> dict:
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
    data = get_json(url)

    if not isinstance(data, dict):
        raise RuntimeError("Réponse GitHub invalide.")

    tag_name = str(data.get("tag_name", "")).strip()
    if not tag_name:
        raise RuntimeError("tag_name absent de la release.")

    remote_version = tag_name.lstrip("vV")
    expected_name = build_versioned_exe_name(remote_version)

    assets = data.get("assets", [])
    if not isinstance(assets, list):
        raise RuntimeError("Liste assets invalide.")

    for asset in assets:
        if not isinstance(asset, dict):
            continue
        if asset.get("name") == expected_name:
            return {
                "version": remote_version,
                "asset_name": expected_name,
                "download_url": asset.get("browser_download_url", ""),
            }

    available = [a.get("name", "?") for a in assets if isinstance(a, dict)]
    raise RuntimeError(
        f"Asset '{expected_name}' introuvable. Assets disponibles: {available}"
    )


def wait_until_file_released(path: Path, timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout

    while time.time() < deadline:
        if not path.exists():
            return True

        try:
            # Tente un renommage neutre pour vérifier que le fichier n'est plus lock
            tmp = path.with_suffix(path.suffix + ".tmpcheck")
            path.rename(tmp)
            tmp.rename(path)
            return True
        except OSError:
            time.sleep(0.4)

    return False


def delete_file_when_possible(path: Path, timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            if not path.exists():
                return True
            path.unlink()
            return True
        except OSError:
            time.sleep(0.4)

    return False


def handle_cleanup_args() -> None:
    """
    À appeler au tout début du programme.
    Si lancé avec:
        --cleanup-old "chemin_ancien_exe"
    alors on attend que l'ancien soit fermé puis on le supprime.
    """
    if "--cleanup-old" not in sys.argv:
        return

    idx = sys.argv.index("--cleanup-old")
    if idx + 1 >= len(sys.argv):
        return

    old_exe = Path(sys.argv[idx + 1])

    # On attend que l'ancien process ait relâché le fichier
    wait_until_file_released(old_exe, timeout=20.0)
    delete_file_when_possible(old_exe, timeout=20.0)


def launch_updated_exe(new_exe: Path, old_exe: Path) -> None:
    subprocess.Popen(
        [str(new_exe), "--cleanup-old", str(old_exe)],
        cwd=str(new_exe.parent),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def check_for_updates() -> bool:
    """
    Retourne True si une mise à jour a été lancée
    et que l'app actuelle doit se fermer.
    """
    release = get_latest_release_info()
    remote_version = release["version"]

    if not is_newer_version(VERSION, remote_version):
        return False

    destination = app_dir() / release["asset_name"]

    # Évite de re-télécharger si déjà présent
    if not destination.exists():
        download_file(release["download_url"], destination)

    old_exe = current_exe_path()
    launch_updated_exe(destination, old_exe)
    return True


def cleanup_other_versions() -> None:
    """
    Supprime les autres exes versionnés sauf celui en cours.
    """
    current = current_exe_path()
    pattern = re.compile(
        rf"^{re.escape(APP_BASENAME)}-\d+\.\d+\.\d+\.exe$",
        re.IGNORECASE,
    )

    for path in app_dir().iterdir():
        if not path.is_file():
            continue
        if path == current:
            continue
        if pattern.match(path.name):
            try:
                path.unlink()
            except OSError:
                pass
