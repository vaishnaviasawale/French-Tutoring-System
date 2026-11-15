"""Text -> expected French phonemes (espeak-ng via phonemizer).

uv run python 02-pronunciation/g2p.py "Les enfants ont un ami."
"""

import sys

from phonemizer import phonemize
from phonemizer.separator import Separator


def text_to_phonemes(text: str) -> list[list[str]]:
    """One list of phonemes per word. Liaison consonants attach to the end of the word (les -> l e z)."""
    out = phonemize(text, language="fr-fr", backend="espeak", strip=True, separator=Separator(phone=" ", word="|"))
    return [word.split() for word in out.split("|") if word.strip()]


if __name__ == "__main__":
    text = " ".join(sys.argv[1:]) or "Les enfants ont un ami."
    for word, phones in zip(text.split(), text_to_phonemes(text)):
        print(f"{word:15} {' '.join(phones)}")
