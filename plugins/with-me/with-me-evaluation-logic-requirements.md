# With-Me Evaluation Logic Requirements

This document specifies the requirements for the evaluation logic in the with-me plugin, which uses information theory and AI reward functions to guide requirement elicitation through entropy-reducing questions.

## 1. Question Reward Scoring

### 1.1 Composite Reward Function

**Requirement:** The system SHALL calculate question quality using a composite reward function with the following weighted components:

```
r = 0.40*info_gain + 0.20*clarity + 0.15*specificity + 
    0.15*actionability + 0.10*relevance - 0.02*kl_divergence
```

**Rationale:** This weighting prioritizes information acquisition (40%) while balancing clarity, specificity, answerability, and relevance. The KL divergence penalty discourages redundancy.

### 1.2 Information Gain (40% weight)

**Requirement:** Information gain SHALL be calculated differently for pre-evaluation and post-evaluation:

**Pre-evaluation (expected gain):**
- Extract target dimension from question text
- Return uncertainty value of target dimension
- Default to 0.5 if dimension cannot be identified

**Post-evaluation (actual gain):**
- Based on answer word count:
  - \> 50 words → 0.9
  - 20-50 words → 0.7
  - 5-20 words → 0.5
  - < 5 words → 0.2

**Rationale:** Higher uncertainty dimensions offer more information gain potential. Word count correlates with information density in answers.

### 1.3 Clarity (20% weight)

**Requirement:** Clarity SHALL be scored based on question structure:

Starting score: 1.0

**Penalties:**
- -0.2 if no question mark present
- -0.2 if > 30 words (too long)
- -0.3 if compound question (multiple `?` with `or/and/also`)
- -0.1 if vague language (`maybe`, `perhaps`, `might`)

**Bonuses:**
- +0.1 if starts with interrogative (`What`, `How`, `Why`, `When`, `Where`, `Who`)

**Rationale:** Clear, focused questions are easier to answer and yield more precise information.

### 1.4 Specificity (15% weight)

**Requirement:** Specificity SHALL be scored based on concrete vs abstract language:

Base score: 0.5

**Bonuses:**
- +0.2 for `example` keyword
- +0.1 for `specific(ally)` keyword
- +0.2 for dimension keywords (`purpose`, `data`, `behavior`, `constraint`, `quality`)

**Penalties:**
- -0.2 for abstract terms (`generally`, `usually`, `typically`)
- -0.1 for overly broad terms (`any`, `anything`, `everything`)

**Rationale:** Specific questions reduce ambiguity and elicit actionable details.

### 1.5 Actionability (15% weight)

**Requirement:** Actionability SHALL detect questions that are difficult to answer:

**Low actionability (0.3):**
- 2+ technical terms (`algorithm`, `complexity`, `optimization`, `architecture`, `implementation`, `framework`, `library`)

**Reduced actionability (0.4):**
- Premature questions (e.g., asking about `behavior` when `purpose` uncertainty > 0.4)

**Default:** 0.8 (answerable)

**Rationale:** Questions must match the user's current knowledge state. Technical or premature questions block progress.

### 1.6 Context Relevance (10% weight)

**Requirement:** Relevance SHALL prioritize high-uncertainty dimensions:

- Extract target dimension from question
- Score = dimension's uncertainty value
- If dimension uncertainty < 0.3 (already clear): Score × 0.5 (penalty for redundant focus)
- Default: 0.5 if dimension cannot be identified

**Rationale:** Maximize entropy reduction by focusing on the most uncertain aspects.

### 1.7 KL Divergence Penalty (-2% weight)

**Requirement:** KL divergence SHALL detect anomalous or redundant questions:

Anomaly score starts at 0.0, then adds:

**Redundancy detection:**
- +1.0 if word overlap > 80% with any of last 5 questions

**Abnormal length:**
- +0.5 if < 3 words OR > 40 words

**Abnormal question marks:**
- +0.3 if 0 question marks OR > 2 question marks

**Rationale:** Redundant questions waste time; abnormal structure indicates poor question formation.

### 1.8 Dimension Extraction

**Requirement:** The system SHALL identify target dimensions using keyword matching:

| Keywords | Dimension |
|----------|-----------|
| `why`, `purpose`, `goal`, `problem` | purpose |
| `what data`, `input`, `output`, `information` | data |
| `how`, `step`, `process`, `flow`, `happen` | behavior |
| `constraint`, `limit`, `requirement`, `performance` | constraints |
| `test`, `success`, `quality`, `fail`, `edge case` | quality |

**Rationale:** Explicit dimension targeting enables strategic question selection.

---

## 2. Uncertainty Calculation

### 2.1 Dimension Uncertainty (0.0-1.0 scale)

**Requirement:** Each dimension's uncertainty SHALL be calculated as follows:

