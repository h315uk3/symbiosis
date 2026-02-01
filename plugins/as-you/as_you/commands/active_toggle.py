#!/usr/bin/env python3
"""Active learning toggle command.

Controls automatic capture of prompts and file edits.

Usage:
    python -m as_you.commands.active_toggle on
    python -m as_you.commands.active_toggle off
    python -m as_you.commands.active_toggle status
"""

import json
import sys
from pathlib import Path

# Add plugin to path for imports
_PLUGIN_ROOT = Path(__file__).parent.parent.parent
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from as_you.lib.common import AsYouConfig

# CLI argument count threshold
_MIN_ARGS = 2


def get_state_file(config: AsYouConfig) -> Path:
    """Get path to active learning state file."""
    return config.claude_dir / "as_you" / "active_learning.enabled"


def get_data_file(config: AsYouConfig) -> Path:
    """Get path to active learning data file."""
    return config.claude_dir / "as_you" / "active_learning.json"


def is_enabled(config: AsYouConfig) -> bool:
    """
    Check if active learning is enabled.

    Examples:
        >>> import tempfile
        >>> from pathlib import Path
        >>> config = AsYouConfig(
        ...     workspace_root=Path(tempfile.mkdtemp()),
        ...     claude_dir=Path(tempfile.mkdtemp()),
        ...     tracker_file=Path("/tmp/t.json"),
        ...     archive_dir=Path("/tmp/a"),
        ...     memo_file=Path("/tmp/m.md"),
        ...     settings={},
        ... )
        >>> is_enabled(config)
        False
    """
    return get_state_file(config).exists()


def enable(config: AsYouConfig) -> str:
    """
    Enable active learning.

    Returns:
        Status message
    """
    state_file = get_state_file(config)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.touch()
    return "Active learning enabled"


def disable(config: AsYouConfig) -> str:
    """
    Disable active learning.

    Returns:
        Status message
    """
    state_file = get_state_file(config)
    if state_file.exists():
        state_file.unlink()
    return "Active learning disabled"


def get_status(config: AsYouConfig) -> str:
    """
    Get active learning status with statistics.

    Returns:
        Formatted status string
    """
    enabled = is_enabled(config)
    data_file = get_data_file(config)

    lines = []
    lines.append(f"Active learning: {'ON' if enabled else 'OFF'}")

    if data_file.exists():
        try:
            data = json.loads(data_file.read_text(encoding="utf-8"))
            prompts = len(data.get("prompts", []))
            edits = len(data.get("edits", []))
            lines.append(f"Captured prompts: {prompts}")
            lines.append(f"Captured edits: {edits}")
        except (json.JSONDecodeError, OSError):
            lines.append("Data file: corrupted or unreadable")
    else:
        lines.append("No data captured yet")

    if not enabled:
        lines.append("")
        lines.append("Enable with: /as-you:active on")

    return "\n".join(lines)


def main() -> None:
    """CLI entry point."""
    try:
        config = AsYouConfig.from_environment()
    except RuntimeError:
        # .claude/ directory not found
        # Check if we're in home directory (should not create .claude/ there)
        cwd = Path.cwd()

        if cwd == Path.home():
            print("Error: Cannot run in home directory", file=sys.stderr)
            print(
                "Please run this command from within a project directory",
                file=sys.stderr,
            )
            sys.exit(1)

        # Safe to create .claude/ in current directory
        claude_dir = cwd / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)

        # Retry loading config
        config = AsYouConfig.from_environment()

    if len(sys.argv) < _MIN_ARGS:
        print(get_status(config))
        return

    action = sys.argv[1].lower()

    if action == "on":
        print(enable(config))
    elif action == "off":
        print(disable(config))
    elif action == "status":
        print(get_status(config))
    else:
        print(f"Unknown action: {action}")
        print("Usage: active_toggle [on|off|status]")
        sys.exit(1)


if __name__ == "__main__":
    import doctest

    if "--test" in sys.argv:
        print("Running active_toggle doctests:")
        results = doctest.testmod(verbose=("-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
