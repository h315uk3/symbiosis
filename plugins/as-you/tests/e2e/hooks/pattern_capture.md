# Test Scenario: Pattern Capture Hooks

Test UserPromptSubmit and PostToolUse hooks: automatic capture of prompts and file edits.

## Prerequisites for All Scenarios

- [ ] as-you plugin installed
- [ ] Active learning **enabled**: `/as-you:active on`

## Scenario 1: UserPromptSubmit Hook (Prompt Capture)

### Test Steps

#### Step 1.1: Submit User Prompts
After enabling active learning, submit various prompts:

```
Create a function to validate email addresses
```

```
Refactor the authentication middleware to use JWT tokens
```

```
Add error handling to the database connection
```

**Expected behavior:**
- [ ] UserPromptSubmit hook triggers after each prompt
- [ ] Prompts captured automatically (background, no user-visible action)
- [ ] Hook executes within timeout (5 seconds)
- [ ] Normal LLM response not affected

**Verification:**
```bash
cat ~/.claude/as_you/active_learning.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Total prompts captured: {len(data.get(\"prompts\", []))}')
print('Recent prompts:')
for p in data.get('prompts', [])[-5:]:
    print(f'  - {p.get(\"content\", \"\")[:60]}...')
    print(f'    Timestamp: {p.get(\"timestamp\", \"unknown\")}')
"
```

Expected:
- [ ] All 3 prompts appear in prompts array
- [ ] Each has timestamp (ISO 8601 format)
- [ ] Content matches submitted prompts
- [ ] Order preserved (chronological)

---

## Scenario 2: PostToolUse Hook (Edit Capture)

### Test Steps

#### Step 2.1: File Edits via Edit Tool
Perform file edits using the Edit tool during the session.

Example:
```
Edit the README.md file to add a new section
```

LLM will use Edit tool with old_string and new_string.

**Expected behavior:**
- [ ] PostToolUse hook triggers after Edit tool use
- [ ] Hook matches "Edit" pattern (hook matcher: "Edit|Write")
- [ ] Edit captured automatically (background)
- [ ] Hook executes within timeout (5 seconds)
- [ ] Normal edit operation not affected

**Verification:**
```bash
cat ~/.claude/as_you/active_learning.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Total edits captured: {len(data.get(\"edits\", []))}')
print('Recent edits:')
for e in data.get('edits', [])[-3:]:
    print(f'  File: {e.get(\"file_path\", \"unknown\")}')
    print(f'  Tool: {e.get(\"tool_name\", \"unknown\")}')
    print(f'  Timestamp: {e.get(\"timestamp\", \"unknown\")}')
    print(f'  Old: {e.get(\"old_string\", \"\")[:40]}...')
    print(f'  New: {e.get(\"new_string\", \"\")[:40]}...')
    print()
"
```

Expected:
- [ ] Edit captured with all details
- [ ] file_path present and correct
- [ ] tool_name is "Edit"
- [ ] old_string and new_string captured
- [ ] Timestamp present

#### Step 2.2: File Creation via Write Tool
Create a new file using the Write tool.

Example:
```
Create a new file utils/helper.py with utility functions
```

LLM will use Write tool.

**Expected behavior:**
- [ ] PostToolUse hook triggers after Write tool use
- [ ] Hook matches "Write" pattern
- [ ] Write operation captured
- [ ] Hook executes within timeout (5 seconds)

**Verification:**
```bash
cat ~/.claude/as_you/active_learning.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Total edits (including writes): {len(data.get(\"edits\", []))}')
writes = [e for e in data.get('edits', []) if e.get('tool_name') == 'Write']
print(f'Write operations: {len(writes)}')
for w in writes:
    print(f'  File: {w.get(\"file_path\", \"unknown\")}')
    print(f'  Content preview: {w.get(\"content\", \"\")[:60]}...')
"
```

Expected:
- [ ] Write operation captured
- [ ] tool_name is "Write"
- [ ] file_path present
- [ ] content field captured (full file content)

---

## Scenario 3: Hook Matcher Verification

### Test Steps

#### Step 3.1: Non-Matching Tools (should not trigger)
Use tools that don't match "Edit|Write" pattern:
- Read tool
- Bash tool
- Glob tool

**Expected behavior:**
- [ ] PostToolUse hook does NOT trigger for these tools
- [ ] Only Edit and Write captured

**Verification:**
```bash
cat ~/.claude/as_you/active_learning.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
tools = [e.get('tool_name') for e in data.get('edits', [])]
print(f'Tools captured: {set(tools)}')
"
```

Expected:
- [ ] Only "Edit" and "Write" in the set
- [ ] No "Read", "Bash", "Glob", etc.

---

## Scenario 4: Capture with Active Learning Disabled

### Prerequisites
- [ ] Active learning disabled: `/as-you:active off`

### Test Steps

#### Step 4.1: Submit Prompts and Edits
Submit prompts and perform edits with active learning OFF.

**Expected behavior:**
- [ ] UserPromptSubmit hook does not capture (or skips if disabled flag checked)
- [ ] PostToolUse hook does not capture (or skips if disabled flag checked)
- [ ] No new entries in active_learning.json

