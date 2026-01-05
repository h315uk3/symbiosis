#!/bin/bash
set -u
# Calculate composite scores combining TF-IDF, time decay, and session spread

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
CLAUDE_DIR="${CLAUDE_DIR:-$PROJECT_ROOT/.claude}"
TRACKER_FILE="$CLAUDE_DIR/as-you/pattern-tracker.json"

# Check if tracker file exists
if [ ! -f "$TRACKER_FILE" ]; then
	echo "Error: pattern-tracker.json not found" >&2
	exit 1
fi

# Weights for composite score
WEIGHT_TFIDF=${WEIGHT_TFIDF:-0.4}      # 40% weight on TF-IDF (importance)
WEIGHT_RECENCY=${WEIGHT_RECENCY:-0.3}  # 30% weight on recency (freshness)
WEIGHT_SPREAD=${WEIGHT_SPREAD:-0.3}    # 30% weight on session spread (consistency)

# Create temporary file for processing
TEMP_FILE=$(mktemp)
cp "$TRACKER_FILE" "$TEMP_FILE"

# Get max values for normalization
MAX_TFIDF=$(jq '[.patterns[].tfidf // 0] | max // 1' "$TRACKER_FILE")
MAX_SESSIONS=$(jq '[.patterns[].sessions | length] | max // 1' "$TRACKER_FILE")

# Ensure valid numbers
if [ -z "$MAX_TFIDF" ] || [ "$MAX_TFIDF" = "null" ]; then
	MAX_TFIDF=1
fi
if [ -z "$MAX_SESSIONS" ] || [ "$MAX_SESSIONS" = "null" ]; then
	MAX_SESSIONS=1
fi

# Avoid division by zero using awk for float comparison
MAX_TFIDF=$(awk -v val="$MAX_TFIDF" 'BEGIN {if (val == 0) print 1; else print val}')
MAX_SESSIONS=$(awk -v val="$MAX_SESSIONS" 'BEGIN {if (val == 0) print 1; else print val}')

# Process each pattern
jq -r '.patterns | keys[]' "$TRACKER_FILE" | while IFS= read -r word; do
	# Skip if empty
	[ -z "$word" ] && continue
	
	# Get pattern data
	TFIDF=$(jq -r ".patterns.\"$word\".tfidf // 0" "$TRACKER_FILE")
	RECENCY=$(jq -r ".patterns.\"$word\".recency_score // 0" "$TRACKER_FILE")
	SESSIONS=$(jq -r ".patterns.\"$word\".sessions | length" "$TRACKER_FILE")
	IS_STOPWORD=$(jq -r ".patterns.\"$word\".is_stopword // false" "$TRACKER_FILE")
	PROMOTED=$(jq -r ".patterns.\"$word\".promoted // false" "$TRACKER_FILE")
	
	# Normalize values to 0-1 range
	NORM_TFIDF=$(awk -v val="$TFIDF" -v max="$MAX_TFIDF" \
		'BEGIN {printf "%.6f", val / max}')
	
	NORM_SPREAD=$(awk -v val="$SESSIONS" -v max="$MAX_SESSIONS" \
		'BEGIN {printf "%.6f", val / max}')
	
	# Calculate composite score
	COMPOSITE=$(awk -v tfidf="$NORM_TFIDF" -v recency="$RECENCY" -v spread="$NORM_SPREAD" \
		-v w_tfidf="$WEIGHT_TFIDF" -v w_recency="$WEIGHT_RECENCY" -v w_spread="$WEIGHT_SPREAD" \
		'BEGIN {
			score = (tfidf * w_tfidf) + (recency * w_recency) + (spread * w_spread)
			printf "%.6f", score
		}')
	
	# Apply penalties
	FINAL_SCORE="$COMPOSITE"
	
	# Penalty for stopwords (reduce by 50%)
	if [ "$IS_STOPWORD" = "true" ]; then
		FINAL_SCORE=$(awk -v score="$COMPOSITE" 'BEGIN {printf "%.6f", score * 0.5}')
	fi
	
	# Zero score for already promoted patterns
	if [ "$PROMOTED" = "true" ]; then
		FINAL_SCORE="0.000000"
	fi
	
	# Update tracker with composite score
	jq ".patterns.\"$word\".composite_score = $FINAL_SCORE" "$TEMP_FILE" >"$TEMP_FILE.new"
	mv "$TEMP_FILE.new" "$TEMP_FILE"
done

# Update promotion candidates based on composite score
# Select top patterns with composite_score > 0.3 and not promoted
jq '.promotion_candidates = ([
	.patterns | to_entries[] |
	select((.value.composite_score // 0) > 0.3 and (.value.promoted // false) == false) |
	{
		pattern: .key,
		composite_score: (.value.composite_score // 0),
		count: (.value.count // 0),
		sessions: ((.value.sessions // []) | length),
		tfidf: (.value.tfidf // 0),
		recency_score: (.value.recency_score // 0),
		is_stopword: (.value.is_stopword // false),
		reason: (
			if (.value.is_stopword // false) then
				"Stopword (score reduced)"
			elif ((.value.composite_score // 0) > 0.7) then
				"High score: TF-IDF=\((.value.tfidf // 0) | tostring | .[0:5]), recently used"
			elif ((.value.composite_score // 0) > 0.5) then
				"Medium score: used across multiple sessions"
			else
				"Low score: candidate for review"
			end
		)
	}
] | sort_by(-(.composite_score // 0)) | .[0:20])' "$TEMP_FILE" >"$TEMP_FILE.new"

# Write back to tracker file
mv "$TEMP_FILE.new" "$TRACKER_FILE"

# Show summary
CANDIDATE_COUNT=$(jq '.promotion_candidates | length' "$TRACKER_FILE")
echo "Composite scores calculated for all patterns"
echo "Top $CANDIDATE_COUNT promotion candidates identified"
