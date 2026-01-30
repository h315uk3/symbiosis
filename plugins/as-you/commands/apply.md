---
description: "Apply learned patterns: save workflows, retrieve context, and reuse knowledge"
argument-hint: "[workflow-name]"
allowed-tools: [Task, Write, Read, Bash, Glob, AskUserQuestion]
---

# Apply Learned Patterns

Use your accumulated knowledge: save workflows, access patterns, and apply best practices.

## Usage Modes

### Mode 1: Save Workflow (with arguments)

**Usage:** `/as-you:apply "workflow-name"`

Save recent work as a reusable workflow.

**Examples:**
```
/as-you:apply "api-endpoint-setup"
/as-you:apply "react-component-testing"
/as-you:apply "database-migration"
```

**Execution:**

1. Analyze recent work (last 10-20 tool uses)
2. Ask: abstraction level (Specific / Generic) and scope (Last 5/10/20 actions)
3. Ensure workflow name has `u-` prefix (e.g., `u-api-endpoint-setup`)
4. Generate workflow file at `.claude/commands/u-{name}.md` with frontmatter including `source: as-you`
5. Confirm and save

---

### Mode 2: Apply Dashboard (without arguments)

**Usage:** `/as-you:apply`

Browse and use saved workflows and patterns.

**Execution Steps:**

1. Use `pattern_context` module to show relevant patterns for current context
2. List as-you workflows from `.claude/commands/u-*.md` (sorted by last used)
3. Ask: "What would you like to do?" (View/Execute workflow, Get pattern context, List all workflows, Save new, Exit)

4. **Execute Based on Selection**

   **If "View workflow":**
   - Ask which workflow, read and display contents with usage stats
   - Ask: "Execute this workflow?" (Yes/No)

   **If "Execute workflow":**
   - Ask which workflow, extract steps, ask confirmation (Execute/Review first/Cancel)
   - Run steps, update usage_count and last_used

   **If "Get pattern context":**
   - Use `pattern_context --thompson 10` to get top patterns (Thompson Sampling)
   - Display patterns with scores, confidence, Thompson state
   - Ask: "View context for which pattern?" (Top 4 + Other + Skip)
   - Show detailed context from notes if pattern selected

   **If "List all workflows":**
   - List all workflows with name, description, dates, usage count
   - Sort by usage count (desc)

   **If "Save new workflow":**
   - Ask for workflow name, continue with Mode 1 execution

   **If "Exit":**
   - Respond: "Done"

## Pattern Context Tips

**Best times to use pattern context:**
- Starting a new feature
- Facing a familiar problem
- Implementing similar functionality
- Reviewing best practices

**Context automatically considers:**
- BM25 distinctiveness (patterns with rare terms score higher)
- Time decay (recent patterns prioritized)
- Bayesian confidence (proven patterns weighted higher)
- Thompson Sampling (balances exploration/exploitation)

## Workflow Best Practices

**Good workflows are:**
- Repeatable: Clear steps, reproducible results
- Parameterized: Abstract where needed
- Documented: Context and rationale included
- Tested: Verified to work

**Common workflow patterns:**
- Build and deploy sequences
- Test setup and execution
- Code generation templates
- Configuration management
- Migration procedures

## Related Commands

- `/as-you:learn` - Capture patterns through notes
- `/as-you:memory` - Analyze and refine patterns
- `/as-you:help` - Full documentation
