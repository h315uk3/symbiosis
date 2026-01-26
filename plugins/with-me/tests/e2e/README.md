# E2E Test Scenarios

Manual end-to-end tests for validating with-me plugin behavior in real Claude Code sessions.

## Purpose

Verify that adaptive requirement elicitation works correctly through actual user interactions, including Bayesian belief updating and information-theoretic question selection.

## Why Manual Testing

These scenarios involve:
- LLM-generated questions based on information gain calculations
- Interactive user answers affecting belief distributions
- Non-deterministic question selection based on entropy
- Complex multi-step workflows with state persistence

Automated testing cannot capture these characteristics.

## Test Philosophy

### Behavioral Verification

Test behavior, not exact questions:
- Questions make sense given context
- Beliefs update correctly from answers
- Convergence occurs when appropriate
- Requirements specification is comprehensive

### Adaptive Nature

Questions adapt based on answers. The same initial prompt may lead to different question sequences depending on user responses.

### State Persistence

Session state persists across commands. Verify state integrity throughout the workflow.

## When to Test

- Before releases
- After algorithm changes
- When modifying question selection logic
- After bug fixes in belief updating

## Test Organization

Organized by workflow:
- **commands/**: Main `/with-me:good-question` command flow
- **workflows/**: Complete end-to-end requirement sessions

Each scenario tests different aspects of the adaptive questioning system.
