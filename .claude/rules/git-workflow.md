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

## Safety Rules

**NEVER**:
- Force push to main/master
- Commit to main directly
- Rebase shared branches
- Commit secrets or API keys

**ALWAYS**:
- Review changes before committing (`git diff`)
- Test before pushing
- Keep commits focused
- Update documentation with code
