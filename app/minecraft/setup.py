from pathlib import Path
from config import get_minecraft_dir

DEFAULT_SUBDIRS = (
    "mods",
    "config",
    "resourcepacks",
    "shaderpacks",
    "saves",
    "logs",
    "crash-reports",
)


def ensure_installation_ready(name="pokecaillou", base_dir=".installations"):
    """
    Prépare un game directory Minecraft isolé, prêt à être utilisé
    avec un profil Fabric existant du launcher.

    Retourne le chemin absolu du dossier créé.
    """
    root = get_minecraft_dir() / base_dir / name
    root.mkdir(parents=True, exist_ok=True)

    for subdir in DEFAULT_SUBDIRS:
        (root / subdir).mkdir(exist_ok=True)

    return root.resolve()