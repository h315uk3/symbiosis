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
- No telemetry or analytics to external services
- User controls all data

### Local Observability

Token consumption and session metrics are observable via a local OTEL stack:
- All telemetry data stays on the local machine (Privacy by Design)
- Docker-based: OTEL Collector → Prometheus (metrics) + Loki (logs) → Grafana
- Opt-in only — requires explicit environment variable configuration
- Tracks per-API-call, per-session, and per-plugin-version usage

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

## Documentation Responsibilities

Clear separation of documentation purposes:

### README.md (User-Facing Marketing)
- **Purpose**: First impression, quick start, concrete examples
- **Length**: < 100 lines
- **Content**: Problem → Solution → Example → Key Features
- **Style**: Simple, concise, example-driven
- **Links to**: technical-overview.md for details

### docs/technical-overview.md (Theory & Configuration)
- **Purpose**: Deep understanding of algorithms, configuration, data structures
- **Audience**: Users + technical readers who want to understand "how it works"
- **Content**: Algorithms, information theory, configuration options, tuning guides
- **Links to**: CONTRIBUTING.md for development

### CONTRIBUTING.md (Contributor Guide)
- **Purpose**: How to develop, test, and contribute
- **Audience**: Contributors and maintainers only
- **Content**: Setup, testing, code style, PR process
- **Never includes**: User-facing documentation, algorithm theory

### Code Docstrings
- **Purpose**: Implementation details, API contracts
- **Audience**: Developers reading the code
- **Content**: Function behavior, parameters, return values, examples (doctests)

## Documentation Rules

**Never Do:**
- ❌ Mix marketing and technical content in README
- ❌ Put development setup/testing in technical docs
- ❌ Create CHANGELOG files (Issues/PRs are source of truth)
- ❌ Create GitHub Releases (decided in past Issues)
- ❌ Document directory structures, file paths, version numbers

**Always Do:**
- ✅ Keep README simple and example-driven
- ✅ Separate theory (technical-overview.md) from process (CONTRIBUTING.md)
- ✅ Link between docs appropriately (README → technical → CONTRIBUTING)
- ✅ Use docstrings for implementation details

---

**Note**: For development constraints, code style, testing, and contribution process, see `.claude/rules/` and `CONTRIBUTING.md`.
