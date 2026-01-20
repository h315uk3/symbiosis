---
description: "Adaptive requirement elicitation - systematically reduce uncertainty through information-maximizing questions"
allowed-tools: [AskUserQuestion, Read, Glob, Grep, WebFetch, Bash, Skill]
---

# Good Question

**Adaptive requirement elicitation using Bayesian belief updating and information theory.**

When requirements are unclear, this command systematically reduces uncertainty through targeted questioning. Each question maximizes expected information gain, adapting to your answers in real-time.

---

## Quick Start

1. Start with `/with-me:good-question`
2. Answer questions about your requirements
3. Questions adapt based on your responses
4. Session ends when clarity is achieved
5. Structured specification generated automatically

**Theory:** See `docs/good-question-theory.md` for mathematical foundation
**Configuration:** See `config/dimensions.json` for dimension definitions

---

## How It Works

### Five Requirement Dimensions

1. **Purpose (Why)**: Problem, users, value
2. **Data (What)**: Inputs, outputs, transformations
3. **Behavior (How)**: Flow, actions, interactions
4. **Constraints (Limits)**: Technical, performance, compatibility
5. **Quality (Success)**: Criteria, edge cases, testing

**Dependency structure:** Purpose → {Data, Behavior} → {Constraints, Quality}

### Adaptive Strategy

- Track uncertainty (entropy) for each dimension using Bayesian belief updating
- Select next question targeting highest-entropy accessible dimension
- Update beliefs after each answer using likelihood estimation
- Stop when all dimensions converge (entropy < 0.3) or user signals clarity

---

## Execution Protocol

### Phase 0: Session Initialization

**Load dimension configuration:**
```bash
DIMENSIONS_CONFIG=$(cat plugins/with-me/config/dimensions.json)
```

**Initialize dimension beliefs:**
- Create uniform prior distribution for each dimension
- All dimensions start at maximum entropy (H ≈ 2.0 bits)
- Load dimension definitions and DAG structure from config

**Start feedback tracking:**
```bash
# Initialize session in feedback manager
python3 -c "
from with_me.lib.question_feedback_manager import QuestionFeedbackManager
from with_me.lib.dimension_belief import create_default_dimension_beliefs

manager = QuestionFeedbackManager()
beliefs = create_default_dimension_beliefs()
session_id = manager.start_session(
    initial_dimension_beliefs={k: v.to_dict() for k, v in beliefs.items()}
)
print(session_id)
" > /tmp/with_me_session_id.txt

SESSION_ID=$(cat /tmp/with_me_session_id.txt)
```

---

### Phase 1: Optional Reference Collection

**Ask using AskUserQuestion:**
```
Question: "Do you have reference materials to save for this session?"
Header: "References"
multiSelect: false
Options:
  - "Git repository" - Clone a repository to /tmp for reference
  - "Documentation URL" - Fetch documentation to /tmp
  - "Local files" - Copy local files to /tmp for reference
  - "No references" - Continue without saving references
```

**If references provided, save to /tmp:**
- Git: `git clone <url> /tmp/ref-$(date +%s)-<project>`
- Docs: `curl <url> -o /tmp/ref-$(date +%s)-doc.pdf`
- Files: `cp <path> /tmp/ref-$(date +%s)-<name>`

**Benefits:** References remain accessible throughout session, faster than repeated fetching.

---

### Phase 2: Adaptive Questioning Loop

**Loop until convergence:**

#### 2.1 Check Convergence

Calculate current entropy for all dimensions:
```python
from with_me.lib.dimension_belief import create_default_dimension_beliefs

beliefs = create_default_dimension_beliefs()
# ... load current beliefs from session state ...

all_converged = all(hs.entropy() < 0.3 for hs in beliefs.values())
```

**If converged:** Jump to Phase 3 (Requirement Analysis)

#### 2.2 Select Next Dimension

**Priority:** Highest entropy among accessible dimensions

