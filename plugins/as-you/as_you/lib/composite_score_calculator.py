#!/usr/bin/env python3
"""Composite score calculator for pattern ranking.

Combines multiple scoring dimensions (BM25, PMI, time decay) into a single
composite score using weighted linear combination. This allows flexible
tuning of pattern ranking by adjusting weights in configuration.

Formula:
    composite_score = Σ(weight_i × score_i) for all enabled scoring dimensions

Where:
    weight_i: Weight for dimension i (configured in as-you.json)
    score_i: Normalized score for dimension i (0-1 range)

Requirements:
    - All weights must sum to 1.0 (validated in config)
    - All scores must be normalized to [0, 1] range
    - Missing scores are treated as 0.0

This design allows:
1. Easy addition of new scoring dimensions
2. Dynamic weight tuning without code changes
3. Transparent ranking based on configurable priorities
"""

import sys
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

# Score normalization constants
MIN_SCORE = 0.0
MAX_SCORE = 1.0

# Display constants
MAX_PATTERN_DISPLAY_LENGTH = 50  # Max characters to display for pattern text


def normalize_scores(scores: dict[str, float]) -> dict[str, float]:
    """Normalize scores to [0, 1] range using min-max normalization.

    Args:
        scores: Dictionary mapping pattern text to score

    Returns:
        Dictionary with normalized scores

    Examples:
        >>> scores = {"a": 10.0, "b": 5.0, "c": 0.0}
        >>> normalized = normalize_scores(scores)
        >>> normalized["a"]
        1.0
        >>> normalized["b"]
        0.5
        >>> normalized["c"]
        0.0
        >>> # Single value
        >>> scores2 = {"x": 5.0}
        >>> normalize_scores(scores2)["x"]
        1.0
        >>> # All same values (no variation)
        >>> scores3 = {"a": 0.0, "b": 0.0}
        >>> normalize_scores(scores3)["a"]
        1.0
    """
    if not scores:
        return {}

    values = list(scores.values())
    min_val = min(values)
    max_val = max(values)

    # If all values are the same, return all 1.0
    if max_val == min_val:
        return {k: MAX_SCORE for k in scores}

    # Min-max normalization
    range_val = max_val - min_val
    return {pattern: (score - min_val) / range_val for pattern, score in scores.items()}


def calculate_composite_score(
    pattern_scores: dict[str, float],
    weights: dict[str, float],
) -> float:
    """Calculate composite score from weighted components.

    Args:
        pattern_scores: Dictionary mapping dimension name to score
        weights: Dictionary mapping dimension name to weight

    Returns:
        Composite score (0-1)

    Examples:
        >>> scores = {"bm25": 0.8, "pmi": 0.6, "time_decay": 0.4}
        >>> weights = {"bm25": 0.4, "pmi": 0.3, "time_decay": 0.3}
        >>> round(calculate_composite_score(scores, weights), 2)
        0.62
        >>> # Missing dimension treated as 0.0
        >>> scores2 = {"bm25": 0.8, "time_decay": 0.4}
        >>> round(calculate_composite_score(scores2, weights), 2)
        0.44
        >>> # Only one dimension
        >>> scores3 = {"bm25": 1.0}
        >>> weights3 = {"bm25": 1.0}
        >>> calculate_composite_score(scores3, weights3)
        1.0
    """
    total = 0.0
    for dimension, weight in weights.items():
        score = pattern_scores.get(dimension, 0.0)
        total += weight * score
    return round(total, 6)


def calculate_composite_scores(
    patterns: dict[str, dict],
    weights: dict[str, float] | None = None,
    normalize: bool = True,
) -> dict[str, float]:
    """Calculate composite scores for all patterns.

    Args:
        patterns: Pattern dictionary from tracker
        weights: Weight dictionary (None = use default)
        normalize: Whether to normalize individual scores first

    Returns:
        Dictionary mapping pattern text to composite score

    Examples:
        >>> patterns = {
        ...     "pattern_a": {
        ...         "bm25_score": 10.0,
        ...         "pmi_score": 5.0,
        ...         "time_decay_score": 0.8,
        ...     },
        ...     "pattern_b": {
        ...         "bm25_score": 5.0,
        ...         "pmi_score": 2.0,
        ...         "time_decay_score": 0.6,
        ...     },
        ...     "pattern_c": {
        ...         "bm25_score": 0.0,
        ...         "pmi_score": 0.0,
        ...         "time_decay_score": 0.2,
        ...     },
        ... }
        >>> weights = {"bm25": 0.5, "pmi": 0.3, "time_decay": 0.2}
        >>> scores = calculate_composite_scores(patterns, weights, normalize=True)
        >>> # pattern_a should have highest score
        >>> scores["pattern_a"] > scores["pattern_b"] > scores["pattern_c"]
        True
        >>> # All scores should be in [0, 1] range
        >>> all(0.0 <= s <= 1.0 for s in scores.values())
        True
    """
    if weights is None:
        weights = DEFAULT_SETTINGS["scoring"]["weights"]

    # Collect all scores by dimension
    dimension_scores: dict[str, dict[str, float]] = {}

    # Map dimension names to score keys
    score_keys = {
        "bm25": "bm25_score",
        "pmi": "pmi_score",
        "time_decay": "time_decay_score",
    }

    # Extract scores for each dimension
    for dimension, score_key in score_keys.items():
        dimension_scores[dimension] = {
            pattern: data.get(score_key, 0.0) for pattern, data in patterns.items()
        }

    # Normalize scores if requested
    if normalize:
        for dimension, scores_dict in dimension_scores.items():
            dimension_scores[dimension] = normalize_scores(scores_dict)

    # Calculate composite scores
    composite_scores = {}
    for pattern in patterns:
        pattern_scores = {
            dimension: dimension_scores[dimension].get(pattern, 0.0)
            for dimension in weights
        }
        composite_scores[pattern] = calculate_composite_score(pattern_scores, weights)

    return composite_scores


def main():
    """CLI entry point."""
    config = AsYouConfig.from_environment()

    print("実行中: Composite Score Calculator")
    print("-" * 50)

    # Load patterns
    data = load_tracker(config.tracker_file)
    patterns = data.get("patterns", {})

    if not patterns:
        print("パターンが見つかりません")
        return

    # Get weights from config
    weights = config.settings["scoring"]["weights"]

    print("スコア重み:")
    for dimension, weight in weights.items():
        print(f"  {dimension}: {weight}")

    # Calculate composite scores
    scores = calculate_composite_scores(patterns, weights)

    # Update patterns
    for pattern_text, score in scores.items():
        if pattern_text in patterns:
            patterns[pattern_text]["composite_score"] = score

    # Save updated data
    save_tracker(config.tracker_file, data)
    print(f"\n✓ {len(scores)}個のパターンに統合スコアを計算しました")

    # Show top patterns
    top_patterns = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]
    print("\nトップ10パターン:")
    for i, (pattern_text, score) in enumerate(top_patterns, 1):
        # Truncate long patterns
        if len(pattern_text) > MAX_PATTERN_DISPLAY_LENGTH:
            display_text = pattern_text[:MAX_PATTERN_DISPLAY_LENGTH] + "..."
        else:
            display_text = pattern_text
        print(f"  {i}. {display_text}: {score:.4f}")


if __name__ == "__main__":
    import doctest

    # Check if running doctests
    if "--test" in sys.argv or "-v" in sys.argv:
        print("Running composite score calculator doctests:")
        results = doctest.testmod(verbose=("--verbose" in sys.argv or "-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
