import tkinter as tk

from config import APP_TITLE, GUI_FONT_SEMIBOLD, PALETTE
from gui.components import create_button


def build_home_screen(parent, on_launch, on_uninstall):
    screen = tk.Frame(parent, bg=PALETTE["bg"])
    screen.grid(row=0, column=0, sticky="nsew")

    center = tk.Frame(screen, bg=PALETTE["bg"])
    center.place(relx=0.5, rely=0.5, anchor="center")
    center.grid_columnconfigure(0, weight=1)

    title = tk.Label(
        center,
        text=APP_TITLE,
        bg=PALETTE["bg"],
        fg=PALETTE["text"],
        font=(GUI_FONT_SEMIBOLD, 42),
    )
    title.grid(row=0, column=0, pady=(0, 28))

    menu = tk.Frame(
        center,
        bg=PALETTE["surface"],
        highlightbackground=PALETTE["border"],
        highlightthickness=1,
        padx=32,
        pady=30,
        width=390,
        height=208,
    )
    menu.grid(row=1, column=0)
    menu.grid_columnconfigure(0, weight=1, minsize=256)
    menu.grid_propagate(False)

    launch = create_button(menu, "Lancer", on_launch)
    launch.grid(row=0, column=0, sticky="ew", pady=(0, 14))

    uninstall = create_button(menu, "Desinstaller", on_uninstall, variant="secondary")
    uninstall.grid(row=1, column=0, sticky="ew")

    return screen
