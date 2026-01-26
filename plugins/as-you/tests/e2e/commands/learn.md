# Test Scenario: /as-you:learn Command

Test the pattern learning command in both modes: quick note addition and interactive dashboard.

## Scenario 1: Quick Note Addition (with argument)

### Prerequisites
- [ ] Fresh Claude Code session started
- [ ] Working directory: any project with `.claude/` directory
- [ ] No previous session notes (or accept existing state)

### Test Steps

#### Step 1.1: Add Note in English
```
/as-you:learn "Always use pathlib instead of os.path for file operations"
```

**Expected behavior:**
- [ ] Command executes without error
- [ ] LLM responds with exactly "Note added" (no additional suggestions/questions)
- [ ] No interactive dialog appears

**Verification:**
```bash
cat .claude/as_you/session_notes.local.md
```
Expected contents:
- [ ] Contains the note text
- [ ] Has timestamp (ISO 8601 format)
- [ ] Note text is in English

#### Step 1.2: Add Note in Japanese (Non-English)
```
/as-you:learn "React hooksを使うとボイラープレートが減る"
```

**Expected behavior:**
- [ ] Command executes without error
- [ ] Note is automatically translated to English
- [ ] LLM responds with "Note added"

**Verification:**
```bash
cat .claude/as_you/session_notes.local.md
```
Expected contents:
- [ ] Contains translated note (English)
- [ ] Technical terms preserved ("React hooks")
- [ ] Has timestamp
- [ ] Two notes now exist in the file

#### Step 1.3: Empty or Invalid Input
```
/as-you:learn ""
```

**Expected behavior:**
- [ ] Appropriate error message or LLM asks for clarification
- [ ] No crash or empty note added

**Verification:**
```bash
cat .claude/as_you/session_notes.local.md | wc -l
```
Expected: Line count unchanged from previous state

---

## Scenario 2: Interactive Dashboard (without argument)

### Prerequisites
- [ ] Fresh Claude Code session
- [ ] Previous notes exist (run Scenario 1 first, or create test notes)

### Test Steps

#### Step 2.1: Open Dashboard
```
/as-you:learn
```

**Expected behavior:**
- [ ] Displays current session notes with count
- [ ] Shows learning summary (notes count, patterns count, promotion candidates)
- [ ] Presents AskUserQuestion with 5 options:
  - "Add another note"
  - "View note history"
  - "Analyze patterns"
  - "Clear current notes"
  - "Exit"

#### Step 2.2: Add Another Note
Select "Add another note" from the menu.

**Expected behavior:**
- [ ] AskUserQuestion prompts for note content
- [ ] Options include "Enter note text" and "Cancel"

Enter note: "JWT tokens should expire after 1 hour for security"

**Expected behavior:**
- [ ] Note added successfully
- [ ] Dashboard menu appears again (returns to Step 2.1 options)

**Verification:**
```bash
cat .claude/as_you/session_notes.local.md | grep -c "JWT"
```
Expected: 1 match

#### Step 2.3: View Note History
Select "View note history" from the menu.

**Expected behavior:**
- [ ] Displays archived notes from past sessions
- [ ] Shows up to 7 most recent archives
- [ ] Each archive has date header (YYYY-MM-DD format)
- [ ] If no archives: "No archived notes found"
- [ ] Returns to main menu

**Verification:**
```bash
ls -la .claude/as_you/session_archive/
```
Check if archive files exist with date-based names.

#### Step 2.4: Analyze Patterns
Select "Analyze patterns" from the menu.

**Expected behavior:**
- [ ] Executes promotion_analyzer command
- [ ] Displays promotion candidates with scores
- [ ] Shows message about using `/as-you:memory` for details
- [ ] Returns to main menu

#### Step 2.5: Clear Current Notes
Select "Clear current notes" from the menu.

**Expected behavior:**
- [ ] AskUserQuestion confirmation dialog appears
- [ ] Options: "Yes, clear them" and "No, cancel"

Select "Yes, clear them":
- [ ] Session notes file is cleared (not deleted)
- [ ] Response: "Session notes cleared"
- [ ] Returns to main menu

**Verification:**
```bash
cat .claude/as_you/session_notes.local.md
```
Expected: Empty file or no content

Select "No, cancel" (if retesting):
- [ ] Notes remain unchanged
- [ ] Returns to main menu

#### Step 2.6: Exit Dashboard
Select "Exit" from the menu.

**Expected behavior:**
- [ ] Response: "Done. Keep learning!" (or similar)
- [ ] Dashboard closes

---

## Edge Cases

### EC1: Very Long Note (>500 characters)
```
/as-you:learn "This is a very long note that contains detailed information about a complex pattern we discovered during development including specific code examples function names file paths and extensive reasoning about why this approach was chosen and what alternatives were considered and rejected..."
```

**Expected behavior:**
- [ ] Note is accepted and stored
- [ ] No truncation or error
- [ ] File system handles long content

### EC2: Special Characters in Note
```
/as-you:learn "Use \`backticks\` for code, \"quotes\" for strings, and $variables carefully"
```

**Expected behavior:**
- [ ] Special characters preserved correctly
- [ ] No shell injection issues
- [ ] Content readable in session_notes.local.md

### EC3: Repeated Identical Notes
Add the same note twice:
```
/as-you:learn "Always validate user input"
/as-you:learn "Always validate user input"
```

**Expected behavior:**
- [ ] Both notes are added (or second is detected as duplicate)
- [ ] Pattern detector should eventually recognize this repetition
- [ ] No error occurs

---

## Cleanup

```bash
# Clear session notes for next test run
> .claude/as_you/session_notes.local.md

# Or remove entire test data (caution: loses all patterns)
# rm -rf .claude/as_you/
```

---

## Related Tests

- [apply.md](./apply.md) - Using learned patterns
- [memory.md](./memory.md) - Analyzing learned patterns
- [hooks/pattern_capture.md](../hooks/pattern_capture.md) - Automatic pattern capture
