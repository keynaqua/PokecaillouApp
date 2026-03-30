import shutil
from pathlib import Path
from config import JAVA_MAJOR
from utils.process import get_command_output
from utils.version import parse_java_major


def get_java_major(java_cmd: str = "java"):
    try:
        output = get_command_output([java_cmd, "-version"])
    except OSError:
        return None

    return parse_java_major(output)


def is_java_ok() -> bool:
    java_path = shutil.which("java")
    if not java_path:
        return False

    major = get_java_major(java_path)
    return major == JAVA_MAJOR


def find_java_bin_default() -> Path | None:
    base_dir = Path(r"C:\Program Files\Eclipse Adoptium")
    if not base_dir.exists():
        return None

    for child in sorted(base_dir.iterdir(), reverse=True):
        java_exe = child / "bin" / "java.exe"
        if not java_exe.exists():
            continue

        major = get_java_major(str(java_exe))
        if major == JAVA_MAJOR:
            return java_exe.parent

    return None