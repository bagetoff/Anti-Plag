import tkinter as tk
from ui_frames import draw_round_rect


class RoundedDropdown(tk.Canvas):
    def __init__(self, parent, textvariable, values, command=None, width=140, height=30,
                 bg_color="#ffffff", border_color="#dadce0", hover_border="#1a73e8",
                 text_color="#202124", font=("Segoe UI", 9), radius=15, **kwargs):
        parent_bg = parent["bg"] if "bg" in parent.keys() else "#f8f9fa"
        super().__init__(parent, width=width, height=height, bg=parent_bg, highlightthickness=0, bd=0, **kwargs)
        self.textvariable = textvariable
        self.values = list(values)
        self.command = command
        self.bg_color = bg_color
        self.border_color = border_color
        self.hover_border = hover_border
        self.cur_border = border_color
        self.text_color = text_color
        self.font = font
        self.radius = radius
        self._state = tk.NORMAL
        self._popup = None

        self.textvariable.trace_add("write", lambda *args: self._redraw())

        self.bind("<Configure>", self._redraw)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._toggle_popup)

    def _redraw(self, event=None):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 2 or h <= 2:
            return

        fill = "#f1f3f4" if self._state == tk.DISABLED else self.bg_color
        fg = "#9aa0a6" if self._state == tk.DISABLED else self.text_color
        val = self.textvariable.get()
        if val == "Не выбран" and self._state != tk.DISABLED:
            fg = "#d93025"

        outline = "#dadce0" if self._state == tk.DISABLED else self.cur_border
        draw_round_rect(self, 1, 1, w - 1, h - 1, self.radius, fill=fill, outline=outline, width=1)

        self.create_text(12, h // 2, text=val, fill=fg, font=self.font, anchor="w")

        cx = w - 15
        cy = h // 2
        self.create_line(cx - 4, cy - 2, cx, cy + 2, cx + 4, cy - 2, fill=fg, width=1.5, capstyle=tk.ROUND, joinstyle=tk.ROUND)

    def _on_enter(self, event):
        if self._state == tk.NORMAL:
            self.cur_border = self.hover_border
            self._redraw()

    def _on_leave(self, event):
        if self._state == tk.NORMAL and not self._popup:
            self.cur_border = self.border_color
            self._redraw()

    def _toggle_popup(self, event=None):
        if self._state != tk.NORMAL:
            return
        if self._popup and self._popup.winfo_exists():
            self._close_popup()
        else:
            self._open_popup()

    def _open_popup(self):
        self._close_popup()
        w = self.winfo_width()
        item_h = 30
        pad = 6
        total_h = len(self.values) * item_h + pad * 2

        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 3

        self._popup = tk.Toplevel(self)
        self._popup.overrideredirect(True)
        self._popup.attributes("-topmost", True)
        self._popup.configure(bg="#f8f9fa")
        self._popup.geometry(f"{w}x{total_h}+{x}+{y}")

        canvas = tk.Canvas(self._popup, width=w, height=total_h, bg="#f8f9fa", highlightthickness=0, bd=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        draw_round_rect(canvas, 1, 1, w - 1, total_h - 1, 12, fill="#ffffff", outline="#dadce0", width=1)

        current_val = self.textvariable.get()

        for idx, item_text in enumerate(self.values):
            iy1 = pad + idx * item_h
            iy2 = iy1 + item_h

            is_selected = (item_text == current_val)
            bg_tag = f"item_bg_{idx}"
            txt_tag = f"item_txt_{idx}"

            init_fill = "#e8f0fe" if is_selected else "#ffffff"
            init_fg = "#1a73e8" if is_selected else "#202124"

            draw_round_rect(
                canvas, 5, iy1 + 1, w - 5, iy2 - 1, 8,
                fill=init_fill, outline="", tags=(bg_tag, f"row_{idx}")
            )
            canvas.create_text(
                14, (iy1 + iy2) // 2,
                text=item_text,
                fill=init_fg,
                font=("Segoe UI", 9, "bold" if is_selected else "normal"),
                anchor="w",
                tags=(txt_tag, f"row_{idx}")
            )

            def on_enter_row(e, b_tag=bg_tag, sel=is_selected):
                canvas.itemconfigure(b_tag, fill="#e8f0fe" if sel else "#f1f3f4")

            def on_leave_row(e, b_tag=bg_tag, sel=is_selected):
                canvas.itemconfigure(b_tag, fill="#e8f0fe" if sel else "#ffffff")

            def on_click_row(e, val=item_text):
                self._select_value(val)

            canvas.tag_bind(f"row_{idx}", "<Enter>", on_enter_row)
            canvas.tag_bind(f"row_{idx}", "<Leave>", on_leave_row)
            canvas.tag_bind(f"row_{idx}", "<Button-1>", on_click_row)

        self._popup.bind("<FocusOut>", lambda e: self._close_popup())
        self._popup.bind("<Escape>", lambda e: self._close_popup())
        self._popup.focus_force()

    def _select_value(self, val):
        self.textvariable.set(val)
        self._close_popup()
        if self.command:
            self.command(val)

    def _close_popup(self):
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()
        self._popup = None
        self.cur_border = self.border_color
        self._redraw()

    def configure(self, **kwargs):
        if "state" in kwargs:
            st = kwargs.pop("state")
            self._state = tk.DISABLED if st in ("disabled", tk.DISABLED) else tk.NORMAL
            if self._state == tk.DISABLED:
                self._close_popup()
        super().configure(**kwargs)
        self._redraw()