#!/usr/bin/env bash
#
# good-question implementation helper
# Bridges good-question.md command with Python implementations
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"

# Python scripts
FEEDBACK_MANAGER="$PLUGIN_ROOT/scripts/lib/question_feedback_manager.py"
REWARD_CALCULATOR="$PLUGIN_ROOT/scripts/lib/question_reward_calculator.py"

# Usage information
usage() {
    cat <<EOF
Usage: good-question-impl.sh <command> [args]

Commands:
    start
        Start a new session
        Returns: {"session_id": "..."}

    record <session_id> <question> <context_json> <answer_json>
        Record a question-answer pair
        Args:
            session_id: Session identifier
            question: Question text
            context_json: Context with uncertainties before/after
            answer_json: Answer data (word_count, has_examples)
        Returns: {"reward_scores": {...}}

    complete <session_id> <final_uncertainties_json>
        Complete a session and generate summary
        Args:
            session_id: Session identifier
            final_uncertainties_json: Final uncertainty scores
        Returns: {"summary": {...}}

Examples:
    # Start session
    SESSION_ID=\$(bash good-question-impl.sh start | jq -r '.session_id')

    # Record question
    bash good-question-impl.sh record "\$SESSION_ID" "What?" '{"uncertainties_before": {...}}' '{"word_count": 50}'

    # Complete session
    bash good-question-impl.sh complete "\$SESSION_ID" '{"purpose": 0.3}'
EOF
}

# Start a new session
start_session() {
    python3 <<EOF
import sys
sys.path.insert(0, "$PLUGIN_ROOT/scripts")

from lib.question_feedback_manager import QuestionFeedbackManager
import json

manager = QuestionFeedbackManager()
session_id = manager.start_session()
print(json.dumps({"session_id": session_id}))
EOF
}

# Record a question
record_question() {
    local session_id="$1"
    local question="$2"
    local context_json="$3"
    local answer_json="$4"

    python3 <<EOF
import sys
sys.path.insert(0, "$PLUGIN_ROOT/scripts")

from lib.question_feedback_manager import QuestionFeedbackManager
from lib.question_reward_calculator import QuestionRewardCalculator
import json

session_id = "$session_id"
question = """$question"""
context = json.loads('''$context_json''')
answer_data = json.loads('''$answer_json''')

# Calculate reward scores
calculator = QuestionRewardCalculator()

# Extract dimension from context or question
dimension = context.get("dimension", "unknown")

# Calculate reward (with answer for post-evaluation)
answer_text = answer_data.get("text", "")
reward_result = calculator.calculate_reward(question, context, answer_text)

# Record question
manager = QuestionFeedbackManager()
manager.record_question(
    session_id,
    question,
    dimension,
    context,
    answer_data,
    reward_result
)

print(json.dumps({"reward_scores": reward_result}))
EOF
}

# Complete a session
complete_session() {
    local session_id="$1"
    local final_uncertainties_json="$2"

    python3 <<EOF
import sys
sys.path.insert(0, "$PLUGIN_ROOT/scripts")

from lib.question_feedback_manager import QuestionFeedbackManager
import json

session_id = "$session_id"
final_uncertainties = json.loads('''$final_uncertainties_json''')

manager = QuestionFeedbackManager()
summary = manager.complete_session(session_id, final_uncertainties)

print(json.dumps({"summary": summary}))
EOF
}

# Main command router
main() {
    if [ $# -lt 1 ]; then
        usage
        exit 1
    fi

    case "$1" in
        start)
            start_session
            ;;
        record)
            if [ $# -ne 5 ]; then
                echo "Error: record requires 4 arguments" >&2
                usage
                exit 1
            fi
            record_question "$2" "$3" "$4" "$5"
            ;;
        complete)
            if [ $# -ne 3 ]; then
                echo "Error: complete requires 2 arguments" >&2
                usage
                exit 1
            fi
            complete_session "$2" "$3"
            ;;
        -h|--help|help)
            usage
            exit 0
            ;;
        *)
            echo "Error: Unknown command '$1'" >&2
            usage
            exit 1
            ;;
    esac
}

main "$@"
