---
description: "Evaluate question clarity using linguistic heuristics"
context: fork
allowed-tools: [Read]
---

# Question Clarity Evaluation

Assess question clarity to improve requirement elicitation quality.

---

## When to Use This Skill

Use this skill to evaluate question clarity when:
- Scoring questions for reward calculation
- Providing feedback on question quality
- Filtering low-quality questions

**Do not use this skill:**
- For semantic analysis (use natural language understanding)
- For domain-specific validation

---

# Question Clarity Evaluation

Evaluate question clarity using linguistic heuristics.

## Scoring Criteria

### Positive Factors (+)

1. **Question mark present**: +0.0 (baseline requirement)
2. **Question word prefix**: +0.1
   - Patterns: "What", "How", "Why", "When", "Where", "Who"
   - Example: "What is the purpose?" scores higher

### Negative Factors (-)

1. **No question mark**: -0.2
   - Example: "Tell me about it" (statement, not question)

2. **Too long (>30 words)**: -0.2
   - Long questions are harder to answer clearly
   - Example: "What is the purpose and also how does it work and what data is needed and..." (poor)

3. **Compound questions**: -0.3
   - Multiple questions in one sentence
   - Patterns: "or", "and", "also" with multiple "?"
   - Example: "What is the purpose? And how does it work?" (poor)
   - Better: Ask separately

4. **Vague language**: -0.1
   - Patterns: "maybe", "perhaps", "might"
   - Example: "Maybe we could use async?" (uncertain)

## Algorithm

**Input:** Question text (string)

**Steps:**
1. Initialize score = 1.0 (perfect clarity baseline)

2. Check negative factors:
   - If no "?" in question: score -= 0.2
   - If word_count > 30: score -= 0.2
   - If compound_question (multiple "?" with conjunctions): score -= 0.3
   - If vague_language ("maybe", "perhaps", "might"): score -= 0.1

3. Check positive factors:
   - If starts with question word: score += 0.1

4. Clamp score to [0.0, 1.0]

5. Return clarity_score

**Output:** Clarity score in [0.0, 1.0]

## Examples

### Example 1: High clarity

**Input:** "What is the main purpose of this project?"

**Analysis:**
- Has question mark: ✓
- Word count = 8 (< 30): ✓
- Starts with "What": +0.1
- No compound question: ✓
- No vague language: ✓

**Calculation:**
- score = 1.0
- score += 0.1 (question word)
- score = min(1.0, 1.1) = 1.0

**Output:** 1.0

### Example 2: Medium clarity

**Input:** "What about the data structures?"

**Analysis:**
- Has question mark: ✓
- Word count = 5 (< 30): ✓
- Starts with "What": +0.1
- No compound question: ✓
- No vague language: ✓

**Calculation:**
- score = 1.0
- score += 0.1 (question word)
- score = 1.0

**Output:** 1.0

### Example 3: Low clarity (no question mark)

**Input:** "Tell me about the architecture"

**Analysis:**
- No question mark: -0.2
- Word count = 5 (< 30): ✓
- No question word prefix: (no bonus)
- No compound question: ✓
- No vague language: ✓

**Calculation:**
- score = 1.0
- score -= 0.2 (no question mark)
- score = 0.8

**Output:** 0.8

### Example 4: Very low clarity (compound + vague)

**Input:** "What is the purpose and maybe how does it work or perhaps what data is needed?"

**Analysis:**
- Has question mark: ✓
- Word count = 16 (< 30): ✓
- Starts with "What": +0.1
- Compound question (or, and with single "?"): -0.3
- Vague language (maybe, perhaps): -0.1

**Calculation:**
- score = 1.0
- score += 0.1 (question word)
- score -= 0.3 (compound)
- score -= 0.1 (vague)
- score = 0.7

**Output:** 0.7

### Example 5: Poor clarity (too long)

**Input:** "What is the main purpose of this project and also can you explain how it works and what are the data structures involved and what dependencies are needed and how should we handle errors and edge cases in production?"

**Analysis:**
- Has question mark: ✓
- Word count = 42 (> 30): -0.2
- Starts with "What": +0.1
- Compound question (multiple topics): -0.3
- No vague language: ✓

**Calculation:**
- score = 1.0
- score += 0.1 (question word)
- score -= 0.2 (too long)
- score -= 0.3 (compound)
- score = 0.6

**Output:** 0.6

## Pattern Matching

### Question Word Detection

**Regex:** `^(What|How|Why|When|Where|Who)\b`

**Case insensitive match at start of sentence.**

### Compound Question Detection

**Regex:** `\b(or|and|also)\b.*\?.*\?`

**Pattern indicates multiple questions joined by conjunctions.**

### Vague Language Detection

**Regex:** `\b(maybe|perhaps|might)\b`

**Case insensitive match anywhere in text.**

## Implementation Notes

**Python Example (for reference only - Claude performs calculation):**

```python
def score_clarity(question: str) -> float:
    score = 1.0

    # Negative factors
    if "?" not in question:
        score -= 0.2
    if len(question.split()) > 30:
        score -= 0.2
    if re.search(r'\b(or|and|also)\b.*\?.*\?', question):
        score -= 0.3
    if re.search(r'\b(maybe|perhaps|might)\b', question, re.IGNORECASE):
        score -= 0.1

    # Positive factors
    if re.match(r'^(What|How|Why|When|Where|Who)\b', question):
        score += 0.1

    return max(0.0, min(1.0, score))
```

## Use Cases

**Reward calculation:**
- Combine with EIG and importance for hybrid reward function
- Weight: typically 0.1 (10% of EIG scale)

**Question filtering:**
- Reject questions below threshold (e.g., < 0.5)
- Provide feedback: "Question is unclear - please be more specific"

**Quality metrics:**
- Track clarity over session
- Identify patterns in poor questions
