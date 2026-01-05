#!/bin/bash
set -u
# Mark a pattern as promoted to skill or agent

# Ensure PATH includes mise shims and common bin directories
if [ -d "$HOME/.local/share/mise/shims" ]; then
	export PATH="$HOME/.local/share/mise/shims:$PATH"
fi
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
CLAUDE_DIR="${CLAUDE_DIR:-$PROJECT_ROOT/.claude}"
TRACKER_FILE="$CLAUDE_DIR/as-you/pattern-tracker.json"

# Usage
usage() {
	cat <<EOF
Usage: $0 <pattern> <type> <path>

Mark a pattern as promoted to prevent duplicate promotion.

Arguments:
  pattern   Pattern name (e.g., "deployment", "testing")
  type      Promotion type: "skill" or "agent"
  path      Path to the promoted skill/agent (e.g., "skills/deployment/")

Examples:
  $0 deployment skill skills/deployment-workflow/
  $0 testing agent agents/test-manager/
EOF
	exit 1
}

# Check arguments
if [ $# -lt 3 ]; then
	usage
fi

PATTERN="$1"
TYPE="$2"
PATH="$3"

# Validate type
if [ "$TYPE" != "skill" ] && [ "$TYPE" != "agent" ]; then
	echo "Error: type must be 'skill' or 'agent'" >&2
	exit 1
fi

# Check if tracker file exists
if [ ! -f "$TRACKER_FILE" ]; then
	echo "Error: pattern-tracker.json not found" >&2
	exit 1
fi

# Check if pattern exists
PATTERN_CHECK=$(jq ".patterns.\"$PATTERN\" // null" "$TRACKER_FILE")
if [ "$PATTERN_CHECK" = "null" ]; then
	echo "Error: pattern '$PATTERN' not found in tracker" >&2
	exit 1
fi

# Get current date
CURRENT_DATE=$(date +%Y-%m-%d)

# Update pattern with promotion info
if jq ".patterns.\"$PATTERN\".promoted = true | \
    .patterns.\"$PATTERN\".promoted_to = \"$TYPE\" | \
    .patterns.\"$PATTERN\".promoted_at = \"$CURRENT_DATE\" | \
    .patterns.\"$PATTERN\".promoted_path = \"$PATH\" | \
    .patterns.\"$PATTERN\".keep_tracking = true" "$TRACKER_FILE" >"$TRACKER_FILE.tmp"; then
	mv "$TRACKER_FILE.tmp" "$TRACKER_FILE"
	echo "✓ Pattern '$PATTERN' marked as promoted to $TYPE at $PATH"
else
	rm -f "$TRACKER_FILE.tmp"
	echo "Error: failed to update tracker" >&2
	exit 1
fi

# Recalculate composite scores to reflect promotion
if [ -f "$SCRIPT_DIR/calculate-composite-score.sh" ]; then
	bash "$SCRIPT_DIR/calculate-composite-score.sh" >/dev/null
fi

echo "✓ Promotion candidates updated"
