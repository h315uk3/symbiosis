---
description: "Manage learned patterns: save as skills/agents, analyze, review quality, and view statistics"
allowed-tools: [Read, Bash, Glob, AskUserQuestion, Task]
---

# Pattern Management

Manage your accumulated patterns: save knowledge as skills or agents, analyze pattern quality, and maintain your knowledge base.

## Execution Steps

1. **Run Analysis and Collect Statistics**

   Execute the following commands:
   ```bash
   pwd
   export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
   python3 -m as_you.lib.analysis_orchestrator
   python3 -m as_you.commands.memory_stats
   ```

   Then read the necessary files:
   - `.claude/as_you/pattern_tracker.json` (if exists)
   - `.claude/as_you/active_learning.json` (if exists)

2. **Display Pattern Statistics**

   Show sections: Pattern Analysis, Confidence Tracking, Knowledge Base, Memory Review (SM-2)

   Include counts for: patterns, scores, confidence levels, skills/agents, SM-2 review status

3. **Present Management Options** using AskUserQuestion

   - Question: "What would you like to do?"
   - Header: "Pattern Management"
   - multiSelect: false
   - Options:
     - Label: "Save as skill/agent"
       Description: "Promote high-value patterns to reusable skills or agents"
     - Label: "Analyze patterns"
       Description: "Deep analysis of pattern quality and promotion recommendations"
     - Label: "Review quality (SM-2)"
       Description: "Assess usefulness of patterns scheduled for review"
     - Label: "View statistics"
       Description: "Show detailed pattern statistics and top patterns"

