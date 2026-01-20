---
description: "Adaptive requirement elicitation - systematically reduce uncertainty through information-maximizing questions"
allowed-tools: [AskUserQuestion, Bash, Skill]
---

# Good Question

@theory/good-question-theory.md

**Adaptive requirement elicitation using Bayesian belief updating and information theory.**

When requirements are unclear, this command systematically reduces uncertainty through targeted questioning. Each question maximizes expected information gain, adapting to your answers in real-time.

---

## Quick Start

1. Run `/with-me:good-question`
2. Answer adaptive questions about your requirements
3. Questions adapt based on your responses using Bayesian belief updating
4. Session ends when all dimensions converge or you signal clarity
5. Structured requirement specification generated automatically

**Configuration:** See `config/dimensions.json` for dimension definitions and thresholds

---

## Execution

Initialize session and run orchestrator:

```bash
python3 <<'EOF'
from with_me.lib.session_orchestrator import SessionOrchestrator
import json

# Initialize orchestrator
orch = SessionOrchestrator()
session_id = orch.initialize_session()

# Output session ID for tracking
print(json.dumps({
    "session_id": session_id,
    "status": "initialized"
}))
EOF
```

### Main Questioning Loop

The orchestrator manages the adaptive questioning process:

**For each iteration:**

1. **Check convergence:**
   ```bash
   python3 <<'EOF'
   from with_me.lib.session_orchestrator import SessionOrchestrator
   orch = SessionOrchestrator()
   # ... restore session state ...
   converged = orch.check_convergence()
   print("converged" if converged else "continue")
   EOF
   ```

2. **Select next question:**
   ```bash
   python3 <<'EOF'
   from with_me.lib.session_orchestrator import SessionOrchestrator
   orch = SessionOrchestrator()
   # ... restore session state ...
   dimension, question = orch.select_next_question()
   print(f"{dimension}:{question}")
   EOF
   ```

3. **Ask user via AskUserQuestion:**
   ```
   Question: <question from orchestrator>
   Header: <dimension short_name>
   multiSelect: false
   Options:
     - "Provide detailed answer"
     - "Provide brief answer"
     - "Skip this question"
     - "End session (clarity achieved)"
   ```

4. **Update beliefs:**
   ```bash
   python3 <<'EOF'
   from with_me.lib.session_orchestrator import SessionOrchestrator
   orch = SessionOrchestrator()
   # ... restore session state ...
   result = orch.update_beliefs(dimension, question, answer)
   print(f"Information gained: {result['information_gain']:.3f} bits")
   EOF
   ```

5. **Display current state:**
   ```bash
   python3 <<'EOF'
   from with_me.lib.session_orchestrator import SessionOrchestrator
   orch = SessionOrchestrator()
   # ... restore session state ...
   state = orch.get_current_state()

   print("\nCurrent Uncertainty (bits):")
   for dim_id, dim_data in state['dimensions'].items():
       status = "✓" if dim_data['converged'] else ""
       blocked = f"  [BLOCKED: needs {', '.join(dim_data['blocked_by'])}]" if dim_data['blocked'] else ""
       bar_length = int(dim_data['entropy'] / 2.0 * 10)
       bar = "█" * bar_length + "░" * (10 - bar_length)
       print(f"  {dim_data['name']:12} {dim_data['entropy']:.2f} {bar}  ({dim_data['confidence']:.0%} confidence) {status}{blocked}")
   EOF
   ```

**Repeat until convergence or user signals completion.**

---

### Post-Convergence Analysis

After convergence, complete session and generate specification:

```bash
python3 <<'EOF'
from with_me.lib.session_orchestrator import SessionOrchestrator
orch = SessionOrchestrator()
# ... restore session state ...
summary = orch.complete_session()
print(f"Session complete: {summary['total_questions']} questions asked")
print(f"Total information gained: {summary['total_info_gain']:.2f} bits")
EOF
```

Then invoke requirement-analysis skill:

```
/with-me:requirement-analysis
```

The skill will:
- Analyze all collected answers
- Detect ambiguities and gaps
- Generate structured requirement specification
- Suggest implementation approach
- Produce acceptance criteria

---

## Best Practices

### For Users

1. **Be specific in answers:** More detail enables better belief updates
2. **Provide examples:** Helps likelihood estimation understand context
3. **Ask for clarification:** If a question is unclear, request rephrasing
4. **Signal when done:** Don't wait for all 50 questions if clarity is achieved

### For Implementation

1. **Persist session state:** Store session_id and beliefs between questions
2. **Handle user interruption:** Allow "Skip" and "End session" options
3. **Display progress:** Show entropy display after each answer
4. **Validate prerequisites:** Orchestrator automatically checks DAG constraints
5. **Record all interactions:** Feedback manager tracks full session history

---

## Error Handling

### No Accessible Dimensions

If `select_next_dimension()` returns `None`:
- All dimensions either converged or blocked by unmet prerequisites
- Force termination and proceed to analysis

**Recovery:** Call `complete_session()` and invoke requirement-analysis

### Session State Loss

If session state is lost mid-session:
- Cannot resume (beliefs cannot be reconstructed)
- Start new session with `/with-me:good-question`

**Prevention:** Persist session_id and beliefs dictionary to temporary file

### Invalid Answers

If user provides off-topic or unclear answer:
- Bayesian update will show minimal information gain
- Question may be repeated or rephrased
- Orchestrator adapts based on posterior distribution

**No explicit handling needed** - Bayesian framework naturally handles noisy data

---

## Configuration

Adjust parameters in `config/dimensions.json`:

```json
{
  "session_config": {
    "convergence_threshold": 0.3,      // Entropy threshold for clarity
    "prerequisite_threshold": 1.5,     // Threshold for prerequisite satisfaction
    "max_questions": 50,                // Safety limit to prevent infinite loops
    "min_questions": 5                  // Minimum before allowing early termination
  }
}
```

For custom dimensions and DAG structure, see theory document section on "Dimension Customization".

---

## References

- **Theory:** `docs/good-question-theory.md` - Mathematical foundation and algorithms
- **Orchestrator:** `with_me/lib/session_orchestrator.py` - Session coordination logic
- **Beliefs:** `with_me/lib/dimension_belief.py` - Bayesian belief updating
- **Rewards:** `with_me/lib/question_reward_calculator.py` - EIG calculation
- **Feedback:** `with_me/lib/question_feedback_manager.py` - Session persistence
- **Analysis Skill:** `skills/requirement-analysis/SKILL.md` - Post-session specification generation
