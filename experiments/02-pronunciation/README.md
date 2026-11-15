# 02 — Pronunciation scoring

**Questions:**
1. Does Whisper "hear" the right French even when you mispronounce it? If so, it can't be used for scoring.
2. Can a phoneme-recognition model plus G2P plus alignment produce a score that separates good attempts from bad ones?
3. Do the phoneme errors land on the sounds you actually got wrong?

## Pipeline

```
reference text --g2p.py-->        expected phonemes ─┐
                                                     ├─ score.py (Levenshtein align) → score + per-word errors
your recording --phoneme_recog.py--> actual phonemes ┘
your recording --asr_check.py--> Whisper transcript  (for question 1)
```

## Run

```bash
uv sync --group speech
uv run python 02-pronunciation/g2p.py "Les enfants ont un ami."

# Record each sentence in sentences.txt twice: once carefully, once with a deliberate mistake.
./02-pronunciation/record.sh s03_good
./02-pronunciation/record.sh s03_bad

uv run python 02-pronunciation/score.py 02-pronunciation/recordings/s03_bad.wav "Les enfants ont un ami."
uv run python 02-pronunciation/asr_check.py 02-pronunciation/recordings/s03_bad.wav --reference "Les enfants ont un ami."
uv run python 02-pronunciation/compare.py --whisper small      # every recording in one table
```

Test the alignment without audio: `score.py --phonemes "l e ɑ̃ f ɑ̃ ..." "Les enfants ont un ami."`

## Things to watch for

- **Symbol mismatch:** the wav2vec2 model and phonemizer both use espeak IPA, but small differences (length marks, ʁ vs r, tie bars) show up as fake errors. `score.normalize()` is where to fix them.
- **Free variation:** many French speakers merge /ɛ̃/ and /œ̃/, and optional liaisons can be skipped. Should those count as errors?
- **Scoring formula:** 1 − edits/length is crude. Once it works, try Goodness of Pronunciation (GOP): use the model's CTC posteriors for the *expected* phoneme instead of argmax decoding.

## Reading

- Witt & Young 2000, *Phone-level pronunciation scoring and assessment for interactive language learning* (GOP).
- Baevski et al. 2020, *wav2vec 2.0*.
- Xu, Baevski & Auli 2021, *Simple and Effective Zero-shot Cross-lingual Phoneme Recognition*: the model used here.
- Radford et al. 2022, *Robust Speech Recognition via Large-Scale Weak Supervision* (Whisper). Its robustness is exactly what makes it bad at catching mistakes.
