"""Watch how FSRS schedules a card under different review histories.

    uv run python 03-learner-model/fsrs_play.py
    uv run python 03-learner-model/fsrs_play.py --retention 0.8    # fewer reviews, more forgetting

Assumes each review happens exactly when the card is due.
"""

import argparse
from datetime import UTC, datetime

from fsrs import Card, Rating, Scheduler

A, H, G, E = Rating.Again, Rating.Hard, Rating.Good, Rating.Easy
HISTORIES = {
    "always good": [G] * 8,
    "forgot once": [G, G, G, A, G, G, G, G],
    "always hard": [H] * 8,
    "always easy": [E] * 8,
}


def fmt_interval(delta) -> str:
    secs = delta.total_seconds()
    return f"{secs / 60:.0f}m" if secs < 86400 else f"{secs / 86400:.1f}d"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--retention", type=float, default=0.9, help="desired probability of recall when a card is due")
    args = ap.parse_args()

    scheduler = Scheduler(desired_retention=args.retention)
    start = datetime(2026, 1, 1, 9, 0, tzinfo=UTC)

    for name, ratings in HISTORIES.items():
        print(f"\n--- {name} ---")
        print(f"{'#':>2} {'rating':7} {'state':10} {'stability':>9} {'difficulty':>10} {'next in':>8} {'total':>7}")
        card, now = Card(due=start), start
        for i, rating in enumerate(ratings, 1):
            card, _ = scheduler.review_card(card, rating, review_datetime=now)
            print(
                f"{i:2} {rating.name:7} {card.state.name:10} {card.stability:9.2f} {card.difficulty:10.2f} "
                f"{fmt_interval(card.due - now):>8} {fmt_interval(card.due - start):>7}"
            )
            now = card.due


if __name__ == "__main__":
    main()
