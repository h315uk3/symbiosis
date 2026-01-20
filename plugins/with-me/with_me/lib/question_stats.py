#!/usr/bin/env python3
"""
Question statistics collector for with-me plugin.

MIGRATION COMPLETE: All statistical computations have been moved to skills.
This module now serves as data aggregation and I/O layer only.

Computation is delegated to:
- /with-me:statistical-measures skill: Mean, median, std dev, variance
- /with-me:correlation skill: Pearson correlation coefficient
- /with-me:entropy skill: Shannon entropy calculation
- /with-me:information-gain skill: IG = H_before - H_after

References:
- Issue #37: Claude Computational Engine architecture
- Skills: plugins/with-me/skills/{statistical-measures,correlation,entropy,information-gain}
"""

import sys
from typing import Any

from .question_feedback_manager import QuestionFeedbackManager, WithMeConfig


def collect_stats() -> dict:
    """
    Collect raw question statistics from feedback manager.

    Returns aggregated data without performing statistical calculations.
    Use Claude with skills to calculate mean, std dev, correlation, etc.

    Returns:
        Dictionary with raw statistics data

    Examples:
        >>> # Mock example without actual feedback file
        >>> stats = {"total_questions": 0, "sessions": []}
        >>> "total_questions" in stats
        True
    """
    config = WithMeConfig.from_environment()
    manager = QuestionFeedbackManager(config.feedback_file)

    if not config.feedback_file.exists():
        return {
            "total_questions": 0,
            "total_sessions": 0,
            "sessions": [],
            "note": "No feedback data available",
        }

    # Load feedback data
    feedback = manager.feedback

    # Aggregate raw data (no computation)
    questions = feedback.get("questions", [])
    sessions = feedback.get("sessions", [])

    return {
        "total_questions": len(questions),
        "total_sessions": len(sessions),
        "sessions": sessions,
        "questions": questions,
        "note": "Use /with-me:statistical-measures skill for calculations",
    }


def collect_enhanced_stats() -> dict:
    """
    Collect enhanced statistics with session-level aggregation.

    Returns raw aggregated data. Use Claude with skills for:
    - Mean/median/std dev: /with-me:statistical-measures
    - Correlation analysis: /with-me:correlation
    - Entropy calculations: /with-me:entropy

    Returns:
        Dictionary with enhanced aggregated data

    Examples:
        >>> # Mock example
        >>> stats = collect_enhanced_stats()
        >>> "total_questions" in stats
        True
    """
    config = WithMeConfig.from_environment()
    manager = QuestionFeedbackManager(config.feedback_file)

    if not config.feedback_file.exists():
        return {
            "total_questions": 0,
            "total_sessions": 0,
            "note": "No feedback data available",
        }

    feedback = manager.feedback
    sessions = feedback.get("sessions", [])

    # Aggregate session-level data
    session_summaries = []
    for session in sessions:
        session_summaries.append({
            "session_id": session.get("session_id"),
            "total_questions": session.get("total_questions", 0),
            "total_info_gain": session.get("total_info_gain", 0.0),
            "dimension_beliefs": session.get("final_dimension_beliefs", {}),
        })

    return {
        "total_questions": sum(s["total_questions"] for s in session_summaries),
        "total_sessions": len(sessions),
        "sessions": session_summaries,
        "note": "Use skills for statistical calculations",
    }


def generate_ascii_report(stats: dict) -> str:
    """
    Generate ASCII report from raw statistics.

    Statistical calculations should be performed by Claude using skills
    before calling this function.

    Args:
        stats: Dictionary with pre-calculated statistics

    Returns:
        Formatted ASCII report

    Examples:
        >>> stats = {"total_questions": 10, "total_sessions": 2}
        >>> report = generate_ascii_report(stats)
        >>> "Questions" in report
        True
    """
    lines = []
    lines.append("=" * 60)
    lines.append("Question Effectiveness Statistics")
    lines.append("=" * 60)
    lines.append("")

    # Summary section
    lines.append("Summary:")
    lines.append(f"  Total Questions: {stats.get('total_questions', 0)}")
    lines.append(f"  Total Sessions: {stats.get('total_sessions', 0)}")
    lines.append("")

    # Note about computation
    if "note" in stats:
        lines.append(f"Note: {stats['note']}")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


# CLI interface
def main():
    """Command-line interface for statistics collection"""
    if len(sys.argv) > 1 and sys.argv[1] == "--enhanced":
        stats = collect_enhanced_stats()
    else:
        stats = collect_stats()

    # Generate report
    report = generate_ascii_report(stats)
    print(report)

    # Output raw data as JSON for processing
    print("\nRaw data (JSON):")
    import json
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
