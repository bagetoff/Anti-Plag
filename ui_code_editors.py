import tkinter as tk

import file_manager
from ui_frames import RoundedFrame
from ui_buttons import RoundedButton
from ui_dropdowns import RoundedDropdown


class CodeEditorsPanel(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f8f9fa")

        self.lang_a_var = tk.StringVar(value="C++")
        self.lang_b_var = tk.StringVar(value="C++")
        self._ext_a = None
        self._ext_b = None

        self._build_ui()

    def _build_ui(self):
        codes_container = tk.Frame(self, bg="#f8f9fa")
        codes_container.pack(fill=tk.X, pady=(0, 6))
        codes_container.columnconfigure(0, weight=1)
        codes_container.columnconfigure(1, weight=1)

        frame_a_wrapper = tk.Frame(codes_container, bg="#f8f9fa")
        frame_a_wrapper.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        top_row_a = tk.Frame(frame_a_wrapper, bg="#f8f9fa")
        top_row_a.pack(fill=tk.X, pady=(0, 6))

        tk.Label(
            top_row_a,
            text="Исходный код (1-ая программа)",
            font=("Segoe UI", 10, "bold"),
            bg="#f8f9fa",
            fg="#3c4043"
        ).pack(side=tk.LEFT)

        RoundedButton(
            top_row_a,
            text="Выбрать файл",
            command=lambda: self._on_choose_file(is_first=True),
            bg_color="#e8eaed",
            hover_color="#dadce0",
            text_color="#202124",
            width=115,
            height=30,
            radius=15
        ).pack(side=tk.RIGHT)

        self.lang_dropdown_a = RoundedDropdown(
            top_row_a,
            textvariable=self.lang_a_var,
            values=["C++", "Pascal ABC", "Python"],
            command=lambda _: self.validate(silent_empty=True),
            width=120,
            height=30,
            radius=15
        )
        self.lang_dropdown_a.pack(side=tk.RIGHT, padx=(0, 8))

        card_a = RoundedFrame(
            frame_a_wrapper, bg_color="#ffffff", border_color="#dadce0", radius=14, height=210
        )
        card_a.pack(fill=tk.BOTH, expand=True)

        self.text_a = tk.Text(
            card_a.inner_frame,
            wrap=tk.NONE,
            font=("Consolas", 10),
            bg="#ffffff",
            fg="#202124",
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0
        )
        self.text_a.pack(fill=tk.BOTH, expand=True)
        self.text_a.bind("<KeyRelease>", lambda e: self.validate(silent_empty=True))

        frame_b_wrapper = tk.Frame(codes_container, bg="#f8f9fa")
        frame_b_wrapper.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        top_row_b = tk.Frame(frame_b_wrapper, bg="#f8f9fa")
        top_row_b.pack(fill=tk.X, pady=(0, 6))

        tk.Label(
            top_row_b,
            text="Исходный код (2-ая программа)",
            font=("Segoe UI", 10, "bold"),
            bg="#f8f9fa",
            fg="#3c4043"
        ).pack(side=tk.LEFT)

        RoundedButton(
            top_row_b,
            text="Выбрать файл",
            command=lambda: self._on_choose_file(is_first=False),
            bg_color="#e8eaed",
            hover_color="#dadce0",
            text_color="#202124",
            width=115,
            height=30,
            radius=15
        ).pack(side=tk.RIGHT)

        self.lang_dropdown_b = RoundedDropdown(
            top_row_b,
            textvariable=self.lang_b_var,
            values=["C++", "Pascal ABC", "Python"],
            command=lambda _: self.validate(silent_empty=True),
            width=120,
            height=30,
            radius=15
        )
        self.lang_dropdown_b.pack(side=tk.RIGHT, padx=(0, 8))

        card_b = RoundedFrame(
            frame_b_wrapper, bg_color="#ffffff", border_color="#dadce0", radius=14, height=210
        )
        card_b.pack(fill=tk.BOTH, expand=True)

        self.text_b = tk.Text(
            card_b.inner_frame,
            wrap=tk.NONE,
            font=("Consolas", 10),
            bg="#ffffff",
            fg="#202124",
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0
        )
        self.text_b.pack(fill=tk.BOTH, expand=True)
        self.text_b.bind("<KeyRelease>", lambda e: self.validate(silent_empty=True))

        self.warning_wrapper = tk.Frame(self, bg="#f8f9fa")
        self.warning_wrapper.pack(fill=tk.X)

        self.warning_card = RoundedFrame(
            self.warning_wrapper,
            bg_color="#fef7e0",
            border_color="#f9ab00",
            radius=12,
            height=38,
            inner_pad=6
        )
        self.warning_label = tk.Label(
            self.warning_card.inner_frame,
            text="",
            font=("Segoe UI", 9, "bold"),
            bg="#fef7e0",
            fg="#b06000"
        )
        self.warning_label.pack(anchor="center", expand=True)

    def show_warning(self, message: str, is_error: bool = False):
        if is_error:
            bg, border, fg = "#fce8e6", "#d93025", "#c5221f"
        else:
            bg, border, fg = "#fef7e0", "#f9ab00", "#b06000"

        self.warning_card.set_colors(bg, border)
        self.warning_label.configure(text=message, bg=bg, fg=fg)
        if not self.warning_card.winfo_ismapped():
            self.warning_card.pack(fill=tk.X, pady=(4, 4))

    def hide_warning(self):
        if self.warning_card.winfo_ismapped():
            self.warning_card.pack_forget()

    def validate(self, silent_empty: bool = True) -> bool:
        is_valid, msg, is_error = file_manager.validate_inputs(
            self.lang_a_var.get(),
            self.lang_b_var.get(),
            self.text_a.get("1.0", tk.END),
            self.text_b.get("1.0", tk.END),
            silent_empty=silent_empty,
        )
        if not is_valid:
            self.show_warning(msg, is_error=is_error)
            return False

        self.hide_warning()
        return True

    def _on_choose_file(self, is_first: bool):
        res = file_manager.select_and_read_file()
        if res is None:
            return

        if not res["ok"]:
            self.show_warning(res["error"], is_error=True)
            return

        if is_first:
            self._ext_a = res["ext"]
            self.lang_a_var.set(res["lang"])
            target_widget = self.text_a
        else:
            self._ext_b = res["ext"]
            self.lang_b_var.set(res["lang"])
            target_widget = self.text_b

        target_widget.delete("1.0", tk.END)
        target_widget.insert(tk.END, res["content"])
        self.validate(silent_empty=True)

    def get_inputs(self):
        text_a = self.text_a.get("1.0", tk.END).strip()
        text_b = self.text_b.get("1.0", tk.END).strip()
        lang = self.lang_a_var.get()
        return text_a, text_b, lang

    def set_dropdowns_state(self, state):
        self.lang_dropdown_a.configure(state=state)
        self.lang_dropdown_b.configure(state=state)