import subprocess
import tempfile
from pathlib import Path

from config import (
    MC_VERSION,
    FABRIC_META_URL,
    FABRIC_INSTALLER_META_URL,
    get_minecraft_dir,
)
from logger import fabric, success
from utils.http import get_json, download_file
from fabric.detect import find_installed_fabric_loader


def get_latest_loader_version(mc_version: str) -> str:
    data = get_json(f"{FABRIC_META_URL}/{mc_version}")

    if not data:
        raise RuntimeError(f"Aucune version Fabric trouvée pour Minecraft {mc_version}")

    return data[0]["loader"]["version"]


def get_latest_installer_version() -> str:
    data = get_json(FABRIC_INSTALLER_META_URL)

    if not data:
        raise RuntimeError("Impossible de récupérer la version de l'installateur Fabric")

    return data[0]["version"]


def run_fabric_installer(jar_path, mc_dir, mc_version, loader_version) -> None:
    cmd = [
        "java",
        "-jar",
        str(jar_path),
        "client",
        "-dir",
        str(mc_dir),
        "-mcversion",
        mc_version,
        "-loader",
        loader_version,
        "-noprofile"
    ]

    fabric("Lancement de l'installateur Fabric...")
    result = subprocess.run(cmd, check=False)

    if result.returncode != 0:
        raise RuntimeError(
            f"Échec de l'installation Fabric (code retour {result.returncode})"
        )


def ensure_fabric_installed() -> None:
    mc_dir = get_minecraft_dir()

    fabric(f"Dossier Minecraft : {mc_dir}")
    fabric(f"Version Minecraft cible : {MC_VERSION}")

    latest_loader = get_latest_loader_version(MC_VERSION)
    installed_loader = find_installed_fabric_loader(mc_dir, MC_VERSION)

    fabric(f"Loader Fabric attendu : {latest_loader}")
    fabric(f"Loader Fabric installé : {installed_loader or 'aucun'}")

    if installed_loader == latest_loader:
        success("Fabric est déjà installé dans la bonne version.")
        return

    fabric("Fabric absent ou pas à jour. Installation en cours...")

    installer_version = get_latest_installer_version()

    with tempfile.TemporaryDirectory() as tmp_dir:
        jar_name = f"fabric-installer-{installer_version}.jar"
        jar_path = Path(tmp_dir) / jar_name
        jar_url = (
            f"https://maven.fabricmc.net/net/fabricmc/"
            f"fabric-installer/{installer_version}/{jar_name}"
        )

        fabric(f"Téléchargement de l'installateur Fabric {installer_version}...")
        download_file(jar_url, jar_path)

        run_fabric_installer(
            jar_path=jar_path,
            mc_dir=mc_dir,
            mc_version=MC_VERSION,
            loader_version=latest_loader,
        )

    installed_loader = find_installed_fabric_loader(mc_dir, MC_VERSION)

    if installed_loader != latest_loader:
        raise RuntimeError("Fabric ne semble pas s'être installé correctement")

    success("Fabric installé / mis à jour avec succès.")
