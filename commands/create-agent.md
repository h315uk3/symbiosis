---
description: "Create a new agent with AI assistance or manual template"
argument-hint: "agent-name [--manual]"
allowed-tools: [Skill, Task, Write, Bash]
---

# Create Agent

Create a new agent (AI-assisted or manual).

If $ARGUMENTS is empty, display help:

## Usage
```
/as-you:create-agent "agent-name"              # AI-assisted mode
/as-you:create-agent "agent-name" --manual     # Manual mode
```

## Examples
```
/as-you:create-agent "bug-investigator"
/as-you:create-agent "code-reviewer" --manual
```

---

If $ARGUMENTS is provided:

### Manual Mode (with --manual flag)

1. Remove unwanted characters from agent name (convert to kebab-case)
2. Create `agents/{agent-name}.md` file
3. Template content:
   ```markdown
   ---
   name: {agent-name}
   description: "Clearly describe this agent's role and when it should be used."
   tools: Read, Write, Glob, Grep, Bash
   model: inherit
   color: blue
   ---

   # {Agent Name}

   You are a specialized agent responsible for [agent role].

   ## Responsibilities

   [Specific role description]

   ## Execution Steps

   1. Step 1
   2. Step 2
   3. Step 3

   ## Reporting Format

   [How to report results]

   ## Notes

   - Note 1
   - Note 2
   ```
4. Respond: "Agent '{agent-name}' template created"
5. Guide: "Edit `agents/{agent-name}.md` to add content"

### AI-Assisted Mode (default)

1. **Load plugin-dev agent-development skill**:
   ```
   Skill tool: "plugin-dev:agent-development"
   ```
2. **Launch component-generator agent**:
   ```
   Task tool:
   subagent_type: "component-generator"
   prompt: "Create agent '{agent-name}'. Clearly define role and execution steps."
   description: "Generate agent component"
   ```
3. Review generated content
4. Request approval using AskUserQuestion
5. If approved, create file
6. Respond: "Agent '{agent-name}' created"

## Related Commands
- `/as-you:create-skill "name"` - Create skill
- `/as-you:memory-analyze` - Analyze patterns
