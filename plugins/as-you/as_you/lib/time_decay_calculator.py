#!/usr/bin/env python3
"""Time decay calculator for pattern relevance over time.

Time decay models the decreasing relevance of patterns as they age.
Using exponential decay with a configurable half-life, we reduce the
weight of older patterns while keeping recent patterns prominent.

Formula:
    decay_factor = 0.5^(days_elapsed / half_life_days)
    decayed_score = original_score × decay_factor

Where:
    days_elapsed: Days since pattern was last seen
    half_life_days: Days for score to decay to 50%

This ensures:
1. Recent patterns (< half_life) maintain high relevance
2. Old patterns gradually fade but never reach zero
3. Configurable decay rate via half_life parameter

References:
    Exponential decay is commonly used in information retrieval and
    recommendation systems to model temporal relevance.
"""

import math
import sys
from datetime import datetime
from pathlib import Path

# Add plugin to path for imports
_PLUGIN_ROOT = Path(__file__).parent.parent.parent
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from as_you.lib.common import (  # noqa: E402
    DEFAULT_SETTINGS,
    AsYouConfig,
    load_tracker,
    save_tracker,
)

# Score thresholds for categorization
RECENT_THRESHOLD = 0.75  # Patterns with score > 0.75 are recent
OLD_THRESHOLD = 0.25  # Patterns with score < 0.25 are old


def calculate_decay_factor(days_elapsed: float, half_life_days: float) -> float:
    """Calculate exponential decay factor.

    Args:
        days_elapsed: Days since pattern was last seen
        half_life_days: Days for score to decay to 50%

    Returns:
        Decay factor (0-1)

    Examples:
        >>> # After 0 days, no decay
        >>> calculate_decay_factor(0, 30)
        1.0
        >>> # After half-life, 50% decay
        >>> calculate_decay_factor(30, 30)
        0.5
        >>> # After 2x half-life, 25% remains
        >>> calculate_decay_factor(60, 30)
        0.25
        >>> # After 3x half-life, 12.5% remains
        >>> round(calculate_decay_factor(90, 30), 3)
        0.125
        >>> # Shorter half-life = faster decay
        >>> short_decay = calculate_decay_factor(10, 10)
        >>> long_decay = calculate_decay_factor(10, 30)
        >>> short_decay < long_decay
        True
    """
    if days_elapsed < 0:
        msg = "days_elapsed must be non-negative"
        raise ValueError(msg)
    if half_life_days <= 0:
        msg = "half_life_days must be positive"
        raise ValueError(msg)

    # 0.5^(days_elapsed / half_life_days)
    exponent = days_elapsed / half_life_days
    return math.pow(0.5, exponent)


def apply_time_decay(score: float, days_elapsed: float, half_life_days: float) -> float:
    """Apply time decay to a score.

    Args:
        score: Original score
        days_elapsed: Days since pattern was last seen
        half_life_days: Days for score to decay to 50%

    Returns:
        Decayed score

    Examples:
        >>> # Recent pattern (5 days old, half-life 30)
        >>> round(apply_time_decay(1.0, 5, 30), 2)
        0.89
        >>> # Older pattern (30 days old)
        >>> apply_time_decay(1.0, 30, 30)
        0.5
        >>> # Very old pattern (90 days old)
        >>> round(apply_time_decay(1.0, 90, 30), 3)
        0.125
        >>> # High score with decay
        >>> round(apply_time_decay(0.8, 30, 30), 2)
        0.4
    """
    decay_factor = calculate_decay_factor(days_elapsed, half_life_days)
    return round(score * decay_factor, 6)


def calculate_days_elapsed(last_seen: str, current: datetime | None = None) -> float:
    """Calculate days elapsed since last seen.

    Args:
        last_seen: ISO date string (YYYY-MM-DD)
        current: Current datetime (None = now)

    Returns:
        Days elapsed

    Examples:
        >>> from datetime import datetime
        >>> # 10 days elapsed
        >>> current = datetime(2026, 1, 11)
        >>> days = calculate_days_elapsed("2026-01-01", current)
        >>> days
        10.0
        >>> # Same day
        >>> days = calculate_days_elapsed("2026-01-11", current)
        >>> days
        0.0
        >>> # Future date (negative)
        >>> days = calculate_days_elapsed("2026-01-20", current)
        >>> days < 0
        True
    """
    if current is None:
        current = datetime.now()

    try:
        last_seen_date = datetime.fromisoformat(last_seen)
    except ValueError as e:
        msg = f"Invalid date format: {last_seen}"
        raise ValueError(msg) from e

    delta = current - last_seen_date
    return delta.total_seconds() / (24 * 3600)


