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

# Import scoring modules
from as_you.lib.bayesian_learning import (  # noqa: E402
    update_bayesian_state,
)
from as_you.lib.bm25_calculator import calculate_bm25_scores  # noqa: E402
from as_you.lib.common import (  # noqa: E402
    AsYouConfig,
    TrackerData,
    load_tracker,
    save_tracker,
)
from as_you.lib.composite_score_calculator import (  # noqa: E402
    calculate_composite_scores,
)
from as_you.lib.ebbinghaus_calculator import (  # noqa: E402
    calculate_ebbinghaus_scores,
)
from as_you.lib.pmi_calculator import calculate_pmi_scores  # noqa: E402
from as_you.lib.shannon_entropy_calculator import (  # noqa: E402
    calculate_shannon_entropy_scores,
    normalize_entropy_scores,
)
from as_you.lib.thompson_sampling import (  # noqa: E402
    ThompsonState,
    update_thompson_state,
)

# Constants
THOMPSON_SUCCESS_THRESHOLD = 0.5  # Threshold for treating composite score as "success"


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
        self.config = AsYouConfig.from_environment()

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

    def run_analysis(self, skip_merge: bool = False) -> AnalysisResult:  # noqa: PLR0912, PLR0915
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

        patterns = self.data.get("patterns", {})
        patterns_analyzed = len(patterns)
        patterns_merged = 0
        scores_updated = 0

        if not patterns:
            # No patterns to analyze
            duration_ms = (time.perf_counter() - start_time) * 1000
            return AnalysisResult(
                patterns_analyzed=0,
                patterns_merged=0,
                scores_updated=0,
                duration_ms=duration_ms,
            )

        # Get configuration settings
        config = AsYouConfig.from_environment()
        scoring_config = config.settings["scoring"]

        # 1. BM25 calculation (replaces TF-IDF)
        if scoring_config["bm25"]["enabled"]:
            bm25_scores = calculate_bm25_scores(
                patterns,
                self.archive_dir,
                k1=scoring_config["bm25"]["k1"],
                b=scoring_config["bm25"]["b"],
            )
            for pattern_text, score in bm25_scores.items():
                if pattern_text in patterns:
                    patterns[pattern_text]["bm25_score"] = score
                    scores_updated += 1

        # 2. PMI calculation (co-occurrence analysis)
        if scoring_config.get("pmi", {}).get("enabled", True):
            pmi_scores = calculate_pmi_scores(
                patterns,
                self.archive_dir,
                min_cooccurrence=scoring_config["pmi"].get("min_cooccurrence", 2),
            )
            for pattern_text, score in pmi_scores.items():
                if pattern_text in patterns:
                    patterns[pattern_text]["pmi_score"] = score
                    scores_updated += 1

        # 3. Ebbinghaus forgetting curve calculation
        memory_config = config.settings["memory"]
        if memory_config.get("ebbinghaus", {}).get("enabled", True):
            ebbinghaus_scores = calculate_ebbinghaus_scores(
                patterns,
                base_strength=memory_config["ebbinghaus"]["base_strength"],
                growth_factor=memory_config["ebbinghaus"]["growth_factor"],
            )
            for pattern_text, score in ebbinghaus_scores.items():
                if pattern_text in patterns:
                    patterns[pattern_text]["ebbinghaus_score"] = score
                    scores_updated += 1

        # 3.5. Shannon Entropy calculation (pattern diversity)
        diversity_config = config.settings.get("diversity", {})
        entropy_config = diversity_config.get("shannon_entropy", {})
        if entropy_config.get("enabled", True):
            context_keys = entropy_config.get("context_keys", ["sessions"])
            aggregation = entropy_config.get("aggregation", "mean")
            max_contexts = entropy_config.get("max_contexts", 10)

            entropy_scores = calculate_shannon_entropy_scores(
                patterns, context_keys=context_keys, aggregation=aggregation
            )
            normalized_entropy = normalize_entropy_scores(entropy_scores, max_contexts)

            for pattern_text, score in normalized_entropy.items():
                if pattern_text in patterns:
                    patterns[pattern_text]["shannon_entropy_score"] = score
                    scores_updated += 1

        # 4. Composite score calculation
        composite_scores = calculate_composite_scores(
            patterns,
            weights=scoring_config["weights"],
            normalize=True,
        )
        for pattern_text, score in composite_scores.items():
            if pattern_text in patterns:
                patterns[pattern_text]["composite_score"] = score
                scores_updated += 1

        # 4.5. Bayesian confidence tracking
        confidence_config = self.config.settings.get("confidence", {})
        bayesian_config = confidence_config.get("bayesian", {})
        if bayesian_config.get("enabled", True):
            prior_mean = bayesian_config.get("prior_mean", 0.5)
            prior_variance = bayesian_config.get("prior_variance", 0.04)

            for _pattern_text, pattern_data in patterns.items():
                # Initialize Bayesian state if not present
                if "bayesian_state" not in pattern_data:
                    pattern_data["bayesian_state"] = {
                        "mean": prior_mean,
                        "variance": prior_variance,
                    }

                # Update Bayesian state using composite score as observation
                composite_score = pattern_data.get("composite_score", 0.0)
                observation_variance = 0.01  # Low variance for composite score

                current_state = pattern_data["bayesian_state"]
                updated_state = update_bayesian_state(
                    prior_mean=current_state["mean"],
                    prior_variance=current_state["variance"],
                    observation=composite_score,
                    observation_variance=observation_variance,
                )

                pattern_data["bayesian_state"] = {
                    "mean": updated_state.mean,
                    "variance": updated_state.variance,
                }
                scores_updated += 1

        # 4.6. Thompson Sampling (Beta-Binomial)
        thompson_config = confidence_config.get("thompson_sampling", {})
        if thompson_config.get("enabled", True):
            initial_alpha = thompson_config.get("initial_alpha", 1.0)
            initial_beta = thompson_config.get("initial_beta", 1.0)

            for _pattern_text, pattern_data in patterns.items():
                # Initialize Thompson state if not present
                if "thompson_state" not in pattern_data:
                    pattern_data["thompson_state"] = {
                        "alpha": initial_alpha,
                        "beta": initial_beta,
                    }

                # Update Thompson state based on composite score
                # Treat high composite score as "success"
                composite_score = pattern_data.get("composite_score", 0.0)
                success = composite_score > THOMPSON_SUCCESS_THRESHOLD

                current_thompson = pattern_data["thompson_state"]
                updated_thompson = update_thompson_state(
                    ThompsonState(
                        alpha=current_thompson["alpha"], beta=current_thompson["beta"]
                    ),
                    success=success,
                )

                pattern_data["thompson_state"] = {
                    "alpha": updated_thompson.alpha,
                    "beta": updated_thompson.beta,
                }
                scores_updated += 1

        # 6. SM-2 state initialization
        memory_config = config.settings.get("memory", {})
        sm2_config = memory_config.get("sm2", {})
        if sm2_config.get("enabled", True):
            from datetime import datetime  # noqa: PLC0415

            from as_you.lib.sm2_memory import create_initial_state  # noqa: PLC0415

            for _pattern_text, pattern_data in patterns.items():
                # Initialize SM-2 state if not present
                if "sm2_state" not in pattern_data:
                    initial_ef = sm2_config.get("initial_easiness", 2.5)
                    state = create_initial_state(initial_ef)
                    pattern_data["sm2_state"] = {
                        "easiness_factor": state.easiness_factor,
                        "interval": state.interval,
                        "repetitions": state.repetitions,
                        "last_review": datetime.now().strftime("%Y-%m-%d"),
                        "next_review": None,  # Will be set when /apply provides feedback
                    }
                    scores_updated += 1

        # 5. Pattern merging (if not skip_merge)
        if not skip_merge:
            from as_you.hooks.pattern_merger import merge_patterns_auto  # noqa: PLC0415

            # Merge similar patterns based on Levenshtein distance
            patterns, merged_count = merge_patterns_auto(
                patterns,
                similarity_threshold=0.85,  # Can make configurable later
                min_count=1,
            )
            patterns_merged += merged_count

            # Update tracker data with merged patterns
            self.data["patterns"] = patterns

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
