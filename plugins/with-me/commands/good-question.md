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

5. **Never Insert Mid-Session Check-ins**
   - Do NOT pause to ask "shall we continue or proceed to requirements analysis?"
   - Continue the loop automatically until `next-question` returns `"converged": true`
   - The only early-exit path is the user selecting "End session (clarity achieved)" from a question's options
   - Violating this rule causes unsolicited interruptions and breaks the convergence contract with the CLI

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

Store the returned `session_id`. Use it as both `SESSION_ID` and `FEEDBACK_SESSION_ID` — feedback tracking is initialized automatically. Do NOT show output to user.

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
- `epistemic_entropy`, `aleatoric_entropy`, `epistemic_ratio`: BALD decomposition (internal use — epistemic = reducible uncertainty)
- `suggested_secondary_dimensions`: Dimensions that would benefit from cross-dimension updates based on presheaf restriction maps. Each entry has `dimension`, `score`, and `hypotheses`.
- `question_phase`: Current phase for this dimension: `"explore"`, `"discriminate"`, `"specify"`, `"validate"`, or `"clarify"`.
- `dominant_hypothesis`, `dominant_probability`: Highest-posterior hypothesis and its probability.
- `question_guidelines`: Phase-keyed guidance strings from dimension config.
- `uncovered_focus_areas`: Focus areas of the dominant hypothesis not yet addressed.
- `suggested_focus_area`: First uncovered focus area (null if all covered); use as primary target in specify phase.
- `clarification_needed`: Whether this dimension has a detected contradiction requiring resolution.

**IMPORTANT:** Do NOT mention dimension names or technical terms to the user.

**Conversational flow transitions:** Before generating the question, check if the dimension has changed from the previous question. If so:
1. **Acknowledge the previous answer**: Briefly summarize what you learned (e.g., "Thanks, that clarifies the data format.")
2. **Use transition template**: Read the `transition_templates` from the dimension config. Use `"entry"` when entering a dimension for the first time, or `"from_other"` when returning to a previously visited dimension. Adapt the template naturally — do not use it verbatim.
3. **Pacing rule**: Track consecutive questions on the same dimension. If you have asked `max_consecutive_same_dimension` (default: 3) questions on the same dimension without switching, force a switch to another accessible dimension even if the current one has higher entropy.

If the dimension has NOT changed, still acknowledge the previous answer briefly before asking the next question.

#### 2.2. Generate and Ask Question

**Generate question:**

**Question strategy by phase** (use `question_phase` from Step 2.1):

- **`"explore"`**: Use dimension-level `focus_areas` to ask a broad categorical question.
  Map the landscape without assuming a direction. Answer options should cover all hypotheses.

- **`"discriminate"`**: Target the top-2 hypotheses by `posterior`. Generate a question
  where different plausible answers map cleanly to different hypotheses.

- **`"specify"`**: The dominant hypothesis (`dominant_hypothesis` at `dominant_probability`)
  is established. Switch to implementation details:
  1. Use `question_guidelines.specify` for dimension-specific guidance.
  2. Use `uncovered_focus_areas` from CLI output (already filtered against prior questions).
     If `suggested_focus_area` is non-null, use it as the primary target.
     If null (all covered), ask about cross-dimension consistency or deployment edge cases.
  3. Ask about the most important uncovered detail not yet addressed.

- **`"validate"`**: The dominant hypothesis is highly confident. Ask about edge cases,
  failure modes, or cross-dimension consistency using `question_guidelines.validate`.

- **`"clarify"`**: A significant contradiction was detected (negative IG on previous update).
  1. Review the conversation history for the two most recent conflicting answers on this dimension.
  2. Use `question_guidelines.clarify` for dimension-specific guidance.
  3. Generate a question that explicitly names the contradiction and asks the user to confirm
     which answer is correct. Do NOT introduce new topics.

Use `question_guidelines[question_phase]` from Step 2.1 output as the primary guideline.

**CRITICAL: Avoid duplicate questions.** Do NOT ask questions that have already been answered or cover the same semantic intent as `recent_questions_this_dimension`.

**Ask user:**

**QUESTIONING PHASE:** Now you ask the actual question. This is NOT evaluation - wait for the user's actual response.

