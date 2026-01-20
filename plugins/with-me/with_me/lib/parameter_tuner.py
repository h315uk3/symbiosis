#!/usr/bin/env python3
"""
Parameter Optimization via Grid Search

MIGRATION COMPLETE: Grid search algorithm has been moved to skill.
This module now serves as data collection and I/O proxy only.

Computation is delegated to:
- /with-me:grid-search skill: Exhaustive parameter space search
- /with-me:statistical-measures skill: Mean, median, std dev calculation
- /with-me:correlation skill: Cross-validation scoring

References:
- Issue #37: Claude Computational Engine architecture
- Skills: plugins/with-me/skills/{grid-search,statistical-measures,correlation}
"""

import sys
from pathlib import Path
from typing import Any

from .question_feedback_manager import QuestionFeedbackManager, WithMeConfig


def collect_parameter_data() -> dict[str, Any]:
    """
    Collect raw session data for parameter optimization.

    Returns aggregated data without performing grid search.
    Use Claude with /with-me:grid-search skill for optimization.

    Returns:
        Dictionary with raw session data and parameter ranges

    Examples:
        >>> # Mock example without actual feedback file
        >>> data = {"sessions": [], "parameter_ranges": {}}
        >>> "sessions" in data
        True
    """
    config = WithMeConfig.from_environment()
    manager = QuestionFeedbackManager(config.feedback_file)

    if not config.feedback_file.exists():
        return {
            "sessions": [],
            "parameter_ranges": {},
            "note": "No feedback data available for optimization",
        }

    feedback = manager.feedback
    sessions = feedback.get("sessions", [])

    # Define parameter ranges for optimization
    parameter_ranges = {
        "convergence_threshold": [0.1, 0.2, 0.3, 0.4, 0.5],
        "prerequisite_threshold": [1.0, 1.5, 2.0, 2.5],
        "max_questions": [20, 30, 40, 50, 60],
    }

    return {
        "sessions": sessions,
        "parameter_ranges": parameter_ranges,
        "total_sessions": len(sessions),
        "note": "Use /with-me:grid-search skill for optimization",
    }


def generate_optimization_report(results: dict[str, Any]) -> str:
    """
    Generate ASCII report from optimization results.

    Grid search should be performed by Claude using /with-me:grid-search skill
    before calling this function.

    Args:
        results: Dictionary with optimization results from skill

    Returns:
        Formatted ASCII report

    Examples:
        >>> results = {
        ...     "best_parameters": {"convergence_threshold": 0.3},
        ...     "best_score": 0.85,
        ... }
        >>> report = generate_optimization_report(results)
        >>> "Best Parameters" in report
        True
    """
    lines = []
    lines.append("=" * 60)
    lines.append("Parameter Optimization Results")
    lines.append("=" * 60)
    lines.append("")

    # Best parameters
    if "best_parameters" in results:
        lines.append("Best Parameters:")
        for param, value in results["best_parameters"].items():
            lines.append(f"  {param}: {value}")
        lines.append("")

    # Best score
    if "best_score" in results:
        lines.append(f"Best Score: {results['best_score']:.4f}")
        lines.append("")

    # Note
    if "note" in results:
        lines.append(f"Note: {results['note']}")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


# CLI interface
def main():
    """Command-line interface for parameter tuning"""
    if len(sys.argv) > 1 and sys.argv[1] == "--collect":
        # Collect data for optimization
        data = collect_parameter_data()
        import json
        print(json.dumps(data, indent=2))
        return

    print("Parameter Optimization Tool")
    print("\nAll grid search computation has been moved to skill.")
    print("\nUsage:")
    print("  --collect    Collect session data for optimization")
    print("\nUse /with-me:grid-search skill for parameter optimization.")
    print("\nWorkflow:")
    print("  1. Collect data: python -m with_me.lib.parameter_tuner --collect")
    print("  2. Invoke skill: /with-me:grid-search")
    print("  3. Provide collected data to Claude")
    print("  4. Claude performs grid search using skill")
    print("  5. Generate report with optimization results")


if __name__ == "__main__":
    main()
