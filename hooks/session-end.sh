#!/bin/bash
set -eo pipefail
# SessionEnd hook: Archive session notes, track patterns, and merge similar patterns

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$REPO_ROOT}"

# Archive session notes
"${REPO_ROOT}/scripts/archive-note.sh" || echo "Archive skipped"

# Track pattern frequency
"${REPO_ROOT}/scripts/track-frequency.sh" || echo "Pattern tracking skipped"

# Merge similar patterns automatically
echo "Checking for similar patterns..."
MERGE_OUTPUT=$("${REPO_ROOT}/scripts/merge-similar-patterns.sh" 2>&1 || echo "")
MERGE_COUNT=$(echo "$MERGE_OUTPUT" | grep -c "Merged" 2>/dev/null || echo "0")

if [ "$MERGE_COUNT" -gt 0 ]; then
  echo "Merged ${MERGE_COUNT} similar patterns"
  echo "$MERGE_OUTPUT" | grep "Merged"
else
  echo "No similar patterns found"
fi

exit 0
