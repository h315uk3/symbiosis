#!/usr/bin/env python3
"""
Calculate PMI (Pointwise Mutual Information) scores for word co-occurrences.
Unicode-aware implementation using Python standard library.
"""

import math
import sys
from pathlib import Path

from as_you.lib.common import AsYouConfig, load_tracker, save_tracker
from as_you.lib.cooccurrence_detector import detect_cooccurrences
from as_you.lib.pattern_detector import extract_patterns

# Constants
WORD_PAIR_SIZE = 2  # Co-occurrence is between exactly 2 words


def count_total_patterns(archive_dir: Path) -> int:
    """
    Count total pattern occurrences across all archives.

    Args:
        archive_dir: Path to session archive directory

    Returns:
        Total number of patterns found

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> import os
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     archive_dir = Path(tmpdir)
        ...     # Create sample archive file
        ...     test_file = archive_dir / "2025-01-01.md"
        ...     _ = test_file.write_text(
        ...         "test deployment authentication system", encoding="utf-8"
        ...     )
        ...     count = count_total_patterns(archive_dir)
        ...     count >= 4  # At least 4 patterns
        True

        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     empty_dir = Path(tmpdir)
        ...     count_total_patterns(empty_dir)
        0
    """
    total = 0

    for md_file in archive_dir.glob("*.md"):
        try:
            text = md_file.read_text(encoding="utf-8")
            patterns = extract_patterns(text)
            total += len(patterns)
        except Exception as e:
            print(f"Warning: Failed to read {md_file}: {e}", file=sys.stderr)
            continue

    return total


def calculate_pmi(tracker_file: Path, archive_dir: Path) -> None:
    """
    Calculate PMI scores for all co-occurrences in tracker file.

    PMI formula:
    PMI(A,B) = log(P(A,B) / (P(A) * P(B)))
             = log((cooccur_count / total) / ((word1_count / total) * (word2_count / total)))
             = log(cooccur_count * total / (word1_count * word2_count))

    Args:
        tracker_file: Path to pattern_tracker.json
        archive_dir: Path to session archive directory

    Examples:
        >>> import tempfile
        >>> import json
        >>> from pathlib import Path
        >>> # Setup test environment
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     base = Path(tmpdir)
        ...     tracker_file = base / "tracker.json"
        ...     archive_dir = base / "archive"
        ...     archive_dir.mkdir()
        ...
        ...     # Create archive with patterns
        ...     _ = (archive_dir / "session1.md").write_text(
        ...         "test deployment authentication system\\n" * 10, encoding="utf-8"
        ...     )
        ...     _ = (archive_dir / "session2.md").write_text(
        ...         "test deployment security network\\n" * 8, encoding="utf-8"
        ...     )
        ...
        ...     # Create tracker with co-occurrences
        ...     tracker_data = {
        ...         "patterns": {
        ...             "test": {"count": 18},
        ...             "deployment": {"count": 18},
        ...             "authentication": {"count": 10},
        ...             "system": {"count": 10},
        ...         },
        ...         "cooccurrences": [
        ...             {"words": ["test", "deployment"], "count": 18},
        ...             {"words": ["deployment", "authentication"], "count": 10},
        ...         ],
        ...     }
        ...     _ = tracker_file.write_text(json.dumps(tracker_data), encoding="utf-8")
        ...
        ...     # Calculate PMI
        ...     calculate_pmi(tracker_file, archive_dir)
        ...
        ...     # Verify PMI scores were added
        ...     result = json.loads(tracker_file.read_text(encoding="utf-8"))
        ...     cooccurs = result["cooccurrences"]
        ...     all(co.get("pmi") is not None for co in cooccurs)
        PMI scores calculated for all co-occurrences
        True

        >>> # Test with zero counts (edge case)
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     base = Path(tmpdir)
        ...     tracker_file = base / "tracker.json"
        ...     archive_dir = base / "archive"
        ...     archive_dir.mkdir()
        ...     _ = (archive_dir / "session.md").write_text("test", encoding="utf-8")
        ...
        ...     # Co-occurrence with zero word count
        ...     tracker_data = {
        ...         "patterns": {"test": {"count": 1}, "unknown": {"count": 0}},
        ...         "cooccurrences": [{"words": ["test", "unknown"], "count": 1}],
        ...     }
        ...     _ = tracker_file.write_text(json.dumps(tracker_data), encoding="utf-8")
        ...
        ...     calculate_pmi(tracker_file, archive_dir)
        ...
        ...     # Verify zero count handled gracefully
        ...     result = json.loads(tracker_file.read_text(encoding="utf-8"))
        ...     result["cooccurrences"][0]["pmi"]
        PMI scores calculated for all co-occurrences
        0.0
    """
    # Load tracker data using common utility
    tracker_data = load_tracker(tracker_file)

    # Count total patterns
    total_patterns = count_total_patterns(archive_dir)
    if total_patterns == 0:
        print("Error: no patterns found in archives", file=sys.stderr)
        sys.exit(1)

    # Get patterns and co-occurrences
    patterns = tracker_data.get("patterns", {})
    cooccurrences = tracker_data.get("cooccurrences", [])

    if not cooccurrences:
        print("Warning: no co-occurrences found in tracker", file=sys.stderr)
        return

    # Calculate PMI for each co-occurrence
    for cooccur in cooccurrences:
        words = cooccur.get("words", [])
        if len(words) != WORD_PAIR_SIZE:
            continue

        word1, word2 = words
        cooccur_count = cooccur.get("count", 0)

        # Get individual word counts
        word1_count = patterns.get(word1, {}).get("count", 0)
        word2_count = patterns.get(word2, {}).get("count", 0)

        # Skip if any count is 0
        if word1_count == 0 or word2_count == 0 or cooccur_count == 0:
            cooccur["pmi"] = 0.0
            continue

        # Calculate probabilities
        p_ab = cooccur_count / total_patterns
        p_a = word1_count / total_patterns
        p_b = word2_count / total_patterns

        # Calculate PMI
        # Avoid log(0) by checking probabilities
        if p_ab > 0 and p_a > 0 and p_b > 0:
            pmi = math.log(p_ab / (p_a * p_b))
            cooccur["pmi"] = round(pmi, 6)
        else:
            cooccur["pmi"] = 0.0

    # Save tracker data using common utility
    save_tracker(tracker_file, tracker_data)
    print("PMI scores calculated for all co-occurrences")


