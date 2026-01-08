#!/usr/bin/env python3
"""
Add timestamped note to current session.
Replaces note_add.sh with testable Python implementation.
"""

import sys
from datetime import datetime
from pathlib import Path


def add_note(content: str, note_file: Path | None = None) -> None:
    """
    Add timestamped note to session file.

    Args:
        content: Note content to add
        note_file: Path to note file (default: .claude/as_you/session_notes.local.md)

    Examples:
        >>> import tempfile
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     note_file = Path(tmpdir) / "notes.md"
        ...     add_note("Test note", note_file)
        ...     lines = note_file.read_text().splitlines()
        ...     assert len(lines) == 1
        ...     assert "Test note" in lines[0]
        ...     assert lines[0].startswith("[")

        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     note_file = Path(tmpdir) / "notes.md"
        ...     add_note("First note", note_file)
        ...     add_note("Second note", note_file)
        ...     lines = note_file.read_text().splitlines()
        ...     assert len(lines) == 2
        ...     assert "First note" in lines[0]
        ...     assert "Second note" in lines[1]
    """
    if note_file is None:
        note_file = Path(".claude/as_you/session_notes.local.md")

    # Ensure directory exists
    note_file.parent.mkdir(parents=True, exist_ok=True)

    # Generate timestamp
    timestamp = datetime.now().strftime("%H:%M")

    # Append note
    with open(note_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {content}\n")


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: note_add.py \"note content\"", file=sys.stderr)
        sys.exit(1)

    content = sys.argv[1]
    add_note(content)


if __name__ == "__main__":
    import doctest

    # Check if running doctests
    if "--test" in sys.argv or "-v" in sys.argv:
        print("Running note_add doctests:")
        results = doctest.testmod(verbose=("--verbose" in sys.argv or "-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
