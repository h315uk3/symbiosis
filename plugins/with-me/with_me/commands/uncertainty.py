#!/usr/bin/env python3
"""
Uncertainty calculation entry point for with-me plugin

Calculates uncertainty scores for requirement dimensions
Called from good-question.md for convergence detection
"""

if __name__ == "__main__":
    from with_me.lib import uncertainty_calculator

    uncertainty_calculator.main()
