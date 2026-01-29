#!/usr/bin/env python3
"""
Initialize skill usage statistics.
Replaces init-usage-stats.sh with testable Python implementation.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

from as_you.lib.common import AsYouConfig


def load_stats(stats_file: Path) -> dict:
    """
    Load usage stats, initialize if needed.

    Args:
        stats_file: Path to skill-usage-stats.json

    Returns:
        Stats data dictionary

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> with tempfile.NamedTemporaryFile(
        ...     mode="w", suffix=".json", delete=False
        ... ) as f:
        ...     _ = f.write('{"skills": {}, "agents": {}}')
        ...     temp_path = Path(f.name)
        >>> stats = load_stats(temp_path)
        >>> "skills" in stats and "agents" in stats
        True
        >>> temp_path.unlink()
    """
    if not stats_file.exists() or stats_file.stat().st_size == 0:
        return {"skills": {}, "agents": {}, "last_updated": ""}

    try:
        with open(stats_file, encoding="utf-8") as f:
            data = json.load(f)

        # Ensure required keys exist
        if "skills" not in data:
            data["skills"] = {}
        if "agents" not in data:
            data["agents"] = {}
        if "last_updated" not in data:
            data["last_updated"] = ""

    except (OSError, json.JSONDecodeError):
        return {"skills": {}, "agents": {}, "last_updated": ""}
    else:
        return data


def scan_skills(skills_dir: Path, stats: dict, current_date: str) -> int:
    """
    Scan skills directory and add to stats.

    Args:
        skills_dir: Path to skills directory
        stats: Stats dictionary (modified in place)
        current_date: Current date (YYYY-MM-DD)

    Returns:
        Number of skills found

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> skills_dir = Path(tempfile.mkdtemp())
        >>> (skills_dir / "test-skill").mkdir()
        >>> stats = {"skills": {}}
        >>> count = scan_skills(skills_dir, stats, "2026-01-06")
        >>> count
        1
        >>> "test-skill" in stats["skills"]
        True
        >>> import shutil
        >>> shutil.rmtree(skills_dir)
    """
    if not skills_dir.exists():
        return 0

    count = 0
    for skill_path in skills_dir.iterdir():
        if not skill_path.is_dir():
            continue

        skill_name = skill_path.name

        # Add to stats if not exists
        if skill_name not in stats["skills"]:
            stats["skills"][skill_name] = {
                "created": current_date,
                "invocations": 0,
                "last_used": None,
                "effectiveness": "unknown",
            }
            count += 1

    return count


def scan_agents(agents_dir: Path, stats: dict, current_date: str) -> int:
    """
    Scan agents directory and add to stats.

    Args:
        agents_dir: Path to agents directory
        stats: Stats dictionary (modified in place)
        current_date: Current date (YYYY-MM-DD)

    Returns:
        Number of agents found

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> agents_dir = Path(tempfile.mkdtemp())
        >>> _ = (agents_dir / "test-agent.md").write_text("# Test Agent")
        >>> stats = {"agents": {}}
        >>> count = scan_agents(agents_dir, stats, "2026-01-06")
        >>> count
        1
        >>> "test-agent" in stats["agents"]
        True
        >>> import shutil
        >>> shutil.rmtree(agents_dir)
    """
    if not agents_dir.exists():
        return 0

    # System agents to skip
    system_agents = {"memory-analyzer", "component-generator", "promotion-reviewer"}

    count = 0
    for agent_file in agents_dir.glob("*.md"):
        if not agent_file.is_file():
            continue

        agent_name = agent_file.stem

        # Skip system agents
        if agent_name in system_agents:
            continue

        # Add to stats if not exists
        if agent_name not in stats["agents"]:
            stats["agents"][agent_name] = {
                "created": current_date,
                "invocations": 0,
                "last_used": None,
                "effectiveness": "unknown",
            }
            count += 1

    return count


def init_usage_stats(
    stats_file: Path, skills_dir: Path, agents_dir: Path
) -> dict[str, int]:
    """
    Initialize usage statistics for skills and agents.

    Args:
        stats_file: Path to skill-usage-stats.json
        skills_dir: Path to skills directory
        agents_dir: Path to agents directory

    Returns:
        Dictionary with skill_count and agent_count

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> temp_dir = Path(tempfile.mkdtemp())
        >>> stats_file = temp_dir / "stats.json"
        >>> skills_dir = temp_dir / "skills"
        >>> agents_dir = temp_dir / "agents"
        >>> skills_dir.mkdir()
        >>> agents_dir.mkdir()
        >>> result = init_usage_stats(stats_file, skills_dir, agents_dir)
        >>> result["skill_count"]
        0
        >>> import shutil
        >>> shutil.rmtree(temp_dir)
    """
    # Load existing stats
    stats = load_stats(stats_file)

    # Get current date
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Scan skills
    scan_skills(skills_dir, stats, current_date)

    # Scan agents
    scan_agents(agents_dir, stats, current_date)

    # Update last_updated timestamp
    stats["last_updated"] = current_date

    # Save stats
    stats_file.parent.mkdir(parents=True, exist_ok=True)
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    return {
        "skill_count": len(stats["skills"]),
        "agent_count": len(stats["agents"]),
    }


def main():
    """CLI entry point."""
    config = AsYouConfig.from_environment()
    stats_file = config.claude_dir / "as_you" / "skill-usage-stats.json"
    skills_dir = config.workspace_root / "skills"
    agents_dir = config.workspace_root / "agents"

    # Initialize stats
    result = init_usage_stats(stats_file, skills_dir, agents_dir)

    print(
        f"Usage stats initialized: {result['skill_count']} skills, {result['agent_count']} agents"
    )


if __name__ == "__main__":
    import doctest

    # Check if running doctests
    if "--test" in sys.argv or "-v" in sys.argv:
        print("Running usage stats initializer doctests:")
        results = doctest.testmod(verbose=("--verbose" in sys.argv or "-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
