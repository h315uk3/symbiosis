# With Me

**"You work with me (Claude)" - Collaborative AI assistant.**

A Claude Code plugin that helps you work more effectively with Claude by facilitating clear communication and requirement gathering.

## Philosophy

Sometimes developers can't articulate what they need. Sometimes requirements are unclear. Sometimes you know what you want but can't express it in words. **With Me** helps bridge that gap through structured dialogue and targeted questioning.

When you use this plugin, you'll find yourself saying "good question" - because the questions surface aspects you hadn't considered and help you clarify what you couldn't express.

## Status

🚧 **Under Development** - Core commands available, more features coming soon.

## Available Commands

### `/with-me:good-question` - Requirement Clarification

**The command that makes you say "good question"**

When you can't articulate your requirements, this command conducts a structured interview to extract all the context Claude needs:

- **Reference Materials**: Documentation, APIs, specifications to review
- **Implementation Context**: Existing code patterns, similar features
- **Requirements**: Expected behavior, inputs, outputs
- **Constraints**: Performance, security, compatibility needs
- **Edge Cases**: Error handling, validation requirements
- **Quality Attributes**: What matters most for this implementation

**Usage:**
```bash
/with-me:good-question
```

The command will guide you through a multi-stage interview, asking progressively deeper questions based on your responses. By the end, both you and Claude will have a clear, unambiguous understanding of what needs to be built.

**Note:** This isn't just a series of questions - it's an active investigation. Claude will:
- Fetch and read documentation you reference
- Examine code files you mention
- Ask follow-up questions when answers are vague
- Validate understanding before proceeding
- Summarize requirements for your confirmation

## Planned Features

- Team workflow coordination
- Code sharing and collaboration tools
- Project synchronization
- Additional communication facilitation commands

## Installation

### Via Marketplace (Recommended)

```bash
# Add marketplace (first time only)
/plugin marketplace add h315uk3/as_you

# Install plugin
/plugin install with-me@h315uk3-as_you
```

### Requirements

- **Claude Code CLI**: https://claude.com/claude-code

## License

GNU AGPL v3 - [LICENSE](../../LICENSE)

## Related Resources

- [Claude Code Plugins](https://code.claude.com/docs/en/plugins)
- [As You Plugin](../as-you/README.md)
