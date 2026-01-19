#!/usr/bin/env python3
"""
Score calculator hook for As You plugin.
Calculates composite scores for patterns and identifies promotion candidates.
Split from frequency_tracker.py for independent execution and testing.
"""

import sys

from as_you.lib.common import AsYouConfig
from as_you.lib.score_calculator import UnifiedScoreCalculator


def main():
    """CLI entry point for score calculation."""
    # Get paths from environment using common config
    config = AsYouConfig.from_environment()

    # Calculate scores
    try:
        calculator = UnifiedScoreCalculator(config.tracker_file, config.archive_dir)

        # Calculate all scores (TF-IDF, PMI, frequency, etc.)
        data = calculator.calculate_all_scores()

        # Save updated tracker with scores and promotion candidates
        calculator.save()

        # Get statistics from data
        pattern_count = len(data.get("patterns", {}))
        candidate_count = len(data.get("promotion_candidates", []))

        print(
            f"Scores calculated: {pattern_count} patterns analyzed, "
            f"{candidate_count} promotion candidates identified"
        )

    except Exception as e:
        print(f"Error calculating scores: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
