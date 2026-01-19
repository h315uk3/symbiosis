#!/usr/bin/env python3
"""
Uncertainty calculation entry point for with-me plugin

Calculates uncertainty scores for requirement dimensions
Called from good-question.md for convergence detection
"""

import sys
from pathlib import Path

# Add scripts/ to path for lib imports (matches as-you pattern)
sys.path.insert(0, str(Path(__file__).parent.parent))

if __name__ == "__main__":
    from lib import uncertainty_calculator

    uncertainty_calculator.main()
