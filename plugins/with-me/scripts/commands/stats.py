#!/usr/bin/env python3
"""
Statistics display entry point for with-me plugin

Provides question effectiveness statistics
Called from stats.md command
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

if __name__ == "__main__":
    from lib import question_stats
    question_stats.main()
