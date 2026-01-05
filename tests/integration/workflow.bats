#!/usr/bin/env bats

# Integration tests for end-to-end workflows

setup() {
    export PROJECT_ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    export SCRIPTS_DIR="$PROJECT_ROOT/scripts"
    export HOOKS_DIR="$PROJECT_ROOT/hooks"
    export FIXTURES_DIR="${BATS_TEST_DIRNAME}/../fixtures"

    export TEST_DIR="$(mktemp -d)"
    export CLAUDE_DIR="$TEST_DIR/.claude"
    mkdir -p "$CLAUDE_DIR/as-you/session-archive"

    export PROJECT_ROOT="$TEST_DIR"
}

teardown() {
    rm -rf "$TEST_DIR"
}

# Test: Complete session workflow
@test "workflow: complete session lifecycle (start -> work -> end)" {
    cd "$TEST_DIR"

    # 1. Session Start
    bash "$HOOKS_DIR/session-start.sh" > /dev/null 2>&1

    # Verify session notes are cleared
    [ ! -f "$CLAUDE_DIR/as-you/session-notes.local.md" ]

    # 2. Simulate work (create session notes)
    cat > "$CLAUDE_DIR/as-you/session-notes.local.md" <<'EOF'
# Work Session

Implemented testing framework.
Added bats tests for scripts.
Testing pattern detection.
EOF

    [ -f "$CLAUDE_DIR/as-you/session-notes.local.md" ]

    # 3. Session End
    bash "$HOOKS_DIR/session-end.sh" > /dev/null 2>&1

    # Verify session notes are archived
    [ -f "$CLAUDE_DIR/as-you/session-archive/$(date +%Y-%m-%d).md" ]

    # Verify pattern tracker is created
    [ -f "$CLAUDE_DIR/as-you/pattern-tracker.json" ]

    # Verify patterns are tracked
    run jq -r '.patterns | keys | length' "$CLAUDE_DIR/as-you/pattern-tracker.json"
    [ "$output" -gt 0 ]
}

# Test: Pattern detection and promotion workflow
@test "workflow: pattern detection leads to promotion suggestions" {
    cd "$TEST_DIR"

    # Create multiple archives with repeated patterns
    for i in {1..3}; do
        cat > "$CLAUDE_DIR/as-you/session-archive/2026-01-0${i}.md" <<EOF
# Session $i

Working on testing the system.
Building test automation.
Testing is important for quality.
EOF
    done

    # Track frequency
    bash "$SCRIPTS_DIR/track-frequency.sh" > /dev/null 2>&1

    # Verify pattern-tracker.json exists
    [ -f "$CLAUDE_DIR/as-you/pattern-tracker.json" ]

    # Verify "test" pattern is tracked
    run jq -r '.patterns.test.count' "$CLAUDE_DIR/as-you/pattern-tracker.json"
    [ "$output" -gt 0 ]

    # Verify promotion candidates exist
    run jq -r '.promotion_candidates | length' "$CLAUDE_DIR/as-you/pattern-tracker.json"
    [ "$output" -gt 0 ]

    # Get promotion suggestions
    run bash "$SCRIPTS_DIR/suggest-promotions.sh"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "test" ]]
}

# Test: Archive cleanup workflow
@test "workflow: old archives are cleaned up automatically" {
    cd "$TEST_DIR"

    # Create archives of different ages - macOS/Linux compatible
    RECENT_DATE=$(date +%Y-%m-%d)
    if date --version >/dev/null 2>&1; then
        # GNU date (Linux)
        OLD_DATE=$(date -d "8 days ago" +%Y-%m-%d)
        OLD_TIMESTAMP="8 days ago"
    else
        # BSD date (macOS)
        OLD_DATE=$(date -v-8d +%Y-%m-%d)
        OLD_TIMESTAMP="$(date -v-8d +%Y%m%d0000)"
    fi

    echo "Recent session" > "$CLAUDE_DIR/as-you/session-archive/${RECENT_DATE}.md"
    if date --version >/dev/null 2>&1; then
        touch -d "$OLD_TIMESTAMP" "$CLAUDE_DIR/as-you/session-archive/${OLD_DATE}.md"
    else
        touch -t "$OLD_TIMESTAMP" "$CLAUDE_DIR/as-you/session-archive/${OLD_DATE}.md"
    fi

    # Run cleanup
    bash "$SCRIPTS_DIR/cleanup-archive.sh" > /dev/null 2>&1

    # Verify recent archive still exists
    [ -f "$CLAUDE_DIR/as-you/session-archive/${RECENT_DATE}.md" ]

    # Verify old archive was deleted
    [ ! -f "$CLAUDE_DIR/as-you/session-archive/${OLD_DATE}.md" ]
}

# Test: Pattern co-occurrence detection
@test "workflow: co-occurrence patterns are detected" {
    cd "$TEST_DIR"

    # Create archive with word co-occurrences
    cat > "$CLAUDE_DIR/as-you/session-archive/2026-01-03.md" <<'EOF'
Testing and validation are important.
Code testing requires good validation.
Validation testing ensures quality.
EOF

    # Detect co-occurrences
    run bash "$SCRIPTS_DIR/detect-cooccurrence.sh"

    [ "$status" -eq 0 ]
    [[ "$output" =~ "testing" ]]
    [[ "$output" =~ "validation" ]]
}

# Test: Context extraction for patterns
@test "workflow: contexts are extracted for frequent patterns" {
    cd "$TEST_DIR"

    # Create tracker with patterns
    cat > "$CLAUDE_DIR/as-you/pattern-tracker.json" <<'EOF'
{
  "patterns": {
    "testing": {
      "count": 5,
      "sessions": ["2026-01-01"],
      "promoted": false
    }
  },
  "promotion_candidates": []
}
EOF

    # Create archive with contexts
    cat > "$CLAUDE_DIR/as-you/session-archive/2026-01-01.md" <<'EOF'
Working on testing the new feature.
Testing is crucial for quality assurance.
Automated testing saves time.
EOF

    # Extract contexts
    run bash "$SCRIPTS_DIR/extract-contexts.sh"

    [ "$status" -eq 0 ]
    [[ "$output" =~ "testing" ]]
}

# Test: Multiple sessions accumulate patterns
@test "workflow: patterns accumulate across multiple sessions" {
    cd "$TEST_DIR"

    # Session 1
    cat > "$CLAUDE_DIR/as-you/session-archive/2026-01-01.md" <<'EOF'
Working on testing functionality.
EOF
    bash "$SCRIPTS_DIR/track-frequency.sh" > /dev/null 2>&1

    FIRST_COUNT=$(jq -r '.patterns.testing.count // 0' "$CLAUDE_DIR/as-you/pattern-tracker.json")

    # Session 2
    cat > "$CLAUDE_DIR/as-you/session-archive/2026-01-02.md" <<'EOF'
More testing work completed.
EOF
    bash "$SCRIPTS_DIR/track-frequency.sh" > /dev/null 2>&1

    SECOND_COUNT=$(jq -r '.patterns.testing.count // 0' "$CLAUDE_DIR/as-you/pattern-tracker.json")

    # Verify count increased
    [ "$SECOND_COUNT" -gt "$FIRST_COUNT" ]

    # Verify sessions list grew
    SESSIONS=$(jq -r '.patterns.testing.sessions | length' "$CLAUDE_DIR/as-you/pattern-tracker.json")
    [ "$SESSIONS" -ge 1 ]
}
