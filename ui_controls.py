import tkinter as tk

from ui_buttons import RoundedButton
from ui_indicators import RoundedProgressBar


class ControlPanel(tk.Frame):
    def __init__(self, parent, on_start, on_pause, on_cancel):
        super().__init__(parent, bg="#f8f9fa")
        self.on_start = on_start
        self.on_pause = on_pause
        self.on_cancel = on_cancel

        self._build_ui()

    def _build_ui(self):
        btn_row = tk.Frame(self, bg="#f8f9fa")
        btn_row.pack(fill=tk.X, pady=(0, 10))

        self.start_btn = RoundedButton(
            btn_row,
            text="Запустить проверку",
            command=self.on_start,
            bg_color="#1a73e8",
            hover_color="#1557b0",
            text_color="#ffffff",
            width=165,
            height=36,
            radius=18
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.pause_btn = RoundedButton(
            btn_row,
            text="Пауза",
            command=self.on_pause,
            bg_color="#e8eaed",
            hover_color="#dadce0",
            text_color="#202124",
            width=110,
            height=36,
            radius=18
        )
        self.pause_btn.configure(state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.cancel_btn = RoundedButton(
            btn_row,
            text="Отмена",
            command=self.on_cancel,
            bg_color="#e8eaed",
            hover_color="#dadce0",
            text_color="#202124",
            width=100,
            height=36,
            radius=18
        )
        self.cancel_btn.configure(state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT)

        self.progress_label = tk.Label(
            btn_row,
            text="Готов",
            font=("Segoe UI", 9),
            bg="#f8f9fa",
            fg="#5f6368"
        )
        self.progress_label.pack(side=tk.RIGHT, padx=4)

        self.progress_bar = RoundedProgressBar(self, height=12)
        self.progress_bar.pack(fill=tk.X)

    def set_running_state(self):
        self.start_btn.configure(state=tk.DISABLED)
        self.pause_btn.configure(state=tk.NORMAL)
        self.pause_btn.set_text("Пауза")
        self.cancel_btn.configure(state=tk.NORMAL)
        self.progress_bar["value"] = 0
        self.progress_label.configure(text="Запуск процесса...")

    def set_paused_state(self, is_paused: bool):
        if is_paused:
            self.pause_btn.set_text("Возобновить")
            self.progress_label.configure(text="Анализ приостановлен")
        else:
            self.pause_btn.set_text("Пауза")
            self.progress_label.configure(text="Продолжение работы...")

    def set_idle_state(self, status_text: str | None = None):
        self.start_btn.configure(state=tk.NORMAL)
        self.pause_btn.configure(state=tk.DISABLED)
        self.pause_btn.set_text("Пауза")
        self.cancel_btn.configure(state=tk.DISABLED)
        if status_text is not None:
            self.progress_label.configure(text=status_text)

    def update_progress(self, pct: int, label: str):
        self.progress_bar["value"] = pct
        self.progress_label.configure(text=f"{label} ({pct}%)")

    def reset_progress(self, status_text: str):
        self.progress_bar["value"] = 0
        self.progress_label.configure(text=status_text)