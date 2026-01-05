#!/bin/bash
set -u
# Calculate PMI (Pointwise Mutual Information) scores for word co-occurrences (Unicode-aware)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
CLAUDE_DIR="${CLAUDE_DIR:-$PROJECT_ROOT/.claude}"

# Use Python script for Unicode-aware PMI calculation
export PROJECT_ROOT CLAUDE_DIR
python3 "$SCRIPT_DIR/lib/pmi_calculator.py"
