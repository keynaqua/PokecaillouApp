import tkinter as tk
import threading
import queue
from tkinter import messagebox

log_queue = queue.Queue()


def _hidden_root():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
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


def start_gui(run_func):
    root = tk.Tk()
    root.title("Pokecaillou Installer")
    root.geometry("900x550")
    root.configure(bg="#1e1e1e")

    container = tk.Frame(root, bg="#1e1e1e")
    container.pack(fill="both", expand=True, padx=10, pady=10)

    log_frame = tk.Frame(container, bg="#1e1e1e")
    log_frame.pack(fill="both", expand=True)

    bottom_frame = tk.Frame(container, bg="#1e1e1e", height=40)
    bottom_frame.pack(fill="x")

    title = tk.Label(
        log_frame,
        text="Installation en cours...",
        bg="#1e1e1e",
        fg="#cccccc",
        font=("Segoe UI", 11, "bold")
    )
    title.pack(anchor="w", pady=(0, 5))

    text_frame = tk.Frame(log_frame, bg="#111111", bd=0)
    text_frame.pack(fill="both", expand=True)

    log_box = tk.Text(
        text_frame,
        wrap=tk.WORD,
        bg="#111111",
        fg="#eeeeee",
        insertbackground="white",
        font=("Consolas", 10),
        relief="flat",
        padx=10,
        pady=10,
        borderwidth=0,
        highlightthickness=0
    )
    log_box.pack(fill="both", expand=True)
    log_box.config(state="disabled")

    log_box.tag_config("red", foreground="#ff4c4c")
    log_box.tag_config("green", foreground="#4cff4c")
    log_box.tag_config("cyan", foreground="#4cc9ff")
    log_box.tag_config("yellow", foreground="#ffd166")
    log_box.tag_config("magenta", foreground="#ff66cc")
    log_box.tag_config("default", foreground="#eeeeee")

    progress_bg = tk.Frame(bottom_frame, bg="#2a2a2a", height=20, bd=0, highlightthickness=0)
    progress_bg.pack(fill="x", padx=5, pady=10)

    progress_bar = tk.Frame(progress_bg, bg="#4cc9ff", height=20, width=0, bd=0)
    progress_bar.pack(side="left")

    progress_value = {"value": 0}

    def set_progress(percent):
        progress_value["value"] = percent
        root.update_idletasks()
        width = progress_bg.winfo_width()
        progress_bar.config(width=int(width * percent / 100))

    def process_logs():
        while not log_queue.empty():
            data = log_queue.get()

            if data[0] == "clear":
                log_box.config(state="normal")
                log_box.delete("1.0", tk.END)
                log_box.config(state="disabled")

            elif data[0] == "log":
                _, msg, tag = data
                log_box.config(state="normal")
                log_box.insert(tk.END, msg + "\n", tag)
                log_box.config(state="disabled")
                log_box.see(tk.END)

            elif data[0] == "progress":
                _, value = data
                set_progress(value)

            elif data[0] == "done":
                _, status = data

                if status == "success":
                    title.config(text="Installation terminée")
                    log_box.config(state="normal")
                    log_box.insert(tk.END, "\n✅ Installation terminée avec succès\n", "green")
                    log_box.config(state="disabled")
                    log_box.see(tk.END)
                    root.after(1200, root.destroy)

                elif status == "error":
                    title.config(text="Erreur lors de l'installation")
                    log_box.config(state="normal")
                    log_box.insert(tk.END, "\n❌ Installation échouée\n", "red")
                    log_box.config(state="disabled")
                    log_box.see(tk.END)

        root.after(50, process_logs)

    def run_thread():
        try:
            run_func()
            log_queue.put(("done", "success"))
        except Exception as e:
            log_queue.put(("log", f"❌ {e}", "red"))
            log_queue.put(("done", "error"))

    threading.Thread(target=run_thread, daemon=True).start()

    process_logs()
    root.mainloop()
