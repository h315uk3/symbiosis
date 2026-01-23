#!/usr/bin/env python3
"""
Habit searcher using BM25 ranking.

Phase 2 of Issue #83: Habit Extraction and Automatic Application.
"""

from pathlib import Path

from as_you.lib.bm25_calculator import calculate_bm25_score, calculate_idf, tokenize
from as_you.lib.common import AsYouConfig, load_tracker
from as_you.lib.note_indexer import calculate_note_freshness


def build_note_corpus(notes: list[dict]) -> dict:
    """
    Build BM25 corpus from notes.

    Args:
        notes: List of note dicts

    Returns:
        Dict with corpus statistics (tokens, doc_freq, avg_length)

    Examples:
        >>> notes = [
        ...     {"text": "Run tests before commit", "id": "n_001"},
        ...     {"text": "Run tests after changes", "id": "n_002"},
        ...     {"text": "Check documentation", "id": "n_003"},
        ... ]
        >>> corpus = build_note_corpus(notes)
        >>> len(corpus["documents"])
        3
        >>> "run" in corpus["doc_freq"]
        True
        >>> corpus["avg_length"] > 0
        True
    """
    documents = []
    doc_freq = {}

    for note in notes:
        tokens = tokenize(note["text"])
        documents.append({"id": note["id"], "tokens": tokens})

        # Count document frequency
        unique_tokens = set(tokens)
        for token in unique_tokens:
            doc_freq[token] = doc_freq.get(token, 0) + 1

    total_docs = len(documents)
    avg_length = (
        sum(len(doc["tokens"]) for doc in documents) / total_docs
        if total_docs > 0
        else 0
    )

    return {
        "documents": documents,
        "doc_freq": doc_freq,
        "avg_length": avg_length,
        "total_docs": total_docs,
    }


def calculate_bm25_for_query(
    query: str,
    corpus: dict,
    k1: float = 1.5,
    b: float = 0.75,
) -> dict[str, float]:
    """
    Calculate BM25 scores for query against all documents.

    Args:
        query: Search query string
        corpus: Corpus built by build_note_corpus()
        k1: BM25 k1 parameter (default: 1.5)
        b: BM25 b parameter (default: 0.75)

    Returns:
        Dict mapping note_id to BM25 score

    Examples:
        >>> notes = [
        ...     {"text": "Run tests before commit", "id": "n_001"},
        ...     {"text": "Check documentation", "id": "n_002"},
        ... ]
        >>> corpus = build_note_corpus(notes)
        >>> scores = calculate_bm25_for_query("run tests", corpus)
        >>> scores["n_001"] > 0
        True
        >>> scores["n_001"] > scores["n_002"]
        True
    """
    query_tokens = tokenize(query)
    documents = corpus["documents"]
    doc_freq = corpus["doc_freq"]
    avg_length = corpus["avg_length"]
    total_docs = corpus["total_docs"]

    scores = {}

    for doc in documents:
        doc_id = doc["id"]
        doc_tokens = doc["tokens"]
        doc_length = len(doc_tokens)

        total_score = 0.0

        for query_token in query_tokens:
            if query_token in doc_freq:
                # Calculate IDF
                idf = calculate_idf(doc_freq[query_token], total_docs)

                # Calculate term frequency in document
                term_freq = doc_tokens.count(query_token)

                # Calculate BM25 score
                score = calculate_bm25_score(
                    term_freq, doc_length, avg_length, idf, k1, b
                )
                total_score += score

        scores[doc_id] = total_score

    return scores


def filter_by_thresholds(
    notes: list[dict],
    min_confidence: float = 0.5,
    min_freshness: float = 0.3,
    half_life_days: int = 30,
) -> list[dict]:
    """
    Filter notes by confidence and freshness thresholds.

    Args:
        notes: List of note dicts
        min_confidence: Minimum confidence score (default: 0.5)
        min_freshness: Minimum freshness score (default: 0.3)
        half_life_days: Half-life for freshness decay (default: 30)

    Returns:
        Filtered list of notes

    Examples:
        >>> notes = [
        ...     {"text": "Test 1", "confidence": {"mean": 0.6}, "last_used": None},
        ...     {"text": "Test 2", "confidence": {"mean": 0.4}, "last_used": None},
        ...     {"text": "Test 3", "confidence": {"mean": 0.7}, "last_used": None},
        ... ]
        >>> filtered = filter_by_thresholds(
        ...     notes, min_confidence=0.5, min_freshness=0.3
        ... )
        >>> len(filtered)
        2
        >>> filtered[0]["confidence"]["mean"] >= 0.5
        True
    """
    filtered = []

    for note in notes:
        confidence = note["confidence"]["mean"]
        freshness = calculate_note_freshness(note.get("last_used"), half_life_days)

        if confidence >= min_confidence and freshness >= min_freshness:
            # Add freshness to note for later use
            note_with_freshness = note.copy()
            note_with_freshness["freshness"] = freshness
            filtered.append(note_with_freshness)

    return filtered


