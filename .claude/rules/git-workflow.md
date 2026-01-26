# Git Workflow

## Branch Strategy

**Format**: `{type}/{description}`

**Types**: `feature/*`, `fix/*`, `docs/*`, `refactor/*`, `test/*`

## Commit Guidelines

**Format**:
```
type: brief description

Optional detailed explanation.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**Types**: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, `perf:`

**Best Practices**:
- Write clear, descriptive messages
- Keep commits atomic (one logical change)
- Use present tense ("add" not "added")
- Run tests before committing
- Never commit broken code or secrets

## Pull Request

**Before PR**:
1. `mise run test`
2. `mise run lint`
3. `mise run validate`

**Requirements**:
- Clear title and description
- All tests passing
- No lint errors
- Updated documentation (if applicable)

**Merge strategy**: Squash and merge (preferred) for clean history

## Destructive Git Operations

**CRITICAL: These commands permanently delete data. NEVER run without explicit user confirmation.**

### Commands that permanently delete uncommitted work:
- `git checkout -- <file>` - Discards all uncommitted changes to file (IRREVERSIBLE)
- `git reset --hard` - Discards all uncommitted changes in working directory
- `git clean -fd` - Deletes all untracked files and directories
- `git restore --staged --worktree <file>` - Discards changes (newer alternative to checkout)

### Commands that rewrite history:
- `git reset --hard <commit>` - Moves HEAD and discards commits
- `git push --force` - Overwrites remote history
- `git rebase -i` - Rewrites commit history

### Mandatory confirmation process:
1. **STOP**: Identify if the command is destructive
2. **VERIFY**: Run `git status` and `git diff` to see what will be lost
3. **ASK**: Show user exactly what will be deleted/changed
4. **WAIT**: Get explicit "yes" or "proceed" from user
5. **EXECUTE**: Only after confirmation

### Safe alternatives:
- Instead of `git checkout -- <file>`: Ask user "Do you want to discard changes to <file>?"
- Instead of `git reset --hard`: Use `git stash` to preserve work
- Instead of `git clean -fd`: List files first with `git clean -n`, then ask

**Example scenario:**
```
User: "unstage the files"
❌ BAD: git checkout -- file.txt
✅ GOOD: git status → show changes → ask "Discard these changes?" → wait for confirmation
```

## Safety Rules

**NEVER**:
- Force push to main/master
- Commit to main directly
- Rebase shared branches
- Commit secrets or API keys
- **Create and push files without explicit user instruction**
- **Push to GitHub without explicit user confirmation**

**ALWAYS**:
- Review changes before committing (`git diff`)
- Test before pushing
- Keep commits focused
- Update documentation with code
- **Show changes locally first, then ask for push permission**
- **Get explicit confirmation before any GitHub operation (commit, push, PR, Issue)**

## Critical: GitHub Operations

**Before any push/PR/GitHub operation**:
1. Show all changes to user (files created, modified, deleted)
2. Explain what will be pushed and why
3. Wait for explicit user confirmation: "OK to push?" or "Create PR?"
4. Never assume permission from implementation requests

**Especially critical for**:
- Hooks and scripts (pre-commit, setup scripts)
- Configuration files (.gitignore, CI/CD configs)
- Documentation changes
- Any file that wasn't explicitly requested

**Rationale**: Once pushed to GitHub, data cannot be easily removed. Commits remain in object storage even after force-push.
