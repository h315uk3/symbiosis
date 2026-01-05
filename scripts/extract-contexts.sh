#!/bin/bash
set -u
# Extract contexts for frequent patterns from archived memos

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
CLAUDE_DIR="${CLAUDE_DIR:-$PROJECT_ROOT/.claude}"
ARCHIVE_DIR="$CLAUDE_DIR/as-you/session-archive"
TRACKER_FILE="$PROJECT_ROOT/.claude/as-you/pattern-tracker.json"

# Output empty JSON if no tracker file
if [ ! -f "$TRACKER_FILE" ]; then
	echo "{}"
	exit 0
fi

# Read top patterns from tracker (top 10 by count)
PATTERNS=$(jq -r '.patterns | to_entries | sort_by(-.value.count) | .[0:10] | .[] | .key' "$TRACKER_FILE" 2>/dev/null)

if [ -z "$PATTERNS" ]; then
	echo "{}"
	exit 0
fi

# Initialize JSON output
echo "{"
echo "  \"patterns\": {"

FIRST=true
while IFS= read -r pattern; do
	# Skip empty lines
	[ -z "$pattern" ] && continue

	# Add comma separator
	if [ "$FIRST" = true ]; then
		FIRST=false
	else
		echo ","
	fi

	echo -n "    \"$pattern\": {"

	# Get count from tracker
	COUNT=$(jq -r ".patterns[\"$pattern\"].count // 0" "$TRACKER_FILE" 2>/dev/null)
	echo -n "\"count\": $COUNT, \"contexts\": ["

	# Extract contexts (grep with context lines)
	CONTEXTS=$(grep -i -h -B 1 -A 1 "$pattern" "$ARCHIVE_DIR"/*.md 2>/dev/null |
		grep -v "^--$" |
		sed 's/"/\\"/g' |
		head -5)

	# Format contexts as JSON array
	FIRST_CTX=true
	while IFS= read -r line; do
		[ -z "$line" ] && continue

		if [ "$FIRST_CTX" = true ]; then
			FIRST_CTX=false
		else
			echo -n ", "
		fi
		echo -n "\"$line\""
	done <<<"$CONTEXTS"

	echo -n "]}"
done <<<"$PATTERNS"

echo ""
echo "  }"
echo "}"
