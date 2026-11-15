# 03 — Learner modeling (BKT + FSRS)

**Questions:**
1. How do BKT's parameters change how fast it decides you've learned something?
2. The correct/incorrect labels come from an LLM (track 01) that will sometimes be wrong. How much grading noise can BKT tolerate before it misleads the tutor?
3. How does FSRS space reviews, and what does `desired_retention` really trade off?

## Run

```bash
uv sync --group learner
uv run python 03-learner-model/bkt_sim.py --plot
uv run python 03-learner-model/bkt_sim.py --true-learn 0.05 --tracker-learn 0.2   # tracker assumes faster learning than reality
uv run python 03-learner-model/fsrs_play.py
uv run python 03-learner-model/fsrs_play.py --retention 0.8
```

## Files

- `bkt.py`: the update rule from planning.md §4, copied verbatim.
- `bkt_sim.py`: simulated learners with a known true state, plus a grader that flips labels with probability `noise`. Metrics:
  - **false_mastery**: tracker says "known" while it isn't, so the tutor stops practising too early.
  - **wasted_drill**: tracker says "weak" while it's known, so you get bored.
  - **detect_lag**: attempts between actually learning and the tracker noticing.
- `fsrs_play.py`: review histories and the intervals FSRS gives them.

## Experiments to try

- Plug the false-positive and missed rates from track 01 into `--noise`. Do the tracker's `p_slip`/`p_guess` absorb the noise if you raise them?
- Give the tracker wrong parameters on purpose (misspecification). In real life you won't know the true ones.
- Fit BKT parameters from simulated data (EM, or grid search on likelihood). This is the step before DKT.
- FSRS: how many reviews does a card need in its first month at retention 0.9 vs 0.8?

## Reading

- Corbett & Anderson 1994, *Knowledge Tracing: Modeling the Acquisition of Procedural Knowledge*.
- Pelánek 2017, *Bayesian knowledge tracing, logistic models, and beyond: an overview of learner modeling techniques*.
- Piech et al. 2015, *Deep Knowledge Tracing*.
- Settles & Meeder 2016, *A Trainable Spaced Repetition Model for Language Learning* (Duolingo half-life regression).
- Ye, Su & Cao 2022, *A Stochastic Shortest Path Algorithm for Optimizing Spaced Repetition Scheduling* (the work behind FSRS). The `open-spaced-repetition/fsrs4anki` wiki explains the model more readably.
