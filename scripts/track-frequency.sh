#!/bin/bash
set -euo pipefail
# Track word frequency and update pattern-tracker.json

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
CLAUDE_DIR="${CLAUDE_DIR:-$PROJECT_ROOT/.claude}"
ARCHIVE_DIR="$CLAUDE_DIR/as-you/session-archive"
TRACKER_FILE="$PROJECT_ROOT/.claude/as-you/pattern-tracker.json"

# Ensure archive directory exists
mkdir -p "$ARCHIVE_DIR"

# Get current date
CURRENT_DATE=$(date +%Y-%m-%d)

# Get detected patterns
PATTERNS=$("$SCRIPT_DIR/detect-patterns.sh")

# Initialize tracker if not exists or empty
if [ ! -f "$TRACKER_FILE" ] || [ ! -s "$TRACKER_FILE" ]; then
	echo '{"patterns":{},"promotion_candidates":[],"cooccurrences":[]}' >"$TRACKER_FILE"
fi

# Validate JSON structure
if ! jq empty "$TRACKER_FILE" 2>/dev/null; then
	echo "Warning: Invalid JSON in tracker file, reinitializing..."
	echo '{"patterns":{},"promotion_candidates":[],"cooccurrences":[]}' >"$TRACKER_FILE"
fi

# Create temporary file for processing
TEMP_FILE=$(mktemp)
cat "$TRACKER_FILE" >"$TEMP_FILE"

# Process each pattern
echo "$PATTERNS" | jq -c '.[]' | while IFS= read -r pattern_obj; do
	WORD=$(echo "$pattern_obj" | jq -r '.word')
	COUNT=$(echo "$pattern_obj" | jq -r '.count')

	[ -z "$WORD" ] && continue

	# Check if pattern already exists
	if jq -e ".patterns.\"$WORD\"" "$TEMP_FILE" >/dev/null 2>&1; then
		# Update existing pattern: increment total count
		OLD_COUNT=$(jq -r ".patterns.\"$WORD\".count" "$TEMP_FILE")
		NEW_COUNT=$((OLD_COUNT + COUNT))

		# Check if today already in sessions
		HAS_TODAY=$(jq -r ".patterns.\"$WORD\".sessions // [] | any(. == \"$CURRENT_DATE\")" "$TEMP_FILE")

		if [ "$HAS_TODAY" = "false" ]; then
			# Add today to sessions
			jq ".patterns.\"$WORD\".count = $NEW_COUNT | \
                .patterns.\"$WORD\".last_seen = \"$CURRENT_DATE\" | \
                .patterns.\"$WORD\".sessions += [\"$CURRENT_DATE\"]" "$TEMP_FILE" >"$TEMP_FILE.new"
		else
			# Just update count and last_seen
			jq ".patterns.\"$WORD\".count = $NEW_COUNT | \
                .patterns.\"$WORD\".last_seen = \"$CURRENT_DATE\"" "$TEMP_FILE" >"$TEMP_FILE.new"
		fi
		mv "$TEMP_FILE.new" "$TEMP_FILE"
	else
		# Add new pattern
		jq ".patterns.\"$WORD\" = {
            \"count\": $COUNT,
            \"last_seen\": \"$CURRENT_DATE\",
            \"sessions\": [\"$CURRENT_DATE\"],
            \"promoted\": false
        }" "$TEMP_FILE" >"$TEMP_FILE.new"
		mv "$TEMP_FILE.new" "$TEMP_FILE"
	fi
done

# Extract contexts for patterns
CONTEXTS=$("$SCRIPT_DIR/extract-contexts.sh")

# Detect co-occurrences
COOCCURRENCES=$("$SCRIPT_DIR/detect-cooccurrence.sh")

# Merge contexts into tracker
echo "$CONTEXTS" | jq -r '.patterns | to_entries | .[] | "\(.key)\t\(.value.contexts | @json)"' |
	while IFS=$'\t' read -r word contexts_json; do
		[ -z "$word" ] && continue

		if jq -e ".patterns.\"$word\"" "$TEMP_FILE" >/dev/null 2>&1; then
			jq ".patterns.\"$word\".contexts = $contexts_json" "$TEMP_FILE" >"$TEMP_FILE.new"
			mv "$TEMP_FILE.new" "$TEMP_FILE"
		fi
	done

# Add co-occurrences to tracker
jq ".cooccurrences = $COOCCURRENCES" "$TEMP_FILE" >"$TRACKER_FILE"

# Calculate advanced scoring metrics
echo "Calculating TF-IDF scores..."
"$SCRIPT_DIR/calculate-tfidf.sh"

echo "Calculating PMI scores..."
"$SCRIPT_DIR/calculate-pmi.sh"

echo "Calculating time decay scores..."
"$SCRIPT_DIR/calculate-time-decay.sh"

echo "Calculating composite scores..."
"$SCRIPT_DIR/calculate-composite-score.sh"

rm -f "$TEMP_FILE" "$TEMP_FILE.new"

PATTERN_COUNT=$(jq '.patterns | length' "$TRACKER_FILE")
CANDIDATE_COUNT=$(jq '.promotion_candidates | length' "$TRACKER_FILE")

echo "Frequency tracker updated: $PATTERN_COUNT patterns tracked, $CANDIDATE_COUNT promotion candidates (scored)"
