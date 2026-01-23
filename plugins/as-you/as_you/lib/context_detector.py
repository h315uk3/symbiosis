#!/usr/bin/env python3
"""
Project context detector for habit search.

Phase 3 of Issue #83: Habit Extraction and Automatic Application.
"""

import re
from collections import Counter
from pathlib import Path


def detect_project_type(project_root: Path) -> list[str]:
    """
    Detect project type from file markers.

    Args:
        project_root: Project root directory

    Returns:
        List of project type tags

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> temp_dir = Path(tempfile.mkdtemp())
        >>> _ = (temp_dir / "package.json").write_text("{}")
        >>> tags = detect_project_type(temp_dir)
        >>> "javascript" in tags or "typescript" in tags
        True
        >>> import shutil
        >>> shutil.rmtree(temp_dir)
    """
    tags = []

    # Python project
    if (project_root / "pyproject.toml").exists() or (
        project_root / "setup.py"
    ).exists():
        tags.append("python")

    # JavaScript/TypeScript project
    if (project_root / "package.json").exists():
        # Check for TypeScript
        if (project_root / "tsconfig.json").exists():
            tags.append("typescript")
        else:
            tags.append("javascript")

    # Rust project
    if (project_root / "Cargo.toml").exists():
        tags.append("rust")

    # Go project
    if (project_root / "go.mod").exists():
        tags.append("go")

    # Deno project
    if (project_root / "deno.json").exists() or (project_root / "deno.jsonc").exists():
        tags.append("deno")

    # Web project (HTML/CSS)
    if list(project_root.glob("*.html")) or (project_root / "public").exists():
        tags.append("web")

    # Git repository
    if (project_root / ".git").exists():
        tags.append("git")

    return tags


def extract_keywords_from_files(
    project_root: Path, max_files: int = 10, max_keywords: int = 20
) -> list[str]:
    """
    Extract keywords from recently modified files.

    Args:
        project_root: Project root directory
        max_files: Maximum files to scan (default: 10)
        max_keywords: Maximum keywords to extract (default: 20)

    Returns:
        List of keywords (most common first)

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> temp_dir = Path(tempfile.mkdtemp())
        >>> _ = (temp_dir / "test.py").write_text("def test(): pass\\ntest()\\ntest()")
        >>> keywords = extract_keywords_from_files(temp_dir, max_files=1)
        >>> "test" in keywords
        True
        >>> import shutil
        >>> shutil.rmtree(temp_dir)
    """
    # Exclude patterns
    exclude_patterns = {
        "__pycache__",
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "dist",
        "build",
        ".pytest_cache",
        ".mypy_cache",
        "target",
    }

    # Collect recent files
    files = []
    for ext in ["*.py", "*.js", "*.ts", "*.rs", "*.go", "*.md"]:
        for file in project_root.rglob(ext):
            # Skip excluded directories
            if any(excluded in file.parts for excluded in exclude_patterns):
                continue
            files.append(file)

    # Sort by modification time (most recent first)
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    files = files[:max_files]

    # Extract words
    word_counter = Counter()
    for file in files:
        try:
            content = file.read_text(encoding="utf-8")
            # Extract identifiers (alphanumeric + underscore)
            words = re.findall(r"\b[a-z_][a-z0-9_]{2,}\b", content.lower())
            word_counter.update(words)
        except (OSError, UnicodeDecodeError):
            continue

    # Filter stopwords and common code words
    stopwords = {
        "def",
        "class",
        "return",
        "import",
        "from",
        "for",
        "while",
        "if",
        "else",
        "elif",
        "try",
        "except",
        "with",
        "as",
        "in",
        "is",
        "not",
        "and",
        "or",
        "self",
        "none",
        "true",
        "false",
        "null",
        "undefined",
        "var",
        "let",
        "const",
        "function",
        "async",
        "await",
        "pub",
        "fn",
        "impl",
        "struct",
        "enum",
        "match",
        "mut",
        "ref",
        "type",
    }

    # Get most common non-stopword keywords
    keywords = [
        word
        for word, _ in word_counter.most_common(max_keywords * 2)
        if word not in stopwords
    ]

    return keywords[:max_keywords]


def build_context_query(tags: list[str], keywords: list[str]) -> str:
    """
    Build search query from tags and keywords.

    Args:
        tags: Project type tags
        keywords: Extracted keywords

    Returns:
        Search query string

    Examples:
        >>> build_context_query(["python", "git"], ["test", "config"])
        'python git test config'
        >>> build_context_query([], ["test"])
        'test'
        >>> build_context_query(["python"], [])
        'python'
    """
    # Combine tags and top keywords
    query_parts = tags + keywords[:10]  # Limit keywords to top 10
    return " ".join(query_parts)


if __name__ == "__main__":
    import doctest
    import sys

    if "--test" in sys.argv:
        print("Running context_detector doctests:")
        results = doctest.testmod(verbose=("-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        # Standalone execution - detect current project context
        import os

        project_root = Path(os.getenv("PROJECT_ROOT", os.getcwd()))

        print("Detecting project context...")
        print(f"Root: {project_root}")
        print("-" * 50)

        tags = detect_project_type(project_root)
        print(f"Project types: {', '.join(tags) if tags else 'unknown'}")

        keywords = extract_keywords_from_files(project_root)
        print(f"Top keywords: {', '.join(keywords[:10])}")

        query = build_context_query(tags, keywords)
        print(f"\nGenerated query: '{query}'")
