#!/usr/bin/env python3
"""
Uncertainty Calculator for Good Question Command

Simplified approximation model inspired by information theory principles.

Design notes:
- No probability distributions: Uses uncertainty scores (0.0-1.0) as proxies
- Information gain: Approximation, not strict I(X;Y) = H(X) - H(X|Y)
- Lexical diversity: Vocabulary variation, not TF-IDF (requires corpus)
- Constraint: Python 3.11+ stdlib only (no NumPy/SciPy)

See: docs/with-me-information-theory-analysis.md for theoretical analysis.
Pure Python standard library implementation.
"""

import json
import math
import sys
from typing import Any


def calculate_entropy(probabilities: list[float]) -> float:
    """
    Calculate Shannon entropy for a probability distribution.

    Args:
        probabilities: List of probability values (must sum to 1.0)

    Returns:
        Entropy value (0.0 = complete certainty, higher = more uncertainty)

    Examples:
        >>> calculate_entropy([1.0])
        0.0
        >>> round(calculate_entropy([0.5, 0.5]), 2)
        1.0
        >>> round(calculate_entropy([0.25, 0.25, 0.25, 0.25]), 2)
        2.0
    """
    result = -sum(p * math.log2(p) for p in probabilities if p > 0)
    return abs(result) if abs(result) < 1e-10 else result  # Handle -0.0


def calculate_lexical_diversity(content: str) -> float:
    """
    Calculate lexical diversity as unique word ratio.

    Linguistic measure (not information-theoretic or TF-IDF):
    - Definition: unique_words / total_words
    - Intuition: Vocabulary variation indicates detailed content
    - Note: Single text only; TF-IDF requires corpus statistics

    Args:
        content: Text content to analyze

    Returns:
        Lexical diversity (0.0-1.0, higher = more varied vocabulary)

    Examples:
        >>> calculate_lexical_diversity("word word word")
        0.3333333333333333
        >>> calculate_lexical_diversity("each word is unique here")
        1.0
        >>> calculate_lexical_diversity("")
        0.0
        >>> # Low diversity: repetitive content
        >>> calculate_lexical_diversity("test test test test")
        0.25
        >>> # High diversity: varied vocabulary
        >>> round(calculate_lexical_diversity("comprehensive analysis reveals multiple dimensions"), 2)
        1.0
    """
    words = content.lower().split()
    if not words:
        return 0.0
    unique_words = set(words)
    return len(unique_words) / len(words)


def calculate_information_density(content: str) -> float:
    """
    Deprecated: Use calculate_lexical_diversity() instead.

    This function has been renamed to clarify that it measures lexical diversity,
    not information density or TF-IDF.

    Args:
        content: Text content to analyze

    Returns:
        Lexical diversity (0.0-1.0)

    Examples:
        >>> calculate_information_density("word word word")
        0.3333333333333333
        >>> calculate_information_density("each word is unique here")
        1.0
        >>> calculate_information_density("")
        0.0
        >>> # Low density: repetitive content
        >>> calculate_information_density("test test test test")
        0.25
        >>> # High density: varied vocabulary
        >>> round(calculate_information_density("comprehensive analysis reveals multiple dimensions"), 2)
        1.0
    """
    return calculate_lexical_diversity(content)


