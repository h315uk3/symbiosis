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

## Claude Computational Engine Architecture

The with-me plugin implements a **hybrid computational architecture** where:
- **Python handles I/O**: Session management, data persistence, CLI interface
- **Claude performs computations**: All mathematical algorithms executed via skills

**Architecture Benefits:**
- **Distributable Intelligence**: Skills are portable markdown files, not compiled code
- **Transparent Computation**: All calculations visible in Claude's reasoning
- **Zero External Dependencies**: No NumPy, SciPy, or ML libraries required
- **Skill Composition**: Skills can invoke other skills for complex workflows

**Information-Theoretic Foundation:**

The system uses Bayesian belief updating and information theory for adaptive questioning:

**Reward Function:**
```
r(Q) = EIG(Q) + 0.1 * clarity(Q) + 0.05 * importance(Q)
```

**Key Concepts:**
1. **Expected Information Gain (EIG)**: Predicts uncertainty reduction through counterfactual simulation
2. **Shannon Entropy**: H(h) = -Σ p(h) log₂ p(h) - measures uncertainty in bits
3. **Bayesian Update**: p₁(h) = [p₀(h) * L(obs|h)] / Σ[p₀(h) * L(obs|h)]
4. **Information Gain**: IG = H_before - H_after - quantifies learning from each answer

This architecture enables continuous improvement through statistical analysis of question effectiveness across sessions.

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

The plugin provides 10 specialized skills for computational tasks:

### Core Computational Skills

**`/with-me:entropy`** - Shannon Entropy Calculation
- Computes H(h) = -Σ p(h) log₂ p(h) from posterior distributions
- Returns uncertainty measurement in bits

**`/with-me:bayesian-update`** - Bayesian Belief Updating
- Applies p₁(h) = [p₀(h) * L(obs|h)] / Σ[p₀(h) * L(obs|h)]
- Updates beliefs after receiving evidence

**`/with-me:information-gain`** - Information Gain Calculation
- Computes IG = H_before - H_after
- Quantifies learning from each question-answer pair

### Question Evaluation Skills

**`/with-me:question-clarity`** - Clarity Scoring
- Evaluates question comprehensibility (0.0-1.0)
- Checks for ambiguity, jargon, and structure

**`/with-me:question-importance`** - Importance Scoring
- Assesses strategic value of question (0.0-1.0)
- Considers dimension priority and context

**`/with-me:eig-calculation`** - Expected Information Gain
- Predicts uncertainty reduction via counterfactual simulation
- Guides optimal question selection

### Statistical Analysis Skills

**`/with-me:statistical-measures`** - Descriptive Statistics
- Computes mean, median, standard deviation, variance
- Used for analyzing question effectiveness metrics

**`/with-me:correlation`** - Pearson Correlation
- Measures linear relationship between two variables
- Validates prediction accuracy and metric relationships

**`/with-me:grid-search`** - Parameter Optimization
- Performs exhaustive search over parameter space
- Optimizes session configuration thresholds

### Specification Generation Skill

**`/with-me:requirement-analysis`** - Structured Requirement Specification
- Transforms interview data into formal specifications
- Uses `context: fork` for isolated sub-agent processing
- Generates comprehensive documentation with acceptance criteria

---

## Installation

See [marketplace README](../../README.md#installation) for installation instructions.

---

## License

GNU AGPL v3 - [LICENSE](../../LICENSE)
