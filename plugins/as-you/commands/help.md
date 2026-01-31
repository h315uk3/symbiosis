---
description: "As You: pattern learning and external memory"
allowed-tools: []
---

# As You

Pattern learning plugin. Captures observations, detects patterns, applies learned habits.

## Commands

### /as-you:learn [note]

Record patterns through notes.

With argument: Add note (auto-translated to English).
Without argument: Interactive dashboard (add/view/analyze notes).

### /as-you:patterns

Manage learned patterns: save as skills/agents, analyze, review quality, view statistics.

Options: Save as skill/agent, Analyze patterns, Review quality (SM-2), View statistics.

### /as-you:workflows [workflow-name]

Manage workflows: save procedures, view/execute, optimize quality.

With argument: Save new workflow.
Without argument: Dashboard (save/view/execute/optimize workflows).

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

**Knowledge Base** (generated artifacts use `u-` prefix):
- Skills: `.claude/skills/u-*/SKILL.md`
- Agents: `.claude/agents/u-*.md`
- Workflows: `.claude/commands/u-*.md`

All data stays local.

## References

- Config: `plugins/as-you/config/as-you.json`
- Schema: `plugins/as-you/config/as-you.schema.json`
