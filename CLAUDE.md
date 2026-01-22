# Symbiosis - Development Philosophy

Core principles for Human-AI symbiotic development tools.

## Core Values

- **Local-First**: No external services, no network calls, no authentication
- **Explicit Over Implicit**: Intentional actions rather than automatic surveillance
- **Statistical Intelligence**: Mathematical approaches, not ML models
- **Zero External Dependencies**: Python standard library only
- **Progressive Accumulation**: Knowledge grows from repeated patterns

## Architectural Philosophy

### Simplicity First

Maintain simplicity through deliberate constraints:
- File-based persistence over databases
- Human-readable formats (JSON, Markdown)
- Explicit and traceable data flow

### Privacy by Design

User data never leaves the local machine:
- All processing happens locally
- No telemetry or analytics
- User controls all data

### Testability as Foundation

Every component must be independently testable:
- Clear input/output contracts
- Reproducible behavior with mock data

## Anti-Patterns

### Over-Engineering
- Don't add features "for the future"
- Don't create abstractions for single-use code
- Don't optimize prematurely

### Breaking Simplicity
- Don't introduce external dependencies casually
- Don't replace clear code with "clever" code

### Sacrificing Privacy
- Don't add analytics "just for metrics"
- Don't share patterns without explicit user action

---

**Note**: For development constraints, code style, testing, and contribution process, see `.claude/rules/` and `CONTRIBUTING.md`.
