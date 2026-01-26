# Test Scenario: Session Lifecycle Hooks

Test SessionStart and SessionEnd hooks: automatic session management and pattern processing.

## Scenario 1: SessionStart Hook

### Prerequisites
- [ ] as-you plugin installed and enabled
- [ ] Previous session notes exist (run `/as-you:learn` to add some notes if needed)

### Test Steps

#### Step 1.1: Start New Session
Exit current session and start fresh:
```bash
/exit
claude-code
```

**Expected behavior:**
- [ ] SessionStart hook triggers automatically
- [ ] Hook executes within timeout (30 seconds)
- [ ] Session initialization completes successfully
- [ ] No visible errors to user
- [ ] LLM can access plugin features immediately

**Background processing (not visible to user):**
- Session metadata initialized
- Pattern tracker loaded
- Memory system prepared
- Previous session archived (if applicable)

**Verification:**
Check that session started cleanly:
```bash
# Check for any error logs (hook should complete silently)
# Session should be ready for commands
/as-you:help
```
Expected: Help displays normally, indicating session is ready.

#### Step 1.2: Verify Previous Session Archive
If previous session had notes, verify archiving:

**Verification:**
```bash
ls -lt .claude/as_you/session_archive/ | head -5
cat .claude/as_you/session_archive/$(ls -t .claude/as_you/session_archive/ | head -1)
```

Expected:
- [ ] Most recent archive file exists
- [ ] Filename format: `YYYY-MM-DD.md` or similar
- [ ] Contains notes from previous session
- [ ] Current session_notes.local.md is empty or reset

---

## Scenario 2: SessionEnd Hook

### Prerequisites
- [ ] Active Claude Code session with as-you plugin
- [ ] Some notes added during session (via `/as-you:learn`)
- [ ] Some patterns may have been updated

### Test Steps

#### Step 2.1: Normal Session End
Add some notes first:
```
/as-you:learn "Test note for session end"
/as-you:learn "Another note for archiving"
```

Then exit:
```bash
/exit
```

**Expected behavior:**
- [ ] SessionEnd hook triggers automatically
- [ ] Hook executes within timeout (60 seconds)
- [ ] Session closes cleanly
- [ ] No error messages

**Background processing (not visible to user):**
- Current session notes archived
- Pattern scores updated
- Memory scheduling processed (SM-2)
- State persisted to disk

**Verification:**
Restart session and check:
```bash
claude-code
```

Check archive was created:
```bash
ls -lt .claude/as_you/session_archive/ | head -1
```

Expected:
- [ ] New archive file created with today's date
- [ ] File contains notes from previous session

Check current session is clean:
```bash
cat .claude/as_you/session_notes.local.md
```

Expected:
- [ ] Empty or minimal content (fresh session)

Check pattern tracker was updated:
```bash
cat .claude/as_you/pattern_tracker.json | python3 -m json.tool | head -30
```

Expected:
- [ ] File exists and is valid JSON
- [ ] Last_modified timestamp updated
- [ ] Patterns from previous session processed

---

## Scenario 3: Rapid Session Cycling

### Test Steps

#### Step 3.1: Multiple Quick Sessions
Start and end sessions rapidly:

```bash
# Session 1
claude-code
/as-you:learn "Note in session 1"
/exit

# Session 2
claude-code
/as-you:learn "Note in session 2"
/exit

# Session 3
claude-code
/as-you:learn "Note in session 3"
/exit
```

**Expected behavior:**
- [ ] Each session handles hooks correctly
- [ ] No race conditions
- [ ] All notes archived properly
- [ ] Archives are distinct (separate files or combined appropriately)

**Verification:**
```bash
ls -l .claude/as_you/session_archive/
```

Expected:
- [ ] Archive files for each session (or combined by date)
- [ ] All notes preserved

---

## Scenario 4: Session Crash/Abnormal Termination

### Test Steps

#### Step 4.1: Simulate Crash
Add notes, then force-kill Claude Code process (Ctrl+C or kill):

```
/as-you:learn "Note before crash"
```

