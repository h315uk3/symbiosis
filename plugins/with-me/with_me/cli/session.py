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
import math
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from with_me.lib.dimension_belief import HypothesisSet, compute_jsd
from with_me.lib.session_orchestrator import SessionOrchestrator

# Convergence thresholds
DIMENSION_RESOLVED_THRESHOLD = (
    0.3  # Entropy threshold for considering a dimension resolved
)

# Likelihood validation constants
LIKELIHOOD_EPSILON = 1e-9  # Minimum non-zero likelihood value


def validate_and_normalize_likelihoods(
    hs: HypothesisSet, likelihoods_in: dict[str, Any]
) -> dict[str, float]:
    """Validate and normalize likelihoods for Bayesian update.

    Handles common input errors from LLM-generated likelihoods:
    - Missing hypotheses → treated as 0.0
    - Negative values → clamped to 0.0
    - All zeros → fallback to uniform distribution
    - Otherwise → normalized to sum=1.0
    - Extreme values → clamped to epsilon

    Args:
        hs: HypothesisSet containing the hypotheses
        likelihoods_in: Raw likelihood dict from LLM

    Returns:
        Normalized likelihood dict (sum=1.0, all non-negative)

    Examples:
        >>> hs = HypothesisSet("test", ["a", "b", "c"])
        >>> # Normal case
        >>> validate_and_normalize_likelihoods(hs, {"a": 0.5, "b": 0.3, "c": 0.2})
        {'a': 0.5, 'b': 0.3, 'c': 0.2}

        >>> # Missing keys → filled with 0.0
        >>> result = validate_and_normalize_likelihoods(hs, {"a": 1.0})
        >>> round(result["a"], 2)
        1.0
        >>> round(result["b"], 2)
        0.0

        >>> # Negative values → clamped to 0.0
        >>> result = validate_and_normalize_likelihoods(
        ...     hs, {"a": 0.5, "b": -0.1, "c": 0.6}
        ... )
        >>> result["b"]
        0.0

        >>> # All zeros → uniform fallback
        >>> result = validate_and_normalize_likelihoods(
        ...     hs, {"a": 0.0, "b": 0.0, "c": 0.0}
        ... )
        >>> round(result["a"], 2)
        0.33

        >>> # Unnormalized → normalized
        >>> result = validate_and_normalize_likelihoods(
        ...     hs, {"a": 2.0, "b": 3.0, "c": 5.0}
        ... )
        >>> round(result["a"], 2)
        0.2
        >>> round(result["c"], 2)
        0.5
    """
    vals = {}
    for h in hs.hypotheses:
        v = float(likelihoods_in.get(h, 0.0))
        if v < 0:
            v = 0.0
        # Clamp extremely small values to epsilon
        if 0 < v < LIKELIHOOD_EPSILON:
            v = LIKELIHOOD_EPSILON
        vals[h] = v

    s = sum(vals.values())
    if s <= 0.0:
        # Uniform fallback when all likelihoods are zero
        u = 1.0 / len(hs.hypotheses) if hs.hypotheses else 1.0
        return {h: u for h in hs.hypotheses}

    # Normalize to sum=1.0
    return {h: v / s for h, v in vals.items()}


