#!/usr/bin/env python3
"""
Uncertainty Calculator for Good Question Command

Calculates uncertainty scores and information gain for requirement dimensions
using information theory principles. Pure Python standard library implementation.
"""

import json
import math
import sys
from typing import Dict, List, Any


def calculate_entropy(probabilities: List[float]) -> float:
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


def calculate_dimension_uncertainty(dimension_data: Dict[str, Any]) -> float:
    """
    Calculate uncertainty score for a single dimension (0.0-1.0).

    Higher score = more uncertain (needs more questions)
    Lower score = more certain (well understood)

    Scoring factors:
    - Has answer: reduces uncertainty
    - Answer detail length: more details = less uncertainty
    - Contradictions present: increases uncertainty
    - Examples provided: reduces uncertainty

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
        >>> calculate_dimension_uncertainty({"answered": True, "content": "short"})
        0.7
        >>> data = {"answered": True, "content": "detailed explanation with specifics", "examples": 2}
        >>> calculate_dimension_uncertainty(data) < 0.6
        True
        >>> data_with_contradiction = {"answered": True, "content": "some info", "contradictions": True}
        >>> calculate_dimension_uncertainty(data_with_contradiction) > 0.8
        True
    """
    if not dimension_data.get("answered", False):
        return 1.0

    # Start with base uncertainty
    uncertainty = 0.7

    # Factor 1: Content detail (more words = less uncertainty)
    content = dimension_data.get("content", "")
    word_count = len(content.split())
    if word_count > 50:
        uncertainty -= 0.5
    elif word_count > 20:
        uncertainty -= 0.4
    elif word_count > 5:
        uncertainty -= 0.2

    # Factor 2: Examples provided (reduces uncertainty)
    examples = dimension_data.get("examples", 0)
    uncertainty -= min(examples * 0.1, 0.2)

    # Factor 3: Contradictions (increases uncertainty)
    if dimension_data.get("contradictions", False):
        uncertainty += 0.4

    # Factor 4: Explicit "not sure" indicators
    if any(
        phrase in content.lower()
        for phrase in ["not sure", "maybe", "unclear", "don't know"]
    ):
        uncertainty += 0.2

    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, uncertainty))


def calculate_information_gain(
    before: Dict[str, float], after: Dict[str, float]
) -> float:
    """
    Calculate information gain from before to after state.

    Uses average uncertainty reduction to measure information gained.

    Args:
        before: Uncertainty scores before questioning
        after: Uncertainty scores after questioning

    Returns:
        Information gain (positive = uncertainty reduced)

    Examples:
        >>> before = {"purpose": 1.0, "data": 1.0, "behavior": 1.0}
        >>> after = {"purpose": 0.3, "data": 0.8, "behavior": 0.9}
        >>> round(calculate_information_gain(before, after), 2)
        0.33
        >>> before2 = {"purpose": 0.3, "data": 0.3}
        >>> after2 = {"purpose": 0.2, "data": 0.2}
        >>> round(calculate_information_gain(before2, after2), 2)
        0.1
    """
    # Calculate average uncertainty before and after
    avg_before = sum(before.values()) / len(before)
    avg_after = sum(after.values()) / len(after)

    # Information gain is reduction in average uncertainty
    return avg_before - avg_after


def should_continue_questioning(
    uncertainties: Dict[str, float], threshold: float = 0.3
) -> bool:
    """
    Determine if more questions are needed based on uncertainty levels.

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


def identify_highest_uncertainty_dimension(uncertainties: Dict[str, float]) -> str:
    """
    Identify the dimension with highest uncertainty (needs most attention).

    Args:
        uncertainties: Current uncertainty scores

    Returns:
        Name of dimension with highest uncertainty

    Examples:
        >>> identify_highest_uncertainty_dimension({"purpose": 0.2, "data": 0.8, "behavior": 0.5})
        'data'
        >>> identify_highest_uncertainty_dimension({"purpose": 1.0, "data": 0.1})
        'purpose'
    """
    return max(uncertainties.items(), key=lambda x: x[1])[0]


def format_uncertainty_report(uncertainties: Dict[str, float]) -> str:
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
        python uncertainty_calculator.py '{"purpose": {"answered": true, "content": "..."}}'
    """
    if len(sys.argv) != 2:
        print("Usage: uncertainty_calculator.py '<json_data>'", file=sys.stderr)
        print("\nExample:", file=sys.stderr)
        print(
            '  python uncertainty_calculator.py \'{"purpose": {"answered": true, "content": "Build API"}}\'',
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        dimension_data = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON - {e}", file=sys.stderr)
        sys.exit(1)

    # Calculate uncertainty for each dimension
    uncertainties = {
        dim: calculate_dimension_uncertainty(data)
        for dim, data in dimension_data.items()
    }

    # Generate report
    report = format_uncertainty_report(uncertainties)
    print(report)

    # Output JSON for programmatic use
    result = {
        "uncertainties": uncertainties,
        "continue_questioning": should_continue_questioning(uncertainties),
        "next_focus": identify_highest_uncertainty_dimension(uncertainties)
        if should_continue_questioning(uncertainties)
        else None,
    }
    print("\n" + json.dumps(result, indent=2))


if __name__ == "__main__":
    import doctest

    doctest.testmod()

    if len(sys.argv) > 1:
        main()
