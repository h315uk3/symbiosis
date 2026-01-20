#!/usr/bin/env python3
"""
Statistics display CLI for with-me plugin.

Collects and outputs enhanced statistics about question effectiveness,
including efficiency analysis, entropy reduction, and correlations.
"""

import json

from with_me.lib.question_stats import collect_enhanced_stats


def main():
    """Main entry point for enhanced statistics"""
    stats = collect_enhanced_stats()

    # Print ASCII report if available
    if "ascii_report" in stats:
        print(stats["ascii_report"])
        print()

    # Print JSON statistics
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
