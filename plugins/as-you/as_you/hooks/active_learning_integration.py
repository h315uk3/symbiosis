#!/usr/bin/env python3
"""Active learning integration hook for SessionEnd.

Integrates captured prompts and edits into pattern_tracker.json.
Called from session_end.py as part of the processing pipeline.
"""

import json
import sys
from collections import Counter
from pathlib import Path

_PLUGIN_ROOT = Path(__file__).parent.parent.parent
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from as_you.lib.common import AsYouConfig, load_tracker, save_tracker


def load_active_learning_data(claude_dir: Path) -> dict:
    """Load active learning data from file."""
    data_file = claude_dir / "as_you" / "active_learning.json"
    if data_file.exists():
        try:
            return json.loads(data_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"prompts": [], "edits": []}


def save_active_learning_data(claude_dir: Path, data: dict) -> None:
    """
    Save active learning data to file.

    Examples:
        >>> import tempfile
        >>> with tempfile.TemporaryDirectory() as tmp:
        ...     tmp_path = Path(tmp)
        ...     as_you_dir = tmp_path / "as_you"
        ...     as_you_dir.mkdir()
        ...     data = {"prompts": [{"text": "test", "integrated": True}], "edits": []}
        ...     save_active_learning_data(tmp_path, data)
        ...     loaded = load_active_learning_data(tmp_path)
        ...     loaded["prompts"][0]["integrated"]
        True
    """
    data_file = claude_dir / "as_you" / "active_learning.json"
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def extract_keywords_from_prompts(prompts: list[dict]) -> Counter[str]:
    """
    Extract keyword frequencies from prompts.

    Examples:
        >>> prompts = [
        ...     {"keywords": ["auth", "login"]},
        ...     {"keywords": ["auth", "api"]},
        ... ]
        >>> result = extract_keywords_from_prompts(prompts)
        >>> result["auth"]
        2
        >>> result["login"]
        1
    """
    counter: Counter[str] = Counter()
    for prompt in prompts:
        counter.update(prompt.get("keywords", []))
    return counter


def extract_patterns_from_edits(edits: list[dict]) -> Counter[str]:
    """
    Extract pattern frequencies from edits.

    Examples:
        >>> edits = [
        ...     {"patterns": ["error_handling", "testing"]},
        ...     {"patterns": ["error_handling"]},
        ... ]
        >>> result = extract_patterns_from_edits(edits)
        >>> result["error_handling"]
        2
        >>> result["testing"]
        1
    """
    counter: Counter[str] = Counter()
    for edit in edits:
        counter.update(edit.get("patterns", []))
    return counter


def extract_intents(prompts: list[dict]) -> Counter[str]:
    """
    Extract intent frequencies from prompts.

    Examples:
        >>> prompts = [
        ...     {"intent": "feature"},
        ...     {"intent": "fix"},
        ...     {"intent": "feature"},
        ... ]
        >>> result = extract_intents(prompts)
        >>> result["feature"]
        2
    """
    counter: Counter[str] = Counter()
    for prompt in prompts:
        intent = prompt.get("intent", "unknown")
        counter[intent] += 1
    return counter


def extract_languages(edits: list[dict]) -> Counter[str]:
    """
    Extract language frequencies from edits.

    Examples:
        >>> edits = [
        ...     {"language": "python"},
        ...     {"language": "typescript"},
        ...     {"language": "python"},
        ... ]
        >>> result = extract_languages(edits)
        >>> result["python"]
        2
    """
    counter: Counter[str] = Counter()
    for edit in edits:
        lang = edit.get("language", "unknown")
        counter[lang] += 1
    return counter


def integrate_active_learning(config: AsYouConfig) -> dict:
    """
    Integrate active learning data into pattern tracker.

    Only processes items that have not been integrated yet (integrated != True).
    After integration, marks all items with integrated: True to prevent
    duplicate counting in future sessions.

    Returns:
        Summary of integration results
    """
    al_data = load_active_learning_data(config.claude_dir)

    # Filter out already-integrated items
    all_prompts = al_data.get("prompts", [])
    all_edits = al_data.get("edits", [])
    prompts = [p for p in all_prompts if not p.get("integrated")]
    edits = [e for e in all_edits if not e.get("integrated")]

    if not prompts and not edits:
        return {"status": "no_data"}

    tracker = load_tracker(config.tracker_file)

    # Initialize active_learning section if not present
    if "active_learning" not in tracker:
        tracker["active_learning"] = {
            "keywords": {},
            "code_patterns": {},
            "intents": {},
            "languages": {},
        }

    al_section = tracker["active_learning"]

    # Merge keywords
    keywords = extract_keywords_from_prompts(prompts)
    for kw, count in keywords.items():
        al_section["keywords"][kw] = al_section["keywords"].get(kw, 0) + count

    # Merge code patterns
    code_patterns = extract_patterns_from_edits(edits)
    for pat, count in code_patterns.items():
        al_section["code_patterns"][pat] = (
            al_section["code_patterns"].get(pat, 0) + count
        )

    # Merge intents
    intents = extract_intents(prompts)
    for intent, count in intents.items():
        al_section["intents"][intent] = al_section["intents"].get(intent, 0) + count

    # Merge languages
    languages = extract_languages(edits)
    for lang, count in languages.items():
        al_section["languages"][lang] = al_section["languages"].get(lang, 0) + count

    # Save updated tracker
    save_tracker(config.tracker_file, tracker)

    # Mark all items as integrated to prevent duplicate counting
    for p in all_prompts:
        p["integrated"] = True
    for e in all_edits:
        e["integrated"] = True

    # Save updated active learning data with integration flags
    save_active_learning_data(config.claude_dir, al_data)

    # Disable active learning after integration (auto-off at session end)
    enabled_file = config.claude_dir / "as_you" / "active_learning.enabled"
    if enabled_file.exists():
        enabled_file.unlink()

    return {
        "status": "success",
        "prompts_processed": len(prompts),
        "edits_processed": len(edits),
        "keywords_added": len(keywords),
        "patterns_added": len(code_patterns),
    }


def main() -> None:
    """CLI entry point."""
    config = AsYouConfig.from_environment()
    result = integrate_active_learning(config)

    if result["status"] == "no_data":
        print("No active learning data to integrate")
    else:
        print(
            f"Integrated {result['prompts_processed']} prompts, {result['edits_processed']} edits"
        )


if __name__ == "__main__":
    import doctest

    if "--test" in sys.argv:
        print("Running active_learning_integration doctests:")
        results = doctest.testmod(verbose=("-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
