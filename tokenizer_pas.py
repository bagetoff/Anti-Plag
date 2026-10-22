import re

KEYWORDS = {
    "and", "array", "as", "auto", "begin", "case", "class", "const", "constructor",
    "destructor", "div", "do", "downto", "else", "end", "event", "except", "extensionmethod",
    "file", "final", "finally", "for", "foreach", "function", "goto", "if", "implementation",
    "in", "inherited", "initialization", "interface", "is", "label", "lock", "loop",
    "mod", "nil", "not", "of", "operator", "or", "params", "procedure", "program",
    "property", "raise", "record", "repeat", "sealed", "sequence", "set", "shl", "shr",
    "sizeof", "static", "template", "then", "to", "try", "type", "typeof", "unit",
    "until", "uses", "var", "virtual", "where", "while", "with", "xor", "yield",
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


def tokenize_core(text: str):
    tokens = []

    for match in master_re.finditer(text):
        kind = match.lastgroup
        value = match.group()

        if kind in ignored:
            continue

        if kind == "IDENT":
            lower_value = value.lower()

            if lower_value in KEYWORDS:
                kind = "KEYWORD"
                value = lower_value
            else:
                value = lower_value

        tokens.append((kind, value))

    return tokens


def tokenize_pas(code: str):
    return tokenize_core(code)