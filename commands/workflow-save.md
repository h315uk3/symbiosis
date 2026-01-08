---
description: "Save recent work as a reusable workflow"
argument-hint: "[workflow-name]"
allowed-tools: [Task, Write, Read, AskUserQuestion]
---

# Save Workflow

Save a sequence of recent work as a reusable workflow command.

## Execution Steps

### 1. Analyze Recent Work

Review the last 10-20 tool uses from conversation history:
- Bash commands
- File operations (Edit, Write, Read)
- Build/test/deploy operations
- Any repeatable patterns

Extract:
- Commands executed
- Files modified
- Patterns and sequences
- Abstraction opportunities

### 2. Gather Requirements

**If $ARGUMENTS is empty:**
- Use AskUserQuestion:
  - Question: "What should we name this workflow?"
  - Header: "Name"
  - Prompt user for workflow name

**If $ARGUMENTS is provided:**
- Use provided name as workflow name

**Then ask about abstraction level:**
- Question: "How should we save this workflow?"
- Header: "Style"
- Options:
  - Label: "Specific (exact paths/commands)"
    Description: "Save exactly as executed"
  - Label: "Generic (abstract patterns)"
    Description: "Generalize for reuse (e.g., *.ts → 'TypeScript files')"

**Then ask about scope:**
- Question: "Which recent work should we include?"
- Header: "Scope"
- Options:
  - Label: "Last 5 actions"
    Description: "Most recent work only"
  - Label: "Last 10 actions"
    Description: "Recent work session"
  - Label: "Last 20 actions"
    Description: "Extended work session"
  - Label: "Let me select"
    Description: "I'll choose specific steps"

If "Let me select":
- Show numbered list of recent actions
- Ask which to include (multiSelect: true)

### 3. Ask for Description

Use AskUserQuestion:
- Question: "Describe what this workflow does (1-2 sentences)"
- Prompt user for description

### 4. Generate Workflow Command

Create `commands/{workflow-name}.md`:

```markdown
---
description: "{user-provided-description}"
allowed-tools: [Bash, Read, Write, Edit, Grep, Glob]
---

# {Workflow Name}

{Description}

## Execution Steps

1. [Step 1 description]
   - Specific operations
   - Expected outcome

2. [Step 2 description]
   - Specific operations
   - Expected outcome

...

## Error Handling

If errors occur:
- Report details
- Ask for confirmation before proceeding to next step

## Related Commands
- `/as-you:workflows` - Manage workflows
```

### 5. Preview & Confirmation

Display generated workflow to user.

Use AskUserQuestion:
- Question: "Save this workflow?"
- Header: "Confirm"
- Options:
  - Label: "Yes, save it"
    Description: "Create /as-you:{name} command"
  - Label: "Modify first"
    Description: "Let me suggest changes"
  - Label: "Cancel"
    Description: "Don't save"

**If "Yes":**
- Write to `commands/{workflow-name}.md`
- Respond:
  ```
  Saved workflow: /as-you:{name}

  To use this workflow, restart the session:
  - Type /exit and press Enter
  - Resume or start new session

  The workflow will be available after restart.
  ```

**If "Modify first":**
- Ask what to change
- Regenerate workflow
- Show preview again
- Re-confirm

**If "Cancel":**
- Respond: "Workflow save cancelled"

### 6. Security Checks

Before saving:
- Check for sensitive data (API keys, passwords, tokens)
- Check for destructive operations (rm -rf, DROP TABLE, force push)
- If found: Warn user and ask for explicit confirmation

## Examples

**Recent work:**
- Ran `npm run format`
- Ran `npm run lint`
- Ran `npm test`

**Generated workflow** (`commands/qa-check.md`):
```markdown
Run quality checks on the project.

1. Identify project type and package manager
2. Run formatter (npm run format or equivalent)
3. Run linter with strict settings
4. Execute test suite
5. Report results (show errors or success message)
```

Usage: `/as-you:qa-check`

## Related Commands
- `/as-you:workflows` - Manage saved workflows
