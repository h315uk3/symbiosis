#!/usr/bin/env python3
"""
Presheaf consistency framework for cross-dimension belief coherence.

Models dimension relationships as a presheaf over the DAG:
each edge carries a restriction map (conditional distribution)
that predicts what the target dimension's posterior "should" look like
given the source dimension's beliefs.

Consistency is measured by JSD between actual and predicted target posteriors.
High JSD indicates the user's answers are contradictory across dimensions.

Related: #37 (Phase 2)
"""

import doctest
import math
import sys
from dataclasses import dataclass
from typing import Any

from with_me.lib.dimension_belief import HypothesisSet, compute_jsd


@dataclass(frozen=True)
class RestrictionMap:
    """A morphism in the presheaf: maps source beliefs to expected target beliefs.

    Models the conditional distribution P(target_hypothesis | source_hypothesis)
    for a single DAG edge. Given the source dimension's posterior, computes the
    expected target posterior via marginalization.

    Args:
        source_dim: Source dimension ID (e.g., "purpose")
        target_dim: Target dimension ID (e.g., "data")
        conditional: Mapping {source_hyp: {target_hyp: probability}}

    Examples:
        >>> rm = RestrictionMap(
        ...     source_dim="purpose",
        ...     target_dim="data",
        ...     conditional={
        ...         "web_app": {
        ...             "structured": 0.5,
        ...             "unstructured": 0.2,
        ...             "streaming": 0.3,
        ...         },
        ...         "cli_tool": {
        ...             "structured": 0.6,
        ...             "unstructured": 0.3,
        ...             "streaming": 0.1,
        ...         },
        ...     },
        ... )
        >>> rm.source_dim
        'purpose'
    """

    source_dim: str
    target_dim: str
    conditional: dict[str, dict[str, float]]

    def expected_target(self, source_posterior: dict[str, float]) -> dict[str, float]:
        """Compute expected target posterior given source beliefs.

        E[target_h] = sum_s source_p[s] * conditional[s][target_h]

        Args:
            source_posterior: Source dimension's posterior {hyp: probability}

        Returns:
            Expected target distribution {hyp: probability}

        Examples:
            >>> rm = RestrictionMap(
            ...     source_dim="purpose",
            ...     target_dim="data",
            ...     conditional={
            ...         "web_app": {
            ...             "structured": 0.5,
            ...             "unstructured": 0.2,
            ...             "streaming": 0.3,
            ...         },
            ...         "cli_tool": {
            ...             "structured": 0.6,
            ...             "unstructured": 0.3,
            ...             "streaming": 0.1,
            ...         },
            ...     },
            ... )
            >>> # Uniform source → weighted average of conditionals
            >>> result = rm.expected_target({"web_app": 0.5, "cli_tool": 0.5})
            >>> round(result["structured"], 2)
            0.55
            >>> round(result["streaming"], 2)
            0.2

            >>> # Certain source → conditional row
            >>> result = rm.expected_target({"web_app": 1.0, "cli_tool": 0.0})
            >>> result["structured"]
            0.5
        """
        # Collect all target hypothesis keys
        target_keys: set[str] = set()
        for dist in self.conditional.values():
            target_keys.update(dist.keys())

        expected: dict[str, float] = {k: 0.0 for k in target_keys}
        for source_hyp, source_prob in source_posterior.items():
            if source_hyp in self.conditional:
                for target_hyp, cond_prob in self.conditional[source_hyp].items():
                    expected[target_hyp] += source_prob * cond_prob

        return expected


@dataclass
class ConsistencyResult:
    """Result of a single edge consistency check.

    Args:
        source_dim: Source dimension ID
        target_dim: Target dimension ID
        jsd: Jensen-Shannon Divergence between actual and expected
        is_consistent: Whether JSD is below threshold

    Examples:
        >>> cr = ConsistencyResult("purpose", "data", 0.15, True)
        >>> cr.is_consistent
        True
    """

    source_dim: str
    target_dim: str
    jsd: float
    is_consistent: bool


