#!/usr/bin/env python3
"""
Pattern context extractor CLI for As You plugin.
Command-line wrapper for lib.context_extractor.get_pattern_contexts().
"""

import sys

from as_you.lib.common import AsYouConfig
from as_you.lib.context_extractor import get_pattern_contexts


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 pattern_context.py <pattern-name>", file=sys.stderr)
        sys.exit(1)

    # Get configuration and pattern name
    config = AsYouConfig.from_environment()
    pattern_name = sys.argv[1]

    # Get contexts using lib function
    contexts = get_pattern_contexts(pattern_name, config.tracker_file)

    if contexts:
        for context in contexts:
            print(context)
    else:
        print(f"No context found for pattern: {pattern_name}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