def calculate_final_score(
    bm25_score: float, confidence: float, freshness: float
) -> float:
    """
    Calculate final ranking score.

    Formula: bm25 × confidence × freshness

    Args:
        bm25_score: BM25 relevance score
        confidence: Confidence score (0.0-1.0)
        freshness: Freshness score (0.0-1.0)

    Returns:
        Final score

    Examples:
        >>> calculate_final_score(10.0, 0.8, 0.9)
        7.2
        >>> calculate_final_score(5.0, 0.5, 0.5)
        1.25
        >>> calculate_final_score(0.0, 1.0, 1.0)
        0.0
    """
    return bm25_score * confidence * freshness


def search_habits(
    query: str,
    tracker_file: Path,
    top_k: int = 5,
    min_confidence: float = 0.5,
    min_freshness: float = 0.3,
    k1: float = 1.5,
    b: float = 0.75,
    half_life_days: int = 30,
) -> list[dict]:
    """
    Search for relevant habits using BM25 ranking.

    Args:
        query: Search query string
        tracker_file: Path to pattern_tracker.json
        top_k: Number of top results to return (default: 5)
        min_confidence: Minimum confidence threshold (default: 0.5)
        min_freshness: Minimum freshness threshold (default: 0.3)
        k1: BM25 k1 parameter (default: 1.5)
        b: BM25 b parameter (default: 0.75)
        half_life_days: Freshness half-life in days (default: 30)

    Returns:
        List of top-k habit dicts with scores

    Examples:
        >>> from pathlib import Path
        >>> import tempfile, json
        >>> temp_file = Path(tempfile.mktemp(suffix=".json"))
        >>> data = {
        ...     "notes": [
        ...         {
        ...             "id": "n_001",
        ...             "text": "Run tests before commit",
        ...             "confidence": {"mean": 0.6, "variance": 0.04},
        ...             "last_used": None,
        ...         },
        ...         {
        ...             "id": "n_002",
        ...             "text": "Check documentation",
        ...             "confidence": {"mean": 0.7, "variance": 0.04},
        ...             "last_used": None,
        ...         },
        ...     ],
        ...     "patterns": {},
        ...     "promotion_candidates": [],
        ...     "cooccurrences": [],
        ... }
        >>> _ = temp_file.write_text(json.dumps(data))
        >>> results = search_habits("run tests", temp_file, top_k=2)
        >>> len(results) > 0
        True
        >>> results[0]["text"] == "Run tests before commit"
        True
        >>> temp_file.unlink()
    """
    # Load tracker
    tracker = load_tracker(tracker_file)
    notes = tracker.get("notes", [])

    if not notes:
        return []

    # Filter by thresholds
    filtered_notes = filter_by_thresholds(
        notes, min_confidence, min_freshness, half_life_days
    )

    if not filtered_notes:
        return []

    # Build corpus
    corpus = build_note_corpus(filtered_notes)

    # Calculate BM25 scores
    bm25_scores = calculate_bm25_for_query(query, corpus, k1, b)

    # Calculate final scores
    results = []
    for note in filtered_notes:
        note_id = note["id"]
        bm25_score = bm25_scores.get(note_id, 0.0)
        confidence = note["confidence"]["mean"]
        freshness = note["freshness"]

        final_score = calculate_final_score(bm25_score, confidence, freshness)

        results.append(
            {
                "id": note_id,
                "text": note["text"],
                "bm25_score": bm25_score,
                "confidence": confidence,
                "freshness": freshness,
                "final_score": final_score,
            }
        )

    # Sort by final score (descending) and return top k
    results.sort(key=lambda x: x["final_score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    import doctest
    import sys

    if "--test" in sys.argv:
        print("Running habit_searcher doctests:")
        results = doctest.testmod(verbose=("-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        # Standalone execution
        config = AsYouConfig.from_environment()

        # Get settings
        habits_config = config.settings.get("habits", {})
        min_confidence = habits_config.get("min_confidence", 0.5)
        min_freshness = habits_config.get("min_freshness", 0.3)
        half_life_days = habits_config.get("freshness_half_life_days", 30)

        bm25_config = config.settings.get("scoring", {}).get("bm25", {})
        k1 = bm25_config.get("k1", 1.5)
        b = bm25_config.get("b", 0.75)

        if len(sys.argv) > 1 and sys.argv[1] != "--test":
            query = " ".join(sys.argv[1:])
        else:
            query = "testing python"

        print(f"Searching for: '{query}'")
        print(f"Settings: confidence>={min_confidence}, freshness>={min_freshness}")
        print("-" * 50)

        results = search_habits(
            query,
            config.tracker_file,
            top_k=5,
            min_confidence=min_confidence,
            min_freshness=min_freshness,
            k1=k1,
            b=b,
            half_life_days=half_life_days,
        )

        if results:
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['text']}")
                print(
                    f"   Score: {result['final_score']:.4f} (BM25: {result['bm25_score']:.4f}, Conf: {result['confidence']:.2f}, Fresh: {result['freshness']:.2f})"
                )
                print()
        else:
            print("No results found")
