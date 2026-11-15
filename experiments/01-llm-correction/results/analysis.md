# Track 01 analysis: which model should do French error correction?

Date: 2026-11-15. CPU only, 18 sentences (13 with an error, 5 correct), temperature 0, one run per config.

## Decision (provisional)

- **Use `mistral-small` for error detection, correction and concept tagging.** It is the only model that gets everything right. The mastery tracker depends on these tags, and the Qwen3 models can't supply them reliably.
- **Keep it off the live conversation path.** At about 31 s per sentence and 2.6 tok/s it is far too slow for the ASR → LLM → TTS loop. Run it in the background after each turn, or in writing mode where waiting is acceptable.
- **Do not use thinking mode** on any model. It is 10 to 30 times slower and no more accurate.
- **There is no case here for `qwen3:8b` over `qwen3:4b`.** It is 2.4 times slower and its correction and tagging are no better. See finding 3.
- **Treat this as provisional.** The test set leaks answers into the prompt (finding 5). Re-run after fixing that before changing `planning.md`.

## Runs analysed

| Config | Raw output | Terminal copy |
| --- | --- | --- |
| qwen3:4b, qwen3:8b, mistral-small (no think) | `20261115-202639.jsonl` | `all_3_run_1.txt` |
| qwen3:8b, think | `20261115-205141.jsonl` | `qwen3-8b-thinking.txt` |
| qwen3:4b, think | `20261115-211321.jsonl` | `qwen3-4b-thinking.txt` |
| mistral-small, think (1 sentence) | `20261115-214310.jsonl` | none |

The last row is excluded. `mistral-small` has no thinking mode, so Ollama rejects the flag and the script silently retries without it. That run is the same as a no-think run.

## Scores

| Model | think | detect_acc | false_pos | missed | fix_exact | concept_recall | sec/sent (mean) | tok/s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mistral-small | no | **1.00** | 0/5 | 0/13 | **1.00** | **1.00** | 31.1 | 2.7 |
| qwen3:4b | no | 0.89 | 0/5 | 2/13 | 0.78 | 0.54 | **3.1** | 34.3 |
| qwen3:8b | no | 0.89 | 0/5 | 2/13 | 0.83 | 0.46 | 7.3 | 13.1 |
| qwen3:4b | yes | 1.00 | 0/5 | 0/13 | 0.72 | 0.77 | 94.5 | 32.4 |
| qwen3:8b | yes | 0.83 | **2/5** | 1/13 | 0.72 | 0.69 | 50.2 | 12.2 |

## Per-sentence results

✓ means detection and exact fix were both right. † marks sentences whose answer appears as an example in `concepts.json` (finding 5).

| id | error type | 4b | 8b | mistral | 4b think | 8b think |
| --- | --- | --- | --- | --- | --- | --- |
| s01 | none (correct) | ✓ | ✓ | ✓ | ✓ | ✗ |
| s02 | participle agreement | ✓ | ✓ | ✓ | ✓ | ✓ |
| s03† | elision | ✓ | ✓ | ✓ | ✓ | ✓ |
| s04 | subjunctive | ✓ | ✗ | ✓ | ✗ | ✓ |
| s05† | gender | ✓ | ✓ | ✓ | ✓ | ✓ |
| s06† | à + le | ✓ | ✓ | ✓ | ✓ | ✓ |
| s07 | none (correct) | ✓ | ✓ | ✓ | ✓ | ✓ |
| s08† | si-clause | ✓ | ✓ | ✓ | ✓ | ✓ |
| s09† | partitive after negation | ✓ | ✓ | ✓ | ✓ | ✓ |
| s10 | passé composé vs imparfait | ✗ | ✗ | ✓ | ✗ | ✗ |
| s11 | adjective agreement | ✗ | ✓ | ✓ | ✓ | ✓ |
| s12 | none (trap) | ✓ | ✓ | ✓ | ✓ | ✗ |
| s13 | que → dont | ✗ | ✗ | ✓ | ✗ | ✗ |
| s14† | beaucoup de | ✓ | ✓ | ✓ | ✗ | ✓ |
| s15 | none (correct) | ✓ | ✓ | ✓ | ✓ | ✓ |
| s16 | pronominal participle | ✓ | ✓ | ✓ | ✗ | ✓ |
| s17† | en Paris → à Paris | ✗ | ✗ | ✓ | ✓ | ✗ |
| s18 | none (correct) | ✓ | ✓ | ✓ | ✓ | ✓ |

## Findings

