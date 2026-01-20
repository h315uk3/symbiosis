#!/usr/bin/env python3
"""
Parameter Optimization via Grid Search

Implements Grid Search parameter optimization to find optimal log_base
and other tunable parameters for the Bayesian belief system.

Theoretical Foundation:
- Grid Search: Exhaustive search over parameter space
- Cross-validation: Session-level evaluation with train/test splits
- Metric: Average information gain per question (bits)

Design Constraints:
- Pure stdlib implementation (no scikit-learn or scipy.optimize)
- Brute-force acceptable for small parameter spaces
- Text-based reporting (no matplotlib)

References:
- Issue #41: Phase 2-B (Grid Search parameter optimization)
- Issue #40: Phase 2-A (Statistical analysis integration)
"""

import json
import math
import statistics
from pathlib import Path
from typing import Any

from .question_feedback_manager import QuestionFeedbackManager, WithMeConfig


class SimpleParameterTuner:
    """
    Grid Search parameter optimization for Bayesian belief system.

    Optimizes log_base parameter by evaluating average information gain
    across completed sessions using cross-validation.

    Examples:
        >>> # Create tuner with feedback data
        >>> config = WithMeConfig.from_environment()
        >>> tuner = SimpleParameterTuner(config.feedback_file)

        >>> # Run Grid Search over log_base values
        >>> results = tuner.grid_search(
        ...     param_name="log_base",
        ...     param_values=[1.5, 2.0, 3.0, 5.0, 10.0]
        ... )  # doctest: +SKIP

        >>> # Get optimal parameter
        >>> optimal = tuner.get_optimal_parameters()  # doctest: +SKIP
        >>> optimal["log_base"]  # doctest: +SKIP
        2.0
    """

    def __init__(self, feedback_file: Path):
        """
        Initialize tuner with feedback data.

        Args:
            feedback_file: Path to feedback JSON file
        """
        self.feedback_file = feedback_file
        self.manager = QuestionFeedbackManager(feedback_file)
        self.results: dict[str, list[dict[str, Any]]] = {}
        self.optimal_params: dict[str, float] = {}

    def grid_search(
        self, param_name: str, param_values: list[float], cv_folds: int = 5
    ) -> list[dict[str, Any]]:
        """
        Perform Grid Search over parameter values.

        Uses cross-validation to evaluate each parameter value by:
        1. Splitting sessions into train/test folds
        2. Simulating belief updates with parameter value
        3. Measuring average information gain per question
        4. Aggregating results across folds

        Args:
            param_name: Parameter name (e.g., "log_base")
            param_values: List of values to evaluate
            cv_folds: Number of cross-validation folds (default 5)

        Returns:
            List of evaluation results, sorted by mean score (descending)

        Examples:
            >>> # Mock evaluation without real session data
            >>> config = WithMeConfig.from_environment()
            >>> tuner = SimpleParameterTuner(config.feedback_file)
            >>> # Simulate grid search results
            >>> results = [
            ...     {"param_value": 2.0, "mean_score": 0.85, "std_score": 0.12},
            ...     {"param_value": 3.0, "mean_score": 0.78, "std_score": 0.15},
            ... ]
            >>> results[0]["mean_score"] > results[1]["mean_score"]
            True
        """
        if not self.feedback_file.exists():
            return []

        # Get completed sessions
        all_sessions = self.manager.get_recent_sessions(limit=100)
        completed_sessions = [s for s in all_sessions if s.get("completed_at")]

        if len(completed_sessions) < cv_folds:
            # Not enough data for cross-validation
            return []

        # Grid Search: evaluate each parameter value
        grid_results = []

        for param_value in param_values:
            # Cross-validation: split sessions into folds
            fold_scores = []
            fold_size = len(completed_sessions) // cv_folds

            for fold_idx in range(cv_folds):
                # Test fold: current fold
                test_start = fold_idx * fold_size
                test_end = (
                    test_start + fold_size
                    if fold_idx < cv_folds - 1
                    else len(completed_sessions)
                )
                test_sessions = completed_sessions[test_start:test_end]

                # Evaluate parameter on test fold
                fold_score = self._evaluate_parameter(
                    param_name, param_value, test_sessions
                )
                fold_scores.append(fold_score)

            # Aggregate cross-validation scores
            mean_score = statistics.mean(fold_scores) if fold_scores else 0.0
            std_score = (
                statistics.stdev(fold_scores) if len(fold_scores) > 1 else 0.0
            )

            grid_results.append(
                {
                    "param_name": param_name,
                    "param_value": param_value,
                    "mean_score": round(mean_score, 4),
                    "std_score": round(std_score, 4),
                    "fold_scores": [round(s, 4) for s in fold_scores],
                }
            )

        # Sort by mean score (descending)
        grid_results.sort(key=lambda x: x["mean_score"], reverse=True)

        # Store results
        self.results[param_name] = grid_results

        # Update optimal parameters
        if grid_results:
            self.optimal_params[param_name] = grid_results[0]["param_value"]

        return grid_results

    def _evaluate_parameter(
        self, param_name: str, param_value: float, sessions: list[dict]
    ) -> float:
        """
        Evaluate parameter value on session data.

        Simulates belief updates using parameter value and calculates
        average information gain per question.

        Args:
            param_name: Parameter name (e.g., "log_base")
            param_value: Parameter value to evaluate
            sessions: List of session data

        Returns:
            Average information gain per question (bits)

        Examples:
            >>> config = WithMeConfig.from_environment()
            >>> tuner = SimpleParameterTuner(config.feedback_file)
            >>> # Mock session with information gain
            >>> sessions = [
            ...     {"questions": [{"info_gain": 0.5}, {"info_gain": 0.8}]},
            ...     {"questions": [{"info_gain": 0.6}]},
            ... ]
            >>> score = tuner._evaluate_parameter("log_base", 2.0, sessions)
            >>> 0.5 <= score <= 0.8  # Average of [0.5, 0.8, 0.6]
            True
        """
        if param_name != "log_base":
            # Only log_base supported in v0.3.0
            return 0.0

        # Collect information gains from all questions in sessions
        all_info_gains = []

        for session in sessions:
            questions = session.get("questions", [])
            for question in questions:
                # Use recorded info_gain if available
                if "info_gain" in question:
                    info_gain = question["info_gain"]
                    # Adjust for different log base
                    # H_new = H_old * log_new(2) = H_old / log_2(new_base)
                    adjusted_gain = info_gain / math.log2(param_value)
                    all_info_gains.append(adjusted_gain)

        # Calculate average information gain per question
        if all_info_gains:
            return statistics.mean(all_info_gains)
        return 0.0

    def sensitivity_analysis(self, param_name: str) -> dict[str, Any]:
        """
        Analyze parameter sensitivity from grid search results.

        Calculates:
        - Score range (max - min)
        - Score variance
        - Parameter impact ranking

        Args:
            param_name: Parameter name

        Returns:
            Sensitivity analysis results

        Examples:
            >>> config = WithMeConfig.from_environment()
            >>> tuner = SimpleParameterTuner(config.feedback_file)
            >>> # Mock grid search results
            >>> tuner.results["log_base"] = [
            ...     {"param_value": 2.0, "mean_score": 0.85, "std_score": 0.10},
            ...     {"param_value": 3.0, "mean_score": 0.75, "std_score": 0.12},
            ...     {"param_value": 5.0, "mean_score": 0.60, "std_score": 0.15},
            ... ]
            >>> analysis = tuner.sensitivity_analysis("log_base")
            >>> analysis["score_range"]
            0.25
            >>> analysis["best_value"]
            2.0
        """
        if param_name not in self.results:
            return {}

        results = self.results[param_name]
        if not results:
            return {}

        scores = [r["mean_score"] for r in results]
        param_values = [r["param_value"] for r in results]

        # Score statistics
        score_range = max(scores) - min(scores)
        score_variance = statistics.variance(scores) if len(scores) > 1 else 0.0

        # Best parameter
        best_result = results[0]  # Already sorted by mean_score

        return {
            "param_name": param_name,
            "score_range": round(score_range, 4),
            "score_variance": round(score_variance, 6),
            "best_value": best_result["param_value"],
            "best_score": best_result["mean_score"],
            "best_std": best_result["std_score"],
            "tested_values": param_values,
            "all_scores": scores,
        }

    def generate_report(self) -> str:
        """
        Generate text-based parameter optimization report.

        Returns:
            Formatted report string

        Examples:
            >>> config = WithMeConfig.from_environment()
            >>> tuner = SimpleParameterTuner(config.feedback_file)
            >>> tuner.results["log_base"] = [
            ...     {"param_value": 2.0, "mean_score": 0.85, "std_score": 0.10},
            ...     {"param_value": 3.0, "mean_score": 0.75, "std_score": 0.12},
            ... ]
            >>> tuner.optimal_params["log_base"] = 2.0
            >>> report = tuner.generate_report()
            >>> "log_base" in report
            True
            >>> "2.0" in report
            True
        """
        lines = []

        lines.append("=" * 60)
        lines.append("Parameter Optimization Report (Grid Search)")
        lines.append("=" * 60)
        lines.append("")

        if not self.results:
            lines.append("No optimization results available.")
            return "\n".join(lines)

        # Optimal parameters summary
        lines.append("Optimal Parameters:")
        lines.append("-" * 40)
        for param, value in self.optimal_params.items():
            lines.append(f"  {param}: {value}")
        lines.append("")

        # Detailed results per parameter
        for param_name, results in self.results.items():
            lines.append(f"Parameter: {param_name}")
            lines.append("-" * 40)

            # Grid search results table
            lines.append(
                f"{'Value':<10} {'Mean Score':<12} {'Std Dev':<12} {'Result':<10}"
            )
            lines.append("-" * 40)

            for i, result in enumerate(results):
                value_str = f"{result['param_value']:<10.2f}"
                mean_str = f"{result['mean_score']:<12.4f}"
                std_str = f"{result['std_score']:<12.4f}"
                marker = "BEST" if i == 0 else ""
                lines.append(f"{value_str} {mean_str} {std_str} {marker}")

            lines.append("")

            # Sensitivity analysis
            analysis = self.sensitivity_analysis(param_name)
            if analysis:
                lines.append("Sensitivity Analysis:")
                lines.append(f"  Score Range:    {analysis['score_range']:.4f}")
                lines.append(f"  Score Variance: {analysis['score_variance']:.6f}")
                lines.append(
                    f"  Impact: {'HIGH' if analysis['score_range'] > 0.1 else 'MODERATE' if analysis['score_range'] > 0.05 else 'LOW'}"
                )

            lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)

    def save_optimal_parameters(self, output_file: Path) -> None:
        """
        Save optimal parameters to JSON configuration file.

        Args:
            output_file: Path to output JSON file

        Examples:
            >>> import tempfile
            >>> config = WithMeConfig.from_environment()
            >>> tuner = SimpleParameterTuner(config.feedback_file)
            >>> tuner.optimal_params["log_base"] = 2.0
            >>> with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            ...     output_path = Path(f.name)
            >>> tuner.save_optimal_parameters(output_path)
            >>> data = json.loads(output_path.read_text())
            >>> data["optimal_parameters"]["log_base"]
            2.0
            >>> output_path.unlink()  # Clean up
        """
        # Ensure parent directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Save parameters with metadata
        config = {
            "optimal_parameters": self.optimal_params,
            "metadata": {
                "version": "0.3.0",
                "optimization_method": "grid_search",
                "parameters_optimized": list(self.optimal_params.keys()),
            },
        }

        output_file.write_text(json.dumps(config, indent=2))

    def get_optimal_parameters(self) -> dict[str, float]:
        """
        Get dictionary of optimal parameters.

        Returns:
            Dictionary mapping parameter names to optimal values

        Examples:
            >>> config = WithMeConfig.from_environment()
            >>> tuner = SimpleParameterTuner(config.feedback_file)
            >>> tuner.optimal_params["log_base"] = 2.5
            >>> params = tuner.get_optimal_parameters()
            >>> params["log_base"]
            2.5
        """
        return self.optimal_params.copy()


