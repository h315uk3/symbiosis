---
description: "Entropy-reducing requirement elicitation - systematically reduce uncertainty through information-maximizing questions"
allowed-tools: [AskUserQuestion, Read, Glob, Grep, WebFetch, Bash, Skill]
---

# Good Question

**When you can't articulate your requirements, let me ask the right questions.**

This command uses an information-theoretic approach to extract requirements by reducing uncertainty (entropy) through adaptive questioning.

---

## Core Principle: Entropy Reduction

Your requirements exist in an uncertain state. Each question aims to maximize information gain, systematically reducing entropy until clarity emerges.

```
Initial State: H(Requirements) = High (Maximum Uncertainty)
↓ Question 1 (Max Info Gain)
State After Q1: H(Requirements|A1) = Reduced
↓ Question 2 (Max Remaining Info Gain)
State After Q2: H(Requirements|A1,A2) = Further Reduced
↓ ...
Terminal State: H(Requirements|All Answers) < Threshold (Sufficient Clarity)
```

---

## Uncertainty Dimensions

Track implicit uncertainty across five key dimensions:

### 1. Purpose (Why)
- What problem is being solved?
- Who benefits from this?
- What is the core value?

### 2. Data (What)
- What information is involved?
- What are the inputs and outputs?
- What transformations occur?

### 3. Behavior (How)
- What actions take place?
- What triggers the functionality?
- What is the step-by-step flow?

### 4. Constraints (Limits)
- What technical limitations exist?
- What performance requirements matter?
- What compatibility needs exist?

### 5. Quality (Success)
- How is success measured?
- What edge cases exist?
- What could go wrong?

---

## Interview Protocol

### Phase 0: Reference Collection (Optional)

Before beginning the interview, check if the developer has reference materials to save for easy access during the session.

**Ask using AskUserQuestion:**
- Question: "Do you have reference materials to save for this session?"
- Header: "References"
- multiSelect: false
- Options:
  - Label: "Git repository", Description: "Clone a repository to /tmp for reference"
  - Label: "Documentation URL", Description: "Fetch documentation to /tmp"
  - Label: "Local files", Description: "Copy local files to /tmp for reference"
  - Label: "No references", Description: "Continue without saving references"

**If references provided:**
- Git repository: Use Bash tool to `git clone <url> /tmp/ref-<timestamp>-<project>`
- Documentation: Use Bash tool to `curl <url> -o /tmp/ref-<timestamp>-doc.pdf` or `wget <url> -P /tmp/`
- Local files: Use Bash tool to `cp <path> /tmp/ref-<timestamp>-<name>`

**Benefits:**
- References remain accessible throughout the session
- Can be examined later during questioning
- Faster than repeatedly fetching the same resources
- /tmp is automatically cleaned on system restart

**Note:** This phase is optional and can be skipped if the developer has no references or prefers to provide them inline during questioning.

---

### Phase 1: Initial Assessment

**Start tracking this question session:**

```bash
SESSION_ID=$(bash "${CLAUDE_PLUGIN_ROOT}/scripts/commands/good-question-impl.sh" start | jq -r '.session_id')
```

Store `SESSION_ID` in a variable for use throughout this session.

---

Begin with an open question to gauge overall clarity:

**Ask using AskUserQuestion:**
- Question: "What do you want to build?"
- Header: "Starting Point"
- multiSelect: false
- Options:
  - Label: "Let me explain", Description: "I'll describe what I have in mind"
  - Label: "Show you examples", Description: "I have references or similar implementations"
  - Label: "Just a goal", Description: "I know what I want to achieve but not how"

**Based on response:**
- Detailed explanation → Assess which dimensions are clear vs uncertain
- Examples provided → Use Read/Grep/WebFetch to understand, then assess gaps
- Just a goal → Start with Purpose dimension (highest uncertainty)

---

### Phase 2: Adaptive Questioning

At each step, identify the dimension with **highest remaining uncertainty** and ask targeted questions.

#### If Purpose has highest uncertainty:

**Ask using AskUserQuestion:**
- Question: "What problem does this solve?"
- Header: "Purpose"
- multiSelect: false
- Options:
  - Label: "Describe the problem", Description: "Let me explain the problem I'm trying to solve"
  - Label: "User needs", Description: "There's a specific user need or pain point"
  - Label: "Technical requirement", Description: "This is needed for technical reasons"

Follow up with:
- "Who experiences this problem?"
- "What happens if this isn't built?"
- "What does success look like from the user's perspective?"

#### If Data has highest uncertainty:

