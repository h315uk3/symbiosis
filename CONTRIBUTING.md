# Contributing to Symbiosis

Thank you for your interest in contributing to Symbiosis plugins!

## Philosophy

### Why These Constraints Exist

**Hybrid Python-Claude Architecture:**
- **Why**: Python handles I/O and state management; Claude performs computational algorithms via skills
- **Purpose**: Distributable intelligence (skills as markdown), transparent computation, zero computational dependencies
- **Responsibility**: Contributors write I/O logic in Python, computational logic in skills; reviewers verify separation of concerns

**Type Hints Required:**
- **Why**: Prevent runtime errors and enable static analysis
- **Purpose**: Catch bugs at development time, not production time
- **Responsibility**: Contributors must annotate all functions; CI enforces this automatically

**Doctests in All Functions:**
- **Why**: Tests colocated with code stay synchronized and serve as living documentation
- **Purpose**: Ensure every function works as documented and examples remain executable
- **Responsibility**: Contributors write doctests for new code; reviewers verify they're meaningful, not trivial

**Standard Library Only:**
- **Why**: External dependencies create maintenance burden, version conflicts, and installation complexity; computational algorithms are delegated to Claude via skills rather than external math libraries
- **Purpose**: Keep the plugin lightweight, portable, and dependency-free; enable distributable intelligence without NumPy/SciPy
- **Responsibility**: Contributors solve I/O problems with standard library, computational problems with skills; maintainers reject PRs with external deps

**Shell Scripts Minimized:**
- **Why**: Hooks require shell, but all logic should be testable Python
- **Purpose**: Keep shell as thin glue code (environment setup + Python invocation only)
- **Responsibility**: Contributors delegate logic to Python; reviewers reject shell scripts with business logic

**Documentation Separation:**
- **Why**: Implementation details change frequently; process/philosophy doesn't
- **Purpose**: CONTRIBUTING.md stays stable; volatile details live in code/docstrings
- **Responsibility**: Contributors update docstrings, not CONTRIBUTING; maintainers enforce separation

**Volatile Information Forbidden:**
- **Why**: Directory structures, file paths, version numbers, code examples, and tool commands become outdated quickly
- **Purpose**: Prevent documentation rot and maintenance burden
- **Responsibility**: Contributors must document "why" (principles) not "what" (implementation); reviewers reject PRs with volatile information in docs

### Roles and Responsibilities

**Contributors:**
- Write type-annotated, doctest-covered Python code
- Ensure all tests pass locally before pushing
- Update relevant documentation (docstrings, tests/README.md)
- Respond to review feedback constructively

**Reviewers:**
- Verify tests are comprehensive and meaningful
- Check type hints are present and correct
- Ensure no external dependencies sneak in
- Validate shell scripts are minimal with no business logic
- Confirm documentation is in the right place

**Maintainers:**
- Enforce architectural principles
- Keep CONTRIBUTING.md focused on philosophy/process
- Reject changes that violate constraints (even if functionally correct)
- Guide contributors toward pythonic, testable solutions

## Development Environment Setup

### Prerequisites

- Git
- [mise](https://mise.jdx.dev/) - Tool version management and task runner

### Setup

```bash
# Clone and setup
git clone https://github.com/h315uk3/symbiosis.git
cd symbiosis

# Install mise (if not already installed)
curl https://mise.run | sh

# Install dependencies (see mise.toml for versions)
mise install

# Run tests
mise run test
```

## Development Workflow

### Testing

```bash
mise run test           # Run all doctests
mise run test:verbose   # Verbose output
mise run test:watch     # Watch mode (auto-run on changes)
```

### Code Quality

```bash
mise run lint           # Lint Python code (ruff)
mise run format         # Format Python code (ruff)
mise run validate       # Validate plugin configuration
```

### Available Tasks

See all available tasks:
```bash
mise tasks
```

## Contributing Guidelines

### Code Standards

**Python**:
- Python 3.11+ with type hints
- Must pass `ruff check` and `ruff format`
- Include comprehensive doctests for all functions
- Standard library only (no external dependencies)

**Shell** (hooks only):
- Keep minimal - delegate logic to Python modules
- Call Python modules directly

**Documentation**:
- Keep CONTRIBUTING.md focused on process, not implementation details
- Avoid documenting volatile information (directory structures, internal flows)

### Plugin-Specific Guidelines

Each plugin has its own contribution guide with specific testing procedures:

- **[as-you CONTRIBUTING](./plugins/as-you/CONTRIBUTING.md)** - Pattern learning plugin development
- **[with-me CONTRIBUTING](./plugins/with-me/CONTRIBUTING.md)** - Requirement elicitation plugin development

## Pull Request Process

**Why This Process Exists:**
- Protects main branch quality
- Enables parallel development
- Provides clear audit trail
- Facilitates code review

**Your Responsibilities as Contributor:**

1. **Fork and Branch**
   ```bash
   git checkout -b feature/descriptive-name
   ```

2. **Develop with Tests**
   ```bash
   mise run test           # Run after every change
   mise run lint           # Fix style issues
   ```

3. **Commit Thoughtfully**
   - Write descriptive commits
   - Reference issues when relevant
   - Keep commits atomic

4. **Push and Create PR**
   - Fill out PR template
   - Explain what/why/how
   - Link related issues

5. **Respond to Reviews**
   - Address feedback promptly
   - Ask questions if unclear
   - Update PR based on comments

**Reviewer Responsibilities:**
- Check code meets standards (type hints, doctests, no external deps)
- Verify tests are meaningful and comprehensive
- Suggest improvements for clarity/performance
- Approve only when all criteria met

## CI/CD

GitHub Actions automatically runs on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

Checks performed:
1. Install dependencies with mise
2. Run linter (`mise run lint`)
3. Run all doctests (`mise run test`)
4. Validate configuration (`mise run validate`)

All checks must pass before merging.

## License

GNU AGPL v3 - See [LICENSE](LICENSE) for details.

## Questions?

- Open an issue for bugs or feature requests
- Check existing issues and discussions before creating new ones
- Be respectful and constructive in all interactions

---

**Note**: Keep this document focused on contribution process, not implementation details. Implementation details belong in code comments, docstrings, and plugin-specific CONTRIBUTING.md files.