**If `answered: false`:**
- Return 1.0 (maximum uncertainty)

**If `answered: true`:**
- Start with base uncertainty: 0.7
- Apply content detail reduction:
  - \> 50 words: -0.5
  - 20-50 words: -0.4
  - 5-20 words: -0.2
- Apply examples reduction: -0.1 per example (max -0.2)
- Apply contradiction penalty: +0.4 if contradictions detected
- Apply vagueness penalty: +0.2 if answer contains "not sure", "maybe", "unclear", "don't know"
- Clamp result to [0.0, 1.0]

**Rationale:** Detailed, example-rich answers indicate clarity. Contradictions and vague language indicate remaining uncertainty.

### 2.2 Information Gain Between States

**Requirement:** Information gain SHALL be calculated as average uncertainty reduction:

```
info_gain = avg(before_uncertainties) - avg(after_uncertainties)
```

**Rationale:** Simple metric for measuring progress across all dimensions.

### 2.3 Convergence Detection

**Requirement:** The system SHALL recommend continuing questions when:

```
any(uncertainty > threshold) where threshold = 0.3 (default)
```

**Requirement:** The system SHALL identify the next focus dimension as:

```
argmax(uncertainties)
```

**Rationale:** 0.3 threshold represents 70% certainty, sufficient for implementation. Focus on highest uncertainty maximizes information gain.

---

## 3. DAG Dependency Logic

### 3.1 Dimension Dependencies

**Requirement:** The system SHALL enforce prerequisite relationships between dimensions:

```
Purpose (no prerequisites)
├── Data (requires: Purpose < 0.4)
├── Behavior (requires: Purpose < 0.4)
    ├── Constraints (requires: Behavior < 0.4 AND Data < 0.4)
    └── Quality (requires: Behavior < 0.4)
```

**Rationale:** Logical ordering prevents premature questions. Cannot define data/behavior without understanding purpose; cannot define constraints without understanding behavior and data.

### 3.2 Dimension Selection Algorithm

**Requirement:** When selecting the next dimension to question, the system SHALL:

1. **Filter by prerequisites:** For each dimension, check if all prerequisite dimensions have uncertainty < 0.4 (sufficiently clear)
2. **Select highest uncertainty:** Among dimensions passing prerequisite check, select the one with maximum uncertainty
3. **Fallback:** If no dimensions pass prerequisite check, force-select `purpose` (foundation dimension)

```python
def can_ask_dimension(dim, uncertainties):
    prerequisites = {
        "purpose": [],
        "data": ["purpose"],
        "behavior": ["purpose"],
        "constraints": ["behavior", "data"],
        "quality": ["behavior"]
    }
    
    for prereq in prerequisites[dim]:
        if uncertainties[prereq] > 0.4:
            return False
    return True

askable_dims = {
    dim: unc 
    for dim, unc in uncertainties.items() 
    if can_ask_dimension(dim, uncertainties)
}

next_dimension = max(askable_dims, key=askable_dims.get)
```

**Rationale:** DAG structure ensures logical information flow and prevents circular dependencies.

---

## 4. Interview Protocol Integration

### 4.1 Session Tracking

**Requirement:** The system SHALL track question-answer pairs with:

- Session ID (ISO timestamp)
- Question text
- Target dimension
- Uncertainties before question
- Uncertainties after answer
- Answer text
- Answer word count
- Answer has examples (boolean)
- Calculated reward scores (all components)

**Rationale:** Complete data enables statistical learning and continuous improvement.

### 4.2 Recording Timing

**Requirement:** Question recording SHALL occur immediately after receiving the user's answer, using:

```bash
python3 -m with_me.commands.session record \
  "$SESSION_ID" \
  "$QUESTION_TEXT" \
  "$CONTEXT_JSON" \
  "$ANSWER_JSON"
```

With `run_in_background: true` to prevent blocking the interview flow.

**Rationale:** Real-time recording ensures data completeness and prevents memory errors.

### 4.3 Content Language Normalization

**Requirement:** Before uncertainty calculation, all `content` fields SHALL be translated to English if in another language.

**Rationale:** Word count heuristics only work correctly with English text. Japanese text has different word segmentation characteristics that would produce incorrect word counts.

**Example:**
- Japanese: "機微情報漏洩防止、配信者一般向け、リスクと価値提案が明確" (1 "word" in naive split)
- English: "Prevent sensitive information leakage, for general streamers, risks and value proposition are clear" (12 words)

### 4.4 Multi-Stage Interview Structure

**Requirement:** The interview SHALL proceed through distinct phases:

