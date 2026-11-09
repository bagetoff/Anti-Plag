import tkinter as tk
from tkinter import ttk

from ui_scrollbar import ThinScrollbar
from ui_code_editors import CodeEditorsPanel
from ui_controls import ControlPanel
from ui_results import ResultsPanel
from ui_diff_viewer import DiffViewerPanel
from pipeline_worker import ComparisonWorker


class AntiPlagApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AntiPlag App")

        self._setup_window_geometry()
        self._apply_styles()
        self._build_scrollable_window()
        self._build_content()

        self.worker = ComparisonWorker(
            on_progress=self._on_worker_progress,
            on_complete=self._on_worker_complete,
            on_cancel=self._on_worker_cancelled,
        )

    def _setup_window_geometry(self):
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        win_w = max(920, int(screen_w * 3 / 5))
        win_h = max(620, int(screen_h * 2 / 3))
        pos_x = max(0, (screen_w - win_w) // 2)
        pos_y = max(0, (screen_h - win_h) // 2)

        self.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
        self.minsize(880, 560)
        self.configure(bg="#f8f9fa")

    def _apply_styles(self):
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        self.style.configure(".", font=("Segoe UI", 10), background="#f8f9fa")

    def _build_scrollable_window(self):
        self.canvas = tk.Canvas(self, bg="#f8f9fa", highlightthickness=0)
        self.v_scrollbar = ThinScrollbar(self, command=self.canvas.yview, width=8)
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set)

        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 4), pady=4)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollable_content = tk.Frame(self.canvas, bg="#f8f9fa", padx=16, pady=16)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.scrollable_content, anchor="nw"
        )

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

        self.editors_panel = CodeEditorsPanel(self.scrollable_content)
        self.editors_panel.pack(fill=tk.X)

        self.controls_panel = ControlPanel(
            self.scrollable_content,
            on_start=self.start_comparison,
            on_pause=self.toggle_pause,
            on_cancel=self.cancel_comparison,
        )
        self.controls_panel.pack(fill=tk.X, pady=(8, 12))

        self.results_panel = ResultsPanel(self.scrollable_content)
        self.results_panel.pack(fill=tk.X, pady=(6, 14))

        self.diff_panel = DiffViewerPanel(self.scrollable_content)
        self.diff_panel.pack(fill=tk.X, pady=(4, 20))

    def start_comparison(self):
        if not self.editors_panel.validate(silent_empty=False):
            return

        text_a, text_b, lang = self.editors_panel.get_inputs()

        self.diff_panel.clear()
        self.controls_panel.set_running_state()
        self.editors_panel.set_dropdowns_state("disabled")
        self.results_panel.reset("Идёт анализ программ...")

        self.worker.start(text_a, text_b, lang)

    def toggle_pause(self):
        is_paused = self.worker.toggle_pause()
        self.controls_panel.set_paused_state(is_paused)

    def cancel_comparison(self):
        self.controls_panel.progress_label.configure(text="Отмена операции...")
        self.worker.cancel()

    def _on_worker_progress(self, pct: int, label: str):
        self.after(0, lambda: self.controls_panel.update_progress(pct, label))

    def _on_worker_cancelled(self):
        def _cb():
            self.controls_panel.reset_progress("Операция отменена")
            self.controls_panel.set_idle_state()
            self.editors_panel.set_dropdowns_state(tk.NORMAL)
            self.results_panel.reset("Проверка была отменена пользователем")
            self.diff_panel.clear()

        self.after(0, _cb)

    def _on_worker_complete(self, result: dict, highlight_data: dict):
        def _cb():
            self.results_panel.show_results(result)
            self.diff_panel.render(highlight_data)
            self.controls_panel.set_idle_state()
            self.editors_panel.set_dropdowns_state(tk.NORMAL)
            self.after(100, lambda: self.canvas.yview_moveto(1.0))

        self.after(0, _cb)


def main():
    app = AntiPlagApp()
    app.mainloop()


if __name__ == "__main__":
    main()