```python
def select_next_dimension(beliefs, dimensions_config):
    """Select dimension with highest entropy that satisfies prerequisites."""
    accessible = []

    for dim_id, hs in beliefs.items():
        # Check prerequisites
        prereqs = dimensions_config['dimensions'][dim_id]['prerequisites']
        prereq_threshold = dimensions_config['dimensions'][dim_id].get('prerequisite_threshold', 1.5)

        if all(beliefs[prereq].entropy() < prereq_threshold for prereq in prereqs):
            accessible.append((dim_id, hs.entropy()))

    if not accessible:
        return None  # No accessible dimensions (shouldn't happen)

    # Sort by entropy (descending), then by importance
    accessible.sort(key=lambda x: (x[1], dimensions_config['dimensions'][x[0]]['importance']), reverse=True)
    return accessible[0][0]  # Return dimension ID
```

#### 2.3 Generate Question

**Load example prompts from config:**
```python
import json
import random

config = json.load(open('plugins/with-me/config/dimensions.json'))
target_dim = selected_dimension_id
prompts = config['dimensions'][target_dim]['prompts']

# Select a prompt (rotate or randomize)
question = random.choice(prompts)
```

**Calculate expected reward:**
```python
from with_me.lib.question_reward_calculator import QuestionRewardCalculator, QuestionContext
import time

calculator = QuestionRewardCalculator()
context = QuestionContext(
    session_id=SESSION_ID,
    timestamp=time.time(),
    dimension_beliefs={k: v.to_dict() for k, v in beliefs.items()},
    question_history=question_history,
    feedback_history=[]
)

reward_response = calculator.calculate_reward_for_question(question, context)
print(f"Expected reward: {reward_response.reward_score:.2f} (EIG: {reward_response.eig:.2f} bits)")
```

#### 2.4 Ask Question

**Use AskUserQuestion:**
```
Question: <generated_question>
Header: <dimension_short_name> (e.g., "Why", "What", "How")
multiSelect: false
Options:
  - Provide detailed answer
  - Provide brief answer
  - Skip this question
  - End session (clarity achieved)
```

**Capture answer:**
- If "End session": Jump to Phase 3
- If "Skip": Select next dimension and repeat
- Otherwise: Process answer and update beliefs

#### 2.5 Update Beliefs

**Apply Bayesian update:**
```python
from with_me.lib.dimension_belief import HypothesisSet

# Capture beliefs before update
beliefs_before = {k: v.to_dict() for k, v in beliefs.items()}

# Update target dimension
information_gain = beliefs[target_dim].update(
    observation=question,
    answer=user_answer_text
)

# Capture beliefs after update
beliefs_after = {k: v.to_dict() for k, v in beliefs.items()}

print(f"Information gained: {information_gain:.3f} bits")
print(f"New entropy for {target_dim}: {beliefs[target_dim].entropy():.2f} bits")
print(f"Confidence: {beliefs[target_dim].get_confidence():.2%}")
```

#### 2.6 Record Question

**Save to feedback manager:**
```python
from with_me.lib.question_feedback_manager import QuestionFeedbackManager

manager = QuestionFeedbackManager()

# Prepare answer data
answer_data = {
    "text": user_answer_text,
    "word_count": len(user_answer_text.split()),
    "has_examples": "example" in user_answer_text.lower()
}

# Prepare context
context_data = {
    "question": question,
    "dimension": target_dim,
    "entropy_before": beliefs_before[target_dim]['entropy'],
    "entropy_after": beliefs_after[target_dim]['entropy']
}

# Record
manager.record_question(
    session_id=SESSION_ID,
    question=question,
    dimension=target_dim,
    context=context_data,
    answer=answer_data,
    reward_scores={
        "total_reward": reward_response.reward_score,
        "eig": reward_response.eig,
        "clarity": reward_response.clarity,
        "importance": reward_response.importance
    },
    dimension_beliefs_before=beliefs_before,
    dimension_beliefs_after=beliefs_after
)
```

#### 2.7 Loop Control

- Increment question counter
- Check max question limit (default: 50)
- If max reached: Jump to Phase 3
- Otherwise: Return to step 2.1

---

### Phase 3: Requirement Analysis

