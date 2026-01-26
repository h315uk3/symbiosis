# Test Scenario: /as-you:memory Command

Test the memory analysis dashboard: pattern exploration, confidence tracking, and knowledge management.

## Scenario 1: Memory Dashboard Overview

### Prerequisites
- [ ] Multiple patterns exist in pattern_tracker.json (add notes via `/as-you:learn` if needed)
- [ ] Patterns have varying scores and confidence levels
- [ ] Some patterns used multiple times, others only once

### Test Steps

#### Step 1.1: Open Memory Dashboard
```
/as-you:memory
```

**Expected behavior:**
- [ ] Executes analysis_orchestrator and memory_stats
- [ ] Displays Memory Dashboard with sections:
  - **Current Session**: Notes count, Archives count
  - **Pattern Analysis**: Detected patterns, BM25 scores, Ebbinghaus scores, Shannon Entropy scores, Composite scores, Promotion candidates
  - **Habit Extraction**: Indexed notes, Habit clusters
  - **Confidence Tracking**: High/Medium/Low confidence pattern counts
  - **Knowledge Base**: Skills count, Agents count, Memory (SM-2) tracked patterns
- [ ] Presents AskUserQuestion menu with 7 options:
  - "View top patterns"
  - "Analyze confidence"
  - "Review promotion candidates"
  - "Detect similar patterns"
  - "Memory review (SM-2)"
  - "Deep analysis"
  - "Exit"

**Verification:**
```bash
cat .claude/as_you/pattern_tracker.json | python3 -m json.tool | head -50
```
Check that pattern_tracker.json exists and contains patterns with scores.

---

## Scenario 2: View Top Patterns

### Test Steps

#### Step 2.1: View Highest-Scoring Patterns
From dashboard menu, select "View top patterns".

**Expected behavior:**
- [ ] Reads pattern_tracker.json
- [ ] Sorts patterns by composite_score (descending)
- [ ] Displays top 10 patterns with:
  - Pattern text
  - Composite score (0.0-1.0)
  - BM25 score (distinctiveness)
  - Ebbinghaus score (memory strength)
  - Shannon Entropy score (diversity)
  - Count (frequency)
  - Last seen date (ISO 8601)
- [ ] Returns to main menu

**Verification:**
- [ ] Patterns are ranked correctly by composite score
- [ ] All scores are in valid ranges (0.0-1.0)
- [ ] Dates are formatted correctly

---

## Scenario 3: Analyze Confidence

### Test Steps

#### Step 3.1: Review Bayesian Confidence
From dashboard menu, select "Analyze confidence".

**Expected behavior:**
- [ ] Reads pattern_tracker.json
- [ ] For patterns with Bayesian state (alpha, beta):
  - Calculates confidence score (mean of Beta distribution)
  - Shows mean, variance, std_dev
  - Shows 95% confidence interval
- [ ] Groups patterns by confidence level:
  - **High**: mean > 0.7
  - **Medium**: 0.4 ≤ mean ≤ 0.7
  - **Low**: mean < 0.4
- [ ] Displays summary with example patterns from each group
- [ ] Returns to main menu

**Verification:**
- [ ] Confidence groupings are correct
- [ ] Variance indicates uncertainty appropriately
- [ ] Confidence intervals are reasonable

---

## Scenario 4: Review Promotion Candidates

### Test Steps

#### Step 4.1: Identify Patterns Ready for Promotion
From dashboard menu, select "Review promotion candidates".

**Expected behavior:**
- [ ] Executes promotion_analyzer command
- [ ] Displays candidates sorted by composite score
- [ ] For each candidate shows:
  - Pattern text
  - Composite score
  - Confidence (Bayesian mean)
  - Frequency count
  - Suggested category (skill/agent)
- [ ] Shows message: "High scores + high confidence = ready for promotion"
- [ ] Asks if user wants to promote

Select "No":
- [ ] Returns to main menu

