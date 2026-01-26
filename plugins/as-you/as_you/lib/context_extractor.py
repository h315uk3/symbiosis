#!/usr/bin/env python3
"""
Extract contexts for frequent patterns from archived memos.
Provides both archive-based extraction and tracker-based retrieval.
Includes active learning data integration and Thompson Sampling for pattern selection.
"""

import json
import random
import sys
from pathlib import Path

from as_you.lib.common import AsYouConfig, load_tracker


def load_active_learning_data(claude_dir: Path) -> dict:
    """
    Load active learning data from file.

    Examples:
        >>> import tempfile
        >>> from pathlib import Path
        >>> d = Path(tempfile.mkdtemp())
        >>> load_active_learning_data(d)
        {'prompts': [], 'edits': []}
    """
    data_file = claude_dir / "as_you" / "active_learning.json"
    if data_file.exists():
        try:
            return json.loads(data_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"prompts": [], "edits": []}


def get_top_patterns(tracker: dict, limit: int = 10) -> list[str]:
    """
    Get top N patterns by count.

    Args:
        tracker: Tracker data dictionary
        limit: Maximum number of patterns to return

    Returns:
        List of pattern names sorted by count (descending)

    Examples:
        >>> tracker = {
        ...     "patterns": {
        ...         "python": {"count": 10},
        ...         "test": {"count": 5},
        ...         "deploy": {"count": 15},
        ...     }
        ... }
        >>> get_top_patterns(tracker, limit=2)
        ['deploy', 'python']
        >>> get_top_patterns(tracker, limit=5)
        ['deploy', 'python', 'test']
    """
    patterns = tracker.get("patterns", {})

    # Sort by count (descending)
    sorted_patterns = sorted(
        patterns.items(), key=lambda x: x[1].get("count", 0), reverse=True
    )

    # Return top N pattern names
    return [name for name, _ in sorted_patterns[:limit]]


def get_top_patterns_thompson(
    tracker: dict, limit: int = 10, seed: int | None = None
) -> list[str]:
    """
    Get top N patterns using Thompson Sampling.

    Balances exploration (uncertain patterns) with exploitation (proven patterns)
    by sampling from each pattern's Beta distribution. This implements the
    exploration-exploitation trade-off from multi-armed bandit theory.

    Args:
        tracker: Tracker data dictionary with thompson_state
        limit: Maximum number of patterns to return
        seed: Random seed for reproducibility (optional, for testing)

    Returns:
        List of pattern names sorted by Thompson sample value (descending)

    Examples:
        >>> tracker = {
        ...     "patterns": {
        ...         "proven": {
        ...             "count": 10,
        ...             "composite_score": 0.8,
        ...             "thompson_state": {"alpha": 10.0, "beta": 2.0},
        ...         },
        ...         "uncertain": {
        ...             "count": 3,
        ...             "composite_score": 0.6,
        ...             "thompson_state": {"alpha": 2.0, "beta": 1.0},
        ...         },
        ...         "no_thompson": {"count": 5, "composite_score": 0.7},
        ...     }
        ... }
        >>> random.seed(42)
        >>> patterns = get_top_patterns_thompson(tracker, limit=3)
        >>> len(patterns)
        2
        >>> "proven" in patterns
        True
        >>> "uncertain" in patterns
        True
        >>> "no_thompson" in patterns  # Skipped (no thompson_state)
        False

        >>> # Test with seed for reproducibility
        >>> random.seed(42)
        >>> p1 = get_top_patterns_thompson(tracker, limit=3, seed=42)
        >>> random.seed(42)
        >>> p2 = get_top_patterns_thompson(tracker, limit=3, seed=42)
        >>> p1 == p2
        True

        >>> # Empty tracker
        >>> get_top_patterns_thompson({"patterns": {}}, limit=5)
        []

        >>> # All patterns without thompson_state
        >>> tracker_no_ts = {"patterns": {"a": {"count": 5}, "b": {"count": 3}}}
        >>> get_top_patterns_thompson(tracker_no_ts, limit=5)
        []
    """
    if seed is not None:
        random.seed(seed)

    patterns = tracker.get("patterns", {})

    # Sample from each pattern's Thompson state
    pattern_samples = []

    for name, data in patterns.items():
        thompson_state = data.get("thompson_state")
        if not thompson_state:
            # Skip patterns without Thompson state
            continue

        alpha = thompson_state.get("alpha", 1.0)
        beta = thompson_state.get("beta", 1.0)

        # Sample from Beta(alpha, beta) using Gamma ratio method
        try:
            x = random.gammavariate(alpha, 1.0)
            y = random.gammavariate(beta, 1.0)
            sample = x / (x + y)
        except (ValueError, ZeroDivisionError):
            # Fallback to mean if sampling fails
            sample = alpha / (alpha + beta)

        pattern_samples.append((name, sample))

    # Sort by sample value (descending)
    pattern_samples.sort(key=lambda x: x[1], reverse=True)

    # Return top N pattern names
    return [name for name, _ in pattern_samples[:limit]]


