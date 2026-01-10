#!/usr/bin/env python3
"""
Unified doctest runner for all Python modules in scripts/.
Runs all doctests and reports results with colored output.

Assumes execution from project root: python3 tests/run_doctests.py
"""

import doctest
import sys
from pathlib import Path
from typing import List, Tuple


# ANSI color codes
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
NC = "\033[0m"  # No Color


def find_python_modules(directory: Path) -> List[Path]:
    """Find all Python modules in directory."""
    return sorted(directory.glob("*.py"))


def run_module_doctests(module_path: Path, verbose: bool = False) -> Tuple[int, int]:
    """
    Run doctests for a single module.

    Args:
        module_path: Path to Python module
        verbose: Enable verbose output

    Returns:
        Tuple of (tests_run, failures)
    """
    module_name = module_path.stem

    # Import module dynamically
    import importlib.util

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        print(f"{YELLOW}⚠{NC} {module_name}: Could not load module")
        return (0, 0)

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    try:
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"{RED}✗{NC} {module_name}: Import failed - {e}")
        return (0, 1)

    # Run doctests
    results = doctest.testmod(module, verbose=verbose, optionflags=doctest.ELLIPSIS)

    # Print result
    if results.failed == 0:
        if results.attempted > 0:
            print(f"{GREEN}✓{NC} {module_name}: {results.attempted} doctests passed")
        else:
            print(f"{YELLOW}⚠{NC} {module_name}: No doctests found")
    else:
        print(
            f"{RED}✗{NC} {module_name}: {results.failed}/{results.attempted} doctests failed"
        )

    return (results.attempted, results.failed)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run doctests for all Python modules")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    # Always use scripts/ directory (relative to project root)
    scripts_dir = Path("scripts")

    # Add scripts directory to sys.path for module imports
    scripts_path = scripts_dir.resolve()
    if str(scripts_path) not in sys.path:
        sys.path.insert(0, str(scripts_path))

    if not scripts_dir.exists():
        print(f"{RED}Error:{NC} Scripts directory not found: {scripts_dir}")
        sys.exit(1)

    # Find all Python modules
    modules = find_python_modules(scripts_dir)

    if not modules:
        print(f"{YELLOW}Warning:{NC} No Python modules found in {scripts_dir}")
        sys.exit(0)

    print(f"Running doctests for {len(modules)} modules...\n")

    # Run doctests for each module
    total_tests = 0
    total_failures = 0

    for module_path in modules:
        tests_run, failures = run_module_doctests(module_path, args.verbose)
        total_tests += tests_run
        total_failures += failures

    # Print summary
    print("\n" + "=" * 50)
    print(f"Total: {total_tests} doctests")
    print(f"Passed: {total_tests - total_failures}")
    print(f"Failed: {total_failures}")

    if total_failures == 0:
        print(f"\n{GREEN}✓ All doctests passed!{NC}")
        sys.exit(0)
    else:
        print(f"\n{RED}✗ Some doctests failed{NC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
