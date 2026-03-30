import shutil
from colorama import Fore, Style, init

init(autoreset=True)


def info(message: str) -> None:
    print(f"{Fore.CYAN}  ℹ️  - {message}{Style.RESET_ALL}")


def success(message: str) -> None:
    print(f"{Fore.GREEN}  [✅] - {message}{Style.RESET_ALL}")


def error(message: str) -> None:
    print(f"{Fore.RED}❌ - {message} - ❌{Style.RESET_ALL}")


def step(message: str) -> None:
    width = shutil.get_terminal_size().columns

    if width % 2 != 0:
        width -= 1

    text = f" {message} "
    line = text.center(width, "─")

    print(f"{Fore.MAGENTA}{line}{Style.RESET_ALL}")

# ----- Fabric ----- #
def fabric(message: str) -> None:
    print(f"  [⛩️ ] - {message}")

# ----- Mods ----- #
def mods(message: str) -> None:
    print(f"  [🧬] - {message}")

def uptodate(message: str) -> None:
    print(f"{Fore.LIGHTCYAN_EX}      • 🎐 {message}{Style.RESET_ALL}")

def outdated(message: str) -> None:
    print(f"{Fore.LIGHTMAGENTA_EX}      • 💤 {message}{Style.RESET_ALL}")

def missing(message: str) -> None:
    print(f"{Fore.LIGHTRED_EX}      • 🏮 {message}{Style.RESET_ALL}")

def extra(message: str) -> None:
    print(f"{Fore.LIGHTYELLOW_EX}      • 🔅 {message}{Style.RESET_ALL}")

# ----- Resourcepacks ----- #
def txtp(message: str) -> None:
    print(f"  [🗻] - {message}")

# ----- Shaderpacks ----- #
def shader(message: str) -> None:
    print(f"  [🌌] - {message}")