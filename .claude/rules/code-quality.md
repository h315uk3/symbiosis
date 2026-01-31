# Code Quality Rules

## Critical: Never Ignore Warnings

**NEVER use warning suppression without structural fixes:**

```python
# ❌ BAD - Hiding the problem
from foo import bar  # noqa: E402
result: Any  # type: ignore
unused_var = 1  # noqa: F841

# ✅ GOOD - Fixing the problem
from foo import bar  # Import at top-level
result: SpecificType  # Use proper type
# Remove unused_var entirely
```

## Linter/Type Checker Warnings Must Be Fixed

### When a warning appears:

1. **Understand why** - Read the warning message and understand the root cause
2. **Fix structurally** - Change the code structure to eliminate the warning
3. **Never suppress** - Do not use noqa, type: ignore, or similar suppressions
4. **Ask if unclear** - If the fix is not obvious, ask the user for guidance

### Common Patterns and Fixes

#### E402: Module level import not at top of file

```python
# ❌ BAD
sys.path.insert(0, str(PLUGIN_ROOT))
from foo import bar  # noqa: E402

# ✅ GOOD
from foo import bar  # Import at top, rely on PYTHONPATH
```

#### PLW1510: subprocess.run without explicit check

```python
# ❌ BAD
result = subprocess.run(cmd)

# ✅ GOOD
result = subprocess.run(cmd, check=False)  # Explicit decision
```

#### TRY300: Consider moving to else block

```python
# ❌ BAD
try:
    result = operation()
    return process(result)
except Error:
    return fallback()

# ✅ GOOD
try:
    result = operation()
except Error:
    return fallback()
else:
    return process(result)
```

#### F841: Local variable assigned but never used

```python
# ❌ BAD
unused = expensive_call()  # noqa: F841

# ✅ GOOD
# Remove the line entirely
# OR if side effects are needed:
_ = expensive_call()  # Explicitly ignored
```

#### reportUnusedImport: Import not accessed

```python
# ❌ BAD
from foo import bar  # Used later, Pyright doesn't see it

# ✅ GOOD
# Move import closer to usage
def function():
    from foo import bar  # Import where it's used
    return bar()
```

## Why This Rule Exists

### Problems with suppression:

1. **Hidden bugs**: Warnings often indicate real problems
2. **Tech debt**: Suppressed warnings accumulate over time
3. **Maintenance**: Future developers don't understand why it was suppressed
4. **False confidence**: Code appears clean but has underlying issues

### Benefits of fixing:

1. **Better code**: Structural fixes improve design
2. **Documentation**: Code explains itself without comments
3. **Reliability**: No hidden issues waiting to surface
4. **Maintainability**: Clear, idiomatic code is easier to modify

## Exceptions (Rare)

Suppression is **only** acceptable when:

1. **External library bug**: The warning is from a third-party library bug
   - Document why with a comment explaining the library issue
   - Link to upstream issue tracker

2. **Intentional design**: The pattern is intentional and well-documented
   - Must have clear comment explaining why
   - Must be reviewed and approved

Even in these cases, prefer alternative designs if possible.

## Enforcement

- All PRs must pass `mise run lint` without warnings
- All PRs must pass `mise run typecheck` without errors
- Reviewers must reject any use of noqa, type: ignore without exceptional justification
- Claude Code must propose structural fixes first, never suppressions

## Examples from this Project

### Session End Hook (Fixed)

**Problem:** E402 - Import after sys.path manipulation

**Bad approach:**
```python
sys.path.insert(0, str(PLUGIN_ROOT))
from as_you.lib.common import AsYouConfig  # noqa: E402
```

**Good approach:**
```python
from as_you.lib.common import AsYouConfig
# Rely on CLAUDE_PLUGIN_ROOT environment variable set by Claude Code
```

**Lesson:** Claude Code already sets PYTHONPATH correctly via CLAUDE_PLUGIN_ROOT. Manual path manipulation is unnecessary and creates linter warnings.

---

**Remember:** Warnings exist for a reason. Fix the root cause, don't hide the symptom.
