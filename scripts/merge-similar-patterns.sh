#!/bin/bash
set -euo pipefail
# Merge similar patterns based on Levenshtein distance

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
CLAUDE_DIR="${CLAUDE_DIR:-$PROJECT_ROOT/.claude}"
TRACKER_FILE="$CLAUDE_DIR/as-you/pattern-tracker.json"

# Check if tracker file exists
if [ ! -f "$TRACKER_FILE" ]; then
	echo "Error: pattern-tracker.json not found" >&2
	exit 1
fi

# Detect similar patterns
SIMILAR=$("$SCRIPT_DIR/detect-similar-patterns.sh")

# Count similar pairs
SIMILAR_COUNT=$(echo "$SIMILAR" | jq 'length')

if [ "$SIMILAR_COUNT" -eq 0 ]; then
	echo "No similar patterns found"
	exit 0
fi

echo "Found $SIMILAR_COUNT similar pattern pair(s)"
echo ""

# Create backup
BACKUP_FILE="$TRACKER_FILE.backup.$(date +%Y%m%d_%H%M%S)"
cp "$TRACKER_FILE" "$BACKUP_FILE"
echo "✓ Created backup: $BACKUP_FILE"
echo ""

# Create temporary file for processing
TEMP_FILE=$(mktemp)
cp "$TRACKER_FILE" "$TEMP_FILE"

# Track merged patterns
MERGED_PATTERNS=$(mktemp)

# Process each similar pair
echo "$SIMILAR" | jq -c '.[]' | while IFS= read -r pair; do
	PATTERN1=$(echo "$pair" | jq -r '.patterns[0]')
	PATTERN2=$(echo "$pair" | jq -r '.patterns[1]')
	DISTANCE=$(echo "$pair" | jq -r '.distance')
	SUGGESTION=$(echo "$pair" | jq -r '.suggestion')
	
	# Skip if already merged
	if grep -q "^$PATTERN1$" "$MERGED_PATTERNS" 2>/dev/null || \
	   grep -q "^$PATTERN2$" "$MERGED_PATTERNS" 2>/dev/null; then
		continue
	fi
	
	echo "Merging: '$PATTERN1' + '$PATTERN2' → '$SUGGESTION' (distance: $DISTANCE)"
	
	# Determine which to keep and which to merge
	if [ "$SUGGESTION" = "$PATTERN1" ]; then
		KEEP="$PATTERN1"
		MERGE="$PATTERN2"
	else
		KEEP="$PATTERN2"
		MERGE="$PATTERN1"
	fi
	
	# Get data from both patterns
	KEEP_DATA=$(jq ".patterns.\"$KEEP\"" "$TEMP_FILE")
	MERGE_DATA=$(jq ".patterns.\"$MERGE\"" "$TEMP_FILE")
	
	# Merge counts
	NEW_COUNT=$(jq -n "$KEEP_DATA.count + $MERGE_DATA.count")
	
	# Merge sessions (unique)
	NEW_SESSIONS=$(jq -n "($KEEP_DATA.sessions + $MERGE_DATA.sessions) | unique")
	
	# Merge contexts (unique, limited to 10)
	NEW_CONTEXTS=$(jq -n \
		"(($KEEP_DATA.contexts // []) + ($MERGE_DATA.contexts // [])) | unique | .[0:10]")
	
	# Get most recent last_seen
	KEEP_DATE=$(echo "$KEEP_DATA" | jq -r '.last_seen')
	MERGE_DATE=$(echo "$MERGE_DATA" | jq -r '.last_seen')
	if [[ "$KEEP_DATE" > "$MERGE_DATE" ]]; then
		NEW_LAST_SEEN="$KEEP_DATE"
	else
		NEW_LAST_SEEN="$MERGE_DATE"
	fi
	
	# Update the kept pattern with merged data
	jq ".patterns.\"$KEEP\".count = $NEW_COUNT | \
	    .patterns.\"$KEEP\".sessions = $NEW_SESSIONS | \
	    .patterns.\"$KEEP\".contexts = $NEW_CONTEXTS | \
	    .patterns.\"$KEEP\".last_seen = \"$NEW_LAST_SEEN\" | \
	    .patterns.\"$KEEP\".merged_from = [\"\$MERGE\"] | \
	    del(.patterns.\"$MERGE\")" "$TEMP_FILE" >"$TEMP_FILE.new"
	
	mv "$TEMP_FILE.new" "$TEMP_FILE"
	
	# Record merged patterns
	echo "$MERGE" >>"$MERGED_PATTERNS"
	
	echo "  ✓ Merged into '$KEEP' (new count: $NEW_COUNT)"
	echo ""
done

# Write back to tracker file
mv "$TEMP_FILE" "$TRACKER_FILE"

# Recalculate all scores
echo "Recalculating scores..."
bash "$SCRIPT_DIR/calculate-tfidf.sh" >/dev/null
bash "$SCRIPT_DIR/calculate-pmi.sh" >/dev/null
bash "$SCRIPT_DIR/calculate-time-decay.sh" >/dev/null
bash "$SCRIPT_DIR/calculate-composite-score.sh" >/dev/null

rm -f "$MERGED_PATTERNS"

FINAL_PATTERN_COUNT=$(jq '.patterns | length' "$TRACKER_FILE")
echo "✓ Merge complete. Total patterns: $FINAL_PATTERN_COUNT"
