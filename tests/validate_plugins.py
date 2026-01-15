#!/usr/bin/env python3
"""
Validate plugin configuration files.

Checks JSON syntax for plugin.json and hooks.json in all plugins.
"""

import json
import sys
from pathlib import Path


def validate_file(file_path: Path) -> bool:
    """
    Validate a JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        True if valid, False otherwise

    Examples:
        >>> from tempfile import NamedTemporaryFile
        >>> with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        ...     f.write('{"valid": true}')
        ...     temp_path = Path(f.name)
        15
        >>> validate_file(temp_path)
        True
        >>> temp_path.unlink()
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            json.load(f)
        return True
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"  ✗ {file_path.name}: {e}", file=sys.stderr)
        return False


def main() -> int:
    """
    Main entry point for plugin validation.

    Returns:
        Exit code: 0 if all valid, 1 if any fail
    """
    root = Path(__file__).parent.parent
    plugins_dir = root / "plugins"

    if not plugins_dir.exists():
        print("✗ plugins/ directory not found")
        return 1

    all_valid = True

    # Find all plugins
    for plugin_dir in sorted(plugins_dir.iterdir()):
        if not plugin_dir.is_dir():
            continue

        print(f"Validating {plugin_dir.name}...")

        # Check plugin.json
        plugin_json = plugin_dir / ".claude-plugin" / "plugin.json"
        if plugin_json.exists():
            if validate_file(plugin_json):
                print(f"  ✓ plugin.json is valid")
            else:
                all_valid = False
        else:
            print(f"  - plugin.json not found (skipping)")

        # Check hooks.json if hooks directory exists
        hooks_json = plugin_dir / "hooks" / "hooks.json"
        if hooks_json.exists():
            if validate_file(hooks_json):
                print(f"  ✓ hooks.json is valid")
            else:
                all_valid = False

    if all_valid:
        print("\n✓ All configuration files are valid")
        return 0
    else:
        print("\n✗ Some configuration files have errors")
        return 1


if __name__ == "__main__":
    sys.exit(main())
