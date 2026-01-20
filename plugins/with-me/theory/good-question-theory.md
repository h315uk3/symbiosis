# Good Question - Theoretical Foundation

This document explains the theoretical basis for the good-question command's adaptive requirement elicitation approach.

---

## Core Principle: Information-Theoretic Uncertainty Reduction

The good-question command is grounded in information theory, using Bayesian belief updating to systematically reduce uncertainty through adaptive questioning.

### Shannon Entropy

Uncertainty is quantified using Shannon entropy:

```
H(h) = -Σ p(h) log₂ p(h)
```

Where:
- `H(h)`: Entropy (uncertainty) in bits
- `p(h)`: Posterior probability of hypothesis h
- `Σ`: Sum over all hypotheses

**Interpretation:**
- `H = 0`: Complete certainty (one hypothesis has p=1.0)
- `H = log₂(N)`: Maximum uncertainty (uniform distribution over N hypotheses)

### Bayesian Belief Updating

Each question-answer pair updates beliefs using Bayes' rule:

```
p₁(h) ∝ p₀(h) × L(observation|h)
```

Where:
- `p₀(h)`: Prior belief (before question)
- `L(obs|h)`: Likelihood of answer given hypothesis
- `p₁(h)`: Posterior belief (after answer)

### Information Gain

The reduction in uncertainty from a question-answer pair:

```
IG = H(h)_before - H(h)_after
```

Measured in bits. Higher IG = more informative question.

### Expected Information Gain (EIG)

Before asking a question, we estimate its expected value:

```
EIG(Q) = E[H_before - H_after]
       ≈ H_current (simplified approximation)
```

**Strategy:** Select questions that target dimensions with highest current entropy (highest EIG).

---

## Requirement Dimensions

Requirements are decomposed into five orthogonal dimensions:

### 1. Purpose (Why)
**What it captures:**
- Core problem being solved
- Target beneficiaries
- Value proposition

**Hypothesis space:**
- web_app: Browser-based application
- cli_tool: Command-line interface
- library: Reusable code package
- service: Background daemon/API

**Keywords:** why, purpose, goal, problem, need, user, benefit

---

### 2. Data (What)
**What it captures:**
- Information inputs and outputs
- Data structures and schemas
- Transformations

**Hypothesis space:**
- structured: JSON, XML, CSV, databases
- unstructured: Text, documents, files
- streaming: Real-time, continuous data

**Keywords:** data, input, output, information, file, format, structure

---

### 3. Behavior (How)
**What it captures:**
- Operational flow and sequencing
- Actions and interactions
- Triggering conditions

**Hypothesis space:**
- synchronous: Sequential, blocking operations
- asynchronous: Concurrent, non-blocking
- interactive: User prompts and responses
- batch: Automated, scheduled processing

**Keywords:** how, step, process, flow, action, trigger, happen, work

---

### 4. Constraints (Limits)
**What it captures:**
- Technical limitations
- Performance requirements
- Compatibility needs

**Hypothesis space:**
- performance: Speed, latency, throughput
- scalability: Load capacity, concurrency
- reliability: Stability, fault tolerance
- security: Authentication, authorization, encryption

**Keywords:** constraint, limit, requirement, performance, speed, scale, secure

---

### 5. Quality (Success)
**What it captures:**
- Success criteria
- Edge cases and failure modes
- Testing strategy

**Hypothesis space:**
- functional: Feature completeness
- usability: User experience
- maintainability: Code quality, documentation

**Keywords:** test, success, quality, edge case, fail, error, validate

---

## Dimension Dependencies (DAG Structure)

Dimensions have prerequisite relationships forming a Directed Acyclic Graph (DAG):

```
Purpose (Foundation)
  ├─→ Data
  └─→ Behavior
       ├─→ Constraints (also requires Data)
       └─→ Quality
```

**Dependency Rules:**

1. **Purpose** → No prerequisites (always addressable)
2. **Data** → Requires Purpose clarity (H < 1.5 bits)
3. **Behavior** → Requires Purpose clarity (H < 1.5 bits)
4. **Constraints** → Requires both Behavior AND Data clarity
5. **Quality** → Requires Behavior clarity

**Rationale:**
- Cannot define data requirements without understanding the problem (Purpose)
- Cannot describe behavior without understanding the problem (Purpose)
- Cannot specify constraints without knowing what's being built (Behavior, Data)
- Cannot define quality criteria without understanding operations (Behavior)

**Validation:** Before selecting next dimension, check that all prerequisites have entropy below the prerequisite threshold (1.5 bits by default).

---

## Question Selection Strategy

### Priority Ordering

1. **Highest Entropy** (Primary):
   - Select dimension with H(h) > threshold
   - If multiple, choose by importance: Purpose > Behavior > Data > Constraints > Quality

2. **Dependency Constraint** (Critical):
   - Only consider dimensions whose prerequisites are satisfied
   - If highest-entropy dimension is blocked, select next highest accessible dimension

3. **Convergence Detection**:
   - Stop when all dimensions have H(h) < convergence_threshold (default: 0.3)
   - Or when user explicitly indicates sufficient clarity

### Question Reward Function (v0.3.0)

Questions are evaluated using:

```
r(Q) = EIG(Q) + 0.1×clarity(Q) + 0.05×importance(Q)
```

**Components:**
- **EIG(Q)**: Expected information gain (primary metric)
- **clarity(Q)**: Question quality (10% adjustment)
- **importance(Q)**: Strategic dimension weighting (5% adjustment)

---

## Likelihood Estimation

When a user answers a question, the likelihood L(answer|hypothesis) is estimated using:

1. **Keyword Matching**: Count occurrences of hypothesis-specific keywords in answer
2. **Laplace Smoothing**: Add-one smoothing to avoid zero probabilities

The more an answer contains keywords associated with a hypothesis, the higher the likelihood that hypothesis receives.

---

## Convergence Criteria

Session terminates when:

1. **Entropy Threshold**: All dimensions have H(h) < 0.3 (≈ 70% confidence)
2. **User Signal**: User explicitly indicates "sufficient clarity"
3. **Max Questions**: Safety limit (default: 50 questions)

**Post-Session:** Invoke `/with-me:requirement-analysis` skill for structured specification generation.
