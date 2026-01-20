#!/usr/bin/env python3
"""
Question statistics collector for with-me plugin.
Collects and outputs JSON statistics about question effectiveness.

Enhanced with BasicStats class for statistical analysis using Python standard library.
"""

import math
import statistics
import sys
from collections import Counter
from typing import Any

from .question_feedback_manager import QuestionFeedbackManager, WithMeConfig


class BasicStats:
    """
    Statistical analysis using Python standard library.

    Provides efficiency metrics, distribution analysis, and correlation calculations
    without external dependencies (NumPy, SciPy, etc.).

    Examples:
        >>> stats = BasicStats([0.7, 0.8, 0.9, 0.85, 0.75])
        >>> result = stats.calculate_efficiency_stats()
        >>> result['mean'] > 0.7 and result['mean'] < 0.9
        True
        >>> result['median'] == 0.8
        True
        >>> len(result['distribution']) <= 5
        True
    """

    def __init__(self, values: list[float]):
        """
        Initialize with numeric values.

        Args:
            values: List of numeric values (e.g., efficiency scores)
        """
        self.values = [v for v in values if v is not None]

    def calculate_efficiency_stats(self) -> dict[str, Any]:
        """
        Calculate statistical measures for efficiency metrics.

        Returns:
            Dictionary with mean, median, std_dev, and distribution

        Examples:
            >>> stats = BasicStats([0.5, 0.6, 0.7, 0.8, 0.9])
            >>> result = stats.calculate_efficiency_stats()
            >>> result['mean']
            0.7
            >>> result['median']
            0.7
        """
        if not self.values:
            return {
                "mean": 0.0,
                "median": 0.0,
                "std_dev": 0.0,
                "distribution": {},
                "min": 0.0,
                "max": 0.0,
            }

        return {
            "mean": statistics.mean(self.values),
            "median": statistics.median(self.values),
            "std_dev": statistics.stdev(self.values) if len(self.values) > 1 else 0.0,
            "distribution": self._create_histogram(5),
            "min": min(self.values),
            "max": max(self.values),
        }

    def _create_histogram(self, bins: int) -> dict[str, int]:
        """
        Create histogram with specified number of bins using collections.Counter.

        Args:
            bins: Number of bins (default 5)

        Returns:
            Dictionary mapping bin range to count

        Examples:
            >>> stats = BasicStats([0.1, 0.3, 0.5, 0.7, 0.9])
            >>> hist = stats._create_histogram(5)
            >>> len(hist) <= 5
            True
        """
        if not self.values:
            return {}

        min_val = min(self.values)
        max_val = max(self.values)

        # Handle single value case
        if min_val == max_val:
            return {f"{min_val:.1f}": len(self.values)}

        bin_width = (max_val - min_val) / bins

        # Assign each value to a bin label using collections.Counter
        bin_labels = []
        for value in self.values:
            # Determine which bin this value belongs to
            bin_index = min(int((value - min_val) / bin_width), bins - 1)
            bin_start = min_val + bin_index * bin_width
            bin_end = bin_start + bin_width

            # Format bin label
            if bin_index == bins - 1:
                label = f"{bin_start:.1f}-{max_val:.1f}"
            else:
                label = f"{bin_start:.1f}-{bin_end:.1f}"

            bin_labels.append(label)

        # Use Counter to count occurrences (Issue #40 specification)
        histogram = Counter(bin_labels)

        # Convert Counter to dict for consistent return type
        return dict(histogram)


def calculate_pearson_correlation(x_values: list[float], y_values: list[float]) -> dict[str, Any]:
    """
    Calculate Pearson correlation coefficient manually.

    Formula: r = Σ((xi - x̄)(yi - ȳ)) / sqrt(Σ(xi - x̄)² × Σ(yi - ȳ)²)

    Args:
        x_values: First variable values
        y_values: Second variable values

    Returns:
        Dictionary with correlation coefficient and interpretation

    Examples:
        >>> result = calculate_pearson_correlation([1, 2, 3, 4, 5], [2, 4, 6, 8, 10])
        >>> result['correlation']
        1.0
        >>> 'positive' in result['interpretation']
        True

        >>> result = calculate_pearson_correlation([1, 2, 3], [3, 2, 1])
        >>> result['correlation']
        -1.0
        >>> 'negative' in result['interpretation']
        True
    """
    if len(x_values) != len(y_values) or len(x_values) < 2:
        return {"correlation": 0.0, "interpretation": "insufficient data"}

    # Calculate means
    x_mean = statistics.mean(x_values)
    y_mean = statistics.mean(y_values)

    # Calculate covariance and standard deviations
    covariance = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values, strict=True))
    x_std = math.sqrt(sum((x - x_mean) ** 2 for x in x_values))
    y_std = math.sqrt(sum((y - y_mean) ** 2 for y in y_values))

    # Avoid division by zero
    if x_std == 0 or y_std == 0:
        return {"correlation": 0.0, "interpretation": "no variance"}

    # Calculate Pearson correlation coefficient
    r = covariance / (x_std * y_std)

    # Interpret correlation strength
    abs_r = abs(r)
    if abs_r >= 0.9:
        strength = "perfect" if abs_r == 1.0 else "very strong"
    elif abs_r >= 0.7:
        strength = "strong"
    elif abs_r >= 0.5:
        strength = "moderate"
    elif abs_r >= 0.3:
        strength = "weak"
    else:
        strength = "very weak"

    direction = "positive" if r >= 0 else "negative"
    interpretation = f"{strength} {direction}"

    return {"correlation": round(r, 3), "interpretation": interpretation}


