#!/usr/bin/env python3
"""
Knowledge Space Theory (KST) for dimension navigation.

Provides feasible state enumeration and fringe computation for
prerequisite-based dimension accessibility. Replaces binary
prerequisite checks with a lattice of valid knowledge states.

References:
    Doignon, J.-P. & Falmagne, J.-C. (1999). Knowledge Spaces.
"""

import doctest
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from with_me.lib.dimension_belief import HypothesisSet


class KnowledgeSpace:
    """Manages feasible knowledge states and fringe computation.

    A knowledge state is a frozenset of "mastered" dimension IDs.
    A state is feasible iff for every item in the state, all its
    prerequisites are also in the state.

    The outer fringe of a state contains items that can be learned next
    (all prerequisites satisfied). The inner fringe contains items
    whose removal still yields a feasible state (no dependent items
    rely on them).

    Examples:
        >>> ks = KnowledgeSpace(
        ...     items=["a", "b", "c"],
        ...     prerequisites={"a": [], "b": ["a"], "c": ["a", "b"]},
        ... )
        >>> frozenset() in ks.feasible_states
        True
        >>> frozenset({"a", "b", "c"}) in ks.feasible_states
        True
        >>> frozenset({"c"}) in ks.feasible_states  # c requires a and b
        False
        >>> frozenset({"b"}) in ks.feasible_states  # b requires a
        False
    """

    def __init__(
        self, items: list[str], prerequisites: dict[str, list[str]]
    ) -> None:
        """Initialize knowledge space from items and prerequisite map.

        Args:
            items: List of dimension IDs
            prerequisites: Mapping from dimension ID to list of prerequisite IDs

        Examples:
            >>> ks = KnowledgeSpace(
            ...     items=["p", "d", "b"],
            ...     prerequisites={"p": [], "d": ["p"], "b": ["p"]},
            ... )
            >>> len(ks.items)
            3
            >>> len(ks.feasible_states) > 0
            True
        """
        self.items = items
        self.prerequisites = prerequisites
        self.feasible_states = self._enumerate_feasible_states(
            items, prerequisites
        )

    @staticmethod
    def _enumerate_feasible_states(
        items: list[str], prerequisites: dict[str, list[str]]
    ) -> frozenset[frozenset[str]]:
        """Enumerate all feasible knowledge states.

        A state is feasible iff every item in the state has all its
        prerequisites also in the state. Iterates over all 2^n subsets.

        Args:
            items: List of dimension IDs
            prerequisites: Mapping from dimension ID to prerequisite IDs

        Returns:
            Frozenset of all feasible states

        Examples:
            >>> # Linear chain: a -> b -> c
            >>> states = KnowledgeSpace._enumerate_feasible_states(
            ...     ["a", "b", "c"],
            ...     {"a": [], "b": ["a"], "c": ["a", "b"]},
            ... )
            >>> sorted([sorted(s) for s in states])
            [[], ['a'], ['a', 'b'], ['a', 'b', 'c']]

            >>> # Diamond: a -> b, a -> c, b+c -> d
            >>> states = KnowledgeSpace._enumerate_feasible_states(
            ...     ["a", "b", "c", "d"],
            ...     {"a": [], "b": ["a"], "c": ["a"], "d": ["b", "c"]},
            ... )
            >>> len(states)
            6
            >>> frozenset({"a", "d"}) in states  # d needs b and c
            False
            >>> frozenset({"a", "b", "c", "d"}) in states
            True

            >>> # No prerequisites: all 2^n states are feasible
            >>> states = KnowledgeSpace._enumerate_feasible_states(
            ...     ["x", "y"], {"x": [], "y": []},
            ... )
            >>> len(states)
            4
        """
        n = len(items)
        feasible: list[frozenset[str]] = []

        for mask in range(1 << n):
            state = frozenset(items[i] for i in range(n) if mask & (1 << i))
            is_feasible = True
            for item in state:
                for prereq in prerequisites.get(item, []):
                    if prereq not in state:
                        is_feasible = False
                        break
                if not is_feasible:
                    break
            if is_feasible:
                feasible.append(state)

        return frozenset(feasible)

    def outer_fringe(self, state: frozenset[str]) -> frozenset[str]:
        """Items that can be added next (all prerequisites in state).

        The outer fringe represents explorable dimensions — those whose
        prerequisites are fully satisfied by the current state.

        Args:
            state: Current knowledge state (set of mastered dimension IDs)

        Returns:
            Frozenset of dimension IDs that can be explored next

        Examples:
            >>> ks = KnowledgeSpace(
            ...     items=["a", "b", "c"],
            ...     prerequisites={"a": [], "b": ["a"], "c": ["a", "b"]},
            ... )
            >>> sorted(ks.outer_fringe(frozenset()))
            ['a']
            >>> sorted(ks.outer_fringe(frozenset({"a"})))
            ['b']
            >>> sorted(ks.outer_fringe(frozenset({"a", "b"})))
            ['c']
            >>> ks.outer_fringe(frozenset({"a", "b", "c"}))
            frozenset()

            >>> # Two roots: both accessible from empty state
            >>> ks2 = KnowledgeSpace(
            ...     items=["p", "c", "d"],
            ...     prerequisites={"p": [], "c": [], "d": ["p"]},
            ... )
            >>> sorted(ks2.outer_fringe(frozenset()))
            ['c', 'p']
            >>> sorted(ks2.outer_fringe(frozenset({"p"})))
            ['c', 'd']
        """
        fringe: list[str] = []
        for item in self.items:
            if item in state:
                continue
            prereqs = self.prerequisites.get(item, [])
            if all(p in state for p in prereqs):
                fringe.append(item)
        return frozenset(fringe)

    def inner_fringe(self, state: frozenset[str]) -> frozenset[str]:
        """Items whose removal still yields a feasible state.

        An item is in the inner fringe if no other item in the state
        depends on it as a prerequisite.

        Args:
            state: Current knowledge state

        Returns:
            Frozenset of removable dimension IDs

        Examples:
            >>> ks = KnowledgeSpace(
            ...     items=["a", "b", "c"],
            ...     prerequisites={"a": [], "b": ["a"], "c": ["a", "b"]},
            ... )
            >>> ks.inner_fringe(frozenset())
            frozenset()
            >>> sorted(ks.inner_fringe(frozenset({"a"})))
            ['a']
            >>> sorted(ks.inner_fringe(frozenset({"a", "b"})))
            ['b']
            >>> sorted(ks.inner_fringe(frozenset({"a", "b", "c"})))
            ['c']

            >>> # Diamond: d depends on b and c
            >>> ks2 = KnowledgeSpace(
            ...     items=["a", "b", "c", "d"],
            ...     prerequisites={"a": [], "b": ["a"], "c": ["a"], "d": ["b", "c"]},
            ... )
            >>> sorted(ks2.inner_fringe(frozenset({"a", "b", "c"})))
            ['b', 'c']
            >>> sorted(ks2.inner_fringe(frozenset({"a", "b", "c", "d"})))
            ['d']
        """
        fringe: list[str] = []
        for item in state:
            # Check if any other item in state depends on this item
            removable = True
            for other in state:
                if other == item:
                    continue
                if item in self.prerequisites.get(other, []):
                    removable = False
                    break
            if removable:
                fringe.append(item)
        return frozenset(fringe)

    def current_state_from_beliefs(
        self,
        beliefs: dict[str, "HypothesisSet"],
        threshold: float,
    ) -> frozenset[str]:
        """Derive current knowledge state from belief entropies.

        Starts with dimensions whose entropy is below the threshold,
        then clamps to a feasible state by iteratively removing items
        whose prerequisites are not satisfied.

        Args:
            beliefs: Mapping from dimension ID to HypothesisSet
            threshold: Entropy threshold below which a dimension is "resolved"

        Returns:
            Feasible knowledge state (frozenset of resolved dimension IDs)

        Examples:
            >>> from with_me.lib.dimension_belief import HypothesisSet
            >>> beliefs = {
            ...     "a": HypothesisSet("a", ["x", "y"]),
            ...     "b": HypothesisSet("b", ["x", "y"]),
            ...     "c": HypothesisSet("c", ["x", "y"]),
            ... }
            >>> ks = KnowledgeSpace(
            ...     items=["a", "b", "c"],
            ...     prerequisites={"a": [], "b": ["a"], "c": ["a", "b"]},
            ... )

            >>> # No resolved dimensions → empty state
            >>> ks.current_state_from_beliefs(beliefs, threshold=1.5)
            frozenset()

            >>> # a resolved → {a}
            >>> beliefs["a"]._cached_entropy = 0.5
            >>> sorted(ks.current_state_from_beliefs(beliefs, threshold=1.5))
            ['a']

            >>> # a and b resolved → {a, b}
            >>> beliefs["b"]._cached_entropy = 0.3
            >>> sorted(ks.current_state_from_beliefs(beliefs, threshold=1.5))
            ['a', 'b']

            >>> # b and c resolved but NOT a → empty (prerequisite violated)
            >>> beliefs2 = {
            ...     "a": HypothesisSet("a", ["x", "y"]),
            ...     "b": HypothesisSet("b", ["x", "y"]),
            ...     "c": HypothesisSet("c", ["x", "y"]),
            ... }
            >>> beliefs2["b"]._cached_entropy = 0.3
            >>> beliefs2["c"]._cached_entropy = 0.2
            >>> ks.current_state_from_beliefs(beliefs2, threshold=1.5)
            frozenset()
        """
        # Raw resolved set: dimensions with entropy below threshold
        raw_resolved: set[str] = set()
        for dim_id in self.items:
            if dim_id not in beliefs:
                continue
            entropy = beliefs[dim_id]._cached_entropy
            if entropy is not None and entropy < threshold:
                raw_resolved.add(dim_id)

        # Clamp to feasible: iteratively remove items with unsatisfied prereqs
        changed = True
        while changed:
            changed = False
            to_remove: list[str] = []
            for item in raw_resolved:
                for prereq in self.prerequisites.get(item, []):
                    if prereq not in raw_resolved:
                        to_remove.append(item)
                        break
            for item in to_remove:
                raw_resolved.discard(item)
                changed = True

        return frozenset(raw_resolved)

    def is_feasible(self, state: frozenset[str]) -> bool:
        """Check if a state is in the knowledge space.

        Args:
            state: State to check

        Returns:
            True if the state is feasible

        Examples:
            >>> ks = KnowledgeSpace(
            ...     items=["a", "b", "c"],
            ...     prerequisites={"a": [], "b": ["a"], "c": ["a", "b"]},
            ... )
            >>> ks.is_feasible(frozenset())
            True
            >>> ks.is_feasible(frozenset({"a", "b"}))
            True
            >>> ks.is_feasible(frozenset({"b"}))
            False
            >>> ks.is_feasible(frozenset({"a", "c"}))  # c needs b
            False
        """
        return state in self.feasible_states

    def adjacent_dimensions(
        self,
        state: frozenset[str],
        dag_edges: list[tuple[str, str]],
    ) -> dict[str, set[str]]:
        """Map outer fringe dimensions to connected inner fringe dimensions.

        For each dimension in the outer fringe, find which inner fringe
        dimensions are connected via DAG edges (in either direction).
        Used for context bonus calculation.

        Args:
            state: Current knowledge state
            dag_edges: List of (from, to) DAG edge tuples

        Returns:
            Mapping from outer fringe dim to set of connected inner fringe dims

        Examples:
            >>> ks = KnowledgeSpace(
            ...     items=["p", "c", "d", "b", "s"],
            ...     prerequisites={
            ...         "p": [], "c": [], "d": ["p"],
            ...         "b": ["p"], "s": ["p"],
            ...     },
            ... )
            >>> edges = [("p", "d"), ("p", "b"), ("p", "s"), ("c", "d")]

            >>> # Empty state: outer={p,c}, inner=empty → no adjacency
            >>> adj = ks.adjacent_dimensions(frozenset(), edges)
            >>> all(len(v) == 0 for v in adj.values())
            True

            >>> # State={p}: inner={p}, outer={c,d,b,s}
            >>> adj = ks.adjacent_dimensions(frozenset({"p"}), edges)
            >>> sorted(adj["d"])  # d connected to p via edge
            ['p']
            >>> sorted(adj["b"])  # b connected to p via edge
            ['p']
            >>> sorted(adj["s"])  # s connected to p via edge
            ['p']

            >>> # State={p,c}: inner={p,c}, outer={d,b,s}
            >>> adj = ks.adjacent_dimensions(frozenset({"p", "c"}), edges)
            >>> sorted(adj["d"])  # d connected to p and c
            ['c', 'p']
        """
        outer = self.outer_fringe(state)
        inner = self.inner_fringe(state)

        # Build edge lookup (both directions)
        edge_set: set[tuple[str, str]] = set()
        for src, dst in dag_edges:
            edge_set.add((src, dst))
            edge_set.add((dst, src))

        result: dict[str, set[str]] = {}
        for o_dim in outer:
            connected: set[str] = set()
            for i_dim in inner:
                if (o_dim, i_dim) in edge_set:
                    connected.add(i_dim)
            result[o_dim] = connected

        return result


if __name__ == "__main__":
    min_argc = 2
    if len(sys.argv) < min_argc:
        print("Usage: python -m with_me.lib.knowledge_space <command>")
        print("\nCommands:")
        print("  test     - Run doctests")
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
