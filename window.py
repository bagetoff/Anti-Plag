import os
import random
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import compare_cpp
import compare_pas
import highlights

cpp_extension = {".cpp"}
python_extension = {".py"}
pas_extension = {".pas"}

all_supported_extensions = cpp_extension | python_extension | pas_extension


class RoundedFrame(tk.Canvas):
    def __init__(self, parent, bg_color="#ffffff", border_color="#dadce0", radius=16, border_width=1, **kwargs):
        super().__init__(parent, bg=parent["bg"] if "bg" in parent.keys() else "#f8f9fa", highlightthickness=0, **kwargs)
        self.bg_color = bg_color
        self.border_color = border_color
        self.radius = radius
        self.border_width = border_width
        self.inner_frame = tk.Frame(self, bg=bg_color)
        self.window_id = self.create_window((0, 0), window=self.inner_frame, anchor="nw")

        self.bind("<Configure>", self._redraw)

    def _draw_round_rect(self, x1, y1, x2, y2, r):
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
        return self.create_polygon(
            points,
            smooth=True,
            fill=self.bg_color,
            outline=self.border_color,
            width=self.border_width,
            tags="bg_shape"
        )

    def _redraw(self, event):
        self.delete("bg_shape")
        w, h = event.width, event.height
        pad = self.border_width
        self._draw_round_rect(pad, pad, w - pad, h - pad, self.radius)
        self.tag_lower("bg_shape")
        inner_pad = 8
        self.coords(self.window_id, inner_pad, inner_pad)
        self.itemconfigure(self.window_id, width=max(1, w - inner_pad * 2), height=max(1, h - inner_pad * 2))


class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command=None, bg_color="#e8eaed", hover_color="#dadce0",
                 text_color="#202124", font=("Segoe UI", 9, "bold"), radius=16, **kwargs):
        super().__init__(parent, bg=parent["bg"] if "bg" in parent.keys() else "#f8f9fa", highlightthickness=0, **kwargs)
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

    def _draw_round_rect(self, x1, y1, x2, y2, r, fill):
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
        return self.create_polygon(points, smooth=True, fill=fill, outline="")

    def _redraw(self, event=None):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1 or h <= 1:
            return

        fill = "#f1f3f4" if self._state == tk.DISABLED else self.cur_bg
        fg = "#9aa0a6" if self._state == tk.DISABLED else self.text_color

        self._draw_round_rect(1, 1, w - 1, h - 1, self.radius, fill)
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
        r_inner = (h - 2) / 2.0

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


class AntiPlagApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AntiPlag App")
        self.geometry("980x920")
        self.minsize(820, 520)
        self.configure(bg="#f8f9fa")

        self.lang_var = tk.StringVar(value="C++")
        self.diff_mode_var = tk.StringVar(value="Сравнение кодов")

        self._ext_a = None
        self._ext_b = None
        self._last_highlights = None

        self._compare_thread = None
        self._cancel_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._is_paused = False

        self._apply_styles()
        self._build_scrollable_window()
        self._build_content()

    def _apply_styles(self):
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        self.style.configure(".", font=("Segoe UI", 10), background="#f8f9fa")
        self.style.configure("TCombobox", padding=4)

    def _build_scrollable_window(self):
        self.canvas = tk.Canvas(self, bg="#f8f9fa", highlightthickness=0)
        self.v_scrollbar = ThinScrollbar(self, command=self.canvas.yview, width=8)
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set)

        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 4), pady=4)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollable_content = tk.Frame(self.canvas, bg="#f8f9fa", padx=16, pady=16)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_content, anchor="nw")

        self.scrollable_content.bind("<Configure>", self._on_content_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.bind_all("<MouseWheel>", self._on_global_mousewheel)
        self.bind_all("<Button-4>", self._on_global_mousewheel)
        self.bind_all("<Button-5>", self._on_global_mousewheel)

    def _on_content_configure(self, event):
        req_w = max(self.scrollable_content.winfo_reqwidth(), self.canvas.winfo_width())
        req_h = self.scrollable_content.winfo_reqheight()
        self.canvas.configure(scrollregion=(0, 0, req_w, req_h))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        req_w = max(self.scrollable_content.winfo_reqwidth(), event.width)
        req_h = self.scrollable_content.winfo_reqheight()
        self.canvas.configure(scrollregion=(0, 0, req_w, req_h))

    def _on_global_mousewheel(self, event):
        widget = event.widget
        if isinstance(widget, tk.Text):
            if event.delta:
                step = int(-1 * (event.delta / 120))
            elif event.num == 4:
                step = -1
            else:
                step = 1

            if widget in (self.diff_text_a, self.diff_text_b):
                self.diff_text_a.yview_scroll(step, "units")
                self.diff_text_b.yview_scroll(step, "units")
            else:
                widget.yview_scroll(step, "units")
            return "break"

        units = int(-1 * (event.delta / 120)) if event.delta else (-1 if event.num == 4 else 1)
        top_pos, bottom_pos = self.canvas.yview()

        if units < 0 and top_pos <= 0.0:
            self.canvas.yview_moveto(0.0)
            return "break"
        if units > 0 and bottom_pos >= 1.0:
            self.canvas.yview_moveto(1.0)
            return "break"

        self.canvas.yview_scroll(units, "units")

    def _build_content(self):
        header_lbl = tk.Label(
            self.scrollable_content,
            text="Сравнение программ на списывание",
            font=("Segoe UI", 16, "bold"),
            bg="#f8f9fa",
            fg="#202124"
        )
        header_lbl.pack(anchor="center", pady=(0, 14))

        codes_container = tk.Frame(self.scrollable_content, bg="#f8f9fa")
        codes_container.pack(fill=tk.X, pady=(0, 10))
        codes_container.columnconfigure(0, weight=1)
        codes_container.columnconfigure(1, weight=1)

        frame_a_wrapper = tk.Frame(codes_container, bg="#f8f9fa")
        frame_a_wrapper.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        top_row_a = tk.Frame(frame_a_wrapper, bg="#f8f9fa")
        top_row_a.pack(fill=tk.X, pady=(0, 6))

        lbl_a = tk.Label(top_row_a, text="Исходный код (1-ая программа)", font=("Segoe UI", 10, "bold"), bg="#f8f9fa", fg="#3c4043")
        lbl_a.pack(side=tk.LEFT)

        btn_a = RoundedButton(
            top_row_a, text="Выбрать файл", command=lambda: self._choose_file(is_first=True),
            bg_color="#e8eaed", hover_color="#dadce0", text_color="#202124",
            width=115, height=30, radius=15
        )
        btn_a.pack(side=tk.RIGHT)

        card_a = RoundedFrame(frame_a_wrapper, bg_color="#ffffff", border_color="#dadce0", radius=14, height=220)
        card_a.pack(fill=tk.BOTH, expand=True)
        self.text_a = tk.Text(card_a.inner_frame, wrap=tk.NONE, font=("Consolas", 10), bg="#ffffff", fg="#202124", relief=tk.FLAT, bd=0, highlightthickness=0)
        self.text_a.pack(fill=tk.BOTH, expand=True)

        frame_b_wrapper = tk.Frame(codes_container, bg="#f8f9fa")
        frame_b_wrapper.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        top_row_b = tk.Frame(frame_b_wrapper, bg="#f8f9fa")
        top_row_b.pack(fill=tk.X, pady=(0, 6))

        lbl_b = tk.Label(top_row_b, text="Исходный код (2-ая программа)", font=("Segoe UI", 10, "bold"), bg="#f8f9fa", fg="#3c4043")
        lbl_b.pack(side=tk.LEFT)

        btn_b = RoundedButton(
            top_row_b, text="Выбрать файл", command=lambda: self._choose_file(is_first=False),
            bg_color="#e8eaed", hover_color="#dadce0", text_color="#202124",
            width=115, height=30, radius=15
        )
        btn_b.pack(side=tk.RIGHT)

        card_b = RoundedFrame(frame_b_wrapper, bg_color="#ffffff", border_color="#dadce0", radius=14, height=220)
        card_b.pack(fill=tk.BOTH, expand=True)
        self.text_b = tk.Text(card_b.inner_frame, wrap=tk.NONE, font=("Consolas", 10), bg="#ffffff", fg="#202124", relief=tk.FLAT, bd=0, highlightthickness=0)
        self.text_b.pack(fill=tk.BOTH, expand=True)

        control_frame = tk.Frame(self.scrollable_content, bg="#f8f9fa")
        control_frame.pack(fill=tk.X, pady=(8, 12))

        btn_row = tk.Frame(control_frame, bg="#f8f9fa")
        btn_row.pack(fill=tk.X, pady=(0, 10))

        lang_box_frame = tk.Frame(btn_row, bg="#f8f9fa")
        lang_box_frame.pack(side=tk.LEFT, padx=(0, 14))

        tk.Label(lang_box_frame, text="Язык:", font=("Segoe UI", 9, "bold"), bg="#f8f9fa", fg="#3c4043").pack(side=tk.LEFT, padx=(0, 6))
        self.lang_combo = ttk.Combobox(
            lang_box_frame,
            textvariable=self.lang_var,
            values=["C++", "Python", "Pascal ABC"],
            state="readonly",
            width=12,
            font=("Segoe UI", 9)
        )
        self.lang_combo.pack(side=tk.LEFT)

        self.start_btn = RoundedButton(
            btn_row, text="Запустить проверку", command=self.start_comparison,
            bg_color="#1a73e8", hover_color="#1557b0", text_color="#ffffff",
            width=165, height=36, radius=18
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.pause_btn = RoundedButton(
            btn_row, text="Пауза", command=self.toggle_pause,
            bg_color="#e8eaed", hover_color="#dadce0", text_color="#202124",
            width=110, height=36, radius=18
        )
        self.pause_btn.configure(state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.cancel_btn = RoundedButton(
            btn_row, text="Отмена", command=self.cancel_comparison,
            bg_color="#e8eaed", hover_color="#dadce0", text_color="#202124",
            width=100, height=36, radius=18
        )
        self.cancel_btn.configure(state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT)

        self.progress_label = tk.Label(btn_row, text="Готов", font=("Segoe UI", 9), bg="#f8f9fa", fg="#5f6368")
        self.progress_label.pack(side=tk.RIGHT, padx=4)

        self.progress_bar = RoundedProgressBar(control_frame, height=12)
        self.progress_bar.pack(fill=tk.X)

        self.result_card = RoundedFrame(self.scrollable_content, bg_color="#ffffff", border_color="#dadce0", radius=16, height=230)
        self.result_card.pack(fill=tk.X, pady=(8, 16))

        self.score_label = tk.Label(self.result_card.inner_frame, text="-- %", font=("Segoe UI", 32, "bold"), bg="#ffffff", fg="#5f6368")
        self.score_label.pack(anchor="center", pady=(4, 6))

        self.criteria_frame = tk.Frame(self.result_card.inner_frame, bg="#ffffff")
        self.criteria_frame.pack(fill=tk.X, padx=12, pady=(0, 8))

        self.empty_label = tk.Label(
            self.criteria_frame,
            text="Загрузите файлы или вставьте код, после чего запустите проверку",
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg="#5f6368"
        )
        self.empty_label.pack(anchor="center", pady=4)

        diff_section = tk.Frame(self.scrollable_content, bg="#f8f9fa")
        diff_section.pack(fill=tk.X, pady=(4, 20))

        diff_header = tk.Frame(diff_section, bg="#f8f9fa")
        diff_header.pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            diff_header,
            text="Режим просмотра:",
            font=("Segoe UI", 10, "bold"),
            bg="#f8f9fa",
            fg="#3c4043"
        ).pack(side=tk.LEFT, padx=(0, 8))

        self.diff_mode_combo = ttk.Combobox(
            diff_header,
            textvariable=self.diff_mode_var,
            values=["Сравнение кодов", "Сравнение токенов"],
            state="readonly",
            width=20,
            font=("Segoe UI", 9)
        )
        self.diff_mode_combo.pack(side=tk.LEFT)
        self.diff_mode_combo.bind("<<ComboboxSelected>>", self._on_diff_mode_change)

        legend_frame = tk.Frame(diff_header, bg="#f8f9fa")
        legend_frame.pack(side=tk.RIGHT)

        badge = ColorPillBadge(legend_frame, color="#9e4a10", width=26, height=12)
        badge.pack(side=tk.LEFT, padx=(0, 6))
        tk.Label(legend_frame, text="Отличия", font=("Segoe UI", 9), bg="#f8f9fa", fg="#3c4043").pack(side=tk.LEFT)

        diff_boxes = tk.Frame(diff_section, bg="#f8f9fa")
        diff_boxes.pack(fill=tk.X)
        diff_boxes.columnconfigure(0, weight=1)
        diff_boxes.columnconfigure(1, weight=1)

        diff_left_wrap = tk.Frame(diff_boxes, bg="#f8f9fa")
        diff_left_wrap.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        tk.Label(diff_left_wrap, text="1-ая программа", font=("Segoe UI", 9, "bold"), bg="#f8f9fa", fg="#5f6368").pack(anchor="w", pady=(0, 4))
        diff_card_a = RoundedFrame(diff_left_wrap, bg_color="#0d1117", border_color="#30363d", radius=14, height=260)
        diff_card_a.pack(fill=tk.BOTH, expand=True)

        self.diff_text_a = tk.Text(
            diff_card_a.inner_frame,
            wrap=tk.NONE,
            font=("Consolas", 10),
            bg="#0d1117",
            fg="#e6edf3",
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
            state=tk.DISABLED
        )
        self.diff_text_a.pack(fill=tk.BOTH, expand=True)

        diff_right_wrap = tk.Frame(diff_boxes, bg="#f8f9fa")
        diff_right_wrap.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        tk.Label(diff_right_wrap, text="2-ая программа", font=("Segoe UI", 9, "bold"), bg="#f8f9fa", fg="#5f6368").pack(anchor="w", pady=(0, 4))
        diff_card_b = RoundedFrame(diff_right_wrap, bg_color="#0d1117", border_color="#30363d", radius=14, height=260)
        diff_card_b.pack(fill=tk.BOTH, expand=True)

        self.diff_text_b = tk.Text(
            diff_card_b.inner_frame,
            wrap=tk.NONE,
            font=("Consolas", 10),
            bg="#0d1117",
            fg="#e6edf3",
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
            state=tk.DISABLED
        )
        self.diff_text_b.pack(fill=tk.BOTH, expand=True)

        self._configure_diff_tags(self.diff_text_a)
        self._configure_diff_tags(self.diff_text_b)

    def _configure_diff_tags(self, text_widget: tk.Text):
        text_widget.tag_configure("lineno", foreground="#6e7681", background="#0d1117")
        text_widget.tag_configure("neutral", foreground="#e6edf3", background="#0d1117")
        text_widget.tag_configure("diff_line", foreground="#e6edf3", background="#2a1a0e")
        text_widget.tag_configure("diff_token", foreground="#ffffff", background="#9e4a10")

    def _on_diff_mode_change(self, event=None):
        if self._last_highlights:
            self._render_highlights(self._last_highlights)

    def _clear_diff_views(self):
        for widget in (self.diff_text_a, self.diff_text_b):
            widget.configure(state=tk.NORMAL)
            widget.delete("1.0", tk.END)
            widget.configure(state=tk.DISABLED)

    def _render_single_diff_widget(self, widget: tk.Text, lines_data):
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)

        total = len(lines_data)
        for idx, line_info in enumerate(lines_data):
            line_no = line_info["line_no"]
            line_tag = line_info["line_tag"]
            segments = line_info["segments"]

            prefix = f"{line_no:>4}.  " if line_no is not None else "       "
            widget.insert(tk.END, prefix, "lineno")

            for seg_text, seg_tag in segments:
                widget.insert(tk.END, seg_text, seg_tag)

            if idx < total - 1:
                widget.insert(tk.END, "\n", line_tag)

        widget.configure(state=tk.DISABLED)

    def _render_highlights(self, highlight_data):
        mode_key = "code" if self.diff_mode_var.get() == "Сравнение кодов" else "tokens"
        mode_data = highlight_data.get(mode_key)
        if not mode_data:
            return

        self._render_single_diff_widget(self.diff_text_a, mode_data["left"])
        self._render_single_diff_widget(self.diff_text_b, mode_data["right"])

    def _choose_file(self, is_first):
        if is_first:
            filetypes = [("Program Files", "*.cpp *.py *.pas"), ("Все файлы", "*.*")]
        else:
            selected_lang = self.lang_var.get()
            if selected_lang == "C++":
                filetypes = [("C++ Files", "*.cpp"), ("Все файлы", "*.*")]
            elif selected_lang == "Python":
                filetypes = [("Python Files", "*.py"), ("Все файлы", "*.*")]
            elif selected_lang == "Pascal ABC":
                filetypes = [("Pascal Files", "*.pas"), ("Все файлы", "*.*")]

        filepath = filedialog.askopenfilename(
            title="Выберите файл программы",
            filetypes=filetypes
        )

        if filepath:
            ext = Path(filepath).suffix.lower()

            if ext not in all_supported_extensions:
                messagebox.showerror(
                    "ERROR: Unsupported File Format (UFF E-003)",
                    f"Неподдерживаемый формат файла: '{ext}'!\n"
                    "Поддерживаются только исходные файлы C++ (.cpp), Python (.py) и Pascal (.pas)."
                )
                return

            if is_first:
                if ext in python_extension:
                    self.lang_var.set("Python")
                elif ext in pas_extension:
                    self.lang_var.set("Pascal ABC")
                elif ext in cpp_extension:
                    self.lang_var.set("C++")

                self._ext_a = ext
            else:
                expected_lang = self.lang_var.get()
                actual_lang = self._get_lang_for_extension(ext)

                if actual_lang != expected_lang:
                    messagebox.showerror(
                        "ERROR: Language Mismatch (LMM E-002)",
                        f"Для второй программы нужно выбрать файл языка {expected_lang}!"
                    )
                    return

                self._ext_b = ext

            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                target_text = self.text_a if is_first else self.text_b
                target_text.delete("1.0", tk.END)
                target_text.insert(tk.END, content)
            except Exception as e:
                messagebox.showerror("Ошибка чтения файла", f"Не удалось прочитать файл:\n{e}")

    def _get_lang_for_extension(self, ext):
        if ext in cpp_extension:
            return "C++"
        if ext in python_extension:
            return "Python"
        if ext in pas_extension:
            return "Pascal ABC"
        return None

    def start_comparison(self):
        text_a = self.text_a.get("1.0", tk.END).strip()
        text_b = self.text_b.get("1.0", tk.END).strip()

        if not text_a or not text_b:
            messagebox.showwarning("ERROR: Can't Compare Files (CCF E-001)", "Вы не заполнили все обязательные поля!")
            return

        lang = self.lang_var.get()

        if self._ext_a and self._ext_b:
            lang_a = self._get_lang_for_extension(self._ext_a)
            lang_b = self._get_lang_for_extension(self._ext_b)

            if lang_a != lang_b:
                messagebox.showerror(
                    "ERROR: Language Mismatch (LMM E-002)",
                    f"Невозможно сравнить файлы разных языков программирования!\n\n"
                    f"Файл 1: {self._ext_a} ({lang_a})\n"
                    f"Файл 2: {self._ext_b} ({lang_b})\n\n"
                    "Для проверки загрузите файлы одного и того же языка."
                )
                return

            if lang != lang_a:
                messagebox.showerror(
                    "ERROR: Language Mode Mismatch (LMM E-004)",
                    f"Выбранный режим анализа ({lang}) не соответствует расширению загруженных файлов ({self._ext_a})!"
                )
                return

        self._cancel_event.clear()
        self._pause_event.set()
        self._is_paused = False
        self._last_highlights = None
        self._clear_diff_views()

        self.start_btn.configure(state=tk.DISABLED)
        self.pause_btn.configure(state=tk.NORMAL)
        self.pause_btn.set_text("Пауза")
        self.cancel_btn.configure(state=tk.NORMAL)
        self.lang_combo.configure(state="disabled")

        self.score_label.configure(text="-- %", fg="#5f6368")
        self._clear_criteria()
        self.empty_label.configure(text="Идёт анализ программ...", fg="#5f6368")
        self.empty_label.pack(anchor="center", pady=4)

        self.progress_bar["value"] = 0
        self.progress_label.configure(text="Запуск процесса...")

        self._compare_thread = threading.Thread(
            target=self._run_pipeline,
            args=(text_a, text_b, lang),
            daemon=True
        )
        self._compare_thread.start()

    def toggle_pause(self):
        if self._is_paused:
            self._pause_event.set()
            self._is_paused = False
            self.pause_btn.set_text("Пауза")
            self.progress_label.configure(text="Продолжение работы...")
        else:
            self._pause_event.clear()
            self._is_paused = True
            self.pause_btn.set_text("Возобновить")
            self.progress_label.configure(text="Анализ приостановлен")

    def cancel_comparison(self):
        self._cancel_event.set()
        self._pause_event.set()
        self.progress_label.configure(text="Отмена операции...")

    def _wait_or_cancel(self):
        self._pause_event.wait()
        return self._cancel_event.is_set()

    def _set_progress_ui(self, pct, label):
        self.after(0, lambda: self._apply_progress(pct, label))

    def _apply_progress(self, pct, label):
        self.progress_bar["value"] = pct
        self.progress_label.configure(text=f"{label} ({pct}%)")

    def _run_pipeline(self, text_a, text_b, lang):
        stages = [
            (15, "Чтение кода (1)"),
            (27, "Чтение кода (2)"),
            (40, f"Токенизация ({lang})"),
            (56, "Запись и нормализация токенов"),
            (65, "Подсчёт расстояния Левенштейна"),
            (83, "Сравнение k-строк"),
        ]

        for pct, label in stages:
            if self._wait_or_cancel():
                self._finish_cancelled()
                return

            self._set_progress_ui(pct, label)
            time.sleep(random.choice([0.6, 0.8, 1.0]))

        if self._wait_or_cancel():
            self._finish_cancelled()
            return

        if lang == "C++":
            result = compare_cpp.compare(text_a, text_b)
            highlight_data = highlights.get_highlights(text_a, text_b, lang)
        elif lang == "Pascal ABC":
            result = compare_pas.compare(text_a, text_b)
            highlight_data = highlights.get_highlights(text_a, text_b, lang)
        else:
            result = {
                "percent": 63,
                "criteria": [
                    {
                        "name": "Совпадение токенов",
                        "value": None,
                        "note": f"Демонстрационное значение — модуль сравнения для {lang} ещё не реализован",
                    },
                    {
                        "name": "k-строки",
                        "value": None,
                        "note": f"Демонстрационное значение — модуль сравнения для {lang} ещё не реализован",
                    },
                    {
                        "name": "Совпадение по позициям",
                        "value": None,
                        "note": f"Демонстрационное значение — модуль сравнения для {lang} ещё не реализован",
                    },
                ],
            }
            highlight_data = None

        if self._wait_or_cancel():
            self._finish_cancelled()
            return

        self._set_progress_ui(93, "Подсчёт итога")
        time.sleep(0.4)

        self._set_progress_ui(100, "Готово!")
        time.sleep(0.3)

        self.after(0, lambda: self._show_results(result, highlight_data))

    def _finish_cancelled(self):
        def _cb():
            self.progress_bar["value"] = 0
            self.progress_label.configure(text="Операция отменена")
            self.start_btn.configure(state=tk.NORMAL)
            self.pause_btn.configure(state=tk.DISABLED)
            self.pause_btn.set_text("Пауза")
            self.cancel_btn.configure(state=tk.DISABLED)
            self.lang_combo.configure(state="readonly")
            self.score_label.configure(text="-- %", fg="#5f6368")
            self._clear_criteria()
            self._clear_diff_views()
            self.empty_label.configure(text="Проверка была отменена пользователем", fg="#5f6368")
            self.empty_label.pack(anchor="center", pady=4)
        self.after(0, _cb)

    def _clear_criteria(self):
        for widget in self.criteria_frame.winfo_children():
            widget.destroy()
        self.empty_label = tk.Label(self.criteria_frame, font=("Segoe UI", 10), bg="#ffffff")

    def _show_results(self, result, highlight_data=None):
        pct = result.get("percent", 0)
        self.score_label.configure(text=f"{pct}%")

        if pct < 30:
            color = "#1e8e3e"
        elif pct < 60:
            color = "#f9ab00"
        else:
            color = "#d93025"

        self.score_label.configure(fg=color)
        self._clear_criteria()

        for c in result.get("criteria", []):
            row = tk.Frame(self.criteria_frame, bg="#ffffff")
            row.pack(fill=tk.X, pady=3)

            tk.Label(
                row,
                text=f"{c['name']}: {c['value']}%",
                font=("Segoe UI", 10, "bold"),
                bg="#ffffff",
                fg="#202124"
            ).pack(anchor="w")

            tk.Label(
                row,
                text=f"    {c['note']}",
                font=("Segoe UI", 9),
                bg="#ffffff",
                fg="#5f6368"
            ).pack(anchor="w")

        self._last_highlights = highlight_data
        if highlight_data:
            self._render_highlights(highlight_data)

        self.start_btn.configure(state=tk.NORMAL)
        self.pause_btn.configure(state=tk.DISABLED)
        self.pause_btn.set_text("Пауза")
        self.cancel_btn.configure(state=tk.DISABLED)
        self.lang_combo.configure(state="readonly")

        self.after(100, lambda: self.canvas.yview_moveto(1.0))


def main():
    app = AntiPlagApp()
    app.mainloop()


if __name__ == "__main__":
    main()
