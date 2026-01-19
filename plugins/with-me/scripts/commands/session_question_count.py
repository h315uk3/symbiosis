#!/usr/bin/env python3
"""
CLI entry point: Get question count for a specific session

This is a thin wrapper around lib.question_feedback_manager.
No business logic or tests here - see lib/ for tested implementations.

Usage:
    cd "${CLAUDE_PLUGIN_ROOT}/scripts/commands" && python3 session_question_count.py <session_id>
"""

import sys
from pathlib import Path

# Add scripts/ to path for lib imports (matches as-you pattern)
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.question_feedback_manager import QuestionFeedbackManager


def main():
    """CLI entry point - argument parsing only"""
    if len(sys.argv) != 2:
        print(
            "Usage: python3 -m scripts.commands.session_question_count <session_id>",
            file=sys.stderr,
        )
        sys.exit(1)

    session_id = sys.argv[1]

    # Delegate to lib - business logic lives there
    manager = QuestionFeedbackManager()
    session = manager._find_session(session_id)
    count = len(session["questions"]) if session else 0

    print(count)


if __name__ == "__main__":
    main()