**Ask using AskUserQuestion:**
- Question: "What data is involved?"
- Header: "Data"
- multiSelect: false
- Options:
  - Label: "Describe the data", Description: "Let me explain the data structure and flow"
  - Label: "Show examples", Description: "I have sample data or schemas"
  - Label: "Not sure yet", Description: "I haven't thought about the data structure"

Follow up with:
- "What triggers data to enter the system?"
- "What format is the data in?"
- "What information must be preserved vs transformed?"

#### If Behavior has highest uncertainty:

**Ask using AskUserQuestion:**
- Question: "What should happen step by step?"
- Header: "Behavior"
- multiSelect: false
- Options:
  - Label: "Walk through it", Description: "Let me describe the flow step by step"
  - Label: "Similar to existing", Description: "It works like [reference] but with differences"
  - Label: "Uncertain", Description: "I'm not sure about the exact flow"

Follow up with:
- "What initiates this process?"
- "What are the critical decision points?"
- "When does the process complete?"

#### If Constraints have highest uncertainty:

**Ask using AskUserQuestion:**
- Question: "Any constraints I should know about?"
- Header: "Constraints"
- multiSelect: true
- Options:
  - Label: "Performance critical", Description: "Speed, memory, or latency requirements"
  - Label: "Security sensitive", Description: "Authentication, authorization, or data protection"
  - Label: "Compatibility needs", Description: "Must work with specific versions or systems"
  - Label: "No specific constraints", Description: "Standard practices are fine"

For each selected constraint, drill deeper:
- Performance: "What are the acceptable thresholds?"
- Security: "What are the threat scenarios?"
- Compatibility: "What must be supported?"

#### If Quality has highest uncertainty:

**Ask using AskUserQuestion:**
- Question: "How do you know it works correctly?"
- Header: "Quality"
- multiSelect: false
- Options:
  - Label: "Describe test cases", Description: "I can explain what scenarios to test"
  - Label: "Follow standards", Description: "Apply standard testing practices"
  - Label: "Not sure", Description: "I need help defining success criteria"

Follow up with:
- "What are the critical success scenarios?"
- "What edge cases concern you?"
- "What failure modes should be handled?"

---

### Phase 3: Convergence Detection

After each answer, assess:

**CRITICAL: Before calculating uncertainty, translate content to English**

The uncertainty calculator uses word count analysis, which only works correctly with English text. Before calling `uncertainty_calculator.py`:

1. **Translate all `content` fields to English**
   - Detect if content is non-English (Japanese, etc.)
   - If non-English: Translate to English while preserving technical terms
   - If already English: Use as-is
   - This ensures consistent word count calculation across languages

Example:
```python
# Before (Japanese content - word count = 1)
"content": "機微情報漏洩防止、配信者一般向け、リスクと価値提案が明確"

# After translation (English content - word count = 12)
"content": "Prevent sensitive information leakage, for general streamers, risks and value proposition are clear"
```

**Then perform uncertainty assessment and record the question:**

1. **Calculate uncertainty scores** (with translated English content):
   ```bash
   UNCERTAINTIES=$(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/uncertainty_calculator.py" "$DIMENSION_DATA_JSON")
   ```

   Where `DIMENSION_DATA_JSON` contains all dimension data with translated English content:
   ```json
   {
     "purpose": {"answered": true, "content": "Translated English text...", "examples": 2, "contradictions": false},
     "data": {"answered": true, "content": "Translated English text...", "examples": 1, "contradictions": false},
     ...
   }
   ```

   The script outputs uncertainty scores and recommendations:
   ```json
   {
     "uncertainties": {"purpose": 0.2, "data": 0.5, ...},
     "continue_questioning": true,
     "next_focus": "data"
   }
   ```

2. **Record this question-answer pair:**
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/commands/good-question-impl.sh" record \
     "$SESSION_ID" \
     "$QUESTION_TEXT" \
     "$CONTEXT_JSON" \
     "$ANSWER_JSON"
   ```

   Where:
   - `CONTEXT_JSON`: `{"dimension": "...", "uncertainties_before": {...}, "uncertainties_after": {...}}`
   - `ANSWER_JSON`: `{"text": "...", "word_count": N, "has_examples": true/false}`

3. **Assess progress:**
   - Did this reduce uncertainty significantly?
     - Yes → Continue on this dimension with deeper questions
     - No → Move to next highest-uncertainty dimension

   - Is this dimension now sufficiently clear?
     - Yes → Mark dimension as resolved, move to next
     - No → Continue questioning this dimension

   - Are all dimensions sufficiently clear?
     - Yes → Proceed to validation phase
     - No → Continue adaptive questioning

---

### Phase 4: Validation & Gap Analysis

When most dimensions have low uncertainty:

**Summarize your understanding:**
```markdown
## My Understanding

