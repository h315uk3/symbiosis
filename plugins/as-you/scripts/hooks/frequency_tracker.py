#!/usr/bin/env python3
"""
Track pattern frequency and update pattern_tracker.json.
Replaces track-frequency.sh with testable Python implementation.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add scripts/ to Python path
scripts_dir = Path(__file__).parent.parent
sys.path.insert(0, str(scripts_dir))

from lib.common import AsYouConfig, load_tracker, save_tracker
from lib.pattern_detector import detect_patterns_from_archives
from lib.context_extractor import extract_contexts as extract_contexts_func
from lib.cooccurrence_detector import detect_cooccurrences
from lib.score_calculator import UnifiedScoreCalculator


def update_pattern(patterns: Dict, word: str, count: int, current_date: str) -> None:
    """
    Update or create pattern entry.

    Args:
        patterns: Patterns dictionary (modified in place)
        word: Pattern word
        count: Occurrence count in this session
        current_date: Current date (YYYY-MM-DD)

    Examples:
        >>> patterns = {}
        >>> update_pattern(patterns, "python", 5, "2026-01-06")
        >>> patterns["python"]["count"]
        5
        >>> patterns["python"]["last_seen"]
        '2026-01-06'
        >>> update_pattern(patterns, "python", 3, "2026-01-07")
        >>> patterns["python"]["count"]
        8
        >>> len(patterns["python"]["sessions"])
        2
    """
    if word in patterns:
        # Update existing pattern
        patterns[word]["count"] = patterns[word].get("count", 0) + count
        patterns[word]["last_seen"] = current_date

        # Add current date to sessions if not already present
        sessions = patterns[word].get("sessions", [])
        if current_date not in sessions:
            sessions.append(current_date)
            patterns[word]["sessions"] = sessions
    else:
        # Create new pattern
        patterns[word] = {
            "count": count,
            "last_seen": current_date,
            "sessions": [current_date],
            "promoted": False,
        }


def merge_contexts(patterns: Dict, contexts_data: Dict) -> None:
    """
    Merge context data into patterns.

    Args:
        patterns: Patterns dictionary (modified in place)
        contexts_data: Context data from extract_contexts

    Examples:
        >>> patterns = {"python": {"count": 5}}
        >>> contexts = {"patterns": {"python": {"contexts": ["test context"]}}}
        >>> merge_contexts(patterns, contexts)
        >>> patterns["python"]["contexts"]
        ['test context']
    """
    contexts_patterns = contexts_data.get("patterns", {})

    for word, context_info in contexts_patterns.items():
        if word in patterns:
            patterns[word]["contexts"] = context_info.get("contexts", [])


def update_frequency(
    tracker_file: Path,
    patterns_data: List[Dict],
    contexts_data: Dict = None,
    cooccurrences: List[Dict] = None,
) -> Dict:
    """
    Update pattern tracker with new frequency data.

    Args:
        tracker_file: Path to pattern_tracker.json
        patterns_data: List of {"word": str, "count": int} dicts
        contexts_data: Optional context data
        cooccurrences: Optional co-occurrence data

    Returns:
        Updated tracker data with statistics

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        ...     _ = f.write('{"patterns": {}, "promotion_candidates": [], "cooccurrences": []}')
        ...     temp_path = Path(f.name)
        >>> patterns = [{"word": "test", "count": 3}, {"word": "python", "count": 5}]
        >>> result = update_frequency(temp_path, patterns)
        >>> result["pattern_count"]
        2
        >>> temp_path.unlink()
    """
    # Load existing tracker
    tracker = load_tracker(tracker_file)
    patterns = tracker["patterns"]

    # Get current date
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Update patterns
    for pattern_obj in patterns_data:
        word = pattern_obj.get("word")
        count = pattern_obj.get("count", 0)

        if not word:
            continue

        update_pattern(patterns, word, count, current_date)

    # Merge contexts if provided
    if contexts_data:
        merge_contexts(patterns, contexts_data)

    # Update co-occurrences if provided
    if cooccurrences is not None:
        tracker["cooccurrences"] = cooccurrences

    # Save tracker using common utility
    save_tracker(tracker_file, tracker)

    # Return statistics
    return {
        "pattern_count": len(patterns),
        "candidate_count": len(tracker.get("promotion_candidates", [])),
    }


def main():
    """CLI entry point."""
    # Get paths from environment using common config
    config = AsYouConfig.from_environment()

    # Ensure archive directory exists
    config.archive_dir.mkdir(parents=True, exist_ok=True)

    # Direct function calls (no subprocess overhead)
    try:
        # 1. Detect patterns from archives (was: subprocess call to pattern_detector.py)
        patterns_data = detect_patterns_from_archives(config.archive_dir)

        # 2. Extract contexts (was: subprocess call to extract-contexts.sh)
        contexts_data = extract_contexts_func(
            config.tracker_file,
            config.archive_dir,
            top_n=10,
            max_contexts=5
        )

        # 3. Detect co-occurrences (was: subprocess call to detect-cooccurrence.sh)
        cooccurrences = detect_cooccurrences(config.archive_dir)

    except Exception as e:
        print(f"Error during pattern processing: {e}", file=sys.stderr)
        sys.exit(1)

    # 4. Update frequency tracker
    stats = update_frequency(
        config.tracker_file,
        patterns_data,
        contexts_data,
        cooccurrences
    )

    # 5. Calculate scores using direct call (was: subprocess call to score_calculator.py)
    try:
        calculator = UnifiedScoreCalculator(
            config.tracker_file,
            config.archive_dir
        )
        calculator.calculate_all_scores()
        calculator.save()
    except Exception as e:
        print(f"Error calculating scores: {e}", file=sys.stderr)
        sys.exit(1)

    # Print statistics
    print(
        f"Frequency tracker updated: {stats['pattern_count']} patterns tracked, "
        f"{stats['candidate_count']} promotion candidates (scored)"
    )


if __name__ == "__main__":
    import doctest

    # Check if running doctests
    if "--test" in sys.argv or "-v" in sys.argv:
        print("Running frequency tracker doctests:")
        results = doctest.testmod(verbose=("--verbose" in sys.argv or "-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