class PresheafChecker:
    """Checks belief consistency across the dimension DAG.

    For each edge (restriction map), computes the JSD between:
    - The actual target posterior (from user answers)
    - The expected target posterior (predicted from source beliefs)

    High JSD indicates contradictory answers across dimensions.

    Args:
        restriction_maps: List of RestrictionMap defining the presheaf
        consistency_threshold: JSD threshold for flagging inconsistency

    Examples:
        >>> maps = [
        ...     RestrictionMap(
        ...         source_dim="purpose",
        ...         target_dim="data",
        ...         conditional={
        ...             "web_app": {
        ...                 "structured": 0.5,
        ...                 "unstructured": 0.2,
        ...                 "streaming": 0.3,
        ...             },
        ...             "cli_tool": {
        ...                 "structured": 0.6,
        ...                 "unstructured": 0.3,
        ...                 "streaming": 0.1,
        ...             },
        ...             "library": {
        ...                 "structured": 0.5,
        ...                 "unstructured": 0.3,
        ...                 "streaming": 0.2,
        ...             },
        ...             "service": {
        ...                 "structured": 0.3,
        ...                 "unstructured": 0.1,
        ...                 "streaming": 0.6,
        ...             },
        ...         },
        ...     ),
        ... ]
        >>> checker = PresheafChecker(maps, consistency_threshold=0.3)
        >>> beliefs = {
        ...     "purpose": HypothesisSet(
        ...         "purpose",
        ...         ["web_app", "cli_tool", "library", "service"],
        ...         alpha={
        ...             "web_app": 5.0,
        ...             "cli_tool": 1.0,
        ...             "library": 1.0,
        ...             "service": 1.0,
        ...         },
        ...     ),
        ...     "data": HypothesisSet(
        ...         "data",
        ...         ["structured", "unstructured", "streaming"],
        ...         alpha={"structured": 4.0, "unstructured": 2.0, "streaming": 1.0},
        ...     ),
        ... }
        >>> results = checker.check_consistency(beliefs)
        >>> len(results)
        1
        >>> results[0].source_dim
        'purpose'
    """

    def __init__(
        self,
        restriction_maps: list[RestrictionMap],
        consistency_threshold: float = 0.3,
    ):
        self.restriction_maps = restriction_maps
        self.consistency_threshold = consistency_threshold

    def check_consistency(
        self, beliefs: dict[str, HypothesisSet]
    ) -> list[ConsistencyResult]:
        """Check all edges for belief consistency.

        Args:
            beliefs: Current belief state {dim_id: HypothesisSet}

        Returns:
            List of ConsistencyResult for each edge

        Examples:
            >>> maps = [
            ...     RestrictionMap(
            ...         source_dim="purpose",
            ...         target_dim="data",
            ...         conditional={
            ...             "web_app": {
            ...                 "structured": 0.5,
            ...                 "unstructured": 0.2,
            ...                 "streaming": 0.3,
            ...             },
            ...             "cli_tool": {
            ...                 "structured": 0.6,
            ...                 "unstructured": 0.3,
            ...                 "streaming": 0.1,
            ...             },
            ...             "library": {
            ...                 "structured": 0.5,
            ...                 "unstructured": 0.3,
            ...                 "streaming": 0.2,
            ...             },
            ...             "service": {
            ...                 "structured": 0.3,
            ...                 "unstructured": 0.1,
            ...                 "streaming": 0.6,
            ...             },
            ...         },
            ...     ),
            ... ]
            >>> checker = PresheafChecker(maps, consistency_threshold=0.3)

            >>> # Consistent: web_app → mostly structured (matches expectation)
            >>> beliefs = {
            ...     "purpose": HypothesisSet(
            ...         "purpose",
            ...         ["web_app", "cli_tool", "library", "service"],
            ...         alpha={
            ...             "web_app": 5.0,
            ...             "cli_tool": 1.0,
            ...             "library": 1.0,
            ...             "service": 1.0,
            ...         },
            ...     ),
            ...     "data": HypothesisSet(
            ...         "data",
            ...         ["structured", "unstructured", "streaming"],
            ...         alpha={
            ...             "structured": 4.0,
            ...             "unstructured": 2.0,
            ...             "streaming": 1.0,
            ...         },
            ...     ),
            ... }
            >>> results = checker.check_consistency(beliefs)
            >>> results[0].is_consistent
            True

            >>> # Inconsistent: web_app dominant but streaming data near-certain
            >>> beliefs["data"] = HypothesisSet(
            ...     "data",
            ...     ["structured", "unstructured", "streaming"],
            ...     alpha={"structured": 0.1, "unstructured": 0.1, "streaming": 10.0},
            ... )
            >>> results = checker.check_consistency(beliefs)
            >>> results[0].is_consistent
            False
        """
        results: list[ConsistencyResult] = []

        for rm in self.restriction_maps:
            if rm.source_dim not in beliefs or rm.target_dim not in beliefs:
                continue

            source_posterior = beliefs[rm.source_dim].posterior
            actual_target = beliefs[rm.target_dim].posterior
            expected_target = rm.expected_target(source_posterior)

            jsd = compute_jsd(actual_target, expected_target)
            results.append(
                ConsistencyResult(
                    source_dim=rm.source_dim,
                    target_dim=rm.target_dim,
                    jsd=jsd,
                    is_consistent=jsd <= self.consistency_threshold,
                )
            )

        return results

    def get_inconsistencies(
        self, beliefs: dict[str, HypothesisSet]
    ) -> list[ConsistencyResult]:
        """Get only inconsistent edges (JSD above threshold).

        Args:
            beliefs: Current belief state

        Returns:
            List of inconsistent ConsistencyResult

        Examples:
            >>> maps = [
            ...     RestrictionMap(
            ...         source_dim="purpose",
            ...         target_dim="data",
            ...         conditional={
            ...             "web_app": {
            ...                 "structured": 0.5,
            ...                 "unstructured": 0.2,
            ...                 "streaming": 0.3,
            ...             },
            ...             "cli_tool": {
            ...                 "structured": 0.6,
            ...                 "unstructured": 0.3,
            ...                 "streaming": 0.1,
            ...             },
            ...             "library": {
            ...                 "structured": 0.5,
            ...                 "unstructured": 0.3,
            ...                 "streaming": 0.2,
            ...             },
            ...             "service": {
            ...                 "structured": 0.3,
            ...                 "unstructured": 0.1,
            ...                 "streaming": 0.6,
            ...             },
            ...         },
            ...     ),
            ... ]
            >>> checker = PresheafChecker(maps, consistency_threshold=0.3)
            >>> beliefs = {
            ...     "purpose": HypothesisSet(
            ...         "purpose",
            ...         ["web_app", "cli_tool", "library", "service"],
            ...         alpha={
            ...             "web_app": 5.0,
            ...             "cli_tool": 1.0,
            ...             "library": 1.0,
            ...             "service": 1.0,
            ...         },
            ...     ),
            ...     "data": HypothesisSet(
            ...         "data",
            ...         ["structured", "unstructured", "streaming"],
            ...         alpha={
            ...             "structured": 4.0,
            ...             "unstructured": 2.0,
            ...             "streaming": 1.0,
            ...         },
            ...     ),
            ... }
            >>> len(checker.get_inconsistencies(beliefs))
            0
        """
        return [r for r in self.check_consistency(beliefs) if not r.is_consistent]

    def suggest_secondary_dimensions(
        self,
        primary_dimension: str,
        beliefs: dict[str, HypothesisSet],
        top_k: int = 3,
    ) -> list[dict[str, str | float | list[str]]]:
        """Suggest secondary dimensions that would benefit from cross-dimension updates.

        For each restriction map where source_dim == primary_dimension,
        computes a score based on the target dimension's normalized entropy.
        Higher entropy targets benefit more from secondary updates.

        Args:
            primary_dimension: The dimension currently being queried
            beliefs: Current belief state {dim_id: HypothesisSet}
            top_k: Maximum number of suggestions to return

        Returns:
            Sorted list of suggestions, each containing:
            - dimension: target dimension ID
            - score: normalized entropy of target (proxy for update value)
            - hypotheses: list of hypothesis IDs for the target

        Examples:
            >>> from with_me.lib.dimension_belief import HypothesisSet
            >>> maps = [
            ...     RestrictionMap(
            ...         source_dim="purpose",
            ...         target_dim="data",
            ...         conditional={
            ...             "web_app": {
            ...                 "structured": 0.5,
            ...                 "unstructured": 0.2,
            ...                 "streaming": 0.3,
            ...             },
            ...             "cli_tool": {
            ...                 "structured": 0.6,
            ...                 "unstructured": 0.3,
            ...                 "streaming": 0.1,
            ...             },
            ...         },
            ...     ),
            ...     RestrictionMap(
            ...         source_dim="purpose",
            ...         target_dim="behavior",
            ...         conditional={
            ...             "web_app": {
            ...                 "synchronous": 0.3,
            ...                 "asynchronous": 0.4,
            ...                 "interactive": 0.2,
            ...                 "batch": 0.1,
            ...             },
            ...             "cli_tool": {
            ...                 "synchronous": 0.5,
            ...                 "asynchronous": 0.1,
            ...                 "interactive": 0.3,
            ...                 "batch": 0.1,
            ...             },
            ...         },
            ...     ),
            ... ]
            >>> checker = PresheafChecker(maps, consistency_threshold=0.3)
            >>> beliefs = {
            ...     "purpose": HypothesisSet(
            ...         "purpose",
            ...         ["web_app", "cli_tool"],
            ...         alpha={"web_app": 5.0, "cli_tool": 1.0},
            ...     ),
            ...     "data": HypothesisSet(
            ...         "data",
            ...         ["structured", "unstructured", "streaming"],
            ...     ),
            ...     "behavior": HypothesisSet(
            ...         "behavior",
            ...         ["synchronous", "asynchronous", "interactive", "batch"],
            ...     ),
            ... }
            >>> suggestions = checker.suggest_secondary_dimensions("purpose", beliefs)
            >>> len(suggestions) == 2
            True
            >>> suggestions[0]["dimension"] in ("data", "behavior")
            True

            >>> # Non-existent primary → empty
            >>> checker.suggest_secondary_dimensions("nonexistent", beliefs)
            []
        """
        candidates: list[dict[str, str | float | list[str]]] = []

        for rm in self.restriction_maps:
            if rm.source_dim != primary_dimension:
                continue
            if rm.target_dim not in beliefs:
                continue

            target_hs = beliefs[rm.target_dim]
            h_max = math.log2(len(target_hs.hypotheses))
            if h_max <= 0:
                continue

            raw_entropy = target_hs.entropy()
            normalized_entropy = raw_entropy / h_max

            candidates.append(
                {
                    "dimension": rm.target_dim,
                    "score": round(normalized_entropy, 4),
                    "hypotheses": list(target_hs.hypotheses),
                }
            )

        # Sort by score descending
        candidates.sort(
            key=lambda c: c["score"] if isinstance(c["score"], float) else 0.0,
            reverse=True,
        )
        return candidates[:top_k]

    def get_coupling_strength(
        self,
        beliefs: dict[str, HypothesisSet],
        source: str,
        target: str,
    ) -> float:
        """Get JSD for a specific edge.

        Args:
            beliefs: Current belief state
            source: Source dimension ID
            target: Target dimension ID

        Returns:
            JSD value, or 0.0 if edge not found

        Examples:
            >>> maps = [
            ...     RestrictionMap(
            ...         source_dim="purpose",
            ...         target_dim="data",
            ...         conditional={
            ...             "web_app": {
            ...                 "structured": 0.5,
            ...                 "unstructured": 0.2,
            ...                 "streaming": 0.3,
            ...             },
            ...             "cli_tool": {
            ...                 "structured": 0.6,
            ...                 "unstructured": 0.3,
            ...                 "streaming": 0.1,
            ...             },
            ...             "library": {
            ...                 "structured": 0.5,
            ...                 "unstructured": 0.3,
            ...                 "streaming": 0.2,
            ...             },
            ...             "service": {
            ...                 "structured": 0.3,
            ...                 "unstructured": 0.1,
            ...                 "streaming": 0.6,
            ...             },
            ...         },
            ...     ),
            ... ]
            >>> checker = PresheafChecker(maps, consistency_threshold=0.3)
            >>> beliefs = {
            ...     "purpose": HypothesisSet(
            ...         "purpose",
            ...         ["web_app", "cli_tool", "library", "service"],
            ...         alpha={
            ...             "web_app": 5.0,
            ...             "cli_tool": 1.0,
            ...             "library": 1.0,
            ...             "service": 1.0,
            ...         },
            ...     ),
            ...     "data": HypothesisSet(
            ...         "data",
            ...         ["structured", "unstructured", "streaming"],
            ...         alpha={
            ...             "structured": 4.0,
            ...             "unstructured": 2.0,
            ...             "streaming": 1.0,
            ...         },
            ...     ),
            ... }
            >>> jsd = checker.get_coupling_strength(beliefs, "purpose", "data")
            >>> 0.0 <= jsd <= 1.0
            True

            >>> # Non-existent edge
            >>> checker.get_coupling_strength(beliefs, "data", "purpose")
            0.0
        """
        for result in self.check_consistency(beliefs):
            if result.source_dim == source and result.target_dim == target:
                return result.jsd
        return 0.0


