import tkinter as tk

from ui_frames import RoundedFrame


class ResultsPanel(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f8f9fa")
        self._build_ui()

    def _build_ui(self):
        self.score_label = tk.Label(
            self,
            text="-- %",
            font=("Segoe UI", 34, "bold"),
            bg="#f8f9fa",
            fg="#5f6368"
        )
        self.score_label.pack(anchor="center", pady=(2, 8))

        self.criteria_frame = tk.Frame(self, bg="#f8f9fa")
        self.criteria_frame.pack(fill=tk.X)

        self.empty_label = tk.Label(
            self.criteria_frame,
            text="Загрузите файлы или вставьте код, после чего запустите проверку",
            font=("Segoe UI", 10),
            bg="#f8f9fa",
            fg="#5f6368"
        )
        self.empty_label.pack(anchor="center", pady=6)

    def clear_criteria(self):
        for widget in self.criteria_frame.winfo_children():
            widget.destroy()
        for col in range(3):
            self.criteria_frame.columnconfigure(col, weight=0, uniform="")
        self.empty_label = tk.Label(self.criteria_frame, font=("Segoe UI", 10), bg="#f8f9fa")

    def reset(self, message: str):
        self.score_label.configure(text="-- %", fg="#5f6368")
        self.clear_criteria()
        self.empty_label.configure(text=message, fg="#5f6368")
        self.empty_label.pack(anchor="center", pady=6)

    def show_results(self, result: dict):
        pct = result.get("percent", 0)
        self.score_label.configure(text=f"{pct}%")

        if pct < 30:
            color = "#1e8e3e"
        elif pct < 60:
            color = "#f9ab00"
        else:
            color = "#d93025"

        self.score_label.configure(fg=color)
        self.clear_criteria()

        for idx, c in enumerate(result.get("criteria", [])):
            self.criteria_frame.columnconfigure(idx, weight=1, uniform="crit")
            padx = (0, 6) if idx == 0 else ((6, 6) if idx == 1 else (6, 0))

            card = RoundedFrame(
                self.criteria_frame,
                bg_color="#ffffff",
                border_color="#dadce0",
                radius=14,
                height=104,
                inner_pad=12
            )
            card.grid(row=0, column=idx, sticky="nsew", padx=padx, pady=2)

            val_str = f"{c['value']}%" if c.get("value") is not None else "--%"
            tk.Label(
                card.inner_frame,
                text=f"{c['name']}: {val_str}",
                font=("Segoe UI", 10, "bold"),
                bg="#ffffff",
                fg="#202124",
                anchor="w",
                justify=tk.LEFT
            ).pack(fill=tk.X, pady=(0, 4))

            note_lbl = tk.Label(
                card.inner_frame,
                text=c["note"],
                font=("Segoe UI", 9),
                bg="#ffffff",
                fg="#5f6368",
                anchor="w",
                justify=tk.LEFT,
                wraplength=260
            )
            note_lbl.pack(fill=tk.X)

            card.inner_frame.bind(
                "<Configure>",
                lambda e, lbl=note_lbl: lbl.configure(wraplength=max(120, e.width - 8))
            )