def compute_joint_likelihoods(
    hs: HypothesisSet, likelihoods_list: list[dict[str, Any]]
) -> dict[str, float]:
    """Compute joint likelihood from multiple answer likelihoods.

    For multi-select answers, computes the pointwise product of
    individually validated likelihoods, then normalizes. This produces
    a single combined observation for a single Bayesian update, avoiding
    the negative information gain that occurs with sequential updates.

    Args:
        hs: HypothesisSet containing the hypotheses
        likelihoods_list: List of likelihood dicts, one per selected answer

    Returns:
        Normalized joint likelihood dict (sum=1.0)

    Examples:
        >>> hs = HypothesisSet("test", ["a", "b", "c"])
        >>> # Two answers: first favors a, second favors b
        >>> L1 = {"a": 0.7, "b": 0.2, "c": 0.1}
        >>> L2 = {"a": 0.2, "b": 0.6, "c": 0.2}
        >>> result = compute_joint_likelihoods(hs, [L1, L2])
        >>> # Joint: a=0.14, b=0.12, c=0.02 → normalized
        >>> round(result["a"], 2)
        0.5
        >>> round(result["b"], 2)
        0.43
        >>> round(result["c"], 2)
        0.07

        >>> # Single answer → same as validate_and_normalize
        >>> result = compute_joint_likelihoods(hs, [{"a": 0.5, "b": 0.3, "c": 0.2}])
        >>> result
        {'a': 0.5, 'b': 0.3, 'c': 0.2}

        >>> # Empty list → uniform fallback
        >>> result = compute_joint_likelihoods(hs, [])
        >>> round(result["a"], 2)
        0.33
    """
    if not likelihoods_list:
        u = 1.0 / len(hs.hypotheses) if hs.hypotheses else 1.0
        return {h: u for h in hs.hypotheses}

    # Compute pointwise product of validated likelihoods
    joint = {h: 1.0 for h in hs.hypotheses}
    for likelihoods in likelihoods_list:
        validated = validate_and_normalize_likelihoods(hs, likelihoods)
        for h in hs.hypotheses:
            joint[h] *= validated[h]

    # Normalize the product
    return validate_and_normalize_likelihoods(hs, joint)


