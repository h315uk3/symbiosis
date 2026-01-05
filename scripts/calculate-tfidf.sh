#!/bin/bash
set -u
# Calculate TF-IDF scores for patterns (Unicode-aware)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
CLAUDE_DIR="${CLAUDE_DIR:-$PROJECT_ROOT/.claude}"
ARCHIVE_DIR="$CLAUDE_DIR/as_you/session_archive"
TRACKER_FILE="$CLAUDE_DIR/as_you/pattern_tracker.json"

# Check if tracker file exists
if [ ! -f "$TRACKER_FILE" ]; then
	echo "Error: pattern_tracker.json not found" >&2
	exit 1
fi

# Check if archive directory exists
if [ ! -d "$ARCHIVE_DIR" ]; then
	echo "Error: archive directory not found" >&2
	exit 1
fi

# Count total documents (sessions)
TOTAL_DOCS=$(find "$ARCHIVE_DIR" -name "*.md" -type f 2>/dev/null | wc -l)
if [ "$TOTAL_DOCS" -eq 0 ]; then
	echo "Error: no archive files found" >&2
	exit 1
fi

# Create temporary file for processing
TEMP_FILE=$(mktemp)
cp "$TRACKER_FILE" "$TEMP_FILE"

# English stopwords list (can be extended for other languages)
STOPWORDS="and|the|for|with|that|this|from|have|has|had|but|not|are|was|were|been|being|you|your|they|their|what|which|who|when|where|why|how|can|could|would|should|will|shall|may|might|must"

# Common Japanese particles and auxiliaries (optional, can be extended)
JP_STOPWORDS="です|ます|した|する|される|いる|ある|なる|くる|できる|という|ため|こと|もの|ところ|とき|など"

# Process each pattern
jq -r '.patterns | keys[]' "$TRACKER_FILE" | while IFS= read -r word; do
	# Skip if empty
	[ -z "$word" ] && continue

	# Get word count (TF)
	TF=$(jq -r ".patterns.\"$word\".count" "$TRACKER_FILE")

	# Count documents containing this pattern (Unicode-aware, case-insensitive)
	# Use perl for proper Unicode handling
	DOC_FREQ=$(perl -CS -ne "
		use utf8;
		binmode(STDIN, ':utf8');
		print \"\$ARGV\\n\" if /\Q$word\E/i;
	" "$ARCHIVE_DIR"/*.md 2>/dev/null | sort -u | wc -l)

	# Calculate IDF: log(N / df)
	# Add 1 to doc_freq to avoid division by zero
	IDF=$(echo "scale=6; l($TOTAL_DOCS / ($DOC_FREQ + 1))" | bc -l)

	# Calculate TF-IDF
	TFIDF=$(echo "scale=6; $TF * $IDF" | bc -l)

	# Check if word is a stopword (English or Japanese)
	IS_STOPWORD="false"
	if echo "$word" | grep -qiE "^($STOPWORDS)$"; then
		IS_STOPWORD="true"
	elif echo "$word" | perl -CS -ne "use utf8; exit(1) unless /^($JP_STOPWORDS)\$/i"; then
		IS_STOPWORD="true"
	fi

	# Update tracker with TF-IDF score
	jq ".patterns.\"$word\".tfidf = $TFIDF | \
	    .patterns.\"$word\".idf = $IDF | \
	    .patterns.\"$word\".is_stopword = $IS_STOPWORD" "$TEMP_FILE" >"$TEMP_FILE.new"
	mv "$TEMP_FILE.new" "$TEMP_FILE"
done

# Write back to tracker file
mv "$TEMP_FILE" "$TRACKER_FILE"

echo "TF-IDF scores calculated for all patterns"
