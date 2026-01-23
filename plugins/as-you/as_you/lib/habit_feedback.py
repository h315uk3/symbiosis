#!/usr/bin/env python3
"""
Habit feedback and Bayesian confidence update.

Phase 4 of Issue #83: Habit Extraction and Automatic Application.
"""

from datetime import datetime
from pathlib import Path

from as_you.lib.bayesian_learning import update_bayesian_state
from as_you.lib.common import load_tracker, save_tracker
from as_you.lib.note_indexer import calculate_note_freshness


def track_habit_usage(note: dict) -> dict:
    """
    Track habit usage by incrementing counters and updating timestamp.

    Args:
        note: Note dict

    Returns:
        Updated note dict

    Examples:
        >>> note = {"use_count": 0, "last_used": None, "id": "n_001"}
        >>> updated = track_habit_usage(note)
        >>> updated["use_count"]
        1
        >>> updated["last_used"] is not None
        True
    """
    note["use_count"] = note.get("use_count", 0) + 1
    note["last_used"] = datetime.now().isoformat() + "Z"
    return note


def update_habit_confidence(
    note: dict, feedback: str, observation_variance: float = 0.01
) -> dict:
    """
    Update habit confidence using Bayesian updating.

    Args:
        note: Note dict with confidence field
        feedback: "success", "partial", or "failure"
        observation_variance: Observation uncertainty (default: 0.01)

    Returns:
        Updated note dict

    Examples:
        >>> note = {
        ...     "confidence": {"mean": 0.5, "variance": 0.04},
        ...     "success_count": 0,
        ...     "failure_count": 0,
        ... }
        >>> updated = update_habit_confidence(note.copy(), "success")
        >>> updated["confidence"]["mean"] > 0.5
        True
        >>> updated["success_count"]
        1
        >>> note2 = {
        ...     "confidence": {"mean": 0.5, "variance": 0.04},
        ...     "success_count": 0,
        ...     "failure_count": 0,
        ... }
        >>> updated2 = update_habit_confidence(note2, "failure")
        >>> updated2["confidence"]["mean"] < 0.5
        True
        >>> updated2["failure_count"]
        1
    """
    # Map feedback to observation score
    observation_map = {"success": 0.8, "partial": 0.5, "failure": 0.2}

    if feedback not in observation_map:
        msg = f"Invalid feedback: {feedback}"
        raise ValueError(msg)

    observation = observation_map[feedback]

    # Get current confidence
    prior_mean = note["confidence"]["mean"]
    prior_variance = note["confidence"]["variance"]

    # Update using Bayesian inference
    posterior = update_bayesian_state(
        prior_mean, prior_variance, observation, observation_variance
    )

    # Update note
    note["confidence"]["mean"] = posterior.mean
    note["confidence"]["variance"] = posterior.variance

    # Update feedback counters
    if feedback == "success":
        note["success_count"] = note.get("success_count", 0) + 1
    elif feedback == "failure":
        note["failure_count"] = note.get("failure_count", 0) + 1

    return note


def calculate_freshness_for_all(
    notes: list[dict], half_life_days: int = 30
) -> list[dict]:
    """
    Recalculate freshness for all notes.

    Args:
        notes: List of note dicts
        half_life_days: Freshness half-life in days (default: 30)

    Returns:
        Updated notes with freshness field

    Examples:
        >>> from datetime import datetime, timedelta
        >>> notes = [
        ...     {"id": "n_001", "last_used": None},
        ...     {
        ...         "id": "n_002",
        ...         "last_used": (datetime.now() - timedelta(days=1)).isoformat() + "Z",
        ...     },
        ... ]
        >>> updated = calculate_freshness_for_all(notes, half_life_days=30)
        >>> len(updated)
        2
        >>> 0.0 <= updated[0]["freshness"] <= 1.0
        True
    """
    for note in notes:
        freshness = calculate_note_freshness(note.get("last_used"), half_life_days)
        note["freshness"] = freshness

    return notes


def apply_feedback(
    tracker_file: Path,
    note_id: str,
    feedback: str,
    half_life_days: int = 30,
) -> dict:
    """
    Apply feedback to a specific note and save tracker.

    Args:
        tracker_file: Path to pattern_tracker.json
        note_id: Note ID to update
        feedback: "success", "partial", or "failure"
        half_life_days: Freshness half-life (default: 30)

    Returns:
        Status dict

    Examples:
        >>> from pathlib import Path
        >>> import tempfile, json
        >>> temp_file = Path(tempfile.mktemp(suffix=".json"))
        >>> data = {
        ...     "notes": [
        ...         {
        ...             "id": "n_001",
        ...             "text": "Test note",
        ...             "confidence": {"mean": 0.5, "variance": 0.04},
        ...             "last_used": None,
        ...             "use_count": 0,
        ...             "success_count": 0,
        ...             "failure_count": 0,
        ...         }
        ...     ],
        ...     "patterns": {},
        ...     "promotion_candidates": [],
        ...     "cooccurrences": [],
        ... }
        >>> _ = temp_file.write_text(json.dumps(data))
        >>> result = apply_feedback(temp_file, "n_001", "success")
        >>> result["success"]
        True
        >>> tracker = json.loads(temp_file.read_text())
        >>> tracker["notes"][0]["confidence"]["mean"] > 0.5
        True
        >>> temp_file.unlink()
    """
    # Load tracker
    tracker = load_tracker(tracker_file)
    notes = tracker.get("notes", [])

    # Find note
    note = next((n for n in notes if n["id"] == note_id), None)
    if not note:
        return {"success": False, "error": f"Note not found: {note_id}"}

    # Track usage
    track_habit_usage(note)

    # Update confidence
    try:
        update_habit_confidence(note, feedback)
    except ValueError as e:
        return {"success": False, "error": str(e)}

    # Recalculate freshness for all notes
    calculate_freshness_for_all(notes, half_life_days)

    # Save tracker
    save_tracker(tracker_file, tracker)

    return {
        "success": True,
        "note_id": note_id,
        "new_confidence": note["confidence"]["mean"],
        "new_variance": note["confidence"]["variance"],
        "use_count": note["use_count"],
    }


if __name__ == "__main__":
    import doctest
    import sys

    if "--test" in sys.argv:
        print("Running habit_feedback doctests:")
        results = doctest.testmod(verbose=("-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        print("Usage: Import this module or run with --test for doctests")
