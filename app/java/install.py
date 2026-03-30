import subprocess
import tempfile
import os
from logger import info
from pathlib import Path
from config import JAVA_MAJOR
from utils.http import get_json, download_file


def get_latest_temurin_msi_info():
    file_name = f"OpenJDK{JAVA_MAJOR}U-jdk_x64_windows_hotspot_latest.msi"
    url = (
        f"https://api.adoptium.net/v3/installer/latest/"
        f"{JAVA_MAJOR}/ga/windows/x64/jdk/hotspot/normal/eclipse"
        f"?project=jdk"
    )
    return file_name, url


def download_java_msi() -> Path:
    file_name, file_url = get_latest_temurin_msi_info()

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".msi")
    tmp_file.close()

    msi_path = Path(tmp_file.name)

    info(f"Téléchargement de Java {JAVA_MAJOR}...")
    return download_file(file_url, msi_path)


def install_java_silently(msi_path: Path) -> None:
    # log temporaire (même principe)
    log_file = tempfile.NamedTemporaryFile(delete=False, suffix=".log")
    log_file.close()
    log_path = Path(log_file.name)

    cmd = [
        "msiexec",
        "/i",
        str(msi_path),
        "ADDLOCAL=FeatureMain,FeatureEnvironment,FeatureJarFileRunWith,FeatureJavaHome",
        "/qn",
        "/norestart",
        "/L*v",
        str(log_path),
    ]

    info(f"Installation silencieuse de Java...")
    info(f"Log MSI : {log_path}")

    try:
        result = subprocess.run(cmd, check=False)

        if result.returncode != 0:
            raise RuntimeError(
                f"Échec de l'installation Java (code retour {result.returncode}). "
                f"Consulte le log MSI : {log_path}"
            )
    finally:
        # 🔥 suppression automatique du MSI
        try:
            if msi_path.exists():
                msi_path.unlink()
        except OSError:
            pass

        # (optionnel) suppression du log si succès
        if log_path.exists():
            try:
                log_path.unlink()
            except OSError:
                pass
