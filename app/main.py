import sys
import ctypes
from pathlib import Path
from mods import update_mods
from txt_packs import update_txt_packs
from java import ensure_java_installed
from logger import step, error
from fabric import ensure_fabric_installed
from shaders import ensure_shaders_installed
from minecraft import create_minecraft_profile
from utils.launcher import launch_minecraft_launcher
from config import MANIFEST_MODS_URL, MANIFEST_TXTP_URL, SHADER_URL
from utils.updater import handle_cleanup_args, cleanup_other_versions, check_for_updates


class InstallerError(Exception):
    pass


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False

def relaunch_as_admin() -> bool:
    if is_admin():
        return True

    script = str(Path(sys.argv[0]).resolve())
    params = " ".join(f'"{arg}"' for arg in sys.argv[1:])

    rc = ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        f'"{script}" {params}'.strip(),
        None,
        1,
    )

    # > 32 = succès
    if rc <= 32:
        raise RuntimeError("Impossible de demander l'élévation administrateur.")

    return False


def run():
    step("☕ Vérification de Java...")
    ensure_java_installed()

    step("🧵 Vérification de Fabric...")
    ensure_fabric_installed()

    step("📁 Préparation de l'installation Minecraft...")
    minecraft_dir = create_minecraft_profile("Pokecaillou")

    step("🧩 Synchronisation des mods...")
    update_mods(Path(minecraft_dir) / "mods", MANIFEST_MODS_URL)

    step("🎨 Synchronisation des packs de ressource...")
    update_txt_packs(Path(minecraft_dir) / "resourcepacks", MANIFEST_TXTP_URL)

    step("🌈 Vérification des shaders...")
    ensure_shaders_installed(Path(minecraft_dir) / "shaderpacks", SHADER_URL)

    step("🎉 Installation terminée !")

    launch_minecraft_launcher()


def main():
    handle_cleanup_args()
    cleanup_other_versions()

    if check_for_updates():
        return 0

    if not relaunch_as_admin():
        return 0

    code = 0

    try:
        run()
        input("\nAppuyez sur Entrée pour quitter...")
        return 0

    except InstallerError as e:
        error("Installation échouée")
        print(f"→ {e}")
        input("\nAppuyez sur Entrée pour quitter...")
        return 1

    except Exception as e:
        error("Erreur inattendue")
        print(f"→ {e}")
        input("\nAppuyez sur Entrée pour quitter...")
        return 1

if __name__ == "__main__":
    sys.exit(main())