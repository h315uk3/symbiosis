#!/usr/bin/env python3
"""UserPromptSubmit hook for passive prompt capture.

Captures user prompts when active learning is enabled.
Extracts keywords and classifies intent heuristically.

Hook input (stdin JSON):
    {
        "session_id": "abc123",
        "prompt": "user prompt text",
        ...
    }
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

HOOK_DIR = Path(__file__).parent.resolve()
REPO_ROOT = HOOK_DIR.parent
sys.path.insert(0, str(REPO_ROOT))

from as_you.lib.common import AsYouConfig


class PromptEntry(TypedDict):
    """Captured prompt entry."""

    id: str
    text: str
    timestamp: str
    intent: str
    keywords: list[str]


def is_active_learning_enabled(claude_dir: Path) -> bool:
    """
    Check if active learning is enabled.

    Examples:
        >>> import tempfile
        >>> from pathlib import Path
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     d = Path(tmpdir)
        ...     assert is_active_learning_enabled(d) == False
        ...     (d / "as_you").mkdir()
        ...     (d / "as_you" / "active_learning.enabled").touch()
        ...     assert is_active_learning_enabled(d) == True
    """
    return (claude_dir / "as_you" / "active_learning.enabled").exists()


def tokenize(text: str) -> list[str]:
    """
    Tokenize text into lowercase words.

    Examples:
        >>> tokenize("Add authentication feature")
        ['add', 'authentication', 'feature']
        >>> tokenize("fix: resolve bug #123")
        ['fix', 'resolve', 'bug', '123']
    """
    return re.findall(r"\w+", text.lower())


def classify_intent(text: str) -> str:
    """
    Classify prompt intent heuristically.

    Examples:
        >>> classify_intent("Add user authentication")
        'feature'
        >>> classify_intent("Fix the login bug")
        'fix'
        >>> classify_intent("What does this function do?")
        'question'
        >>> classify_intent("Refactor the module")
        'refactor'
    """
    t = text.lower()

    if "?" in text or any(t.startswith(q) for q in ["what", "how", "why", "where", "can"]):
        return "question"
    if any(w in t for w in ["add", "create", "implement", "new", "build"]):
        return "feature"
    if any(w in t for w in ["fix", "bug", "issue", "error", "broken"]):
        return "fix"
    if any(w in t for w in ["refactor", "restructure", "reorganize", "clean"]):
        return "refactor"
    if any(w in t for w in ["update", "improve", "enhance", "optimize"]):
        return "enhancement"
    if any(w in t for w in ["remove", "delete"]):
        return "removal"
    if any(w in t for w in ["test", "verify", "check"]):
        return "testing"
    if any(w in t for w in ["document", "docs", "readme"]):
        return "documentation"

    return "general"


def load_active_learning_data(claude_dir: Path) -> dict:
    """Load active learning data from file. Returns default on error."""
    default_data: dict = {"prompts": [], "edits": []}
    data_file = claude_dir / "as_you" / "active_learning.json"

    if not data_file.exists():
        return default_data

    try:
        return json.loads(data_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"prompt_capture: corrupted active_learning.json: {e}", file=sys.stderr)
        return default_data
    except OSError as e:
        print(f"prompt_capture: cannot read active_learning.json: {e}", file=sys.stderr)
        return default_data


def save_active_learning_data(claude_dir: Path, data: dict) -> None:
    """Save active learning data atomically."""
    data_file = claude_dir / "as_you" / "active_learning.json"
    data_file.parent.mkdir(parents=True, exist_ok=True)
    temp_file = data_file.with_suffix(".tmp")
    temp_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_file.replace(data_file)


def capture_prompt(prompt: str) -> PromptEntry | None:
    """
    Capture prompt with metadata.

    Examples:
        >>> entry = capture_prompt("Add authentication feature")
        >>> entry["intent"]
        'feature'
        >>> "authentication" in entry["keywords"]
        True
        >>> capture_prompt("hi") is None  # Too short
        True
    """
    if len(prompt.strip()) < 10:
        return None

    timestamp = datetime.now(timezone.utc).isoformat()
    keywords = tokenize(prompt)

    stop_words = {"the", "a", "an", "is", "are", "to", "for", "of", "in", "on", "it", "this", "that"}
    keywords = [k for k in keywords if k not in stop_words and len(k) > 2]

    return PromptEntry(
        id=f"p_{hash(timestamp) % 0xFFFFFF:06x}",
        text=prompt[:500],  # Limit length
        timestamp=timestamp,
        intent=classify_intent(prompt),
        keywords=keywords[:20],
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
        print(f"prompt_capture: config error: {e}", file=sys.stderr)
        return {"continue": True}

    if not is_active_learning_enabled(config.claude_dir):
        return {"continue": True}

    try:
        hook_input = json.load(sys.stdin)
        prompt = hook_input.get("prompt", "")
    except (json.JSONDecodeError, KeyError) as e:
        print(f"prompt_capture: invalid input: {e}", file=sys.stderr)
        return {"continue": True}

    if not prompt:
        return {"continue": True}

    try:
        entry = capture_prompt(prompt)
        if entry:
            data = load_active_learning_data(config.claude_dir)
            data["prompts"].append(dict(entry))
            # Keep last 200 prompts
            data["prompts"] = data["prompts"][-200:]
            save_active_learning_data(config.claude_dir, data)
    except Exception as e:
        print(f"prompt_capture: capture failed: {e}", file=sys.stderr)

    return {"continue": True}


if __name__ == "__main__":
    import doctest

    if "--test" in sys.argv:
        print("Running prompt_capture doctests:")
        results = doctest.testmod(verbose=("-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        result = main()
        print(json.dumps(result))
