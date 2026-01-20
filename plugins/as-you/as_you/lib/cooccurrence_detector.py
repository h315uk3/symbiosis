#!/usr/bin/env python3
"""
Detect word co-occurrences within same memo lines.
Replaces detect-cooccurrence.sh with optimized Python implementation.
Uses itertools.combinations for efficient pair generation.
"""

import os
import re
import sys
from collections import Counter
from contextlib import suppress
from itertools import combinations
from pathlib import Path


def extract_words(text: str, min_length: int = 3) -> list[str]:
    """
    Extract words from text (lowercase, min length).

    Args:
        text: Input text
        min_length: Minimum word length to extract

    Returns:
        Sorted unique list of words

    Examples:
        >>> extract_words("Testing Python code")
        ['code', 'python', 'testing']
        >>> extract_words("a bb ccc dddd")
        ['ccc', 'dddd']
        >>> extract_words("")
        []
    """
    # Extract alphabetic words (min length)
    words = re.findall(r"[a-zA-Z]{" + str(min_length) + r",}", text.lower())
    # Return unique, sorted words
    return sorted(set(words))


def generate_word_pairs(words: list[str]) -> list[tuple]:
    """
    Generate all unique word pairs from a list.

    Args:
        words: List of words

    Returns:
        List of sorted tuples (word1, word2) where word1 < word2

    Examples:
        >>> pairs = generate_word_pairs(["test", "code", "python"])
        >>> len(pairs)
        3
        >>> ("code", "test") in pairs
        True
        >>> generate_word_pairs(["single"])
        []
        >>> generate_word_pairs([])
        []
    """
    if len(words) < 2:
        return []

    # Use itertools.combinations for efficient pair generation
    # combinations already returns sorted order, but we ensure alphabetical
    return [tuple(sorted(pair)) for pair in combinations(words, 2)]


def detect_cooccurrences(archive_dir: Path, top_n: int = 20) -> list[dict]:
    """
    Detect word co-occurrences from archive files.

    Args:
        archive_dir: Path to session archive directory
        top_n: Number of top co-occurrences to return

    Returns:
        List of co-occurrence dictionaries with 'words' and 'count'

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> temp_dir = Path(tempfile.mkdtemp())
        >>> _ = (temp_dir / "test.md").write_text(
        ...     "Testing Python code\\nPython testing"
        ... )
        >>> result = detect_cooccurrences(temp_dir, top_n=5)
        >>> len(result) > 0
        True
        >>> result[0]["words"]
        ['python', 'testing']
        >>> import shutil
        >>> shutil.rmtree(temp_dir)
    """
    if not archive_dir.exists():
        return []

    # Counter for word pair frequencies
    pair_counter = Counter()

    try:
        # Process all markdown files in archive
        for md_file in archive_dir.glob("*.md"):
            if not md_file.is_file():
                continue

            with suppress(OSError, UnicodeDecodeError):
                with open(md_file, encoding="utf-8") as f:
                    for line in f:
                        # Remove timestamps [HH:MM]
                        line = re.sub(r"\[\d{2}:\d{2}\]", "", line)

                        # Extract words from line
                        words = extract_words(line)

                        # Generate word pairs
                        pairs = generate_word_pairs(words)

                        # Count pairs
                        for pair in pairs:
                            pair_counter[pair] += 1

    except Exception as e:
        print(f"Error while detecting cooccurrences in '{archive_dir}': {e}", file=sys.stderr)

    # Return top N pairs as list of dicts
    result = []
    for (word1, word2), count in pair_counter.most_common(top_n):
        result.append({"words": [word1, word2], "count": count})

    return result


def main():
    """CLI entry point."""
    import json

    # Get paths from environment or defaults
    project_root = os.getenv("PROJECT_ROOT", os.getcwd())
    claude_dir = Path(os.getenv("CLAUDE_DIR", os.path.join(project_root, ".claude")))
    archive_dir = claude_dir / "as_you" / "session_archive"

    # Detect co-occurrences
    cooccurrences = detect_cooccurrences(archive_dir, top_n=20)

    # Output JSON
    print(json.dumps(cooccurrences, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    import doctest

    # Check if running doctests
    if "--test" in sys.argv or "-v" in sys.argv:
        print("Running cooccurrence detector doctests:")
        results = doctest.testmod(verbose=("--verbose" in sys.argv or "-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
