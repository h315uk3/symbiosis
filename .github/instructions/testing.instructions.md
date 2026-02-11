---
applyTo: "tests/**,plugins/*/tests/**"
---

# Testing Standards

## Doctest-Driven Development

- Tests are written as doctests embedded in function docstrings
- Tests are executable specifications that double as documentation
- Run with `mise run test` (runs all doctests)

## Test Isolation

- Use `tempfile.mkdtemp()` or explicit `/tmp/` paths for file operations
- Never assume `.claude/` directory structure exists during tests
- Pass isolated file paths as parameters to functions under test
- Clean up temporary directories after tests complete

## Test Data

- Use realistic, representative data — not trivial values like `1 + 1 == 2`
- Cover: normal operation, edge cases (empty input, max values), boundary conditions (0, 1, n-1, n), error conditions

## Coverage

- Focus on core algorithms in `lib/` modules (target 70%+)
- CLI entry points have structurally low coverage — this is expected
- Run `mise run coverage:all` for periodic quality checks
- Coverage is not a CI gate — it's a quality tool
