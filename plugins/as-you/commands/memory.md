---
description: "Analyze memory: patterns, confidence scores, and knowledge management"
allowed-tools: [Read, Bash, Glob, AskUserQuestion, Task]
---

# Memory Analysis

Explore pattern memory, analyze confidence, and manage knowledge base.

## Execution Steps

1. **Run Analysis and Collect Statistics**

   Execute analysis and gather stats:
   ```bash
   pwd
   export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
   python3 -m as_you.lib.analysis_orchestrator
   python3 -m as_you.commands.memory_stats
   ```

2. **Display Memory Dashboard**

   Format and display comprehensive statistics:
   ```markdown
   # As You Memory Dashboard

   ## Current Session
   - Notes: X entries
   - Archives: X days

   ## Pattern Analysis (v0.3.0)
   - Detected patterns: X
   - BM25 scores: X
   - Ebbinghaus scores: X
   - Shannon Entropy scores: X
   - Composite scores: X
   - Promotion candidates: X

   ## Habit Extraction (v0.3.1)
   - Indexed notes: X
   - Habit clusters: X

   ## Confidence Tracking
   - High confidence (>0.7): X patterns
   - Medium confidence (0.4-0.7): X patterns
   - Low confidence (<0.4): X patterns

   ## Knowledge Base
   - Skills: X
   - Agents: X
   - Memory (SM-2): X patterns tracked
   ```

3. **Present Analysis Options** using AskUserQuestion:
   - Question: "What would you like to explore?"
   - Header: "Explore"
   - multiSelect: false
   - Options:
     - Label: "View top patterns"
       Description: "Show highest-scoring patterns by composite score"
     - Label: "Analyze confidence"
       Description: "Review Bayesian confidence and uncertainty"
     - Label: "Review promotion candidates"
       Description: "Patterns ready for skill/agent promotion"
     - Label: "Detect similar patterns"
       Description: "Find and merge similar patterns"
     - Label: "Memory review (SM-2)"
       Description: "Show patterns due for review using spaced repetition"
     - Label: "Deep analysis"
       Description: "Launch memory-analyzer agent for detailed insights"
     - Label: "Exit"
       Description: "Close memory dashboard"

4. **Execute Based on Selection**

   **If "View top patterns":**
   - Read `{pwd}/.claude/as_you/pattern_tracker.json`
   - Sort patterns by `composite_score` (descending)
   - Display top 10 patterns with:
     - Pattern text
     - Composite score
     - BM25 score
     - Ebbinghaus score (memory strength)
     - Shannon Entropy score (diversity)
     - Count (frequency)
     - Last seen date
   - Return to step 3

   **If "Analyze confidence":**
   - Read `{pwd}/.claude/as_you/pattern_tracker.json`
   - For patterns with Bayesian state:
     - Calculate confidence score
     - Show mean, variance, std_dev
     - Show 95% confidence interval
   - Group by confidence level:
     - High: mean > 0.7
     - Medium: 0.4 ≤ mean ≤ 0.7
     - Low: mean < 0.4
   - Display summary and examples from each group
   - Return to step 3

   **If "Review promotion candidates":**
   - Execute:
     ```bash
     export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
     python3 -m as_you.commands.promotion_analyzer
     ```
   - Display candidates sorted by composite score
   - For each candidate show:
     - Pattern text
     - Composite score
     - Confidence (Bayesian mean)
     - Frequency count
     - Suggested category (skill/agent)
   - Show message: "High scores + high confidence = ready for promotion"
   - Ask if user wants to promote:
     - If yes: Guide to `/as-you:promote` command
     - If no: Return to step 3

   **If "Detect similar patterns":**
   - Execute:
     ```bash
     export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
     python3 -m as_you.commands.similarity_detector
     ```
   - Display similar pattern pairs with:
     - Levenshtein distance
     - BK-tree detection results
     - Similarity score
   - Ask if user wants to merge:
     - If yes:
       - Execute:
         ```bash
         export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
         python3 -m as_you.hooks.pattern_merger
         ```
       - Show merge results
     - If no: Return to step 3
   - Return to step 3

   **If "Memory review (SM-2)":**
   - Read `{pwd}/.claude/as_you/pattern_tracker.json`
   - For patterns with SM-2 state:
     - Calculate if review is due (interval elapsed)
     - Show patterns ordered by:
       1. Overdue (days past due)
       2. Due today
       3. Due soon (next 7 days)
   - For each pattern show:
     - Pattern text
     - Easiness factor
     - Current interval (days)
     - Repetitions count
     - Next review date
   - Explain: "Review helps strengthen memory. Patterns you use successfully get longer intervals."
   - Return to step 3

   **If "Deep analysis":**
   - Launch memory-analyzer agent using Task tool:
     ```
     subagent_type: "as-you:memory-analyzer"
     prompt: "Analyze pattern_tracker.json using v0.3.0 scoring (BM25, Ebbinghaus, Shannon Entropy, composite scores, Bayesian confidence, Thompson Sampling). Provide detailed insights on:
     1. High-value patterns (composite score > 0.7)
     2. Patterns with high uncertainty (Bayesian variance > 0.1)
     3. General-purpose vs specialized patterns (Shannon Entropy)
     4. Patterns with strong memory (Ebbinghaus score)
     5. Promotion recommendations with reasoning
     6. Potential pattern merges

     Working directory: {pwd} (use absolute paths)"
     description: "Deep memory analysis"
     ```
   - Summarize agent output focusing on:
     - High-value patterns (score > 0.7)
     - Pattern stability (Bayesian variance)
     - General vs specialized patterns (Shannon Entropy)
     - Memory strength (Ebbinghaus score)
     - Promotion recommendations (Tier 1/2/3)
     - Pattern merge candidates
     - Noise patterns (score < 0.3)
   - Present action-oriented menu using AskUserQuestion (step 4)

   **If "Exit":**
   - Respond: "Done"

