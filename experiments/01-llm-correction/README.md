# 01 — LLM error correction

**Question:** Can a local model find French errors, fix them minimally, tag them with the right concept, and leave correct sentences alone, fast enough on CPU?

The rest of the system depends on this answer. The mastery tracker only learns what the LLM's error tags tell it.

## Run

```bash
ollama pull qwen3:8b            # qwen3:4b is already installed
uv run python 01-llm-correction/run_eval.py --models qwen3:4b qwen3:8b
uv run python 01-llm-correction/run_eval.py --models qwen3:8b --think     # does reasoning help?
```

Also worth trying: `qwen3:14b`, `mistral-small` (Mistral is a French company), and `gemma3:12b`.

## Files

- `test_sentences.jsonl`: gold data. **Add your own real mistakes here.** They're worth more than the made-up ones. Some sentences are deliberately correct (e.g. `s12`, a trap for over-correction).
- `concepts.json`: the tag set the model must choose from. It's the seed for `data/concepts_seed.json` later.
- `run_eval.py`: runs every model on every sentence and prints a summary table. Full outputs, including explanations, go to `results/`.

## What to look at

- **false_pos**: correct sentences the model "fixed". For a learner, this is the worst failure.
- **concept_recall**: whether it tagged the right concept. This feeds BKT directly.
- **sec/sent** and **tok/s**: is conversation mode going to feel laggy?
- Read the explanations in `results/`. Are they right, and would they help you?

## Ideas once the basics work

- Few-shot examples in the prompt vs zero-shot.
- Ask the model to grade against a CEFR level ("only flag A2-level errors").
- Run each sentence several times at temperature > 0 to see how consistent it is.

## Reading

- Coyne et al. 2023, *An Analysis of GPT-3's Performance in Grammatical Error Correction*: over-correction, and minimal vs fluent edits.
- Bryant et al. 2023, *Grammatical Error Correction: A Survey of the State of the Art*: how GEC is evaluated (ERRANT, M²).
