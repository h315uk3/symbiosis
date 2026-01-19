#!/usr/bin/env python3
"""
Dimension Selector for with-me plugin

Implements the DAG-based dimension selection algorithm for systematic requirement elicitation.
Enforces prerequisite relationships to ensure logical questioning order.

DAG Structure:
    Purpose (no prerequisites)
    ├── Data (requires: Purpose < 0.4)
    ├── Behavior (requires: Purpose < 0.4)
        ├── Constraints (requires: Behavior < 0.4 AND Data < 0.4)
        └── Quality (requires: Behavior < 0.4)
"""

import json
import sys
from typing import Dict


class DimensionSelector:
    """
    Selects next dimension to question based on DAG dependencies and uncertainty scores.

    The selector enforces prerequisite relationships between dimensions to prevent
    premature or illogical questions.
    """

    # Prerequisite mapping: dimension -> list of required dimensions
    PREREQUISITES: Dict[str, list[str]] = {
        "purpose": [],  # Foundation - no prerequisites
        "data": ["purpose"],  # Requires understanding the problem first
        "behavior": ["purpose"],  # Requires understanding the goal first
        "constraints": ["behavior", "data"],  # Requires both behavior and data
        "quality": ["behavior"],  # Requires understanding behavior first
    }

    def __init__(self, prerequisite_threshold: float = 0.4):
        """
        Initialize dimension selector

        Args:
            prerequisite_threshold: Uncertainty threshold for prerequisite clearance
                                   (default 0.4 = 60% certain)

        Examples:
            >>> selector = DimensionSelector()
            >>> selector.prerequisite_threshold
            0.4
        """
        self.prerequisite_threshold = prerequisite_threshold

    def can_ask_dimension(self, dimension: str, uncertainties: Dict[str, float]) -> bool:
        """
        Check if a dimension can be questioned based on prerequisites

        A dimension can be asked if all its prerequisites have uncertainty below the threshold.

        Args:
            dimension: Dimension to check
            uncertainties: Current uncertainty scores for all dimensions

        Returns:
            True if dimension is askable (prerequisites satisfied)

        Examples:
            >>> selector = DimensionSelector()
            >>> # Purpose has no prerequisites, always askable
            >>> selector.can_ask_dimension("purpose", {"purpose": 0.8})
            True
            >>> # Data requires purpose < 0.4
            >>> selector.can_ask_dimension("data", {"purpose": 0.3, "data": 0.8})
            True
            >>> selector.can_ask_dimension("data", {"purpose": 0.5, "data": 0.8})
            False
            >>> # Constraints requires both behavior AND data < 0.4
            >>> selector.can_ask_dimension(
            ...     "constraints",
            ...     {"purpose": 0.2, "data": 0.3, "behavior": 0.3, "constraints": 0.8},
            ... )
            True
            >>> selector.can_ask_dimension(
            ...     "constraints",
            ...     {"purpose": 0.2, "data": 0.5, "behavior": 0.3, "constraints": 0.8},
            ... )
            False
        """
        if dimension not in self.PREREQUISITES:
            # Unknown dimension, be conservative and allow
            return True

        prerequisites = self.PREREQUISITES[dimension]

        # Check each prerequisite
        for prereq in prerequisites:
            prereq_uncertainty = uncertainties.get(prereq, 1.0)
            if prereq_uncertainty > self.prerequisite_threshold:
                # Prerequisite not sufficiently clear
                return False

        return True

    def select_next_dimension(
        self, uncertainties: Dict[str, float]
    ) -> tuple[str, str | None]:
        """
        Select the next dimension to question based on DAG order and uncertainty

        Algorithm:
        1. Filter dimensions by prerequisites (only askable dimensions)
        2. Select dimension with highest uncertainty among askable
        3. If no dimensions pass prerequisites, fallback to "purpose" (foundation)

        Args:
            uncertainties: Current uncertainty scores for all dimensions

        Returns:
            Tuple of (selected_dimension, reason or None)
            - selected_dimension: The dimension to question next
            - reason: Optional explanation if dimension was blocked or forced

        Examples:
            >>> selector = DimensionSelector()
            >>> # All uncertainties high, purpose not clear -> select purpose
            >>> dim, reason = selector.select_next_dimension(
            ...     {"purpose": 0.9, "data": 0.8, "behavior": 0.7, "constraints": 0.6, "quality": 0.5}
            ... )
            >>> dim
            'purpose'
            >>> # Purpose clear, data has highest uncertainty -> select data
            >>> dim, reason = selector.select_next_dimension(
            ...     {"purpose": 0.2, "data": 0.8, "behavior": 0.7, "constraints": 0.6, "quality": 0.5}
            ... )
            >>> dim
            'data'
            >>> # Purpose and data clear, behavior has highest uncertainty -> select behavior
            >>> dim, reason = selector.select_next_dimension(
            ...     {"purpose": 0.2, "data": 0.3, "behavior": 0.7, "constraints": 0.6, "quality": 0.5}
            ... )
            >>> dim
            'behavior'
            >>> # All low-level dimensions ready, constraints has highest uncertainty
            >>> dim, reason = selector.select_next_dimension(
            ...     {"purpose": 0.2, "data": 0.3, "behavior": 0.3, "constraints": 0.6, "quality": 0.5}
            ... )
            >>> dim
            'constraints'
        """
        # Filter dimensions by prerequisites
        askable_dims = {
            dim: unc
            for dim, unc in uncertainties.items()
            if self.can_ask_dimension(dim, uncertainties)
        }

        if not askable_dims:
            # No dimensions pass prerequisites, force purpose (foundation)
            return (
                "purpose",
                "No dimensions satisfy prerequisites, focusing on foundation",
            )

        # Select highest uncertainty among askable dimensions
        next_dim = max(askable_dims, key=askable_dims.get)

        # Check if any dimensions were blocked
        blocked_dims = set(uncertainties.keys()) - set(askable_dims.keys())
        if blocked_dims and uncertainties.get(next_dim, 0) < max(
            uncertainties.get(d, 0) for d in blocked_dims
        ):
            # Selected dimension has lower uncertainty than blocked ones
            highest_blocked = max(
                blocked_dims, key=lambda d: uncertainties.get(d, 0)
            )
            prereqs = self.PREREQUISITES.get(highest_blocked, [])
            return (
                next_dim,
                f"Dimension '{highest_blocked}' has higher uncertainty but blocked by prerequisites: {prereqs}",
            )

        return (next_dim, None)

    def get_blocked_dimensions(
        self, uncertainties: Dict[str, float]
    ) -> Dict[str, list[str]]:
        """
        Identify dimensions that cannot be asked due to unmet prerequisites

        Args:
            uncertainties: Current uncertainty scores for all dimensions

        Returns:
            Dictionary mapping blocked dimensions to their unmet prerequisites

        Examples:
            >>> selector = DimensionSelector()
            >>> # Purpose unclear blocks data and behavior
            >>> blocked = selector.get_blocked_dimensions(
            ...     {"purpose": 0.8, "data": 0.5, "behavior": 0.6, "constraints": 0.4, "quality": 0.3}
            ... )
            >>> "data" in blocked
            True
            >>> "purpose" in blocked["data"]
            True
            >>> # Behavior unclear blocks constraints and quality
            >>> blocked = selector.get_blocked_dimensions(
            ...     {"purpose": 0.2, "data": 0.2, "behavior": 0.8, "constraints": 0.5, "quality": 0.6}
            ... )
            >>> "constraints" in blocked
            True
            >>> "behavior" in blocked["constraints"]
            True
        """
        blocked = {}

        for dim, unc in uncertainties.items():
            if not self.can_ask_dimension(dim, uncertainties):
                # Identify which prerequisites are unmet
                unmet_prereqs = [
                    prereq
                    for prereq in self.PREREQUISITES.get(dim, [])
                    if uncertainties.get(prereq, 1.0) > self.prerequisite_threshold
                ]
                blocked[dim] = unmet_prereqs

        return blocked

    def validate_prerequisite_order(self, dimension_order: list[str]) -> tuple[bool, str]:
        """
        Validate if a sequence of dimensions respects DAG order

        Useful for testing or validating interview logs.

        Args:
            dimension_order: Ordered list of dimensions as they were questioned

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if order respects all prerequisites
            - error_message: Empty if valid, explanation if invalid

        Examples:
            >>> selector = DimensionSelector()
            >>> # Valid order: purpose -> data -> behavior -> constraints
            >>> valid, msg = selector.validate_prerequisite_order(
            ...     ["purpose", "data", "behavior", "constraints"]
            ... )
            >>> valid
            True
            >>> # Invalid: data before purpose
            >>> valid, msg = selector.validate_prerequisite_order(
            ...     ["data", "purpose", "behavior"]
            ... )
            >>> valid
            False
            >>> "purpose" in msg
            True
            >>> # Invalid: constraints before behavior
            >>> valid, msg = selector.validate_prerequisite_order(
            ...     ["purpose", "data", "constraints", "behavior"]
            ... )
            >>> valid
            False
        """
        seen_dimensions = set()

        for i, dim in enumerate(dimension_order):
            if dim not in self.PREREQUISITES:
                # Unknown dimension, skip validation
                continue

            prerequisites = self.PREREQUISITES[dim]

            # Check if all prerequisites have been seen before this dimension
            unmet = [prereq for prereq in prerequisites if prereq not in seen_dimensions]

            if unmet:
                return (
                    False,
                    f"Dimension '{dim}' at position {i} requires {unmet} to be addressed first",
                )

            seen_dimensions.add(dim)

        return (True, "")


# CLI interface for testing
def main():
    """Command-line usage example"""
    if len(sys.argv) < 2:
        print("Usage: dimension_selector.py <uncertainties_json>")
        print("\nExample:")
        print(
            '  python dimension_selector.py \'{"purpose": 0.8, "data": 0.5, "behavior": 0.6}\''
        )
        sys.exit(1)

    try:
        uncertainties = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON - {e}", file=sys.stderr)
        sys.exit(1)

    selector = DimensionSelector()

    # Select next dimension
    next_dim, reason = selector.select_next_dimension(uncertainties)

    # Get blocked dimensions
    blocked = selector.get_blocked_dimensions(uncertainties)

    result = {
        "next_dimension": next_dim,
        "reason": reason,
        "blocked_dimensions": blocked,
        "prerequisite_threshold": selector.prerequisite_threshold,
    }

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
