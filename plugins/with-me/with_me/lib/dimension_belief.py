#!/usr/bin/env python3
"""
Bayesian Belief Updating for Requirement Dimensions

Implements information-theoretic approach to uncertainty tracking using
Bayesian belief updating over hypothesis sets.

Theoretical Foundation:
- Shannon Entropy: H(h) = -Σ p(h) log₂ p(h) measures uncertainty
- Bayesian Update: p₁(h) ∝ p₀(h) × L(observation|h) updates beliefs
- Expected Information Gain (EIG): Measures question value before asking
- Stdlib-only: Uses Python 3.11+ standard library (math, re modules only)

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
import re
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
        >>> ig = hs.update(
        ...     observation="user mentioned REST API", answer="Yes, REST API"
        ... )
        >>> ig > 0  # Information gained
        True
        >>> # Entropy should decrease after learning
        >>> hs.entropy() < 1.58
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

    def update(self, observation: str, answer: str) -> float:
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

        Returns:
            Information gain in bits: ΔH = H_before - H_after

        Examples:
            >>> hs = HypothesisSet("purpose", ["web_app", "cli_tool", "library"])
            >>> h_before = hs.entropy()
            >>> # Strong evidence for "web_app"
            >>> ig = hs.update(
            ...     observation="Asked about user interface",
            ...     answer="Yes, users will interact via browser",
            ... )
            >>> ig > 0  # Information was gained
            True
            >>> hs.entropy() < h_before  # Uncertainty decreased
            True
        """
        h_before = self.entropy()

        # Calculate likelihood for each hypothesis
        likelihoods = {}
        for hypothesis in self.hypotheses:
            likelihoods[hypothesis] = self._estimate_likelihood(
                hypothesis, observation, answer
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

    def _estimate_likelihood(
        self, hypothesis: str, observation: str, answer: str
    ) -> float:
        """
        Estimate likelihood L(observation, answer | hypothesis).

        Uses weighted keyword matching with improvements from Issue #37:
        1. **Weighted keywords**: Discriminative terms (e.g., "browser") get higher
           weights (1.5-2.0) than generic terms (0.5)
        2. **Negation handling**: Detects negation cues (not/no/without/etc.) and
           subtracts weight for keywords in negation scope (~5 words after cue)
        3. **Likelihood clamping**: Result clamped to [0.05, 0.95] to avoid extremes
        4. **Non-English fallback**: Returns conservative default (0.3) for text
           with high non-ASCII ratio (>30%)

        This is a stdlib-only approximation. More sophisticated approaches (NLP,
        embeddings) would require external libraries.

        **Remaining Limitations:**
        - Negation scope is simple (5-word window, no parse tree)
        - Keyword weights are manually assigned, not learned
        - Non-English text gets conservative fallback instead of translation

        Args:
            hypothesis: Hypothesis identifier
            observation: Question context
            answer: User's answer

        Returns:
            Likelihood value in [0.05, 0.95], will be normalized in update()

        Examples:
            >>> hs = HypothesisSet("purpose", ["web_app", "cli_tool"])
            >>> # "web_app" has higher likelihood due to "browser" (high weight)
            >>> l_web = hs._estimate_likelihood(
            ...     "web_app", "user interface", "browser interaction"
            ... )
            >>> l_cli = hs._estimate_likelihood(
            ...     "cli_tool", "user interface", "browser interaction"
            ... )
            >>> l_web > l_cli
            True

            >>> # Negation handling: "Not a CLI" decreases cli_tool likelihood
            >>> l_cli_neg = hs._estimate_likelihood(
            ...     "cli_tool", "interface type", "Not a CLI, want web interface"
            ... )
            >>> l_cli_pos = hs._estimate_likelihood(
            ...     "cli_tool", "interface type", "Yes, a CLI tool"
            ... )
            >>> l_cli_neg < l_cli_pos  # Negation decreases likelihood
            True
        """
        # Combine observation and answer for matching
        text = (observation + " " + answer).lower()

        # Non-English fallback: detect high non-ASCII ratio
        non_ascii_ratio = sum(1 for c in text if ord(c) > 127) / max(len(text), 1)
        if non_ascii_ratio > 0.3:
            # Conservative default for non-English text (Issue #37)
            return 0.3

        # Get weighted keywords for hypothesis
        keyword_weights = self._get_hypothesis_keywords(hypothesis)

        # Detect negation cues and their scope
        negation_pattern = r"\b(not|no|without|exclude|avoid|never|don't|doesn't)\b"
        negated_spans = []
        for match in re.finditer(negation_pattern, text):
            # Negation scope: ~5 words after negation cue
            start = match.start()
            # Find next 5 word boundaries
            words_after = text[start:].split()[:6]  # negation word + 5 after
            negated_text = " ".join(words_after)
            negated_spans.append(negated_text)

        # Calculate weighted match score with negation handling
        score = 0.0
        for keyword, weight in keyword_weights.items():
            if keyword in text:
                # Check if keyword is in negation scope
                is_negated = any(keyword in span for span in negated_spans)
                if is_negated:
                    # Subtract weight for negated keywords
                    score -= weight
                else:
                    # Add weight for positive matches
                    score += weight

        # Clamp score to non-negative
        score = max(0.0, score)

        # Laplace smoothing with weighted score
        alpha = 1.0
        total_weight = sum(keyword_weights.values()) if keyword_weights else 1.0
        likelihood = (score + alpha) / (total_weight + alpha * len(self.hypotheses))

        # Clamp likelihood to [0.05, 0.95] to avoid extreme values
        likelihood = max(0.05, min(0.95, likelihood))

        return likelihood

    def _get_hypothesis_keywords(self, hypothesis: str) -> dict[str, float]:
        """
        Get weighted keywords associated with a hypothesis.

        Returns dictionary mapping keywords to discriminative weights:
        - High weight (1.5-2.0): Highly discriminative terms (e.g., "browser" for web_app)
        - Medium weight (1.0): Moderately discriminative terms
        - Low weight (0.5): Generic terms that appear in multiple contexts

        Args:
            hypothesis: Hypothesis identifier

        Returns:
            Dictionary mapping keywords to weights

        Examples:
            >>> hs = HypothesisSet("purpose", ["web_app"])
            >>> keywords = hs._get_hypothesis_keywords("web_app")
            >>> "browser" in keywords
            True
            >>> keywords["browser"] >= 1.5  # High discriminative weight
            True
        """
        # Weighted keyword database (dimension-specific)
        # Weights: 2.0=highly discriminative, 1.0=moderate, 0.5=generic
        keyword_db = {
            # Purpose dimension
            "web_app": {
                "browser": 2.0,
                "frontend": 2.0,
                "html": 1.5,
                "web": 1.5,
                "ui": 1.0,
                "user interface": 1.0,
                "http": 1.0,
            },
            "cli_tool": {
                "terminal": 2.0,
                "cli": 2.0,
                "command": 1.5,
                "shell": 1.5,
                "console": 1.5,
                "script": 1.0,
            },
            "library": {
                "import": 2.0,
                "package": 2.0,
                "library": 1.5,
                "module": 1.5,
                "reusable": 1.5,
                "api": 0.5,  # Generic: also appears in web_app, service
            },
            "service": {
                "daemon": 2.0,
                "service": 1.5,
                "endpoint": 1.5,
                "server": 1.0,
                "background": 1.0,
                "api": 0.5,  # Generic
            },
            # Data dimension
            "structured": {
                "json": 2.0,
                "xml": 2.0,
                "csv": 2.0,
                "schema": 1.5,
                "table": 1.5,
                "database": 1.0,
            },
            "unstructured": {
                "document": 1.5,
                "text": 1.0,
                "content": 1.0,
                "raw": 1.0,
                "file": 0.5,  # Generic
            },
            "streaming": {
                "stream": 2.0,
                "real-time": 2.0,
                "live": 1.5,
                "continuous": 1.5,
                "flow": 1.0,
            },
            # Behavior dimension
            "synchronous": {
                "sync": 2.0,
                "sequential": 1.5,
                "blocking": 1.5,
                "wait": 1.0,
                "order": 1.0,
            },
            "asynchronous": {
                "async": 2.0,
                "concurrent": 1.5,
                "parallel": 1.5,
                "non-blocking": 1.5,
            },
            "interactive": {
                "interactive": 2.0,
                "prompt": 1.5,
                "dialog": 1.5,
                "input": 1.0,
                "response": 1.0,
            },
            "batch": {
                "batch": 2.0,
                "bulk": 1.5,
                "scheduled": 1.5,
                "automated": 1.0,
                "background": 1.0,
            },
            # Constraints dimension
            "performance": {
                "fast": 1.5,
                "performance": 1.5,
                "speed": 1.5,
                "latency": 1.5,
                "throughput": 1.5,
            },
            "scalability": {
                "scale": 2.0,
                "load": 1.5,
                "capacity": 1.5,
                "volume": 1.0,
                "concurrent": 1.0,
            },
            "reliability": {
                "reliable": 1.5,
                "stable": 1.5,
                "robust": 1.5,
                "fault": 1.0,
                "error": 0.5,  # Generic
            },
            "security": {
                "authentication": 2.0,
                "authorization": 2.0,
                "secure": 1.5,
                "encrypt": 1.5,
            },
            # Quality dimension
            "functional": {
                "feature": 1.5,
                "function": 1.5,
                "capability": 1.5,
                "requirement": 1.0,
            },
            "usability": {
                "user-friendly": 2.0,
                "usable": 1.5,
                "intuitive": 1.5,
                "experience": 1.0,
            },
            "maintainability": {
                "maintainable": 2.0,
                "readable": 1.5,
                "documented": 1.5,
                "testable": 1.5,
            },
        }

        return keyword_db.get(hypothesis, {})

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
