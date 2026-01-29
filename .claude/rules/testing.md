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

## Type Checking

**Tool**: Pyright (Pylance CLI)

**Why**: Catch type errors before runtime, improve code quality, enable better IDE support.

**Requirements**:
- All public functions must have type hints
- Use Python 3.11+ syntax: `list[str]`, `dict[str, Any]`
- Avoid `Any` unless truly necessary

**Running**:
```bash
mise run typecheck      # Type check all plugin code
```

**Common Issues**:
- Missing return type annotations
- Incorrect parameter types
- Untyped dictionary access
- Missing None checks for optional values

## Coverage Measurement

**Tool**: coverage.py

**Why**: Visibility into untested code paths, identify missing error handling, track test quality over time.

**Optional but recommended**: Coverage is not required for every PR, but periodic checks help maintain test quality.

**Running**:
```bash
mise run coverage:all    # Run tests with coverage and show report
mise run coverage:html   # Generate detailed HTML report
```

**Current Baseline**: 56% (established 2026-01-29)

**Guidelines**:
- Focus on testing critical paths and error handling
- Don't chase 100% coverage - aim for meaningful tests
- Use coverage to find gaps in edge case testing
- Coverage reports help identify untested error branches and edge cases

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
2. `mise run typecheck`
3. `mise run test`
4. `mise run validate`

## Test-First Workflow

1. Write doctest (it fails)
2. Implement function
3. Verify (it passes)
4. Commit with confidence
