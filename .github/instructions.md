# Claude Code Plugin Development Guide

**IMPORTANT**: This is a general reference guide for developing Claude Code plugins. It describes the standard plugin architecture, component types, and best practices that apply to ANY Claude Code plugin project. This is NOT documentation of this specific project's structure.

For information about this specific project (Symbiosis plugins), see the README.md and project-specific documentation in the repository.

---

This guide provides foundational knowledge for developing Claude Code plugins, suitable for both GitHub Copilot and Claude Code development workflows.

## Plugin Architecture Overview

Claude Code plugins extend Claude's capabilities through a structured component system. Each plugin consists of:

- **Commands**: Slash commands that users invoke explicitly (e.g., `/commit`, `/review`)
- **Skills**: Context-aware knowledge bases that Claude can invoke automatically
- **Agents**: Autonomous subprocesses for complex, multi-step tasks
- **Hooks**: Event-driven scripts that respond to Claude's actions
- **MCP Servers**: External tool integrations via Model Context Protocol
- **LSP Servers**: Language Server Protocol integrations for code intelligence features

## Directory Structure

```
.claude/plugins/your-plugin/
├── .claude-plugin/
│   └── plugin.json      # Plugin manifest (required)
├── commands/            # Slash command definitions
│   └── command-name.md
├── skills/              # Auto-invoked knowledge bases
│   └── skill-name/
│       └── SKILL.md     # Uppercase required
├── agents/              # Autonomous task handlers
│   └── agent-name.md
├── hooks/               # Event-driven automation
│   ├── hooks.json       # Hook configuration
│   └── script-name.sh   # Hook scripts
└── .mcp.json           # MCP server configuration (optional)
```

**Key Points:**
- `plugin.json` must be in `.claude-plugin/` directory
- Skills use `skill-name/SKILL.md` structure (uppercase filename)
- Commands and agents are flat `.md` files in their directories

## Core Components

### 1. Commands

Commands are user-invoked slash commands defined in Markdown files with YAML frontmatter.

