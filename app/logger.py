log_queue = None

def progress(value: int):
    if log_queue:
        log_queue.put(("progress", value))

def _send(msg: str, tag: str = "default"):
    if log_queue:
        log_queue.put(("log", msg, tag))
    else:
        print(msg)


def info(message: str) -> None:
    _send(f"ℹ️  {message}", "cyan")


def success(message: str) -> None:
    _send(f"✅ {message}", "green")


def error(message: str) -> None:
    _send(f"❌ {message}", "red")


def step(message: str) -> None:
    width = 80
    text = f" {message} "
    line = text.center(width, "─")

    if log_queue:
        # log_queue.put(("clear", ""))  # ❌ désactivé pour l’instant

        pass

    _send(line, "magenta")


# ----- Fabric ----- #
def fabric(message: str) -> None:
    _send(f"[⛩️] {message}", "yellow")


# ----- Mods ----- #
def mods(message: str) -> None:
    _send(f"[🧬] {message}", "yellow")


def uptodate(message: str) -> None:
    _send(f"  • 🎐 {message}", "cyan")


def outdated(message: str) -> None:
    _send(f"  • 💤 {message}", "magenta")


def missing(message: str) -> None:
    _send(f"  • 🏮 {message}", "red")


def extra(message: str) -> None:
    _send(f"  • 🔅 {message}", "yellow")


# ----- Resourcepacks ----- #
def txtp(message: str) -> None:
    _send(f"[🗻] {message}", "yellow")


# ----- Shaderpacks ----- #
def shader(message: str) -> None:
    _send(f"[🌌] {message}", "yellow")