def entropy_reduction_by_dimension(session_data: dict) -> dict[str, dict[str, float]]:
    """
    Analyze entropy reduction per dimension from session data.

    Args:
        session_data: Session with dimension_beliefs_before and dimension_beliefs_after

    Returns:
        Dictionary mapping dimension to entropy reduction metrics

    Examples:
        >>> session = {
        ...     "dimension_beliefs_before": {
        ...         "purpose": {"entropy": 2.0},
        ...         "data": {"entropy": 2.0}
        ...     },
        ...     "dimension_beliefs_after": {
        ...         "purpose": {"entropy": 0.5},
        ...         "data": {"entropy": 1.0}
        ...     }
        ... }
        >>> result = entropy_reduction_by_dimension(session)
        >>> result["purpose"]["reduction"]
        1.5
        >>> result["purpose"]["percent"]
        75.0
    """
    beliefs_before = session_data.get("dimension_beliefs_before", {})
    beliefs_after = session_data.get("dimension_beliefs_after", {})

    reduction_stats = {}

    for dimension in beliefs_before:
        if dimension in beliefs_after:
            h_before = beliefs_before[dimension].get("entropy", 0.0)
            h_after = beliefs_after[dimension].get("entropy", 0.0)
            reduction = h_before - h_after
            percent = (reduction / h_before * 100) if h_before > 0 else 0.0

            reduction_stats[dimension] = {
                "entropy_before": round(h_before, 2),
                "entropy_after": round(h_after, 2),
                "reduction": round(reduction, 2),
                "percent": round(percent, 1),
            }

    return reduction_stats


def generate_ascii_report(stats: dict) -> str:
    """
    Generate ASCII table report from statistics.

    Args:
        stats: Statistics dictionary with overview and entropy_reduction

    Returns:
        Formatted ASCII table string

    Examples:
        >>> stats = {
        ...     "overview": {"efficiency": {"mean": 0.82, "median": 0.85, "std_dev": 0.15, "min": 0.60, "max": 0.95}},
        ...     "entropy_reduction": {
        ...         "purpose": {"entropy_before": 2.0, "entropy_after": 0.5, "reduction": 1.5, "percent": 75.0}
        ...     }
        ... }
        >>> report = generate_ascii_report(stats)
        >>> "Session Efficiency" in report
        True
        >>> "purpose" in report
        True
    """
    lines = []

    # Header
    lines.append("╔═══════════════════════════════════════════════════════╗")
    lines.append("║           Session Efficiency Analysis                ║")
    lines.append("╠═══════════════════════════════════════════════════════╣")

    # Efficiency stats
    if "overview" in stats and "efficiency" in stats["overview"]:
        eff = stats["overview"]["efficiency"]
        lines.append(f"║ Mean Efficiency:     {eff['mean']:.2f} (±{eff['std_dev']:.2f})                   ║")
        lines.append(f"║ Median:              {eff['median']:.2f}                             ║")
        lines.append(f"║ Range:               {eff['min']:.2f} - {eff['max']:.2f}                      ║")

    lines.append("╚═══════════════════════════════════════════════════════╝")
    lines.append("")

    # Entropy reduction table
    if stats.get("entropy_reduction"):
        lines.append("Entropy Reduction by Dimension:")
        lines.append("┌──────────────┬─────────┬────────┬───────────┬─────────┐")
        lines.append("│ Dimension    │ Before  │ After  │ Reduction │ Percent │")
        lines.append("├──────────────┼─────────┼────────┼───────────┼─────────┤")

        for dim, data in stats["entropy_reduction"].items():
            dim_padded = dim.ljust(12)
            before = f"{data['entropy_before']:5.2f}"
            after = f"{data['entropy_after']:5.2f}"
            reduction = f"{data['reduction']:7.2f}"
            percent = f"{data['percent']:5.1f}%"
            lines.append(f"│ {dim_padded} │ {before} │ {after} │ {reduction} │ {percent} │")

        lines.append("└──────────────┴─────────┴────────┴───────────┴─────────┘")

    return "\n".join(lines)