1. **Mistral-small is the only model that passes everything.** It fixed every error, left all five correct sentences alone, and tagged every concept correctly. It also solved the sentences that all the Qwen runs fail: s10 (imparfait), s13 (dont) and, apart from 4b-think, s17 (à Paris).
2. **Qwen3 fails on the subtle, French-specific errors.** s10 and s13 fail in all four Qwen configs. When Qwen "fixes" s13 it adds a stray *de* ("que je t'ai parlé de"), or invents *dit* or *t'aie*. Qwen3:8b even rewrote s10's error tag into "verb_conjugation" with an incoherent explanation (past historic / imparfait mix-up). These are the grammar points a learner most needs help with.
3. **8b is not better than 4b.** In the no-think runs, 4b and 8b have the same detection, and 8b is one sentence better on exact fixes (0.83 vs 0.78). That is within noise for 18 sentences. 8b is 2.4 times slower and has lower concept recall (0.46 vs 0.54). The plan's default of Qwen3:8b or 14b isn't supported. Qwen3:14b is unlikely to close the s10 and s13 gap given that 8b didn't improve on 4b.
4. **Thinking mode hurts.**
   - It costs 30 times more latency for 4b (3 s → 95 s).
   - It raised 4b's detection from 0.89 to 1.00, but exact fixes fell from 0.78 to 0.72.
   - It introduced new errors, mostly missing elision: "je allais", "de amis", "de sa enfance", "vienne".
   - It "corrected" correct sentences. 8b-think turned s01 into "allée" and s12 into "lavées", failing the trap. False positives rose from 0/5 to 2/5, which the README calls the worst failure for a learner.
   - The better concept recall in the think runs (0.77 and 0.69) doesn't offset this.
5. **The test set leaks answers.** Seven of the 13 error sentences (s03, s05, s06, s08, s09, s14, s17) appear nearly verbatim as examples in the `concepts.json` descriptions that go into the system prompt, such as "la problème -> le problème" and "en Paris -> à Paris". Scores on those sentences and on concept recall are inflated for every model. On the six unleaked error sentences (s02, s04, s10, s11, s13, s16), 4b and 8b each get 3 of 6 right, and mistral gets 6 of 6. The ranking holds, but the Qwen numbers are optimistic. Qwen still failed s17 even with its answer printed in the prompt.
6. **Speed.** Qwen3:4b at about 3 s per sentence is fast enough for conversation. Mistral-small ranges from 12 s to 43 s per sentence. The first-call model-load cost is not what makes it slow, since its first sentence took 31 s, about the same as the mean. Long outputs are, so shorter explanations or an explanation-free mode should cut the time.
7. **Explanation quality is mostly good but not perfect.** Of mistral's 13 explanations, only s03's is garbled ("'un' should be elided to 'un'"), even though the fix is right. It is fine for tagging but should not be shown to the learner unreviewed.
8. **The model doesn't keep its fields consistent.** For s04, qwen3:8b output the right correction but set `has_error` to false. Deriving detection from `corrected != text` would catch cases like this. It would not help s10, s13 or s17, where the text came back unchanged.

## Caveats

- **Small sample.** There are 18 sentences, so one sentence is 5.5 percentage points. Small gaps (4b vs 8b) are noise. The mistral-vs-Qwen gap is not.
- **Easy test set.** Every error sentence has exactly one textbook error. Real learner text has several errors at once, plus spelling, punctuation and register.
- **One run per config** at temperature 0. There is no variance estimate.
- **Conversation quality is not measured.** This experiment tests correction only. It says nothing about which model gives better tutor replies.
- **CPU contention is untested.** Running mistral-small (about 14 GB at typical quantization) in the background while Whisper, Piper and a chat model run has not been tried. RAM and CPU sharing could erase the benefit of moving it off the live path.

## Proposed changes to the plan (not yet applied)

- §2 and §9: replace "Qwen3:8b or 14b" as the single LLM. Use a small fast model (qwen3:4b, no thinking) for conversation turns and `mistral-small` for error analysis.
- §5, conversation mode: split the "generate reply + note any errors" step. The reply goes out immediately. Error detection and tagging run as a background job that updates `mastery` when it finishes.
- State explicitly that thinking mode is off.

Per CLAUDE.md, `planning.md` changes go through plan mode, so these are listed here instead of being applied.

## Next

1. Remove the literal examples from the `concepts.json` descriptions, or move them out of the gold set, and re-run all three models.
2. Add 20 or more sentences, including multi-error and tricky correct ones, and a few of your own real mistakes.
3. Try `gemma3:12b` (listed in the README) as a possible middle ground on speed and accuracy.
4. Try a shorter output format for mistral-small (tags and corrections only, no explanations) and measure the latency saving.
5. Measure mistral-small and a chat model running together on this machine.
6. Add `--out` or a printed warning to `run_eval.py` for the silent `think` fallback.
