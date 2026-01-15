# Development Constraints

## Critical Rules

### 1. No Speculation
Never propose implementations based on assumptions. Always verify with official documentation, source code, or latest information via WebFetch/WebSearch.

### 2. Root Cause Analysis Required
Always identify and report the root cause before fixing errors. Never apply band-aid fixes without understanding the underlying issue.

### 3. No Legacy Code Reuse
Never copy-paste old implementation patterns. Verify API versions, check current best practices, and avoid deprecated patterns.

## Technology Constraints

**Allowed**:
- Python 3.11+ standard library only
- Built-in modules: pathlib, json, math, difflib, re, datetime

**Forbidden**:
- External Python packages
- Network calls to external services
- Database systems
- Cloud APIs or authentication

**Architecture**:
- Local-first processing
- File-based persistence (JSON, Markdown)
- Human-readable formats
- Testable, modular code

## Quality Standards

### Before Any Change
1. Read the file first
2. Verify approach with documentation
3. Consider side effects
4. Test locally

### Error Handling
- Handle errors at appropriate boundaries
- Provide clear error messages
- Log for debugging
- Don't catch-all without reason
