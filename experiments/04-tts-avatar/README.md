# 04 — TTS and avatar lip-sync

**Questions:**
1. Which French voice sounds good enough to listen to every day, and is it fast on CPU?
2. Does Piper give phoneme timings accurate enough for lip-sync? (planning.md §6 assumes it does.)
3. How few mouth shapes can we get away with?

**Answer to question 2 so far:** yes, with a caveat. Stock voices don't output timings, but `PiperVoice.load(..., include_alignments=True)` patches the model in memory, which needs the `piper-tts[alignment]` extra. Timings come per Unicode codepoint, so `ɑ̃` arrives as `ɑ` plus a combining tilde. `visemes.py` folds those back together.

## Run

```bash
uv sync --group tts
uv run python -m piper.download_voices fr_FR-siwis-medium --download-dir 04-tts-avatar/voices   # already downloaded
uv run python 04-tts-avatar/piper_try.py "Bonjour ! Aujourd'hui, on va parler de ton week-end."
uv run python 04-tts-avatar/visemes.py 04-tts-avatar/results/sample.json
xdg-open 04-tts-avatar/viseme_player.html    # pick results/sample.wav + results/sample.visemes.json
```

Other French voices: run `uv run python -m piper.download_voices` with no arguments to list them all (`fr_FR-upmc-medium`, `fr_FR-tom-medium`, `fr_FR-gilles-low`, ...). Pass `--voice voices/<name>.onnx` to `piper_try.py`.

## Files

- `piper_try.py`: synthesis plus a per-phoneme timeline. Also prints the real-time factor; below 1 means faster than real time.
- `visemes.py`: maps IPA to 12 mouth shapes and merges adjacent duplicates. It reports any phoneme it couldn't map.
- `viseme_player.html`: a crude SVG mouth driven by the viseme timeline, for judging sync by eye before investing in a real rig.

## Experiments to try

- Does the sync look right in the player? Try shifting all timings by ±50 ms. Animators often open the mouth slightly *before* the sound.
- Try fewer shapes (6? 4?) by merging groups in `_GROUPS`. When does it start looking wrong?
- Compare Piper against a more expressive TTS model on naturalness vs speed.
- Next step for the real avatar: get the `pixi-live2d-display` demo running in a browser with a free sample model, then drive its mouth parameter from `*.visemes.json`.
