#!/usr/bin/env python3
"""
CLI interface for question feedback manager

Provides command-line access to question feedback operations.
Designed to be called from shell scripts with minimal overhead.
"""

import json
import sys

from with_me.lib.question_feedback_manager import QuestionFeedbackManager


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
    information_gain = context.get("information_gain")

    reward_scores = context.get(
        "reward_scores",
        {
            "total_reward": 0.0,
            "components": {"info_gain": 0.0, "clarity": 0.0, "importance": 0.0},
            "confidence": 0.0,
        },
    )

    manager = QuestionFeedbackManager()
    manager.record_question(
        session_id,
        question,
        dimension,
        context,
        answer_data,
        reward_scores,
        information_gain=information_gain,
    )

    print(json.dumps({"recorded": True, "information_gain": information_gain}))


def cmd_record_batch(session_id: str, questions_json: str) -> None:
    """Record multiple questions at once"""
    questions = json.loads(questions_json)

    manager = QuestionFeedbackManager()

    recorded = 0
    for q_data in questions:
        question = q_data["question"]
        dimension = q_data["dimension"]
        context = q_data["context"]
        answer_data = q_data["answer"]
        information_gain = q_data.get("information_gain")

        reward_scores = q_data.get(
            "reward_scores",
            {
                "total_reward": 0.0,
                "components": {"info_gain": 0.0, "clarity": 0.0, "importance": 0.0},
                "confidence": 0.0,
            },
        )

        manager.record_question(
            session_id,
            question,
            dimension,
            context,
            answer_data,
            reward_scores,
            information_gain=information_gain,
        )
        recorded += 1

    print(json.dumps({"recorded": recorded}))


def cmd_complete(
    session_id: str,
    final_uncertainties_json: str,
    final_dimension_beliefs_json: str | None = None,
) -> None:
    """Complete a session"""
    final_uncertainties = json.loads(final_uncertainties_json)
    final_dimension_beliefs = (
        json.loads(final_dimension_beliefs_json)
        if final_dimension_beliefs_json
        else None
    )

    manager = QuestionFeedbackManager()
    summary = manager.complete_session(
        session_id, final_uncertainties, final_dimension_beliefs
    )

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
    elif command == "complete" and len(args) not in (
        expected_complete_argc,
        expected_complete_argc + 1,
    ):
        msg = "complete requires 2 or 3 arguments"
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
            complete_with_beliefs = 4  # command + session_id + uncertainties + beliefs
            beliefs_json = args[3] if len(args) == complete_with_beliefs else None
            cmd_complete(args[1], args[2], beliefs_json)
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
