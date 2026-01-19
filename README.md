# Symbiosis

**Human-AI symbiotic development tools**

A Claude Code plugin marketplace exploring the philosophical relationship between developers and AI through complementary capabilities.

## Core Principles

**No auth, No backend, No external APIs**

All processing happens locally on your machine. Your data never leaves your computer. No telemetry, no cloud services, no authentication required.

## The Philosophy

**Symbiosis** represents the mutual relationship between human developers and AI:

- **As You**: Claude learns your patterns and acts as your extended memory
- **With Me**: Working with you, Claude elicits requirements and guides your thinking

Together, they form a symbiotic development environment where human creativity and AI capabilities enhance each other.

---

## Available Plugins

### [As You](./plugins/as-you/README.md)

**"I (Claude) act as you"**

Claude learns from your work patterns and builds knowledge automatically from your explicit notes.

**Key Features:**
- Pattern extraction from session notes through statistical analysis
- Automatic skill and agent generation from repeated patterns
- Statistical scoring (TF-IDF, PMI, time-decay)
- Pure Python implementation with standard library only

### [With Me](./plugins/with-me/README.md)

**"You work with me (Claude)"**

Working with you, Claude elicits requirements through information theory-inspired adaptive questioning.

**Key Features:**
- `/with-me:good-question` - Adaptive requirement elicitation with automatic effectiveness tracking
- `/with-me:stats` - Question effectiveness dashboard with reward-based analytics
- Adaptive questioning based on uncertainty dimensions (simplified approximation model)
- Structured specification generation via forked context analysis

---

## Installation

### Add Marketplace

```bash
# Add this marketplace to Claude Code
/plugin marketplace add h315uk3/symbiosis
```

### Install Plugins

```bash
# Install As You plugin
/plugin install as-you@h315uk3-symbiosis

# Install With Me plugin
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

## Resources

- [Claude Code Plugins](https://code.claude.com/docs/en/plugins)
- [Plugin Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
