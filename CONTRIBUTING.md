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
- **Rule**: Never document directory structures, file paths, version numbers, concrete code examples, tool syntax, API signatures, configuration details, or step-by-step procedures in CONTRIBUTING.md or .claude/rules/

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
  - **Why**: Eliminates dependency hell, version conflicts, and installation issues; computational algorithms are delegated to Claude via skills, not external math libraries
  - **Responsibility**: Contributors solve I/O problems with stdlib, computational problems with skills; maintainers provide guidance on stdlib alternatives or skill-based approaches

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

### Testing Prompt Files (Commands, Agents & Skills)

Prompt files (`commands/*.md`, `agents/*.md`, `skills/*.md`) define Claude's behavior but cannot be automatically tested. Human testing is required.

**Component Types:**
- **Commands**: User-invocable slash commands (e.g., `/as-you:note`)
- **Agents**: Autonomous multi-step task handlers invoked by Claude
- **Skills**: Computational algorithms executed by Claude (hybrid architecture component)

**Why Manual Testing?**
- Claude Code interprets prompts at runtime
- AskUserQuestion UI must be visually verified
- LLM responses are non-deterministic
- Tool availability varies by version
- Skill computations must be validated against expected mathematical results

#### General Test Setup

1. **Start Fresh Session**
   ```bash
   /exit
   claude-code
   ```

2. **Verify Plugin Loaded**
   - Check for "As You plugin loaded" message
   - If promotion candidates exist, summary should display

#### Testing Current Commands

Test modified commands using these procedures:

**`/as-you:note` - Add Note**

```bash
# Test 1: Add simple note
/as-you:note Testing note functionality

# Verify:
# - Script executes: python3 scripts/commands/note_add.py
# - Note is translated to English if non-English input
# - Confirmation message appears
# - File .claude/as_you/session_notes.local.md is updated

# Test 2: Add note with special characters
/as-you:note Testing with "quotes" and special: chars!

# Verify: Special characters are preserved correctly
```

**`/as-you:notes` - View/Manage Notes**

```bash
# Prerequisite: Add at least one note first
/as-you:note Test note for viewing

# Test:
/as-you:notes

# Verify interactive flow:
# 1. Current notes are displayed
# 2. AskUserQuestion appears with options:
#    - "View history"
#    - "Clear current notes"
#    - "Exit"
# 3. Select each option and verify:
#    - View history: Shows archived notes from .claude/as_you/session_archive/
#    - Clear current notes: Asks confirmation, then clears
#    - Exit: Returns without action
```

**`/as-you:memory` - Memory Dashboard**

```bash
# Test:
/as-you:memory

# Verify display:
# 1. Statistics are shown:
#    - Current session notes count
#    - Archive days count
#    - Detected patterns count
#    - Promotion candidates count
# 2. AskUserQuestion appears with options:
#    - "View promotion candidates"
#    - "Analyze patterns"
#    - "Detect similar patterns"
#    - "Review knowledge base"
# 3. Test each option:
#    - View candidates: Executes promotion_analyzer.py, shows list
#    - Analyze patterns: Launches memory-analyzer agent
#    - Detect similar: Executes similarity_detector.py
#    - Review KB: Shows unused skills/agents stats
```

**`/as-you:promote` - Promote Pattern**

```bash
# Prerequisite: Have promotion candidates
# (Add notes across multiple sessions to generate patterns)

# Test 1: With candidate selection
/as-you:promote

# Verify flow:
# 1. promotion_analyzer.py executes
# 2. If no candidates: Shows message "No promotion candidates available yet"
# 3. If candidates exist: AskUserQuestion shows candidate list
# 4. After selection:
#    - pattern_context.py retrieves pattern contexts
#    - AI analyzes whether pattern is Skill or Agent
#    - Component is generated
#    - Confirmation prompt appears
# 5. If confirmed:
#    - File created in skills/ or agents/
#    - promotion_marker.py marks pattern as promoted
#    - Success message with file path

# Test 2: With specific pattern name
/as-you:promote testing

# Verify: Skips candidate selection, directly promotes "testing" pattern
```

**`/as-you:workflows` - Manage Workflows**

