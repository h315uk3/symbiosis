# Symbiosis

**Human-AI symbiotic development tools**

A Claude Code plugin marketplace exploring the philosophical relationship between developers and AI through complementary capabilities.

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
- Local-first knowledge base with zero external dependencies
- Automatic skill and agent generation from repeated patterns
- Privacy by design - all data stays on your machine

### [With Me](./plugins/with-me/README.md)

**"You work with me (Claude)"**

Working with you, Claude elicits requirements through entropy-reducing communication and adaptive questioning.

**Key Features:**
- `/good-question` - Information-theoretic requirement elicitation
- Adaptive questioning based on uncertainty dimensions
- Structured specification generation via forked context analysis
- Multi-turn conversation optimization with prompt caching

---

## Installation

### Add Marketplace

```bash
# Add this marketplace to Claude Code
/plugin marketplace add h315uk3/as_you
```

### Install Plugins

```bash
# Install As You plugin
/plugin install as-you@h315uk3-as_you

# Install With Me plugin
/plugin install with-me@h315uk3-as_you
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
