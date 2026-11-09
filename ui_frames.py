import tkinter as tk


def draw_round_rect(canvas: tk.Canvas, x1, y1, x2, y2, r, fill="", outline="", width=1, tags=()):
    points = [
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1,
    ]
    return canvas.create_polygon(
        points,
        smooth=True,
        fill=fill,
        outline=outline,
        width=width,
        tags=tags
    )


class RoundedFrame(tk.Canvas):
    def __init__(self, parent, bg_color="#ffffff", border_color="#dadce0", radius=16, border_width=1, inner_pad=8, **kwargs):
        parent_bg = parent["bg"] if "bg" in parent.keys() else "#f8f9fa"
        super().__init__(parent, bg=parent_bg, highlightthickness=0, bd=0, **kwargs)
        self.bg_color = bg_color
        self.border_color = border_color
        self.radius = radius
        self.border_width = border_width
        self.inner_pad = inner_pad
        self.inner_frame = tk.Frame(self, bg=bg_color)
        self.window_id = self.create_window((0, 0), window=self.inner_frame, anchor="nw")

        self.bind("<Configure>", self._redraw)

    def set_colors(self, bg_color, border_color):
        self.bg_color = bg_color
        self.border_color = border_color
        self.inner_frame.configure(bg=bg_color)
        self._redraw()

    def _redraw(self, event=None):
        self.delete("bg_shape")
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 2 or h <= 2:
            return
        pad = self.border_width
        draw_round_rect(
            self, pad, pad, w - pad, h - pad, self.radius,
            fill=self.bg_color, outline=self.border_color, width=self.border_width, tags="bg_shape"
        )
        self.tag_lower("bg_shape")
        ip = self.inner_pad
        self.coords(self.window_id, ip, ip)
        self.itemconfigure(self.window_id, width=max(1, w - ip * 2), height=max(1, h - ip * 2))