1. **Phase 0 (Optional):** Reference collection
2. **Phase 1:** Initial assessment (1 open question)
3. **Phase 2-1:** Initial survey (5 lightweight questions, one per dimension)
4. **Phase 2-2:** DAG-based deep dive (targeted questions following DAG order)
5. **Phase 2-3:** Contradiction resolution
6. **Phase 3:** Convergence detection (all dimensions < 0.3)
7. **Phase 4:** Validation & gap analysis
8. **Phase 4.5:** Recording verification
9. **Phase 5:** Analysis with `requirement-analysis` skill

**Rationale:** Structured approach guarantees completeness (2-1), efficiency (2-2 with DAG), and data quality (4.5).

---

## 5. Statistical Learning

### 5.1 Session Summary Generation

**Requirement:** Upon session completion, the system SHALL generate:

- Total questions asked
- Average reward score
- Total information gain (sum of per-question reductions)
- Dimensions resolved (count of dimensions reaching < 0.3)
- Session efficiency (info_gain / questions)

**Rationale:** Metrics enable comparison of different questioning strategies.

### 5.2 Historical Pattern Analysis

**Requirement:** The `/with-me:stats` command SHALL display:

- Total sessions and questions
- Best performing question patterns (highest reward scores)
- Dimension-specific statistics (avg info gain per dimension)
- Recent session summaries

**Rationale:** Historical data guides future question selection toward proven patterns.

---

## 6. Quality Thresholds

### 6.1 Question Pre-Evaluation

**Requirement:** Before asking a question, the system SHOULD evaluate it:

- `total_reward > 0.7`: High quality, proceed
- `0.5 < total_reward ≤ 0.7`: Acceptable, consider refinement
- `total_reward ≤ 0.5`: Low quality, rephrase

**Rationale:** Proactive quality control improves interview efficiency.

### 6.2 Convergence Threshold

**Requirement:** The system SHALL use:

- **Dimension clarity threshold:** 0.3 (70% certain)
- **Continue questioning if:** any dimension > 0.3
- **Average certainty for validation:** < 0.25 (75% certain overall)

**Rationale:** Balances thoroughness with practicality. 70% certainty is sufficient for implementation planning.

---

## 7. Data Persistence

### 7.1 Storage Location

**Requirement:** All session data SHALL be stored in:

```
~/.claude/with_me/question_feedback.json
```

**Schema:**
```json
{
  "sessions": [
    {
      "session_id": "2024-01-19T10:30:00.000Z",
      "questions": [
        {
          "question": "...",
          "dimension": "purpose",
          "context": {...},
          "answer": {...},
          "reward_scores": {...}
        }
      ],
      "summary": {
        "total_questions": 12,
        "avg_reward": 0.73,
        "total_info_gain": 3.2,
        "dimensions_resolved": 5,
        "session_efficiency": 0.27
      }
    }
  ],
  "statistics": {
    "total_sessions": 45,
    "total_questions": 523,
    "avg_questions_per_session": 11.6,
    "best_questions": [...]
  }
}
```

### 7.2 Atomic Writes

**Requirement:** File updates SHALL use atomic write operations (temp file + rename) to prevent corruption.

**Rationale:** Prevents data loss if process is interrupted during write.

---

## 8. Error Handling

### 8.1 Missing Prerequisites

**Requirement:** If user jumps to an advanced dimension before prerequisites are clear, the system SHALL:

1. Detect prerequisite violation using `can_ask_dimension()`
2. Explain the dependency (e.g., "We need to clarify Purpose before discussing Constraints")
3. Redirect to the prerequisite dimension

**Rationale:** Prevents logical inconsistencies and wasted questions.

### 8.2 Stuck Dimensions

**Requirement:** If a dimension remains > 0.3 after 3+ questions:

1. Acknowledge user may not know the answer
2. Document the assumption/uncertainty in the specification
3. Proceed with validation

**Rationale:** Some dimensions may be genuinely unclear to the user. Infinite loops are unacceptable.

---

## 9. Non-Functional Requirements

### 9.1 Performance

**Requirement:** Reward calculation and uncertainty assessment SHALL complete in < 100ms per question.

**Rationale:** Real-time feedback during interviews requires fast computation.

### 9.2 Privacy

**Requirement:** All data SHALL remain local. No network calls SHALL be made by evaluation logic.

**Rationale:** Consistent with plugin privacy-by-design principles.

### 9.3 Testability

**Requirement:** All calculation functions SHALL include doctest examples.

**Rationale:** Enables lightweight verification without external test frameworks.

---

## 10. Future Enhancements (Non-Required)

These are design notes for potential improvements, NOT current requirements:

### 10.1 Adaptive Weights

**Future:** Machine learning could tune reward function weights based on historical performance.

### 10.2 Multi-Language Support

**Future:** Native support for non-English content without translation requirement.

### 10.3 Real-Time Dashboard

**Future:** Live visualization of uncertainty reduction during interviews.

---

## Revision History

- **2024-01-19:** Initial requirements document based on implemented behavior in with-me v1.0
