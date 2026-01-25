#!/usr/bin/env python3
"""
Pattern context extractor CLI for As You plugin.
Command-line wrapper for lib.context_extractor.get_pattern_contexts().

Extended to include active learning context (prompts and edits).
"""

import sys

from as_you.lib.common import AsYouConfig
from as_you.lib.context_extractor import get_active_learning_context, get_pattern_contexts


def main():
    """
    Main entry point.

    Examples:
        >>> # CLI usage: python3 pattern_context.py <pattern-name>
        >>> # Returns contexts from pattern_tracker.json and active_learning.json
        >>> pass
    """
    min_argc = 2  # program name + pattern name
    if len(sys.argv) < min_argc:
        print("Usage: python3 pattern_context.py <pattern-name>", file=sys.stderr)
        sys.exit(1)

    # Get configuration and pattern name
    config = AsYouConfig.from_environment()
    pattern_name = sys.argv[1]

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


if __name__ == "__main__":
    main()
