import tkinter as tk
from tkinter import messagebox

from config import GUI_MESSAGEBOX_TOPMOST


def _hidden_root():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", GUI_MESSAGEBOX_TOPMOST)
    return root


def ask_update_confirmation(title: str, message: str) -> bool:
    root = _hidden_root()
    try:
        return messagebox.askokcancel(title, message, parent=root)
    finally:
        root.destroy()


def show_info_dialog(title: str, message: str) -> None:
    root = _hidden_root()
    try:
        messagebox.showinfo(title, message, parent=root)
    finally:
        root.destroy()


def show_error_dialog(title: str, message: str) -> None:
    root = _hidden_root()
    try:
        messagebox.showerror(title, message, parent=root)
    finally:
        root.destroy()
