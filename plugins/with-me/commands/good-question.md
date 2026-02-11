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

Run the permission setup script:

```bash
export CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT}"
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/setup_permissions.py"
```

The script will:
- Create `.claude/settings.local.json` if it doesn't exist
- Add 12 required permissions (1 PYTHONPATH + 6 session CLI + 3 feedback CLI + 1 Skill + 1 Read)
- Deduplicate existing permissions
- Output setup status as JSON

Expected output:
```json
{"status": "updated", "added": 9, "total": 9, "file": ".claude/settings.local.json"}
```

Or if already configured:
```json
{"status": "already_configured", "total": 9, "file": ".claude/settings.local.json"}
```

If the script reports an error, check that:
- You are in the workspace root directory (where `.claude/` is located)
- `CLAUDE_PLUGIN_ROOT` is set correctly
- The `.claude/` directory is writable

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

Also initialize feedback tracking for cross-session analytics:

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.feedback start --plain-output
```

Store the returned value as `FEEDBACK_SESSION_ID`. This is separate from `SESSION_ID` and used only for recording question feedback.

**User-facing message:** "Let's clarify your requirements. I'll ask a series of questions to understand what you need."

### 2. Question Loop

Repeat until convergence:

#### 2.1. Select Dimension

Get next dimension to query:

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.session next-question --session-id <SESSION_ID>
```

If output shows `"converged": true`, skip to step 3. Otherwise, the output contains:
- `dimension`: Dimension ID (internal use only)
- `dimension_name`: Display name for AskUserQuestion header
- `dimension_description`: What this dimension explores
- `focus_areas`: Key topics to probe
- `hypotheses`: Possible answers with descriptions and focus areas
- `supports_multi_select`: Whether this dimension allows multiple selections (true/false)

Get current session state:

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.session status --session-id <SESSION_ID>
```

The status output contains:
- `question_count`: Number of questions asked so far (used in Step 2.2b for performance optimization)
- `dimensions`: Current entropy, confidence, and most likely hypothesis for each dimension

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

**PERFORMANCE OPTIMIZATION:** Check the `question_count` from the session status (obtained in step 2.1). If `question_count < 2`, skip the evaluation steps below and proceed directly to step 2.2c. This significantly reduces latency while maintaining quality, as initial questions are typically straightforward and high-value.

For question 3 onwards (`question_count >= 2`), perform full evaluation:

**Step 1: Get evaluation formulas and data**

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.session evaluate-question \
  --session-id <SESSION_ID> \
  --dimension <DIMENSION> \
  --question <YOUR_GENERATED_QUESTION>
```

The CLI outputs evaluation formulas and data. Use this information to calculate quality metrics yourself.

**Step 2: Calculate CLARITY (0.0-1.0)**

Based on the clarity criteria from CLI output, evaluate your question:
- Question mark present
- Appropriate length (10-30 words)
- No ambiguous terms (maybe, perhaps, might)
- Single focused question (no compound or/and)

Store as `CLARITY` (float [0.0, 1.0])

**Step 3: Calculate IMPORTANCE (0.0-1.0)**

Use the formula provided by CLI:
```
IMPORTANCE = importance_base × (0.5 + 0.5 × current_entropy / h_max)
```

All values are provided in the CLI output. Calculate and store as `IMPORTANCE` (float [0.0, 1.0])

**Step 4: Estimate EIG (bits)**

**Probability-Based Estimation Method:**

For each hypothesis h_i with posterior probability P(h_i), consider how the question's answer templates would affect beliefs:

1. **Enumerate likely answer templates** (2-4 realistic user responses)
2. **For each template t**: Estimate P(h_i | t) - how would each hypothesis's probability change?
3. **Calculate entropy after template**: H(t) = -Σ P(h_i | t) × log₂(P(h_i | t))
4. **Estimate template probability**: P(t) - how likely is this answer?
5. **Compute expected entropy**: H_expected = Σ P(t) × H(t)
6. **Calculate EIG**: EIG = H_current - H_expected

**IMPORTANT:** These answer templates are HYPOTHETICAL, for calculation only. They are NOT the user's actual answer. You must still ask the user and wait for their real response in Step 2.2c.

**Practical Guidelines:**
- Strong discriminating questions with clear answer patterns: 0.5-1.0 bits
- Moderate questions that partially narrow uncertainty: 0.3-0.5 bits
- Weak questions with ambiguous or overlapping answers: 0.1-0.3 bits

