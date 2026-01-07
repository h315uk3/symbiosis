#!/bin/bash
set -u
# SessionEnd hook: Archive session notes, track patterns, and merge similar patterns

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$REPO_ROOT}"
CLAUDE_DIR="${CLAUDE_DIR:-$PROJECT_ROOT/.claude}"
ERROR_LOG="$CLAUDE_DIR/as_you/errors.log"

# Ensure log directory exists
mkdir -p "$(dirname "$ERROR_LOG")"

# Archive session notes
if ! python3 "${REPO_ROOT}/scripts/note_archiver.py" 2>>"$ERROR_LOG"; then
  echo "Archive failed (see $ERROR_LOG for details)"
fi

# Track pattern frequency
if ! python3 "${REPO_ROOT}/scripts/frequency_tracker.py" 2>>"$ERROR_LOG"; then
  echo "Pattern tracking failed (see $ERROR_LOG for details)"
fi

# Periodic merge (every N sessions)
MERGE_INTERVAL="${AS_YOU_MERGE_INTERVAL:-10}"
COUNTER_FILE="$CLAUDE_DIR/as_you/.session_count"

# Ensure directory exists
mkdir -p "$(dirname "$COUNTER_FILE")"

# Read and increment counter
COUNT=$(cat "$COUNTER_FILE" 2>/dev/null || echo "0")
COUNT=$((COUNT + 1))
echo "$COUNT" > "$COUNTER_FILE"

# Check if merge should run
if [ $((COUNT % MERGE_INTERVAL)) -eq 0 ]; then
  echo "Running periodic pattern merge (session $COUNT)..."
  if MERGE_OUTPUT=$(python3 "${REPO_ROOT}/scripts/pattern_merger.py" 2>>"$ERROR_LOG"); then
    MERGE_COUNT=$(echo "$MERGE_OUTPUT" | grep -c "Merged" 2>/dev/null || echo "0")

    if [ "$MERGE_COUNT" -gt 0 ]; then
      echo "Merged ${MERGE_COUNT} similar patterns"
      echo "$MERGE_OUTPUT" | grep "Merged"
    else
      echo "No similar patterns found"
    fi
  else
    echo "Pattern merge failed (see $ERROR_LOG for details)"
  fi
else
  NEXT_MERGE=$((COUNT + MERGE_INTERVAL - (COUNT % MERGE_INTERVAL)))
  echo "Pattern merge skipped (runs every $MERGE_INTERVAL sessions, next at session $NEXT_MERGE)"
fi

exit 0