**Verification:**
Count prompts/edits before and after:
```bash
cat ~/.claude/as_you/active_learning.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Enabled: {data.get(\"enabled\", False)}')
print(f'Prompts: {len(data.get(\"prompts\", []))}')
print(f'Edits: {len(data.get(\"edits\", []))}')
"
```

Counts should not increase.

---

## Scenario 5: High-Volume Capture

### Test Steps

#### Step 5.1: Many Prompts and Edits
Enable active learning and perform 50+ prompts and edits.

**Expected behavior:**
- [ ] All captures stored correctly
- [ ] No data loss
- [ ] Performance acceptable (hooks complete within timeout)
- [ ] File size manageable

**Verification:**
```bash
ls -lh ~/.claude/as_you/active_learning.json
wc -l ~/.claude/as_you/active_learning.json
cat ~/.claude/as_you/active_learning.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Total prompts: {len(data.get(\"prompts\", []))}')
print(f'Total edits: {len(data.get(\"edits\", []))}')
"
```

Expected:
- [ ] File size reasonable (<10MB for 50 captures)
- [ ] All captures present
- [ ] Valid JSON structure maintained

---

## Scenario 6: Hook Timeout Handling

### Test Steps

#### Step 6.1: Verify Hook Timeouts
Hooks have timeout: 5 seconds

Under normal conditions, hooks complete in <1 second.

**Expected behavior:**
- [ ] Hooks complete quickly
- [ ] If timeout exceeded, hook terminated
- [ ] User operation continues regardless

**Verification:**
Monitor session for any timeout warnings or errors (should not occur normally).

---

## Scenario 7: Special Characters and Edge Cases

### Test Steps

#### Step 7.1: Prompts with Special Characters
```
Use `backticks` for code, "quotes" for strings, and $variables carefully
```

```
Handle this: {"json": "data", "array": [1, 2, 3]}
```

**Expected behavior:**
- [ ] Special characters captured correctly
- [ ] No JSON encoding issues
- [ ] Content preserved exactly

**Verification:**
```bash
cat ~/.claude/as_you/active_learning.json | python3 -m json.tool > /dev/null && echo "Valid JSON"
```

Expected: "Valid JSON"

Check captured content:
```bash
cat ~/.claude/as_you/active_learning.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
prompt = data['prompts'][-1]['content']
print(prompt)
"
```

Expected: Exact match with submitted prompt

#### Step 7.2: Very Long Prompts
Submit a prompt >1000 characters.

**Expected behavior:**
- [ ] Entire prompt captured (no truncation)
- [ ] File handles long content

#### Step 7.3: Unicode and Non-ASCII
```
日本語のプロンプト: データベースを最適化する
```

```
Emojis: 🚀 Deploy to production 🎉
```

**Expected behavior:**
- [ ] Unicode preserved correctly
- [ ] UTF-8 encoding maintained

---

## Scenario 8: Data Structure Verification

### Test Steps

#### Step 8.1: Verify JSON Schema
```bash
cat ~/.claude/as_you/active_learning.json | python3 -c "
import json, sys
data = json.load(sys.stdin)

# Check top-level structure
assert 'enabled' in data, 'Missing enabled field'
assert 'prompts' in data, 'Missing prompts field'
assert 'edits' in data, 'Missing edits field'
assert isinstance(data['prompts'], list), 'prompts must be list'
assert isinstance(data['edits'], list), 'edits must be list'

# Check prompt structure
for p in data['prompts']:
    assert 'content' in p, 'Prompt missing content'
    assert 'timestamp' in p, 'Prompt missing timestamp'

# Check edit structure
for e in data['edits']:
    assert 'file_path' in e, 'Edit missing file_path'
    assert 'tool_name' in e, 'Edit missing tool_name'
    assert 'timestamp' in e, 'Edit missing timestamp'
    if e['tool_name'] == 'Edit':
        assert 'old_string' in e, 'Edit missing old_string'
        assert 'new_string' in e, 'Edit missing new_string'
    elif e['tool_name'] == 'Write':
        assert 'content' in e, 'Write missing content'

print('✓ All schema checks passed')
"
```

Expected: "✓ All schema checks passed"

---

## Edge Cases

### EC1: First Capture (Empty File)
Delete active_learning.json, enable, capture:

```bash
rm ~/.claude/as_you/active_learning.json
```

```
/as-you:active on
```

Submit a prompt.

**Expected behavior:**
- [ ] File created automatically
- [ ] Proper structure initialized
- [ ] First prompt captured

### EC2: Concurrent Captures
Submit prompt while edit is being performed (rare timing).

**Expected behavior:**
- [ ] Both captured correctly
- [ ] No race conditions
- [ ] Data integrity maintained

### EC3: Malformed Existing File
Manually corrupt active_learning.json.

**Expected behavior:**
- [ ] Hook detects corruption
- [ ] Resets file or logs error
- [ ] Continues operation

---

## Cleanup

```bash
# Clear captured data
cat > ~/.claude/as_you/active_learning.json <<'EOF'
{
  "enabled": false,
  "prompts": [],
  "edits": []
}
EOF

# Disable active learning
```
```
/as-you:active off
```

---

## Related Tests

- [active.md](../commands/active.md) - Managing active learning state
- [session_lifecycle.md](./session_lifecycle.md) - Session start/end hooks
- [learn.md](../commands/learn.md) - Manual pattern learning
