# Contributing to as-you

This guide covers as-you plugin specific development. For general contribution guidelines, see the [root CONTRIBUTING.md](../../CONTRIBUTING.md).

## Plugin Overview

as-you is a pattern learning plugin that:
- Captures user notes and detects patterns
- Scores patterns using statistical methods (BM25, Bayesian, Ebbinghaus)
- Promotes high-value patterns to skills/agents
- Provides context-aware pattern retrieval

## Architecture

**Key Components:**
- **Hooks**: SessionStart/SessionEnd lifecycle, UserPromptSubmit, PostToolUse
- **Commands**: User-facing slash commands (`/as-you:learn`, `/as-you:apply`, etc.)
- **Agents**: Autonomous task handlers (pattern-learner, memory-analyzer, etc.)
- **Library**: Shared Python modules for scoring, pattern detection, and data management

**Data Flow:**
1. User adds notes via `/as-you:learn`
2. SessionEnd hook processes and scores patterns
3. Patterns accumulate across sessions
4. `/as-you:apply` retrieves relevant patterns for context

## Testing Commands and Agents

Prompt files (`commands/*.md`, `agents/*.md`) cannot be automatically tested. Manual testing is required.

### Why Manual Testing?

- Claude Code interprets prompts at runtime
- AskUserQuestion UI must be visually verified
- LLM responses are non-deterministic
- Tool availability varies by version

### Test Setup

1. **Start Fresh Session**
   ```bash
   /exit
   claude
   ```

2. **Verify Plugin Loaded**
   - Check for "As You plugin loaded" message
   - If promotion candidates exist, summary should display

### Command Test Procedures

**`/as-you:learn` - Add Note**
- Test: Add a note with various inputs
- Verify: Note is translated to English if non-English, confirmation appears

**`/as-you:memory` - Memory Dashboard**
- Test: Run without prerequisites
- Verify: Statistics display, options appear (View candidates, Analyze, Detect similar)

**`/as-you:apply` - Apply Context**
- Test: Run with task description
- Verify: Relevant patterns retrieved, context provided

**`/as-you:active` - Toggle Active Learning**
- Test: `/as-you:active on`, then `/as-you:active status`, then `/as-you:active off`
- Verify: State toggles correctly, statistics shown

**`/as-you:help` - Help Display**
- Test: Run command
- Verify: All commands listed with descriptions

### Agent Testing

Agents are invoked automatically. Test by triggering their conditions:

**`memory-analyzer`**: Triggered from `/as-you:memory` → "Analyze patterns"

**`component-generator`**: Triggered from promotion flow

### When to Test

**Must test before commit:**
- New command/agent creation
- Logic flow changes
- Frontmatter modifications
- Script path changes

**Optional:**
- Minor wording improvements
- Comment/documentation changes

## Adding New Python Modules

1. Follow existing module patterns in `as_you/lib/` for structure and doctest format
2. Run `mise run test` to verify doctests pass
3. Run `mise run lint` to ensure code style compliance

## Common Issues

**Frontmatter Errors:**
- Missing `allowed-tools`: Add required tools to frontmatter
- Invalid YAML: Check indentation and quotes

**Script Path Errors:**
- Verify path from workspace root
- Test script directly before integrating

**AskUserQuestion Errors:**
- Maximum 4 options (excluding auto-added "Other")
- Ensure options are distinct

## Resources

- [Technical Overview](./docs/technical-overview.md) - Algorithms and configuration
- [Root CONTRIBUTING](../../CONTRIBUTING.md) - General guidelines
