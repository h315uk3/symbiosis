---
applyTo: "**/*.py"
---

# Python Development Standards

## Language & Runtime

- Python 3.11+ required
- Standard library only — no external packages allowed
- Use modern syntax: `list[str]`, `dict[str, Any]`, `X | None`

## Type Hints

- Required for all function parameters and return types
- Avoid `Any` unless truly necessary
- Use `from __future__ import annotations` only if needed for forward references

## Doctests

- Required for all public functions
- Include: happy path, edge cases (empty input, boundaries), error conditions
- Use realistic data, not trivial examples
- Doctests must use isolated paths (`tempfile.mkdtemp()`) for file operations

## Formatting & Linting

- Enforced by `ruff` (line length 88, double quotes)
- Never use warning suppression (`noqa`, `type: ignore`) — fix the root cause structurally
- All code must pass `mise run lint` and `mise run typecheck` (pyright)

## Error Handling

- Handle errors at appropriate boundaries with clear messages
- Don't catch-all without reason
- Prefer `try/except/else` over returning inside `try` block
