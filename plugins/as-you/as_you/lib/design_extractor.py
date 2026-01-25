#!/usr/bin/env python3
"""Design pattern extractor for active learning.

Detects common design patterns from code edits:
- Singleton, Factory, Builder patterns
- Dependency injection patterns
- Error handling styles
- Configuration patterns

Uses heuristics (no external AST libraries beyond stdlib).
"""

import re
import sys
from pathlib import Path
from typing import TypedDict

_PLUGIN_ROOT = Path(__file__).parent.parent.parent
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

# Minimum thresholds for pattern detection
_MIN_TYPED_PARAMS = 2  # Minimum typed params to suggest dependency injection
_MIN_FLUENT_METHODS = 2  # Minimum return self methods for builder pattern
_MIN_OBSERVER_EVIDENCE = 2  # Minimum evidence items for observer pattern


class DesignPattern(TypedDict):
    """Detected design pattern."""

    name: str
    confidence: float  # 0.0-1.0
    evidence: list[str]


def detect_singleton(content: str, language: str) -> DesignPattern | None:
    """
    Detect singleton pattern.

    Examples:
        >>> code = '''
        ... class Database:
        ...     _instance = None
        ...     def __new__(cls):
        ...         if cls._instance is None:
        ...             cls._instance = super().__new__(cls)
        ...         return cls._instance
        ... '''
        >>> result = detect_singleton(code, "python")
        >>> result is not None
        True
        >>> result["name"]
        'singleton'
    """
    evidence = []

    if language == "python":
        if "_instance" in content and "__new__" in content:
            evidence.append("_instance with __new__")
        if re.search(r"@staticmethod\s+def\s+get_instance", content):
            evidence.append("get_instance staticmethod")

    elif language in ("javascript", "typescript"):
        if re.search(r"static\s+instance", content, re.IGNORECASE):
            evidence.append("static instance property")
        if re.search(r"getInstance\s*\(", content):
            evidence.append("getInstance method")

    if evidence:
        return DesignPattern(
            name="singleton",
            confidence=min(len(evidence) * 0.5, 1.0),
            evidence=evidence,
        )
    return None


def detect_factory(content: str, language: str) -> DesignPattern | None:
    """
    Detect factory pattern.

    Examples:
        >>> code = '''
        ... class AnimalFactory:
        ...     def create_animal(self, animal_type):
        ...         if animal_type == "dog":
        ...             return Dog()
        ...         return Cat()
        ... '''
        >>> result = detect_factory(code, "python")
        >>> result is not None
        True
        >>> result["name"]
        'factory'
    """
    evidence = []

    # Class name contains Factory
    if re.search(r"class\s+\w*Factory", content):
        evidence.append("Factory class name")

    # Method named create_* or build_*
    if re.search(r"def\s+(create|build|make)_\w+", content):
        evidence.append("create/build method")

    # Returns different types based on condition
    if re.search(r"if.*:\s*\n\s*return\s+\w+\(\)", content):
        evidence.append("conditional return of instances")

    if evidence:
        return DesignPattern(
            name="factory",
            confidence=min(len(evidence) * 0.4, 1.0),
            evidence=evidence,
        )
    return None


def detect_dependency_injection(content: str, language: str) -> DesignPattern | None:
    """
    Detect dependency injection pattern.

    Examples:
        >>> code = '''
        ... class UserService:
        ...     def __init__(self, repository: UserRepository, logger: Logger):
        ...         self.repository = repository
        ...         self.logger = logger
        ... '''
        >>> result = detect_dependency_injection(code, "python")
        >>> result is not None
        True
        >>> result["name"]
        'dependency_injection'
    """
    evidence = []

    if language == "python":
        # Constructor with typed dependencies
        if re.search(r"def\s+__init__\s*\(self,\s*\w+:\s*\w+", content):
            # Multiple typed parameters
            init_match = re.search(r"def\s+__init__\s*\([^)]+\)", content)
            if init_match:
                params = init_match.group(0)
                typed_params = len(re.findall(r"\w+:\s*\w+", params))
                if typed_params >= _MIN_TYPED_PARAMS:
                    evidence.append(f"{typed_params} typed constructor params")

        # Self assignment of dependencies
        if re.search(r"self\.\w+\s*=\s*\w+\s*$", content, re.MULTILINE):
            evidence.append("dependency assignment")

    elif language in ("javascript", "typescript"):
        # Constructor injection
        if re.search(r"constructor\s*\([^)]*private\s+\w+", content):
            evidence.append("private constructor injection")

    if evidence:
        return DesignPattern(
            name="dependency_injection",
            confidence=min(len(evidence) * 0.5, 1.0),
            evidence=evidence,
        )
    return None


