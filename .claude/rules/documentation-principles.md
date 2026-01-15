# Documentation Principles

## Golden Rule: Avoid Volatile Information

**Never document information that changes frequently.**

### Volatile (DO NOT document)

- Specific directory structures
- File paths and file names
- Version numbers
- Concrete code examples
- Tool commands and syntax
- API signatures
- Configuration details
- Step-by-step procedures

**Why**: These become outdated quickly, creating maintenance burden and misleading information.

**Where to put**: Code comments, docstrings, or discover via code exploration.

### Stable (DO document)

- Why we make decisions (philosophy)
- Design principles (constraints, values)
- Architecture patterns (high-level)
- Anti-patterns to avoid
- Quality standards (what, not how)
- Responsibilities (roles)

**Why**: These rarely change and provide lasting value.

## Documentation Hierarchy

**CLAUDE.md**: Unchanging philosophy and core principles

**CONTRIBUTING.md**: Stable process and contribution guidelines

**.claude/rules/**: Agent-focused principles and constraints

**Docstrings**: Function-specific documentation with examples

**Code comments**: Implementation details and complex logic

## Review Checklist

Before adding documentation, ask:
1. Will this be outdated in 6 months?
2. Can this be discovered by reading code?
3. Is this "what" (volatile) or "why" (stable)?

**If volatile → Don't document it. Put in code or docstring.**

**If stable → Document the principle, not the implementation.**
