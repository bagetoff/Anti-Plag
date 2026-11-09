import tkinter as tk

from ui_frames import RoundedFrame
from ui_dropdowns import RoundedDropdown
from ui_indicators import ColorPillBadge


class DiffViewerPanel(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f8f9fa")
        self.diff_mode_var = tk.StringVar(value="Сравнение кодов")
        self._last_highlights = None

        self._build_ui()

    def _build_ui(self):
        diff_header = tk.Frame(self, bg="#f8f9fa")
        diff_header.pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            diff_header,
            text="Режим просмотра:",
            font=("Segoe UI", 10, "bold"),
            bg="#f8f9fa",
            fg="#3c4043"
        ).pack(side=tk.LEFT, padx=(0, 8))

        self.diff_mode_dropdown = RoundedDropdown(
            diff_header,
            textvariable=self.diff_mode_var,
            values=["Сравнение кодов", "Сравнение токенов"],
            command=self._on_mode_change,
            width=175,
            height=30,
            radius=15
        )
        self.diff_mode_dropdown.pack(side=tk.LEFT)

        legend_frame = tk.Frame(diff_header, bg="#f8f9fa")
        legend_frame.pack(side=tk.RIGHT)

        ColorPillBadge(legend_frame, color="#9e4a10", width=26, height=12).pack(side=tk.LEFT, padx=(0, 6))
        tk.Label(legend_frame, text="Отличия", font=("Segoe UI", 9), bg="#f8f9fa", fg="#3c4043").pack(side=tk.LEFT)

        diff_boxes = tk.Frame(self, bg="#f8f9fa")
        diff_boxes.pack(fill=tk.X)
        diff_boxes.columnconfigure(0, weight=1)
        diff_boxes.columnconfigure(1, weight=1)

        diff_left_wrap = tk.Frame(diff_boxes, bg="#f8f9fa")
        diff_left_wrap.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        tk.Label(
            diff_left_wrap, text="1-ая программа", font=("Segoe UI", 9, "bold"), bg="#f8f9fa", fg="#5f6368"
        ).pack(anchor="w", pady=(0, 4))

        diff_card_a = RoundedFrame(diff_left_wrap, bg_color="#0d1117", border_color="#30363d", radius=14, height=250)
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

        tk.Label(
            diff_right_wrap, text="2-ая программа", font=("Segoe UI", 9, "bold"), bg="#f8f9fa", fg="#5f6368"
        ).pack(anchor="w", pady=(0, 4))

        diff_card_b = RoundedFrame(diff_right_wrap, bg_color="#0d1117", border_color="#30363d", radius=14, height=250)
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

        for widget in (self.diff_text_a, self.diff_text_b):
            widget.tag_configure("lineno", foreground="#6e7681", background="#0d1117")
            widget.tag_configure("neutral", foreground="#e6edf3", background="#0d1117")
            widget.tag_configure("diff_line", foreground="#e6edf3", background="#2a1a0e")
            widget.tag_configure("diff_token", foreground="#ffffff", background="#9e4a10")

    def _on_mode_change(self, _=None):
        if self._last_highlights:
            self.render(self._last_highlights)

    def clear(self):
        self._last_highlights = None
        for widget in (self.diff_text_a, self.diff_text_b):
            widget.configure(state=tk.NORMAL)
            widget.delete("1.0", tk.END)
            widget.configure(state=tk.DISABLED)

    def _render_single(self, widget: tk.Text, lines_data: list):
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)

        total = len(lines_data)
        for idx, line_info in enumerate(lines_data):
            line_no = line_info["line_no"]
            line_tag = line_info["line_tag"]
            prefix = f"{line_no:>4}.  " if line_no is not None else "       "
            widget.insert(tk.END, prefix, "lineno")

            for seg_text, seg_tag in line_info["segments"]:
                widget.insert(tk.END, seg_text, seg_tag)

            if idx < total - 1:
                widget.insert(tk.END, "\n", line_tag)

        widget.configure(state=tk.DISABLED)

    def render(self, highlight_data: dict | None):
        self._last_highlights = highlight_data
        if not highlight_data:
            return

        mode_key = "code" if self.diff_mode_var.get() == "Сравнение кодов" else "tokens"
        mode_data = highlight_data.get(mode_key)
        if mode_data:
            self._render_single(self.diff_text_a, mode_data["left"])
            self._render_single(self.diff_text_b, mode_data["right"])