---
description: "Toggle active learning: capture prompts and file edits automatically"
argument-hint: "[on|off|status]"
allowed-tools: [Bash]
---

# Active Learning Toggle

Control automatic capture of prompts and file edits for pattern learning.

## What is Active Learning?

When enabled, As You automatically captures:
- **Prompts**: Your requests, questions, and instructions
- **Edits**: File changes made via Edit/Write tools

This data is stored locally in `.claude/as_you/active_learning.json` and used to improve pattern recognition and skill generation.

## Usage

### Enable Active Learning

```
/as-you:active on
```

**Execution:**
```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m as_you.commands.active_toggle on
```

**Response:** "Active learning enabled"

### Disable Active Learning

```
/as-you:active off
```

**Execution:**
```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m as_you.commands.active_toggle off
```

**Response:** "Active learning disabled"

### Check Status

```
/as-you:active
/as-you:active status
```

**Execution:**
```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m as_you.commands.active_toggle status
```

**Response:** Display current status with statistics.

## Privacy

- All data remains local (no external services)
- Data stored in `~/.claude/as_you/active_learning.json`
- Default: OFF (opt-in)
- Clear data anytime by deleting the file

## Related Commands

- `/as-you:learn` - Add notes manually
- `/as-you:memory` - View captured patterns
- `/as-you:apply` - Apply learned patterns
