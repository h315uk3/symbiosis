#!/usr/bin/env python3
"""
Fast similarity detection using BK-Tree.
Replaces O(n²) brute force with O(n log n) tree-based search.
"""

import json
import sys
from pathlib import Path

from as_you.lib.bktree import build_bktree_from_patterns
from as_you.lib.common import AsYouConfig, load_tracker
from as_you.lib.levenshtein import levenshtein_distance


def detect_similar_patterns(
    tracker_file: Path, threshold: int = 2, min_count: int = 1
) -> list[dict]:
    """
    Detect similar patterns using BK-Tree for efficiency.

    Args:
        tracker_file: Path to pattern_tracker.json
        threshold: Maximum Levenshtein distance for similarity
        min_count: Minimum pattern count to consider

    Returns:
        List of similar pattern pairs with metadata

    Complexity:
        - Brute force: O(n²) comparisons
        - BK-Tree: O(n log n) average case
        - Space: O(n)

    Examples:
        >>> from pathlib import Path
        >>> import tempfile, json
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     # Create tracker with similar patterns
        ...     tracker_file = Path(tmpdir) / "pattern_tracker.json"
        ...     data = {
        ...         "patterns": {
        ...             "test": {"count": 5, "composite_score": 0.8},
        ...             "tests": {"count": 3, "composite_score": 0.6},
        ...             "testing": {"count": 2, "composite_score": 0.5},
        ...         }
        ...     }
        ...     _ = tracker_file.write_text(json.dumps(data), encoding="utf-8")
        ...
        ...     # Detect similar patterns
        ...     pairs = detect_similar_patterns(tracker_file, threshold=2)
        ...
        ...     # Should find test/tests as similar
        ...     len(pairs) > 0
        True

        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     # Test with min_count filter
        ...     tracker_file = Path(tmpdir) / "pattern_tracker.json"
        ...     data = {
        ...         "patterns": {
        ...             "rare": {"count": 1, "composite_score": 0.5},
        ...             "rarer": {"count": 1, "composite_score": 0.4},
        ...         }
        ...     }
        ...     _ = tracker_file.write_text(json.dumps(data), encoding="utf-8")
        ...     pairs = detect_similar_patterns(tracker_file, threshold=2, min_count=2)
        ...     len(pairs)
        0

        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     # Test with non-existent file
        ...     tracker_file = Path(tmpdir) / "nonexistent.json"
        ...     pairs = detect_similar_patterns(tracker_file)
        ...     len(pairs)
        0
    """
    # Load patterns
    try:
        data = load_tracker(tracker_file)
        patterns = data.get("patterns", {})
    except (OSError, json.JSONDecodeError):
        # Corrupted or inaccessible file - return empty
        return []

    if not patterns:
        return []

    # Filter by minimum count
    if min_count > 1:
        patterns = {
            word: meta
            for word, meta in patterns.items()
            if meta.get("count", 0) >= min_count
        }

    if len(patterns) < 2:
        return []

    # Build BK-Tree
    tree = build_bktree_from_patterns(patterns, levenshtein_distance)

    # Find all similar pairs
    similar_pairs = []

    for word in patterns:
        # Search for similar words within threshold
        matches = tree.search(word, threshold)

        for match_word, distance in matches:
            if distance == 0:
                # Skip self-match
                continue

            # Ensure consistent ordering (alphabetical)
            if word < match_word:
                p1, p2 = word, match_word
            else:
                p1, p2 = match_word, word
                continue  # Already processed in reverse order

            # Get pattern metadata
            meta1 = patterns[p1]
            meta2 = patterns[p2]

            count1 = meta1.get("count", 0)
            count2 = meta2.get("count", 0)
            score1 = meta1.get("composite_score", 0)
            score2 = meta2.get("composite_score", 0)

            # Determine suggestion (prefer higher count)
            if count1 > count2:
                suggestion = p1
            elif count2 > count1:
                suggestion = p2
            else:
                # Equal counts, prefer alphabetically first
                suggestion = p1

            similar_pairs.append(
                {
                    "patterns": [p1, p2],
                    "distance": distance,
                    "counts": [count1, count2],
                    "scores": [score1, score2],
                    "total_count": count1 + count2,
                    "suggestion": suggestion,
                }
            )

    # Sort by total count (descending)
    similar_pairs.sort(key=lambda x: x["total_count"], reverse=True)

    return similar_pairs


def main():
    """CLI entry point."""
    import os

    # Get paths from environment
    config = AsYouConfig.from_environment()
    tracker_file = config.tracker_file

    # Get threshold from environment or default
    threshold = int(os.getenv("SIMILARITY_THRESHOLD", "2"))

    # Detect similar patterns
    similar_pairs = detect_similar_patterns(tracker_file, threshold)

    # Output as JSON
    print(json.dumps(similar_pairs, ensure_ascii=False, indent=0))


if __name__ == "__main__":
    import doctest
    import sys

    # Check if running doctests
    if "--test" in sys.argv or "-v" in sys.argv:
        print("Running similarity detector doctests:")
        results = doctest.testmod(verbose=("--verbose" in sys.argv or "-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
