# As You - Claude Code Plugin Development Guide

This file defines the core principles and architectural philosophy for As You plugin development.

## Project Philosophy

**As You** is a Claude Code plugin that learns from your work patterns and builds knowledge automatically from your explicit notes. It embodies a pattern-first, privacy-focused approach to personal knowledge management.

### Core Values

- **Local-First**: No external services, no network calls, no authentication
- **Explicit Over Implicit**: Intentional note-taking rather than automatic surveillance
- **Statistical Intelligence**: Mathematical approaches to pattern detection, not ML models
- **Zero External Dependencies**: Pure standard library implementation for maintainability
- **Progressive Accumulation**: Knowledge grows organically from repeated patterns

## Architectural Principles

### 1. Simplicity First

The plugin maintains simplicity through deliberate constraints:

- Use only standard library features
- Avoid complex NLP or ML dependencies
- Prefer file-based persistence over databases
- Keep data formats human-readable (JSON, Markdown)
- Make data flow explicit and traceable

### 2. Privacy by Design

User data never leaves the local machine:

- All processing happens locally
- No telemetry or analytics
- No cloud synchronization
- User controls all data
- Transparent data storage in .claude directory

### 3. Testability as Foundation

Every component must be independently testable:

- Scripts are self-contained units
- Test coverage for all core logic
- Reproducible behavior with mock data
- Clear input/output contracts

### 4. Performance Through Intelligence

Rather than brute force, use smart algorithms:

- Statistical scoring identifies important patterns
- Similarity detection reduces redundancy
- Time-decay ensures relevance
- Configurable thresholds balance accuracy and speed

## Data Flow Architecture

The plugin follows a clear pipeline:

```
Manual Input → Archival → Analysis → Knowledge Base
```

Each stage is independent and can be tested separately:

1. **Capture**: User explicitly records notes
2. **Archive**: Session notes are preserved chronologically
3. **Extract**: Statistical analysis identifies patterns
4. **Score**: Multiple metrics evaluate pattern importance
5. **Merge**: Similar patterns are consolidated
6. **Promote**: High-scoring patterns become reusable knowledge

## Development Constraints

### What We Avoid

- **External APIs**: No network dependencies
- **Heavy Libraries**: No nltk, spaCy, transformers, etc.
- **Implicit Tracking**: No automatic session recording
- **Opaque Algorithms**: No black-box ML models
- **Database Systems**: No SQLite, PostgreSQL, etc.

### What We Embrace

- **Python Standard Library**: pathlib, json, math, difflib
- **Bash Scripting**: For hooks and utilities
- **Markdown**: For human-readable definitions
- **Mathematical Scoring**: TF-IDF, PMI, Levenshtein distance
- **Git-Friendly Formats**: Text-based, diff-friendly

## Component Architecture

### Commands (User Interface)

Commands are the user-facing interface. They should:

- Have clear, single-purpose descriptions
- Follow consistent naming conventions
- Provide helpful error messages
- Document when they should be used

### Agents (Autonomous Actions)

Agents perform complex, multi-step tasks. They should:

- Have specific triggering conditions
- Access appropriate tools
- Follow the same principles as the main codebase
- Be composable with other agents

### Skills (Knowledge Representation)

Skills capture reusable knowledge. They should:

- Use progressive disclosure
- Focus on specific domains
- Be generated from actual patterns
- Evolve based on usage

### Hooks (Event Handling)

Hooks respond to lifecycle events. They should:

- Be fast and non-blocking
- Handle errors gracefully
- Perform focused, atomic operations
- Not interfere with user workflow

## Quality Standards

### Code Quality

- Clear, descriptive variable names
- Comprehensive error handling
- Inline documentation for complex logic
- Type hints where applicable (Python 3.11+)

### Test Quality

- Test both success and failure cases
- Cover edge cases and boundary conditions
- Use realistic mock data
- Keep tests fast and independent

### Documentation Quality

- Explain the "why" not just the "what"
- Keep examples up-to-date with code
- Document assumptions and constraints
- Use consistent terminology

## Extension Points

The plugin is designed to be extended:

### Pattern Scoring

New scoring algorithms can be added by:
- Implementing the same input/output contract
- Adding weight configuration
- Maintaining composability with existing scores

### Pattern Detection

New pattern types can be detected by:
- Adding extraction logic to the pipeline
- Following the same JSON schema
- Respecting existing scoring infrastructure

### Knowledge Promotion

New promotion targets can be added by:
- Following the same selection flow
- Generating appropriate file formats
- Integrating with the plugin structure

## Anti-Patterns to Avoid

### Over-Engineering

- Don't add features "for the future"
- Don't create abstractions for single-use code
- Don't optimize prematurely
- Don't add configuration for everything

### Breaking Simplicity

- Don't introduce external dependencies casually
- Don't add network calls "just for convenience"
- Don't replace clear code with "clever" code
- Don't hide important logic in magic methods

### Sacrificing Privacy

- Don't add analytics "just for metrics"
- Don't sync data "just for convenience"
- Don't store sensitive data in plain text
- Don't share patterns without explicit user action

## Success Metrics

The plugin succeeds when:

- Users can understand their knowledge growth
- Patterns accurately reflect their work
- Knowledge base reduces repetitive explanations
- System remains fast and responsive
- Data remains under user control
- Code remains maintainable by contributors

## Contributing Philosophy

Contributions should:

- Align with core values
- Maintain simplicity
- Include tests
- Preserve privacy
- Enhance rather than complicate

---

This guide represents the unchanging principles of As You. Implementation details may evolve, but these values remain constant.
