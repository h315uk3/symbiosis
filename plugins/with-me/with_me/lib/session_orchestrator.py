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
import sys
from pathlib import Path
from typing import Any

from with_me.lib.dimension_belief import (
    HypothesisSet,
    create_default_dimension_beliefs,
)
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
        >>> orch = SessionOrchestrator()
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

    def __init__(self, config_path: str | None = None):
        """
        Initialize orchestrator with configuration.

        Args:
            config_path: Path to dimensions.json config file
                        If None, uses default location
        """
        # Load configuration
        if config_path is None:
            # Path: with_me/lib/session_orchestrator.py → plugins/with-me/
            plugin_root = Path(__file__).parent.parent.parent
            config_path = str(plugin_root / "config" / "dimensions.json")

        with open(config_path) as f:
            self.config = json.load(f)

        # Initialize components
        self.manager = QuestionFeedbackManager()

        # Session state (initialized in initialize_session)
        self.session_id: str | None = None
        self.beliefs: dict[str, HypothesisSet] = {}
        self.question_history: list[str] = []
        self.question_count = 0

    def initialize_session(self) -> str:
        """
        Initialize a new requirement elicitation session.

        Creates:
        - Uniform prior distributions for all dimensions
        - Session record in feedback manager
        - Empty question history

        Returns:
            Session ID for tracking

        Examples:
            >>> orch = SessionOrchestrator()
            >>> session_id = orch.initialize_session()
            >>> len(session_id) > 0
            True
        """
        # Create default dimension beliefs (uniform priors)
        self.beliefs = create_default_dimension_beliefs()

        # Start session in feedback manager
        self.session_id = self.manager.start_session(
            initial_dimension_beliefs={k: v.to_dict() for k, v in self.beliefs.items()}
        )

        # Initialize tracking
        self.question_history = []
        self.question_count = 0

        return self.session_id

    def check_convergence(self) -> bool:
        """
        Check if session has converged (all dimensions clear).

        Convergence criteria:
        1. All dimensions have H(h) < convergence_threshold
        2. Max question limit not exceeded

        Returns:
            True if converged, False otherwise

        Examples:
            >>> orch = SessionOrchestrator()
            >>> _ = orch.initialize_session()
            >>> # Initially not converged (uniform priors)
            >>> orch.check_convergence()
            False
        """
        # Check max question limit
        max_questions = self.config["session_config"]["max_questions"]
        if self.question_count >= max_questions:
            return True

        # Check entropy thresholds (use cached values from persist-computation)
        conv_threshold = self.config["session_config"]["convergence_threshold"]
        for hs in self.beliefs.values():
            if hs._cached_entropy is None:
                # No cached entropy - session just started, not converged
                return False
            if hs._cached_entropy >= conv_threshold:
                return False

        return True

    def select_next_dimension(self) -> str | None:
        """
        Select next dimension to query based on entropy and prerequisites.

        Algorithm:
        1. Filter dimensions by prerequisite satisfaction
        2. Sort by entropy (descending) then importance
        3. Return highest-entropy accessible dimension

        Returns:
            Dimension ID to query, or None if no accessible dimensions

        Examples:
            >>> orch = SessionOrchestrator()
            >>> _ = orch.initialize_session()
            >>> dim = orch.select_next_dimension()
            >>> dim == "purpose"  # Purpose has no prerequisites
            True
        """
        accessible = []

        for dim_id, hs in self.beliefs.items():
            # Check prerequisites
            dim_config = self.config["dimensions"][dim_id]
            prereqs = dim_config["prerequisites"]
            prereq_threshold = dim_config.get("prerequisite_threshold", 1.5)

            # Get cached entropy (use large value if not cached)
            prereq_satisfied = True
            for prereq in prereqs:
                prereq_entropy = self.beliefs[prereq]._cached_entropy
                if prereq_entropy is None or prereq_entropy >= prereq_threshold:
                    prereq_satisfied = False
                    break

            if prereq_satisfied:
                # Use cached entropy or default to high value (max entropy for N hypotheses)
                entropy = (
                    hs._cached_entropy
                    if hs._cached_entropy is not None
                    else math.log2(len(hs.hypotheses))
                )
                accessible.append((dim_id, entropy, dim_config["importance"]))

        if not accessible:
            return None  # No accessible dimensions

        # Sort by entropy (descending), then by importance (descending)
        accessible.sort(key=lambda x: (x[1], x[2]), reverse=True)

        return accessible[0][0]  # Return dimension ID

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
            >>> orch = SessionOrchestrator()
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
            >>> orch = SessionOrchestrator()
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

    def get_current_state(self) -> dict[str, Any]:
        """
        Get current session state for display.

        Returns:
            Dictionary with entropy, confidence, convergence status per dimension

        Examples:
            >>> orch = SessionOrchestrator()
            >>> _ = orch.initialize_session()
            >>> state = orch.get_current_state()
            >>> "dimensions" in state
            True
        """
        conv_threshold = self.config["session_config"]["convergence_threshold"]

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

            # Check if blocked by prerequisites
            dim_config = self.config["dimensions"][dim_id]
            prereqs = dim_config["prerequisites"]
            prereq_threshold = dim_config.get("prerequisite_threshold", 1.5)

            blocked_by = []
            for prereq in prereqs:
                prereq_entropy = self.beliefs[prereq]._cached_entropy
                if prereq_entropy is None or prereq_entropy >= prereq_threshold:
                    blocked_by.append(prereq)

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
            }

        return {
            "session_id": self.session_id,
            "question_count": self.question_count,
            "dimensions": dimensions,
            "all_converged": self.check_convergence(),
        }

    def complete_session(self) -> dict[str, Any]:
        """
        Complete session and return summary.

        Calls feedback manager to finalize session with statistics.

        Returns:
            Dictionary with session summary

        Examples:
            >>> orch = SessionOrchestrator()
            >>> _ = orch.initialize_session()
            >>> summary = orch.complete_session()
            >>> summary["total_questions"] == 0
            True
        """
        # Calculate final uncertainties using cached entropy values
        final_uncertainties = {
            dim: hs._cached_entropy if hs._cached_entropy is not None else 0.0
            for dim, hs in self.beliefs.items()
        }

        # Complete session in feedback manager
        summary = self.manager.complete_session(
            session_id=self.session_id or "unknown",
            final_uncertainties=final_uncertainties,
            final_dimension_beliefs={k: v.to_dict() for k, v in self.beliefs.items()},
        )

        return summary


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