Select "Yes":
- [ ] Guides to using appropriate promotion command
- [ ] Returns to main menu

**Verification:**
```bash
cat .claude/as_you/pattern_tracker.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
candidates = [p for p in data.get('patterns', []) if p.get('composite_score', 0) > 0.7]
print(f'Candidates with score > 0.7: {len(candidates)}')
"
```

---

## Scenario 5: Detect Similar Patterns

### Prerequisites
- [ ] Patterns with similar text exist (e.g., "Use pathlib" and "Use pathlib for files")

### Test Steps

#### Step 5.1: Find Similar Patterns
From dashboard menu, select "Detect similar patterns".

**Expected behavior:**
- [ ] Executes similarity_detector command
- [ ] Displays similar pattern pairs with:
  - Levenshtein distance (edit distance)
  - BK-tree detection results
  - Similarity score
- [ ] If similar pairs found, asks if user wants to merge

Select "Yes" (if duplicates exist):
- [ ] Executes pattern_merger command
- [ ] Merges similar patterns
- [ ] Shows merge results (combined pattern, summed counts)
- [ ] Returns to main menu

Select "No":
- [ ] Returns to main menu

**Verification:**
After merge, check pattern_tracker.json:
```bash
cat .claude/as_you/pattern_tracker.json | python3 -m json.tool
```
Verify that duplicate patterns have been consolidated.

---

## Scenario 6: Memory Review (SM-2)

### Prerequisites
- [ ] Patterns with SM-2 state (easiness_factor, interval, repetitions, next_review)
- [ ] Some patterns overdue for review (adjust dates if needed for testing)

### Test Steps

#### Step 6.1: Check Spaced Repetition Schedule
From dashboard menu, select "Memory review (SM-2)".

**Expected behavior:**
- [ ] Reads pattern_tracker.json
- [ ] For patterns with SM-2 state:
  - Calculates if review is due (interval elapsed since last_review)
  - Orders patterns by:
    1. Overdue (days past due)
    2. Due today
    3. Due soon (next 7 days)
- [ ] For each pattern shows:
  - Pattern text
  - Easiness factor (2.5 = default)
  - Current interval (days)
  - Repetitions count
  - Next review date
- [ ] Explains: "Review helps strengthen memory. Patterns you use successfully get longer intervals."
- [ ] Returns to main menu

**Verification:**
- [ ] Patterns are sorted correctly by due date
- [ ] Easiness factors are reasonable (1.3 to 2.5+)
- [ ] Intervals increase with repetitions

---

## Scenario 7: Deep Analysis with Agent

### Prerequisites
- [ ] Sufficient patterns for meaningful analysis (10+ patterns recommended)
- [ ] Patterns with varying scores, confidence, and characteristics

### Test Steps

#### Step 7.1: Launch Memory Analyzer Agent
From dashboard menu, select "Deep analysis".

**Expected behavior:**
- [ ] Launches memory-analyzer agent via Task tool
- [ ] Agent analyzes pattern_tracker.json using v0.3.0 scoring
- [ ] Agent provides insights on:
  1. High-value patterns (composite score > 0.7)
  2. Patterns with high uncertainty (Bayesian variance > 0.1)
  3. General-purpose vs specialized patterns (Shannon Entropy)
  4. Patterns with strong memory (Ebbinghaus score)
  5. Promotion recommendations with reasoning (Tier 1/2/3)
  6. Potential pattern merges
- [ ] LLM summarizes agent output focusing on actionable insights
- [ ] Presents action-oriented menu with 4 options:
  - "Merge patterns"
  - "Consider skill creation"
  - "Consider agent creation"
  - "Exit"

#### Step 7.2: Merge Patterns (from action menu)
Select "Merge patterns".

**Expected behavior:**
- [ ] Identifies merge candidates from analysis
- [ ] For each group:
  - Shows patterns and co-occurrence count
  - Asks if user wants to merge
- [ ] If yes: Executes pattern_merger, shows results
- [ ] Returns to main menu (Step 1.1)

