#!/usr/bin/env python3
"""
Doctest runner for all plugins.

Discovers and runs doctests from all Python files in plugin scripts directories.
Uses only Python standard library to maintain zero external dependencies.

Usage:
    python3 tests/run_doctests.py           # Run all doctests
    python3 tests/run_doctests.py --verbose # Run with verbose output

Examples:
    >>> # This file doesn't contain doctests itself
    >>> # It's a runner that discovers doctests in other files
"""

import doctest
import importlib.util
import sys
from contextlib import suppress
from pathlib import Path


def discover_and_test(root: Path, verbose: bool = False) -> tuple[int, int]:
    """
    Discover and run doctests from all plugin Python files.

    Args:
        root: Project root directory
        verbose: Whether to show verbose output

    Returns:
        Tuple of (total_tests, failures)

    Examples:
        >>> root = Path("/tmp/test_project")
        >>> tests, failures = discover_and_test(root, verbose=False)
        >>> isinstance(tests, int) and isinstance(failures, int)
        True
    """
    total_tests = 0
    total_failures = 0

    plugins = [
        ("as-you", "as_you"),
        ("with-me", "with_me")
    ]

    for plugin_dir, plugin_pkg in plugins:
        plugin_root = root / "plugins" / plugin_dir
        if not plugin_root.exists():
            continue

        print(f"Testing plugins/{plugin_dir}...")

        # Add plugin root to path for imports (for as_you.* / with_me.* imports)
        sys.path.insert(0, str(plugin_root))

        # Find all Python files, prioritizing lib/ first for dependencies
        py_files = []

        # First add lib/ files (dependencies)
        lib_dir = plugin_root / plugin_pkg / "lib"
        if lib_dir.exists():
            py_files.extend(sorted(lib_dir.glob("*.py")))

        # Then add other files
        for subdir in ["commands", "hooks"]:
            subdir_path = plugin_root / plugin_pkg / subdir
            if subdir_path.exists():
                py_files.extend(sorted(subdir_path.glob("*.py")))

        for py_file in py_files:
            # Skip __init__.py files (shouldn't exist but check anyway)
            if py_file.name == "__init__.py":
                continue

            # Import module dynamically with proper module name
            # Calculate relative path from plugin package root
            rel_parts = py_file.relative_to(plugin_root / plugin_pkg).parts
            module_name = f"{plugin_pkg}.{'.'.join(rel_parts[:-1])}.{py_file.stem}" if len(rel_parts) > 1 else f"{plugin_pkg}.{py_file.stem}"

            spec = importlib.util.spec_from_file_location(module_name, py_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                try:
                    spec.loader.exec_module(module)
                except Exception as e:
                    print(f"  ✗ {py_file.name} (import failed: {e})")
                    total_failures += 1
                    continue

                # Run doctest on the module
                result = doctest.testmod(
                    module,
                    verbose=verbose,
                    optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE,
                )

                total_tests += result.attempted
                total_failures += result.failed

                # Show status
                status = "✓" if result.failed == 0 else "✗"
                print(f"  {status} {py_file.name}")

    return total_tests, total_failures


def main() -> int:
    """
    Main entry point for the doctest runner.

    Returns:
        Exit code: 0 if all tests pass, 1 if any fail
    """
    root = Path(__file__).parent.parent
    verbose = "--verbose" in sys.argv

    tests, failures = discover_and_test(root, verbose)

    # Print summary
    print()
    if failures == 0:
        print("✓ All doctests passed")
        return 0
    else:
        print(f"✗ {failures} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
