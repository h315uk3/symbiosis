#!/usr/bin/env python3
"""
Belief state management for requirement dimensions.

Manages posterior distributions over hypothesis sets.
All computation performed by Claude using skills.

Responsibilities:
- State initialization and persistence
- Data structure management (posterior, observation_history)
- Serialization (to_dict/from_dict)

Skills:
- /with-me:entropy
- /with-me:bayesian-update
- /with-me:information-gain

Related: #37
"""

from typing import Any


class HypothesisSet:
    """
    Manages hypothesis set and posterior distribution for a dimension.

    A hypothesis set represents possible values for a requirement dimension
    (e.g., "web app", "CLI tool", "library" for purpose dimension).

    This class provides state management only. All computations are delegated to skills:
    - /with-me:entropy for entropy calculation
    - /with-me:bayesian-update for posterior updating
    - /with-me:information-gain for information gain calculation

    Examples:
        >>> # Initialize with uniform prior
        >>> hs = HypothesisSet(
        ...     dimension="purpose", hypotheses=["web_app", "cli_tool", "library"]
        ... )
        >>> hs.posterior["web_app"]
        0.333...

        >>> # Get most likely hypothesis
        >>> hs.posterior = {"web_app": 0.7, "cli_tool": 0.2, "library": 0.1}
        >>> hs.get_most_likely()
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

        # Cached computation results (set by persist-computation CLI)
        self._cached_entropy: float | None = None
        self._cached_confidence: float | None = None

    # Computation methods removed - use skills instead:
    # - /with-me:entropy for H(h) calculation
    # - /with-me:bayesian-update for posterior updating
    # - /with-me:information-gain for IG calculation
    #
    # CLI commands:
    # - python -m with_me.cli.session compute-entropy
    # - python -m with_me.cli.session bayesian-update
    # - python -m with_me.cli.session persist-computation

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

    # get_confidence() removed - use /with-me:entropy skill
    # Calculate: confidence = 1 - (H / H_max) where H_max = log₂(N)

    def copy(self) -> "HypothesisSet":
        """
        Create independent copy for state management.

        Used for simulation or backup purposes without modifying original state.

        Returns:
            Independent HypothesisSet with same state

        Examples:
            >>> hs = HypothesisSet("purpose", ["web_app", "cli_tool"])
            >>> hs.posterior = {"web_app": 0.7, "cli_tool": 0.3}
            >>> hs_copy = hs.copy()
            >>> hs_copy.posterior["web_app"]
            0.7
            >>> # Modifying copy doesn't affect original
            >>> hs_copy.posterior["web_app"] = 0.9
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
            "observation_history": self.observation_history,
            "_cached_entropy": self._cached_entropy,
            "_cached_confidence": self._cached_confidence,
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
        # Restore cached computation results
        hs._cached_entropy = data.get("_cached_entropy")
        hs._cached_confidence = data.get("_cached_confidence")
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
        >>> len(beliefs["purpose"].hypotheses)
        4
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
        print("  test     - Run doctests")
        print("\nNote: Computation demo removed.")
        print("Use CLI commands instead:")
        print("  python -m with_me.cli.session compute-entropy")
        print("  python -m with_me.cli.session bayesian-update")
        sys.exit(1)

    command = sys.argv[1]

    if command == "test":
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
