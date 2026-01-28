# GitHub Discussions

## Language Rule

**CRITICAL**: All discussion posts MUST be written in English.
- This is a hard requirement for GitHub collaboration
- Never create discussions in Japanese or other languages
- If user provides Japanese text, translate to English before posting

## Categories

- **Announcements**: Updates from maintainers (project status, releases, breaking changes)
- **Q&A**: Questions from users
- **Ideas**: Feature suggestions and feedback
- **Show and tell**: User showcases

## Announcement Templates

### Status Update
```markdown
Hi everyone,

[Brief description of current status]

**What's happening:**
- [Item 1]
- [Item 2]

**Timeline:** [Expected duration or date]

Thank you for your patience!

---
*This announcement will be updated when [condition].*
```

### Release Announcement
```markdown
## [Version] Released

[Brief description of what's new]

**Highlights:**
- [Feature 1]
- [Feature 2]

**Breaking Changes:** [None / List]

**Upgrade Guide:** [Link or instructions]

See the full changelog in the PR: #[number]
```

### Maintenance Notice
```markdown
## Scheduled Maintenance

**When:** [Date and time with timezone]
**Duration:** [Expected duration]
**Impact:** [What will be affected]

**Details:**
[Description of maintenance work]

We apologize for any inconvenience.
```

## Best Practices

- Keep announcements concise and actionable
- Include timelines when possible
- Update or close discussions when status changes
- Pin important announcements

## Adding Comments via CLI

**CRITICAL**: Always retrieve the Discussion ID first before adding comments.

```bash
# Step 1: Get Discussion ID
gh api graphql -f query='{
  repository(owner: "h315uk3", name: "symbiosis") {
    discussion(number: NUMBER) { id }
  }
}'

# Step 2: Add comment using the retrieved ID
gh api graphql -f query='
mutation {
  addDiscussionComment(input: {
    discussionId: "RETRIEVED_ID",
    body: "Comment content here"
  }) {
    comment { url }
  }
}'
```

Never guess or reuse Discussion IDs from previous sessions.
