import os
import random
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import compare_cpp

cpp_extensions = {".cpp"}

class AntiPlagApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AntiPlag App")
        self.geometry("980x780")
        self.minsize(820, 520)

        self.lang_var = tk.StringVar(value="C++")

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
        self.configure(bg="#f8f9fa")

        self.style.configure(
            "Header.TLabel",
            font=("Segoe UI", 16, "bold"),
            background="#f8f9fa",
            foreground="#202124"
        )
        self.style.configure(
            "Muted.TLabel",
            font=("Segoe UI", 9),
            background="#f8f9fa",
            foreground="#5f6368"
        )

        self.style.configure(
            "CodeBox.TLabelframe",
            background="#f8f9fa",
            padding=8,
            relief="solid",
            borderwidth=1
        )

        self.style.configure(
            "CodeBox.TLabelframe.Label",
            font=("Segoe UI", 10, "bold"),
            background="#f8f9fa",
            foreground="#3c4043"
        )

        self.style.configure(
            "TButton",
            font=("Segoe UI", 9),
            padding=(10, 5),
            borderwidth=1
        )

        self.style.configure(
            "Accent.TButton",
            font=("Segoe UI", 9, "bold"),
            padding=(12, 5),
            background="#1a73e8",
            foreground="#ffffff"
        )
        self.style.map(
            "Accent.TButton",
            background=[("active", "#1557b0"), ("disabled", "#e0e0e0")],
            foreground=[("disabled", "#9e9e9e")]
        )

        self.style.configure(
            "Score.TLabel",
            font=("Segoe UI", 32, "bold"),
            background="#f8f9fa",
            foreground="#5f6368"
        )

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

        self.scrollable_content = ttk.Frame(self.canvas, padding=16)
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
        header_frame = ttk.Frame(self.scrollable_content)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(
            header_frame,
            text="Сравнение программ на списывание",
            style="Header.TLabel"
        ).pack(anchor="center")

        paned = ttk.PanedWindow(self.scrollable_content, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.X, pady=(0, 8))

        frame_a = ttk.LabelFrame(paned, text=" Исходный код (1-ая программа) ", style="CodeBox.TLabelframe")
        paned.add(frame_a, weight=1)

        btn_row_a = ttk.Frame(frame_a)
        btn_row_a.pack(fill=tk.X, pady=(0, 4))
        ttk.Button(
            btn_row_a,
            text="Выбрать файл",
            command=lambda: self._choose_file(is_first=True)
        ).pack(side=tk.RIGHT)

        self.text_a = tk.Text(
            frame_a,
            wrap=tk.NONE,
            font=("Consolas", 10),
            height=12,
            relief=tk.FLAT,
            bd=1,
            highlightthickness=1,
            highlightbackground="#dadce0",
            highlightcolor="#1a73e8"
        )
        self.text_a.pack(fill=tk.BOTH, expand=True, pady=(2, 0))

        frame_b = ttk.LabelFrame(paned, text=" Исходный код (2-ая программа) ", style="CodeBox.TLabelframe")
        paned.add(frame_b, weight=1)

        btn_row_b = ttk.Frame(frame_b)
        btn_row_b.pack(fill=tk.X, pady=(0, 4))
        ttk.Button(
            btn_row_b,
            text="Выбрать файл",
            command=lambda: self._choose_file(is_first=False)
        ).pack(side=tk.RIGHT)

        self.text_b = tk.Text(
            frame_b,
            wrap=tk.NONE,
            font=("Consolas", 10),
            height=12,
            relief=tk.FLAT,
            bd=1,
            highlightthickness=1,
            highlightbackground="#dadce0",
            highlightcolor="#1a73e8"
        )
        self.text_b.pack(fill=tk.BOTH, expand=True, pady=(2, 0))

        control_frame = ttk.Frame(self.scrollable_content)
        control_frame.pack(fill=tk.X, pady=(6, 8))

        btn_row = ttk.Frame(control_frame)
        btn_row.pack(fill=tk.X, pady=(0, 6))

        lang_frame = ttk.Frame(btn_row)
        lang_frame.pack(side=tk.LEFT, padx=(0, 12))
        ttk.Label(lang_frame, text="Язык:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 6))
        self.lang_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.lang_var,
            values=["C++"],
            state="readonly",
            width=10
        )
        self.lang_combo.pack(side=tk.LEFT)

        self.start_btn = ttk.Button(
            btn_row,
            text="Запустить проверку",
            style="Accent.TButton",
            command=self.start_comparison
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.pause_btn = ttk.Button(
            btn_row,
            text="Пауза",
            state=tk.DISABLED,
            command=self.toggle_pause
        )
        self.pause_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.cancel_btn = ttk.Button(
            btn_row,
            text="Отмена",
            state=tk.DISABLED,
            command=self.cancel_comparison
        )
        self.cancel_btn.pack(side=tk.LEFT)

        self.progress_label = ttk.Label(btn_row, text="Готов", style="Muted.TLabel")
        self.progress_label.pack(side=tk.RIGHT, padx=4)

        self.progress_bar = ttk.Progressbar(control_frame, orient=tk.HORIZONTAL, mode="determinate")
        self.progress_bar.pack(fill=tk.X, pady=(2, 0))

        self.result_frame = ttk.Frame(self.scrollable_content)
        self.result_frame.pack(fill=tk.X, pady=(10, 20))

        self.score_label = ttk.Label(self.result_frame, text="-- %", style="Score.TLabel")
        self.score_label.pack(anchor="center", pady=(0, 6))

        self.criteria_frame = ttk.Frame(self.result_frame)
        self.criteria_frame.pack(fill=tk.X, padx=10)

        self.empty_label = ttk.Label(
            self.criteria_frame,
            text="Загрузите файлы или вставьте код, после чего запустите проверку",
            font=("Segoe UI", 10),
            foreground="#5f6368"
        )
        self.empty_label.pack(anchor="center", pady=4)

    def _choose_file(self, is_first):
        selected_lang = self.lang_var.get()

        if selected_lang == "C++":
            filetypes = [("C++ Files", "*.cpp"), ("Все файлы", "*.*")]

        filepath = filedialog.askopenfilename(
            title="Выберите файл программы",
            filetypes=filetypes
        )

        if filepath:
            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                target_text = self.text_a if is_first else self.text_b
                target_text.delete("1.0", tk.END)
                target_text.insert(tk.END, content)
            except Exception as e:
                messagebox.showerror("Ошибка чтения файла", f"Не удалось прочитать файл:\n{e}")

    def start_comparison(self):
        text_a = self.text_a.get("1.0", tk.END).strip()
        text_b = self.text_b.get("1.0", tk.END).strip()

        if not text_a or not text_b:
            messagebox.showwarning("ERROR: Can't Compare Files (CCF E-001)", "Вы не заполнили все обязательные поля!")
            return

        lang = self.lang_var.get()

        self._cancel_event.clear()
        self._pause_event.set()
        self._is_paused = False

        self.start_btn.configure(state=tk.DISABLED)
        self.pause_btn.configure(state=tk.NORMAL, text="⏸  Пауза")
        self.cancel_btn.configure(state=tk.NORMAL)
        self.lang_combo.configure(state="disabled")

        self.score_label.configure(text="-- %", foreground="#5f6368")
        self._clear_criteria()
        self.empty_label.configure(text="Идёт анализ программ...", foreground="#5f6368")
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
            self.pause_btn.configure(text="Пауза")
            self.progress_label.configure(text="Продолжение работы...")
        else:
            self._pause_event.clear()
            self._is_paused = True
            self.pause_btn.configure(text="Возобновить")
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
            self.pause_btn.configure(state=tk.DISABLED, text="⏸  Пауза")
            self.cancel_btn.configure(state=tk.DISABLED)
            self.lang_combo.configure(state="readonly")
            self.score_label.configure(text="-- %", foreground="#5f6368")
            self._clear_criteria()
            self.empty_label.configure(text="Проверка была отменена пользователем", foreground="#5f6368")
            self.empty_label.pack(anchor="center", pady=4)
        self.after(0, _cb)

    def _clear_criteria(self):
        for widget in self.criteria_frame.winfo_children():
            widget.destroy()
        self.empty_label = ttk.Label(self.criteria_frame, font=("Segoe UI", 10))

    def _show_results(self, result):
        pct = result.get("percent", 0)
        self.score_label.configure(text=f"{pct}%")

        if pct < 30:
            color = "#1e8e3e"
        elif pct < 60:
            color = "#f9ab00"
        else:
            color = "#d93025"

        self.score_label.configure(foreground=color)

        self._clear_criteria()

        for c in result.get("criteria", []):
            row = ttk.Frame(self.criteria_frame)
            row.pack(fill=tk.X, pady=3)

            ttk.Label(
                row,
                text=f"•  {c['name']}: {c['value']}%",
                font=("Segoe UI", 10, "bold"),
                foreground="#202124"
            ).pack(anchor="w")

            ttk.Label(
                row,
                text=f"    {c['note']}",
                font=("Segoe UI", 9),
                foreground="#5f6368"
            ).pack(anchor="w")

        self.start_btn.configure(state=tk.NORMAL)
        self.pause_btn.configure(state=tk.DISABLED, text="⏸  Пауза")
        self.cancel_btn.configure(state=tk.DISABLED)
        self.lang_combo.configure(state="readonly")

        self.after(100, lambda: self.canvas.yview_moveto(1.0))


def main():
    app = AntiPlagApp()
    app.mainloop()


if __name__ == "__main__":
    main()