def get_pattern_contexts(pattern_name: str, tracker_file: Path) -> list[str]:
    """
    Get stored contexts for a pattern from tracker.

    This is a lightweight retrieval function that returns already-extracted
    contexts from pattern_tracker.json, as opposed to extract_contexts_for_pattern()
    which scans archive files.

    Args:
        pattern_name: Name of the pattern to get contexts for
        tracker_file: Path to pattern_tracker.json

    Returns:
        List of context strings for the pattern

    Examples:
        >>> from pathlib import Path
        >>> import tempfile, json
        >>> tracker_data = {
        ...     "patterns": {
        ...         "python": {
        ...             "count": 5,
        ...             "contexts": ["Working on Python script", "Python testing"],
        ...         }
        ...     }
        ... }
        >>> with tempfile.NamedTemporaryFile(
        ...     mode="w", suffix=".json", delete=False
        ... ) as f:
        ...     json.dump(tracker_data, f)
        ...     temp_path = Path(f.name)
        >>> contexts = get_pattern_contexts("python", temp_path)
        >>> len(contexts)
        2
        >>> contexts[0]
        'Working on Python script'
        >>> temp_path.unlink()

        >>> # Test non-existent pattern
        >>> with tempfile.NamedTemporaryFile(
        ...     mode="w", suffix=".json", delete=False
        ... ) as f:
        ...     json.dump({"patterns": {}}, f)
        ...     temp_path = Path(f.name)
        >>> get_pattern_contexts("missing", temp_path)
        []
        >>> temp_path.unlink()
    """
    try:
        data = load_tracker(tracker_file)
        patterns = data.get("patterns", {})
        pattern_data = patterns.get(pattern_name, {})
        return pattern_data.get("contexts", [])
    except (OSError, KeyError):
        return []


def extract_contexts_for_pattern(
    pattern: str, archive_dir: Path, max_contexts: int = 5
) -> list[str]:
    """
    Extract context lines for a pattern from archived memos.

    Args:
        pattern: Pattern to search for
        archive_dir: Path to session archive directory
        max_contexts: Maximum number of context lines to return

    Returns:
        List of context lines (with surrounding context)

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> temp_dir = Path(tempfile.mkdtemp())
        >>> _ = (temp_dir / "memo1.md").write_text(
        ...     "Line before\\nPython is great\\nLine after"
        ... )
        >>> contexts = extract_contexts_for_pattern("Python", temp_dir, max_contexts=3)
        >>> len(contexts) > 0
        True
        >>> import shutil
        >>> shutil.rmtree(temp_dir)
    """
    if not archive_dir.exists():
        return []

    contexts = []

    # Search all .md files in archive
    for md_file in archive_dir.glob("*.md"):
        if not md_file.is_file():
            continue

        try:
            with open(md_file, encoding="utf-8") as f:
                lines = f.readlines()
        except (OSError, UnicodeDecodeError):
            continue

        # Search for pattern (case-insensitive)
        pattern_lower = pattern.lower()
        for i, line in enumerate(lines):
            if pattern_lower in line.lower():
                # Get context: line before, matching line, line after
                context_lines = []
                if i > 0:
                    context_lines.append(lines[i - 1].strip())
                context_lines.append(line.strip())
                if i < len(lines) - 1:
                    context_lines.append(lines[i + 1].strip())

                # Add non-empty context lines
                for ctx_line in context_lines:
                    if ctx_line and ctx_line != "--":
                        contexts.append(ctx_line)

                        if len(contexts) >= max_contexts:
                            return contexts

    return contexts