#### Step 7.3: Consider Skill Creation (from action menu)
Select "Consider skill creation".

**Expected behavior:**
- [ ] Displays Tier 1 promotion recommendations
- [ ] Shows: pattern group, combined occurrences, suggested skill name
- [ ] Asks if user wants to proceed

Select "Yes":
- [ ] Generates skill content based on patterns:
  - Title, Overview, When to Use, Guidelines, Examples, Best Practices
- [ ] Writes content to temporary file
- [ ] Executes skill_creator command
- [ ] Displays result and skill location
- [ ] Cleans up temporary file
- [ ] Returns to main menu

Select "No":
- [ ] Returns to main menu

**Verification:**
If skill created, check:
```bash
ls -la skills/
cat skills/{skill-name}.md
```

#### Step 7.4: Consider Agent Creation (from action menu)
Select "Consider agent creation".

**Expected behavior:**
- [ ] Displays Tier 2 promotion recommendations
- [ ] Shows: pattern group, PMI scores, suggested agent name
- [ ] Guides user through agent creation
- [ ] Asks if user wants to proceed

Select "Yes":
- [ ] Provides guidance for creating agent file
- [ ] References promotion recommendations
- [ ] Returns to main menu

Select "No":
- [ ] Returns to main menu

#### Step 7.5: Exit (from action menu)
Select "Exit".

**Expected behavior:**
- [ ] Response: "Done"
- [ ] Closes dashboard

---

## Scenario 8: Score Interpretation

### Prerequisites
- [ ] Patterns with diverse characteristics in pattern_tracker.json

### Test Steps

#### Step 8.1: Verify Score Meanings
Review top patterns and verify scoring makes sense:

**BM25 Score:**
- [ ] Patterns with rare, specific terms have higher BM25 scores
- [ ] Patterns with common terms have lower BM25 scores

**Ebbinghaus Score:**
- [ ] Frequently repeated patterns have higher scores
- [ ] Recent patterns have higher scores than old ones
- [ ] Score decays over time without repetition

**Shannon Entropy Score:**
- [ ] General-purpose patterns (many contexts) have high entropy (>0.7)
- [ ] Specialized patterns (specific contexts) have low entropy (<0.3)

**Composite Score:**
- [ ] Weighted combination reflects overall importance
- [ ] High composite score = valuable pattern to keep

**Bayesian Confidence:**
- [ ] Mean represents expected quality
- [ ] Variance shows uncertainty (new patterns have high variance)
- [ ] Confidence interval narrows with more observations

---

## Edge Cases

### EC1: No Patterns Exist
Delete pattern_tracker.json:
```bash
rm .claude/as_you/pattern_tracker.json
```

Run:
```
/as-you:memory
```

**Expected behavior:**
- [ ] Dashboard shows zero patterns
- [ ] No errors occur
- [ ] Menu options handle empty state gracefully

### EC2: Corrupted Pattern Data
Manually corrupt pattern_tracker.json (invalid JSON).

Run:
```
/as-you:memory
```

**Expected behavior:**
- [ ] Detects corrupted file
- [ ] Shows appropriate error message
- [ ] Offers to reset or fix

### EC3: Patterns with Missing Scores
Manually remove some score fields from patterns.

**Expected behavior:**
- [ ] Handles missing fields gracefully
- [ ] Uses default values or recalculates
- [ ] No crashes

---

## Cleanup

```bash
# Backup before cleanup (optional)
cp .claude/as_you/pattern_tracker.json /tmp/pattern_tracker_backup.json

# Reset pattern tracker (caution: loses all patterns)
# rm .claude/as_you/pattern_tracker.json
```

---

## Related Tests

- [learn.md](./learn.md) - Creating patterns to analyze
- [apply.md](./apply.md) - Using analyzed patterns
- [hooks/pattern_capture.md](../hooks/pattern_capture.md) - How patterns are captured
