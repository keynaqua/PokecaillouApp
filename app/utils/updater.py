import re
import subprocess
import sys
from pathlib import Path

from config import (
    APP_BASENAME,
    UPDATE_HTTP_RETRIES,
    UPDATE_HTTP_TIMEOUT,
    UPDATE_SCRIPT_NAME,
    VERSION,
    github_release_api,
    pending_update_name,
    release_exe_name,
)
from gui import ask_update_confirmation, show_error_dialog, show_info_dialog
from logger import info
from utils.http import download_file, get_json


def parse_version(version: str) -> tuple[int, ...]:
    version = version.strip().lstrip("vV")
    parts = []

    for part in version.split("."):
        try:
            parts.append(int(part))
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


def pending_update_path() -> Path:
    return app_dir() / pending_update_name()


def updater_script_path() -> Path:
    return app_dir() / UPDATE_SCRIPT_NAME


def get_latest_release_info() -> dict:
    data = get_json(github_release_api(), timeout=UPDATE_HTTP_TIMEOUT, retries=UPDATE_HTTP_RETRIES)

    if not isinstance(data, dict):
        raise RuntimeError("Reponse GitHub invalide.")

    tag_name = str(data.get("tag_name", "")).strip()
    if not tag_name:
        raise RuntimeError("tag_name absent de la release.")

    expected_name = release_exe_name()
    assets = data.get("assets", [])

    if not isinstance(assets, list):
        raise RuntimeError("Liste assets invalide.")

    for asset in assets:
        if not isinstance(asset, dict):
            continue
        if asset.get("name") == expected_name:
            download_url = asset.get("browser_download_url")
            if not isinstance(download_url, str) or not download_url.strip():
                raise RuntimeError(f"download_url manquant pour '{expected_name}'")

            return {
                "version": tag_name.lstrip("vV"),
                "asset_name": expected_name,
                "download_url": download_url,
            }

    available = [asset.get("name", "?") for asset in assets if isinstance(asset, dict)]
    raise RuntimeError(
        f"Asset '{expected_name}' introuvable. Assets disponibles: {available}"
    )


def handle_cleanup_args() -> None:
    # Compatibility with older versioned builds. The current updater replaces
    # KayouInstaller.exe before relaunching, so there is no old exe to delete.
    if "--cleanup-old" in sys.argv:
        info(f"Programme mis a jour vers la version {VERSION}")


def write_replacement_script(new_exe: Path, target_exe: Path, old_exe: Path) -> Path:
    script = updater_script_path()
    script.write_text(
        "\n".join(
            [
                "@echo off",
                "setlocal",
                f'set "NEW={new_exe}"',
                f'set "TARGET={target_exe}"',
                f'set "OLD={old_exe}"',
                "set /a TRIES=0",
                "",
                ":wait_old",
                'if /I "%OLD%"=="%TARGET%" goto replace',
                'if not exist "%OLD%" goto replace',
                'move /Y "%OLD%" "%OLD%.tmpcheck" >nul 2>nul',
                "if not errorlevel 1 goto restore_old",
                "set /a TRIES+=1",
                "if %TRIES% GEQ 60 goto failed",
                "timeout /t 1 /nobreak >nul",
                "goto wait_old",
                "",
                ":restore_old",
                'move /Y "%OLD%.tmpcheck" "%OLD%" >nul 2>nul',
                "set /a TRIES=0",
                "goto replace",
                "",
                ":replace",
                'move /Y "%NEW%" "%TARGET%" >nul 2>nul',
                "if not errorlevel 1 goto launch",
                "set /a TRIES+=1",
                "if %TRIES% GEQ 60 goto failed",
                "timeout /t 1 /nobreak >nul",
                "goto replace",
                "",
                ":launch",
                'if /I not "%OLD%"=="%TARGET%" del "%OLD%" >nul 2>nul',
                'start "" "%TARGET%"',
                'del "%~f0" >nul 2>nul',
                "exit /b 0",
                "",
                ":failed",
                "exit /b 1",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return script


def launch_replacement_script(script: Path) -> None:
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW

    subprocess.Popen(
        ["cmd.exe", "/c", str(script)],
        cwd=str(script.parent),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )


def check_for_updates() -> bool:
    """
    Returns True when an update has been started and this process should exit.
    """
    if not getattr(sys, "frozen", False):
        return False

    try:
        release = get_latest_release_info()
    except Exception as exc:
        info(f"Impossible de verifier les mises a jour : {exc}")
        return False

    remote_version = release["version"]

    if not is_newer_version(VERSION, remote_version):
        return False

    accepted = ask_update_confirmation(
        title="Mise a jour disponible",
        message=(
            f"Une nouvelle version est disponible.\n\n"
            f"Version actuelle : {VERSION}\n"
            f"Nouvelle version : {remote_version}\n\n"
            "Clique sur OK pour telecharger et installer la mise a jour."
        ),
    )

    if not accepted:
        return False

    pending_exe = pending_update_path()
    old_exe = current_exe_path()
    target_exe = app_dir() / release_exe_name()

    try:
        if pending_exe.exists():
            pending_exe.unlink()

        info(f"Telechargement de la version {remote_version}...")
        download_file(release["download_url"], pending_exe)

        show_info_dialog(
            "Mise a jour",
            "La mise a jour est prete. L'application va redemarrer.",
        )

        script = write_replacement_script(pending_exe, target_exe, old_exe)
        launch_replacement_script(script)
        return True

    except Exception as exc:
        try:
            if pending_exe.exists():
                pending_exe.unlink()
        except OSError:
            pass

        show_error_dialog("Erreur de mise a jour", str(exc))
        return False


def cleanup_other_versions() -> None:
    current = current_exe_path()
    legacy_versioned_exe = re.compile(
        rf"^{re.escape(APP_BASENAME)}-\d+\.\d+\.\d+\.exe$",
        re.IGNORECASE,
    )

    for path in app_dir().iterdir():
        if not path.is_file() or path == current:
            continue

        should_delete = (
            legacy_versioned_exe.match(path.name)
            or path.name == pending_update_path().name
        )

        if should_delete:
            try:
                path.unlink()
            except OSError:
                pass
