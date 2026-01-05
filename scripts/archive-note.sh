#!/bin/bash
set -euo pipefail
# Archive session notes to session-archive

# Load common library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

# Initialize paths
init_paths

MEMO_FILE="$CLAUDE_DIR/as-you/session-notes.local.md"
ARCHIVE_DIR="$CLAUDE_DIR/as-you/session-archive"

# Ensure archive directory exists
ensure_dir "$ARCHIVE_DIR"

# Check if memo file exists and is not empty
if [ ! -f "$MEMO_FILE" ] || [ ! -s "$MEMO_FILE" ]; then
	# No memo or empty memo - skip archiving
	exit 0
fi

# Archive with date
DATE=$(date +%Y-%m-%d)
ARCHIVE_FILE="$ARCHIVE_DIR/$DATE.md"

# If archive for today already exists, append; otherwise create
if [ -f "$ARCHIVE_FILE" ]; then
	{
		echo ""
		echo "---"
		echo ""
		cat "$MEMO_FILE"
	} >>"$ARCHIVE_FILE"
else
	cp "$MEMO_FILE" "$ARCHIVE_FILE"
fi

log_info "Memo archived to $DATE.md"
