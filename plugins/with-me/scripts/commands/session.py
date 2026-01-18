#!/usr/bin/env python3
"""
Session management entry point for with-me plugin

Provides session operations called from good-question.md
Outputs plain values (not JSON) for shell script usage without jq dependency
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

if __name__ == "__main__":
    # Delegate to lib.question_feedback_cli with --plain-output flag
    sys.argv.insert(1, "--plain-output") if len(sys.argv) > 1 else None

    from lib import question_feedback_cli
    question_feedback_cli.main()
