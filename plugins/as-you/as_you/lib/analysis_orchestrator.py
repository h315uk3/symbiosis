#!/usr/bin/env python3
"""Analysis orchestrator for unified pattern analysis workflow.

This module consolidates all pattern analysis steps (pattern detection,
TF-IDF calculation, PMI calculation, score calculation, pattern merging)
into a single coordinated workflow, replacing sequential script calls
in hooks/session_end.py.
"""

import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Add plugin to path for imports
_PLUGIN_ROOT = Path(__file__).parent.parent.parent
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from as_you.lib.common import (  # noqa: E402
    AsYouConfig,
    TrackerData,
    load_tracker,
    save_tracker,
)


@dataclass
class AnalysisResult:
    """Result of pattern analysis.

    Examples:
        >>> result = AnalysisResult(
        ...     patterns_analyzed=10,
        ...     patterns_merged=2,
        ...     scores_updated=10,
        ...     duration_ms=150.5,
        ... )
        >>> result.patterns_analyzed
        10
        >>> result.duration_ms
        150.5
    """

    patterns_analyzed: int
    patterns_merged: int
    scores_updated: int
    duration_ms: float

    def __repr__(self) -> str:
        return (
            f"AnalysisResult(analyzed={self.patterns_analyzed}, "
            f"merged={self.patterns_merged}, "
            f"scores_updated={self.scores_updated}, "
            f"duration={self.duration_ms:.1f}ms)"
        )


