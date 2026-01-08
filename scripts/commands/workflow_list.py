#!/usr/bin/env python3
"""
List user-created workflows (exclude built-in commands).
Replaces workflow_list.sh with testable Python implementation.
"""

import sys
from datetime import datetime
from pathlib import Path

# Built-in commands to exclude
BUILTIN_COMMANDS = {
    "note",
    "notes",
    "memory",
    "promote",
    "workflows",
    "workflow-save",
    "help",
}


def list_workflows(commands_dir: Path | None = None) -> list[dict]:
    """
    List user workflows sorted by modification time.

    Args:
        commands_dir: Path to commands directory (default: ./commands)

    Returns:
        List of workflow dicts with 'name', 'mtime', and 'mtime_str' keys

    Examples:
        >>> import tempfile
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     commands_dir = Path(tmpdir)
        ...     _ = (commands_dir / "note.md").write_text("# Built-in")
        ...     _ = (commands_dir / "custom.md").write_text("# User workflow")
        ...     workflows = list_workflows(commands_dir)
        ...     assert len(workflows) == 1
        ...     assert workflows[0]["name"] == "custom"

        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     commands_dir = Path(tmpdir)
        ...     _ = (commands_dir / "workflow1.md").write_text("# W1")
        ...     _ = (commands_dir / "workflow2.md").write_text("# W2")
        ...     _ = (commands_dir / "note.md").write_text("# Built-in")
        ...     workflows = list_workflows(commands_dir)
        ...     assert len(workflows) == 2
        ...     names = [w["name"] for w in workflows]
        ...     assert "workflow1" in names
        ...     assert "workflow2" in names
        ...     assert "note" not in names

        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     commands_dir = Path(tmpdir)
        ...     workflows = list_workflows(commands_dir)
        ...     assert len(workflows) == 0

        >>> workflows = list_workflows(Path("/nonexistent/path"))
        >>> assert len(workflows) == 0
    """
    if commands_dir is None:
        commands_dir = Path("commands")

    if not commands_dir.exists():
        return []

    workflows = []

    for md_file in commands_dir.glob("*.md"):
        name = md_file.stem

        # Exclude built-in commands
        if name in BUILTIN_COMMANDS:
            continue

        # Get modification time
        mtime = md_file.stat().st_mtime

        workflows.append({
            "name": name,
            "mtime": mtime,
            "mtime_str": datetime.fromtimestamp(mtime).strftime("%b %d %H:%M"),
        })

    # Sort by modification time (newest first)
    workflows.sort(key=lambda w: w["mtime"], reverse=True)

    return workflows


def main():
    """CLI entry point."""
    workflows = list_workflows()

    # Output format: name date (compatible with shell version)
    for workflow in workflows:
        print(f"{workflow['name']} {workflow['mtime_str']}")


if __name__ == "__main__":
    import doctest

    # Check if running doctests
    if "--test" in sys.argv or "-v" in sys.argv:
        print("Running workflow_list doctests:")
        results = doctest.testmod(verbose=("--verbose" in sys.argv or "-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
