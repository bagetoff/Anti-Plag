from pathlib import Path
from tkinter import filedialog

CPP_EXTENSIONS = {".cpp"}
PYTHON_EXTENSIONS = {".py"}
PAS_EXTENSIONS = {".pas"}
TXT_EXTENSIONS = {".txt"}

ALL_SUPPORTED_EXTENSIONS = (
    CPP_EXTENSIONS | PYTHON_EXTENSIONS | PAS_EXTENSIONS | TXT_EXTENSIONS
)


def select_and_read_file():
    filetypes = [
        ("Поддерживаемые файлы", "*.cpp *.pas *.py *.txt"),
        ("C++ Files", "*.cpp"),
        ("Pascal Files", "*.pas"),
        ("Python Files", "*.py"),
        ("Text Files", "*.txt"),
        ("Все файлы", "*.*"),
    ]

    filepath = filedialog.askopenfilename(
        title="Выберите файл программы",
        filetypes=filetypes
    )

    if not filepath:
        return None

    ext = Path(filepath).suffix.lower()

    if ext not in ALL_SUPPORTED_EXTENSIONS:
        return {
            "ok": False,
            "error": f"Неподдерживаемое расширение файла '{ext}'. Разрешены только: .cpp, .pas, .py, .txt",
        }

    if ext in CPP_EXTENSIONS:
        detected_lang = "C++"
    elif ext in PAS_EXTENSIONS:
        detected_lang = "Pascal ABC"
    elif ext in PYTHON_EXTENSIONS:
        detected_lang = "Python"
    else:
        detected_lang = "Не выбран"

    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        return {
            "ok": False,
            "error": f"Ошибка чтения файла: {e}",
        }

    return {
        "ok": True,
        "ext": ext,
        "lang": detected_lang,
        "content": content,
    }


def validate_inputs(lang_a: str, lang_b: str, text_a: str, text_b: str, silent_empty: bool = True):
    if lang_a == "Не выбран" and lang_b == "Не выбран":
        return False, "Загружены файлы .txt — выберите язык программирования над обоими полями кода", False

    if lang_a == "Не выбран":
        return False, "Для 1-ой программы (.txt) необходимо выбрать язык программирования в списке сверху", False

    if lang_b == "Не выбран":
        return False, "Для 2-ой программы (.txt) необходимо выбрать язык программирования в списке сверху", False

    if lang_a != lang_b:
        return (
            False,
            f"Сравнение невозможно: выбраны разные языки программирования ({lang_a} и {lang_b})",
            True,
        )

    if not silent_empty:
        clean_a = text_a.strip()
        clean_b = text_b.strip()

        if not clean_a and not clean_b:
            return False, "Оба поля кода пусты — загрузите файлы или вставьте код для сравнения", True
        if not clean_a:
            return False, "Поле 1-ой программы пустое — загрузите файл или вставьте исходный код", True
        if not clean_b:
            return False, "Поле 2-ой программы пустое — загрузите файл или вставьте исходный код", True

    return True, "", False