def main():
    """CLI interface for parameter tuning"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python parameter_tuner.py <command>")
        print("\nCommands:")
        print("  optimize  - Run Grid Search optimization")
        print("  report    - Display optimization report")
        print("  test      - Run doctests")
        sys.exit(1)

    command = sys.argv[1]

    if command == "optimize":
        # Run Grid Search optimization
        config = WithMeConfig.from_environment()
        tuner = SimpleParameterTuner(config.feedback_file)

        print("Running Grid Search optimization...")
        print("Parameter: log_base")
        print("Range: 1.5 to 10.0")
        print()

        # Define parameter grid
        log_base_values = [1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.0, 10.0]

        # Run Grid Search
        results = tuner.grid_search("log_base", log_base_values, cv_folds=5)

        if not results:
            print("Insufficient session data for optimization.")
            print("At least 5 completed sessions required.")
            sys.exit(1)

        # Display report
        print(tuner.generate_report())

        # Save optimal parameters
        output_file = config.feedback_file.parent / "optimal_parameters.json"
        tuner.save_optimal_parameters(output_file)
        print(f"\nOptimal parameters saved to: {output_file}")

    elif command == "report":
        # Display existing optimization report
        config = WithMeConfig.from_environment()
        param_file = config.feedback_file.parent / "optimal_parameters.json"

        if not param_file.exists():
            print("No optimization results found.")
            print("Run 'python parameter_tuner.py optimize' first.")
            sys.exit(1)

        data = json.loads(param_file.read_text())
        print("Optimal Parameters:")
        print(json.dumps(data["optimal_parameters"], indent=2))

    elif command == "test":
        import doctest

        print("Running doctests...")
        result = doctest.testmod()
        if result.failed == 0:
            print("✓ All doctests passed")
        else:
            print(f"✗ {result.failed} doctest(s) failed")
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
