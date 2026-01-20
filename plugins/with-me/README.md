# With Me

**"You work with me (Claude)" - Collaborative AI assistant**

Working with you, Claude elicits requirements through information theory-inspired adaptive questioning.

---

## Available Commands

### `/with-me:good-question` - Adaptive Requirement Elicitation

**Note**: This command now includes automatic question effectiveness tracking. Each question's reward score (information gain, clarity, specificity, etc.) is recorded for continuous improvement.

### `/with-me:stats` - Question Effectiveness Dashboard

View statistics about question effectiveness from past sessions.

**What it shows:**
- Total sessions and questions asked
- Best performing question patterns (highest reward scores)
- Dimension-specific statistics (avg information gain per dimension)
- Recent session summaries

**Usage:**
```bash
/with-me:stats
```

**Data Storage**: All statistics are stored locally in `~/.claude/with_me/question_feedback.json`

---

## Question Effectiveness System (v0.3.0)

The with-me plugin uses an information-theoretically grounded question evaluation system based on Bayesian belief updating:

**EIG-based Reward Function:**
```
r(Q) = EIG(Q) + 0.1×clarity(Q) + 0.05×importance(Q)
```

**Key Components:**
1. **Expected Information Gain (EIG)**: Primary metric - measures expected reduction in Shannon entropy (bits of uncertainty)
2. **Clarity** (10% adjustment): Ensures questions are well-formed and understandable
3. **Importance** (5% adjustment): Strategic weighting by dimension priority

**Theoretical Foundation:**
- **Bayesian Belief Updating**: Maintains explicit posterior distributions over hypotheses for each requirement dimension
- **Shannon Entropy**: H(h) = -Σ p(h) log₂ p(h) quantifies uncertainty in bits
- **Information Gain**: Measures actual reduction in entropy after receiving an answer
- **Stdlib-only**: Pure Python 3.11+ implementation (no NumPy/SciPy)

**v0.3.0 Benefits:**
- Principled information-theoretic foundation (replaces heuristic proxies)
- Formal confidence estimation based on posterior distributions
- API contract for as-you plugin integration (QuestionContext/RewardResponse)
- Backward compatible with v0.2.x feedback data

This system helps identify which questions are most effective at eliciting requirements, enabling continuous improvement of the interview process.

---

### `/with-me:good-question` - Adaptive Requirement Elicitation

When you can't articulate your requirements, this command uses an information theory-inspired approach to systematically reduce uncertainty through adaptive questioning.

**How it works:**

The command tracks uncertainty across five key dimensions:
1. **Purpose (Why)**: What problem is being solved and for whom
2. **Data (What)**: Inputs, outputs, transformations
3. **Behavior (How)**: Step-by-step flow and interactions
4. **Constraints (Limits)**: Technical requirements and limitations
5. **Quality (Success)**: Test scenarios and success criteria

At each step, Claude identifies the dimension with highest remaining uncertainty and asks questions that maximize information gain. The interview adapts dynamically based on your answers.

**Usage:**
```bash
/with-me:good-question
```

**Process:**
1. Initial Assessment - Claude gauges your overall clarity
2. Adaptive Questioning - Questions target the most uncertain aspects
3. Convergence Detection - Claude recognizes when clarity is sufficient
4. Validation - Your understanding is summarized and confirmed
5. Analysis - Structured specification generated via `requirement-analysis` skill

---

## Available Skills

### `requirement-analysis` - Structured Requirement Specification

Transforms raw interview data into formal, actionable requirement specifications.

**Context Isolation:** Uses `context: fork` to run in an isolated sub-agent context, keeping your main conversation clean during analysis.

**What it does:**
- Organizes scattered information into clear structure
- Detects ambiguities, contradictions, and gaps
- Generates implementation recommendations
- Assesses risks and suggests mitigation strategies
- Produces acceptance criteria and testing strategy

**Output:**
A comprehensive specification document including:
- Purpose & context
- Functional and non-functional requirements
- Implementation guidance
- Risk assessment
- Open questions requiring clarification

---

## Installation

See [marketplace README](../../README.md#installation) for installation instructions.

---

## License

GNU AGPL v3 - [LICENSE](../../LICENSE)
