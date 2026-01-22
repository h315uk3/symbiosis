#!/usr/bin/env python3
"""SM-2 (SuperMemo 2) spaced repetition algorithm for pattern memory.

SM-2 is a spaced repetition algorithm developed by Piotr Wozniak in 1987.
It calculates optimal review intervals based on recall performance, making
learning more efficient by spacing reviews at increasing intervals.

Algorithm:
    EF' = EF + (0.1 - (5 - q) × (0.08 + (5 - q) × 0.02))
    EF' = max(1.3, EF')

    If q < 3: repetitions = 0, interval = 1
    If repetitions == 0: interval = 1
    If repetitions == 1: interval = 6
    If repetitions > 1: interval = previous_interval × EF'

Where:
    EF: Easiness Factor (quality of recall, min 1.3)
    q: Quality of recall (0-5, where 5 is perfect)
    repetitions: Number of consecutive successful recalls

References:
    Wozniak, P. (1990). Optimization of learning.
    https://www.supermemo.com/en/archives1990-2015/english/ol
"""

import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

# Add plugin to path for imports
_PLUGIN_ROOT = Path(__file__).parent.parent.parent
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from as_you.lib.common import DEFAULT_SETTINGS  # noqa: E402

# SM-2 constants
MIN_EASINESS_FACTOR = 1.3
INITIAL_EASINESS_FACTOR = 2.5
PERFECT_RECALL = 5
MIN_QUALITY = 0
MAX_QUALITY = 5
PASS_THRESHOLD = 3  # Quality < 3 is considered failed recall


@dataclass
class SM2State:
    """SM-2 memory state.

    Examples:
        >>> state = SM2State(easiness_factor=2.5, interval=1, repetitions=0)
        >>> state.easiness_factor
        2.5
        >>> state.interval
        1
        >>> state.repetitions
        0
    """

    easiness_factor: float  # Quality of recall (min 1.3)
    interval: int  # Days until next review
    repetitions: int  # Consecutive successful recalls


def calculate_new_easiness(easiness_factor: float, quality: int) -> float:
    """Calculate new easiness factor based on recall quality.

    Args:
        easiness_factor: Current easiness factor
        quality: Recall quality (0-5, where 5 is perfect)

    Returns:
        New easiness factor (min 1.3)

    Examples:
        >>> calculate_new_easiness(2.5, 5)  # Perfect recall
        2.6
        >>> calculate_new_easiness(2.5, 3)  # Adequate recall
        2.36
        >>> round(calculate_new_easiness(2.5, 0), 2)  # Failed recall
        1.7
        >>> calculate_new_easiness(1.5, 0)  # Already low, can't go below 1.3
        1.3
    """
    if quality < MIN_QUALITY or quality > MAX_QUALITY:
        msg = f"Quality must be {MIN_QUALITY}-{MAX_QUALITY}, got {quality}"
        raise ValueError(msg)

    # SM-2 formula
    new_ef = easiness_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))

    # Enforce minimum
    return max(MIN_EASINESS_FACTOR, new_ef)


def calculate_next_interval(
    current_interval: int, repetitions: int, easiness_factor: float, quality: int
) -> int:
    """Calculate next review interval.

    Args:
        current_interval: Current interval in days
        repetitions: Number of consecutive successful recalls
        easiness_factor: Current easiness factor
        quality: Recall quality (0-5)

    Returns:
        Next interval in days

    Examples:
        >>> calculate_next_interval(1, 0, 2.5, 4)  # First review, good recall
        1
        >>> calculate_next_interval(1, 1, 2.5, 4)  # Second review
        6
        >>> calculate_next_interval(6, 2, 2.5, 4)  # Third review
        15
        >>> calculate_next_interval(15, 3, 2.5, 5)  # Fourth review, perfect
        37
        >>> calculate_next_interval(6, 2, 2.5, 2)  # Failed recall
        1
    """
    if quality < PASS_THRESHOLD:
        # Failed recall - restart
        return 1

    # Successful recall
    if repetitions == 0:
        return 1
    elif repetitions == 1:
        return 6
    else:
        # Multiply by easiness factor
        return int(current_interval * easiness_factor)


