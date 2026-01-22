#!/usr/bin/env python3
"""Shannon Entropy for pattern diversity measurement.

Implements Shannon Entropy to measure pattern uncertainty and diversity
across different contexts (sessions, categories, co-occurrences).

Formula:
    H(X) = -Σ p(x) log₂ p(x)

Where:
    p(x): Probability of event x
    H(X): Entropy in bits

Key properties:
1. High entropy = Pattern appears in diverse contexts (general purpose)
2. Low entropy = Pattern appears in specific contexts (specialized)
3. Entropy = 0 when pattern only appears in one context
4. Maximum entropy when pattern uniformly distributed across contexts

References:
    Shannon, C. E. (1948). A Mathematical Theory of Communication.
    Cover, T. M., & Thomas, J. A. (2006). Elements of Information Theory.
"""

import math
import sys
from pathlib import Path

# Add plugin to path for imports
_PLUGIN_ROOT = Path(__file__).parent.parent.parent
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from as_you.lib.common import (  # noqa: E402
    AsYouConfig,
    load_tracker,
    save_tracker,
)

# Constants for probability validation (allow floating point error)
PROBABILITY_SUM_MIN = 0.99
PROBABILITY_SUM_MAX = 1.01

# Entropy thresholds for categorization
HIGH_ENTROPY_THRESHOLD = 0.7  # Patterns with high diversity (general purpose)
LOW_ENTROPY_THRESHOLD = 0.3  # Patterns with low diversity (specialized)


def calculate_entropy(probabilities: list[float]) -> float:
    """Calculate Shannon entropy from probability distribution.

    H(X) = -Σ p(x) log₂ p(x)

    Args:
        probabilities: List of probabilities (must sum to 1.0)

    Returns:
        Entropy in bits (0 to log₂(n))

    Examples:
        >>> # Uniform distribution (maximum entropy)
        >>> probs = [0.25, 0.25, 0.25, 0.25]
        >>> round(calculate_entropy(probs), 2)
        2.0
        >>> # Skewed distribution (lower entropy)
        >>> probs = [0.7, 0.2, 0.05, 0.05]
        >>> round(calculate_entropy(probs), 2)
        1.26
        >>> # Single outcome (zero entropy)
        >>> probs = [1.0]
        >>> calculate_entropy(probs)
        0.0
        >>> # Two equal outcomes
        >>> probs = [0.5, 0.5]
        >>> round(calculate_entropy(probs), 2)
        1.0
    """
    if not probabilities:
        return 0.0

    # Validate probabilities
    total = sum(probabilities)
    if not (PROBABILITY_SUM_MIN <= total <= PROBABILITY_SUM_MAX):
        msg = f"Probabilities must sum to 1.0, got {total}"
        raise ValueError(msg)

    entropy = 0.0
    for p in probabilities:
        if p > 0:
            # H = -Σ p(x) log₂ p(x)
            entropy -= p * math.log2(p)

    return round(entropy, 6)


def calculate_pattern_entropy(
    pattern_data: dict, context_key: str = "sessions"
) -> float:
    """Calculate entropy for a single pattern based on context distribution.

    Args:
        pattern_data: Pattern data dictionary
        context_key: Key for context data (default: "sessions")

    Returns:
        Entropy score (0 to log₂(n))

    Examples:
        >>> # Pattern appears in 4 sessions uniformly (high entropy)
        >>> pattern = {"sessions": ["s1", "s2", "s3", "s4"], "count": 8}
        >>> round(calculate_pattern_entropy(pattern), 2)
        2.0
        >>> # Pattern appears mostly in one session (low entropy)
        >>> pattern = {"sessions": ["s1", "s1", "s1", "s2"], "count": 4}
        >>> round(calculate_pattern_entropy(pattern), 2)
        0.81
        >>> # Pattern appears in only one session (zero entropy)
        >>> pattern = {"sessions": ["s1"], "count": 5}
        >>> calculate_pattern_entropy(pattern)
        0.0
        >>> # Pattern with categories
        >>> pattern = {"categories": ["style", "process", "style"], "count": 3}
        >>> round(calculate_pattern_entropy(pattern, context_key="categories"), 2)
        0.92
    """
    contexts = pattern_data.get(context_key, [])

    if not contexts:
        return 0.0

    # Count occurrences of each context
    context_counts: dict[str, int] = {}
    for context in contexts:
        context_counts[context] = context_counts.get(context, 0) + 1

    # Calculate probabilities
    total = sum(context_counts.values())
    probabilities = [count / total for count in context_counts.values()]

    return calculate_entropy(probabilities)