class AnalysisOrchestrator:
    """Orchestrate pattern analysis workflow.

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> import json
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     # Setup test data
        ...     tracker_file = Path(tmpdir) / "pattern_tracker.json"
        ...     archive_dir = Path(tmpdir) / "archive"
        ...     archive_dir.mkdir()
        ...     data = {
        ...         "patterns": {"test": {"count": 5, "last_seen": "2026-01-20"}},
        ...         "cooccurrences": [],
        ...         "promotion_candidates": [],
        ...     }
        ...     _ = tracker_file.write_text(json.dumps(data))
        ...     _ = (archive_dir / "2026-01-20.md").write_text("test test")
        ...
        ...     # Create orchestrator
        ...     orchestrator = AnalysisOrchestrator(tracker_file, archive_dir)
        ...     orchestrator.tracker_file == tracker_file
        True
    """

    def __init__(self, tracker_file: Path, archive_dir: Path):
        """Initialize orchestrator.

        Args:
            tracker_file: Path to pattern_tracker.json
            archive_dir: Path to session archive directory
        """
        self.tracker_file = tracker_file
        self.archive_dir = archive_dir
        self.data: TrackerData | None = None

    def load_data(self) -> TrackerData:
        """Load tracker data.

        Returns:
            Tracker data dictionary

        Examples:
            >>> from pathlib import Path
            >>> import tempfile, json
            >>> with tempfile.TemporaryDirectory() as tmpdir:
            ...     tracker_file = Path(tmpdir) / "tracker.json"
            ...     archive_dir = Path(tmpdir) / "archive"
            ...     archive_dir.mkdir()
            ...     data = {"patterns": {}, "cooccurrences": []}
            ...     _ = tracker_file.write_text(json.dumps(data))
            ...     orch = AnalysisOrchestrator(tracker_file, archive_dir)
            ...     loaded = orch.load_data()
            ...     "patterns" in loaded
            True
        """
        self.data = load_tracker(self.tracker_file)
        return self.data

    def save_data(self) -> None:
        """Save tracker data.

        Examples:
            >>> from pathlib import Path
            >>> import tempfile, json
            >>> with tempfile.TemporaryDirectory() as tmpdir:
            ...     tracker_file = Path(tmpdir) / "tracker.json"
            ...     archive_dir = Path(tmpdir) / "archive"
            ...     archive_dir.mkdir()
            ...     orch = AnalysisOrchestrator(tracker_file, archive_dir)
            ...     orch.data = {"patterns": {"test": {"count": 1}}}
            ...     orch.save_data()
            ...     tracker_file.exists()
            True
        """
        if self.data is None:
            msg = "No data loaded"
            raise ValueError(msg)
        save_tracker(self.tracker_file, self.data)

    def run_analysis(self, skip_merge: bool = False) -> AnalysisResult:
        """Run complete pattern analysis workflow.

        Args:
            skip_merge: Skip pattern merging step

        Returns:
            Analysis result with statistics

        Examples:
            >>> from pathlib import Path
            >>> import tempfile, json
            >>> with tempfile.TemporaryDirectory() as tmpdir:
            ...     tracker_file = Path(tmpdir) / "tracker.json"
            ...     archive_dir = Path(tmpdir) / "archive"
            ...     archive_dir.mkdir()
            ...     data = {"patterns": {}, "cooccurrences": []}
            ...     _ = tracker_file.write_text(json.dumps(data))
            ...     orch = AnalysisOrchestrator(tracker_file, archive_dir)
            ...     result = orch.run_analysis()
            ...     result.patterns_analyzed >= 0
            True
        """
        start_time = time.perf_counter()

        # Load data
        self.load_data()

        patterns_analyzed = len(self.data.get("patterns", {}))
        patterns_merged = 0
        scores_updated = 0

        # TODO: Phase 3 - Add actual analysis steps:
        # 1. TF-IDF/BM25 calculation
        # 2. PMI calculation
        # 3. Time decay calculation
        # 4. Composite score calculation
        # 5. Pattern merging (if not skip_merge)

        # Save results
        self.save_data()

        duration_ms = (time.perf_counter() - start_time) * 1000

        return AnalysisResult(
            patterns_analyzed=patterns_analyzed,
            patterns_merged=patterns_merged,
            scores_updated=scores_updated,
            duration_ms=duration_ms,
        )

    def get_statistics(self) -> dict[str, Any]:
        """Get pattern statistics.

        Returns:
            Dictionary with pattern statistics

        Examples:
            >>> from pathlib import Path
            >>> import tempfile, json
            >>> with tempfile.TemporaryDirectory() as tmpdir:
            ...     tracker_file = Path(tmpdir) / "tracker.json"
            ...     archive_dir = Path(tmpdir) / "archive"
            ...     archive_dir.mkdir()
            ...     data = {
            ...         "patterns": {"a": {"count": 5}, "b": {"count": 3}},
            ...         "cooccurrences": [],
            ...         "promotion_candidates": [],
            ...     }
            ...     _ = tracker_file.write_text(json.dumps(data))
            ...     orch = AnalysisOrchestrator(tracker_file, archive_dir)
            ...     _ = orch.load_data()  # Suppress output
            ...     stats = orch.get_statistics()
            ...     stats["total_patterns"]
            2
        """
        if self.data is None:
            msg = "No data loaded"
            raise ValueError(msg)

        patterns = self.data.get("patterns", {})
        return {
            "total_patterns": len(patterns),
            "total_cooccurrences": len(self.data.get("cooccurrences", [])),
            "promotion_candidates": len(self.data.get("promotion_candidates", [])),
        }


def main():
    """CLI entry point for orchestrator."""
    config = AsYouConfig.from_environment()

    print("実行中: Pattern Analysis Orchestrator")
    print("-" * 50)

    orchestrator = AnalysisOrchestrator(config.tracker_file, config.archive_dir)

    # Run analysis
    result = orchestrator.run_analysis()
    print(f"✓ 分析完了: {result}")

    # Show statistics
    stats = orchestrator.get_statistics()
    print("\n統計情報:")
    print(f"  パターン総数: {stats['total_patterns']}")
    print(f"  共起パターン: {stats['total_cooccurrences']}")
    print(f"  昇格候補: {stats['promotion_candidates']}")


if __name__ == "__main__":
    import doctest

    # Check if running doctests
    if "--test" in sys.argv or "-v" in sys.argv:
        print("Running analysis orchestrator doctests:")
        results = doctest.testmod(verbose=("--verbose" in sys.argv or "-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
