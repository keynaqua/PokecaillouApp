from logger import fabric
from pathlib import Path
from config import TEMP_DIR
from utils.http import download_file


def download_fabric_installer(installer_version: str) -> Path:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    jar_name = f"fabric-installer-{installer_version}.jar"
    jar_path = TEMP_DIR / jar_name
    jar_url = (
        f"https://maven.fabricmc.net/net/fabricmc/"
        f"fabric-installer/{installer_version}/{jar_name}"
    )

    fabric(f"Téléchargement de l'installateur Fabric {installer_version}...")
    return download_file(jar_url, jar_path)
