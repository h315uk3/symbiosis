#!/usr/bin/env python3
"""
Statistics display entry point for with-me plugin

Provides question effectiveness statistics
Called from stats.md command
"""

if __name__ == "__main__":
    from ..lib import question_stats

    question_stats.main()
