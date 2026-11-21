# Track 01 analysis: which model should do French error correction?

Date: first runs 2026-11-15, re-run 2026-11-17 after removing the answer leak and making grading consistent (commit `c2b34a5`). CPU only, 18 sentences (13 with an error, 5 correct), temperature 0, one run per config.

## Decision (provisional)

- **Use `mistral-small` for error detection and correction, without explanations.** It is the only model with perfect detection (18/18, 0/5 false positives) and it fixes 17 of 18 sentences exactly. Its one miss (s16) is a rewrite, not a missed error. Dropping the `explanation` field (`--no-explain`) cut latency to 24 s per sentence with the same accuracy (finding 10).
- **Do not treat concept tags as reliable for any model yet.** With the leak gone, mistral-small tags 10 of 13 correctly with explanations and 11 of 13 without (0.77 and 0.85), gemma3:12b 10 of 13 (0.77), and the Qwen3 models 4 of 13 (4b) and 7 of 13 (8b). The mastery tracker depends on these tags. Most tag misses are label overlaps (finding 4), so a taxonomy fix may be cheaper than a model change.
- **Keep it off the live conversation path.** Even without explanations it takes 24 to 47 s per sentence depending on how fast the machine is running (finding 10), far too slow for the ASR → LLM → TTS loop. It is fast enough to run as a queued per-turn background job, but not to answer in real time. Batch it (end of session) or use it in writing mode where waiting is acceptable.
- **`gemma3:12b` is not a replacement.** It is 2.5 times faster than mistral-small (22 s per sentence) but it adds a false positive and misses s17. It is still too slow for live use.
- **Do not use thinking mode** on any model. The thinking runs were not repeated, so this rests on the first, leaky-prompt run (finding 6). It is 10 to 30 times slower and showed no accuracy gain there.
- **There is no case for `qwen3:8b` over `qwen3:4b`.** It is 2.3 times slower and equal on correction (finding 3).
- **Still provisional.** The test set is small and easy (see Caveats), and no model has been run more than once.

## Runs analysed

| Config | Raw output |
| --- | --- |
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

The 2026-11-17 runs are the main results. The 2026-11-15 runs used a prompt that leaked answers and different grading, so their numbers are not comparable. For example, qwen3:8b's exact-fix score of 0.83 at that time does not match its own per-sentence table, which implies 0.78.

## Scores (clean prompt, 2026-11-17)

| Model | think | detect_acc | false_pos | missed | fix_exact | concept_recall | sec/sent (mean) | tok/s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mistral-small, no explanation | no | **1.00** | 0/5 | 0/13 | **0.94** | **0.85** | 24.4 | 2.7 |
| mistral-small | no | **1.00** | 0/5 | 0/13 | **0.94** | 0.77 | 54.0 | 1.6 |
| gemma3:12b | no | 0.89 | 1/5 | 1/13 | 0.83 | **0.77** | 21.8 | 5.3 |
| qwen3:8b | no | 0.89 | 0/5 | 2/13 | 0.78 | 0.54 | 8.6 | 13.0 |
| qwen3:4b | no | 0.78 | 0/5 | 4/13 | 0.78 | 0.31 | **3.7** | 34.4 |

The "no explanation" row ran on 2026-11-19 with `--no-explain`: the prompt and schema ask only for `corrected` and, per error, `original`, `correction` and `concept`. Its numbers are not from the same session as the other rows (finding 10).

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

## Per-sentence results (clean prompt)

✓ means detection and exact fix were both right.

