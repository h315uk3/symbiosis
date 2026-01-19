#!/usr/bin/env python3
"""
Optimized Levenshtein distance calculation using Python standard library only.
Uses dynamic programming with space optimization.
"""


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate Levenshtein distance between two strings.

    Optimized with:
    - Space complexity: O(min(m, n)) instead of O(m × n)
    - Early termination for empty strings
    - Single array reuse

    Args:
        s1: First string
        s2: Second string

    Returns:
        Minimum edit distance (insertions, deletions, substitutions)

    Time: O(m × n) where m, n are string lengths
    Space: O(min(m, n))

    Examples:
        >>> levenshtein_distance("kitten", "sitting")
        3
        >>> levenshtein_distance("saturday", "sunday")
        3
        >>> levenshtein_distance("testing", "tasting")
        1
        >>> levenshtein_distance("", "abc")
        3
        >>> levenshtein_distance("abc", "")
        3
        >>> levenshtein_distance("same", "same")
        0
    """
    # Ensure s1 is the shorter string for space optimization
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    # Early termination
    if len(s1) == 0:
        return len(s2)
    if len(s2) == 0:
        return len(s1)

    # Initialize: only need two rows (previous and current)
    # Using single array and rolling update
    previous_row = list(range(len(s2) + 1))

    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Calculate costs
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)

            current_row.append(min(insertions, deletions, substitutions))

        previous_row = current_row

    return previous_row[-1]


def can_be_similar(s1: str, s2: str, max_distance: int) -> bool:
    """
    Quick check if two strings can be within max_distance.
    Uses length difference as lower bound (faster than full calculation).

    Args:
        s1: First string
        s2: Second string
        max_distance: Maximum allowed distance

    Returns:
        True if strings might be within distance, False if definitely not

    Time: O(1)

    Examples:
        >>> can_be_similar("kitten", "sitting", 3)
        True
        >>> can_be_similar("abc", "defghijk", 2)
        False
        >>> can_be_similar("test", "test", 0)
        True
        >>> can_be_similar("a", "abc", 2)
        True
    """
    len_diff = abs(len(s1) - len(s2))
    return len_diff <= max_distance


if __name__ == "__main__":
    import doctest
    import sys

    if len(sys.argv) == 3:
        # CLI usage: python levenshtein.py "string1" "string2"
        distance = levenshtein_distance(sys.argv[1], sys.argv[2])
        print(distance)
    else:
        # Run doctests
        print("Running Levenshtein distance doctests:")
        results = doctest.testmod(verbose=True)
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
