#!/bin/bash
set -u
# Detect similar patterns using Levenshtein distance

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
CLAUDE_DIR="${CLAUDE_DIR:-$PROJECT_ROOT/.claude}"
TRACKER_FILE="$CLAUDE_DIR/as-you/pattern-tracker.json"

# Load levenshtein function
# shellcheck source=scripts/levenshtein.sh
source "$SCRIPT_DIR/levenshtein.sh"

# Check if tracker file exists
if [ ! -f "$TRACKER_FILE" ]; then
	echo "[]"
	exit 0
fi

# Distance threshold (default: 2)
THRESHOLD=${SIMILARITY_THRESHOLD:-2}

# Create temporary file for results
TEMP_RESULTS=$(mktemp)

# Get all pattern names
PATTERNS=$(jq -r '.patterns | keys[]' "$TRACKER_FILE")

# Compare each pair of patterns
echo "$PATTERNS" | while IFS= read -r pattern1; do
	echo "$PATTERNS" | while IFS= read -r pattern2; do
		# Skip if same pattern or already processed (alphabetical order)
		if [[ "$pattern1" < "$pattern2" ]]; then
			# Calculate distance
			distance=$(levenshtein "$pattern1" "$pattern2")
			
			# If distance is within threshold, record it
			if [ "$distance" -le "$THRESHOLD" ]; then
				# Get pattern info
				count1=$(jq -r ".patterns.\"$pattern1\".count" "$TRACKER_FILE")
				count2=$(jq -r ".patterns.\"$pattern2\".count" "$TRACKER_FILE")
				composite1=$(jq -r ".patterns.\"$pattern1\".composite_score // 0" "$TRACKER_FILE")
				composite2=$(jq -r ".patterns.\"$pattern2\".composite_score // 0" "$TRACKER_FILE")
				
				# Output as JSON
				jq -n \
					--arg p1 "$pattern1" \
					--arg p2 "$pattern2" \
					--argjson dist "$distance" \
					--argjson c1 "$count1" \
					--argjson c2 "$count2" \
					--argjson s1 "$composite1" \
					--argjson s2 "$composite2" \
					'{
						patterns: [$p1, $p2],
						distance: $dist,
						counts: [$c1, $c2],
						scores: [$s1, $s2],
						total_count: ($c1 + $c2),
						suggestion: (if $c1 > $c2 then $p1 elif $c2 > $c1 then $p2 else $p1 end)
					}' >>"$TEMP_RESULTS"
			fi
		fi
	done
done

# Output results as JSON array
if [ -s "$TEMP_RESULTS" ]; then
	jq -s 'sort_by(-.total_count)' "$TEMP_RESULTS"
else
	echo "[]"
fi

rm -f "$TEMP_RESULTS"
