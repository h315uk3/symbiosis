# Test Scenario: Full Requirement Sessions

Complete end-to-end requirement elicitation scenarios simulating real-world use cases.

## Purpose

Test the entire workflow from initial prompt to final specification with realistic project scenarios. Verify that the adaptive questioning system produces comprehensive and accurate requirements.

## Scenario 1: Web Application Project

### Prerequisites
- [ ] Fresh Claude Code session
- [ ] with-me plugin installed and configured

### Test Scenario: E-commerce Platform

#### Step 1: Initial Request
Provide initial context to Claude:

```
I need to build an e-commerce platform for selling handmade crafts. Can you help me define the requirements?
```

**Expected behavior:**
- [ ] LLM suggests using `/with-me:good-question`
- [ ] Initiates requirement session

Execute:
```
/with-me:good-question
```

#### Step 2: Answer Questions Consistently
Answer questions based on this scenario profile:

**Project Context:**
- Purpose: E-commerce platform
- Target: Small craft vendors
- Scale: 50-100 concurrent users
- Timeline: 3 months MVP
- Budget: Limited (small team)
- Features: Product catalog, shopping cart, payment processing, vendor dashboard
- Tech preferences: Modern web stack, cloud hosting
- Performance: Standard e-commerce expectations
- Security: PCI compliance required

**Answer questions naturally** based on this profile. The system will ask different questions in different orders, but maintain consistency.

**Expected behavior:**
- [ ] Questions probe different dimensions:
  - Purpose and goals
  - User types and scale
  - Core features
  - Technical requirements
  - Performance needs
  - Security requirements
  - Timeline and resources
- [ ] Questions become more specific as session progresses
- [ ] Follow-up questions based on previous answers
- [ ] No contradictory questions

#### Step 3: Verify Question Quality
Throughout the session, check question quality:

**Good questions:**
- [ ] Clear and focused (one thing at a time)
- [ ] Relevant to previous answers
- [ ] Not duplicate or redundant
- [ ] Appropriate level of detail (broad early, specific later)
- [ ] Options are mutually exclusive (unless multi-select)

**Bad questions (should NOT appear):**
- [ ] Asking same thing twice
- [ ] Irrelevant to project type
- [ ] Too vague ("What do you want?")
- [ ] Compound questions (multiple questions in one)

#### Step 4: Convergence
Continue until convergence (typically 10-15 questions for complex projects).

**Expected behavior:**
- [ ] Session converges when most dimensions have low entropy
- [ ] Completion message displayed
- [ ] Proceeds to specification generation

#### Step 5: Verify Requirement Specification
Review the generated specification.

**Must include:**
- [ ] Project overview matching initial context
- [ ] Functional requirements:
  - [ ] Product catalog with search/filter
  - [ ] Shopping cart functionality
  - [ ] Payment processing integration
  - [ ] Vendor dashboard
  - [ ] Order management
- [ ] Non-functional requirements:
  - [ ] Performance targets (50-100 concurrent users)
  - [ ] Security requirements (PCI compliance)
  - [ ] Scalability considerations
- [ ] Technical considerations:
  - [ ] Modern web stack
  - [ ] Cloud hosting
  - [ ] Database requirements
- [ ] Timeline: 3-month MVP
- [ ] Success criteria

**Must NOT include:**
- [ ] Hallucinated features not mentioned
- [ ] Contradictions with answers
- [ ] Irrelevant technologies
- [ ] Unrealistic expectations

**Verification:**
```bash
# Check session file
cat .claude/with_me/sessions/*.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Questions asked: {data.get(\"question_count\", 0)}')
print(f'Information gain: {data.get(\"total_info_gain\", 0):.2f} bits')
print(f'Dimensions covered: {len(data.get(\"dimensions\", {}))}')
for dim, state in data.get('dimensions', {}).items():
    print(f'  {dim}: entropy={state.get(\"entropy\", 0):.2f}, confidence={state.get(\"confidence\", 0):.0%}')
"
```

Expected:
- [ ] 10-15 questions
- [ ] Total IG: 7-12 bits
- [ ] Most dimensions have entropy <0.5 (high confidence)

---

## Scenario 2: CLI Tool Project

### Test Scenario: File Backup Utility

#### Step 1: Initial Request
```
I want to create a command-line tool for backing up files to cloud storage.
```

Execute:
```
/with-me:good-question
```

#### Step 2: Answer Questions

**Project Context:**
- Purpose: CLI backup tool
- Target: Technical users (developers, sysadmins)
- Scale: Single-user, local execution
- Features: Incremental backups, encryption, multiple cloud providers
- Tech: Go or Rust (performance-critical)
- Performance: Handle large files (>1GB)
- Security: End-to-end encryption
- Timeline: Personal project, no deadline

Answer questions based on this profile.

**Expected behavior:**
- [ ] Questions adapt to CLI tool context (no UI questions)
- [ ] Focus on performance, reliability, data handling
- [ ] Technical depth appropriate for developer tool

