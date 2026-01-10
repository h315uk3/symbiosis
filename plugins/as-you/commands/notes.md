---
description: "View and manage session notes"
allowed-tools: [Read, Bash, Glob, AskUserQuestion]
---

# View Notes

Display and manage session notes.

## Execution Steps

1. **Display Current Session Notes**
   - Get current directory: Execute `pwd` with Bash tool
   - Read `{pwd}/.claude/as_you/session_notes.local.md` using absolute path
   - If empty or doesn't exist: "No notes in current session"
   - If exists: Display contents with line count

2. **Present Options** using AskUserQuestion:
   - Question: "What would you like to do?"
   - Header: "Action"
   - Options:
     - Label: "View history (past 7 days)"
       Description: "Show archived notes from previous sessions"
     - Label: "Clear current notes"
       Description: "Remove all notes from current session"
     - Label: "Exit"
       Description: "Close notes management"

3. **Execute Based on Selection**

   **If "View history":**
   - Use Glob to search `{pwd}/.claude/as_you/session_archive/*.md` (where {pwd} is from step 1)
   - If no archives: "No archived notes found"
   - If archives exist:
     - For each file (sorted by date, newest first):
       - Extract date from filename (YYYY-MM-DD)
       - Display: "## YYYY-MM-DD"
       - Read and display file content
       - Add separator
     - Display total: "Total archives: X days"

   **If "Clear current notes":**
   - Confirm with AskUserQuestion:
     - Question: "Clear all notes from current session?"
     - Header: "Confirm"
     - Options:
       - Label: "Yes, clear them"
         Description: "Notes will be preserved in session archive on session end"
       - Label: "No, cancel"
         Description: "Keep current notes"
   - If confirmed:
     - Execute Bash: `> {pwd}/.claude/as_you/session_notes.local.md` (using absolute path)
     - Respond: "Session notes cleared"
   - If cancelled:
     - Respond: "Cancelled"

   **If "Exit":**
   - Respond: "Done"

## Related Commands
- `/as-you:note "text"` - Add note
- `/as-you:memory` - Analyze patterns
