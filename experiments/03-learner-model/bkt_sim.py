"""Simulate learners with a known ground truth and see how well BKT tracks them.

    uv run python 03-learner-model/bkt_sim.py
    uv run python 03-learner-model/bkt_sim.py --noise 0 0.1 0.2 0.3 --plot
    uv run python 03-learner-model/bkt_sim.py --true-learn 0.05 --tracker-learn 0.2   # misspecified tracker

"noise" = probability the grader (the LLM from track 01) flips correct/incorrect.
"""

import argparse
from pathlib import Path

import numpy as np
from bkt import update_mastery

HERE = Path(__file__).parent


def simulate(rng, n_learners, n_attempts, true, tracker, noise, p_init):
    """Returns (truth, estimate) arrays of shape (n_learners, n_attempts), estimate taken *before* each attempt."""
    truth = np.zeros((n_learners, n_attempts), dtype=bool)
    est = np.zeros((n_learners, n_attempts))
    for i in range(n_learners):
        known = rng.random() < true["p_init"]
        p = p_init
        for t in range(n_attempts):
            truth[i, t], est[i, t] = known, p
            correct = rng.random() < (1 - true["p_slip"] if known else true["p_guess"])
            if rng.random() < noise:
                correct = not correct
            p = update_mastery(p, correct, **tracker)
            if not known and rng.random() < true["p_learn"]:
                known = True
    return truth, est


def metrics(truth, est, threshold):
    mastered = est >= threshold
    lags = []
    for row_t, row_m in zip(truth, mastered):
        if row_t.any() and not row_t[0]:
            learned_at = row_t.argmax()
            hits = np.flatnonzero(row_m[learned_at:])
            lags.append(hits[0] if hits.size else len(row_t) - learned_at)
    return {
        "brier": float(np.mean((est - truth) ** 2)),
        "false_mastery": float(np.mean(mastered & ~truth)),  # says "known" while it isn't -> stops practising too early
        "wasted_drill": float(np.mean(~mastered & truth)),  # says "weak" while it's known -> boring repetition
        "detect_lag": float(np.mean(lags)) if lags else float("nan"),  # attempts from learning to being recognised
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--learners", type=int, default=2000)
    ap.add_argument("--attempts", type=int, default=30)
    ap.add_argument("--noise", type=float, nargs="+", default=[0.0, 0.1, 0.2, 0.3])
    ap.add_argument("--threshold", type=float, default=0.6, help="p_known below this = weak (planning.md)")
    ap.add_argument("--p-init", type=float, default=0.3, help="tracker's starting p_known (schema default)")
    for side, defaults in (("true", (0.1, 0.1, 0.2)), ("tracker", (0.1, 0.1, 0.2))):
        for name, d in zip(("learn", "slip", "guess"), defaults):
            ap.add_argument(f"--{side}-{name}", type=float, default=d)
    ap.add_argument("--true-init", type=float, default=0.2, help="fraction of learners who already know the concept")
    ap.add_argument("--plot", action="store_true", help=f"save a plot to {HERE / 'results'}")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    true = {"p_init": args.true_init, "p_learn": args.true_learn, "p_slip": args.true_slip, "p_guess": args.true_guess}
    tracker = {"p_learn": args.tracker_learn, "p_slip": args.tracker_slip, "p_guess": args.tracker_guess}

    curves = {}
    print(f"{'noise':>6} {'brier':>7} {'false_mastery':>14} {'wasted_drill':>13} {'detect_lag':>11}")
    for noise in args.noise:
        rng = np.random.default_rng(args.seed)
        truth, est = simulate(rng, args.learners, args.attempts, true, tracker, noise, args.p_init)
        m = metrics(truth, est, args.threshold)
        curves[noise] = (truth.mean(axis=0), est.mean(axis=0))
        print(
            f"{noise:6.2f} {m['brier']:7.3f} {m['false_mastery']:14.3f} {m['wasted_drill']:13.3f} {m['detect_lag']:11.1f}"
        )

    if args.plot:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(next(iter(curves.values()))[0], "k--", label="truth: fraction known")
        for noise, (_, est_mean) in curves.items():
            ax.plot(est_mean, label=f"BKT estimate, noise={noise}")
        ax.axhline(args.threshold, color="grey", lw=0.5)
        ax.set(xlabel="attempt", ylabel="p(known), averaged over learners", ylim=(0, 1))
        ax.legend()
        out = HERE / "results" / "bkt_sim.png"
        fig.savefig(out, dpi=120, bbox_inches="tight")
        print(f"\nSaved {out}")


if __name__ == "__main__":
    main()
