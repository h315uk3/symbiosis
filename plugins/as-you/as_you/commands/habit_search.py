#!/usr/bin/env python3
"""
Habit search command (debug tool).

Phase 2 of Issue #83: Habit Extraction and Automatic Application.

Usage:
    python3 -m as_you.commands.habit_search "query string"
    python3 -m as_you.commands.habit_search "query" --json
"""

import json
import sys
from pathlib import Path

# Add plugin root to Python path
COMMAND_DIR = Path(__file__).parent.resolve()
REPO_ROOT = COMMAND_DIR.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from as_you.lib.common import AsYouConfig
from as_you.lib.habit_searcher import search_habits


def main():
    """Main entry point for habit search command."""
    min_argc = 2  # program name + query
    if len(sys.argv) < min_argc or sys.argv[1] in ["-h", "--help"]:
        print("Usage: python3 -m as_you.commands.habit_search <query> [--json]")
        print("       python3 -m as_you.commands.habit_search 'testing python'")
        print("       python3 -m as_you.commands.habit_search 'run tests' --json")
        sys.exit(0)

    # Parse arguments
    json_output = "--json" in sys.argv
    query_parts = [arg for arg in sys.argv[1:] if arg != "--json"]
    query = " ".join(query_parts)

    # Load config
    config = AsYouConfig.from_environment()

    # Get settings
    habits_config = config.settings.get("habits", {})
    min_confidence = habits_config.get("min_confidence", 0.5)
    min_freshness = habits_config.get("min_freshness", 0.3)
    half_life_days = habits_config.get("freshness_half_life_days", 30)

    bm25_config = config.settings.get("scoring", {}).get("bm25", {})
    k1 = bm25_config.get("k1", 1.5)
    b = bm25_config.get("b", 0.75)

    # Search
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

    # Output
    if json_output:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        if not results:
            print(f"No habits found for query: '{query}'")
            sys.exit(0)

        print(f"Found {len(results)} habit(s) for: '{query}'")
        print(f"Filters: confidence>={min_confidence}, freshness>={min_freshness}")
        print("-" * 60)

        for i, result in enumerate(results, 1):
            print(f"{i}. {result['text']}")
            print(f"   ID: {result['id']}")
            print(
                f"   Score: {result['final_score']:.4f} "
                f"(BM25: {result['bm25_score']:.4f}, "
                f"Confidence: {result['confidence']:.2f}, "
                f"Freshness: {result['freshness']:.2f})"
            )
            print()


if __name__ == "__main__":
    main()
