#!/usr/bin/env python3
"""
SessionEnd hook wrapper for note indexer.

Phase 1 of Issue #83: Habit Extraction and Automatic Application.
"""

import sys
from pathlib import Path

# Add plugin root to Python path
HOOK_DIR = Path(__file__).parent.resolve()
REPO_ROOT = HOOK_DIR.parent
sys.path.insert(0, str(REPO_ROOT))

from as_you.lib.common import AsYouConfig
from as_you.lib.note_indexer import index_notes


def main() -> int:
    """
    Main entry point for note indexer hook.

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    try:
        config = AsYouConfig.from_environment()
        result = index_notes(config)

    except Exception as e:
        print(f"Note indexer error: {e}", file=sys.stderr)
        return 1
    else:
        print(
            f"Note indexing: {result['new_notes']} new, {result['total_notes']} total, {result['clusters']} clusters"
        )
        return 0


if __name__ == "__main__":
    sys.exit(main())