def get_session_dir() -> Path:
    """Get session persistence directory.

    Searches upward from current directory for .claude/ directory.
    Excludes home directory's ~/.claude/ (personal config, not workspace).
    Falls back to project-local storage if no workspace found.
    """
    # Look for .claude directory in current or parent directories
    current = Path.cwd()
    home = Path.home()

    # Search upward, but stop at home directory
    # Don't use ~/.claude/ (personal config, not workspace)
    while current not in (current.parent, home):
        claude_dir = current / ".claude" / "with_me" / "sessions"
        if claude_dir.parent.parent.exists():
            claude_dir.mkdir(parents=True, exist_ok=True)
            return claude_dir
        current = current.parent

    # Fallback: Use .with_me in current directory (no workspace found)
    # This avoids polluting ~/.claude/ when run outside a workspace
    fallback = Path.cwd() / ".with_me" / "sessions"
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
        "recent_information_gains": orchestrator.recent_information_gains,
        "thompson_states": orchestrator.thompson_states,
    }

    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def load_session_state(session_id: str) -> SessionOrchestrator:
    """Load session state from disk."""
    session_file = get_session_dir() / f"{session_id}.json"

    if not session_file.exists():
        print(
            json.dumps(
                {"error": f"Session not found: {session_id}"}, ensure_ascii=False
            ),
            file=sys.stderr,
        )
        sys.exit(1)

    with open(session_file) as f:
        state = json.load(f)

    # Reconstruct orchestrator
    orch = SessionOrchestrator()
    orch.session_id = state["session_id"]
    orch.beliefs = {k: HypothesisSet.from_dict(v) for k, v in state["beliefs"].items()}
    orch.question_history = state["question_history"]
    orch.question_count = state["question_count"]
    orch.recent_information_gains = state.get("recent_information_gains", [])
    orch.thompson_states = state.get("thompson_states", {})

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
            },
            ensure_ascii=False,
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
                },
                ensure_ascii=False,
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
                },
                ensure_ascii=False,
            )
        )
        return

    # Get dimension metadata with detailed information for question generation
    dim_config = orch.config["dimensions"][dimension]

    # Extract hypothesis information for context
    hypotheses_info = []
    for hyp_id, hyp_data in dim_config.get("hypotheses", {}).items():
        hypotheses_info.append(
            {
                "id": hyp_id,
                "name": hyp_data["name"],
                "description": hyp_data["description"],
                "focus_areas": hyp_data["focus_areas"],
            }
        )

    print(
        json.dumps(
            {
                "converged": False,
                "dimension": dimension,
                "dimension_name": dim_config["name"],
                "dimension_description": dim_config.get("description", ""),
                "focus_areas": dim_config.get("focus_areas", []),
                "hypotheses": hypotheses_info,
                "question": question,
                "supports_multi_select": dim_config.get("supports_multi_select", False),
                "importance": dim_config.get("importance", 0.5),
                "posterior": orch.beliefs[dimension].posterior,
            },
            ensure_ascii=False,
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

    print(json.dumps(output, indent=2, ensure_ascii=False))


def cmd_complete(args: argparse.Namespace) -> None:
    """Complete session and generate summary."""
    session_file = get_session_dir() / f"{args.session_id}.json"

    if not session_file.exists():
        print(
            json.dumps(
                {"error": f"Session file not found: {args.session_id}"},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        sys.exit(1)

    # Load session data
    with open(session_file, encoding="utf-8") as f:
        session_data = json.load(f)

    # Calculate summary from question_history
    question_history = session_data.get("question_history", [])
    beliefs = session_data.get("beliefs", {})

    total_questions = len(question_history)
    total_info_gain = sum(q.get("information_gain", 0) for q in question_history)

    # Calculate avg_reward from evaluation_scores in question_history
    rewards = [
        q["evaluation_scores"]["total_reward"]
        for q in question_history
        if "evaluation_scores" in q
    ]
    avg_reward = sum(rewards) / len(rewards) if rewards else 0.0

    # Calculate final clarity score (1 - normalized average entropy)
    final_entropies = {
        dim: belief.get("_cached_entropy", 0) for dim, belief in beliefs.items()
    }
    final_clarity = 1.0 - (
        sum(final_entropies.values()) / len(final_entropies) if final_entropies else 0
    )

    # Dimensions resolved (entropy < threshold)
    dimensions_resolved = [
        dim
        for dim, entropy in final_entropies.items()
        if entropy < DIMENSION_RESOLVED_THRESHOLD
    ]

    summary = {
        "total_questions": total_questions,
        "avg_reward_per_question": avg_reward,
        "total_info_gain": total_info_gain,
        "final_clarity_score": final_clarity,
        "dimensions_resolved": dimensions_resolved,
        "session_efficiency": total_info_gain / total_questions
        if total_questions > 0
        else 0,
    }

    # Add completion metadata
    session_data["completed"] = True
    session_data["completed_at"] = datetime.now(tz=UTC).isoformat()
    session_data["summary"] = summary

    # Save updated session with completion status
    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2, ensure_ascii=False)

    print(
        json.dumps(
            {
                "session_id": args.session_id,
                "total_questions": total_questions,
                "total_info_gain": round(total_info_gain, 2),
                "status": "completed",
                "archived": True,
            },
            ensure_ascii=False,
        )
    )


def cmd_evaluate_question(args: argparse.Namespace) -> None:
    """Output question evaluation formulas and data for LLM to calculate."""
    orch = load_session_state(args.session_id)

    # Get dimension configuration
    dim_config = orch.config["dimensions"][args.dimension]
    hs = orch.beliefs[args.dimension]

    # Calculate current entropy for importance
    current_entropy = (
        hs._cached_entropy
        if hs._cached_entropy is not None
        else math.log2(len(hs.hypotheses))
    )
    h_max = math.log2(len(hs.hypotheses))

    # Output evaluation formulas and data
    print(
        json.dumps(
            {
                "evaluation_data": {
                    "question": args.question,
                    "dimension": args.dimension,
                    "dimension_name": dim_config["name"],
                    "current_entropy": round(current_entropy, 4),
                    "h_max": round(h_max, 4),
                    "importance_base": dim_config["importance"],
                    "hypotheses": [
                        {
                            "id": hyp_id,
                            "name": hyp_data["name"],
                            "description": hyp_data["description"],
                        }
                        for hyp_id, hyp_data in dim_config.get("hypotheses", {}).items()
                    ],
                    "posterior": hs.posterior,
                },
                "formulas": {
                    "clarity": {
                        "description": "Evaluate question clarity on discriminative power and precision",
                        "criteria": [
                            "Hypothesis targeting: Does the question distinguish between the current top 2-3 hypotheses? (0.0 generic, 0.5 partially targeting, 1.0 directly discriminating)",
                            "Answer actionability: Would each possible answer shift beliefs meaningfully toward different hypotheses? (0.0 all answers equivalent, 0.5 some differentiation, 1.0 each answer clearly maps to different hypotheses)",
                            "Specificity: Is the question about concrete details rather than abstract concepts? (0.0 very abstract, 0.5 moderate, 1.0 concrete and specific)",
                        ],
                        "formula": "CLARITY = mean of the three criteria scores",
                        "scale": "0.0 (non-discriminative) to 1.0 (maximally discriminative)",
                    },
                    "importance": {
                        "description": "Calculate importance based on dimension weight and uncertainty",
                        "formula": "IMPORTANCE = importance_base * (0.5 + 0.5 * current_entropy / h_max)",
                        "explanation": "Higher entropy (uncertainty) increases importance",
                    },
                    "eig": {
                        "description": "Estimate expected information gain from this question",
                        "approach": "Consider how well the question discriminates between hypotheses",
                        "criteria": [
                            "Does the question target high-probability hypotheses?",
                            "Would different answers clearly distinguish hypotheses?",
                            "Is the question relevant to current uncertainty?",
                        ],
                        "scale": "0.0 (no information) to h_max bits (maximum information)",
                        "heuristic": "Strong discriminating questions: 0.5-1.0 bits, Weak: 0.1-0.3 bits",
                    },
                },
                "instruction": (
                    "Calculate CLARITY (0.0-1.0), IMPORTANCE (0.0-1.0), and EIG (bits) "
                    "based on the formulas and data above. "
                    "Then compute: REWARD = EIG + 0.1 * CLARITY + 0.05 * IMPORTANCE. "
                    "If REWARD < 0.5, regenerate question. If REWARD >= 0.5, proceed to ask user."
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _apply_secondary_updates(
    args: argparse.Namespace,
    orch: SessionOrchestrator,
) -> list[dict[str, Any]]:
    """Apply cross-dimension secondary updates with reduced weight.

    Returns:
        List of secondary update result dicts
    """
    secondary_updates: list[dict[str, Any]] = []
    secondary_weight = orch.config["session_config"].get("secondary_update_weight", 0.3)

    if not getattr(args, "secondary_dimensions", None) or not getattr(
        args, "secondary_likelihoods", None
    ):
        return secondary_updates

    try:
        sec_likelihoods = json.loads(args.secondary_likelihoods)
    except json.JSONDecodeError:
        return secondary_updates

    sec_dims = [d.strip() for d in args.secondary_dimensions.split(",")]
    for sec_dim in sec_dims:
        if sec_dim not in orch.beliefs or sec_dim not in sec_likelihoods:
            continue

        sec_hs = orch.beliefs[sec_dim]
        sec_validated = validate_and_normalize_likelihoods(
            sec_hs, sec_likelihoods[sec_dim]
        )

        sec_posterior_before = dict(sec_hs.posterior)
        sec_h_before = sec_hs.entropy()
        sec_hs.update(sec_validated, weight=secondary_weight)
        sec_h_after = sec_hs.entropy()
        sec_jsd = compute_jsd(sec_posterior_before, sec_hs.posterior)
        sec_ig = sec_h_before - sec_h_after

        # Update cached values
        sec_h_max = math.log2(len(sec_hs.hypotheses))
        sec_hs._cached_entropy = sec_h_after
        sec_hs._cached_confidence = (
            1.0 - (sec_h_after / sec_h_max) if sec_h_max > 0 else 1.0
        )

        secondary_updates.append(
            {
                "dimension": sec_dim,
                "weight": secondary_weight,
                "entropy_before": round(sec_h_before, 4),
                "entropy_after": round(sec_h_after, 4),
                "information_gain": round(sec_ig, 4),
                "jsd": round(sec_jsd, 4),
            }
        )

    return secondary_updates


def cmd_update_with_computation(args: argparse.Namespace) -> None:
    """Update beliefs with complete computation chain (Phase B + C).

    Supports both single-select and multi-select answers:
    - Single: --likelihoods '{"h1": 0.5, "h2": 0.3}'
    - Multi:  --likelihoods '[{"h1": 0.8, ...}, {"h1": 0.3, ...}]'

    For multi-select, computes the joint likelihood (pointwise product)
    and performs a single Bayesian update, avoiding the negative
    information gain that sequential independent updates can produce.
    """
    orch = load_session_state(args.session_id)

    # Parse likelihoods from LLM
    try:
        likelihoods_raw = json.loads(args.likelihoods)
    except json.JSONDecodeError as e:
        print(
            json.dumps(
                {"error": f"Invalid JSON in --likelihoods: {e}"}, ensure_ascii=False
            ),
            file=sys.stderr,
        )
        sys.exit(1)

    # Phase B: Computation chain (Python)
    hs = orch.beliefs[args.dimension]

    # Detect multi-select batch (JSON array) vs single-select (JSON object)
    if isinstance(likelihoods_raw, list):
        validated_likelihoods = compute_joint_likelihoods(hs, likelihoods_raw)
    else:
        validated_likelihoods = validate_and_normalize_likelihoods(hs, likelihoods_raw)

    # B1: Entropy before + capture pre-update posterior for JSD
    h_before = hs.entropy()
    posterior_before = dict(hs.posterior)

    # B2: Dirichlet update with validated likelihoods
    hs.update(validated_likelihoods)

    # B3: Entropy after + JSD between pre/post distributions
    h_after = hs.entropy()
    jsd = compute_jsd(posterior_before, hs.posterior)

    # B4: Information gain
    info_gain = h_before - h_after

    # Cache results for session_orchestrator methods
    h_max = math.log2(len(hs.hypotheses))
    hs._cached_entropy = h_after
    hs._cached_confidence = 1.0 - (h_after / h_max) if h_max > 0 else 1.0

    # Build evaluation scores if provided
    evaluation_scores: dict[str, Any] | None = None
    if args.reward is not None:
        eig = max(0.0, args.eig) if args.eig is not None else 0.0
        evaluation_scores = {
            "total_reward": args.reward,
            "components": {
                "info_gain": eig,
                "clarity": args.clarity if args.clarity is not None else 0.0,
                "importance": args.importance if args.importance is not None else 0.0,
            },
            "confidence": hs._cached_confidence,
        }

    # Phase C: Persist to session history
    history_entry: dict[str, Any] = {
        "dimension": args.dimension,
        "question": args.question,
        "answer": args.answer,
        "entropy_before": h_before,
        "entropy_after": h_after,
        "information_gain": info_gain,
        "jsd": jsd,
    }
    if evaluation_scores is not None:
        history_entry["evaluation_scores"] = evaluation_scores

    # Cross-dimension secondary updates (P2.5)
    secondary_updates = _apply_secondary_updates(args, orch)
    if secondary_updates:
        history_entry["secondary_updates"] = secondary_updates

    orch.question_history.append(history_entry)
    orch.question_count += 1

    # Update Thompson Sampling state and record IG
    orch.update_thompson_state(args.dimension, info_gain)
    orch.record_information_gain(info_gain)

    # Save updated state
    save_session_state(args.session_id, orch)

    # Output results
    output: dict[str, Any] = {
        "status": "updated",
        "dimension": args.dimension,
        "entropy_before": round(h_before, 4),
        "entropy_after": round(h_after, 4),
        "information_gain": round(info_gain, 4),
        "jsd": round(jsd, 4),
        "question_count": orch.question_count,
    }
    if evaluation_scores is not None:
        output["evaluation_scores"] = evaluation_scores
    if secondary_updates:
        total_cross_dim_ig = sum(u["information_gain"] for u in secondary_updates)
        output["secondary_updates"] = secondary_updates
        output["total_cross_dimension_ig"] = round(total_cross_dim_ig, 4)
    print(json.dumps(output, ensure_ascii=False))


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Good Question session management CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init command
    subparsers.add_parser("init", help="Initialize new session")

    # next-question command
    next_parser = subparsers.add_parser("next-question", help="Get next question")
    next_parser.add_argument("--session-id", required=True, help="Session ID")

    # status command
    status_parser = subparsers.add_parser("status", help="Display session state")
    status_parser.add_argument("--session-id", required=True, help="Session ID")

    # complete command
    complete_parser = subparsers.add_parser("complete", help="Complete session")
    complete_parser.add_argument("--session-id", required=True, help="Session ID")

    # evaluate-question command
    eval_parser = subparsers.add_parser(
        "evaluate-question",
        help="Output question evaluation formulas and data for LLM calculation",
    )
    eval_parser.add_argument("--session-id", required=True, help="Session ID")
    eval_parser.add_argument("--dimension", required=True, help="Dimension ID")
    eval_parser.add_argument("--question", required=True, help="Question to evaluate")

    # update-with-computation command
    update_comp_parser = subparsers.add_parser(
        "update-with-computation",
        help="Update beliefs with complete computation chain (Phase B + C)",
    )
    update_comp_parser.add_argument("--session-id", required=True, help="Session ID")
    update_comp_parser.add_argument("--dimension", required=True, help="Dimension ID")
    update_comp_parser.add_argument("--question", required=True, help="Question asked")
    update_comp_parser.add_argument("--answer", required=True, help="User's answer")
    update_comp_parser.add_argument(
        "--likelihoods",
        type=str,
        required=True,
        help=(
            "Likelihoods as JSON object or array. "
            "Single: '{\"h1\": 0.5, ...}'. "
            'Multi-select: \'[{"h1": 0.8, ...}, {"h1": 0.3, ...}]\''
        ),
    )
    update_comp_parser.add_argument(
        "--reward",
        type=float,
        default=None,
        help="Total reward score from evaluation (optional)",
    )
    update_comp_parser.add_argument(
        "--eig",
        type=float,
        default=None,
        help="Expected information gain from evaluation (optional)",
    )
    update_comp_parser.add_argument(
        "--clarity",
        type=float,
        default=None,
        help="Clarity score from evaluation (optional)",
    )
    update_comp_parser.add_argument(
        "--importance",
        type=float,
        default=None,
        help="Importance score from evaluation (optional)",
    )
    update_comp_parser.add_argument(
        "--secondary-dimensions",
        type=str,
        default=None,
        help="Comma-separated secondary dimension IDs for cross-dim update",
    )
    update_comp_parser.add_argument(
        "--secondary-likelihoods",
        type=str,
        default=None,
        help='Secondary likelihoods as JSON: {"dim_id": {"hyp": prob}}',
    )

    args = parser.parse_args()

    # Dispatch to command handler
    if args.command == "init":
        cmd_init(args)
    elif args.command == "next-question":
        cmd_next_question(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "complete":
        cmd_complete(args)
    elif args.command == "evaluate-question":
        cmd_evaluate_question(args)
    elif args.command == "update-with-computation":
        cmd_update_with_computation(args)


if __name__ == "__main__":
    main()
