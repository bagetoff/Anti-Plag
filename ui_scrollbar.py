import tkinter as tk


class ThinScrollbar(tk.Canvas):
    def __init__(self, parent, command=None, width=8, bg_color="#f8f9fa",
                 thumb_color="#c1c6cc", hover_color="#9aa0a6", **kwargs):
        super().__init__(parent, width=width, bg=bg_color, highlightthickness=0, bd=0, **kwargs)
        self.command = command
        self.bar_width = width
        self.thumb_color = thumb_color
        self.hover_color = hover_color
        self.cur_color = thumb_color

        self._first = 0.0
        self._last = 1.0
        self._drag_start_y = None
        self._drag_start_first = 0.0

        self.bind("<Configure>", self._redraw)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)

    def set(self, first, last):
        self._first = float(first)
        self._last = float(last)
        self._redraw()

    def _redraw(self, event=None):
        self.delete("all")
        if self._first <= 0.0 and self._last >= 1.0:
            return

        h = self.winfo_height()
        w = self.bar_width
        if h <= 10:
            return

        pad = 4
        track_h = h - pad * 2
        y1 = pad + self._first * track_h
        y2 = pad + self._last * track_h

        min_thumb = 28
        if y2 - y1 < min_thumb:
            y2 = min(h - pad, y1 + min_thumb)
            y1 = max(pad, y2 - min_thumb)

        cx = w / 2.0
        self.create_line(cx, y1, cx, y2, width=w - 2, fill=self.cur_color, capstyle=tk.ROUND)

    def _on_enter(self, event):
        self.cur_color = self.hover_color
        self._redraw()

    def _on_leave(self, event):
        if self._drag_start_y is None:
            self.cur_color = self.thumb_color
            self._redraw()

    def _on_press(self, event):
        h = self.winfo_height()
        pad = 4
        track_h = max(1, h - pad * 2)
        y1 = pad + self._first * track_h
        y2 = pad + self._last * track_h

        if y1 <= event.y <= y2:
            self._drag_start_y = event.y
            self._drag_start_first = self._first
        else:
            span = self._last - self._first
            target = (event.y - pad) / track_h - span / 2.0
            target = max(0.0, min(1.0 - span, target))
            if self.command:
                self.command("moveto", target)

    def _on_drag(self, event):
        if self._drag_start_y is None:
            return
        h = self.winfo_height()
        pad = 4
        track_h = max(1, h - pad * 2)
        dy = event.y - self._drag_start_y
        delta = dy / track_h
        span = self._last - self._first
        target = max(0.0, min(1.0 - span, self._drag_start_first + delta))
        if self.command:
            self.command("moveto", target)

    def _on_release(self, event):
        self._drag_start_y = None