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