def calculate_dimension_uncertainty(dimension_data: dict[str, Any]) -> float:
    """
    Calculate uncertainty score for a single dimension (0.0-1.0).

    Theoretical basis:
    - Shannon entropy: H(X) ∝ log(n), information grows logarithmically
    - Information density: TF-IDF concept, unique word ratio indicates content richness
    - Threshold 0.3: Derived from 70% certainty requirement (1.0 - 0.7 = 0.3)

    References:
    - Cover & Thomas, "Elements of Information Theory", 2006
    - Requirements doc: docs/with-me-evaluation-logic-requirements.md

    Higher score = more uncertain (needs more questions)
    Lower score = more certain (well understood)

    Args:
        dimension_data: Dictionary containing dimension information
            - answered: bool (has this dimension been addressed?)
            - content: str (the actual answer/information)
            - examples: int (number of examples provided)
            - contradictions: bool (are there contradictions?)

    Returns:
        Uncertainty score (0.0 = certain, 1.0 = completely uncertain)

    Examples:
        >>> calculate_dimension_uncertainty({"answered": False})
        1.0
        >>> data_short = {"answered": True, "content": "short"}
        >>> 0.4 < calculate_dimension_uncertainty(data_short) < 0.6
        True
        >>> data_detailed = {
        ...     "answered": True,
        ...     "content": "detailed explanation with many specific technical terms and examples",
        ...     "examples": 2,
        ... }
        >>> calculate_dimension_uncertainty(data_detailed) < 0.4
        True
        >>> data_contradiction = {
        ...     "answered": True,
        ...     "content": "some information provided here",
        ...     "contradictions": True,
        ... }
        >>> calculate_dimension_uncertainty(data_contradiction) > 0.7
        True
        >>> # Test logarithmic decay: more words = less uncertainty (but not linearly)
        >>> # Use unique words to avoid density penalty
        >>> data_5_words = {"answered": True, "content": " ".join([f"word{i}" for i in range(5)])}
        >>> data_10_words = {"answered": True, "content": " ".join([f"word{i}" for i in range(10)])}
        >>> data_20_words = {"answered": True, "content": " ".join([f"word{i}" for i in range(20)])}
        >>> u5 = calculate_dimension_uncertainty(data_5_words)
        >>> u10 = calculate_dimension_uncertainty(data_10_words)
        >>> u20 = calculate_dimension_uncertainty(data_20_words)
        >>> # Verify decreasing uncertainty
        >>> u5 > u10 > u20
        True
        >>> # Verify logarithmic curve: difference decreases as word count grows
        >>> (u5 - u10) > (u10 - u20)
        True
        >>> # Test lexical diversity impact
        >>> low_diversity = {"answered": True, "content": "word word word word word"}
        >>> high_diversity = {"answered": True, "content": "each word is unique here"}
        >>> calculate_dimension_uncertainty(low_diversity) > calculate_dimension_uncertainty(high_diversity)
        True
    """
    if not dimension_data.get("answered", False):
        # Unanswered dimension = complete uncertainty
        return 1.0

    content = dimension_data.get("content", "")
    word_count = len(content.split())

    # Base uncertainty for answered dimension
    # Theoretical basis: Even with an answer, some initial uncertainty remains
    base_uncertainty = 0.8

    # Factor 1: Logarithmic reduction based on word count
    # Empirical heuristic (not Shannon entropy H(X) = -Σp log p):
    # - Longer answers typically indicate more complete knowledge
    # - log-scaling: diminishing returns (word 100 ≠ word 200)
    # - base=100: Empirical choice (typical Q&A length)
    if word_count > 0:
        # log(word_count + 1) / log(100): Normalize to 0-1 range
        info_gain = math.log(word_count + 1) / math.log(100)
        # Maximum 0.6 reduction from word count alone
        base_uncertainty -= min(info_gain, 0.6)

    # Factor 2: Lexical diversity adjustment
    # Empirical observation (not TF-IDF, which requires corpus):
    # - Vocabulary variation correlates with detailed content
    # - Repetitive content suggests incomplete understanding
    diversity = calculate_lexical_diversity(content)
    # Up to 20% additional reduction for high-diversity content
    base_uncertainty *= 1.0 - (0.2 * diversity)

    # Factor 3: Examples provided (concrete instances reduce uncertainty)
    examples = dimension_data.get("examples", 0)
    # Each example reduces uncertainty by 0.1, max 0.2 total
    base_uncertainty -= min(examples * 0.1, 0.2)

    # Factor 4: Contradictions (increase uncertainty significantly)
    # Contradictory information means understanding is incomplete or flawed
    if dimension_data.get("contradictions", False):
        base_uncertainty += 0.4

    # Factor 5: Explicit uncertainty indicators
    # Phrases like "not sure" indicate the responder lacks confidence
    if any(
        phrase in content.lower()
        for phrase in ["not sure", "maybe", "unclear", "don't know"]
    ):
        base_uncertainty += 0.2

    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, base_uncertainty))


