---
description: "Calculate strategic importance of questions based on target dimension"
context: fork
allowed-tools: [Read]
---

# Question Importance Calculation

Assign strategic importance scores to questions based on requirement dimension hierarchy.

---

## When to Use This Skill

Use this skill to calculate importance when:
- Prioritizing questions in requirement elicitation
- Calculating hybrid reward scores
- Designing adaptive questioning strategies

**Do not use this skill:**
- For question clarity evaluation (use `/with-me:question-clarity`)
- For information gain calculation (use `/with-me:entropy`)

---

# Question Importance Calculation

Calculate strategic importance of questions based on target dimension.

## Concept

Some requirement dimensions are inherently more important than others in software development:

- **Purpose**: Why does this exist? (Most critical)
- **Behavior**: How does it work?
- **Data**: What information flows through it?
- **Constraints**: What limits or requirements apply?
- **Quality**: How do we ensure it works correctly?

Questions targeting high-priority dimensions receive higher importance scores.

## Dimension Importance Hierarchy

### Priority Ranking

1. **Purpose** (1.0): Most important
   - Defines project goals and raison d'être
   - Must be understood before other dimensions
   - Keywords: "why", "purpose", "goal", "problem", "need"

2. **Behavior** (0.8): Very important
   - Defines system operation and functionality
   - Critical for architecture decisions
   - Keywords: "how", "step", "process", "flow", "happen", "work"

3. **Data** (0.7): Important
   - Defines information structures and flow
   - Affects design choices
   - Keywords: "what data", "input", "output", "information", "store"

4. **Constraints** (0.6): Moderately important
   - Defines system boundaries and requirements
   - Influences technical decisions
   - Keywords: "constraint", "limit", "requirement", "performance", "scale"

5. **Quality** (0.5): Baseline importance
   - Defines testing and success criteria
   - Important but often derivative
   - Keywords: "test", "success", "quality", "fail", "edge case"

## Algorithm

**Input:** Question text (string)

**Steps:**

1. Extract target dimension from question:
   - Convert question to lowercase
   - Check for dimension keywords (see Keyword Matching section)
   - Return first matching dimension or None

2. Look up importance score from hierarchy:
   - purpose → 1.0
   - behavior → 0.8
   - data → 0.7
   - constraints → 0.6
   - quality → 0.5
   - unspecified → 0.5 (default)

3. Return importance score

**Output:** Importance score in [0.0, 1.0]

## Keyword Matching

### Purpose Dimension

**Keywords:** why, purpose, goal, problem, need, motivation, reason

**Examples:**
- "Why is this needed?"
- "What is the purpose?"
- "What problem does this solve?"
- "What is the main goal?"

**Output:** 1.0

### Behavior Dimension

**Keywords:** how, step, process, flow, happen, work, execute, operate

**Examples:**
- "How does it work?"
- "What steps are involved?"
- "What is the process?"
- "How will it execute?"

**Output:** 0.8

### Data Dimension

**Keywords:** what data, input, output, information, store, format, structure

**Examples:**
- "What data is involved?"
- "What are the inputs?"
- "What information is needed?"
- "How is data stored?"

**Output:** 0.7

### Constraints Dimension

**Keywords:** constraint, limit, requirement, performance, scale, throughput, latency

**Examples:**
- "What are the constraints?"
- "What are the performance requirements?"
- "How should it scale?"
- "What are the limits?"

**Output:** 0.6

### Quality Dimension

**Keywords:** test, success, quality, fail, edge case, validate, verify

**Examples:**
- "How do we test this?"
- "What defines success?"
- "What edge cases exist?"
- "How do we validate?"

**Output:** 0.5

### Unspecified Dimension

**No matching keywords found.**

**Default:** 0.5

## Examples

### Example 1: Purpose question (highest importance)

**Input:** "Why is this project needed?"

**Analysis:**
- Lowercase: "why is this project needed?"
- Contains "why" → purpose dimension
- Importance: 1.0

**Output:** 1.0

### Example 2: Behavior question (very important)

**Input:** "How does the authentication process work?"

**Analysis:**
- Lowercase: "how does the authentication process work?"
- Contains "how" and "process" → behavior dimension
- Importance: 0.8

**Output:** 0.8

### Example 3: Data question (important)

**Input:** "What data format should we use?"

**Analysis:**
- Lowercase: "what data format should we use?"
- Contains "what data" → data dimension
- Importance: 0.7

**Output:** 0.7

### Example 4: Constraints question (moderately important)

**Input:** "What are the performance requirements?"

**Analysis:**
- Lowercase: "what are the performance requirements?"
- Contains "performance" and "requirement" → constraints dimension
- Importance: 0.6

**Output:** 0.6

### Example 5: Quality question (baseline importance)

**Input:** "How should we test edge cases?"

**Analysis:**
- Lowercase: "how should we test edge cases?"
- Contains "test" and "edge case" → quality dimension
- Importance: 0.5

**Output:** 0.5

### Example 6: Unspecified dimension (default)

**Input:** "Can you explain more?"

**Analysis:**
- Lowercase: "can you explain more?"
- No dimension keywords found
- Default importance: 0.5

**Output:** 0.5

## Multiple Keyword Matches

If question contains keywords from multiple dimensions, **use the first match** in priority order:

1. Check purpose keywords
2. Check behavior keywords
3. Check data keywords
4. Check constraints keywords
5. Check quality keywords
6. Default to 0.5

**Example:**

**Input:** "How does it work and why is it needed?"

**Analysis:**
- Contains "how" (behavior) and "why" (purpose)
- Purpose has higher priority → purpose dimension
- Importance: 1.0

**Output:** 1.0

## Use Cases

### Hybrid Reward Function

Combine with EIG and clarity for question scoring:

```
reward = EIG + 0.1 × clarity + 0.05 × importance
```

**Example:**
- EIG = 1.5 bits
- clarity = 0.9
- importance = 1.0
- reward = 1.5 + 0.1×0.9 + 0.05×1.0 = 1.5 + 0.09 + 0.05 = 1.64

### Question Prioritization

When multiple questions are available, prioritize by importance:

```
Sort questions by: (EIG × importance) descending
```

### Adaptive Questioning

Adjust question selection based on session phase:
- Early phase: Focus on purpose (importance = 1.0)
- Mid phase: Focus on behavior and data (importance = 0.7-0.8)
- Late phase: Focus on constraints and quality (importance = 0.5-0.6)

## Implementation Notes

**Python Example (for reference only - Claude performs calculation):**

```python
def calculate_importance(question: str) -> float:
    q_lower = question.lower()

    # Priority order matching
    if any(kw in q_lower for kw in ["why", "purpose", "goal", "problem", "need"]):
        return 1.0  # purpose
    if any(kw in q_lower for kw in ["how", "step", "process", "flow", "happen", "work"]):
        return 0.8  # behavior
    if any(kw in q_lower for kw in ["what data", "input", "output", "information"]):
        return 0.7  # data
    if any(kw in q_lower for kw in ["constraint", "limit", "requirement", "performance"]):
        return 0.6  # constraints
    if any(kw in q_lower for kw in ["test", "success", "quality", "fail", "edge case"]):
        return 0.5  # quality

    return 0.5  # default
```
