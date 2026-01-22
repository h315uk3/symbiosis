#!/usr/bin/env python3
"""A/B testing framework for algorithm validation.

This module provides infrastructure for comparing algorithm variants
(e.g., BM25 vs TF-IDF) on real data with multiple metrics.

Usage:
    python3 tests/ab_testing/framework.py
    python3 tests/ab_testing/framework.py --verbose
"""

import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class AlgorithmVariant:
    """Algorithm variant for testing.

    Examples:
        >>> def simple_scorer(data: list[str]) -> list[float]:
        ...     return [len(s) for s in data]
        >>> variant = AlgorithmVariant("Length", simple_scorer, {})
        >>> variant.name
        'Length'
        >>> variant.config
        {}
    """

    name: str
    implementation: Callable[[list[Any]], list[float]]
    config: dict[str, Any]


@dataclass
class TestResult:
    """A/B test result for a single metric.

    Examples:
        >>> result = TestResult("BM25", "accuracy", 0.85, True)
        >>> result.variant_name
        'BM25'
        >>> result.better_than_baseline
        True
        >>> result = TestResult("Slow", "speed", 0.5, False)
        >>> result.better_than_baseline
        False
    """

    variant_name: str
    metric_name: str
    value: float
    better_than_baseline: bool

    def __repr__(self) -> str:
        status = "✓" if self.better_than_baseline else "✗"
        return f"{status} {self.variant_name} - {self.metric_name}: {self.value:.4f}"


