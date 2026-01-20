---
description: "Find optimal parameter values through exhaustive grid search"
context: fork
allowed-tools: [Read]
---

# Grid Search Optimization

Find optimal parameter values by exhaustive search over parameter space.

---

## When to Use This Skill

Use this skill to optimize parameters when:
- Tuning convergence thresholds or importance weights
- Finding best configuration for question effectiveness metrics
- Exploring parameter combinations systematically

**Do not use this skill:**
- For continuous optimization (grid search is for discrete values)
- When parameter space is too large (use random search or Bayesian optimization)

---

# Grid Search Optimization

Find optimal parameter values by exhaustive search over parameter space.

## Concept

Grid search evaluates a function at all combinations of parameter values from predefined ranges, selecting the combination that yields the best score.

## Algorithm

**Input:**
- parameter_ranges: Dictionary of {parameter_name: [value1, value2, ...]}
- objective_function: Function to optimize (maximize or minimize)
- optimization_goal: "maximize" or "minimize"

**Steps:**

1. Generate all parameter combinations:
   - For each parameter, take all possible values
   - Create Cartesian product of all value lists

2. For each parameter combination:
   - Evaluate objective_function(parameters)
   - Record score and parameter values

3. Select best combination:
   - If maximizing: Choose combination with highest score
   - If minimizing: Choose combination with lowest score

4. Return optimal parameters and score

**Output:**
- best_parameters: Dictionary of {parameter_name: optimal_value}
- best_score: Objective function value at optimal parameters

## Python Role vs Claude Role

**Python handles:**
- Loop iteration over combinations
- State tracking (current best score)
- File I/O for persistence
- Progress reporting

**Claude handles:**
- Objective function evaluation (e.g., cross-validation score)
- Comparison logic (which score is better)
- Final selection recommendation

**Workflow:**
```
1. Python generates combination: {"learning_rate": 0.01, "threshold": 0.3}
2. Python outputs state JSON
3. Claude evaluates objective function with these parameters
4. Claude returns score: 0.85
5. Python records score
6. Repeat for all combinations
7. Claude identifies best: {"learning_rate": 0.01, "threshold": 0.5, "score": 0.92}
```

## Examples

### Example 1: Two parameters

**Input:**
```json
{
  "parameter_ranges": {
    "threshold": [0.1, 0.3, 0.5],
    "weight": [0.5, 1.0, 1.5]
  },
  "optimization_goal": "maximize"
}
```

**Parameter combinations (Cartesian product):**
1. {threshold: 0.1, weight: 0.5}
2. {threshold: 0.1, weight: 1.0}
3. {threshold: 0.1, weight: 1.5}
4. {threshold: 0.3, weight: 0.5}
5. {threshold: 0.3, weight: 1.0}
6. {threshold: 0.3, weight: 1.5}
7. {threshold: 0.5, weight: 0.5}
8. {threshold: 0.5, weight: 1.0}
9. {threshold: 0.5, weight: 1.5}

**Evaluation (example scores):**
| Combination | Threshold | Weight | Score |
|-------------|-----------|--------|-------|
| 1 | 0.1 | 0.5 | 0.72 |
| 2 | 0.1 | 1.0 | 0.78 |
| 3 | 0.1 | 1.5 | 0.75 |
| 4 | 0.3 | 0.5 | 0.81 |
| 5 | 0.3 | 1.0 | 0.88 |
| 6 | 0.3 | 1.5 | 0.85 |
| 7 | 0.5 | 0.5 | 0.79 |
| 8 | 0.5 | 1.0 | 0.83 |
| 9 | 0.5 | 1.5 | 0.80 |

**Best combination:**
- Combination 5: {threshold: 0.3, weight: 1.0}
- Score: 0.88

**Output:**
```json
{
  "best_parameters": {"threshold": 0.3, "weight": 1.0},
  "best_score": 0.88
}
```

### Example 2: Three parameters with minimization

**Input:**
```json
{
  "parameter_ranges": {
    "alpha": [0.01, 0.1],
    "beta": [0.5, 1.0],
    "gamma": [2, 4, 8]
  },
  "optimization_goal": "minimize"
}
```

**Total combinations:** 2 × 2 × 3 = 12

**Evaluation (error metric, lower is better):**
| Alpha | Beta | Gamma | Error |
|-------|------|-------|-------|
| 0.01 | 0.5 | 2 | 0.25 |
| 0.01 | 0.5 | 4 | 0.18 |
| 0.01 | 0.5 | 8 | 0.22 |
| 0.01 | 1.0 | 2 | 0.20 |
| 0.01 | 1.0 | 4 | 0.15 |
| 0.01 | 1.0 | 8 | 0.19 |
| 0.1 | 0.5 | 2 | 0.28 |
| 0.1 | 0.5 | 4 | 0.21 |
| 0.1 | 0.5 | 8 | 0.24 |
| 0.1 | 1.0 | 2 | 0.23 |
| 0.1 | 1.0 | 4 | 0.17 |
| 0.1 | 1.0 | 8 | 0.20 |

**Best combination (minimum error):**
- {alpha: 0.01, beta: 1.0, gamma: 4}
- Error: 0.15

**Output:**
```json
{
  "best_parameters": {"alpha": 0.01, "beta": 1.0, "gamma": 4},
  "best_score": 0.15
}
```

## Computational Complexity

**Total evaluations:** Product of all parameter range sizes

Examples:
- 3 params × 5 values each = 5³ = 125 evaluations
- 2 params × 10 values + 1 param × 5 values = 10 × 10 × 5 = 500 evaluations

**Time complexity:** O(n₁ × n₂ × ... × nₖ) where nᵢ is size of range for parameter i

## Selection Strategy

### Maximize

Find combination with highest score:

```
best_score = -infinity
best_params = None

for each combination:
  score = evaluate(combination)
  if score > best_score:
    best_score = score
    best_params = combination

return best_params, best_score
```

### Minimize

Find combination with lowest score:

```
best_score = +infinity
best_params = None

for each combination:
  score = evaluate(combination)
  if score < best_score:
    best_score = score
    best_params = combination

return best_params, best_score
```

## Advantages

- **Complete coverage:** Evaluates entire search space
- **Guaranteed optimal:** Finds global optimum within discrete grid
- **Simple:** Easy to implement and understand
- **Parallelizable:** Evaluations independent

## Disadvantages

- **Computationally expensive:** Exponential in number of parameters
- **Discrete:** Misses optimal values between grid points
- **Curse of dimensionality:** Becomes infeasible with many parameters

## Best Practices

**Parameter range selection:**
- Start with coarse grid (few values, wide range)
- Refine grid around promising regions
- Use logarithmic spacing for scale-sensitive parameters

**Efficiency improvements:**
- Early stopping: Terminate if no improvement after N iterations
- Adaptive grid: Zoom in on best regions
- Random search: Sample random combinations (more efficient for high dimensions)

**Example refinement:**
```
Phase 1 (coarse): threshold ∈ {0.1, 0.5, 0.9}
Best: 0.5

Phase 2 (fine): threshold ∈ {0.3, 0.4, 0.5, 0.6, 0.7}
Best: 0.6

Phase 3 (ultra-fine): threshold ∈ {0.55, 0.60, 0.65}
Best: 0.60
```

## Use Cases in with-me

**Parameter tuning for:**
- Convergence thresholds
- Importance weights
- Prerequisite thresholds
- EIG calculation parameters

**Objective functions:**
- Question efficiency (IG per question)
- Session length (total questions to convergence)
- User satisfaction proxy (pattern in responses)
