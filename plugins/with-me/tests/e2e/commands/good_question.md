# Test Scenario: /with-me:good-question Command

Test the adaptive requirement elicitation command through complete questioning sessions.

## Scenario 1: First-Time Setup

### Prerequisites
- [ ] Fresh Claude Code session
- [ ] with-me plugin installed
- [ ] No previous permissions configured

### Test Steps

#### Step 1.1: Run Setup (First Time)
```
/with-me:good-question
```

**Expected behavior:**
- [ ] LLM detects missing permissions
- [ ] Executes setup_permissions.py script automatically
- [ ] Creates `.claude/settings.local.json` if not exists
- [ ] Adds 9 required permissions
- [ ] Reports setup status
- [ ] Proceeds to session initialization

**Verification:**
```bash
cat .claude/settings.local.json | python3 -m json.tool | grep -A2 "allowedPrompts"
```

Expected:
- [ ] File exists
- [ ] Contains with_me permission entries
- [ ] Total permissions: 9 (1 PYTHONPATH + 6 CLI + 1 Skill + 1 Read)

---

## Scenario 2: Basic Question Session

### Prerequisites
- [ ] Permissions configured (run Scenario 1 first)
- [ ] Fresh session (no previous with-me sessions)

### Test Steps

#### Step 2.1: Initialize Session
```
/with-me:good-question
```

**Expected behavior:**
- [ ] LLM initializes session silently (no technical details shown)
- [ ] User-facing message: Simple introduction
  - Example: "Let's clarify your requirements. I'll ask a series of questions to understand what you need."
- [ ] No session IDs, entropy values, or technical terms visible
- [ ] Proceeds directly to first question

**What user should NOT see:**
- [ ] Session ID
- [ ] "Initializing session..."
- [ ] JSON outputs
- [ ] Dimension names or entropy values

#### Step 2.2: First Question
**Expected behavior:**
- [ ] Question is clear and relevant
- [ ] AskUserQuestion tool invoked with:
  - Natural question text
  - 2-4 answer options
  - "Skip this question" option
  - "End session (clarity achieved)" option
  - Header with dimension name (e.g., "Purpose", "Scale")
- [ ] No evaluation scores visible
- [ ] No technical terminology

**Example good question:**
```
What problem are you trying to solve with this software?

Options:
• Automate a repetitive task
• Analyze or visualize data
• Build a user-facing application
• Other
```

**Answer** one of the options (e.g., "Build a user-facing application").

**Expected behavior:**
- [ ] Answer accepted without error
- [ ] Belief update happens silently
- [ ] Next question appears

#### Step 2.3: Subsequent Questions
Continue answering questions (answer naturally based on a coherent scenario).

**Expected behavior:**
- [ ] Questions adapt based on previous answers
- [ ] No duplicate questions
- [ ] Questions become more specific as session progresses
- [ ] Optional progress indicator (simple format):
  - Good: "Question 5 of ~12"
  - Bad: "Entropy: 1.23, Confidence: 38%"
- [ ] Multi-select questions supported when appropriate

**Verification after 3-5 questions:**
```bash
ls -la .claude/with_me/sessions/
cat .claude/with_me/sessions/*.json | python3 -m json.tool | head -50
```

Expected:
- [ ] Session file created
- [ ] Valid JSON structure
- [ ] Questions and answers recorded
- [ ] Dimensions updated with posteriors
- [ ] Information gain tracked

#### Step 2.4: Convergence
Continue until convergence.

**Expected behavior:**
- [ ] After sufficient questions (typically 8-15), session converges
- [ ] LLM detects convergence and stops questioning
- [ ] Completion message displayed (simple language)
  - Good: "Great! I've gathered enough information. Let me analyze your requirements."
  - Bad: JSON status output
- [ ] Session marked as completed

**Verification:**
```bash
cat .claude/with_me/sessions/*.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Status: {data.get(\"status\", \"unknown\")}')
print(f'Total questions: {data.get(\"question_count\", 0)}')
print(f'Total information gain: {data.get(\"total_info_gain\", 0):.2f} bits')
"
```

Expected:
- [ ] Status: "completed"
- [ ] Question count: 8-20 (depends on answers)
- [ ] Total information gain: >5 bits (typical range: 5-12 bits)

#### Step 2.5: Generate Requirements Specification
**Expected behavior:**
- [ ] LLM reads session file
- [ ] Invokes `/with-me:requirement-analysis` skill
- [ ] Generates structured requirement specification with:
  - Project overview
  - Functional requirements
  - Non-functional requirements
  - Technical considerations
  - Success criteria
- [ ] Specification is comprehensive and based on answers

**Verification:**
Review the generated specification:
- [ ] Accurately reflects user answers
- [ ] Well-structured and readable
- [ ] Includes specific details from session
- [ ] No hallucinated requirements

---

## Scenario 3: Early Termination

### Test Steps

#### Step 3.1: User Requests Early End
Start a session, answer 2-3 questions, then select "End session (clarity achieved)".

**Expected behavior:**
- [ ] Session ends immediately
- [ ] Status marked as "completed" (early)
- [ ] LLM proceeds to generate specification with available information
- [ ] Specification may be less detailed but still coherent

