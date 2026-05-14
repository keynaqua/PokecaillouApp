from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from zipfile import ZipFile

from config import (
    CONFIG_DIR_NAME,
    REMOTE_CONFIG_DIR_NAME,
    get_install_subdir,
)
from logger import info, success
from utils.http import download_file


class ConfigSyncError(RuntimeError):
    pass


def _github_zip_url(owner: str, repo: str, branch: str) -> str:
    return f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"


def sync_config_folder(
    owner: str,
    repo: str,
    branch: str,
    installation_name: str,
    target_subdir: str = CONFIG_DIR_NAME,
) -> Path:
    source_dir = REMOTE_CONFIG_DIR_NAME.strip("/")

    target_root = get_install_subdir(
        installation_name,
        target_subdir,
    )

    target_root.mkdir(parents=True, exist_ok=True)

    info(f" - [CONFIG] Source GitHub: {owner}/{repo}@{branch}/{source_dir}")
    info(f" - [CONFIG] Dossier cible: {target_root}")

    zip_url = _github_zip_url(owner, repo, branch)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        zip_path = tmp_path / "repo.zip"

        try:
            info(" - [CONFIG] Telechargement de l'archive GitHub...")
            download_file(zip_url, zip_path)

            extract_dir = tmp_path / "extract"
            extract_dir.mkdir(parents=True, exist_ok=True)

            info(" - [CONFIG] Extraction de l'archive...")
            with ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)

        except Exception as exc:
            raise ConfigSyncError(
                f"Impossible de telecharger/extract l'archive GitHub: {exc}"
            ) from exc

        extracted_dirs = [p for p in extract_dir.iterdir() if p.is_dir()]

        if not extracted_dirs:
          raise ConfigSyncError(
             "Aucun dossier trouve dans l'archive GitHub"
         )

        repo_root = extracted_dirs[0]

        source_root = repo_root / source_dir

        if not source_root.exists():
            info(" - [CONFIG] Aucun dossier config trouve dans le repo.")
            return target_root

        files = [p for p in source_root.rglob("*") if p.is_file()]

        if not files:
            info(" - [CONFIG] Aucun fichier trouve dans le dossier config.")
            return target_root

        for src_file in files:
            relative_path = src_file.relative_to(source_root)
            dst_file = target_root / relative_path

            dst_file.parent.mkdir(parents=True, exist_ok=True)

            info(f" - [CONFIG] Overwrite: {relative_path}")

            shutil.copy2(src_file, dst_file)

    success("Config synchronisee avec succes.")

    return target_root