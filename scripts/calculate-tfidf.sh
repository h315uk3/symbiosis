#!/bin/bash
set -u
# Calculate TF-IDF scores for patterns (Unicode-aware)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
CLAUDE_DIR="${CLAUDE_DIR:-$PROJECT_ROOT/.claude}"

# Use Python script for Unicode-aware TF-IDF calculation
export PROJECT_ROOT CLAUDE_DIR
python3 "$SCRIPT_DIR/lib/tfidf_calculator.py"
