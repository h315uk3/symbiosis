#!/usr/bin/env python3
"""BM25 scoring algorithm for pattern relevance ranking.

BM25 (Best Matching 25) is a ranking function used by search engines to estimate
the relevance of documents to a given search query. It's an improvement over TF-IDF
that incorporates:
1. Term frequency saturation (prevents over-weighting of high-frequency terms)
2. Document length normalization (accounts for varying document lengths)

Formula:
    BM25(D, Q) = Σ IDF(qi) × (f(qi, D) × (k1 + 1)) / (f(qi, D) + k1 × (1 - b + b × |D| / avgdl))

Where:
    D: Document (pattern text)
    Q: Query (search terms)
    qi: Query term i
    f(qi, D): Frequency of qi in D
    |D|: Length of document D
    avgdl: Average document length
    k1: Term frequency saturation parameter (typically 1.2-2.0)
    b: Length normalization parameter (typically 0.75)
    IDF(qi): Inverse document frequency of qi

References:
    Robertson, S. & Zaragoza, H. (2009). The Probabilistic Relevance Framework:
    BM25 and Beyond. Foundations and Trends in Information Retrieval.
"""

import math
import re
import sys
from collections import defaultdict
from pathlib import Path

# Add plugin to path for imports
_PLUGIN_ROOT = Path(__file__).parent.parent.parent
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from as_you.lib.common import (  # noqa: E402
    DEFAULT_SETTINGS,
    AsYouConfig,
    load_tracker,
    save_tracker,
)


def calculate_idf(doc_freq: int, total_docs: int) -> float:
    """Calculate Inverse Document Frequency (IDF).

    Args:
        doc_freq: Number of documents containing the term
        total_docs: Total number of documents

    Returns:
        IDF score

    Examples:
        >>> round(calculate_idf(1, 10), 3)  # Rare term
        1.992
        >>> round(calculate_idf(5, 10), 3)  # Common term
        0.693
        >>> round(calculate_idf(10, 10), 3)  # Very common term
        0.047
    """
    return math.log((total_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0)


def calculate_bm25_score(
    term_freq: int,
    doc_length: int,
    avg_doc_length: float,
    idf: float,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    """Calculate BM25 score for a single term in a document.

    Args:
        term_freq: Term frequency in document
        doc_length: Length of document (in tokens)
        avg_doc_length: Average document length across corpus
        idf: Inverse document frequency of term
        k1: Term frequency saturation parameter (default: 1.5)
        b: Length normalization parameter (default: 0.75)

    Returns:
        BM25 score for the term

    Examples:
        >>> # Short document, frequent term
        >>> round(calculate_bm25_score(5, 10, 20, 2.0, k1=1.5, b=0.75), 3)
        4.211
        >>> # Long document, same term
        >>> round(calculate_bm25_score(5, 40, 20, 2.0, k1=1.5, b=0.75), 3)
        3.279
        >>> # Very frequent term (saturation effect)
        >>> round(calculate_bm25_score(100, 200, 200, 2.0, k1=1.5, b=0.75), 3)
        4.926
    """
    # Length normalization factor
    length_norm = 1 - b + b * (doc_length / avg_doc_length)

    # BM25 formula
    numerator = term_freq * (k1 + 1)
    denominator = term_freq + k1 * length_norm

    return idf * (numerator / denominator)


def tokenize(text: str) -> list[str]:
    """Tokenize text into words.

    Args:
        text: Input text

    Returns:
        List of lowercase tokens

    Examples:
        >>> tokenize("Hello World")
        ['hello', 'world']
        >>> tokenize("test-pattern testing")
        ['test', 'pattern', 'testing']
        >>> tokenize("BM25 scoring!")
        ['bm25', 'scoring']
    """
    # Split on non-alphanumeric characters
    tokens = re.findall(r"\w+", text.lower())
    return tokens


def calculate_bm25_scores(
    patterns: dict[str, dict],
    archive_dir: Path,
    k1: float | None = None,
    b: float | None = None,
) -> dict[str, float]:
    """Calculate BM25 scores for all patterns.

    Args:
        patterns: Pattern dictionary from tracker
        archive_dir: Path to archive directory
        k1: BM25 k1 parameter (None = use default from config)
        b: BM25 b parameter (None = use default from config)

    Returns:
        Dictionary mapping pattern text to BM25 score

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     archive_dir = Path(tmpdir)
        ...     _ = (archive_dir / "doc1.md").write_text("python testing code")
        ...     _ = (archive_dir / "doc2.md").write_text("python code review")
        ...     patterns = {
        ...         "python": {"count": 5},
        ...         "testing": {"count": 2},
        ...         "code": {"count": 3},
        ...     }
        ...     scores = calculate_bm25_scores(patterns, archive_dir)
        ...     "python" in scores and "testing" in scores
        True
    """
    # Get parameters from config or use defaults
    if k1 is None:
        k1 = DEFAULT_SETTINGS["scoring"]["bm25"]["k1"]
    if b is None:
        b = DEFAULT_SETTINGS["scoring"]["bm25"]["b"]

    # Build document collection
    documents = []
    for doc_path in archive_dir.glob("*.md"):
        try:
            text = doc_path.read_text(encoding="utf-8")
            documents.append(tokenize(text))
        except (OSError, UnicodeDecodeError) as e:
            print(f"Warning: Failed to read {doc_path}: {e}")
            continue

    if not documents:
        return {}

    total_docs = len(documents)
    avg_doc_length = sum(len(doc) for doc in documents) / total_docs

    # Calculate document frequency for each term
    doc_freq: dict[str, int] = defaultdict(int)
    for doc in documents:
        unique_terms = set(doc)
        for term in unique_terms:
            doc_freq[term] += 1

    # Calculate BM25 scores for each pattern
    scores = {}
    for pattern_text in patterns:
        pattern_tokens = tokenize(pattern_text)
        total_score = 0.0

        # Sum BM25 scores for all tokens in pattern
        for token in pattern_tokens:
            if token in doc_freq:
                idf = calculate_idf(doc_freq[token], total_docs)

                # Calculate average term frequency across documents
                term_freq = sum(doc.count(token) for doc in documents) / total_docs
                doc_length = avg_doc_length  # Use average for simplicity

                score = calculate_bm25_score(
                    int(term_freq), int(doc_length), avg_doc_length, idf, k1, b
                )
                total_score += score

        scores[pattern_text] = total_score

    return scores


def main():
    """CLI entry point."""
    config = AsYouConfig.from_environment()

    print("実行中: BM25 Calculator")
    print("-" * 50)

    # Load patterns
    data = load_tracker(config.tracker_file)
    patterns = data.get("patterns", {})

    if not patterns:
        print("パターンが見つかりません")
        return

    # Get BM25 parameters from config
    bm25_config = config.settings["scoring"]["bm25"]
    k1 = bm25_config["k1"]
    b = bm25_config["b"]

    print(f"BM25パラメータ: k1={k1}, b={b}")

    # Calculate scores
    scores = calculate_bm25_scores(patterns, config.archive_dir, k1, b)

    # Update patterns
    for pattern_text, score in scores.items():
        if pattern_text in patterns:
            patterns[pattern_text]["bm25_score"] = round(score, 6)

    # Save updated data
    save_tracker(config.tracker_file, data)
    print(f"✓ {len(scores)}個のパターンにBM25スコアを計算しました")


if __name__ == "__main__":
    import doctest

    # Check if running doctests
    if "--test" in sys.argv or "-v" in sys.argv:
        print("Running BM25 calculator doctests:")
        results = doctest.testmod(verbose=("--verbose" in sys.argv or "-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
