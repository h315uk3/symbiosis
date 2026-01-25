#!/usr/bin/env python3
"""Implementation pattern analyzer for active learning data.

Analyzes captured edits to extract:
- Language usage patterns
- Code pattern frequencies
- File type tendencies
- Temporal activity patterns

These patterns feed into the existing scoring pipeline.
"""

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import TypedDict

_PLUGIN_ROOT = Path(__file__).parent.parent.parent
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from as_you.lib.common import AsYouConfig  # noqa: E402

# Maximum files to track per language
_MAX_FILES_PER_LANG = 50


class LanguageStats(TypedDict):
    """Language usage statistics."""

    count: int
    patterns: dict[str, int]
    files: list[str]


class AnalysisResult(TypedDict):
    """Complete analysis result."""

    total_edits: int
    languages: dict[str, LanguageStats]
    patterns: dict[str, int]
    change_types: dict[str, int]
    hourly_activity: dict[int, int]


def load_active_learning_data(claude_dir: Path) -> dict:
    """
    Load active learning data from file.

    Examples:
        >>> import tempfile
        >>> from pathlib import Path
        >>> d = Path(tempfile.mkdtemp())
        >>> load_active_learning_data(d)
        {'prompts': [], 'edits': []}
    """
    data_file = claude_dir / "as_you" / "active_learning.json"
    if data_file.exists():
        try:
            return json.loads(data_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"prompts": [], "edits": []}


def analyze_languages(edits: list[dict]) -> dict[str, LanguageStats]:
    """
    Analyze language usage from edits.

    Examples:
        >>> edits = [
        ...     {"language": "python", "patterns": ["error_handling"], "file_path": "/a.py"},
        ...     {"language": "python", "patterns": ["testing"], "file_path": "/b.py"},
        ...     {"language": "typescript", "patterns": ["async"], "file_path": "/c.ts"},
        ... ]
        >>> result = analyze_languages(edits)
        >>> result["python"]["count"]
        2
        >>> result["python"]["patterns"]["error_handling"]
        1
    """
    lang_stats: dict[str, LanguageStats] = {}

    for edit in edits:
        lang = edit.get("language", "unknown")
        if lang not in lang_stats:
            lang_stats[lang] = LanguageStats(count=0, patterns={}, files=[])

        lang_stats[lang]["count"] += 1

        for pattern in edit.get("patterns", []):
            lang_stats[lang]["patterns"][pattern] = (
                lang_stats[lang]["patterns"].get(pattern, 0) + 1
            )

        file_path = edit.get("file_path", "")
        if file_path and file_path not in lang_stats[lang]["files"]:
            lang_stats[lang]["files"].append(file_path)
            # Keep only recent files per language
            if len(lang_stats[lang]["files"]) > _MAX_FILES_PER_LANG:
                lang_stats[lang]["files"] = lang_stats[lang]["files"][-_MAX_FILES_PER_LANG:]

    return lang_stats


def analyze_patterns(edits: list[dict]) -> dict[str, int]:
    """
    Aggregate pattern frequencies across all edits.

    Examples:
        >>> edits = [
        ...     {"patterns": ["error_handling", "testing"]},
        ...     {"patterns": ["error_handling", "async"]},
        ...     {"patterns": ["testing"]},
        ... ]
        >>> result = analyze_patterns(edits)
        >>> result["error_handling"]
        2
        >>> result["testing"]
        2
        >>> result["async"]
        1
    """
    counter: Counter[str] = Counter()
    for edit in edits:
        counter.update(edit.get("patterns", []))
    return dict(counter.most_common())


def analyze_change_types(edits: list[dict]) -> dict[str, int]:
    """
    Analyze change type distribution.

    Examples:
        >>> edits = [
        ...     {"change_type": "create"},
        ...     {"change_type": "modify"},
        ...     {"change_type": "modify"},
        ... ]
        >>> result = analyze_change_types(edits)
        >>> result["modify"]
        2
        >>> result["create"]
        1
    """
    counter: Counter[str] = Counter()
    for edit in edits:
        change_type = edit.get("change_type", "unknown")
        counter[change_type] += 1
    return dict(counter)