def load_restriction_maps(config: dict[str, Any]) -> list[RestrictionMap]:
    """Parse restriction maps from dimensions.json config.

    Args:
        config: Parsed dimensions.json content

    Returns:
        List of RestrictionMap instances

    Examples:
        >>> config = {
        ...     "restriction_maps": {
        ...         "purpose->data": {
        ...             "web_app": {
        ...                 "structured": 0.5,
        ...                 "unstructured": 0.2,
        ...                 "streaming": 0.3,
        ...             },
        ...             "cli_tool": {
        ...                 "structured": 0.6,
        ...                 "unstructured": 0.3,
        ...                 "streaming": 0.1,
        ...             },
        ...         }
        ...     }
        ... }
        >>> maps = load_restriction_maps(config)
        >>> len(maps)
        1
        >>> maps[0].source_dim
        'purpose'
        >>> maps[0].target_dim
        'data'

        >>> # Empty config → empty list
        >>> load_restriction_maps({})
        []
    """
    expected_parts = 2  # "source->target" splits into exactly 2 parts
    maps: list[RestrictionMap] = []
    raw = config.get("restriction_maps", {})

    for edge_key, conditional in raw.items():
        parts = edge_key.split("->")
        if len(parts) != expected_parts:
            continue
        source, target = parts[0].strip(), parts[1].strip()
        maps.append(
            RestrictionMap(
                source_dim=source,
                target_dim=target,
                conditional=conditional,
            )
        )

    return maps


# CLI interface
def main():
    """Command-line usage."""
    min_argc = 2
    if len(sys.argv) < min_argc:
        print("Usage: python presheaf.py <command>")
        print("\nCommands:")
        print("  test     - Run doctests")
        sys.exit(1)

    if sys.argv[1] == "test":
        print("Running doctests...")
        result = doctest.testmod()
        if result.failed == 0:
            print("✓ All doctests passed")
        else:
            print(f"✗ {result.failed} doctest(s) failed")
            sys.exit(1)
    else:
        print(f"Unknown command: {sys.argv[1]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