| id | error type | 4b | 8b | mistral | gemma3:12b |
| --- | --- | --- | --- | --- | --- |
| s01 | none (correct) | ✓ | ✓ | ✓ | ✓ |
| s02 | participle agreement | ✓ | ✓ | ✓ | ✓ |
| s03 | elision | ✓ | ✓ | ✓ | ✓ |
| s04 | subjunctive | ✓ | ✗ | ✓ | ✓ |
| s05 | gender | ✓ | ✓ | ✓ | ✓ |
| s06 | à + le | ✓ | ✓ | ✓ | ✓ |
| s07 | none (correct) | ✓ | ✓ | ✓ | ✓ |
| s08 | si-clause | ✓ | ✓ | ✓ | ✓ |
| s09 | partitive after negation | ✓ | ✓ | ✓ | ✗ |
| s10 | passé composé vs imparfait | ✗ | ✗ | ✓ | ✓ |
| s11 | adjective agreement | ✗ | ✓ | ✓ | ✓ |
| s12 | none (trap) | ✓ | ✓ | ✓ | ✗ |
| s13 | que → dont | ✗ | ✗ | ✓ | ✓ |
| s14 | beaucoup de | ✓ | ✓ | ✓ | ✓ |
| s15 | none (correct) | ✓ | ✓ | ✓ | ✓ |
| s16 | pronominal participle | ✓ | ✓ | ✗ | ✓ |
| s17 | en Paris → à Paris | ✗ | ✗ | ✓ | ✗ |
| s18 | none (correct) | ✓ | ✓ | ✓ | ✓ |

Concept tags missed (expected → got):

| id | expected | 4b | 8b | mistral | gemma3:12b |
| --- | --- | --- | --- | --- | --- |
| s02 | past_participle_agreement | verb_conjugation | verb_conjugation | ok | ok |
| s03 | elision | contraction_articles | contraction_articles | contraction_articles (same without explanation) | contraction_articles |
| s04 | subjunctive_present | verb_conjugation | none | verb_conjugation (ok without explanation) | ok |
| s08 | si_clause_conditional | passe_compose_vs_imparfait | verb_conjugation | ok | ok |
| s11 | adjective_agreement | none | ok | ok | ok |
| s13 | relative_pronouns | other | ok | ok | ok |
| s14 | quantity_de | spelling | ok | elision (same without explanation) | contraction_articles |
| s16 | past_participle_agreement | gender_agreement | verb_conjugation | ok | ok |
| s17 | prepositions_places | none | none | ok | none |

## Findings

1. **Mistral-small is still the best on correction, but not perfect.** It detected every error, left all five correct sentences alone, and exactly fixed 12 of 13 errors. It is the only model that solves s10 (imparfait), s13 (dont) and s17 (à Paris) at once with the answers out of the prompt. Its one miss is s16. It returned "Elle s'en est souvenue." instead of "Elle s'est souvenue de son enfance." The participle agreement is right, but it rewrote the sentence, dropped "de son enfance" and added an `other` tag. The grader counts that as a fix miss. The output is correct French: "s'en souvenir" is a valid construction. The model found the error and fixed it. It drifted from the correction the sentence needed, which is to change as little as possible, and it did so in every run, with and without explanations and at any CPU speed. For a learner it is over-correction, not a failure to spot the error. A tighter prompt is the fix to try (see Next).
2. **Qwen3 fails on the subtle, French-specific errors, and the gap is now larger.** s10, s13 and s17 fail on both sizes. s11 also fails on 4b, and s04 on 8b. 8b rewrites s10 to "chaque été" (an unrelated change) and adds a stray *de* in s13 ("que je t'ai parlé de"). Qwen tagging collapsed without the leak. 4b tags 4 of 13 correctly (0.54 → 0.31) and 8b 7 of 13. Both often use the generic `verb_conjugation`. They fix 9 of 13 errors each, against mistral's 12 of 13.
3. **8b is not better than 4b.** Both fix 14 of 18 sentences (0.78). 8b detects more (0.89 vs 0.78) and tags better (0.54 vs 0.31), but 4b's detection misses are the same sentences it fails to fix, and the s10 and s13 failures are shared. 8b is 2.3 times slower. The plan's default of Qwen3:8b or 14b is still unsupported. 14b is unlikely to close the s10, s13 and s17 gap given that 8b didn't improve on 4b.
4. **Tag misses are mostly label overlap, not wrong understanding.** All four models tag s03 ("de un" → "d'un") as `contraction_articles` instead of `elision`, which is arguably right because the same change also covers de + un. Mistral tags s14 ("beaucoup des amis" → "d'amis") as `elision` and gemma as `contraction_articles`, instead of `quantity_de`. Both are defensible. Mistral also tags s04 `verb_conjugation` instead of `subjunctive_present`. Before ranking models on concept recall, review `concepts.json` for overlapping labels, or accept a set of equivalent tags per sentence. Until then 0.77 understates mistral and gemma, and 0.31 to 0.54 still tells us Qwen is worse.
5. **Gemma3:12b is a middle ground on speed, not on accuracy.** It detects all 13 errors except s17 and fixes 11 of 13 exactly. It gets s10 and s13 right, which neither Qwen does, and ties mistral on tags. Its failures:
   - s09: it fixes "des frères" to "de frère" and changes the number.
   - s12, the trap sentence: it writes "lavé(e)" and adds an agreement tag to a correct sentence. This is a false positive, which the README calls the worst failure for a learner.
   - s17: it missed the error entirely, like both Qwens.

   At 22 s per sentence (10 s on correct sentences, 20 to 31 s on errors) it is 2.5 times faster than mistral-small but still 6 times slower than qwen3:4b. The false positive rules it out as the primary corrector unless a prompt tweak fixes the "(e)" hedging.
