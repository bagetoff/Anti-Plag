import random
import threading
import time

import compare_cpp
import compare_pas
import compare_py
import highlights


class ComparisonWorker:
    def __init__(self, on_progress, on_complete, on_cancel):
        self.on_progress = on_progress
        self.on_complete = on_complete
        self.on_cancel = on_cancel

        self._thread = None
        self._cancel_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()
        self.is_paused = False

    def start(self, text_a: str, text_b: str, lang: str):
        self._cancel_event.clear()
        self._pause_event.set()
        self.is_paused = False

        self._thread = threading.Thread(
            target=self._run_pipeline,
            args=(text_a, text_b, lang),
            daemon=True
        )
        self._thread.start()

    def toggle_pause(self) -> bool:
        if self.is_paused:
            self._pause_event.set()
            self.is_paused = False
        else:
            self._pause_event.clear()
            self.is_paused = True
        return self.is_paused

    def cancel(self):
        self._cancel_event.set()
        self._pause_event.set()

    def _wait_or_cancel(self) -> bool:
        self._pause_event.wait()
        return self._cancel_event.is_set()

    def _run_pipeline(self, text_a: str, text_b: str, lang: str):
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
                self.on_cancel()
                return

            self.on_progress(pct, label)
            time.sleep(random.choice([0.6, 0.8, 1.0]))

        if self._wait_or_cancel():
            self.on_cancel()
            return

        if lang == "C++":
            result = compare_cpp.compare(text_a, text_b)
        elif lang == "Pascal ABC":
            result = compare_pas.compare(text_a, text_b)
        else:
            result = compare_py.compare(text_a, text_b)

        highlight_data = highlights.get_highlights(text_a, text_b, lang)

        if self._wait_or_cancel():
            self.on_cancel()
            return

        self.on_progress(93, "Подсчёт итога")
        time.sleep(0.4)

        self.on_progress(100, "Готово!")
        time.sleep(0.3)

        self.on_complete(result, highlight_data)