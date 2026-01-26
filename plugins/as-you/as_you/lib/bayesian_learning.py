#!/usr/bin/env python3
"""Bayesian learning for pattern confidence tracking.

Bayesian inference updates our belief about a pattern's quality based on
observed data. This module implements Bayesian updating of a pattern's
confidence using a Gaussian (Normal) distribution model.

The posterior distribution after observing data is:
    posterior_mean = (prior_mean/prior_var + observation/obs_var) /
                     (1/prior_var + 1/obs_var)
    posterior_var = 1 / (1/prior_var + 1/obs_var)

This provides:
1. Confidence mean: Expected quality of the pattern
2. Confidence variance: Uncertainty about the quality

References:
    Bishop, C. M. (2006). Pattern Recognition and Machine Learning.
    Chapter 2: Probability Distributions.
"""

import math
import sys
from dataclasses import dataclass
from pathlib import Path

# Add plugin to path for imports
_PLUGIN_ROOT = Path(__file__).parent.parent.parent
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from as_you.lib.common import DEFAULT_SETTINGS  # noqa: E402


@dataclass
class BayesianState:
    """Bayesian confidence state.

    Examples:
        >>> state = BayesianState(mean=0.5, variance=0.04)
        >>> state.mean
        0.5
        >>> state.variance
        0.04
        >>> state.std_dev
        0.2
    """

    mean: float  # Posterior mean (expected quality)
    variance: float  # Posterior variance (uncertainty)

    @property
    def std_dev(self) -> float:
        """Standard deviation (square root of variance).

        Examples:
            >>> state = BayesianState(0.5, 0.04)
            >>> state.std_dev
            0.2
            >>> state2 = BayesianState(0.7, 0.01)
            >>> state2.std_dev
            0.1
        """
        return math.sqrt(self.variance)

    @property
    def confidence_interval_95(self) -> tuple[float, float]:
        """95% confidence interval (mean ± 1.96 * std_dev).

        Examples:
            >>> state = BayesianState(0.5, 0.04)
            >>> lower, upper = state.confidence_interval_95
            >>> round(lower, 2)
            0.11
            >>> round(upper, 2)
            0.89
        """
        margin = 1.96 * self.std_dev
        return (self.mean - margin, self.mean + margin)


def update_bayesian_state(
    prior_mean: float,
    prior_variance: float,
    observation: float,
    observation_variance: float,
) -> BayesianState:
    """Update Bayesian state with new observation.

    Args:
        prior_mean: Prior belief mean
        prior_variance: Prior belief variance
        observation: New observed value
        observation_variance: Uncertainty in observation

    Returns:
        Updated Bayesian state

    Examples:
        >>> # Start with neutral prior (0.5 ± 0.2)
        >>> state = update_bayesian_state(0.5, 0.04, 0.8, 0.01)
        >>> round(state.mean, 2)
        0.74
        >>> round(state.variance, 4)
        0.008
        >>> # High confidence observation (low variance)
        >>> state2 = update_bayesian_state(0.5, 0.04, 0.9, 0.001)
        >>> round(state2.mean, 2)
        0.89
        >>> # Low confidence observation (high variance)
        >>> state3 = update_bayesian_state(0.5, 0.04, 0.9, 0.1)
        >>> round(state3.mean, 2)
        0.61
    """
    # Precision (inverse variance) is easier to work with
    prior_precision = 1.0 / prior_variance
    obs_precision = 1.0 / observation_variance

    # Posterior precision (sum of precisions)
    posterior_precision = prior_precision + obs_precision

    # Posterior variance (inverse precision)
    posterior_variance = 1.0 / posterior_precision

    # Posterior mean (weighted average)
    posterior_mean = posterior_variance * (
        prior_precision * prior_mean + obs_precision * observation
    )

    return BayesianState(mean=posterior_mean, variance=posterior_variance)


