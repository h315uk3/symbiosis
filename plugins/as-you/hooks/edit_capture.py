#!/usr/bin/env python3
"""PostToolUse hook for active edit capture.

Captures file edits when active learning is enabled.
Detects language from extension and extracts code patterns.

Hook input (stdin JSON):
    {
        "session_id": "abc123",
        "tool_name": "Edit",
        "tool_input": {
            "file_path": "/path/to/file.py",
            "old_string": "...",
            "new_string": "..."
        },
        "tool_response": {"success": true, ...}
    }
"""

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

from as_you.lib.common import AsYouConfig

HOOK_DIR = Path(__file__).parent.resolve()
PLUGIN_ROOT = HOOK_DIR.parent


class EditEntry(TypedDict):
    """Captured edit entry."""

    id: str
    file_path: str
    tool: str
    timestamp: str
    language: str
    change_type: str
    patterns: list[str]


# Extension to language mapping
LANG_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".rb": "ruby",
    ".php": "php",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".md": "markdown",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".xml": "xml",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".sql": "sql",
}


def is_active_learning_enabled(claude_dir: Path) -> bool:
    """Check if active learning is enabled."""
    return (claude_dir / "as_you" / "active_learning.enabled").exists()


def detect_language(file_path: str) -> str:
    """
    Detect language from file extension.

    Examples:
        >>> detect_language("/src/main.py")
        'python'
        >>> detect_language("/src/app.tsx")
        'typescript'
        >>> detect_language("/config.yaml")
        'yaml'
        >>> detect_language("/unknown.xyz")
        'unknown'
    """
    ext = Path(file_path).suffix.lower()
    return LANG_MAP.get(ext, "unknown")


def detect_change_type(tool: str, content: str | None) -> str:
    """
    Detect change type from tool and content.

    Examples:
        >>> detect_change_type("Write", "new content")
        'create'
        >>> detect_change_type("Edit", "modified")
        'modify'
    """
    if tool == "Write":
        return "create"
    return "modify"


def detect_patterns(content: str, language: str) -> list[str]:
    """
    Detect code patterns in content.

    Examples:
        >>> detect_patterns("try:\\n    x = 1\\nexcept Exception:", "python")
        ['error_handling']
        >>> "testing" in detect_patterns("def test_foo():", "python")
        True
        >>> "class_definition" in detect_patterns("class Foo:\\n    def __init__(self):", "python")
        True
    """
    patterns = []
    content_lower = content.lower()

    # Error handling
    if (language == "python" and ("try:" in content or "except" in content)) or (language in ("javascript", "typescript") and ("try {" in content or "catch" in content)) or (language == "go" and "if err != nil" in content):
        patterns.append("error_handling")

    # Testing
    if any(p in content_lower for p in ["def test_", "it(", "describe(", "test(", "@test"]):
        patterns.append("testing")

    # Class definition
    if (language == "python" and re.search(r"class\s+\w+", content)) or (language in ("javascript", "typescript") and re.search(r"class\s+\w+", content)):
        patterns.append("class_definition")

    # Function definition
    if (language == "python" and re.search(r"def\s+\w+\s*\(", content)) or (language in ("javascript", "typescript") and re.search(r"(function\s+\w+|=>\s*\{)", content)) or (language == "go" and re.search(r"func\s+\w+", content)):
        patterns.append("function_definition")

    # Import/dependency
    if re.search(r"^(import|from|require|use)\s+", content, re.MULTILINE):
        patterns.append("import")

    # Type annotations
    if (language == "python" and re.search(r":\s*(str|int|float|bool|list|dict|Any)", content)) or (language == "typescript" and re.search(r":\s*(string|number|boolean|any)", content)):
        patterns.append("type_annotation")

    # Async patterns
    if any(p in content for p in ["async def", "async function", "await ", "Promise"]):
        patterns.append("async")

    # Logging
    if any(p in content_lower for p in ["console.log", "print(", "log.", "logger."]):
        patterns.append("logging")

    return patterns[:5]  # Limit patterns


def load_active_learning_data(claude_dir: Path) -> dict:
    """Load active learning data from file. Returns default on error."""
    default_data: dict = {"prompts": [], "edits": []}
    data_file = claude_dir / "as_you" / "active_learning.json"

    if not data_file.exists():
        return default_data

    try:
        return json.loads(data_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"edit_capture: corrupted active_learning.json: {e}", file=sys.stderr)
        return default_data
    except OSError as e:
        print(f"edit_capture: cannot read active_learning.json: {e}", file=sys.stderr)
        return default_data


def save_active_learning_data(claude_dir: Path, data: dict) -> None:
    """Save active learning data atomically."""
    data_file = claude_dir / "as_you" / "active_learning.json"
    data_file.parent.mkdir(parents=True, exist_ok=True)
    temp_file = data_file.with_suffix(".tmp")
    temp_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_file.replace(data_file)


def capture_edit(tool_name: str, tool_input: dict) -> EditEntry | None:
    """
    Capture edit with metadata.

    Examples:
        >>> entry = capture_edit("Edit", {"file_path": "/src/main.py", "new_string": "def foo():"})
        >>> entry["language"]
        'python'
        >>> entry["tool"]
        'Edit'
    """
    file_path = tool_input.get("file_path", "")
    if not file_path:
        return None

    # Get content for pattern detection
    content = tool_input.get("new_string", "") or tool_input.get("content", "")
    language = detect_language(file_path)
    change_type = detect_change_type(tool_name, content)
    patterns = detect_patterns(content, language) if content else []

    timestamp = datetime.now(UTC).isoformat()

    return EditEntry(
        id=f"e_{hash(timestamp) % 0xFFFFFF:06x}",
        file_path=file_path,
        tool=tool_name,
        timestamp=timestamp,
        language=language,
        change_type=change_type,
        patterns=patterns,
    )


def main() -> dict:
    """
    Hook entry point.

    Must always return {"continue": True} to not block Claude.
    Errors are logged to stderr for debugging.
    """
    try:
        config = AsYouConfig.from_environment()
    except Exception as e:
        print(f"edit_capture: config error: {e}", file=sys.stderr)
        return {"continue": True}

    if not is_active_learning_enabled(config.claude_dir):
        return {"continue": True}

    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"edit_capture: invalid JSON input: {e}", file=sys.stderr)
        return {"continue": True}

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})
    tool_response = hook_input.get("tool_response", {})

    # Only capture successful operations
    if not tool_response.get("success", True):
        return {"continue": True}

    if tool_name not in ("Edit", "Write"):
        return {"continue": True}

    try:
        entry = capture_edit(tool_name, tool_input)
        if entry:
            data = load_active_learning_data(config.claude_dir)
            data["edits"].append(dict(entry))
            # Keep last 500 edits
            data["edits"] = data["edits"][-500:]
            save_active_learning_data(config.claude_dir, data)
    except Exception as e:
        print(f"edit_capture: capture failed: {e}", file=sys.stderr)

    return {"continue": True}


if __name__ == "__main__":
    import doctest

    if "--test" in sys.argv:
        print("Running edit_capture doctests:")
        results = doctest.testmod(verbose=("-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        result = main()
        print(json.dumps(result))
