#!/usr/bin/env python3
"""
Performance benchmarks for with-me plugin evaluation logic.

Verifies that evaluation functions meet the < 100ms performance requirement.
Uses only Python standard library for minimal dependencies.

Usage:
    python3 tests/test_with_me_performance.py
    
Environment:
    PYTHONPATH can be set to include the plugin directory, or
    the script will auto-detect the plugin path relative to itself.
"""

import os
import sys
import time
from pathlib import Path

# Add plugin to path - check environment first, fallback to relative path
if "PYTHONPATH" not in os.environ or "with-me" not in os.environ.get("PYTHONPATH", ""):
    # Auto-detect plugin path relative to test file location
    plugin_root = Path(__file__).parent.parent / "plugins" / "with-me"
    if plugin_root.exists():
        sys.path.insert(0, str(plugin_root))
    else:
        raise RuntimeError(
            f"Plugin directory not found at {plugin_root}. "
            "Set PYTHONPATH to include the with-me plugin directory."
        )

from with_me.lib.question_reward_calculator import QuestionRewardCalculator
from with_me.lib.uncertainty_calculator import calculate_dimension_uncertainty
from with_me.lib.dimension_selector import DimensionSelector


def benchmark_function(func, *args, iterations: int = 100, **kwargs) -> dict:
    """
    Benchmark a function's execution time

    Args:
        func: Function to benchmark
        *args: Positional arguments for function
        iterations: Number of iterations to run
        **kwargs: Keyword arguments for function

    Returns:
        Dict with timing statistics (min, max, avg, total)
    """
    times = []

    for _ in range(iterations):
        start = time.perf_counter()
        func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        times.append(elapsed * 1000)  # Convert to milliseconds

    return {
        "min_ms": min(times),
        "max_ms": max(times),
        "avg_ms": sum(times) / len(times),
        "total_ms": sum(times),
        "iterations": iterations,
    }


def test_reward_calculation_performance():
    """Test question reward calculation performance"""
    calculator = QuestionRewardCalculator()
    
    context = {
        "uncertainties": {"purpose": 0.9, "data": 0.7, "behavior": 0.6},
        "answered_dimensions": [],
        "question_history": ["What is this?"],
    }
    
    question = "What problem does this solve specifically?"
    
    stats = benchmark_function(
        calculator.calculate_reward, question, context, None, iterations=100
    )
    
    print("Question Reward Calculation:")
    print(f"  Average: {stats['avg_ms']:.2f}ms")
    print(f"  Min: {stats['min_ms']:.2f}ms")
    print(f"  Max: {stats['max_ms']:.2f}ms")
    
    # Verify requirement: < 100ms
    if stats['avg_ms'] < 100:
        print(f"  ✓ PASS: Average time ({stats['avg_ms']:.2f}ms) < 100ms threshold")
        return True
    else:
        print(f"  ✗ FAIL: Average time ({stats['avg_ms']:.2f}ms) exceeds 100ms threshold")
        return False


def test_uncertainty_calculation_performance():
    """Test uncertainty calculation performance"""
    dimension_data = {
        "answered": True,
        "content": "This is a detailed explanation of the purpose with multiple sentences describing the problem, the users, and the expected outcomes. It includes specific examples and clear descriptions.",
        "examples": 2,
        "contradictions": False,
    }
    
    stats = benchmark_function(
        calculate_dimension_uncertainty, dimension_data, iterations=100
    )
    
    print("\nUncertainty Calculation:")
    print(f"  Average: {stats['avg_ms']:.2f}ms")
    print(f"  Min: {stats['min_ms']:.2f}ms")
    print(f"  Max: {stats['max_ms']:.2f}ms")
    
    # Verify requirement: < 100ms
    if stats['avg_ms'] < 100:
        print(f"  ✓ PASS: Average time ({stats['avg_ms']:.2f}ms) < 100ms threshold")
        return True
    else:
        print(f"  ✗ FAIL: Average time ({stats['avg_ms']:.2f}ms) exceeds 100ms threshold")
        return False


def test_dimension_selection_performance():
    """Test DAG-based dimension selection performance"""
    selector = DimensionSelector()
    
    uncertainties = {
        "purpose": 0.3,
        "data": 0.7,
        "behavior": 0.6,
        "constraints": 0.8,
        "quality": 0.5,
    }
    
    stats = benchmark_function(
        selector.select_next_dimension, uncertainties, iterations=100
    )
    
    print("\nDimension Selection (DAG):")
    print(f"  Average: {stats['avg_ms']:.2f}ms")
    print(f"  Min: {stats['min_ms']:.2f}ms")
    print(f"  Max: {stats['max_ms']:.2f}ms")
    
    # Verify requirement: < 100ms
    if stats['avg_ms'] < 100:
        print(f"  ✓ PASS: Average time ({stats['avg_ms']:.2f}ms) < 100ms threshold")
        return True
    else:
        print(f"  ✗ FAIL: Average time ({stats['avg_ms']:.2f}ms) exceeds 100ms threshold")
        return False


def test_combined_workflow_performance():
    """Test realistic combined workflow performance"""
    calculator = QuestionRewardCalculator()
    selector = DimensionSelector()
    
    # Simulate a typical workflow:
    # 1. Select dimension
    # 2. Calculate reward
    # 3. Update uncertainties
    # 4. Repeat
    
    uncertainties = {
        "purpose": 0.8,
        "data": 0.9,
        "behavior": 0.7,
        "constraints": 0.6,
        "quality": 0.5,
    }
    
    def combined_workflow():
        # Select dimension
        next_dim, _ = selector.select_next_dimension(uncertainties)
        
        # Prepare context
        context = {
            "uncertainties": uncertainties,
            "answered_dimensions": [],
            "question_history": [],
        }
        
        # Calculate reward for a hypothetical question
        question = f"What {next_dim} information do you have?"
        calculator.calculate_reward(question, context)
        
        # Calculate uncertainty
        dimension_data = {
            "answered": True,
            "content": "Some answer content",
            "examples": 1,
            "contradictions": False,
        }
        calculate_dimension_uncertainty(dimension_data)
    
    stats = benchmark_function(combined_workflow, iterations=100)
    
    print("\nCombined Workflow (Select + Reward + Uncertainty):")
    print(f"  Average: {stats['avg_ms']:.2f}ms")
    print(f"  Min: {stats['min_ms']:.2f}ms")
    print(f"  Max: {stats['max_ms']:.2f}ms")
    
    # For combined workflow, allow slightly higher threshold
    threshold = 200  # 200ms for 3 operations
    if stats['avg_ms'] < threshold:
        print(f"  ✓ PASS: Average time ({stats['avg_ms']:.2f}ms) < {threshold}ms threshold")
        return True
    else:
        print(f"  ✗ FAIL: Average time ({stats['avg_ms']:.2f}ms) exceeds {threshold}ms threshold")
        return False


def main() -> int:
    """
    Run all performance benchmarks

    Returns:
        Exit code: 0 if all benchmarks pass, 1 if any fail
    """
    print("=" * 60)
    print("With-Me Performance Benchmarks")
    print("=" * 60)
    print()
    
    results = []
    
    # Run individual benchmarks
    results.append(test_reward_calculation_performance())
    results.append(test_uncertainty_calculation_performance())
    results.append(test_dimension_selection_performance())
    results.append(test_combined_workflow_performance())
    
    # Summary
    print()
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✓ All {total} performance benchmarks PASSED")
        return 0
    else:
        print(f"✗ {total - passed}/{total} performance benchmarks FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
