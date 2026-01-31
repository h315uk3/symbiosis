# As You Plugin - E2E Manual Test

Complete end-to-end test covering all commands, scenarios, and edge cases.
Copy and paste commands into Claude Code session to verify functionality.

**Time estimate:** 30-45 minutes for full test

---

## Prerequisites

- Claude Code session running
- Working directory: project with `.claude/` directory
- Clean state recommended (see Cleanup section)

---

**Note:** Commands in `bash` code blocks can be executed by:
1. Copying and asking Claude Code to run them
2. Typing `!` prefix directly in prompt (e.g., `!cat .claude/as_you/session_notes.local.md`)


## /as-you:learn

### Basic: Add Note (English)

```
/as-you:learn "Always use pathlib instead of os.path for file operations"
```

**Expected:** "Note added"

**Verify:**
```bash
cat .claude/as_you/session_notes.local.md
```
Should contain: note text with `[HH:MM]` timestamp

---

### Translation: Add Note (Japanese)

```
/as-you:learn "React hooksを使うとボイラープレートが減る"
```

**Expected:** Note automatically translated to English, "Note added"

**Verify:**
```bash
cat .claude/as_you/session_notes.local.md
```
Should contain: translated English note with "React hooks" preserved

---

### Edge Case: Empty Input

```
/as-you:learn ""
```

**Expected:** Error message or clarification request, no empty note added

---

### Edge Case: Long Note

```
/as-you:learn "This is a very long note that contains detailed information about a complex pattern we discovered during development including specific code examples function names file paths and extensive reasoning about why this approach was chosen and what alternatives were considered and rejected along with performance benchmarks and security considerations that influenced our final decision making process"
```

**Expected:** Note accepted and stored without truncation

---

### Edge Case: Special Characters

```
/as-you:learn "Use \`backticks\` for code, \"quotes\" for strings, and $variables carefully"
```

**Expected:** Special characters preserved correctly

**Verify:**
```bash
cat .claude/as_you/session_notes.local.md | tail -5
```
Should show: special characters intact

---

### Dashboard: Open

```
/as-you:learn
```

**Expected:**
- Displays session notes with count
- Learning summary (notes/patterns/candidates)
- 5 menu options: Add/View/Analyze/Clear/Exit

**Action:** Select "Exit"

---

### Dashboard: Add Another Note

```
/as-you:learn
```

Select: "Add another note"
Enter: "JWT tokens should expire after 1 hour for security"

**Expected:** Note added, menu returns

**Verify:**
```bash
cat .claude/as_you/session_notes.local.md | grep -c "JWT"
```
Should output: `1`

---

### Dashboard: View Note History

```
/as-you:learn
```

Select: "View note history"

**Expected:**
- Shows archived notes (if exist)
- Up to 7 most recent archives
- Date headers (YYYY-MM-DD)
- Returns to menu

**Verify:**
```bash
ls -la .claude/as_you/session_archive/
```

---

### Dashboard: Analyze Patterns

```
/as-you:learn
```

Select: "Analyze patterns"

**Expected:**
- Displays promotion candidates with scores
- Message about `/as-you:patterns` for details
- Returns to menu

---

### Dashboard: Clear Notes

```
/as-you:learn
```

Select: "Clear current notes" → "Yes, clear them"

**Expected:** "Session notes cleared", returns to menu

**Verify:**
```bash
cat .claude/as_you/session_notes.local.md
```
Should be empty

Select: "Exit"

---

## /as-you:active

### Basic: Check Status

```
/as-you:active
```

**Expected:** Shows ON/OFF status, statistics

**Verify:**
```bash
test -f .claude/as_you/active_learning.enabled && echo "Should be disabled: FAIL" || echo "Disabled: OK"
```

---

### Basic: Enable

```
/as-you:active on
```

**Expected:** "Active learning enabled"

**Verify:**
```bash
test -f .claude/as_you/active_learning.enabled && echo "Enabled: OK" || echo "Enabled: FAIL"
```
Should output: `Enabled: OK`

---

### Basic: Check Status After Enable

```
/as-you:active status
```

**Expected:** Shows "ON" or "Enabled" with statistics

---

### Capture: Test Prompt Capture

After enabling, submit test prompts:
```
Create a simple hello world function
```
```
Add error handling to the function
```

**Expected:** Prompts captured silently (no visible indication)

