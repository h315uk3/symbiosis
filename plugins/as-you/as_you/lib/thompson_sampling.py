#!/usr/bin/env python3
"""Thompson Sampling for pattern selection and exploration-exploitation.

Thompson Sampling is a Bayesian approach to the multi-armed bandit problem,
balancing exploration of uncertain patterns with exploitation of known good
patterns. It uses Beta distribution to model success/failure probabilities.

The Beta distribution parameters (alpha, beta) represent:
    alpha: Number of successes + 1
    beta: Number of failures + 1

After observing a success/failure:
    alpha' = alpha + 1 (if success)
    beta' = beta + 1 (if failure)

The mean of Beta(alpha, beta) is alpha / (alpha + beta), and variance
decreases as more observations are collected, leading to less exploration
and more exploitation.

References:
    Agrawal, S. & Goyal, N. (2012). Analysis of Thompson Sampling for
    the Multi-armed Bandit Problem. Conference on Learning Theory.
"""

import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path

# Add plugin to path for imports
_PLUGIN_ROOT = Path(__file__).parent.parent.parent
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from as_you.lib.common import DEFAULT_SETTINGS  # noqa: E402


@dataclass
class ThompsonState:
    """Thompson Sampling state using Beta distribution.

    Examples:
        >>> state = ThompsonState(alpha=5.0, beta=2.0)
        >>> state.alpha
        5.0
        >>> state.beta
        2.0
        >>> round(state.mean, 2)
        0.71
    """

    alpha: float  # Success count + 1
    beta: float  # Failure count + 1

    @property
    def mean(self) -> float:
        """Expected success rate (mean of Beta distribution).

        Examples:
            >>> state = ThompsonState(5.0, 2.0)
            >>> round(state.mean, 2)
            0.71
            >>> state2 = ThompsonState(1.0, 1.0)  # Uniform prior
            >>> state2.mean
            0.5
        """
        return self.alpha / (self.alpha + self.beta)

    @property
    def variance(self) -> float:
        """Variance of Beta distribution (uncertainty).

        Examples:
            >>> state = ThompsonState(5.0, 2.0)
            >>> round(state.variance, 3)
            0.026
            >>> state2 = ThompsonState(1.0, 1.0)  # High uncertainty
            >>> round(state2.variance, 3)
            0.083
        """
        alpha_beta = self.alpha + self.beta
        return (self.alpha * self.beta) / (alpha_beta * alpha_beta * (alpha_beta + 1))

    @property
    def std_dev(self) -> float:
        """Standard deviation (square root of variance).

        Examples:
            >>> state = ThompsonState(5.0, 2.0)
            >>> round(state.std_dev, 2)
            0.16
        """
        return math.sqrt(self.variance)


def sample_from_beta(alpha: float, beta: float) -> float:
    """Sample from Beta(alpha, beta) distribution.

    Uses ratio of two Gamma distributions:
        X ~ Gamma(alpha, 1)
        Y ~ Gamma(beta, 1)
        Beta ~ X / (X + Y)

    Args:
        alpha: Success parameter
        beta: Failure parameter

    Returns:
        Sample from Beta(alpha, beta) in [0, 1]

    Examples:
        >>> random.seed(42)
        >>> sample = sample_from_beta(5.0, 2.0)
        >>> 0.0 <= sample <= 1.0
        True
        >>> # Higher alpha should give higher samples on average
        >>> random.seed(42)
        >>> high_alpha = sample_from_beta(10.0, 2.0)
        >>> low_alpha = sample_from_beta(2.0, 10.0)
        >>> high_alpha > low_alpha
        True
    """
    x = random.gammavariate(alpha, 1.0)
    y = random.gammavariate(beta, 1.0)
    return x / (x + y)


def sample_from_state(state: ThompsonState) -> float:
    """Sample from Thompson state's Beta distribution.

    Args:
        state: Thompson state

    Returns:
        Sampled success probability

    Examples:
        >>> random.seed(42)
        >>> state = ThompsonState(5.0, 2.0)
        >>> sample = sample_from_state(state)
        >>> 0.0 <= sample <= 1.0
        True
    """
    return sample_from_beta(state.alpha, state.beta)


def update_thompson_state(state: ThompsonState, success: bool) -> ThompsonState:
    """Update Thompson state with feedback.

    Args:
        state: Current state
        success: Whether action was successful

    Returns:
        Updated state

    Examples:
        >>> state = ThompsonState(1.0, 1.0)  # Uniform prior
        >>> state.mean
        0.5
        >>> # After success, mean increases
        >>> state2 = update_thompson_state(state, True)
        >>> state2.alpha
        2.0
        >>> state2.beta
        1.0
        >>> round(state2.mean, 2)
        0.67
        >>> # After failure, mean decreases
        >>> state3 = update_thompson_state(state, False)
        >>> state3.alpha
        1.0
        >>> state3.beta
        2.0
        >>> round(state3.mean, 2)
        0.33
        >>> # Multiple successes increase confidence
        >>> state4 = update_thompson_state(state2, True)
        >>> state4.alpha
        3.0
        >>> round(state4.mean, 2)
        0.75
    """
    if success:
        return ThompsonState(alpha=state.alpha + 1, beta=state.beta)
    else:
        return ThompsonState(alpha=state.alpha, beta=state.beta + 1)


