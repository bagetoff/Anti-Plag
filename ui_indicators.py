import tkinter as tk


class RoundedProgressBar(tk.Canvas):
    def __init__(self, parent, height=12, bg_color="#ffffff", border_color="#dadce0",
                 fill_color="#1a73e8", **kwargs):
        parent_bg = parent["bg"] if "bg" in parent.keys() else "#f8f9fa"
        super().__init__(parent, height=height, bg=parent_bg, highlightthickness=0, bd=0, **kwargs)
        self.bar_height = height
        self.bg_color = bg_color
        self.border_color = border_color
        self.fill_color = fill_color
        self._value = 0

        self.bind("<Configure>", self._redraw)

    def __setitem__(self, key, value):
        if key == "value":
            self._value = max(0, min(100, float(value)))
            self._redraw()
        else:
            super().__setitem__(key, value)

    def __getitem__(self, key):
        if key == "value":
            return self._value
        return super().__getitem__(key)

    def _redraw(self, event=None):
        self.delete("all")
        w = self.winfo_width()
        h = self.bar_height
        if w <= h:
            return

        cy = h / 2.0
        r_outer = h / 2.0

        self.create_line(
            r_outer, cy, w - r_outer, cy,
            width=h, fill=self.border_color, capstyle=tk.ROUND
        )

        self.create_line(
            r_outer, cy, w - r_outer, cy,
            width=h - 2, fill=self.bg_color, capstyle=tk.ROUND
        )

        if self._value > 0:
            avail_w = w - h
            fill_end = r_outer + avail_w * (self._value / 100.0)
            self.create_line(
                r_outer, cy, fill_end, cy,
                width=h - 2, fill=self.fill_color, capstyle=tk.ROUND
            )


class ColorPillBadge(tk.Canvas):
    def __init__(self, parent, color="#9e4a10", width=24, height=12, **kwargs):
        parent_bg = parent["bg"] if "bg" in parent.keys() else "#f8f9fa"
        super().__init__(parent, width=width, height=height, bg=parent_bg, highlightthickness=0, bd=0, **kwargs)
        self.color = color
        self.pill_w = width
        self.pill_h = height
        self.bind("<Configure>", self._redraw)

    def _redraw(self, event=None):
        self.delete("all")
        r = self.pill_h / 2.0
        cy = self.pill_h / 2.0
        self.create_line(r, cy, self.pill_w - r, cy, width=self.pill_h, fill=self.color, capstyle=tk.ROUND)