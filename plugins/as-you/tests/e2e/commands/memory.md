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
  - **Knowledge Base**: Skills count, Agents count
  - **Memory Review (SM-2)**: Tracked patterns, Overdue for review, Due today, Due soon (7 days)
- [ ] Presents AskUserQuestion menu with 4 options:
  - "Analyze active edits"
  - "View top patterns"
  - "Review promotion candidates"
  - "Review due patterns"

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

## Scenario 6: SM-2 Spaced Repetition Review

### Prerequisites
- [ ] Create test patterns with SM-2 state (some overdue for testing)

#### Setup Test Data
```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -c "
import json
from datetime import datetime, timedelta
from pathlib import Path

tracker_file = Path('.claude/as_you/pattern_tracker.json')
tracker = json.loads(tracker_file.read_text()) if tracker_file.exists() else {}

# Ensure patterns dict exists
if 'patterns' not in tracker:
    tracker['patterns'] = {}

# Add test patterns with SM-2 state
test_patterns = {
    'Use pathlib for file operations': {
        'count': 5,
        'last_seen': (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),
        'composite_score': 0.75,
        'sm2_state': {
            'easiness_factor': 2.5,
            'interval': 6,
            'repetitions': 2,
            'last_review': (datetime.now() - timedelta(days=8)).strftime('%Y-%m-%d'),
            'next_review': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')  # Overdue by 2 days
        }
    },
    'Use type hints for function parameters': {
        'count': 3,
        'last_seen': datetime.now().strftime('%Y-%m-%d'),
        'composite_score': 0.65,
        'sm2_state': {
            'easiness_factor': 2.2,
            'interval': 1,
            'repetitions': 1,
            'last_review': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
            'next_review': datetime.now().strftime('%Y-%m-%d')  # Due today
        }
    }
}

tracker['patterns'].update(test_patterns)
tracker_file.write_text(json.dumps(tracker, indent=2))
print('Test patterns created')
"
```

### Test Steps

#### Step 6.1: Access Review Menu
From dashboard menu, select "Review due patterns".

**Expected behavior:**
- [ ] Checks if pattern_tracker.json exists
- [ ] Finds patterns due for review
- [ ] Displays count and list of due patterns with days overdue

**Verification:**
```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m as_you.commands.pattern_review find-due
```

#### Step 6.2: Review First Pattern
**Expected behavior:**
- [ ] Displays SM-2 explanation (quality ratings 0-5)
- [ ] Shows first pattern context:
  - Pattern text
  - Usage count
  - Last seen date
  - Current state (interval, repetitions, easiness factor)
- [ ] Presents quality rating options via AskUserQuestion

**Select:** "4 - Good" (good quality assessment)

**Expected behavior:**
- [ ] Applies feedback with quality=4
- [ ] Updates SM-2 state:
  - Increases easiness factor
  - Increases interval (previous × EF)
  - Increments repetitions
  - Sets new next_review date
- [ ] Displays result: "✓ Good quality assessment! Next review in X days (EF: X.XX)"

**Verification:**
```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m as_you.commands.pattern_review verify-pattern "Use pathlib for file operations"
```
- [ ] Interval increased (should be > 6 days)
- [ ] Repetitions = 3
- [ ] Easiness factor increased slightly

#### Step 6.3: Review Second Pattern with Low Quality
**Select:** "2 - Poor" (low quality assessment)

**Expected behavior:**
- [ ] Applies feedback with quality=2
- [ ] Updates SM-2 state:
  - Decreases easiness factor
  - **Resets interval to 1** (low quality assessment)
  - **Resets repetitions to 0**
  - Sets next_review to tomorrow
- [ ] Displays result: "○ Needs more practice. Interval reset to 1 day for reinforcement."

**Verification:**
```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m as_you.commands.pattern_review verify-pattern "Use type hints for function parameters"
```
- [ ] Interval = 1 day
- [ ] Repetitions = 0
- [ ] Easiness factor decreased

#### Step 6.4: Complete Review Session
**Expected behavior:**
- [ ] After reviewing all due patterns, displays summary:
  - Reviewed: X patterns
  - Successful (≥3): X
  - Need practice (<3): X
  - Next due: Today X, Soon X
- [ ] Returns to main menu

**Verification:**
```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m as_you.commands.pattern_review summary
```

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

## Scenario 9: SM-2 Edge Cases

### Test Case 9.1: No Patterns Due

#### Setup
```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -c "
import json
from datetime import datetime, timedelta
from pathlib import Path

tracker_file = Path('.claude/as_you/pattern_tracker.json')
tracker = json.loads(tracker_file.read_text()) if tracker_file.exists() else {}

if 'patterns' not in tracker:
    tracker['patterns'] = {}

# Add pattern not due yet
tracker['patterns']['Future pattern'] = {
    'count': 3,
    'last_seen': datetime.now().strftime('%Y-%m-%d'),
    'composite_score': 0.6,
    'sm2_state': {
        'easiness_factor': 2.5,
        'interval': 7,
        'repetitions': 2,
        'last_review': datetime.now().strftime('%Y-%m-%d'),
        'next_review': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    }
}

tracker_file.write_text(json.dumps(tracker, indent=2))
print('Future pattern created')
"
```

