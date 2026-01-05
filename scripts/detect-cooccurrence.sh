#!/bin/bash
set -u
# Detect word co-occurrences within same memo lines

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
CLAUDE_DIR="${CLAUDE_DIR:-$PROJECT_ROOT/.claude}"
ARCHIVE_DIR="$CLAUDE_DIR/as-you/session-archive"

# Check if archive directory exists
if [ ! -d "$ARCHIVE_DIR" ]; then
	echo "[]"
	exit 0
fi

# Create temporary file for word pairs
TEMP_PAIRS=$(mktemp)

# Process each archive file
cat "$ARCHIVE_DIR"/*.md 2>/dev/null |
	# Remove timestamps
	sed 's/\[[0-9][0-9]:[0-9][0-9]\]//g' |
	# Process line by line
	while IFS= read -r line; do
		# Extract words from line (3+ chars, lowercase)
		words=$(echo "$line" | grep -oE '[a-zA-Z]{3,}' | tr '[:upper:]' '[:lower:]' | sort -u)

		# Skip empty lines or lines without words
		if [ -z "$words" ] || [ "$words" = "" ]; then
			continue
		fi

		# Convert words to array (compatible with bash 3.2+)
		read -r -a word_array <<< "$words"
		word_count=${#word_array[@]}
		
		# Need at least 2 words for a pair
		if [ "$word_count" -lt 2 ]; then
			continue
		fi

		# Generate all pairs (combinations)
		for ((i = 0; i < word_count; i++)); do
			for ((j = i + 1; j < word_count; j++)); do
				word1="${word_array[i]}"
				word2="${word_array[j]}"

				# Sort pair alphabetically to avoid duplicates (A,B) vs (B,A)
				if [[ "$word1" < "$word2" ]]; then
					echo "$word1,$word2"
				else
					echo "$word2,$word1"
				fi
			done
		done
	done >"$TEMP_PAIRS"

# Count pair frequencies and output top 20 as JSON
if [ -s "$TEMP_PAIRS" ]; then
	sort "$TEMP_PAIRS" | uniq -c | sort -rn | head -20 |
		awk 'BEGIN{print "["}
        {
            split($2, words, ",")
            printf "%s{\"words\":[\"%s\",\"%s\"],\"count\":%d}",
                (NR>1?",":""), words[1], words[2], $1
        }
        END{print "]"}'
else
	echo "[]"
fi

rm -f "$TEMP_PAIRS"
