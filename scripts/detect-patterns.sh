#!/bin/bash
set -u
# Detect patterns from archived memos using language-agnostic tokenization

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
CLAUDE_DIR="${CLAUDE_DIR:-$PROJECT_ROOT/.claude}"
ARCHIVE_DIR="$CLAUDE_DIR/as_you/session_archive"

# Check if archive directory exists
if [ ! -d "$ARCHIVE_DIR" ]; then
	echo "[]"
	exit 0
fi

# Check if there are any archives
if ! ls "$ARCHIVE_DIR"/*.md >/dev/null 2>&1; then
	echo "[]"
	exit 0
fi

# Extract patterns from all archives using Unicode-aware tokenization
# Approach:
# 1. Space-delimited tokens (English, etc.): extract as words
# 2. Non-space scripts (Japanese, Chinese, etc.): extract as 3-grams
cat "$ARCHIVE_DIR"/*.md 2>/dev/null |
	# Remove timestamps [HH:MM]
	sed 's/\[[0-9][0-9]:[0-9][0-9]\]//g' |
	# Unicode-aware tokenization using Perl
	perl -CS -nle '
		use utf8;
		binmode(STDOUT, ":utf8");

		# Extract space-delimited words (3+ chars, letters/numbers)
		while (/(\p{L}[\p{L}\p{N}]{2,})/g) {
			print lc($1);
		}

		# Extract 3-grams from non-space scripts (CJK, etc.)
		# Remove spaces first to get continuous text
		my $text = $_;
		$text =~ s/\s+//g;

		# Extract 3-character sequences from CJK and similar scripts
		while ($text =~ /(?=([\p{Han}\p{Hiragana}\p{Katakana}\p{Hangul}]{3}))/g) {
			print $1;
		}
	' |
	# Count frequency
	sort | uniq -c | sort -rn |
	# Output top 20
	head -20 |
	# Format as JSON array with proper escaping
	perl -MJSON::PP -e '
		use utf8;
		binmode(STDIN, ":utf8");
		binmode(STDOUT, ":utf8");
		my @patterns;
		while (<>) {
			if (/^\s*(\d+)\s+(.+)$/) {
				push @patterns, {word => $2, count => int($1)};
			}
		}
		print JSON::PP->new->utf8(0)->encode(\@patterns);
	'
