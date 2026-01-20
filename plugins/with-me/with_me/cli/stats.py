#!/usr/bin/env python3
"""
Statistics display CLI for with-me plugin.

Collects and outputs JSON statistics about question effectiveness.
"""

import json

from with_me.lib.question_stats import collect_stats


def main():
    """Main entry point"""
    stats = collect_stats()
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
