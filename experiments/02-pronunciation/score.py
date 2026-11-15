"""Align expected vs spoken phonemes and score the attempt.

    uv run python 02-pronunciation/score.py recordings/s03_bad.wav "Les enfants ont un ami."
    uv run python 02-pronunciation/score.py --phonemes "l e ɑ̃ f ɑ̃ ɔ̃ t œ̃ n a m i" "Les enfants ont un ami."

--phonemes skips the audio model, which is handy for testing the alignment by hand.
"""

import argparse
import json
import unicodedata

from g2p import text_to_phonemes

# Stress and length marks aren't errors we want to penalise (yet).
_STRIP = str.maketrans("", "", "ˈˌːˑ")


def normalize(phone: str) -> str:
    return unicodedata.normalize("NFC", phone).translate(_STRIP)


def align(expected: list[str], actual: list[str]) -> list[dict]:
    """Levenshtein alignment with backtrace. op is one of: match, sub, del (missing), ins (extra)."""
    n, m = len(expected), len(actual)
    dist = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dist[i][0] = i
    for j in range(m + 1):
        dist[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = expected[i - 1] != actual[j - 1]
            dist[i][j] = min(dist[i - 1][j - 1] + cost, dist[i - 1][j] + 1, dist[i][j - 1] + 1)

    ops = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dist[i][j] == dist[i - 1][j - 1] + (expected[i - 1] != actual[j - 1]):
            op = "match" if expected[i - 1] == actual[j - 1] else "sub"
            ops.append({"op": op, "expected": expected[i - 1], "actual": actual[j - 1], "position": i - 1})
            i, j = i - 1, j - 1
        elif i > 0 and dist[i][j] == dist[i - 1][j] + 1:
            ops.append({"op": "del", "expected": expected[i - 1], "actual": None, "position": i - 1})
            i -= 1
        else:
            ops.append({"op": "ins", "expected": None, "actual": actual[j - 1], "position": i})
            j -= 1
    return ops[::-1]


def score_attempt(reference: str, actual: list[str]) -> dict:
    words = text_to_phonemes(reference)
    expected = [normalize(p) for w in words for p in w]
    word_of = [wi for wi, w in enumerate(words) for _ in w]  # expected phoneme index -> word index
    actual = [normalize(p) for p in actual]

    # espeak drops punctuation; if word counts still disagree (numbers, etc.) fall back to indices.
    ref_words = [w for w in reference.split() if any(ch.isalpha() for ch in w)]
    if len(ref_words) != len(words):
        ref_words = [f"word {i + 1}" for i in range(len(words))]

    ops = align(expected, actual)
    errors = [o for o in ops if o["op"] != "match"]
    for o in errors:
        o["word"] = ref_words[word_of[min(o["position"], len(word_of) - 1)]]
    return {
        "reference": reference,
        "expected": " ".join(expected),
        "actual": " ".join(actual),
        "score": max(0.0, 1 - len(errors) / len(expected)),
        "errors": errors,
        "ops": ops,
    }


def print_diff(result: dict) -> None:
    top, bottom = [], []
    for o in result["ops"]:
        e, a = o["expected"] or "·", o["actual"] or "·"
        w = max(len(e), len(a))
        flag = o["op"] != "match"
        top.append(e.ljust(w))
        bottom.append((a if flag else " " * len(a)).ljust(w))
    print("expected:", " ".join(top))
    print("diff:    ", " ".join(bottom), " (blank = match, · = missing/extra)")
    print(f"score:    {result['score']:.2f}")
    for o in result["errors"]:
        print(f"  {o['op']:5} in '{o['word']}': expected {o['expected']!s:4} got {o['actual']}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio", nargs="?", help="recording to score")
    ap.add_argument("reference", help="the sentence that was supposed to be read")
    ap.add_argument("--phonemes", help="space-separated phonemes to score instead of running the audio model")
    ap.add_argument("--json", action="store_true", help="print the full result as JSON")
    args = ap.parse_args()

    if args.phonemes:
        actual = args.phonemes.split()
    else:
        from audio import load_audio
        from phoneme_recog import recognize

        actual = recognize(load_audio(args.audio))

    result = score_attempt(args.reference, actual)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_diff(result)


if __name__ == "__main__":
    main()
