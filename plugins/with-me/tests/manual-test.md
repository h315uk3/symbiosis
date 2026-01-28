# With Me Plugin - E2E Manual Test

Complete end-to-end test for adaptive requirement elicitation.
Copy and paste commands into Claude Code session to verify functionality.

**Time estimate:** 20-30 minutes for full test

---

## Prerequisites

- Claude Code session running
- Working directory: project with `.claude/` directory
- Clean state recommended (see Cleanup section)

---

**Note:** Commands in `bash` code blocks can be executed by:
1. Copying and asking Claude Code to run them
2. Typing `!` prefix directly in prompt (e.g., `!cat .claude/as_you/session_notes.local.md`)


## /with-me:good-question

### First Time: Permission Setup

**Note:** Only needed on first run

```
/with-me:good-question
```

**Expected:**
- Permission setup runs automatically
- Creates/updates `.claude/settings.local.json`
- Adds 9 required permissions
- Proceeds to session initialization

**Verify:**
```bash
grep -c "with_me" .claude/settings.local.json
```
Should output: `9`

---

### Basic: Initialize and Answer Questions

```
/with-me:good-question
```

**Expected:**
- Simple introduction (no technical jargon)
- First question with 2-4 answer options
- Options include "Skip" and "End session"
- No session IDs or entropy values visible

**Example question:**
```
What problem are you trying to solve?
• Automate a task
• Analyze data
• Build an application
• Other
```

**Action:** Answer naturally based on coherent scenario (e.g., "building a web app")

**Expected for each question:**
- Questions adapt to previous answers
- Clear and relevant
- No duplicates
- Header shows dimension (e.g., "Purpose", "Scale")

**Continue:** Answer 2-3 more questions

---

### Early Termination

On next question, select: "End session (clarity achieved)"

**Expected:**
- Session terminates immediately
- Simple completion message (no JSON)
- Proceeds to requirement analysis

**Verify session file:**
```bash
mise run test:e2e:verify:session
```

Should show: Questions 2-3, Completed True

**Expected session file structure:**
- `session_id` (str): UUID
- `completed` (bool): Termination status
- `question_count` (int): Total questions asked
- `beliefs` (array): Belief state for each dimension
  - `dimension` (str): Dimension name
  - `hypotheses` (array): Hypothesis probabilities
  - `entropy` (float): Current uncertainty
- `question_history` (array): All Q&A pairs
  - `question` (str): Question text
  - `answer` (str): User's answer
  - `dimension` (str): Dimension name
  - `information_gain` (float): IG in bits
- `summary` (dict): Session statistics
  - `total_info_gain` (float): Cumulative IG
  - `final_entropy` (float): Remaining uncertainty

---

### Requirement Analysis

**Expected:**
- LLM reads session file
- Invokes `/with-me:requirement-analysis` skill
- Generates structured specification:
  - Project overview
  - Functional requirements
  - Non-functional requirements
  - Technical considerations

**Note:** Content depends on your answers

---

### Full Session: Complete Convergence

```
/with-me:good-question
```

**Action:** Answer all questions until convergence (8-15 questions typical)

**Expected:**
- Questions adapt throughout
- Progress indicator (optional)
- Convergence detected automatically
- Completion message

**Verify:**
```bash
mise run test:e2e:verify:session
```
Should show: Questions 8-20, Info gain >5 bits, Completed True

---

### Skip Questions

```
/with-me:good-question
```

**Action:** Skip 2-3 questions by selecting "Skip this question"

**Expected:**
- Skipped questions not recorded
- Session continues to next dimension
- May take longer to converge

**Verify:**
```bash
mise run test:e2e:verify:session
```
Check: Question history entries should reflect skipped questions (fewer entries)

---

### Multi-Select Questions

**Action:** Wait for multi-select question (indicated by "Select all that apply")

**Expected:**
- Multiple options can be selected
- All selections processed sequentially
- Beliefs updated for each

---

### Reference Materials

**Action:** When answering, provide URL or file path instead of direct answer

Example: "See requirements at https://example.com/spec.md"

**Expected:**
- LLM uses WebFetch or Read to retrieve content
- Analyzes retrieved information
- Estimates likelihoods from content
- Updates beliefs correctly
- Session continues

---

### Edge Case: Contradictory Answers

**Action:** Provide answers that contradict previous responses

Example:
- Q1: "What type?" → "Web application"
- Q5: "Need server?" → "No, static site only"

**Expected:**
- Detects negative information gain
- Handles gracefully (no crash)
- Beliefs reflect uncertainty
- Session continues

**Verify:**
```bash
mise run test:e2e:verify:session:contradictions
```

---

### Edge Case: Session File Corruption

**Setup:**
```bash
echo "invalid json" > .claude/with_me/sessions/test-session.json
```

**Run:**
```
/with-me:good-question
```

**Expected:**
- Detects corrupted file
- Creates new session (ignores corrupted)
- No crash

**Cleanup:**
```bash
rm .claude/with_me/sessions/test-session.json
```

---

### Edge Case: Very Long Answer

**Action:** When selecting "Other", provide extremely long answer (>1000 words)

**Expected:**
- Answer accepted
- Likelihood estimation handles long text
- No truncation errors
- Session continues

---

### Edge Case: Empty Answer

**Action:** Select "Other" and provide empty text or gibberish

**Expected:**
- Handles gracefully
- May show low information gain
- Session continues

---

### Advanced: Verify Permission Structure

```bash
cat .claude/settings.local.json | jq '.permissions.allow[] | select(. | tostring | contains("with_me"))'
```

**Expected:** 9 permission entries:
1. PYTHONPATH environment variable
2-7. CLI commands (init, next-question, evaluate-question, update-with-computation, status, complete)
8. Skill (with-me:requirement-analysis)
9. Read (session data)

---

### Advanced: Direct CLI Test

**Test init:**
```bash
mise run test:e2e:cli:with-me:init
```

**Expected:** JSON output with `session_id` and `status: initialized`

**Test next-question:**
```bash
SESSION_ID=<SESSION_ID> mise run test:e2e:cli:with-me:next-question
```

**Expected:** JSON with dimension info and hypotheses

**Note:** Replace `<SESSION_ID>` with the actual session ID from init output

---

## Cleanup

After testing:

```bash
# Remove test sessions
rm -rf .claude/with_me/sessions/
```

**Optional: Remove permissions (if needed)**
```bash
# Edit .claude/settings.local.json manually to remove with_me entries
```

---

## Troubleshooting

### Permission Setup Fails

**Check:**
```bash
cat .claude/settings.local.json | jq .
```

If invalid JSON, recreate:
```bash
echo '{"permissions": {"allow": []}}' > .claude/settings.local.json
```

Then run `/with-me:good-question` again

---

### Session File Not Found

**Create directory:**
```bash
mkdir -p .claude/with_me/sessions
```

---

## Test Completion Checklist

- [ ] First-time permission setup
- [ ] Initialize session and answer questions
- [ ] Early termination
- [ ] Requirement analysis generation
- [ ] Full session to convergence
- [ ] Skip questions
- [ ] Multi-select questions (if applicable)
- [ ] Reference materials (if applicable)
- [ ] Edge case: contradictory answers
- [ ] Edge case: corrupted session file
- [ ] Edge case: very long answer
- [ ] Edge case: empty answer
- [ ] Permission structure verification
- [ ] Direct CLI test (advanced)
- [ ] All cleanup completed

**Total test scenarios:** 14+
**Coverage:** All command flows, all scenarios, all edge cases
