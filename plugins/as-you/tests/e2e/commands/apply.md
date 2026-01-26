# Test Scenario: /as-you:apply Command

Test the pattern application command: save workflows and use learned patterns.

## Scenario 1: Save Workflow (with argument)

### Prerequisites
- [ ] Claude Code session with recent work history (10-20 tool uses)
- [ ] Some file edits, bash commands, or other operations completed
- [ ] Working directory: any project with `.claude/` directory

### Test Steps

#### Step 1.1: Save Recent Work as Workflow
```
/as-you:apply "api-endpoint-setup"
```

**Expected behavior:**
- [ ] LLM analyzes recent work (last 10-20 tool uses)
- [ ] AskUserQuestion: "How should we save this workflow?"
  - Options: "Specific (exact paths/commands)" or "Generic (abstract patterns)"

Select "Generic (abstract patterns)":
- [ ] AskUserQuestion: "Which recent work should we include?"
  - Options: "Last 5 actions", "Last 10 actions", "Last 20 actions"

Select "Last 10 actions":
- [ ] LLM generates workflow content based on recent work
- [ ] Displays generated workflow for review
- [ ] Asks for confirmation to save

Confirm save:
- [ ] Workflow file created at `.claude/as_you/workflows/api-endpoint-setup.md`
- [ ] Response confirms workflow saved

**Verification:**
```bash
ls -la .claude/as_you/workflows/
cat .claude/as_you/workflows/api-endpoint-setup.md
```

Expected workflow file structure:
- [ ] YAML frontmatter with: description, created, usage_count (0), last_used (null)
- [ ] Markdown heading with workflow name
- [ ] "## Steps" section with numbered steps
- [ ] Code blocks for commands/examples
- [ ] "## Context" section mentioning patterns
- [ ] "## Notes" section with additional info

#### Step 1.2: Duplicate Workflow Name
```
/as-you:apply "api-endpoint-setup"
```

**Expected behavior:**
- [ ] Detects existing workflow with same name
- [ ] Asks whether to overwrite or choose different name
- [ ] Handles user choice appropriately

---

## Scenario 2: Apply Dashboard (without argument)

### Prerequisites
- [ ] At least one workflow saved (run Scenario 1 first)
- [ ] Some patterns learned (use `/as-you:learn` to add notes if needed)

### Test Steps

#### Step 2.1: Open Dashboard
```
/as-you:apply
```

**Expected behavior:**
- [ ] Executes pattern_context command
- [ ] Shows most relevant patterns for current context
- [ ] Lists available workflows with metadata:
  - Name
  - Description
  - Usage count
  - Last used date
- [ ] Workflows sorted by: last used (desc), then usage count (desc)
- [ ] Presents AskUserQuestion menu with 6 options:
  - "View workflow"
  - "Execute workflow"
  - "Get pattern context"
  - "List all workflows"
  - "Save new workflow"
  - "Exit"

#### Step 2.2: View Workflow
Select "View workflow" from menu.

**Expected behavior:**
- [ ] AskUserQuestion lists available workflows
- [ ] User selects a workflow

Select a workflow (e.g., "api-endpoint-setup"):
- [ ] Displays full workflow contents
- [ ] Shows usage statistics
- [ ] Asks: "Execute this workflow?" (Yes/No)

Select "No":
- [ ] Returns to main dashboard menu

#### Step 2.3: Execute Workflow
Select "Execute workflow" from menu.

**Expected behavior:**
- [ ] AskUserQuestion lists available workflows
- [ ] User selects a workflow to execute

Select workflow:
- [ ] Shows confirmation dialog
- [ ] Displays preview of first 3 steps
- [ ] Options: "Execute", "Review first", "Cancel"

Select "Review first":
- [ ] Shows complete workflow
- [ ] Asks for execution confirmation again

Select "Execute":
- [ ] Runs each step sequentially
- [ ] Updates workflow metadata (usage_count++, last_used = now)
- [ ] Shows execution results
- [ ] Returns to main menu

**Verification:**
```bash
cat .claude/as_you/workflows/api-endpoint-setup.md | grep "usage_count"
```
Expected: usage_count increased by 1

