---
description: "Add note to current session memory with timestamp"
argument-hint: "<memo-content>"
allowed-tools: [Bash]
---

# Add Session Note

If $ARGUMENTS is empty, display help:

## Usage
```
/as-you:note "note content"
```

## Examples
```
/as-you:note "Investigating User.findById() returning null issue"
/as-you:note "JWT verification error - secret key not set in environment variables"
/as-you:note "Implementing Phase 5: Scripts done, next is Hooks"
```

## Features
- Recorded with timestamp
- Automatically archived on session end
- Frequent patterns suggested for knowledge base creation

## Related Commands
- `/as-you:note-show` - Display current session notes
- `/as-you:note-history` - View notes from last 7 days
- `/as-you:memory-analyze` - Analyze patterns

---

If $ARGUMENTS is provided, execute the following:

1. Translate $ARGUMENTS to English using your language capabilities:
   - If already in English, preserve as-is
   - If in another language (e.g., Japanese, Spanish, French), translate to English
   - Maintain technical terms and proper nouns correctly

2. Execute with Bash tool, constructing the echo command with the actual translated text:
   ```bash
   mkdir -p .claude/as_you
   echo "[$(date +%H:%M)] <insert translated text here>" >> .claude/as_you/session_notes.local.md
   ```
   Important: You must replace `<insert translated text here>` with the actual translated content from step 1 when you construct this command. Do not execute this command with the placeholder text.

3. Respond: "Note added (translated to English if needed)"
