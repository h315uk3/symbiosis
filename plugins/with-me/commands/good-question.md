---
description: "Adaptive requirement elicitation - systematically reduce uncertainty through information-maximizing questions"
allowed-tools: [AskUserQuestion, Bash, Skill]
---

# Good Question

**Adaptive requirement elicitation using Bayesian belief updating and information theory.**

When requirements are unclear, this command systematically reduces uncertainty through targeted questioning. Each question maximizes expected information gain, adapting to your answers in real-time.

---

## LLM Interaction Guidelines

When executing this command, maintain a clean separation between internal operations and user-facing communication.

### Principles for User Communication

1. **Focus on Requirements, Not Mechanisms**
   - Users should think about *what* they want to build, not *how* the system asks questions
   - Frame questions naturally without mentioning the framework's internal concepts

2. **Hide Technical Terminology from User View**
   - Terms like "entropy", "dimension", "posterior", "Bayesian update", "EIG" are for internal use only
   - Don't explain statistical concepts unless the user specifically asks
   - Translate technical status to plain language:
     - ❌ "Entropy: 1.23, Confidence: 38%"
     - ✅ "Still exploring options (38% confident)"

3. **Minimize Tool Execution Visibility**
   - Suppress CLI command display and JSON outputs from user view
   - When showing progress, use simple indicators: "Question 3 of ~12"
   - Only show computation results if they failed (for debugging)

4. **Present Clean Question Flows**
   - Ask questions directly without preambles about dimension selection
   - Provide answer options in natural language
   - Avoid meta-commentary about question quality scores or information gain predictions

### What Users Should See

**Good Example:**
```
Let's clarify your requirements. I'll ask a series of questions to understand what you need.

Question 1: What problem are you trying to solve with this software?

• Automate a repetitive task
• Analyze or visualize data
• Build a user-facing application
• Other (please describe)
```

### What Users Should NOT See

**Bad Example:**
```
Initializing session with ID 2026-01-20T23:51:27.956551
Selecting dimension: purpose (entropy: 2.0, confidence: 0%)
Executing: python3 -m with_me.cli.session next-question...
Output: {"converged": false, "dimension": "purpose"}
Evaluating question clarity: 0.85, importance: 0.72, EIG: 0.68
Reward score: 0.766 (threshold: 0.5) ✓

What problem are you trying to solve with this software?
```

### Implementation Notes

- Use internal variables for tracking (SESSION_ID, DIMENSION, etc.) without displaying them
- Summarize progress in simple terms: "We've covered 3 areas so far, focusing on 2 more"
- Only surface technical details if an error occurs that requires user action
- The requirement analysis output (step 4) can be detailed, as that's the desired deliverable

---

## Execution Protocol

### 0. Setup Permissions (First Time Only)

Check if permissions are already configured:

```bash
grep -c "with_me.cli.session" .claude/settings.local.json 2>/dev/null || echo "0"
```

If the output is `9`, skip to step 1. Otherwise, run the setup script:

```bash
if [ ! -f .claude/settings.local.json ]; then
  mkdir -p .claude
  echo '{"permissions":{"allow":[]}}' > .claude/settings.local.json
fi

if ! grep -q "with_me.cli.session" .claude/settings.local.json 2>/dev/null; then
  jq '.permissions.allow = ((.permissions.allow + [
    "Bash(python3 -m with_me.cli.session init*)",
    "Bash(python3 -m with_me.cli.session next-question*)",
    "Bash(python3 -m with_me.cli.session update*)",
    "Bash(python3 -m with_me.cli.session status*)",
    "Bash(python3 -m with_me.cli.session complete*)",
    "Bash(python3 -m with_me.cli.session compute-entropy*)",
    "Bash(python3 -m with_me.cli.session bayesian-update*)",
    "Bash(python3 -m with_me.cli.session information-gain*)",
    "Bash(python3 -m with_me.cli.session persist-computation*)"
  ]) | unique)' .claude/settings.local.json > /tmp/settings.tmp && mv /tmp/settings.tmp .claude/settings.local.json
fi
```

Verify setup succeeded by checking the count again. If not `9`, report the error.

### 1. Initialize Session

Execute the session CLI to initialize:

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.session init
```

Expected output (internal use only, do NOT show to user):
```json
{"session_id": "2026-01-20T12:34:56.789012", "status": "initialized"}
```

Store the `session_id` for subsequent commands.

**User-facing message:** "Let's clarify your requirements. I'll ask a series of questions to understand what you need."

### 2. Question Loop

Repeat until convergence:

#### 2.1. Select Dimension

Get next dimension to query:

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.session next-question --session-id <SESSION_ID>
```

If output shows `"converged": true`, skip to step 3. Otherwise, note the `dimension` and `dimension_name` (internal use only).

