"""Score every recording and check whether the score separates good from bad attempts.

    uv run python 02-pronunciation/compare.py
    uv run python 02-pronunciation/compare.py --whisper small    # also check what Whisper heard

Recordings must be named <sentence id>_<label>.wav, e.g. s03_good.wav, s03_bad.wav (see sentences.txt).
"""

import argparse
import json
from pathlib import Path

from audio import load_audio
from phoneme_recog import recognize
from score import score_attempt

HERE = Path(__file__).parent


def load_sentences() -> dict[str, str]:
    rows = [line.split("|") for line in (HERE / "sentences.txt").read_text().splitlines() if not line.startswith("#")]
    return {r[0].strip(): r[1].strip() for r in rows if len(r) >= 2}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--whisper", help="also transcribe with this Whisper model size")
    args = ap.parse_args()

    sentences = load_sentences()
    whisper = None
    if args.whisper:
        from faster_whisper import WhisperModel

        whisper = WhisperModel(args.whisper, device="cpu", compute_type="int8")

    results = []
    for path in sorted((HERE / "recordings").glob("*.wav")):
        sid, _, label = path.stem.partition("_")
        if sid not in sentences:
            print(f"skip {path.name}: unknown sentence id {sid!r}")
            continue
        audio = load_audio(path)
        result = score_attempt(sentences[sid], recognize(audio))
        result.update(file=path.name, label=label)
        if whisper:
            segments, _ = whisper.transcribe(audio, language="fr")
            result["whisper"] = " ".join(s.text.strip() for s in segments)
        results.append(result)

        errs = ", ".join(f"{o['word']}:{o['expected'] or '·'}→{o['actual'] or '·'}" for o in result["errors"])
        print(f"{path.name:18} score={result['score']:.2f}  {errs}")
        if whisper:
            print(f"{'':18} whisper: {result['whisper']}")

    out = HERE / "results" / "compare.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\nSaved {out}")


if __name__ == "__main__":
    main()
