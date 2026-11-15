"""Bayesian Knowledge Tracing update (same rule as planning.md §4)."""


def update_mastery(p_known: float, correct: bool, p_learn=0.1, p_slip=0.1, p_guess=0.2) -> float:
    # Bayesian update given observation
    if correct:
        numer = p_known * (1 - p_slip)
        denom = numer + (1 - p_known) * p_guess
    else:
        numer = p_known * p_slip
        denom = numer + (1 - p_known) * (1 - p_guess)
    p_known_given_obs = numer / denom
    # apply learning transition
    return p_known_given_obs + (1 - p_known_given_obs) * p_learn
