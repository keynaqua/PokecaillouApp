import ctypes
from config import JAVA_MAJOR
from logger import info, success
from java.path import add_directory_to_user_path
from java.detect import is_java_ok, find_java_bin_default
from java.install import download_java_msi, install_java_silently

def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False

def ensure_java_in_path_from_default_install() -> bool:
    java_bin = find_java_bin_default()
    if not java_bin:
        return False

    info(f"Java {JAVA_MAJOR} détecté au chemin par défaut : {java_bin}")
    add_directory_to_user_path(java_bin)
    success("Java ajouté au PATH utilisateur.")
    return True


def ensure_java_installed() -> None:
    if is_java_ok():
        success(f"Java {JAVA_MAJOR} déjà installé et disponible dans le PATH.")
        return

    if ensure_java_in_path_from_default_install():
        if is_java_ok():
            success(f"Java {JAVA_MAJOR} est maintenant disponible.")
            return

    msi_path = download_java_msi()
    if not is_admin():
        raise RuntimeError(
            "L'installation de Java nécessite des droits administrateur. "
            "Relance le terminal ou l'installeur en tant qu'administrateur."
        )
    install_java_silently(msi_path)

    if is_java_ok():
        success(f"Java {JAVA_MAJOR} installé avec succès.")
        return

    if ensure_java_in_path_from_default_install() and is_java_ok():
        success(f"Java {JAVA_MAJOR} installé et ajouté au PATH.")
        return

    raise RuntimeError(
        f"Java {JAVA_MAJOR} a été installé, mais n'est toujours pas détecté correctement."
    )
