from logger import success
from config import (MC_VERSION, get_minecraft_dir)
from minecraft.setup import ensure_installation_ready
from minecraft.profile import create_launcher_profile
from fabric.detect import get_installed_fabric_version_id


def create_minecraft_profile(name="Pokecaillou"):
    """
    Crée un gameDir dédié et un profil Minecraft Launcher
    qui utilise la version Fabric déjà installée.

    Retourne un tuple:
        (profile_name, game_dir, version_id)
    """
    path = ensure_installation_ready("pokecaillou")
    version = get_installed_fabric_version_id(get_minecraft_dir(), MC_VERSION)
    create_launcher_profile("Pokecaillou", path, version)
    
    success(f"Installation de la config minecraft terminée")
    return path
