# Symbiosis - Copilot Instructions

Instructions for GitHub Copilot code completion and code review.

Path-specific standards are defined in `.github/instructions/*.instructions.md` — this file covers project-wide context and review policy.

---

## Project Context

Symbiosis is a local-first, privacy-by-design Human-AI development tool suite. Two Claude Code plugins:

- **as-you**: Pattern learning via BM25 scoring, Thompson sampling, SM-2 spaced repetition
- **with-me**: Bayesian requirement elicitation via belief tracking and Thompson sampling

### Hard Constraints

- Python 3.11+ standard library only — no external packages, no exceptions
- All processing local — no network calls, no external services, no telemetry
- File-based persistence — JSON and Markdown, human-readable
- CI enforces: `ruff` lint, `pyright` type check, doctests, plugin validation

### Infrastructure

- `.monitoring/` — Local-only Docker dev tooling (OTEL Collector, Prometheus, Loki, Grafana). Not production infrastructure. Ephemeral, user-controlled, `:latest` tags are intentional.
- Shell scripts — Minimal glue code under 10 lines delegating to Python. `set -euo pipefail` provides sufficient error handling for local dev scripts.

---

## Code Review Policy

### Comment only when the issue is actionable and correct

Before commenting, verify:

1. **Is the claim factually correct?** Check syntax rules, API docs, and language specs before flagging "incorrect" usage. Do not guess.
2. **Does this require a code change?** If no change is needed, do not comment.
3. **Is this already handled?** Linters (`ruff`), type checkers (`pyright`), and CI catch style, formatting, and type issues. Do not duplicate their coverage.

### Comment priorities (descending)

1. **Security vulnerabilities** — injection, path traversal, secret exposure
2. **Logic bugs** — incorrect behavior, wrong algorithm, off-by-one
3. **Data loss risk** — unhandled errors that silently corrupt or drop data
4. **API misuse** — calling functions with wrong types or invalid arguments

### Do not comment on

- **Style or formatting** — `ruff` enforces this. No opinions on naming, spacing, quote style.
- **Type annotations** — `pyright` enforces this. No suggestions about types.
- **Informational observations** — "This could be X" or "Consider Y" without a concrete problem.
- **PR description accuracy** — Description text is not code. Do not review it.
- **Standard configuration patterns** — Loki schema dates, Docker `:latest` tags for dev tooling, `chmod` permissions for local containers. These are intentional choices for a local dev stack.
- **Over-engineering suggestions** — Do not suggest additional error handling, abstraction layers, configurability, or defensive code beyond what is needed. This project values simplicity.
- **Alternative syntaxes** — If valid syntax is used (e.g., LogQL backticks, shell parameter expansion), do not suggest alternatives.

### Scope

- Review only the diff. Do not comment on unchanged code.
- One comment per distinct issue. Do not repeat the same finding across multiple lines.
- If uncertain whether something is a bug, do not comment.

---

## Code Completion Context

### Python modules (`plugins/**/lib/*.py`)

- Pure functions with type hints and doctests
- Algorithms: BM25, Thompson sampling, SM-2, Bayesian updating
- Use `math`, `json`, `pathlib`, `datetime`, `re`, `difflib` from stdlib
- Doctest isolation: use `tempfile.mkdtemp()` for file operations

### Commands/Agents (`commands/*.md`, `agents/*.md`)

- Markdown with YAML frontmatter (`description`, `allowed-tools`)
- Thin entry points delegating logic to `lib/` modules

### Monitoring configs (`.monitoring/`)

- Docker Compose, OTEL Collector YAML, Prometheus YAML, Loki YAML, Grafana JSON
- PromQL for Prometheus queries, LogQL for Loki queries
- LogQL supports both `"double quotes"` and `` `backticks` `` for string literals

### Shell scripts (`.monitoring/*.sh`)

- Bash with `set -euo pipefail`
- Under 10 lines of logic, delegates to Python or Docker

---

## Build & Test

Prerequisite: [mise](https://mise.jdx.dev/) manages Python and all tool versions.

```bash
mise run test            # All doctests
mise run lint            # ruff check
mise run typecheck       # pyright
mise run validate        # Plugin config validation
```

CI requires all four checks to pass.
