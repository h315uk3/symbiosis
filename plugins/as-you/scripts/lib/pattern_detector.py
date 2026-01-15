#!/usr/bin/env python3
"""
Unicode-aware pattern detection for session archives.
Extracts patterns from text using language-agnostic tokenization.
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

from lib.common import AsYouConfig


def extract_patterns(text: str) -> list[str]:
    """
    Extract patterns from English text.

    Note: All notes are translated to English before storage (see commands/note.md).
    This function extracts English words (3+ characters).

    Examples:
        >>> extract_patterns("This is a test message")
        ['this', 'test', 'message']
        >>> extract_patterns("testing and debugging")
        ['testing', 'and', 'debugging']
        >>> extract_patterns("[12:34] timestamp removed")
        ['timestamp', 'removed']
        >>> extract_patterns("short ab c")
        ['short']
    """
    # Remove timestamps [HH:MM]
    text = re.sub(r"\[\d{2}:\d{2}\]", "", text)

    # Extract space-delimited words (3+ chars, letters and numbers)
    words = re.findall(r"\b[a-zA-Z][a-zA-Z0-9]{2,}\b", text)
    return [word.lower() for word in words]


def detect_patterns_from_archives(
    archive_dir: Path, top_n: int = 20
) -> list[dict[str, any]]:
    """
    Detect frequent patterns from all markdown files in archive directory.

    Args:
        archive_dir: Path to session archive directory
        top_n: Number of top patterns to return

    Returns:
        List of dicts with 'word' and 'count' keys, sorted by frequency
    """
    if not archive_dir.exists() or not archive_dir.is_dir():
        return []

    # Collect all patterns from all markdown files
    all_patterns = []

    for md_file in archive_dir.glob("*.md"):
        try:
            text = md_file.read_text(encoding="utf-8")
            all_patterns.extend(extract_patterns(text))
        except Exception as e:
            print(f"Warning: Failed to read {md_file}: {e}", file=sys.stderr)
            continue

    if not all_patterns:
        return []

    # Count frequency
    pattern_counts = Counter(all_patterns)

    # Get top N patterns
    top_patterns = pattern_counts.most_common(top_n)

    # Format as list of dicts
    return [{"word": word, "count": count} for word, count in top_patterns]


def main():
    """Main entry point for CLI usage."""
    config = AsYouConfig.from_environment()
    archive_dir = config.archive_dir

    # Detect patterns
    patterns = detect_patterns_from_archives(archive_dir)

    # Output as JSON
    print(json.dumps(patterns, ensure_ascii=False, indent=0))


if __name__ == "__main__":
    import doctest
    import sys

    # Check if running doctests
    if "--test" in sys.argv or "-v" in sys.argv:
        print("Running pattern detector doctests:")
        results = doctest.testmod(verbose=("--verbose" in sys.argv or "-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
