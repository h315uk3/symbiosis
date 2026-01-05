#!/usr/bin/env bats

# Unit tests for scripts/*.sh

setup() {
    export PROJECT_ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    export SCRIPTS_DIR="$PROJECT_ROOT/scripts"
    export FIXTURES_DIR="${BATS_TEST_DIRNAME}/../fixtures"

    export TEST_DIR="$(mktemp -d)"
    export CLAUDE_DIR="$TEST_DIR/.claude"
    mkdir -p "$CLAUDE_DIR/as-you/session-archive"

    cp "$FIXTURES_DIR/sample-note.md" "$CLAUDE_DIR/as-you/session-notes.local.md"
    cp "$FIXTURES_DIR/sample-archive.md" "$CLAUDE_DIR/as-you/session-archive/2026-01-03.md"

    export PROJECT_ROOT="$TEST_DIR"
}

teardown() {
    # Clean up temporary test environment
    rm -rf "$TEST_DIR"
}

# Test: detect-patterns.sh
@test "detect-patterns.sh: should detect word patterns from archives" {
    cd "$TEST_DIR"

    run bash "$SCRIPTS_DIR/detect-patterns.sh"

    [ "$status" -eq 0 ]
    [[ "$output" =~ "testing" ]]
}

@test "detect-patterns.sh: should return empty JSON when no archives exist" {
    rm -rf "$CLAUDE_DIR/as-you/session-archive"/*
    cd "$TEST_DIR"

    run bash "$SCRIPTS_DIR/detect-patterns.sh"

    [ "$status" -eq 0 ]
    [[ "$output" == "[]" ]]
}

# Test: archive-note.sh
@test "archive-note.sh: should archive session notes to session-archive" {
    cd "$TEST_DIR"

    run bash "$SCRIPTS_DIR/archive-note.sh"

    [ "$status" -eq 0 ]
    [ -f "$CLAUDE_DIR/as-you/session-archive/$(date +%Y-%m-%d).md" ]
}

@test "archive-note.sh: should skip archiving when memo is empty" {
    rm -f "$CLAUDE_DIR/as-you/session-notes.local.md"
    touch "$CLAUDE_DIR/as-you/session-notes.local.md"
    cd "$TEST_DIR"

    run bash "$SCRIPTS_DIR/archive-note.sh"

    [ "$status" -eq 0 ]
}

# Test: cleanup-archive.sh
@test "cleanup-archive.sh: should remove old archives" {
    cd "$TEST_DIR"

    # Create old archive (8 days ago) - macOS/Linux compatible
    if date --version >/dev/null 2>&1; then
        # GNU date (Linux)
        OLD_DATE=$(date -d "8 days ago" +%Y-%m-%d)
        touch -d "8 days ago" "$CLAUDE_DIR/as-you/session-archive/${OLD_DATE}.md"
    else
        # BSD date (macOS)
        OLD_DATE=$(date -v-8d +%Y-%m-%d)
        touch -t "$(date -v-8d +%Y%m%d0000)" "$CLAUDE_DIR/as-you/session-archive/${OLD_DATE}.md"
    fi

    run bash "$SCRIPTS_DIR/cleanup-archive.sh"

    [ "$status" -eq 0 ]
    [ ! -f "$CLAUDE_DIR/as-you/session-archive/${OLD_DATE}.md" ]
}

# Test: track-frequency.sh
@test "track-frequency.sh: should create pattern-tracker.json" {
    cd "$TEST_DIR"

    run bash "$SCRIPTS_DIR/track-frequency.sh"

    [ "$status" -eq 0 ]
    [ -f "$CLAUDE_DIR/as-you/pattern-tracker.json" ]
}

@test "track-frequency.sh: should track pattern frequency" {
    cd "$TEST_DIR"

    bash "$SCRIPTS_DIR/track-frequency.sh"

    # Verify JSON structure
    run jq -r '.patterns | keys | length' "$CLAUDE_DIR/as-you/pattern-tracker.json"
    [ "$status" -eq 0 ]
    [ "$output" -gt 0 ]
}

# Test: suggest-promotions.sh
@test "suggest-promotions.sh: should return empty array when no tracker exists" {
    cd "$TEST_DIR"

    run bash "$SCRIPTS_DIR/suggest-promotions.sh"

    [ "$status" -eq 0 ]
    [[ "$output" == "[]" ]]
}

@test "suggest-promotions.sh: should suggest promotions when patterns exist" {
    cd "$TEST_DIR"

    # Create mock tracker with promotion candidates
    cat > "$CLAUDE_DIR/as-you/pattern-tracker.json" <<'EOF'
{
  "patterns": {
    "test": {
      "count": 10,
      "sessions": ["2026-01-01", "2026-01-02", "2026-01-03"],
      "contexts": ["testing the system", "test cases"],
      "promoted": false
    }
  },
  "promotion_candidates": [
    {
      "pattern": "test",
      "count": 10,
      "sessions": 3,
      "reason": "10回出現、3セッションで使用"
    }
  ]
}
EOF

    run bash "$SCRIPTS_DIR/suggest-promotions.sh"

    [ "$status" -eq 0 ]
    [[ "$output" =~ "test" ]]
}

# Test: All scripts are executable
@test "all scripts should be executable" {
    for script in "$SCRIPTS_DIR"/*.sh; do
        [ -x "$script" ]
    done
}

# Test: All scripts should have bash shebang
@test "all scripts should have bash shebang" {
    for script in "$SCRIPTS_DIR"/*.sh; do
        run head -n 1 "$script"
        [[ "$output" =~ "#!/bin/bash" ]]
    done
}
