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
from with_me.lib.question_feedback_manager import QuestionFeedbackManager
from with_me.lib.session_orchestrator import SessionOrchestrator

# Convergence thresholds
DIMENSION_RESOLVED_THRESHOLD = (
    0.3  # Entropy threshold for considering a dimension resolved
)

# Likelihood validation constants
LIKELIHOOD_EPSILON = 1e-9  # Minimum non-zero likelihood value

# Minimum meaningful information gain per question
LOW_IG_THRESHOLD = 0.02


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

    # BALD decomposition for selected dimension
    hs = orch.beliefs[dimension]
    decomp = hs.uncertainty_decomposition()

    # Secondary dimension suggestions via presheaf
    suggested_secondary = orch.presheaf_checker.suggest_secondary_dimensions(
        dimension, orch.beliefs
    )

    # Theoretical maximum IG for a single question given current alpha state
    update_weight = orch.config["session_config"].get("update_weight", 1.0)
    alpha_sum = sum(hs.alpha.values())
    max_single_ig = round(math.log2((alpha_sum + update_weight) / alpha_sum), 4)

    # Recent questions for this dimension (last 2) to aid duplicate avoidance
    recent_questions = [
        q["question"] for q in orch.question_history if q.get("dimension") == dimension
    ][-2:]

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
                "posterior": hs.posterior,
                "epistemic_entropy": round(decomp["epistemic"], 4),
                "aleatoric_entropy": round(decomp["aleatoric"], 4),
                "epistemic_ratio": round(decomp["epistemic_ratio"], 4),
                "max_single_ig": max_single_ig,
                "question_count": orch.question_count,
                "recent_questions_this_dimension": recent_questions,
                "suggested_secondary_dimensions": suggested_secondary,
            },
            ensure_ascii=False,
        )
    )


def cmd_status(args: argparse.Namespace) -> None:
    """Display current session state."""
    orch = load_session_state(args.session_id)

    state = orch.get_current_state()
    compact = getattr(args, "compact", False)

    # Format for display
    output: dict[str, Any] = {
        "session_id": state["session_id"],
        "question_count": state["question_count"],
        "all_converged": state["all_converged"],
        "dimensions": {},
    }

    for dim_id, dim_data in state["dimensions"].items():
        if compact:
            output["dimensions"][dim_id] = {
                "confidence": round(dim_data["confidence"], 2),
                "converged": dim_data["converged"],
                "blocked": dim_data["blocked"],
            }
        else:
            output["dimensions"][dim_id] = {
                "name": dim_data["name"],
                "entropy": round(dim_data["entropy"], 2),
                "confidence": round(dim_data["confidence"], 2),
                "converged": dim_data["converged"],
                "blocked": dim_data["blocked"],
                "blocked_by": dim_data["blocked_by"],
                "most_likely": dim_data["most_likely"],
                "epistemic_entropy": round(dim_data["epistemic_entropy"], 4),
                "aleatoric_entropy": round(dim_data["aleatoric_entropy"], 4),
                "epistemic_ratio": round(dim_data["epistemic_ratio"], 4),
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

    # Per-dimension entropy lookup (used for dimensions_resolved threshold)
    final_entropies = {
        dim: belief.get("_cached_entropy") or 0 for dim, belief in beliefs.items()
    }
    # Normalize each dimension's entropy by its max possible entropy (log2 of
    # hypothesis count) so final_clarity stays in [0, 1].  Without normalization,
    # average entropy ~1.8 (4-hypothesis near-uniform prior) yields -0.8.
    normalized_ratios = []
    for belief in beliefs.values():
        entropy = belief.get("_cached_entropy") or 0
        n_hyp = len(belief.get("hypotheses") or [])
        h_max = math.log2(n_hyp) if n_hyp > 1 else 2.0  # default: 4-hyp H_max
        normalized_ratios.append(entropy / h_max)
    final_clarity = 1.0 - (
        sum(normalized_ratios) / len(normalized_ratios) if normalized_ratios else 0
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
                    "If REWARD < 0.6, regenerate question. If REWARD >= 0.6, proceed to ask user."
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
    """Apply cross-dimension secondary updates with reduced confidence.

    Returns:
        List of secondary update result dicts
    """
    secondary_updates: list[dict[str, Any]] = []
    update_weight = orch.config["session_config"].get("update_weight", 1.0)
    # Secondary confidence is proportional to secondary_update_weight (default 0.3)
    secondary_confidence = orch.config["session_config"].get(
        "secondary_update_weight", 0.3
    )

    if not getattr(args, "secondary_dimensions", None) or not getattr(
        args, "secondary_posteriors", None
    ):
        return secondary_updates

    try:
        sec_posteriors = json.loads(args.secondary_posteriors)
    except json.JSONDecodeError:
        return secondary_updates

    sec_dims = [d.strip() for d in args.secondary_dimensions.split(",")]
    for sec_dim in sec_dims:
        if sec_dim not in orch.beliefs or sec_dim not in sec_posteriors:
            continue

        sec_hs = orch.beliefs[sec_dim]
        sec_validated = validate_and_normalize_likelihoods(
            sec_hs, sec_posteriors[sec_dim]
        )

        sec_posterior_before = dict(sec_hs.posterior)
        sec_h_before = sec_hs.entropy()
        sec_hs.set_posterior_belief(sec_validated, secondary_confidence, update_weight)
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
                "confidence": secondary_confidence,
                "entropy_before": round(sec_h_before, 4),
                "entropy_after": round(sec_h_after, 4),
                "information_gain": round(sec_ig, 4),
                "jsd": round(sec_jsd, 4),
            }
        )

    return secondary_updates