```bash
cat .claude/as_you/workflows/api-endpoint-setup.md | grep "last_used"
```
Expected: last_used has today's date

#### Step 2.4: Get Pattern Context
Select "Get pattern context" from menu.

**Expected behavior:**
- [ ] AskUserQuestion: "What are you working on?"
- [ ] Prompt for task description

Enter: "Building a REST API with authentication"

**Expected behavior:**
- [ ] Executes pattern_context command with task description
- [ ] Displays relevant patterns with:
  - Pattern text
  - Composite score
  - Confidence (Bayesian)
  - Last seen date
  - Frequency count
- [ ] Shows Thompson Sampling recommendations:
  - High-confidence patterns to exploit
  - Uncertain patterns to explore
- [ ] Returns to main menu

**Verification:**
Check that displayed patterns relate to the task description (authentication, REST API, etc.)

#### Step 2.5: List All Workflows
Select "List all workflows" from menu.

**Expected behavior:**
- [ ] Displays all workflows with metadata:
  - Name
  - Description
  - Created date
  - Usage count
  - Last used date
- [ ] Sorted by usage count (descending)
- [ ] Shows total count: "X workflows available"
- [ ] Returns to main menu

#### Step 2.6: Save New Workflow
Select "Save new workflow" from menu.

**Expected behavior:**
- [ ] Prompts for workflow name
- [ ] Continues with Mode 1 execution (same as Scenario 1)
- [ ] After saving, returns to main menu

#### Step 2.7: Exit Dashboard
Select "Exit" from menu.

**Expected behavior:**
- [ ] Response: "Done"
- [ ] Dashboard closes

---

## Scenario 3: Pattern Context Retrieval

### Prerequisites
- [ ] Multiple patterns with varying scores in pattern_tracker.json
- [ ] Some patterns related to different topics (API, frontend, database, etc.)

### Test Steps

#### Step 3.1: Context-Specific Pattern Retrieval
```
/as-you:apply
```

Select "Get pattern context", enter task: "Database migration with zero downtime"

**Expected behavior:**
- [ ] Patterns ranked by composite score
- [ ] BM25 scoring prioritizes patterns with rare terms related to "database", "migration", "downtime"
- [ ] Time decay favors recent patterns
- [ ] Bayesian confidence weights proven patterns
- [ ] Thompson Sampling balances exploration/exploitation

**Verification:**
Patterns displayed should be relevant to database/migration topics, not unrelated patterns.

---

## Edge Cases

### EC1: No Recent Work to Save
Start fresh session, immediately run:
```
/as-you:apply "empty-workflow"
```

**Expected behavior:**
- [ ] LLM detects insufficient work history
- [ ] Suggests adding some work first or canceling
- [ ] No empty workflow created

### EC2: No Workflows Exist
Delete all workflows:
```bash
rm -rf .claude/as_you/workflows/*.md
```

Then run:
```
/as-you:apply
```

**Expected behavior:**
- [ ] Dashboard shows "No workflows available"
- [ ] Menu still offers "Save new workflow" option
- [ ] No errors occur

### EC3: Workflow with Special Characters
```
/as-you:apply "test-workflow-with-$pecial_chars!"
```

**Expected behavior:**
- [ ] Filename sanitized appropriately
- [ ] Workflow saved successfully
- [ ] No filesystem errors

### EC4: Empty Pattern Context Query
```
/as-you:apply
```
Select "Get pattern context", enter: "" (empty string)

**Expected behavior:**
- [ ] Handles gracefully (all patterns or error message)
- [ ] No crash

---

## Cleanup

```bash
# Remove test workflows
rm -rf .claude/as_you/workflows/

# Or remove specific test workflow
rm .claude/as_you/workflows/api-endpoint-setup.md
```

---

## Related Tests

- [learn.md](./learn.md) - Creating patterns to apply
- [memory.md](./memory.md) - Analyzing pattern scores
- [hooks/pattern_capture.md](../hooks/pattern_capture.md) - Automatic pattern detection