4. **Present Action-Oriented Menu** (Step 4 - after Deep Analysis)

   Using AskUserQuestion:
   - Question: "What would you like to do next?"
   - Header: "Next"
   - multiSelect: false
   - Options:
     - Label: "Merge patterns"
       Description: "Consolidate duplicate patterns to reduce noise"
     - Label: "Consider skill creation"
       Description: "Create skills recommended by analysis"
     - Label: "Consider agent creation"
       Description: "Create agents recommended by analysis"
     - Label: "Exit"
       Description: "Close memory dashboard"

5. **Execute Based on Step 4 Selection**

   **If "Merge patterns":**
   - Read pattern_tracker.json and identify merge candidates from analysis
   - For each merge candidate group:
     - Show patterns and co-occurrence count
     - Ask if user wants to merge
   - If yes:
     - Execute:
       ```bash
       export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
       python3 -m as_you.hooks.pattern_merger
       ```
     - Show merge results
   - Return to step 3

   **If "Consider skill creation":**
   - Display Tier 1 promotion recommendations from analysis
   - Show pattern group, combined occurrences, suggested skill name
   - Ask if user wants to proceed with skill creation
   - If yes:
     1. Generate skill content based on analysis:
        - Title: Pattern group name
        - Overview: Combined patterns summary
        - When to Use: Contexts from pattern occurrences
        - Guidelines: Evidence-based best practices
        - Examples: Concrete use cases from pattern history
        - Best Practices: Key recommendations
     2. Write content to temporary file:
        ```bash
        cat > /tmp/skill_content.md <<'EOF'
        # Generated skill content here
        EOF
        ```
     3. Create skill using skill_creator.py:
        ```bash
        export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
        python3 -m as_you.commands.skill_creator \
          "{skill-name}" \
          "{description}" \
          "$(cat /tmp/skill_content.md)" \
          "fork" \
          "Read,Bash,Glob"
        ```
     4. Display result and skill location
     5. Clean up temporary file: `rm /tmp/skill_content.md`
   - If no: Return to step 3

   **If "Consider agent creation":**
   - Display Tier 2 promotion recommendations from analysis
   - Show pattern group, PMI scores, suggested agent name
   - Guide user to create agent file:
     - Agent location: `agents/{agent-name}.md`
     - Include workflow patterns and automation logic
     - Reference promotion recommendations
   - Ask if user wants to proceed:
     - If yes: Guide through agent creation
     - If no: Return to step 3

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
