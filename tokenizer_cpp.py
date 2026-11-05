import re

KEYWORDS = {
    "alignas", "alignof", "and", "and_eq", "asm", "atomic_cancel", "atomic_commit",
    "atomic_noexcept", "bitand", "bitor", "break", "case", "catch", "class",
    "compl", "concept", "const", "consteval", "constexpr", "constinit", "const_cast",
    "continue", "co_await", "co_return", "co_yield", "decltype", "default", "delete",
    "do", "dynamic_cast", "else", "enum", "explicit", "export", "extern", "false",
    "for", "friend", "goto", "if", "inline", "mutable", "namespace", "new",
    "noexcept", "not", "not_eq", "nullptr", "operator", "or", "or_eq", "private",
    "protected", "public", "register", "reinterpret_cast", "requires", "return",
    "sizeof", "static", "static_assert", "static_cast", "struct", "switch",
    "template", "this", "thread_local", "throw", "true", "try", "typedef", "typeid",
    "typename", "union", "using", "virtual", "volatile", "while", "xor", "xor_eq",
}

TYPES = {
    "auto", "bool", "char", "char8_t", "char16_t", "char32_t", "double", "float",
    "int", "long", "short", "signed", "unsigned", "void", "wchar_t", "size_t",
    "int8_t", "int16_t", "int32_t", "int64_t", "uint8_t", "uint16_t", "uint32_t", "uint64_t",
    "string", "vector", "map", "set", "unordered_map", "unordered_set", "pair",
    "queue", "stack", "deque", "list", "array",
}

BUILTINS = {
    "std", "main", "cin", "cout", "cerr", "clog", "endl", "ws",
    "printf", "scanf", "puts", "gets", "getchar", "putchar",
    "sort", "swap", "min", "max", "abs", "sqrt", "pow", "sin", "cos", "tan",
    "malloc", "calloc", "realloc", "free", "exit", "abort",
}

token_spec = [
    ("COMMENT_BLOCK", r"/\*.*?\*/"),
    ("COMMENT_LINE", r"//[^\n]*"),
    ("STRING", r'"(?:\\.|[^"\\])*"'),
    ("CHAR", r"'(?:\\.|[^'\\])*'"),
    ("NUMBER",
        r"0[xX][0-9a-fA-F]+[uUlL]*"
        r"|\d+\.\d*(?:[eE][+-]?\d+)?[fFlL]?"
        r"|\.\d+(?:[eE][+-]?\d+)?[fFlL]?"
        r"|\d+[eE][+-]?\d+[fFlL]?"
        r"|\d+[uUlL]*"),
    ("IDENT", r"[A-Za-z_]\w*"),
    ("OP",
        r"<<=|>>=|\.\.\.|->\*|"
        r"::|->|\+\+|--|<<|>>|<=|>=|==|!=|&&|\|\||"
        r"\+=|-=|\*=|/=|%=|&=|\|=|\^=|##|"
        r"[+\-*/%=<>!&|^~.,;:?(){}\[\]#]"),
    ("NEWLINE", r"\n"),
    ("SKIP", r"[ \t\r]+"),
    ("MISMATCH", r"."),
]

master_re = re.compile(
    "|".join(f"(?P<{name}>{pattern})" for name, pattern in token_spec),
    re.DOTALL,
)

ignored = {"COMMENT_BLOCK", "COMMENT_LINE", "NEWLINE", "SKIP", "MISMATCH"}
preproc_line_re = re.compile(r"^[ \t]*#(?:.*\\\r?\n)*.*$", re.MULTILINE)
include_target_re = re.compile(r'<[^>\n]+>|"[^"\n]+"')


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


def tokenize_preprocessor_line(raw: str):
    tokens = [("PP_HASH", "#")]
    text = raw.lstrip()[1:]

    m = re.match(r"\s*([A-Za-z_]\w*)", text)

    if not m:
        return tokens

    directive = m.group(1)
    tokens.append(("PP_DIRECTIVE", directive))
    remainder = text[m.end():]

    if directive == "include":
        hm = include_target_re.search(remainder)

        if hm:
            tokens.append(("PP_HEADER", hm.group()))
    else:
        tokens.extend(tokenize_core(remainder))

    return tokens


def tokenize_cpp(code: str):
    tokens = []
    pos = 0

    for match in preproc_line_re.finditer(code):
        start, end = match.span()

        if start > pos:
            tokens.extend(tokenize_core(code[pos:start]))

        tokens.extend(tokenize_preprocessor_line(match.group()))
        pos = end

    if pos < len(code):
        tokens.extend(tokenize_core(code[pos:]))

    return tokens
