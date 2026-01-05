#!/usr/bin/env python3
"""
Unicode-aware pattern detection for session archives.
Extracts patterns from text using language-agnostic tokenization.
"""

import re
import json
import sys
from pathlib import Path
from collections import Counter
from typing import List, Dict


def extract_patterns(text: str) -> List[str]:
    """
    Extract patterns from text using Unicode-aware tokenization.

    Approach:
    1. Space-delimited tokens (Latin alphabet, etc.): extract as words (3+ chars)
    2. Non-space scripts (Japanese, Chinese, Korean): extract as 3-grams
    """
    patterns = []

    # Remove timestamps [HH:MM]
    text = re.sub(r'\[\d{2}:\d{2}\]', '', text)

    # Extract space-delimited words (3+ chars, ASCII/Latin letters and numbers only)
    # This captures English and similar languages but not CJK
    words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9]{2,}\b', text)
    patterns.extend(word.lower() for word in words)

    # Extract 3-grams from CJK scripts
    # Remove all non-CJK characters to get continuous CJK text
    cjk_chars = ''.join(re.findall(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]', text))

    # Extract all 3-character sequences from CJK text
    # Han: Chinese characters (U+4E00-U+9FFF)
    # Hiragana: Japanese (U+3040-U+309F)
    # Katakana: Japanese (U+30A0-U+30FF)
    # Hangul: Korean (U+AC00-U+D7AF)
    for i in range(len(cjk_chars) - 2):
        trigram = cjk_chars[i:i+3]
        patterns.append(trigram)

    return patterns


def detect_patterns_from_archives(archive_dir: Path, top_n: int = 20) -> List[Dict[str, any]]:
    """
    Detect frequent patterns from all markdown files in archive directory.

    Args:
        archive_dir: Path to session archive directory
        top_n: Number of top patterns to return

    Returns:
        List of dicts with 'word' and 'count' keys, sorted by frequency
    """
    if not archive_dir.exists() or not archive_dir.is_dir():
        return []

    # Collect all patterns from all markdown files
    all_patterns = []

    for md_file in archive_dir.glob('*.md'):
        try:
            text = md_file.read_text(encoding='utf-8')
            all_patterns.extend(extract_patterns(text))
        except Exception as e:
            print(f"Warning: Failed to read {md_file}: {e}", file=sys.stderr)
            continue

    if not all_patterns:
        return []

    # Count frequency
    pattern_counts = Counter(all_patterns)

    # Get top N patterns
    top_patterns = pattern_counts.most_common(top_n)

    # Format as list of dicts
    return [{'word': word, 'count': count} for word, count in top_patterns]


def main():
    """Main entry point for CLI usage."""
    import os

    # Get archive directory from environment or default
    project_root = os.getenv('PROJECT_ROOT', os.getcwd())
    claude_dir = os.getenv('CLAUDE_DIR', os.path.join(project_root, '.claude'))
    archive_dir = Path(claude_dir) / 'as_you' / 'session_archive'

    # Detect patterns
    patterns = detect_patterns_from_archives(archive_dir)

    # Output as JSON
    print(json.dumps(patterns, ensure_ascii=False, indent=0))


if __name__ == '__main__':
    main()