Force terminate (Ctrl+C or close terminal).

**Expected behavior:**
- [ ] SessionEnd hook may not execute (abnormal termination)
- [ ] Data loss possible for unsaved state

Restart session:
```bash
claude-code
```

**Verification:**
```bash
cat .claude/as_you/session_notes.local.md
```

Expected:
- [ ] Note added before crash may or may not be saved (depends on timing)
- [ ] System recovers gracefully
- [ ] No corruption in data files

Check data integrity:
```bash
cat .claude/as_you/pattern_tracker.json | python3 -m json.tool > /dev/null && echo "Valid JSON"
```

Expected: "Valid JSON"

---

## Scenario 5: Hook Timeout Handling

### Test Steps

#### Step 5.1: Verify Hook Timeouts
Hooks have timeouts:
- SessionStart: 30 seconds
- SessionEnd: 60 seconds

Under normal conditions, hooks complete in <5 seconds.

To test timeout handling (advanced):
- Modify hook script to include `sleep 35` (SessionStart) or `sleep 65` (SessionEnd)
- Start/end session
- Verify timeout is enforced and session continues

**Expected behavior:**
- [ ] Timeout enforced (hook terminated)
- [ ] Session continues despite timeout
- [ ] Error logged but user experience not blocked

**Note:** This test requires modifying hook scripts. Skip for routine testing.

---

## Scenario 6: Hook Execution Order

### Test Steps

#### Step 6.1: Verify SessionStart Order
SessionStart should complete before user can interact.

Start session:
```bash
claude-code
```

Immediately try to use plugin:
```
/as-you:help
```

**Expected behavior:**
- [ ] Help command works immediately
- [ ] SessionStart completed before command executed
- [ ] No race conditions

#### Step 6.2: Verify SessionEnd Order
SessionEnd should process before session fully closes.

```bash
/exit
```

**Expected behavior:**
- [ ] Session archives data before closing
- [ ] User may see "Saving..." or similar (optional)
- [ ] Session closes cleanly after hook completes (or times out)

---

## Edge Cases

### EC1: No Notes in Session
Start and end session without adding any notes:

```bash
claude-code
/exit
```

**Expected behavior:**
- [ ] Hooks execute normally
- [ ] No archive created (or empty archive)
- [ ] No errors

### EC2: First-Time Session
Delete all plugin data:
```bash
rm -rf .claude/as_you/
```

Start session:
```bash
claude-code
```

**Expected behavior:**
- [ ] SessionStart initializes directories and files
- [ ] Creates necessary data structures
- [ ] Plugin ready to use

### EC3: Corrupted Archive Directory
Create invalid archive directory:
```bash
rm -rf .claude/as_you/session_archive/
touch .claude/as_you/session_archive  # File instead of directory
```

Start session:
```bash
claude-code
```

**Expected behavior:**
- [ ] Hook detects issue
- [ ] Handles gracefully (recreates directory or logs error)
- [ ] Session starts despite issue

---

## Verification Checklist

### SessionStart Hook
- [ ] Executes automatically on session start
- [ ] Completes within 30 seconds
- [ ] Initializes session state
- [ ] Archives previous session (if applicable)
- [ ] Handles errors gracefully
- [ ] Doesn't block user interaction

### SessionEnd Hook
- [ ] Executes automatically on session end
- [ ] Completes within 60 seconds
- [ ] Archives current session notes
- [ ] Updates pattern tracker
- [ ] Persists all state
- [ ] Handles errors gracefully

### Data Integrity
- [ ] Archives are created correctly
- [ ] JSON files remain valid
- [ ] No data loss under normal conditions
- [ ] Graceful recovery from errors

---

## Cleanup

```bash
# Remove test archives
rm -rf .claude/as_you/session_archive/

# Or keep for inspection
# ls -la .claude/as_you/session_archive/
```

---

## Related Tests

- [pattern_capture.md](./pattern_capture.md) - Automatic pattern capture during session
- [learn.md](../commands/learn.md) - Manual note addition
- [memory.md](../commands/memory.md) - Pattern analysis and memory
