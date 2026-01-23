#!/usr/bin/env python3
"""
Note indexer for habit extraction system.

Extracts notes from session archives, deduplicates, and clusters similar notes.
Phase 1 of Issue #83: Habit Extraction and Automatic Application.
"""

import math
import re
from datetime import datetime
from pathlib import Path

from as_you.lib.common import AsYouConfig, load_tracker, save_tracker
from as_you.lib.levenshtein import levenshtein_distance


def calculate_similarity(s1: str, s2: str) -> float:
    """
    Calculate normalized similarity between two strings (0.0 to 1.0).

    Uses Levenshtein distance normalized by maximum possible distance.

    Args:
        s1: First string
        s2: Second string

    Returns:
        Similarity score (1.0 = identical, 0.0 = completely different)

    Examples:
        >>> calculate_similarity("kitten", "sitting")
        0.5714285714285714
        >>> calculate_similarity("same", "same")
        1.0
        >>> calculate_similarity("abc", "xyz")
        0.0
        >>> calculate_similarity("", "")
        1.0
    """
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    max_len = max(len(s1), len(s2))
    distance = levenshtein_distance(s1, s2)
    return 1.0 - (distance / max_len)


def extract_notes_from_archive(archive_file: Path) -> list[dict]:
    """
    Extract notes from a single archive file.

    Args:
        archive_file: Path to archive markdown file (YYYY-MM-DD.md)

    Returns:
        List of note dicts with text, timestamp, session_date, source_archive

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> with tempfile.NamedTemporaryFile(
        ...     mode="w", suffix=".md", delete=False, encoding="utf-8"
        ... ) as f:
        ...     _ = f.write("[14:30] First note\\n[14:35] Second note\\n")
        ...     temp_path = Path(f.name)
        >>> notes = extract_notes_from_archive(temp_path)
        >>> len(notes)
        2
        >>> notes[0]["text"]
        'First note'
        >>> "timestamp" in notes[0]
        True
        >>> temp_path.unlink()
    """
    if not archive_file.exists():
        return []

    try:
        content = archive_file.read_text(encoding="utf-8")
    except OSError:
        return []

    # Extract session date from filename (YYYY-MM-DD.md)
    session_date = archive_file.stem

    # Parse notes: [HH:MM] Note text
    note_pattern = re.compile(r"\[(\d{2}:\d{2})\]\s*(.+)")
    notes = []

    for line in content.split("\n"):
        match = note_pattern.match(line.strip())
        if match:
            time_str, text = match.groups()
            # Combine session_date and time for full timestamp
            timestamp = f"{session_date}T{time_str}:00Z"
            notes.append(
                {
                    "text": text.strip(),
                    "timestamp": timestamp,
                    "session_date": session_date,
                    "source_archive": archive_file.name,
                }
            )

    return notes


def extract_notes_from_archives(archive_dir: Path) -> list[dict]:
    """
    Extract all notes from all archive files.

    Args:
        archive_dir: Directory containing archive files

    Returns:
        List of all notes from all archives

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> temp_dir = Path(tempfile.mkdtemp())
        >>> _ = (temp_dir / "2026-01-01.md").write_text("[10:00] Note 1")
        >>> _ = (temp_dir / "2026-01-02.md").write_text("[11:00] Note 2")
        >>> notes = extract_notes_from_archives(temp_dir)
        >>> len(notes)
        2
        >>> import shutil
        >>> shutil.rmtree(temp_dir)
    """
    if not archive_dir.exists():
        return []

    all_notes = []
    for archive_file in sorted(archive_dir.glob("*.md")):
        notes = extract_notes_from_archive(archive_file)
        all_notes.extend(notes)

    return all_notes


def deduplicate_notes(notes: list[dict], threshold: float = 0.9) -> list[dict]:
    """
    Remove duplicate notes using similarity threshold.

    Args:
        notes: List of note dicts
        threshold: Similarity threshold for deduplication (default: 0.9)

    Returns:
        Deduplicated list of notes

    Examples:
        >>> notes = [
        ...     {"text": "Testing workflow", "timestamp": "2026-01-01T10:00:00Z"},
        ...     {"text": "Testing workflow", "timestamp": "2026-01-01T11:00:00Z"},
        ...     {"text": "Different note", "timestamp": "2026-01-01T12:00:00Z"},
        ... ]
        >>> deduped = deduplicate_notes(notes, threshold=0.9)
        >>> len(deduped)
        2
        >>> deduped[0]["text"]
        'Testing workflow'
        >>> deduped[1]["text"]
        'Different note'
    """
    if not notes:
        return []

    unique_notes = []
    for note in notes:
        is_duplicate = False
        for existing in unique_notes:
            similarity = calculate_similarity(note["text"], existing["text"])
            if similarity >= threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            unique_notes.append(note)

    return unique_notes


