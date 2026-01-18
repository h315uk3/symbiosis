#!/usr/bin/env python3
"""
Question statistics collector for with-me plugin.
Collects and outputs JSON statistics about question effectiveness.
"""

import json
import sys

from question_feedback_manager import QuestionFeedbackManager, WithMeConfig


def collect_stats() -> dict:
    """
    Collect question effectiveness statistics

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


def main():
    """Main entry point"""
    stats = collect_stats()
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