def extract_contexts(
    tracker_file: Path,
    archive_dir: Path,
    top_n: int = 10,
    max_contexts: int = 5,
    use_thompson: bool = True,
) -> dict:
    """
    Extract contexts for top N patterns.

    Args:
        tracker_file: Path to pattern_tracker.json
        archive_dir: Path to session archive directory
        top_n: Number of top patterns to process
        max_contexts: Maximum contexts per pattern
        use_thompson: Use Thompson Sampling for pattern selection (default: True)

    Returns:
        Dictionary with pattern contexts

    Examples:
        >>> from pathlib import Path
        >>> import tempfile, json
        >>> tracker_data = {"patterns": {"test": {"count": 5}}}
        >>> with tempfile.NamedTemporaryFile(
        ...     mode="w", suffix=".json", delete=False
        ... ) as f:
        ...     json.dump(tracker_data, f)
        ...     tracker_path = Path(f.name)
        >>> archive_path = Path(tempfile.mkdtemp())
        >>> result = extract_contexts(tracker_path, archive_path, use_thompson=False)
        >>> "patterns" in result
        True
        >>> tracker_path.unlink()
        >>> archive_path.rmdir()
    """
    # Load tracker
    tracker = load_tracker(tracker_file)
    if not tracker:
        return {}

    # Get top patterns (Thompson Sampling or count-based)
    if use_thompson:
        top_patterns = get_top_patterns_thompson(tracker, limit=top_n)
        # Fallback to count-based if no Thompson states
        if not top_patterns:
            top_patterns = get_top_patterns(tracker, limit=top_n)
    else:
        top_patterns = get_top_patterns(tracker, limit=top_n)

    if not top_patterns:
        return {}

    # Extract contexts for each pattern
    result = {"patterns": {}}

    for pattern in top_patterns:
        count = tracker["patterns"][pattern].get("count", 0)
        contexts = extract_contexts_for_pattern(pattern, archive_dir, max_contexts)

        result["patterns"][pattern] = {"count": count, "contexts": contexts}

    return result


def get_active_learning_context(
    pattern: str, claude_dir: Path, max_results: int = 5
) -> dict:
    """
    Get context from active learning data for a pattern.

    Searches prompts and edits for keyword matches.

    Note:
        Prompts may contain non-English text (Japanese, Chinese, etc.)
        as they are captured as-is. Claude should translate when
        presenting context to users.

    Args:
        pattern: Pattern keyword to search for
        claude_dir: Path to .claude directory
        max_results: Maximum results per category

    Returns:
        Dict with matching prompts and edits

    Examples:
        >>> import tempfile, json
        >>> from pathlib import Path
        >>> d = Path(tempfile.mkdtemp())
        >>> (d / "as_you").mkdir()
        >>> data = {
        ...     "prompts": [
        ...         {"text": "Add authentication feature", "intent": "feature"},
        ...         {"text": "Fix login bug", "intent": "fix"},
        ...     ],
        ...     "edits": [
        ...         {
        ...             "file_path": "/auth.py",
        ...             "language": "python",
        ...             "patterns": ["auth"],
        ...         },
        ...     ],
        ... }
        >>> _ = (d / "as_you" / "active_learning.json").write_text(json.dumps(data))
        >>> result = get_active_learning_context("auth", d)
        >>> len(result["prompts"])
        1
        >>> len(result["edits"])
        1
        >>> import shutil
        >>> shutil.rmtree(d)
    """
    data = load_active_learning_data(claude_dir)
    pattern_lower = pattern.lower()

    matching_prompts = []
    for prompt in data.get("prompts", []):
        text = prompt.get("text", "").lower()
        keywords = prompt.get("keywords", [])
        if pattern_lower in text or pattern_lower in keywords:
            matching_prompts.append(prompt)
            if len(matching_prompts) >= max_results:
                break

    matching_edits = []
    for edit in data.get("edits", []):
        file_path = edit.get("file_path", "").lower()
        patterns = edit.get("patterns", [])
        if pattern_lower in file_path or pattern_lower in patterns:
            matching_edits.append(edit)
            if len(matching_edits) >= max_results:
                break

    return {
        "prompts": matching_prompts,
        "edits": matching_edits,
    }


def main():
    """CLI entry point."""
    config = AsYouConfig.from_environment()

    # Extract contexts
    result = extract_contexts(
        config.tracker_file, config.archive_dir, top_n=10, max_contexts=5
    )

    # Output JSON
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    import doctest

    # Check if running doctests
    if "--test" in sys.argv or "-v" in sys.argv:
        print("Running context extractor doctests:")
        results = doctest.testmod(verbose=("--verbose" in sys.argv or "-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