def calculate_pmi_scores(  # noqa: PLR0912
    patterns: dict[str, dict],
    archive_dir: Path,
    min_cooccurrence: int = 2,
) -> dict[str, float]:
    """Calculate PMI scores for patterns based on co-occurrence analysis.

    Strategy:
    1. Extract co-occurrences from archive files
    2. Calculate PMI for each pattern pair
    3. Aggregate pattern-level score (mean of all PMIs involving pattern)
    4. Normalize to [0, 1] range

    Args:
        patterns: Pattern data dict
        archive_dir: Session archive directory
        min_cooccurrence: Minimum co-occurrence count threshold

    Returns:
        Dict mapping pattern text to normalized PMI score

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> # Test with empty archive
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     patterns = {"test": {"count": 5}, "deploy": {"count": 3}}
        ...     scores = calculate_pmi_scores(patterns, Path(tmpdir))
        ...     isinstance(scores, dict)
        True

        >>> # Test with no patterns
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     scores = calculate_pmi_scores({}, Path(tmpdir))
        ...     scores
        {}

        >>> # Test PMI calculation with co-occurring patterns
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     archive_dir = Path(tmpdir)
        ...     # Create archive with co-occurring patterns
        ...     _ = (archive_dir / "s1.md").write_text(
        ...         "test deployment\\ntest authentication\\n" * 5, encoding="utf-8"
        ...     )
        ...     _ = (archive_dir / "s2.md").write_text(
        ...         "deployment security\\nauthentication system\\n" * 3,
        ...         encoding="utf-8",
        ...     )
        ...
        ...     patterns = {
        ...         "test": {"count": 10},
        ...         "deployment": {"count": 8},
        ...         "authentication": {"count": 8},
        ...         "security": {"count": 3},
        ...     }
        ...     scores = calculate_pmi_scores(patterns, archive_dir, min_cooccurrence=2)
        ...
        ...     # Verify all patterns have scores
        ...     len(scores) == len(patterns)
        True

        >>> # Verify scores are normalized [0, 1]
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     archive_dir = Path(tmpdir)
        ...     _ = (archive_dir / "s1.md").write_text(
        ...         "test deploy\\n" * 10, encoding="utf-8"
        ...     )
        ...     patterns = {"test": {"count": 10}, "deploy": {"count": 10}}
        ...     scores = calculate_pmi_scores(patterns, archive_dir)
        ...     all(0.0 <= score <= 1.0 for score in scores.values())
        True

        >>> # Test with no co-occurrences (patterns on separate lines)
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     archive_dir = Path(tmpdir)
        ...     _ = (archive_dir / "s1.md").write_text(
        ...         "word1\\nword2\\n", encoding="utf-8"
        ...     )
        ...     patterns = {"word1": {"count": 1}, "word2": {"count": 1}}
        ...     scores = calculate_pmi_scores(patterns, archive_dir)
        ...     # No co-occurrences detected, all scores are 0.0
        ...     all(score == 0.0 for score in scores.values())
        True

        >>> # Test normalization with co-occurring patterns
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     archive_dir = Path(tmpdir)
        ...     _ = (archive_dir / "s1.md").write_text(
        ...         "alpha beta\\n", encoding="utf-8"
        ...     )
        ...     _ = (archive_dir / "s2.md").write_text(
        ...         "alpha beta\\n", encoding="utf-8"
        ...     )
        ...     patterns = {"alpha": {"count": 2}, "beta": {"count": 2}}
        ...     scores = calculate_pmi_scores(patterns, archive_dir, min_cooccurrence=2)
        ...     # Both patterns co-occur equally, normalized to 0.5
        ...     all(score == 0.5 for score in scores.values())
        True
    """
    # Handle empty patterns
    if not patterns:
        return {}

    # Count total patterns in archive
    total_patterns = count_total_patterns(archive_dir)
    if total_patterns == 0:
        # No data in archive, return zero scores
        return {pattern: 0.0 for pattern in patterns}

    # Detect co-occurrences from archive (get top 1000)
    cooccurrences = detect_cooccurrences(archive_dir, top_n=1000)
    if not cooccurrences:
        # No co-occurrences found, return zero scores
        return {pattern: 0.0 for pattern in patterns}

    # Calculate PMI for each pattern
    pmi_scores = {}
    for pattern_text, pattern_data in patterns.items():
        pattern_count = pattern_data.get("count", 0)
        if pattern_count == 0:
            pmi_scores[pattern_text] = 0.0
            continue

        # Find all co-occurrences involving this pattern
        related_pmis = []
        for cooccur in cooccurrences:
            words = cooccur["words"]
            if pattern_text not in words:
                continue

            cooccur_count = cooccur["count"]
            if cooccur_count < min_cooccurrence:
                continue

            # Get both word counts
            word1, word2 = words
            word1_count = patterns.get(word1, {}).get("count", 0)
            word2_count = patterns.get(word2, {}).get("count", 0)

            # Calculate PMI if both words have counts
            if word1_count > 0 and word2_count > 0:
                p_ab = cooccur_count / total_patterns
                p_a = word1_count / total_patterns
                p_b = word2_count / total_patterns

                # PMI formula: log(P(A,B) / (P(A) * P(B)))
                if p_ab > 0 and p_a > 0 and p_b > 0:
                    pmi = math.log(p_ab / (p_a * p_b))
                    related_pmis.append(pmi)

        # Aggregate PMI scores for this pattern (mean)
        if related_pmis:
            pmi_scores[pattern_text] = sum(related_pmis) / len(related_pmis)
        else:
            pmi_scores[pattern_text] = 0.0

    # Normalize scores to [0, 1] range
    if pmi_scores:
        min_pmi = min(pmi_scores.values())
        max_pmi = max(pmi_scores.values())

        if max_pmi > min_pmi:
            # Min-max normalization
            for pattern in list(pmi_scores.keys()):
                normalized = (pmi_scores[pattern] - min_pmi) / (max_pmi - min_pmi)
                pmi_scores[pattern] = round(normalized, 6)
        else:
            # All scores are the same, set to 0.5
            for pattern in pmi_scores:
                pmi_scores[pattern] = 0.5

    return pmi_scores


def main():
    """Main entry point for CLI usage."""
    config = AsYouConfig.from_environment()
    tracker_file = config.tracker_file
    archive_dir = config.archive_dir

    # Validate paths
    if not tracker_file.exists():
        print("Error: pattern_tracker.json not found", file=sys.stderr)
        sys.exit(1)

    if not archive_dir.exists() or not archive_dir.is_dir():
        print("Error: archive directory not found", file=sys.stderr)
        sys.exit(1)

    # Calculate PMI
    calculate_pmi(tracker_file, archive_dir)


if __name__ == "__main__":
    import doctest
    import sys

    # Check if running doctests
    if "--test" in sys.argv or "-v" in sys.argv:
        print("Running PMI calculator doctests:")
        results = doctest.testmod(verbose=("--verbose" in sys.argv or "-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
