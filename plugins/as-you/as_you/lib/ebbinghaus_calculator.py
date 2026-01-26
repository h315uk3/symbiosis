#!/usr/bin/env python3
"""Ebbinghaus Forgetting Curve for pattern memory decay.

Implements the Ebbinghaus forgetting curve for modeling how pattern
relevance decreases over time, with repetition strengthening memory.

Formula:
    R(t) = e^(-t/s)

Where:
    t: Time elapsed since last seen (days)
    s: Memory strength (increases with repetition)
    R(t): Retention rate at time t

Key properties:
1. Repeated patterns have higher s → slower decay
2. Single-occurrence patterns decay faster
3. Based on cognitive psychology research

References:
    Ebbinghaus, H. (1885). Memory: A Contribution to Experimental Psychology.
    Murre, J. M., & Dros, J. (2015). Replication and Analysis of Ebbinghaus'
    Forgetting Curve. PLOS ONE.
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


def calculate_memory_strength(
    repetitions: int, base_strength: float = 1.0, growth_factor: float = 0.5
) -> float:
    """Calculate memory strength based on repetition count.

    Memory strength increases with each repetition, making the pattern
    more resistant to forgetting.

    Args:
        repetitions: Number of times pattern has been observed
        base_strength: Base memory strength (default: 1.0)
        growth_factor: How much each repetition increases strength (default: 0.5)

    Returns:
        Memory strength (s)

    Examples:
        >>> # Single occurrence (weak memory)
        >>> calculate_memory_strength(1)
        1.0
        >>> # Multiple occurrences (stronger memory)
        >>> calculate_memory_strength(5)
        3.0
        >>> # Many occurrences (very strong memory)
        >>> calculate_memory_strength(10)
        5.5
        >>> # Custom base and growth
        >>> calculate_memory_strength(3, base_strength=2.0, growth_factor=1.0)
        4.0
    """
    if repetitions < 1:
        msg = "repetitions must be at least 1"
        raise ValueError(msg)

    # s = base + growth * (n - 1)
    # First occurrence has base strength, each additional adds growth_factor
    return base_strength + growth_factor * (repetitions - 1)


def ebbinghaus_retention(days_elapsed: float, strength: float) -> float:
    """Calculate retention using Ebbinghaus forgetting curve.

    R(t) = e^(-t/s)

    Args:
        days_elapsed: Days since pattern was last seen
        strength: Memory strength (higher = slower decay)

    Returns:
        Retention rate (0-1)

    Examples:
        >>> # No time passed, perfect retention
        >>> ebbinghaus_retention(0, 1.0)
        1.0
        >>> # Weak memory (s=1), 1 day elapsed
        >>> round(ebbinghaus_retention(1, 1.0), 3)
        0.368
        >>> # Strong memory (s=3), 1 day elapsed
        >>> round(ebbinghaus_retention(1, 3.0), 3)
        0.717
        >>> # Same elapsed time, stronger memory retains better
        >>> weak = ebbinghaus_retention(7, 1.0)
        >>> strong = ebbinghaus_retention(7, 5.0)
        >>> strong > weak
        True
    """
    if days_elapsed < 0:
        msg = "days_elapsed must be non-negative"
        raise ValueError(msg)
    if strength <= 0:
        msg = "strength must be positive"
        raise ValueError(msg)

    # R(t) = e^(-t/s)
    return math.exp(-days_elapsed / strength)


def calculate_ebbinghaus_score(
    days_elapsed: float,
    repetitions: int,
    base_strength: float = 1.0,
    growth_factor: float = 0.5,
) -> float:
    """Calculate Ebbinghaus-based relevance score.

    Combines time elapsed with repetition count to determine pattern relevance.

    Args:
        days_elapsed: Days since pattern was last seen
        repetitions: Number of times pattern has been observed
        base_strength: Base memory strength
        growth_factor: Strength increase per repetition

    Returns:
        Relevance score (0-1)

    Examples:
        >>> # Recent, single occurrence
        >>> round(calculate_ebbinghaus_score(1, 1), 3)
        0.368
        >>> # Recent, repeated pattern (stronger memory)
        >>> round(calculate_ebbinghaus_score(1, 5), 3)
        0.717
        >>> # Old, single occurrence (mostly forgotten)
        >>> round(calculate_ebbinghaus_score(30, 1), 4)
        0.0
        >>> # Old, repeated pattern (better retention)
        >>> round(calculate_ebbinghaus_score(30, 10), 3)
        0.004
    """
    strength = calculate_memory_strength(repetitions, base_strength, growth_factor)
    retention = ebbinghaus_retention(days_elapsed, strength)
    return round(retention, 6)


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


def calculate_ebbinghaus_scores(
    patterns: dict[str, dict],
    base_strength: float | None = None,
    growth_factor: float | None = None,
    current: datetime | None = None,
) -> dict[str, float]:
    """Calculate Ebbinghaus scores for all patterns.

    Args:
        patterns: Pattern dictionary from tracker
        base_strength: Base memory strength (None = use default)
        growth_factor: Growth per repetition (None = use default)
        current: Current datetime (None = now)

    Returns:
        Dictionary mapping pattern text to Ebbinghaus score

    Examples:
        >>> from datetime import datetime
        >>> patterns = {
        ...     "recent_frequent": {"last_seen": "2026-01-20", "count": 10},
        ...     "recent_rare": {"last_seen": "2026-01-20", "count": 1},
        ...     "old_frequent": {"last_seen": "2025-12-01", "count": 10},
        ...     "old_rare": {"last_seen": "2025-12-01", "count": 1},
        ... }
        >>> current = datetime(2026, 1, 22)
        >>> scores = calculate_ebbinghaus_scores(patterns, current=current)
        >>> # Recent frequent > recent rare
        >>> scores["recent_frequent"] > scores["recent_rare"]
        True
        >>> # Recent > old (regardless of frequency)
        >>> scores["recent_rare"] > scores["old_frequent"]
        True
    """
    if base_strength is None:
        base_strength = float(
            DEFAULT_SETTINGS["memory"]["ebbinghaus"]["base_strength"]
        )
    if growth_factor is None:
        growth_factor = float(
            DEFAULT_SETTINGS["memory"]["ebbinghaus"]["growth_factor"]
        )

    if current is None:
        current = datetime.now()

    scores = {}
    for pattern_text, pattern_data in patterns.items():
        last_seen = pattern_data.get("last_seen")
        count = pattern_data.get("count", 1)

        if not last_seen:
            # No last_seen date, assume very old
            scores[pattern_text] = 0.01
            continue

        try:
            days_elapsed = calculate_days_elapsed(last_seen, current)
            # Clamp to non-negative
            days_elapsed = max(0, days_elapsed)
            scores[pattern_text] = calculate_ebbinghaus_score(
                days_elapsed, count, base_strength, growth_factor
            )
        except ValueError:
            # Invalid date format
            scores[pattern_text] = 0.01

    return scores


def main():
    """CLI entry point."""
    config = AsYouConfig.from_environment()

    print("実行中: Ebbinghaus Calculator")
    print("-" * 50)

    # Load patterns
    data = load_tracker(config.tracker_file)
    patterns = data.get("patterns", {})

    if not patterns:
        print("パターンが見つかりません")
        return

    # Get Ebbinghaus parameters from config
    ebbinghaus_config = config.settings["memory"]["ebbinghaus"]
    base_strength = ebbinghaus_config["base_strength"]
    growth_factor = ebbinghaus_config["growth_factor"]

    print(f"基本強度: {base_strength}, 成長係数: {growth_factor}")

    # Calculate scores
    scores = calculate_ebbinghaus_scores(patterns, base_strength, growth_factor)

    # Update patterns
    for pattern_text, score in scores.items():
        if pattern_text in patterns:
            patterns[pattern_text]["ebbinghaus_score"] = score

    # Save updated data
    save_tracker(config.tracker_file, data)
    print(f"✓ {len(scores)}個のパターンにEbbinghausスコアを計算しました")

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
        print("Running Ebbinghaus calculator doctests:")
        results = doctest.testmod(verbose=("--verbose" in sys.argv or "-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
