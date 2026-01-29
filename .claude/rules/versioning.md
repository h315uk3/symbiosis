# Versioning

## Plugin Version Management

### When to Bump Version

**CRITICAL**: When modifying any file under `plugins/` directory, you MUST increment the plugin version in `.claude-plugin/plugin.json`.

**Files that require version bump**:
- Python code (`*.py`)
- Command definitions (`commands/*.md`)
- Agent definitions (`agents/*.md`)
- Skills (`skills/*.md`)
- Hooks (`hooks/*`)
- Configuration schemas (`config/*.json`)

**Files that DO NOT require version bump**:
- Documentation (`docs/**/*`)
- Contributor guides (`CONTRIBUTING.md`)
- README files (`README.md`)
- Manual test documentation (`tests/manual-test.md`)

### Version Format

Follow semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes, API incompatibilities
- **MINOR**: New features, backward-compatible changes
- **PATCH**: Bug fixes, minor improvements

### How to Bump Version

**For as-you plugin**:
```bash
# Edit: plugins/as-you/.claude-plugin/plugin.json
{
  "name": "as-you",
  "version": "0.3.4",  # Increment this
  ...
}
```

**For with-me plugin**:
```bash
# Edit: plugins/with-me/.claude-plugin/plugin.json
{
  "name": "with-me",
  "version": "0.3.5",  # Increment this
  ...
}
```

### Commit Message

Include version bump in separate commit:
```bash
chore: bump plugin versions

- as-you: 0.3.3 → 0.3.4
- with-me: 0.3.4 → 0.3.5

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

### Pull Request Requirements

**Every PR that modifies plugin code MUST**:
1. Include version bump commit
2. Update both affected plugins
3. Document version changes in PR description

**Checklist for reviewers**:
- [ ] Version bumped for all modified plugins
- [ ] Semantic versioning applied correctly
- [ ] Separate commit for version bump

## Examples

### Example 1: Bug Fix in as-you

**Changed files**:
- `plugins/as-you/hooks/session_start.py` (bug fix)

**Required version change**:
- as-you: `0.3.3` → `0.3.4` (PATCH bump)

### Example 2: New Feature in with-me

**Changed files**:
- `plugins/with-me/commands/analyze.md` (new command)
- `plugins/with-me/with_me/commands/analyze.py` (implementation)

**Required version change**:
- with-me: `0.3.4` → `0.4.0` (MINOR bump)

### Example 3: Documentation Only

**Changed files**:
- `plugins/as-you/docs/technical-overview.md`
- `plugins/as-you/README.md`

**Required version change**:
- None (documentation changes don't require version bump)

## Rationale

**Why this rule exists**:
- Users need to know when plugins have changed
- Version numbers communicate the nature of changes
- Makes debugging and issue reporting easier
- Enables proper dependency management

**Enforcement**:
- Reviewed during PR process
- No automated enforcement (intentional - allows flexibility for docs-only PRs)
