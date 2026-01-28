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

**Documentation Responsibilities**:
- **README.md**: User-facing marketing (simple, example-driven, < 100 lines)
- **docs/technical-overview.md**: Theory, algorithms, configuration (for users + technical readers)
- **CONTRIBUTING.md**: Development setup, testing, PR process (for contributors only)
- **Code docstrings**: Implementation details, API documentation

**Documentation Rules**:
- ❌ Never mix marketing and technical content in README
- ❌ No development setup/testing in technical docs (belongs in CONTRIBUTING.md)
- ❌ No CHANGELOG files (Issues/PRs are the source of truth)
- ❌ No GitHub Releases (decided in past Issues)
- ❌ Forbidden: Directory structures, file paths, version numbers in docs
- ✅ README links to technical-overview.md for deeper understanding
- ✅ technical-overview.md links to CONTRIBUTING.md for development

**Anti-Patterns**:
- ❌ External dependencies (except stdlib)
- ❌ Volatile information in docs
- ❌ Over-engineering, premature optimization
- ❌ Privacy-compromising features

## Workflow

```bash
mise install        # Setup
mise run test       # Doctests
mise run lint       # Lint (ruff check)
mise run typecheck  # Type check (pyright)
mise run format:check  # Format check
mise run validate   # Plugin config validation
```

**Before committing**: Run `mise run test && mise run lint && mise run typecheck`

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