def calculate_shannon_entropy_scores(
    patterns: dict[str, dict],
    context_keys: list[str] | None = None,
    aggregation: str = "mean",
) -> dict[str, float]:
    """Calculate Shannon entropy scores for all patterns.

    Args:
        patterns: Pattern dictionary from tracker
        context_keys: List of context keys to analyze (default: ["sessions"])
        aggregation: How to combine multiple context entropies ("mean" or "max")

    Returns:
        Dictionary mapping pattern text to entropy score

    Examples:
        >>> patterns = {
        ...     "diverse_pattern": {
        ...         "sessions": ["s1", "s2", "s3", "s4"],
        ...         "count": 4,
        ...     },
        ...     "specialized_pattern": {
        ...         "sessions": ["s1", "s1", "s1", "s1"],
        ...         "count": 4,
        ...     },
        ...     "moderate_pattern": {
        ...         "sessions": ["s1", "s1", "s2"],
        ...         "count": 3,
        ...     },
        ... }
        >>> scores = calculate_shannon_entropy_scores(patterns)
        >>> # Diverse pattern should have highest entropy
        >>> scores["diverse_pattern"] > scores["moderate_pattern"]
        True
        >>> scores["moderate_pattern"] > scores["specialized_pattern"]
        True
        >>> # Specialized pattern should have zero entropy
        >>> scores["specialized_pattern"]
        0.0
    """
    if context_keys is None:
        context_keys = ["sessions"]

    scores = {}
    for pattern_text, pattern_data in patterns.items():
        entropies = []

        for context_key in context_keys:
            entropy = calculate_pattern_entropy(pattern_data, context_key)
            entropies.append(entropy)

        # Aggregate entropies
        if aggregation == "mean":
            score = sum(entropies) / len(entropies) if entropies else 0.0
        elif aggregation == "max":
            score = max(entropies) if entropies else 0.0
        else:
            msg = f"Unknown aggregation method: {aggregation}"
            raise ValueError(msg)

        scores[pattern_text] = round(score, 6)

    return scores


def normalize_entropy_scores(
    entropy_scores: dict[str, float], max_contexts: int = 10
) -> dict[str, float]:
    """Normalize entropy scores to [0, 1] range.

    Divides by theoretical maximum entropy (log₂(max_contexts)).

    Args:
        entropy_scores: Dictionary of pattern -> entropy score
        max_contexts: Maximum number of contexts (default: 10)

    Returns:
        Dictionary of pattern -> normalized entropy score

    Examples:
        >>> scores = {"pattern_a": 2.0, "pattern_b": 1.0, "pattern_c": 0.0}
        >>> # Maximum entropy for 4 contexts is log₂(4) = 2.0
        >>> normalized = normalize_entropy_scores(scores, max_contexts=4)
        >>> normalized["pattern_a"]
        1.0
        >>> normalized["pattern_b"]
        0.5
        >>> normalized["pattern_c"]
        0.0
    """
    if max_contexts <= 0:
        msg = "max_contexts must be positive"
        raise ValueError(msg)

    max_entropy = math.log2(max_contexts)

    if max_entropy == 0:
        return {pattern: 0.0 for pattern in entropy_scores}

    return {
        pattern: round(score / max_entropy, 6)
        for pattern, score in entropy_scores.items()
    }


def main():
    """CLI entry point."""
    config = AsYouConfig.from_environment()

    print("実行中: Shannon Entropy Calculator")
    print("-" * 50)

    # Load patterns
    data = load_tracker(config.tracker_file)
    patterns = data.get("patterns", {})

    if not patterns:
        print("パターンが見つかりません")
        return

    # Get Shannon entropy parameters from config
    entropy_config = config.settings.get("diversity", {}).get("shannon_entropy", {})
    context_keys = entropy_config.get("context_keys", ["sessions"])
    aggregation = entropy_config.get("aggregation", "mean")
    max_contexts = entropy_config.get("max_contexts", 10)

    print(f"コンテキストキー: {context_keys}, 集約: {aggregation}")

    # Calculate entropy scores
    entropy_scores = calculate_shannon_entropy_scores(
        patterns, context_keys=context_keys, aggregation=aggregation
    )

    # Normalize scores
    normalized_scores = normalize_entropy_scores(entropy_scores, max_contexts)

    # Update patterns
    for pattern_text, score in normalized_scores.items():
        if pattern_text in patterns:
            patterns[pattern_text]["shannon_entropy_score"] = score

    # Save updated data
    save_tracker(config.tracker_file, data)
    print(
        f"✓ {len(normalized_scores)}個のパターンにShannon Entropyスコアを計算しました"
    )

    # Show statistics
    high_entropy = sum(
        1 for s in normalized_scores.values() if s > HIGH_ENTROPY_THRESHOLD
    )
    medium_entropy = sum(
        1
        for s in normalized_scores.values()
        if LOW_ENTROPY_THRESHOLD <= s <= HIGH_ENTROPY_THRESHOLD
    )
    low_entropy = sum(
        1 for s in normalized_scores.values() if s < LOW_ENTROPY_THRESHOLD
    )

    print("\n統計:")
    print(f"  高エントロピー (>{HIGH_ENTROPY_THRESHOLD}): {high_entropy} (汎用的)")
    print(
        f"  中エントロピー ({LOW_ENTROPY_THRESHOLD}-{HIGH_ENTROPY_THRESHOLD}): {medium_entropy} (バランス)"
    )
    print(f"  低エントロピー (<{LOW_ENTROPY_THRESHOLD}): {low_entropy} (専門的)")


if __name__ == "__main__":
    import doctest

    # Check if running doctests
    if "--test" in sys.argv or "-v" in sys.argv:
        print("Running Shannon entropy calculator doctests:")
        results = doctest.testmod(verbose=("--verbose" in sys.argv or "-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
