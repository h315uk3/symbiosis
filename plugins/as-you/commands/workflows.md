---
description: "Manage workflows: save procedures, view/execute, and optimize quality"
argument-hint: "[workflow-name]"
allowed-tools: [Task, Write, Read, Bash, Glob, AskUserQuestion]
---

# Workflow Management

Save, manage, and optimize reusable workflows for your development tasks.

## Usage Modes

### Mode 1: Save Workflow (with arguments)

**Usage:** `/as-you:workflows "workflow-name"`

Save recent work as a reusable workflow.

**Examples:**
```
/as-you:workflows "api-endpoint-setup"
/as-you:workflows "react-component-testing"
/as-you:workflows "database-migration"
```

**Execution:**

1. Show relevant patterns for context using `pattern_context`:
   ```bash
   export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
   python3 -m as_you.commands.pattern_context --thompson 10
   ```
   - Display top 10 patterns (Thompson Sampling) with scores
   - Help user incorporate relevant patterns into workflow

2. Analyze recent work (last 10-20 tool uses)

3. Ask: abstraction level (Specific / Generic) and scope (Last 5/10/20 actions)

4. Generate workflow content:
   - Extract steps from recent tool uses
   - Include context and rationale
   - Add prerequisites and dependencies

5. Ensure workflow name has `u-` prefix (e.g., `u-api-endpoint-setup`)

6. Create workflow file at `.claude/commands/u-{name}.md` with frontmatter:
   ```yaml
   ---
   description: Workflow description
   source: as-you
   created: 2026-01-31T10:00:00Z
   usage_count: 0
   last_used: null
   ---
   ```

7. Confirm and save

---

### Mode 2: Workflow Dashboard (without arguments)

**Usage:** `/as-you:workflows`

Browse, execute, and optimize saved workflows.

**Execution Steps:**

1. List as-you workflows from `.claude/commands/u-*.md` (sorted by last_used, then usage_count)

2. Display workflow summary:
   - Total workflows
   - Most used workflow
   - Recently added workflows

3. Ask: "What would you like to do?" (Save new workflow / View and execute / Optimize quality / Exit)

4. **Execute Based on Selection**

   **If "Save new workflow":**
   - Ask for workflow name
   - Continue with Mode 1 execution

   **If "View & execute":**
   - List all workflows with: name, description, usage_count, last_used, created date
   - Sort by usage_count (desc)
   - Ask: "Which workflow?" (Top 4 + Other + Back)
   - If workflow selected:
     - Read workflow file from `.claude/commands/u-{name}.md`
     - Display: full contents with usage stats
     - Ask: "What would you like to do?" (Execute / View steps only / Back)
     - If "Execute":
       - Extract steps from workflow content
       - Ask confirmation: "Execute these steps?" (Yes / No)
       - If Yes:
         - Execute steps sequentially
         - Update frontmatter: increment usage_count, set last_used to current timestamp
         - Save updated workflow file
         - Display: "✓ Workflow executed. Usage count: {count}"
     - If "View steps only":
       - Display steps without executing
   - Return to step 3

   **If "Optimize quality":**
   - Check if workflows exist in `.claude/commands/u-*.md`
   - If no workflows: Display "No workflows to optimize yet. Use /as-you:workflows to save one.", return to step 3
   - If workflows exist:
     - Launch `as-you:workflow-optimizer` agent via Task tool
     - Agent analyzes all u-*.md workflows in `.claude/commands/`
     - Display optimization report with:
       - Summary: total workflows, issues found, consolidation opportunities
       - Critical issues: hardcoded paths, missing error handling, unclear steps, missing tools
       - Recommended optimizations: redundancy elimination, performance improvements, documentation gaps
       - Consolidation opportunities: similar workflows that could be merged/parameterized
     - Ask: "Would you like to fix any issues?" (Yes / No)
     - If Yes: Guide user through fixing identified issues
   - Return to step 3

   **If "Exit":**
   - Respond: "Done"

## Workflow Best Practices

**Good workflows are:**
- Repeatable: Clear steps, reproducible results
- Parameterized: Abstract where needed (avoid hardcoded paths)
- Documented: Context, prerequisites, and rationale included
- Tested: Verified to work across environments
- Error-handled: Rollback procedures for failures

**Common workflow patterns:**
- Build and deploy sequences
- Test setup and execution
- Code generation templates
- Configuration management
- Migration procedures

**Quality criteria (checked by optimizer):**
- No hardcoded absolute paths (use relative paths or workspace_root)
- Proper error handling with rollback procedures
- Clear step descriptions (not vague like "Run deployment")
- Prerequisites documented (required tools, environment variables)
- Tools properly specified in frontmatter

## Pattern Context Integration

When saving workflows, relevant patterns are automatically displayed using Thompson Sampling:
- **BM25 distinctiveness**: Patterns with rare terms score higher
- **Time decay**: Recent patterns prioritized
- **Bayesian confidence**: Proven patterns weighted higher
- **Thompson Sampling**: Balances exploration/exploitation

Use these patterns to enrich your workflow with best practices.

## Related Commands

- `/as-you:learn` - Capture patterns through notes
- `/as-you:patterns` - Manage and promote patterns
- `/as-you:help` - Full documentation
