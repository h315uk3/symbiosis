---
applyTo: "**/*.md"
---

# Documentation Standards

## Language

- PR titles, PR descriptions, and GitHub Discussions must be in English
- Code comments and docstrings in English

## Volatile Information — Forbidden in Docs

Never document information that changes frequently:
- Directory structures, file paths, file names
- Version numbers
- Concrete code examples or API signatures
- Tool commands and syntax
- Step-by-step procedures

These belong in code comments, docstrings, or are discoverable via code exploration.

## Stable Information — Document These

- Why decisions were made (philosophy)
- Design principles and constraints
- Architecture patterns (high-level)
- Anti-patterns to avoid
- Quality standards (what, not how)

## Document Responsibilities

- **README.md**: User-facing marketing (simple, example-driven, < 100 lines)
- **docs/technical-overview.md**: Theory, algorithms, configuration
- **CONTRIBUTING.md**: Development setup, testing, PR process (contributors only)
- **Code docstrings**: Implementation details, API documentation

## Rules

- Never mix marketing and technical content in README
- No CHANGELOG files — Issues/PRs are the source of truth
- No GitHub Releases
- README links to technical-overview.md; technical-overview.md links to CONTRIBUTING.md
