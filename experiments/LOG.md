# Lab log

One entry per experiment, newest first. Keep entries short. The important line is **"Changes to plan"**.

<!--
## YYYY-MM-DD — <track>: <what you tried>
**Question:**
**Setup:** model / params / data
**Result:** numbers, observations, surprises
**Changes to plan:** none | what to update in planning.md
**Next:**
-->

## 2026-11-15 — 01 LLM: qwen3:4b / qwen3:8b / mistral-small, with and without thinking
**Question:** Which local model can detect, fix and tag French errors well enough to feed the mastery tracker, at an acceptable CPU speed?
**Setup:** 18 sentences (13 with errors, 5 correct), temperature 0, one run per config. Full write-up: `01-llm-correction/results/analysis.md`.
**Result:**
- mistral-small is perfect (detect 1.00, fix 1.00, concept recall 1.00) but takes about 31 s per sentence at 2.6 tok/s.
- qwen3:4b is fast (3.1 s) but weak: fix 0.78, concept recall 0.54. qwen3:8b is no better (fix 0.83, recall 0.46) and 2.4 times slower.
- Both Qwen sizes fail s10 (passé composé vs imparfait) and s13 (que → dont) in every config.
- Thinking mode hurts: 50 to 95 s per sentence, new elision errors, and false positives on correct sentences (8b: 2/5, including the s12 trap).
- mistral-small has no thinking mode, so Ollama rejects `--think` and the script silently retries without it.
- **Test set leak:** 7 of 13 error sentences appear as examples in the `concepts.json` descriptions that go into the prompt, so scores are inflated. On the unleaked sentences, Qwen gets 3/6 and mistral 6/6.
**Changes to plan:** proposed, not yet applied: use mistral-small for background error analysis and a small fast model for live conversation; thinking off; drop the Qwen3:8b/14b default in §2 and §9; split the "reply + note errors" step in §5. Needs plan mode because it touches `planning.md`.
**Next:** remove the leaked examples and re-run; add 20+ harder sentences and some of my real mistakes; try gemma3:12b; test a shorter output format for mistral-small; measure it running alongside the chat model.

## 2026-10-28 — first smoke tests (synthetic audio, not my voice yet)
**01 LLM:** qwen3:4b, 5 sentences, no thinking: all detections and corrections right, but concept recall only 0.50. About 3.8 s per sentence at roughly 37 tok/s on CPU.
**02 Pronunciation:** Piper TTS sentences scored by the wav2vec2 espeak model.
- *Correctly* spoken TTS scores only 0.54–0.89. That's a high noise floor.
- The model is weak on /y/ (heard as i/e/u). It swaps nasals (œ̃→ɑ̃, which many native speakers merge anyway). It misses liaison /z/.
- On "Tu as vu la rue ?" it heard the deliberately wrong "vou/rou" perfectly but garbled the correct version. Whisper garbled that clip too ("J'ai avu la rue"), so the TTS audio itself may be poor.
- Whisper transcribed "roue" when "roue" was said. With real-word substitutions it did *not* auto-correct to the reference. Still to test: human non-word mispronunciations.

**10-second takeaway:** raw edit distance against espeak G2P will over-flag errors. Next: record real audio, compare good vs bad *score gaps* rather than absolute scores, and consider GOP or ignoring known free-variation pairs.
**Changes to plan:** none yet. Wait for real recordings before deciding.

## 2026-10-28 — setup
**Result:** Scaffolding created. Piper voices don't expose phoneme timings out of the box. `PiperVoice.load(..., include_alignments=True)` patches the ONNX model in memory, which needs the `onnx` package from `piper-tts[alignment]`.
**Changes to plan:** §6 avatar pipeline: note that Piper alignment needs that flag/extra (verify quality in track 04).
