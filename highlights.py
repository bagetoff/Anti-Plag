import difflib
import re

import tokenizer_cpp
import tokenizer_pas
import tokenizer_py


def _tokenize_cpp_with_spans(code: str):
    spans = []
    pos = 0

    def process_core(segment, offset):
        for match in tokenizer_cpp.master_re.finditer(segment):
            kind = match.lastgroup
            value = match.group()

            if kind in tokenizer_cpp.ignored:
                continue

            if kind == "IDENT":
                kind = tokenizer_cpp.classify_ident(value)

            spans.append({
                "kind": kind,
                "value": value,
                "start": offset + match.start(),
                "end": offset + match.end(),
            })

    def process_preproc(raw, offset):
        stripped = raw.lstrip()
        lead_ws = len(raw) - len(stripped)
        hash_pos = offset + lead_ws

        spans.append({
            "kind": "PP_HASH",
            "value": "#",
            "start": hash_pos,
            "end": hash_pos + 1,
        })

        text = stripped[1:]
        m = re.match(r"\s*([A-Za-z_]\w*)", text)
        if not m:
            return

        directive = m.group(1)
        dir_start = hash_pos + 1 + m.start(1)
        dir_end = hash_pos + 1 + m.end(1)

        spans.append({
            "kind": "PP_DIRECTIVE",
            "value": directive,
            "start": dir_start,
            "end": dir_end,
        })

        rem_offset = hash_pos + 1 + m.end()
        remainder = text[m.end():]

        if directive == "include":
            hm = tokenizer_cpp.include_target_re.search(remainder)
            if hm:
                spans.append({
                    "kind": "PP_HEADER",
                    "value": hm.group(),
                    "start": rem_offset + hm.start(),
                    "end": rem_offset + hm.end(),
                })
        else:
            process_core(remainder, rem_offset)

    for match in tokenizer_cpp.preproc_line_re.finditer(code):
        start, end = match.span()
        if start > pos:
            process_core(code[pos:start], pos)
        process_preproc(match.group(), start)
        pos = end

    if pos < len(code):
        process_core(code[pos:], pos)

    return spans


def _tokenize_pas_with_spans(code: str):
    spans = []

    for match in tokenizer_pas.master_re.finditer(code):
        kind = match.lastgroup
        value = match.group()

        if kind in tokenizer_pas.ignored:
            continue

        if kind == "IDENT":
            lower_value = value.lower()
            kind = tokenizer_pas.classify_ident(lower_value)
            value = lower_value

        spans.append({
            "kind": kind,
            "value": value,
            "start": match.start(),
            "end": match.end(),
        })

    return spans


def _tokenize_py_with_spans(code: str):
    spans = []

    for match in tokenizer_py.master_re.finditer(code):
        kind = match.lastgroup
        value = match.group()

        if kind in tokenizer_py.ignored:
            continue

        if kind == "IDENT":
            kind = tokenizer_py.classify_ident(value)

        spans.append({
            "kind": kind,
            "value": value,
            "start": match.start(),
            "end": match.end(),
        })

    return spans


def _normalize_for_comparison(spans):
    normalized = []

    for item in spans:
        kind = item["kind"]
        value = item["value"]

        if kind in {"IDENT", "NUMBER", "STRING", "CHAR"}:
            norm_key = (kind,)
        else:
            norm_key = (kind, value)

        normalized.append(norm_key)

    return normalized


def _mark_statuses(spans_a, spans_b, seq_a, seq_b):
    matcher = difflib.SequenceMatcher(None, seq_a, seq_b, autojunk=False)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        status = "match" if tag == "equal" else "diff"

        for i in range(i1, i2):
            spans_a[i]["status"] = status
        for j in range(j1, j2):
            spans_b[j]["status"] = status


def _build_line_offsets(text: str):
    lines = text.splitlines(keepends=True)
    if not lines and text == "":
        return [("", 0, 0)]

    result = []
    offset = 0
    for line in lines:
        clean_line = line.rstrip("\r\n")
        result.append((clean_line, offset, offset + len(clean_line)))
        offset += len(line)

    return result


def _build_code_lines(text: str, spans):
    line_infos = _build_line_offsets(text)
    rendered_lines = []

    span_idx = 0
    num_spans = len(spans)

    for line_no, (line_text, line_start, line_end) in enumerate(line_infos, start=1):
        while span_idx < num_spans and spans[span_idx]["end"] <= line_start:
            span_idx += 1

        temp_idx = span_idx
        line_spans = []
        while temp_idx < num_spans and spans[temp_idx]["start"] < line_end:
            line_spans.append(spans[temp_idx])
            temp_idx += 1

        if not line_spans:
            rendered_lines.append({
                "line_no": line_no,
                "line_tag": "neutral",
                "segments": [(line_text, "neutral")],
            })
            continue

        has_diff = any(s["status"] == "diff" for s in line_spans)
        line_tag = "diff_line" if has_diff else "neutral"

        segments = []
        cursor = line_start

        for s in line_spans:
            s_start = max(s["start"], line_start)
            s_end = min(s["end"], line_end)

            if s_start > cursor:
                segments.append((line_text[cursor - line_start:s_start - line_start], line_tag))

            tok_tag = "diff_token" if s["status"] == "diff" else line_tag
            segments.append((line_text[s_start - line_start:s_end - line_start], tok_tag))
            cursor = s_end

        if cursor < line_end:
            segments.append((line_text[cursor - line_start:], line_tag))

        rendered_lines.append({
            "line_no": line_no,
            "line_tag": line_tag,
            "segments": segments,
        })

    return rendered_lines


def _build_token_lines(spans):
    rendered_lines = []

    for idx, s in enumerate(spans, start=1):
        is_diff = s["status"] == "diff"
        line_tag = "diff_line" if is_diff else "neutral"
        tok_tag = "diff_token" if is_diff else "neutral"

        kind_str = f"{s['kind']:<14}"
        val_str = s["value"].replace("\n", "\\n")

        segments = [
            (kind_str, tok_tag),
            (" | ", line_tag),
            (val_str, tok_tag),
        ]

        rendered_lines.append({
            "line_no": idx,
            "line_tag": line_tag,
            "segments": segments,
        })

    return rendered_lines


def get_highlights(text_a: str, text_b: str, lang: str):
    if lang == "Pascal ABC":
        spans_a = _tokenize_pas_with_spans(text_a)
        spans_b = _tokenize_pas_with_spans(text_b)
    elif lang == "Python":
        spans_a = _tokenize_py_with_spans(text_a)
        spans_b = _tokenize_py_with_spans(text_b)
    else:
        spans_a = _tokenize_cpp_with_spans(text_a)
        spans_b = _tokenize_cpp_with_spans(text_b)

    seq_a = _normalize_for_comparison(spans_a)
    seq_b = _normalize_for_comparison(spans_b)

    _mark_statuses(spans_a, spans_b, seq_a, seq_b)

    return {
        "code": {
            "left": _build_code_lines(text_a, spans_a),
            "right": _build_code_lines(text_b, spans_b),
        },
        "tokens": {
            "left": _build_token_lines(spans_a),
            "right": _build_token_lines(spans_b),
        },
    }
