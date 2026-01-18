---
description: Display question effectiveness statistics and analytics
allowed-tools: [Bash]
---

# Question Effectiveness Dashboard

Display statistics about question effectiveness from past sessions.

## Overview

Shows:
- Total sessions and questions
- Best performing question patterns
- Dimension-specific statistics
- Recent session summaries

## Implementation

```bash
# Run statistics collector
cd "${CLAUDE_PLUGIN_ROOT}/scripts" && python3 -m lib.question_stats
```

## Display Format

The statistics are displayed in the following sections:

### Overview Metrics
- Total sessions conducted
- Total questions asked
- Average questions per session

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

## Example Output

```
## Question Effectiveness Statistics

### Overview
- Total Sessions: 12
- Total Questions: 96
- Average Questions/Session: 8.0

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
```

## Usage

Simply run the command:

```
/with-me:stats
```

No arguments required. The command reads from `~/.claude/with-me/question_feedback.json`.
