import tkinter as tk

from config import GUI_FONT_SEMIBOLD, GUI_MODPACK_NAMES, PALETTE
from gui.components import create_button


def build_modpack_screen(
    parent,
    on_select,
    on_back,
    title_text: str = "Choisir un modpack",
    show_safe_mode: bool = True,
):
    screen = tk.Frame(parent, bg=PALETTE["bg"])
    screen.grid(row=0, column=0, sticky="nsew")

    center = tk.Frame(screen, bg=PALETTE["bg"])
    center.place(relx=0.5, rely=0.5, anchor="center")
    center.grid_columnconfigure(0, weight=1)

    title = tk.Label(
        center,
        text=title_text,
        bg=PALETTE["bg"],
        fg=PALETTE["text"],
        font=(GUI_FONT_SEMIBOLD, 34),
    )
    title.grid(row=0, column=0, pady=(0, 28))

    packs = tk.Frame(
        center,
        bg=PALETTE["surface"],
        highlightbackground=PALETTE["border"],
        highlightthickness=1,
        padx=32,
        pady=30,
        width=430,
        height=288,
    )
    packs.grid(row=1, column=0)
    packs.grid_columnconfigure(0, weight=1, minsize=296)
    packs.grid_propagate(False)

    safe_mode = tk.BooleanVar(value=False)

    for index, modpack_name in enumerate(GUI_MODPACK_NAMES):
        item = create_button(
            packs,
            modpack_name,
            lambda selected=modpack_name: on_select(selected, safe_mode.get()),
            variant="primary" if index == 0 else "secondary",
        )
        item.grid(row=index, column=0, sticky="ew", pady=(0 if index == 0 else 12, 0))

    if show_safe_mode:
        safe_check = tk.Checkbutton(
            center,
            text="Safe mode",
            variable=safe_mode,
            bg=PALETTE["bg"],
            fg=PALETTE["text"],
            activebackground=PALETTE["bg"],
            activeforeground=PALETTE["text"],
            selectcolor=PALETTE["surface"],
            font=(GUI_FONT_SEMIBOLD, 11),
        )
        safe_check.grid(row=2, column=0, pady=(18, 0))

    back = create_button(center, "Retour", on_back, variant="secondary")
    back.grid(row=3 if show_safe_mode else 2, column=0, pady=(18, 0))

    return screen
