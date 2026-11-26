# Track 01 analysis: which model should do French error correction?

Date: first runs 2026-11-15, re-run 2026-11-17 after removing the answer leak and making grading consistent (commit `c2b34a5`). All four models have now been run with the tightened prompt (2026-11-21). CPU only, 18 sentences (13 with an error, 5 correct), temperature 0, one run per config.

**Correction (2026-11-26):** the runs below were most likely not CPU only. Ollama uses the laptop's NVIDIA GPU, and how much of a model fits on it depends on what else is loaded. Treat the latency figures and findings 7 and 10 with that in mind. qwen3:4b also fails as a chat model with thinking off. See [Checks on 2026-11-26](#checks-on-2026-11-26). Accuracy scores are not re-tested.

## Decision (provisional)

- **Use `mistral-small` for error detection and correction, without explanations.** With the tightened prompt it is the only model with perfect detection (18/18, 0/5 false positives), and it fixes all 18 sentences exactly (17 of 18 before). The next best, gemma3:12b, fixes 15. The old miss (s16) was a valid but over-aggressive rewrite. Dropping the `explanation` field (`--no-explain`) cut latency to about 24 s per sentence at full machine speed, with the same accuracy (finding 10). The 18 of 18 is one run, and the prompt was tightened after seeing s16, so it is optimistic (finding 1).
- **Do not treat concept tags as reliable for any model yet.** With the tightened prompt and no explanations, mistral-small tags 11 of 13 correctly (0.85), gemma3:12b 9 of 13 (0.69), qwen3:8b 6 of 13 (0.46) and qwen3:4b 4 of 13 (0.31). The mastery tracker depends on these tags. All of mistral's and gemma's tag misses are label overlaps (finding 4), so a taxonomy fix may be cheaper than a model change.
- **Keep it off the live conversation path.** Even without explanations it takes 24 to 47 s per sentence depending on how fast the machine is running (finding 10), far too slow for the ASR → LLM → TTS loop. It is fast enough to run as a queued per-turn background job, but not to answer in real time. Batch it (end of session) or use it in writing mode where waiting is acceptable.
- **`gemma3:12b` is not a replacement.** At 16 s per sentence it is about 1.5 times faster than mistral-small, but the tightened prompt did not remove its false positive on s12, and it fails s10 and s17. It is still too slow for live use.
- **Do not use thinking mode** on any model. The thinking runs were not repeated, so this rests on the first, leaky-prompt run (finding 6). It is 10 to 30 times slower and showed no accuracy gain there.
- **Neither Qwen3 size is a candidate for correction.** On the tightened prompt 8b fixes 14 of 18 and 4b 12 of 18. A two-sentence gap in one run does not settle which is better (finding 3).
- **Still provisional.** The test set is small and easy (see Caveats), and no model has been run more than once.

## Runs analysed

| Config | Raw output |
| --- | --- |
| mistral-small, gemma3:12b, qwen3:4b, qwen3:8b (no think, `--no-explain`), **tightened prompt** (keep every word unless wrong), 2026-11-21 | `07_clean_prompt_mistral_4b_8b_gemma.jsonl` |
| mistral-small (no think), with then without `--no-explain`, back to back, `performance` governor, 2026-11-21 | `06_clean_prompt_mistral_ab_performance_governor.jsonl` |
| mistral-small (no think, `--no-explain`), clean prompt, `powersave` governor | `05_clean_prompt_mistral_no_explain.jsonl` |
| qwen3:4b, qwen3:8b, mistral-small, gemma3:12b (no think), clean prompt | `03_clean_prompt_nothink_4_models.jsonl` |
| qwen3:4b think (complete), qwen3:8b think (first 6 sentences only, then timed out), clean prompt, 2026-11-18 | `04_clean_prompt_think_4b.jsonl` |
| qwen3:4b, qwen3:8b, mistral-small (no think), leaky prompt | `01_initial_leaky_nothink.jsonl` |
| qwen3:8b, think, leaky prompt | `02_initial_leaky_think_4b_8b.jsonl` |
| qwen3:4b, think, leaky prompt | `02_initial_leaky_think_4b_8b.jsonl` |

