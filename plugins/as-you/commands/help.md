---
description: "As You: pattern learning and external memory"
allowed-tools: []
---

# As You

Pattern learning plugin. Captures observations, detects patterns, applies learned habits.

## Commands

### /as-you:learn [note]

With argument: Add note (auto-translated to English).
Without argument: Interactive dashboard (add/view/analyze notes).

### /as-you:memory

Pattern analysis and SM-2 review dashboard.

### /as-you:apply [workflow]

With argument: Save workflow.
Without argument: Browse and execute workflows.

### /as-you:active [on|off|status]

Toggle automatic capture of prompts and edits.
Without argument: Show status.
Default: OFF.

### /as-you:help

This guide.

## Data

Location: `.claude/as_you/`

- `session_notes.local.md` - Current session notes
- `session_archive/*.md` - Archived notes
- `pattern_tracker.json` - Pattern database
- `active_learning.json` - Captured prompts/edits
- `workflows/*.md` - Saved workflows

All data stays local.

## References

- Config: `plugins/as-you/config/as-you.json`
- Schema: `plugins/as-you/config/as-you.schema.json`