def cluster_similar_notes(
    notes: list[dict], threshold: float = 0.85
) -> dict[str, list[str]]:
    """
    Cluster similar notes using simple single-linkage clustering.

    Args:
        notes: List of note dicts with "id" field
        threshold: Similarity threshold for clustering (default: 0.85)

    Returns:
        Dict mapping cluster_id to list of note_ids

    Examples:
        >>> notes = [
        ...     {"id": "n_001", "text": "Run tests before commit"},
        ...     {"id": "n_002", "text": "Run tests before committing"},
        ...     {"id": "n_003", "text": "Check documentation"},
        ... ]
        >>> clusters = cluster_similar_notes(notes, threshold=0.85)
        >>> len(clusters)
        2
        >>> any(len(ids) >= 2 for ids in clusters.values())
        True
    """
    if not notes:
        return {}

    # Initialize: each note starts in its own cluster
    clusters: dict[str, list[str]] = {}
    note_to_cluster: dict[str, str] = {}

    cluster_counter = 1

    for note in notes:
        note_id = note["id"]
        note_text = note["text"]

        # Find most similar cluster
        best_cluster = None
        best_similarity = 0.0

        for cluster_id, note_ids in clusters.items():
            # Compare with first note in cluster (representative)
            representative_id = note_ids[0]
            representative = next(n for n in notes if n["id"] == representative_id)

            similarity = calculate_similarity(note_text, representative["text"])
            if similarity >= threshold and similarity > best_similarity:
                best_cluster = cluster_id
                best_similarity = similarity

        if best_cluster:
            # Add to existing cluster
            clusters[best_cluster].append(note_id)
            note_to_cluster[note_id] = best_cluster
        else:
            # Create new cluster
            new_cluster_id = f"c{cluster_counter:03d}"
            clusters[new_cluster_id] = [note_id]
            note_to_cluster[note_id] = new_cluster_id
            cluster_counter += 1

    return clusters


def calculate_note_freshness(last_used: str | None, half_life_days: int = 30) -> float:
    """
    Calculate freshness score with exponential decay.

    Args:
        last_used: ISO timestamp of last use (None if never used)
        half_life_days: Days for score to decay to 0.5

    Returns:
        Freshness score (1.0 = just used, 0.5 = half_life_days ago, 0.0 = very old)

    Examples:
        >>> calculate_note_freshness(None, half_life_days=30)
        0.5
        >>> from datetime import datetime, timedelta
        >>> now = datetime.now()
        >>> recent = (now - timedelta(days=1)).isoformat() + "Z"
        >>> score = calculate_note_freshness(recent, half_life_days=30)
        >>> 0.9 < score <= 1.0
        True
    """
    if last_used is None:
        # Never used: return medium freshness
        return 0.5

    try:
        last_used_dt = datetime.fromisoformat(last_used.replace("Z", "+00:00"))
        now = datetime.now(last_used_dt.tzinfo)
        days_since_use = (now - last_used_dt).days

        # Exponential decay: score = 2^(-days/half_life)
        decay_score = math.pow(2, -days_since_use / half_life_days)
        return max(0.0, min(1.0, decay_score))
    except (ValueError, AttributeError):
        return 0.5


def generate_note_id(session_date: str, index: int) -> str:
    """
    Generate note ID from session date and index.

    Args:
        session_date: Session date (YYYY-MM-DD)
        index: Note index within session

    Returns:
        Note ID (n_YYYYMMDD_XXX)

    Examples:
        >>> generate_note_id("2026-01-23", 1)
        'n_20260123_001'
        >>> generate_note_id("2026-01-23", 42)
        'n_20260123_042'
    """
    date_str = session_date.replace("-", "")
    return f"n_{date_str}_{index:03d}"


