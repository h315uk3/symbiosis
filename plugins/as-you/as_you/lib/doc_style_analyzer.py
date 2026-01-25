#!/usr/bin/env python3
"""Documentation style analyzer for active learning.

Detects documentation conventions from code edits:
- Docstring formats (Google, NumPy, Sphinx, reStructuredText)
- Comment styles (inline, block, TODO conventions)
- Type annotation preferences
- README/markdown patterns

Uses heuristics to identify user's preferred documentation style.
"""

import re
import sys
from collections import Counter
from pathlib import Path
from typing import TypedDict

_PLUGIN_ROOT = Path(__file__).parent.parent.parent
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))


class DocStyle(TypedDict):
    """Detected documentation style."""

    style: str
    confidence: float
    indicators: list[str]


def detect_google_docstring(content: str) -> DocStyle | None:
    """
    Detect Google-style docstrings.

    Examples:
        >>> code = '''
        ... def foo(x):
        ...     \"\"\"Do something.
        ...
        ...     Args:
        ...         x: The input value.
        ...
        ...     Returns:
        ...         The result.
        ...     \"\"\"
        ...     return x
        ... '''
        >>> result = detect_google_docstring(code)
        >>> result is not None
        True
        >>> result["style"]
        'google'
    """
    indicators = []

    # Google style sections
    if re.search(r"^\s*Args:\s*$", content, re.MULTILINE):
        indicators.append("Args section")
    if re.search(r"^\s*Returns:\s*$", content, re.MULTILINE):
        indicators.append("Returns section")
    if re.search(r"^\s*Raises:\s*$", content, re.MULTILINE):
        indicators.append("Raises section")
    if re.search(r"^\s*Examples:\s*$", content, re.MULTILINE):
        indicators.append("Examples section")
    if re.search(r"^\s*Note:\s*$", content, re.MULTILINE):
        indicators.append("Note section")

    if indicators:
        return DocStyle(
            style="google",
            confidence=min(len(indicators) * 0.25, 1.0),
            indicators=indicators,
        )
    return None


def detect_numpy_docstring(content: str) -> DocStyle | None:
    """
    Detect NumPy-style docstrings.

    Examples:
        >>> code = '''
        ... def foo(x):
        ...     \"\"\"Do something.
        ...
        ...     Parameters
        ...     ----------
        ...     x : int
        ...         The input value.
        ...
        ...     Returns
        ...     -------
        ...     int
        ...         The result.
        ...     \"\"\"
        ...     return x
        ... '''
        >>> result = detect_numpy_docstring(code)
        >>> result is not None
        True
        >>> result["style"]
        'numpy'
    """
    indicators = []

    # NumPy style underlined sections
    if re.search(r"Parameters\s*\n\s*-{5,}", content):
        indicators.append("Parameters section")
    if re.search(r"Returns\s*\n\s*-{5,}", content):
        indicators.append("Returns section")
    if re.search(r"Raises\s*\n\s*-{5,}", content):
        indicators.append("Raises section")
    if re.search(r"Examples\s*\n\s*-{5,}", content):
        indicators.append("Examples section")

    if indicators:
        return DocStyle(
            style="numpy",
            confidence=min(len(indicators) * 0.3, 1.0),
            indicators=indicators,
        )
    return None


def detect_sphinx_docstring(content: str) -> DocStyle | None:
    """
    Detect Sphinx-style docstrings.

    Examples:
        >>> code = '''
        ... def foo(x):
        ...     \"\"\"Do something.
        ...
        ...     :param x: The input value.
        ...     :type x: int
        ...     :returns: The result.
        ...     :rtype: int
        ...     \"\"\"
        ...     return x
        ... '''
        >>> result = detect_sphinx_docstring(code)
        >>> result is not None
        True
        >>> result["style"]
        'sphinx'
    """
    indicators = []

    # Sphinx style :param: and :returns:
    if re.search(r":param\s+\w+:", content):
        indicators.append(":param directive")
    if re.search(r":type\s+\w+:", content):
        indicators.append(":type directive")
    if re.search(r":returns?:", content):
        indicators.append(":returns directive")
    if re.search(r":rtype:", content):
        indicators.append(":rtype directive")
    if re.search(r":raises?\s+\w+:", content):
        indicators.append(":raises directive")

    if indicators:
        return DocStyle(
            style="sphinx",
            confidence=min(len(indicators) * 0.25, 1.0),
            indicators=indicators,
        )
    return None