class ABTest:
    """A/B testing framework for comparing algorithm variants.

    Examples:
        >>> def baseline_algo(data: list[str]) -> list[float]:
        ...     return [len(s) for s in data]
        >>> baseline = AlgorithmVariant("Baseline", baseline_algo, {})
        >>> test = ABTest("Length Test", baseline)
        >>> test.test_name
        'Length Test'
        >>> len(test.variants)
        0
    """

    def __init__(self, test_name: str, baseline: AlgorithmVariant):
        self.test_name = test_name
        self.baseline = baseline
        self.variants: list[AlgorithmVariant] = []
        self.results: list[TestResult] = []

    def add_variant(self, variant: AlgorithmVariant) -> None:
        """Add a variant to test.

        Args:
            variant: Algorithm variant to test

        Examples:
            >>> def baseline_algo(data: list[str]) -> list[float]:
            ...     return [1.0 for _ in data]
            >>> def variant_algo(data: list[str]) -> list[float]:
            ...     return [2.0 for _ in data]
            >>> baseline = AlgorithmVariant("Baseline", baseline_algo, {})
            >>> test = ABTest("Test", baseline)
            >>> test.add_variant(AlgorithmVariant("Variant", variant_algo, {}))
            >>> len(test.variants)
            1
        """
        self.variants.append(variant)

    def run(
        self,
        test_data: list[Any],
        metrics: dict[str, Callable[[list[float]], float]],
    ) -> None:
        """Run A/B test on test data.

        Args:
            test_data: Data to test algorithms on
            metrics: Dictionary of metric name to metric function

        Examples:
            >>> def baseline_algo(data: list[str]) -> list[float]:
            ...     return [1.0 for _ in data]
            >>> def variant_algo(data: list[str]) -> list[float]:
            ...     return [2.0 for _ in data]
            >>> def mean_metric(scores: list[float]) -> float:
            ...     return sum(scores) / len(scores)
            >>> baseline = AlgorithmVariant("Baseline", baseline_algo, {})
            >>> test = ABTest("Test", baseline)
            >>> test.add_variant(AlgorithmVariant("Variant", variant_algo, {}))
            >>> test.run(["a", "b", "c"], {"mean": mean_metric})
            >>> len(test.results)
            1
            >>> test.results[0].variant_name
            'Variant'
        """
        # Run baseline
        baseline_scores = self.baseline.implementation(test_data)
        baseline_metrics = {
            name: func(baseline_scores) for name, func in metrics.items()
        }

        # Run each variant
        for variant in self.variants:
            variant_scores = variant.implementation(test_data)
            variant_metrics = {
                name: func(variant_scores) for name, func in metrics.items()
            }

            # Compare to baseline
            for metric_name in metrics:
                result = TestResult(
                    variant_name=variant.name,
                    metric_name=metric_name,
                    value=variant_metrics[metric_name],
                    better_than_baseline=variant_metrics[metric_name]
                    > baseline_metrics[metric_name],
                )
                self.results.append(result)

    def report(self) -> str:
        """Generate A/B test report.

        Returns:
            Formatted report string

        Examples:
            >>> def baseline_algo(data: list[str]) -> list[float]:
            ...     return [1.0 for _ in data]
            >>> def variant_algo(data: list[str]) -> list[float]:
            ...     return [2.0 for _ in data]
            >>> def mean_metric(scores: list[float]) -> float:
            ...     return sum(scores) / len(scores)
            >>> baseline = AlgorithmVariant("Baseline", baseline_algo, {})
            >>> test = ABTest("Test", baseline)
            >>> test.add_variant(AlgorithmVariant("Variant", variant_algo, {}))
            >>> test.run(["a", "b", "c"], {"mean": mean_metric})
            >>> report = test.report()
            >>> "A/Bテストレポート: Test" in report
            True
            >>> "Variant" in report
            True
        """
        lines = [f"A/Bテストレポート: {self.test_name}", "=" * 60]

        if not self.results:
            lines.append("結果がありません。まずrun()を実行してください。")
        else:
            for result in self.results:
                lines.append(str(result))

        return "\n".join(lines)

    def save(self, path: Path) -> None:
        """Save results to JSON file.

        Args:
            path: Output file path

        Examples:
            >>> import tempfile
            >>> def baseline_algo(data: list[str]) -> list[float]:
            ...     return [1.0 for _ in data]
            >>> def mean_metric(scores: list[float]) -> float:
            ...     return sum(scores) / len(scores)
            >>> baseline = AlgorithmVariant("Baseline", baseline_algo, {})
            >>> test = ABTest("Test", baseline)
            >>> test.run(["a"], {"mean": mean_metric})
            >>> with tempfile.NamedTemporaryFile(
            ...     mode="w", suffix=".json", delete=False
            ... ) as f:
            ...     temp_path = Path(f.name)
            >>> test.save(temp_path)
            >>> data = json.loads(temp_path.read_text())
            >>> data["test_name"]
            'Test'
            >>> temp_path.unlink()
        """
        data = {
            "test_name": self.test_name,
            "baseline": self.baseline.name,
            "results": [
                {
                    "variant": r.variant_name,
                    "metric": r.metric_name,
                    "value": r.value,
                    "better": r.better_than_baseline,
                }
                for r in self.results
            ],
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def example_test() -> ABTest:
    """Example A/B test setup (framework demonstration).

    Returns:
        Configured ABTest instance

    Note:
        This is a placeholder. Real tests will compare TF-IDF vs BM25
        on actual pattern data.
    """

    def baseline_algo(data: list[str]) -> list[float]:
        """Simple baseline: return string lengths."""
        return [float(len(s)) for s in data]

    def variant_algo(data: list[str]) -> list[float]:
        """Simple variant: return string lengths * 2."""
        return [float(len(s) * 2) for s in data]

    baseline = AlgorithmVariant("Baseline", baseline_algo, {})
    test = ABTest("Example Test", baseline)
    test.add_variant(AlgorithmVariant("Variant", variant_algo, {}))

    return test


def main():
    """CLI entry point for A/B tests."""
    print("実行中: A/Bテストフレームワーク例")
    print("-" * 50)

    test = example_test()

    # Example metrics
    def mean_score(scores: list[float]) -> float:
        return sum(scores) / len(scores) if scores else 0.0

    def max_score(scores: list[float]) -> float:
        return max(scores) if scores else 0.0

    test.run(["test", "example", "data"], {"mean": mean_score, "max": max_score})

    print(test.report())

    # Save results
    output_path = Path("tests/ab_testing/example_results.json")
    test.save(output_path)
    print(f"\n結果を保存: {output_path}")


if __name__ == "__main__":
    import doctest

    # Check if running doctests
    if "--test" in __import__("sys").argv:
        print("Running A/B testing framework doctests:")
        results = doctest.testmod(verbose=("--verbose" in __import__("sys").argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            __import__("sys").exit(1)
    else:
        main()
