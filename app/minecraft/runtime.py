from config import MC_VERSION, get_minecraft_dir
from fabric.detect import get_installed_fabric_version_id
from logger import success
from minecraft.profile import create_launcher_profile
from minecraft.setup import ensure_installation_ready


def create_minecraft_profile(name="Pokecaillou"):
    """
    Prepare a dedicated Minecraft installation and keep its launcher
    profile aligned with the currently installed Fabric version.
    """
    mc_dir = get_minecraft_dir()
    install_path = mc_dir / ".installations" / "pokecaillou"
    already_exists = install_path.exists()

    path = ensure_installation_ready("pokecaillou")
    version = get_installed_fabric_version_id(mc_dir, MC_VERSION)

    create_launcher_profile(name, path, version)

    if not already_exists:
        success("Installation de la config minecraft terminee")
    else:
        success("Installation deja presente, profil mis a jour")

    return path
