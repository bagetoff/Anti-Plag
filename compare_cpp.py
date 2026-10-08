from collections import Counter

import tokenizer_cpp

NUM_PLACEHOLDER = 1
STR_PLACEHOLDER = 2
CHAR_PLACEHOLDER = 3

IDENT_BASE = 10_000

VOCAB_BASE = 100

def encode_tokens(tokens, shared_vocab):
    ident_ids = {}

    next_ident_id = IDENT_BASE
    encoded = []

    for kind, value in tokens:
        if kind == "IDENT":
            if value not in ident_ids:
                ident_ids[value] = next_ident_id
                next_ident_id += 1

            encoded.append(ident_ids[value])
        elif kind == "NUMBER":
            encoded.append(NUM_PLACEHOLDER)
        elif kind == "STRING":
            encoded.append(STR_PLACEHOLDER)
        elif kind == "CHAR":
            encoded.append(CHAR_PLACEHOLDER)
        else:
            key = (kind, value)

            if key not in shared_vocab:
                shared_vocab[key] = len(shared_vocab) + VOCAB_BASE

            encoded.append(shared_vocab[key])

    return encoded


def compare_positions(seq_a, seq_b):
    n = min(len(seq_a), len(seq_b))
    same_position = sum(1 for i in range(n) if seq_a[i] == seq_b[i])

    counter_a = Counter(seq_a)
    counter_b = Counter(seq_b)

    common_total = sum(min(count, counter_b[value]) for value, count in counter_a.items())
    same_value_elsewhere = max(common_total - same_position, 0)

    return {
        "same_position": same_position,
        "same_value_elsewhere": same_value_elsewhere,
        "length_a": len(seq_a),
        "length_b": len(seq_b),
    }


def levenshtein_distance(seq_a, seq_b):
    n, m = len(seq_a), len(seq_b)

    if n == 0:
        return m
    if m == 0:
        return n

    previous_row = list(range(m + 1))

    for i in range(1, n + 1):
        current_row = [i] + [0] * m

        for j in range(1, m + 1):

            cost = 0 if seq_a[i - 1] == seq_b[j - 1] else 1

            current_row[j] = min(
                previous_row[j] + 1,
                current_row[j - 1] + 1,
                previous_row[j - 1] + cost,
            )

        previous_row = current_row

    return previous_row[m]


def levenshtein_similarity(seq_a, seq_b):
    distance = levenshtein_distance(seq_a, seq_b)

    longest = max(len(seq_a), len(seq_b), 1)

    return max(0.0, 1 - distance / longest)


def kgrams(seq, k):
    if len(seq) < k:
        return set()

    return {tuple(seq[i:i + k]) for i in range(len(seq) - k + 1)}


def kgram_similarity(seq_a, seq_b, k=3):
    grams_a = kgrams(seq_a, k)
    grams_b = kgrams(seq_b, k)

    if not grams_a and not grams_b:
        return 1.0

    union = grams_a | grams_b

    if not union:
        return 0.0

    intersection = grams_a & grams_b
    return len(intersection) / len(union)


def compare(text_a, text_b, k=3):
    tokens_a = tokenizer_cpp.tokenize_cpp(text_a)
    tokens_b = tokenizer_cpp.tokenize_cpp(text_b)

    shared_vocab = {}
    seq_a = encode_tokens(tokens_a, shared_vocab)
    seq_b = encode_tokens(tokens_b, shared_vocab)

    positions = compare_positions(seq_a, seq_b)
    lev_sim = levenshtein_similarity(seq_a, seq_b)
    kgram_sim = kgram_similarity(seq_a, seq_b, k)

    overall = round((lev_sim * 0.5 + kgram_sim * 0.5) * 100)

    max_len = max(positions["length_a"], positions["length_b"], 1)
    position_share = round(positions["same_position"] / max_len * 100)

    return {
        "percent": overall,
        "criteria": [
            {
                "name": "Расстояние Левенштейна",
                "value": round(lev_sim * 100),
                "note": f"{positions['length_a']} токенов в 1-ом файле, {positions['length_b']} — во 2-ом файле",
            },
            {
                "name": f"K-строки (k={k})",
                "value": round(kgram_sim * 100),
                "note": f"Доля совпадающих последовательностей из {k} токенов подряд",
            },
            {
                "name": "Совпадение по позициям",
                "value": position_share,
                "note": (
                    f"{positions['same_position']} токенов совпали на тех же позициях, "
                    f"{positions['same_value_elsewhere']} совпали по значению, но в другом месте"
                ),
            },
        ],
    }