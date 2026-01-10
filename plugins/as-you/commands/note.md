---
description: "Add note to current session memory with timestamp"
argument-hint: "<note-content>"
allowed-tools: [Bash]
---

# Add Note

Add a timestamped note to the current session.

If $ARGUMENTS is empty, display usage:

```
Usage: /as-you:note "note content"

Examples:
  /as-you:note "Investigating authentication bug"
  /as-you:note "User.findById() returning null"
  /as-you:note "JWT verification error in middleware"

To view notes: /as-you:notes
```

---

If $ARGUMENTS is provided:

1. **CRITICAL: Translate to English**
   - Detect input language
   - If non-English: MUST translate to English (preserve technical terms, code, proper nouns)
   - If already English: Use as-is
   - Self-check: Verify output contains only English text

2. Execute with Bash tool:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/commands/note_add.py" "<english-text>"
   ```
   Replace `<english-text>` with translated content from step 1.

3. **CRITICAL: Response protocol**
   - Respond EXACTLY: "Note added"
   - Do NOT add suggestions
   - Do NOT ask questions
   - Do NOT provide analysis
   - Do NOT start conversations about the note content