**Verification:**
```bash
cat .claude/with_me/sessions/*.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Question count: {data.get(\"question_count\", 0)}')
print(f'Status: {data.get(\"status\", \"unknown\")}')
"
```

Expected:
- [ ] Question count: 2-3 (less than normal convergence)
- [ ] Status: "completed"

---

## Scenario 4: Skip Questions

### Test Steps

#### Step 4.1: Skip Multiple Questions
Start a session, skip 2-3 questions by selecting "Skip this question".

**Expected behavior:**
- [ ] Skipped questions not recorded
- [ ] LLM moves to next dimension
- [ ] Session continues normally
- [ ] Convergence may take longer (more questions needed)

**Verification:**
```bash
cat .claude/with_me/sessions/*.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
answers = data.get('question_history', [])
print(f'Total interactions: {len(answers)}')
print(f'Skipped: {sum(1 for a in answers if a.get(\"answer\", \"\").lower().startswith(\"skip\"))}')
"
```

Expected:
- [ ] Skipped questions appear in history with "skip" marker

---

## Scenario 5: Multi-Select Questions

### Test Steps

#### Step 5.1: Answer Multi-Select Question
When a multi-select question appears (multiSelect: true):

**Expected behavior:**
- [ ] Question phrasing indicates multiple selections allowed
  - Example: "Select all that apply"
- [ ] User can select multiple options
- [ ] All selected options processed sequentially

**Select 2-3 options.**

**Expected behavior:**
- [ ] Each selection updates beliefs separately
- [ ] Belief updates are cumulative
- [ ] Next question adapts to all selected answers

**Verification:**
Check session file for multiple likelihood updates from one question.

---

## Scenario 6: Reference Materials

### Test Steps

#### Step 6.1: Provide Reference URL
When answering a question, provide a URL or file path instead of direct answer:

Example: "See requirements at https://example.com/spec.md"

**Expected behavior:**
- [ ] LLM detects reference material
- [ ] Uses WebFetch or Read tool to retrieve content
- [ ] Analyzes retrieved information
- [ ] Estimates likelihoods based on analyzed content
- [ ] Updates beliefs correctly
- [ ] Continues session

**Verification:**
- [ ] Answer recorded with reference information
- [ ] Beliefs updated appropriately based on content

---

## Scenario 7: Negative Information Gain

### Test Steps

#### Step 7.1: Provide Contradictory Answers
Intentionally provide answers that contradict previous responses:

Example:
- Question 1: "What type of application?" → Answer: "Web application"
- Question 5: "Do you need a server?" → Answer: "No, completely client-side static site"

**Expected behavior:**
- [ ] LLM detects negative information gain (entropy increases)
- [ ] System handles gracefully (no crash)
- [ ] Beliefs updated to reflect uncertainty
- [ ] Session continues
- [ ] Future questions may address the contradiction

**Verification:**
```bash
cat .claude/with_me/sessions/*.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for q in data.get('question_history', []):
    if q.get('information_gain', 0) < 0:
        print(f'Negative IG detected: {q.get(\"information_gain\"):.3f} bits')
        print(f'Question: {q.get(\"question\", \"unknown\")}')
"
```

Expected:
- [ ] Negative information gain recorded
- [ ] Session continues despite anomaly

---

## Scenario 8: Progress Display

### Test Steps

#### Step 8.1: Verify Progress Updates
During a session, observe progress indicators.

**Expected behavior:**
- [ ] Progress shown in simple language
- [ ] Question count displayed (e.g., "Question 5 of ~12")
- [ ] Optional: High-level dimension status
  - Good: "✓ Goals clarified, → Exploring tech stack"
  - Bad: "dimension: purpose, entropy: 0.82, confidence: 0.45"
- [ ] No raw JSON or technical metrics

---

## Edge Cases

### EC1: Session File Corruption
Manually corrupt a session file (invalid JSON).

```bash
echo "invalid json" > .claude/with_me/sessions/test-session.json
```

Run:
```
/with-me:good-question
```

**Expected behavior:**
- [ ] Detects corrupted file
- [ ] Creates new session (ignores corrupted one)
- [ ] No crash

### EC2: Very Long Answers
Provide an extremely long answer (>1000 words).

**Expected behavior:**
- [ ] Answer accepted
- [ ] Likelihood estimation handles long text
- [ ] No truncation errors

### EC3: Empty or Invalid Answers
Select "Other" and provide empty text or gibberish.

**Expected behavior:**
- [ ] Handles gracefully
- [ ] May show low information gain
- [ ] Session continues

### EC4: Maximum Questions Reached
Force session to hit max_questions limit (default: 50).

**Expected behavior:**
- [ ] Session terminates at limit
- [ ] Marked as completed
- [ ] Generates specification with available data

### EC5: No Convergence (All Skipped)
Skip every question.

**Expected behavior:**
- [ ] Reaches min_questions limit (default: 5)
- [ ] Eventually terminates
- [ ] Generates minimal specification

---

## Cleanup

```bash
# Remove test sessions
rm -rf .claude/with_me/sessions/

# Reset permissions (if needed)
# rm .claude/settings.local.json
```

---

## Related Tests

- [workflows/full_session.md](../workflows/full_session.md) - Complete requirement scenarios
