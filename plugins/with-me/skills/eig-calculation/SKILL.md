---
description: "Calculate Expected Information Gain (EIG) for questions using Bayesian belief updating"
context: fork
allowed-tools: [Read, Skill]
---

# Expected Information Gain (EIG) Calculation

Calculate EIG to measure the expected uncertainty reduction from asking a question.

---

## When to Use This Skill

Use this skill to calculate EIG when:
- Evaluating question effectiveness before asking
- Ranking multiple candidate questions
- Calculating reward scores for reinforcement learning

**Do not use this skill:**
- For entropy calculation only (use `/with-me:entropy`)
- For single Bayesian update (use `/with-me:bayesian-update`)

---

# Expected Information Gain (EIG) Calculation

Measure expected uncertainty reduction from asking a question.

## Concept

**Expected Information Gain (EIG)** quantifies how much a question is expected to reduce uncertainty, accounting for all plausible answers and their probabilities.

Unlike simple entropy reduction (which measures actual reduction after getting an answer), EIG predicts reduction **before** asking, enabling proactive question selection.

## Formula

```
EIG(Q) = Σ_a P(a|Q) × [H_before - H_after(a)]

Where:
- Q: Question
- a: Possible answer
- P(a|Q): Probability of answer a given question Q
- H_before: Entropy before asking
- H_after(a): Entropy after receiving answer a
```

## Algorithm

**Input:**
- question: Question text
- current_beliefs: Current posterior distribution over hypotheses
- answer_templates: List of (answer_text, probability) tuples

**Steps:**

1. **Calculate H_before:**
   - Use `/with-me:entropy` skill with current_beliefs
   - Store as H_before

2. **For each answer template (answer_text, prob):**

   a. **Simulate belief update:**
      - Create copy of current_beliefs
      - Estimate likelihoods P(answer|hypothesis) for each hypothesis
      - Use `/with-me:bayesian-update` to compute posterior
      - Use `/with-me:entropy` to calculate H_after

   b. **Calculate information gain for this answer:**
      - IG_a = H_before - H_after

   c. **Weight by answer probability:**
      - Weighted_IG_a = prob × IG_a

3. **Sum weighted information gains:**
   - EIG = Σ Weighted_IG_a

4. **Return EIG**

**Output:** Expected information gain in bits

## Answer Template Generation

To calculate EIG, we need plausible answer templates with probabilities. These vary by:

### Question Specificity

**Specific questions** → Concentrated answer distribution → Higher EIG

Example: "Which type: web app or CLI?"
- Answer probabilities: [0.6, 0.35, 0.05] (sharply peaked)
- Higher EIG

**Vague questions** → Uniform answer distribution → Lower EIG

Example: "What about the purpose?"
- Answer probabilities: [0.25, 0.25, 0.25, 0.25] (uniform)
- Lower EIG

### Dimension-Specific Templates

**Purpose dimension:**
- "web application for users" (0.25)
- "command-line tool for automation" (0.25)
- "library for developers" (0.25)
- "background service for processing" (0.25)

**Data dimension:**
- "structured JSON or XML data" (0.3)
- "unstructured text documents" (0.3)
- "streaming real-time data" (0.2)
- "binary files or blobs" (0.2)

**Behavior dimension:**
- "synchronous request-response" (0.3)
- "asynchronous event-driven" (0.3)
- "interactive user sessions" (0.2)
- "batch processing jobs" (0.2)

## Examples

### Example 1: Specific question (high EIG)

**Input:**
- Question: "Which specific type: web app or CLI tool?"
- Current beliefs (uniform prior):
  ```json
  {
    "web_app": 0.25,
    "cli_tool": 0.25,
    "library": 0.25,
    "service": 0.25
  }
  ```

**Step 1: Calculate H_before**

Use `/with-me:entropy` skill:

H_before = -0.25×log₂(0.25) - 0.25×log₂(0.25) - 0.25×log₂(0.25) - 0.25×log₂(0.25)
        = -4 × 0.25 × (-2)
        = 2.0 bits

**Step 2: Generate answer templates (specific question)**

Sharpened distribution:
- "web application" → 0.60
- "command-line tool" → 0.30
- "library" → 0.08
- "service" → 0.02

**Step 3: Calculate EIG**

**For answer "web application" (prob = 0.60):**

Likelihoods P(answer|hypothesis):
- web_app: 0.95
- cli_tool: 0.02
- library: 0.02
- service: 0.01

Bayesian update:
```
Unnormalized:
- web_app: 0.25 × 0.95 = 0.2375
- cli_tool: 0.25 × 0.02 = 0.005
- library: 0.25 × 0.02 = 0.005
- service: 0.25 × 0.01 = 0.0025

Total = 0.25

Normalized posterior:
- web_app: 0.95
- cli_tool: 0.02
- library: 0.02
- service: 0.01
```

