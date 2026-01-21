#!/usr/bin/env python3
"""
Setup permissions for with-me plugin.

Adds 9 required permissions to .claude/settings.local.json:
- 1 PYTHONPATH environment variable
- 6 CLI commands (init, next-question, evaluate-question, update-with-computation, status, complete)
- 1 Skill (requirement-analysis for post-session analysis)
- 1 Read permission (session data)
"""

import json
import sys
from pathlib import Path

# Required permissions for with-me plugin
REQUIRED_PERMISSIONS = [
    # Environment setup
    'Bash(export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}")',
    # CLI commands
    "Bash(python3 -m with_me.cli.session init*)",
    "Bash(python3 -m with_me.cli.session next-question*)",
    "Bash(python3 -m with_me.cli.session evaluate-question*)",
    "Bash(python3 -m with_me.cli.session update-with-computation*)",
    "Bash(python3 -m with_me.cli.session status*)",
    "Bash(python3 -m with_me.cli.session complete*)",
    # Skills (for post-session analysis only)
    "Skill(with-me:requirement-analysis)",
    # Read permissions for session data
    "Read(.claude/with_me/sessions/*.json)",
]


def get_settings_file() -> Path:
    """
    Get path to settings.local.json.

    Returns:
        Path to .claude/settings.local.json in current directory

    Examples:
        >>> path = get_settings_file()
        >>> path.name
        'settings.local.json'
        >>> path.parent.name
        '.claude'
    """
    return Path.cwd() / ".claude" / "settings.local.json"


def load_settings(settings_file: Path) -> dict:
    """
    Load settings with default structure.

    Args:
        settings_file: Path to settings.local.json

    Returns:
        Settings dictionary with permissions.allow list

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> with tempfile.NamedTemporaryFile(
        ...     mode="w", suffix=".json", delete=False
        ... ) as f:
        ...     _ = f.write('{"permissions": {"allow": ["test"]}}')
        ...     temp_path = Path(f.name)
        >>> settings = load_settings(temp_path)
        >>> settings["permissions"]["allow"]
        ['test']
        >>> temp_path.unlink()
    """
    if not settings_file.exists():
        return {"permissions": {"allow": []}}

    try:
        with open(settings_file, encoding="utf-8") as f:
            settings = json.load(f)

        # Ensure structure exists
        if "permissions" not in settings:
            settings["permissions"] = {}
        if "allow" not in settings["permissions"]:
            settings["permissions"]["allow"] = []

        return settings
    except (json.JSONDecodeError, OSError) as e:
        print(
            json.dumps(
                {"error": f"Failed to parse settings file: {e}"}, ensure_ascii=False
            ),
            file=sys.stderr,
        )
        sys.exit(1)


def save_settings(settings_file: Path, settings: dict) -> None:
    """
    Save settings atomically.

    Uses temp file + rename for atomicity.

    Args:
        settings_file: Path to settings.local.json
        settings: Settings dictionary to save

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> import shutil
        >>> temp_dir = Path(tempfile.mkdtemp())
        >>> settings_file = temp_dir / ".claude" / "settings.local.json"
        >>> settings = {"permissions": {"allow": ["test"]}}
        >>> save_settings(settings_file, settings)
        >>> settings_file.exists()
        True
        >>> shutil.rmtree(temp_dir)
    """
    # Ensure parent directory exists
    settings_file.parent.mkdir(parents=True, exist_ok=True)

    # Atomic write
    temp_file = settings_file.with_suffix(".tmp")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
            f.write("\n")  # Trailing newline
        temp_file.replace(settings_file)
    except Exception as e:
        if temp_file.exists():
            temp_file.unlink()
        print(
            json.dumps(
                {"error": f"Failed to save settings: {e}"}, ensure_ascii=False
            ),
            file=sys.stderr,
        )
        sys.exit(1)


def setup_permissions() -> None:
    """
    Setup permissions for with-me plugin.

    Adds required permissions to .claude/settings.local.json.
    Deduplicates existing permissions.
    """
    settings_file = get_settings_file()

    # Load current settings
    settings = load_settings(settings_file)
    current_permissions = settings["permissions"]["allow"]

    # Add required permissions (deduplicate)
    updated_permissions = list(dict.fromkeys(current_permissions + REQUIRED_PERMISSIONS))

    # Count new permissions
    new_count = len(updated_permissions) - len(current_permissions)

    # Save if changed
    if new_count > 0:
        settings["permissions"]["allow"] = updated_permissions
        save_settings(settings_file, settings)

        print(
            json.dumps(
                {
                    "status": "updated",
                    "added": new_count,
                    "total": len(updated_permissions),
                    "file": str(settings_file),
                },
                ensure_ascii=False,
            )
        )
    else:
        print(
            json.dumps(
                {
                    "status": "already_configured",
                    "total": len(current_permissions),
                    "file": str(settings_file),
                },
                ensure_ascii=False,
            )
        )


def main() -> None:
    """CLI entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Run doctests
        import doctest

        print("Running doctests...")
        result = doctest.testmod()
        if result.failed == 0:
            print("✓ All doctests passed")
        else:
            print(f"✗ {result.failed} doctest(s) failed")
            sys.exit(1)
    else:
        setup_permissions()


if __name__ == "__main__":
    main()
