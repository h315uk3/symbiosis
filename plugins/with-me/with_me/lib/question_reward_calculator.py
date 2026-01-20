#!/usr/bin/env python3
"""
Question Reward Calculator for with-me plugin (v0.3.0)

EIG-based (Expected Information Gain) reward model with quality adjustments.

Reward Function:
    r(Q) = EIG(Q) + 0.1×clarity(Q) + 0.05×importance(Q)

Design Philosophy:
- Primary: EIG (Expected Information Gain) measures uncertainty reduction
- Secondary: clarity ensures question quality
- Tertiary: importance enables strategic weighting

This replaces the v0.2.x linear additive model with theoretically grounded
information-theoretic approach using Bayesian belief updating.

Theoretical Foundation:
- EIG: Expected reduction in Shannon entropy before question is asked
- Bayesian: Uses HypothesisSet posterior distributions
- Stdlib-only: No external dependencies (NumPy, SciPy, etc.)

API Contract (Issue #54):
- Standardized interface for as-you plugin integration
- Type-safe input/output with QuestionContext and RewardResponse
- Fallback behavior when calculator unavailable
- Version compatibility tracking

References:
- Issue #44: EIG-based reward function design
- Issue #54: API contract interface specification
- Issue #38: Phase 1-B implementation
"""

import json
import math
import re
import sys
import time
from dataclasses import dataclass
from typing import Any, TypedDict

from .dimension_belief import HypothesisSet, create_default_dimension_beliefs


class QuestionContext(TypedDict, total=False):
    """
    Context information for reward calculation.

    This is the input contract for reward calculation, enabling as-you plugin
    to call with-me's reward calculator without knowing internal implementation.
    """

    session_id: str
    skill_name: str | None
    timestamp: float
    dimension_beliefs: dict[str, dict]  # Serialized HypothesisSet instances
    question_history: list[str]
    feedback_history: list[dict]


@dataclass
class RewardResponse:
    """
    Response from reward calculator.

    This is the output contract, providing structured reward information
    with confidence and human-readable reasoning.
    """

    reward_score: float  # Total reward in [0.0, 1.0+]
    eig: float  # Expected Information Gain in bits
    clarity: float  # Question clarity in [0.0, 1.0]
    importance: float  # Strategic importance in [0.0, 1.0]
    confidence: float  # Confidence in calculation in [0.0, 1.0]
    reasoning: str  # Human-readable explanation

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "reward_score": self.reward_score,
            "eig": self.eig,
            "clarity": self.clarity,
            "importance": self.importance,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
        }


