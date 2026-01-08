# As You Plugin Tests

This directory contains the test suite for the As You plugin.

## Testing Philosophy

**Python-centric testing strategy**: Core logic is implemented in Python modules (`scripts/*.py`) and thoroughly tested with doctests. Shell scripts serve as thin wrappers that delegate to Python modules.

## Test Structure

```
tests/
├── run_doctests.py     # Unified doctest runner (standard approach)
└── README.md           # This file

Note: Integration tests (integration/) are planned for future implementation.
      Currently, all functionality is covered by Python doctests.
```

## Running Tests

### Prerequisites

- **Python 3.11+**: Required for doctest runner execution
- **mise**: Task runner (recommended)

```bash
# Install mise
curl https://mise.run | sh
```

### Running with mise (Recommended)

```bash
# Run from project root
mise run test              # Run all Python doctests
mise run test:verbose      # Run doctests with verbose output
mise run test:watch        # Watch mode (auto-run every 5 seconds)

# Other development tasks
mise tasks                 # List all available tasks
mise run lint              # Lint shell scripts + Python code (shellcheck + ruff)
mise run lint:python       # Lint Python code only (ruff)
mise run format            # Format all code (shfmt + ruff)
mise run format:python     # Format Python code only (ruff)
mise run validate          # Validate plugin configuration files
```

### Direct Execution

```bash
# Python doctest runner
python3 tests/run_doctests.py

# Verbose output
python3 tests/run_doctests.py -v

# Test individual modules
python3 scripts/hooks/pattern_tracker_update.py --test
python3 scripts/lib/score_calculator.py --test
```

## Test Coverage

### Python Doctests (Primary Tests)

213 doctests across 16 modules with 100% pass rate:

| Module | Doctests | Description |
|--------|----------|-------------|
| usage_stats_initializer.py | 38 | Usage statistics initialization |
| context_extractor.py | 26 | Context extraction from archives |
| frequency_tracker.py | 24 | Pattern frequency tracking |
| pattern_updater.py | 20 | Pattern metadata updates |
| bktree.py | 19 | BK-Tree similarity search |
| cooccurrence_detector.py | 17 | Co-occurrence pattern detection |
| promotion_analyzer.py | 11 | Promotion candidate analysis |
| levenshtein.py | 10 | Levenshtein distance calculation |
| pattern_merger.py | 8 | Pattern merging with backups |
| promotion_marker.py | 8 | Mark patterns as promoted |
| pattern_detector.py | 7 | Pattern detection from text |
| note_archiver.py | 6 | Note archiving to session_archive |
| tfidf_calculator.py | 5 | TF-IDF score calculation |
| pmi_calculator.py | 5 | PMI score calculation |
| similarity_detector.py | 5 | Similar pattern detection |
| score_calculator.py | 4 | Unified score calculation |

**Coverage**: 213 doctests total, 100% passing (expanded from 191 to 213)

### Integration Tests (Future)

End-to-end workflow tests planned:
- Session lifecycle (start → work → end)
- Pattern detection → scoring → promotion flow
- Archive management and cleanup

## Adding Tests

When adding new functionality:

### 1. Add Doctests to Python Functions/Classes

```python
def my_function(arg: str) -> int:
    """
    Brief description of function.

    Args:
        arg: Description of argument

    Returns:
        Description of return value

    Examples:
        >>> my_function("test")
        4
        >>> my_function("")
        0
    """
    return len(arg)
```

### 2. Doctest Guidelines

- **Self-contained**: Each doctest should be independently executable
- **Temporary files**: Use `tempfile.TemporaryDirectory()` for isolation
- **Error cases**: Test both normal and edge cases
- **Simplicity**: Avoid complex setup
- **Deterministic**: Same input should produce same output

### 3. Verify Tests

```bash
# Test individual module
python3 scripts/your_module.py --test

# Test all modules
mise run test
```

## CI/CD Integration

Automated tests run via GitHub Actions:

- On push to `main` or `develop` branches
- On pull requests to `main` or `develop`

Test results are available in the Checks tab of each PR.

## Architecture Benefits

### Python-Centric Approach

1. **Testability**: Function-level unit tests with doctests
2. **Type Safety**: Static analysis via type hints
3. **Maintainability**: Tests colocated with code
4. **Performance**: Faster than shell script execution
5. **Extensibility**: Handles complex logic easily

### Direct Python Execution

All functionality is implemented as standalone Python modules in `scripts/`:
- No shell script wrappers needed
- Direct execution: `python3 scripts/module_name.py`
- Hooks (`hooks/*.sh`) call Python modules directly
- Commands call Python modules via Bash tool

## Troubleshooting

### Doctest Failures

```bash
# Run with verbose output
python3 scripts/module_name.py --test -v

# Or use unified runner with verbose mode
python3 tests/run_doctests.py -v
```

### Module Import Errors

Doctests run within module scope, so relative imports may not work. For doctests:

```python
# ❌ Doesn't work
>>> from .levenshtein import levenshtein_distance

# ✅ Works (define simple function)
>>> def simple_dist(a, b): return abs(len(a) - len(b))
```

### Python Version

Python 3.11+ is recommended. Older versions may not support some type hints and features.

## References

- [Python doctest documentation](https://docs.python.org/3/library/doctest.html)
- [mise task runner](https://mise.jdx.dev/)
- [ruff linter & formatter](https://docs.astral.sh/ruff/)

---

**Note**: This testing strategy ensures the As You plugin maintains high quality and maintainability. Always include doctests when adding new features.
