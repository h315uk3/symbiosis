---
description: "Calculate mean, median, standard deviation, and variance for data analysis"
context: fork
allowed-tools: [Read]
---

# Statistical Measures

Calculate descriptive statistics for data analysis.

---

## When to Use This Skill

Use this skill to calculate statistical measures when:
- Analyzing question effectiveness metrics
- Computing summary statistics for session data
- Evaluating distribution properties

**Do not use this skill:**
- For entropy or information gain (use `/with-me:entropy` or `/with-me:information-gain`)
- For correlation analysis (use `/with-me:correlation`)

---

# Statistical Measures

Calculate descriptive statistics for data analysis.

## Mean (Average)

### Formula

mean = (Σ x_i) / n

Where:
- x_i: individual values
- n: number of values
- Σ: sum over all values

### Algorithm

**Input:** List of numeric values [x₁, x₂, ..., xₙ]

**Steps:**
1. Calculate sum = x₁ + x₂ + ... + xₙ
2. Calculate count = n
3. Calculate mean = sum / count
4. Return mean

**Output:** Mean value (float)

### Example

**Input:** [2.0, 4.0, 6.0, 8.0, 10.0]

**Calculation:**
- Sum = 2.0 + 4.0 + 6.0 + 8.0 + 10.0 = 30.0
- Count = 5
- Mean = 30.0 / 5 = 6.0

**Output:** 6.0

---

## Median

### Formula

For sorted data:
- If n is odd: median = x_{(n+1)/2}
- If n is even: median = (x_{n/2} + x_{(n/2)+1}) / 2

Where x_{i} is the i-th value in sorted order.

### Algorithm

**Input:** List of numeric values [x₁, x₂, ..., xₙ]

**Steps:**
1. Sort values in ascending order
2. If count n is odd:
   - Return middle value at position (n+1)/2
3. If count n is even:
   - Calculate average of two middle values at positions n/2 and (n/2)+1
4. Return median

**Output:** Median value (float)

### Examples

**Example 1: Odd count**

**Input:** [3.0, 1.0, 5.0, 2.0, 4.0]

**Calculation:**
- Sorted: [1.0, 2.0, 3.0, 4.0, 5.0]
- Count = 5 (odd)
- Position = (5+1)/2 = 3
- Median = 3.0

**Output:** 3.0

**Example 2: Even count**

**Input:** [4.0, 1.0, 3.0, 2.0]

**Calculation:**
- Sorted: [1.0, 2.0, 3.0, 4.0]
- Count = 4 (even)
- Positions = 2 and 3
- Median = (2.0 + 3.0) / 2 = 2.5

**Output:** 2.5

---

## Standard Deviation

### Formula

Population standard deviation:

σ = √(Σ(x_i - μ)² / n)

Sample standard deviation:

s = √(Σ(x_i - x̄)² / (n-1))

Where:
- x_i: individual values
- μ or x̄: mean
- n: number of values
- √: square root

### Algorithm

**Input:**
- values: List of numeric values [x₁, x₂, ..., xₙ]
- population: Boolean (true for population, false for sample)

**Steps:**
1. Calculate mean: μ = (Σ x_i) / n
2. For each value x_i:
   - Calculate squared_diff = (x_i - μ)²
3. Calculate sum_squared_diffs = Σ squared_diff
4. If population:
   - variance = sum_squared_diffs / n
5. If sample:
   - variance = sum_squared_diffs / (n - 1)
6. Calculate std_dev = √variance
7. Return std_dev

**Output:** Standard deviation (float)

### Examples

**Example 1: Population standard deviation**

**Input:** values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0], population = true

**Calculation:**
- Mean = (2+4+4+4+5+5+7+9) / 8 = 40 / 8 = 5.0
- Squared differences:
  - (2-5)² = 9
  - (4-5)² = 1
  - (4-5)² = 1
  - (4-5)² = 1
  - (5-5)² = 0
  - (5-5)² = 0
  - (7-5)² = 4
  - (9-5)² = 16
- Sum = 9 + 1 + 1 + 1 + 0 + 0 + 4 + 16 = 32
- Variance = 32 / 8 = 4.0
- Std dev = √4.0 = 2.0

**Output:** 2.0

**Example 2: Sample standard deviation**

**Input:** values = [2.0, 4.0, 6.0, 8.0], population = false

**Calculation:**
- Mean = (2+4+6+8) / 4 = 20 / 4 = 5.0
- Squared differences:
  - (2-5)² = 9
  - (4-5)² = 1
  - (6-5)² = 1
  - (8-5)² = 9
- Sum = 9 + 1 + 1 + 9 = 20
- Variance = 20 / (4-1) = 20 / 3 ≈ 6.667
- Std dev = √6.667 ≈ 2.582

**Output:** 2.582

---

## Variance

### Formula

Variance = σ² or s² (square of standard deviation)

Population variance: σ² = Σ(x_i - μ)² / n

Sample variance: s² = Σ(x_i - x̄)² / (n-1)

### Algorithm

Follow standard deviation algorithm, but return variance (before square root).

---

## Properties

**Mean:**
- Sensitive to outliers
- Always between minimum and maximum values
- Sum of deviations from mean = 0

**Median:**
- Robust to outliers
- 50th percentile
- Better than mean for skewed distributions

**Standard Deviation:**
- Measures spread/dispersion
- Same unit as original data
- σ = 0 means all values identical
- Larger σ means more variability

**Variance:**
- Always non-negative
- Unit is square of original data unit
- More sensitive to outliers than std dev