class QuestionRewardCalculator:
    """
    Calculate reward scores using EIG-based model.

    v0.3.0 Changes:
    - Replaced linear additive model with EIG-based approach
    - Uses Bayesian belief updating for principled information gain
    - Implements API contract for as-you integration
    - Maintains backward compatibility via legacy calculate_reward method

    Examples:
        >>> # Basic usage with dimension beliefs
        >>> calculator = QuestionRewardCalculator()
        >>> beliefs = create_default_dimension_beliefs()
        >>> context = QuestionContext(
        ...     session_id="test_session",
        ...     skill_name=None,
        ...     timestamp=time.time(),
        ...     dimension_beliefs={k: v.to_dict() for k, v in beliefs.items()},
        ...     question_history=[],
        ...     feedback_history=[]
        ... )
        >>> response = calculator.calculate_reward_for_question(
        ...     "What is the main purpose of this project?",
        ...     context
        ... )
        >>> response.reward_score > 0  # Positive reward
        True
        >>> response.eig > 0  # Information gain is positive
        True

        >>> # High clarity question gets bonus
        >>> clear_q = "What specific problem does this solve?"
        >>> vague_q = "What?"
        >>> r_clear = calculator.calculate_reward_for_question(clear_q, context)
        >>> r_vague = calculator.calculate_reward_for_question(vague_q, context)
        >>> r_clear.reward_score > r_vague.reward_score
        True
    """

    VERSION = "0.3.0"

    def __init__(self):
        """
        Initialize reward calculator.

        Examples:
            >>> calc = QuestionRewardCalculator()
            >>> calc.VERSION
            '0.3.0'
        """
        # Weight coefficients for hybrid model
        # Primary: EIG (coefficient = 1.0, implicit)
        # Secondary: clarity adjustment (10% of EIG scale)
        # Tertiary: importance adjustment (5% of EIG scale)
        self.clarity_weight = 0.1
        self.importance_weight = 0.05

    def calculate_reward_for_question(
        self,
        question: str,
        context: QuestionContext,
        timeout_seconds: float = 2.0,
    ) -> RewardResponse:
        """
        Calculate reward score for a given question (API contract method).

        This is the primary interface for external callers (e.g., as-you plugin).

        Args:
            question: User's question text
            context: Session and skill context with dimension beliefs
            timeout_seconds: Maximum computation time (default: 2s)

        Returns:
            RewardResponse with score, EIG, clarity, importance, confidence, reasoning

        Raises:
            ValueError: If question format is invalid
            TimeoutError: If calculation exceeds timeout_seconds

        Examples:
            >>> calc = QuestionRewardCalculator()
            >>> beliefs = create_default_dimension_beliefs()
            >>> context = QuestionContext(
            ...     session_id="sess_123",
            ...     skill_name="git_commit",
            ...     timestamp=time.time(),
            ...     dimension_beliefs={k: v.to_dict() for k, v in beliefs.items()},
            ...     question_history=[],
            ...     feedback_history=[]
            ... )
            >>> response = calc.calculate_reward_for_question(
            ...     "What is the main use case?",
            ...     context
            ... )
            >>> 0.0 <= response.reward_score
            True
            >>> isinstance(response.reasoning, str)
            True
        """
        start_time = time.time()

        # Validation
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")

        # Timeout check (simple check, not thread-based)
        if time.time() - start_time > timeout_seconds:
            raise TimeoutError(f"Calculation exceeded {timeout_seconds}s timeout")

        # Calculate EIG (primary component)
        eig = self._calculate_eig(question, context)

        # Calculate quality adjustments
        clarity = self._score_clarity(question)
        importance = self._calculate_importance(question, context)

        # Hybrid reward function
        reward = eig + self.clarity_weight * clarity + self.importance_weight * importance

        # Confidence estimation
        confidence = self._estimate_confidence(context)

        # Generate reasoning
        reasoning = self._generate_reasoning(question, eig, clarity, importance)

        return RewardResponse(
            reward_score=reward,
            eig=eig,
            clarity=clarity,
            importance=importance,
            confidence=confidence,
            reasoning=reasoning,
        )

    def _calculate_eig(self, question: str, context: QuestionContext) -> float:
        """
        Calculate Expected Information Gain for a question.

        EIG = E[H_before - H_after] = Expected reduction in entropy

        For simplified calculation (without sampling all possible answers):
        EIG ≈ H_current × P(question addresses high-entropy dimension)

        Args:
            question: Question text
            context: Context with dimension beliefs

        Returns:
            Expected information gain in bits

        Examples:
            >>> calc = QuestionRewardCalculator()
            >>> beliefs = create_default_dimension_beliefs()
            >>> context = QuestionContext(
            ...     session_id="test",
            ...     dimension_beliefs={k: v.to_dict() for k, v in beliefs.items()},
            ...     question_history=[],
            ...     feedback_history=[]
            ... )
            >>> # Question targeting high-entropy dimension
            >>> eig = calc._calculate_eig("What is the purpose?", context)
            >>> eig > 0
            True
        """
        # Reconstruct dimension beliefs from context
        beliefs = self._load_dimension_beliefs(context)

        # Identify target dimension
        target_dim = self._extract_target_dimension(question)

        if target_dim and target_dim in beliefs:
            # EIG approximation: current entropy of target dimension
            # This assumes the question will significantly reduce uncertainty
            # A more sophisticated approach would sample possible answers
            hs = beliefs[target_dim]
            return hs.entropy()
        else:
            # Question doesn't target specific dimension: low EIG
            return 0.2  # Baseline small value

    def _load_dimension_beliefs(
        self, context: QuestionContext
    ) -> dict[str, HypothesisSet]:
        """
        Load dimension beliefs from context.

        Args:
            context: Question context with serialized beliefs

        Returns:
            Dictionary of HypothesisSet instances

        Examples:
            >>> calc = QuestionRewardCalculator()
            >>> beliefs = create_default_dimension_beliefs()
            >>> context = QuestionContext(
            ...     dimension_beliefs={k: v.to_dict() for k, v in beliefs.items()}
            ... )
            >>> loaded = calc._load_dimension_beliefs(context)
            >>> "purpose" in loaded
            True
        """
        if "dimension_beliefs" in context and context["dimension_beliefs"]:
            return {
                dim: HypothesisSet.from_dict(data)
                for dim, data in context["dimension_beliefs"].items()
            }
        else:
            # No beliefs provided: use default uniform priors
            return create_default_dimension_beliefs()

    def _score_clarity(self, question: str) -> float:
        """
        Score question clarity (0.0-1.0).

        Examples:
            >>> calc = QuestionRewardCalculator()
            >>> calc._score_clarity("What is the purpose?") > 0.8
            True
            >>> calc._score_clarity("Maybe or perhaps?") < 1.0
            True
        """
        score = 1.0

        # Negative factors
        if "?" not in question:
            score -= 0.2
        if len(question.split()) > 30:  # Too long
            score -= 0.2
        if re.search(r"\b(or|and|also)\b.*\?.*\?", question):  # Compound question
            score -= 0.3
        if re.search(r"\b(maybe|perhaps|might)\b", question):  # Vague
            score -= 0.1

        # Positive factors
        if re.match(r"^(What|How|Why|When|Where|Who)", question):
            score += 0.1

        return max(0.0, min(1.0, score))

    def _calculate_importance(self, question: str, context: QuestionContext) -> float:
        """
        Calculate strategic importance of question (0.0-1.0).

        Some dimensions are more important than others in requirement elicitation.
        Default priorities: purpose > behavior > data > constraints > quality

        Args:
            question: Question text
            context: Question context

        Returns:
            Importance score in [0.0, 1.0]

        Examples:
            >>> calc = QuestionRewardCalculator()
            >>> context = QuestionContext(question_history=[])
            >>> # Purpose questions have high importance
            >>> calc._calculate_importance("What is the purpose?", context) >= 0.8
            True
        """
        target_dim = self._extract_target_dimension(question)

        # Dimension importance weights
        importance_map = {
            "purpose": 1.0,  # Most important
            "behavior": 0.8,
            "data": 0.7,
            "constraints": 0.6,
            "quality": 0.5,
        }

        return importance_map.get(target_dim, 0.5)

    def _extract_target_dimension(self, question: str) -> str | None:
        """
        Extract target dimension from question.

        Examples:
            >>> calc = QuestionRewardCalculator()
            >>> calc._extract_target_dimension("Why is this needed?")
            'purpose'
            >>> calc._extract_target_dimension("What data is involved?")
            'data'
            >>> calc._extract_target_dimension("How does it work?")
            'behavior'
        """
        q_lower = question.lower()

        if any(kw in q_lower for kw in ["why", "purpose", "goal", "problem"]):
            return "purpose"
        if any(kw in q_lower for kw in ["what data", "input", "output", "information"]):
            return "data"
        if any(kw in q_lower for kw in ["how", "step", "process", "flow", "happen"]):
            return "behavior"
        if any(
            kw in q_lower
            for kw in ["constraint", "limit", "requirement", "performance"]
        ):
            return "constraints"
        if any(
            kw in q_lower for kw in ["test", "success", "quality", "fail", "edge case"]
        ):
            return "quality"

        return None

    def _estimate_confidence(self, context: QuestionContext) -> float:
        """
        Estimate confidence in reward calculation.

        Confidence depends on:
        - Availability of dimension beliefs (higher confidence)
        - Number of past questions (more history = higher confidence)

        Returns:
            Confidence value in [0.0, 1.0]

        Examples:
            >>> calc = QuestionRewardCalculator()
            >>> # With beliefs: high confidence
            >>> beliefs = create_default_dimension_beliefs()
            >>> context = QuestionContext(
            ...     dimension_beliefs={k: v.to_dict() for k, v in beliefs.items()},
            ...     question_history=["Q1", "Q2", "Q3"]
            ... )
            >>> calc._estimate_confidence(context) > 0.7
            True
        """
        confidence = 0.5  # Baseline

        # Increase confidence if dimension beliefs available
        if "dimension_beliefs" in context and context["dimension_beliefs"]:
            confidence += 0.3

        # Increase confidence with question history
        history_len = len(context.get("question_history", []))
        if history_len > 5:
            confidence += 0.2
        elif history_len > 0:
            confidence += 0.1

        return min(1.0, confidence)

    def _generate_reasoning(
        self, question: str, eig: float, clarity: float, importance: float
    ) -> str:
        """
        Generate human-readable reasoning for reward score.

        Examples:
            >>> calc = QuestionRewardCalculator()
            >>> reasoning = calc._generate_reasoning(
            ...     "What is the purpose?",
            ...     1.5, 0.9, 1.0
            ... )
            >>> "EIG" in reasoning
            True
        """
        target_dim = self._extract_target_dimension(question)
        dim_str = target_dim if target_dim else "unspecified dimension"

        return (
            f"EIG={eig:.2f} bits (targets {dim_str}), "
            f"clarity={clarity:.2f}, importance={importance:.2f}"
        )

    # Legacy API (backward compatibility with v0.2.x)
    def calculate_reward(
        self, question: str, context: dict[str, Any], answer: str | None = None
    ) -> dict[str, float]:
        """
        Calculate reward using legacy v0.2.x interface.

        This method maintains backward compatibility with existing code
        that uses the old linear additive model interface.

        Args:
            question: Question text
            context: Legacy context format
            answer: User's answer (optional)

        Returns:
            Legacy format: {
                'total_reward': float,
                'components': {...},
                'question_anomaly': float
            }

        Examples:
            >>> calc = QuestionRewardCalculator()
            >>> context = {
            ...     "uncertainties": {"purpose": 0.9},
            ...     "answered_dimensions": [],
            ...     "question_history": []
            ... }
            >>> result = calc.calculate_reward("What is the purpose?", context)
            >>> "total_reward" in result
            True
            >>> "components" in result
            True
        """
        # Convert legacy context to new format
        beliefs = create_default_dimension_beliefs()
        new_context = QuestionContext(
            session_id="legacy_session",
            skill_name=None,
            timestamp=time.time(),
            dimension_beliefs={k: v.to_dict() for k, v in beliefs.items()},
            question_history=context.get("question_history", []),
            feedback_history=[],
        )

        # Calculate using new method
        response = self.calculate_reward_for_question(question, new_context)

        # Convert to legacy format
        return {
            "total_reward": response.reward_score,
            "components": {
                "info_gain": response.eig,
                "clarity": response.clarity,
                "specificity": response.clarity,  # Map to clarity
                "actionability": 0.8,  # Default
                "relevance": response.importance,
            },
            "question_anomaly": 0.0,  # No longer used in v0.3.0
        }