Get current session state:

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.session status --session-id <SESSION_ID>
```

Read dimension configuration from `config/dimensions.json` for the selected dimension.

**IMPORTANT:** Do NOT mention dimension names or technical terms to the user. Proceed directly to generating the question in step 2.2.

#### 2.2. Generate and Evaluate Question

**a) Generate candidate question:**

Generate a contextual question based on:
- Dimension's focus areas from config
- Current entropy level (broad if >1.0, specific if ≤1.0)
- Previous answers from status output
- Follow-up opportunities

**b) Evaluate question quality:**

**PERFORMANCE OPTIMIZATION:** Check the `question_count` from the session status (obtained in step 2.1). If `question_count < 2`, skip the evaluation steps (Step 1-5 below) and proceed directly to step 2.2c. This significantly reduces latency while maintaining quality, as initial questions are typically straightforward and high-value.

For question 3 onwards (`question_count >= 2`), perform full evaluation:

**IMPORTANT:**
- You MUST invoke all three skills using the Skill tool. Do NOT estimate or calculate these values yourself.
- Do NOT show evaluation scores (CLARITY, IMPORTANCE, EIG, REWARD) to the user. These are internal quality metrics.

**Step 1: Evaluate clarity**

MUST invoke `/with-me:question-clarity` skill:
- Input: Your generated question text
- Output: Store as `CLARITY` (float [0.0, 1.0])

**Step 2: Evaluate importance**

MUST invoke `/with-me:question-importance` skill:
- Input: Your generated question text
- Output: Store as `IMPORTANCE` (float [0.0, 1.0])

**Step 3: Calculate Expected Information Gain**

**EVALUATION ONLY:** This step uses hypothetical answer templates for EIG calculation. Do NOT treat these templates as actual user answers.

First, get current beliefs from session status:
```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.session status --session-id <SESSION_ID>
```

Extract the posterior distribution for the selected dimension from the status output.

**CRITICAL: DO NOT estimate EIG yourself. You MUST invoke the skill for accurate counterfactual simulation.**

Then, MUST invoke `/with-me:eig-calculation` skill with:
- Question: Your generated question text
- Current beliefs: The posterior distribution from status output
- Answer templates: 3-4 representative answer options (HYPOTHETICAL, for calculation only)

Output: Store as `EIG` (float, bits)

**IMPORTANT:** Discard the answer templates after EIG calculation. They are NOT user responses.

**Step 4: Calculate reward score**

```
REWARD = EIG + 0.1 * CLARITY + 0.05 * IMPORTANCE
```

**Step 5: Quality threshold check**

If REWARD < 0.5:
- Regenerate question
- Return to Step 1 with new question

If REWARD >= 0.5:
- Proceed to Step 2.2c (Ask user)

**c) Ask user (AFTER evaluation is complete):**

**QUESTIONING PHASE:** Now you ask the actual question. This is NOT evaluation - wait for the user's actual response.

Generate 2-4 quick answer options relevant to your question, plus standard options:
- "Skip this question" / "Move to the next question without answering"
- "End session (clarity achieved)" / "I have sufficient clarity now"

Translate all text to the language specified in your system prompt.

**CRITICAL:** You MUST invoke the AskUserQuestion tool now. Do NOT skip this step. Do NOT use evaluation templates as answers.

Ask user using `AskUserQuestion` tool:
- Question: Your evaluated question
- Header: Use `dimension_name` from CLI
- Options: Your options (translated)
- multiSelect: false

Wait for the user's actual response. Do NOT proceed until the user answers.

Handle user response:
- Quick answer or "Other": Proceed to step 2.3 with the answer
- "Skip": Return to step 2.1
- "End session": Skip to step 3

#### 2.3. Update Beliefs

**IMPORTANT:**
- You MUST execute all CLI commands using Bash tool and invoke all skills using Skill tool. DO NOT estimate likelihoods, calculate entropy, or perform Bayesian updates yourself.
- Do NOT show CLI outputs, likelihoods, entropy values, or Bayesian update results to the user. These are internal computations.

**Step 1: Get hypothesis definitions and estimate likelihoods**

MUST execute this CLI command using Bash tool:

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.session update \
  --session-id <SESSION_ID> \
  --dimension <DIMENSION> \
  --question <QUESTION> \
  --answer <ANSWER> \
  --enable-semantic-evaluation
```

The CLI will output hypothesis definitions with their descriptions and focus areas.

Based on the user's answer and the hypothesis definitions, estimate P(answer | hypothesis) for each hypothesis using semantic evaluation.

Store the likelihoods as JSON: `LIKELIHOODS='{"hyp1": 0.x, "hyp2": 0.y, ...}'`

The likelihoods should sum to approximately 1.0.

**Step 2: Calculate entropy before update**

MUST execute this CLI command using Bash tool:

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.session compute-entropy \
  --session-id <SESSION_ID> \
  --dimension <DIMENSION>
