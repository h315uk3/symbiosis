#!/usr/bin/env python3
"""SessionEnd lifecycle hook for As You plugin."""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from as_you.lib.common import AsYouConfig

# Plugin root path (for subprocess calls)
HOOK_DIR = Path(__file__).parent.resolve()
PLUGIN_ROOT = HOOK_DIR.parent


def run_python_script(
    script_path: Path,
    args: list[str] | None = None,
    error_log: Path | None = None,
    timeout: int = 30
) -> dict:
    """
    Run Python script and return results.

    Args:
        script_path: Path to Python script
        args: Command-line arguments
        error_log: Path to error log (optional)
        timeout: Timeout in seconds

    Returns:
        Dict with keys: success (bool), stdout (str), stderr (str), returncode (int)
    """
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    # Inherit environment and ensure PYTHONPATH includes plugin root
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PLUGIN_ROOT)
    # Child processes inherit environment from parent

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.getcwd(),
            env=env,
            check=False
        )
    except subprocess.TimeoutExpired:
        error_msg = f"{script_path.name} timeout after {timeout}s"
        if error_log:
            with open(error_log, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] {error_msg}\n")
        return {
            "success": False,
            "stdout": "",
            "stderr": error_msg,
            "returncode": -1
        }
    except Exception as e:
        error_msg = f"{script_path.name} error: {e}"
        if error_log:
            with open(error_log, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] {error_msg}\n")
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }
    else:
        # Log stderr if present
        if result.stderr and error_log:
            with open(error_log, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] {script_path.name} stderr:\n")
                f.write(result.stderr)
                f.write("\n")

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }


def main() -> dict:
    """
    Main entry point for SessionEnd hook.

    Returns:
        Hook output dict for Claude Code
    """
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

    # 1. Archive session notes
    result = run_python_script(
        PLUGIN_ROOT / "as_you/hooks/note_archiver.py",
        error_log=error_log,
        timeout=10
    )
    if not result["success"]:
        print(f"Warning: Note archiving failed: {result['stderr']}", file=sys.stderr)

    # 1.5. Index notes from archives (Phase 1 of Issue #83)
    result = run_python_script(
        PLUGIN_ROOT / "as_you/hooks/note_indexer_hook.py",
        error_log=error_log,
        timeout=20
    )
    if not result["success"]:
        print(f"Warning: Note indexing failed: {result['stderr']}", file=sys.stderr)

    # 2. Update pattern tracker (detect patterns, extract contexts, update tracker)
    result = run_python_script(
        PLUGIN_ROOT / "as_you/hooks/pattern_tracker_update.py",
        error_log=error_log,
        timeout=30
    )
    if not result["success"]:
        print(f"Warning: Pattern tracker update failed: {result['stderr']}", file=sys.stderr)
        # Continue to next step even if update fails

    # 3. Calculate pattern scores (independent from tracker update)
    result = run_python_script(
        PLUGIN_ROOT / "as_you/hooks/score_calculator_hook.py",
        error_log=error_log,
        timeout=30
    )
    if not result["success"]:
        print(f"Warning: Score calculation failed: {result['stderr']}", file=sys.stderr)
        # Non-fatal: tracker is still updated, just without scores

    # 3.5. Update habit freshness (Phase 4 of Issue #83)
    result = run_python_script(
        PLUGIN_ROOT / "as_you/hooks/habit_freshness_update.py",
        error_log=error_log,
        timeout=10
    )
    if not result["success"]:
        print(f"Warning: Habit freshness update failed: {result['stderr']}", file=sys.stderr)

    # 3.6. Integrate active learning data (Issue #93)
    result = run_python_script(
        PLUGIN_ROOT / "as_you/hooks/active_learning_integration.py",
        error_log=error_log,
        timeout=15
    )
    if not result["success"]:
        print(f"Warning: Active learning integration failed: {result['stderr']}", file=sys.stderr)

    # Pattern merge is now user-initiated via /as-you:patterns → "Analyze patterns"
    # No automatic merge to maintain transparency and user control

    return {
        "continue": True,
        "suppressOutput": False
    }


if __name__ == "__main__":
    import doctest

    # Check if running doctests
    if "--test" in sys.argv:
        print("Running session_end doctests:")
        results = doctest.testmod(verbose=("-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        result = main()
        print(json.dumps(result))