def collect_stats() -> dict:
    """
    Collect question effectiveness statistics (legacy function).

    Returns:
        Statistics dictionary with overview, best questions, and dimension stats
    """
    try:
        config = WithMeConfig.from_environment()
        manager = QuestionFeedbackManager(config.feedback_file)

        if not config.feedback_file.exists():
            return {
                "overview": {
                    "total_sessions": 0,
                    "total_questions": 0,
                    "avg_questions_per_session": 0.0,
                },
                "best_questions": [],
                "dimension_stats": {},
                "recent_sessions": [],
            }

        statistics = manager.get_statistics()
        recent_sessions = manager.get_recent_sessions(limit=5)

        # Format recent sessions for display
        formatted_sessions = []
        for session in recent_sessions:
            if session.get("completed_at"):
                formatted_sessions.append(
                    {
                        "session_id": session["session_id"],
                        "questions_asked": len(session["questions"]),
                        "avg_reward": session["summary"]["avg_reward_per_question"]
                        if session.get("summary")
                        else 0,
                        "efficiency": session["summary"]["session_efficiency"]
                        if session.get("summary")
                        else 0,
                        "completed_at": session["completed_at"],
                    }
                )

        return {
            "overview": {
                "total_sessions": statistics.get("total_sessions", 0),
                "total_questions": statistics.get("total_questions", 0),
                "avg_questions_per_session": statistics.get(
                    "avg_questions_per_session", 0.0
                ),
            },
            "best_questions": statistics.get("best_questions", [])[:5],  # Top 5
            "dimension_stats": statistics.get("dimension_stats", {}),
            "recent_sessions": formatted_sessions,
        }

    except Exception as e:
        print(f"Error collecting stats: {e}", file=sys.stderr)
        return {
            "overview": {
                "total_sessions": 0,
                "total_questions": 0,
                "avg_questions_per_session": 0.0,
            },
            "best_questions": [],
            "dimension_stats": {},
            "recent_sessions": [],
            "error": str(e),
        }


def collect_enhanced_stats() -> dict:
    """
    Collect enhanced statistics with BasicStats analysis.

    Returns:
        Enhanced statistics dictionary with efficiency analysis,
        entropy reduction, correlations, and ASCII report (when data available)

    Examples:
        >>> # Always returns at least basic stats structure
        >>> stats = collect_enhanced_stats()
        >>> "overview" in stats
        True
        >>> "total_sessions" in stats["overview"]
        True
        >>> # ASCII report is string when present, or absent when no data
        >>> report = stats.get("ascii_report")
        >>> report is None or isinstance(report, str)
        True
    """
    # Get basic stats
    basic_stats = collect_stats()

    try:
        config = WithMeConfig.from_environment()
        manager = QuestionFeedbackManager(config.feedback_file)

        if not config.feedback_file.exists():
            return basic_stats

        # Get all completed sessions
        all_sessions = manager.get_recent_sessions(limit=100)
        completed_sessions = [s for s in all_sessions if s.get("completed_at")]

        if not completed_sessions:
            return basic_stats

        # Calculate efficiency stats
        efficiencies = [
            s["summary"].get("session_efficiency", 0)
            for s in completed_sessions
            if s.get("summary")
        ]

        if efficiencies:
            efficiency_stats = BasicStats(efficiencies).calculate_efficiency_stats()
            basic_stats["overview"]["efficiency"] = efficiency_stats

        # Calculate entropy reduction for recent sessions
        entropy_reductions = {}
        for session in completed_sessions[:10]:  # Last 10 sessions
            reduction = entropy_reduction_by_dimension(session)
            for dim, stats_data in reduction.items():
                if dim not in entropy_reductions:
                    entropy_reductions[dim] = {
                        "reductions": [],
                        "percents": [],
                    }
                entropy_reductions[dim]["reductions"].append(stats_data["reduction"])
                entropy_reductions[dim]["percents"].append(stats_data["percent"])

        # Average entropy reduction by dimension
        avg_entropy_reduction = {}
        for dim, data in entropy_reductions.items():
            avg_entropy_reduction[dim] = {
                "entropy_before": 2.0,  # Typical starting entropy
                "entropy_after": 2.0 - statistics.mean(data["reductions"]),
                "reduction": statistics.mean(data["reductions"]),
                "percent": statistics.mean(data["percents"]),
            }

        basic_stats["entropy_reduction"] = avg_entropy_reduction

        # Calculate correlations
        if len(completed_sessions) >= 3:
            question_counts = [len(s["questions"]) for s in completed_sessions]
            info_gains = [
                s["summary"].get("total_info_gain", 0)
                for s in completed_sessions
                if s.get("summary")
            ]

            if len(question_counts) == len(info_gains) and info_gains:
                corr = calculate_pearson_correlation(question_counts, info_gains)
                basic_stats["correlations"] = {
                    "questions_info_gain": corr
                }

        # Generate ASCII report
        basic_stats["ascii_report"] = generate_ascii_report(basic_stats)

    except Exception as e:
        print(f"Error in enhanced stats: {e}", file=sys.stderr)

    return basic_stats


if __name__ == "__main__":
    # For backward compatibility, delegate to CLI
    from with_me.cli.stats import main
    main()
