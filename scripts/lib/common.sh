#!/bin/bash
set -u
# Common utility functions for As You plugin scripts

# Initialize standard paths
# Usage: init_paths
# Sets: SCRIPT_DIR, REPO_ROOT, PROJECT_ROOT, CLAUDE_DIR
init_paths() {
	SCRIPT_DIR="${SCRIPT_DIR:-$(cd "$(dirname "${BASH_SOURCE[1]}")" && pwd)}"
	REPO_ROOT="${REPO_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
	PROJECT_ROOT="${PROJECT_ROOT:-$REPO_ROOT}"
	CLAUDE_DIR="${CLAUDE_DIR:-$PROJECT_ROOT/.claude}"

	export SCRIPT_DIR REPO_ROOT PROJECT_ROOT CLAUDE_DIR
}

# Ensure directory exists
# Usage: ensure_dir "/path/to/dir"
ensure_dir() {
	local dir="$1"
	if [ ! -d "$dir" ]; then
		mkdir -p "$dir"
	fi
}

# Ensure file exists with default content
# Usage: ensure_file "/path/to/file" "default content"
ensure_file() {
	local file="$1"
	local default_content="${2:-}"

	if [ ! -f "$file" ]; then
		ensure_dir "$(dirname "$file")"
		echo "$default_content" > "$file"
	fi
}

# Initialize tracker JSON file
# Usage: init_tracker_file "/path/to/tracker.json"
init_tracker_file() {
	local tracker_file="$1"

	if [ ! -f "$tracker_file" ]; then
		ensure_dir "$(dirname "$tracker_file")"
		echo '{"patterns": {}, "promotion_candidates": []}' > "$tracker_file"
	fi
}

# Check if file exists, exit with error if not
# Usage: require_file "/path/to/file" "Error message"
require_file() {
	local file="$1"
	local error_msg="${2:-File not found: $file}"

	if [ ! -f "$file" ]; then
		echo "Error: $error_msg" >&2
		exit 1
	fi
}

# Log message with timestamp
# Usage: log_info "message"
log_info() {
	echo "[$(date +%H:%M:%S)] $*"
}

# Log error message with timestamp to stderr
# Usage: log_error "message"
log_error() {
	echo "[$(date +%H:%M:%S)] ERROR: $*" >&2
}

# Safe JSON read with jq
# Usage: json_get "/path/to/file.json" ".key.path" "default_value"
json_get() {
	local file="$1"
	local jq_path="$2"
	local default="${3:-null}"

	if [ ! -f "$file" ]; then
		echo "$default"
		return
	fi

	jq -r "$jq_path // $default" "$file" 2>/dev/null || echo "$default"
}

# Safe JSON write with atomic operation
# Usage: json_update "/path/to/file.json" ".key.path = value"
json_update() {
	local file="$1"
	local jq_expr="$2"
	local temp_file

	require_file "$file" "JSON file not found: $file"

	temp_file=$(mktemp)
	if jq "$jq_expr" "$file" > "$temp_file" 2>/dev/null; then
		mv "$temp_file" "$file"
	else
		rm -f "$temp_file"
		log_error "Failed to update JSON: $file"
		return 1
	fi
}

# Validate JSON file
# Usage: validate_json "/path/to/file.json"
validate_json() {
	local file="$1"

	if ! jq '.' "$file" >/dev/null 2>&1; then
		log_error "Invalid JSON: $file"
		return 1
	fi
	return 0
}

# Avoid division by zero in awk
# Usage: safe_divide numerator denominator
safe_divide() {
	local numerator="$1"
	local denominator="$2"

	awk -v num="$numerator" -v denom="$denominator" \
		'BEGIN {
			if (denom == 0) print 0
			else printf "%.6f", num / denom
		}'
}

# Get max value from JSON array
# Usage: json_max "/path/to/file.json" ".patterns[].count"
json_max() {
	local file="$1"
	local jq_path="$2"

	jq "[$jq_path] | max // 1" "$file" 2>/dev/null || echo "1"
}

# Initialize As You directory structure
# Usage: init_as_you_dirs
init_as_you_dirs() {
	init_paths

	local as_you_dir="$CLAUDE_DIR/as-you"
	ensure_dir "$as_you_dir"
	ensure_dir "$as_you_dir/session-archive"
	init_tracker_file "$as_you_dir/pattern-tracker.json"
}
