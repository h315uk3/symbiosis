---
description: "Analyze memory: patterns, confidence scores, and knowledge management"
allowed-tools: [Read, Bash, Glob, AskUserQuestion, Task]
---

# Memory Analysis

Explore pattern memory, analyze confidence, and manage knowledge base.

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

   Count workflows using Glob (do not read contents):
   - `.claude/as_you/workflows/*.md`

2. **Display Memory Dashboard**

   Show sections: Current Session, Pattern Analysis, Habit Extraction, Confidence Tracking, Knowledge Base, Memory Review (SM-2)

   Include counts for: notes, patterns, scores, confidence levels, skills/agents, SM-2 review status

3. **Present Analysis Options** using AskUserQuestion

   - Question: "What would you like to explore?"
   - Header: "Analysis"
   - multiSelect: false
   - Options:
     - Label: "Analyze active edits"
       Description: "Classify semantic patterns from recent file edits"
       (Replace with "Exit" option if no active edits need analysis)
     - Label: "View top patterns"
       Description: "Show highest-scoring patterns by composite score"
     - Label: "Review promotion candidates"
       Description: "Identify patterns ready to become skills or agents"
     - Label: "Review pattern quality"
       Description: "Assess usefulness of patterns scheduled for review"

4. **Execute Based on Selection**

   **If "View top patterns":**
   - Check if .claude/as_you/pattern_tracker.json exists
   - If NOT exist: Display setup instructions, return to step 3
   - Read .claude/as_you/pattern_tracker.json and sort by composite_score (descending)
   - Display top 10 patterns with: text, composite/BM25/Ebbinghaus/Shannon scores, count, last seen
   - Return to step 3

   **If "Review promotion candidates":**
   - Check if .claude/as_you/pattern_tracker.json exists
   - If NOT exist: Display initialization message, return to step 3
   - Use `promotion_analyzer` module to get candidates
   - Display candidates with: text, composite score, confidence, frequency, category
   - Show: "High scores + high confidence = ready for promotion"
   - If user wants to promote: Guide to `/as-you:promote` command
   - Return to step 3

   **If "Review pattern quality":**
   - Check if .claude/as_you/pattern_tracker.json exists
   - If NOT exist: Display setup instructions, return to step 3
   - Execute with Bash tool to find due patterns:
     ```bash
     export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
     python3 -m as_you.commands.pattern_review find-due
     ```
   - If output shows "0 patterns due":
     - Display: "No patterns due yet. SM-2 schedules reviews at optimal intervals."
     - Show next 5 upcoming review dates from pattern_tracker.json
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
         Replace `<pattern-text>` with the exact pattern text and `<quality>` with user's rating (0-5).
       - Parse output and display result:
         - If "✓ Updated": Extract and show "next review in X days (EF: X.XX)"
         - If "✗ Error": Show error and continue to next pattern
     - After review session:
       - Return to step 3

   **If "Analyze active edits":**
   - Read .claude/as_you/active_learning.json and count edits where `semantic_patterns` is null
   - If count == 0: Display "All edits analyzed", return to step 3
   - If count > 0:
     - Launch `as-you:code-pattern-analyzer` agent via Task tool
     - Agent analyzes edits and classifies semantic patterns
     - Display summary: total analyzed, pattern distribution
     - Return to step 3

   **If "Deep analysis":**
   - Check if .claude/as_you/pattern_tracker.json exists
   - If NOT exist: Display "No pattern data available", return to step 3
   - If exists:
     - Launch `as-you:memory-analyzer` agent via Task tool
     - Agent analyzes using BM25, Ebbinghaus, Shannon Entropy, Bayesian confidence
     - Summarize: high-value patterns, uncertainty, general vs specialized, promotion recommendations
     - Present action-oriented menu (step 4)

   **If "Exit":**
   - Respond: "Done"

4. **Action Menu** (after Deep Analysis)

   Ask: "What would you like to do next?" (Merge patterns / Consider skill creation / Consider agent creation / Exit)

5. **Execute Action**

   **If "Merge patterns":**
   - Identify merge candidates from analysis
   - Show patterns and co-occurrence count
   - Use `pattern_merger` module to merge if confirmed
   - Return to step 3

   **If "Consider skill creation":**
   - Display Tier 1 promotion recommendations
   - Generate skill content from patterns: title, overview, guidelines, examples
   - Use `skill_creator` module to create skill
   - Return to step 3

   **If "Consider agent creation":**
   - Display Tier 2 promotion recommendations
   - Guide user to create agent file at `agents/{name}.md`
   - Return to step 3

   **If "Exit":**
   - Respond: "Done"

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
- Replaces simple exponential decay with cognitive psychology model

**Shannon Entropy Score**
- Measures pattern diversity across contexts (sessions, categories)
- High entropy (>0.7) = general-purpose pattern (appears in diverse contexts)
- Low entropy (<0.3) = specialized pattern (appears in specific contexts)
- Helps identify patterns suitable for different use cases

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
- `/as-you:apply` - Use patterns in workflows
- `/as-you:help` - Full documentation
