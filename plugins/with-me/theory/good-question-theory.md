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

**Validation:** Before selecting next dimension, check prerequisites:
```python
def is_dimension_accessible(dim, dimension_beliefs):
    prerequisites = {
        'purpose': [],
        'data': ['purpose'],
        'behavior': ['purpose'],
        'constraints': ['behavior', 'data'],
        'quality': ['behavior']
    }

    for prereq in prerequisites[dim]:
        if dimension_beliefs[prereq].entropy() >= 1.5:
            return False  # Prerequisite not sufficiently clear

    return True
```

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

**Implementation:** See `with_me/lib/question_reward_calculator.py`

---

## Likelihood Estimation

When a user answers a question, we estimate L(answer|hypothesis) using:

1. **Keyword Matching**: Count occurrences of hypothesis-specific keywords in answer
2. **Laplace Smoothing**: Add-one smoothing to avoid zero probabilities

```python
L(answer|h) = (keyword_matches + 1) / (total_keywords + N_hypotheses)
```

**Keyword Database:** See `with_me/lib/dimension_belief.py` → `_get_hypothesis_keywords()`

---

## Convergence Criteria

Session terminates when:

1. **Entropy Threshold**: All dimensions have H(h) < 0.3 (≈ 70% confidence)
2. **User Signal**: User explicitly indicates "sufficient clarity"
3. **Max Questions**: Safety limit (default: 50 questions)

**Post-Session:** Invoke `/with-me:requirement-analysis` skill for structured specification generation.

---

## Implementation Notes

### Stdlib-Only Constraint

All calculations use Python 3.11+ standard library only:
- Shannon entropy: `math.log2()`
- Bayesian update: Basic arithmetic
- Likelihood: String matching and counting
- No NumPy, SciPy, or ML libraries

**Rationale:** Local-first, zero external dependencies, easy deployment.

### Simplified Approximations

1. **EIG Approximation**: Use current entropy instead of sampling all possible answers
2. **Likelihood**: Keyword matching instead of NLP embeddings
3. **Independence Assumption**: Dimensions treated as independent (minor simplification)

**Justification:** Practical effectiveness over theoretical purity. Results are "good enough" for requirement elicitation while maintaining simplicity.

---

## References

- Shannon (1948): "A Mathematical Theory of Communication"
- Jaynes (2003): "Probability Theory: The Logic of Science"
- with-me Plugin Design Docs: Issues #43, #44, #45 (Bayesian refactor)
- Implementation: `with_me/lib/dimension_belief.py`, `with_me/lib/question_reward_calculator.py`

---

## Version History

- **v0.2.x**: Heuristic uncertainty (word count-based)
- **v0.3.0**: Bayesian belief updating with EIG-based reward (current)

For implementation details, see:
- API Contract: Issue #54
- Phase 1 Implementation: Issues #37-42
- good-question Refactoring: Issue #46 (Case A approach)
