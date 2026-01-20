---
description: "Adaptive requirement elicitation - systematically reduce uncertainty through information-maximizing questions"
allowed-tools: [AskUserQuestion, Bash, Skill]
---

# Good Question

@theory/good-question-theory.md

**Adaptive requirement elicitation using Bayesian belief updating and information theory.**

When requirements are unclear, this command systematically reduces uncertainty through targeted questioning. Each question maximizes expected information gain, adapting to your answers in real-time.

---

## Execution Protocol

### 0. Setup Permissions (First Time Only)

Add session CLI commands to allowed permissions:

```bash
if ! grep -q "with_me.cli.session" ~/.claude/settings.local.json 2>/dev/null; then
  jq '.permissions.allow += [
    "Bash(PYTHONPATH=\"plugins/with-me:${PYTHONPATH:-}\" python3 -m with_me.cli.session init*)",
    "Bash(PYTHONPATH=\"plugins/with-me:${PYTHONPATH:-}\" python3 -m with_me.cli.session next-question*)",
    "Bash(PYTHONPATH=\"plugins/with-me:${PYTHONPATH:-}\" python3 -m with_me.cli.session update*)",
    "Bash(PYTHONPATH=\"plugins/with-me:${PYTHONPATH:-}\" python3 -m with_me.cli.session status*)",
    "Bash(PYTHONPATH=\"plugins/with-me:${PYTHONPATH:-}\" python3 -m with_me.cli.session complete*)"
  ] | unique' ~/.claude/settings.local.json > /tmp/settings.tmp && mv /tmp/settings.tmp ~/.claude/settings.local.json
fi
```

This adds permissions for session commands only, without affecting other Python development.

### 1. Initialize Session

Execute the session CLI to initialize:

```bash
PYTHONPATH="plugins/with-me:${PYTHONPATH:-}" python3 -m with_me.cli.session init
```

Expected output:
```json
{"session_id": "2026-01-20T12:34:56.789012", "status": "initialized"}
```

Store the `session_id` for subsequent commands.

### 2. Question Loop

Repeat until convergence:

#### 2.1-2.2. Generate and Ask Question

Get next dimension to query:

```bash
PYTHONPATH="plugins/with-me:${PYTHONPATH:-}" python3 -m with_me.cli.session next-question --session-id <SESSION_ID>
```

If output shows `"converged": true`, skip to step 3. Otherwise, note the `dimension` and `dimension_name`.

Get current session state:

```bash
PYTHONPATH="plugins/with-me:${PYTHONPATH:-}" python3 -m with_me.cli.session status --session-id <SESSION_ID>
```

Read dimension configuration from `config/dimensions.json` for the selected dimension. Use `focus_areas` and `question_guidelines` to understand what to ask.

Generate a contextual question based on:
- Dimension's focus areas
- Current entropy level (broad if >1.0, specific if ≤1.0)
- Previous answers from status output
- Follow-up opportunities

Generate 2-4 quick answer options relevant to your question, plus standard options:
- "Skip this question" / "Move to the next question without answering"
- "End session (clarity achieved)" / "I have sufficient clarity now"

Translate all text to the language specified in your system prompt.

Ask user using `AskUserQuestion` tool:
- Question: Your generated question
- Header: Use `dimension_name` from CLI
- Options: Your options (translated)
- multiSelect: false

Handle user response:
- Quick answer or "Other": Proceed to step 2.3 with the answer
- "Skip": Return to step 2.1-2.2
- "End session": Skip to step 3

#### 2.3. Update Beliefs

Execute CLI to get evaluation request:

```bash
PYTHONPATH="plugins/with-me:${PYTHONPATH:-}" python3 -m with_me.cli.session update \
  --session-id <SESSION_ID> \
  --dimension <DIMENSION> \
  --question <QUESTION> \
  --answer <ANSWER> \
  --enable-semantic-evaluation
```

The CLI outputs evaluation request JSON with hypothesis definitions. Read this output.

Calculate likelihoods P(answer | hypothesis) for each hypothesis:
- Use hypothesis `description` and `focus_areas` for context
- Evaluate semantic alignment between question-answer pair and each hypothesis
- Ensure likelihoods sum to approximately 1.0
- Format as JSON object: `{"hyp1": 0.x, "hyp2": 0.y, ...}`

Execute CLI to update beliefs with your calculated likelihoods:

```bash
PYTHONPATH="plugins/with-me:${PYTHONPATH:-}" python3 -m with_me.cli.session update \
  --session-id <SESSION_ID> \
  --dimension <DIMENSION> \
  --question <QUESTION> \
  --answer <ANSWER> \
  --likelihoods '<YOUR_CALCULATED_LIKELIHOODS>'
```

The CLI outputs information gain and updated entropy values.

#### 2.4. Display Progress (Optional)

Show entropy reduction to user:

```bash
PYTHONPATH="plugins/with-me:${PYTHONPATH:-}" python3 -m with_me.cli.session status --session-id <SESSION_ID>
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
PYTHONPATH="plugins/with-me:${PYTHONPATH:-}" python3 -m with_me.cli.session complete --session-id <SESSION_ID>
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
