---
description: "Adaptive requirement elicitation - systematically reduce uncertainty through information-maximizing questions"
allowed-tools: [AskUserQuestion, Bash, Skill]
---

# Good Question

**Adaptive requirement elicitation using Bayesian belief updating and information theory.**

When requirements are unclear, this command systematically reduces uncertainty through targeted questioning. Each question maximizes expected information gain, adapting to your answers in real-time.

---

## Execution Protocol

### 0. Setup Permissions (First Time Only)

Add session CLI commands to allowed permissions:

```bash
if [ ! -f .claude/settings.local.json ]; then
  mkdir -p .claude
  echo '{"permissions":{"allow":[]}}' > .claude/settings.local.json
fi

if ! grep -q "with_me.cli.session" .claude/settings.local.json 2>/dev/null; then
  jq '.permissions.allow += [
    "Bash(python3 -m with_me.cli.session init*)",
    "Bash(python3 -m with_me.cli.session next-question*)",
    "Bash(python3 -m with_me.cli.session update*)",
    "Bash(python3 -m with_me.cli.session status*)",
    "Bash(python3 -m with_me.cli.session complete*)",
    "Bash(python3 -m with_me.cli.session compute-entropy*)",
    "Bash(python3 -m with_me.cli.session bayesian-update*)",
    "Bash(python3 -m with_me.cli.session information-gain*)",
    "Bash(python3 -m with_me.cli.session persist-computation*)"
  ] | unique' .claude/settings.local.json > /tmp/settings.tmp && mv /tmp/settings.tmp .claude/settings.local.json
fi
```

This adds permissions for all session commands required by the adaptive questioning workflow, without affecting other Python development.

### 1. Initialize Session

Execute the session CLI to initialize:

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.session init
```

Expected output:
```json
{"session_id": "2026-01-20T12:34:56.789012", "status": "initialized"}
```

Store the `session_id` for subsequent commands.

### 2. Question Loop

Repeat until convergence:

#### 2.1. Select Dimension

Get next dimension to query:

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.session next-question --session-id <SESSION_ID>
```

If output shows `"converged": true`, skip to step 3. Otherwise, note the `dimension` and `dimension_name`.

Get current session state:

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.session status --session-id <SESSION_ID>
```

Read dimension configuration from `config/dimensions.json` for the selected dimension.

#### 2.2. Generate and Evaluate Question

**a) Generate candidate question:**

Generate a contextual question based on:
- Dimension's focus areas from config
- Current entropy level (broad if >1.0, specific if ≤1.0)
- Previous answers from status output
- Follow-up opportunities

**b) Evaluate question quality:**

**IMPORTANT: You MUST invoke all three skills using the Skill tool. Do NOT estimate or calculate these values yourself.**

**Step 1: Evaluate clarity**

MUST invoke `/with-me:question-clarity` skill:
- Input: Your generated question text
- Output: Store as `CLARITY` (float [0.0, 1.0])

**Step 2: Evaluate importance**

MUST invoke `/with-me:question-importance` skill:
- Input: Your generated question text
- Output: Store as `IMPORTANCE` (float [0.0, 1.0])

**Step 3: Calculate Expected Information Gain**

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
- Answer templates: 3-4 representative answer options you would ask the user

Output: Store as `EIG` (float, bits)

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

**c) Ask user:**

Generate 2-4 quick answer options relevant to your question, plus standard options:
- "Skip this question" / "Move to the next question without answering"
- "End session (clarity achieved)" / "I have sufficient clarity now"

Translate all text to the language specified in your system prompt.

Ask user using `AskUserQuestion` tool:
- Question: Your evaluated question
- Header: Use `dimension_name` from CLI
- Options: Your options (translated)
- multiSelect: false

Handle user response:
- Quick answer or "Other": Proceed to step 2.3 with the answer
- "Skip": Return to step 2.1
- "End session": Skip to step 3

#### 2.3. Update Beliefs

**IMPORTANT: You MUST execute all CLI commands using Bash tool and invoke all skills using Skill tool. DO NOT estimate likelihoods, calculate entropy, or perform Bayesian updates yourself.**

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

Show entropy reduction to user:

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.session status --session-id <SESSION_ID>
```

Output:
```json
{
  "session_id": "...",
  "question_count": 5,
  "all_converged": false,
  "dimensions": {
    "purpose": {
      "name": "Purpose",
      "entropy": 1.23,
      "confidence": 0.38,
      "converged": false,
      "blocked": false,
      "most_likely": null
    },
    ...
  }
}
```

Format dimensions for user display (entropy bars, confidence percentages, convergence status).

Return to step 2.1-2.2.

### 3. Complete Session

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.session complete --session-id <SESSION_ID>
```

Output:
```json
{
  "session_id": "...",
  "total_questions": 12,
  "total_info_gain": 8.45,
  "status": "completed"
}
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