4. **Execute Based on Selection**

   **If "Save as skill/agent":**
   - Check if .claude/as_you/pattern_tracker.json exists
   - If NOT exist: Display initialization message, return to step 3
   - Execute with Bash tool:
     ```bash
     export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
     python3 -m as_you.commands.promotion_analyzer
     ```
   - Parse JSON output and display promotion candidates
   - Show: pattern text, type (skill/agent), suggested name, composite score, count, sessions
   - Ask: "Which pattern would you like to promote?" (Top 4 candidates + Other + Skip)
   - If pattern selected:
     - If type is "skill":
       - Generate skill content from pattern contexts: title, overview, guidelines, examples
       - Ensure skill name has `u-` prefix (e.g., `u-python-patterns`)
       - Execute with Bash tool:
         ```bash
         export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
         python3 -m as_you.commands.skill_creator "<pattern-name>" "<skill-content>"
         ```
       - Skill creator auto-adds `u-` prefix and `source: as-you` frontmatter
       - Display: "✓ Skill created at .claude/skills/u-{name}/SKILL.md"
     - If type is "agent":
       - Generate agent content from pattern contexts: name, description, tools, execution steps
       - Ensure agent name has `u-` prefix (e.g., `u-lint-fix`)
       - Launch `as-you:component-generator` agent via Task tool with agent spec
       - Agent creates file at `.claude/agents/u-{name}.md` with `source: as-you`
       - Launch `as-you:promotion-reviewer` agent via Task tool to validate
       - Display: "✓ Agent created at .claude/agents/u-{name}.md"
   - Return to step 3

   **If "Analyze patterns":**
   - Check if .claude/as_you/pattern_tracker.json exists
   - If NOT exist: Display "No pattern data available", return to step 3
   - Launch `as-you:memory-analyzer` agent via Task tool
   - Agent analyzes using BM25, Ebbinghaus, Shannon Entropy, Bayesian confidence
   - Display analysis summary: high-value patterns, uncertainty, general vs specialized
   - Ask: "What would you like to do next?" (Merge patterns / Return to menu)
   - If "Merge patterns":
     - Show merge candidates with co-occurrence count
     - Execute with Bash tool (pattern_merger module) if confirmed
   - Return to step 3

   **If "Review quality (SM-2)":**
   - Check if .claude/as_you/pattern_tracker.json exists
   - If NOT exist: Display setup instructions, return to step 3
   - Execute with Bash tool to find due patterns:
     ```bash
     export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
     python3 -m as_you.commands.pattern_review find-due
     ```
   - If output shows "0 patterns due":
     - Display: "No patterns due yet. SM-2 schedules reviews at optimal intervals."
     - Read pattern_tracker.json and show next 5 upcoming review dates
     - Return to step 3
   - If patterns due:
     - Display SM-2 quality scale:
       ```
       # Pattern Quality Assessment

       SM-2 schedules pattern reviews to maintain knowledge quality.
       Rate each pattern's usefulness and accuracy (0-5):

       5 - Excellent: Very useful, accurate, would use again
       4 - Good: Useful and accurate
       3 - Adequate: Still useful (minimum to keep)
       2 - Poor: Outdated or inaccurate information
       1 - Very Poor: Rarely useful
       0 - Obsolete: Completely wrong or irrelevant

       Note: Quality < 3 resets review interval to 1 day for re-evaluation.
       Quality ≥ 3 extends the interval based on your confidence.
       ```
     - For each pattern (max 10):
       - Read .claude/as_you/pattern_tracker.json and find pattern details
       - Display: pattern text, usage count, current SM-2 state (interval/repetitions/EF)
       - Ask quality rating (0-5) using AskUserQuestion:
         - Question: "How useful and accurate is this pattern? (Use Other for 0-1)"
         - Header: "Quality"
         - Options:
           - "5 - Excellent" / Description: "Very useful, accurate, would use again"
           - "4 - Good" / Description: "Useful and accurate"
           - "3 - Adequate" / Description: "Still useful (minimum to keep)"
           - "2 - Poor" / Description: "Outdated or inaccurate information"
         - Note: If quality is 0 (Obsolete) or 1 (Very poor), select "Other" and enter the number
       - Execute with Bash tool to apply feedback:
         ```bash
         export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
         python3 -m as_you.commands.pattern_review apply-feedback "<pattern-text>" <quality>
         ```
       - Parse output and display result:
         - If "✓ Updated": Extract and show "next review in X days (EF: X.XX)"
         - If "✗ Error": Show error and continue to next pattern
     - Return to step 3

   **If "View statistics":**
   - Check if .claude/as_you/pattern_tracker.json exists
   - If NOT exist: Display "No pattern data yet. Use /as-you:learn to start.", return to step 3
   - Read .claude/as_you/pattern_tracker.json
   - Display detailed statistics:
     - Total patterns, promotion candidates, SM-2 tracked patterns
     - Top 10 patterns sorted by composite_score (descending)
     - For each: text, composite/BM25/Ebbinghaus scores, count, last seen
   - Display active edits analysis status (from active_learning.json)
   - If unanalyzed edits exist:
     - Ask: "Analyze active edits now?" (Yes/No)
     - If Yes: Launch `as-you:code-pattern-analyzer` agent
   - Return to step 3

## Understanding the Scores

**BM25 Score**
- Measures pattern distinctiveness based on term rarity in the corpus
- Higher = pattern contains rare, specific terminology
- Lower = pattern contains common, general terms
- Saturates to avoid over-weighting repeated terms (k1=1.5, b=0.75)

**Ebbinghaus Score**
- Based on Ebbinghaus forgetting curve: R(t) = e^(-t/s)
- Memory strength increases with repetition count
- Recent and frequently-repeated patterns maintain high scores

**Shannon Entropy Score**
- Measures pattern diversity across contexts (sessions, categories)
- High entropy (>0.7) = general-purpose pattern (appears in diverse contexts)
- Low entropy (<0.3) = specialized pattern (appears in specific contexts)

**Composite Score**
- Weighted combination: BM25 (40%) + PMI (30%) + Ebbinghaus (30%)
- Final ranking metric for pattern importance
- Range: 0.0 to 1.0

**Bayesian Confidence**
- Mean: Expected quality/usefulness (0-1)
- Variance: Uncertainty in the estimate
- Confidence interval: 95% probability range
- Updated with each pattern observation

**Thompson Sampling (Beta-Binomial)**
- Alpha: Success count + 1
- Beta: Failure count + 1
- Used for exploration-exploitation balance in pattern selection
- Patterns with high success rate sampled more frequently

## Related Commands

- `/as-you:learn` - Add notes and capture patterns
- `/as-you:workflows` - Save and manage workflows
- `/as-you:help` - Full documentation
