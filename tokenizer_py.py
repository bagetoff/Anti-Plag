import re

KEYWORDS = {
    "and", "as", "assert", "async", "await", "break", "case", "class", "continue",
    "def", "del", "elif", "else", "except", "False", "finally", "for", "from",
    "global", "if", "import", "in", "is", "lambda", "match", "None", "nonlocal",
    "not", "or", "pass", "raise", "return", "True", "try", "while", "with", "yield",
}

TYPES = {
    "bool", "bytearray", "bytes", "complex", "dict", "float", "frozenset", "int",
    "list", "memoryview", "object", "range", "set", "slice", "str", "tuple", "type",
}

BUILTINS = {
    "abs", "all", "any", "ascii", "bin", "callable", "chr", "classmethod",
    "compile", "delattr", "dir", "divmod", "enumerate", "eval", "exec", "filter",
    "format", "getattr", "globals", "hasattr", "hash", "help", "hex", "id",
    "input", "isinstance", "issubclass", "iter", "len", "locals", "map", "max",
    "min", "next", "oct", "open", "ord", "pow", "print", "property", "repr",
    "reversed", "round", "setattr", "sorted", "staticmethod", "sum", "super",
    "vars", "zip", "__import__", "self", "cls", "__init__", "__name__", "__main__",
}

token_spec = [
    ("COMMENT_LINE", r"#[^\n]*"),
    ("STRING",
        r"(?:[rRfFbBuU]{1,2})?"
        r"(?:'''[\s\S]*?'''|\"\"\"[\s\S]*?\"\"\"|'(?:\\.|[^'\\\n])*'|\"(?:\\.|[^\"\\\n])*\")"),
    ("NUMBER",
        r"0[xX][0-9a-fA-F_]+"
        r"|0[bB][01_]+"
        r"|0[oO][0-7_]+"
        r"|\d[\d_]*\.[\d_]*(?:[eE][+-]?[\d_]+)?[jJ]?"
        r"|\.[\d_]+(?:[eE][+-]?[\d_]+)?[jJ]?"
        r"|\d[\d_]*[eE][+-]?[\d_]+[jJ]?"
        r"|\d[\d_]*[jJ]?"),
    ("IDENT", r"[A-Za-z_]\w*"),
    ("OP",
        r"\*\*=|//=|<<=|>>=|\+=|-=|\*=|/=|%=|&=|\|=|\^=|:=|->|"
        r"\*\*|//|<<|>>|<=|>=|==|!=|"
        r"[+\-*/%&|^~<>!()\[\]{},.:;=@]"),
    ("NEWLINE", r"\n"),
    ("SKIP", r"[ \t\r]+"),
    ("MISMATCH", r"."),
]

master_re = re.compile(
    "|".join(f"(?P<{name}>{pattern})" for name, pattern in token_spec),
    re.DOTALL,
)

ignored = {"COMMENT_LINE", "NEWLINE", "SKIP", "MISMATCH"}


def classify_ident(value: str) -> str:
    if value in KEYWORDS:
        return "KEYWORD"
    if value in TYPES:
        return "TYPE"
    if value in BUILTINS:
        return "BUILTIN"
    return "IDENT"


def tokenize_core(text: str):
    tokens = []

    for match in master_re.finditer(text):
        kind = match.lastgroup
        value = match.group()

        if kind in ignored:
            continue

        if kind == "IDENT":
            kind = classify_ident(value)

        tokens.append((kind, value))

    return tokens


def tokenize_py(code: str):
    return tokenize_core(code)