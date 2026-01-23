#!/usr/bin/env python3
"""
Apply habits command.

Phase 3 of Issue #83: Habit Extraction and Automatic Application.

Usage:
    python3 -m as_you.commands.apply_habits [query]
    python3 -m as_you.commands.apply_habits "testing python"
    python3 -m as_you.commands.apply_habits  # Auto-detect context
"""

import sys
from pathlib import Path

# Add plugin root to Python path
COMMAND_DIR = Path(__file__).parent.resolve()
REPO_ROOT = COMMAND_DIR.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from as_you.lib.common import AsYouConfig
from as_you.lib.context_detector import (
    build_context_query,
    detect_project_type,
    extract_keywords_from_files,
)
from as_you.lib.habit_searcher import search_habits


def main():
    """Main entry point for apply habits command."""
    config = AsYouConfig.from_environment()

    # Get settings
    habits_config = config.settings.get("habits", {})
    min_confidence = habits_config.get("min_confidence", 0.5)
    min_freshness = habits_config.get("min_freshness", 0.3)
    half_life_days = habits_config.get("freshness_half_life_days", 30)

    bm25_config = config.settings.get("scoring", {}).get("bm25", {})
    k1 = bm25_config.get("k1", 1.5)
    b = bm25_config.get("b", 0.75)

    # Determine query
    if len(sys.argv) > 1 and sys.argv[1] not in ["-h", "--help"]:
        # Manual query
        query = " ".join(sys.argv[1:])
        print(f"Searching for habits: '{query}'")
    else:
        # Auto-detect context
        print("Auto-detecting project context...")
        tags = detect_project_type(config.project_root)
        keywords = extract_keywords_from_files(config.project_root)
        query = build_context_query(tags, keywords)
        print(f"Detected query: '{query}'")

    print("-" * 60)

    # Search for habits
    results = search_habits(
        query,
        config.tracker_file,
        top_k=5,
        min_confidence=min_confidence,
        min_freshness=min_freshness,
        k1=k1,
        b=b,
        half_life_days=half_life_days,
    )

    if not results:
        print("No relevant habits found.")
        sys.exit(0)

    # Display results
    print(f"Found {len(results)} relevant habit(s):\n")
    for i, habit in enumerate(results, 1):
        print(f"{i}. {habit['text']}")
        print(
            f"   Score: {habit['final_score']:.4f} "
            f"(Confidence: {habit['confidence']:.2f}, "
            f"Freshness: {habit['freshness']:.2f})"
        )
        print()

    print("Apply these habits in your current work session.")


if __name__ == "__main__":
    main()
