# Experiments

Each folder answers one question about [planning.md](../planning.md). Each one is meant to be thrown away. What you keep is what you learned, written down in [LOG.md](LOG.md).

| Track | Question | Deps group |
| --- | --- | --- |
| [01-llm-correction](01-llm-correction/) | Can a local LLM reliably find and tag French errors, and is it fast enough on CPU? | none (stdlib + Ollama) |
| [02-pronunciation](02-pronunciation/) | Can we score pronunciation at the phoneme level, and does Whisper hide mistakes? | `speech` |
| [03-learner-model](03-learner-model/) | How do BKT and FSRS behave, and how much grading noise can BKT tolerate? | `learner` |
| [04-tts-avatar](04-tts-avatar/) | Does Piper give usable phoneme timings for lip-sync? | `tts` |

## Setup

```bash
cd experiments
uv sync --group learner --group speech --group tts   # or just the group you need
uv run python <track>/<script>.py --help
```

Optional: `uv sync --all-groups` adds JupyterLab (`uv run jupyter lab`) if you'd rather poke at things in notebooks.

The environment is pinned to Python 3.12 with CPU-only torch, because this machine has no NVIDIA GPU.

## Conventions

- Every script takes `--help`. Outputs go to the track's `results/` folder, which is git-ignored.
- After each experiment, add an entry to [LOG.md](LOG.md). If the result contradicts `planning.md`, update the plan.
