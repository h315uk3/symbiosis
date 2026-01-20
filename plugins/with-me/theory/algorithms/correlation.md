# Pearson Correlation Coefficient

Measure linear relationship between two variables.

## Formula

r = Σ[(x_i - x̄)(y_i - ȳ)] / √[Σ(x_i - x̄)² × Σ(y_i - ȳ)²]

Alternative computational formula:

r = [n(Σx_iy_i) - (Σx_i)(Σy_i)] / √{[n(Σx_i²) - (Σx_i)²][n(Σy_i²) - (Σy_i)²]}

Where:
- x_i, y_i: paired data points
- x̄, ȳ: means of x and y
- n: number of pairs
- r: correlation coefficient

## Algorithm

**Input:** Two lists of equal length
- x_values: [x₁, x₂, ..., xₙ]
- y_values: [y₁, y₂, ..., yₙ]

**Steps:**

**Method 1: Using means (more intuitive)**
1. Calculate mean_x = (Σ x_i) / n
2. Calculate mean_y = (Σ y_i) / n
3. For each pair (x_i, y_i):
   - Calculate dx_i = x_i - mean_x
   - Calculate dy_i = y_i - mean_y
4. Calculate numerator = Σ(dx_i × dy_i)
5. Calculate sum_dx_squared = Σ(dx_i²)
6. Calculate sum_dy_squared = Σ(dy_i²)
7. Calculate denominator = √(sum_dx_squared × sum_dy_squared)
8. Calculate r = numerator / denominator
9. Return r

**Method 2: Computational formula (avoids intermediate storage)**
1. Calculate n, Σx_i, Σy_i, Σx_i², Σy_i², Σ(x_i × y_i)
2. Calculate numerator = n(Σx_iy_i) - (Σx_i)(Σy_i)
3. Calculate denom_x = n(Σx_i²) - (Σx_i)²
4. Calculate denom_y = n(Σy_i²) - (Σy_i)²
5. Calculate denominator = √(denom_x × denom_y)
6. Calculate r = numerator / denominator
7. Return r

**Output:** Correlation coefficient r (float, range: -1.0 to 1.0)

## Examples

### Example 1: Perfect positive correlation

**Input:**
```json
{
  "x": [1.0, 2.0, 3.0, 4.0, 5.0],
  "y": [2.0, 4.0, 6.0, 8.0, 10.0]
}
```

**Calculation (Method 1):**
- mean_x = 3.0, mean_y = 6.0
- Deviations:
  - dx: [-2.0, -1.0, 0.0, 1.0, 2.0]
  - dy: [-4.0, -2.0, 0.0, 2.0, 4.0]
- Products: [8.0, 2.0, 0.0, 2.0, 8.0]
- Numerator = 8.0 + 2.0 + 0.0 + 2.0 + 8.0 = 20.0
- sum_dx_squared = 4 + 1 + 0 + 1 + 4 = 10.0
- sum_dy_squared = 16 + 4 + 0 + 4 + 16 = 40.0
- Denominator = √(10.0 × 40.0) = √400 = 20.0
- r = 20.0 / 20.0 = 1.0

**Output:** 1.0 (perfect positive correlation)

### Example 2: Perfect negative correlation

**Input:**
```json
{
  "x": [1.0, 2.0, 3.0, 4.0, 5.0],
  "y": [10.0, 8.0, 6.0, 4.0, 2.0]
}
```

**Calculation:**
- mean_x = 3.0, mean_y = 6.0
- Deviations:
  - dx: [-2.0, -1.0, 0.0, 1.0, 2.0]
  - dy: [4.0, 2.0, 0.0, -2.0, -4.0]
- Products: [-8.0, -2.0, 0.0, -2.0, -8.0]
- Numerator = -8.0 - 2.0 + 0.0 - 2.0 - 8.0 = -20.0
- sum_dx_squared = 10.0 (same as Example 1)
- sum_dy_squared = 16 + 4 + 0 + 4 + 16 = 40.0
- Denominator = √(10.0 × 40.0) = 20.0
- r = -20.0 / 20.0 = -1.0

**Output:** -1.0 (perfect negative correlation)

### Example 3: No correlation

**Input:**
```json
{
  "x": [1.0, 2.0, 3.0, 4.0, 5.0],
  "y": [3.0, 5.0, 2.0, 6.0, 4.0]
}
```

**Calculation:**
- mean_x = 3.0, mean_y = 4.0
- Deviations:
  - dx: [-2.0, -1.0, 0.0, 1.0, 2.0]
  - dy: [-1.0, 1.0, -2.0, 2.0, 0.0]
- Products: [2.0, -1.0, 0.0, 2.0, 0.0]
- Numerator = 2.0 - 1.0 + 0.0 + 2.0 + 0.0 = 3.0
- sum_dx_squared = 10.0
- sum_dy_squared = 1 + 1 + 4 + 4 + 0 = 10.0
- Denominator = √(10.0 × 10.0) = 10.0
- r = 3.0 / 10.0 = 0.3

**Output:** 0.3 (weak positive correlation)

### Example 4: Moderate correlation

**Input:**
```json
{
  "x": [1.5, 2.3, 3.1, 4.2, 5.0],
  "y": [2.8, 3.5, 4.9, 5.1, 6.2]
}
```

**Calculation (Method 2):**
- n = 5
- Σx_i = 1.5 + 2.3 + 3.1 + 4.2 + 5.0 = 16.1
- Σy_i = 2.8 + 3.5 + 4.9 + 5.1 + 6.2 = 22.5
- Σx_i² = 2.25 + 5.29 + 9.61 + 17.64 + 25.0 = 59.79
- Σy_i² = 7.84 + 12.25 + 24.01 + 26.01 + 38.44 = 108.55
- Σ(x_i × y_i) = 4.2 + 8.05 + 15.19 + 21.42 + 31.0 = 79.86
- Numerator = 5(79.86) - (16.1)(22.5) = 399.3 - 362.25 = 37.05
- denom_x = 5(59.79) - (16.1)² = 298.95 - 259.21 = 39.74
- denom_y = 5(108.55) - (22.5)² = 542.75 - 506.25 = 36.5
- Denominator = √(39.74 × 36.5) = √1450.51 ≈ 38.09
- r = 37.05 / 38.09 ≈ 0.973

**Output:** 0.973 (strong positive correlation)

## Interpretation

**Value ranges:**
- r = 1.0: Perfect positive linear relationship
- 0.7 < r < 1.0: Strong positive correlation
- 0.3 < r < 0.7: Moderate positive correlation
- -0.3 < r < 0.3: Weak or no correlation
- -0.7 < r < -0.3: Moderate negative correlation
- -1.0 < r < -0.7: Strong negative correlation
- r = -1.0: Perfect negative linear relationship

**Important notes:**
- Measures only linear relationships
- Does not imply causation
- Sensitive to outliers
- Requires normally distributed variables for significance testing

## Properties

- **Range:** -1.0 ≤ r ≤ 1.0
- **Symmetry:** corr(x, y) = corr(y, x)
- **Scale invariant:** Unaffected by linear transformations
- **Sign:** Positive r means x and y increase together, negative r means inverse relationship
- **Magnitude:** |r| measures strength of linear relationship

## Edge Cases

**Constant values:**
- If all x_i identical or all y_i identical: r is undefined (division by zero)
- Return null or special value to indicate undefined correlation

**Perfect alignment:**
- If y = ax + b for some constants a, b: r = +1 (if a > 0) or r = -1 (if a < 0)
