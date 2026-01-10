# Claude Code Plugin Marketplace

Personal productivity and collaboration plugins for Claude Code.

## Available Plugins

### 🧠 [As You](./plugins/as-you/README.md)

**"I (Claude) act as you" - AI learns and mimics your habits.**

Local-first pattern learning and external memory system.

- Automatically extract patterns from session notes
- Build personalized knowledge base through statistical analysis
- Create reusable skills and agents from repeated patterns
- Privacy-focused with no external dependencies

**Category**: Productivity

### 🤝 [With Me](./plugins/with-me/README.md)

**"You work with me (Claude)" - Collaborative AI assistant.**

Collaborative development and team workflow assistant.

- Team workflow coordination
- Code sharing and collaboration tools
- Project synchronization

**Status**: 🚧 Under Development

**Category**: Collaboration

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

## Requirements

- **Claude Code CLI**: https://claude.com/claude-code
- **Python 3.11+** (for As You plugin)

## Repository Structure

```
as_you/
├── .claude-plugin/
│   └── marketplace.json       # Plugin marketplace registry
├── plugins/
│   ├── as-you/               # Pattern learning plugin
│   └── with-me/             # Collaboration plugin
├── .github/                  # CI/CD configurations
├── docs/                     # Shared documentation
└── README.md                 # This file
```

## Development

See individual plugin documentation for development details:

- [As You Development](./plugins/as-you/README.md#development)
- [With Me Development](./plugins/with-me/README.md)

## License

GNU AGPL v3 - [LICENSE](LICENSE)

## Resources

- [Claude Code Plugins](https://code.claude.com/docs/en/plugins)
- [Plugin Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
