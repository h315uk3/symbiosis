#!/bin/bash
set -euo pipefail
# Detect patterns from archived memos using simple word frequency

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
CLAUDE_DIR="${CLAUDE_DIR:-$PROJECT_ROOT/.claude}"
ARCHIVE_DIR="$CLAUDE_DIR/as-you/session-archive"

# Check if archive directory exists
if [ ! -d "$ARCHIVE_DIR" ]; then
	echo "[]"
	exit 0
fi

# Check if there are any archives
if ! ls "$ARCHIVE_DIR"/*.md >/dev/null 2>&1; then
	echo "[]"
	exit 0
fi

# Extract words from all archives, count frequency
# Filter: minimum 3 characters, exclude common words
cat "$ARCHIVE_DIR"/*.md 2>/dev/null |
	# Remove timestamps [HH:MM]
	sed 's/\[[0-9][0-9]:[0-9][0-9]\]//g' |
	# Extract words (English only for now, 3+ chars)
	grep -oE '[a-zA-Z]{3,}' |
	# Convert to lowercase
	tr '[:upper:]' '[:lower:]' |
	# Count frequency
	sort | uniq -c | sort -rn |
	# Output top 20
	head -20 |
	# Format as JSON array
	awk 'BEGIN{printf "["} {printf "%s{\"word\":\"%s\",\"count\":%d}", (NR>1?",":""), $2, $1} END{printf "]\n"}'