def detect_jsdoc_style(content: str) -> DocStyle | None:
    """
    Detect JSDoc-style documentation.

    Examples:
        >>> code = '''
        ... /**
        ...  * Do something.
        ...  * @param {number} x - The input value.
        ...  * @returns {number} The result.
        ...  */
        ... function foo(x) { return x; }
        ... '''
        >>> result = detect_jsdoc_style(code)
        >>> result is not None
        True
        >>> result["style"]
        'jsdoc'
    """
    indicators = []

    # JSDoc tags
    if re.search(r"@param\s+\{", content):
        indicators.append("@param tag")
    if re.search(r"@returns?\s+\{", content):
        indicators.append("@returns tag")
    if re.search(r"@type\s+\{", content):
        indicators.append("@type tag")
    if re.search(r"@typedef", content):
        indicators.append("@typedef tag")

    # /** */ block comments
    if re.search(r"/\*\*[\s\S]*?\*/", content):
        indicators.append("/** */ block")

    if indicators:
        return DocStyle(
            style="jsdoc",
            confidence=min(len(indicators) * 0.25, 1.0),
            indicators=indicators,
        )
    return None


def detect_comment_conventions(content: str) -> dict[str, int]:
    """
    Detect comment conventions in code.

    Examples:
        >>> code = '''
        ... # TODO: fix this
        ... # FIXME: broken
        ... # NOTE: important
        ... x = 1  # inline comment
        ... '''
        >>> result = detect_comment_conventions(code)
        >>> result["TODO"] >= 1
        True
        >>> result["inline_comments"] >= 1
        True
    """
    conventions: Counter[str] = Counter()

    # TODO/FIXME/NOTE comments
    conventions["TODO"] = len(re.findall(r"#\s*TODO", content, re.IGNORECASE))
    conventions["FIXME"] = len(re.findall(r"#\s*FIXME", content, re.IGNORECASE))
    conventions["NOTE"] = len(re.findall(r"#\s*NOTE", content, re.IGNORECASE))
    conventions["XXX"] = len(re.findall(r"#\s*XXX", content, re.IGNORECASE))

    # Inline comments (code # comment)
    conventions["inline_comments"] = len(
        re.findall(r"\S+\s+#\s+\S", content)
    )

    # Block comments
    conventions["block_comments"] = len(
        re.findall(r"^#[^!]", content, re.MULTILINE)
    )

    return dict(conventions)


def detect_type_annotation_style(content: str, language: str) -> dict:
    """
    Detect type annotation preferences.

    Examples:
        >>> code = '''
        ... def foo(x: int, y: str) -> bool:
        ...     items: list[str] = []
        ...     return True
        ... '''
        >>> result = detect_type_annotation_style(code, "python")
        >>> result["uses_annotations"]
        True
        >>> result["modern_generics"]
        True
    """
    result = {
        "uses_annotations": False,
        "modern_generics": False,  # list[str] vs List[str]
        "return_annotations": False,
        "variable_annotations": False,
    }

    if language == "python":
        # Function parameter annotations
        if re.search(r"def\s+\w+\s*\([^)]*:\s*\w+", content):
            result["uses_annotations"] = True

        # Return type annotations
        if re.search(r"\)\s*->\s*\w+", content):
            result["return_annotations"] = True
            result["uses_annotations"] = True

        # Variable annotations
        if re.search(r"^\s*\w+\s*:\s*\w+\s*=", content, re.MULTILINE):
            result["variable_annotations"] = True
            result["uses_annotations"] = True

        # Modern generics (Python 3.9+)
        if re.search(r":\s*(list|dict|set|tuple)\[", content):
            result["modern_generics"] = True

        # Legacy generics (typing.List, etc.)
        if re.search(r":\s*(List|Dict|Set|Tuple)\[", content):
            result["modern_generics"] = False

    return result


def analyze_doc_style(content: str, language: str) -> dict:
    """
    Analyze documentation style of content.

    Examples:
        >>> code = '''
        ... def foo(x):
        ...     \"\"\"Do something.
        ...
        ...     Args:
        ...         x: The input.
        ...
        ...     Returns:
        ...         The result.
        ...     \"\"\"
        ...     return x
        ... '''
        >>> result = analyze_doc_style(code, "python")
        >>> result["docstring_style"]["style"]
        'google'
    """
    # Detect docstring style
    docstring_detectors = [
        detect_google_docstring,
        detect_numpy_docstring,
        detect_sphinx_docstring,
        detect_jsdoc_style,
    ]

    docstring_style = None
    for detector in docstring_detectors:
        result = detector(content)
        if result:
            if docstring_style is None or result["confidence"] > docstring_style["confidence"]:
                docstring_style = result

    return {
        "docstring_style": docstring_style,
        "comment_conventions": detect_comment_conventions(content),
        "type_annotations": detect_type_annotation_style(content, language),
    }


def main() -> None:
    """CLI entry point for testing."""
    print("Documentation style analyzer")
    print("Use analyze_doc_style(content, language) in code")


if __name__ == "__main__":
    import doctest

    if "--test" in sys.argv:
        print("Running doc_style_analyzer doctests:")
        results = doctest.testmod(verbose=("-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
