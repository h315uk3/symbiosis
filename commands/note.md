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

1. Translate $ARGUMENTS to English if needed:
   - If already English, preserve as-is
   - If another language, translate while preserving technical terms

2. Execute with Bash tool:
   ```bash
   python3 scripts/commands/note_add.py "<translated-text>"
   ```
   Replace `<translated-text>` with actual content from step 1.

3. Respond: "Note added"
