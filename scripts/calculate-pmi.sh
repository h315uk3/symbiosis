#!/bin/bash
set -u
# Calculate PMI (Pointwise Mutual Information) scores for word co-occurrences (Unicode-aware)

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

# Count total pattern occurrences across all archives (Unicode-aware)
TOTAL_WORDS=$(cat "$ARCHIVE_DIR"/*.md 2>/dev/null |
	sed 's/\[[0-9][0-9]:[0-9][0-9]\]//g' |
	perl -CS -nle '
		use utf8;

		# Count space-delimited words (3+ chars)
		my $count = 0;
		while (/(\p{L}[\p{L}\p{N}]{2,})/g) {
			$count++;
		}

		# Count 3-grams from CJK scripts
		my $text = $_;
		$text =~ s/\s+//g;
		while ($text =~ /(?=([\p{Han}\p{Hiragana}\p{Katakana}\p{Hangul}]{3}))/g) {
			$count++;
		}

		print $count;
	' |
	awk '{sum += $1} END {print sum}')

if [ "$TOTAL_WORDS" -eq 0 ]; then
	echo "Error: no patterns found in archives" >&2
	exit 1
fi

# Create temporary file for processing
TEMP_FILE=$(mktemp)
cp "$TRACKER_FILE" "$TEMP_FILE"

# Process each co-occurrence
jq -c '.cooccurrences[]?' "$TRACKER_FILE" 2>/dev/null | while IFS= read -r cooccur; do
	WORD1=$(echo "$cooccur" | jq -r '.words[0]')
	WORD2=$(echo "$cooccur" | jq -r '.words[1]')
	COOCCUR_COUNT=$(echo "$cooccur" | jq -r '.count')

	# Skip if empty
	[ -z "$WORD1" ] || [ -z "$WORD2" ] && continue

	# Get individual word counts from patterns
	WORD1_COUNT=$(jq -r ".patterns.\"$WORD1\".count // 0" "$TRACKER_FILE")
	WORD2_COUNT=$(jq -r ".patterns.\"$WORD2\".count // 0" "$TRACKER_FILE")

	# Skip if either word count is 0
	[ "$WORD1_COUNT" -eq 0 ] || [ "$WORD2_COUNT" -eq 0 ] && continue

	# Calculate probabilities
	# P(A,B) = cooccur_count / total_words
	# P(A) = word1_count / total_words
	# P(B) = word2_count / total_words

	# PMI = log(P(A,B) / (P(A) * P(B)))
	#     = log((cooccur_count / total) / ((word1_count / total) * (word2_count / total)))
	#     = log(cooccur_count * total / (word1_count * word2_count))

	PMI=$(awk -v cc="$COOCCUR_COUNT" -v tw="$TOTAL_WORDS" \
		-v w1="$WORD1_COUNT" -v w2="$WORD2_COUNT" \
		'BEGIN {
			if (w1 == 0 || w2 == 0) {
				print 0
			} else {
				p_ab = cc / tw
				p_a = w1 / tw
				p_b = w2 / tw
				if (p_ab > 0 && p_a > 0 && p_b > 0) {
					pmi = log(p_ab / (p_a * p_b))
					printf "%.6f", pmi
				} else {
					print 0
				}
			}
		}')

	# Update cooccurrences array with PMI score
	jq "(.cooccurrences[] | select(.words[0] == \"$WORD1\" and .words[1] == \"$WORD2\") | .pmi) = $PMI" \
		"$TEMP_FILE" >"$TEMP_FILE.new"
	mv "$TEMP_FILE.new" "$TEMP_FILE"
done

# Write back to tracker file
mv "$TEMP_FILE" "$TRACKER_FILE"

echo "PMI scores calculated for all co-occurrences"
