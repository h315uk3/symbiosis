#!/usr/bin/env python3
"""
Calculate TF-IDF scores for patterns in pattern_tracker.json.
Unicode-aware implementation using Python standard library.
"""

import json
import math
import re
import sys
from pathlib import Path
from typing import Dict, Set


# English stopwords (common words to exclude from high scores)
ENGLISH_STOPWORDS = {
    'and', 'the', 'for', 'with', 'that', 'this', 'from', 'have', 'has', 'had',
    'but', 'not', 'are', 'was', 'were', 'been', 'being', 'you', 'your', 'they',
    'their', 'what', 'which', 'who', 'when', 'where', 'why', 'how', 'can',
    'could', 'would', 'should', 'will', 'shall', 'may', 'might', 'must'
}

# Common Japanese particles and auxiliaries
JAPANESE_STOPWORDS = {
    'です', 'ます', 'した', 'する', 'される', 'いる', 'ある', 'なる', 'くる',
    'できる', 'という', 'ため', 'こと', 'もの', 'ところ', 'とき', 'など'
}


def is_stopword(word: str) -> bool:
    """Check if word is a stopword (English or Japanese)."""
    word_lower = word.lower()
    return word_lower in ENGLISH_STOPWORDS or word in JAPANESE_STOPWORDS


def count_documents_containing_pattern(pattern: str, archive_dir: Path) -> int:
    """
    Count number of documents containing the pattern (case-insensitive).

    Args:
        pattern: Pattern to search for
        archive_dir: Directory containing markdown archive files

    Returns:
        Number of documents containing the pattern
    """
    count = 0
    # Use case-insensitive regex for matching
    pattern_re = re.compile(re.escape(pattern), re.IGNORECASE | re.UNICODE)

    for md_file in archive_dir.glob('*.md'):
        try:
            text = md_file.read_text(encoding='utf-8')
            if pattern_re.search(text):
                count += 1
        except Exception as e:
            print(f"Warning: Failed to read {md_file}: {e}", file=sys.stderr)
            continue

    return count


def calculate_tfidf(tracker_file: Path, archive_dir: Path) -> None:
    """
    Calculate TF-IDF scores for all patterns in tracker file.

    Args:
        tracker_file: Path to pattern_tracker.json
        archive_dir: Path to session archive directory
    """
    # Load tracker data
    try:
        with tracker_file.open('r', encoding='utf-8') as f:
            tracker_data = json.load(f)
    except Exception as e:
        print(f"Error: Failed to read tracker file: {e}", file=sys.stderr)
        sys.exit(1)

    # Count total documents
    total_docs = len(list(archive_dir.glob('*.md')))
    if total_docs == 0:
        print("Error: no archive files found", file=sys.stderr)
        sys.exit(1)

    # Get patterns
    patterns = tracker_data.get('patterns', {})
    if not patterns:
        print("Warning: no patterns found in tracker", file=sys.stderr)
        return

    # Calculate TF-IDF for each pattern
    for word, word_data in patterns.items():
        # TF: term frequency (count)
        tf = word_data.get('count', 0)

        # DF: document frequency (number of docs containing this pattern)
        doc_freq = count_documents_containing_pattern(word, archive_dir)

        # IDF: inverse document frequency
        # Add 1 to doc_freq to avoid division by zero
        idf = math.log(total_docs / (doc_freq + 1))

        # TF-IDF score
        tfidf = tf * idf

        # Update pattern data
        word_data['tfidf'] = round(tfidf, 6)
        word_data['idf'] = round(idf, 6)
        word_data['is_stopword'] = is_stopword(word)

    # Write back to tracker file
    try:
        with tracker_file.open('w', encoding='utf-8') as f:
            json.dump(tracker_data, f, ensure_ascii=False, indent=2)
        print("TF-IDF scores calculated for all patterns")
    except Exception as e:
        print(f"Error: Failed to write tracker file: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point for CLI usage."""
    import os

    # Get paths from environment or defaults
    project_root = os.getenv('PROJECT_ROOT', os.getcwd())
    claude_dir = os.getenv('CLAUDE_DIR', os.path.join(project_root, '.claude'))
    tracker_file = Path(claude_dir) / 'as_you' / 'pattern_tracker.json'
    archive_dir = Path(claude_dir) / 'as_you' / 'session_archive'

    # Validate paths
    if not tracker_file.exists():
        print("Error: pattern_tracker.json not found", file=sys.stderr)
        sys.exit(1)

    if not archive_dir.exists() or not archive_dir.is_dir():
        print("Error: archive directory not found", file=sys.stderr)
        sys.exit(1)

    # Calculate TF-IDF
    calculate_tfidf(tracker_file, archive_dir)


if __name__ == '__main__':
    main()