```bash
# Prerequisite: Create a workflow first using /as-you:workflow-save

# Test:
/as-you:workflows

# Verify flow:
# 1. workflow_list.py executes
# 2. If no workflows: Shows "No saved workflows found" + guide
# 3. If workflows exist:
#    - Table displays with Name and Last Updated
#    - AskUserQuestion shows options:
#      - "View workflow details"
#      - "Update workflow"
#      - "Delete workflow"
#      - "Exit"
# 4. Test each option:
#    - View: Select workflow → displays content
#    - Update: Select workflow → select update method → preview → confirm
#    - Delete: Select workflow → confirm → deleted
#    - Exit: Returns without action
```

**`/as-you:workflow-save` - Save New Workflow**

```bash
# Prerequisite: Perform some work (use tools: Bash, Read, Write, etc.)

# Test:
/as-you:workflow-save

# Verify flow:
# 1. Prompts for workflow name
# 2. Analyzes last 10-20 tool uses
# 3. Generates workflow definition
# 4. Shows preview
# 5. AskUserQuestion for confirmation
# 6. If confirmed:
#    - Creates commands/{name}.md
#    - Success message with restart instruction
# 7. After restart: New command /as-you:{name} should be available
```

**`/as-you:help` - Help Display**

```bash
# Test:
/as-you:help

# Verify:
# - Plugin description displayed
# - All commands listed with descriptions
# - Related commands section shown
# - Format is readable and complete
```

**`/with-me:good-question` - Requirement Elicitation**

```bash
# Test:
/with-me:good-question

# Verify flow:
# 1. Session starts (question_feedback.json created/updated)
# 2. Adaptive questions are asked based on uncertainty dimensions
# 3. Each question-answer pair is recorded with reward scores
# 4. Session completes with summary displayed
# 5. Check ~/.claude/with_me/question_feedback.json contains session data
```

**`/with-me:stats` - Question Effectiveness Dashboard**

```bash
# Prerequisite: Complete at least one /with-me:good-question session

# Test:
/with-me:stats

# Verify display:
# - Overview metrics (total sessions, questions, averages)
# - Best questions (top 5 with avg reward, times used)
# - Dimension statistics (avg info gain per dimension)
# - Recent sessions (last 5 with metrics)
```

#### Testing Agents

Agents are invoked automatically or via Task tool. Test by triggering their conditions:

**`memory-analyzer`**
```bash
# Triggered from /as-you:memory → "Analyze patterns"
# Verify: Analyzes pattern_tracker.json, provides recommendations
```

**`component-generator`**
```bash
# Triggered from /as-you:promote
# Verify: Generates skill or agent definition based on pattern
```

**Other agents**: pattern-learner, pattern-curator, workflow-optimizer, promotion-reviewer
- Test by invoking their specific triggering conditions
- Verify they have access to declared tools
- Verify they complete without errors

#### Common Issues & Solutions

**Frontmatter Errors:**
```yaml
# Missing allowed-tools
description: "My command"
# Error: Tools used but not declared
# Fix: Add allowed-tools: [Bash, Read, Write]
```

**Script Path Errors:**
```bash
# Wrong path
python3 scripts/my_script.py
# Error: Script not found
# Fix: Verify path from PROJECT_ROOT, test script directly
```

**AskUserQuestion Errors:**
```yaml
# Too many options (>4)
options: [{}, {}, {}, {}, {}]
# Error: Max 4 options (excluding auto-added "Other")
# Fix: Combine or remove options to stay under limit
```

#### Testing Best Practices

1. **Test after every prompt change** - Don't accumulate untested changes
2. **Start fresh session** - Avoid state pollution from previous commands
3. **Test error paths** - Try invalid inputs, cancellations
4. **Compare with existing** - Look at similar working prompts
5. **Document unexpected behavior** - Note for future reference

#### When to Test

**Must test before commit:**
- New command/agent/skill creation
- Logic flow changes
- Frontmatter modifications (allowed-tools, description, context)
- Script path changes
- AskUserQuestion structure changes
- Skill computational logic changes (verify mathematical correctness)

**Optional testing:**
- Minor wording improvements
- Comment/documentation changes

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
