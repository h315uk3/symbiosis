# Symbiosis - GitHub Copilot Instructions

**For GitHub Copilot**: Project-specific development principles.

**For Claude Code**: See `CLAUDE.md` and `.claude/rules/` for detailed constraints.

---

## Philosophy

- **Local-First, Privacy-by-Design**: All processing local, no external services
- **Hybrid Python-Claude**: Python for I/O, Claude Skills for computation
- **Zero External Dependencies**: Standard library only
- **Testability**: Type hints and doctests required
- **Statistical Intelligence**: Transparent math, no ML black boxes

## Development Standards

**Python**: 3.11+, type hints, doctests, `ruff` compliance (CI enforced)

**Shell**: Minimal glue code - business logic in Python

**Documentation**: Principles over implementation details
- ❌ Forbidden: Directory structures, file paths, version numbers, code examples, step-by-step procedures
- ✅ Required: Document "why" (principles), not "what" (implementation)

**Anti-Patterns**:
- ❌ External dependencies (except stdlib)
- ❌ Volatile information in docs
- ❌ Over-engineering, premature optimization
- ❌ Privacy-compromising features

## Workflow

```bash
mise install    # Setup
mise run test   # Doctests
mise run lint   # Quality check
```

**Git**: `feature/`, `fix/`, `docs/` branches. Descriptive commits, reference issues.

## Architecture

**as-you**: Pattern learning (Detection → Scoring → Merging → SM-2)

**with-me**: Bayesian requirement elicitation (Belief tracking → Thompson sampling)

**Claude Plugins**: Commands (`commands/*.md`), Skills (`skills/*/SKILL.md`), Agents (`agents/*.md`), Hooks (`hooks/hooks.json`)

## Reference

- `CLAUDE.md` - Philosophy
- `CONTRIBUTING.md` - Process
- `.claude/rules/` - Constraints
- `gh issue list` - Current issues
- `gh pr list` - Current PRs

---

For current implementation details, examine the codebase directly.
