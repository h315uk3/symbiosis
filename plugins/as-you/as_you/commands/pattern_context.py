#!/usr/bin/env python3
"""
Pattern context extractor CLI for As You plugin.
Command-line wrapper for lib.context_extractor functions.

Modes:
    1. python3 pattern_context.py <pattern-name>
       - Get contexts for specific pattern
    2. python3 pattern_context.py --thompson [limit]
       - List top patterns using Thompson Sampling

Extended to include active learning context (prompts and edits).
"""

import sys

from as_you.lib.common import AsYouConfig, load_tracker
from as_you.lib.context_extractor import (
    get_active_learning_context,
    get_pattern_contexts,
    get_top_patterns_thompson,
)

# CLI argument count constants
MIN_ARGS = 2  # program name + command/pattern
MIN_ARGS_WITH_LIMIT = 3  # program name + --thompson + limit


def show_thompson_patterns(config: AsYouConfig, limit: int = 10):
    """Show top patterns selected by Thompson Sampling."""
    tracker = load_tracker(config.tracker_file)
    if not tracker:
        print("No pattern tracker found", file=sys.stderr)
        sys.exit(1)

    top_patterns = get_top_patterns_thompson(tracker, limit=limit)

    if not top_patterns:
        print("No patterns with Thompson state found", file=sys.stderr)
        sys.exit(1)

    print(f"# Top {len(top_patterns)} Patterns (Thompson Sampling)")
    print("\nExploration-Exploitation Balance:")
    print("- High-confidence patterns (proven) are likely selected")
    print("- Low-confidence patterns (uncertain) have chance to explore")
    print()

    patterns_dict = tracker.get("patterns", {})

    for i, pattern_name in enumerate(top_patterns, 1):
        pattern_data = patterns_dict.get(pattern_name, {})
        composite = pattern_data.get("composite_score", 0.0)
        count = pattern_data.get("count", 0)
        last_seen = pattern_data.get("last_seen", "unknown")

        thompson_state = pattern_data.get("thompson_state", {})
        alpha = thompson_state.get("alpha", 1.0)
        beta = thompson_state.get("beta", 1.0)
        mean = alpha / (alpha + beta)

        bayesian = pattern_data.get("bayesian_confidence", {})
        confidence_mean = bayesian.get("mean", mean)

        print(f"{i}. {pattern_name}")
        print(f"   Composite: {composite:.3f} | Confidence: {confidence_mean:.3f}")
        print(f"   Thompson: alpha={alpha:.1f}, beta={beta:.1f} (mean={mean:.3f})")
        print(f"   Count: {count} | Last seen: {last_seen}")
        print()


def show_pattern_context(config: AsYouConfig, pattern_name: str):
    """Show contexts for a specific pattern."""
    found_any = False

    # Get contexts from pattern_tracker.json
    contexts = get_pattern_contexts(pattern_name, config.tracker_file)
    if contexts:
        print("## Pattern Contexts (from notes)")
        for context in contexts:
            print(f"  - {context}")
        found_any = True

    # Get contexts from active learning data
    al_context = get_active_learning_context(pattern_name, config.claude_dir)

    if al_context["prompts"]:
        print("\n## Related Prompts (from active learning)")
        for prompt in al_context["prompts"]:
            text = prompt.get("text", "")[:100]
            intent = prompt.get("intent", "unknown")
            print(f"  - [{intent}] {text}")
        found_any = True

    if al_context["edits"]:
        print("\n## Related Edits (from active learning)")
        for edit in al_context["edits"]:
            file_path = edit.get("file_path", "")
            lang = edit.get("language", "unknown")
            patterns = edit.get("patterns", [])
            patterns_str = ", ".join(patterns) if patterns else "none"
            print(f"  - {file_path} [{lang}] patterns: {patterns_str}")
        found_any = True

    if not found_any:
        print(f"No context found for pattern: {pattern_name}", file=sys.stderr)
        sys.exit(1)


def main():
    """
    Main entry point.

    Examples:
        >>> # CLI usage: python3 pattern_context.py <pattern-name>
        >>> # Returns contexts from pattern_tracker.json and active_learning.json
        >>> pass
    """
    if len(sys.argv) < MIN_ARGS:
        print(
            "Usage: python3 pattern_context.py <pattern-name> | --thompson [limit]",
            file=sys.stderr,
        )
        sys.exit(1)

    config = AsYouConfig.from_environment()

    # Thompson Sampling mode
    if sys.argv[1] == "--thompson":
        limit = 10
        if len(sys.argv) >= MIN_ARGS_WITH_LIMIT:
            try:
                limit = int(sys.argv[2])
            except ValueError:
                print(f"Invalid limit: {sys.argv[2]}", file=sys.stderr)
                sys.exit(1)
        show_thompson_patterns(config, limit)
    else:
        # Pattern context mode
        pattern_name = sys.argv[1]
        show_pattern_context(config, pattern_name)


if __name__ == "__main__":
    main()
