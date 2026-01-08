#!/usr/bin/env python3
"""
Analyze promotion candidates from pattern_tracker.json.
Replaces suggest-promotions.sh with testable Python implementation.
"""

import json
import re
import sys
from pathlib import Path

# Add scripts/ to Python path
scripts_dir = Path(__file__).parent.parent
sys.path.insert(0, str(scripts_dir))

from lib.common import AsYouConfig, load_tracker


def determine_type(contexts: list[str]) -> str:
    """
    Determine if pattern should be promoted to agent or skill.

    Agent keywords indicate action-oriented patterns (analyze, generate, etc.)
    Skill keywords indicate knowledge-oriented patterns.

    Args:
        contexts: List of context strings where pattern was used

    Returns:
        "agent" or "skill"

    Examples:
        >>> determine_type(["analyze the code", "generate report"])
        'agent'
        >>> determine_type(["Python syntax rules", "best practices"])
        'skill'
        >>> determine_type([])
        'skill'
    """
    agent_keywords = [
        "analyze",
        "generate",
        "validate",
        "check",
        "review",
        "test",
        "build",
        "deploy",
        "run",
        "execute",
        "create",
        "update",
        "delete",
        "fix",
    ]

    contexts_text = " ".join(contexts).lower()

    for keyword in agent_keywords:
        if keyword in contexts_text:
            return "agent"

    return "skill"


def extract_description(contexts: list[str], max_length: int = 100) -> str:
    """
    Extract description from contexts (first 3, cleaned).

    Args:
        contexts: List of context strings
        max_length: Maximum description length

    Returns:
        Cleaned description string

    Examples:
        >>> extract_description(["[12:34] Test message", "Another context"])
        'Test message Another context'
        >>> extract_description([])
        ''
        >>> len(extract_description(["x" * 200]))
        100
    """
    if not contexts:
        return ""

    # Take first 3 contexts
    sample = contexts[:3]

    # Clean timestamps and extra spaces
    cleaned = []
    for ctx in sample:
        # Remove timestamps [HH:MM]
        ctx = re.sub(r"\[\d{2}:\d{2}\]\s*", "", ctx)
        # Normalize spaces
        ctx = re.sub(r"\s+", " ", ctx).strip()
        if ctx:
            cleaned.append(ctx)

    description = " ".join(cleaned)
    return description[:max_length]


def to_kebab_case(text: str) -> str:
    """
    Convert text to kebab-case.

    Examples:
        >>> to_kebab_case("Hello World")
        'hello-world'
        >>> to_kebab_case("Python_Programming")
        'python-programming'
        >>> to_kebab_case("API-Design")
        'api-design'
    """
    # Convert to lowercase
    text = text.lower()
    # Replace underscores and spaces with hyphens
    text = re.sub(r"[_\s]+", "-", text)
    # Remove non-alphanumeric except hyphens
    text = re.sub(r"[^a-z0-9-]", "", text)
    # Remove duplicate hyphens
    text = re.sub(r"-+", "-", text)
    # Strip leading/trailing hyphens
    return text.strip("-")


def analyze_promotions(tracker_file: Path) -> list[dict]:
    """
    Analyze promotion candidates and suggest type/name/description.

    Args:
        tracker_file: Path to pattern_tracker.json

    Returns:
        List of promotion suggestions with metadata
    """
    try:
        data = load_tracker(tracker_file)
        candidates = data.get("promotion_candidates", [])
        patterns = data.get("patterns", {})
    except (json.JSONDecodeError, IOError):
        # Corrupted file - no candidates to show
        return []

    if not candidates:
        return []

    suggestions = []

    for candidate in candidates:
        pattern = candidate
        pattern_data = patterns.get(pattern, {})

        contexts = pattern_data.get("contexts", [])
        count = pattern_data.get("count", 0)
        sessions = pattern_data.get("sessions", [])

        # Determine type based on contexts
        promotion_type = determine_type(contexts)

        # Generate suggested name
        suggested_name = to_kebab_case(pattern)

        # Generate description
        description = extract_description(contexts)

        suggestions.append(
            {
                "type": promotion_type,
                "pattern": pattern,
                "suggested_name": suggested_name,
                "count": count,
                "sessions": sessions,
                "contexts": contexts,
                "suggested_description": description,
                "composite_score": pattern_data.get("composite_score", 0),
            }
        )

    return suggestions


def get_promotion_summary(tracker_file: Path) -> dict:
    """
    Get summary of promotion candidates.

    Args:
        tracker_file: Path to pattern_tracker.json

    Returns:
        Dictionary with counts and top candidate

    Examples:
        >>> # Mock example (actual usage requires real file)
        >>> summary = {
        ...     "total": 5,
        ...     "skills": 3,
        ...     "agents": 2,
        ...     "top_pattern": "python-testing",
        ...     "top_type": "skill"
        ... }
        >>> summary["total"]
        5
    """
    suggestions = analyze_promotions(tracker_file)

    if not suggestions:
        return {
            "total": 0,
            "skills": 0,
            "agents": 0,
            "top_pattern": None,
            "top_type": None,
        }

    skill_count = len([s for s in suggestions if s["type"] == "skill"])
    agent_count = len([s for s in suggestions if s["type"] == "agent"])

    return {
        "total": len(suggestions),
        "skills": skill_count,
        "agents": agent_count,
        "top_pattern": suggestions[0]["pattern"],
        "top_type": suggestions[0]["type"],
    }


def main():
    """CLI entry point."""
    config = AsYouConfig.from_environment()
    tracker_file = config.tracker_file

    # Get mode from arguments
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"

    if mode == "summary":
        # Output summary only (for session-start.sh)
        summary = get_promotion_summary(tracker_file)
        print(json.dumps(summary, ensure_ascii=False))
    elif mode == "summary-line":
        # Output as space-separated line for easy shell parsing
        summary = get_promotion_summary(tracker_file)
        print(
            f"{summary['total']} {summary['skills']} {summary['agents']} "
            f"{summary['top_pattern'] or 'null'} {summary['top_type'] or 'null'}"
        )
    else:
        # Output full suggestions (replaces suggest-promotions.sh)
        suggestions = analyze_promotions(tracker_file)
        print(json.dumps(suggestions, ensure_ascii=False, indent=0))


if __name__ == "__main__":
    import doctest

    # Check if running doctests
    if "--test" in sys.argv or "-v" in sys.argv:
        print("Running promotion analyzer doctests:")
        results = doctest.testmod(verbose=("--verbose" in sys.argv or "-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
