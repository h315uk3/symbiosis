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

**Step A: Get Dimension Context**

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

**Step B: Get Session State for Context**

```bash
PYTHONPATH="plugins/with-me:${PYTHONPATH:-}" python3 -m with_me.cli.session status --session-id <SESSION_ID>
```

This provides current entropy levels and previous answers for contextual question generation.

**Step C: Generate Contextual Question and Options**

Based on the dimension context from CLI, generate a contextual question and quick answer options:

**Generation Guidelines:**

1. **Load dimension configuration** from `config/dimensions.json`:
   - Use `focus_areas` to understand what aspects to explore
   - Use `question_guidelines.when_high_entropy` if entropy > 1.0 (broad, exploratory)
   - Use `question_guidelines.when_converging` if entropy ≤ 1.0 (specific, validation)
   - Use `question_guidelines.follow_up_triggers` to detect opportunities for follow-up

2. **Consider conversation context**:
   - Review previous answers (from status output) to avoid repetition
   - Look for follow-up opportunities based on what user mentioned
   - Adapt question depth based on current entropy level

3. **Generate question**: Create a contextual question that:
   - Aligns with dimension's focus areas
   - Matches entropy level (broad vs. specific)
   - Follows up on previous answers when appropriate
   - Is clear and answerable

4. **Generate 2-4 quick answer options** that:
   - Are relevant to the specific question
   - Cover common answer patterns for this dimension
   - Are mutually exclusive
   - Are brief (1-5 words)

5. **Add standard options**:
   - "Skip this question" / "Move to the next question without answering"
   - "End session (clarity achieved)" / "I have sufficient clarity now"

**Translation**: Translate all questions, options, labels, and descriptions according to the language specified in your system prompt.

**Step D: Ask User with AskUserQuestion**

Use the `AskUserQuestion` tool:

- **Question**: Your generated contextual question
- **Header**: Use the `dimension_name` field from CLI
- **Options**: Your generated quick answers + standard options (all translated)
- **multiSelect**: false

**User Response Handling:**
- If user selects a quick answer option: Use that as the answer. Proceed to step 2.3.
- If user selects "Other" option: This contains the user's detailed answer. Proceed to step 2.3.
- If user selects "Skip this question": Return to step 2.1-2.2.
- If user selects "End session": Skip to step 3.

#### 2.3. Update Beliefs

Uses Claude-based semantic evaluation for likelihood estimation.

**Step 1: Request Evaluation Context**

```bash
PYTHONPATH="plugins/with-me:${PYTHONPATH:-}" python3 -m with_me.cli.session update \
  --session-id <SESSION_ID> \
  --dimension <DIMENSION> \
  --question <QUESTION> \
  --answer <ANSWER> \
  --enable-semantic-evaluation
```

**Note:** Use the original answer in any language (no translation required).

Output (evaluation request):
```json
{
  "evaluation_request": true,
  "dimension": "purpose",
  "dimension_name": "Purpose",
  "hypotheses": [
    {
      "id": "web_app",
      "name": "Web Application",
      "description": "Browser-based applications with user interfaces...",
      "focus_areas": ["user interface design...", ...]
    },
    ...
  ],
  "question": "What problem are you trying to solve?",
  "answer": "新機能の開発",
  "instruction": "Based on the question and answer, estimate the likelihood..."
}
```

**Step 2: Perform Semantic Evaluation**

Read the evaluation request and estimate likelihoods based on:
- Hypothesis descriptions
- Focus areas
- Question-answer alignment
- Semantic understanding

Return likelihoods as JSON:
```json
{
  "likelihoods": {
    "web_app": 0.35,
    "cli_tool": 0.40,
    "library": 0.15,
    "service": 0.10
  }
}
```

**Step 3: Update Beliefs with Likelihoods**

```bash
PYTHONPATH="plugins/with-me:${PYTHONPATH:-}" python3 -m with_me.cli.session update \
  --session-id <SESSION_ID> \
  --dimension <DIMENSION> \
  --question <QUESTION> \
  --answer <ANSWER> \
  --likelihoods '{"web_app": 0.35, "cli_tool": 0.40, "library": 0.15, "service": 0.10}'
```

Output:
```json
{
  "information_gain": 0.08,
  "entropy_before": 2.0,
  "entropy_after": 1.92,
  "dimension": "purpose"
}
```

**Benefits of Semantic Evaluation:**
- Context-aware understanding
- Works with any language
- Higher information gain for natural responses
- No keyword dependency

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
