import queue
import threading
import tkinter as tk
from tkinter import messagebox

from utils.launcher import launch_minecraft_launcher

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
    root.geometry("960x620")
    root.minsize(820, 540)
    root.configure(bg="#0b1220")

    ui_state = {
        "status": "running",
        "progress": 0,
    }

    palette = {
        "bg": "#0b1220",
        "panel": "#111a2b",
        "panel_alt": "#162235",
        "border": "#24344f",
        "text": "#ecf3ff",
        "muted": "#9cb0ce",
        "accent": "#58c4ff",
        "accent_soft": "#153756",
        "success": "#43d18d",
        "success_soft": "#153b2c",
        "error": "#ff6b81",
        "error_soft": "#3d1f2b",
        "warning": "#ffd166",
        "log_bg": "#09111d",
        "button": "#2a85ff",
        "button_hover": "#4a98ff",
        "button_disabled": "#273246",
        "button_disabled_text": "#7f90ae",
    }

    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)

    outer = tk.Frame(root, bg=palette["bg"])
    outer.grid(sticky="nsew", padx=18, pady=18)
    outer.grid_columnconfigure(0, weight=1)
    outer.grid_rowconfigure(1, weight=1)

    header = tk.Frame(outer, bg=palette["panel"], highlightbackground=palette["border"], highlightthickness=1)
    header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
    header.grid_columnconfigure(0, weight=1)

    eyebrow = tk.Label(
        header,
        text="INSTALLATEUR MINECRAFT",
        bg=palette["panel"],
        fg=palette["muted"],
        font=("Segoe UI Semibold", 9),
        pady=0,
    )
    eyebrow.grid(row=0, column=0, sticky="w", padx=18, pady=(16, 2))

    title = tk.Label(
        header,
        text="Préparation de l'instance Pokecaillou",
        bg=palette["panel"],
        fg=palette["text"],
        font=("Segoe UI Semibold", 18),
    )
    title.grid(row=1, column=0, sticky="w", padx=18)

    subtitle = tk.Label(
        header,
        text="Installation, mise à jour et validation de l'environnement de jeu.",
        bg=palette["panel"],
        fg=palette["muted"],
        font=("Segoe UI", 10),
    )
    subtitle.grid(row=2, column=0, sticky="w", padx=18, pady=(4, 14))

    content = tk.Frame(outer, bg=palette["bg"])
    content.grid(row=1, column=0, sticky="nsew")
    content.grid_columnconfigure(0, weight=1)
    content.grid_rowconfigure(1, weight=1)

    status_card = tk.Frame(
        content,
        bg=palette["panel_alt"],
        highlightbackground=palette["border"],
        highlightthickness=1,
        padx=16,
        pady=14,
    )
    status_card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
    status_card.grid_columnconfigure(0, weight=1)

    status_row = tk.Frame(status_card, bg=palette["panel_alt"])
    status_row.grid(row=0, column=0, sticky="ew")
    status_row.grid_columnconfigure(0, weight=1)

    status_label = tk.Label(
        status_row,
        text="Installation en cours...",
        bg=palette["panel_alt"],
        fg=palette["text"],
        font=("Segoe UI Semibold", 12),
    )
    status_label.grid(row=0, column=0, sticky="w")

    percent_label = tk.Label(
        status_row,
        text="0%",
        bg=palette["panel_alt"],
        fg=palette["accent"],
        font=("Segoe UI Semibold", 11),
    )
    percent_label.grid(row=0, column=1, sticky="e")

    progress_track = tk.Frame(status_card, bg=palette["accent_soft"], height=12)
    progress_track.grid(row=1, column=0, sticky="ew", pady=(12, 10))
    progress_track.grid_propagate(False)

    progress_fill = tk.Frame(progress_track, bg=palette["accent"], width=0, height=12)
    progress_fill.place(x=0, y=0, relheight=1.0)

    helper_label = tk.Label(
        status_card,
        text="Le launcher restera fermé jusqu'à la fin de l'installation.",
        bg=palette["panel_alt"],
        fg=palette["muted"],
        font=("Segoe UI", 9),
    )
    helper_label.grid(row=2, column=0, sticky="w")

    log_card = tk.Frame(
        content,
        bg=palette["panel"],
        highlightbackground=palette["border"],
        highlightthickness=1,
    )
    log_card.grid(row=1, column=0, sticky="nsew")
    log_card.grid_columnconfigure(0, weight=1)
    log_card.grid_rowconfigure(1, weight=1)

    log_title = tk.Label(
        log_card,
        text="Journal d'installation",
        bg=palette["panel"],
        fg=palette["text"],
        font=("Segoe UI Semibold", 11),
        anchor="w",
        padx=16,
        pady=12,
    )
    log_title.grid(row=0, column=0, sticky="ew")

    text_wrap = tk.Frame(log_card, bg=palette["panel"])
    text_wrap.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
    text_wrap.grid_columnconfigure(0, weight=1)
    text_wrap.grid_rowconfigure(0, weight=1)

    log_box = tk.Text(
        text_wrap,
        wrap=tk.WORD,
        bg=palette["log_bg"],
        fg=palette["text"],
        insertbackground=palette["text"],
        font=("Cascadia Mono", 10),
        relief="flat",
        padx=14,
        pady=14,
        borderwidth=0,
        highlightthickness=0,
        spacing1=2,
        spacing3=2,
    )
    log_box.grid(row=0, column=0, sticky="nsew")
    log_box.config(state="disabled")

    scrollbar = tk.Scrollbar(
        text_wrap,
        orient="vertical",
        command=log_box.yview,
        troughcolor=palette["panel"],
        activebackground=palette["button_hover"],
        bg=palette["panel_alt"],
    )
    scrollbar.grid(row=0, column=1, sticky="ns")
    log_box.configure(yscrollcommand=scrollbar.set)

    log_box.tag_config("red", foreground=palette["error"])
    log_box.tag_config("green", foreground=palette["success"])
    log_box.tag_config("cyan", foreground=palette["accent"])
    log_box.tag_config("yellow", foreground=palette["warning"])
    log_box.tag_config("magenta", foreground="#ff8ad8")
    log_box.tag_config("default", foreground=palette["text"])

    footer = tk.Frame(
        outer,
        bg=palette["panel"],
        highlightbackground=palette["border"],
        highlightthickness=1,
        padx=16,
        pady=14,
    )
    footer.grid(row=2, column=0, sticky="ew", pady=(14, 0))
    footer.grid_columnconfigure(0, weight=1)

    footer_message = tk.Label(
        footer,
        text="Le bouton d'ouverture du launcher s'activera quand l'installation sera validée.",
        bg=palette["panel"],
        fg=palette["muted"],
        font=("Segoe UI", 9),
    )
    footer_message.grid(row=0, column=0, sticky="w")

    launch_button = tk.Button(
        footer,
        text="Lancer Minecraft",
        state="disabled",
        bg=palette["button_disabled"],
        fg=palette["button_disabled_text"],
        activebackground=palette["button_hover"],
        activeforeground=palette["text"],
        disabledforeground=palette["button_disabled_text"],
        relief="flat",
        bd=0,
        padx=18,
        pady=10,
        font=("Segoe UI Semibold", 10),
        cursor="arrow",
    )
    launch_button.grid(row=0, column=1, sticky="e", padx=(12, 0))

    def set_progress(percent):
        percent = max(0, min(100, int(percent)))
        ui_state["progress"] = percent
        percent_label.config(text=f"{percent}%")
        root.update_idletasks()
        width = max(progress_track.winfo_width(), 1)
        progress_fill.place_configure(width=int(width * percent / 100))

    def set_running_state():
        status_label.config(text="Installation en cours...", fg=palette["text"])
        helper_label.config(
            text="Le launcher restera fermé jusqu'à la fin de l'installation.",
            fg=palette["muted"],
        )
        progress_track.config(bg=palette["accent_soft"])
        progress_fill.config(bg=palette["accent"])
        footer_message.config(
            text="Le bouton d'ouverture du launcher s'activera quand l'installation sera validée.",
            fg=palette["muted"],
        )

    def set_success_state():
        ui_state["status"] = "success"
        status_label.config(text="Installation terminée", fg=palette["success"])
        helper_label.config(
            text="Tous les contrôles sont passés. Tu peux lancer Minecraft quand tu veux.",
            fg=palette["success"],
        )
        progress_track.config(bg=palette["success_soft"])
        progress_fill.config(bg=palette["success"])
        footer_message.config(
            text="Aucune erreur détectée. Le launcher Minecraft est prêt à être ouvert.",
            fg=palette["text"],
        )
        launch_button.config(
            state="normal",
            bg=palette["button"],
            fg=palette["text"],
            cursor="hand2",
        )

    def set_error_state():
        ui_state["status"] = "error"
        status_label.config(text="Installation échouée", fg=palette["error"])
        helper_label.config(
            text="Corrige l'erreur indiquée dans le journal avant de relancer l'installation.",
            fg=palette["error"],
        )
        progress_track.config(bg=palette["error_soft"])
        progress_fill.config(bg=palette["error"])
        footer_message.config(
            text="Le launcher reste bloqué tant que l'installation n'est pas terminée sans erreur.",
            fg=palette["muted"],
        )
        launch_button.config(
            state="disabled",
            bg=palette["button_disabled"],
            fg=palette["button_disabled_text"],
            cursor="arrow",
        )

    def on_launch_click():
        if ui_state["status"] != "success":
            return

        launch_button.config(state="disabled")
        root.destroy()
        launch_minecraft_launcher()

    def on_button_enter(_event):
        if launch_button["state"] == "normal":
            launch_button.config(bg=palette["button_hover"])

    def on_button_leave(_event):
        if launch_button["state"] == "normal":
            launch_button.config(bg=palette["button"])

    launch_button.config(command=on_launch_click)
    launch_button.bind("<Enter>", on_button_enter)
    launch_button.bind("<Leave>", on_button_leave)

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
                    set_progress(100)
                    set_success_state()
                    log_box.config(state="normal")
                    log_box.insert(
                        tk.END,
                        "\nInstallation terminée avec succès. Clique sur le bouton pour ouvrir Minecraft.\n",
                        "green",
                    )
                    log_box.config(state="disabled")
                    log_box.see(tk.END)

                elif status == "error":
                    set_error_state()
                    log_box.config(state="normal")
                    log_box.insert(tk.END, "\nInstallation échouée.\n", "red")
                    log_box.config(state="disabled")
                    log_box.see(tk.END)

        root.after(50, process_logs)

    def run_thread():
        try:
            run_func()
            log_queue.put(("done", "success"))
        except Exception as exc:
            log_queue.put(("log", f"❌ {exc}", "red"))
            log_queue.put(("done", "error"))

    set_running_state()
    root.after(100, lambda: set_progress(ui_state["progress"]))
    root.bind("<Configure>", lambda _event: set_progress(ui_state["progress"]))

    threading.Thread(target=run_thread, daemon=True).start()

    process_logs()
    root.mainloop()
