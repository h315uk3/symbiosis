#!/usr/bin/env python3
"""
CLI interface for question feedback manager

Provides command-line access to question feedback operations.
Designed to be called from shell scripts with minimal overhead.
"""

import json
import sys

from with_me.lib.question_feedback_manager import QuestionFeedbackManager
from with_me.lib.question_reward_calculator import QuestionRewardCalculator


def cmd_start(plain_output: bool = False) -> None:
    """Start a new session"""
    manager = QuestionFeedbackManager()
    session_id = manager.start_session()
    if plain_output:
        print(session_id)
    else:
        print(json.dumps({"session_id": session_id}))


def cmd_record(
    session_id: str, question: str, context_json: str, answer_json: str
) -> None:
    """Record a question-answer pair"""
    context = json.loads(context_json)
    answer_data = json.loads(answer_json)
    dimension = context.get("dimension", "unknown")

    calculator = QuestionRewardCalculator()
    answer_text = answer_data.get("text", "")
    reward_result = calculator.calculate_reward(question, context, answer_text)

    manager = QuestionFeedbackManager()
    manager.record_question(
        session_id, question, dimension, context, answer_data, reward_result
    )

    print(json.dumps({"reward_scores": reward_result}))


def cmd_record_batch(session_id: str, questions_json: str) -> None:
    """Record multiple questions at once"""
    questions = json.loads(questions_json)

    manager = QuestionFeedbackManager()
    calculator = QuestionRewardCalculator()

    recorded = 0
    for q_data in questions:
        question = q_data["question"]
        dimension = q_data["dimension"]
        context = q_data["context"]
        answer_data = q_data["answer"]

        answer_text = answer_data.get("text", "")
        reward_result = calculator.calculate_reward(question, context, answer_text)

        manager.record_question(
            session_id, question, dimension, context, answer_data, reward_result
        )
        recorded += 1

    print(json.dumps({"recorded": recorded}))


def cmd_complete(session_id: str, final_uncertainties_json: str) -> None:
    """Complete a session"""
    final_uncertainties = json.loads(final_uncertainties_json)

    manager = QuestionFeedbackManager()
    summary = manager.complete_session(session_id, final_uncertainties)

    print(json.dumps({"summary": summary}))


def cmd_stats() -> None:
    """Get statistics"""
    manager = QuestionFeedbackManager()
    stats = manager.get_statistics()
    print(json.dumps(stats, indent=2))


def usage() -> None:
    """Print usage information"""
    print("Usage: question_feedback_cli.py <command> [args]", file=sys.stderr)
    print("\nCommands:", file=sys.stderr)
    print("  start", file=sys.stderr)
    print(
        "  record <session_id> <question> <context_json> <answer_json>",
        file=sys.stderr,
    )
    print("  record-batch <session_id> <questions_json>", file=sys.stderr)
    print("  complete <session_id> <final_uncertainties_json>", file=sys.stderr)
    print("  stats", file=sys.stderr)


def _validate_args(command: str, args: list[str]) -> None:
    """Validate command arguments (raises ValueError if invalid)"""
    expected_record_argc = 5  # command + 4 args
    expected_batch_argc = 3  # command + 2 args
    expected_complete_argc = 3  # command + 2 args

    if command == "record" and len(args) != expected_record_argc:
        msg = "record requires 4 arguments"
        raise ValueError(msg)
    elif command == "record-batch" and len(args) != expected_batch_argc:
        msg = "record-batch requires 2 arguments"
        raise ValueError(msg)
    elif command == "complete" and len(args) != expected_complete_argc:
        msg = "complete requires 2 arguments"
        raise ValueError(msg)


def main() -> None:
    """CLI entry point"""
    min_argc = 2  # program name + command
    if len(sys.argv) < min_argc:
        usage()
        sys.exit(1)

    # Check for --plain-output flag
    plain_output = False
    args = sys.argv[1:]
    if "--plain-output" in args:
        plain_output = True
        args.remove("--plain-output")
        sys.argv = [sys.argv[0], *args]  # Rebuild argv without flag

    if len(args) < 1:
        usage()
        sys.exit(1)

    command = args[0]

    # Validate arguments before entering try block
    try:
        _validate_args(command, args)
    except ValueError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

    try:
        if command == "start":
            cmd_start(plain_output=plain_output)
        elif command == "record":
            cmd_record(args[1], args[2], args[3], args[4])
        elif command == "record-batch":
            cmd_record_batch(args[1], args[2])
        elif command == "complete":
            cmd_complete(args[1], args[2])
        elif command == "stats":
            cmd_stats()
        else:
            print(f"Unknown command: {command}", file=sys.stderr)
            usage()
            sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