**Complete session:**
```python
from with_me.lib.question_feedback_manager import QuestionFeedbackManager

manager = QuestionFeedbackManager()

# Calculate final uncertainties
final_uncertainties = {dim: hs.entropy() for dim, hs in beliefs.items()}

# Complete session with final beliefs
summary = manager.complete_session(
    session_id=SESSION_ID,
    final_uncertainties=final_uncertainties,
    final_dimension_beliefs={k: v.to_dict() for k, v in beliefs.items()}
)

print(f"Session complete: {summary['total_questions']} questions asked")
print(f"Total information gained: {summary['total_info_gain']:.2f} bits")
print(f"Session efficiency: {summary['session_efficiency']:.2f} bits/question")
```

**Generate structured specification:**

Use the `requirement-analysis` skill:
```
/with-me:requirement-analysis
```

This skill:
- Analyzes all collected answers
- Detects ambiguities and gaps
- Generates structured requirements document
- Suggests implementation approach
- Produces acceptance criteria

**Output format:**
- Purpose & context
- Functional requirements
- Non-functional requirements
- Implementation guidance
- Risk assessment
- Open questions

---

## Convergence Criteria

**Session terminates when:**

1. **Entropy threshold met:**
   - All dimensions have H(h) < 0.3 (convergence_threshold)
   - Approximately 70%+ confidence in each dimension

2. **User signals clarity:**
   - User selects "End session (clarity achieved)" option
   - Explicit indication that requirements are sufficiently clear

3. **Max questions reached:**
   - Safety limit (default: 50 questions)
   - Prevents infinite loops

**Post-convergence:** Always invoke requirement-analysis skill for formal specification.

---

## Question Quality Evaluation

Each question is evaluated using:

```
reward(Q) = EIG(Q) + 0.1×clarity(Q) + 0.05×importance(Q)
```

**Components:**
- **EIG (Expected Information Gain):** Entropy of target dimension (bits)
- **Clarity:** Question quality score [0.0-1.0]
- **Importance:** Strategic dimension weighting [0.0-1.0]

**Implementation:** `with_me/lib/question_reward_calculator.py`

---

## Error Handling

### Invalid Dimension Access

**Error:** Attempting to query dimension before prerequisites satisfied

**Detection:**
```python
prereqs = config['dimensions'][dim_id]['prerequisites']
for prereq in prereqs:
    if beliefs[prereq].entropy() >= prereq_threshold:
        raise ValueError(f"Cannot query {dim_id}: {prereq} not sufficiently clear")
```

**Recovery:** Select next highest-entropy accessible dimension

### Session State Corruption

