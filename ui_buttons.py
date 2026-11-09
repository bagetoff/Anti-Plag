import tkinter as tk
from ui_frames import draw_round_rect


class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command=None, bg_color="#e8eaed", hover_color="#dadce0",
                 text_color="#202124", font=("Segoe UI", 9, "bold"), radius=15, **kwargs):
        parent_bg = parent["bg"] if "bg" in parent.keys() else "#f8f9fa"
        super().__init__(parent, bg=parent_bg, highlightthickness=0, bd=0, **kwargs)
        self.command = command
        self.text = text
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.cur_bg = bg_color
        self.font = font
        self.radius = radius
        self._state = tk.NORMAL

        self.bind("<Configure>", self._redraw)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _redraw(self, event=None):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1 or h <= 1:
            return

        fill = "#f1f3f4" if self._state == tk.DISABLED else self.cur_bg
        fg = "#9aa0a6" if self._state == tk.DISABLED else self.text_color

        draw_round_rect(self, 1, 1, w - 1, h - 1, self.radius, fill=fill, outline="")
        self.create_text(w // 2, h // 2, text=self.text, fill=fg, font=self.font)

    def _on_enter(self, e):
        if self._state == tk.NORMAL:
            self.cur_bg = self.hover_color
            self._redraw()

    def _on_leave(self, e):
        if self._state == tk.NORMAL:
            self.cur_bg = self.bg_color
            self._redraw()

    def _on_click(self, e):
        if self._state == tk.NORMAL and self.command:
            self.command()

    def configure(self, **kwargs):
        if "state" in kwargs:
            self._state = kwargs.pop("state")
        if "text" in kwargs:
            self.text = kwargs.pop("text")
        super().configure(**kwargs)
        self._redraw()

    def set_text(self, text):
        self.text = text
        self._redraw()