```

The CLI will output JSON with the current posterior distribution.

**CRITICAL: DO NOT calculate entropy yourself, even if the CLI output says "computation_request". You MUST invoke the skill.**

Then, MUST invoke `/with-me:entropy` skill with:
- Input: The posterior distribution from CLI output
- Formula: H(h) = -Σ p(h) log₂ p(h)
- Output: Store as `H_BEFORE` (float, bits)

**Step 3: Perform Bayesian update**

MUST execute this CLI command using Bash tool:

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.session bayesian-update \
  --session-id <SESSION_ID> \
  --dimension <DIMENSION> \
  --likelihoods "$LIKELIHOODS"
```

The CLI will output JSON with prior and likelihoods.

**CRITICAL: DO NOT perform Bayesian update yourself, even if the CLI output says "computation_request". You MUST invoke the skill.**

Then, MUST invoke `/with-me:bayesian-update` skill with:
- Input: Prior distribution and likelihoods from CLI output
- Formula: p₁(h) = [p₀(h) * L(obs|h)] / Σ[p₀(h) * L(obs|h)]
- Output: Store as `UPDATED_POSTERIOR='{"hyp1": 0.x, "hyp2": 0.y, ...}'`

**Step 4: Calculate entropy after update**

MUST invoke `/with-me:entropy` skill with:
- Input: `UPDATED_POSTERIOR` from Step 3
- Formula: H(h) = -Σ p(h) log₂ p(h)
- Output: Store as `H_AFTER` (float, bits)

**Step 5: Calculate information gain**

MUST invoke `/with-me:information-gain` skill with:
- Input: `H_BEFORE` from Step 2 and `H_AFTER` from Step 4
- Formula: IG = H_before - H_after
- Output: Store as `INFORMATION_GAIN` (float, bits)

**Step 6: Persist computation results**

MUST execute this CLI command using Bash tool:

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.session persist-computation \
  --session-id <SESSION_ID> \
  --dimension <DIMENSION> \
  --question <QUESTION> \
  --answer <ANSWER> \
  --entropy-before $H_BEFORE \
  --entropy-after $H_AFTER \
  --information-gain $INFORMATION_GAIN \
  --updated-posterior "$UPDATED_POSTERIOR"
```

The CLI will confirm persistence and increment the question count.

#### 2.4. Display Progress (Optional)

Get current session status:

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.session status --session-id <SESSION_ID>
```

**IMPORTANT:** Do NOT show the raw JSON output to the user. Instead, translate the status into simple, user-friendly language.

**Good progress display:**
```
Progress: Question 5 of ~12
✓ Understanding your goals (confident)
→ Exploring technical approach (38% confident)
• Performance requirements (not started)
```

**Bad progress display:**
```json
{"session_id": "...", "question_count": 5, "dimensions": {"purpose": {"entropy": 1.23, "confidence": 0.38}}}
```

Return to step 2.1-2.2.

### 3. Complete Session

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.session complete --session-id <SESSION_ID>
```

**IMPORTANT:** Do NOT show the raw JSON output to the user. Instead, provide a simple completion message.

**Good completion message:**
```
Great! I've gathered enough information through 12 questions. Let me now analyze your requirements and create a specification.
```

**Bad completion message:**
```json
{"session_id": "2026-01-20T...", "total_questions": 12, "total_info_gain": 8.45, "status": "completed"}
```

### 4. Generate Requirements Specification

Invoke the requirement-analysis skill:

```
/with-me:requirement-analysis
```

The skill will analyze all collected answers and generate a structured requirement specification.

---

## Configuration

Adjust thresholds in `config/dimensions.json`:

- **convergence_threshold**: Entropy threshold for clarity (default: 0.3)
- **prerequisite_threshold**: Threshold for prerequisite satisfaction (default: 1.5)
- **max_questions**: Safety limit (default: 50)
- **min_questions**: Minimum before early termination (default: 5)

---

## Error Handling

### Session Not Found

If CLI returns error "Session not found":
- Session state was lost or deleted
- Initialize new session with step 1

### No Accessible Dimensions

If CLI returns `{"converged": true, "reason": "No accessible dimensions"}`:
- All dimensions blocked by unmet prerequisites
- Proceed to step 3 (complete session)

### Invalid Answers

If user provides unclear or off-topic answers:
- Bayesian update will show minimal information gain
- Continue questioning (framework handles noisy data naturally)

---

## References

- **Theory**: `theory/good-question-theory.md` - Mathematical foundation
- **CLI**: `with_me/cli/session.py` - Session management commands
- **Orchestrator**: `with_me/lib/session_orchestrator.py` - Core logic
- **Beliefs**: `with_me/lib/dimension_belief.py` - Bayesian updating
- **Analysis Skill**: `skills/requirement-analysis/SKILL.md` - Post-session specification
