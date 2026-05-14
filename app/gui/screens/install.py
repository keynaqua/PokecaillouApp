import tkinter as tk

from config import GUI_FONT, GUI_FONT_SEMIBOLD, GUI_MONO_FONT, PALETTE
from gui.core.state import log_queue


class InstallationScreen:
    def __init__(
        self,
        parent,
        root,
        state,
        modpack_name: str,
        on_open_launcher,
        operation: str = "install",
    ):
        self.parent = parent
        self.root = root
        self.state = state
        self.modpack_name = modpack_name
        self.on_open_launcher = on_open_launcher
        self.operation = operation

        self.screen = None
        self.percent_label = None
        self.progress_track = None
        self.progress_fill = None
        self.status_label = None
        self.helper_label = None
        self.footer_message = None
        self.launch_button = None
        self.log_box = None

    def render(self):
        self.screen = tk.Frame(self.parent, bg=PALETTE["bg"])
        self.screen.grid(row=0, column=0, sticky="nsew", padx=22, pady=22)
        self.screen.grid_columnconfigure(0, weight=1)
        self.screen.grid_rowconfigure(1, weight=1)

        self._render_header()
        self._render_content()
        self._render_footer()
        self._bind_resize()

    def _render_header(self):
        header = tk.Frame(
            self.screen,
            bg=PALETTE["surface"],
            highlightbackground=PALETTE["border"],
            highlightthickness=1,
        )
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header.grid_columnconfigure(0, weight=1)

        tk.Label(
            header,
            text="INSTALLATEUR MINECRAFT" if self.operation == "install" else "DESINSTALLATEUR MINECRAFT",
            bg=PALETTE["surface"],
            fg=PALETTE["muted"],
            font=(GUI_FONT_SEMIBOLD, 9),
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(16, 2))

        tk.Label(
            header,
            text=f"Installation de {self.modpack_name}"
            if self.operation == "install"
            else f"Desinstallation de {self.modpack_name}",
            bg=PALETTE["surface"],
            fg=PALETTE["text"],
            font=(GUI_FONT_SEMIBOLD, 22),
        ).grid(row=1, column=0, sticky="w", padx=18)

        tk.Label(
            header,
            text="Installation, mise a jour et validation de l'environnement de jeu."
            if self.operation == "install"
            else "Suppression des fichiers selectionnes pour ce modpack.",
            bg=PALETTE["surface"],
            fg=PALETTE["muted"],
            font=(GUI_FONT, 10),
        ).grid(row=2, column=0, sticky="w", padx=18, pady=(4, 14))

    def _render_content(self):
        content = tk.Frame(self.screen, bg=PALETTE["bg"])
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)

        self._render_status(content)
        self._render_log(content)

    def _render_status(self, parent):
        status_card = tk.Frame(
            parent,
            bg=PALETTE["surface_alt"],
            highlightbackground=PALETTE["border"],
            highlightthickness=1,
            padx=16,
            pady=14,
        )
        status_card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        status_card.grid_columnconfigure(0, weight=1)

        status_row = tk.Frame(status_card, bg=PALETTE["surface_alt"])
        status_row.grid(row=0, column=0, sticky="ew")
        status_row.grid_columnconfigure(0, weight=1)

        self.status_label = tk.Label(
            status_row,
            text="Installation en cours..."
            if self.operation == "install"
            else "Desinstallation en cours...",
            bg=PALETTE["surface_alt"],
            fg=PALETTE["text"],
            font=(GUI_FONT_SEMIBOLD, 12),
        )
        self.status_label.grid(row=0, column=0, sticky="w")

        self.percent_label = tk.Label(
            status_row,
            text="0%",
            bg=PALETTE["surface_alt"],
            fg=PALETTE["accent"],
            font=(GUI_FONT_SEMIBOLD, 11),
        )
        self.percent_label.grid(row=0, column=1, sticky="e")

        self.progress_track = tk.Frame(status_card, bg=PALETTE["accent_dark"], height=12)
        self.progress_track.grid(row=1, column=0, sticky="ew", pady=(12, 10))
        self.progress_track.grid_propagate(False)

        self.progress_fill = tk.Frame(self.progress_track, bg=PALETTE["accent"], width=0, height=12)
        self.progress_fill.place(x=0, y=0, relheight=1.0)

        self.helper_label = tk.Label(
            status_card,
            text="Le launcher restera ferme jusqu'a la fin de l'installation."
            if self.operation == "install"
            else "Ne ferme pas l'application pendant la suppression des fichiers.",
            bg=PALETTE["surface_alt"],
            fg=PALETTE["muted"],
            font=(GUI_FONT, 9),
        )
        self.helper_label.grid(row=2, column=0, sticky="w")

    def _render_log(self, parent):
        log_card = tk.Frame(
            parent,
            bg=PALETTE["surface"],
            highlightbackground=PALETTE["border"],
            highlightthickness=1,
        )
        log_card.grid(row=1, column=0, sticky="nsew")
        log_card.grid_columnconfigure(0, weight=1)
        log_card.grid_rowconfigure(1, weight=1)

        tk.Label(
            log_card,
            text="Journal d'installation"
            if self.operation == "install"
            else "Journal de desinstallation",
            bg=PALETTE["surface"],
            fg=PALETTE["text"],
            font=(GUI_FONT_SEMIBOLD, 11),
            anchor="w",
            padx=16,
            pady=12,
        ).grid(row=0, column=0, sticky="ew")

        text_wrap = tk.Frame(log_card, bg=PALETTE["surface"])
        text_wrap.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        text_wrap.grid_columnconfigure(0, weight=1)
        text_wrap.grid_rowconfigure(0, weight=1)

        self.log_box = tk.Text(
            text_wrap,
            wrap=tk.WORD,
            bg=PALETTE["log_bg"],
            fg=PALETTE["text"],
            insertbackground=PALETTE["text"],
            font=(GUI_MONO_FONT, 10),
            relief="flat",
            padx=14,
            pady=14,
            borderwidth=0,
            highlightthickness=0,
            spacing1=2,
            spacing3=2,
        )
        self.log_box.grid(row=0, column=0, sticky="nsew")
        self.log_box.config(state="disabled")

        scrollbar = tk.Scrollbar(text_wrap, orient="vertical", command=self.log_box.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_box.configure(yscrollcommand=scrollbar.set)

        self.log_box.tag_config("red", foreground=PALETTE["error"])
        self.log_box.tag_config("green", foreground=PALETTE["success"])
        self.log_box.tag_config("cyan", foreground=PALETTE["accent"])
        self.log_box.tag_config("yellow", foreground=PALETTE["warning"])
        self.log_box.tag_config("magenta", foreground=PALETTE["magenta"])
        self.log_box.tag_config("default", foreground=PALETTE["text"])

    def _render_footer(self):
        footer = tk.Frame(
            self.screen,
            bg=PALETTE["surface"],
            highlightbackground=PALETTE["border"],
            highlightthickness=1,
            padx=16,
            pady=14,
        )
        footer.grid(row=2, column=0, sticky="ew", pady=(14, 0))
        footer.grid_columnconfigure(0, weight=1)

        self.footer_message = tk.Label(
            footer,
            text="Le bouton d'ouverture du launcher s'activera quand l'installation sera validee."
            if self.operation == "install"
            else "Le bouton de fermeture s'activera quand la desinstallation sera terminee.",
            bg=PALETTE["surface"],
            fg=PALETTE["muted"],
            font=(GUI_FONT, 9),
        )
        self.footer_message.grid(row=0, column=0, sticky="w")

        self.launch_button = tk.Button(
            footer,
            text="Lancer Minecraft" if self.operation == "install" else "Fermer",
            command=self.on_open_launcher,
            state="disabled",
            bg=PALETTE["button_disabled"],
            fg=PALETTE["button_disabled_text"],
            activebackground=PALETTE["button_hover"],
            activeforeground=PALETTE["text"],
            disabledforeground=PALETTE["button_disabled_text"],
            relief="flat",
            bd=0,
            padx=18,
            pady=10,
            font=(GUI_FONT_SEMIBOLD, 10),
            cursor="arrow",
        )
        self.launch_button.grid(row=0, column=1, sticky="e", padx=(12, 0))
        self.launch_button.bind("<Enter>", self._on_launch_enter)
        self.launch_button.bind("<Leave>", self._on_launch_leave)

    def _bind_resize(self):
        self.root.after(100, lambda: self.set_progress(self.state["progress"]))
        self.root.bind("<Configure>", lambda _event: self.set_progress(self.state["progress"]))

    def _on_launch_enter(self, _event):
        if self.launch_button["state"] == "normal":
            self.launch_button.config(bg=PALETTE["button_hover"])

    def _on_launch_leave(self, _event):
        if self.launch_button["state"] == "normal":
            self.launch_button.config(bg=PALETTE["button"])

    def set_progress(self, percent):
        percent = max(0, min(100, int(percent)))
        self.state["progress"] = percent
        self.percent_label.config(text=f"{percent}%")
        self.root.update_idletasks()

        width = max(self.progress_track.winfo_width(), 1)
        self.progress_fill.place_configure(width=int(width * percent / 100))

    def set_success_state(self):
        self.state["status"] = "success"
        self.status_label.config(
            text="Installation terminee"
            if self.operation == "install"
            else "Desinstallation terminee",
            fg=PALETTE["success"],
        )
        self.helper_label.config(
            text="Tous les controles sont passes. Tu peux lancer Minecraft quand tu veux."
            if self.operation == "install"
            else "La desinstallation demandee est terminee.",
            fg=PALETTE["success"],
        )
        self.progress_track.config(bg=PALETTE["success_dark"])
        self.progress_fill.config(bg=PALETTE["success"])
        self.footer_message.config(
            text="Aucune erreur detectee. Le launcher Minecraft est pret a etre ouvert."
            if self.operation == "install"
            else "Aucune erreur detectee. Tu peux fermer l'application.",
            fg=PALETTE["text"],
        )
        self.launch_button.config(
            state="normal",
            bg=PALETTE["button"],
            fg=PALETTE["text"],
            cursor="hand2",
        )

    def set_error_state(self):
        self.state["status"] = "error"
        self.status_label.config(
            text="Installation echouee"
            if self.operation == "install"
            else "Desinstallation echouee",
            fg=PALETTE["error"],
        )
        self.helper_label.config(
            text="Corrige l'erreur indiquee dans le journal avant de relancer l'installation."
            if self.operation == "install"
            else "Lis l'erreur indiquee dans le journal avant de reessayer.",
            fg=PALETTE["error"],
        )
        self.progress_track.config(bg=PALETTE["error_dark"])
        self.progress_fill.config(bg=PALETTE["error"])
        if self.operation == "install":
            self.footer_message.config(
                text="Le launcher reste bloque tant que l'installation n'est pas terminee sans erreur.",
                fg=PALETTE["muted"],
            )
            self.launch_button.config(
                state="disabled",
                bg=PALETTE["button_disabled"],
                fg=PALETTE["button_disabled_text"],
                cursor="arrow",
            )
        else:
            self.footer_message.config(
                text="Une erreur est survenue. Tu peux fermer l'application et reessayer.",
                fg=PALETTE["text"],
            )
            self.launch_button.config(
                state="normal",
                bg=PALETTE["button"],
                fg=PALETTE["text"],
                cursor="hand2",
            )

    def append_log(self, message: str, tag: str):
        self.log_box.config(state="normal")
        self.log_box.insert(tk.END, message + "\n", tag)
        self.log_box.config(state="disabled")
        self.log_box.see(tk.END)

    def process_logs(self):
        while not log_queue.empty():
            data = log_queue.get()

            if data[0] == "clear":
                self.log_box.config(state="normal")
                self.log_box.delete("1.0", tk.END)
                self.log_box.config(state="disabled")

            elif data[0] == "log":
                _, msg, tag = data
                self.append_log(msg, tag)

            elif data[0] == "progress":
                _, value = data
                self.set_progress(value)

            elif data[0] == "done":
                _, status = data
                self.handle_done(status)

        if self.screen and self.screen.winfo_exists():
            self.root.after(50, self.process_logs)

    def handle_done(self, status: str):
        if status == "success":
            self.set_progress(100)
            self.set_success_state()
            self.append_log(
                "\nInstallation terminee avec succes. Clique sur le bouton pour ouvrir Minecraft."
                if self.operation == "install"
                else "\nDesinstallation terminee avec succes.",
                "green",
            )
        elif status == "error":
            self.set_error_state()
            self.append_log(
                "\nInstallation echouee."
                if self.operation == "install"
                else "\nDesinstallation echouee.",
                "red",
            )
