#!/usr/bin/env python3
"""
Skill creator for pattern-to-skill promotion.

Creates Claude Code skills in the proper location with correct format.
Called from /as-you:memory dashboard after deep analysis.
"""

import json
import sys
from pathlib import Path


def create_skill(
    skill_name: str,
    description: str,
    content: str,
    context: str = "fork",
    allowed_tools: list[str] | None = None,
) -> dict:
    """
    Create a Claude Code skill in plugins/as-you/skills/.

    Args:
        skill_name: Skill directory name (e.g., "python-project-setup")
        description: Short description for frontmatter
        content: Main skill content (markdown)
        context: Claude Code context (default: "fork")
        allowed_tools: List of allowed tools (default: None)

    Returns:
        Status dict with success flag and skill_path

    Examples:
        >>> # Test with missing plugins directory
        >>> import os
        >>> cwd = os.getcwd()
        >>> os.chdir("/tmp")
        >>> result = create_skill(
        ...     skill_name="test-skill",
        ...     description="Test skill",
        ...     content="# Test\\n\\nContent here",
        ... )
        >>> result["success"]
        False
        >>> "not found" in result["error"]
        True
        >>> os.chdir(cwd)
    """
    # Locate plugins/as-you/skills directory
    plugins_dir = Path("plugins/as-you/skills")

    if not plugins_dir.exists():
        return {
            "success": False,
            "error": f"Skills directory not found: {plugins_dir}",
        }

    # Create skill directory
    skill_dir = plugins_dir / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)

    # Generate frontmatter
    frontmatter_lines = [
        "---",
        f'description: "{description}"',
    ]

    if context:
        frontmatter_lines.append(f"context: {context}")

    if allowed_tools:
        tools_str = ", ".join(allowed_tools)
        frontmatter_lines.append(f"allowed-tools: [{tools_str}]")

    frontmatter_lines.append("---")
    frontmatter = "\n".join(frontmatter_lines)

    # Write SKILL.md
    skill_file = skill_dir / "SKILL.md"
    skill_content = f"{frontmatter}\n\n{content}"

    try:
        skill_file.write_text(skill_content, encoding="utf-8")
    except OSError as e:
        return {
            "success": False,
            "error": f"Failed to write skill file: {e}",
        }

    return {
        "success": True,
        "skill_path": str(skill_file),
        "skill_name": skill_name,
    }


def main():
    """Main entry point for skill creator CLI."""
    min_argc = 4  # program name + skill_name + description + content
    if len(sys.argv) < min_argc or sys.argv[1] in ["-h", "--help"]:
        print("Usage: python3 -m as_you.commands.skill_creator <name> <desc> <content>")
        print(
            "       python3 -m as_you.commands.skill_creator test-skill 'Test' 'Content'"
        )
        sys.exit(0)

    skill_name = sys.argv[1]
    description = sys.argv[2]
    content = sys.argv[3]

    # Optional: context and allowed_tools from environment or args
    context_idx = 4
    tools_idx = 5
    context = sys.argv[context_idx] if len(sys.argv) > context_idx else "fork"
    allowed_tools = (
        sys.argv[tools_idx].split(",") if len(sys.argv) > tools_idx else None
    )

    result = create_skill(skill_name, description, content, context, allowed_tools)

    # Output JSON result
    print(json.dumps(result, indent=2))

    if not result["success"]:
        sys.exit(1)


if __name__ == "__main__":
    import doctest

    if "--test" in sys.argv:
        print("Running skill_creator doctests:")
        results = doctest.testmod(verbose=("-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
