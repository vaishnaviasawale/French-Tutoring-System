# French tutoring system

A fully local, adaptive French tutor (conversation, pronunciation, writing, spaced repetition, weak-spot tracking, avatar). The architecture is in @planning.md. Right now the repo only has throwaway experiments in `experiments/`, which feed decisions back into the plan.

## Workflow
- `experiments/LOG.md` is the lab notebook. After each experiment, add a short entry. The "Changes to plan" line matters most. If a result contradicts `planning.md`, update the plan in the same change.
- Experiments are meant to be thrown away. Keep scripts small, give each a `--help`, and write outputs to the track's git-ignored `results/` folder.

## Commands (run from `experiments/`)
- Setup: `uv sync --group <learner|speech|tts>`. Only install the groups a track needs.
- Run: `uv run python <track>/<script>.py --help`
- Lint and format: `uv run ruff check --fix . && uv run ruff format .`

## Conventions
- Python 3.12 only. Torch is CPU-only because there is no NVIDIA GPU, so don't add CUDA wheels.
- Manage dependencies with uv (`uv add`), never `pip install`. Put new dependencies in the right group.
- Line length is 120 (`pyproject.toml`). Ruff is the linter and formatter. A hook runs it after every Python edit and before `git commit`, so don't fight it. `.flake8` is legacy.
- Everything must run offline once models are downloaded. Don't add a cloud API call without asking.
- Local models (Ollama, whisper, Piper) are the default. Report latency on CPU, because speed is a real constraint.

## Working with Claude here
- Use plan mode for anything that touches more than one track or `planning.md`.
- Don't spawn subagents unless asked. Keep token use low.
- Before a commit, run `/code-review` on the diff. Run `/security-review` before any change that handles user data, recordings, or API keys.
