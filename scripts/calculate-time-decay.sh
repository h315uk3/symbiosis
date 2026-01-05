#!/bin/bash
set -euo pipefail
# Calculate time decay scores for patterns

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
CLAUDE_DIR="${CLAUDE_DIR:-$PROJECT_ROOT/.claude}"
TRACKER_FILE="$CLAUDE_DIR/as-you/pattern-tracker.json"

# Check if tracker file exists
if [ ! -f "$TRACKER_FILE" ]; then
	echo "Error: pattern-tracker.json not found" >&2
	exit 1
fi

# Decay parameter (lambda)
# λ = 0.1 means score reduces to ~37% after 10 days
LAMBDA=${DECAY_LAMBDA:-0.1}

# Get current epoch time
CURRENT_EPOCH=$(date +%s)

# Create temporary file for processing
TEMP_FILE=$(mktemp)
cp "$TRACKER_FILE" "$TEMP_FILE"

# Process each pattern
jq -r '.patterns | keys[]' "$TRACKER_FILE" | while IFS= read -r word; do
	# Skip if empty
	[ -z "$word" ] && continue
	
	# Get pattern data
	COUNT=$(jq -r ".patterns.\"$word\".count" "$TRACKER_FILE")
	LAST_SEEN=$(jq -r ".patterns.\"$word\".last_seen" "$TRACKER_FILE")
	
	# Convert last_seen to epoch time
	LAST_EPOCH=$(date -d "$LAST_SEEN" +%s 2>/dev/null || echo "$CURRENT_EPOCH")
	
	# Calculate days since last seen
	DAYS_AGO=$(((CURRENT_EPOCH - LAST_EPOCH) / 86400))
	
	# Calculate decay score: count * e^(-λ * days)
	DECAY_SCORE=$(awk -v count="$COUNT" -v lambda="$LAMBDA" -v days="$DAYS_AGO" \
		'BEGIN {
			decay = exp(-lambda * days)
			score = count * decay
			printf "%.6f", score
		}')
	
	# Calculate recency bonus (0-1 scale, higher for recent patterns)
	# 0 days = 1.0, 10 days = 0.37, 30 days = 0.05
	RECENCY_SCORE=$(awk -v lambda="$LAMBDA" -v days="$DAYS_AGO" \
		'BEGIN {
			recency = exp(-lambda * days)
			printf "%.6f", recency
		}')
	
	# Update tracker with decay scores
	jq ".patterns.\"$word\".decay_score = $DECAY_SCORE | \
	    .patterns.\"$word\".recency_score = $RECENCY_SCORE | \
	    .patterns.\"$word\".days_since_use = $DAYS_AGO" "$TEMP_FILE" >"$TEMP_FILE.new"
	mv "$TEMP_FILE.new" "$TEMP_FILE"
done

# Write back to tracker file
mv "$TEMP_FILE" "$TRACKER_FILE"

echo "Time decay scores calculated for all patterns"
