#!/usr/bin/env python3
"""
Archive session notes to session_archive.
Date-based archiving with append support.
Replaces archive-note.sh with testable implementation.
"""

import sys
from datetime import date
from pathlib import Path

from as_you.lib.common import AsYouConfig


def archive_note(memo_file: Path, archive_dir: Path) -> Path | None:
    """
    Archive memo to date-based file.

    Args:
        memo_file: Path to session notes file
        archive_dir: Path to archive directory

    Returns:
        Path to archive file if archived, None if skipped

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     # Create test memo
        ...     memo = Path(tmpdir) / "session_notes.md"
        ...     archive_dir = Path(tmpdir) / "archive"
        ...     archive_dir.mkdir()
        ...
        ...     _ = memo.write_text("Test note content", encoding="utf-8")
        ...
        ...     # Archive note
        ...     archived = archive_note(memo, archive_dir)
        ...
        ...     # Verify archived
        ...     archived is not None and archived.exists()
        True

        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     # Test append to existing archive
        ...     memo = Path(tmpdir) / "session_notes.md"
        ...     archive_dir = Path(tmpdir) / "archive"
        ...     archive_dir.mkdir()
        ...
        ...     # First archive
        ...     _ = memo.write_text("First note", encoding="utf-8")
        ...     archived1 = archive_note(memo, archive_dir)
        ...
        ...     # Second archive (same day)
        ...     _ = memo.write_text("Second note", encoding="utf-8")
        ...     archived2 = archive_note(memo, archive_dir)
        ...
        ...     # Should be same file
        ...     archived1 == archived2
        True

        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     # Test empty memo (should skip)
        ...     memo = Path(tmpdir) / "session_notes.md"
        ...     archive_dir = Path(tmpdir) / "archive"
        ...     archive_dir.mkdir()
        ...
        ...     _ = memo.write_text("", encoding="utf-8")
        ...     result = archive_note(memo, archive_dir)
        ...     result is None
        True

        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     # Test non-existent memo (should skip)
        ...     memo = Path(tmpdir) / "nonexistent.md"
        ...     archive_dir = Path(tmpdir) / "archive"
        ...     archive_dir.mkdir()
        ...
        ...     result = archive_note(memo, archive_dir)
        ...     result is None
        True
    """
    # Check if memo exists and is not empty
    if not memo_file.exists() or memo_file.stat().st_size == 0:
        return None

    # Ensure archive directory exists
    archive_dir.mkdir(parents=True, exist_ok=True)

    # Generate archive filename with today's date
    today = date.today().strftime("%Y-%m-%d")
    archive_file = archive_dir / f"{today}.md"

    # Read memo content
    memo_content = memo_file.read_text(encoding="utf-8")

    # If archive for today already exists, append; otherwise create
    if archive_file.exists():
        # Append with separator
        existing_content = archive_file.read_text(encoding="utf-8")
        combined_content = f"{existing_content}\n\n---\n\n{memo_content}"
        archive_file.write_text(combined_content, encoding="utf-8")
    else:
        # Create new archive
        archive_file.write_text(memo_content, encoding="utf-8")

    return archive_file


def main():
    """CLI entry point."""
    # Get paths from common configuration
    config = AsYouConfig.from_environment()

    # Archive note
    archived_file = archive_note(config.memo_file, config.archive_dir)

    if archived_file:
        date_str = archived_file.stem  # Extract date from filename
        print(f"Memo archived to {date_str}.md")
    else:
        # Silent exit if no memo or empty
        pass


if __name__ == "__main__":
    import doctest

    # Check if running doctests
    if "--test" in sys.argv or "-v" in sys.argv:
        print("Running note archiver doctests:")
        results = doctest.testmod(verbose=("--verbose" in sys.argv or "-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