def calculate_information_gain(
    before: dict[str, float], after: dict[str, float]
) -> float:
    """
    Calculate information gain from before to after state.

    Theoretical basis:
    - Shannon entropy measures uncertainty: H(X) = -Σ p(x) log₂ p(x)
    - Information gain = H(before) - H(after)
    - Treats uncertainty scores as probability distribution over knowledge states

    For simplicity, uses average uncertainty reduction as proxy for entropy reduction.
    Full entropy calculation would require probability distributions over all dimensions.

    References:
    - Cover & Thomas, "Elements of Information Theory", 2006
    - Mutual Information: I(X;Y) = H(X) - H(X|Y)

    Args:
        before: Uncertainty scores before questioning
        after: Uncertainty scores after questioning

    Returns:
        Information gain (positive = uncertainty reduced, in bits)

    Examples:
        >>> before = {"purpose": 1.0, "data": 1.0, "behavior": 1.0}
        >>> after = {"purpose": 0.3, "data": 0.8, "behavior": 0.9}
        >>> round(calculate_information_gain(before, after), 2)
        0.33
        >>> before2 = {"purpose": 0.3, "data": 0.3}
        >>> after2 = {"purpose": 0.2, "data": 0.2}
        >>> round(calculate_information_gain(before2, after2), 2)
        0.1
        >>> before3 = {"purpose": 0.5}
        >>> after3 = {"purpose": 0.5}
        >>> calculate_information_gain(before3, after3)
        0.0
    """
    # Calculate average uncertainty before and after
    avg_before = sum(before.values()) / len(before)
    avg_after = sum(after.values()) / len(after)

    # Information gain is reduction in average uncertainty
    # This is a simplified proxy for entropy reduction:
    # H(before) - H(after) ≈ avg_uncertainty(before) - avg_uncertainty(after)
    #
    # Full Shannon entropy calculation would be:
    # H_before = calculate_entropy([before[d]/sum(before.values()) for d in before])
    # H_after = calculate_entropy([after[d]/sum(after.values()) for d in after])
    # return H_before - H_after
    #
    # We use average difference for simplicity and interpretability
    return avg_before - avg_after


def should_continue_questioning(
    uncertainties: dict[str, float], threshold: float = 0.3
) -> bool:
    """
    Determine if more questions are needed based on uncertainty levels.

    Theoretical basis for threshold 0.3:
    - Represents 70% certainty requirement (1.0 - 0.7 = 0.3)
    - Derived from information theory: achieving 70% of maximum certainty
    - For 5 dimensions: max entropy = log₂(5) ≈ 2.32 bits
    - 70% certainty means 30% remaining uncertainty
    - Normalized: 0.3 * 2.32 / 2.32 = 0.3

    References:
    - Shannon entropy threshold for "sufficient information"
    - Requirements doc: docs/with-me-evaluation-logic-requirements.md

    Args:
        uncertainties: Current uncertainty score for each dimension
        threshold: Uncertainty threshold (default 0.3 = 70% certainty)

    Returns:
        True if any dimension exceeds threshold (more questions needed)

    Examples:
        >>> should_continue_questioning({"purpose": 0.2, "data": 0.1})
        False
        >>> should_continue_questioning({"purpose": 0.2, "data": 0.5})
        True
        >>> should_continue_questioning({"purpose": 0.3}, threshold=0.3)
        False
        >>> should_continue_questioning({"purpose": 0.31}, threshold=0.3)
        True
    """
    return any(u > threshold for u in uncertainties.values())


