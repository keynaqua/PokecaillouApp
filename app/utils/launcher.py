import subprocess
from config import AUMID

def launch_minecraft_launcher() -> None:
    subprocess.Popen(
        ["explorer.exe", f"shell:AppsFolder\\{AUMID}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )