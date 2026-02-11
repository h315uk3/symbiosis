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

```bash
export CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT}"
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/setup_permissions.py"
```

If the script reports an error, check that you are in the workspace root, `CLAUDE_PLUGIN_ROOT` is set, and `.claude/` is writable.

### 1. Initialize Session

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.session init
```

Store the returned `session_id`. Do NOT show output to user.

Initialize feedback tracking:

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.feedback start --plain-output
```

Store the returned value as `FEEDBACK_SESSION_ID`.

**User-facing message:** "Let's clarify your requirements. I'll ask a series of questions to understand what you need."

### 2. Question Loop

Repeat until convergence:

#### 2.1. Select Dimension

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.session next-question --session-id <SESSION_ID>
```

If `"converged": true`, skip to step 3. Otherwise, the output contains:
- `dimension`, `dimension_name`, `dimension_description`: Dimension metadata (internal use)
- `focus_areas`: Key topics to probe
- `hypotheses`: Possible answers with descriptions and focus areas
- `importance`: Dimension weight (used in evaluation, step 2.2b)
- `posterior`: Current probability distribution over hypotheses (used in evaluation)
- `supports_multi_select`: Whether multiple selections are allowed

Get current session state:

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.session status --session-id <SESSION_ID>
```

The status provides `question_count`, per-dimension `entropy`/`confidence`, and convergence state.

**IMPORTANT:** Do NOT mention dimension names or technical terms to the user.

**Conversational flow transitions:** Before generating the question, check if the dimension has changed from the previous question. If so:
1. **Acknowledge the previous answer**: Briefly summarize what you learned (e.g., "Thanks, that clarifies the data format.")
2. **Use transition template**: Read the `transition_templates` from the dimension config. Use `"entry"` when entering a dimension for the first time, or `"from_other"` when returning to a previously visited dimension. Adapt the template naturally — do not use it verbatim.
3. **Pacing rule**: Track consecutive questions on the same dimension. If you have asked `max_consecutive_same_dimension` (default: 3) questions on the same dimension without switching, force a switch to another accessible dimension even if the current one has higher entropy.

If the dimension has NOT changed, still acknowledge the previous answer briefly before asking the next question.

#### 2.2. Generate and Evaluate Question

**a) Generate candidate question:**

Generate a contextual question based on:
- Dimension's focus areas and hypotheses from CLI output (Step 2.1)
- Current entropy level from status (broad if >1.0, specific if ≤1.0)
- Previous answers from question history in status output
- Follow-up opportunities based on past responses

**CRITICAL: Avoid duplicate questions.** Before generating, review the session's `question_history` (from session file or status output). Do NOT ask questions that:
- Have already been answered directly
- Cover the same semantic intent as previous questions
- Are redundant given what you already know

**b) Evaluate question quality:**

**PERFORMANCE OPTIMIZATION:** If `question_count < 2` (from status), skip evaluation and proceed directly to step 2.2c.

For question 3 onwards, evaluate using data from Step 2.1 output (`importance`, `posterior`, `hypotheses`) and status output (`entropy`):

**CLARITY (0.0-1.0):** Mean of three criteria:
- Hypothesis targeting: Does the question distinguish between the top 2-3 hypotheses by posterior probability? (0.0 generic → 1.0 directly discriminating)
- Answer actionability: Would each possible answer shift beliefs toward different hypotheses? (0.0 all equivalent → 1.0 each answer maps to different hypotheses)
- Specificity: Is the question about concrete details rather than abstract concepts? (0.0 abstract → 1.0 concrete)

**IMPORTANCE (0.0-1.0):**
```
IMPORTANCE = importance × (0.5 + 0.5 × current_entropy / h_max)
```
where `importance` is from next-question output, `current_entropy` is from status, and `h_max = log₂(number of hypotheses)`.

**EIG (bits):** Estimate expected information gain by considering how different hypothetical answers would redistribute the `posterior` from Step 2.1. For each plausible answer template (2-4), estimate how posterior probabilities would shift, then compute expected entropy reduction.

