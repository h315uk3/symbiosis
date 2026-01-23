#!/usr/bin/env python3
"""
Habit feedback command.

Phase 4 of Issue #83: Habit Extraction and Automatic Application.

Usage:
    python3 -m as_you.commands.habit_feedback <note_id> <feedback>
    python3 -m as_you.commands.habit_feedback n_20260123_001 success
    python3 -m as_you.commands.habit_feedback n_20260123_001 partial
    python3 -m as_you.commands.habit_feedback n_20260123_001 failure
"""

import sys

from as_you.lib.common import AsYouConfig
from as_you.lib.habit_feedback import apply_feedback


def main():
    """Main entry point for habit feedback command."""
    min_argc = 3  # program name + note_id + feedback
    if len(sys.argv) < min_argc or sys.argv[1] in ["-h", "--help"]:
        print("Usage: python3 -m as_you.commands.habit_feedback <note_id> <feedback>")
        print("Feedback types: success, partial, failure")
        print("\nExamples:")
        print("  python3 -m as_you.commands.habit_feedback n_20260123_001 success")
        print("  python3 -m as_you.commands.habit_feedback n_20260123_001 partial")
        print("  python3 -m as_you.commands.habit_feedback n_20260123_001 failure")
        sys.exit(0)

    note_id = sys.argv[1]
    feedback = sys.argv[2].lower()

    # Validate feedback
    if feedback not in ["success", "partial", "failure"]:
        print(f"Error: Invalid feedback '{feedback}'")
        print("Valid feedback types: success, partial, failure")
        sys.exit(1)

    # Load config
    config = AsYouConfig.from_environment()
    half_life_days = config.settings.get("habits", {}).get(
        "freshness_half_life_days", 30
    )

    # Apply feedback
    result = apply_feedback(config.tracker_file, note_id, feedback, half_life_days)

    if result["success"]:
        print("Feedback applied successfully:")
        print(f"  Note ID: {result['note_id']}")
        print(f"  New confidence: {result['new_confidence']:.3f}")
        print(f"  Variance: {result['new_variance']:.4f}")
        print(f"  Total uses: {result['use_count']}")
    else:
        print(f"Error: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
