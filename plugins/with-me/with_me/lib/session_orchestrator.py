#!/usr/bin/env python3
"""
Session Orchestrator for Good Question Command

Coordinates the adaptive requirement elicitation process by managing:
- Session initialization with Bayesian beliefs
- Dimension selection based on entropy and prerequisites
- Question generation and ranking
- Convergence detection
- Post-session analysis invocation

This module encapsulates the core logic previously embedded in good-question.md,
allowing the command file to focus on user interaction via AskUserQuestion.
"""

import doctest
import json
import math
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from with_me.lib.dimension_belief import (
    HypothesisSet,
    create_default_dimension_beliefs,
)
from with_me.lib.knowledge_space import KnowledgeSpace
from with_me.lib.presheaf import PresheafChecker, load_restriction_maps
from with_me.lib.question_feedback_manager import QuestionFeedbackManager

# Thresholds
CONFIDENCE_THRESHOLD_FOR_DISPLAY = (
    0.5  # Minimum confidence to show most_likely hypothesis
)


class SessionOrchestrator:
    """
    Orchestrates adaptive requirement elicitation sessions.

    Responsibilities:
    - Initialize session with dimension beliefs
    - Select next dimension to query based on entropy + prerequisites
    - Generate questions for selected dimension
    - Update beliefs after receiving answers
    - Detect convergence and terminate session

    Examples:
        >>> # Initialize orchestrator
        >>> from pathlib import Path
        >>> orch = SessionOrchestrator(
        ...     feedback_file_path=Path("/tmp/test_feedback.json")
        ... )
        >>> session_id = orch.initialize_session()

        >>> # Main loop (simplified) - use demo mode for actual testing
        >>> # while not orch.check_convergence():
        >>> #     dim, question = orch.select_next_question()
        >>> #     answer = input(question)  # Ask user
        >>> #     orch.update_beliefs(dim, question, answer)

        >>> # Get final analysis
        >>> summary = orch.complete_session()
        >>> summary["total_questions"] == 0  # No questions asked in doctest
        True
    """

    def __init__(
        self, config_path: str | None = None, feedback_file_path: Path | None = None
    ):
        """
        Initialize orchestrator with configuration.

        Args:
            config_path: Path to dimensions.json config file
                        If None, uses default location
            feedback_file_path: Path to feedback JSON file for testing
                               If None, uses default location from environment
        """
        # Load configuration
        if config_path is None:
            # Path: with_me/lib/session_orchestrator.py → plugins/with-me/
            plugin_root = Path(__file__).parent.parent.parent
            config_path = str(plugin_root / "config" / "dimensions.json")

        with open(config_path) as f:
            self.config = json.load(f)

        # Initialize components
        self.manager = QuestionFeedbackManager(feedback_file_path)
        restriction_maps = load_restriction_maps(self.config)
        consistency_threshold = self.config.get("session_config", {}).get(
            "consistency_threshold", 0.3
        )
        self.presheaf_checker = PresheafChecker(restriction_maps, consistency_threshold)

        # Initialize KST knowledge space
        items = list(self.config["dimensions"].keys())
        prerequisites = {
            dim_id: dim_data.get("prerequisites", [])
            for dim_id, dim_data in self.config["dimensions"].items()
        }
        self.knowledge_space = KnowledgeSpace(items, prerequisites)
        self._dag_edges: list[tuple[str, str]] = [
            (e["from"], e["to"]) for e in self.config.get("dag", {}).get("edges", [])
        ]

        # Session state (initialized in initialize_session)
        self.session_id: str | None = None
        self.beliefs: dict[str, HypothesisSet] = {}
        self.question_history: list[dict[str, Any]] = []
        self.question_count = 0
        self.recent_information_gains: list[float] = []
        self.thompson_states: dict[str, dict[str, float]] = {}

    def initialize_session(self) -> str:
        """
        Initialize a new requirement elicitation session.

        Creates:
        - Uniform prior distributions for all dimensions
        - Empty question history

        Feedback tracking is handled externally via the CLI's ``feedback start``
        command, not by the orchestrator.

        Returns:
            Session ID for tracking

        Examples:
            >>> from pathlib import Path
        >>> orch = SessionOrchestrator(
        ...     feedback_file_path=Path("/tmp/test_feedback.json")
        ... )
            >>> session_id = orch.initialize_session()
            >>> len(session_id) > 0
            True
        """
        # Create default dimension beliefs (uniform priors)
        self.beliefs = create_default_dimension_beliefs()

        # Generate session ID (feedback tracking via CLI's `feedback start` command)
        self.session_id = datetime.now().isoformat()

        # Initialize tracking
        self.question_history = []
        self.question_count = 0
        self.recent_information_gains = []

        # Initialize Thompson Sampling states per dimension
        self.thompson_states = {}
        for dim_id in self.beliefs:
            dim_config = self.config["dimensions"][dim_id]
            importance = dim_config["importance"]
            # Initial entropy is H_max (uniform prior), normalized to [0, 1]
            normalized_entropy = 1.0  # uniform prior → max entropy
            self.thompson_states[dim_id] = {
                "alpha": 1.0 + importance * normalized_entropy,
                "beta": 1.0,
            }

        return self.session_id

    def record_information_gain(self, ig: float) -> None:
        """
        Record information gain from a question for diminishing returns tracking.

        Args:
            ig: Information gain in bits from the last question

        Examples:
            >>> from pathlib import Path
            >>> orch = SessionOrchestrator(
            ...     feedback_file_path=Path("/tmp/test_feedback.json")
            ... )
            >>> _ = orch.initialize_session()
            >>> orch.record_information_gain(0.5)
            >>> orch.record_information_gain(0.3)
            >>> len(orch.recent_information_gains)
            2
        """
        self.recent_information_gains.append(ig)

    def check_convergence(self) -> bool:
        """
        Check if session has converged using multiple criteria.

        Convergence criteria (any triggers stop):
        1. Max question limit reached (safety fallback)
        2. Diminishing returns: max IG of last N questions < epsilon
        3. Normalized confidence: all dimensions above target_confidence

        Normalized confidence uses 1 - H/H_max instead of a fixed entropy
        threshold, ensuring consistent convergence across dimensions with
        different hypothesis counts.

        Returns:
            True if converged, False otherwise

        Examples:
            >>> from pathlib import Path
            >>> orch = SessionOrchestrator(
            ...     feedback_file_path=Path("/tmp/test_feedback.json")
            ... )
            >>> _ = orch.initialize_session()
            >>> # Initially not converged (uniform priors → confidence = 0)
            >>> orch.check_convergence()
            False

            >>> # Diminishing returns: all recent IG below epsilon
            >>> orch.question_count = 6  # past min_questions
            >>> orch.recent_information_gains = [0.8, 0.5, 0.3, 0.02, 0.01, 0.03]
            >>> orch.check_convergence()
            True

            >>> # Normalized convergence: all dimensions above target_confidence
            >>> orch2 = SessionOrchestrator(
            ...     feedback_file_path=Path("/tmp/test_feedback2.json")
            ... )
            >>> _ = orch2.initialize_session()
            >>> # Set high confidence on all 7 dimensions
            >>> # purpose (4 hyps): H_max=2.0, H=0.2 → confidence=0.9
            >>> orch2.beliefs["purpose"]._cached_entropy = 0.2
            >>> # context (4 hyps): H=0.2 → confidence=0.9
            >>> orch2.beliefs["context"]._cached_entropy = 0.2
            >>> # data (3 hyps): H_max≈1.585, H=0.15 → confidence≈0.905
            >>> orch2.beliefs["data"]._cached_entropy = 0.15
            >>> # behavior (4 hyps): H=0.1 → confidence=0.95
            >>> orch2.beliefs["behavior"]._cached_entropy = 0.1
            >>> # stakeholders (4 hyps): H=0.2 → confidence=0.9
            >>> orch2.beliefs["stakeholders"]._cached_entropy = 0.2
            >>> # constraints (4 hyps): H=0.25 → confidence=0.875
            >>> orch2.beliefs["constraints"]._cached_entropy = 0.25
            >>> # quality (3 hyps): H=0.1 → confidence≈0.937
            >>> orch2.beliefs["quality"]._cached_entropy = 0.1
            >>> orch2.check_convergence()
            True
        """
        # 1. Max question limit (safety fallback)
        max_questions = self.config["session_config"]["max_questions"]
        if self.question_count >= max_questions:
            return True

        # 2. Diminishing returns: recent IG all below epsilon
        window = self.config["session_config"].get("diminishing_returns_window", 3)
        epsilon = self.config["session_config"].get("diminishing_returns_epsilon", 0.05)
        min_questions = self.config["session_config"].get("min_questions", 5)
        if (
            self.question_count >= min_questions
            and len(self.recent_information_gains) >= window
        ):
            recent = self.recent_information_gains[-window:]
            if max(recent) < epsilon:
                return True

        # 3. Normalized convergence: all dimensions above target_confidence
        target_confidence = self.config["session_config"].get("target_confidence", 0.85)
        for hs in self.beliefs.values():
            if hs._cached_entropy is None:
                # No cached entropy - session just started, not converged
                return False
            h_max = math.log2(len(hs.hypotheses))
            confidence = 1.0 - (hs._cached_entropy / h_max)
            if confidence < target_confidence:
                return False

        return True

    def _get_current_kst_state(self) -> frozenset[str]:
        """Get current feasible knowledge state from beliefs via KST.

        Uses entropy threshold to determine which dimensions are "resolved",
        then computes the maximal feasible subset via prerequisite clamping.

        Returns:
            Feasible knowledge state (frozenset of resolved dimension IDs)

        Examples:
            >>> from pathlib import Path
            >>> orch = SessionOrchestrator(
            ...     feedback_file_path=Path("/tmp/test_feedback.json")
            ... )
            >>> _ = orch.initialize_session()
            >>> orch._get_current_kst_state()  # All uniform → empty state
            frozenset()

            >>> orch.beliefs["purpose"]._cached_entropy = 0.5
            >>> sorted(orch._get_current_kst_state())
            ['purpose']
        """
        threshold = self.config["session_config"].get(
            "prerequisite_threshold_default", 1.8
        )
        return self.knowledge_space.current_state_from_beliefs(self.beliefs, threshold)

    def _get_accessible_dimensions(
        self,
    ) -> list[tuple[str, float, float, float]]:
        """Get accessible dimensions with normalized entropy, importance, and epistemic score.

        Uses KST outer fringe to determine which dimensions are accessible
        based on the current feasible knowledge state.

        Returns:
            List of (dim_id, normalized_entropy, importance, epistemic_score) tuples.
            epistemic_score = epistemic_entropy / H_max, measuring reducible uncertainty.

        Examples:
            >>> from pathlib import Path
            >>> orch = SessionOrchestrator(
            ...     feedback_file_path=Path("/tmp/test_feedback.json")
            ... )
            >>> _ = orch.initialize_session()
            >>> accessible = orch._get_accessible_dimensions()
            >>> any(d[0] == "purpose" for d in accessible)
            True
            >>> all(len(d) == 4 for d in accessible)
            True

            >>> # With purpose resolved, dependent dimensions become accessible
            >>> orch_p = SessionOrchestrator(
            ...     feedback_file_path=Path("/tmp/test_feedback_p.json")
            ... )
            >>> _ = orch_p.initialize_session()
            >>> orch_p.beliefs["purpose"]._cached_entropy = 0.5
            >>> accessible_p = orch_p._get_accessible_dimensions()
            >>> ids_p = {d[0] for d in accessible_p}
            >>> "data" in ids_p  # data requires purpose ✓
            True
            >>> "behavior" in ids_p  # behavior requires purpose ✓
            True
            >>> "constraints" not in ids_p  # constraints requires behavior AND data
            True
        """
        current_state = self._get_current_kst_state()
        fringe = self.knowledge_space.outer_fringe(current_state)

        # Include dimensions in current_state that haven't converged yet.
        # A dimension enters current_state when entropy < prerequisite_threshold (1.8),
        # but still needs questions until entropy < convergence_threshold (0.3).
        conv_threshold = self.config["session_config"]["convergence_threshold"]
        unconverged_in_state = frozenset(
            d
            for d in current_state
            if d in self.beliefs
            and (
                self.beliefs[d]._cached_entropy is None
                or self.beliefs[d]._cached_entropy >= conv_threshold
            )
        )
        queryable = fringe | unconverged_in_state

        accessible = []
        for dim_id in queryable:
            hs = self.beliefs[dim_id]
            dim_config = self.config["dimensions"][dim_id]

            raw_entropy = (
                hs._cached_entropy
                if hs._cached_entropy is not None
                else math.log2(len(hs.hypotheses))
            )
            h_max = math.log2(len(hs.hypotheses))
            normalized_entropy = raw_entropy / h_max

            # Compute epistemic score from Dirichlet alpha
            epistemic_score = hs.epistemic_entropy() / h_max if h_max > 0 else 0.0

            accessible.append(
                (
                    dim_id,
                    normalized_entropy,
                    dim_config["importance"],
                    epistemic_score,
                )
            )

        return accessible

    def select_next_dimension(self, deterministic: bool = True) -> str | None:
        """
        Select next dimension to query.

        Two modes:
        - deterministic=True: Greedy selection by epistemic entropy score,
          prioritizing dimensions with the most reducible uncertainty (BALD).
        - deterministic=False: Thompson Sampling with Beta distribution for
          exploration-exploitation balance

        Args:
            deterministic: If True, use greedy epistemic-based selection.
                          If False, use Thompson Sampling.

        Returns:
            Dimension ID to query, or None if no accessible dimensions

        Examples:
            >>> from pathlib import Path
            >>> orch = SessionOrchestrator(
            ...     feedback_file_path=Path("/tmp/test_feedback.json")
            ... )
            >>> _ = orch.initialize_session()
            >>> dim = orch.select_next_dimension()
            >>> dim == "purpose"  # Purpose has no prerequisites
            True

            >>> # Epistemic score prioritizes reducible uncertainty
            >>> # Set purpose as converged so data, behavior, stakeholders accessible
            >>> orch.beliefs["purpose"]._cached_entropy = 0.5
            >>> # Converge context and stakeholders so they don't dominate
            >>> orch.beliefs["context"]._cached_entropy = 0.2
            >>> orch.beliefs["stakeholders"]._cached_entropy = 0.2
            >>> # behavior (4 hyps): raw=1.8, normalized=1.8/2.0=0.90
            >>> orch.beliefs["behavior"]._cached_entropy = 1.8
            >>> # data (3 hyps): raw=1.5, normalized=1.5/log₂(3)≈0.946
            >>> orch.beliefs["data"]._cached_entropy = 1.5
            >>> # With uniform priors (alpha=1), epistemic score ≈ normalized entropy
            >>> # data still wins because its epistemic/H_max ratio is highest
            >>> orch.select_next_dimension()
            'data'

            >>> # Thompson Sampling with fixed seed for reproducibility
            >>> random.seed(42)
            >>> dim_ts = orch.select_next_dimension(deterministic=False)
            >>> dim_ts in [
            ...     "purpose",
            ...     "context",
            ...     "data",
            ...     "behavior",
            ...     "stakeholders",
            ...     "constraints",
            ...     "quality",
            ... ]
            True

            >>> # Context bonus: with purpose in KST state, adjacent outer fringe dims
            >>> # (data, behavior, stakeholders) receive +0.1 per connected inner fringe dim
            >>> orch_cb = SessionOrchestrator(
            ...     feedback_file_path=Path("/tmp/test_feedback_cb.json")
            ... )
            >>> _ = orch_cb.initialize_session()
            >>> orch_cb.beliefs["purpose"]._cached_entropy = 0.5  # purpose resolved
            >>> state_cb = orch_cb._get_current_kst_state()
            >>> sorted(state_cb)
            ['purpose']
            >>> adj = orch_cb.knowledge_space.adjacent_dimensions(
            ...     state_cb, orch_cb._dag_edges
            ... )
            >>> "purpose" in adj["data"]  # data connected to purpose via DAG edge
            True
            >>> "purpose" in adj["behavior"]  # behavior connected to purpose
            True
            >>> "purpose" in adj["stakeholders"]  # stakeholders connected to purpose
            True
            >>> len(adj["context"]) == 0  # context has no DAG edge to inner fringe
            True
        """
        accessible = self._get_accessible_dimensions()

        if not accessible:
            return None

        # Compute context bonus from inner fringe adjacency
        current_state = self._get_current_kst_state()
        adjacency = self.knowledge_space.adjacent_dimensions(
            current_state, self._dag_edges
        )
        context_bonus_weight = self.config["session_config"].get(
            "context_bonus_weight", 0.1
        )

        if deterministic:
            # Fatigue penalty: reduce score for dimensions asked many times so
            # the system naturally diversifies to under-explored dimensions.
            fatigue_weight = self.config["session_config"].get("fatigue_weight", 0.05)
            questions_per_dim: dict[str, int] = {}
            for q in self.question_history:
                d = q.get("dimension", "")
                questions_per_dim[d] = questions_per_dim.get(d, 0) + 1

            # Greedy: sort by epistemic score + context bonus - fatigue (desc),
            # then importance (desc)
            def _score(x: tuple[str, float, float, float]) -> tuple[float, float]:
                dim_id = x[0]
                bonus = context_bonus_weight * len(adjacency.get(dim_id, set()))
                fatigue = fatigue_weight * questions_per_dim.get(dim_id, 0)
                return (x[3] + bonus - fatigue, x[2])

            accessible.sort(key=_score, reverse=True)
            return accessible[0][0]

        # Thompson Sampling: sample Beta(alpha, beta) + context bonus
        best_dim = None
        best_sample = -1.0

        for dim_id, _norm_ent, _importance, _epi_score in accessible:
            ts = self.thompson_states.get(dim_id, {"alpha": 1.0, "beta": 1.0})
            bonus = context_bonus_weight * len(adjacency.get(dim_id, set()))
            sample = random.betavariate(ts["alpha"], ts["beta"]) + bonus
            if sample > best_sample:
                best_sample = sample
                best_dim = dim_id

        return best_dim

    def update_thompson_state(self, dimension: str, information_gain: float) -> None:
        """
        Update Thompson Sampling state based on information gain.

        If IG > epsilon (informative question), increment alpha (success).
        Otherwise increment beta (failure/low-information).

        Args:
            dimension: Dimension ID that was queried
            information_gain: IG in bits from the question

        Examples:
            >>> from pathlib import Path
            >>> orch = SessionOrchestrator(
            ...     feedback_file_path=Path("/tmp/test_feedback.json")
            ... )
            >>> _ = orch.initialize_session()
            >>> # Successful question (high IG)
            >>> orch.update_thompson_state("purpose", 0.5)
            >>> orch.thompson_states["purpose"]["alpha"]
            3.0
            >>> orch.thompson_states["purpose"]["beta"]
            1.0

            >>> # Uninformative question (low IG)
            >>> orch.update_thompson_state("purpose", 0.01)
            >>> orch.thompson_states["purpose"]["alpha"]
            3.0
            >>> orch.thompson_states["purpose"]["beta"]
            2.0
        """
        epsilon = self.config["session_config"].get("diminishing_returns_epsilon", 0.05)

        if dimension not in self.thompson_states:
            self.thompson_states[dimension] = {"alpha": 1.0, "beta": 1.0}

        if information_gain > epsilon:
            self.thompson_states[dimension]["alpha"] += 1.0
        else:
            self.thompson_states[dimension]["beta"] += 1.0

    def generate_question(self, dimension: str) -> str:
        """
        Generate a question for the specified dimension.

        NOTE: Question generation now handled by Claude in good-question.md.
        This method returns a placeholder for backward compatibility.

        Args:
            dimension: Dimension ID to generate question for

        Returns:
            Placeholder question text

        Examples:
            >>> from pathlib import Path
        >>> orch = SessionOrchestrator(
        ...     feedback_file_path=Path("/tmp/test_feedback.json")
        ... )
            >>> _ = orch.initialize_session()
            >>> question = orch.generate_question("purpose")
            >>> "placeholder" in question.lower()
            True
        """
        # Question generation now handled by Claude in good-question.md workflow
        # See Step 2.1-2.2 for context-aware question generation
        dim_name = self.config["dimensions"][dimension]["name"]
        return f"[Placeholder: Claude generates question for {dim_name} dimension]"

    # calculate_question_reward() removed - use skills instead:
    # - /with-me:question-clarity
    # - /with-me:question-importance
    # - /with-me:eig-calculation
    #
    # Reward function: r(Q) = EIG(Q) + 0.1 * clarity(Q) + 0.05 * importance(Q)

    def select_next_question(self) -> tuple[str, str] | tuple[None, None]:
        """
        Select next question to ask user.

        Combines dimension selection with question generation.

        Returns:
            Tuple of (dimension, question) or (None, None) if converged

        Examples:
            >>> from pathlib import Path
        >>> orch = SessionOrchestrator(
        ...     feedback_file_path=Path("/tmp/test_feedback.json")
        ... )
            >>> _ = orch.initialize_session()
            >>> dim, question = orch.select_next_question()
            >>> dim == "purpose"  # Purpose has no prerequisites
            True
            >>> "placeholder" in question.lower()
            True
        """
        # Select dimension
        dimension = self.select_next_dimension()
        if dimension is None:
            return None, None

        # Generate question placeholder
        question = self.generate_question(dimension)

        return dimension, question

    # update_beliefs() removed - use CLI workflow instead:
    # 1. compute-entropy to get H_before
    # 2. bayesian-update with Claude skill
    # 3. persist-computation to save results
    #
    # See commands/good-question.md Step 2.3 for new workflow

    def update_beliefs(
        self, dimension: str, question: str, answer: str
    ) -> dict[str, Any]:
        """
        Update beliefs for a dimension based on answer.

        Note: This is a stub for testing. Actual belief updates are performed
        by the CLI (session.py) using Bayesian updates with LLM-generated likelihoods.

        Args:
            dimension: Dimension ID to update
            question: Question that was asked
            answer: Answer received

        Returns:
            Dictionary with update results (stub values for demo)

        Examples:
            >>> from pathlib import Path
        >>> orch = SessionOrchestrator(
        ...     feedback_file_path=Path("/tmp/test_feedback.json")
        ... )
            >>> _ = orch.initialize_session()
            >>> result = orch.update_beliefs("purpose", "What?", "Web app")
            >>> "information_gain" in result
            True
        """
        self.question_count += 1
        return {
            "information_gain": 0.0,
            "entropy_before": 1.0,
            "entropy_after": 1.0,
        }

    def get_current_state(self) -> dict[str, Any]:
        """
        Get current session state for display.

        Returns:
            Dictionary with entropy, confidence, convergence status per dimension

        Examples:
            >>> from pathlib import Path
        >>> orch = SessionOrchestrator(
        ...     feedback_file_path=Path("/tmp/test_feedback.json")
        ... )
            >>> _ = orch.initialize_session()
            >>> state = orch.get_current_state()
            >>> "dimensions" in state
            True
        """
        conv_threshold = self.config["session_config"]["convergence_threshold"]
        current_state = self._get_current_kst_state()

        dimensions = {}
        for dim_id, hs in self.beliefs.items():
            # Use cached values from persist-computation
            entropy = (
                hs._cached_entropy
                if hs._cached_entropy is not None
                else math.log2(len(hs.hypotheses))
            )
            confidence = (
                hs._cached_confidence if hs._cached_confidence is not None else 0.0
            )
            converged = entropy < conv_threshold

            # Check if blocked by prerequisites (KST-based)
            dim_config = self.config["dimensions"][dim_id]
            prereqs = dim_config["prerequisites"]
            blocked_by = [p for p in prereqs if p not in current_state]

            # BALD decomposition
            decomp = hs.uncertainty_decomposition()

            dimensions[dim_id] = {
                "name": dim_config["name"],
                "entropy": entropy,
                "confidence": confidence,
                "converged": converged,
                "blocked": len(blocked_by) > 0,
                "blocked_by": blocked_by,
                "most_likely": hs.get_most_likely()
                if confidence > CONFIDENCE_THRESHOLD_FOR_DISPLAY
                else None,
                "epistemic_entropy": decomp["epistemic"],
                "aleatoric_entropy": decomp["aleatoric"],
                "epistemic_ratio": decomp["epistemic_ratio"],
            }

        # Presheaf consistency check
        consistency_results = self.presheaf_checker.check_consistency(self.beliefs)
        consistency = [
            {
                "edge": f"{r.source_dim}->{r.target_dim}",
                "jsd": round(r.jsd, 4),
                "is_consistent": r.is_consistent,
            }
            for r in consistency_results
        ]

        return {
            "session_id": self.session_id,
            "question_count": self.question_count,
            "dimensions": dimensions,
            "consistency": consistency,
            "all_converged": self.check_convergence(),
        }

    def complete_session(self) -> dict[str, Any]:
        """
        Complete session and return summary.

        Computes summary from current beliefs and question history without
        touching the feedback manager (feedback finalization is done via
        the CLI's ``feedback complete`` command).

        Returns:
            Dictionary with session summary

        Examples:
            >>> from pathlib import Path
        >>> orch = SessionOrchestrator(
        ...     feedback_file_path=Path("/tmp/test_feedback.json")
        ... )
            >>> _ = orch.initialize_session()
            >>> summary = orch.complete_session()
            >>> summary["total_questions"] == 0
            True
        """
        total_questions = self.question_count
        total_info_gain = sum(
            q.get("information_gain", 0) for q in self.question_history
        )
        rewards = [
            q["evaluation_scores"]["total_reward"]
            for q in self.question_history
            if "evaluation_scores" in q
        ]
        avg_reward = sum(rewards) / len(rewards) if rewards else 0.0

        conv_threshold = self.config["session_config"]["convergence_threshold"]
        normalized_ratios = []
        for hs in self.beliefs.values():
            entropy = hs._cached_entropy or 0
            n_hyp = len(hs.hypotheses)
            h_max = math.log2(n_hyp) if n_hyp > 1 else 2.0
            normalized_ratios.append(entropy / h_max)
        final_clarity = 1.0 - (
            sum(normalized_ratios) / len(normalized_ratios) if normalized_ratios else 0
        )

        dimensions_resolved = [
            dim
            for dim, hs in self.beliefs.items()
            if (hs._cached_entropy or 0) < conv_threshold
        ]

        return {
            "total_questions": total_questions,
            "avg_reward_per_question": avg_reward,
            "total_info_gain": total_info_gain,
            "final_clarity_score": final_clarity,
            "dimensions_resolved": dimensions_resolved,
            "session_efficiency": total_info_gain / total_questions
            if total_questions > 0
            else 0,
        }