#### Step 3: Verify Specification
**Must include:**
- [ ] CLI interface design
- [ ] Incremental backup strategy
- [ ] Encryption requirements
- [ ] Cloud provider support (multiple)
- [ ] Performance considerations (large files)
- [ ] Error handling and recovery
- [ ] Configuration management

**Must NOT include:**
- [ ] UI/UX requirements (it's CLI)
- [ ] User authentication (single-user)
- [ ] Concurrency requirements (local tool)

---

## Scenario 3: Data Analysis Project

### Test Scenario: Sales Analytics Dashboard

#### Step 1: Initial Request
```
We need to analyze sales data and visualize trends for management reporting.
```

Execute:
```
/with-me:good-question
```

#### Step 2: Answer Questions

**Project Context:**
- Purpose: Data analysis and visualization
- Target: Management team (non-technical)
- Data: Sales transactions, customer data
- Scale: Company-wide (500 employees, 10K customers)
- Features: Interactive dashboards, reports, trend analysis, forecasting
- Tech: Python (pandas, plotly) or BI tool
- Performance: Real-time updates not critical
- Security: Internal access only, role-based permissions
- Timeline: 2 months

Answer questions based on this profile.

**Expected behavior:**
- [ ] Questions focus on data sources and analytics needs
- [ ] Explore visualization requirements
- [ ] Clarify user access and permissions
- [ ] Less emphasis on technical implementation (business-focused)

#### Step 3: Verify Specification
**Must include:**
- [ ] Data sources and integration
- [ ] Key metrics and KPIs
- [ ] Visualization types (charts, graphs, tables)
- [ ] Interactive filtering capabilities
- [ ] Report generation
- [ ] User roles and access control
- [ ] Data refresh frequency

---

## Scenario 4: Mobile App Project

### Test Scenario: Fitness Tracking App

#### Step 1: Initial Request
```
Build a mobile app for tracking workouts and nutrition.
```

Execute:
```
/with-me:good-question
```

#### Step 2: Answer Questions

**Project Context:**
- Purpose: Mobile fitness app
- Target: Fitness enthusiasts, beginners
- Platform: iOS and Android (cross-platform)
- Scale: 1000+ users
- Features: Workout logging, nutrition tracking, progress charts, social features
- Tech: React Native or Flutter
- Performance: Offline support, sync when online
- Integrations: Wearables (Fitbit, Apple Watch)
- Monetization: Freemium model
- Timeline: 6 months

Answer questions based on this profile.

**Expected behavior:**
- [ ] Questions cover mobile-specific concerns (platform, offline support)
- [ ] Explore user engagement features
- [ ] Clarify data privacy (health data)
- [ ] Business model considerations

#### Step 3: Verify Specification
**Must include:**
- [ ] Platform requirements (iOS/Android)
- [ ] Core features (workout, nutrition, progress)
- [ ] Offline functionality
- [ ] Data synchronization
- [ ] Wearable integrations
- [ ] Privacy and data security (health data)
- [ ] Monetization strategy
- [ ] User onboarding flow

---

## Scenario 5: Contradictory Requirements (Edge Case)

### Test Scenario: Intentional Inconsistencies

#### Step 1: Initial Request
```
I need a web application for real-time collaboration.
```

Execute:
```
/with-me:good-question
```

#### Step 2: Provide Contradictory Answers
Intentionally answer inconsistently to test robustness:

- Q: "How many users?" → A: "Thousands concurrently"
- Q: "Performance requirements?" → A: "Real-time, sub-100ms latency"
- Q: "Infrastructure?" → A: "Shared hosting on a single server"
- Q: "Budget?" → A: "Very limited, minimal costs"

**Expected behavior:**
- [ ] System detects contradictions via negative information gain
- [ ] Entropy may increase for some dimensions
- [ ] Questions attempt to resolve contradictions
- [ ] Final specification may flag inconsistencies or make reasonable assumptions

#### Step 3: Verify Handling
**Expected behavior:**
- [ ] No crash or infinite loop
- [ ] Specification acknowledges constraints or recommends alternatives
- [ ] Clearly states assumptions made

---

## Verification Checklist

For each scenario, verify:

### Question Quality
- [ ] Clear and unambiguous
- [ ] Relevant to project type
- [ ] No duplicates
- [ ] Appropriate depth progression
- [ ] Effective answer options

### Belief Updates
- [ ] Entropy decreases with good answers
- [ ] Confidence increases over time
- [ ] Contradictions detected (negative IG)
- [ ] Multi-select handled correctly

### Specification Quality
- [ ] Accurate to user answers
- [ ] Comprehensive coverage
- [ ] Well-structured
- [ ] Actionable
- [ ] No hallucinations

### Session Metrics
- [ ] Question count: 8-20 (typical)
- [ ] Total information gain: 5-15 bits
- [ ] Convergence achieved (entropy <0.5 for most dimensions)
- [ ] Session data persisted correctly

---

## Cleanup

```bash
# Archive sessions for reference
mkdir -p test_sessions_archive
cp -r .claude/with_me/sessions/* test_sessions_archive/

# Clear for next test
rm -rf .claude/with_me/sessions/
```

---

## Related Tests

- [good_question.md](../commands/good_question.md) - Individual feature tests
