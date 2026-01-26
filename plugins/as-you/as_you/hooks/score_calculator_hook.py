#!/usr/bin/env python3
"""
Score calculator hook for As You plugin.
Uses AnalysisOrchestrator with BM25, time decay, and composite scoring.
"""

import sys
from pathlib import Path

# Add plugin to path for imports
_PLUGIN_ROOT = Path(__file__).parent.parent.parent
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from as_you.lib.analysis_orchestrator import AnalysisOrchestrator
from as_you.lib.common import AsYouConfig


def main():
    """CLI entry point for score calculation."""
    # Get paths from environment using common config
    config = AsYouConfig.from_environment()

    # Run analysis with orchestrator
    try:
        orchestrator = AnalysisOrchestrator(config.tracker_file, config.archive_dir)

        # Run complete analysis (BM25, time decay, composite scoring)
        result = orchestrator.run_analysis(skip_merge=True)

        print(
            f"Scoring complete: {result.patterns_analyzed} patterns analyzed, "
            f"{result.scores_updated} scores updated "
            f"({result.duration_ms:.1f}ms)"
        )

        # Get statistics
        stats = orchestrator.get_statistics()
        if stats["promotion_candidates"] > 0:
            print(f"Promotion candidates: {stats['promotion_candidates']}")

    except Exception as e:
        print(f"Error calculating scores: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
