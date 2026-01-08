#!/usr/bin/env python3
"""
Update patterns in pattern_tracker.json.
Handles merging similar patterns and marking promotions.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

from lib.common import load_tracker, save_tracker


def merge_patterns(tracker_file: Path, keep_pattern: str, merge_pattern: str) -> dict:
    """
    Merge two similar patterns into one.

    Args:
        tracker_file: Path to pattern_tracker.json
        keep_pattern: Pattern to keep
        merge_pattern: Pattern to merge into keep_pattern

    Returns:
        Result dictionary with status

    Examples:
        >>> from pathlib import Path
        >>> import tempfile, json
        >>> data = {
        ...     "patterns": {
        ...         "python": {"count": 5, "sessions": ["2026-01-01"], "last_seen": "2026-01-01"},
        ...         "Python": {"count": 3, "sessions": ["2026-01-02"], "last_seen": "2026-01-02"}
        ...     },
        ...     "promotion_candidates": [],
        ...     "cooccurrences": []
        ... }
        >>> with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        ...     json.dump(data, f)
        ...     temp_path = Path(f.name)
        >>> result = merge_patterns(temp_path, "python", "Python")
        >>> result["status"]
        'success'
        >>> tracker = load_tracker(temp_path)
        >>> tracker["patterns"]["python"]["count"]
        8
        >>> "Python" in tracker["patterns"]
        False
        >>> temp_path.unlink()
    """
    data = load_tracker(tracker_file)
    patterns = data["patterns"]

    if keep_pattern not in patterns:
        return {"status": "error", "message": f"Pattern '{keep_pattern}' not found"}

    if merge_pattern not in patterns:
        return {"status": "error", "message": f"Pattern '{merge_pattern}' not found"}

    keep_data = patterns[keep_pattern]
    merge_data = patterns[merge_pattern]

    # Merge counts
    keep_data["count"] = keep_data.get("count", 0) + merge_data.get("count", 0)

    # Merge sessions (unique)
    keep_sessions = set(keep_data.get("sessions", []))
    merge_sessions = set(merge_data.get("sessions", []))
    keep_data["sessions"] = sorted(keep_sessions | merge_sessions)

    # Merge contexts (unique)
    keep_contexts = keep_data.get("contexts", [])
    merge_contexts = merge_data.get("contexts", [])
    keep_data["contexts"] = list(dict.fromkeys(keep_contexts + merge_contexts))

    # Keep most recent last_seen
    keep_date = keep_data.get("last_seen", "1900-01-01")
    merge_date = merge_data.get("last_seen", "1900-01-01")
    keep_data["last_seen"] = max(keep_date, merge_date)

    # Delete merged pattern
    del patterns[merge_pattern]

    # Save
    save_tracker(tracker_file, data)

    return {
        "status": "success",
        "kept": keep_pattern,
        "merged": merge_pattern,
        "new_count": keep_data["count"],
    }


def mark_promoted(
    tracker_file: Path, pattern: str, promotion_type: str, location: str
) -> dict:
    """
    Mark pattern as promoted to skill or agent.

    Args:
        tracker_file: Path to pattern_tracker.json
        pattern: Pattern name
        promotion_type: "skill" or "agent"
        location: File path where promoted

    Returns:
        Result dictionary

    Examples:
        >>> from pathlib import Path
        >>> import tempfile, json
        >>> data = {
        ...     "patterns": {
        ...         "test": {"count": 5, "promoted": False}
        ...     },
        ...     "promotion_candidates": [],
        ...     "cooccurrences": []
        ... }
        >>> with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        ...     json.dump(data, f)
        ...     temp_path = Path(f.name)
        >>> result = mark_promoted(temp_path, "test", "skill", "skills/test/")
        >>> result["status"]
        'success'
        >>> tracker = load_tracker(temp_path)
        >>> tracker["patterns"]["test"]["promoted"]
        True
        >>> tracker["patterns"]["test"]["promoted_to"]
        'skill'
        >>> temp_path.unlink()
    """
    data = load_tracker(tracker_file)
    patterns = data["patterns"]

    if pattern not in patterns:
        return {"status": "error", "message": f"Pattern '{pattern}' not found"}

    # Mark as promoted
    patterns[pattern]["promoted"] = True
    patterns[pattern]["promoted_to"] = promotion_type
    patterns[pattern]["promoted_at"] = datetime.now().strftime("%Y-%m-%d")
    patterns[pattern]["promoted_path"] = location

    # Save
    save_tracker(tracker_file, data)

    return {"status": "success", "pattern": pattern, "type": promotion_type}


def main():
    """CLI entry point."""
    import sys

    if len(sys.argv) < 2:
        print("Usage:", file=sys.stderr)
        print(
            "  pattern_updater.py merge <tracker_file> <keep> <merge>", file=sys.stderr
        )
        print(
            "  pattern_updater.py mark <tracker_file> <pattern> <type> <location>",
            file=sys.stderr,
        )
        sys.exit(1)

    command = sys.argv[1]

    if command == "merge":
        if len(sys.argv) != 5:
            print(
                "Usage: pattern_updater.py merge <tracker_file> <keep> <merge>",
                file=sys.stderr,
            )
            sys.exit(1)

        tracker_file = Path(sys.argv[2])
        keep = sys.argv[3]
        merge = sys.argv[4]

        result = merge_patterns(tracker_file, keep, merge)
        print(json.dumps(result))
        sys.exit(0 if result["status"] == "success" else 1)

    elif command == "mark":
        if len(sys.argv) != 6:
            print(
                "Usage: pattern_updater.py mark <tracker_file> <pattern> <type> <location>",
                file=sys.stderr,
            )
            sys.exit(1)

        tracker_file = Path(sys.argv[2])
        pattern = sys.argv[3]
        promotion_type = sys.argv[4]
        location = sys.argv[5]

        result = mark_promoted(tracker_file, pattern, promotion_type, location)
        print(json.dumps(result))
        sys.exit(0 if result["status"] == "success" else 1)

    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    import doctest

    # Check if running doctests
    if "--test" in sys.argv or "-v" in sys.argv:
        print("Running pattern updater doctests:")
        results = doctest.testmod(verbose=("--verbose" in sys.argv or "-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