def identify_highest_uncertainty_dimension(uncertainties: dict[str, float]) -> str:
    """
    Identify the dimension with highest uncertainty (needs most attention).

    Args:
        uncertainties: Current uncertainty scores

    Returns:
        Name of dimension with highest uncertainty

    Examples:
        >>> identify_highest_uncertainty_dimension(
        ...     {"purpose": 0.2, "data": 0.8, "behavior": 0.5}
        ... )
        'data'
        >>> identify_highest_uncertainty_dimension({"purpose": 1.0, "data": 0.1})
        'purpose'
    """
    return max(uncertainties.items(), key=lambda x: x[1])[0]


def format_uncertainty_report(uncertainties: dict[str, float]) -> str:
    """
    Format uncertainty scores as human-readable report.

    Args:
        uncertainties: Current uncertainty scores

    Returns:
        Formatted string report

    Examples:
        >>> report = format_uncertainty_report({"purpose": 0.2, "data": 0.8})
        >>> "Purpose: 80% certain" in report
        True
        >>> "Data: 20% certain" in report
        True
    """
    lines = ["## Uncertainty Analysis\n"]

    for dimension, uncertainty in sorted(uncertainties.items()):
        certainty = (1.0 - uncertainty) * 100
        status = "✓" if uncertainty < 0.3 else "⚠" if uncertainty < 0.6 else "✗"
        lines.append(
            f"{status} {dimension.capitalize()}: {certainty:.0f}% certain (uncertainty: {uncertainty:.2f})"
        )

    avg_uncertainty = sum(uncertainties.values()) / len(uncertainties)
    overall_certainty = (1.0 - avg_uncertainty) * 100
    lines.append(f"\nOverall Certainty: {overall_certainty:.0f}%")

    if should_continue_questioning(uncertainties):
        highest = identify_highest_uncertainty_dimension(uncertainties)
        lines.append(f"\nRecommendation: Focus next questions on {highest} dimension")
    else:
        lines.append(
            "\nRecommendation: Sufficient clarity achieved, proceed to validation"
        )

    return "\n".join(lines)


def main():
    """
    CLI interface for uncertainty calculation.

    Usage:
        python uncertainty_calculator.py [--json-only] '<json_data>'

    Flags:
        --json-only    Output only JSON (for programmatic use)
    """
    # Parse arguments
    json_only = False
    args = sys.argv[1:]

    if "--json-only" in args:
        json_only = True
        args.remove("--json-only")

    if len(args) != 1:
        print("Usage: uncertainty_calculator.py [--json-only] '<json_data>'", file=sys.stderr)
        print("\nExample:", file=sys.stderr)
        print(
            '  python uncertainty_calculator.py \'{"purpose": {"answered": true, "content": "Build API"}}\'',
            file=sys.stderr,
        )
        print(
            '  python uncertainty_calculator.py --json-only \'{"purpose": {...}}\'',
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        dimension_data = json.loads(args[0])
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON - {e}", file=sys.stderr)
        sys.exit(1)

    # Calculate uncertainty for each dimension
    uncertainties = {
        dim: calculate_dimension_uncertainty(data)
        for dim, data in dimension_data.items()
    }

    # Generate result
    result = {
        "uncertainties": uncertainties,
        "continue_questioning": should_continue_questioning(uncertainties),
        "next_focus": identify_highest_uncertainty_dimension(uncertainties)
        if should_continue_questioning(uncertainties)
        else None,
    }

    if json_only:
        # JSON only mode (for programmatic use)
        print(json.dumps(result, indent=2))
    else:
        # Human-readable report + JSON
        report = format_uncertainty_report(uncertainties)
        print(report)
        print("\n" + json.dumps(result, indent=2))


if __name__ == "__main__":
    import doctest

    doctest.testmod()

    if len(sys.argv) > 1:
        main()
