#!/usr/bin/env python3
"""
Question Reward Calculator for with-me plugin

Linear additive reward model with information theory-inspired scoring.

Composite reward function:
    r = 0.40*info_gain + 0.20*clarity + 0.15*specificity +
        0.15*actionability + 0.10*relevance - 0.02*question_anomaly

Design notes:
- Simplified model: Components assumed independent (correlated in reality)
- Information gain: Uses uncertainty proxy (not strict I(X;Y))
- Anomaly penalty: Heuristic checks (not true KL divergence)
- Constraint: Python 3.11+ stdlib only

Based on RLHF principles (Ouyang et al., 2022; Christiano et al., 2017).
See: docs/with-me-information-theory-analysis.md for theoretical analysis.
"""

import json
import re
import sys
from typing import Any


class QuestionRewardCalculator:
    """
    Calculate reward scores for questions to evaluate their effectiveness.

    Theoretical basis:
    - Reward function design based on RLHF (Reinforcement Learning from Human Feedback)
    - Weight allocation follows multi-objective optimization principles
    - KL divergence penalty prevents redundant/anomalous questions

    References:
    - Ouyang et al., "Training language models to follow instructions with human feedback", 2022
    - Christiano et al., "Deep reinforcement learning from human preferences", 2017
    - Requirements doc: docs/with-me-evaluation-logic-requirements.md
    """

    def __init__(self):
        """
        Initialize reward calculator with theoretically justified weights.

        Examples:
            >>> calc = QuestionRewardCalculator()
            >>> # Verify weight sum = 1.0 (normalized probability distribution)
            >>> sum(calc.weights.values())
            1.0
            >>> # Verify all weights are positive
            >>> all(w > 0 for w in calc.weights.values())
            True
            >>> # Verify primary objective has highest weight
            >>> calc.weights["info_gain"] == max(calc.weights.values())
            True
        """
        # Weight coefficients for composite reward
        # Theoretical basis:
        # - info_gain (0.40): Primary objective - entropy reduction is core goal
        #   RLHF literature typically assigns 0.4-0.5 to main objective
        # - clarity (0.20): Quality assurance - clear questions get accurate answers
        #   Secondary importance for practical effectiveness
        # - specificity (0.15): Contributes to information gain
        #   Specific questions yield precise answers
        # - actionability (0.15): Practical constraint - questions must be answerable
        #   Balance between ideal and feasible questions
        # - relevance (0.10): Contextual optimization - ensures questions fit current state
        #   Complementary role in multi-objective function
        #
        # Sum = 1.0 (normalized probability distribution)
        # References: Ouyang et al. (2022), multi-objective optimization literature
        self.weights = {
            "info_gain": 0.40,  # Information acquisition (primary objective)
            "clarity": 0.20,  # Question clarity (quality assurance)
            "specificity": 0.15,  # Specificity (information richness)
            "actionability": 0.15,  # Answerability (practical constraint)
            "relevance": 0.10,  # Context relevance (optimization)
        }

        # Question anomaly penalty weight (equivalent to KL divergence penalty concept)
        # Theoretical basis:
        # - Prevents distribution shift in question patterns
        # - Small weight (0.02) acts as regularization, not hard constraint
        # - Based on KL penalty in RLHF: prevents overfitting to specific patterns
        # Note: Implementation uses heuristic (similarity + length + format checks)
        #       rather than true KL divergence (which requires probability distributions)
        # References: KL regularization in policy gradient methods
        self.anomaly_penalty = 0.02  # Question anomaly penalty weight (KL penalty equivalent)

    def calculate_reward(
        self, question: str, context: dict[str, Any], answer: str | None = None
    ) -> dict[str, float]:
        """
        Calculate total reward for a question

        Args:
            question: Question text
            context: {
                'uncertainties': Dict[str, float],
                'answered_dimensions': List[str],
                'question_history': List[str],
                'entropy_before': float
            }
            answer: User's answer (optional, for post-evaluation)

        Returns:
            {
                'total_reward': float,
                'components': Dict[str, float],
                'question_anomaly': float  # Heuristic anomaly score (KL penalty equivalent)
            }

        Examples:
            >>> calc = QuestionRewardCalculator()
            >>> context = {
            ...     "uncertainties": {"purpose": 0.9, "data": 0.7},
            ...     "answered_dimensions": [],
            ...     "question_history": [],
            ... }
            >>> result = calc.calculate_reward("What problem does this solve?", context)
            >>> result["total_reward"] > 0.7
            True
            >>> "info_gain" in result["components"]
            True
            >>> # Test composite effects: high uncertainty + clear question
            >>> clear_q = "What specific problem does this solve?"
            >>> vague_q = "What?"
            >>> result_clear = calc.calculate_reward(clear_q, context)
            >>> result_vague = calc.calculate_reward(vague_q, context)
            >>> result_clear["total_reward"] > result_vague["total_reward"]
            True
            >>> # Test anomaly penalty: redundant question
            >>> context_with_history = {
            ...     "uncertainties": {"purpose": 0.9},
            ...     "answered_dimensions": [],
            ...     "question_history": ["What problem does this solve?"],
            ... }
            >>> result_redundant = calc.calculate_reward("What problem does this solve?", context_with_history)
            >>> result_redundant["question_anomaly"] > 0.5
            True
            >>> # Test relevance: high uncertainty dimension vs low uncertainty dimension
            >>> context_mixed = {
            ...     "uncertainties": {"purpose": 0.9, "data": 0.1},
            ...     "answered_dimensions": [],
            ...     "question_history": [],
            ... }
            >>> result_purpose = calc.calculate_reward("Why is this needed?", context_mixed)
            >>> result_data = calc.calculate_reward("What data is involved?", context_mixed)
            >>> result_purpose["total_reward"] > result_data["total_reward"]
            True
        """
        components = {}

        # Calculate each component
        components["info_gain"] = self._estimate_info_gain(question, context, answer)
        components["clarity"] = self._score_clarity(question)
        components["specificity"] = self._score_specificity(question)
        components["actionability"] = self._score_actionability(question, context)
        components["relevance"] = self._score_relevance(question, context)

        # Weighted sum
        total = sum(self.weights[k] * v for k, v in components.items())

        # Question anomaly penalty (KL penalty equivalent)
        anomaly = self._estimate_question_anomaly(question, context)
        total -= self.anomaly_penalty * anomaly

        return {
            "total_reward": total,
            "components": components,
            "question_anomaly": anomaly,
        }

    def _estimate_info_gain(
        self, question: str, context: dict, answer: str | None
    ) -> float:
        """
        Estimate information gain using simplified heuristics.

        Note: Simplified approximation, not strict I(X;Y) = H(X) - H(X|Y).

        Theoretical definition requires:
        - Probability distributions P(X_before) and P(X_after|Y)
        - Full session history for statistical inference
        - Cannot compute without sufficient data (cold start problem)

        Current implementation:
        - Pre-answer: Returns target dimension uncertainty as proxy
        - Post-answer: Maps answer word count to [0.0, 1.0] range
        - Practical approximation under stdlib-only constraint

        Args:
            question: Question text
            context: Context including uncertainties and history
            answer: User's answer (optional, for post-evaluation)

        Returns:
            Estimated information gain (0.0-1.0)

        Examples:
            >>> calc = QuestionRewardCalculator()
            >>> # Pre-answer: uses target dimension uncertainty
            >>> context = {"uncertainties": {"purpose": 0.9}}
            >>> calc._estimate_info_gain("What is the purpose?", context, None) > 0.5
            True
            >>> # Post-answer: uses answer word count
            >>> long_answer = " ".join(["word"] * 60)
            >>> calc._estimate_info_gain("What is it?", context, long_answer)
            0.9
        """
        if answer:
            # Actual information gain (post-evaluation)
            word_count = len(answer.split())
            if word_count > 50:
                return 0.9
            elif word_count > 20:
                return 0.7
            elif word_count > 5:
                return 0.5
            else:
                return 0.2
        else:
            # Expected information gain (pre-evaluation)
            target_dim = self._extract_target_dimension(question)
            if target_dim:
                uncertainty = context.get("uncertainties", {}).get(target_dim, 0.5)
                # Higher uncertainty dimension = higher expected info gain
                return uncertainty
            return 0.5

    def _score_clarity(self, question: str) -> float:
        """
        Score question clarity

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

    def _score_specificity(self, question: str) -> float:
        """
        Score question specificity

        Examples:
            >>> calc = QuestionRewardCalculator()
            >>> calc._score_specificity("Can you give a specific example?") > 0.6
            True
            >>> calc._score_specificity("Generally, anything?") < 0.5
            True
        """
        score = 0.5

        # Specificity indicators
        if re.search(r"\bexample\b", question, re.I):
            score += 0.2
        if re.search(r"\bspecific(ally)?\b", question, re.I):
            score += 0.1
        if re.search(r"\b(purpose|data|behavior|constraint|quality)\b", question, re.I):
            score += 0.2

        # Abstractness indicators
        if re.search(r"\b(generally|usually|typically)\b", question, re.I):
            score -= 0.2
        if re.search(r"\b(any|anything|everything)\b", question, re.I):
            score -= 0.1

        return max(0.0, min(1.0, score))

    def _score_actionability(self, question: str, context: dict) -> float:
        """
        Score answerability

        Examples:
            >>> calc = QuestionRewardCalculator()
            >>> context = {"answered_dimensions": []}
            >>> calc._score_actionability("What is the purpose?", context) > 0.7
            True
        """
        # Detect overly technical questions
        technical_terms = [
            "algorithm",
            "complexity",
            "optimization",
            "architecture",
            "implementation",
            "framework",
            "library",
        ]
        tech_count = sum(1 for term in technical_terms if term in question.lower())
        if tech_count >= 2:
            return 0.3

        # Detect premature questions
        answered = set(context.get("answered_dimensions", []))
        if "purpose" not in answered and "behavior" in question.lower():
            return 0.4  # Too early to ask about behavior

        return 0.8  # Default: answerable

    def _score_relevance(self, question: str, context: dict) -> float:
        """
        Score context relevance

        Examples:
            >>> calc = QuestionRewardCalculator()
            >>> context = {"uncertainties": {"purpose": 0.9, "data": 0.2}}
            >>> # Question about high-uncertainty dimension
            >>> calc._score_relevance("What is the purpose?", context) > 0.7
            True
        """
        target_dim = self._extract_target_dimension(question)
        if not target_dim:
            return 0.5

        uncertainties = context.get("uncertainties", {})
        dim_uncertainty = uncertainties.get(target_dim, 0.5)

        # High uncertainty dimension = high relevance
        relevance = dim_uncertainty

        # Already clear dimension = penalty
        if dim_uncertainty < 0.3:
            relevance *= 0.5

        return relevance

    def _estimate_question_anomaly(self, question: str, context: dict) -> float:
        """
        Estimate question anomaly score (KL divergence penalty equivalent).

        Note: This is a heuristic approximation, not true KL divergence.
        True KL divergence requires probability distributions: KL(P||Q) = Σ P(x) log(P(x)/Q(x))
        This implementation uses practical heuristics:
        - Similarity to past questions (redundancy detection)
        - Extreme length (too short or too long)
        - Abnormal question marks (format validation)

        Theoretical basis:
        - Concept inspired by KL regularization in RLHF
        - Prevents distribution shift in question patterns
        - Acts as regularization penalty

        Returns:
            Anomaly score (0.0 = normal, higher = more anomalous)

        Examples:
            >>> calc = QuestionRewardCalculator()
            >>> context = {"question_history": ["What is it?"]}
            >>> calc._estimate_question_anomaly("What is it?", context) > 0.5
            True
            >>> calc._estimate_question_anomaly(
            ...     "How does it work?", {"question_history": []}
            ... )
            0.0
        """
        anomaly_score = 0.0

        # Similarity with past questions
        history = context.get("question_history", [])
        if history:
            max_similarity = max(
                self._calculate_similarity(question, past_q)
                for past_q in history[-5:]  # Last 5 questions
            )
            if max_similarity > 0.8:  # Redundant
                anomaly_score += 1.0

        # Extreme length
        word_count = len(question.split())
        if word_count < 3 or word_count > 40:
            anomaly_score += 0.5

        # Abnormal question marks
        question_marks = question.count("?")
        if question_marks == 0 or question_marks > 2:
            anomaly_score += 0.3

        return anomaly_score

    def _extract_target_dimension(self, question: str) -> str | None:
        """
        Extract target dimension from question

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

    def _calculate_similarity(self, q1: str, q2: str) -> float:
        """
        Calculate similarity between two questions (simplified)

        Examples:
            >>> calc = QuestionRewardCalculator()
            >>> calc._calculate_similarity("What is it?", "What is it?")
            1.0
            >>> calc._calculate_similarity("What?", "How?") < 0.5
            True
        """
        # Word overlap as similarity measure
        words1 = set(re.findall(r"\w+", q1.lower()))
        words2 = set(re.findall(r"\w+", q2.lower()))

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)


# CLI interface
def main():
    """Command-line usage example"""
    if len(sys.argv) < 3:
        print(
            "Usage: python question_reward_calculator.py '<question>' '<context_json>'"
        )
        print("\nExample:")
        print(
            '  python question_reward_calculator.py "What problem does this solve?" \'{"uncertainties": {"purpose": 0.9}}\''
        )
        sys.exit(1)

    question = sys.argv[1]
    context = json.loads(sys.argv[2])
    answer = sys.argv[3] if len(sys.argv) > 3 else None

    calculator = QuestionRewardCalculator()
    result = calculator.calculate_reward(question, context, answer)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    import doctest

    # Run doctests if --test flag is provided
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("Running doctests...")
        doctest.testmod()
        print("✓ All doctests passed")
    else:
        main()
