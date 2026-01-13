---
description: "Interactive requirement clarification - systematically ask developers targeted questions to gather context, references, and constraints"
allowed-tools: [AskUserQuestion, Read, Glob, Grep, WebFetch]
---

# Good Question

**When you can't articulate your requirements, let me ask the right questions.**

This command helps developers who struggle to express their needs by conducting a structured interview to gather all necessary context for implementation.

---

## What This Command Does

You will conduct a comprehensive, multi-stage interview to understand the developer's needs. The goal is to extract:

1. **Reference Materials**: Documentation, APIs, specifications
2. **Implementation Context**: Existing code, similar implementations
3. **Requirements**: Expected behavior, inputs/outputs
4. **Constraints**: Technical limitations, performance needs
5. **Edge Cases**: Error handling, validation requirements
6. **Quality Attributes**: Security, performance, maintainability

---

## Interview Protocol

### Stage 1: Information Sources

**Question 1 - Documentation**

Ask using AskUserQuestion:
- Question: "Do you have reference documentation or specifications I should review before starting?"
- Header: "Docs"
- Options:
  - Label: "Yes, specific docs/URLs", Description: "I have specific documentation, API specs, or technical resources to share"
  - Label: "Check official docs", Description: "Review the official documentation for the technology/library being used"
  - Label: "No documentation", Description: "No specific documentation available"
  - Label: "Not sure", Description: "I'm not sure what documentation would be relevant"

If "Yes" or "Check official", ask for specifics via free text:
- URLs or file paths
- Specific sections to focus on

**Question 2 - Existing Code**

Ask using AskUserQuestion:
- Question: "Is there existing code I should reference or learn from?"
- Header: "Reference Code"
- Options:
  - Label: "Files in this project", Description: "Specific files or modules in the current codebase"
  - Label: "Similar feature", Description: "Similar functionality implemented elsewhere in the project"
  - Label: "External examples", Description: "Open source projects or examples from other codebases"
  - Label: "No reference code", Description: "This is a new implementation without existing examples"

If code references provided:
- Use Read, Glob, or Grep to examine the code
- Ask clarifying questions about patterns to follow or avoid

---

### Stage 2: Requirements & Behavior

**Question 3 - Primary Goal**

Ask using AskUserQuestion:
- Question: "What type of functionality are you building?"
- Header: "Functionality"
- multiSelect: true
- Options:
  - Label: "Data processing", Description: "Transform, validate, or manipulate data"
  - Label: "User interface", Description: "UI components, forms, displays, interactions"
  - Label: "API/Service", Description: "Backend endpoints, services, or integrations"
  - Label: "Integration", Description: "Connect with external systems, APIs, or services"

Based on the answer, ask follow-up questions about:
- Specific inputs and outputs
- Data formats and structures
- User interactions or API contracts

**Question 4 - Input/Output Specifications**

Ask via free text prompt:
```
Please describe:
1. What are the inputs? (types, formats, examples)
2. What should the output be? (types, formats, examples)
3. What transformations or processing should happen?
4. Are there any data volume or scale considerations?
```

---

### Stage 3: Constraints & Requirements

**Question 5 - Technical Constraints**

Ask using AskUserQuestion:
- Question: "What technical constraints or requirements should I consider?"
- Header: "Constraints"
- multiSelect: true
- Options:
  - Label: "Performance critical", Description: "Speed, memory usage, or latency requirements"
  - Label: "Security sensitive", Description: "Authentication, authorization, data protection"
  - Label: "Compatibility needs", Description: "Must work with specific versions, browsers, or systems"
  - Label: "Library restrictions", Description: "Must use or avoid specific libraries/frameworks"

For each selected constraint, ask follow-up questions:
- Performance: What are the acceptable thresholds?
- Security: What threat model should I consider?
- Compatibility: What versions/systems must be supported?
- Libraries: What should I use or avoid, and why?

**Question 6 - Error Handling**

Ask using AskUserQuestion:
- Question: "How should errors and edge cases be handled?"
- Header: "Error Handling"
- Options:
  - Label: "Strict validation", Description: "Fail fast with clear error messages for invalid inputs"
  - Label: "Graceful degradation", Description: "Handle errors smoothly, provide fallback behavior"
  - Label: "Retry logic", Description: "Automatically retry failed operations with backoff"
  - Label: "User guidance", Description: "Provide helpful error messages that guide users to fix issues"

---

### Stage 4: Clarification & Validation

Based on all previous answers, identify and ask about:

1. **Ambiguities**: Any unclear or contradictory requirements
2. **Missing Details**: Aspects not yet covered that are necessary
3. **Assumptions**: Validate assumptions you need to make
4. **Preferences**: When multiple approaches are valid, ask for preference

Use AskUserQuestion or free text prompts as appropriate.

---

## Interview Guidelines

**Do:**
- Ask one stage at a time, don't overwhelm
- Drill deeper when answers are vague
- Reference specific files or URLs when provided
- Actually fetch and read documentation (WebFetch) if URLs given
- Actually read code files (Read, Glob, Grep) if mentioned
- Summarize understanding and ask for confirmation
- Ask follow-up questions to resolve ambiguity

**Don't:**
- Ask redundant questions
- Accept vague answers without clarification
- Move forward with ambiguity
- Make assumptions without validation
- Skip stages unless clearly not applicable

---

## Final Deliverable

After completing the interview, provide a structured summary:

```markdown
## Requirements Analysis

### Information Sources
- Documentation: [URLs, file paths, or "None provided"]
- Reference Code: [Files, patterns, or "None"]
- External Resources: [Any additional context]

### Functional Requirements
- Primary Goal: [What needs to be built]
- Inputs: [Types, formats, examples]
- Outputs: [Types, formats, examples]
- Processing: [Transformations, business logic]

### Technical Requirements
- Performance: [Requirements or "No specific requirements"]
- Security: [Considerations or "Standard practices"]
- Compatibility: [Constraints or "None"]
- Technology Stack: [Required/prohibited libraries]

### Error Handling Strategy
- Approach: [Chosen strategy]
- Validation: [Input validation requirements]
- Error Messages: [User-facing or developer-facing]

### Implementation Considerations
- [Key architectural decisions]
- [Patterns to follow]
- [Patterns to avoid]
- [Testing requirements]

### Uncertainties
- [Any remaining ambiguities to resolve during implementation]

## Recommended Next Steps
1. [First action based on gathered information]
2. [Second action]
3. [Continue...]
```

---

## Success Criteria

This command succeeds when:
- All necessary context has been gathered
- No significant ambiguity remains
- Clear implementation path is identified
- Developer feels understood and heard
- You have enough information to proceed confidently

The developer should think "good question" after each question you ask - meaning the questions surface aspects they hadn't considered or help them articulate what they couldn't express.