6. **Thinking mode was not re-tested, and its evidence is weaker.** A re-run on 2026-11-18 failed. qwen3:4b finished, but qwen3:8b timed out. Ollama was decoding at about 1.6 tok/s on a thinking generation that had already run to 2900 tokens. The user decided to skip thinking mode for now. `run_eval.py` now caps output at 2048 tokens and records a timeout or truncation as a failed row instead of crashing. The think numbers come from the leaky prompt, which inflates tagging in particular. What probably still holds is the cost: 30 times the latency for 4b (3 s → 95 s). The accuracy results were mixed even with the answers in the prompt. 4b-think raised detection from 0.89 to 1.00 but lowered exact fixes from 0.78 to 0.72, with new elision errors ("je allais", "de amis", "de sa enfance", "vienne"). 8b-think "corrected" correct sentences s01 and s12, so false positives rose from 0/5 to 2/5. The no-think default is safe. Re-run with the clean prompt only if there is a reason to revisit it.
7. **Speed is unstable, and the CPU governor is not the cause.** Mistral-small's throughput has varied between runs on the same machine: 2.7 tok/s (2026-11-15, `powersave`), 1.6 (11-17, `powersave`), 2.7 (11-19, `powersave`), 2.67 and then 1.40 (11-21, `performance`, back to back). Mean latency moved with it, from 24 s to 54 s. Switching to `performance` did not stop the drop, which happened within one session. Thermal throttling or background load are the likely causes, but I haven't measured either. The Qwen models also slowed by about 18% on 11-17 (4b 3.1 → 3.7 s, 8b 7.3 → 8.6 s). Treat any single latency figure as ±50% and compare configs only inside one run. The first call of each model includes the load cost (qwen3:8b s01 25 s against 3 s for later correct sentences). Output length also matters (finding 10).
8. **The model doesn't always keep its fields consistent.** For s04, qwen3:8b outputs the corrected text unchanged, with no error flagged and no tag. In the first run it produced the right correction with `has_error` set to false. Deriving detection from `corrected != text` would catch that earlier pattern. It would not help s10, s13 or s17, where the text comes back unchanged.
9. **The leak fix changed the conclusions less than feared, but it did change them.** Mistral's perfect concept recall (1.00) was inflated by the leak, and it is now 0.77. Mistral's fix accuracy only dropped from 1.00 to 0.94. Qwen's ranking against mistral is the same. The leak never explained why Qwen fails s10 and s13, since those sentences were never leaked.
10. **Dropping explanations reduces mistral-small's work by roughly a quarter, but the clean A/B was ruined by machine speed.** In the back-to-back run (2026-11-21, `performance` governor) the no-explanation run was slower in wall-clock time (46.8 s vs 32.1 s per sentence), only because throughput fell from 2.67 to 1.40 tok/s between the two runs. Multiplying latency by tok/s gives a rough measure of work done, which includes prompt processing, so it is not an exact token count:
   - Error sentences: about 96 (36 s × 2.67) with explanations against about 69 (49 s × 1.4) without, a saving of about 28%.
   - Correct sentences: about 35 against about 34, no change.

   Accuracy was identical in both runs (detect 1.00, fix 0.94, 0 false positives), and s16 is still rewritten to "Elle s'en est souvenue." with or without explanations. The earlier 11-19 result (24.4 s at 2.72 tok/s) fits the same picture: when the machine ran at full speed, no-explain took 24 s, against 32 s with explanations at the same speed, a saving of about 25%. The "halves latency" claim from the 11-19 run was mostly the machine speeding up, since the explained run it was compared with ran at 1.6 tok/s. Concept recall is 0.85 without explanations and 0.77 with them in both pairs of runs. The difference is s04, which is tagged `subjunctive_present` only without explanations. It reproduced at temperature 0, so it looks like a real but tiny effect of the shorter prompt and schema. s03 and s14 are mislabelled in every run. The near-constant cost of correct sentences (about 12 to 16 s at full speed, with almost nothing to generate) points to a fixed per-call cost, most likely processing the long system prompt, which is the next thing to measure.

