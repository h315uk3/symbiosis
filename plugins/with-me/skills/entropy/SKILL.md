---
description: "Calculate Shannon entropy to measure uncertainty in probability distributions"
context: fork
allowed-tools: [Read]
---

# Shannon Entropy Calculation

Calculate uncertainty in posterior distribution using information theory.

---

## When to Use This Skill

Use this skill to calculate Shannon entropy H(h) = -Σ p(h) log₂ p(h) when:
- Measuring uncertainty in belief distributions
- Evaluating information content before/after observations
- Computing convergence metrics for requirement elicitation

**Do not use this skill:**
- For statistical variance or standard deviation (use `/with-me:statistical-measures`)
- For correlation analysis (use `/with-me:correlation`)

---

## Formula

H(h) = -Σ p(h) log₂ p(h)

Where:
- h: hypothesis (any key in the posterior distribution)
- p(h): probability of hypothesis h
- Σ: sum over all hypotheses in the distribution

---

## Algorithm

**Input:** Posterior distribution as dictionary {hypothesis_id: probability, ...}

**Steps:**
1. Initialize entropy = 0.0
2. For each (hypothesis, probability) pair in the distribution:
   - If probability = 0: skip (lim x→0 x log x = 0)
   - If probability > 0: entropy -= probability × log₂(probability)
3. Return entropy in bits

**Output:** Entropy value (float, rounded to 4 decimal places)

---

## Logarithm Calculation

log₂(x) = ln(x) / ln(2)

Where:
- ln(x): natural logarithm
- ln(2) ≈ 0.693147

---

## Examples

### Example 1: Maximum uncertainty (uniform distribution)

**Given:** 4 hypotheses with equal probability

**Input:**
```json
{"h1": 0.25, "h2": 0.25, "h3": 0.25, "h4": 0.25}
```

**Calculation:**
- h1: -0.25 × log₂(0.25) = -0.25 × (-2) = 0.5
- h2: -0.25 × log₂(0.25) = -0.25 × (-2) = 0.5
- h3: -0.25 × log₂(0.25) = -0.25 × (-2) = 0.5
- h4: -0.25 × log₂(0.25) = -0.25 × (-2) = 0.5
- Sum: 0.5 + 0.5 + 0.5 + 0.5 = 2.0

**Output:** 2.0000 bits

### Example 2: Complete certainty

**Given:** 4 hypotheses, one with probability 1.0

**Input:**
```json
{"h1": 1.0, "h2": 0.0, "h3": 0.0, "h4": 0.0}
```

**Calculation:**
- h1: -1.0 × log₂(1.0) = -1.0 × 0 = 0.0
- h2: skip (p = 0)
- h3: skip (p = 0)
- h4: skip (p = 0)
- Sum: 0.0

**Output:** 0.0000 bits

### Example 3: Partial uncertainty

**Given:** 4 hypotheses with varying probabilities

**Input:**
```json
{"h1": 0.5, "h2": 0.3, "h3": 0.15, "h4": 0.05}
```

**Calculation:**
- h1: -0.5 × log₂(0.5) = -0.5 × (-1) = 0.5
- h2: -0.3 × log₂(0.3) ≈ -0.3 × (-1.7370) ≈ 0.5211
- h3: -0.15 × log₂(0.15) ≈ -0.15 × (-2.7370) ≈ 0.4106
- h4: -0.05 × log₂(0.05) ≈ -0.05 × (-4.3219) ≈ 0.2161
- Sum: 0.5 + 0.5211 + 0.4106 + 0.2161 ≈ 1.6478

**Output:** 1.6478 bits

### Example 4: Three hypotheses

**Given:** 3 hypotheses

**Input:**
```json
{"h1": 0.6, "h2": 0.3, "h3": 0.1}
```

**Calculation:**
- h1: -0.6 × log₂(0.6) ≈ -0.6 × (-0.7370) ≈ 0.4422
- h2: -0.3 × log₂(0.3) ≈ -0.3 × (-1.7370) ≈ 0.5211
- h3: -0.1 × log₂(0.1) ≈ -0.1 × (-3.3219) ≈ 0.3322
- Sum: 0.4422 + 0.5211 + 0.3322 ≈ 1.2955

**Output:** 1.2955 bits

---

## Properties

- **Minimum entropy:** H = 0 (complete certainty, one hypothesis has p = 1.0)
- **Maximum entropy:** H = log₂(N) (uniform distribution over N hypotheses)
- **Range:** 0 ≤ H ≤ log₂(N) for N hypotheses
- **Unit:** bits (base-2 logarithm)

---

## References

- Shannon (1948): A Mathematical Theory of Communication
- Cover & Thomas (2006): Elements of Information Theory
