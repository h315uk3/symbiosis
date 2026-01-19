---
description: "View memory statistics and analyze patterns"
allowed-tools: [Read, Bash, Glob, AskUserQuestion, Task]
---

# Memory Dashboard

Display memory statistics and analyze patterns.

## Execution Steps

1. **Collect Statistics**

   Get current directory and execute statistics collection:
   ```bash
   pwd
   export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
   python3 -m as_you.commands.memory_stats
   ```

2. **Display Dashboard**

   Format and display:
   ```markdown
   # As You Memory Dashboard

   ## Current Session
   - Notes: X entries
   - Archives: X days

   ## Pattern Analysis
   - Detected patterns: X
   - Promotion candidates: X

   ## Knowledge Base
   - Skills: X
   - Agents: X
   ```

3. **Present Options** using AskUserQuestion:
   - Question: "What would you like to explore?"
   - Header: "Explore"
   - Options:
     - Label: "View promotion candidates"
       Description: "Show patterns ready for promotion to skills/agents"
     - Label: "Analyze patterns"
       Description: "Deep analysis with memory-analyzer agent"
     - Label: "Detect similar patterns"
       Description: "Find and suggest merging similar patterns"
     - Label: "Review knowledge base"
       Description: "Review skills/agents usage and maintenance"
     - Label: "Exit"
       Description: "Close memory dashboard"

4. **Execute Based on Selection**

   **If "View promotion candidates":**
   - Execute:
     ```bash
     export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
     python3 -m as_you.commands.promotion_analyzer
     ```
   - Display candidates with scores
   - Suggest: "Use /as-you:promote to create skill/agent"

   **If "Analyze patterns":**
   - Launch memory-analyzer agent using Task tool:
     ```
     subagent_type: "as-you:memory-analyzer"
     prompt: "Analyze pattern_tracker.json and provide detailed promotion recommendations. Working directory: {pwd} (use absolute paths)"
     description: "Analyze memory patterns"
     ```

   **If "Detect similar patterns":**
   - Execute:
     ```bash
     export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
     python3 -m as_you.commands.similarity_detector
     ```
   - Display similar pairs with Levenshtein distance
   - Ask if user wants to merge:
     - If yes: Execute:
       ```bash
       export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
       python3 -m as_you.hooks.pattern_merger
       ```
     - If no: Return to menu

   **If "Review knowledge base":**
   - Read `{pwd}/.claude/as_you/skill-usage-stats.json` using absolute path (where {pwd} is from step 1)
   - Identify unused skills/agents (30+ days)
   - Display recommendations
   - Ask about archiving unused items

   **If "Exit":**
   - Respond: "Done"

## Related Commands
- `/as-you:promote` - Promote pattern to skill/agent
- `/as-you:notes` - View session notes