**Verify:**
```bash
mise run test:e2e:verify:active
```

---

### Basic: Disable

```
/as-you:active off
```

**Expected:** "Active learning disabled", data preserved

**Verify:**
```bash
test ! -f .claude/as_you/active_learning.enabled && echo "Disabled: OK" || echo "Disabled: FAIL"
mise run test:e2e:verify:active
```

---

### Edge Case: Toggle Multiple Times

```
/as-you:active on
/as-you:active off
/as-you:active on
/as-you:active status
```

**Expected:** Each command succeeds, final status shows ON

---

### Edge Case: Invalid Argument

```
/as-you:active invalid-arg
```

**Expected:** Error message or defaults to status, suggests valid options

---

### Privacy: Verify Data Location

```bash
ls -la .claude/as_you/active_learning.json
cat .claude/as_you/active_learning.json | jq .
```

**Expected:** File in project-local `.claude/as_you/`, valid JSON, no external URLs

---

## /as-you:workflows

### Basic: Save Workflow

**Note:** Requires work history (previous tests provide enough)

```
/as-you:workflows "test-workflow"
```

**Expected:**
- Asks abstraction level (Specific/Generic)
- Asks scope (Last 5/10/20 actions)
- Shows workflow preview
- Asks confirmation

**Action:** Answer questions, confirm save

**Verify:**
```bash
ls .claude/commands/test-workflow.md
WORKFLOW_FILE=.claude/commands/test-workflow.md mise run test:e2e:verify:workflow
```

Should contain YAML frontmatter with:
- `description:` (text describing the workflow)
- `created:` (ISO 8601 timestamp)
- `usage_count: 0` (initially zero)
- `last_used: null` (initially null)

Should contain markdown sections:
- `# [Workflow Name]` (heading)
- `## Steps` (numbered steps section)
- Code blocks with commands/examples
- `## Context` or `## Notes` sections

---

### Edge Case: Duplicate Workflow Name

```
/as-you:workflows "test-workflow"
```

**Expected:** Detects duplicate, asks to overwrite or rename

---

### Dashboard: Open

```
/as-you:workflows
```

**Expected:**
- Shows pattern context
- Lists workflows with metadata
- 6 menu options: View/Execute/Get pattern context/List all/Save new/Exit

**Action:** Select "Exit"

---

### Dashboard: View Workflow

```
/as-you:workflows
```

Select: "View workflow" → Choose "test-workflow" → "No"

**Expected:** Displays full workflow, usage stats, returns to menu

---

### Dashboard: Execute Workflow

```
/as-you:workflows
```

Select: "Execute workflow" → Choose workflow → "Execute"

**Expected:** Runs steps, updates metadata, shows results

**Verify:**
```bash
WORKFLOW_FILE=.claude/commands/test-workflow.md mise run test:e2e:verify:workflow
```
Should show: usage_count incremented, last_used updated

---

### Dashboard: Get Pattern Context

```
/as-you:workflows
```

Select: "Get pattern context"
Enter: "Building a REST API with authentication"

**Expected:**
- Displays relevant patterns with scores
- Thompson Sampling recommendations
- Returns to menu

---

### Dashboard: List All Workflows

```
/as-you:workflows
```

Select: "List all workflows"

**Expected:** All workflows with metadata, sorted by usage count

---

### Dashboard: Save New Workflow

```
/as-you:workflows
```

Select: "Save new workflow"

**Expected:**
- Prompts for workflow name
- Enter: "dashboard-created-workflow"
- Continues with same flow as Mode 1 (abstraction level, scope)
- Generates workflow preview
- Asks confirmation

**Action:** Confirm save

**Verify:**
```bash
ls .claude/commands/dashboard-created-workflow.md
WORKFLOW_FILE=.claude/commands/dashboard-created-workflow.md mise run test:e2e:verify:workflow
```

Should contain: YAML frontmatter with all required fields, markdown structure

**Expected after save:** Returns to main dashboard menu

---

### Edge Case: No Recent Work

Start fresh session:
```
/as-you:workflows "empty-workflow"
```

**Expected:** Detects insufficient history, suggests adding work first

---

### Edge Case: No Workflows

```bash
rm -rf .claude/commands/*.md
```

```
/as-you:workflows
```

**Expected:** Shows "No workflows available", menu still offers "Save new workflow"

