# Contributing to with-me

This guide covers with-me plugin specific development. For general contribution guidelines, see the [root CONTRIBUTING.md](../../CONTRIBUTING.md).

## Plugin Overview

with-me is a requirement elicitation plugin that:
- Guides users through adaptive questioning
- Explores uncertainty dimensions systematically
- Tracks question effectiveness with reward scoring
- Converges when sufficient information is gathered

## Architecture

**Key Components:**
- **Commands**: User-facing slash commands (`/with-me:good-question`)
- **Skills**: Computational algorithms (`/with-me:requirement-analysis`)
- **Library**: Shared Python modules for feedback tracking and statistics

**Question Dimensions:**
- Purpose and goals
- Data and information
- Behavior and interactions
- Constraints and requirements
- Quality attributes

## Testing Commands

### Test Setup

1. **Start Fresh Session**
   ```bash
   /exit
   claude
   ```

2. **Verify Plugin Loaded**
   - Check for plugin loaded message

### Command Test Procedures

**`/with-me:good-question` - Requirement Elicitation**
- Test: Start a new elicitation session
- Verify:
  1. Session starts (question_feedback.json created/updated)
  2. Adaptive questions are asked based on uncertainty dimensions
  3. Each question-answer pair is recorded with reward scores
  4. Session completes with summary displayed
  5. Check `<workspace>/.claude/with_me/question_feedback.json` contains session data

### Skill Test Procedures

**`/with-me:requirement-analysis` - Analyze Requirements**
- Test: Run after collecting requirements via good-question
- Verify: Structured analysis output with ambiguities and suggestions

### When to Test

**Must test before commit:**
- New command creation
- Question logic changes
- Feedback tracking modifications
- Frontmatter modifications

**Optional:**
- Minor wording improvements
- Comment/documentation changes

## Adding New Python Modules

1. Follow existing module patterns in `with_me/lib/` for structure and doctest format
2. Run `mise run test` to verify doctests pass
3. Run `mise run lint` to ensure code style compliance

## Common Issues

**Frontmatter Errors:**
- Missing `allowed-tools`: Add required tools to frontmatter
- Invalid YAML: Check indentation and quotes

**AskUserQuestion Errors:**
- Maximum 4 options (excluding auto-added "Other")
- Ensure options are distinct and meaningful

## Resources

- [Technical Overview](./docs/technical-overview.md) - Architecture and information theory
- [Root CONTRIBUTING](../../CONTRIBUTING.md) - General guidelines