def update_sm2_state(state: SM2State, quality: int) -> SM2State:
    """Update SM-2 state based on recall quality.

    Args:
        state: Current SM-2 state
        quality: Recall quality (0-5)

    Returns:
        New SM-2 state

    Examples:
        >>> state = SM2State(2.5, 1, 0)
        >>> new_state = update_sm2_state(state, 4)
        >>> new_state.interval
        1
        >>> new_state.repetitions
        1
        >>> state2 = update_sm2_state(new_state, 4)
        >>> state2.interval
        6
        >>> state2.repetitions
        2
        >>> state3 = update_sm2_state(state2, 4)
        >>> state3.interval
        15
        >>> state3.repetitions
        3
        >>> # Failed recall resets
        >>> failed = update_sm2_state(state3, 2)
        >>> failed.interval
        1
        >>> failed.repetitions
        0
    """
    # Calculate new easiness factor
    new_ef = calculate_new_easiness(state.easiness_factor, quality)

    # Update repetitions (failed recall resets, successful increments)
    new_reps = 0 if quality < PASS_THRESHOLD else state.repetitions + 1

    # Calculate next interval
    new_interval = calculate_next_interval(
        state.interval, state.repetitions, new_ef, quality
    )

    return SM2State(easiness_factor=new_ef, interval=new_interval, repetitions=new_reps)


def calculate_next_review_date(last_review: datetime, interval: int) -> datetime:
    """Calculate next review date.

    Args:
        last_review: Date of last review
        interval: Interval in days

    Returns:
        Next review date

    Examples:
        >>> from datetime import datetime
        >>> last = datetime(2026, 1, 1)
        >>> next_date = calculate_next_review_date(last, 6)
        >>> next_date.day
        7
        >>> next_date.month
        1
    """
    return last_review + timedelta(days=interval)


def is_review_due(last_review: datetime, interval: int, current: datetime) -> bool:
    """Check if review is due.

    Args:
        last_review: Date of last review
        interval: Interval in days
        current: Current date

    Returns:
        True if review is due

    Examples:
        >>> from datetime import datetime
        >>> last = datetime(2026, 1, 1)
        >>> current = datetime(2026, 1, 8)
        >>> is_review_due(last, 6, current)  # 7 days passed, interval is 6
        True
        >>> is_review_due(last, 6, datetime(2026, 1, 5))  # Only 4 days
        False
    """
    next_review = calculate_next_review_date(last_review, interval)
    return current >= next_review


def create_initial_state(
    initial_ef: float | None = None,
) -> SM2State:
    """Create initial SM-2 state for new pattern.

    Args:
        initial_ef: Initial easiness factor (None = use default)

    Returns:
        Initial SM-2 state

    Examples:
        >>> state = create_initial_state()
        >>> state.easiness_factor
        2.5
        >>> state.interval
        1
        >>> state.repetitions
        0
        >>> custom = create_initial_state(2.0)
        >>> custom.easiness_factor
        2.0
    """
    if initial_ef is None:
        initial_ef = DEFAULT_SETTINGS["memory"]["sm2"]["initial_easiness"]

    return SM2State(
        easiness_factor=initial_ef,
        interval=1,
        repetitions=0,
    )


if __name__ == "__main__":
    import doctest

    # Check if running doctests
    if "--test" in sys.argv or "-v" in sys.argv:
        print("Running SM-2 memory doctests:")
        results = doctest.testmod(verbose=("--verbose" in sys.argv or "-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        # Demo
        print("SM-2 Memory Model Demo")
        print("-" * 50)

        state = create_initial_state()
        print(f"Initial state: {state}")

        # Simulate reviews
        qualities = [4, 4, 5, 3, 5]
        for i, q in enumerate(qualities, 1):
            state = update_sm2_state(state, q)
            print(f"Review {i} (quality={q}): {state}")
