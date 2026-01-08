---
description: "View and manage saved workflows"
allowed-tools: [Glob, Bash, Read, AskUserQuestion, Write]
---

# Workflow Management

View and manage saved workflows.

## Execution Steps

### 1. List Workflows

Execute to find user workflows (exclude built-in commands):
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/commands/workflow_list.py"
```

If no workflows:
- Respond: "No saved workflows found"
- Guide: "Create workflows with /as-you:workflow-save"

### 2. Display Workflow List

Format as table:
```markdown
# Saved Workflows

| Name | Last Updated |
|------|--------------|
| workflow1 | 2026-01-08 |
| workflow2 | 2026-01-07 |
...

Total: X workflows
```

### 3. Present Options

Use AskUserQuestion:
- Question: "What would you like to do?"
- Header: "Action"
- Options:
  - Label: "View workflow details"
    Description: "Show full workflow content"
  - Label: "Update workflow"
    Description: "Modify workflow based on recent work"
  - Label: "Delete workflow"
    Description: "Remove workflow (with confirmation)"
  - Label: "Exit"
    Description: "Close workflow management"

### 4. Execute Based on Selection

**If "View workflow details":**
- Use AskUserQuestion to select workflow from list
- Read `commands/{workflow-name}.md`
- Display contents
- Show metadata (file path, last modified)
- Return to menu or exit

**If "Update workflow":**
- Use AskUserQuestion to select workflow
- Read current workflow
- Analyze last 10-20 tool uses (Bash, Edit, Write, Read)
- Ask update method:
  - Label: "Append new steps"
    Description: "Add recent work at the end"
  - Label: "Prepend new steps"
    Description: "Add recent work at the beginning"
  - Label: "Refine existing"
    Description: "Improve descriptions without adding steps"
  - Label: "Cancel"
    Description: "Don't update"
- If not cancelled:
  - Generate updated workflow
  - Show preview (side-by-side or diff)
  - Confirm with AskUserQuestion
  - If confirmed: Write to `commands/{name}.md`
  - Respond: "Workflow updated: {name}\n\nRestart session (/exit) to use updated workflow"

**If "Delete workflow":**
- Use AskUserQuestion to select workflow
- Confirm with AskUserQuestion:
  - Question: "Delete workflow '{name}'?"
  - Header: "Confirm"
  - Options:
    - Label: "Yes, delete it"
      Description: "This cannot be undone"
    - Label: "No, cancel"
      Description: "Keep the workflow"
- If confirmed:
  - Execute: `rm commands/{name}.md`
  - Respond: "Workflow '{name}' deleted"
- Return to menu or exit

**If "Exit":**
- Respond: "Done"

## Related Commands
- `/as-you:workflow-save` - Create new workflow
