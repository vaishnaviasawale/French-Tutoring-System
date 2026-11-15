"""Turn a Piper phoneme timeline into a viseme (mouth shape) timeline.

    uv run python 04-tts-avatar/visemes.py 04-tts-avatar/results/sample.json

Writes results/<name>.visemes.json, which viseme_player.html plays back in sync with the wav.
Piper aligns per Unicode codepoint, so nasal ɑ̃ arrives as 'ɑ' + combining tilde, and stress marks
get their own durations. Those are folded into the neighbouring phoneme here.
"""

import json
import sys
import unicodedata
from pathlib import Path

# ~12 shapes is plenty for a 2D avatar. Nasal vowels share the mouth shape of their oral vowel.
_GROUPS = {
    "MBP": "pbm",  # lips closed
    "FV": "fv",  # lower lip to teeth
    "TDNL": "tdnlɲ",  # tongue behind teeth, mouth slightly open
    "SZ": "sz",  # teeth together, spread
    "CH": "ʃʒ",  # lips pushed forward
    "KGR": "kgʁʀrxŋ",  # back of the tongue, jaw relaxed
    "AA": "aɑ",  # wide open
    "EI": "eɛij",  # spread
    "O": "oɔ",  # rounded, open
    "U": "uywɥ",  # tightly rounded
    "EU": "øœə",  # rounded, mid
}
PHONEME_TO_VISEME = {ch: v for v, chars in _GROUPS.items() for ch in chars}
SILENCE = set("^$_.,;:!?…")
# Word-boundary spaces are included: connected speech doesn't close the mouth between words.
MODIFIERS = set("ˈˌːˑ- ")


def merge_modifiers(timeline: list[dict]) -> list[dict]:
    """Fold combining marks, stress/length marks and word spaces into the previous phoneme."""
    out: list[dict] = []
    for t in timeline:
        p = t["phoneme"]
        is_mod = p in MODIFIERS or all(unicodedata.combining(c) for c in p)
        if is_mod and out:
            out[-1]["end_ms"] = t["end_ms"]
            if p not in MODIFIERS:
                out[-1]["phoneme"] = unicodedata.normalize("NFC", out[-1]["phoneme"] + p)
        else:
            out.append(dict(t))
    return out


def to_visemes(timeline: list[dict]) -> tuple[list[dict], set[str]]:
    visemes, unknown = [], set()
    for t in merge_modifiers(timeline):
        base = t["phoneme"][0]
        if t["phoneme"] in SILENCE:
            v = "rest"
        elif base in PHONEME_TO_VISEME:
            v = PHONEME_TO_VISEME[base]
        else:
            v = "rest"
            unknown.add(t["phoneme"])
        if visemes and visemes[-1]["viseme"] == v:
            visemes[-1]["end_ms"] = t["end_ms"]
        else:
            visemes.append({"viseme": v, "start_ms": t["start_ms"], "end_ms": t["end_ms"], "phonemes": ""})
        visemes[-1]["phonemes"] += t["phoneme"]
    return visemes, unknown


if __name__ == "__main__":
    path = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "results" / "sample.json")
    visemes, unknown = to_visemes(json.loads(path.read_text()))
    for v in visemes:
        print(f"{v['start_ms']:6}-{v['end_ms']:<6} {v['viseme']:5} {v['phonemes']}")
    if unknown:
        print(f"\nunmapped phonemes (shown as rest): {sorted(unknown)}")
    out = path.with_suffix(".visemes.json")
    out.write_text(json.dumps(visemes, ensure_ascii=False, indent=1))
    print(f"\nSaved {out}")
