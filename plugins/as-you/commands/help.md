---
description: "Display As You plugin help and usage guide"
allowed-tools: []
---

# As You Plugin Help

**A personal memory plugin that learns from your work patterns**

---

## Core Commands

### 📝 Note Taking

**`/as-you:note "text"`**
- Add timestamped note to current session
- Auto-translated to English if needed
- Example: `/as-you:note "Investigating auth bug"`

**`/as-you:notes`**
- View current session notes (interactive)
- Options: View history, Clear notes, Exit
- All notes archived automatically on session end

---

### 🧠 Memory & Analysis

**`/as-you:memory`**
- Interactive memory dashboard
- View statistics, patterns, and promotion candidates
- Options:
  - View promotion candidates
  - Analyze patterns (with AI agent)
  - Detect similar patterns
  - Review knowledge base
  - Exit

---

### 🚀 Pattern Promotion

**`/as-you:promote [pattern]`**
- Promote frequent pattern to knowledge base
- AI automatically determines: Skill or Agent
- Interactive selection if pattern not specified
- Generates component with context

**How it works:**
1. AI analyzes pattern characteristics
2. Determines optimal type (Skill/Agent)
3. Generates appropriate component
4. User reviews and confirms

---

### 🔄 Workflow Management

**`/as-you:workflows`**
- View and manage saved workflows (interactive)
- Options: View details, Update, Delete, Exit
- All workflows sorted by last modified

**`/as-you:workflow-save [name]`**
- Save recent work as reusable workflow
- Interactive configuration:
  - Workflow name
  - Abstraction level (specific/generic)
  - Scope (last 5/10/20 actions)
  - Description
- Security checks for sensitive data

---

## How It Works

### Automatic Pattern Learning

```
You work → Take notes → SessionEnd hook
           ↓
     Pattern detection
           ↓
     Statistical scoring
     (TF-IDF, PMI, time decay)
           ↓
     Promotion candidates
           ↓
     SessionStart notification
           ↓
     You promote → Knowledge base
```

### Pattern Analysis

- **Frequency**: How often pattern appears
- **Sessions**: Across how many sessions
- **TF-IDF**: Statistical importance
- **PMI**: Co-occurrence strength
- **Time Decay**: Recent vs. old patterns

### Promotion Thresholds

Patterns become candidates when:
- Appears in 3+ sessions, OR
- Total count 5+, AND
- Composite score > 0.3

---

## Automatic Features

### SessionStart Hook
- Clear current session notes
- Delete archives older than 7 days
- Notify about promotion candidates

### SessionEnd Hook
- Archive session notes (if not empty)
- Update pattern frequencies
- Calculate scores
- Merge similar patterns
- Detect promotion candidates

---

## Directory Structure

```
.claude/as_you/
├── session_notes.local.md     # Current session notes
├── pattern_tracker.json        # Pattern database (TF-IDF, scores)
└── session_archive/            # 7-day archive
    ├── 2026-01-08.md
    └── 2026-01-07.md

plugins/as_you/
├── commands/                   # User commands (6)
├── agents/                     # System agents (6)
├── hooks/                      # Lifecycle hooks (2)
└── skills/                     # Knowledge base
```

---

## Quick Start

### 1. Take Notes During Work
```bash
/as-you:note "Investigating authentication bug"
/as-you:note "User.findById() returns null"
/as-you:note "Fixed: JWT secret not loaded"
```

### 2. Check Memory Dashboard
```bash
/as-you:memory
# See: 3 notes, 12 patterns, 2 candidates
```

### 3. Promote Patterns
```bash
/as-you:promote
# AI suggests: "authentication" → Skill
# Review and confirm
```

### 4. Save Workflows
```bash
# After running tests and build
/as-you:workflow-save qa-check
# Save as reusable workflow
```

---

## Design Philosophy

**Simplicity First**: 6 commands only, no complex syntax

**Local-First**: No external services, full privacy

**Explicit Over Implicit**: You control what to record

**Statistical Intelligence**: Math-based pattern detection

**Zero Dependencies**: Pure standard library

**Progressive Learning**: Knowledge grows organically

---

## Tips

- **Take notes liberally**: More data = better patterns
- **Use natural language**: AI understands context
- **Check /memory regularly**: See what's being learned
- **Promote early**: Build knowledge base incrementally
- **Save workflows**: Automate repetitive tasks

---

For detailed command help, run each command without arguments.
