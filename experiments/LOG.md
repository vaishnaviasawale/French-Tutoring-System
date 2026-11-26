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

## 2026-11-26 — 01 LLM: two models loaded together, and lenient tag scoring
**Question:** Does chat stay usable while error analysis runs, and how many tag misses are only label overlap?
**Setup:** `contention.py` (qwen3:4b chat, mistral-small analysis, 6 turns per phase), short Ollama probes, `run_eval.py --rescore` on saved outputs (new `also_accept` field in the test sentences). Method and full tables: `01-llm-correction/results/analysis.md`. Ollama 0.32.1, `powersave` governor, one run.
**Result:**
- **Ollama is using an NVIDIA RTX 1000 Ada (6 GB) through Vulkan.** Earlier "CPU only" latencies are wrong about the hardware. Alone, qwen3:4b runs 100% on the GPU, qwen3:8b 77% and mistral-small 29%.
- With mistral-small loaded, qwen3:4b drops from 39 to about 4.5 tok/s even when mistral is idle: only 19% of it stays on the GPU. An 80-token reply went from 2.4 s to 20.2 s while analysis ran. This is the likely cause of the slow 4b run on 11-21.
- Analysis barely changed (2.7 → 2.4 tok/s). Lowest free RAM 16.8 GB; swap rose from 0.3 to 2.2 GB.
- **qwen3:4b does not stop thinking.** With `think: false` (also with `/no_think`) it writes English reasoning as the reply and used up 700 tokens without a final answer. qwen3:8b answered in clean French (1 prompt).
- Lenient tags (s03 and s14 accept overlapping labels), tightened-prompt run: mistral-small 13/13 (strict 11), gemma3:12b 11/13 (9), qwen3:8b 8/13 (6), qwen3:4b 5/13 (4).
**Changes to plan:** pending. The results contradict §2 and §9: qwen3:4b is unfit for conversation as configured, and the two-model setup needs a GPU placement fix. CLAUDE.md also says there is no NVIDIA GPU.
**Next:** run mistral-small on the CPU only (`num_gpu: 0`) so the chat model keeps the GPU; test qwen3:8b as the chat model; then update the plan.

## 2026-11-21 — 01 LLM: clean and tightened prompt, 4 models, no explanations
**Question:** With the answer leak removed, which model should do error correction, and does a stricter "fix only the wrong words" prompt help?
**Setup:** Same 18 sentences, temperature 0, no thinking, `--no-explain`, one run per model. Covers the leak-free re-runs since 11-15. Full write-up: `01-llm-correction/results/analysis.md`.
**Result:**
- mistral-small: detect 1.00, exact fix 18/18 (17/18 before the stricter prompt), 0/5 false positives, concept recall 0.85, 23.6 s per sentence at 2.7 tok/s. The prompt was written after seeing its one miss, so 18/18 is optimistic.
- gemma3:12b: fix 15/18, 1 false positive (s12 trap), recall 0.69, 15.9 s.
- qwen3:8b: fix 14/18, 0 false positives, recall 0.46, 6.2 s. qwen3:4b: fix 12/18, 1 false positive, recall 0.31.
- qwen3:4b decoded at 3.3 tok/s (34 on 11-17), so its 19.1 s latency is anomalous and the cause unknown.
- The stricter prompt did not clearly help gemma or Qwen. Their earlier runs also had explanations, so the cause is not isolated.
- Throughput varies a lot between runs, even with the `performance` governor.
**Changes to plan:** applied. §1, §2 and §9: qwen3:4b for conversation (provisional) and mistral-small for error analysis replace Qwen3:8b/14b; thinking off. §5: reply is sent first, error analysis runs in the background without explanations; mistral-small grades writing. §4 and §5: tag-driven mastery updates on hold until the tags are reliable.
**Next:** fix overlapping concept tags; write 20+ new sentences without looking at model outputs; re-measure qwen3:4b speed; run mistral-small alongside a chat model.

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
