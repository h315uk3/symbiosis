#!/usr/bin/env python3
"""
Get question count for a specific session

Usage:
    python3 session_question_count.py <session_id>

Returns:
    Number of questions in the session (0 if not found)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.question_feedback_manager import QuestionFeedbackManager


def get_question_count(session_id: str, feedback_file: Path | None = None) -> int:
    """
    Get the number of questions in a session

    Args:
        session_id: Session identifier
        feedback_file: Optional path to feedback file

    Returns:
        Number of questions (0 if session not found)

    Examples:
        >>> import tempfile
        >>> feedback_file = Path(tempfile.mktemp(suffix=".json"))
        >>> manager = QuestionFeedbackManager(feedback_file)
        >>> session_id = manager.start_session()
        >>> get_question_count(session_id, feedback_file)
        0
        >>> manager.record_question(
        ...     session_id, "test", "purpose",
        ...     {"uncertainties_before": {}, "uncertainties_after": {}},
        ...     {"word_count": 10, "has_examples": False},
        ...     {"total_reward": 0.5}
        ... )
        >>> get_question_count(session_id, feedback_file)
        1
        >>> feedback_file.unlink()
    """
    manager = QuestionFeedbackManager(feedback_file)
    session = manager._find_session(session_id)
    return len(session["questions"]) if session else 0


def main():
    """CLI entry point"""
    if len(sys.argv) != 2:
        print("Usage: session_question_count.py <session_id>", file=sys.stderr)
        sys.exit(1)

    session_id = sys.argv[1]
    count = get_question_count(session_id)
    print(count)


if __name__ == "__main__":
    main()
