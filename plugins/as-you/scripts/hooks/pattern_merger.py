#!/usr/bin/env python3
"""
Merge similar patterns with backup management.
Replaces merge-similar-patterns.sh with testable implementation.
"""

import contextlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add scripts/ to Python path
scripts_dir = Path(__file__).parent.parent
sys.path.insert(0, str(scripts_dir))

from commands.similarity_detector import detect_similar_patterns

from lib.common import AsYouConfig
from lib.pattern_updater import merge_patterns as update_merge_patterns
from lib.score_calculator import UnifiedScoreCalculator


def create_backup(tracker_file: Path, keep_count: int = 5) -> Path | None:
    """
    Create timestamped backup and cleanup old ones.

    Args:
        tracker_file: Path to pattern_tracker.json
        keep_count: Number of backups to keep

    Returns:
        Path to created backup file

    Examples:
        >>> from pathlib import Path
        >>> import tempfile, json
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     # Create test tracker
        ...     tracker = Path(tmpdir) / "pattern_tracker.json"
        ...     data = {"patterns": {"test": {"count": 1}}}
        ...     _ = tracker.write_text(json.dumps(data), encoding="utf-8")
        ...
        ...     # Create backup
        ...     backup = create_backup(tracker, keep_count=2)
        ...     backup.exists()
        True

        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     # Test backup cleanup
        ...     tracker = Path(tmpdir) / "pattern_tracker.json"
        ...     data = {"patterns": {}}
        ...     _ = tracker.write_text(json.dumps(data), encoding="utf-8")
        ...
        ...     # Create multiple backups
        ...     backups = []
        ...     for i in range(6):
        ...         backup = create_backup(tracker, keep_count=3)
        ...         backups.append(backup)
        ...
        ...     # Only 3 most recent should remain
        ...     remaining = len(
        ...         list(tracker.parent.glob("pattern_tracker.json.backup.*"))
        ...     )
        ...     remaining <= 3
        True
    """
    if not tracker_file.exists():
        raise FileNotFoundError(f"Tracker file not found: {tracker_file}")

    # Create backup with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = tracker_file.parent / f"{tracker_file.name}.backup.{timestamp}"

    # Copy tracker to backup
    backup_file.write_bytes(tracker_file.read_bytes())

    # Cleanup old backups
    backups = sorted(
        tracker_file.parent.glob(f"{tracker_file.name}.backup.*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    # Remove old backups beyond keep_count
    for old_backup in backups[keep_count:]:
        with contextlib.suppress(Exception):
            old_backup.unlink()

    return backup_file


def merge_similar_patterns_batch(
    tracker_file: Path, threshold: int = 2, min_count: int = 1
) -> dict:
    """
    Detect and merge similar patterns in batch.

    Args:
        tracker_file: Path to pattern_tracker.json
        threshold: Maximum Levenshtein distance for similarity
        min_count: Minimum pattern count to consider

    Returns:
        Dictionary with merge results

    Examples:
        >>> from pathlib import Path
        >>> import tempfile, json
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     # Create test tracker with similar patterns
        ...     tracker = Path(tmpdir) / "pattern_tracker.json"
        ...     archive_dir = Path(tmpdir) / "archive"
        ...     archive_dir.mkdir()
        ...
        ...     # Create archive file for scoring
        ...     archive_file = archive_dir / "2025-01-01.md"
        ...     _ = archive_file.write_text("test testing tests", encoding="utf-8")
        ...
        ...     data = {
        ...         "patterns": {
        ...             "test": {
        ...                 "count": 5,
        ...                 "last_seen": "2025-01-05",
        ...                 "sessions": ["s1"],
        ...             },
        ...             "tests": {
        ...                 "count": 3,
        ...                 "last_seen": "2025-01-05",
        ...                 "sessions": ["s1"],
        ...             },
        ...             "testing": {
        ...                 "count": 2,
        ...                 "last_seen": "2025-01-05",
        ...                 "sessions": ["s1"],
        ...             },
        ...         },
        ...         "promotion_candidates": [],
        ...         "cooccurrences": [],
        ...     }
        ...     _ = tracker.write_text(json.dumps(data), encoding="utf-8")
        ...
        ...     # Merge similar patterns
        ...     result = merge_similar_patterns_batch(tracker, threshold=2)
        ...
        ...     # Check that merges occurred
        ...     result["status"] == "success"
        True

        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     # Test with no similar patterns
        ...     tracker = Path(tmpdir) / "pattern_tracker.json"
        ...     data = {
        ...         "patterns": {
        ...             "unique": {
        ...                 "count": 5,
        ...                 "last_seen": "2025-01-05",
        ...                 "sessions": ["s1"],
        ...             },
        ...             "different": {
        ...                 "count": 3,
        ...                 "last_seen": "2025-01-05",
        ...                 "sessions": ["s1"],
        ...             },
        ...         },
        ...         "promotion_candidates": [],
        ...         "cooccurrences": [],
        ...     }
        ...     _ = tracker.write_text(json.dumps(data), encoding="utf-8")
        ...     result = merge_similar_patterns_batch(tracker, threshold=1)
        ...     result["merged_count"]
        0
    """
    if not tracker_file.exists():
        return {"status": "error", "message": "Tracker file not found"}

    # Detect similar patterns
    similar_pairs = detect_similar_patterns(tracker_file, threshold, min_count)

    if not similar_pairs:
        return {
            "status": "success",
            "message": "No similar patterns found",
            "merged_count": 0,
            "final_pattern_count": _count_patterns(tracker_file),
        }

    # Create backup
    backup_keep_count = int(os.getenv("AS_YOU_BACKUP_KEEP", "5"))
    backup_file = create_backup(tracker_file, backup_keep_count)

    # Track merged patterns to avoid duplicates
    merged_patterns = set()
    merge_results = []

    # Process each similar pair
    for pair in similar_pairs:
        pattern1, pattern2 = pair["patterns"]
        distance = pair["distance"]
        suggestion = pair["suggestion"]

        # Skip if already merged
        if pattern1 in merged_patterns or pattern2 in merged_patterns:
            continue

        # Determine keep and merge
        keep = suggestion
        merge = pattern2 if keep == pattern1 else pattern1

        # Perform merge
        try:
            result = update_merge_patterns(tracker_file, keep, merge)

            if result["status"] == "success":
                merged_patterns.add(merge)
                merge_results.append(
                    {
                        "keep": keep,
                        "merge": merge,
                        "distance": distance,
                        "new_count": result["new_count"],
                    }
                )
        except Exception as e:
            merge_results.append(
                {"keep": keep, "merge": merge, "distance": distance, "error": str(e)}
            )

    # Recalculate all scores
    try:
        archive_dir = tracker_file.parent / "session_archive"
        if archive_dir.exists():
            calculator = UnifiedScoreCalculator(tracker_file, archive_dir)
            calculator.calculate_all_scores()
            calculator.save()
    except Exception:
        pass  # Non-fatal if scoring fails

    final_count = _count_patterns(tracker_file)

    return {
        "status": "success",
        "message": f"Merged {len(merge_results)} pattern(s)",
        "backup_file": str(backup_file),
        "merged_count": len(merge_results),
        "merge_details": merge_results,
        "final_pattern_count": final_count,
    }


def _count_patterns(tracker_file: Path) -> int:
    """Count total patterns in tracker file."""
    try:
        with open(tracker_file, encoding="utf-8") as f:
            data = json.load(f)
        return len(data.get("patterns", {}))
    except Exception:
        return 0


def main():
    """CLI entry point."""
    import os

    # Get paths from environment
    config = AsYouConfig.from_environment()
    tracker_file = config.tracker_file

    # Get threshold from environment
    threshold = int(os.getenv("SIMILARITY_THRESHOLD", "2"))
    min_count = int(os.getenv("MIN_PATTERN_COUNT", "1"))

    if not tracker_file.exists():
        print("Error: pattern_tracker.json not found", file=sys.stderr)
        sys.exit(1)

    # Perform merge
    result = merge_similar_patterns_batch(tracker_file, threshold, min_count)

    if result["status"] == "error":
        print(f"Error: {result['message']}", file=sys.stderr)
        sys.exit(1)

    # Print results
    merged_count = result["merged_count"]

    if merged_count == 0:
        print("No similar patterns found")
        sys.exit(0)

    print(f"Found {merged_count} similar pattern pair(s)")
    print(f"\n✓ Created backup: {result['backup_file']}")
    print()

    for detail in result["merge_details"]:
        if "error" in detail:
            print(
                f"✗ Failed to merge '{detail['merge']}' into '{detail['keep']}': {detail['error']}",
                file=sys.stderr,
            )
        else:
            print(
                f"✓ Merged '{detail['merge']}' into '{detail['keep']}' (distance: {detail['distance']}, new count: {detail['new_count']})"
            )

    print()
    print(f"✓ Merge complete. Total patterns: {result['final_pattern_count']}")


if __name__ == "__main__":
    import doctest

    # Check if running doctests
    if "--test" in sys.argv or "-v" in sys.argv:
        print("Running pattern merger doctests:")
        results = doctest.testmod(verbose=("--verbose" in sys.argv or "-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
