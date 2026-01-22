#!/usr/bin/env python3
"""Performance benchmarks for as-you plugin.

This module establishes baseline performance metrics and tracks regressions.
All benchmarks should complete within their target times to pass.

Usage:
    python3 tests/performance/benchmarks.py
    python3 tests/performance/benchmarks.py --verbose
"""

import json
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

# Add plugins directory to Python path for imports
_REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT / "plugins/as-you"))


@dataclass
class BenchmarkResult:
    """Performance benchmark result.

    Examples:
        >>> result = BenchmarkResult("test", 0.5, 1.0)
        >>> result.passed
        True
        >>> result = BenchmarkResult("slow", 2.0, 1.0)
        >>> result.passed
        False
    """

    name: str
    duration: float
    target: float

    @property
    def passed(self) -> bool:
        """Check if benchmark passed (duration <= target)."""
        return self.duration <= self.target

    def __repr__(self) -> str:
        status = "✓" if self.passed else "✗"
        return (
            f"{status} {self.name}: {self.duration:.3f}秒 (目標: {self.target:.3f}秒)"
        )


class Benchmark:
    """Benchmark runner.

    Examples:
        >>> bench = Benchmark()
        >>> result = bench.run("test", lambda: time.sleep(0.01))
        >>> result.name
        'test'
        >>> result.passed
        True
    """

    # Performance targets (in seconds)
    TARGETS: ClassVar[dict[str, float]] = {
        # Command execution
        "note_add": 0.5,
        "notes_display": 0.3,
        "promote_analysis": 1.0,
        # Core operations
        "pattern_tracker_update": 2.0,
        "tfidf_calculation_100": 1.0,
        "pmi_calculation_100": 1.0,
        "score_calculation": 0.5,
        "promote_check": 0.1,
        # Hook performance
        "session_end_hook": 3.0,
        # Data operations
        "json_load": 0.1,
        "json_save": 0.1,
        "pattern_search": 0.2,
    }

    def __init__(self):
        self.results: list[BenchmarkResult] = []

    def run(self, name: str, func: Callable[[], Any]) -> BenchmarkResult:
        """Run a benchmark and record result.

        Args:
            name: Benchmark name (must be in TARGETS)
            func: Function to benchmark (no arguments)

        Returns:
            BenchmarkResult with timing information

        Examples:
            >>> bench = Benchmark()
            >>> def quick_task():
            ...     return sum(range(100))
            >>> result = bench.run("test", quick_task)
            >>> result.duration < 1.0
            True
        """
        start = time.perf_counter()
        func()
        duration = time.perf_counter() - start

        target = self.TARGETS.get(name, float("inf"))
        result = BenchmarkResult(name, duration, target)
        self.results.append(result)

        return result

    def report(self) -> str:
        """Generate benchmark report.

        Returns:
            Formatted report string with all results

        Examples:
            >>> bench = Benchmark()
            >>> _ = bench.run("test", lambda: None)
            >>> report = bench.report()
            >>> "パフォーマンスベンチマークレポート" in report
            True
        """
        lines = ["パフォーマンスベンチマークレポート", "=" * 50]

        for result in self.results:
            lines.append(str(result))

        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        lines.append(f"\n合格: {passed}/{total}")

        return "\n".join(lines)

    def save(self, path: Path) -> None:
        """Save results to JSON file.

        Args:
            path: Output file path

        Examples:
            >>> import tempfile
            >>> bench = Benchmark()
            >>> _ = bench.run("test", lambda: None)
            >>> with tempfile.NamedTemporaryFile(
            ...     mode="w", suffix=".json", delete=False
            ... ) as f:
            ...     temp_path = Path(f.name)
            >>> bench.save(temp_path)
            >>> data = json.loads(temp_path.read_text())
            >>> "timestamp" in data
            True
            >>> "results" in data
            True
            >>> temp_path.unlink()
        """
        data = {
            "timestamp": time.time(),
            "results": [
                {
                    "name": r.name,
                    "duration": r.duration,
                    "target": r.target,
                    "passed": r.passed,
                }
                for r in self.results
            ],
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def create_test_data(base_dir: Path, num_patterns: int = 100) -> dict[str, Any]:
    """Create test data for benchmarking.

    Args:
        base_dir: Base directory for test files
        num_patterns: Number of patterns to create

    Returns:
        Dictionary with test data paths and content
    """
    # Create directories
    tracker_file = base_dir / "pattern_tracker.json"
    archive_dir = base_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    # Generate test patterns
    patterns = {}
    for i in range(num_patterns):
        pattern_text = f"test pattern {i}"
        patterns[pattern_text] = {
            "count": i + 1,
            "last_seen": f"2026-01-{(i % 28) + 1:02d}",
            "sessions": [f"2026-01-{(j % 28) + 1:02d}" for j in range(i % 5 + 1)],
            "promoted": False,
            "contexts": [f"context {i}"],
        }

    # Create cooccurrences
    cooccurrences = []
    for i in range(min(num_patterns // 2, 50)):
        cooccurrences.append(
            {
                "words": [f"test pattern {i}", f"test pattern {i+1}"],
                "count": i + 1,
            }
        )

    # Write tracker file
    tracker_data = {
        "patterns": patterns,
        "cooccurrences": cooccurrences,
        "promotion_candidates": [],
    }
    tracker_file.write_text(json.dumps(tracker_data, indent=2, ensure_ascii=False))

    # Create archive files
    for i in range(10):
        archive_file = archive_dir / f"2026-01-{i+1:02d}.md"
        content_lines = [
            f"test pattern {j}"
            for j in range(i * 10, min((i + 1) * 10, num_patterns))
        ]
        archive_file.write_text("\n".join(content_lines))

    return {
        "tracker_file": tracker_file,
        "archive_dir": archive_dir,
        "num_patterns": num_patterns,
    }


def benchmark_current_implementation() -> Benchmark:
    """Benchmark current implementation (v1).

    Returns:
        Benchmark object with all results

    Note:
        Creates temporary test data and measures actual v1 operations.
        All test data is cleaned up after benchmarking.
    """
    import shutil
    import tempfile

    bench = Benchmark()

    # Create temporary directory for test data
    temp_dir = Path(tempfile.mkdtemp(prefix="as_you_bench_"))

    try:
        # Create test data
        test_data = create_test_data(temp_dir, num_patterns=100)

        # Benchmark: JSON load
        def json_load():
            json.loads(test_data["tracker_file"].read_text())

        bench.run("json_load", json_load)

        # Benchmark: JSON save
        def json_save():
            data = json.loads(test_data["tracker_file"].read_text())
            test_data["tracker_file"].write_text(json.dumps(data, indent=2))

        bench.run("json_save", json_save)

        # Benchmark: TF-IDF calculation (100 patterns)
        def tfidf_calculation():
            from as_you.lib.tfidf_calculator import calculate_tfidf_single_pass

            data = json.loads(test_data["tracker_file"].read_text())
            patterns = data.get("patterns", {})
            calculate_tfidf_single_pass(patterns, test_data["archive_dir"])

        bench.run("tfidf_calculation_100", tfidf_calculation)

        # Benchmark: PMI calculation (100 patterns)
        def pmi_calculation():
            from as_you.lib.pmi_calculator import count_total_patterns

            count_total_patterns(test_data["archive_dir"])

        bench.run("pmi_calculation_100", pmi_calculation)

        # Benchmark: Score calculation
        def score_calculation():
            from as_you.lib.score_calculator import UnifiedScoreCalculator

            calc = UnifiedScoreCalculator(
                test_data["tracker_file"], test_data["archive_dir"]
            )
            calc.calculate_all_scores()

        bench.run("score_calculation", score_calculation)

        # Benchmark: Pattern search
        def pattern_search():
            data = json.loads(test_data["tracker_file"].read_text())
            patterns = data.get("patterns", {})
            # Simulate searching for top patterns
            sorted_patterns = sorted(
                patterns.items(), key=lambda x: x[1].get("count", 0), reverse=True
            )
            top_10 = sorted_patterns[:10]
            return top_10

        bench.run("pattern_search", pattern_search)

    finally:
        # Cleanup temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)

    return bench


def main():
    """CLI entry point for benchmarks."""
    print("実行中: as-you パフォーマンスベンチマーク")
    print("-" * 50)

    bench = benchmark_current_implementation()

    print(bench.report())

    # Save results
    output_path = Path("tests/performance/baseline_v1.json")
    bench.save(output_path)
    print(f"\n結果を保存: {output_path}")

    # Exit with error if any benchmark failed
    if not all(r.passed for r in bench.results):
        sys.exit(1)


if __name__ == "__main__":
    import doctest

    # Check if running doctests
    if "--test" in sys.argv:
        print("Running performance benchmarks doctests:")
        results = doctest.testmod(verbose=("--verbose" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