### Purpose
[What problem this solves and for whom]

### Data
[Input/output/transformations]

### Behavior
[Step-by-step flow]

### Constraints
[Technical limitations and requirements]

### Quality
[Success criteria and edge cases]
```

**Then ask using AskUserQuestion:**
- Question: "Does this capture your requirements correctly?"
- Header: "Validation"
- multiSelect: false
- Options:
  - Label: "Yes, accurate", Description: "This correctly represents what I want"
  - Label: "Needs refinement", Description: "Close, but some aspects need adjustment"
  - Label: "Missing key aspects", Description: "There are important parts not covered"

If refinement needed, identify remaining gaps and ask targeted follow-ups.

---

### Phase 5: Analysis (Forked Context)

Once all dimensions are sufficiently clear and validated:

**Complete the question session tracking:**

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/commands/good-question-impl.sh" complete \
  "$SESSION_ID" \
  "$FINAL_UNCERTAINTIES_JSON"
```

Where `FINAL_UNCERTAINTIES_JSON` contains the final uncertainty scores for all dimensions:
```json
{"purpose": 0.2, "data": 0.3, "behavior": 0.25, "constraints": 0.15, "quality": 0.28}
```

This generates session statistics for the `/with-me:stats` command.

---

**Invoke the requirement-analysis skill:**

The `requirement-analysis` skill uses `context: fork`, which automatically runs in an isolated sub-agent context, keeping the main session clean.

Simply invoke the skill with all collected information:

```
Use the requirement-analysis skill to analyze the gathered requirements.

Provide all collected answers and context:
- Purpose: [answers from Purpose dimension]
- Data: [answers from Data dimension]
- Behavior: [answers from Behavior dimension]
- Constraints: [answers from Constraints dimension]
- Quality: [answers from Quality dimension]

The skill will generate:
1. Structured requirement specification
2. Identified ambiguities or contradictions
3. Implementation approach suggestions
4. Risk assessment and challenges
```

The skill automatically runs in a forked context, so the analysis won't pollute the main conversation.

---

## Questioning Heuristics

### Information Gain Prioritization

Choose questions that maximize expected information gain:

**High Gain Questions:**
- Open-ended: "Describe..." "Explain..." "Walk me through..."
- Reveal unknowns: "What haven't we discussed?"
- Expose conflicts: "How does X relate to Y?"

**Medium Gain Questions:**
- Binary choices: "Is this performance-critical?"
- Categorical: "Which type of feature is this?"

**Low Gain Questions:**
- Confirmations: "Is this correct?"
- Already-implied information

### Adaptive Depth

- High uncertainty → Broad exploratory questions
- Medium uncertainty → Targeted clarification questions
- Low uncertainty → Validation questions

### Branching Logic

Based on answer patterns:
- Vague answers → Increase question specificity
- Detailed answers → Extract implied constraints and assumptions
- Contradictory answers → Resolve conflicts immediately
- Confident answers → Validate with edge cases

---

## Interviewing Principles

### Do:
- Ask questions that reduce the most uncertainty
- Drill deeper when answers are vague or reveal new uncertainty
- Validate understanding before moving to next dimension
- Use Read/Grep/WebFetch when references are provided
- Adjust questioning based on developer's communication style
- Summarize and confirm understanding regularly

### Don't:
- Ask questions about dimensions that are already clear
- Accept ambiguity when clarification would significantly reduce uncertainty
- Make assumptions without validation
- Continue questioning past the point of diminishing returns
- Skip validation even if you think you understand

---

## Terminal Conditions

End the interview when:

1. **Sufficient Clarity:** All dimensions below uncertainty threshold
2. **Diminishing Returns:** No available question would significantly reduce remaining uncertainty
3. **Implementation Ready:** You have enough context to proceed confidently
4. **Developer Confirmation:** Developer validates your understanding

Then invoke the `requirement-analysis` skill, which runs in a forked context to generate the formal specification without polluting the main conversation.

---

## Success Criteria

This command succeeds when:
- Uncertainty has been systematically reduced across all dimensions
- No critical ambiguities remain
- Clear implementation path is identified
- Developer feels understood and requirements are captured
- The resulting specification enables confident implementation

**The developer should think "good question" after each question** - meaning the questions surface aspects they hadn't articulated or help them clarify what they couldn't express.