## Caveats

- **Small sample.** There are 18 sentences, so one sentence is 5.5 percentage points. Small gaps (4b vs 8b, mistral vs gemma on tags) are noise. The mistral-vs-Qwen gap on fixes (12/13 vs 9/13) is larger but still only 3 sentences.
- **Easy test set.** Every error sentence has exactly one textbook error. Real learner text has several errors at once, plus spelling, punctuation and register.
- **One run per config** at temperature 0. There is no variance estimate. The latency drift between runs (finding 7) shows that single numbers can move a lot.
- **Tag grading is strict.** One expected label per sentence, with overlapping labels (finding 4), so concept recall is a lower bound.
- **Conversation quality is not measured.** This experiment tests correction only. It says nothing about which model gives better tutor replies.
- **CPU contention is untested.** Running mistral-small (about 14 GB at typical quantization) in the background while Whisper, Piper and a chat model run has not been tried. RAM and CPU sharing could erase the benefit of moving it off the live path, and the slowdown in finding 7 suggests the margin is thin.

## Proposed changes to the plan (not yet applied)

- §2 and §9: replace "Qwen3:8b or 14b" as the single LLM. Use a small fast model (qwen3:4b, no thinking) for conversation turns and `mistral-small` for error analysis, with explanations off.
- §5, conversation mode: split the "generate reply + note any errors" step. The reply goes out immediately. Error detection runs as a background or end-of-session batch job. At 24 to 47 s per sentence (without explanations, depending on machine speed) it can keep up with a queue between turns, but not in real time. Tag-driven `mastery` updates should wait until the tag taxonomy is fixed (finding 4).
- State explicitly that thinking mode is off.
- Note `gemma3:12b` (22 s with explanations, so probably faster without) as a fallback if mistral-small's latency is still too high, with the false-positive risk.
- If the learner needs explanations, generate them separately, only for the errors found, rather than in the detection call.

Per CLAUDE.md, `planning.md` changes go through plan mode, so these are listed here instead of being applied.

## Next

1. Tighten the prompt so the model keeps every word unless it is wrong (it rewrote s16 although the result was valid French), and re-run mistral-small to see whether s16 passes without breaking other sentences.
2. Review `concepts.json` for overlapping labels (elision vs contraction_articles, quantity_de vs elision, subjunctive vs verb_conjugation) and re-score the existing outputs with equivalent tags allowed.
3. Add 20 or more sentences, including multi-error and tricky correct ones, and a few of your own real mistakes. Re-run mistral-small and gemma3:12b.
4. Find out what makes throughput drop within a session (finding 7). Watch CPU temperature and frequency with `sensors` or `turbostat` during a run, and check what else is using the CPU. Then repeat the A/B, alternating the order, with a short warm-up first. Also try `gemma3:12b --no-explain`.
5. Measure how much of the 12 to 16 s floor on correct sentences is prompt processing. Try a shorter system prompt, and check that Ollama reuses the cached prefix between calls.
6. Repeat each model two or three times, with nothing else running, to get latency variance.
7. Measure mistral-small and a chat model running together on this machine.
8. Add `--out` or a printed warning to `run_eval.py` for the silent `think` fallback.
9. Optional: re-run thinking mode for qwen3:4b on the clean prompt, to confirm finding 6.
