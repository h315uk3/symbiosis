#!/bin/bash
set -u
# SessionStart hook: Clean up and notify patterns

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$REPO_ROOT}"
CLAUDE_DIR="${CLAUDE_DIR:-$PROJECT_ROOT/.claude}"
MEMO_FILE="$CLAUDE_DIR/as_you/session_notes.local.md"
TRACKER_FILE="$CLAUDE_DIR/as_you/pattern_tracker.json"
ERROR_LOG="$CLAUDE_DIR/as_you/errors.log"

# Ensure log directory exists
mkdir -p "$(dirname "$ERROR_LOG")"

# Clean up old archives (older than 7 days)
ARCHIVE_DIR="$CLAUDE_DIR/as_you/session_archive"
if [ -d "$ARCHIVE_DIR" ]; then
	find "$ARCHIVE_DIR" -name "*.md" -type f -mtime +7 -delete 2>/dev/null || true
fi

# Clear session notes for new session
rm -f "$MEMO_FILE"

# Check for promotion candidates (using Python for better testability)
if [ -f "$TRACKER_FILE" ]; then
	# Get summary from Python script (single call, space-separated output)
	if ! read -r TOTAL SKILLS AGENTS TOP_PATTERN TOP_TYPE < <(
		python3 "${REPO_ROOT}/scripts/promotion_analyzer.py" summary-line 2>>"$ERROR_LOG"
	); then
		echo "Warning: Failed to analyze promotion candidates (see $ERROR_LOG)" >&2
		TOTAL=0
	fi

	if [ -n "$TOTAL" ] && [ "$TOTAL" -gt 0 ] 2>/dev/null; then
		echo ""
		echo "📊 Knowledge base promotion candidates detected ($TOTAL patterns)"

		[ "${SKILLS:-0}" -gt 0 ] 2>/dev/null && echo "  - Skill candidates: $SKILLS"
		[ "${AGENTS:-0}" -gt 0 ] 2>/dev/null && echo "  - Agent candidates: $AGENTS"

		if [ -n "$TOP_PATTERN" ] && [ "$TOP_PATTERN" != "null" ] && [ "$TOP_PATTERN" != "None" ]; then
			echo "  - Top priority: \"$TOP_PATTERN\" ($TOP_TYPE)"
		fi

		echo ""
		echo "Detailed analysis: /as-you:memory-analyze"
		echo ""
	fi
fi

echo "As You plugin loaded"
echo "Quick start: /as-you:help"
