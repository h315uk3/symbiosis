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

**Test Isolation**: Doctests are isolated from your project's `.claude/` directory to prevent test artifacts from contaminating actual configuration and data files. This ensures clean, reproducible test execution regardless of your local workspace state.

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

### Understanding the 56% Baseline

**This is structurally appropriate, not a problem to fix.** The coverage reflects doctest-driven development constraints:

**High Coverage (70-89%) - Core algorithms:**
- BM25, Thompson Sampling, SM-2, Bayesian learning
- Pure computational logic (well-suited for doctests)
- These are the critical paths and are well-tested

**Low Coverage (11-41%) - CLI commands:**
- `pattern_context.py` (11%), `memory_stats.py` (15%), etc.
- These modules handle:
  - `sys.argv` parsing (command-line arguments)
  - `sys.exit()` calls (process termination)
  - File I/O with real filesystem
  - User interaction flows
- **Doctests cannot easily test these** without complex mocking

**Why not chase higher coverage:**
- CLI layer is intentionally thin (delegates to lib/)
- Core business logic in lib/ is well-tested (60-89%)
- Adding integration tests for CLI would increase complexity
- Manual testing covers CLI behavior adequately

### Guidelines

**Do:**
- Focus on testing critical paths and error handling in lib/
- Use coverage to find gaps in edge case testing
- Check coverage after adding new algorithms or core logic
- Aim for 70%+ coverage in lib/ modules

**Don't:**
- Chase 100% coverage (diminishing returns)
- Write complex mocks just to test CLI argument parsing
- Feel obligated to test every `sys.exit()` branch
- Add coverage checks to CI/CD (it's a periodic quality tool, not a gate)

**When to investigate low coverage:**
- Core algorithm modules (lib/) below 60%
- Missing error handling in critical paths
- New features without doctests

**When to accept low coverage:**
- CLI entry points (commands/ modules)
- Hook handlers (event-driven code)
- File I/O wrappers

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
1. `mise run format --check`
2. `mise run lint`
3. `mise run typecheck`
4. `mise run test`
5. `mise run validate`

## Test-First Workflow

1. Write doctest (it fails)
2. Implement function
3. Verify (it passes)
4. Commit with confidence
