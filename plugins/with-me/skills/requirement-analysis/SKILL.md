---
description: "Analyze collected requirements from interviews, detect ambiguities, generate structured specifications, and suggest implementation approaches"
context: fork
allowed-tools: [Bash, Read]
---

# Requirement Analysis Skill

This skill transforms raw interview data into structured, actionable requirement specifications.

---

## When to Use This Skill

Use this skill after completing a requirement elicitation interview (e.g., via `/good-question`) when you have:
- Collected answers across multiple requirement dimensions
- Raw notes from developer conversations
- Unstructured information that needs formalization

**Do not use this skill:**
- During active interviews (use it after information gathering is complete)
- For code analysis or implementation tasks
- When requirements are already well-structured

---

## What This Skill Does

### 1. Structure Requirements

Transform raw interview data into a formal specification organized by:
- **Purpose**: Problem statement, stakeholders, value proposition
- **Data**: Input/output specifications, data models, transformations
- **Behavior**: Functional flows, state transitions, business logic
- **Constraints**: Technical requirements, limitations, dependencies
- **Quality**: Success criteria, testing requirements, edge cases

### 2. Detect Issues

Identify and report:
- **Ambiguities**: Vague or underspecified requirements
- **Contradictions**: Conflicting statements or incompatible requirements
- **Gaps**: Missing information critical for implementation
- **Assumptions**: Implicit assumptions that need validation

### 3. Generate Implementation Guidance

Provide:
- **Architecture Recommendations**: Suggested technical approaches
- **Risk Assessment**: Potential challenges and mitigation strategies
- **Testing Strategy**: Test scenarios based on requirements
- **Open Questions**: Remaining uncertainties to resolve

---

## Input Format

Provide the raw interview data in any format:

```markdown
## Interview Transcript

User said: "I want to build a dashboard..."
Question 1: What problem does this solve?
Answer: "Users need to see their metrics..."

Question 2: What data is involved?
Answer: "User activity logs, API call counts..."

[etc.]
```

Or as structured notes:

```markdown
## Collected Information

Purpose: Users need visibility into system metrics
Data: Time-series data from monitoring APIs
Behavior: Real-time updates every 30 seconds
Constraints: Must work in mobile browsers
Quality: No specific test requirements mentioned
```

---

## Output Format

### Structured Requirement Specification

```markdown
# Requirement Specification: [Project Name]

## 1. Purpose & Context

### Problem Statement
[Clear description of the problem being solved]

### Stakeholders
[Who will use this and how they benefit]

### Success Criteria
[What defines a successful implementation]

---

## 2. Functional Requirements

### Data Requirements

#### Inputs
- **Source**: [Where data comes from]
- **Format**: [Data structure and types]
- **Volume**: [Expected scale]
- **Validation**: [Required validations]

#### Outputs
- **Destination**: [Where results go]
- **Format**: [Output structure]
- **Transformations**: [Processing applied]

### Behavioral Requirements

#### Primary Flow
1. [Step-by-step description]
2. [Decision points and conditions]
3. [State changes]

#### Alternative Flows
- **Scenario**: [Alternative path description]
- **Trigger**: [What causes this path]

#### Edge Cases
- [Edge case 1]
- [Edge case 2]

---

## 3. Non-Functional Requirements

### Performance
- [Latency requirements]
- [Throughput requirements]
- [Resource constraints]

### Security
- [Authentication requirements]
- [Authorization rules]
- [Data protection needs]

### Compatibility
- [Platform requirements]
- [Browser/version support]
- [Dependency constraints]

---

## 4. Quality Requirements

### Testing Strategy
- **Unit Tests**: [What to test at unit level]
- **Integration Tests**: [What to test at integration level]
- **User Acceptance**: [How users will validate]

### Acceptance Criteria
- [ ] [Specific measurable criterion 1]
- [ ] [Specific measurable criterion 2]

---

## 5. Implementation Considerations

### Recommended Architecture
[Suggested technical approach with rationale]

### Technology Stack
- **Required**: [Must-use technologies]
- **Recommended**: [Suggested technologies]
- **Avoid**: [Technologies to avoid and why]

### Key Design Decisions
1. **Decision**: [What needs to be decided]
   - **Options**: [Available choices]
   - **Recommendation**: [Suggested choice with reasoning]

---

## 6. Risks & Challenges

### Technical Risks
- **Risk**: [Description]
  - **Impact**: [Severity]
  - **Mitigation**: [How to address]

### Requirement Risks
- **Risk**: [Ambiguity or gap]
  - **Impact**: [Effect on implementation]
  - **Resolution**: [How to clarify]

---

## 7. Open Questions

Questions that require clarification before or during implementation:

1. [Question about unclear aspect]
   - **Why it matters**: [Impact on implementation]
   - **Suggested resolution**: [How to resolve]

2. [Next question]

---

## 8. Next Steps

Recommended actions:

1. **Immediate**: [What to do right away]
2. **Before Implementation**: [Prerequisites]
3. **During Implementation**: [Ongoing considerations]
```

