import sys
import ctypes
from pathlib import Path

from mods import update_mods
from txt_packs import update_txt_packs
from java import ensure_java_installed
from config_sync import sync_config_branch
from fabric import ensure_fabric_installed
from shaders import ensure_shaders_installed
from minecraft import create_minecraft_profile
from utils.launcher import launch_minecraft_launcher
from config import MANIFEST_MODS_URL, MANIFEST_TXTP_URL, SHADER_URL
from utils.updater import (
    handle_cleanup_args,
    cleanup_other_versions,
    check_for_updates,
)

class InstallerError(Exception):
    pass

import logger
from logger import step, error, progress
from gui import start_gui, log_queue, show_error_dialog

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

    # Si app packagée -> relance directement l'exe
    # Sinon -> relance via python
    if getattr(sys, "frozen", False):
        executable = exe_or_script
        arguments = params
    else:
        executable = sys.executable
        arguments = f'"{exe_or_script}" {params}'.strip()

    rc = ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        executable,
        arguments,
        None,
        1,
    )

    if rc <= 32:
        raise RuntimeError("Impossible de demander l'élévation administrateur.")

    return False


def run():
    progress(10)
    step("☕ Vérification de Java...")
    ensure_java_installed()

    progress(20)
    step("🧵 Vérification de Fabric...")
    ensure_fabric_installed()

    progress(30)
    step("📁 Préparation de l'installation Minecraft...")
    minecraft_dir = create_minecraft_profile("Pokecaillou")

    progress(50)
    step("🧩 Synchronisation des mods...")
    update_mods(Path(minecraft_dir) / "mods", MANIFEST_MODS_URL)

    progress(70)
    step("🎨 Synchronisation des packs de ressource...")
    update_txt_packs(Path(minecraft_dir) / "resourcepacks", MANIFEST_TXTP_URL)

    progress(80)
    step("🌈 Vérification des shaders...")
    ensure_shaders_installed(Path(minecraft_dir) / "shaderpacks", SHADER_URL)

    progress(90)
    step("⛲️ Synchronisation des configs nécessaires... (BETA)")
    sync_config_branch("keynaqua", "Pokecaillou", "configs")

    progress(100)
    step("🎉 Installation terminée !")

    launch_minecraft_launcher()


def main():
    try:
        # 1) si le nouveau programme vient d'être lancé après update,
        # il supprime l'ancien exe ici
        handle_cleanup_args()

        # 2) nettoie les autres versions éventuelles
        cleanup_other_versions()

        # 3) check update AVANT de lancer l'install
        if check_for_updates():
            return 0

        # 4) ensuite seulement admin
        if not relaunch_as_admin():
            return 0

        start_gui(run)
        return 1

    except InstallerError as e:
        show_error_dialog("Installation échouée", str(e))
        return 1

    except Exception as e:
        error("Erreur inattendue")
        show_error_dialog("Erreur inattendue", str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())