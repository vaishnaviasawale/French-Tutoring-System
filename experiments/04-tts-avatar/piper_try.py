"""Synthesize French with Piper and extract per-phoneme timings (the input for lip-sync).

    uv run python -m piper.download_voices fr_FR-siwis-medium --download-dir 04-tts-avatar/voices
    uv run python 04-tts-avatar/piper_try.py "Bonjour ! Aujourd'hui, on va parler de ton week-end."

Writes results/<name>.wav and results/<name>.json ([{phoneme, start_ms, end_ms}, ...]).
Stock Piper voices don't output timings; include_alignments=True patches the ONNX model in memory.
"""

import argparse
import json
import time
import wave
from pathlib import Path

import numpy as np
from piper import PiperVoice

HERE = Path(__file__).parent


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("text", nargs="?", default="Bonjour ! Aujourd'hui, on va parler de ton week-end.")
    ap.add_argument("--voice", type=Path, default=HERE / "voices" / "fr_FR-siwis-medium.onnx")
    ap.add_argument("--name", default="sample", help="output file stem in results/")
    args = ap.parse_args()

    voice = PiperVoice.load(args.voice, include_alignments=True)
    t0 = time.perf_counter()
    chunks = list(voice.synthesize(args.text, include_alignments=True))
    elapsed = time.perf_counter() - t0

    sr = chunks[0].sample_rate
    timeline, chunk_start = [], 0
    for chunk in chunks:
        if chunk.phoneme_alignments is None:
            print("! no alignments for chunk:", "".join(chunk.phonemes))
        else:
            pos = chunk_start
            for a in chunk.phoneme_alignments:
                start_ms, end_ms = 1000 * pos / sr, 1000 * (pos + a.num_samples) / sr
                timeline.append({"phoneme": a.phoneme, "start_ms": round(start_ms), "end_ms": round(end_ms)})
                pos += a.num_samples
        chunk_start += len(chunk.audio_int16_array)

    audio = np.concatenate([c.audio_int16_array for c in chunks])
    wav_path, json_path = HERE / "results" / f"{args.name}.wav", HERE / "results" / f"{args.name}.json"
    with wave.open(str(wav_path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes(audio.tobytes())
    json_path.write_text(json.dumps(timeline, ensure_ascii=False, indent=1))

    duration = len(audio) / sr
    print(f"audio {duration:.2f}s, synthesized in {elapsed:.2f}s (real-time factor {elapsed / duration:.2f})")
    for t in timeline:
        print(f"{t['start_ms']:6}-{t['end_ms']:<6} {t['phoneme']!r}")
    print(f"\nSaved {wav_path}\n      {json_path}")


if __name__ == "__main__":
    main()
