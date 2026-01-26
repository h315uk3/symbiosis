#!/usr/bin/env python3
"""
Pattern review command using SM-2 spaced repetition.

Implements spaced repetition review workflow for learned patterns
using the SM-2 algorithm. Helps reinforce pattern memory through
quality feedback and adaptive review scheduling.

Usage:
    python3 -m as_you.commands.pattern_review

Functions:
    find_due_patterns: Find patterns ready for review
    apply_quality_feedback: Update SM-2 state based on recall quality
    get_review_summary: Get SM-2 review statistics

Examples:
    # Find patterns due for review
    from datetime import datetime
    from pathlib import Path
    patterns = find_due_patterns(Path('.claude/as_you/pattern_tracker.json'), datetime.now())

    # Apply quality feedback
    result = apply_quality_feedback(
        Path('.claude/as_you/pattern_tracker.json'),
        'Use pathlib for file operations',
        4
    )
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add plugin to path for imports
_PLUGIN_ROOT = Path(__file__).parent.parent.parent
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from as_you.lib.common import load_tracker, save_tracker
from as_you.lib.sm2_memory import (
    SM2State,
    calculate_next_review_date,
    is_review_due,
    update_sm2_state,
)

# Constants
MAX_QUALITY_SCORE = 5
MIN_ARGS_BASE = 2  # Program name + command
MIN_ARGS_PATTERN = 3  # Program name + command + pattern
MIN_ARGS_FEEDBACK = 4  # Program name + command + pattern + quality


def find_due_patterns(tracker_file: Path, current_date: datetime) -> list[dict]:
    """Find patterns due for review based on SM-2 schedule.

    Args:
        tracker_file: Path to pattern_tracker.json
        current_date: Current date for comparison

    Returns:
        List of due patterns sorted by days_overdue DESC, composite_score DESC:
        [
            {
                "pattern_text": str,
                "pattern_data": dict,
                "days_overdue": int,
                "next_review": str,
                "sm2_state": dict
            },
            ...
        ]

    Examples:
        >>> from datetime import datetime, timedelta
        >>> from pathlib import Path
        >>> import tempfile, json
        >>> temp_dir = Path(tempfile.mkdtemp())
        >>> tracker = temp_dir / "tracker.json"
        >>> # Pattern overdue by 2 days
        >>> data = {
        ...     "patterns": {
        ...         "Use pathlib": {
        ...             "count": 5,
        ...             "composite_score": 0.75,
        ...             "sm2_state": {
        ...                 "easiness_factor": 2.5,
        ...                 "interval": 6,
        ...                 "repetitions": 2,
        ...                 "last_review": (
        ...                     datetime.now() - timedelta(days=8)
        ...                 ).strftime("%Y-%m-%d"),
        ...                 "next_review": (
        ...                     datetime.now() - timedelta(days=2)
        ...                 ).strftime("%Y-%m-%d"),
        ...             },
        ...         },
        ...         "No SM-2": {"count": 3, "composite_score": 0.5},
        ...     }
        ... }
        >>> _ = tracker.write_text(json.dumps(data))
        >>> due = find_due_patterns(tracker, datetime.now())
        >>> len(due)
        1
        >>> due[0]["pattern_text"]
        'Use pathlib'
        >>> due[0]["days_overdue"]
        2
        >>> import shutil
        >>> shutil.rmtree(temp_dir)

        >>> # No patterns due
        >>> temp_dir2 = Path(tempfile.mkdtemp())
        >>> tracker2 = temp_dir2 / "tracker.json"
        >>> data2 = {
        ...     "patterns": {
        ...         "Future": {
        ...             "count": 5,
        ...             "sm2_state": {
        ...                 "easiness_factor": 2.5,
        ...                 "interval": 6,
        ...                 "repetitions": 1,
        ...                 "last_review": datetime.now().strftime("%Y-%m-%d"),
        ...                 "next_review": (
        ...                     datetime.now() + timedelta(days=5)
        ...                 ).strftime("%Y-%m-%d"),
        ...             },
        ...         }
        ...     }
        ... }
        >>> _ = tracker2.write_text(json.dumps(data2))
        >>> due2 = find_due_patterns(tracker2, datetime.now())
        >>> len(due2)
        0
        >>> shutil.rmtree(temp_dir2)

        >>> # Empty tracker
        >>> temp_dir3 = Path(tempfile.mkdtemp())
        >>> tracker3 = temp_dir3 / "tracker.json"
        >>> _ = tracker3.write_text('{"patterns": {}}')
        >>> due3 = find_due_patterns(tracker3, datetime.now())
        >>> len(due3)
        0
        >>> shutil.rmtree(temp_dir3)
    """
    try:
        tracker = load_tracker(tracker_file)
    except (OSError, json.JSONDecodeError):
        return []

    patterns = tracker.get("patterns", {})
    due_patterns = []

    for pattern_text, pattern_data in patterns.items():
        sm2_state = pattern_data.get("sm2_state")
        if not sm2_state:
            continue

        # Check if review is due
        try:
            last_review_str = sm2_state.get("last_review")
            next_review_str = sm2_state.get("next_review")
            interval = sm2_state.get("interval", 1)

            if not last_review_str:
                continue

            last_review = datetime.strptime(last_review_str, "%Y-%m-%d")

            # Check if due
            if is_review_due(last_review, interval, current_date):
                # Calculate days overdue
                if next_review_str:
                    next_review = datetime.strptime(next_review_str, "%Y-%m-%d")
                    days_overdue = (current_date - next_review).days
                else:
                    # Fallback: calculate from last_review + interval
                    next_review = calculate_next_review_date(last_review, interval)
                    days_overdue = (current_date - next_review).days

                due_patterns.append(
                    {
                        "pattern_text": pattern_text,
                        "pattern_data": pattern_data,
                        "days_overdue": days_overdue,
                        "next_review": next_review_str
                        or next_review.strftime("%Y-%m-%d"),
                        "sm2_state": sm2_state,
                    }
                )
        except (ValueError, KeyError):
            # Invalid date format or missing keys - skip pattern
            continue

    # Sort by days_overdue DESC, then composite_score DESC
    due_patterns.sort(
        key=lambda p: (
            -p["days_overdue"],
            -p["pattern_data"].get("composite_score", 0),
        )
    )

    return due_patterns


def apply_quality_feedback(tracker_file: Path, pattern_text: str, quality: int) -> dict:
    """Apply quality feedback and update SM-2 state.

    Args:
        tracker_file: Path to pattern_tracker.json
        pattern_text: Pattern text to update
        quality: Recall quality (0-5, where 5=perfect, 3=pass, <3=fail)

    Returns:
        Result dictionary:
        {
            "success": True,
            "new_easiness": float,
            "new_interval": int,
            "new_repetitions": int,
            "next_review": "YYYY-MM-DD"
        }
        Or on error:
        {
            "success": False,
            "error": str
        }

    Examples:
        >>> from pathlib import Path
        >>> import tempfile, json
        >>> from datetime import datetime, timedelta
        >>> temp_dir = Path(tempfile.mkdtemp())
        >>> tracker = temp_dir / "tracker.json"
        >>> # Initial state
        >>> data = {
        ...     "patterns": {
        ...         "Use pathlib": {
        ...             "count": 5,
        ...             "sm2_state": {
        ...                 "easiness_factor": 2.5,
        ...                 "interval": 6,
        ...                 "repetitions": 2,
        ...                 "last_review": (
        ...                     datetime.now() - timedelta(days=8)
        ...                 ).strftime("%Y-%m-%d"),
        ...                 "next_review": (
        ...                     datetime.now() - timedelta(days=2)
        ...                 ).strftime("%Y-%m-%d"),
        ...             },
        ...         }
        ...     }
        ... }
        >>> _ = tracker.write_text(json.dumps(data))
        >>> # Good recall (quality=4)
        >>> result = apply_quality_feedback(tracker, "Use pathlib", 4)
        >>> result["success"]
        True
        >>> result["new_interval"] > 6  # Interval increased
        True
        >>> result["new_repetitions"]
        3
        >>> import shutil
        >>> shutil.rmtree(temp_dir)

        >>> # Failed recall (quality=2) resets interval
        >>> temp_dir2 = Path(tempfile.mkdtemp())
        >>> tracker2 = temp_dir2 / "tracker.json"
        >>> data2 = {
        ...     "patterns": {
        ...         "Pattern": {
        ...             "count": 5,
        ...             "sm2_state": {
        ...                 "easiness_factor": 2.5,
        ...                 "interval": 15,
        ...                 "repetitions": 3,
        ...                 "last_review": datetime.now().strftime("%Y-%m-%d"),
        ...                 "next_review": datetime.now().strftime("%Y-%m-%d"),
        ...             },
        ...         }
        ...     }
        ... }
        >>> _ = tracker2.write_text(json.dumps(data2))
        >>> result2 = apply_quality_feedback(tracker2, "Pattern", 2)
        >>> result2["success"]
        True
        >>> result2["new_interval"]
        1
        >>> result2["new_repetitions"]
        0
        >>> shutil.rmtree(temp_dir2)

        >>> # Invalid quality
        >>> temp_dir3 = Path(tempfile.mkdtemp())
        >>> tracker3 = temp_dir3 / "tracker.json"
        >>> _ = tracker3.write_text(
        ...     '{"patterns": {"Test": {"sm2_state": {"easiness_factor": 2.5, "interval": 1, "repetitions": 0}}}}'
        ... )
        >>> result3 = apply_quality_feedback(tracker3, "Test", 10)
        >>> result3["success"]
        False
        >>> "Quality must be 0-5" in result3["error"]
        True
        >>> shutil.rmtree(temp_dir3)

        >>> # Pattern not found
        >>> temp_dir4 = Path(tempfile.mkdtemp())
        >>> tracker4 = temp_dir4 / "tracker.json"
        >>> _ = tracker4.write_text('{"patterns": {}}')
        >>> result4 = apply_quality_feedback(tracker4, "Missing", 4)
        >>> result4["success"]
        False
        >>> "Pattern not found" in result4["error"]
        True
        >>> shutil.rmtree(temp_dir4)
    """
    # Validate quality
    if quality < 0 or quality > MAX_QUALITY_SCORE:
        return {
            "success": False,
            "error": f"Quality must be 0-{MAX_QUALITY_SCORE}, got {quality}",
        }

    # Load tracker
    try:
        tracker = load_tracker(tracker_file)
    except (OSError, json.JSONDecodeError) as e:
        return {"success": False, "error": f"Failed to load tracker: {e}"}

    # Find pattern and validate SM-2 state
    patterns = tracker.get("patterns", {})
    pattern_data = patterns.get(pattern_text)

    # Validate pattern exists with SM-2 state
    error_msg = None
    if not pattern_data:
        error_msg = "Pattern not found"
    elif not pattern_data.get("sm2_state"):
        error_msg = "Pattern has no SM-2 state"

    if error_msg:
        return {"success": False, "error": error_msg}

    sm2_state_dict = pattern_data["sm2_state"]

    # Construct current state
    current_state = SM2State(
        easiness_factor=sm2_state_dict.get("easiness_factor", 2.5),
        interval=sm2_state_dict.get("interval", 1),
        repetitions=sm2_state_dict.get("repetitions", 0),
    )

    # Update SM-2 state
    try:
        new_state = update_sm2_state(current_state, quality)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    # Calculate next review date
    now = datetime.now()
    next_review = calculate_next_review_date(now, new_state.interval)

    # Update pattern data
    pattern_data["sm2_state"] = {
        "easiness_factor": new_state.easiness_factor,
        "interval": new_state.interval,
        "repetitions": new_state.repetitions,
        "last_review": now.strftime("%Y-%m-%d"),
        "next_review": next_review.strftime("%Y-%m-%d"),
    }

    # Save tracker atomically
    try:
        save_tracker(tracker_file, tracker)
    except OSError as e:
        return {"success": False, "error": f"Failed to save tracker: {e}"}

    return {
        "success": True,
        "new_easiness": new_state.easiness_factor,
        "new_interval": new_state.interval,
        "new_repetitions": new_state.repetitions,
        "next_review": next_review.strftime("%Y-%m-%d"),
    }


def get_review_summary(tracker_file: Path) -> dict:
    """Get SM-2 review statistics.

    Args:
        tracker_file: Path to pattern_tracker.json

    Returns:
        Statistics dictionary:
        {
            "total_tracked": int,       # Patterns with SM-2 state
            "overdue": int,              # Overdue for review
            "due_today": int,            # Due today
            "due_soon": int,             # Due within 7 days
            "not_due": int,              # Not due yet
            "avg_easiness": float,       # Average easiness factor
            "max_interval": int          # Maximum interval
        }

    Examples:
        >>> from pathlib import Path
        >>> import tempfile, json
        >>> from datetime import datetime, timedelta
        >>> temp_dir = Path(tempfile.mkdtemp())
        >>> tracker = temp_dir / "tracker.json"
        >>> # Mix of patterns
        >>> data = {
        ...     "patterns": {
        ...         "Overdue": {
        ...             "sm2_state": {
        ...                 "easiness_factor": 2.5,
        ...                 "interval": 6,
        ...                 "repetitions": 2,
        ...                 "last_review": (
        ...                     datetime.now() - timedelta(days=10)
        ...                 ).strftime("%Y-%m-%d"),
        ...                 "next_review": (
        ...                     datetime.now() - timedelta(days=2)
        ...                 ).strftime("%Y-%m-%d"),
        ...             }
        ...         },
        ...         "Today": {
        ...             "sm2_state": {
        ...                 "easiness_factor": 2.0,
        ...                 "interval": 1,
        ...                 "repetitions": 1,
        ...                 "last_review": (
        ...                     datetime.now() - timedelta(days=1)
        ...                 ).strftime("%Y-%m-%d"),
        ...                 "next_review": datetime.now().strftime("%Y-%m-%d"),
        ...             }
        ...         },
        ...         "Soon": {
        ...             "sm2_state": {
        ...                 "easiness_factor": 3.0,
        ...                 "interval": 15,
        ...                 "repetitions": 3,
        ...                 "last_review": datetime.now().strftime("%Y-%m-%d"),
        ...                 "next_review": (
        ...                     datetime.now() + timedelta(days=5)
        ...                 ).strftime("%Y-%m-%d"),
        ...             }
        ...         },
        ...         "Not due": {
        ...             "sm2_state": {
        ...                 "easiness_factor": 2.2,
        ...                 "interval": 30,
        ...                 "repetitions": 4,
        ...                 "last_review": datetime.now().strftime("%Y-%m-%d"),
        ...                 "next_review": (
        ...                     datetime.now() + timedelta(days=20)
        ...                 ).strftime("%Y-%m-%d"),
        ...             }
        ...         },
        ...         "No SM-2": {"count": 5},
        ...     }
        ... }
        >>> _ = tracker.write_text(json.dumps(data))
        >>> summary = get_review_summary(tracker)
        >>> summary["total_tracked"]
        4
        >>> summary["overdue"]
        1
        >>> summary["due_today"]
        1
        >>> summary["due_soon"]
        1
        >>> summary["not_due"]
        1
        >>> summary["avg_easiness"]
        2.425
        >>> summary["max_interval"]
        30
        >>> import shutil
        >>> shutil.rmtree(temp_dir)

        >>> # Empty tracker
        >>> temp_dir2 = Path(tempfile.mkdtemp())
        >>> tracker2 = temp_dir2 / "tracker.json"
        >>> _ = tracker2.write_text('{"patterns": {}}')
        >>> summary2 = get_review_summary(tracker2)
        >>> summary2["total_tracked"]
        0
        >>> summary2["overdue"]
        0
        >>> shutil.rmtree(temp_dir2)

        >>> # Non-existent tracker
        >>> temp_dir3 = Path(tempfile.mkdtemp())
        >>> tracker3 = temp_dir3 / "nonexistent.json"
        >>> summary3 = get_review_summary(tracker3)
        >>> summary3["total_tracked"]
        0
        >>> shutil.rmtree(temp_dir3)
    """
    try:
        tracker = load_tracker(tracker_file)
    except (OSError, json.JSONDecodeError):
        return {
            "total_tracked": 0,
            "overdue": 0,
            "due_today": 0,
            "due_soon": 0,
            "not_due": 0,
            "avg_easiness": 0.0,
            "max_interval": 0,
        }

    patterns = tracker.get("patterns", {})
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    soon_cutoff = now + timedelta(days=7)

    total_tracked = 0
    overdue = 0
    due_today = 0
    due_soon = 0
    not_due = 0
    easiness_sum = 0.0
    max_interval = 0

    for pattern_data in patterns.values():
        sm2_state = pattern_data.get("sm2_state")
        if not sm2_state:
            continue

        total_tracked += 1

        # Get dates
        try:
            next_review_str = sm2_state.get("next_review")
            if not next_review_str:
                continue

            next_review = datetime.strptime(next_review_str, "%Y-%m-%d")

            # Categorize
            if next_review < today_start:
                overdue += 1
            elif next_review.date() == now.date():
                due_today += 1
            elif next_review <= soon_cutoff:
                due_soon += 1
            else:
                not_due += 1

        except (ValueError, KeyError):
            # Invalid date format - skip
            continue

        # Collect stats
        easiness_sum += sm2_state.get("easiness_factor", 0)
        interval = sm2_state.get("interval", 0)
        max_interval = max(max_interval, interval)

    avg_easiness = easiness_sum / total_tracked if total_tracked > 0 else 0.0

    return {
        "total_tracked": total_tracked,
        "overdue": overdue,
        "due_today": due_today,
        "due_soon": due_soon,
        "not_due": not_due,
        "avg_easiness": avg_easiness,
        "max_interval": max_interval,
    }


def cmd_find_due(tracker_file: Path) -> None:
    """Execute find-due command."""
    due = find_due_patterns(tracker_file, datetime.now())
    print(f"{len(due)} patterns due")
    for p in due[:10]:
        pattern_text = p["pattern_text"][:50]
        days = p["days_overdue"]
        print(f"{pattern_text}... (overdue: {days} days)")


def cmd_apply_feedback(tracker_file: Path) -> None:
    """Execute apply-feedback command."""
    if len(sys.argv) < MIN_ARGS_FEEDBACK:
        print(
            'Usage: pattern_review.py apply-feedback "<pattern>" <quality>',
            file=sys.stderr,
        )
        sys.exit(1)

    pattern_text = sys.argv[2]
    quality = int(sys.argv[3])

    result = apply_quality_feedback(tracker_file, pattern_text, quality)

    if result["success"]:
        print(
            f"✓ Updated: next review in {result['new_interval']} days (EF: {result['new_easiness']:.2f})"
        )
    else:
        print(f"✗ Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
        sys.exit(1)


def cmd_verify_pattern(tracker_file: Path) -> None:
    """Execute verify-pattern command."""
    if len(sys.argv) < MIN_ARGS_PATTERN:
        print('Usage: pattern_review.py verify-pattern "<pattern>"', file=sys.stderr)
        sys.exit(1)

    pattern_text = sys.argv[2]

    if not tracker_file.exists():
        print("✗ Error: pattern_tracker.json not found", file=sys.stderr)
        sys.exit(1)

    with open(tracker_file, encoding="utf-8") as f:
        tracker = json.load(f)

    pattern_data = tracker.get("patterns", {}).get(pattern_text)
    if not pattern_data:
        print("✗ Error: Pattern not found", file=sys.stderr)
        sys.exit(1)

    sm2 = pattern_data.get("sm2_state", {})
    print(f"Pattern: {pattern_text}")
    print(f"Count: {pattern_data.get('count', 0)}")
    print(f"Interval: {sm2.get('interval', 'N/A')} days")
    print(f"Repetitions: {sm2.get('repetitions', 'N/A')}")
    print(f"Easiness Factor: {sm2.get('easiness_factor', 'N/A')}")
    print(f"Last Review: {sm2.get('last_review', 'N/A')}")
    print(f"Next Review: {sm2.get('next_review', 'N/A')}")


def cmd_summary(tracker_file: Path) -> None:
    """Execute summary command."""
    summary = get_review_summary(tracker_file)
    print(f"Tracked: {summary['total_tracked']}")
    print(f"Overdue: {summary['overdue']}")
    print(f"Due today: {summary['due_today']}")
    print(f"Due soon: {summary['due_soon']}")
    print(f"Not due: {summary['not_due']}")
    print(f"Avg easiness: {summary['avg_easiness']:.2f}")
    print(f"Max interval: {summary['max_interval']} days")


def main():
    """CLI entry point."""
    if len(sys.argv) < MIN_ARGS_BASE:
        print("Usage:", file=sys.stderr)
        print("  pattern_review.py find-due", file=sys.stderr)
        print(
            '  pattern_review.py apply-feedback "<pattern>" <quality>', file=sys.stderr
        )
        print('  pattern_review.py verify-pattern "<pattern>"', file=sys.stderr)
        print("  pattern_review.py summary", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    tracker_file = Path(".claude/as_you/pattern_tracker.json")

    if command == "find-due":
        cmd_find_due(tracker_file)
    elif command == "apply-feedback":
        cmd_apply_feedback(tracker_file)
    elif command == "verify-pattern":
        cmd_verify_pattern(tracker_file)
    elif command == "summary":
        cmd_summary(tracker_file)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    import doctest

    # Check if running doctests
    if "--test" in sys.argv or "-v" in sys.argv:
        print("Running pattern review doctests:")
        results = doctest.testmod(verbose=("--verbose" in sys.argv or "-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
