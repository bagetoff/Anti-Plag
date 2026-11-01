import os
import random
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import compare_cpp
import compare_pas

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


class AntiPlagApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AntiPlag App")
        self.geometry("980x800")
        self.minsize(820, 520)
        self.configure(bg="#f8f9fa")

        self.lang_var = tk.StringVar(value="C++")

        self._ext_a = None
        self._ext_b = None

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
        self.style.configure(
            "TProgressbar",
            troughcolor="#e8eaed",
            background="#1a73e8",
            thickness=6
        )

    def _build_scrollable_window(self):
        self.canvas = tk.Canvas(self, bg="#f8f9fa", highlightthickness=0)
        self.v_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set)

        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
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
                widget.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif event.num == 4:
                widget.yview_scroll(-1, "units")
            elif event.num == 5:
                widget.yview_scroll(1, "units")
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
        btn_row.pack(fill=tk.X, pady=(0, 8))

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
            width=180, height=36, radius=18
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
            width=110, height=36, radius=18
        )

        self.cancel_btn.configure(state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT)

        self.progress_label = tk.Label(btn_row, text="Готов", font=("Segoe UI", 9), bg="#f8f9fa", fg="#5f6368")
        self.progress_label.pack(side=tk.RIGHT, padx=4)

        self.progress_bar = ttk.Progressbar(control_frame, orient=tk.HORIZONTAL, mode="determinate")
        self.progress_bar.pack(fill=tk.X)

        self.result_card = RoundedFrame(self.scrollable_content, bg_color="#ffffff", border_color="#dadce0", radius=16, height=230)
        self.result_card.pack(fill=tk.X, pady=(8, 20))

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
        elif lang == "Pascal ABC":
            result = compare_pas.compare(text_a, text_b)
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

        if self._wait_or_cancel():
            self._finish_cancelled()
            return

        self._set_progress_ui(93, "Подсчёт итога")
        time.sleep(0.4)

        self._set_progress_ui(100, "Готово!")
        time.sleep(0.3)

        self.after(0, lambda: self._show_results(result))

    def _finish_cancelled(self):
        def _cb():
            self.progress_bar["value"] = 0
            self.progress_label.configure(text="Операция отменена")
            self.start_btn.configure(state=tk.NORMAL)
            self.pause_btn.configure(state=tk.DISABLED)
            self.pause_btn.set_text("⏸  Пауза")
            self.cancel_btn.configure(state=tk.DISABLED)
            self.lang_combo.configure(state="readonly")
            self.score_label.configure(text="-- %", fg="#5f6368")
            self._clear_criteria()
            self.empty_label.configure(text="Проверка была отменена пользователем", fg="#5f6368")
            self.empty_label.pack(anchor="center", pady=4)
        self.after(0, _cb)

    def _clear_criteria(self):
        for widget in self.criteria_frame.winfo_children():
            widget.destroy()
        self.empty_label = tk.Label(self.criteria_frame, font=("Segoe UI", 10), bg="#ffffff")

    def _show_results(self, result):
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
                text=f"•  {c['name']}: {c['value']}%",
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

        self.start_btn.configure(state=tk.NORMAL)
        self.pause_btn.configure(state=tk.DISABLED)
        self.pause_btn.set_text("⏸  Пауза")
        self.cancel_btn.configure(state=tk.DISABLED)
        self.lang_combo.configure(state="readonly")

        self.after(100, lambda: self.canvas.yview_moveto(1.0))


def main():
    app = AntiPlagApp()
    app.mainloop()


if __name__ == "__main__":
    main()