**Cognitive load constraints:** Check `max_options` from dimension config (default: 5, never exceed 7 per Miller's 7±2 rule). Adjust by `disclosure_layer`:
- `"overview"`: 2-3 choices
- `"detail"`: 3-4 choices
- `"edge_case"`: up to `max_options`

Generate exactly the number of content options allowed by the cognitive load constraint.
**Do NOT add "Skip" or "End session" as explicit options.** These are handled via the built-in free-text input ("Type something").
When the user submits free text, first determine intent before proceeding:
- **Skip intent**: the response does not answer the question but instead expresses intent to skip, defer, or pass (e.g., "skip", "undecided", "N/A", or any equivalent in any language)
  - Honored when `question_count` ≥ 5 AND `recent_questions_this_dimension` is non-empty
  - If honored: **do NOT call `update-with-computation`**, return directly to step 2.1
  - If not honored (conditions unmet): acknowledge and ask them to choose a content option
- **End session intent**: the response expresses that the user has sufficient clarity and wants to stop (e.g., "done", "enough", "end", or equivalent)
  - Honored when `question_count` ≥ 20
  - If honored: skip to step 3
  - If not honored: acknowledge and ask them to choose a content option
- **Substantive answer**: anything else — proceed to step 2.3

Translate all content options to the language specified in your system prompt.

**CRITICAL:** You MUST invoke the AskUserQuestion tool now. Do NOT skip this step. Do NOT use evaluation templates as answers.

**⚠ MANDATORY TOOL CALL — NO EXCEPTIONS:**
Step 2.2 is ONLY complete when AskUserQuestion has been called and the user has responded.
- You may NOT proceed to step 2.3 without calling AskUserQuestion first.
- You may NOT answer on behalf of the user.
- If you have already written your question text, call AskUserQuestion NOW.

**Multi-select support:** Check `supports_multi_select` from CLI output (Step 2.1):
- If `true`: Use "Select all that apply" phrasing with `multiSelect: true`
- If `false`: Use single-selection phrasing with `multiSelect: false`

Ask user using `AskUserQuestion`:
- Question: Your evaluated question (adjusted for multi-select if applicable)
- Header: Use `dimension_name` from CLI
- Options: Content options only (translated), no Skip/End session
- multiSelect: Based on `supports_multi_select`

Wait for the user's actual response. Do NOT proceed until the user answers.

Handle user response:
- Selected option or substantive free-text answer: Proceed to step 2.3
- Free-text with skip/end intent: Apply intent detection rules above
- "Chat about this": Treat as substantive answer, proceed to step 2.3

#### 2.3. Update Beliefs

**Estimate Posterior:**

**CRITICAL: Handle reference materials properly.** If the user provides reference materials (URLs, file paths, documentation links) instead of a direct answer, retrieve and analyze them before estimating.

Based on the user's answer and all previous answers, estimate the current posterior P(h | all evidence) for each hypothesis.

State your confidence in this estimate (0.0-1.0):
- 0.8-1.0: Clear, unambiguous answer directly identifying a hypothesis
- 0.5-0.7: Moderate evidence, suggestive but not definitive
- 0.3-0.5: Ambiguous answer, multiple hypotheses still plausible

**Multi-select:** Incorporate all selected answers into a single posterior estimate.

**Secondary dimension identification (strongly recommended):** Use `suggested_secondary_dimensions` from Step 2.1. For each suggested dimension with score > 0.5, estimate posterior if the answer provides relevant evidence.

- Store as `SECONDARY_DIMS` (comma-separated) and `SECONDARY_POSTERIORS` (JSON object mapping dim_id to posterior dict)

Posterior format: `'{"hyp1": 0.x, "hyp2": 0.y, ...}'` (must sum to 1.0)

**Update and Persist:**

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.session update-with-computation \
  --session-id <SESSION_ID> \
  --feedback-session-id "$FEEDBACK_SESSION_ID" \
  --dimension <DIMENSION> \
  --question <QUESTION> \
  --answer <ANSWER> \
  --posterior "$POSTERIOR" \
  --confidence <CONFIDENCE>
```

Additional flags when secondary dimensions identified:
- `--secondary-dimensions "dim1,dim2"`
- `--secondary-posteriors '{"dim1": {"h1": 0.x, ...}, "dim2": {"h1": 0.y, ...}}'`

If `question_phase` was `"specify"` or `"validate"` and you targeted a specific focus area
from `uncovered_focus_areas`, add:
- `--targeted-focus-area "<focus_area_string>"`
  (Use the exact string from `uncovered_focus_areas`, not a paraphrase)

Notes:
- `--answer`: For multi-select, combine all selected answers into a single string (e.g., "Answer1; Answer2; Answer3")
- `--confidence`: 0.8+ for clear answers, 0.5-0.7 for moderate, 0.3-0.5 for ambiguous
- If `low_ig: true` in response: next question should more directly distinguish the top-2 posterior hypotheses by name
- Feedback is recorded automatically by this command. Do NOT call `feedback record` separately.

Do NOT show output to the user.

**Negative Information Gain (IG < 0):**

If `information_gain` is negative, uncertainty increased rather than decreased. Two possible causes:

1. **Estimation error**: Your P(answer | hypothesis) estimates contradicted previous answers. Review likelihood values for logical consistency with the full answer history.
2. **Genuine conflict**: User's answer genuinely contradicts prior responses. This is valid — the system correctly reflects the conflict.

If `information_gain` is significantly negative (< -0.05):
- The CLI has set `clarification_needed` for this dimension.
- The next iteration will automatically use `question_phase: "clarify"`.
- No special action needed here — continue to step 2.4.

If `information_gain` is slightly negative (≥ -0.05 and < 0):
- Treat as noise. Continue normally.

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

Read the final session beliefs using the Read tool:
- Path: `.claude/with_me/sessions/<SESSION_ID>.json`
- Extract the `beliefs` field and store as `FINAL_BELIEFS` (the full JSON object)

Complete feedback session with all 7 dimension entropy values and final beliefs:

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.cli.feedback complete <FEEDBACK_SESSION_ID> \
  '{"purpose": <E>, "context": <E>, "data": <E>, "behavior": <E>, "stakeholders": <E>, "constraints": <E>, "quality": <E>}' \
  "$FINAL_BELIEFS"
```

Entropy values are available from the session status output. `FINAL_BELIEFS` is the `beliefs` object read from the session file.

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
- **prerequisite_threshold_default**: KST gate threshold (default: 1.8)
- **update_weight**: Base weight for posterior updates (default: 3.0)
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