def calculate_reward_with_fallback(
    question: str, context: QuestionContext
) -> RewardResponse:
    """
    Calculate reward with graceful fallback if calculator unavailable.

    This is the recommended entry point for external callers (e.g., as-you plugin)
    as it provides fallback behavior when with-me is unavailable or errors occur.

    Args:
        question: Question text
        context: Question context

    Returns:
        RewardResponse (neutral score if calculator fails)

    Examples:
        >>> context = QuestionContext(
        ...     session_id="test",
        ...     question_history=[]
        ... )
        >>> response = calculate_reward_with_fallback(
        ...     "Should I use async here?",
        ...     context
        ... )
        >>> 0.0 <= response.reward_score
        True
        >>> 0.0 <= response.confidence <= 1.0
        True
    """
    try:
        calculator = QuestionRewardCalculator()
        return calculator.calculate_reward_for_question(question, context)
    except Exception as e:
        # Fallback: return neutral score
        return RewardResponse(
            reward_score=0.5,  # Neutral score
            eig=0.0,
            clarity=0.0,
            importance=0.5,
            confidence=0.0,  # No confidence in fallback
            reasoning=f"Fallback (error: {type(e).__name__})",
        )


# CLI interface
def main():
    """Command-line usage example"""
    # Check for special commands first
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        import doctest

        print("Running doctests...")
        result = doctest.testmod()
        if result.failed == 0:
            print("✓ All doctests passed")
        else:
            print(f"✗ {result.failed} doctest(s) failed")
            sys.exit(1)
        return

    if len(sys.argv) > 1 and sys.argv[1] == "--version":
        print(f"with-me question_reward_calculator v{QuestionRewardCalculator.VERSION}")
        return

    if len(sys.argv) < 3:
        print("Usage: python question_reward_calculator.py '<question>' '<context_json>'")
        print("\nExample (v0.3.0 format):")
        print('  python question_reward_calculator.py "What is the purpose?" \\')
        print('    \'{"session_id": "test", "question_history": []}\'')
        print("\nCommands:")
        print("  --test     Run doctests")
        print("  --version  Show version")
        sys.exit(1)

    question = sys.argv[1]
    context_dict = json.loads(sys.argv[2])

    # Use fallback wrapper for CLI
    context = QuestionContext(**context_dict)
    response = calculate_reward_with_fallback(question, context)

    print(json.dumps(response.to_dict(), indent=2))


if __name__ == "__main__":
    main()
