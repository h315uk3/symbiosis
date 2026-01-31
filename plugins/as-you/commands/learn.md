---
description: "Learn from your work: add notes, view patterns, and build knowledge"
argument-hint: "[note-content]"
allowed-tools: [Bash, Read, Glob, AskUserQuestion]
---

# Learn from Your Work

Capture insights and build knowledge from your development sessions.

## Usage Modes

### Mode 1: Add Note (with arguments)

**Usage:** `/as-you:learn "your note content"`

Add a timestamped observation to current session.

**Examples:**
```
/as-you:learn "Using React hooks reduces boilerplate"
/as-you:learn "JWT tokens expire after 1 hour"
/as-you:learn "User.findById() null check is critical"
```

**Execution:**

1. **CRITICAL: Translate to English**
   - Detect input language
   - If non-English: MUST translate to English (preserve technical terms, code, proper nouns)
   - If already English: Use as-is
   - Self-check: Verify output contains only English text

2. Execute with Bash tool:
   ```bash
   export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
   python3 -m as_you.commands.note_add "<english-text>"
   ```
   Replace `<english-text>` with translated content from step 1.

3. **CRITICAL: Response protocol**
   - Respond EXACTLY: "Note added"
   - Do NOT add suggestions
   - Do NOT ask questions
   - Do NOT provide analysis
   - Do NOT start conversations about the note content

---

### Mode 2: Learning Dashboard (without arguments)

**Usage:** `/as-you:learn`

View notes, patterns, and learning opportunities.

**Execution Steps:**

1. **Display Current Session Notes**
   - Get current directory: Execute `pwd` with Bash tool
   - Read `<workspace>/.claude/as_you/session_notes.local.md` using absolute path
   - If empty or doesn't exist: "No notes in current session"
   - If exists: Display contents with "Session Notes (X entries)" header

2. **Show Quick Statistics**
   Execute:
   ```bash
   export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
   python3 -m as_you.commands.memory_stats
   ```
   Display summary:
   ```
   Learning Summary:
   - Notes this session: X
   - Total patterns: X
   - Promotion candidates: X
   ```

3. **Present Learning Options** using AskUserQuestion:
   - Question: "What would you like to do?"
   - Header: "Action"
   - multiSelect: false
   - Options:
     - Label: "Add another note"
       Description: "Capture a new observation"
     - Label: "View note history"
       Description: "Browse archived notes from past sessions"
     - Label: "Analyze patterns"
       Description: "Review detected patterns and promotion candidates"
     - Label: "Clear current notes"
       Description: "Start fresh (notes preserved in archive)"
     - Label: "Exit"
       Description: "Close learning dashboard"

4. **Execute Based on Selection**

   **If "Add another note":**
   - Use AskUserQuestion to collect note:
     - Question: "What did you learn?"
     - Header: "Note"
     - Options:
       - Label: "Enter note text"
         Description: "Type your observation"
       - Label: "Cancel"
         Description: "Return to dashboard"
   - If note provided:
     - Execute same translation and add logic as Mode 1
     - Return to step 3 (show options again)
   - If cancelled:
     - Return to step 3

   **If "View note history":**
   - Use Glob to search `<workspace>/.claude/as_you/session_archive/*.md`
   - If no archives: "No archived notes found"
   - If archives exist:
     - For each file (sorted by date, newest first, limit to 7 most recent):
       - Extract date from filename (YYYY-MM-DD)
       - Display: "## YYYY-MM-DD"
       - Read and display file content
       - Add separator
     - Display: "Showing 7 most recent archives. Total: X days"
   - Return to step 3

   **If "Analyze patterns":**
   - Execute:
     ```bash
     export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
     python3 -m as_you.commands.promotion_analyzer
     ```
   - Display promotion candidates with scores
   - Show message: "Use /as-you:patterns to explore and promote patterns"
   - Return to step 3

   **If "Clear current notes":**
   - Confirm with AskUserQuestion:
     - Question: "Clear all notes from current session?"
     - Header: "Confirm"
     - multiSelect: false
     - Options:
       - Label: "Yes, clear them"
         Description: "Notes will be preserved in session archive"
       - Label: "No, cancel"
         Description: "Keep current notes"
   - If confirmed:
     - Execute Bash: `> <workspace>/.claude/as_you/session_notes.local.md`
     - Respond: "Session notes cleared"
   - If cancelled:
     - Respond: "Cancelled"
   - Return to step 3

   **If "Exit":**
   - Respond: "Done. Keep learning!"

## Learning Tips

**Good notes are:**
- Specific: "JWT validation happens in authMiddleware.js:42"
- Actionable: "Always check user.role before admin operations"
- Context-rich: "PostgreSQL EXPLAIN shows sequential scan on users table"

**Patterns emerge from:**
- Repeated observations (3+ occurrences)
- Similar solutions across contexts
- Consistent preferences or decisions

## Related Commands

- `/as-you:patterns` - Manage and promote patterns
- `/as-you:workflows` - Save and manage workflows
- `/as-you:help` - Full documentation