`06_...` holds 36 rows: the first 18 are the run with explanations and the next 18 the run without (check the `explain` field).

Each file is the concatenation of the original timestamped result files for that stage, with every row unchanged. Each row records its own `model`, `think` and `explain` fields. `01_initial_leaky_nothink.jsonl` also holds an early 5-sentence qwen3:4b smoke run (2026-10-28) and the 1-sentence mistral-small "think" run described below. The two empty result files from failed runs and all the terminal copies (`.txt`) were deleted, since the jsonl files hold the same output.

The 2026-11-15 `mistral-small` think run (1 sentence) is excluded. `mistral-small` has no thinking mode, so Ollama rejects the flag and the script silently retries without it.

The tightened-prompt runs (`07_...`) are the main results. The 2026-11-15 runs used a prompt that leaked answers and different grading, so their numbers are not comparable. For example, qwen3:8b's exact-fix score of 0.83 at that time does not match its own per-sentence table, which implies 0.78.

## Scores (tightened prompt, `--no-explain`)

| Model | think | detect_acc | false_pos | missed | fix_exact | concept_recall | sec/sent (mean) | tok/s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mistral-small | no | **1.00** | 0/5 | 0/13 | **1.00** | **0.85** | 23.6 | 2.7 |
| gemma3:12b | no | 0.89 | 1/5 | 1/13 | 0.83 | 0.69 | 15.9 | 5.3 |
| qwen3:8b | no | 0.83 | 0/5 | 3/13 | 0.78 | 0.46 | **6.2** | 13.0 |
| qwen3:4b | no | 0.67 | 1/5 | 5/13 | 0.67 | 0.31 | 19.1 (anomalous, finding 7) | 3.3 |

### Previous prompt, for comparison

| Model | explanations | date | detect_acc | false_pos | missed | fix_exact | concept_recall | sec/sent (mean) | tok/s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mistral-small | no | 11-19 | 1.00 | 0/5 | 0/13 | 0.94 | 0.85 | 24.4 | 2.7 |
| mistral-small | yes | 11-17 | 1.00 | 0/5 | 0/13 | 0.94 | 0.77 | 54.0 | 1.6 |
| gemma3:12b | yes | 11-17 | 0.89 | 1/5 | 1/13 | 0.83 | 0.77 | 21.8 | 5.3 |
| qwen3:8b | yes | 11-17 | 0.89 | 0/5 | 2/13 | 0.78 | 0.54 | 8.6 | 13.0 |
| qwen3:4b | yes | 11-17 | 0.78 | 0/5 | 4/13 | 0.78 | 0.31 | 3.7 | 34.4 |

For gemma3:12b and both Qwens, the new rows differ from these in two ways (tightened prompt and no explanations), so a change cannot be pinned on either one. Only the mistral-small 11-19 row isolates the prompt (finding 11).

### Back-to-back A/B, `performance` governor (2026-11-21)

