import tkinter as tk

from config import GUI_FONT, GUI_FONT_SEMIBOLD, PALETTE
from gui.components import create_button
from uninstall import UninstallMode


CLASSIC_DESCRIPTION = (
    "Supprime les mods, resourcepacks et shaderpacks declares dans les manifests. "
    "Les saves, options, logs et configs joueur restent dans le dossier."
)
FULL_DESCRIPTION = (
    "Supprime entierement le dossier du modpack et retire son profil du launcher. "
    "Les saves et settings de ce modpack sont supprimes avec le dossier."
)


def build_uninstall_options_screen(parent, modpack_name: str, on_select, on_back):
    screen = tk.Frame(parent, bg=PALETTE["bg"])
    screen.grid(row=0, column=0, sticky="nsew")

    center = tk.Frame(screen, bg=PALETTE["bg"])
    center.place(relx=0.5, rely=0.5, anchor="center")
    center.grid_columnconfigure(0, weight=1)

    tk.Label(
        center,
        text=f"Desinstaller {modpack_name}",
        bg=PALETTE["bg"],
        fg=PALETTE["text"],
        font=(GUI_FONT_SEMIBOLD, 32),
    ).grid(row=0, column=0, pady=(0, 24))

    options = tk.Frame(
        center,
        bg=PALETTE["surface"],
        highlightbackground=PALETTE["border"],
        highlightthickness=1,
        padx=32,
        pady=28,
        width=520,
        height=270,
    )
    options.grid(row=1, column=0)
    options.grid_columnconfigure(0, weight=1, minsize=380)
    options.grid_propagate(False)

    description = tk.Label(
        options,
        text="Survole une option pour voir ce qui sera supprime.",
        bg=PALETTE["surface"],
        fg=PALETTE["muted"],
        font=(GUI_FONT, 10),
        wraplength=390,
        justify="left",
        anchor="w",
    )
    description.grid(row=2, column=0, sticky="ew", pady=(18, 0))

    def attach_description(button, text: str):
        button.bind("<Enter>", lambda event: description.config(text=text), add="+")
        button.bind(
            "<Leave>",
            lambda event: description.config(
                text="Survole une option pour voir ce qui sera supprime."
            ),
            add="+",
        )

    classic = create_button(
        options,
        "Desinstallation classique",
        lambda: on_select(UninstallMode.CLASSIC),
        variant="primary",
    )
    classic.grid(row=0, column=0, sticky="ew")
    attach_description(classic, CLASSIC_DESCRIPTION)

    full = create_button(
        options,
        "Supprimer le dossier",
        lambda: on_select(UninstallMode.FULL),
        variant="danger",
    )
    full.grid(row=1, column=0, sticky="ew", pady=(12, 0))
    attach_description(full, FULL_DESCRIPTION)

    back = create_button(center, "Retour", on_back, variant="secondary")
    back.grid(row=2, column=0, pady=(18, 0))

    return screen
