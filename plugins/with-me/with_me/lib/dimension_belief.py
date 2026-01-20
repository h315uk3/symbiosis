#!/usr/bin/env python3
"""
Bayesian Belief Updating for Requirement Dimensions

Implements information-theoretic approach to uncertainty tracking using
Bayesian belief updating over hypothesis sets.

Theoretical Foundation:
- Shannon Entropy: H(h) = -Σ p(h) log₂ p(h) measures uncertainty
- Bayesian Update: p₁(h) ∝ p₀(h) × L(observation|h) updates beliefs
- Expected Information Gain (EIG): Measures question value before asking
- Likelihood Estimation: Uses Claude-based semantic evaluation (Issue #37)

Design Rationale:
This module replaces heuristic uncertainty proxies (e.g., word count)
with principled probabilistic reasoning. Each dimension maintains explicit
posterior distributions over hypotheses, enabling:
- Formal entropy calculation (bits of uncertainty)
- Information gain measurement (bits learned)
- Confidence estimation (distribution spread)

References:
- Issue #43: Theoretical Foundation (Bayesian approach)
- Issue #44: EIG-based reward function
- Shannon (1948): A Mathematical Theory of Communication
"""

import math
from typing import Any


class HypothesisSet:
    """
    Manages hypothesis set and posterior distribution for a dimension.

    A hypothesis set represents possible values for a requirement dimension
    (e.g., "web app", "CLI tool", "library" for purpose dimension).

    Examples:
        >>> # Initialize with uniform prior
        >>> hs = HypothesisSet(
        ...     dimension="purpose", hypotheses=["web_app", "cli_tool", "library"]
        ... )
        >>> hs.entropy() > 1.0  # log₂(3) ≈ 1.58 bits
        True

        >>> # Update belief based on observation
        >>> h_before = hs.entropy()
        >>> ig = hs.update(
        ...     observation="user mentioned web browser", answer="Yes, browser based"
        ... )
        >>> ig > 0  # Information gained
        True
        >>> # Entropy should decrease after learning
        >>> hs.entropy() < h_before
        True

        >>> # Get most likely hypothesis
        >>> hs.get_most_likely()  # doctest: +SKIP
        'web_app'
    """

    def __init__(
        self,
        dimension: str,
        hypotheses: list[str],
        prior: dict[str, float] | None = None,
    ):
        """
        Initialize hypothesis set with prior distribution.

        Args:
            dimension: Dimension name (e.g., "purpose", "data", "behavior")
            hypotheses: List of hypothesis identifiers
            prior: Optional prior distribution {hypothesis: probability}
                   If None, uses uniform distribution

        Examples:
            >>> # Uniform prior (default)
            >>> hs = HypothesisSet("purpose", ["web_app", "cli_tool"])
            >>> hs.posterior["web_app"]
            0.5

            >>> # Custom prior
            >>> hs = HypothesisSet(
            ...     "purpose",
            ...     ["web_app", "cli_tool"],
            ...     prior={"web_app": 0.7, "cli_tool": 0.3},
            ... )
            >>> hs.posterior["web_app"]
            0.7
        """
        self.dimension = dimension
        self.hypotheses = hypotheses

        # Initialize posterior with prior or uniform
        if prior:
            self.posterior = prior.copy()
            # Normalize to ensure valid probability distribution
            total = sum(self.posterior.values())
            if total > 0:
                self.posterior = {h: p / total for h, p in self.posterior.items()}
        else:
            # Uniform prior: p(h) = 1/N for all hypotheses
            uniform_prob = 1.0 / len(hypotheses)
            self.posterior = {h: uniform_prob for h in hypotheses}

        # History of observations (for debugging/analysis)
        self.observation_history: list[dict[str, Any]] = []

    def entropy(self) -> float:
        """
        Calculate Shannon entropy of current posterior distribution.

        Shannon entropy H(h) = -Σ p(h) log₂ p(h) measures uncertainty in bits.
        - H = 0: Complete certainty (one hypothesis has p=1.0)
        - H = log₂(N): Maximum uncertainty (uniform distribution)

        Returns:
            Entropy in bits

        Examples:
            >>> # Maximum uncertainty: uniform distribution over 4 hypotheses
            >>> hs = HypothesisSet("purpose", ["h1", "h2", "h3", "h4"])
            >>> abs(hs.entropy() - 2.0) < 0.01  # log₂(4) = 2.0
            True

            >>> # Minimum uncertainty: complete certainty
            >>> hs.posterior = {"h1": 1.0, "h2": 0.0, "h3": 0.0, "h4": 0.0}
            >>> hs.entropy()
            0.0

            >>> # Partial uncertainty
            >>> hs.posterior = {"h1": 0.5, "h2": 0.3, "h3": 0.15, "h4": 0.05}
            >>> 0.0 < hs.entropy() < 2.0
            True
        """
        entropy_value = 0.0
        for prob in self.posterior.values():
            if prob > 0:  # Skip zero probabilities (lim x→0 x log x = 0)
                entropy_value -= prob * math.log2(prob)
        return entropy_value

    def update(
        self,
        observation: str,
        answer: str,
        likelihoods: dict[str, float],
    ) -> float:
        """
        Update posterior distribution using Bayesian rule.

        Bayes Rule: p₁(h) ∝ p₀(h) × L(observation|h)

        Where:
        - p₀(h): prior belief (current posterior)
        - L(obs|h): likelihood of observation given hypothesis
        - p₁(h): posterior belief after update

        Args:
            observation: Context of the question asked
            answer: User's answer text
            likelihoods: Pre-computed likelihoods for each hypothesis from
                        semantic evaluation. Must contain entries for all hypotheses.

        Returns:
            Information gain in bits: ΔH = H_before - H_after

        Examples:
            >>> # Using semantic evaluation likelihoods
            >>> hs = HypothesisSet("purpose", ["web_app", "cli_tool", "library"])
            >>> ig = hs.update(
            ...     observation="Question about purpose",
            ...     answer="Browser-based application",
            ...     likelihoods={"web_app": 0.7, "cli_tool": 0.2, "library": 0.1},
            ... )
            >>> ig > 0
            True
        """
        h_before = self.entropy()

        # Validate provided likelihoods
        if set(likelihoods.keys()) != set(self.hypotheses):
            raise ValueError(
                f"Provided likelihoods must contain all hypotheses. "
                f"Expected {set(self.hypotheses)}, got {set(likelihoods.keys())}"
            )

        # Bayesian update: p1(h) proportional to p0(h) * L(obs|h)
        unnormalized = {h: self.posterior[h] * likelihoods[h] for h in self.hypotheses}

        # Normalize to get valid probability distribution
        total = sum(unnormalized.values())
        if total > 0:
            self.posterior = {h: p / total for h, p in unnormalized.items()}
        # else: no evidence, posterior unchanged

        # Record observation
        self.observation_history.append(
            {
                "observation": observation,
                "answer": answer,
                "likelihoods": likelihoods.copy(),
                "posterior_after": self.posterior.copy(),
            }
        )

        h_after = self.entropy()
        information_gain = h_before - h_after

        return information_gain

    def get_most_likely(self) -> str:
        """
        Get hypothesis with highest posterior probability.

        Returns:
            Most likely hypothesis identifier

        Examples:
            >>> hs = HypothesisSet("purpose", ["web_app", "cli_tool"])
            >>> hs.posterior = {"web_app": 0.8, "cli_tool": 0.2}
            >>> hs.get_most_likely()
            'web_app'
        """
        return max(self.posterior.items(), key=lambda x: x[1])[0]

    def get_confidence(self) -> float:
        """
        Get confidence level as inverse of normalized entropy.

        Confidence = 1 - (H / H_max)
        - Confidence = 1.0: Complete certainty
        - Confidence = 0.0: Maximum uncertainty

        Returns:
            Confidence value in [0.0, 1.0]

        Examples:
            >>> # Complete certainty
            >>> hs = HypothesisSet("purpose", ["web_app", "cli_tool"])
            >>> hs.posterior = {"web_app": 1.0, "cli_tool": 0.0}
            >>> hs.get_confidence()
            1.0

            >>> # Maximum uncertainty (uniform)
            >>> hs.posterior = {"web_app": 0.5, "cli_tool": 0.5}
            >>> abs(hs.get_confidence() - 0.0) < 0.01
            True
        """
        h_max = math.log2(len(self.hypotheses)) if len(self.hypotheses) > 1 else 1.0
        if h_max == 0:
            return 1.0
        return 1.0 - (self.entropy() / h_max)

    def copy(self) -> "HypothesisSet":
        """
        Create independent copy for counterfactual simulation.

        Used in EIG calculation to simulate belief updates for multiple
        hypothetical answers without modifying the original belief state.

        Returns:
            Independent HypothesisSet with same state

        Examples:
            >>> hs = HypothesisSet("purpose", ["web_app", "cli_tool"])
            >>> hs.posterior = {"web_app": 0.7, "cli_tool": 0.3}
            >>> hs_copy = hs.copy()
            >>> hs_copy.posterior["web_app"]
            0.7
            >>> # Modifying copy doesn't affect original
            >>> _ = hs_copy.update("test", "browser interface")
            >>> hs.posterior["web_app"]
            0.7
        """
        hs_copy = HypothesisSet(self.dimension, self.hypotheses)
        hs_copy.posterior = dict(self.posterior)
        hs_copy.observation_history = [dict(obs) for obs in self.observation_history]
        return hs_copy

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize to dictionary for JSON storage.

        Returns:
            Dictionary representation

        Examples:
            >>> hs = HypothesisSet("purpose", ["web_app", "cli_tool"])
            >>> data = hs.to_dict()
            >>> data["dimension"]
            'purpose'
            >>> "posterior" in data
            True
        """
        return {
            "dimension": self.dimension,
            "hypotheses": self.hypotheses,
            "posterior": self.posterior,
            "entropy": self.entropy(),
            "confidence": self.get_confidence(),
            "observation_history": self.observation_history,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HypothesisSet":
        """
        Deserialize from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            HypothesisSet instance

        Examples:
            >>> data = {
            ...     "dimension": "purpose",
            ...     "hypotheses": ["web_app", "cli_tool"],
            ...     "posterior": {"web_app": 0.6, "cli_tool": 0.4},
            ... }
            >>> hs = HypothesisSet.from_dict(data)
            >>> hs.dimension
            'purpose'
        """
        hs = cls(
            dimension=data["dimension"],
            hypotheses=data["hypotheses"],
            prior=data.get("posterior"),
        )
        if "observation_history" in data:
            hs.observation_history = data["observation_history"]
        return hs


def create_default_dimension_beliefs() -> dict[str, HypothesisSet]:
    """
    Create default hypothesis sets for standard requirement dimensions.

    Returns:
        Dictionary mapping dimension names to HypothesisSet instances

    Examples:
        >>> beliefs = create_default_dimension_beliefs()
        >>> "purpose" in beliefs
        True
        >>> beliefs["purpose"].entropy() > 0
        True
    """
    return {
        "purpose": HypothesisSet(
            dimension="purpose",
            hypotheses=["web_app", "cli_tool", "library", "service"],
        ),
        "data": HypothesisSet(
            dimension="data",
            hypotheses=["structured", "unstructured", "streaming"],
        ),
        "behavior": HypothesisSet(
            dimension="behavior",
            hypotheses=["synchronous", "asynchronous", "interactive", "batch"],
        ),
        "constraints": HypothesisSet(
            dimension="constraints",
            hypotheses=["performance", "scalability", "reliability", "security"],
        ),
        "quality": HypothesisSet(
            dimension="quality",
            hypotheses=["functional", "usability", "maintainability"],
        ),
    }


# CLI interface
def main():
    """Command-line usage example"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python dimension_belief.py <command>")
        print("\nCommands:")
        print("  demo     - Run interactive demonstration")
        print("  test     - Run doctests")
        sys.exit(1)

    command = sys.argv[1]

    if command == "demo":
        # Interactive demonstration
        beliefs = create_default_dimension_beliefs()
        print("Initial beliefs (uniform priors):")
        for dim, hs in beliefs.items():
            print(f"  {dim}: H={hs.entropy():.2f} bits")

        print("\nSimulating observation: 'User mentioned REST API and browser'")
        ig = beliefs["purpose"].update(
            observation="Asked about user interface",
            answer="Users will interact via browser, REST API for data",
        )
        print(f"Information gained: {ig:.3f} bits")
        print(f"Updated entropy: {beliefs['purpose'].entropy():.2f} bits")
        print(f"Most likely: {beliefs['purpose'].get_most_likely()}")
        print(f"Confidence: {beliefs['purpose'].get_confidence():.2f}")

    elif command == "test":
        import doctest

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
