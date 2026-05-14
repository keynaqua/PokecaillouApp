import ctypes
import sys
from pathlib import Path

import logger
from config import (
    CONFIG_DIR_NAME,
    LAUNCHER_FABRIC,
    LAUNCHER_NEOFORGE,
    MODPACK_DATA_OWNER,
    MODPACK_DATA_REPO,
    MODS_DIR_NAME,
    modpack_key,
)
from config_sync import sync_config_folder
from fabric import ensure_fabric_installed
from gui import log_queue, show_error_dialog, start_gui
from java import ensure_java_installed
from logger import error, progress, step
from minecraft import create_minecraft_profile
from modpack import ModpackInfo, load_modpack_info
from mods import update_mods
from neoforge import ensure_neoforge_installed
from shaders import ensure_shaders_installed
from txt_packs import update_txt_packs
from uninstall import uninstall_modpack
from utils.updater import check_for_updates, cleanup_other_versions, handle_cleanup_args


class InstallerError(Exception):
    pass


logger.log_queue = log_queue


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin() -> bool:
    if is_admin():
        return True

    exe_or_script = str(Path(sys.argv[0]).resolve())
    params = " ".join(f'"{arg}"' for arg in sys.argv[1:])

    if getattr(sys, "frozen", False):
        executable = exe_or_script
        arguments = params
    else:
        executable = sys.executable
        arguments = f'"{exe_or_script}" {params}'.strip()

    rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, arguments, None, 1)
    if rc <= 32:
        raise RuntimeError("Impossible de demander l'elevation administrateur.")

    return False


def ensure_launcher_installed(info: ModpackInfo) -> str:
    if info.launcher == LAUNCHER_FABRIC:
        return ensure_fabric_installed(info.minecraft_version, info.launcher_version)
    if info.launcher == LAUNCHER_NEOFORGE:
        return ensure_neoforge_installed(info.minecraft_version, info.launcher_version)
    raise InstallerError(f"Lanceur inconnu: {info.launcher}")


def run(info: ModpackInfo, safe_mode: bool):
    progress(10)
    step("Verification de Java...")
    ensure_java_installed()

    progress(20)
    step(f"Verification du lanceur {info.launcher}...")
    version_id = ensure_launcher_installed(info)

    progress(30)
    step("Preparation de l'installation Minecraft...")
    minecraft_dir = create_minecraft_profile(info.name, info.installation_dir, version_id)

    progress(50)
    step("Synchronisation des mods...")
    update_mods(Path(minecraft_dir) / MODS_DIR_NAME, info.key, safe_mode=safe_mode)

    progress(70)
    step("Synchronisation des packs de ressource...")
    update_txt_packs(minecraft_dir, info.key)

    progress(80)
    step("Verification des shaders...")
    ensure_shaders_installed(minecraft_dir, info.key)

    progress(90)
    step("Synchronisation des configs necessaires... (BETA)")
    sync_config_folder(
        MODPACK_DATA_OWNER,
        MODPACK_DATA_REPO,
        info.key,
        info.installation_dir,
        CONFIG_DIR_NAME,
    )

    progress(100)
    step("Installation terminee !")


def run_modpack(modpack_name: str, safe_mode: bool = False):
    key = modpack_key(modpack_name)
    try:
        info = load_modpack_info(key)
    except Exception as exc:
        raise InstallerError(
            f"Le manifest modpack.json de '{modpack_name}' est introuvable ou invalide: {exc}"
        ) from exc
    if not info.launcher:
        raise InstallerError(f"Le modpack '{modpack_name}' n'a pas de lanceur configure.")

    run(info, safe_mode)


def main():
    try:
        handle_cleanup_args()
        cleanup_other_versions()

        if check_for_updates():
            return 0

        if not relaunch_as_admin():
            return 0

        start_gui(run_modpack, uninstall_modpack)
        return 1

    except InstallerError as exc:
        show_error_dialog("Installation echouee", str(exc))
        return 1

    except Exception as exc:
        error("Erreur inattendue")
        show_error_dialog("Erreur inattendue", str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
