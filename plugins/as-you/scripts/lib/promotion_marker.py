#!/usr/bin/env python3
"""
Mark patterns as promoted to skills/agents.
CLI tool with argparse and full validation.
Replaces mark-promoted.sh with testable implementation.
"""

import argparse
import sys
from enum import Enum
from pathlib import Path
from typing import Self

from lib.common import AsYouConfig
from lib.pattern_updater import mark_promoted as mark_pattern_as_promoted
from lib.score_calculator import UnifiedScoreCalculator


class PromotionType(Enum):
    """Promotion type enumeration."""

    SKILL = "skill"
    AGENT = "agent"

    @classmethod
    def from_string(cls, value: str) -> Self | None:
        """
        Create PromotionType from string.

        Examples:
            >>> PromotionType.from_string("skill")
            <PromotionType.SKILL: 'skill'>
            >>> PromotionType.from_string("agent")
            <PromotionType.AGENT: 'agent'>
            >>> PromotionType.from_string("invalid") is None
            True
        """
        try:
            return cls(value.lower())
        except ValueError:
            return None


def mark_as_promoted(
    tracker_file: Path, pattern: str, promotion_type: PromotionType, location: str
) -> dict:
    """
    Mark pattern as promoted to prevent duplicate promotion.

    Args:
        tracker_file: Path to pattern_tracker.json
        pattern: Pattern name (e.g., "deployment")
        promotion_type: Type of promotion (skill or agent)
        location: Path to the promoted skill/agent

    Returns:
        Result dictionary with status and message

    Examples:
        >>> from pathlib import Path
        >>> import tempfile, json
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     # Create test tracker
        ...     tracker = Path(tmpdir) / "pattern_tracker.json"
        ...     data = {
        ...         "patterns": {
        ...             "deployment": {"count": 10, "last_seen": "2025-01-05", "sessions": ["s1"]}
        ...         },
        ...         "promotion_candidates": ["deployment"],
        ...         "cooccurrences": []
        ...     }
        ...     _ = tracker.write_text(json.dumps(data), encoding="utf-8")
        ...
        ...     # Mark as promoted
        ...     result = mark_as_promoted(
        ...         tracker, "deployment", PromotionType.SKILL, "skills/deployment/"
        ...     )
        ...
        ...     # Verify success
        ...     result["status"] == "success"
        True

        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     # Test with non-existent pattern
        ...     tracker = Path(tmpdir) / "pattern_tracker.json"
        ...     data = {"patterns": {}, "promotion_candidates": [], "cooccurrences": []}
        ...     _ = tracker.write_text(json.dumps(data), encoding="utf-8")
        ...     result = mark_as_promoted(
        ...         tracker, "nonexistent", PromotionType.SKILL, "skills/test/"
        ...     )
        ...     result["status"] == "error"
        True

        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     # Test with non-existent tracker file
        ...     tracker = Path(tmpdir) / "nonexistent.json"
        ...     result = mark_as_promoted(
        ...         tracker, "test", PromotionType.SKILL, "skills/test/"
        ...     )
        ...     result["status"] == "error"
        True
    """
    if not tracker_file.exists():
        return {
            "status": "error",
            "message": f"Tracker file not found: {tracker_file}",
        }

    try:
        # Call pattern_updater to mark as promoted
        result = mark_pattern_as_promoted(
            tracker_file, pattern, promotion_type.value, location
        )

        if result["status"] == "success":
            # Recalculate scores to reflect promotion
            try:
                archive_dir = tracker_file.parent / "session_archive"
                if archive_dir.exists():
                    calculator = UnifiedScoreCalculator(tracker_file, archive_dir)
                    calculator.calculate_all_scores()
                    calculator.save()
            except Exception:
                pass  # Non-fatal if scoring fails

        return result

    except Exception as e:
        return {"status": "error", "message": str(e)}


def main():
    """CLI entry point with argparse."""
    parser = argparse.ArgumentParser(
        description="Mark a pattern as promoted to prevent duplicate promotion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s deployment skill skills/deployment-workflow/
  %(prog)s testing agent agents/test-manager/
        """,
    )

    parser.add_argument("pattern", help="Pattern name (e.g., 'deployment', 'testing')")
    parser.add_argument(
        "type",
        choices=["skill", "agent"],
        help="Promotion type: 'skill' or 'agent'",
    )
    parser.add_argument(
        "path",
        help="Path to the promoted skill/agent (e.g., 'skills/deployment/')",
    )

    args = parser.parse_args()

    # Get paths from environment
    config = AsYouConfig.from_environment()
    tracker_file = config.tracker_file

    # Parse promotion type
    promotion_type = PromotionType.from_string(args.type)
    if promotion_type is None:
        print(f"Error: Invalid promotion type: {args.type}", file=sys.stderr)
        sys.exit(1)

    # Mark as promoted
    result = mark_as_promoted(tracker_file, args.pattern, promotion_type, args.path)

    if result["status"] == "error":
        print(f"Error: {result['message']}", file=sys.stderr)
        sys.exit(1)

    print(
        f"✓ Pattern '{args.pattern}' marked as promoted to {args.type} at {args.path}"
    )
    print("✓ Promotion candidates updated")


if __name__ == "__main__":
    import doctest

    # Check if running doctests
    if "--test" in sys.argv:
        print("Running promotion marker doctests:")
        # Remove --test to avoid argparse errors
        sys.argv.remove("--test")
        results = doctest.testmod(verbose=("--verbose" in sys.argv or "-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