**Quality Checks:**
- Does the question target high-probability hypotheses?
- Would different answers clearly distinguish hypotheses?
- Is the question relevant to current uncertainty (high entropy dimensions)?

Store as `EIG` (float, bits)

**Step 5: Calculate reward score**

```
REWARD = EIG + 0.1 × CLARITY + 0.05 × IMPORTANCE
```

**Step 6: Quality threshold check**

If REWARD < 0.5:
- Regenerate question
- Return to Step 1 with new question

If REWARD >= 0.5:
- Proceed to Step 2.2c (Ask user)

**IMPORTANT:** Do NOT show evaluation scores to the user. These are internal quality metrics.

**c) Ask user (AFTER evaluation is complete):**

**QUESTIONING PHASE:** Now you ask the actual question. This is NOT evaluation - wait for the user's actual response.

**Cognitive load constraints:** Check the `max_options` field from the dimension config (Step 2.1 CLI output). Generate answer options respecting this limit (default: 5, never exceed 7 per Miller's 7±2 rule). Also check `disclosure_layer`:
- `"overview"` dimensions: Use broad, simple options (2-3 choices)
- `"detail"` dimensions: Use moderately specific options (3-4 choices)
- `"edge_case"` dimensions: Use targeted, specific options (up to `max_options`)

Generate answer options (respecting the `max_options` limit) plus standard options:
- "Skip this question" / "Move to the next question without answering"
- "End session (clarity achieved)" / "I have sufficient clarity now"

Translate all text to the language specified in your system prompt.

**CRITICAL:** You MUST invoke the AskUserQuestion tool now. Do NOT skip this step. Do NOT use evaluation templates as answers.

**Multi-select support:** Check the `supports_multi_select` field from the CLI output (Step 2.1):
- If `true`: Adjust question phrasing to "Select all that apply" style and use `multiSelect: true`
- If `false`: Use single-selection phrasing and `multiSelect: false`

Ask user using `AskUserQuestion` tool:
- Question: Your evaluated question (adjusted for multi-select if applicable)
- Header: Use `dimension_name` from CLI
- Options: Your options (translated)
- multiSelect: Use value based on `supports_multi_select` flag

Wait for the user's actual response. Do NOT proceed until the user answers.

Handle user response:
- Quick answer(s) or "Other": Proceed to step 2.3 with the answer (may be multiple items if multi-select)
- "Skip": Return to step 2.1
- "End session": Skip to step 3

#### 2.3. Update Beliefs

**Phase A: Estimate Likelihoods**

**CRITICAL: Handle reference materials properly.** If the user provides reference materials (URLs, file paths, documentation links) instead of a direct answer, you MUST retrieve and analyze them before estimating likelihoods:

- Use appropriate tools (WebFetch, Read, etc.) to retrieve the actual content
- Analyze the information contained in the reference
- Then estimate likelihoods based on the analyzed content, not the reference itself

Example workflow:
```
User provides reference → Retrieve content → Analyze information → Estimate likelihoods
```

Based on the user's answer (or analyzed content from references), the dimension description, and hypothesis information from Step 2.1, estimate the likelihood P(answer | hypothesis) for each hypothesis.

**Multi-select handling:** If the user selected multiple answers, estimate likelihoods for **each selected item independently**, then pass them all at once as a JSON array to `update-with-computation`. The CLI computes the joint likelihood (pointwise product) and performs a **single** Bayesian update. This avoids negative information gain from contradictory sequential updates.

Consider:
- How well does the answer align with each hypothesis description?
- Which hypothesis focus areas are mentioned or implied in the answer?
- Semantic meaning and context, not just keyword matching
- **Consistency with previous answers** (avoid contradicting established facts)

**Secondary dimension identification:** After estimating likelihoods for the primary dimension, check if the answer also provides information about other dimensions. For example, an answer about "purpose" mentioning "real-time collaboration" may also inform "behavior" (asynchronous) and "stakeholders" (team). If secondary dimensions are identified:
- Estimate likelihoods for each secondary dimension
- Store as `SECONDARY_DIMS` (comma-separated) and `SECONDARY_LIKELIHOODS` (JSON object mapping dim_id to likelihood dict)

Store as:
- Single-select: `LIKELIHOODS='{"hyp1": 0.x, "hyp2": 0.y, ...}'` (must sum to ~1.0)
- Multi-select: `LIKELIHOODS='[{"hyp1": 0.x, ...}, {"hyp1": 0.y, ...}]'` (one dict per selected answer, each summing to ~1.0)

**Phase B+C: Update and Persist** (single CLI command)

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

If secondary dimensions were identified in Phase A, add:
```bash
  --secondary-dimensions "behavior,stakeholders" \
  --secondary-likelihoods '{"behavior": {"synchronous": 0.1, "asynchronous": 0.6, "interactive": 0.2, "batch": 0.1}, "stakeholders": {"individual_user": 0.1, "team": 0.7, "organization": 0.1, "external_customers": 0.1}}'
```

- `--answer`: For multi-select, combine all selected answers into a single string (e.g., "Answer1; Answer2; Answer3")
- `--likelihoods`: For multi-select, pass a JSON array of likelihood dicts (one per selected answer). The CLI computes the joint likelihood internally.
- `--reward`, `--eig`, `--clarity`, `--importance`: Evaluation scores from Step 2.2b. These are persisted to the session file for structural reliability.
- `--secondary-dimensions`, `--secondary-likelihoods`: Cross-dimension updates applied with reduced weight (default 0.3). Only include when the answer clearly provides information about other dimensions.
- For the first 2 questions (where evaluation was skipped), omit the evaluation optional flags.

This command internally:
- For multi-select: computes joint likelihood (pointwise product of individual likelihoods, normalized)
- Calculates entropy before/after using Shannon formula
- Performs Dirichlet update (alpha += weight * likelihood)
- Calculates information gain (H_before - H_after) and JSD (belief shift)
- Applies secondary dimension updates with reduced weight
- Updates Thompson Sampling state and records IG
- Persists results and evaluation scores to session file

Output (internal use only): `status`, `entropy_before`, `entropy_after`, `information_gain`, `jsd`, `question_count`, `evaluation_scores` (if provided), `secondary_updates` and `total_cross_dimension_ig` (if secondary dimensions provided)

**Record feedback** (after each update, using values from the output above):

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.feedback record <FEEDBACK_SESSION_ID> \
  <QUESTION> \
  '{"dimension": "<DIMENSION>", "information_gain": <INFORMATION_GAIN>, "reward_scores": <EVALUATION_SCORES>}' \
  '{"text": "<ANSWER>"}'
```

- `<INFORMATION_GAIN>`: From `information_gain` in `update-with-computation` output
- `<EVALUATION_SCORES>`: From `evaluation_scores` in `update-with-computation` output (the full JSON object). If `evaluation_scores` is absent (first 2 questions), omit `reward_scores` from the context JSON.

Do NOT show output to the user.

**ANOMALY DETECTION: Negative Information Gain**

If `information_gain` is negative (IG < 0), this means uncertainty *increased* rather than decreased. This is an anomaly with two possible root causes:

**Root Cause 1: Inconsistent Likelihood Estimation**
- Your P(answer | hypothesis) estimates contradicted previous answers
- Example: Previously indicated "web app", but new likelihood strongly favored "CLI tool"
- **Action**: Review answer history and ensure new estimates are consistent with established facts

**Root Cause 2: Genuinely Conflicting Information**
- User's answer genuinely contradicts their previous responses
- Example: User said "real-time updates" but later rejected "WebSocket" and "database"
- **Action**: This is valid uncertainty - system correctly reflects the conflict

**How to Proceed:**
1. **Check for estimation errors first**: Review your likelihood values for logical consistency
2. **If estimates are sound**: Accept the negative IG - the user may need to resolve contradictions
3. **Continue normally**: The system handles negative IG gracefully with validation (values are clamped to valid probabilities)
4. **Future questions**: Pay extra attention to consistency with ALL previous answers, not just the most recent one

The system will continue execution - this warning helps you maintain quality in future likelihood estimates.

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

Also complete the feedback session with final entropy values from the session status:

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.feedback complete <FEEDBACK_SESSION_ID> \
  '{"purpose": <ENTROPY>, "data": <ENTROPY>, "behavior": <ENTROPY>, "constraints": <ENTROPY>, "quality": <ENTROPY>}'
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

**IMPORTANT:** Session data is stored at `.claude/with_me/sessions/<SESSION_ID>.json`

Read the completed session data using the Read tool:
```
.claude/with_me/sessions/<SESSION_ID>.json
```

Then invoke the requirement-analysis skill:
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
