---
description: "Promote frequent pattern to knowledge base (skill or agent)"
argument-hint: "[pattern-name]"
allowed-tools: [Bash, Read, Task, AskUserQuestion, Write, Skill]
---

# Promote Pattern

Promote a frequent pattern to knowledge base (Skill or Agent).

## Execution Steps

### 1. Retrieve Promotion Candidates

Get current directory and retrieve candidates:
```bash
pwd
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/commands/promotion_analyzer.py"
```

If 0 candidates:
- Respond: "No promotion candidates available yet"
- Guide: "Record notes across multiple sessions to detect patterns"

### 2. Pattern Selection

**If $ARGUMENTS is empty:**
- Use AskUserQuestion to select pattern:
  - Question: "Which pattern would you like to promote?"
  - Header: "Pattern"
  - Options: List candidates with format: `{pattern} [{score}%] - {reason}`
  - Include "Cancel" option

**If $ARGUMENTS is provided:**
- Use specified pattern name
- Verify it exists in candidates
- If not found: "Pattern '{name}' not in promotion candidates"

### 3. AI Analysis & Type Determination

Analyze selected pattern to determine if it should be Skill or Agent:

**Read pattern context:**
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/commands/pattern_context.py" PATTERN_NAME
```

**Analyze characteristics:**
- **Agent indicators** (task-oriented):
  - Action verbs: "deploy", "test", "build", "analyze", "validate"
  - Multi-step procedures
  - Tool usage: Bash, Write, etc.
  - Temporal sequences

- **Skill indicators** (knowledge-oriented):
  - Domain concepts: "authentication", "api-design", "optimization"
  - Best practices
  - Reference information
  - Guidelines and principles

**AI Decision:**
- Analyze pattern name and contexts
- Determine: Skill or Agent
- Explain reasoning

### 4. Generate Component

**If determined as Agent:**

1. Infer required tools from pattern:
   - "analyze", "review", "investigate" → Read, Grep, Bash
   - "generate", "create", "write" → Write, Read
   - "test", "validate", "check" → Bash, Read
   - "build", "deploy", "execute" → Bash

2. Use plugin-dev:agent-development skill
3. Launch component-generator agent:
   ```
   subagent_type: "as-you:component-generator"
   prompt: "Create agent '{pattern-name}' with tools: {inferred-tools}. Context: {contexts}. Working directory: {pwd} (use absolute paths for all file operations)"
   description: "Generate agent component"
   ```

**If determined as Skill:**

1. Use plugin-dev:skill-development skill
2. Launch component-generator agent:
   ```
   subagent_type: "as-you:component-generator"
   prompt: "Create skill '{pattern-name}'. Context: {contexts}. Working directory: {pwd} (use absolute paths for all file operations)"
   description: "Generate skill component"
   ```

### 5. User Confirmation

Present generated component and ask:
- Question: "Create this {skill/agent}?"
- Header: "Confirm"
- Options:
  - Label: "Yes, create it"
    Description: "Save to {path}"
  - Label: "Modify first"
    Description: "Let me suggest changes"
  - Label: "Cancel"
    Description: "Don't create"

**If "Yes":**
- Create file (skills/{name}/SKILL.md or agents/{name}.md)
- Mark as promoted in pattern_tracker.json:
  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lib/promotion_marker.py" "PATTERN_NAME" {skill|agent} "{path}"
  ```
- Respond: "{Skill/Agent} created: {name}\n\nFile: {path}\n\nUse /as-you:memory to view updated stats"

**If "Modify first":**
- Ask for specific modifications
- Regenerate component
- Re-confirm

**If "Cancel":**
- Respond: "Promotion cancelled"

### 6. Check for Duplicates

Before creating, search existing using Glob with absolute paths (where {pwd} is from step 1):
- Skills: `{pwd}/skills/*/SKILL.md`
- Agents: `{pwd}/agents/*.md`

If similar name exists, warn and ask for confirmation.

## Related Commands
- `/as-you:memory` - View promotion candidates
- `/as-you:notes` - View pattern sources