---

## /as-you:patterns

### Dashboard: Open

```
/as-you:patterns
```

**Expected:**
- Memory Dashboard with sections:
  - Current Session
  - Pattern Analysis
  - Habit Extraction
  - Confidence Tracking
  - Knowledge Base
  - Memory Review (SM-2)
- 4 menu options: Analyze edits/View top/Review candidates/Review quality

**Action:** Select appropriate option or Exit

---

### Analyze Active Edits

From menu, select: "Analyze active edits"

**Expected:**
- Analyzes recent file edits
- Extracts semantic patterns
- Updates pattern_tracker.json with new patterns
- Shows analysis summary

**Verify pattern tracker updated:**
```bash
mise run test:e2e:verify:patterns
```

**Expected fields in pattern_tracker.json:**
- `patterns` (dict): Pattern text as keys, metadata as values
  - `count` (int): Occurrence count
  - `last_seen` (str): ISO date
  - `composite_score` (float): Combined score from all metrics
  - `bm25_score` (float): BM25 relevance score
  - `ebbinghaus_retention` (float): Memory retention factor
  - `shannon_entropy` (float): Information content
  - `sm2_state` (dict, optional): Spaced repetition state
    - `easiness_factor` (float)
    - `interval` (int)
    - `repetitions` (int)
    - `last_review` (str)
    - `next_review` (str)

---

### View Top Patterns

From menu, select: "View top patterns"

**Expected:** Top 10 patterns with scores, sorted by composite score

---

### Review Promotion Candidates

From menu, select: "Review promotion candidates"

**Expected:** Candidates with scores, suggested categories

---

### Verify Pattern Tracker Structure

**Check detailed structure:**
```bash
mise run test:e2e:verify:patterns
```

**Expected:**
- All patterns have `count`, `last_seen`, `composite_score`
- Optional fields: `bm25_score`, `ebbinghaus_retention`, `shannon_entropy`, `sm2_state`
- SM-2 state (if present): `easiness_factor`, `interval`, `repetitions`, `last_review`, `next_review`

---

### SM-2 Review Setup (Advanced)

Create test pattern with review due:

```bash
mise run test:e2e:setup:sm2-pattern
```

---

### SM-2 Review Execute

```
/as-you:patterns
```

Select: "Review pattern quality"

**Expected:** Shows patterns due for review

**For each pattern:**
- Shows context and current state
- Presents quality ratings (0-5)

**Test:** Select "4 - Good"

**Expected:** Updates SM-2 state, increases interval

**Verify:**
```bash
mise run test:e2e:verify:sm2-review
```

---

### Edge Case: No Patterns

```bash
rm .claude/as_you/pattern_tracker.json
```

```
/as-you:patterns
```

**Expected:** Shows zero patterns, no errors, menu handles empty state

---

## /as-you:help

### Basic: Display Help

```
/as-you:help
```

**Expected:**
- Plugin information
- All 5 commands listed with syntax
- Data location (`.claude/as_you/`)
- Privacy statement
- Well-formatted output

---

### Edge Case: Help with Arguments

```
/as-you:help some-argument
```

**Expected:** Arguments ignored, standard help displayed

---

## Cleanup

After testing:

```bash
# Remove test files
rm -f .claude/as_you/session_notes.local.md
rm -f .claude/as_you/active_learning.enabled
rm -f .claude/as_you/active_learning.json
rm -rf .claude/commands/
```

**Optional: Full reset (loses all patterns)**
```bash
# rm -rf .claude/as_you/
```

---

## Test Completion Checklist

- [ ] /as-you:learn - Basic notes (English/Japanese)
- [ ] /as-you:learn - Dashboard all menus
- [ ] /as-you:learn - Edge cases
- [ ] /as-you:active - Enable/disable/status
- [ ] /as-you:active - Capture verification
- [ ] /as-you:active - Edge cases
- [ ] /as-you:workflows - Save workflow
- [ ] /as-you:workflows - Dashboard all menus
- [ ] /as-you:workflows - Edge cases
- [ ] /as-you:patterns - Dashboard
- [ ] /as-you:patterns - Top patterns
- [ ] /as-you:patterns - SM-2 review
- [ ] /as-you:help - Display
- [ ] All cleanup completed

**Total commands tested:** ~50+
**Coverage:** All commands, all scenarios, all edge cases