---

## Analysis Process

### Step 1: Organize Information

Group collected data by the five dimensions:
- Purpose answers → Problem statement, stakeholders
- Data answers → Input/output specifications
- Behavior answers → Functional flows
- Constraint answers → Non-functional requirements
- Quality answers → Testing strategy

### Step 2: Identify Issues

Scan for:
- **Ambiguous statements**: "fast enough", "user-friendly", "secure"
- **Contradictions**: Performance vs. feature richness conflicts
- **Gaps**: No mention of error handling, no data validation discussed
- **Implicit assumptions**: "Users will know how to...", "Data will always be..."

### Step 3: Synthesize Recommendations

Based on the requirements:
- Match requirements to appropriate architectural patterns
- Identify suitable technologies and frameworks
- Propose testing approaches aligned with quality needs
- Highlight design decisions that need stakeholder input

### Step 4: Assess Risks

Consider:
- **Complexity risks**: Requirements that suggest high complexity
- **Uncertainty risks**: Underspecified areas prone to rework
- **Dependency risks**: External systems or data sources
- **Performance risks**: Scale or speed requirements that may be challenging

---

## Example Usage

**Input:**
```
User wants to build a file upload feature with progress tracking.
- Files up to 1GB
- Must show upload progress
- Support multiple simultaneous uploads
- Works on mobile
- Mentioned "secure" but didn't specify details
```

**Analysis Output:**

```markdown
# Requirement Specification: File Upload Feature

## 1. Purpose & Context
### Problem Statement
Users need to upload large files (up to 1GB) with visibility into upload progress.

### Stakeholders
- End users uploading files from desktop and mobile browsers
- Backend system receiving and processing uploads

### Success Criteria
- Files up to 1GB upload successfully
- Progress is visible throughout upload
- Multiple uploads can occur concurrently
- Works on mobile browsers

---

## 2. Functional Requirements

### Data Requirements
#### Inputs
- **Source**: User file selection (browser file input)
- **Format**: Binary files, any MIME type, max 1GB
- **Validation**: File size must not exceed 1GB
- **Volume**: Multiple concurrent uploads per user

#### Outputs
- **Destination**: Server storage endpoint
- **Format**: Uploaded file plus metadata (filename, size, MIME type)
- **Confirmation**: Upload completion status

### Behavioral Requirements
#### Primary Flow
1. User selects file(s) to upload
2. System validates file size (reject if >1GB)
3. Upload begins with chunking for progress tracking
4. Progress indicator updates as chunks complete
5. Upload completes, user receives confirmation

#### Alternative Flows
- **Network interruption**: Resume or retry mechanism needed
- **Validation failure**: Clear error message shown

#### Edge Cases
- Upload interrupted mid-transfer
- Multiple uploads competing for bandwidth
- Mobile network transitions (WiFi to cellular)

---

## 3. Non-Functional Requirements

### Performance
- Progress updates at least every 2-3 seconds
- Multiple uploads shouldn't block UI
- Mobile browsers may have memory constraints

### Security
⚠️ **AMBIGUITY DETECTED**: "Secure" was mentioned but not specified.
**Needs clarification:**
- Authentication required before upload?
- File type restrictions (prevent malicious files)?
- HTTPS required?
- Virus scanning?

### Compatibility
- Must work in mobile browsers (iOS Safari, Android Chrome)
- Desktop browser support (Chrome, Firefox, Safari, Edge)

---

## 4. Quality Requirements

### Testing Strategy
- **Unit Tests**: Chunking logic, progress calculation
- **Integration Tests**: Upload flow end-to-end
- **Load Tests**: Multiple concurrent uploads
- **Mobile Tests**: Network interruption handling

### Acceptance Criteria
- [ ] 1GB file uploads successfully
- [ ] Progress bar updates smoothly
- [ ] 3 simultaneous uploads work without issues
- [ ] Feature works on iOS Safari and Android Chrome

---

## 5. Implementation Considerations

### Recommended Architecture
- **Chunked uploads**: Split large files into chunks (5-10MB) for progress tracking and resumability
- **Background workers**: Use Web Workers to avoid blocking main thread
- **Upload queue**: Manage concurrent uploads to prevent resource exhaustion

### Technology Stack
- **Recommended**:
  - XMLHttpRequest or Fetch API with upload progress events
  - File API for client-side chunking
  - Server: Multipart upload or chunked transfer encoding
- **Avoid**:
  - Simple form POST (no progress tracking)

### Key Design Decisions
1. **Chunking Strategy**
   - **Options**: Fixed chunk size vs. adaptive based on network speed
   - **Recommendation**: Fixed 5MB chunks for simplicity

2. **Resume Mechanism**
   - **Options**: Store upload state server-side vs. client-side
   - **Recommendation**: Server-side with upload ID for reliability

---

## 6. Risks & Challenges

### Technical Risks
- **Mobile memory limits**: 1GB file may exceed mobile browser memory
  - **Mitigation**: Stream chunks without loading entire file

- **Network instability**: Mobile uploads prone to interruption
  - **Mitigation**: Implement resumable uploads

### Requirement Risks
- **Security underspecified**: Unknown threat model
  - **Resolution**: Clarify authentication and file validation needs

---

## 7. Open Questions

1. **What security measures are required?**
   - Why it matters: Affects authentication, validation, scanning
   - Suggested resolution: Ask about user authentication and file type restrictions

2. **What happens after upload completes?**
   - Why it matters: May need webhooks, notifications, or processing triggers
   - Suggested resolution: Clarify post-upload workflow

3. **What's the expected concurrent upload limit per user?**
   - Why it matters: Affects queue design and resource allocation
   - Suggested resolution: Define reasonable upper bound (e.g., 5 uploads)

---

## 8. Next Steps

1. **Immediate**: Clarify security requirements (authentication, file validation)
2. **Before Implementation**: Decide on chunking and resume strategy
3. **During Implementation**: Test on actual mobile devices early
```

