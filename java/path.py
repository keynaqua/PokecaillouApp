import os
import winreg
from pathlib import Path


def add_directory_to_user_path(directory: Path) -> None:
    directory_str = str(directory)

    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        "Environment",
        0,
        winreg.KEY_READ | winreg.KEY_WRITE
    ) as key:
        try:
            current_path, _ = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            current_path = ""

        entries = [entry.strip() for entry in current_path.split(";") if entry.strip()]
        lowered = [entry.lower() for entry in entries]

        if directory_str.lower() not in lowered:
            new_path = current_path + (";" if current_path else "") + directory_str
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)

    os.environ["PATH"] = directory_str + os.pathsep + os.environ.get("PATH", "")
