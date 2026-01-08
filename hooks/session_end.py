#!/usr/bin/env python3
"""SessionEnd lifecycle hook for As You plugin."""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Add scripts/ to Python path
HOOK_DIR = Path(__file__).parent.resolve()
REPO_ROOT = HOOK_DIR.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.common import AsYouConfig


class SessionCounter:
    """Manage session counter with file-based persistence."""

    def __init__(self, counter_file: Path):
        """Initialize counter with file path."""
        self.counter_file = counter_file
        self.counter_file.parent.mkdir(parents=True, exist_ok=True)

    def read(self) -> int:
        """
        Read current counter value.

        Returns:
            Current count (0 if file doesn't exist or is invalid)

        Examples:
            >>> import tempfile
            >>> with tempfile.TemporaryDirectory() as tmpdir:
            ...     counter_file = Path(tmpdir) / "count"
            ...     counter = SessionCounter(counter_file)
            ...     assert counter.read() == 0

            >>> with tempfile.TemporaryDirectory() as tmpdir:
            ...     counter_file = Path(tmpdir) / "count"
            ...     _ = counter_file.write_text("42")
            ...     counter = SessionCounter(counter_file)
            ...     assert counter.read() == 42
        """
        try:
            content = self.counter_file.read_text(encoding="utf-8").strip()
            return int(content)
        except (FileNotFoundError, ValueError):
            return 0

    def increment(self) -> int:
        """
        Increment counter atomically.

        Returns:
            New counter value after increment

        Examples:
            >>> import tempfile
            >>> with tempfile.TemporaryDirectory() as tmpdir:
            ...     counter_file = Path(tmpdir) / "count"
            ...     counter = SessionCounter(counter_file)
            ...     assert counter.increment() == 1
            ...     assert counter.increment() == 2
            ...     assert counter.increment() == 3
        """
        count = self.read() + 1
        self.counter_file.write_text(str(count), encoding="utf-8")
        return count

    def should_merge(self, count: int, interval: int) -> bool:
        """
        Check if merge should run at this session count.

        Args:
            count: Current session number
            interval: Sessions between merges

        Returns:
            True if merge should run

        Examples:
            >>> counter = SessionCounter(Path("/tmp/test"))
            >>> assert counter.should_merge(10, 10) == True
            >>> assert counter.should_merge(9, 10) == False
            >>> assert counter.should_merge(20, 10) == True
        """
        return count % interval == 0

    def next_merge_session(self, count: int, interval: int) -> int:
        """
        Calculate next session where merge will run.

        Args:
            count: Current session number
            interval: Sessions between merges

        Returns:
            Next merge session number

        Examples:
            >>> counter = SessionCounter(Path("/tmp/test"))
            >>> assert counter.next_merge_session(5, 10) == 10
            >>> assert counter.next_merge_session(10, 10) == 20
            >>> assert counter.next_merge_session(15, 10) == 20
        """
        remainder = count % interval
        if remainder == 0:
            return count + interval
        return count + (interval - remainder)


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

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=REPO_ROOT
        )

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


def parse_merge_output(output: str) -> list[str]:
    """
    Parse pattern merger output for merge results.

    Args:
        output: stdout from pattern_merger.py

    Returns:
        List of lines containing "Merged"

    Examples:
        >>> output = "Starting merge\\nMerged 'test' into 'testing'\\nMerged 'foo' into 'foobar'\\nDone"
        >>> result = parse_merge_output(output)
        >>> assert len(result) == 2
        >>> assert "Merged 'test' into 'testing'" in result
        >>> assert "Merged 'foo' into 'foobar'" in result
    """
    return [line for line in output.split("\n") if "Merged" in line]


def main() -> dict:
    """
    Main entry point for SessionEnd hook.

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

    # 1. Archive session notes
    result = run_python_script(
        REPO_ROOT / "scripts/hooks/note_archiver.py",
        error_log=error_log,
        timeout=10
    )
    if not result["success"]:
        print(f"Warning: Note archiving failed: {result['stderr']}", file=sys.stderr)

    # 2. Update pattern tracker (detect patterns, extract contexts, update tracker)
    result = run_python_script(
        REPO_ROOT / "scripts/hooks/pattern_tracker_update.py",
        error_log=error_log,
        timeout=30
    )
    if not result["success"]:
        print(f"Warning: Pattern tracker update failed: {result['stderr']}", file=sys.stderr)
        # Continue to next step even if update fails

    # 3. Calculate pattern scores (independent from tracker update)
    result = run_python_script(
        REPO_ROOT / "scripts/hooks/score_calculator_hook.py",
        error_log=error_log,
        timeout=30
    )
    if not result["success"]:
        print(f"Warning: Score calculation failed: {result['stderr']}", file=sys.stderr)
        # Non-fatal: tracker is still updated, just without scores

    # 4. Periodic pattern merge
    merge_interval = int(os.getenv("AS_YOU_MERGE_INTERVAL", "10"))
    counter = SessionCounter(as_you_dir / ".session_count")
    session_num = counter.increment()

    if counter.should_merge(session_num, merge_interval):
        print(f"Running periodic pattern merge (session {session_num})...")

        result = run_python_script(
            REPO_ROOT / "scripts/hooks/pattern_merger.py",
            error_log=error_log,
            timeout=60
        )

        if result["success"]:
            merge_lines = parse_merge_output(result["stdout"])
            if merge_lines:
                print(f"Merged {len(merge_lines)} similar patterns")
                for line in merge_lines:
                    print(line)
            else:
                print("No similar patterns found")
        else:
            print(f"Pattern merge failed (see error log for details)", file=sys.stderr)
    else:
        next_merge = counter.next_merge_session(session_num, merge_interval)
        print(f"Pattern merge skipped (next at session {next_merge})")

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