H_after = -0.95×log₂(0.95) - 0.02×log₂(0.02) - 0.02×log₂(0.02) - 0.01×log₂(0.01)
        ≈ -0.95×(-0.074) - 0.02×(-5.644) - 0.02×(-5.644) - 0.01×(-6.644)
        ≈ 0.070 + 0.113 + 0.113 + 0.066
        ≈ 0.362 bits

IG = H_before - H_after = 2.0 - 0.362 = 1.638 bits

Weighted: 0.60 × 1.638 = 0.983 bits

**For answer "CLI tool" (prob = 0.30):**

Similar calculation → IG ≈ 1.5 bits → Weighted: 0.30 × 1.5 = 0.45 bits

**For other answers (prob = 0.10 combined):**

Weighted: ~0.15 bits

**Total EIG:**

EIG = 0.983 + 0.45 + 0.15 ≈ **1.58 bits**

### Example 2: Vague question (low EIG)

**Input:**
- Question: "What about the purpose?"
- Same current beliefs (uniform prior)

**Step 1: H_before = 2.0 bits** (same as above)

**Step 2: Generate answer templates (vague question)**

Uniform distribution (answers are dispersed):
- "web application" → 0.25
- "CLI tool" → 0.25
- "library" → 0.25
- "service" → 0.25

**Step 3: Calculate EIG**

With uniform answer probabilities and less confident likelihoods:

**For each answer (prob = 0.25):**
- IG ≈ 0.8 bits (less confident updates)
- Weighted: 0.25 × 0.8 = 0.2 bits

**Total EIG:**

EIG = 4 × 0.2 ≈ **0.8 bits**

**Comparison:**
- Specific question: 1.58 bits
- Vague question: 0.8 bits
- **Ratio: 1.98× higher EIG for specific question**

### Example 3: Off-topic question (zero EIG)

**Input:**
- Question: "Tell me a joke"
- Current beliefs: (any)

**Analysis:**
- Question doesn't target any requirement dimension
- No relevant information gain expected
- All answer templates have zero probability

**Output:** EIG = 0.0 bits

## Dimension Targeting

Questions must target a specific dimension to have positive EIG:

| Dimension   | Keywords                                      |
|-------------|-----------------------------------------------|
| Purpose     | why, purpose, goal, problem, need             |
| Data        | what data, input, output, information, store  |
| Behavior    | how, step, process, flow, happen, work        |
| Constraints | constraint, limit, requirement, performance   |
| Quality     | test, success, quality, fail, edge case       |

**If no dimension matches:** EIG = 0.0

## Practical Simplifications

For computational efficiency, use representative answer samples:

**Sample size:**
- 4-5 answer templates per dimension
- Cover diverse hypothesis support
- Probabilities sum to 1.0

**Likelihood estimation:**
- Use semantic similarity between answer and hypothesis
- Or use heuristic rules based on keywords
- Or invoke Claude for semantic evaluation

## Use Cases

### Question Selection

Choose question with highest EIG:

```
best_question = argmax_Q EIG(Q)
```

### Question Ranking

Sort candidate questions by EIG:

```
ranked = sort(questions, key=lambda q: EIG(q), reverse=True)
```

### Hybrid Reward Function

Combine EIG with quality factors:

```
reward = EIG + 0.1 × clarity + 0.05 × importance
```

## Implementation Notes

**Python Example (for reference only - Claude performs calculation):**

```python
def calculate_eig(question, beliefs, answer_templates):
    # 1. Calculate H_before
    h_before = calculate_entropy(beliefs)  # Use /with-me:entropy

    # 2. Sum over answer templates
    eig = 0.0
    for answer_text, prob in answer_templates:
        # Simulate belief update
        likelihoods = estimate_likelihoods(answer_text, beliefs)
        posterior = bayesian_update(beliefs, likelihoods)  # Use /with-me:bayesian-update
        h_after = calculate_entropy(posterior)  # Use /with-me:entropy

        # Weight by probability
        ig = h_before - h_after
        eig += prob * ig

    return eig
```

## Comparison with Simple IG

**Information Gain (IG):** Measures actual reduction after getting an answer
- Calculated: **After** asking question
- Formula: IG = H_before - H_after
- Use: Evaluate question effectiveness post-hoc

**Expected Information Gain (EIG):** Measures expected reduction before asking
- Calculated: **Before** asking question
- Formula: EIG = Σ P(a|Q) × [H_before - H_after(a)]
- Use: Select best question proactively

**Relationship:** EIG = E[IG] (expectation over answers)
