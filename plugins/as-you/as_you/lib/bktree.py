#!/usr/bin/env python3
"""
BK-Tree (Burkhard-Keller Tree) implementation for fast similarity search.

Uses metric space properties (triangle inequality) to prune search space.
Reduces O(n²) all-pairs comparison to O(n log n) for similarity search.

Standard library only - no external dependencies.
"""


class BKTreeNode:
    """Node in a BK-Tree."""

    def __init__(self, word: str):
        self.word = word
        self.children: dict[int, BKTreeNode] = {}


class BKTree:
    """
    BK-Tree for efficient similarity search using edit distance.

    Properties:
    - Build: O(n log n) average, O(n²) worst case
    - Query: O(log n) average, O(n) worst case
    - All similar pairs: O(n log n) average vs O(n²) brute force

    Triangle inequality:
    If d(a,b) > d(a,c) + threshold, then d(b,c) > threshold
    This allows pruning without calculating all distances.
    """

    def __init__(self, distance_func):
        """
        Initialize BK-Tree.

        Args:
            distance_func: Function(str, str) -> int for calculating distance
        """
        self.root: BKTreeNode | None = None
        self.distance_func = distance_func
        self.size = 0

    def add(self, word: str) -> None:
        """
        Add word to tree.

        Time: O(log n) average, O(n) worst case

        Examples:
            >>> def simple_dist(a, b):
            ...     return abs(len(a) - len(b))
            >>> tree1 = BKTree(simple_dist)
            >>> tree1.add("kitten")
            >>> tree1.size
            1
            >>> tree2 = BKTree(simple_dist)
            >>> tree2.add("kitten")
            >>> tree2.add("sitting")
            >>> tree2.size
            2
            >>> tree3 = BKTree(simple_dist)
            >>> tree3.add("test")
            >>> tree3.add("test")  # Duplicate
            >>> tree3.size
            1
        """
        if self.root is None:
            self.root = BKTreeNode(word)
            self.size = 1
            return

        current = self.root
        distance = self.distance_func(word, current.word)

        # Check for duplicate at root level
        if distance == 0:
            return

        while distance in current.children:
            current = current.children[distance]
            distance = self.distance_func(word, current.word)
            if distance == 0:
                # Duplicate word, skip
                return

        current.children[distance] = BKTreeNode(word)
        self.size += 1

    def search(self, word: str, max_distance: int) -> list[tuple[str, int]]:
        """
        Find all words within max_distance of the query word.

        Uses triangle inequality to prune search:
        If d(node, query) = x, only explore children with distance
        in range [x - max_distance, x + max_distance]

        Args:
            word: Query word
            max_distance: Maximum edit distance

        Returns:
            List of (word, distance) tuples within max_distance

        Time: O(log n) average, O(n) worst case

        Examples:
            >>> def simple_dist(a, b):
            ...     return abs(len(a) - len(b))
            >>> tree = BKTree(simple_dist)
            >>> for w in ["cat", "cats", "dog"]:
            ...     tree.add(w)
            >>> results = tree.search("cat", 1)
            >>> len(results) >= 1  # At least finds "cat" itself
            True
            >>> results = tree.search("cats", 0)
            >>> len(results) == 1  # Exact match only
            True
        """
        if self.root is None:
            return []

        results: list[tuple[str, int]] = []
        candidates: list[tuple[BKTreeNode, int | None]] = [(self.root, None)]

        while candidates:
            node, _ = candidates.pop()
            distance = self.distance_func(word, node.word)

            if distance <= max_distance:
                results.append((node.word, distance))

            # Triangle inequality: only explore children in range
            min_dist = max(0, distance - max_distance)
            max_dist = distance + max_distance

            for child_dist, child_node in node.children.items():
                if min_dist <= child_dist <= max_dist:
                    candidates.append((child_node, child_dist))

        return results

    def find_all_similar_pairs(
        self, max_distance: int, _min_count: int = 1
    ) -> list[dict]:
        """
        Find all similar pairs in the tree within max_distance.

        This is more efficient than O(n²) brute force because:
        1. Each query is O(log n) instead of O(n)
        2. Triangle inequality reduces comparisons

        Args:
            max_distance: Maximum edit distance for similarity
            _min_count: Minimum pattern count (reserved for future use, currently unused)

        Returns:
            List of similarity pair dictionaries

        Time: O(n log n) average vs O(n²) brute force
        """
        if self.root is None:
            return []

        # Collect all words via tree traversal
        all_words = self._collect_all_words()

        # Track seen pairs to avoid duplicates
        seen_pairs: set[tuple[str, str]] = set()
        similar_pairs = []

        for word in all_words:
            # Search for similar words
            matches = self.search(word, max_distance)

            for match_word, distance in matches:
                if distance == 0:
                    # Skip self-match
                    continue

                # Ensure consistent ordering to avoid duplicates
                sorted_pair = sorted([word, match_word])
                pair: tuple[str, str] = (sorted_pair[0], sorted_pair[1])

                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    similar_pairs.append(
                        {"word1": pair[0], "word2": pair[1], "distance": distance}
                    )

        return similar_pairs

    def _collect_all_words(self) -> list[str]:
        """Collect all words in the tree via DFS."""
        if self.root is None:
            return []

        words = []
        stack = [self.root]

        while stack:
            node = stack.pop()
            words.append(node.word)
            stack.extend(node.children.values())

        return words


def build_bktree_from_patterns(patterns: dict[str, dict], distance_func) -> BKTree:
    """
    Build BK-Tree from pattern dictionary.

    Args:
        patterns: Dict of {word: {count, last_seen, ...}}
        distance_func: Distance function

    Returns:
        Populated BK-Tree

    Time: O(n log n) average
    """
    tree = BKTree(distance_func)

    for word in patterns:
        tree.add(word)

    return tree


if __name__ == "__main__":
    import doctest
    import sys

    # Check if running doctests
    if "--test" in sys.argv or "-v" in sys.argv:
        print("Running BK-Tree doctests:")
        results = doctest.testmod(verbose=("--verbose" in sys.argv or "-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        # Self-test demo
        from levenshtein import levenshtein_distance

        print("BK-Tree self-test:")

        # Build tree
        words = ["kitten", "sitting", "kittens", "bitten", "written", "mitten"]
        tree = BKTree(levenshtein_distance)

        for word in words:
            tree.add(word)

        print(f"Built tree with {tree.size} words")

        # Test search
        query = "kitten"
        max_dist = 2
        results = tree.search(query, max_dist)

        print(f"\nWords within distance {max_dist} of '{query}':")
        for word, dist in sorted(results, key=lambda x: x[1]):
            print(f"  {word}: {dist}")

        # Test all similar pairs
        print(f"\nAll similar pairs (distance ≤ {max_dist}):")
        pairs = tree.find_all_similar_pairs(max_dist)
        for pair in pairs:
            print(f"  {pair['word1']} ↔ {pair['word2']}: {pair['distance']}")

        print(f"\nTotal similar pairs: {len(pairs)}")
        print(
            f"Brute force would require: {len(words) * (len(words) - 1) // 2} comparisons"
        )
