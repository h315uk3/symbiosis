# Code Style

## Python Standards

**Version**: Python 3.11+ required

**Type Hints**: Required for all functions
- Annotate parameters and return types
- Use modern syntax: `list[str]`, `dict[str, Any]`

**Doctests**: Required for all public functions
- Include realistic examples
- Cover edge cases and errors
- Keep examples executable

**Formatting**: Enforced by ruff
- Line length: 88 characters
- Double quotes for strings
- Run `mise run format` before committing (or verify with `mise run format --check`)
- Run `mise run lint` to check for style and import issues

## Shell Scripts

**Use only for**:
- Hook entry points
- Environment setup
- Calling Python modules

**Keep under 10 lines** and delegate all logic to Python.

## File Organization

**Python modules**: `plugins/{plugin-name}/scripts/`
- One module per logical component
- Self-contained with doctest runner
- 644 permissions (rw-r--r--)

**Commands/Agents**: `plugins/{plugin-name}/commands/` or `agents/`
- Frontmatter required with `description` and `allowed-tools`
- Test interactively before commit

## Documentation

**Inline comments**: Only for complex algorithms or non-obvious behavior

**Docstrings**: One-line summary + Examples section with doctests
- Explain "why" not "what"
- Include edge cases

## Testing Considerations

**Doctest Isolation**: Prevent test contamination of workspace `.claude/` directory

**Requirements**:
- Use isolated paths (temporary directories, explicit test paths)
- Never assume `.claude/` directory structure exists during tests
- Pass isolated file paths as parameters to functions that interact with `.claude/`
- Use `tempfile.mkdtemp()` or explicit `/tmp/` paths in doctest examples

**Example Pattern**:
```python
>>> import tempfile
>>> from pathlib import Path
>>> temp_root = Path(tempfile.mkdtemp())
>>> # Use temp_root for all file operations in doctest
>>> # Clean up at end
>>> import shutil
>>> shutil.rmtree(temp_root)
```

**Why**: Ensures tests are reproducible and don't leave artifacts in user's workspace
