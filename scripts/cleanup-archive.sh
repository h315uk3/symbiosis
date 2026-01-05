#!/bin/bash
set -euo pipefail
# Clean up old archives (older than 7 days)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
CLAUDE_DIR="${CLAUDE_DIR:-$PROJECT_ROOT/.claude}"
ARCHIVE_DIR="$CLAUDE_DIR/as-you/session-archive"

# Check if archive directory exists
if [ ! -d "$ARCHIVE_DIR" ]; then
	exit 0
fi

# Delete files older than 7 days
find "$ARCHIVE_DIR" -name "*.md" -type f -mtime +7 -delete

# Count remaining archives
COUNT=$(find "$ARCHIVE_DIR" -name "*.md" -type f | wc -l)
echo "Cleaned up old archives. $COUNT archives remaining."