**Structure:**
```markdown
---
description: Brief description shown in autocomplete
allowed-tools: Bash(git add:*), Bash(git status:*), Read, Task  # Comma-separated with optional restrictions
args: [optional, positional, arguments]  # Optional: Positional arguments
---

# Command Implementation

Your command content here. Can include:
- Markdown instructions for Claude
- Bash script blocks with ```bash
- File reference patterns using **/*.ext
- Tool invocations (must be in allowed-tools)
```

**Key Points:**
- Filename determines command name: `command-name.md` → `/command-name`
- First H1 (`#`) is used as command title
- `allowed-tools` specifies which tools Claude can invoke (comma-separated format)
- Can optionally restrict tool usage with `ToolName(pattern:*)` syntax
- Can execute bash scripts directly in code blocks
- Use `${CLAUDE_PLUGIN_ROOT}` for plugin directory references

### 2. Skills

Skills are automatically invoked by Claude when relevant to the task. They contain specialized knowledge.

**Directory Structure:**
```
skills/
└── skill-name/
    └── SKILL.md    # Uppercase filename required
```

**SKILL.md Structure:**
```markdown
---
name: skill-name  # Required: Unique skill identifier
description: When to use this skill (critical for auto-detection)
license: MIT      # Optional: License information
---

# Skill Content

Provide comprehensive knowledge about a specific domain:
- Technical specifications
- Implementation patterns
- Best practices
- Code examples
- Progressive disclosure (500-line limit recommended)
```

**Best Practices:**
- Write clear, specific trigger descriptions in `description`
- Focus on "when to use" over "what it does"
- Break large skills into smaller, focused pieces
- Use practical examples over theoretical explanations
- Place in `skill-name/SKILL.md` structure (not flat files)

### 3. Agents

Agents are autonomous subprocesses for complex workflows requiring multiple steps.

**Structure:**
```markdown
---
name: agent-name                # Required: Unique agent identifier
description: Brief agent purpose and trigger conditions
tools: Read, Bash, Grep         # Required: Comma-separated tool list (not array)
model: inherit                  # Required: Model to use (inherit, sonnet, opus, haiku)
color: blue                     # Optional: UI color indicator
---

# Agent System Prompt

Define the agent's:
- Role and responsibilities
- Available tools and usage patterns
- Decision-making criteria
- Output format expectations
- Error handling approach
```

**Key Points:**
- `name` must be unique across all agents
- `tools` uses comma-separated format, NOT array `[...]`
- `model: inherit` means use parent conversation's model
- `description` should include both purpose AND when to invoke

**When to Create Agents:**
- Multi-step workflows requiring autonomy
- Tasks needing specialized decision-making
- Background processing requirements
- Repeated complex operations

### 4. Hooks

Hooks are shell scripts triggered by Claude Code events.

**Configuration (hooks/hooks.json):**
```json
{
  "description": "Plugin hooks description",
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh",
            "timeout": 30
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session-end.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

**Structure Requirements:**
- Top-level `hooks` object contains event arrays
- Each event is an array of hook groups
- Each hook has: `type` (always "command"), `command` (script path), `timeout` (seconds)
- Use `${CLAUDE_PLUGIN_ROOT}` for portability

**Available Events:**
- `PreToolUse` / `PostToolUse`: Before/after tool execution
- `PostToolUseFailure`: After Claude tool execution fails
- `SessionStart` / `SessionEnd`: Session lifecycle
- `UserPromptSubmit`: After user sends message
- `SubagentStart`: When subagent is started
- `SubagentStop`: When subagent completes
- `Stop`: When Claude stops generating
- `PreCompact`: Before conversation summarization
- `PermissionRequest`: When permission dialog is shown
- `Notification`: On notification events

**Hook Input (stdin):**
Hooks receive event data as JSON via stdin. Parse with Python or jq:
```bash
#!/bin/bash
event_data=$(cat)
# With jq:
tool_name=$(echo "$event_data" | jq -r '.toolName // empty')
# With Python:
tool_name=$(echo "$event_data" | python3 -c "import sys,json; print(json.load(sys.stdin).get('toolName',''))")
```

### 5. Plugin Manifest (plugin.json)

**Simple Structure (Recommended):**
```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "Plugin description",
  "author": {
    "name": "Your Name"
  },
  "homepage": "https://github.com/user/plugin",
  "repository": "https://github.com/user/plugin",
  "license": "MIT",
  "hooks": "./hooks/hooks.json"
}
```

**Key Points:**
- `commands`, `skills`, `agents` are **auto-discovered** from standard directories
- No need to explicitly configure paths unless using non-standard locations
- `hooks` path is required if using hooks
- `author` can be string or object with `name` field
- Standard directory layout is automatically detected:
  - `commands/*.md` → slash commands
  - `skills/*/SKILL.md` → skills
  - `agents/*.md` → agents

**Advanced Configuration (Optional):**
Only needed for custom paths:
```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "...",
  "commands": {
    "autoDiscover": true,
    "path": "./custom-commands"
  },
  "skills": {
    "autoDiscover": true,
    "path": "./custom-skills"
  }
}
```

## Key Development Patterns

### 1. File References in Commands

Commands can reference files using glob patterns:
```markdown
Review these files:

**/*.py
src/**/*.ts
```

Claude will automatically read matching files.

### 2. Interactive Commands with AskUserQuestion

Commands can prompt users for choices:
```markdown
Before proceeding, ask the user:

Use AskUserQuestion tool with:
- Question: "Which approach do you prefer?"
- Options: ["Option A", "Option B", "Option C"]
```

### 3. Dynamic Script Execution

Commands can execute bash scripts:
```markdown
Run the following analysis:

```bash
#!/bin/bash
# Your script here
source "${CLAUDE_PLUGIN_ROOT}/scripts/common-functions.sh"
analyze_codebase
```
```

### 4. Plugin Settings with .local.md

Store user-configurable settings:
```
.claude/plugin-name.local.md
```

Content:
```markdown
---
apiKey: user-specific-key
threshold: 0.85
---

