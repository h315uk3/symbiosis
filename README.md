# Symbiosis

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/downloads/)
[![Tests](https://github.com/h315uk3/symbiosis/actions/workflows/test.yml/badge.svg)](https://github.com/h315uk3/symbiosis/actions/workflows/test.yml)
[![CodeQL](https://github.com/h315uk3/symbiosis/actions/workflows/codeql.yml/badge.svg)](https://github.com/h315uk3/symbiosis/actions/workflows/codeql.yml)

**Claude Code plugins that just work**

> No setup. No dependencies. No databases. No servers.
> Just install and start using.

Two plugins to enhance your Claude Code workflow—one remembers your patterns, the other helps clarify your requirements.

## Core Principles

**No auth, No backend, No external APIs**

All processing happens locally on your machine. Your data never leaves your computer. No telemetry, no cloud services, no authentication required.

## The Philosophy

**Symbiosis** represents the mutual relationship between human developers and AI:

- **As You**: Claude learns your patterns and acts as your extended memory
- **With Me**: Working with you, Claude elicits requirements and guides your thinking

Together, they form a symbiotic development environment where human creativity and AI capabilities enhance each other.

---

## Plugins

### [as-you](./plugins/as-you/README.md) — Teach Once, Remember Forever

Claude learns your coding patterns and applies them automatically.

```bash
# Teach once
/as-you:learn "Use environment variables for API keys"

# Applied automatically in future sessions
```

**Why use it:**
- No external dependencies (Python standard library only)
- 100% local—no network calls* (*except Claude Code itself, obviously), no databases
- Privacy by design—your patterns stay on your machine
- Works immediately after installation

### [with-me](./plugins/with-me/README.md) — Claude Asks the Right Questions

Claude helps you clarify requirements through adaptive questioning.

```bash
/with-me:good-question
> "Is this for internal use or customer-facing?"
# Claude adapts questions based on your answers
```

**Why use it:**
- No external dependencies (Python standard library only)
- Adaptive questioning—gets smarter as you answer
- 100% local processing* (*Claude Code does the thinking, we handle the data)
- Works immediately after installation

---

## Installation

### Add Marketplace

Add this marketplace to Claude Code:

```bash
/plugin marketplace add h315uk3/symbiosis
```

### Install Plugins

Install As You plugin:

```bash
/plugin install as-you@h315uk3-symbiosis
```

Install With Me plugin:

```bash
/plugin install with-me@h315uk3-symbiosis
```

Or use the interactive UI:

1. Run `/plugin`
2. Select the **Discover** tab
3. Choose your plugin and press **Enter**
4. Select installation scope (User/Project/Local)

---

## License

GNU AGPL v3 - [LICENSE](LICENSE)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and contribution guidelines.

## Resources

- [Claude Code Plugins](https://code.claude.com/docs/en/plugins)
- [Plugin Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
