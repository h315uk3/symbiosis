# E2E Test Scenarios

Manual end-to-end tests for validating plugin behavior in real Claude Code sessions.

## Purpose

Verify that plugin features work correctly through actual user interactions, including LLM-generated responses and interactive dialogs.

## Why Manual Testing

These scenarios involve:
- LLM-generated responses (non-deterministic)
- Interactive user questions and answers
- Behavioral validation rather than exact output matching
- Real-world usage patterns

Automated testing cannot capture these characteristics.

## Test Philosophy

### Behavioral Verification

Test behavior, not exact outputs:
- Commands execute without errors
- Expected state changes occur
- Files modified correctly
- Interactive flows work as designed

### Independence and Dependencies

Some scenarios are independent; others build on previous state. Each scenario documents its prerequisites.

### Reproducibility

Start with clean state when needed. Document state requirements clearly.

## When to Test

- Before releases
- After refactoring
- When adding new features
- After bug fixes

## Test Organization

Organized by feature area:
- **commands/**: Individual slash command behaviors
- **hooks/**: Event-driven automatic behaviors

Each scenario follows a consistent structure with prerequisites, steps, verification, and edge cases.
