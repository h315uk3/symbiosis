#!/usr/bin/env python3
"""
Memory statistics collector for As You plugin.
Collects and outputs JSON statistics about current memory state.
"""

import json
import os
import sys
from pathlib import Path

# Add scripts/ to Python path
scripts_dir = Path(__file__).parent.parent
sys.path.insert(0, str(scripts_dir))

from lib.common import load_tracker


def collect_stats() -> dict:
    """Collect memory statistics."""
    stats = {}

    # Session notes
    notes_file = ".claude/as_you/session_notes.local.md"
    if os.path.exists(notes_file):
        with open(notes_file, encoding="utf-8") as f:
            stats["current_notes"] = len(f.readlines())
    else:
        stats["current_notes"] = 0

    # Archives
    archive_dir = Path(".claude/as_you/session_archive")
    if archive_dir.exists():
        stats["archives"] = len(list(archive_dir.glob("*.md")))
    else:
        stats["archives"] = 0

    # Patterns
    tracker_file = Path(".claude/as_you/pattern_tracker.json")
    try:
        data = load_tracker(tracker_file)
        stats["patterns"] = len(data.get("patterns", {}))
        stats["candidates"] = len(data.get("promotion_candidates", []))
    except (json.JSONDecodeError, IOError):
        # Corrupted or inaccessible file - use defaults
        stats["patterns"] = 0
        stats["candidates"] = 0

    # Skills
    skills_dir = Path("skills")
    if skills_dir.exists():
        stats["skills"] = len(list(skills_dir.glob("*/SKILL.md")))
    else:
        stats["skills"] = 0

    # Agents
    agents_dir = Path("agents")
    if agents_dir.exists():
        stats["agents"] = len(list(agents_dir.glob("*.md")))
    else:
        stats["agents"] = 0

    return stats


def main():
    """Main entry point."""
    stats = collect_stats()
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
