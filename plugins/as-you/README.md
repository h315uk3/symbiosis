# as-you

**Teach Once, Remember Forever**

> Claude learns your coding patterns and makes them accessible when needed.
> No setup. No dependencies. No databases. (Just Claude Code itself.)

## Example

```
You: /as-you:learn "Use environment variables for API keys"
Claude: Note added

[Later, in a new session...]

You: /as-you:apply
Claude: [Shows top patterns using Thompson Sampling]
        1. Use environment variables for API keys
        2. ...

You: Add Stripe payment integration
Claude: I'll implement the Stripe integration using environment variables
for the API key, following your established pattern.
```

> **How it works**: Patterns are presented as context when you use `/as-you:apply`. Claude considers them based on relevance to your current task. Pattern selection uses Thompson Sampling to balance proven patterns with exploration of uncertain ones.

---

## Key Features

- **Automatic Pattern Learning** - Patterns emerge from your notes over time
- **Statistical Scoring** - BM25 relevance, Bayesian confidence, time decay
- **Memory Review** - SM-2 spaced repetition schedules pattern reviews
- **Smart Selection** - Thompson Sampling balances proven vs. uncertain patterns
- **Local-First** - All data stays on your machine, no external services
- **Zero Dependencies** - Pure Python standard library only

---

## Available Commands

- **`/as-you:learn`** - Add notes and build knowledge from your development sessions
- **`/as-you:memory`** - Analyze patterns, review quality, and manage your knowledge base
- **`/as-you:apply`** - Get pattern context or save workflows for reuse
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
