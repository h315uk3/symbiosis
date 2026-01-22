#!/usr/bin/env python3
"""Common utilities for As You pattern tracking scripts.

Provides configuration management, tracker I/O, and shared utilities
using Python 3.11+ features (dataclasses, | unions, TypedDict).
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Self, TypedDict


@dataclass(frozen=True)
class AsYouConfig:
    """Immutable configuration with type safety (Python 3.11+ syntax)."""

    project_root: Path
    claude_dir: Path
    tracker_file: Path
    archive_dir: Path
    memo_file: Path
    settings: dict  # Algorithm settings from config/as-you.json

    @classmethod
    def from_environment(cls) -> Self:
        """
        Load configuration from environment variables and config file.

        Replaces duplicated code in 13 files:
            project_root = os.getenv("PROJECT_ROOT", os.getcwd())
            claude_dir = os.getenv("CLAUDE_DIR", ...)

        Returns:
            Immutable configuration object with loaded settings

        Examples:
            >>> config = AsYouConfig.from_environment()
            >>> config.tracker_file.name
            'pattern_tracker.json'
            >>> config.archive_dir.name
            'session_archive'
            >>> "scoring" in config.settings
            True
        """
        project_root = Path(os.getenv("PROJECT_ROOT", os.getcwd()))
        claude_dir = Path(
            os.getenv("CLAUDE_DIR", os.path.join(project_root, ".claude"))
        )

        as_you_dir = claude_dir / "as_you"

        # Load algorithm settings
        settings = load_settings(project_root)

        return cls(
            project_root=project_root,
            claude_dir=claude_dir,
            tracker_file=as_you_dir / "pattern_tracker.json",
            archive_dir=as_you_dir / "session_archive",
            memo_file=as_you_dir / "session_notes.local.md",
            settings=settings,
        )


# Validation constants
_WEIGHT_SUM_MIN = 0.99  # Allow floating point error
_WEIGHT_SUM_MAX = 1.01
_BM25_K1_MIN = 1.2
_BM25_K1_MAX = 2.0
_BM25_B_MIN = 0.0
_BM25_B_MAX = 1.0

# Default settings (fallback if config file not found)
DEFAULT_SETTINGS = {
    "version": 1,
    "scoring": {
        "bm25": {"enabled": True, "k1": 1.5, "b": 0.75},
        "pmi": {"enabled": True, "min_cooccurrence": 2, "window_size": 5},
        "weights": {"bm25": 0.4, "pmi": 0.3, "ebbinghaus": 0.3},
    },
    "memory": {
        "ebbinghaus": {"enabled": True, "base_strength": 1.0, "growth_factor": 0.5},
        "sm2": {"enabled": True, "initial_easiness": 2.5, "min_easiness": 1.3},
    },
    "confidence": {
        "bayesian": {"enabled": True, "prior_mean": 0.5, "prior_variance": 0.04},
        "thompson_sampling": {
            "enabled": True,
            "initial_alpha": 1.0,
            "initial_beta": 1.0,
        },
    },
    "diversity": {
        "shannon_entropy": {
            "enabled": True,
            "context_keys": ["sessions"],
            "aggregation": "mean",
            "max_contexts": 10,
        }
    },
    "promotion": {"threshold": 0.3, "min_observations": 3, "min_confidence": 0.6},
    "categories": [
        "preference",
        "style",
        "process",
        "decision",
        "observation",
        "workflow",
    ],
}


def load_settings(project_root: Path) -> dict:
    """
    Load algorithm settings from config file.

    Searches for config/as-you.json in:
    1. plugins/as-you/config/as-you.json (plugin default)
    2. .claude/as_you/config.json (user override)

    Args:
        project_root: Project root directory

    Returns:
        Settings dictionary (merged with defaults)

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> temp_dir = Path(tempfile.mkdtemp())
        >>> settings = load_settings(temp_dir)
        >>> settings["version"]
        1
        >>> "scoring" in settings
        True
        >>> import shutil
        >>> shutil.rmtree(temp_dir)
    """
    # Try plugin default config
    plugin_config = project_root / "plugins/as-you/config/as-you.json"

    if plugin_config.exists():
        try:
            with open(plugin_config, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"Warning: Failed to load {plugin_config}: {e}")
            print("Using default settings")

    # Fallback to default
    return DEFAULT_SETTINGS.copy()


def merge_settings(default: dict, user: dict) -> dict:
    """
    Merge user settings with defaults.

    Args:
        default: Default settings
        user: User-provided settings

    Returns:
        Merged settings dictionary

    Examples:
        >>> default = {"a": 1, "b": {"c": 2, "d": 3}}
        >>> user = {"b": {"c": 99}}
        >>> merged = merge_settings(default, user)
        >>> merged["a"]
        1
        >>> merged["b"]["c"]
        99
        >>> merged["b"]["d"]
        3
    """
    result = default.copy()
    for key, value in user.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = merge_settings(result[key], value)
        else:
            result[key] = value
    return result


def validate_settings(settings: dict) -> bool:
    """
    Validate settings structure and ranges.

    Args:
        settings: Settings dictionary to validate

    Returns:
        True if valid

    Raises:
        ValueError: If settings are invalid

    Examples:
        >>> validate_settings(DEFAULT_SETTINGS)
        True
        >>> validate_settings({"version": 2})
        Traceback (most recent call last):
            ...
        ValueError: Invalid config version
    """
    # Version check
    if settings.get("version") != 1:
        msg = "Invalid config version"
        raise ValueError(msg)

    # Weights sum check
    if "scoring" in settings and "weights" in settings["scoring"]:
        weights = settings["scoring"]["weights"]
        total_weight = sum(weights.values())
        if not (_WEIGHT_SUM_MIN <= total_weight <= _WEIGHT_SUM_MAX):
            msg = f"Weight sum must be ~1.0, got {total_weight}"
            raise ValueError(msg)

    # BM25 range checks
    if "scoring" in settings and "bm25" in settings["scoring"]:
        bm25 = settings["scoring"]["bm25"]
        k1 = bm25.get("k1", 1.5)
        b = bm25.get("b", 0.75)
        if not (_BM25_K1_MIN <= k1 <= _BM25_K1_MAX):
            msg = f"BM25 k1 out of range: {k1}"
            raise ValueError(msg)
        if not (_BM25_B_MIN <= b <= _BM25_B_MAX):
            msg = f"BM25 b out of range: {b}"
            raise ValueError(msg)

    return True


class TrackerData(TypedDict, total=False):
    """Type definition for tracker JSON structure."""

    patterns: dict[str, dict]
    promotion_candidates: list[str]
    cooccurrences: list[dict]


def load_tracker(tracker_file: Path) -> TrackerData:
    """
    Load pattern tracker with unified error handling.

    Consolidates 3 different implementations:
    - pattern_updater.py:14-17 (simple)
    - frequency_tracker.py:14-53 (complex with defaults)
    - context_extractor.py:14-42 (medium complexity)

    Args:
        tracker_file: Path to pattern_tracker.json

    Returns:
        Tracker data with guaranteed keys

    Raises:
        IOError: If file cannot be read

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> with tempfile.NamedTemporaryFile(
        ...     mode="w", suffix=".json", delete=False
        ... ) as f:
        ...     _ = f.write('{"patterns": {}, "promotion_candidates": []}')
        ...     temp_path = Path(f.name)
        >>> data = load_tracker(temp_path)
        >>> "patterns" in data
        True
        >>> "cooccurrences" in data
        True
        >>> temp_path.unlink()
    """
    default_data: TrackerData = {
        "patterns": {},
        "promotion_candidates": [],
        "cooccurrences": [],
    }

    if not tracker_file.exists() or tracker_file.stat().st_size == 0:
        return default_data

    try:
        with open(tracker_file, encoding="utf-8") as f:
            data = json.load(f)

        # Ensure all required keys exist
        for key in default_data:
            if key not in data:
                data[key] = default_data[key]

    except (OSError, json.JSONDecodeError) as e:
        # Python 3.11+: Add context to exception
        e.add_note(f"Failed to load tracker file: {tracker_file}")
        e.add_note("File may be corrupted. Consider restoring from backup.")
        raise
    else:
        return data


def save_tracker(tracker_file: Path, data: TrackerData) -> None:
    """
    Save tracker data atomically.

    Args:
        tracker_file: Path to pattern_tracker.json
        data: Tracker data to save

    Raises:
        IOError: If file cannot be written

    Examples:
        >>> from pathlib import Path
        >>> import tempfile, json
        >>> temp_dir = Path(tempfile.mkdtemp())
        >>> tracker_file = temp_dir / "pattern_tracker.json"
        >>> data: TrackerData = {"patterns": {"test": {"count": 5}}}
        >>> save_tracker(tracker_file, data)
        >>> tracker_file.exists()
        True
        >>> loaded = json.loads(tracker_file.read_text())
        >>> loaded["patterns"]["test"]["count"]
        5
        >>> import shutil
        >>> shutil.rmtree(temp_dir)
    """
    try:
        tracker_file.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write: write to temp file, then rename
        temp_file = tracker_file.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        temp_file.replace(tracker_file)

    except OSError as e:
        e.add_note(f"Failed to save tracker file: {tracker_file}")
        raise


def get_archive_files(archive_dir: Path) -> list[Path]:
    """
    Get all markdown archive files sorted by date.

    Args:
        archive_dir: Path to session archive directory

    Returns:
        List of archive file paths (sorted, newest first)

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> temp_dir = Path(tempfile.mkdtemp())
        >>> (temp_dir / "2024-01-01.md").write_text("old")
        3
        >>> (temp_dir / "2024-01-02.md").write_text("new")
        3
        >>> files = get_archive_files(temp_dir)
        >>> len(files)
        2
        >>> files[0].name > files[1].name  # Newest first
        True
        >>> import shutil
        >>> shutil.rmtree(temp_dir)
    """
    if not archive_dir.exists():
        return []

    return sorted(
        archive_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True
    )


if __name__ == "__main__":
    import doctest
    import sys

    # Check if running doctests
    if "--test" in sys.argv or "-v" in sys.argv:
        print("Running common utilities doctests:")
        results = doctest.testmod(verbose=("--verbose" in sys.argv or "-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        # Demo usage
        config = AsYouConfig.from_environment()
        print("Configuration loaded:")
        print(f"  Tracker file: {config.tracker_file}")
        print(f"  Archive dir: {config.archive_dir}")
