#!/usr/bin/env python3
"""
Calculate PMI (Pointwise Mutual Information) scores for word co-occurrences.
Unicode-aware implementation using Python standard library.
"""

import math
import sys
from pathlib import Path

from lib.common import AsYouConfig, load_tracker, save_tracker
from lib.pattern_detector import extract_patterns


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
        ...     _ = test_file.write_text("test deployment authentication system", encoding="utf-8")
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
        if len(words) != 2:
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
