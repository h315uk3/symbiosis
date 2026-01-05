#!/usr/bin/env bats

# Unit tests for hooks/*.sh

setup() {
    export PROJECT_ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    export HOOKS_DIR="$PROJECT_ROOT/hooks"
    export FIXTURES_DIR="${BATS_TEST_DIRNAME}/../fixtures"

    export TEST_DIR="$(mktemp -d)"
    export CLAUDE_DIR="$TEST_DIR/.claude"
    mkdir -p "$CLAUDE_DIR/as-you/session-archive"

    cp "$FIXTURES_DIR/sample-note.md" "$CLAUDE_DIR/as-you/session-notes.local.md"

    export PROJECT_ROOT="$TEST_DIR"
}

teardown() {
    rm -rf "$TEST_DIR"
}

# Test: session-start.sh
@test "session-start.sh: should execute without errors" {
    cd "$TEST_DIR"

    run bash "$HOOKS_DIR/session-start.sh"

    [ "$status" -eq 0 ]
}

@test "session-start.sh: should clear session notes" {
    cd "$TEST_DIR"

    bash "$HOOKS_DIR/session-start.sh" > /dev/null 2>&1

    [ ! -f "$CLAUDE_DIR/as-you/session-notes.local.md" ]
}

@test "session-start.sh: should display plugin loaded message" {
    cd "$TEST_DIR"

    run bash "$HOOKS_DIR/session-start.sh"

    [[ "$output" =~ "As You plugin loaded" ]]
}

@test "session-start.sh: should show promotion candidates if they exist" {
    cd "$TEST_DIR"

    # Create mock tracker with candidates
    cat > "$CLAUDE_DIR/as-you/pattern-tracker.json" <<'EOF'
{
  "patterns": {},
  "promotion_candidates": [
    {
      "pattern": "test",
      "count": 10,
      "sessions": 3
    }
  ]
}
EOF

    run bash "$HOOKS_DIR/session-start.sh"

    [[ "$output" =~ "Knowledge base promotion candidates detected" ]]
}

# Test: session-end.sh
@test "session-end.sh: should execute without errors" {
    cd "$TEST_DIR"

    run bash "$HOOKS_DIR/session-end.sh"

    [ "$status" -eq 0 ]
}

@test "session-end.sh: should archive session notes" {
    cd "$TEST_DIR"

    bash "$HOOKS_DIR/session-end.sh" > /dev/null 2>&1

    [ -f "$CLAUDE_DIR/as-you/session-archive/$(date +%Y-%m-%d).md" ]
}

@test "session-end.sh: should track patterns" {
    cd "$TEST_DIR"

    bash "$HOOKS_DIR/session-end.sh" > /dev/null 2>&1

    [ -f "$CLAUDE_DIR/as-you/pattern-tracker.json" ]
}

# Test: post-edit-format.sh
@test "post-edit-format.sh: should execute without errors" {
    cd "$TEST_DIR"

    # Create a test file to edit
    echo "test content" > "$TEST_DIR/test.txt"

    run bash "$HOOKS_DIR/post-edit-format.sh"

    [ "$status" -eq 0 ]
}

# Test: All hooks are executable
@test "all hooks should be executable" {
    for hook in "$HOOKS_DIR"/*.sh; do
        [ -x "$hook" ]
    done
}

# Test: All hooks have bash shebang
@test "all hooks should have bash shebang" {
    for hook in "$HOOKS_DIR"/*.sh; do
        run head -n 1 "$hook"
        [[ "$output" =~ "#!/bin/bash" ]]
    done
}
