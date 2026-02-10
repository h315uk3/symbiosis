#!/usr/bin/env python3
"""
Belief state management for requirement dimensions.

Manages Dirichlet distributions over hypothesis sets.
All computation performed by Claude using skills.

Responsibilities:
- State initialization and persistence
- Data structure management (alpha/posterior, observation_history)
- Serialization (to_dict/from_dict)

Skills:
- /with-me:entropy
- /with-me:bayesian-update
- /with-me:information-gain

Related: #37
"""

import doctest
import math
import sys
from typing import Any


class HypothesisSet:
    """
    Manages hypothesis set and Dirichlet distribution for a dimension.

    A hypothesis set represents possible values for a requirement dimension
    (e.g., "web app", "CLI tool", "library" for purpose dimension).

    Internally tracks Dirichlet concentration parameters (alpha). The posterior
    probability distribution is derived as p(h) = alpha[h] / sum(alpha).

    This class provides state management only. All computations are delegated to skills:
    - /with-me:entropy for entropy calculation
    - /with-me:bayesian-update for posterior updating
    - /with-me:information-gain for information gain calculation

    Constants:
        EPSILON: Small value to avoid log(0) errors in entropy calculation

    Examples:
        >>> # Initialize with uniform prior
        >>> hs = HypothesisSet(
        ...     dimension="purpose", hypotheses=["web_app", "cli_tool", "library"]
        ... )
        >>> round(hs.posterior["web_app"], 2)
        0.33

        >>> # Get most likely hypothesis
        >>> hs.posterior = {"web_app": 0.7, "cli_tool": 0.2, "library": 0.1}
        >>> hs.get_most_likely()
        'web_app'
    """

    # Class constants
    EPSILON = 1e-10  # Threshold to avoid log(0) in entropy calculation

    def __init__(
        self,
        dimension: str,
        hypotheses: list[str],
        prior: dict[str, float] | None = None,
        alpha: dict[str, float] | None = None,
    ):
        """
        Initialize hypothesis set with Dirichlet parameters.

        Args:
            dimension: Dimension name (e.g., "purpose", "data", "behavior")
            hypotheses: List of hypothesis identifiers
            prior: Optional prior distribution {hypothesis: probability}
                   Converted to alpha: alpha[h] = prior[h]/total * N
            alpha: Optional Dirichlet concentration parameters (takes precedence)

        Examples:
            >>> # Uniform prior (default) - alpha = 1.0 for each
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

            >>> # Direct alpha initialization
            >>> hs = HypothesisSet(
            ...     "test", ["a", "b"], alpha={"a": 5.0, "b": 3.0}
            ... )
            >>> round(hs.posterior["a"], 3)
            0.625
        """
        self.dimension = dimension
        self.hypotheses = hypotheses

        if alpha is not None:
            # Direct alpha initialization (preferred for deserialization)
            self.alpha = dict(alpha)
        elif prior is not None:
            # Convert prior probabilities to alpha: alpha[h] = p(h) * N
            total = sum(prior.values())
            n = len(hypotheses)
            if total > 0:
                self.alpha = {h: (prior[h] / total) * n for h in hypotheses}
            else:
                self.alpha = {h: 1.0 for h in hypotheses}
        else:
            # Uniform prior: alpha[h] = 1.0 for all hypotheses
            self.alpha = {h: 1.0 for h in hypotheses}

        # History of observations (for debugging/analysis)
        self.observation_history: list[dict[str, Any]] = []

        # Cached computation results (set by persist-computation CLI)
        self._cached_entropy: float | None = None
        self._cached_confidence: float | None = None

    @property
    def posterior(self) -> dict[str, float]:
        """
        Compute posterior from Dirichlet alpha: p(h) = alpha[h] / sum(alpha).

        Returns:
            Posterior probability distribution

        Examples:
            >>> hs = HypothesisSet("test", ["a", "b"], alpha={"a": 3.0, "b": 1.0})
            >>> hs.posterior["a"]
            0.75
        """
        total = sum(self.alpha.values())
        if total > 0:
            return {h: self.alpha[h] / total for h in self.hypotheses}
        return {h: 1.0 / len(self.hypotheses) for h in self.hypotheses}

    @posterior.setter
    def posterior(self, value: dict[str, float]) -> None:
        """
        Set alpha from posterior probabilities (backward compatibility).

        Preserves total alpha sum (information content) while adjusting
        the distribution to match the given probabilities.

        Examples:
            >>> hs = HypothesisSet("test", ["a", "b"])
            >>> hs.posterior = {"a": 0.8, "b": 0.2}
            >>> hs.posterior["a"]
            0.8
        """
        alpha_sum = sum(self.alpha.values())
        for h in self.hypotheses:
            self.alpha[h] = value.get(h, 0.0) * alpha_sum

    @property
    def total_observations(self) -> float:
        """
        Total pseudo-observations beyond the initial prior.

        Computed as sum(alpha) - len(alpha), since each hypothesis
        starts with alpha=1.0 in the uniform prior case.

        Returns:
            Number of effective observations accumulated

        Examples:
            >>> hs = HypothesisSet("test", ["a", "b", "c"])
            >>> hs.total_observations
            0.0
            >>> hs.update({"a": 0.5, "b": 0.3, "c": 0.2})
            >>> round(hs.total_observations, 1)
            1.0
        """
        return sum(self.alpha.values()) - len(self.alpha)

    def entropy(self) -> float:
        """
        Calculate Shannon entropy: H(h) = -Sigma p(h) log2 p(h)

        Returns:
            Entropy in bits (0 = certain, log2(N) = maximum uncertainty)

        Examples:
            >>> # Maximum uncertainty (uniform distribution)
            >>> hs = HypothesisSet("test", ["a", "b", "c", "d"])
            >>> round(hs.entropy(), 2)
            2.0

            >>> # Complete certainty
            >>> hs.posterior = {"a": 1.0, "b": 0.0, "c": 0.0, "d": 0.0}
            >>> round(hs.entropy(), 2)
            0.0

            >>> # Partial uncertainty
            >>> hs.posterior = {"a": 0.7, "b": 0.2, "c": 0.05, "d": 0.05}
            >>> 0.9 < hs.entropy() < 1.3
            True
        """
        h = 0.0
        post = self.posterior
        for p in post.values():
            if p > self.EPSILON:  # Avoid log(0)
                h -= p * math.log2(p)
        return h

    def update(self, likelihoods: dict[str, float], weight: float = 1.0) -> None:
        """
        Additive Dirichlet update: alpha_new[h] = alpha_old[h] + weight * L[h].

        Unlike multiplicative Bayesian updates, this produces gradual convergence
        where a single observation cannot dramatically shift beliefs.

        Args:
            likelihoods: L(observation|h) for each hypothesis (normalized, from LLM)
            weight: Scaling factor for the update (default 1.0)

        Examples:
            >>> hs = HypothesisSet("test", ["web_app", "cli_tool"])
            >>> # Start with uniform prior
            >>> hs.posterior["web_app"]
            0.5

            >>> # User answer strongly suggests CLI tool
            >>> hs.update({"web_app": 0.1, "cli_tool": 0.9})
            >>> hs.posterior["cli_tool"] > 0.6
            True

            >>> # Another observation refines belief
            >>> hs.update({"web_app": 0.2, "cli_tool": 0.8})
            >>> hs.posterior["cli_tool"] > 0.65
            True

            >>> # Weighted update (e.g., secondary dimension)
            >>> hs2 = HypothesisSet("test", ["a", "b"])
            >>> hs2.update({"a": 0.8, "b": 0.2}, weight=0.3)
            >>> round(hs2.alpha["a"], 2)
            1.24
        """
        for h in self.hypotheses:
            self.alpha[h] += weight * likelihoods.get(h, 0.0)

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
        post = self.posterior
        return max(post.items(), key=lambda x: x[1])[0]

    # get_confidence() removed - use /with-me:entropy skill
    # Calculate: confidence = 1 - (H / H_max) where H_max = log2(N)

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
            >>> # Modifying copy's alpha doesn't affect original
            >>> hs_copy.alpha["web_app"] = 3.0
            >>> hs.posterior["web_app"]
            0.7
        """
        hs_copy = HypothesisSet(
            self.dimension, self.hypotheses, alpha=dict(self.alpha)
        )
        hs_copy.observation_history = [dict(obs) for obs in self.observation_history]
        hs_copy._cached_entropy = self._cached_entropy
        hs_copy._cached_confidence = self._cached_confidence
        return hs_copy

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize to dictionary for JSON storage.

        Includes both alpha (Dirichlet) and posterior (backward compatibility).

        Returns:
            Dictionary representation

        Examples:
            >>> hs = HypothesisSet("purpose", ["web_app", "cli_tool"])
            >>> data = hs.to_dict()
            >>> data["dimension"]
            'purpose'
            >>> "alpha" in data
            True
            >>> "posterior" in data
            True
        """
        return {
            "dimension": self.dimension,
            "hypotheses": self.hypotheses,
            "alpha": dict(self.alpha),
            "posterior": self.posterior,
            "observation_history": self.observation_history,
            "_cached_entropy": self._cached_entropy,
            "_cached_confidence": self._cached_confidence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HypothesisSet":
        """
        Deserialize from dictionary.

        Prefers alpha field if present; falls back to posterior for v0.3.x compat.

        Args:
            data: Dictionary representation

        Returns:
            HypothesisSet instance

        Examples:
            >>> # v0.4.0 format (with alpha)
            >>> data = {
            ...     "dimension": "purpose",
            ...     "hypotheses": ["web_app", "cli_tool"],
            ...     "alpha": {"web_app": 3.0, "cli_tool": 1.0},
            ...     "posterior": {"web_app": 0.75, "cli_tool": 0.25},
            ... }
            >>> hs = HypothesisSet.from_dict(data)
            >>> hs.alpha["web_app"]
            3.0

            >>> # v0.3.x format (posterior only, backward compat)
            >>> data_old = {
            ...     "dimension": "purpose",
            ...     "hypotheses": ["web_app", "cli_tool"],
            ...     "posterior": {"web_app": 0.6, "cli_tool": 0.4},
            ... }
            >>> hs_old = HypothesisSet.from_dict(data_old)
            >>> hs_old.dimension
            'purpose'
            >>> round(hs_old.posterior["web_app"], 1)
            0.6
        """
        alpha = data.get("alpha")
        if alpha is not None:
            hs = cls(
                dimension=data["dimension"],
                hypotheses=data["hypotheses"],
                alpha=alpha,
            )
        else:
            # Backward compatibility: reconstruct alpha from posterior
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


def compute_jsd(p: dict[str, float], q: dict[str, float]) -> float:
    """
    Compute Jensen-Shannon Divergence between two distributions.

    JSD(P||Q) = H(M) - 0.5*H(P) - 0.5*H(Q), where M = 0.5*(P+Q).
    Uses log base 2, so result is in [0, 1].

    Args:
        p: First probability distribution {key: probability}
        q: Second probability distribution {key: probability}

    Returns:
        JSD value in [0, 1]

    Examples:
        >>> # Identical distributions -> JSD = 0
        >>> p = {"a": 0.5, "b": 0.3, "c": 0.2}
        >>> round(compute_jsd(p, p), 4)
        0.0

        >>> # Very different distributions -> high JSD
        >>> p = {"a": 1.0, "b": 0.0}
        >>> q = {"a": 0.0, "b": 1.0}
        >>> round(compute_jsd(p, q), 4)
        1.0

        >>> # Partially different distributions
        >>> p = {"a": 0.7, "b": 0.2, "c": 0.1}
        >>> q = {"a": 0.3, "b": 0.4, "c": 0.3}
        >>> 0.05 < compute_jsd(p, q) < 0.15
        True
    """
    epsilon = 1e-10
    keys = set(p.keys()) | set(q.keys())

    def _entropy(dist: dict[str, float]) -> float:
        h = 0.0
        for k in keys:
            v = dist.get(k, 0.0)
            if v > epsilon:
                h -= v * math.log2(v)
        return h

    # M = 0.5 * (P + Q)
    m = {k: 0.5 * (p.get(k, 0.0) + q.get(k, 0.0)) for k in keys}

    jsd = _entropy(m) - 0.5 * _entropy(p) - 0.5 * _entropy(q)
    return max(0.0, jsd)  # Clamp floating-point negatives


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
    min_argc = 2  # program name + command
    if len(sys.argv) < min_argc:
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