| Config | detect_acc | false_pos | fix_exact | concept_recall | sec/sent (mean) | tok/s | correct sentences (s) | error sentences (s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mistral-small, explanations (run first) | 1.00 | 0/5 | 0.94 | 0.77 | 32.1 | 2.67 | 12 to 16 (first call 32) | 33 to 42 (s16 60) |
| mistral-small, `--no-explain` (run second) | 1.00 | 0/5 | 0.94 | 0.85 | 46.8 | 1.40 | 24 to 33 (first call 65) | 44 to 61 (s16 74) |

The no-explanation run was slower, because the machine ran at about half the throughput during it (1.40 vs 2.67 tok/s). See finding 10.

For reference, the first run on the leaky prompt scored mistral-small 1.00 / 1.00 / 1.00 (detect / fix / concept), qwen3:4b 0.89 / 0.78 / 0.54 and qwen3:8b 0.89 / 0.83 / 0.46. The think runs are below.

### Thinking mode (2026-11-15, leaky prompt, not repeated)

| Model | think | detect_acc | false_pos | missed | fix_exact | concept_recall | sec/sent (mean) | tok/s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| qwen3:4b | yes | 1.00 | 0/5 | 0/13 | 0.72 | 0.77 | 94.5 | 32.4 |
| qwen3:8b | yes | 0.83 | 2/5 | 1/13 | 0.72 | 0.69 | 50.2 | 12.2 |

## Per-sentence results (tightened prompt, `--no-explain`)

✓ means detection and exact fix were both right.

| id | error type | 4b | 8b | mistral | gemma3:12b |
| --- | --- | --- | --- | --- | --- |
| s01 | none (correct) | ✓ | ✓ | ✓ | ✓ |
| s02 | participle agreement | ✓ | ✓ | ✓ | ✓ |
| s03 | elision | ✓ | ✓ | ✓ | ✓ |
| s04 | subjunctive | ✓ | ✓ | ✓ | ✓ |
| s05 | gender | ✓ | ✓ | ✓ | ✓ |
| s06 | à + le | ✓ | ✓ | ✓ | ✓ |
| s07 | none (correct) | ✓ | ✓ | ✓ | ✓ |
| s08 | si-clause | ✗ | ✓ | ✓ | ✓ |
| s09 | partitive after negation | ✓ | ✓ | ✓ | ✓ |
| s10 | passé composé vs imparfait | ✗ | ✗ | ✓ | ✗ |
| s11 | adjective agreement | ✗ | ✓ | ✓ | ✓ |
| s12 | none (trap) | ✗ | ✓ | ✓ | ✗ |
| s13 | que → dont | ✗ | ✗ | ✓ | ✓ |
| s14 | beaucoup de | ✓ | ✓ | ✓ | ✓ |
| s15 | none (correct) | ✓ | ✓ | ✓ | ✓ |
| s16 | pronominal participle | ✓ | ✗ | ✓ | ✓ |
| s17 | en Paris → à Paris | ✗ | ✗ | ✓ | ✗ |
| s18 | none (correct) | ✓ | ✓ | ✓ | ✓ |

Concept tags missed (expected → got):

| id | expected | 4b | 8b | mistral | gemma3:12b |
| --- | --- | --- | --- | --- | --- |
| s02 | past_participle_agreement | adjective_agreement | verb_conjugation | ok | ok |
| s03 | elision | contraction_articles | contraction_articles | contraction_articles | contraction_articles |
| s04 | subjunctive_present | verb_conjugation | ok | ok | verb_conjugation |
| s08 | si_clause_conditional | passe_compose_vs_imparfait | verb_conjugation | ok | ok |
| s09 | partitive_negation | ok | ok | ok | contraction_articles |
| s10 | passe_compose_vs_imparfait | verb_conjugation | verb_conjugation | ok | ok |
| s11 | adjective_agreement | none | ok | ok | ok |
| s13 | relative_pronouns | verb_conjugation | ok | ok | ok |
| s14 | quantity_de | ok | elision | elision | contraction_articles |
| s16 | past_participle_agreement | gender_agreement | verb_conjugation | ok | ok |
| s17 | prepositions_places | none | none | ok | ok |

## Findings

1. **Mistral-small is the best on correction.** With the tightened prompt it detects every error, leaves all five correct sentences alone and exactly fixes all 13 errors. It is the only model that solves s10 (imparfait) and s17 (à Paris). With the previous prompt its one miss was s16, where it returned "Elle s'en est souvenue." instead of "Elle s'est souvenue de son enfance." That is correct French with the right agreement, but it rewrote the sentence and dropped "de son enfance", which is over-correction for a learner. The prompt now says to fix only the wrong words, keep every other word, and not to rephrase or use pronouns even if the result is valid French. s16 now comes back as expected. For mistral nothing else changed in correction: no other corrected sentence moved, there are still 0/5 false positives, concept recall is the same (0.85) and latency is the same (23.6 s against 24.4 s at 2.72 tok/s both times). Two cautions. It is a single run. And the prompt was written after seeing the s16 failure, so s16 is no longer a held-out test. The 1.00 shows the rule works on that sentence, not that mistral-small is perfect.
2. **Qwen3 fails on the subtle, French-specific errors.** s10, s13 and s17 fail on both sizes. 4b also fails s08, s11 and the s12 trap ("Je me suis lavées les mains"), and 8b also fails s16. 8b still adds a stray *de* in s13 ("que je t'ai parlé de"). On exact fixes of error sentences, 4b gets 8 of 13 and 8b 9 of 13, against 13 for mistral. Tagging is weak: 4 of 13 for 4b and 6 of 13 for 8b, often with the generic `verb_conjugation`.
3. **8b is now slightly ahead of 4b, within noise.** It fixes 14 of 18 against 12, has no false positive (4b has one) and tags 6 against 4. On the previous prompt both fixed 14. The speed comparison from this run is not usable, because 4b ran about 10 times slower than before (finding 7). At normal speed 4b was 2.3 times faster than 8b. The plan's default of Qwen3:8b or 14b is still unsupported.

4. **Mistral's and gemma's tag misses are label overlap, not wrong understanding.** All four models tag s03 ("de un" → "d'un") as `contraction_articles` instead of `elision`, which is arguably right because the same change also covers de + un. For s14 ("beaucoup des amis" → "d'amis") mistral and 8b say `elision` and gemma `contraction_articles` instead of `quantity_de`. Gemma also tags s04 `verb_conjugation` and s09 `contraction_articles`. All are defensible. Before ranking models on concept recall, review `concepts.json` for overlapping labels, or accept a set of equivalent tags per sentence. Until then 0.85 and 0.69 understate mistral and gemma. Qwen has some real mislabels as well (4b tags s08 `passe_compose_vs_imparfait`).
5. **Gemma3:12b is a middle ground on speed, not on accuracy.** It fixes 11 of 13 errors exactly, the same count as on the previous prompt. It gets s13 right, which neither Qwen does. Its failures:
   - s10: it returns the sentence unchanged, although its error list names the problem and suggests "allais". On the previous prompt it fixed this.
   - s12, the trap sentence: it still writes "lavé(e)" and adds an agreement tag to a correct sentence. This is a false positive, which the README calls the worst failure for a learner.
   - s17: it changes "en Paris" to "en France" instead of "à Paris". The grader counts this as detected because the text changed, but the fix is wrong and changes the meaning. On the previous prompt it left the sentence unchanged.

   s09, which it previously got wrong ("de frère"), is now fixed. At 16 s per sentence (15 s without the first call, which includes loading) it is about 1.5 times faster than mistral-small. The false positive persists with the stricter prompt, which rules it out as the primary corrector for now.

6. **Thinking mode was not re-tested, and its evidence is weaker.** A re-run on 2026-11-18 failed. qwen3:4b finished, but qwen3:8b timed out. Ollama was decoding at about 1.6 tok/s on a thinking generation that had already run to 2900 tokens. The user decided to skip thinking mode for now. `run_eval.py` now caps output at 2048 tokens and records a timeout or truncation as a failed row instead of crashing. The think numbers come from the leaky prompt, which inflates tagging in particular. What probably still holds is the cost: 30 times the latency for 4b (3 s → 95 s). The accuracy results were mixed even with the answers in the prompt. 4b-think raised detection from 0.89 to 1.00 but lowered exact fixes from 0.78 to 0.72, with new elision errors ("je allais", "de amis", "de sa enfance", "vienne"). 8b-think "corrected" correct sentences s01 and s12, so false positives rose from 0/5 to 2/5. The no-think default is safe. Re-run with the clean prompt only if there is a reason to revisit it.
7. **Speed is unstable, and the CPU governor is not the cause.** Mistral-small's throughput has varied between runs on the same machine: 2.7 tok/s (2026-11-15, `powersave`), 1.6 (11-17, `powersave`), 2.7 (11-19, `powersave`), 2.67 and then 1.40 (11-21, `performance`, back to back). Mean latency moved with it, from 24 s to 54 s. Switching to `performance` did not stop the drop, which happened within one session. Thermal throttling or background load are the likely causes, but I haven't measured either. The Qwen models also slowed by about 18% on 11-17 (4b 3.1 → 3.7 s, 8b 7.3 → 8.6 s). In the tightened-prompt run, qwen3:4b decoded at 3.2 to 4.7 tok/s, against 28 to 36 on 11-17, and took 19.1 s per sentence. qwen3:8b (13.0 tok/s) and gemma3:12b (5.3) ran at the same speed as before. I don't know the cause, so don't use that 4b latency until it is re-measured. Treat any single latency figure as ±50% (more in the 4b case) and compare configs only inside one run. The first call of each model includes the load cost (qwen3:8b s01 25 s against 3 s for later correct sentences). Output length also matters (finding 10).
8. **The model doesn't always keep its fields consistent.** In the 11-17 run (previous prompt), for s04, qwen3:8b output the corrected text unchanged, with no error flagged and no tag. In the first run it produced the right correction with `has_error` set to false. Deriving detection from `corrected != text` would catch that earlier pattern. It would not help where the text comes back unchanged. The tightened-prompt run has more mismatches: gemma3:12b on s10 and qwen3:8b on s16 list a correction but leave `corrected` unchanged, and gemma3:12b on s17 changes the text while setting `has_error` to false. qwen3:4b flags the correct s07 with a no-op "vertes" → "vertes" entry. Reading the error list as well as `corrected` could recover some misses, but would need its own false-positive check.
9. **The leak fix changed the conclusions less than feared, but it did change them.** These figures compare the leaky and clean runs on the previous prompt. Mistral's perfect concept recall (1.00) was inflated by the leak, and it is now 0.77. Mistral's fix accuracy only dropped from 1.00 to 0.94. Qwen's ranking against mistral is the same. The leak never explained why Qwen fails s10 and s13, since those sentences were never leaked.
10. **Dropping explanations reduces mistral-small's work by roughly a quarter, but the clean A/B was ruined by machine speed.** In the back-to-back run (2026-11-21, `performance` governor) the no-explanation run was slower in wall-clock time (46.8 s vs 32.1 s per sentence), only because throughput fell from 2.67 to 1.40 tok/s between the two runs. Multiplying latency by tok/s gives a rough measure of work done, which includes prompt processing, so it is not an exact token count:
   - Error sentences: about 96 (36 s × 2.67) with explanations against about 69 (49 s × 1.4) without, a saving of about 28%.
   - Correct sentences: about 35 against about 34, no change.

   Accuracy was identical in both runs (detect 1.00, fix 0.94, 0 false positives), and s16 is still rewritten to "Elle s'en est souvenue." with or without explanations. The earlier 11-19 result (24.4 s at 2.72 tok/s) fits the same picture: when the machine ran at full speed, no-explain took 24 s, against 32 s with explanations at the same speed, a saving of about 25%. The "halves latency" claim from the 11-19 run was mostly the machine speeding up, since the explained run it was compared with ran at 1.6 tok/s. Concept recall is 0.85 without explanations and 0.77 with them in both pairs of runs. The difference is s04, which is tagged `subjunctive_present` only without explanations. It reproduced at temperature 0, so it looks like a real but tiny effect of the shorter prompt and schema. s03 and s14 are mislabelled in every run. The near-constant cost of correct sentences (about 12 to 16 s at full speed, with almost nothing to generate) points to a fixed per-call cost, most likely processing the long system prompt, which is the next thing to measure.
11. **The tightened prompt helped mistral-small and did not clearly help the others.** Against the previous rows: gemma3:12b gained s09 and lost s10 (15 of 18 both times). qwen3:8b gained s04 and lost s16 (14 both times), and no longer rewrites s10 but leaves it unfixed. qwen3:4b lost s08 and gained a false positive on s12 (14 → 12). Missed errors rose for 4b (4 → 5) and 8b (2 → 3) and stayed at 1 for gemma. That fits the risk that "change less" wording leads to unchanged output, but explanations were dropped in the same step, so the cause is not isolated. At the same tok/s as on 11-17, mean latency fell from 21.8 to 15.9 s for gemma3:12b and from 8.6 to 6.2 s for qwen3:8b, in line with the saving from dropping explanations (finding 10).

## Caveats

- **Small sample.** There are 18 sentences, so one sentence is 5.5 percentage points. Small gaps (4b vs 8b, mistral vs gemma on tags) are noise. The mistral-vs-gemma gap on fixes (18/18 vs 15/18) is only 3 sentences (s10, s12, s17). Mistral's 18 of 18 also includes s16, the failure that shaped the new prompt.
- **Easy test set.** Every error sentence has exactly one textbook error. Real learner text has several errors at once, plus spelling, punctuation and register.
- **One run per config** at temperature 0. There is no variance estimate. The latency drift between runs (finding 7) shows that single numbers can move a lot.
- **Tag grading is strict.** One expected label per sentence, with overlapping labels (finding 4), so concept recall is a lower bound.
- **Conversation quality is not measured.** This experiment tests correction only. It says nothing about which model gives better tutor replies.
- **CPU contention is untested.** Running mistral-small (about 14 GB at typical quantization) in the background while Whisper, Piper and a chat model run has not been tried. RAM and CPU sharing could erase the benefit of moving it off the live path, and the slowdown in finding 7 suggests the margin is thin.

## Changes applied to the plan

- §2 and §9: replace "Qwen3:8b or 14b" as the single LLM. Use a small fast model for conversation turns (qwen3:4b, no thinking, once its speed is re-measured) and `mistral-small` for error analysis, with explanations off.
- §5, conversation mode: split the "generate reply + note any errors" step. The reply goes out immediately. Error detection runs as a background or end-of-session batch job. At 24 to 47 s per sentence (without explanations, depending on machine speed) it can keep up with a queue between turns, but not in real time. Tag-driven `mastery` updates should wait until the tag taxonomy is fixed (finding 4).
- State explicitly that thinking mode is off.
- Note `gemma3:12b` (16 s without explanations) as a fallback if mistral-small's latency is still too high, with the false-positive risk.
- If the learner needs explanations, generate them separately, only for the errors found, rather than in the detection call.

## Next

1. Review `concepts.json` for overlapping labels (elision vs contraction_articles, quantity_de vs elision, subjunctive vs verb_conjugation) and re-score the existing outputs with equivalent tags allowed.
2. Add 20 or more new sentences, including multi-error and tricky correct ones, and a few of your own real mistakes. Write them without looking at model outputs, so the prompt isn't tuned on them. Run mistral-small and gemma3:12b on them.
3. Re-measure qwen3:4b's speed and find out what makes throughput drop (finding 7). Watch CPU temperature and frequency with `sensors` or `turbostat` during a run, and check what else is using the CPU and whether the model is loaded alongside another (`ollama ps`).
4. Measure how much of the 12 to 16 s floor on correct sentences is prompt processing. Try a shorter system prompt, and check that Ollama reuses the cached prefix between calls.
5. Repeat each model two or three times, with nothing else running, to get latency and accuracy variance.
6. Measure mistral-small and a chat model running together on this machine.
7. Optional: re-run thinking mode for qwen3:4b on the clean prompt, to confirm finding 6.

## Checks on 2026-11-26

One run each, `powersave` governor, Ollama 0.32.1.

### Code changes

| File | Change |
| --- | --- |
| `run_eval.py` | New `concepts_match` function, used for the strict `concept_ok` and the new `concept_ok_lenient`. The summary table has a `concept_lenient` column. New `--rescore FILE...` option re-grades saved results against the current test sentences without calling a model or changing the files, and skips rows with no matching sentence. |
| `test_sentences.jsonl` | New `also_accept` field: s03 also accepts `contraction_articles`; s14 also accepts `elision` and `contraction_articles`. |
| `contention.py` (new) | Times chat alone, analysis alone, then chat while analysis loops. Logs time to first word, tok/s, load time, loaded models, free RAM and swap. Stops chat turns and reports the error if analysis fails. |
| `README.md` | Usage and notes for the three changes above. |

Not accepted as alternatives: `verb_conjugation` for s04 (subjunctive) and `contraction_articles` for s09 (negation). The mastery tracker would credit the wrong concept.

### Re-scored tags (tightened-prompt run, `07_...`)

| Model | Strict | Lenient |
| --- | --- | --- |
| mistral-small | 11/13 | 13/13 |
| gemma3:12b | 9/13 | 11/13 |
| qwen3:8b | 6/13 | 8/13 |
| qwen3:4b | 4/13 | 5/13 |

Command: `run_eval.py --rescore` on files `03`, `05`, `06` and `07`.

### Both models together (`contention.py`, defaults)

Raw output: `contention-20261126-220906.jsonl`. Means over 6 chat turns per phase.

| | Alone | Together |
| --- | --- | --- |
| qwen3:4b chat, tok/s | 39.1 | 4.8 |
| qwen3:4b chat, seconds per 80-token reply | 2.4 | 20.2 (first turn 29.5, including 11.9 s reload) |
| qwen3:4b chat, seconds to first word | 0.3 | 3.7 (1.5 to 2.1 after the first turn) |
| mistral-small analysis, tok/s | 2.7 | 2.4 |
| mistral-small analysis, seconds per sentence | 25.9 | 26.4 |

Lowest free RAM was 16.8 GB. Swap use went from 0.3 to 2.2 GB. "First word" is the first output of any kind, which for qwen3:4b was reasoning, not the reply. Ollama had unloaded qwen3:4b by the time the together phase started.

### Thinking settings (one-off script, not kept)

One prompt ("Je voudrais visiter Lyon l'été prochain.") to `/api/chat` with the system prompt from `contention.py`, temperature 0, `num_predict` 700.

| Model | `think: false` | `think: false` + `/no_think` | `think: true` |
| --- | --- | --- | --- |
| qwen3:4b | English reasoning as the reply, cut off at 700 tokens | same | 700 tokens of reasoning, empty reply |
| qwen3:8b | clean French reply, 38 tokens | clean French reply, 32 tokens | clean French reply, 111 tokens |

### GPU placement (one-off script, not kept)

Each model generated 120 tokens through `/api/generate`, with models unloaded between cases using `ollama stop`. Run twice; the second run also printed `ollama ps`. `lspci` and the Ollama system log identified the GPU (NVIDIA RTX 1000 Ada, 6 GB, through Vulkan).

| Case | tok/s | Share on GPU |
| --- | --- | --- |
| qwen3:4b alone | 38.5 to 39.1 | 100% |
| qwen3:4b with mistral-small idle | 4.3 to 4.5 | 19% |
| qwen3:8b alone | 14.1 to 14.8 | 77% |
| qwen3:8b after mistral-small, first run | 2.2 | not recorded (both loaded) |
| qwen3:8b after mistral-small, second run | 14.3 | 77% (mistral-small was unloaded) |
| mistral-small alone | 2.6 to 2.7 | 29% |
