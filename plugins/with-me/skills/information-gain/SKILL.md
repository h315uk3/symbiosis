---
description: "Calculate information gain to measure uncertainty reduction from observations"
context: fork
allowed-tools: [Read]
---

# Information Gain Calculation

Measure uncertainty reduction from question-answer observations.

---

## When to Use This Skill

Use this skill to calculate information gain IG = H_before - H_after when:
- Measuring effectiveness of questions in requirement elicitation
- Evaluating how much uncertainty was reduced by an observation
- Computing reward scores for question evaluation

**Do not use this skill:**
- For entropy calculation itself (use `/with-me:entropy`)
- For Expected Information Gain (EIG) prediction (not yet implemented)

---

## Formula

IG = H_before - H_after

Where:
- H_before: Shannon entropy before observation
- H_after: Shannon entropy after Bayesian update
- IG: Information gained (in bits)

---

## Algorithm

**Input:**
- entropy_before: Entropy of prior distribution (float)
- entropy_after: Entropy of posterior distribution (float)

**Steps:**
1. Calculate information_gain = entropy_before - entropy_after
2. Return information_gain

**Output:** Information gain in bits (float, can be rounded to 4 decimal places)

---

## Interpretation

- **IG > 0:** Uncertainty reduced (typical case)
- **IG = 0:** No information gained (observation didn't discriminate between hypotheses)
- **IG < 0:** Should not occur (violates information theory, indicates calculation error)

---

## Examples

### Example 1: Strong evidence

**Given:** Uniform prior becomes concentrated after observation

**Input:**
- entropy_before: 2.0000 bits (uniform over 4 hypotheses)
- entropy_after: 1.1568 bits (concentrated: {0.7, 0.2, 0.1, 0.0})

**Calculation:**
- IG = 2.0000 - 1.1568 = 0.8432

**Output:** 0.8432 bits

**Interpretation:** Question reduced uncertainty by 42% (0.8432 / 2.0)

### Example 2: Complete resolution

**Given:** Distribution becomes certain

**Input:**
- entropy_before: 1.5850 bits (distribution: {0.33, 0.33, 0.34})
- entropy_after: 0.0000 bits (certain: {1.0, 0.0, 0.0})

**Calculation:**
- IG = 1.5850 - 0.0000 = 1.5850

**Output:** 1.5850 bits

**Interpretation:** Complete uncertainty elimination (100%)

### Example 3: Weak evidence

**Given:** Small change in distribution

**Input:**
- entropy_before: 1.5000 bits
- entropy_after: 1.4500 bits

**Calculation:**
- IG = 1.5000 - 1.4500 = 0.0500

**Output:** 0.0500 bits

**Interpretation:** Minimal uncertainty reduction (3.3%)

### Example 4: No information

**Given:** Distribution unchanged

**Input:**
- entropy_before: 1.8000 bits
- entropy_after: 1.8000 bits

**Calculation:**
- IG = 1.8000 - 1.8000 = 0.0000

**Output:** 0.0000 bits

**Interpretation:** Question provided no discriminatory information

---

## Relationship to Entropy

**Maximum possible information gain:**
- IG_max = H_before (when H_after = 0, complete certainty achieved)

**Percentage uncertainty reduction:**
- Reduction% = (IG / H_before) × 100%

**Example:**
- H_before = 2.0 bits
- H_after = 1.0 bits
- IG = 1.0 bits
- Reduction = (1.0 / 2.0) × 100% = 50%

---

## Properties

- **Non-negative:** IG ≥ 0 (information never lost in Bayesian update)
- **Upper bound:** IG ≤ H_before (cannot reduce more uncertainty than exists)
- **Additive:** Total IG over sequence of questions = Σ IG_i
- **Unit:** bits (consistent with entropy measurement)

---

## Use in Question Selection

**High information gain indicates:**
- Question effectively discriminated between hypotheses
- Good question design
- Observation aligned with hypothesis predictions

**Low information gain indicates:**
- Question didn't help narrow down possibilities
- Observation consistent with all hypotheses equally
- May need different question strategy

**Expected Information Gain (EIG):**
- Can predict IG before asking question
- EIG = Σ p(answer) × IG(answer) over possible answers
- Used for optimal question selection

---

## References

- Shannon (1948): A Mathematical Theory of Communication
- MacKay (2003): Information Theory, Inference, and Learning Algorithms
