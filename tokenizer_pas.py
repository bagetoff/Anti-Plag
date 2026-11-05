import re

KEYWORDS = {
    "and", "as", "begin", "case", "class", "const", "constructor", "destructor",
    "div", "do", "downto", "else", "end", "event", "except", "extensionmethod",
    "final", "finally", "for", "foreach", "function", "goto", "if", "implementation",
    "in", "inherited", "initialization", "interface", "is", "label", "lock", "loop",
    "mod", "nil", "not", "of", "operator", "or", "params", "procedure", "program",
    "property", "raise", "repeat", "sealed", "shl", "shr", "sizeof", "static",
    "template", "then", "to", "try", "type", "typeof", "unit", "until", "uses",
    "var", "virtual", "where", "while", "with", "xor", "yield", "true", "false",
    "break", "continue", "exit",
}

TYPES = {
    "array", "auto", "boolean", "byte", "cardinal", "char", "double", "extended",
    "file", "int64", "integer", "longint", "longword", "real", "record", "sequence",
    "set", "shortint", "single", "smallint", "string", "uint64", "word",
}

BUILTINS = {
    "read", "readln", "write", "writeln", "print", "println",
    "abs", "sqr", "sqrt", "sin", "cos", "ln", "exp", "trunc", "round",
    "inc", "dec", "ord", "chr", "length", "copy", "delete", "insert", "pos",
    "odd", "random", "randomize", "halt", "swap", "min", "max",
}

token_spec = [
    ("COMMENT_CURLY", r"\{.*?\}"),
    ("COMMENT_PAREN", r"\(\*.*?\*\)"),
    ("COMMENT_LINE", r"//[^\n]*"),
    ("STRING", r"'(?:''|[^'\n])*'"),
    ("NUMBER",
        r"\$[0-9a-fA-F]+"
        r"|\d+\.\d*(?:[eE][+-]?\d+)?"
        r"|\.\d+(?:[eE][+-]?\d+)?"
        r"|\d+[eE][+-]?\d+"
        r"|\d+"),
    ("IDENT", r"[A-Za-z_]\w*"),
    ("OP",
        r":=|\+=|-=|\*=|/=|<=|>=|<>|\.\.|"
        r"[+\-*/=<>:;.,^@()\[\]]"),
    ("NEWLINE", r"\n"),
    ("SKIP", r"[ \t\r]+"),
    ("MISMATCH", r"."),
]

master_re = re.compile(
    "|".join(f"(?P<{name}>{pattern})" for name, pattern in token_spec),
    re.DOTALL,
)

ignored = {"COMMENT_CURLY", "COMMENT_PAREN", "COMMENT_LINE", "NEWLINE", "SKIP", "MISMATCH"}


def classify_ident(lower_value: str) -> str:
    if lower_value in KEYWORDS:
        return "KEYWORD"
    if lower_value in TYPES:
        return "TYPE"
    if lower_value in BUILTINS:
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
            lower_value = value.lower()
            kind = classify_ident(lower_value)
            value = lower_value

        tokens.append((kind, value))

    return tokens


def tokenize_pas(code: str):
    return tokenize_core(code)
