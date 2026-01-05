#!/usr/bin/env python3
"""
Calculate PMI (Pointwise Mutual Information) scores for word co-occurrences.
Unicode-aware implementation using Python standard library.
"""

import json
import math
import sys
from pathlib import Path
from typing import Dict

# Import pattern extraction from pattern_detector
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from pattern_detector import extract_patterns


def count_total_patterns(archive_dir: Path) -> int:
    """
    Count total pattern occurrences across all archives.

    Args:
        archive_dir: Path to session archive directory

    Returns:
        Total number of patterns found
    """
    total = 0

    for md_file in archive_dir.glob('*.md'):
        try:
            text = md_file.read_text(encoding='utf-8')
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
    # Load tracker data
    try:
        with tracker_file.open('r', encoding='utf-8') as f:
            tracker_data = json.load(f)
    except Exception as e:
        print(f"Error: Failed to read tracker file: {e}", file=sys.stderr)
        sys.exit(1)

    # Count total patterns
    total_patterns = count_total_patterns(archive_dir)
    if total_patterns == 0:
        print("Error: no patterns found in archives", file=sys.stderr)
        sys.exit(1)

    # Get patterns and co-occurrences
    patterns = tracker_data.get('patterns', {})
    cooccurrences = tracker_data.get('cooccurrences', [])

    if not cooccurrences:
        print("Warning: no co-occurrences found in tracker", file=sys.stderr)
        return

    # Calculate PMI for each co-occurrence
    for cooccur in cooccurrences:
        words = cooccur.get('words', [])
        if len(words) != 2:
            continue

        word1, word2 = words
        cooccur_count = cooccur.get('count', 0)

        # Get individual word counts
        word1_count = patterns.get(word1, {}).get('count', 0)
        word2_count = patterns.get(word2, {}).get('count', 0)

        # Skip if any count is 0
        if word1_count == 0 or word2_count == 0 or cooccur_count == 0:
            cooccur['pmi'] = 0.0
            continue

        # Calculate probabilities
        p_ab = cooccur_count / total_patterns
        p_a = word1_count / total_patterns
        p_b = word2_count / total_patterns

        # Calculate PMI
        # Avoid log(0) by checking probabilities
        if p_ab > 0 and p_a > 0 and p_b > 0:
            pmi = math.log(p_ab / (p_a * p_b))
            cooccur['pmi'] = round(pmi, 6)
        else:
            cooccur['pmi'] = 0.0

    # Write back to tracker file
    try:
        with tracker_file.open('w', encoding='utf-8') as f:
            json.dump(tracker_data, f, ensure_ascii=False, indent=2)
        print("PMI scores calculated for all co-occurrences")
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

    # Calculate PMI
    calculate_pmi(tracker_file, archive_dir)


if __name__ == '__main__':
    main()
