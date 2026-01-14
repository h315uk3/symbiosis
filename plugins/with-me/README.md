# With Me

**"You work with me (Claude)" - Collaborative AI assistant**

Working with you, Claude elicits requirements through entropy-reducing communication and adaptive questioning.

---

## Available Commands

### `/with-me:good-question` - Entropy-Reducing Requirement Elicitation

When you can't articulate your requirements, this command uses an information-theoretic approach to systematically reduce uncertainty through adaptive questioning.

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