User-specific notes or configuration details.
```

Read in scripts:
```bash
config_file=".claude/plugin-name.local.md"
api_key=$(grep -m1 "^apiKey:" "$config_file" | cut -d' ' -f2)
```

### 5. MCP Server Integration

Define external tools via `.mcp.json`:
```json
{
  "mcpServers": {
    "server-name": {
      "command": "node",
      "args": ["./server.js"],
      "env": {
        "API_KEY": "value"
      }
    }
  }
}
```

## Best Practices

### Do:
- Keep commands focused on single responsibilities
- Write descriptive skill trigger descriptions
- Use meaningful variable names in hooks
- Test hooks with sample event data
- Document complex logic with inline comments
- Use `${CLAUDE_PLUGIN_ROOT}` for portability
- Validate user input in interactive commands
- Handle errors gracefully with clear messages

### Don't:
- Create overly broad skills that trigger too often
- Use emoji in technical documentation
- Make assumptions about user environment
- Skip error handling in hooks
- Hard-code absolute paths
- Ignore hook exit codes (non-zero blocks operations)
- Create deeply nested command dependencies

## Common Patterns

### Pattern: Session Initialization
```bash
# hooks/session-start.sh
#!/bin/bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT}"
DATA_DIR="${PLUGIN_ROOT}/data"

mkdir -p "$DATA_DIR"
echo "Session started at $(date)" >> "$DATA_DIR/sessions.log"
```

### Pattern: Tool Use Validation
```bash
# hooks/pre-tool-use.sh
#!/bin/bash
event_data=$(cat)

# Parse with Python (recommended - no external dependencies)
read -r tool_name command < <(
  echo "$event_data" | python3 <<'EOF'
import json, sys
data = json.load(sys.stdin)
print(data.get('toolName', ''), data.get('parameters', {}).get('command', ''))
EOF
)

if [[ "$tool_name" == "Bash" ]] && [[ "$command" == *"rm -rf /"* ]]; then
  echo "Blocked: Dangerous command detected" >&2
  exit 1
fi
```

**Alternative with jq** (requires jq installed):
```bash
tool_name=$(echo "$event_data" | jq -r '.toolName')
command=$(echo "$event_data" | jq -r '.parameters.command')
```

### Pattern: Multi-Step Agent
```markdown
---
description: Multi-step analysis workflow
tools: [Read, Grep, Bash, Edit]
---

# System Prompt

You are an analysis agent. Follow these steps:

1. Use Grep to find relevant code patterns
2. Use Read to examine matching files
3. Use Bash to run static analysis tools
4. Summarize findings in structured format

Output Format:
- Issues Found: [count]
- Severity: [high/medium/low]
- Recommendations: [list]
```

## Debugging Tips

1. **Test Commands Independently**: Invoke with `/command-name` to verify behavior
2. **Validate Hook JSON**: Ensure hooks.json syntax is correct
3. **Check Hook Permissions**: Hooks must be executable (`chmod +x`)
4. **Log Hook Events**: Use stderr for debug logging (`>&2 echo "Debug: ..."`)
5. **Verify File Paths**: Use absolute paths or `${CLAUDE_PLUGIN_ROOT}`
6. **Test Event Data**: Manually pipe test JSON to hooks for validation

## Security Considerations

- Never commit API keys or secrets to plugin files
- Use `.local.md` for user-specific sensitive data
- Validate all user input in interactive commands
- Be cautious with `PreToolUse` hooks blocking tool execution
- Review bash commands for injection vulnerabilities
- Limit hook execution time to prevent blocking
- Use readonly operations where possible

## Performance Guidelines

- Keep skills under 500 lines for optimal loading
- Minimize hook execution time (< 1 second ideal)
- Cache expensive computations in session files
- Use background processes for long-running tasks
- Avoid recursive agent invocations
- Limit file reads in hooks to essential checks

## Testing Workflow

1. **Manual Testing**: Use Claude Code CLI to test commands interactively
2. **Hook Testing**: Create sample event JSON and pipe to hooks
3. **Integration Testing**: Verify component interactions work correctly
4. **Edge Cases**: Test with empty inputs, large files, special characters
5. **Error Paths**: Verify error messages are clear and actionable

## Additional Resources

- Official Documentation: [claude.ai/docs](https://claude.ai/docs)
- Plugin Examples: Browse community plugins for patterns
- MCP Specification: For advanced external tool integration
- Agent SDK: For programmatic plugin development

---

This guide covers fundamental concepts for Claude Code plugin development. For specific implementation questions, consult the official documentation or examine existing well-structured plugins for reference patterns.
