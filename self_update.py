import os
import sys
import subprocess
from pathlib import Path

from app_meta import APP_NAME, APP_VERSION
from utils.http import get_json, download_file, DownloadError


class UpdateError(Exception):
    pass


def get_running_executable() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    return Path(sys.argv[0]).resolve()


def parse_version(version: str) -> tuple[int, ...]:
    try:
        return tuple(int(part) for part in version.strip().split("."))
    except ValueError as e:
        raise UpdateError(f"Version invalide: {version}") from e


def is_newer_version(local_version: str, remote_version: str) -> bool:
    return parse_version(remote_version) > parse_version(local_version)


def cleanup_update_temp_files(app_dir: Path) -> None:
    for name in ("update_tmp.bat", f"{APP_NAME}_new.exe"):
        path = app_dir / name
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass


def fetch_update_manifest() -> dict:
    try:
        data = get_json(UPDATE_MANIFEST_URL)
    except DownloadError as e:
        raise UpdateError(str(e)) from e

    if not isinstance(data, dict):
        raise UpdateError("Le manifest de mise à jour doit être un objet JSON.")

    version = data.get("version")
    url = data.get("url")

    if not version or not isinstance(version, str):
        raise UpdateError("Le manifest doit contenir une clé 'version' valide.")

    if not url or not isinstance(url, str):
        raise UpdateError("Le manifest doit contenir une clé 'url' valide.")

    return data


def write_update_script(script_path: Path, current_exe: Path, new_exe: Path) -> None:
    script = f"""@echo off
setlocal

timeout /t 2 /nobreak > nul

:retry_delete
del "{current_exe}" > nul 2>&1
if exist "{current_exe}" (
    timeout /t 1 /nobreak > nul
    goto retry_delete
)

rename "{new_exe.name}" "{current_exe.name}"
start "" "{current_exe.name}"

del "%~f0"
exit
"""
    script_path.write_text(script, encoding="utf-8")


def apply_update(download_url: str) -> None:
    current_exe = get_running_executable()
    app_dir = current_exe.parent
    new_exe = app_dir / f"{APP_NAME}_new.exe"
    update_script = app_dir / "update_tmp.bat"

    if current_exe.suffix.lower() != ".exe":
        raise UpdateError("L'auto-update complet fonctionne sur la version packagée en .exe.")

    try:
        download_file(download_url, new_exe)
    except DownloadError as e:
        raise UpdateError(str(e)) from e

    if not new_exe.exists() or new_exe.stat().st_size == 0:
        raise UpdateError("Le nouvel exécutable téléchargé est introuvable ou vide.")

    write_update_script(update_script, current_exe, new_exe)

    subprocess.Popen(
        ["cmd", "/c", str(update_script.name)],
        cwd=str(app_dir),
        shell=False,
    )

    sys.exit(0)


def check_and_update() -> None:
    current_exe = get_running_executable()
    app_dir = current_exe.parent

    cleanup_update_temp_files(app_dir)

    manifest = fetch_update_manifest()
    remote_version = manifest["version"]
    download_url = manifest["url"]

    if is_newer_version(APP_VERSION, remote_version):
        print(f"Nouvelle version disponible : {remote_version}")
        print("Téléchargement de la mise à jour...")
        apply_update(download_url)