**IMPORTANT:** Answer templates used for EIG estimation are HYPOTHETICAL only. Do NOT present them as user options.

Practical reference: Strong discriminating questions yield 0.5-1.0 bits. Moderate: 0.3-0.5 bits. Weak: 0.1-0.3 bits. See `theory/good-question-theory.md` for mathematical details.

**REWARD:**
```
REWARD = EIG + 0.1 × CLARITY + 0.05 × IMPORTANCE
```

If REWARD < 0.5, regenerate question and re-evaluate. If REWARD >= 0.5, proceed to step 2.2c.

Do NOT show evaluation scores to the user.

**c) Ask user (AFTER evaluation is complete):**

**QUESTIONING PHASE:** Now you ask the actual question. This is NOT evaluation - wait for the user's actual response.

**Cognitive load constraints:** Check `max_options` from dimension config (default: 5, never exceed 7 per Miller's 7±2 rule). Adjust by `disclosure_layer`:
- `"overview"`: 2-3 choices
- `"detail"`: 3-4 choices
- `"edge_case"`: up to `max_options`

Generate answer options plus standard options:
- "Skip this question" / "Move to the next question without answering"
- "End session (clarity achieved)" / "I have sufficient clarity now"

Translate all text to the language specified in your system prompt.

**CRITICAL:** You MUST invoke the AskUserQuestion tool now. Do NOT skip this step. Do NOT use evaluation templates as answers.

**Multi-select support:** Check `supports_multi_select` from CLI output (Step 2.1):
- If `true`: Use "Select all that apply" phrasing with `multiSelect: true`
- If `false`: Use single-selection phrasing with `multiSelect: false`

Ask user using `AskUserQuestion`:
- Question: Your evaluated question (adjusted for multi-select if applicable)
- Header: Use `dimension_name` from CLI
- Options: Your options (translated)
- multiSelect: Based on `supports_multi_select`

Wait for the user's actual response. Do NOT proceed until the user answers.

Handle user response:
- Quick answer(s) or "Other": Proceed to step 2.3 with the answer (may be multiple items if multi-select)
- "Skip": Return to step 2.1
- "End session": Skip to step 3

#### 2.3. Update Beliefs

**Estimate Likelihoods:**

**CRITICAL: Handle reference materials properly.** If the user provides reference materials (URLs, file paths, documentation links) instead of a direct answer, you MUST retrieve and analyze them before estimating likelihoods:
- Use appropriate tools (WebFetch, Read, etc.) to retrieve the actual content
- Analyze the information contained in the reference
- Then estimate likelihoods based on the analyzed content, not the reference itself

Based on the user's answer, dimension description, and hypothesis information from Step 2.1, estimate P(answer | hypothesis) for each hypothesis.

**Multi-select handling:** If the user selected multiple answers, estimate likelihoods for **each selected item independently**, then pass them all at once as a JSON array. The CLI computes the joint likelihood (pointwise product) and performs a **single** Bayesian update.

Consider:
- How well does the answer align with each hypothesis description?
- Which hypothesis focus areas are mentioned or implied in the answer?
- Semantic meaning and context, not just keyword matching
- **Consistency with previous answers** (avoid contradicting established facts)

**Secondary dimension identification:** After estimating likelihoods for the primary dimension, check if the answer also provides information about other dimensions. If so:
- Estimate likelihoods for each secondary dimension
- Store as `SECONDARY_DIMS` (comma-separated) and `SECONDARY_LIKELIHOODS` (JSON object mapping dim_id to likelihood dict)

Likelihood format:
- Single-select: `'{"hyp1": 0.x, "hyp2": 0.y, ...}'` (must sum to ~1.0)
- Multi-select: `'[{"hyp1": 0.x, ...}, {"hyp1": 0.y, ...}]'` (one dict per selected answer, each summing to ~1.0)

**Update and Persist:**

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.session update-with-computation \
  --session-id <SESSION_ID> \
  --dimension <DIMENSION> \
  --question <QUESTION> \
  --answer <ANSWER> \
  --likelihoods "$LIKELIHOODS" \
  --reward <REWARD> \
  --eig <EIG> \
  --clarity <CLARITY> \
  --importance <IMPORTANCE>
```

Additional flags when secondary dimensions identified:
- `--secondary-dimensions "dim1,dim2"`
- `--secondary-likelihoods '{"dim1": {"h1": 0.x, ...}, "dim2": {"h1": 0.y, ...}}'`

Notes:
- `--answer`: For multi-select, combine all selected answers into a single string (e.g., "Answer1; Answer2; Answer3")
- `--likelihoods`: For multi-select, pass a JSON array of likelihood dicts (one per selected answer)
- For the first 2 questions (where evaluation was skipped), omit `--reward`, `--eig`, `--clarity`, `--importance`
- Secondary dimension updates apply with reduced weight (default 0.3). Only include when the answer clearly provides information about other dimensions.

Do NOT show output to the user.

**Record feedback:**

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.feedback record <FEEDBACK_SESSION_ID> \
  <QUESTION> \
  '{"dimension": "<DIMENSION>", "information_gain": <IG>, "reward_scores": <EVAL_SCORES>}' \
  '{"text": "<ANSWER>"}'
```

Use `information_gain` and `evaluation_scores` from `update-with-computation` output. If evaluation was skipped (first 2 questions), omit `reward_scores` from the context JSON.

Do NOT show output to the user.

**Negative Information Gain (IG < 0):**

If `information_gain` is negative, uncertainty increased rather than decreased. Two possible causes:

1. **Estimation error**: Your P(answer | hypothesis) estimates contradicted previous answers. Review likelihood values for logical consistency with the full answer history.
2. **Genuine conflict**: User's answer genuinely contradicts prior responses. This is valid — the system correctly reflects the conflict.

Continue normally. The system handles negative IG gracefully. Pay extra attention to consistency with ALL previous answers in future estimates.

#### 2.4. Display Progress (Optional)

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.session status --session-id <SESSION_ID>
```

**IMPORTANT:** Do NOT show raw JSON. Translate to user-friendly language:

```
Progress: Question 5 of ~12
✓ Understanding your goals (confident)
→ Exploring technical approach (38% confident)
• Performance requirements (not started)
```

Return to step 2.1.

### 3. Complete Session

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.session complete --session-id <SESSION_ID>
```

Complete feedback session with final entropy values from session status:

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.feedback complete <FEEDBACK_SESSION_ID> \
  '{"purpose": <ENTROPY>, "data": <ENTROPY>, "behavior": <ENTROPY>, "constraints": <ENTROPY>, "quality": <ENTROPY>}'
```

Do NOT show raw output. Provide a simple completion message.

### 4. Generate Requirements Specification

Read session data from `.claude/with_me/sessions/<SESSION_ID>.json`, then invoke:

```
/with-me:requirement-analysis
```

Provide the session data to the skill. The skill will analyze all collected answers and generate a structured requirement specification.

---

## Configuration

Adjust thresholds in `config/dimensions.json`:

- **convergence_threshold**: Entropy threshold for clarity (default: 0.3)
- **prerequisite_threshold**: Threshold for prerequisite satisfaction (default: 1.5)
- **max_questions**: Safety limit (default: 50)
- **min_questions**: Minimum before early termination (default: 5)

---

## Error Handling

- **Session Not Found**: Initialize new session with step 1
- **No Accessible Dimensions**: All blocked by prerequisites → proceed to step 3
- **Invalid Answers**: Minimal information gain; continue (framework handles noisy data)

---

## References

- **Theory**: `theory/good-question-theory.md` - Mathematical foundation (EIG, entropy, Bayesian methods)
- **CLI**: `with_me/cli/session.py` - Session management commands
- **Orchestrator**: `with_me/lib/session_orchestrator.py` - Core logic
- **Beliefs**: `with_me/lib/dimension_belief.py` - Bayesian updating
- **Analysis Skill**: `skills/requirement-analysis/SKILL.md` - Post-session specification
