#!/bin/bash
set -u
# SessionStart hook: Clean up and notify patterns

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$REPO_ROOT}"
CLAUDE_DIR="${CLAUDE_DIR:-$PROJECT_ROOT/.claude}"
MEMO_FILE="$CLAUDE_DIR/as-you/session-notes.local.md"
TRACKER_FILE="$CLAUDE_DIR/as-you/pattern-tracker.json"

# Clean up old archives
"${REPO_ROOT}/scripts/cleanup-archive.sh" 2>/dev/null || true

# Clear session notes for new session
rm -f "$MEMO_FILE"

# Check for promotion candidates
if [ -f "$TRACKER_FILE" ]; then
	CANDIDATES=$(jq -r '.promotion_candidates | length' "$TRACKER_FILE" 2>/dev/null)
	if [ "$CANDIDATES" -gt 0 ]; then
		echo ""
		echo "📊 Knowledge base promotion candidates detected ($CANDIDATES patterns)"

		# Show detailed suggestions
		SUGGESTIONS=$("${REPO_ROOT}/scripts/suggest-promotions.sh" 2>/dev/null)
		SKILL_COUNT=$(echo "$SUGGESTIONS" | jq '[.[] | select(.type == "skill")] | length' 2>/dev/null)
		AGENT_COUNT=$(echo "$SUGGESTIONS" | jq '[.[] | select(.type == "agent")] | length' 2>/dev/null)

		if [ "$SKILL_COUNT" -gt 0 ]; then
			echo "  - Skill candidates: $SKILL_COUNT"
		fi
		if [ "$AGENT_COUNT" -gt 0 ]; then
			echo "  - Agent candidates: $AGENT_COUNT"
		fi

		# Show top candidate
		TOP_PATTERN=$(echo "$SUGGESTIONS" | jq -r '.[0].pattern' 2>/dev/null)
		TOP_TYPE=$(echo "$SUGGESTIONS" | jq -r '.[0].type' 2>/dev/null)
		if [ -n "$TOP_PATTERN" ] && [ "$TOP_PATTERN" != "null" ]; then
			echo "  - Top priority: \"$TOP_PATTERN\" ($TOP_TYPE)"
		fi

		echo ""
		echo "Detailed analysis: /as-you:memory-analyze"
		echo ""
	fi
fi

echo "As You plugin loaded"
echo "Available features:"
echo "- Session notes: /as-you:note, /as-you:note-show, /as-you:note-history"
echo "- Workflows: /as-you:save-workflow, /as-you:list-workflows"
echo "- Analysis: /as-you:memory-analyze, /as-you:memory-stats"
echo "- Help: /as-you:help"
