#!/usr/bin/env python3
"""
SessionEnd hook for habit freshness update.

Phase 4 of Issue #83: Habit Extraction and Automatic Application.
"""

import sys
from pathlib import Path

# Add plugin root to Python path
HOOK_DIR = Path(__file__).parent.resolve()
REPO_ROOT = HOOK_DIR.parent
sys.path.insert(0, str(REPO_ROOT))

from as_you.lib.common import AsYouConfig, load_tracker, save_tracker
from as_you.lib.habit_feedback import calculate_freshness_for_all


def main() -> int:
    """
    Main entry point for freshness update hook.

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    try:
        config = AsYouConfig.from_environment()

        # Get half-life from settings
        half_life_days = config.settings.get("habits", {}).get(
            "freshness_half_life_days", 30
        )

        # Load tracker
        tracker = load_tracker(config.tracker_file)
        notes = tracker.get("notes", [])

        if not notes:
            print("No notes to update")
            return 0

        # Recalculate freshness for all notes
        calculate_freshness_for_all(notes, half_life_days)

        # Save tracker
        save_tracker(config.tracker_file, tracker)

    except Exception as e:
        print(f"Freshness update error: {e}", file=sys.stderr)
        return 1
    else:
        print(f"Freshness updated for {len(notes)} note(s)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