def _record_to_feedback(
    args: argparse.Namespace,
    info_gain: float,
) -> None:
    """Record question result to feedback file if --feedback-session-id is set.

    Silently skips on failure so the main update operation is not interrupted.
    """
    if not getattr(args, "feedback_session_id", None):
        return
    try:
        feedback_manager = QuestionFeedbackManager()
        context: dict[str, Any] = {
            "dimension": args.dimension,
            "information_gain": round(info_gain, 4),
            "confidence": getattr(args, "confidence", 0.0),
        }
        reward: dict[str, Any] = {
            "total_reward": info_gain,
            "components": {"info_gain": info_gain},
            "confidence": getattr(args, "confidence", 0.0),
        }
        feedback_manager.record_question(
            args.feedback_session_id,
            args.question,
            args.dimension,
            context,
            {"text": args.answer},
            reward,
            information_gain=info_gain,
        )
    except (ValueError, OSError):
        pass  # Feedback failure does not block the main operation


def cmd_update_with_computation(args: argparse.Namespace) -> None:
    """Update beliefs from direct posterior estimate (Plan C).

    Claude states its posterior P(h | all evidence) directly with a
    confidence score, enabling larger single-step entropy reductions
    than likelihood-based Dirichlet updates.
    """
    orch = load_session_state(args.session_id)

    # Parse posterior from Claude
    try:
        posterior_raw = json.loads(args.posterior)
    except json.JSONDecodeError as e:
        print(
            json.dumps(
                {"error": f"Invalid JSON in --posterior: {e}"}, ensure_ascii=False
            ),
            file=sys.stderr,
        )
        sys.exit(1)

    hs = orch.beliefs[args.dimension]
    update_weight = orch.config["session_config"].get("update_weight", 1.0)

    # Validate and normalize the stated posterior
    validated_posterior = validate_and_normalize_likelihoods(hs, posterior_raw)

    # Capture pre-update state
    h_before = hs.entropy()
    posterior_before = dict(hs.posterior)

    # Apply direct posterior belief update
    hs.set_posterior_belief(validated_posterior, args.confidence, update_weight)

    # Compute metrics
    h_after = hs.entropy()
    jsd = compute_jsd(posterior_before, hs.posterior)
    info_gain = h_before - h_after

    # Cache results
    h_max = math.log2(len(hs.hypotheses))
    hs._cached_entropy = h_after
    hs._cached_confidence = 1.0 - (h_after / h_max) if h_max > 0 else 1.0

    # Persist to session history
    history_entry: dict[str, Any] = {
        "dimension": args.dimension,
        "question": args.question,
        "answer": args.answer,
        "entropy_before": h_before,
        "entropy_after": h_after,
        "information_gain": info_gain,
        "jsd": jsd,
        "confidence": args.confidence,
    }

    # Cross-dimension secondary updates
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

    # Auto-record to feedback file
    _record_to_feedback(args, info_gain)

    # BALD decomposition for updated dimension
    decomp = hs.uncertainty_decomposition()

    # low_ig: actual IG below meaningful threshold
    low_ig = info_gain < LOW_IG_THRESHOLD

    # Output results
    if getattr(args, "compact", False):
        output: dict[str, Any] = {
            "status": "updated",
            "information_gain": round(info_gain, 4),
            "low_ig": low_ig,
            "question_count": orch.question_count,
            "converged": orch.check_convergence(),
        }
    else:
        output = {
            "status": "updated",
            "dimension": args.dimension,
            "entropy_before": round(h_before, 4),
            "entropy_after": round(h_after, 4),
            "information_gain": round(info_gain, 4),
            "low_ig": low_ig,
            "jsd": round(jsd, 4),
            "question_count": orch.question_count,
            "epistemic_entropy": round(decomp["epistemic"], 4),
            "aleatoric_entropy": round(decomp["aleatoric"], 4),
        }
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
    status_parser.add_argument(
        "--compact",
        action="store_true",
        default=False,
        help="Output only confidence, converged, blocked per dimension",
    )

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
        "--posterior",
        type=str,
        required=True,
        help='Direct posterior estimate as JSON: \'{"h1": 0.7, "h2": 0.2, ...}\'',
    )
    update_comp_parser.add_argument(
        "--confidence",
        type=float,
        required=True,
        help="Confidence in the posterior estimate (0.0-1.0)",
    )
    update_comp_parser.add_argument(
        "--secondary-dimensions",
        type=str,
        default=None,
        help="Comma-separated secondary dimension IDs for cross-dim update",
    )
    update_comp_parser.add_argument(
        "--secondary-posteriors",
        type=str,
        default=None,
        help='Secondary posteriors as JSON: {"dim_id": {"hyp": prob}}',
    )
    update_comp_parser.add_argument(
        "--feedback-session-id",
        type=str,
        default=None,
        help="Feedback session ID for auto-recording to feedback file",
    )
    update_comp_parser.add_argument(
        "--compact",
        action="store_true",
        default=False,
        help="Output only status, information_gain, low_ig, question_count, converged",
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
