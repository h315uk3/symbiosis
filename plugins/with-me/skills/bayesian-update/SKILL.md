---
description: "Perform Bayesian belief updating given prior beliefs and observation likelihoods"
context: fork
allowed-tools: [Read]
---

# Bayesian Belief Updating

Update posterior distribution given new evidence using Bayes' rule.

---

## When to Use This Skill

Use this skill to update probability distributions when:
- Incorporating new observations into existing beliefs
- Calculating posterior probabilities after receiving evidence
- Performing sequential belief updates in requirement elicitation

**Do not use this skill:**
- For initial uniform prior setup (just assign equal probabilities)
- For entropy calculation (use `/with-me:entropy`)
- For information gain calculation (use `/with-me:information-gain`)

---

## Formula

p₁(h) ∝ p₀(h) × L(obs|h)

Normalized form:

p₁(h) = [p₀(h) × L(obs|h)] / Σ[p₀(h) × L(obs|h)]

Where:
- p₀(h): prior belief (current posterior probability)
- L(obs|h): likelihood of observation given hypothesis
- p₁(h): posterior belief after update
- Σ: sum over all hypotheses

---

## Algorithm

**Input:**
- Prior distribution: {hypothesis_id: prior_probability, ...}
- Likelihoods: {hypothesis_id: likelihood, ...}

**Steps:**
1. For each hypothesis h:
   - Calculate unnormalized[h] = prior[h] × likelihood[h]
2. Calculate total = Σ unnormalized[h] across all hypotheses
3. For each hypothesis h:
   - Calculate posterior[h] = unnormalized[h] / total
4. Return posterior distribution

**Output:** Updated posterior distribution {hypothesis_id: posterior_probability, ...}

---

## Examples

### Example 1: Standard update with 4 hypotheses

**Given:** Uniform prior, strong evidence for h1

**Input:**
```json
{
  "prior": {"h1": 0.25, "h2": 0.25, "h3": 0.25, "h4": 0.25},
  "likelihoods": {"h1": 0.7, "h2": 0.2, "h3": 0.1, "h4": 0.0}
}
```

**Calculation:**

**Step 1: Multiply prior by likelihood**
- h1: 0.25 × 0.7 = 0.175
- h2: 0.25 × 0.2 = 0.05
- h3: 0.25 × 0.1 = 0.025
- h4: 0.25 × 0.0 = 0.0

**Step 2: Calculate total**
- Total = 0.175 + 0.05 + 0.025 + 0.0 = 0.25

**Step 3: Normalize**
- h1: 0.175 / 0.25 = 0.7
- h2: 0.05 / 0.25 = 0.2
- h3: 0.025 / 0.25 = 0.1
- h4: 0.0 / 0.25 = 0.0

**Output:**
```json
{"h1": 0.7, "h2": 0.2, "h3": 0.1, "h4": 0.0}
```

### Example 2: Non-uniform prior with 3 hypotheses

**Given:** Prior with existing belief, moderate evidence

**Input:**
```json
{
  "prior": {"h1": 0.5, "h2": 0.3, "h3": 0.2},
  "likelihoods": {"h1": 0.4, "h2": 0.5, "h3": 0.1}
}
```

**Calculation:**

**Step 1: Multiply prior by likelihood**
- h1: 0.5 × 0.4 = 0.2
- h2: 0.3 × 0.5 = 0.15
- h3: 0.2 × 0.1 = 0.02

**Step 2: Calculate total**
- Total = 0.2 + 0.15 + 0.02 = 0.37

**Step 3: Normalize**
- h1: 0.2 / 0.37 ≈ 0.5405
- h2: 0.15 / 0.37 ≈ 0.4054
- h3: 0.02 / 0.37 ≈ 0.0541

**Output:**
```json
{"h1": 0.5405, "h2": 0.4054, "h3": 0.0541}
```

### Example 3: Extreme evidence eliminates hypothesis

**Given:** Equal prior, evidence completely rules out one hypothesis

**Input:**
```json
{
  "prior": {"h1": 0.33, "h2": 0.33, "h3": 0.34},
  "likelihoods": {"h1": 0.8, "h2": 0.2, "h3": 0.0}
}
```

**Calculation:**

**Step 1: Multiply prior by likelihood**
- h1: 0.33 × 0.8 = 0.264
- h2: 0.33 × 0.2 = 0.066
- h3: 0.34 × 0.0 = 0.0

**Step 2: Calculate total**
- Total = 0.264 + 0.066 + 0.0 = 0.33

**Step 3: Normalize**
- h1: 0.264 / 0.33 = 0.8
- h2: 0.066 / 0.33 = 0.2
- h3: 0.0 / 0.33 = 0.0

**Output:**
```json
{"h1": 0.8, "h2": 0.2, "h3": 0.0}
```

---

## Properties

- **Conservation:** Σ p₁(h) = 1.0 (probabilities sum to 1)
- **Influence:** Higher likelihood → higher posterior probability
- **Zero evidence:** If L(obs|h) = 0, then p₁(h) = 0 (hypothesis ruled out)
- **Weak evidence:** If likelihoods are uniform, posterior equals prior (no information gained)

---

## Edge Cases

**All likelihoods zero:**
- This should not occur in practice (means observation impossible under all hypotheses)
- If encountered, return prior distribution unchanged

**Likelihoods don't sum to 1.0:**
- This is expected and normal
- Likelihoods are P(observation|hypothesis), not probabilities over hypotheses
- Normalization step ensures posterior sums to 1.0

---

## References

- Bayes, Thomas (1763): An Essay towards solving a Problem in the Doctrine of Chances
- Jaynes, E. T. (2003): Probability Theory: The Logic of Science