def index_notes(config: AsYouConfig) -> dict:
    """
    Main entry point for note indexing.

    Extracts notes from archives, deduplicates, clusters, and updates tracker.

    Args:
        config: As You configuration

    Returns:
        Status dict with counts

    Examples:
        >>> from pathlib import Path
        >>> import tempfile, json
        >>> temp_dir = Path(tempfile.mkdtemp())
        >>> config = AsYouConfig(
        ...     project_root=temp_dir,
        ...     claude_dir=temp_dir / ".claude",
        ...     tracker_file=temp_dir / "tracker.json",
        ...     archive_dir=temp_dir / "archives",
        ...     memo_file=temp_dir / "memo.md",
        ...     settings={
        ...         "habits": {
        ...             "deduplication_threshold": 0.9,
        ...             "clustering_threshold": 0.85,
        ...             "freshness_half_life_days": 30,
        ...         }
        ...     },
        ... )
        >>> config.archive_dir.mkdir(parents=True)
        >>> _ = (config.archive_dir / "2026-01-01.md").write_text("[10:00] Test note")
        >>> result = index_notes(config)
        >>> result["extracted"] > 0
        True
        >>> result["deduplicated"] > 0
        True
        >>> import shutil
        >>> shutil.rmtree(temp_dir)
    """
    # Load configuration
    dedup_threshold = config.settings.get("habits", {}).get(
        "deduplication_threshold", 0.9
    )
    cluster_threshold = config.settings.get("habits", {}).get(
        "clustering_threshold", 0.85
    )

    # 1. Extract notes from archives
    all_notes = extract_notes_from_archives(config.archive_dir)

    # 2. Deduplicate notes
    unique_notes = deduplicate_notes(all_notes, threshold=dedup_threshold)

    # 3. Load existing tracker
    tracker = load_tracker(config.tracker_file)

    # 4. Assign IDs to new notes (avoid duplicates with existing notes)
    existing_notes = tracker.get("notes", [])
    existing_texts = {n["text"] for n in existing_notes}

    # Filter out notes that already exist in tracker
    new_notes = [n for n in unique_notes if n["text"] not in existing_texts]

    # Assign IDs to new notes
    for i, note in enumerate(new_notes, start=1):
        note_id = generate_note_id(note["session_date"], i)
        note["id"] = note_id
        note["cluster_id"] = None
        note["confidence"] = {"mean": 0.5, "variance": 0.04}
        note["last_used"] = None
        note["use_count"] = 0
        note["success_count"] = 0
        note["failure_count"] = 0

    # 5. Combine with existing notes
    all_indexed_notes = existing_notes + new_notes

    # 6. Cluster all notes (re-cluster to include new notes)
    if all_indexed_notes:
        clusters = cluster_similar_notes(all_indexed_notes, threshold=cluster_threshold)

        # Update cluster_id in notes
        for cluster_id, note_ids in clusters.items():
            for note_id in note_ids:
                note = next((n for n in all_indexed_notes if n["id"] == note_id), None)
                if note:
                    note["cluster_id"] = cluster_id

        # Calculate cluster confidence (mean of note confidences)
        cluster_data = {}
        for cluster_id, note_ids in clusters.items():
            cluster_notes = [n for n in all_indexed_notes if n["id"] in note_ids]
            mean_confidence = sum(n["confidence"]["mean"] for n in cluster_notes) / len(
                cluster_notes
            )

            cluster_data[cluster_id] = {
                "label": None,  # Phase 1: skip automatic labeling
                "note_ids": note_ids,
                "confidence": mean_confidence,
                "created_at": datetime.now().isoformat() + "Z",
            }
    else:
        cluster_data = {}

    # 7. Update tracker
    tracker["notes"] = all_indexed_notes
    tracker["clusters"] = cluster_data

    # 8. Save tracker
    save_tracker(config.tracker_file, tracker)

    return {
        "extracted": len(all_notes),
        "deduplicated": len(unique_notes),
        "new_notes": len(new_notes),
        "total_notes": len(all_indexed_notes),
        "clusters": len(cluster_data),
    }


if __name__ == "__main__":
    import doctest
    import sys

    if "--test" in sys.argv:
        print("Running note_indexer doctests:")
        results = doctest.testmod(verbose=("-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        # Standalone execution
        config = AsYouConfig.from_environment()
        result = index_notes(config)
        print("Note indexing complete:")
        print(f"  Extracted: {result['extracted']}")
        print(f"  Deduplicated: {result['deduplicated']}")
        print(f"  New notes: {result['new_notes']}")
        print(f"  Total notes: {result['total_notes']}")
        print(f"  Clusters: {result['clusters']}")
