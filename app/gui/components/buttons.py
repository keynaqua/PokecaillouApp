import tkinter as tk

from config import GUI_FONT_SEMIBOLD, PALETTE


def create_button(parent, text: str, command, variant: str = "primary"):
    if variant == "primary":
        bg = PALETTE["button"]
        hover = PALETTE["button_hover"]
    elif variant == "danger":
        bg = PALETTE["error_dark"]
        hover = PALETTE["error"]
    else:
        bg = PALETTE["button_alt"]
        hover = PALETTE["button_alt_hover"]

    widget = tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg,
        fg=PALETTE["text"],
        activebackground=hover,
        activeforeground=PALETTE["text"],
        relief="flat",
        bd=0,
        padx=28,
        pady=16,
        font=(GUI_FONT_SEMIBOLD, 13),
        cursor="hand2",
    )
    widget.bind("<Enter>", lambda _event: widget.config(bg=hover))
    widget.bind("<Leave>", lambda _event: widget.config(bg=bg))
    return widget
