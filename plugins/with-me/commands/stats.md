---
description: Display question effectiveness statistics and analytics
allowed-tools: [Bash, Skill]
---

# Question Effectiveness Dashboard

Display statistics about question effectiveness from past sessions.

## Overview

Shows:
- Total sessions and questions
- Statistical measures (mean, median, std dev)
- Correlation analysis between metrics
- Dimension-specific statistics
- Recent session summaries
- Optional parameter optimization

## Execution Protocol

### 1. Collect Raw Data

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.lib.question_stats --enhanced
```

This outputs raw session data in JSON format. Store the output for skill processing.

### 2. Calculate Statistical Measures

Use `/with-me:statistical-measures` skill for each metric:

**a) Information Gain per Question:**
- Input: List of information gain values from all questions
- Output: Mean, median, standard deviation, variance

**b) Questions per Session:**
- Input: List of question counts from all sessions
- Output: Mean, median, standard deviation, variance

**c) Reward Scores:**
- Input: List of reward scores from question history
- Output: Mean, median, standard deviation, variance

### 3. Correlation Analysis

Use `/with-me:correlation` skill to analyze relationships:

**a) Clarity vs Information Gain:**
- Input: Arrays of clarity scores and corresponding information gain values
- Output: Pearson correlation coefficient

**b) Importance vs Reward:**
- Input: Arrays of importance scores and corresponding reward values
- Output: Pearson correlation coefficient

**c) EIG vs Actual Information Gain:**
- Input: Arrays of predicted EIG and actual measured information gain
- Output: Pearson correlation coefficient (validation of EIG prediction accuracy)

### 4. Parameter Optimization (Optional)

When you need to optimize session configuration parameters (convergence_threshold, prerequisite_threshold, max_questions):

**a) Collect parameter tuning data:**

```bash
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT}"
python3 -m with_me.lib.parameter_tuner --collect
```

This outputs:
- Raw session data with parameter configurations
- Defined parameter ranges for optimization
- Total sessions available for tuning

**b) Perform grid search:**

Use `/with-me:grid-search` skill:

**Input:**
- Sessions data (from step 4a)
- Parameter ranges:
  - convergence_threshold: [0.1, 0.2, 0.3, 0.4, 0.5]
  - prerequisite_threshold: [1.0, 1.5, 2.0, 2.5]
  - max_questions: [20, 30, 40, 50, 60]
- Objective function: Minimize average questions while maintaining high information gain

**Output:**
- Best parameter combination
- Objective function score for each combination
- Performance comparison across parameter space

**c) Update configuration:**

Apply the optimized parameters to `plugins/with-me/config/dimensions.json`:
- Update `session_config.convergence_threshold`
- Update `session_config.prerequisite_threshold`
- Update `session_config.max_questions`

## Display Format

The statistics are displayed in the following sections:

### Overview Metrics
- Total sessions conducted
- Total questions asked
- Mean questions per session (with std dev)
- Mean information gain per question (with std dev)

### Statistical Analysis
- Information Gain: mean, median, std dev, variance
- Questions per Session: mean, median, std dev, variance
- Reward Scores: mean, median, std dev, variance

### Correlation Analysis
- Clarity vs Information Gain: r = X.XX
- Importance vs Reward: r = X.XX
- EIG Prediction Accuracy: r = X.XX

### Best Questions (Top 5)
- Question text
- Average reward score
- Times used
- Target dimension

### Dimension Statistics
For each dimension (purpose, data, behavior, constraints, quality):
- Average information gain
- Average questions needed to resolve

### Recent Sessions (Last 5)
- Session timestamp
- Questions asked
- Average reward
- Efficiency score

### Parameter Optimization Results (if performed)
- Best parameters found
- Objective function score
- Performance improvement vs current configuration

## Example Output

```
## Question Effectiveness Statistics

### Overview
- Total Sessions: 12
- Total Questions: 96
- Mean Questions/Session: 8.0 (σ = 2.1)
- Mean Information Gain/Question: 0.68 bits (σ = 0.15)

### Statistical Analysis
Information Gain:
  - Mean: 0.68 bits
  - Median: 0.65 bits
  - Std Dev: 0.15 bits
  - Variance: 0.0225

Questions per Session:
  - Mean: 8.0 questions
  - Median: 7.5 questions
  - Std Dev: 2.1 questions
  - Variance: 4.41

Reward Scores:
  - Mean: 0.75
  - Median: 0.73
  - Std Dev: 0.12
  - Variance: 0.0144

### Correlation Analysis
- Clarity vs Information Gain: r = 0.72 (strong positive)
- Importance vs Reward: r = 0.68 (moderate positive)
- EIG Prediction Accuracy: r = 0.85 (strong positive - model validates well)

### Best Questions
1. "What problem does this solve?" (Purpose)
   - Avg Reward: 0.88
   - Used: 12 times

2. "What data is involved?" (Data)
   - Avg Reward: 0.85
   - Used: 10 times

### Dimension Statistics
- Purpose: 0.72 avg info gain, 2.3 questions to resolve
- Data: 0.68 avg info gain, 2.8 questions to resolve
- Behavior: 0.65 avg info gain, 3.1 questions to resolve

### Parameter Optimization Results
Best Parameters:
  - convergence_threshold: 0.3
  - prerequisite_threshold: 1.5
  - max_questions: 40

Objective Score: 0.82 (12% improvement over current configuration)
```

## Usage

Run the command to start the statistical analysis workflow:

```
/with-me:stats
```

The command will:
1. Collect raw data from `~/.claude/with_me/question_feedback.json`
2. Invoke skills for statistical calculations (`/with-me:statistical-measures`, `/with-me:correlation`)
3. Display comprehensive statistics with computed measures
4. Optionally perform parameter optimization if requested

**For parameter optimization:**

After reviewing the statistics, you can request parameter tuning by invoking `/with-me:grid-search` skill with the collected parameter data. This will:
1. Perform exhaustive grid search over parameter space
2. Display optimization results
3. Recommend configuration updates to `config/dimensions.json`
