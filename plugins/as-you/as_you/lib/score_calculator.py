#!/usr/bin/env python3
"""
Unified score calculator for pattern_tracker.json.
Calculates TF-IDF, PMI, time decay, and composite scores in single pass.
Replaces 4 separate script calls with 1 unified call.

All input notes are translated to English before storage (commands/note.md),
ensuring consistent pattern analysis across all languages:
- Japanese: "デバッグ中のバグを調査" → "Investigating bug during debugging"
- Chinese: "实现用户认证功能" → "Implementing user authentication feature"
- Korean: "데이터베이스 연결 오류 수정" → "Fixing database connection error"
- Spanish: "refactorización del código" → "code refactoring"
- French: "optimisation des performances" → "performance optimization"
- German: "Fehlerbehandlung implementieren" → "implement error handling"
- Arabic: "تحسين واجهة المستخدم" → "improving user interface"
- Russian: "добавление новой функции" → "adding new feature"
"""

import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path

# Import from existing modules
from as_you.lib.common import AsYouConfig
from as_you.lib.pmi_calculator import count_total_patterns
from as_you.lib.tfidf_calculator import calculate_tfidf_single_pass, is_stopword


class UnifiedScoreCalculator:
    """
    Calculate all scores in unified manner.

    Examples:
        >>> from pathlib import Path
        >>> import tempfile, json
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     # Setup test data
        ...     tracker_file = Path(tmpdir) / "pattern_tracker.json"
        ...     archive_dir = Path(tmpdir) / "archive"
        ...     archive_dir.mkdir()
        ...
        ...     # Create sample tracker
        ...     data = {
        ...         "patterns": {
        ...             "test": {
        ...                 "count": 5,
        ...                 "last_seen": "2025-01-05",
        ...                 "sessions": ["s1", "s2"],
        ...             }
        ...         },
        ...         "cooccurrences": [],
        ...     }
        ...     _ = tracker_file.write_text(json.dumps(data), encoding="utf-8")
        ...
        ...     # Create sample archive
        ...     archive_file = archive_dir / "2025-01-05.md"
        ...     _ = archive_file.write_text("test test test", encoding="utf-8")
        ...
        ...     # Calculate scores
        ...     calc = UnifiedScoreCalculator(tracker_file, archive_dir)
        ...     result = calc.calculate_all_scores()
        ...
        ...     # Verify scores were calculated
        ...     "tfidf" in result["patterns"]["test"]
        True
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     # Test with empty patterns
        ...     tracker_file = Path(tmpdir) / "pattern_tracker.json"
        ...     archive_dir = Path(tmpdir) / "archive"
        ...     archive_dir.mkdir()
        ...     data = {"patterns": {}, "cooccurrences": []}
        ...     _ = tracker_file.write_text(json.dumps(data), encoding="utf-8")
        ...     calc = UnifiedScoreCalculator(tracker_file, archive_dir)
        ...     result = calc.calculate_all_scores()
        ...     len(result["patterns"])
        0
    """

    def __init__(self, tracker_file: Path, archive_dir: Path):
        self.tracker_file = tracker_file
        self.archive_dir = archive_dir
        self.data = None
        self.total_patterns = 0
        self.total_docs = 0

        # Load tracker data
        with open(tracker_file, encoding="utf-8") as f:
            self.data = json.load(f)

        self.patterns = self.data.get("patterns", {})
        self.cooccurrences = self.data.get("cooccurrences", [])

    def calculate_all_scores(self) -> dict:
        """Calculate all scores in single pass."""
        if not self.patterns:
            return self.data

        # Pre-calculate totals
        self.total_patterns = count_total_patterns(self.archive_dir)
        self.total_docs = len(list(self.archive_dir.glob("*.md")))

        if self.total_patterns == 0:
            self.total_patterns = 1
        if self.total_docs == 0:
            self.total_docs = 1

        # Calculate each score type
        self._calculate_tfidf_scores()
        self._calculate_pmi_scores()
        self._calculate_time_decay_scores()
        self._calculate_composite_scores()
        self._update_promotion_candidates()

        return self.data

    def _calculate_tfidf_scores(self) -> None:
        """Calculate TF-IDF scores using optimized single-pass algorithm."""
        # Use optimized algorithm - scans all documents once for all patterns
        tfidf_scores = calculate_tfidf_single_pass(self.patterns, self.archive_dir)

        # Update patterns with calculated scores
        for word, (idf, tfidf) in tfidf_scores.items():
            self.patterns[word]["tfidf"] = round(tfidf, 6)
            self.patterns[word]["idf"] = round(idf, 6)
            self.patterns[word]["is_stopword"] = is_stopword(word)

    def _calculate_pmi_scores(self) -> None:
        """Calculate PMI scores for co-occurrences."""
        if not self.cooccurrences:
            return

        for cooccur in self.cooccurrences:
            words = cooccur.get("words", [])
            if len(words) != 2:
                continue

            word1, word2 = words
            cooccur_count = cooccur.get("count", 0)

            # Get individual counts
            count1 = self.patterns.get(word1, {}).get("count", 0)
            count2 = self.patterns.get(word2, {}).get("count", 0)

            if count1 == 0 or count2 == 0 or cooccur_count == 0:
                cooccur["pmi"] = 0.0
                continue

            # Calculate probabilities
            p_ab = cooccur_count / self.total_patterns
            p_a = count1 / self.total_patterns
            p_b = count2 / self.total_patterns

            # PMI = log(P(A,B) / (P(A) * P(B)))
            if p_ab > 0 and p_a > 0 and p_b > 0:
                pmi = math.log(p_ab / (p_a * p_b))
                cooccur["pmi"] = round(pmi, 6)
            else:
                cooccur["pmi"] = 0.0

    def _calculate_time_decay_scores(self) -> None:
        """Calculate time decay scores (recency)."""
        today = datetime.now().date()
        decay_lambda = float(os.getenv("DECAY_LAMBDA", "0.1"))

        for word, meta in self.patterns.items():
            last_seen_str = meta.get("last_seen")
            if not last_seen_str:
                self.patterns[word]["recency_score"] = 0.0
                self.patterns[word]["days_since_use"] = 9999
                continue

            try:
                last_seen = datetime.strptime(last_seen_str, "%Y-%m-%d").date()
                days_ago = (today - last_seen).days

                # Exponential decay: score = e^(-λt)
                recency_score = math.exp(-decay_lambda * days_ago)

                # Also calculate decay_score (count-weighted)
                count = meta.get("count", 0)
                decay_score = count * recency_score

                self.patterns[word]["recency_score"] = round(recency_score, 6)
                self.patterns[word]["decay_score"] = round(decay_score, 6)
                self.patterns[word]["days_since_use"] = days_ago
            except Exception:
                self.patterns[word]["recency_score"] = 0.0
                self.patterns[word]["decay_score"] = 0.0
                self.patterns[word]["days_since_use"] = 9999

    def _calculate_composite_scores(self) -> None:
        """Calculate composite scores combining all metrics."""
        # Weights (configurable via environment)
        weight_tfidf = float(os.getenv("WEIGHT_TFIDF", "0.4"))
        weight_recency = float(os.getenv("WEIGHT_RECENCY", "0.3"))
        weight_spread = float(os.getenv("WEIGHT_SPREAD", "0.3"))

        # Find max values for normalization
        max_tfidf = max(
            (meta.get("tfidf", 0) for meta in self.patterns.values()), default=1.0
        )
        max_sessions = max(
            (len(meta.get("sessions", [])) for meta in self.patterns.values()),
            default=1,
        )

        # Avoid division by zero
        max_tfidf = max(max_tfidf, 0.0001)
        max_sessions = max(max_sessions, 1)

        for word, meta in self.patterns.items():
            # Normalize components
            tfidf_norm = meta.get("tfidf", 0) / max_tfidf
            recency_norm = meta.get("recency_score", 0)  # Already 0-1
            spread_norm = len(meta.get("sessions", [])) / max_sessions

            # Penalty for stopwords
            stopword_penalty = 0.5 if meta.get("is_stopword", False) else 1.0

            # Composite score
            composite = (
                weight_tfidf * tfidf_norm
                + weight_recency * recency_norm
                + weight_spread * spread_norm
            ) * stopword_penalty

            self.patterns[word]["composite_score"] = round(composite, 6)

    def _update_promotion_candidates(self) -> None:
        """Update promotion candidates list."""
        threshold = float(os.getenv("PROMOTION_THRESHOLD", "0.3"))

        candidates = [
            word
            for word, meta in self.patterns.items()
            if meta.get("composite_score", 0) > threshold
            and not meta.get("promoted", False)
        ]

        # Sort by composite score descending
        candidates.sort(
            key=lambda w: self.patterns[w].get("composite_score", 0), reverse=True
        )

        self.data["promotion_candidates"] = candidates

    def save(self) -> None:
        """Save updated data back to tracker file."""
        with open(self.tracker_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)


def main():
    """CLI entry point."""
    # Get paths from environment
    config = AsYouConfig.from_environment()

    if not config.tracker_file.exists():
        print("Error: pattern_tracker.json not found", file=sys.stderr)
        sys.exit(1)

    # Calculate all scores using optimized algorithms
    calculator = UnifiedScoreCalculator(config.tracker_file, config.archive_dir)
    calculator.calculate_all_scores()
    calculator.save()

    # Print summary
    candidate_count = len(calculator.data.get("promotion_candidates", []))

    print("TF-IDF scores calculated for all patterns")
    print("PMI scores calculated for all co-occurrences")
    print("Time decay scores calculated for all patterns")
    print("Composite scores calculated for all patterns")
    print(f"Top {candidate_count} promotion candidates identified")


if __name__ == "__main__":
    import doctest
    import sys

    # Check if running doctests
    if "--test" in sys.argv or "-v" in sys.argv:
        print("Running score calculator doctests:")
        results = doctest.testmod(verbose=("--verbose" in sys.argv or "-v" in sys.argv))
        if results.failed == 0:
            print(f"\n✓ All {results.attempted} doctests passed")
        else:
            print(f"\n✗ {results.failed}/{results.attempted} doctests failed")
            sys.exit(1)
    else:
        main()
