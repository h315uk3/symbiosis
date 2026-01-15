# As You

**"I (Claude) act as you" - AI learns and mimics your habits**

Claude learns from your work patterns and builds knowledge automatically from your explicit notes.

---

## How It Works

### Automatic Extraction Flow

```
1. During Session
   /as-you:note "Investigating authentication feature bug"
   → Saved to .claude/as_you/session_notes.local.md

2. On SessionEnd (Automatic)
   → Archive session_notes.local.md
   → Save as .claude/as_you/session_archive/2026-01-08.md

3. Pattern Extraction & Scoring (Automatic)
   → Extract words from archive
   → Calculate TF-IDF, PMI, time-decay scores
   → Auto-merge similar patterns (Levenshtein distance)
   → Save to .claude/as_you/pattern_tracker.json

4. Promotion Notification (Automatic)
   → Display patterns with composite score > 0.3 as promotion candidates
   → Viewable with /as-you:memory

5. Knowledge Base Creation (Manual)
   → /as-you:promote to create Skill or Agent
   → AI automatically determines optimal type
   → Save to skills/*, agents/*
```

Patterns are automatically extracted from your session notes, and frequently-appearing patterns accumulate as your knowledge base.

---

## Available Commands

```bash
# Note taking
/as-you:note "text"      # Add timestamped note
/as-you:notes            # View/manage notes (interactive)

# Memory analysis
/as-you:memory           # Memory dashboard (interactive)

# Pattern promotion
/as-you:promote [name]   # Promote to skill/agent (AI-assisted)

# Workflow management
/as-you:workflows        # Manage workflows (interactive)
/as-you:workflow-save    # Save new workflow

# Help
/as-you:help             # Show detailed help
```

---

## Key Features

- **No auth, no backend, no external APIs** - Completely local execution
- **Pattern Extraction & Accumulation** - Automatically extract frequently-appearing patterns from manual notes and make them reusable
- **Statistical Scoring** - TF-IDF, PMI, and time-decay-based importance evaluation
- **Automatic Pattern Merging** - Automatically merge similar patterns using Levenshtein distance
- **Interactive Commands** - Simple, dialog-based interface
- **Pure Python Implementation** - Testable, maintainable code using Python standard library (no NLP libraries)

---

## Installation

See [marketplace README](../../README.md#installation) for installation instructions.

**Requirements:** Python 3.11+

---

## License

GNU AGPL v3 - [LICENSE](../../LICENSE)