---

## Best Practices

### Do:
- Organize scattered information into clear structure
- Call out ambiguities explicitly with specific questions
- Provide rationale for recommendations
- Identify risks with concrete mitigation strategies
- Use acceptance criteria as implementation checklist

### Don't:
- Make assumptions about unclear requirements (call them out instead)
- Recommend technologies without justification
- Ignore contradictions or conflicts
- Over-engineer solutions beyond stated needs
- Skip risk assessment even for "simple" requirements

---

## Success Criteria

This skill succeeds when:
- Requirements are structured and unambiguous
- All critical gaps and contradictions are identified
- Implementation guidance is actionable
- Risk assessment is realistic and helpful
- The specification enables confident implementation

---

## Uncertainty Quantification & Loop Decision

After generating the initial specification, quantify remaining uncertainty to determine if additional questioning is needed.

### Step 1: Prepare Dimension Data

Based on the collected information, assess each dimension:

```json
{
  "purpose": {
    "answered": true/false,
    "content": "summary of what was learned",
    "examples": number_of_examples_provided,
    "contradictions": true/false
  },
  "data": { ... },
  "behavior": { ... },
  "constraints": { ... },
  "quality": { ... }
}
```

### Step 2: Calculate Uncertainty

Use the uncertainty_calculator.py script to quantify uncertainty:

```bash
python3 ../../scripts/uncertainty_calculator.py '<json_data>'
```

The script will output:
- Uncertainty score for each dimension (0.0-1.0)
- Overall certainty percentage
- Recommendation on whether to continue questioning
- Which dimension needs the most attention

### Step 3: Loop Decision

**If `continue_questioning: true`:**
1. Include the uncertainty analysis in your response
2. Identify the dimension with highest uncertainty
3. Recommend returning to the good-question interview for additional clarification
4. Specify what aspects need further exploration

**If `continue_questioning: false`:**
1. Include the final uncertainty analysis showing all dimensions are sufficiently clear
2. Proceed with generating the complete specification
3. Mark any remaining minor ambiguities in the "Open Questions" section

### Example Output (High Uncertainty - Loop Back)

```markdown
## Uncertainty Analysis

✗ Data: 20% certain (uncertainty: 0.80)
⚠ Behavior: 55% certain (uncertainty: 0.45)
✓ Purpose: 85% certain (uncertainty: 0.15)
✓ Constraints: 90% certain (uncertainty: 0.10)
✓ Quality: 75% certain (uncertainty: 0.25)

Overall Certainty: 65%

Recommendation: Focus next questions on Data dimension

---

## Analysis Result

While the purpose and constraints are well understood, the **data structure and flow remain highly uncertain**.

**Recommendation**: Return to the interview and ask targeted questions about:
1. Specific data schemas and formats
2. Data validation requirements
3. Data transformation steps
4. Data volume and scale considerations

Once the Data dimension achieves >70% certainty, this analysis should be repeated.
```

### Example Output (Sufficient Clarity - Proceed)

```markdown
## Uncertainty Analysis

✓ Purpose: 90% certain (uncertainty: 0.10)
✓ Data: 80% certain (uncertainty: 0.20)
✓ Behavior: 85% certain (uncertainty: 0.15)
✓ Constraints: 95% certain (uncertainty: 0.05)
✓ Quality: 75% certain (uncertainty: 0.25)

Overall Certainty: 85%

Recommendation: Sufficient clarity achieved, proceed to validation

---

## Requirements Specification

[Generate complete specification as described earlier in this skill]
```

### Important Notes

- **Threshold**: Default uncertainty threshold is 0.3 (70% certainty). Any dimension above this triggers a loop recommendation.
- **Script Location**: The uncertainty_calculator.py script is located at `../../scripts/uncertainty_calculator.py` relative to this skill.
- **JSON Format**: Ensure the JSON passed to the script is properly formatted and escaped.
- **Iterative Refinement**: Each loop iteration should target the highest-uncertainty dimension first, following the information gain maximization principle.
