"""Does Whisper transcribe what you *said* or what you *meant*?

    uv run python 02-pronunciation/asr_check.py recordings/s02_bad.wav --reference "Tu as vu la rue ?"

Prints word-level timestamps and confidence. If Whisper outputs the reference sentence even for a
badly pronounced recording, it can't be used for pronunciation scoring (but is fine for conversation).
Uses faster-whisper (same weights as whisper.cpp, easier from Python). Models download on first use.
"""

import argparse
import difflib
import re

from audio import load_audio
from faster_whisper import WhisperModel


def words_of(text: str) -> list[str]:
    return re.findall(r"[\w'’-]+", text.lower())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio")
    ap.add_argument("--reference", help="sentence you meant to read")
    ap.add_argument("--model", default="small", help="tiny | base | small | medium | large-v3 | large-v3-turbo")
    args = ap.parse_args()

    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    # Pass decoded samples: faster-whisper's own PyAV decoding breaks with some PyAV versions.
    segments, _ = model.transcribe(load_audio(args.audio), language="fr", word_timestamps=True, beam_size=5)

    words = [w for seg in segments for w in seg.words]
    for w in words:
        bar = "#" * round(w.probability * 10)
        print(f"{w.start:6.2f}-{w.end:5.2f}s  {w.word.strip():15} p={w.probability:.2f} {bar}")

    transcript = "".join(w.word for w in words).strip()
    print(f"\ntranscript: {transcript}")
    if args.reference:
        ref, hyp = words_of(args.reference), words_of(transcript)
        ratio = difflib.SequenceMatcher(None, ref, hyp).ratio()
        print(f"reference:  {args.reference}")
        print(f"word match: {ratio:.2f}  (1.00 = Whisper heard exactly the reference)")


if __name__ == "__main__":
    main()
