import threading
import tkinter as tk
from tkinter import messagebox

from config import APP_TITLE, PALETTE
from utils.launcher import launch_minecraft_launcher

from .core.state import log_queue
from .screens.home import build_home_screen
from .screens.install import InstallationScreen
from .screens.modpacks import build_modpack_screen
from .screens.uninstall import build_uninstall_options_screen


class InstallerGui:
    def __init__(self, run_func):
        self.run_func = run_func
        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.configure(bg=PALETTE["bg"])

        self.state = {
            "status": "idle",
            "progress": 0,
            "selected_modpack": None,
        }

        self.install_screen = None
        self.uninstall_func = None
        self._configure_window()

        self.container = tk.Frame(self.root, bg=PALETTE["bg"])
        self.container.grid(row=0, column=0, sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

    def _configure_window(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = max(960, int(screen_width * 2 / 3))
        height = max(640, int(screen_height * 2 / 3))
        x = max(0, int((screen_width - width) / 2))
        y = max(0, int((screen_height - height) / 2))

        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(900, 600)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

    def run(self):
        self.show_home()
        self.root.mainloop()

    def clear(self):
        self.install_screen = None
        for child in self.container.winfo_children():
            child.destroy()

    def show_home(self):
        self.state["status"] = "idle"
        self.state["progress"] = 0
        self.clear()
        build_home_screen(
            self.container,
            on_launch=self.show_modpacks,
            on_uninstall=self.show_uninstall_modpacks,
        )

    def show_modpacks(self):
        self.clear()
        build_modpack_screen(
            self.container,
            on_select=self.start_install,
            on_back=self.show_home,
        )

    def show_uninstall_modpacks(self):
        self.clear()
        build_modpack_screen(
            self.container,
            on_select=lambda modpack_name, _safe_mode=False: self.show_uninstall_options(modpack_name),
            on_back=self.show_home,
            title_text="Desinstaller un modpack",
            show_safe_mode=False,
        )

    def show_uninstall_options(self, modpack_name: str):
        self.state["selected_modpack"] = modpack_name
        self.clear()
        build_uninstall_options_screen(
            self.container,
            modpack_name,
            on_select=lambda mode: self.start_uninstall(modpack_name, mode),
            on_back=self.show_uninstall_modpacks,
        )

    def start_install(self, modpack_name: str, safe_mode: bool = False):
        self.state["selected_modpack"] = modpack_name
        self.state["safe_mode"] = safe_mode
        self.state["status"] = "running"
        self.state["progress"] = 0

        while not log_queue.empty():
            log_queue.get()

        self.clear()
        self.install_screen = InstallationScreen(
            self.container,
            self.root,
            self.state,
            modpack_name,
            on_open_launcher=self.open_launcher,
        )
        self.install_screen.render()
        self.install_screen.process_logs()

        threading.Thread(target=self.run_install, args=(modpack_name, safe_mode), daemon=True).start()

    def start_uninstall(self, modpack_name: str, mode):
        if getattr(mode, "value", mode) == "full":
            confirmed = messagebox.askyesno(
                "Confirmer la desinstallation",
                "Cette option supprime entierement le dossier du modpack, saves et settings inclus.\n\n"
                "Continuer ?",
                parent=self.root,
            )
            if not confirmed:
                return

        self.state["selected_modpack"] = modpack_name
        self.state["status"] = "running"
        self.state["progress"] = 0

        while not log_queue.empty():
            log_queue.get()

        self.clear()
        self.install_screen = InstallationScreen(
            self.container,
            self.root,
            self.state,
            modpack_name,
            on_open_launcher=self.root.destroy,
            operation="uninstall",
        )
        self.install_screen.render()
        self.install_screen.process_logs()

        threading.Thread(target=self.run_uninstall, args=(modpack_name, mode), daemon=True).start()

    def run_install(self, modpack_name: str, safe_mode: bool):
        try:
            self.run_func(modpack_name, safe_mode)
            log_queue.put(("done", "success"))
        except Exception as exc:
            log_queue.put(("log", f"Erreur: {exc}", "red"))
            log_queue.put(("done", "error"))

    def run_uninstall(self, modpack_name: str, mode):
        try:
            self.uninstall_func(modpack_name, mode)
            log_queue.put(("done", "success"))
        except Exception as exc:
            log_queue.put(("log", f"Erreur: {exc}", "red"))
            log_queue.put(("done", "error"))

    def open_launcher(self):
        if self.state["status"] != "success":
            return

        self.root.destroy()
        launch_minecraft_launcher()


def start_gui(run_func, uninstall_func=None):
    gui = InstallerGui(run_func)
    gui.uninstall_func = uninstall_func
    gui.run()
