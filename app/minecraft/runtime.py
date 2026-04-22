from logger import success
from config import MC_VERSION, get_minecraft_dir
from minecraft.setup import ensure_installation_ready
from minecraft.profile import create_launcher_profile
from fabric.detect import get_installed_fabric_version_id


def create_minecraft_profile(name="Pokecaillou"):
    """
    Crée une installation Minecraft dédiée et son profil launcher
    uniquement lors de la première installation.

    Retourne le chemin du game_dir.
    """
    mc_dir = get_minecraft_dir()
    install_path = mc_dir / ".installations" / "pokecaillou"
    already_exists = install_path.exists()

    path = ensure_installation_ready("pokecaillou")
    version = get_installed_fabric_version_id(mc_dir, MC_VERSION)

    if not already_exists:
        create_launcher_profile(name, path, version)
        success("Installation de la config minecraft terminée")
    else:
        success("Installation déjà présente, profil conservé")

    return path