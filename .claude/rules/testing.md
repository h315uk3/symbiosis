# Testing

## Philosophy

Every function must be testable:
- Clear input/output contracts
- Reproducible with mock data
- No external dependencies

## Doctest-Driven Development

**Why**: Tests are documentation, stay synchronized, and are executable specifications.

**Coverage Requirements**:
- Normal operation (happy path)
- Edge cases (empty input, max values)
- Boundary conditions (0, 1, n-1, n)
- Error conditions (invalid input, missing files)

**Use realistic data**, not trivial tests like `1 + 1 == 2`.

## Running Tests

```bash
mise run test           # All doctests
mise run test:verbose   # Verbose output
mise run test:watch     # Auto-run on changes
```

## Interactive Testing

**Manual testing required for**:
- Slash commands (UI interaction)
- AskUserQuestion flows
- Agent behavior
- Hook triggers

**Procedure**:
1. Start fresh session: `/exit` then `claude-code`
2. Test command with various inputs
3. Verify output and file changes
4. Test edge cases (invalid input, cancellation)

## CI/CD

All checks must pass before merging:
1. `mise run lint`
2. `mise run test`
3. `mise run validate`

## Test-First Workflow

1. Write doctest (it fails)
2. Implement function
3. Verify (it passes)
4. Commit with confidence
