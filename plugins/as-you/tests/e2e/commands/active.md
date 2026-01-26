# Test Scenario: /as-you:active Command

Test the active learning toggle: enable/disable automatic capture of prompts and file edits.

## Scenario 1: Check Status (default state)

### Prerequisites
- [ ] Fresh Claude Code session
- [ ] No previous active learning state (or accept existing state)

### Test Steps

#### Step 1.1: Check Initial Status
```
/as-you:active
```
Or:
```
/as-you:active status
```

**Expected behavior:**
- [ ] Displays current status (ON or OFF)
- [ ] Shows statistics:
  - Number of prompts captured
  - Number of edits captured
  - Last capture timestamp (if applicable)
- [ ] Default state: OFF (unless previously enabled)
- [ ] No errors occur

**Verification:**
```bash
cat ~/.claude/as_you/active_learning.json | python3 -m json.tool
```
Expected contents:
- [ ] JSON with `enabled` field (true/false)
- [ ] `prompts` array (empty if never enabled)
- [ ] `edits` array (empty if never enabled)
- [ ] Metadata fields

---

## Scenario 2: Enable Active Learning

### Prerequisites
- [ ] Active learning currently disabled

### Test Steps

#### Step 2.1: Enable
```
/as-you:active on
```

**Expected behavior:**
- [ ] Command executes without error
- [ ] Response: "Active learning enabled"
- [ ] No additional prompts or confirmations

**Verification:**
```bash
cat ~/.claude/as_you/active_learning.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Enabled: {data.get(\"enabled\", False)}')
"
```
Expected output: `Enabled: True`

#### Step 2.2: Verify Status After Enabling
```
/as-you:active status
```

**Expected behavior:**
- [ ] Status shows: ON/Enabled
- [ ] Shows current capture statistics

---

## Scenario 3: Capture Prompts and Edits

### Prerequisites
- [ ] Active learning enabled (run Scenario 2 first)

### Test Steps

#### Step 3.1: Submit User Prompts
After enabling, submit some prompts:
```
Create a new function to calculate Fibonacci numbers
```
```
Refactor the authentication middleware
```

**Expected behavior:**
- [ ] Prompts are captured automatically
- [ ] No visible indication to user (background capture)

**Verification:**
```bash
cat ~/.claude/as_you/active_learning.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Prompts captured: {len(data.get(\"prompts\", []))}')
for p in data.get('prompts', []):
    print(f'  - {p.get(\"content\", \"\")[:50]}...')
"
```
Expected: Prompts appear in the list

#### Step 3.2: Perform File Edits
Use Edit or Write tool to modify files during the session.

**Expected behavior:**
- [ ] Edits are captured automatically via PostToolUse hook
- [ ] Captured data includes: file_path, old_string, new_string, timestamp

**Verification:**
```bash
cat ~/.claude/as_you/active_learning.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Edits captured: {len(data.get(\"edits\", []))}')
for e in data.get('edits', []):
    print(f'  - {e.get(\"file_path\", \"unknown\")}: {e.get(\"timestamp\", \"no timestamp\")}')
"
```
Expected: Edits appear in the list with correct file paths

---

## Scenario 4: Disable Active Learning

### Prerequisites
- [ ] Active learning currently enabled

### Test Steps

#### Step 4.1: Disable
```
/as-you:active off
```

**Expected behavior:**
- [ ] Command executes without error
- [ ] Response: "Active learning disabled"
- [ ] Previously captured data is preserved (not deleted)

**Verification:**
```bash
cat ~/.claude/as_you/active_learning.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Enabled: {data.get(\"enabled\", False)}')
print(f'Prompts still in file: {len(data.get(\"prompts\", []))}')
print(f'Edits still in file: {len(data.get(\"edits\", []))}')
"
```
Expected:
- `Enabled: False`
- Prompts and edits counts unchanged (data preserved)

#### Step 4.2: Verify No New Captures After Disabling
Submit a new prompt and perform an edit.

**Expected behavior:**
- [ ] No new prompts captured
- [ ] No new edits captured

**Verification:**
Check that counts remain the same:
```bash
cat ~/.claude/as_you/active_learning.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Prompts: {len(data.get(\"prompts\", []))}')
print(f'Edits: {len(data.get(\"edits\", []))}')
"
```
Counts should match previous check.

---

## Scenario 5: Toggle Multiple Times

### Test Steps

#### Step 5.1: Rapid On/Off Switching
```
/as-you:active on
/as-you:active off
/as-you:active on
/as-you:active status
```

**Expected behavior:**
- [ ] Each command executes successfully
- [ ] Final status shows current state (ON)
- [ ] No errors or race conditions
- [ ] Data integrity maintained

---

## Scenario 6: Privacy Verification

### Test Steps

#### Step 6.1: Verify Data Location and Privacy
```bash
ls -la ~/.claude/as_you/active_learning.json
```

**Expected behavior:**
- [ ] File exists in local user directory
- [ ] Permissions: 644 (rw-r--r--) or 600 (rw-------)
- [ ] File is human-readable JSON

**Verification:**
```bash
cat ~/.claude/as_you/active_learning.json | python3 -m json.tool
```
- [ ] Validate JSON structure
- [ ] Check for any unexpected data
- [ ] Confirm all data is local (no URLs, no external references)

#### Step 6.2: Manual Data Deletion
```bash
rm ~/.claude/as_you/active_learning.json
```

**Expected behavior:**
- [ ] File deleted successfully
- [ ] User has full control over their data

Re-enable to verify recreation:
```
/as-you:active on
```

**Expected behavior:**
- [ ] New active_learning.json created
- [ ] Empty prompts and edits arrays
- [ ] Status: enabled

---

## Edge Cases

### EC1: Enable When Already Enabled
```
/as-you:active on
/as-you:active on
```

**Expected behavior:**
- [ ] Second command is idempotent (no error)
- [ ] Response confirms state or acknowledges already enabled
- [ ] Data integrity maintained

### EC2: Disable When Already Disabled
```
/as-you:active off
/as-you:active off
```

**Expected behavior:**
- [ ] Second command is idempotent (no error)
- [ ] Response confirms state or acknowledges already disabled

### EC3: Invalid Argument
```
/as-you:active invalid-arg
```

**Expected behavior:**
- [ ] Shows error message or defaults to status display
- [ ] Suggests valid options: on, off, status
- [ ] No crash

### EC4: File Corrupted
Manually corrupt active_learning.json (invalid JSON).

```
/as-you:active status
```

**Expected behavior:**
- [ ] Detects corrupted file
- [ ] Shows error message
- [ ] Offers to reset or fix
- [ ] No crash

### EC5: Large Capture Volume
Enable active learning and perform 100+ prompts/edits.

**Expected behavior:**
- [ ] All captures stored correctly
- [ ] File size manageable
- [ ] Performance acceptable
- [ ] No data loss

Check file size:
```bash
ls -lh ~/.claude/as_you/active_learning.json
```

---

## Cleanup

```bash
# Clear captured data but keep file
cat > ~/.claude/as_you/active_learning.json <<'EOF'
{
  "enabled": false,
  "prompts": [],
  "edits": []
}
EOF

# Or completely remove file
rm ~/.claude/as_you/active_learning.json
```

---

## Related Tests

- [hooks/pattern_capture.md](../hooks/pattern_capture.md) - How prompts and edits are captured
- [learn.md](./learn.md) - Manual pattern learning
- [memory.md](./memory.md) - Analyzing captured patterns
