#!/bin/bash
# Simple test runner - replacement for bats
set -u

TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_result() {
    local name="$1"
    local status=$2

    TESTS_TOTAL=$((TESTS_TOTAL + 1))

    if [ $status -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} $name"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Test hooks
test_session_start() {
    local test_dir=$(mktemp -d)
    local claude_dir="$test_dir/.claude"
    mkdir -p "$claude_dir/as_you"

    (
        export PROJECT_ROOT="$test_dir"
        export CLAUDE_DIR="$claude_dir"
        bash hooks/session-start.sh > /dev/null 2>&1
    )
    local result=$?

    rm -rf "$test_dir"
    test_result "session-start.sh executes" $result
}

test_session_end() {
    local test_dir=$(mktemp -d)
    local claude_dir="$test_dir/.claude"
    mkdir -p "$claude_dir/as_you/session_archive"
    echo "test content" > "$claude_dir/as_you/session_notes.local.md"

    (
        export PROJECT_ROOT="$test_dir"
        export CLAUDE_DIR="$claude_dir"
        bash hooks/session-end.sh > /dev/null 2>&1
    )
    local result=$?

    rm -rf "$test_dir"
    test_result "session-end.sh executes" $result
}

test_track_frequency() {
    local test_dir=$(mktemp -d)
    local claude_dir="$test_dir/.claude"
    mkdir -p "$claude_dir/as_you/session_archive"
    echo "test deployment authentication" > "$claude_dir/as_you/session_archive/2025-01-05.md"

    (
        export PROJECT_ROOT="$test_dir"
        export CLAUDE_DIR="$claude_dir"
        bash scripts/track-frequency.sh > /dev/null 2>&1
    )
    local result=$?

    [ -f "$claude_dir/as_you/pattern_tracker.json" ] || result=1

    rm -rf "$test_dir"
    test_result "track-frequency.sh creates tracker" $result
}

test_plugin_json() {
    jq '.' .claude-plugin/plugin.json > /dev/null 2>&1
    test_result "plugin.json is valid JSON" $?
}

test_hooks_json() {
    jq '.' hooks/hooks.json > /dev/null 2>&1
    test_result "hooks.json is valid JSON" $?
}

# Test frontmatter validation
test_command_frontmatter() {
    local result=0
    for cmd in commands/*.md; do
        [ ! -f "$cmd" ] && continue
        if ! grep -q "^---$" "$cmd"; then
            result=1
            break
        fi
        if ! sed -n '/^---$/,/^---$/p' "$cmd" | grep -q "description:"; then
            result=1
            break
        fi
    done
    test_result "All commands have valid frontmatter" $result
}

test_agent_frontmatter() {
    local result=0
    for agent in agents/*.md; do
        [ ! -f "$agent" ] && continue
        if ! grep -q "^---$" "$agent"; then
            result=1
            break
        fi
        if ! sed -n '/^---$/,/^---$/p' "$agent" | grep -q "description:"; then
            result=1
            break
        fi
    done
    test_result "All agents have valid frontmatter" $result
}

test_skill_frontmatter() {
    local result=0
    for skill_dir in skills/*/; do
        [ ! -d "$skill_dir" ] && continue
        skill_file="${skill_dir}SKILL.md"
        [ ! -f "$skill_file" ] && continue
        if ! grep -q "^---$" "$skill_file"; then
            result=1
            break
        fi
        if ! sed -n '/^---$/,/^---$/p' "$skill_file" | grep -q "description:"; then
            result=1
            break
        fi
    done
    test_result "All skills have valid SKILL.md frontmatter" $result
}

# Test pattern-tracker.json structure
test_pattern_tracker_structure() {
    local test_dir=$(mktemp -d)
    local claude_dir="$test_dir/.claude"
    mkdir -p "$claude_dir/as_you/session_archive"
    echo "test deployment authentication" > "$claude_dir/as_you/session_archive/2025-01-05.md"

    (
        export PROJECT_ROOT="$test_dir"
        export CLAUDE_DIR="$claude_dir"
        bash scripts/track-frequency.sh > /dev/null 2>&1
    )

    local result=0
    if [ ! -f "$claude_dir/as_you/pattern_tracker.json" ]; then
        result=1
    elif ! jq -e '.patterns' "$claude_dir/as_you/pattern_tracker.json" > /dev/null 2>&1; then
        result=1
    elif ! jq -e '.promotion_candidates' "$claude_dir/as_you/pattern_tracker.json" > /dev/null 2>&1; then
        result=1
    fi

    rm -rf "$test_dir"
    test_result "pattern-tracker.json has valid structure" $result
}

# Test script error handling
test_track_frequency_with_empty_archive() {
    local test_dir=$(mktemp -d)
    local claude_dir="$test_dir/.claude"
    mkdir -p "$claude_dir/as_you/session_archive"
    touch "$claude_dir/as_you/session_archive/empty.md"

    (
        export PROJECT_ROOT="$test_dir"
        export CLAUDE_DIR="$claude_dir"
        bash scripts/track-frequency.sh > /dev/null 2>&1
    )
    local result=$?

    rm -rf "$test_dir"
    test_result "track-frequency.sh handles empty archive" $result
}

# Test hook integration
test_hooks_reference_existing_scripts() {
    local result=0
    local hooks_content=$(cat hooks/hooks.json)

    # Extract script paths from hooks.json and verify they exist
    for script_path in $(echo "$hooks_content" | jq -r '.. | .command? // empty' | grep '\.sh$'); do
        # Replace ${CLAUDE_PLUGIN_ROOT} with current directory
        script_path="${script_path//\$\{CLAUDE_PLUGIN_ROOT\}/$(pwd)}"
        if [ ! -f "$script_path" ]; then
            result=1
            break
        fi
    done

    test_result "hooks.json references existing scripts" $result
}

# Test workflow: note archiving
test_note_archiving_workflow() {
    local test_dir=$(mktemp -d)
    local claude_dir="$test_dir/.claude"
    mkdir -p "$claude_dir/as_you/session_archive"
    echo "test note content" > "$claude_dir/as_you/session_notes.local.md"

    (
        export PROJECT_ROOT="$test_dir"
        export CLAUDE_DIR="$claude_dir"
        bash scripts/archive-note.sh > /dev/null 2>&1
    )

    local result=0
    local date_str=$(date +%Y-%m-%d)
    if [ ! -f "$claude_dir/as_you/session_archive/$date_str.md" ]; then
        result=1
    fi

    rm -rf "$test_dir"
    test_result "Note archiving workflow works" $result
}

# Test pattern detection workflow
test_pattern_detection_workflow() {
    local test_dir=$(mktemp -d)
    local claude_dir="$test_dir/.claude"
    mkdir -p "$claude_dir/as_you/session_archive"

    # Create sample archive with repeated patterns
    cat > "$claude_dir/as_you/session_archive/2025-01-05.md" << 'EOF'
## Session Notes

Working on authentication system.
Implemented OAuth2 authentication.
Testing authentication flow.
EOF

    (
        export PROJECT_ROOT="$test_dir"
        export CLAUDE_DIR="$claude_dir"
        bash scripts/track-frequency.sh > /dev/null 2>&1
    )

    local result=0
    if [ ! -f "$claude_dir/as_you/pattern_tracker.json" ]; then
        result=1
    else
        # Check if "authentication" was tracked
        if ! jq -e '.patterns.authentication' "$claude_dir/as_you/pattern_tracker.json" > /dev/null 2>&1; then
            result=1
        fi
    fi

    rm -rf "$test_dir"
    test_result "Pattern detection workflow detects frequent words" $result
}

# Run all tests
echo "Running tests..."
echo ""

# JSON validation
test_plugin_json
test_hooks_json

# Hook execution
test_session_start
test_session_end

# Script functionality
test_track_frequency
test_track_frequency_with_empty_archive
test_pattern_tracker_structure

# Frontmatter validation
test_command_frontmatter
test_agent_frontmatter
test_skill_frontmatter

# Hook integration
test_hooks_reference_existing_scripts

# Workflow tests
test_note_archiving_workflow
test_pattern_detection_workflow

echo ""
echo "========================================="
echo "Tests: $TESTS_TOTAL  Passed: $TESTS_PASSED  Failed: $TESTS_FAILED"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed${NC}"
    exit 1
fi
