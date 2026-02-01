# as-you

**Teach Once, Remember Forever**

> Claude learns your coding patterns and makes them accessible when needed.
> No setup. No dependencies. No databases. (Just Claude Code itself.)

## Example

```
You: /as-you:learn "Use environment variables for API keys"
Claude: Note added

[Later, in a new session...]

You: /as-you:patterns
Claude: [Shows pattern analysis and options]
        1. Review pattern quality (SM-2)
        2. View top patterns
        3. Promote to skill/agent
        ...

You: Add Stripe payment integration
Claude: I'll implement the Stripe integration using environment variables
for the API key, following your established pattern.
```

> **How it works**: Patterns are analyzed and scored automatically. Claude considers relevant patterns based on your current task. Pattern selection uses Thompson Sampling to balance proven patterns with exploration of uncertain ones.

---

## Demos

### Learning Patterns

![Learning Demo](https://h315uk3.github.io/symbiosis/assets/video/demo-as-you-learning.gif)

### Managing Patterns

![Patterns Demo](https://h315uk3.github.io/symbiosis/assets/video/demo-as-you-patterns.gif)

### Active Learning Mode

![Active Mode Demo](https://h315uk3.github.io/symbiosis/assets/video/demo-as-you-active.gif)

### Managing Workflows

![Workflows Demo](https://h315uk3.github.io/symbiosis/assets/video/demo-as-you-workflows.gif)

---

## Key Features

- **Automatic Pattern Learning** - Patterns emerge from your notes over time
- **Statistical Scoring** - BM25 relevance, Bayesian confidence, time decay
- **Memory Review** - SM-2 spaced repetition schedules pattern reviews
- **Smart Selection** - Thompson Sampling balances proven vs. uncertain patterns
- **Hybrid Architecture** - Python handles algorithms, Claude handles interaction
- **Local-First** - All data stays on your machine, no external services
- **Zero Dependencies** - Pure Python standard library only

---

## Available Commands

- **`/as-you:learn`** - Add notes and build knowledge from your development sessions
- **`/as-you:patterns`** - Analyze patterns, review quality (SM-2), and promote to skills/agents
- **`/as-you:workflows`** - Save, view, and execute reusable workflows
- **`/as-you:active`** - Toggle automatic capture of prompts and file edits
- **`/as-you:help`** - Show detailed usage documentation

---

## Documentation

- **[Technical Overview](./docs/technical-overview.md)** - Algorithms, configuration, data structures, and development guide

---

## Installation

See [main README](../../README.md#installation) for installation instructions.

**Requirements:**
- Python 3.11+
- Claude Code CLI

---

## License

GNU AGPL v3 - [LICENSE](../../LICENSE)