#### Test Steps
From dashboard menu, select "Review due patterns".

**Expected behavior:**
- [ ] Finds no patterns due for review
- [ ] Displays message: "No patterns due for review yet."
- [ ] Shows next 5 upcoming reviews with dates
- [ ] Returns to main menu

**Verification:**
```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -c "
from datetime import datetime
from pathlib import Path
from as_you.commands.pattern_review import find_due_patterns

due = find_due_patterns(Path('.claude/as_you/pattern_tracker.json'), datetime.now())
print(f'Due patterns: {len(due)} (should be 0)')
"
```

---

### Test Case 9.2: Invalid Quality Rating

#### Setup
Use test patterns from Scenario 6.

#### Test Steps
From review workflow, attempt to provide invalid quality rating.

**Expected behavior:**
- [ ] Quality ratings are constrained by AskUserQuestion options (0-5)
- [ ] If invalid quality somehow provided, apply_quality_feedback returns error
- [ ] Error message: "Quality must be 0-5, got X"

**Verification:**
```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -c "
from pathlib import Path
from as_you.commands.pattern_review import apply_quality_feedback

# Try invalid quality
result = apply_quality_feedback(
    Path('.claude/as_you/pattern_tracker.json'),
    'Use pathlib for file operations',
    10
)

print(f'Success: {result[\"success\"]} (should be False)')
print(f'Error: {result.get(\"error\", \"\")}')
"
```
- [ ] Success = False
- [ ] Error contains "Quality must be 0-5"

---

### Test Case 9.3: Pattern Not Found

#### Test Steps
Attempt to apply feedback to non-existent pattern.

**Expected behavior:**
- [ ] Returns error: "Pattern not found"

**Verification:**
```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -c "
from pathlib import Path
from as_you.commands.pattern_review import apply_quality_feedback

result = apply_quality_feedback(
    Path('.claude/as_you/pattern_tracker.json'),
    'Non-existent pattern',
    4
)

print(f'Success: {result[\"success\"]} (should be False)')
print(f'Error: {result.get(\"error\", \"\")}')
"
```
- [ ] Success = False
- [ ] Error = "Pattern not found"

---

### Test Case 9.4: Tracker Not Initialized

#### Setup
Temporarily move pattern_tracker.json.

```bash
mv .claude/as_you/pattern_tracker.json .claude/as_you/pattern_tracker.json.backup
```

#### Test Steps
From dashboard menu, select "Review due patterns".

**Expected behavior:**
- [ ] Checks if pattern_tracker.json exists
- [ ] Displays message: "Pattern tracker not initialized."
- [ ] Shows setup instructions (enable active learning, work, exit session)
- [ ] Returns to main menu

#### Cleanup
```bash
mv .claude/as_you/pattern_tracker.json.backup .claude/as_you/pattern_tracker.json
```

---

### Test Case 9.5: All Quality Levels (0-5)

#### Setup
Use test pattern from Scenario 6.

#### Test Steps
Test each quality level:

**Quality 5 (Perfect):**
- [ ] Easiness factor increases most
- [ ] Interval increases (previous × new EF)
- [ ] Repetitions increments

**Quality 4 (Good):**
- [ ] Easiness factor increases
- [ ] Interval increases
- [ ] Repetitions increments

**Quality 3 (Adequate - minimum pass):**
- [ ] Easiness factor decreases slightly
- [ ] Interval still increases (EF ≥ 1.3)
- [ ] Repetitions increments

**Quality 2 (Poor):**
- [ ] Easiness factor decreases
- [ ] **Interval resets to 1**
- [ ] **Repetitions resets to 0**

**Quality 1 (Very poor):**
- [ ] Similar to quality 2
- [ ] Interval = 1
- [ ] Repetitions = 0

**Quality 0 (No usefulness):**
- [ ] Easiness factor decreases most
- [ ] Interval = 1
- [ ] Repetitions = 0

**Verification:**
```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -c "
from pathlib import Path
from as_you.commands.pattern_review import apply_quality_feedback

# Test quality 3 (pass threshold)
result = apply_quality_feedback(
    Path('.claude/as_you/pattern_tracker.json'),
    'Use pathlib for file operations',
    3
)

print(f'Quality 3 (pass):')
print(f'  Interval: {result[\"new_interval\"]} (should be > 1)')
print(f'  Repetitions: {result[\"new_repetitions\"]} (should increment)')

# Test quality 2 (fail threshold)
result2 = apply_quality_feedback(
    Path('.claude/as_you/pattern_tracker.json'),
    'Use type hints for function parameters',
    2
)

print(f'Quality 2 (fail):')
print(f'  Interval: {result2[\"new_interval\"]} (should be 1)')
print(f'  Repetitions: {result2[\"new_repetitions\"]} (should be 0)')
"
```

---

## Related Tests

- [learn.md](./learn.md) - Creating patterns to analyze
- [apply.md](./apply.md) - Using analyzed patterns
- [hooks/pattern_capture.md](../hooks/pattern_capture.md) - How patterns are captured