def select_pattern(states: dict[str, ThompsonState]) -> str:
    """Select pattern using Thompson Sampling.

    Samples from each pattern's Beta distribution and selects
    the pattern with highest sample (exploration-exploitation).

    Args:
        states: Mapping of pattern text to Thompson state

    Returns:
        Selected pattern text

    Examples:
        >>> random.seed(42)
        >>> states = {
        ...     "pattern_a": ThompsonState(10.0, 2.0),  # High success
        ...     "pattern_b": ThompsonState(2.0, 10.0),  # Low success
        ...     "pattern_c": ThompsonState(1.0, 1.0),  # Unknown
        ... }
        >>> # High success pattern usually selected
        >>> selected = select_pattern(states)
        >>> selected in states
        True
    """
    if not states:
        msg = "No patterns to select from"
        raise ValueError(msg)

    samples = {pattern: sample_from_state(state) for pattern, state in states.items()}
    return max(samples, key=samples.get)


def create_initial_state(
    initial_alpha: float | None = None,
    initial_beta: float | None = None,
) -> ThompsonState:
    """Create initial Thompson state.

    Args:
        initial_alpha: Initial alpha (None = use default)
        initial_beta: Initial beta (None = use default)

    Returns:
        Initial Thompson state

    Examples:
        >>> state = create_initial_state()
        >>> state.alpha
        1.0
        >>> state.beta
        1.0
        >>> state.mean
        0.5
        >>> custom = create_initial_state(2.0, 3.0)
        >>> custom.alpha
        2.0
        >>> custom.beta
        3.0
        >>> custom.mean
        0.4
    """
    if initial_alpha is None:
        initial_alpha = DEFAULT_SETTINGS["confidence"]["thompson_sampling"][
            "initial_alpha"
        ]
    if initial_beta is None:
        initial_beta = DEFAULT_SETTINGS["confidence"]["thompson_sampling"][
            "initial_beta"
        ]

    return ThompsonState(alpha=initial_alpha, beta=initial_beta)


def calculate_exploration_score(state: ThompsonState) -> float:
    """Calculate exploration score (higher = more uncertain).

    Uses standard deviation as exploration metric.
    High std_dev = high uncertainty = more exploration value.

    Args:
        state: Thompson state

    Returns:
        Exploration score (0-1)

    Examples:
        >>> # New pattern (high uncertainty)
        >>> state1 = ThompsonState(1.0, 1.0)
        >>> round(calculate_exploration_score(state1), 3)
        0.289
        >>> # Established pattern (low uncertainty)
        >>> state2 = ThompsonState(50.0, 50.0)
        >>> round(calculate_exploration_score(state2), 3)
        0.05
        >>> # Exploration decreases with more observations
        >>> state1_score = calculate_exploration_score(ThompsonState(1.0, 1.0))
        >>> state2_score = calculate_exploration_score(ThompsonState(10.0, 10.0))
        >>> state1_score > state2_score
        True
    """
    return state.std_dev


def calculate_exploitation_score(state: ThompsonState) -> float:
    """Calculate exploitation score (higher = more proven success).

    Uses mean success rate as exploitation metric.

    Args:
        state: Thompson state

    Returns:
        Exploitation score (0-1)

    Examples:
        >>> state1 = ThompsonState(9.0, 1.0)  # 90% success
        >>> round(calculate_exploitation_score(state1), 1)
        0.9
        >>> state2 = ThompsonState(1.0, 9.0)  # 10% success
        >>> round(calculate_exploitation_score(state2), 1)
        0.1
    """
    return state.mean


if __name__ == "__main__":
    import doctest

    # Check if running doctests
    if "--test" in sys.argv or "-v" in sys.argv:
        print("Running Thompson Sampling doctests:")
        results = doctest.testmod(verbose=("--verbose" in sys.argv or "-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        # Demo
        print("Thompson Sampling Demo")
        print("-" * 50)

        # Simulate pattern selection with feedback
        patterns = {
            "pattern_a": create_initial_state(),
            "pattern_b": create_initial_state(),
            "pattern_c": create_initial_state(),
        }

        print("Initial states:")
        for name, state in patterns.items():
            print(
                f"  {name}: alpha={state.alpha}, beta={state.beta}, mean={state.mean:.3f}"
            )

        # Simulate 10 rounds
        random.seed(42)
        for round_num in range(1, 11):
            selected = select_pattern(patterns)
            # Simulate success (pattern_a has 80% success rate, others 40%)
            success = random.random() < (0.8 if selected == "pattern_a" else 0.4)
            patterns[selected] = update_thompson_state(patterns[selected], success)

            result = "✓" if success else "✗"
            print(f"\nRound {round_num}: Selected {selected} {result}")
            state = patterns[selected]
            print(
                f"  Updated: alpha={state.alpha:.1f}, beta={state.beta:.1f}, mean={state.mean:.3f}"
            )

        print("\nFinal states:")
        for name, state in sorted(
            patterns.items(), key=lambda x: x[1].mean, reverse=True
        ):
            explore = calculate_exploration_score(state)
            exploit = calculate_exploitation_score(state)
            print(
                f"  {name}: mean={state.mean:.3f}, "
                f"explore={explore:.3f}, exploit={exploit:.3f}"
            )
