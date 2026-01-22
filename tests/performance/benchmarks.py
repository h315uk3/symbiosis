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


def benchmark_current_implementation() -> Benchmark:
    """Benchmark current implementation (v1).

    Returns:
        Benchmark object with all results

    Note:
        Actual benchmark implementations will be added as we measure
        the current system performance. This is a placeholder for the
        framework structure.
    """
    bench = Benchmark()

    # TODO: Add actual benchmarks
    # bench.run("note_add", lambda: ...)
    # bench.run("pattern_tracker_update", lambda: ...)

    # Placeholder: framework test
    bench.run("test", lambda: time.sleep(0.001))

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