def create_initial_bayesian_state(
    initial_mean: float | None = None,
    initial_variance: float | None = None,
) -> BayesianState:
    """Create initial Bayesian state.

    Args:
        initial_mean: Initial mean (None = use default)
        initial_variance: Initial variance (None = use default)

    Returns:
        Initial Bayesian state

    Examples:
        >>> state = create_initial_bayesian_state()
        >>> state.mean
        0.5
        >>> state.variance
        0.04
        >>> custom = create_initial_bayesian_state(0.7, 0.01)
        >>> custom.mean
        0.7
        >>> custom.variance
        0.01
    """
    if initial_mean is None:
        initial_mean = float(DEFAULT_SETTINGS["confidence"]["bayesian"]["prior_mean"])
    if initial_variance is None:
        initial_variance = float(
            DEFAULT_SETTINGS["confidence"]["bayesian"]["prior_variance"]
        )

    return BayesianState(mean=initial_mean, variance=initial_variance)


def calculate_observation_score(
    success: bool,
    success_quality: float = 0.8,
    failure_quality: float = 0.2,
) -> float:
    """Convert binary success/failure to observation score.

    Args:
        success: Whether the pattern was successfully applied
        success_quality: Score for successful application (default: 0.8)
        failure_quality: Score for failed application (default: 0.2)

    Returns:
        Observation score

    Examples:
        >>> calculate_observation_score(True)
        0.8
        >>> calculate_observation_score(False)
        0.2
        >>> calculate_observation_score(True, 0.9, 0.1)
        0.9
    """
    return success_quality if success else failure_quality


def update_with_feedback(
    state: BayesianState,
    success: bool,
    observation_variance: float = 0.01,
) -> BayesianState:
    """Update Bayesian state with user feedback.

    Args:
        state: Current Bayesian state
        success: Whether pattern application was successful
        observation_variance: Uncertainty in observation (default: 0.01)

    Returns:
        Updated Bayesian state

    Examples:
        >>> state = create_initial_bayesian_state()
        >>> state.mean
        0.5
        >>> # Successful application increases confidence
        >>> state2 = update_with_feedback(state, True)
        >>> state2.mean > state.mean
        True
        >>> state2.variance < state.variance
        True
        >>> # Failed application decreases confidence
        >>> state3 = update_with_feedback(state, False)
        >>> state3.mean < state.mean
        True
        >>> # Multiple successes increase confidence further
        >>> state4 = update_with_feedback(state2, True)
        >>> state4.mean > state2.mean
        True
    """
    observation = calculate_observation_score(success)
    return update_bayesian_state(
        state.mean, state.variance, observation, observation_variance
    )


def calculate_confidence_score(state: BayesianState) -> float:
    """Calculate overall confidence score (0-1).

    Confidence is high when:
    1. Mean is high (good quality)
    2. Variance is low (high certainty)

    Formula: mean * (1 - sqrt(variance))

    Args:
        state: Bayesian state

    Returns:
        Confidence score (0-1)

    Examples:
        >>> # High mean, low variance = high confidence
        >>> state1 = BayesianState(0.9, 0.01)
        >>> round(calculate_confidence_score(state1), 2)
        0.81
        >>> # High mean, high variance = medium confidence
        >>> state2 = BayesianState(0.9, 0.04)
        >>> round(calculate_confidence_score(state2), 2)
        0.72
        >>> # Low mean = low confidence
        >>> state3 = BayesianState(0.3, 0.01)
        >>> round(calculate_confidence_score(state3), 2)
        0.27
    """
    certainty = 1.0 - math.sqrt(state.variance)
    return state.mean * certainty


if __name__ == "__main__":
    import doctest

    # Check if running doctests
    if "--test" in sys.argv or "-v" in sys.argv:
        print("Running Bayesian learning doctests:")
        results = doctest.testmod(verbose=("--verbose" in sys.argv or "-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        # Demo
        print("Bayesian Learning Demo")
        print("-" * 50)

        state = create_initial_bayesian_state()
        print(f"Initial state: mean={state.mean:.3f}, variance={state.variance:.4f}")

        # Simulate feedback
        feedbacks = [True, True, False, True, True]
        for i, success in enumerate(feedbacks, 1):
            state = update_with_feedback(state, success)
            confidence = calculate_confidence_score(state)
            result = "✓ success" if success else "✗ failure"
            print(
                f"Feedback {i} ({result}): "
                f"mean={state.mean:.3f}, "
                f"variance={state.variance:.4f}, "
                f"confidence={confidence:.3f}"
            )
