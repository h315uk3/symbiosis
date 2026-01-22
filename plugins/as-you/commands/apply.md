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

1. **Analyze Recent Work**
   - Review last 10-20 tool uses from conversation history
   - Extract commands, files, patterns
   - Identify abstraction opportunities

2. **Gather Preferences**
   - Use AskUserQuestion for abstraction level:
     - Question: "How should we save this workflow?"
     - Header: "Style"
     - multiSelect: false
     - Options:
       - Label: "Specific (exact paths/commands)"
         Description: "Save exactly as executed"
       - Label: "Generic (abstract patterns)"
         Description: "Generalize for reuse"

3. **Ask About Scope**
   - Question: "Which recent work should we include?"
   - Header: "Scope"
   - multiSelect: false
   - Options:
     - Label: "Last 5 actions"
       Description: "Most recent work only"
     - Label: "Last 10 actions"
       Description: "Recent work session"
     - Label: "Last 20 actions"
       Description: "Extended work session"

4. **Generate Workflow**
   - Create workflow file at: `{pwd}/.claude/as_you/workflows/{workflow-name}.md`
   - Format:
     ```markdown
     ---
     description: "Brief description"
     created: YYYY-MM-DD
     usage_count: 0
     last_used: null
     ---

     # {Workflow Name}

     ## Steps

     1. Step description
        ```bash
        command here
        ```

     2. Next step...

     ## Context

     Patterns used:
     - Pattern 1
     - Pattern 2

     ## Notes

     Additional context...
     ```

5. **Confirm**
   - Display generated workflow
   - Ask for confirmation
   - Save if confirmed
   - Update workflow list

---

### Mode 2: Apply Dashboard (without arguments)

**Usage:** `/as-you:apply`

Browse and use saved workflows and patterns.

**Execution Steps:**

1. **Display Quick Access**
   - Execute:
     ```bash
     pwd
     export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
     python3 -m as_you.commands.pattern_context
     ```
   - Show most relevant patterns for current context

2. **List Available Workflows**
   - Use Glob: `{pwd}/.claude/as_you/workflows/*.md`
   - Display workflow list with:
     - Name
     - Description
     - Usage count
     - Last used date
   - Sort by: Last used (desc), then usage count (desc)

3. **Present Options** using AskUserQuestion:
   - Question: "What would you like to do?"
   - Header: "Action"
   - multiSelect: false
   - Options:
     - Label: "View workflow"
       Description: "Show workflow details"
     - Label: "Execute workflow"
       Description: "Run a saved workflow"
     - Label: "Get pattern context"
       Description: "Retrieve relevant patterns for current task"
     - Label: "List all workflows"
       Description: "Browse all saved workflows"
     - Label: "Save new workflow"
       Description: "Capture recent work"
     - Label: "Exit"
       Description: "Close apply dashboard"

4. **Execute Based on Selection**

   **If "View workflow":**
   - Ask which workflow to view (list from step 2)
   - Read workflow file
   - Display contents
   - Show usage stats
   - Ask: "Execute this workflow?" (Yes/No)
   - If Yes: Continue to execution
   - If No: Return to step 3

   **If "Execute workflow":**
   - Ask which workflow to execute
   - Read workflow file
   - Extract steps
   - Ask for confirmation with details:
     - Question: "Execute '{workflow-name}'?"
     - Header: "Confirm"
     - Show first 3 steps preview
     - multiSelect: false
     - Options:
       - Label: "Execute"
         Description: "Run all steps"
       - Label: "Review first"
         Description: "Show full workflow before executing"
       - Label: "Cancel"
         Description: "Don't execute"
   - If Execute:
     - Run each step
     - Update usage_count and last_used
     - Show results
   - If Review first:
     - Show full workflow
     - Ask for execution confirmation again
   - If Cancel:
     - Return to step 3

   **If "Get pattern context":**
   - Ask for task description:
     - Question: "What are you working on?"
     - Header: "Task"
     - Prompt for context
   - Execute:
     ```bash
     export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
     python3 -m as_you.commands.pattern_context "<task-description>"
     ```
   - Display relevant patterns with:
     - Pattern text
     - Composite score
     - Confidence
     - Last seen
     - Frequency
   - Show Thompson Sampling recommendations:
     - High-confidence patterns to exploit
     - Uncertain patterns to explore
   - Return to step 3

   **If "List all workflows":**
   - Use Glob: `{pwd}/.claude/as_you/workflows/*.md`
   - For each workflow, display:
     - Name
     - Description
     - Created date
     - Usage count
     - Last used
   - Sort by usage count (desc)
   - Show total: "X workflows available"
   - Return to step 3

   **If "Save new workflow":**
   - Ask for workflow name
   - Continue with Mode 1 execution (steps 1-5)
   - Return to step 3 after saving

   **If "Exit":**
   - Respond: "Done"

## Pattern Context Tips

**Best times to use pattern context:**
- Starting a new feature
- Facing a familiar problem
- Implementing similar functionality
- Reviewing best practices

**Context automatically considers:**
- BM25 relevance to your description
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