def detect_builder(content: str, language: str) -> DesignPattern | None:
    """
    Detect builder pattern.

    Examples:
        >>> code = '''
        ... class QueryBuilder:
        ...     def select(self, fields):
        ...         self._fields = fields
        ...         return self
        ...     def where(self, condition):
        ...         self._condition = condition
        ...         return self
        ...     def build(self):
        ...         return Query(self._fields, self._condition)
        ... '''
        >>> result = detect_builder(code, "python")
        >>> result is not None
        True
        >>> result["name"]
        'builder'
    """
    evidence = []

    # Class name contains Builder
    if re.search(r"class\s+\w*Builder", content):
        evidence.append("Builder class name")

    # Methods returning self (fluent interface)
    return_self_count = len(re.findall(r"return\s+self\s*$", content, re.MULTILINE))
    if return_self_count >= _MIN_FLUENT_METHODS:
        evidence.append(f"{return_self_count} fluent methods")

    # build() method
    if re.search(r"def\s+build\s*\(", content):
        evidence.append("build method")

    if evidence:
        return DesignPattern(
            name="builder",
            confidence=min(len(evidence) * 0.4, 1.0),
            evidence=evidence,
        )
    return None


def detect_observer(content: str, language: str) -> DesignPattern | None:
    """
    Detect observer pattern.

    Examples:
        >>> code = '''
        ... class EventEmitter:
        ...     def __init__(self):
        ...         self._listeners = []
        ...     def subscribe(self, listener):
        ...         self._listeners.append(listener)
        ...     def notify(self):
        ...         for listener in self._listeners:
        ...             listener.update()
        ... '''
        >>> result = detect_observer(code, "python")
        >>> result is not None
        True
    """
    evidence = []

    # Listener/observer collection
    if re.search(r"(listeners|observers|subscribers)\s*=\s*\[\]", content):
        evidence.append("observer collection")

    # Subscribe/unsubscribe methods
    if re.search(r"def\s+(subscribe|add_listener|attach)", content):
        evidence.append("subscribe method")

    # Notify/emit methods
    if re.search(r"def\s+(notify|emit|dispatch)", content):
        evidence.append("notify method")

    if len(evidence) >= _MIN_OBSERVER_EVIDENCE:
        return DesignPattern(
            name="observer",
            confidence=min(len(evidence) * 0.4, 1.0),
            evidence=evidence,
        )
    return None


def extract_design_patterns(content: str, language: str) -> list[DesignPattern]:
    """
    Extract all detected design patterns from content.

    Examples:
        >>> code = '''
        ... class Config:
        ...     _instance = None
        ...     def __new__(cls):
        ...         if cls._instance is None:
        ...             cls._instance = super().__new__(cls)
        ...         return cls._instance
        ... '''
        >>> patterns = extract_design_patterns(code, "python")
        >>> len(patterns) >= 1
        True
        >>> any(p["name"] == "singleton" for p in patterns)
        True
    """
    detectors = [
        detect_singleton,
        detect_factory,
        detect_dependency_injection,
        detect_builder,
        detect_observer,
    ]

    patterns = []
    for detector in detectors:
        result = detector(content, language)
        if result:
            patterns.append(result)

    return patterns


def main() -> None:
    """CLI entry point for testing."""
    print("Design pattern extractor")
    print("Use extract_design_patterns(content, language) in code")


if __name__ == "__main__":
    import doctest

    if "--test" in sys.argv:
        print("Running design_extractor doctests:")
        results = doctest.testmod(verbose=("-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
