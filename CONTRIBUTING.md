# Contributing Guide

Thank you for your interest in contributing to the As You plugin!

## Philosophy

### Why These Constraints Exist

**Python-Centric Architecture:**
- **Why**: Shell scripts are difficult to test, debug, and maintain at scale
- **Purpose**: Enable comprehensive testing and rapid iteration
- **Responsibility**: Contributors must write testable, type-safe Python code; reviewers must verify test coverage

**Type Hints Required:**
- **Why**: Prevent runtime errors and enable static analysis
- **Purpose**: Catch bugs at development time, not production time
- **Responsibility**: Contributors must annotate all functions; CI enforces this automatically

**Doctests in All Functions:**
- **Why**: Tests colocated with code stay synchronized and serve as living documentation
- **Purpose**: Ensure every function works as documented and examples remain executable
- **Responsibility**: Contributors write doctests for new code; reviewers verify they're meaningful, not trivial

**Standard Library Only:**
- **Why**: External dependencies create maintenance burden, version conflicts, and installation complexity
- **Purpose**: Keep the plugin lightweight, portable, and dependency-free for all users
- **Responsibility**: Contributors must solve problems with standard library; maintainers reject PRs with external deps

**Shell Scripts Minimized:**
- **Why**: Hooks require shell, but all logic should be testable Python
- **Purpose**: Keep shell as thin glue code (environment setup + Python invocation only)
- **Responsibility**: Contributors delegate logic to Python; reviewers reject shell scripts with business logic

**Documentation Separation:**
- **Why**: Implementation details change frequently; process/philosophy doesn't
- **Purpose**: CONTRIBUTING.md stays stable; volatile details live in code/docstrings
- **Responsibility**: Contributors update docstrings, not CONTRIBUTING; maintainers enforce separation

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
git clone https://github.com/h315uk3/as_you.git
cd as_you

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

**Python** (scripts/*.py):
- Python 3.11+ with type hints
  - **Why**: Modern Python features (match/case, improved type system) improve code quality
  - **Responsibility**: Contributors verify Python version locally; CI rejects incompatible code
- Must pass `ruff check` and `ruff format`
  - **Why**: Consistent style reduces cognitive load and prevents style debates
  - **Responsibility**: Contributors run `mise run lint` before pushing; CI blocks non-conforming code
- Include comprehensive doctests for all functions
  - **Why**: Executable examples prevent documentation drift and catch regressions
  - **Responsibility**: Contributors write realistic examples; reviewers reject trivial tests (e.g., `>>> 1 + 1\n2`)
- Standard library only (no external dependencies)
  - **Why**: Eliminates dependency hell, version conflicts, and installation issues
  - **Responsibility**: Contributors solve problems creatively with stdlib; maintainers provide guidance on stdlib alternatives

**Shell** (hooks/*.sh only):
- Keep minimal - delegate logic to Python modules
  - **Why**: Shell is untestable and error-prone; Python is testable and maintainable
  - **Responsibility**: Contributors extract logic to Python; reviewers reject shell scripts with business logic
- Call Python modules directly (`python3 scripts/module_name.py`)
  - **Why**: Direct invocation is simpler than managing shell function libraries
  - **Responsibility**: Contributors use absolute paths or proper PATH; reviewers verify portability

**Documentation**:
- Update tests/README.md if adding new modules
  - **Why**: Centralized module overview helps new contributors understand the codebase
  - **Responsibility**: Contributors update module table when adding files; maintainers keep overview current
- Keep CONTRIBUTING.md focused on process, not implementation details
  - **Why**: Process/philosophy is stable; implementation details are volatile
  - **Responsibility**: Contributors put implementation details in docstrings; maintainers reject volatile content
- Avoid documenting volatile information (directory structures, internal flows)
  - **Why**: Documentation maintenance cost > value for frequently changing details
  - **Responsibility**: Contributors use code comments for volatile info; reviewers suggest moving details to docstrings

### Adding New Python Modules

1. Create module in `scripts/` with permissions `644` (rw-r--r--):
   ```python
   """Module description."""

   def my_function(arg: str) -> int:
       """
       Function description.

       Examples:
           >>> my_function("test")
           4
       """
       return len(arg)

   if __name__ == "__main__":
       import doctest
       doctest.testmod()
   ```

2. Run tests:
   ```bash
   python3 scripts/my_module.py --test  # Test single module
   mise run test                        # Test all modules
   ```

3. Ensure it passes linting:
   ```bash
   mise run lint
   ```

### Pull Request Process

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
   - **Why**: Isolates your changes; prevents conflicts with other contributors
   - **Responsibility**: Use descriptive branch names; keep branches focused on single features

2. **Develop with Tests**
   ```bash
   mise run test           # Run after every change
   mise run lint           # Fix style issues
   ```
   - **Why**: Catch bugs early; avoid CI failures that waste reviewer time
   - **Responsibility**: Ensure 100% test pass rate locally before pushing

3. **Commit Thoughtfully**
   ```bash
   git commit -m "Add BK-Tree similarity search (O(n log n))"
   ```
   - **Why**: Clear history helps debugging and understanding changes
   - **Responsibility**: Write descriptive commits; reference issues when relevant; keep commits atomic

4. **Push and Create PR**
   ```bash
   git push origin feature/descriptive-name
   ```
   - **Why**: Makes your work visible and reviewable
   - **Responsibility**: Fill out PR template; explain what/why/how; link related issues

5. **Respond to Reviews**
   - **Why**: Reviewers invest time to improve your code
   - **Responsibility**: Address feedback promptly; ask questions if unclear; update PR based on comments

**Reviewer Responsibilities:**
- Check code meets standards (type hints, doctests, no external deps)
- Verify tests are meaningful and comprehensive
- Suggest improvements for clarity/performance
- Approve only when all criteria met
- Be respectful and constructive

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

## Plugin Architecture

For implementation details, see:
- `tests/README.md` - Testing strategy and module overview
- `.github/instructions.md` - General plugin development guide (not As You specific)
- Individual module docstrings - Implementation documentation

## License

GNU AGPL v3 - See [LICENSE](LICENSE) for details.

## Questions?

- Open an issue for bugs or feature requests
- Check existing issues and discussions before creating new ones
- Be respectful and constructive in all interactions

---

**Note**: Keep this document focused on contribution process, not implementation details. Implementation details belong in code comments, docstrings, and tests/README.md.
