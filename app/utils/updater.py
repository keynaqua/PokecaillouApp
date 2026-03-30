import re
import sys
import time
import subprocess
from pathlib import Path

from logger import info
from config import VERSION, GITHUB_OWNER, GITHUB_REPO, APP_BASENAME
from utils.http import get_json, download_file
from gui import ask_update_confirmation, show_info_dialog, show_error_dialog


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


def wait_until_file_released(path: Path, timeout: float = 20.0) -> bool:
    deadline = time.time() + timeout

    while time.time() < deadline:
        if not path.exists():
            return True

        try:
            tmp = path.with_suffix(path.suffix + ".tmpcheck")
            path.rename(tmp)
            tmp.rename(path)
            return True
        except OSError:
            time.sleep(0.4)

    return False


def delete_file_when_possible(path: Path, timeout: float = 20.0) -> bool:
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
    if "--cleanup-old" not in sys.argv:
        return

    idx = sys.argv.index("--cleanup-old")
    if idx + 1 >= len(sys.argv):
        return

    old_exe = Path(sys.argv[idx + 1])

    wait_until_file_released(old_exe, timeout=20.0)
    deleted = delete_file_when_possible(old_exe, timeout=20.0)

    if deleted:
        info(f"Programme mis à jour vers la version {VERSION}")
    else:
        info("Mise à jour effectuée, mais l'ancienne version n'a pas pu être supprimée immédiatement.")


def launch_updated_exe(new_exe: Path, old_exe: Path) -> None:
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW

    subprocess.Popen(
        [str(new_exe), "--cleanup-old", str(old_exe)],
        cwd=str(new_exe.parent),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )


def check_for_updates() -> bool:
    """
    Retourne True si une mise à jour a été lancée
    et que l'app actuelle doit se fermer.
    """
    try:
        release = get_latest_release_info()
    except Exception as e:
        # en cas d'erreur update, on n'empêche pas l'install de continuer
        info(f"Impossible de vérifier les mises à jour : {e}")
        return False

    remote_version = release["version"]

    if not is_newer_version(VERSION, remote_version):
        return False

    accepted = ask_update_confirmation(
        title="Mise à jour disponible",
        message=(
            f"Une nouvelle version est disponible.\n\n"
            f"Version actuelle : {VERSION}\n"
            f"Nouvelle version : {remote_version}\n\n"
            f"Clique sur OK pour télécharger et lancer la mise à jour."
        ),
    )

    if not accepted:
        return False

    destination = app_dir() / release["asset_name"]

    try:
        if not destination.exists():
            info(f"Téléchargement de la version {remote_version}...")
            download_file(release["download_url"], destination)

        old_exe = current_exe_path()
        launch_updated_exe(destination, old_exe)
        show_info_dialog(
            "Mise à jour",
            "La nouvelle version va être lancée."
        )
        return True

    except Exception as e:
        show_error_dialog("Erreur de mise à jour", str(e))
        return False


def cleanup_other_versions() -> None:
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
