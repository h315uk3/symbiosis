#!/usr/bin/env python3
"""
Question Reward Calculator for with-me plugin (v0.3.0)

MIGRATION COMPLETE: All computational algorithms have been moved to skills.
This module now provides only type definitions for API contract.

Reward Function:
    r(Q) = EIG(Q) + 0.1×clarity(Q) + 0.05×importance(Q)

Computation is delegated to:
- /with-me:eig-calculation skill: EIG(Q) = Σ P(a|Q) × [H_before - H_after(a)]
- /with-me:question-clarity skill: clarity(Q) evaluation
- /with-me:question-importance skill: importance(Q) scoring
- /with-me:entropy skill: H(h) = -Σ p(h) log₂ p(h)
- /with-me:bayesian-update skill: p₁(h) ∝ p₀(h) × L(obs|h)

API Contract (Issue #54):
- Standardized interface for as-you plugin integration
- Type-safe input/output with QuestionContext and RewardResponse

Usage:
    Claude reads the skill markdown files and performs computations directly.
    Python code should only prepare input context and parse output results.

References:
- Issue #37: Claude Computational Engine architecture
- Issue #44: EIG-based reward function design
- Issue #54: API contract interface specification
- Skills: plugins/with-me/skills/{eig-calculation,question-clarity,question-importance}
"""

from dataclasses import dataclass
from typing import Any, TypedDict


class CalculatorUnavailable(Exception):
    """Raised when reward calculator cannot be initialized or is incompatible."""

    pass


class QuestionContext(TypedDict):
    """
    Context information for reward calculation.

    This is the input contract for reward calculation, enabling as-you plugin
    to call with-me's reward calculator without knowing internal implementation.

    All fields are required. Early-stage project, backward compatibility not needed.

    Examples:
        >>> import time
        >>> context = QuestionContext(
        ...     session_id="test_session",
        ...     timestamp=time.time(),
        ...     dimension_beliefs={},
        ...     question_history=[],
        ...     feedback_history=[],
        ...     skill_name=None,
        ... )
        >>> context["session_id"]
        'test_session'
    """

    session_id: str
    timestamp: float
    dimension_beliefs: dict[str, dict]  # Serialized HypothesisSet instances
    question_history: list[str]
    feedback_history: list[dict]
    skill_name: str | None  # Nullable but required field


@dataclass
class RewardResponse:
    """
    Response from reward calculator.

    This is the output contract, providing structured reward information
    with confidence and human-readable reasoning.

    Examples:
        >>> response = RewardResponse(
        ...     reward_score=1.65,
        ...     eig=1.5,
        ...     clarity=0.9,
        ...     importance=1.0,
        ...     confidence=0.8,
        ...     reasoning="High EIG for purpose dimension",
        ... )
        >>> response.reward_score
        1.65
        >>> result = response.to_dict()
        >>> result["eig"]
        1.5
    """

    reward_score: float  # Total reward in [0.0, 1.0+]
    eig: float  # Expected Information Gain in bits
    clarity: float  # Question clarity in [0.0, 1.0]
    importance: float  # Strategic importance in [0.0, 1.0]
    confidence: float  # Confidence in calculation in [0.0, 1.0]
    reasoning: str  # Human-readable explanation

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.

        Returns:
            Dictionary with all response fields

        Examples:
            >>> response = RewardResponse(
            ...     reward_score=1.5, eig=1.2, clarity=0.9,
            ...     importance=0.8, confidence=0.85,
            ...     reasoning="Test"
            ... )
            >>> data = response.to_dict()
            >>> "reward_score" in data
            True
            >>> data["eig"]
            1.2
        """
        return {
            "reward_score": self.reward_score,
            "eig": self.eig,
            "clarity": self.clarity,
            "importance": self.importance,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
        }


# Computation workflow (performed by Claude with skills):
#
# 1. Question Clarity:
#    - Invoke: /with-me:question-clarity
#    - Input: question text
#    - Output: clarity score [0.0, 1.0]
#
# 2. Question Importance:
#    - Invoke: /with-me:question-importance
#    - Input: question text
#    - Output: importance score [0.0, 1.0]
#
# 3. Expected Information Gain (EIG):
#    - Invoke: /with-me:eig-calculation
#    - Input: question, current_beliefs, answer_templates
#    - Uses: /with-me:entropy, /with-me:bayesian-update internally
#    - Output: EIG in bits
#
# 4. Hybrid Reward:
#    - Calculate: reward = EIG + 0.1 × clarity + 0.05 × importance
#    - Return: RewardResponse with all components


# CLI interface for testing
def main():
    """Command-line usage example"""
    import doctest
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("Running doctests...")
        result = doctest.testmod()
        if result.failed == 0:
            print("✓ All doctests passed")
        else:
            print(f"✗ {result.failed} doctest(s) failed")
            sys.exit(1)
        return

    print("Question Reward Calculator v0.3.0")
    print("\nAll computation has been moved to skills.")
    print("Use the following skills for reward calculation:")
    print("  - /with-me:question-clarity")
    print("  - /with-me:question-importance")
    print("  - /with-me:eig-calculation")
    print("\nFor testing, run: python -m with_me.lib.question_reward_calculator --test")


if __name__ == "__main__":
    main()