**Error:** Belief state becomes invalid (probabilities don't sum to 1.0)

**Detection:** Check distribution validity after each update

**Recovery:** Re-initialize affected dimension with uniform prior

### No Accessible Dimensions

**Error:** All dimensions either converged or blocked by prerequisites

**Action:** Force termination and proceed to Phase 3

---

## Best Practices

### For Users

1. **Be specific in answers:** More detail = better belief updates
2. **Provide examples:** Helps likelihood estimation
3. **Ask for clarification:** If question is unclear, say so
4. **Signal when done:** Don't wait for all 50 questions if clarity achieved

### For Claude (Implementation)

1. **Check prerequisites before each question:** Validate DAG constraints
2. **Record all questions:** Enable Phase 2 statistical analysis
3. **Calculate actual information gain:** Compare entropy before/after
4. **Adapt question style:** Based on user's answer patterns
5. **Handle edge cases:** Empty answers, contradictions, uncertainty expressions

---

## Debugging & Monitoring

### Real-time Entropy Display

After each answer, show:
```
Current Uncertainty (bits):
  Purpose:      0.25 ████░░░░░░  (87% confidence) ✓
  Data:         0.82 ██████░░░░  (59% confidence)
  Behavior:     1.15 ████████░░  (43% confidence)
  Constraints:  1.98 ██████████  (1% confidence)  [BLOCKED: needs Behavior + Data]
  Quality:      1.85 ██████████  (8% confidence)  [BLOCKED: needs Behavior]

Next target: Behavior (H = 1.15 bits)
```

### Session Statistics

Track and display:
- Questions asked per dimension
- Average information gain per question
- Time per question
- Total session duration
- Dimensions resolved

---

## Configuration

### Adjustable Parameters

**In `config/dimensions.json`:**
- `convergence_threshold`: Entropy threshold for dimension clarity (default: 0.3)
- `prerequisite_threshold`: Entropy threshold for prerequisite satisfaction (default: 1.5)
- `max_questions`: Maximum questions per session (default: 50)
- `min_questions`: Minimum questions before allowing early termination (default: 5)

### Dimension Customization

Add custom dimensions by extending `dimensions.json`:
```json
{
  "dimensions": {
    "custom_dimension": {
      "id": "custom_dimension",
      "name": "Custom Dimension",
      "short_name": "Custom",
      "description": "Description of what this captures",
      "importance": 0.6,
      "prerequisites": ["purpose"],
      "prerequisite_threshold": 1.5,
      "convergence_threshold": 0.3,
      "prompts": ["Question 1?", "Question 2?"],
      "keywords": ["keyword1", "keyword2"]
    }
  },
  "dag": {
    "nodes": ["purpose", "data", "behavior", "constraints", "quality", "custom_dimension"],
    "edges": [
      ... existing edges ...,
      {"from": "purpose", "to": "custom_dimension"}
    ]
  }
}
```

---

## Implementation Notes

### Bayesian Belief Updating (v0.3.0)

**Previous approach (v0.2.x):** Heuristic word-count-based uncertainty
```python
uncertainty = log(word_count + 1) / log(100)  # Not theoretically grounded
```

**Current approach (v0.3.0):** Bayesian posterior distributions
```python
# Maintain explicit probability distributions
posterior = {"web_app": 0.6, "cli_tool": 0.3, "library": 0.1}
entropy = -sum(p * log2(p) for p in posterior.values() if p > 0)
```

**Benefits:**
- Formal information-theoretic foundation
- Measurable information gain in bits
- Confidence estimation from distribution spread
- Principled question selection via EIG

**Implementation:** `with_me/lib/dimension_belief.py`

### Stdlib-Only Constraint

All calculations use Python 3.11+ standard library:
- Shannon entropy: `math.log2()`
- Bayesian updates: Basic arithmetic
- Likelihood: String matching (`str.lower()`, `keyword in text`)
- No NumPy, SciPy, sklearn, or ML libraries

**Rationale:** Local-first, zero dependencies, easy deployment

---

## Troubleshooting

### "No accessible dimensions" error

**Cause:** All dimensions blocked by unmet prerequisites

**Solution:** Check Purpose dimension - it has no prerequisites and should always be accessible

### Slow convergence (many questions needed)

**Cause:** Vague answers provide little information (low IG)

**Solution:** Encourage specific, detailed responses with examples

### Incorrect dimension prioritization

**Cause:** Entropy not accurately reflecting uncertainty

**Solution:** Verify keyword database in `dimension_belief.py` → `_get_hypothesis_keywords()`

### Session state not persisting

**Cause:** `question_feedback_manager.py` failing to save

**Solution:** Check file permissions on `~/.claude/with_me/question_feedback.json`

---

## See Also

- **Theory:** `docs/good-question-theory.md` - Mathematical foundation
- **Config:** `config/dimensions.json` - Dimension definitions and DAG
- **Implementation:** `with_me/lib/dimension_belief.py` - Bayesian core
- **Reward function:** `with_me/lib/question_reward_calculator.py` - EIG calculation
- **Feedback tracking:** `with_me/lib/question_feedback_manager.py` - Session persistence
- **Analysis skill:** `skills/requirement-analysis/SKILL.md` - Spec generation

---

## Version History

- **v0.2.x:** Heuristic uncertainty with word-count proxy
- **v0.3.0:** Bayesian belief updating with EIG-based reward (current)

**Breaking changes in v0.3.0:**
- Uncertainty calculation replaced (backward compatible data format)
- API contract for as-you integration (Issue #54)
- good-question refactored to 400-line execution logic (Issue #46, Case A)

---

## License

GNU AGPL v3 - See [LICENSE](../../LICENSE)
