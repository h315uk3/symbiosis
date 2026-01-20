#!/usr/bin/env python3
"""
CLI for good-question session management.

Provides JSON output for Claude Code to consume:
- init: Initialize new session
- next-question: Select next question
- update: Update beliefs with answer
- status: Display current state
- complete: Finalize session

Session state is persisted to .claude/with_me/sessions/<session_id>.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from with_me.lib.session_orchestrator import SessionOrchestrator


def get_session_dir() -> Path:
    """Get session persistence directory."""
    # Look for .claude directory in current or parent directories
    current = Path.cwd()
    while current != current.parent:
        claude_dir = current / ".claude" / "with_me" / "sessions"
        if claude_dir.parent.parent.exists():
            claude_dir.mkdir(parents=True, exist_ok=True)
            return claude_dir
        current = current.parent

    # Fallback to home directory
    fallback = Path.home() / ".claude" / "with_me" / "sessions"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def save_session_state(session_id: str, orchestrator: SessionOrchestrator) -> None:
    """Save session state to disk."""
    session_file = get_session_dir() / f"{session_id}.json"

    state = {
        "session_id": orchestrator.session_id,
        "beliefs": {k: v.to_dict() for k, v in orchestrator.beliefs.items()},
        "question_history": orchestrator.question_history,
        "question_count": orchestrator.question_count,
    }

    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def load_session_state(session_id: str) -> SessionOrchestrator:
    """Load session state from disk."""
    session_file = get_session_dir() / f"{session_id}.json"

    if not session_file.exists():
        print(
            json.dumps({"error": f"Session not found: {session_id}"}), file=sys.stderr
        )
        sys.exit(1)

    with open(session_file) as f:
        state = json.load(f)

    # Reconstruct orchestrator
    from with_me.lib.dimension_belief import HypothesisSet

    orch = SessionOrchestrator()
    orch.session_id = state["session_id"]
    orch.beliefs = {k: HypothesisSet.from_dict(v) for k, v in state["beliefs"].items()}
    orch.question_history = state["question_history"]
    orch.question_count = state["question_count"]

    return orch


def cmd_init(args: argparse.Namespace) -> None:
    """Initialize new session."""
    orch = SessionOrchestrator()
    session_id = orch.initialize_session()

    # Save initial state
    save_session_state(session_id, orch)

    # Output JSON
    print(
        json.dumps(
            {
                "session_id": session_id,
                "status": "initialized",
            }
        )
    )


def cmd_next_question(args: argparse.Namespace) -> None:
    """Select next question to ask."""
    orch = load_session_state(args.session_id)

    # Check convergence first
    if orch.check_convergence():
        print(
            json.dumps(
                {
                    "converged": True,
                    "reason": "All dimensions converged or max questions reached",
                }
            )
        )
        return

    dimension, question = orch.select_next_question()

    if dimension is None:
        print(
            json.dumps(
                {
                    "converged": True,
                    "reason": "No accessible dimensions (all blocked by prerequisites)",
                }
            )
        )
        return

    # Get dimension metadata
    dim_config = orch.config["dimensions"][dimension]

    print(
        json.dumps(
            {
                "converged": False,
                "dimension": dimension,
                "dimension_name": dim_config["name"],
                "question": question,
            }
        )
    )


def cmd_update(args: argparse.Namespace) -> None:
    """Update beliefs with user answer."""
    orch = load_session_state(args.session_id)

    # If semantic evaluation is enabled, output evaluation request for Claude
    if getattr(args, "enable_semantic_evaluation", False):
        dim_config = orch.config["dimensions"][args.dimension]
        hypotheses = []

        for hyp_id, hyp_data in dim_config.get("hypotheses", {}).items():
            hypotheses.append(
                {
                    "id": hyp_id,
                    "name": hyp_data["name"],
                    "description": hyp_data["description"],
                    "focus_areas": hyp_data["focus_areas"],
                }
            )

        evaluation_request = {
            "evaluation_request": True,
            "dimension": args.dimension,
            "dimension_name": dim_config["name"],
            "hypotheses": hypotheses,
            "question": args.question,
            "answer": args.answer,
            "instruction": (
                "Based on the question and answer, estimate the likelihood (0.0-1.0) "
                "that each hypothesis is true. Consider the hypothesis descriptions and "
                "focus areas. Return JSON with format: "
                '{"likelihoods": {"hypothesis_id": probability, ...}}. '
                "Likelihoods should sum to approximately 1.0."
            ),
        }

        print(json.dumps(evaluation_request, indent=2))
        return

    # Parse likelihoods (required)
    if not getattr(args, "likelihoods", None):
        print(
            json.dumps(
                {
                    "error": "Missing required --likelihoods argument. "
                    "Use --enable-semantic-evaluation to get evaluation request first."
                }
            ),
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        likelihoods = json.loads(args.likelihoods)
    except json.JSONDecodeError as e:
        print(
            json.dumps({"error": f"Invalid JSON in --likelihoods: {e}"}),
            file=sys.stderr,
        )
        sys.exit(1)

    result = orch.update_beliefs(
        args.dimension, args.question, args.answer, likelihoods
    )

    # Save updated state
    save_session_state(args.session_id, orch)

    print(
        json.dumps(
            {
                "information_gain": round(result["information_gain"], 3),
                "entropy_before": round(result["entropy_before"], 2),
                "entropy_after": round(result["entropy_after"], 2),
                "dimension": result["dimension"],
            }
        )
    )


def cmd_status(args: argparse.Namespace) -> None:
    """Display current session state."""
    orch = load_session_state(args.session_id)

    state = orch.get_current_state()

    # Format for display
    output: dict[str, Any] = {
        "session_id": state["session_id"],
        "question_count": state["question_count"],
        "all_converged": state["all_converged"],
        "dimensions": {},
    }

    for dim_id, dim_data in state["dimensions"].items():
        output["dimensions"][dim_id] = {
            "name": dim_data["name"],
            "entropy": round(dim_data["entropy"], 2),
            "confidence": round(dim_data["confidence"], 2),
            "converged": dim_data["converged"],
            "blocked": dim_data["blocked"],
            "blocked_by": dim_data["blocked_by"],
            "most_likely": dim_data["most_likely"],
        }

    print(json.dumps(output, indent=2))


def cmd_complete(args: argparse.Namespace) -> None:
    """Complete session and generate summary."""
    orch = load_session_state(args.session_id)

    summary = orch.complete_session()

    # Clean up session file
    session_file = get_session_dir() / f"{args.session_id}.json"
    if session_file.exists():
        session_file.unlink()

    print(
        json.dumps(
            {
                "session_id": args.session_id,
                "total_questions": summary.get("total_questions", 0),
                "total_info_gain": round(summary.get("total_info_gain", 0.0), 2),
                "status": "completed",
            }
        )
    )


def cmd_compute_entropy(args: argparse.Namespace) -> None:
    """Output skill input for Claude to calculate entropy."""
    orch = load_session_state(args.session_id)
    posterior = orch.beliefs[args.dimension].posterior

    # Output skill input for Claude
    print(
        json.dumps(
            {
                "skill_input": "entropy",
                "dimension": args.dimension,
                "posterior": posterior,
                "theory_file": "plugins/with-me/theory/algorithms/entropy.md",
                "instruction": (
                    "MUST invoke /with-me:entropy skill with the posterior distribution. "
                    "Calculate Shannon entropy H(h) = -Σ p(h) log₂ p(h). "
                    "Return the entropy value in bits, rounded to 4 decimal places."
                ),
            },
            indent=2,
        )
    )


def cmd_bayesian_update(args: argparse.Namespace) -> None:
    """Output skill input for Claude to perform Bayesian update."""
    orch = load_session_state(args.session_id)
    prior = orch.beliefs[args.dimension].posterior
    likelihoods = json.loads(args.likelihoods)

    # Output skill input for Claude
    print(
        json.dumps(
            {
                "skill_input": "bayesian_update",
                "dimension": args.dimension,
                "prior": prior,
                "likelihoods": likelihoods,
                "theory_file": "plugins/with-me/theory/algorithms/bayesian_update.md",
                "instruction": (
                    "MUST invoke /with-me:bayesian-update skill with the prior and likelihoods. "
                    "Perform Bayesian belief updating: p₁(h) = [p₀(h) * L(obs|h)] / Σ[p₀(h) * L(obs|h)]. "
                    "Return the normalized posterior distribution."
                ),
            },
            indent=2,
        )
    )


def cmd_information_gain(args: argparse.Namespace) -> None:
    """Output skill input for Claude to calculate information gain."""
    # Information gain doesn't need session state
    print(
        json.dumps(
            {
                "skill_input": "information_gain",
                "entropy_before": args.entropy_before,
                "entropy_after": args.entropy_after,
                "theory_file": "plugins/with-me/theory/algorithms/information_gain.md",
                "instruction": (
                    "MUST invoke /with-me:information-gain skill with H_before and H_after. "
                    "Calculate information gain: IG = H_before - H_after. "
                    "Return the information gain in bits."
                ),
            },
            indent=2,
        )
    )


def cmd_persist_computation(args: argparse.Namespace) -> None:
    """Persist Claude-computed results to session state."""
    orch = load_session_state(args.session_id)

    # Parse computed values
    updated_posterior = json.loads(args.updated_posterior)

    # Update belief state with Claude-computed posterior
    orch.beliefs[args.dimension].posterior = updated_posterior

    # Cache entropy and confidence for session_orchestrator methods
    orch.beliefs[args.dimension]._cached_entropy = args.entropy_after
    # Confidence = 1 - (H / H_max) where H_max = log₂(N)
    import math

    h_max = math.log2(len(orch.beliefs[args.dimension].hypotheses))
    if h_max > 0:
        orch.beliefs[args.dimension]._cached_confidence = 1.0 - (
            args.entropy_after / h_max
        )
    else:
        orch.beliefs[args.dimension]._cached_confidence = 1.0

    # Record question-answer in history
    orch.question_history.append(
        {
            "dimension": args.dimension,
            "question": args.question,
            "answer": args.answer,
            "entropy_before": args.entropy_before,
            "entropy_after": args.entropy_after,
            "information_gain": args.information_gain,
        }
    )

    orch.question_count += 1

    # Save updated state
    save_session_state(args.session_id, orch)

    # Output confirmation
    print(
        json.dumps(
            {
                "status": "persisted",
                "dimension": args.dimension,
                "entropy_before": round(args.entropy_before, 4),
                "entropy_after": round(args.entropy_after, 4),
                "information_gain": round(args.information_gain, 4),
                "question_count": orch.question_count,
            }
        )
    )


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Good Question session management CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init command
    subparsers.add_parser("init", help="Initialize new session")

    # next-question command
    next_parser = subparsers.add_parser("next-question", help="Get next question")
    next_parser.add_argument("--session-id", required=True, help="Session ID")

    # update command
    update_parser = subparsers.add_parser("update", help="Update beliefs with answer")
    update_parser.add_argument("--session-id", required=True, help="Session ID")
    update_parser.add_argument("--dimension", required=True, help="Dimension ID")
    update_parser.add_argument("--question", required=True, help="Question asked")
    update_parser.add_argument("--answer", required=True, help="User's answer")
    update_parser.add_argument(
        "--enable-semantic-evaluation",
        action="store_true",
        help="Output evaluation request for Claude instead of computing likelihoods",
    )
    update_parser.add_argument(
        "--likelihoods",
        type=str,
        help='Pre-computed likelihoods as JSON string: \'{"hyp1": 0.5, "hyp2": 0.3, ...}\'',
    )

    # status command
    status_parser = subparsers.add_parser("status", help="Display session state")
    status_parser.add_argument("--session-id", required=True, help="Session ID")

    # complete command
    complete_parser = subparsers.add_parser("complete", help="Complete session")
    complete_parser.add_argument("--session-id", required=True, help="Session ID")

    # compute-entropy command
    entropy_parser = subparsers.add_parser(
        "compute-entropy", help="Request Claude to calculate entropy"
    )
    entropy_parser.add_argument("--session-id", required=True, help="Session ID")
    entropy_parser.add_argument("--dimension", required=True, help="Dimension ID")

    # bayesian-update command
    bayes_parser = subparsers.add_parser(
        "bayesian-update", help="Request Claude to perform Bayesian update"
    )
    bayes_parser.add_argument("--session-id", required=True, help="Session ID")
    bayes_parser.add_argument("--dimension", required=True, help="Dimension ID")
    bayes_parser.add_argument(
        "--likelihoods",
        type=str,
        required=True,
        help="Likelihoods as JSON: '{\"hyp1\": 0.5, ...}'",
    )

    # information-gain command
    ig_parser = subparsers.add_parser(
        "information-gain", help="Request Claude to calculate information gain"
    )
    ig_parser.add_argument(
        "--entropy-before", type=float, required=True, help="Entropy before update"
    )
    ig_parser.add_argument(
        "--entropy-after", type=float, required=True, help="Entropy after update"
    )

    # persist-computation command
    persist_parser = subparsers.add_parser(
        "persist-computation", help="Persist Claude-computed results to session"
    )
    persist_parser.add_argument("--session-id", required=True, help="Session ID")
    persist_parser.add_argument("--dimension", required=True, help="Dimension ID")
    persist_parser.add_argument("--question", required=True, help="Question asked")
    persist_parser.add_argument("--answer", required=True, help="User's answer")
    persist_parser.add_argument(
        "--entropy-before", type=float, required=True, help="Claude-computed H_before"
    )
    persist_parser.add_argument(
        "--entropy-after", type=float, required=True, help="Claude-computed H_after"
    )
    persist_parser.add_argument(
        "--information-gain", type=float, required=True, help="Claude-computed IG"
    )
    persist_parser.add_argument(
        "--updated-posterior",
        type=str,
        required=True,
        help="Claude-computed posterior as JSON: '{\"hyp1\": 0.7, ...}'",
    )

    args = parser.parse_args()

    # Dispatch to command handler
    if args.command == "init":
        cmd_init(args)
    elif args.command == "next-question":
        cmd_next_question(args)
    elif args.command == "update":
        cmd_update(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "complete":
        cmd_complete(args)
    elif args.command == "compute-entropy":
        cmd_compute_entropy(args)
    elif args.command == "bayesian-update":
        cmd_bayesian_update(args)
    elif args.command == "information-gain":
        cmd_information_gain(args)
    elif args.command == "persist-computation":
        cmd_persist_computation(args)


if __name__ == "__main__":
    main()