def calculate_time_decay_scores(
    patterns: dict[str, dict],
    half_life_days: float | None = None,
    current: datetime | None = None,
) -> dict[str, float]:
    """Calculate time decay scores for all patterns.

    Args:
        patterns: Pattern dictionary from tracker
        half_life_days: Half-life in days (None = use default)
        current: Current datetime (None = now)

    Returns:
        Dictionary mapping pattern text to decay score

    Examples:
        >>> from datetime import datetime
        >>> patterns = {
        ...     "recent": {"last_seen": "2026-01-20"},
        ...     "old": {"last_seen": "2025-12-21"},
        ...     "very_old": {"last_seen": "2025-10-22"},
        ... }
        >>> current = datetime(2026, 1, 22)
        >>> scores = calculate_time_decay_scores(patterns, 30, current)
        >>> # Recent pattern (2 days) has high score
        >>> scores["recent"] > 0.9
        True
        >>> # Old pattern (32 days) has ~50% score
        >>> 0.4 < scores["old"] < 0.6
        True
        >>> # Very old pattern (92 days) has low score
        >>> scores["very_old"] < 0.2
        True
    """
    if half_life_days is None:
        config_value = (
            DEFAULT_SETTINGS.get("scoring", {})
            .get("time_decay", {})
            .get("half_life_days", 30.0)
        )
        half_life_days = float(config_value) if config_value is not None else 30.0

    if current is None:
        current = datetime.now()

    scores = {}
    for pattern_text, pattern_data in patterns.items():
        last_seen = pattern_data.get("last_seen")
        if not last_seen:
            # No last_seen date, assume very old (use max decay)
            scores[pattern_text] = 0.01
            continue

        try:
            days_elapsed = calculate_days_elapsed(last_seen, current)
            # Clamp to non-negative (future dates get score 1.0)
            days_elapsed = max(0, days_elapsed)
            scores[pattern_text] = apply_time_decay(1.0, days_elapsed, half_life_days)
        except ValueError:
            # Invalid date format, treat as very old
            scores[pattern_text] = 0.01

    return scores


def main():
    """CLI entry point."""
    config = AsYouConfig.from_environment()

    print("実行中: Time Decay Calculator")
    print("-" * 50)

    # Load patterns
    data = load_tracker(config.tracker_file)
    patterns = data.get("patterns", {})

    if not patterns:
        print("パターンが見つかりません")
        return

    # Get time decay parameters from config
    time_decay_config = config.settings["scoring"]["time_decay"]
    half_life_days = time_decay_config["half_life_days"]

    print(f"半減期: {half_life_days}日")

    # Calculate scores
    scores = calculate_time_decay_scores(patterns, half_life_days)

    # Update patterns
    for pattern_text, score in scores.items():
        if pattern_text in patterns:
            patterns[pattern_text]["time_decay_score"] = score

    # Save updated data
    save_tracker(config.tracker_file, data)
    print(f"✓ {len(scores)}個のパターンに時間減衰スコアを計算しました")

    # Show statistics
    recent_count = sum(1 for s in scores.values() if s > RECENT_THRESHOLD)
    medium_count = sum(
        1 for s in scores.values() if OLD_THRESHOLD <= s <= RECENT_THRESHOLD
    )
    old_count = sum(1 for s in scores.values() if s < OLD_THRESHOLD)

    print("\n統計:")
    print(f"  最近のパターン (>{RECENT_THRESHOLD}): {recent_count}")
    print(f"  中程度のパターン ({OLD_THRESHOLD}-{RECENT_THRESHOLD}): {medium_count}")
    print(f"  古いパターン (<{OLD_THRESHOLD}): {old_count}")


if __name__ == "__main__":
    import doctest

    # Check if running doctests
    if "--test" in sys.argv or "-v" in sys.argv:
        print("Running time decay calculator doctests:")
        results = doctest.testmod(verbose=("--verbose" in sys.argv or "-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
