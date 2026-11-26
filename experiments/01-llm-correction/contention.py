"""Time chat replies with and without error analysis running on a second Ollama model.

    uv run python 01-llm-correction/contention.py
    uv run python 01-llm-correction/contention.py --chat-model qwen3:4b --analysis-model gemma3:12b

Phases: chat alone, analysis alone, then chat while analysis runs in a loop. Reports speed only, not reply quality.
Uses only the standard library. Ollama must be running.
"""

import argparse
import json
import threading
import time
import urllib.request
from datetime import datetime
from pathlib import Path

from run_eval import HERE, OLLAMA_URL, TIMEOUT_S, chat

CHAT_SYSTEM = "Tu es un tuteur de français. Réponds en deux phrases simples et pose une question."
CHAT_PROMPTS = [
    "Bonjour ! Aujourd'hui je suis allé au marché avec ma sœur.",
    "J'aime beaucoup cuisiner le week-end, surtout des plats italiens.",
    "Hier soir, j'ai regardé un film qui m'a vraiment surpris.",
    "Je voudrais visiter Lyon l'été prochain.",
    "Mon travail est intéressant, mais je suis souvent fatigué.",
    "Quand j'étais petit, je jouais au football tous les mercredis.",
]


def chat_turn(model: str, prompt: str) -> dict:
    """Stream one reply, so the wait for the first words can be measured."""
    body = {
        "model": model,
        "messages": [{"role": "system", "content": CHAT_SYSTEM}, {"role": "user", "content": prompt}],
        "think": False,
        "stream": True,
        "options": {"temperature": 0, "num_predict": 80},
    }
    req = urllib.request.Request(
        OLLAMA_URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    start = time.monotonic()
    first = None
    reply = ""
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        for line in resp:
            chunk = json.loads(line)
            if "error" in chunk:
                raise RuntimeError(chunk["error"])
            piece = chunk.get("message", {}).get("content", "")
            if piece and first is None:
                first = time.monotonic() - start
            reply += piece
    return {
        "first_word_s": first,
        "total_s": time.monotonic() - start,
        "load_s": chunk.get("load_duration", 0) / 1e9,
        "tok_per_s": chunk["eval_count"] / (chunk["eval_duration"] / 1e9) if chunk.get("eval_duration") else 0.0,
        "reply": reply,
    }


def analyse(model: str, sentence: str) -> dict:
    resp, _ = chat(model, sentence, think=False, explain=False)
    return {
        "total_s": resp["total_duration"] / 1e9,
        "load_s": resp.get("load_duration", 0) / 1e9,
        "tok_per_s": resp["eval_count"] / (resp["eval_duration"] / 1e9) if resp.get("eval_duration") else 0.0,
    }


def snapshot() -> dict:
    """Which models Ollama has loaded, and how much RAM and swap are left (Linux only)."""
    with urllib.request.urlopen(OLLAMA_URL.replace("/chat", "/ps"), timeout=30) as resp:
        loaded = {m["name"]: round(m["size"] / 1e9, 1) for m in json.load(resp)["models"]}
    mem = dict(line.split(":") for line in Path("/proc/meminfo").read_text().splitlines())
    kib = {k: int(v.split()[0]) for k, v in mem.items()}
    return {
        "loaded_gb": loaded,
        "ram_available_gb": round(kib["MemAvailable"] * 1024 / 1e9, 1),
        "swap_used_gb": round((kib["SwapTotal"] - kib["SwapFree"]) * 1024 / 1e9, 1),
    }


def mean(rows: list[dict], key: str) -> float:
    values = [r[key] for r in rows if r[key] is not None]
    return sum(values) / len(values) if values else float("nan")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--chat-model", default="qwen3:4b")
    ap.add_argument("--analysis-model", default="mistral-small")
    ap.add_argument("--turns", type=int, default=len(CHAT_PROMPTS), help="chat turns per phase (max %(default)s)")
    ap.add_argument("--sentences", type=int, default=4, help="sentences in the analysis-alone phase")
    args = ap.parse_args()

    prompts = CHAT_PROMPTS[: args.turns]
    data = (HERE / "test_sentences.jsonl").read_text().splitlines()
    sentences = [json.loads(line)["text"] for line in data if line.strip()]
    out_path = HERE / "results" / f"contention-{datetime.now():%Y%m%d-%H%M%S}.jsonl"
    rows: list[dict] = []

    with out_path.open("w") as out:

        def record(phase: str, kind: str, result: dict) -> None:
            row = {"phase": phase, "kind": kind, **result, **snapshot()}
            row["model"] = args.chat_model if kind == "chat" else args.analysis_model
            rows.append(row)
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            out.flush()
            print(
                f"{phase:>8} {kind:<8} total {row['total_s']:6.1f} s  load {row['load_s']:5.1f} s  "
                f"{row['tok_per_s']:5.1f} tok/s  RAM free {row['ram_available_gb']} GB  loaded {row['loaded_gb']}"
            )

        chat_turn(args.chat_model, "Salut !")  # warm-up, so loading isn't counted in the first turn
        for p in prompts:
            record("alone", "chat", chat_turn(args.chat_model, p))

        analyse(args.analysis_model, sentences[0])  # warm-up
        for s in sentences[1 : args.sentences + 1]:
            record("alone", "analysis", analyse(args.analysis_model, s))

        stop = threading.Event()
        errors: list[Exception] = []

        def analysis_loop() -> None:
            i = 0
            try:
                while not stop.is_set():
                    result = analyse(args.analysis_model, sentences[i % len(sentences)])
                    record("together", "analysis", result)
                    i += 1
            except Exception as e:  # noqa: BLE001 (re-raised in the main thread)
                errors.append(e)

        worker = threading.Thread(target=analysis_loop, daemon=True)
        worker.start()
        time.sleep(3)  # let the first analysis request get going
        for p in prompts:
            result = chat_turn(args.chat_model, p)
            if errors:  # without analysis running, this turn and later ones would not be "together"
                break
            record("together", "chat", result)
            time.sleep(2)  # the learner takes a moment before the next turn
        stop.set()
        worker.join()
        if errors:
            raise errors[0]

    print(f"\n{'phase':<10}{'kind':<10}{'n':>3}{'first word s':>14}{'total s':>10}{'load s':>9}{'tok/s':>8}")
    for kind in ("chat", "analysis"):
        for phase in ("alone", "together"):
            g = [r for r in rows if r["kind"] == kind and r["phase"] == phase]
            if not g:
                continue
            first = f"{mean(g, 'first_word_s'):.1f}" if kind == "chat" else "-"
            print(
                f"{phase:<10}{kind:<10}{len(g):>3}{first:>14}{mean(g, 'total_s'):>10.1f}"
                f"{mean(g, 'load_s'):>9.1f}{mean(g, 'tok_per_s'):>8.1f}"
            )
    print(f"\nLowest free RAM: {min(r['ram_available_gb'] for r in rows)} GB")
    print(f"Highest swap use: {max(r['swap_used_gb'] for r in rows)} GB")
    print(f"Full outputs (incl. chat replies): {out_path}")


if __name__ == "__main__":
    main()