# CLI interface for testing
def main():
    """Command-line interface for testing orchestrator."""
    min_argc = 2  # program name + command
    if len(sys.argv) < min_argc:
        print("Usage: python3 -m with_me.lib.session_orchestrator <command>")
        print("\nCommands:")
        print("  demo     - Run interactive demonstration")
        print("  test     - Run doctests")
        sys.exit(1)

    command = sys.argv[1]

    if command == "demo":
        # Interactive demonstration
        orch = SessionOrchestrator()
        session_id = orch.initialize_session()
        print(f"Session initialized: {session_id}\n")

        # Show initial state
        state = orch.get_current_state()
        print("Initial uncertainties:")
        for dim_data in state["dimensions"].values():
            print(f"  {dim_data['name']}: H={dim_data['entropy']:.2f} bits")

        # Generate first question
        dim, question = orch.select_next_question()
        if dim is None or question is None:
            print("No question available")
            sys.exit(1)
        print(f"\nNext question (targeting {dim}): {question}")

        # Simulate answer
        answer = "web application for users"
        print(f"Simulated answer: {answer}")

        # Update beliefs
        result = orch.update_beliefs(dim, question, answer)
        print(f"\nInformation gained: {result['information_gain']:.3f} bits")
        print(
            f"Entropy: {result['entropy_before']:.2f} → {result['entropy_after']:.2f}"
        )

        # Complete session
        summary = orch.complete_session()
        print(f"\nSession complete: {summary['total_questions']} questions asked")

    elif command == "test":
        print("Running doctests...")
        result = doctest.testmod()
        if result.failed == 0:
            print("✓ All doctests passed")
        else:
            print(f"✗ {result.failed} doctest(s) failed")
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
