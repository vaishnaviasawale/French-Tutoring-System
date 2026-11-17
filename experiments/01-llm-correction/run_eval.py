"""Compare local LLMs (via Ollama) on French error detection, correction, and concept tagging.

    uv run python 01-llm-correction/run_eval.py --models qwen3:4b qwen3:8b
    uv run python 01-llm-correction/run_eval.py --models qwen3:8b --think --limit 5

Uses only the standard library, so no `uv sync` group is needed. Ollama must be running.
"""

import argparse
import json
import re
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
OLLAMA_URL = "http://localhost:11434/api/chat"
CONCEPTS = json.loads((HERE / "concepts.json").read_text())
CONCEPT_NAMES = [c["name"] for c in CONCEPTS]

SYSTEM_PROMPT = """You are a careful French teacher checking one sentence written by a learner.

- has_error: true only if the sentence contains a real grammatical or spelling error in standard French. Style preferences are NOT errors.
- corrected: the minimally corrected sentence (change as little as possible). If there is no error, copy the sentence exactly.
- errors: one entry per error with the original fragment, its correction, one concept tag from the list below, and a one-sentence explanation in English.

Concept tags:
""" + "\n".join(f"- {c['name']}: {c['description']}" for c in CONCEPTS)

# Ollama's structured outputs constrain decoding to this schema.
SCHEMA = {
    "type": "object",
    "properties": {
        "has_error": {"type": "boolean"},
        "corrected": {"type": "string"},
        "errors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "original": {"type": "string"},
                    "correction": {"type": "string"},
                    "concept": {"type": "string", "enum": CONCEPT_NAMES},
                    "explanation": {"type": "string"},
                },
                "required": ["original", "correction", "concept", "explanation"],
            },
        },
    },
    "required": ["has_error", "corrected", "errors"],
}


def chat(model: str, sentence: str, think: bool) -> tuple[dict, bool]:
    """Return (response, think_applied). think_applied is False if the model rejected the flag."""
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": sentence},
        ],
        "format": SCHEMA,
        "stream": False,
        "think": think,
        "options": {"temperature": 0},
    }
    try:
        return _post(body), think
    except urllib.error.HTTPError as e:
        # Models without a thinking mode reject the "think" field.
        if e.code == 400 and "think" in e.read().decode():
            del body["think"]
            return _post(body), False
        raise


def _post(body: dict) -> dict:
    req = urllib.request.Request(
        OLLAMA_URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=900) as resp:
        return json.load(resp)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text).replace("’", "'")
    return re.sub(r"\s+", " ", text).strip()


def grade(gold: dict, pred: dict, text: str) -> dict:
    # Models sometimes set has_error inconsistently with `corrected`, so derive detection from the text itself.
    pred = {**pred, "has_error": normalize(pred["corrected"]) != normalize(text)}
    pred_concepts = {e["concept"] for e in pred["errors"]}
    return {
        "detect_ok": pred["has_error"] == gold["has_error"],
        "false_positive": pred["has_error"] and not gold["has_error"],
        "missed": gold["has_error"] and not pred["has_error"],
        "fix_exact": normalize(pred["corrected"]) == normalize(gold["corrected"]),
        # Only meaningful for sentences that actually contain errors.
        "concept_ok": set(gold["concepts"]) <= pred_concepts if gold["has_error"] else None,
    }


def summarize(model: str, rows: list[dict]) -> dict:
    n_err = sum(r["gold"]["has_error"] for r in rows)
    n_ok = len(rows) - n_err
    concept_rows = [r for r in rows if r["metrics"]["concept_ok"] is not None]
    return {
        "model": model,
        "n": len(rows),
        "detect_acc": sum(r["metrics"]["detect_ok"] for r in rows) / len(rows),
        "false_pos": f"{sum(r['metrics']['false_positive'] for r in rows)}/{n_ok}",
        "missed": f"{sum(r['metrics']['missed'] for r in rows)}/{n_err}",
        "fix_exact": sum(r["metrics"]["fix_exact"] for r in rows) / len(rows),
        "concept_recall": (
            sum(r["metrics"]["concept_ok"] for r in concept_rows) / len(concept_rows) if concept_rows else 0
        ),
        "sec/sent": sum(r["latency_s"] for r in rows) / len(rows),
        "tok/s": sum(r["tok_per_s"] for r in rows) / len(rows),
    }


def print_table(summaries: list[dict]) -> None:
    cols = list(summaries[0])
    fmt = lambda v: f"{v:.2f}" if isinstance(v, float) else str(v)
    widths = [max(len(c), *(len(fmt(s[c])) for s in summaries)) for c in cols]
    print("  ".join(c.ljust(w) for c, w in zip(cols, widths)))
    for s in summaries:
        print("  ".join(fmt(s[c]).ljust(w) for c, w in zip(cols, widths)))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models", nargs="+", default=["qwen3:4b"])
    ap.add_argument("--data", type=Path, default=HERE / "test_sentences.jsonl")
    ap.add_argument("--think", action="store_true", help="enable thinking mode (slower, maybe more accurate)")
    ap.add_argument("--limit", type=int, help="only run the first N sentences")
    args = ap.parse_args()

    gold_rows = [json.loads(line) for line in args.data.read_text().splitlines() if line.strip()]
    gold_rows = gold_rows[: args.limit]
    out_path = HERE / "results" / f"{datetime.now():%Y%m%d-%H%M%S}.jsonl"

    summaries = []
    with out_path.open("w") as out:
        for model in args.models:
            print(f"\n=== {model} (think={args.think}) ===")
            rows = []
            warned = False
            for gold in gold_rows:
                resp, think_applied = chat(model, gold["text"], args.think)
                if args.think and not think_applied and not warned:
                    print(f"WARNING: {model} has no thinking mode; running WITHOUT thinking.")
                    warned = True
                pred = json.loads(resp["message"]["content"])
                metrics = grade(gold, pred, gold["text"])
                row = {
                    "model": model,
                    "think": think_applied,
                    "think_requested": args.think,
                    "gold": gold,
                    "pred": pred,
                    "metrics": metrics,
                    "latency_s": resp["total_duration"] / 1e9,
                    "tok_per_s": resp["eval_count"] / (resp["eval_duration"] / 1e9),
                }
                rows.append(row)
                out.write(json.dumps(row, ensure_ascii=False) + "\n")

                mark = "ok " if metrics["detect_ok"] and metrics["fix_exact"] else "XX "
                print(f"{mark}{gold['id']}  {gold['text']}")
                if mark == "XX ":
                    print(f"     expected: {gold['corrected']}")
                    print(f"     got:      {pred['corrected']}  {[e['concept'] for e in pred['errors']]}")
            summaries.append(summarize(model, rows))

    print()
    print_table(summaries)
    print(f"\nFull outputs (incl. explanations): {out_path}")


if __name__ == "__main__":
    main()
