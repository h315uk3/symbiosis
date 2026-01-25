# as-you

**Teach Once, Remember Forever**

> Claude learns your coding patterns and applies them automatically.
> No setup. No dependencies. No databases. (Just Claude Code itself.)

## Example

```
You: /as-you:learn "Use environment variables for API keys"
Claude: Note added

[Later, in a new session...]

You: Add Stripe payment integration
Claude: I'll implement the Stripe integration using environment variables 
for the API key, following your established pattern.
```

---

## Key Features

- **Automatic Pattern Learning** - Patterns emerge from your notes over time
- **Statistical Scoring** - BM25, Bayesian confidence, time decay, and more
- **Local-First** - All data stays on your machine, no external services
- **Zero Dependencies** - Pure Python standard library only
- **Memory Management** - Spaced repetition ensures patterns stay fresh
- **Context-Aware** - Retrieves relevant patterns for your current task

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
