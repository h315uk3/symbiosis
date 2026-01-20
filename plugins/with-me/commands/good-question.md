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

#### 2.1. Get Next Question

```bash
PYTHONPATH="plugins/with-me:${PYTHONPATH:-}" python3 -m with_me.cli.session next-question --session-id <SESSION_ID>
```

Output (if not converged):
```json
{
  "converged": false,
  "dimension": "purpose",
  "dimension_name": "Purpose",
  "question": "What is the core value you're providing?"
}
```

Output (if converged):
```json
{
  "converged": true,
  "reason": "All dimensions converged or max questions reached"
}
```

If `converged` is `true`, skip to step 3.

#### 2.2. Ask User

Use the `AskUserQuestion` tool with the question from step 2.1:

- **Question**: Use the `question` field from CLI output
- **Header**: Use the `dimension_name` field
- **Options** (translate to system prompt language):
  - "Provide detailed answer" / Description: "I'll give a comprehensive explanation"
  - "Provide brief answer" / Description: "I'll give a concise summary"
  - "Skip this question" / Description: "Move to the next question without answering"
  - "End session (clarity achieved)" / Description: "I have sufficient clarity now"
- **multiSelect**: false
- **IMPORTANT**: Translate all labels and descriptions according to the language specified in your system prompt

If user chooses "End session", skip to step 3.

If user chooses "Skip", return to step 2.1.

Otherwise, capture the user's answer and proceed to step 2.3.

#### 2.3. Update Beliefs

```bash
PYTHONPATH="plugins/with-me:${PYTHONPATH:-}" python3 -m with_me.cli.session update \
  --session-id <SESSION_ID> \
  --dimension <DIMENSION> \
  --question <QUESTION> \
  --answer <USER_ANSWER>
```

Output:
```json
{
  "information_gain": 1.234,
  "entropy_before": 2.0,
  "entropy_after": 0.766,
  "dimension": "purpose"
}
```

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

Return to step 2.1.

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