def analyze_temporal(edits: list[dict]) -> dict[int, int]:
    """
    Analyze hourly activity distribution.

    Examples:
        >>> edits = [
        ...     {"timestamp": "2026-01-25T10:30:00Z"},
        ...     {"timestamp": "2026-01-25T10:45:00Z"},
        ...     {"timestamp": "2026-01-25T14:00:00Z"},
        ... ]
        >>> result = analyze_temporal(edits)
        >>> result[10]
        2
        >>> result[14]
        1
    """
    hourly: dict[int, int] = defaultdict(int)
    for edit in edits:
        ts = edit.get("timestamp", "")
        if ts:
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                hourly[dt.hour] += 1
            except ValueError:
                pass
    return dict(hourly)


def analyze_edits(edits: list[dict]) -> AnalysisResult:
    """
    Perform complete analysis of edits.

    Examples:
        >>> edits = [
        ...     {
        ...         "language": "python",
        ...         "patterns": ["error_handling"],
        ...         "change_type": "modify",
        ...         "timestamp": "2026-01-25T10:30:00Z",
        ...         "file_path": "/a.py"
        ...     }
        ... ]
        >>> result = analyze_edits(edits)
        >>> result["total_edits"]
        1
        >>> "python" in result["languages"]
        True
    """
    return AnalysisResult(
        total_edits=len(edits),
        languages=analyze_languages(edits),
        patterns=analyze_patterns(edits),
        change_types=analyze_change_types(edits),
        hourly_activity=analyze_temporal(edits),
    )


def analyze_prompts(prompts: list[dict]) -> dict:
    """
    Analyze prompt patterns.

    Examples:
        >>> prompts = [
        ...     {"intent": "feature", "keywords": ["auth", "login"]},
        ...     {"intent": "fix", "keywords": ["bug", "auth"]},
        ...     {"intent": "feature", "keywords": ["api"]},
        ... ]
        >>> result = analyze_prompts(prompts)
        >>> result["intents"]["feature"]
        2
        >>> result["keywords"]["auth"]
        2
    """
    intents: Counter[str] = Counter()
    keywords: Counter[str] = Counter()

    for prompt in prompts:
        intent = prompt.get("intent", "unknown")
        intents[intent] += 1
        keywords.update(prompt.get("keywords", []))

    return {
        "total_prompts": len(prompts),
        "intents": dict(intents.most_common()),
        "keywords": dict(keywords.most_common(50)),
    }


def get_implementation_summary(config: AsYouConfig) -> dict:
    """
    Get complete implementation analysis summary.

    Returns:
        Dict with edits analysis and prompts analysis
    """
    data = load_active_learning_data(config.claude_dir)

    edits = data.get("edits", [])
    prompts = data.get("prompts", [])

    return {
        "edits": analyze_edits(edits),
        "prompts": analyze_prompts(prompts),
    }


def main() -> None:
    """CLI entry point."""
    config = AsYouConfig.from_environment()
    summary = get_implementation_summary(config)

    print("Implementation Analysis")
    print("=" * 50)

    edits = summary["edits"]
    print(f"\nEdits: {edits['total_edits']}")

    if edits["languages"]:
        print("\nLanguages:")
        for lang, stats in sorted(
            edits["languages"].items(), key=lambda x: x[1]["count"], reverse=True
        ):
            print(f"  {lang}: {stats['count']} edits")
            if stats["patterns"]:
                top_patterns = sorted(
                    stats["patterns"].items(), key=lambda x: x[1], reverse=True
                )[:3]
                print(f"    Top patterns: {', '.join(p[0] for p in top_patterns)}")

    if edits["patterns"]:
        print("\nTop Patterns:")
        for pattern, count in list(edits["patterns"].items())[:10]:
            print(f"  {pattern}: {count}")

    prompts = summary["prompts"]
    print(f"\nPrompts: {prompts['total_prompts']}")

    if prompts["intents"]:
        print("\nIntent Distribution:")
        for intent, count in prompts["intents"].items():
            print(f"  {intent}: {count}")


if __name__ == "__main__":
    import doctest

    if "--test" in sys.argv:
        print("Running implementation_analyzer doctests:")
        results = doctest.testmod(verbose=("-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
