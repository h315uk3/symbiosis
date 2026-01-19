#!/usr/bin/env python3
"""
Calculate TF-IDF scores for patterns in pattern_tracker.json.
Unicode-aware implementation using Python standard library.
"""

import math
import re
import sys
from collections import defaultdict
from pathlib import Path

from as_you.lib.common import AsYouConfig, load_tracker, save_tracker

# English stopwords (common words to exclude from high scores)
# Notes are now translated to English before storage, so only English stopwords needed
STOPWORDS = {
    "and",
    "the",
    "for",
    "with",
    "that",
    "this",
    "from",
    "have",
    "has",
    "had",
    "but",
    "not",
    "are",
    "was",
    "were",
    "been",
    "being",
    "you",
    "your",
    "they",
    "their",
    "what",
    "which",
    "who",
    "when",
    "where",
    "why",
    "how",
    "can",
    "could",
    "would",
    "should",
    "will",
    "shall",
    "may",
    "might",
    "must",
}


def is_stopword(word: str) -> bool:
    """
    Check if word is an English stopword.

    All notes are translated to English before storage (commands/note.md),
    so pattern analysis only needs to handle English stopwords.

    Examples:
        >>> is_stopword("the")
        True
        >>> is_stopword("THE")
        True
        >>> is_stopword("python")
        False
        >>> is_stopword("debugging")
        False
        >>> is_stopword("implementation")
        False
    """
    return word.lower() in STOPWORDS


def calculate_tfidf_single_pass(
    patterns: dict[str, dict], archive_dir: Path
) -> dict[str, tuple[float, float]]:
    """
    Calculate TF-IDF scores in single pass (O(m) instead of O(n×m)).

    This optimized algorithm scans each document once and counts all patterns
    simultaneously, instead of scanning all documents for each pattern.

    Args:
        patterns: Pattern dictionary from tracker
        archive_dir: Path to archive directory

    Returns:
        Dict mapping pattern -> (idf, tfidf)

    Complexity:
        Old: O(n×m) where n=patterns, m=documents
        New: O(m) - scan documents once
        Speedup: ~n (e.g., 100x for 100 patterns)

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> temp_dir = Path(tempfile.mkdtemp())
        >>> (temp_dir / "doc1.md").write_text("Python is great")
        15
        >>> (temp_dir / "doc2.md").write_text("Python and testing")
        18
        >>> patterns = {"python": {"count": 5}, "testing": {"count": 2}}
        >>> results = calculate_tfidf_single_pass(patterns, temp_dir)
        >>> "python" in results and "testing" in results
        True
        >>> import shutil
        >>> shutil.rmtree(temp_dir)
    """
    # Build regex matching all patterns simultaneously
    pattern_list = list(patterns.keys())
    if not pattern_list:
        return {}

    # Compile single regex with word boundaries for all patterns
    # Use word boundaries for more accurate matching
    try:
        pattern_regex = re.compile(
            "|".join(rf"\b{re.escape(p)}\b" for p in pattern_list),
            re.IGNORECASE | re.UNICODE,
        )
    except re.error:
        # Fallback: without word boundaries if regex is too complex
        pattern_regex = re.compile(
            "|".join(re.escape(p) for p in pattern_list),
            re.IGNORECASE | re.UNICODE,
        )

    # Single pass: count document frequency for all patterns
    doc_freq: dict[str, int] = defaultdict(int)
    total_docs = 0

    for doc_path in archive_dir.glob("*.md"):
        total_docs += 1

        try:
            text = doc_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            print(f"Warning: Failed to read {doc_path}: {e}", file=sys.stderr)
            continue

        # Find all pattern matches in this document
        found_patterns = set()
        for match in pattern_regex.finditer(text):
            pattern = match.group(0).lower()
            found_patterns.add(pattern)

        # Update document frequency
        for pattern in found_patterns:
            doc_freq[pattern] += 1

    # Calculate TF-IDF for all patterns
    if total_docs == 0:
        return {}

    results = {}
    for word, word_data in patterns.items():
        tf = word_data.get("count", 0)
        df = doc_freq.get(word.lower(), 0)
        idf = math.log(total_docs / (df + 1))
        tfidf = tf * idf

        results[word] = (idf, tfidf)

    return results


def calculate_tfidf(tracker_file: Path, archive_dir: Path) -> None:
    """
    Calculate TF-IDF scores using optimized single-pass algorithm.

    Args:
        tracker_file: Path to pattern_tracker.json
        archive_dir: Path to session archive directory
    """
    # Load tracker data using common utility
    data = load_tracker(tracker_file)
    patterns = data.get("patterns", {})

    if not patterns:
        print("Warning: no patterns found in tracker", file=sys.stderr)
        return

    # Use optimized single-pass algorithm
    tfidf_scores = calculate_tfidf_single_pass(patterns, archive_dir)

    # Update pattern data
    for word, (idf, tfidf) in tfidf_scores.items():
        patterns[word]["tfidf"] = round(tfidf, 6)
        patterns[word]["idf"] = round(idf, 6)
        patterns[word]["is_stopword"] = is_stopword(word)

    # Save tracker data using common utility
    save_tracker(tracker_file, data)
    print("TF-IDF scores calculated for all patterns")


def main():
    """Main entry point for CLI usage."""
    config = AsYouConfig.from_environment()

    # Validate paths
    if not config.tracker_file.exists():
        print("Error: pattern_tracker.json not found", file=sys.stderr)
        sys.exit(1)

    if not config.archive_dir.exists() or not config.archive_dir.is_dir():
        print("Error: archive directory not found", file=sys.stderr)
        sys.exit(1)

    # Calculate TF-IDF using optimized algorithm
    calculate_tfidf(config.tracker_file, config.archive_dir)


if __name__ == "__main__":
    import doctest
    import sys

    # Check if running doctests
    if "--test" in sys.argv or "-v" in sys.argv:
        print("Running TF-IDF calculator doctests:")
        results = doctest.testmod(verbose=("--verbose" in sys.argv or "-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
