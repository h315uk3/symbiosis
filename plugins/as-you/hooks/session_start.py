#!/usr/bin/env python3
"""SessionStart lifecycle hook for As You plugin."""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import time

# Add plugin root to Python path
HOOK_DIR = Path(__file__).parent.resolve()
REPO_ROOT = HOOK_DIR.parent
sys.path.insert(0, str(REPO_ROOT))

from as_you.lib.common import AsYouConfig


def cleanup_old_archives(archive_dir: Path, days: int = 7) -> int:
    """
    Delete archive files older than specified days.

    Args:
        archive_dir: Path to session archive directory
        days: Number of days to retain (default 7)

    Returns:
        Number of files deleted

    Examples:
        >>> import tempfile
        >>> from pathlib import Path
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     archive_dir = Path(tmpdir)
        ...     old_file = archive_dir / "old.md"
        ...     old_file.touch()
        ...     # Set mtime to 8 days ago
        ...     import time, os
        ...     old_time = time.time() - (8 * 24 * 60 * 60)
        ...     os.utime(old_file, (old_time, old_time))
        ...     deleted = cleanup_old_archives(archive_dir, days=7)
        ...     assert deleted == 1
    """
    if not archive_dir.exists():
        return 0

    threshold = time.time() - (days * 24 * 60 * 60)
    deleted = 0

    for md_file in archive_dir.glob("*.md"):
        try:
            if md_file.stat().st_mtime < threshold:
                md_file.unlink()
                deleted += 1
        except OSError:
            # Silently ignore deletion errors (match bash behavior)
            pass

    return deleted


def fetch_promotion_summary_from_analyzer(repo_root: Path, error_log: Path) -> dict | None:
    """
    Fetch promotion candidates summary from analyzer subprocess.

    Args:
        repo_root: Repository root path
        error_log: Path to error log file

    Returns:
        Dict with keys: total, skills, agents, top_pattern, top_type
        None if analysis fails
    """
    script = repo_root / "as_you/commands/promotion_analyzer.py"

    try:
        result = subprocess.run(
            [sys.executable, str(script), "summary-line"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=repo_root
        )

        # Log stderr
        if result.stderr:
            with open(error_log, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] promotion_analyzer stderr:\n")
                f.write(result.stderr)
                f.write("\n")

        if result.returncode != 0:
            return None

        # Parse space-separated output
        parts = result.stdout.strip().split()
        if len(parts) < 5:
            return None

        return {
            "total": int(parts[0]),
            "skills": int(parts[1]),
            "agents": int(parts[2]),
            "top_pattern": parts[3],
            "top_type": parts[4]
        }

    except (subprocess.TimeoutExpired, ValueError, IndexError) as e:
        with open(error_log, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] promotion_analyzer error: {e}\n")
        return None


def display_promotion_info(summary: dict) -> None:
    """
    Display promotion candidates information.

    Args:
        summary: Dict from get_promotion_summary()
    """
    if not summary or summary["total"] <= 0:
        return

    total = summary["total"]
    skills = summary["skills"]
    agents = summary["agents"]
    top_pattern = summary["top_pattern"]
    top_type = summary["top_type"]

    print(f"Knowledge base promotion candidates detected ({total} patterns)")

    if skills > 0:
        print(f"  - Skill candidates: {skills}")

    if agents > 0:
        print(f"  - Agent candidates: {agents}")

    if top_pattern and top_pattern not in ("null", "None"):
        print(f'  - Top priority: "{top_pattern}" ({top_type})')

    print("\nDetailed analysis: /as-you:memory-analyze\n")


def main() -> dict:
    """
    Main entry point for SessionStart hook.

    Returns:
        Hook output dict for Claude Code
    """
    # Ensure PROJECT_ROOT is set correctly for hook execution
    if "PROJECT_ROOT" not in os.environ:
        os.environ["PROJECT_ROOT"] = str(REPO_ROOT)

    try:
        config = AsYouConfig.from_environment()
    except Exception as e:
        return {
            "continue": True,
            "systemMessage": f"As You: Config error: {e}"
        }

    as_you_dir = config.claude_dir / "as_you"
    error_log = as_you_dir / "errors.log"
    error_log.parent.mkdir(parents=True, exist_ok=True)

    # 1. Cleanup old archives
    try:
        deleted = cleanup_old_archives(config.archive_dir, days=7)
        if deleted > 0:
            print(f"Cleaned up {deleted} old archive(s)")
    except Exception as e:
        # Non-fatal
        with open(error_log, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Archive cleanup error: {e}\n")

    # 2. Clear session notes for fresh start
    try:
        if config.memo_file.exists():
            config.memo_file.unlink()
    except OSError as e:
        # Non-fatal
        with open(error_log, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Session notes clear error: {e}\n")

    # 3. Analyze and display promotion candidates
    if config.tracker_file.exists():
        summary = fetch_promotion_summary_from_analyzer(REPO_ROOT, error_log)
        if summary:
            display_promotion_info(summary)

    # 3.5. Inject relevant habits (Phase 3 of Issue #83)
    try:
        from as_you.lib.context_detector import (
            detect_project_type,
            extract_keywords_from_files,
            build_context_query
        )
        from as_you.lib.habit_searcher import search_habits

        # Detect context
        tags = detect_project_type(config.project_root)
        keywords = extract_keywords_from_files(config.project_root)
        query = build_context_query(tags, keywords)

        # Get settings
        habits_config = config.settings.get("habits", {})
        min_confidence = habits_config.get("min_confidence", 0.6)  # Higher threshold for auto-injection
        min_freshness = habits_config.get("min_freshness", 0.4)    # Higher threshold for auto-injection
        half_life_days = habits_config.get("freshness_half_life_days", 30)

        bm25_config = config.settings.get("scoring", {}).get("bm25", {})
        k1 = bm25_config.get("k1", 1.5)
        b = bm25_config.get("b", 0.75)

        # Search for habits (top 3, high threshold to reduce noise)
        habits = search_habits(
            query,
            config.tracker_file,
            top_k=3,
            min_confidence=min_confidence,
            min_freshness=min_freshness,
            k1=k1,
            b=b,
            half_life_days=half_life_days,
        )

        if habits:
            print("Relevant habits for this session:")
            for i, habit in enumerate(habits, 1):
                print(f"  {i}. {habit['text']}")
            print()

    except Exception as e:
        # Non-fatal error - don't block session start
        with open(error_log, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Habit injection error: {e}\n")

    # 4. Display welcome message
    print("As You plugin loaded")
    print("Quick start: /as-you:help")

    return {
        "continue": True,
        "suppressOutput": False
    }


if __name__ == "__main__":
    import doctest

    # Check if running doctests
    if "--test" in sys.argv:
        print("Running session_start doctests:")
        results = doctest.testmod(verbose=("-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        result = main()
        print(json.dumps(result))
