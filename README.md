# Symbiosis

![Symbiosis](https://h315uk3.github.io/symbiosis/assets/images/banner.webp)

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/downloads/)
[![Tests](https://github.com/h315uk3/symbiosis/actions/workflows/test.yml/badge.svg)](https://github.com/h315uk3/symbiosis/actions/workflows/test.yml)
[![CodeQL](https://github.com/h315uk3/symbiosis/actions/workflows/codeql.yml/badge.svg)](https://github.com/h315uk3/symbiosis/actions/workflows/codeql.yml)

## Two Problems Slowing Down Your Development

Claude guesses instead of asking. Claude forgets everything between sessions. **Symbiosis fixes both.**

### Problem 1: Claude Guesses Instead of Asking

```
You: "Add authentication"
Claude: *implements JWT*
You: "I meant OAuth"
Claude: *rebuilds everything*
```

**Time lost to miscommunication.**

→ **with-me** asks clarifying questions before building.

### Problem 2: Claude Forgets Everything Next Session

```
Today: "Remember, User.findById() can return null - null checks are critical"
Tomorrow: *Claude writes code without null checks*
You: "I told you yesterday about null checks..."
Claude: "Sorry, I don't remember previous sessions"
```

**You repeat the same lessons in every session.**

→ **as-you** captures insights and surfaces them when relevant.

## The Solution

**[with-me](./plugins/with-me/)** — Asks intelligent questions before building. No more guessing. No more rebuilding.

**[as-you](./plugins/as-you/)** — Captures insights, extracts patterns, promotes to reusable skills and workflows. No more losing knowledge between sessions.

> **Zero setup.** Install and use immediately. No configuration. No external services.

**See it work:** [with-me demo](./plugins/with-me/README.md#demo) | [as-you demos](./plugins/as-you/README.md#demos)

## How It Works

### with-me: Clarify Before Building

Turns vague ideas into detailed specifications through systematic questioning.

```bash
You: "Add authentication"

/with-me:good-question

Claude: "What authentication method?"
  → OAuth 2.0, JWT, session-based, or API keys?

Claude: "Where to store tokens?"
  → localStorage, httpOnly cookies, or memory?

# Continues across 5 dimensions until clear

Result: Detailed specification with acceptance criteria,
edge cases, security considerations, and implementation steps.
```

### as-you: Build Persistent Knowledge

Claude forgets between sessions. Your insights, discoveries, and hard-earned knowledge disappear.

**as-you** stores notes and extracts patterns automatically. Learn once. Reference forever.

```bash
# During development: Capture insights
/as-you:learn "User.findById() returns null if not found - null check critical"
/as-you:learn "Auth middleware checks user.role before admin routes"

# Manage patterns: promote to skills/agents, review quality, view statistics
/as-you:patterns

# Next session: Relevant patterns shown at session start
Session start: "Relevant habits for this session:
  1. User.findById() returns null if not found..."
```

## Why It Works

**with-me** covers 5 critical dimensions systematically: what you're building, what data it uses, how it behaves, what constraints exist, and what quality standards matter. Stops when everything is clear.

**as-you** captures notes automatically from your work. Patterns emerge from repeated observations. Scores by relevance and recency. Promote valuable patterns to reusable skills. Review quality periodically. Surfaces the right patterns at the right time.

Pure Python 3.11+ standard library—no external dependencies, no network calls except Claude Code API.

**Fast. Private. Auditable. Works offline.**

## Quick Start

Add the marketplace:

```
/plugin marketplace add h315uk3/symbiosis
```

Install plugins:

```
/plugin install with-me@h315uk3-symbiosis
/plugin install as-you@h315uk3-symbiosis
```

**Start immediately:**

```bash
/with-me:good-question    # Clarify requirements
/as-you:learn             # Capture insights
/as-you:patterns          # Manage learned patterns
```

No configuration files. No API keys. No setup steps.

## Usage Examples

### with-me: Clarify Requirements Through Questions

**Scenario**: "Add user authentication"

```bash
/with-me:good-question

# Claude asks 5-12 targeted questions:
Claude: "What authentication method?"
  → OAuth 2.0, JWT, session-based, or API keys?

Claude: "Where to store tokens?"
  → localStorage, httpOnly cookies, or memory?

Claude: "Token expiration strategy?"
  → Short-lived only, refresh tokens, or remember-me?

# Result: Detailed specification including:
# - Acceptance criteria
# - Edge cases (token expiration, concurrent sessions)
# - Security considerations
# - Implementation steps
```

### as-you: Capture Insights

**Scenario**: Recording discoveries during development

```bash
/as-you:learn "User.findById() can return null - null check is critical"
/as-you:learn "PostgreSQL EXPLAIN shows sequential scan on users table"
/as-you:learn "JWT tokens expire after 1 hour in this project"

# Patterns emerge from repeated notes automatically
# High-value patterns can be promoted to reusable skills
# Common procedures can be saved as executable workflows
```

### as-you: Manage Patterns

**Scenario**: Reviewing and promoting learned patterns

```bash
/as-you:patterns

# Options shown:
# - Save as skill/agent (promote high-value patterns to reusable components)
# - Analyze patterns (identify valuable patterns worth promoting)
# - Review quality (periodic assessment to maintain knowledge)
# - View statistics (see top patterns and usage frequency)

# Example: Promoting a pattern to a reusable skill
Select: "Save as skill/agent"
Pattern: "Always check User.findById() for null before accessing properties"
Type: skill
Result: Skill created at .claude/skills/u-null-safety/SKILL.md
```

### as-you: Save Reusable Workflows

**Scenario**: Repeating multi-step procedures

```bash
# Save recent work as workflow
/as-you:workflows "deploy-to-staging"
# Creates custom command: /u-deploy-to-staging

# Execute directly as slash command
/u-deploy-to-staging

# Or execute from dashboard
/as-you:workflows
# Select workflow → Execute
```

## What Makes This Different

Most AI tools add features. Symbiosis fixes fundamental problems.

**with-me** asks before implementing. Covers purpose, data, behavior, constraints, and quality systematically. Requirements become clear before any code is written. No more expensive rebuilds from miscommunication.

**as-you** captures insights during development. Patterns emerge automatically from your notes. Promote valuable patterns to reusable skills and agents. Review quality periodically. Surfaces them when relevant. No more losing hard-earned knowledge between sessions.

### Local-First, Privacy-First

Your code, your patterns, your requirements—stay on your machine.

- No telemetry
- No cloud services
- No authentication
- No network calls (except Claude Code API itself)

**Auditable**: Pure Python standard library. Read the source. Verify the algorithms.

## Deep Dive

Want to understand the algorithms? See the technical documentation:

- **[with-me: Technical Overview](./plugins/with-me/docs/technical-overview.md)** — Shannon entropy, Bayesian inference, expected information gain, 5-dimension convergence framework
- **[as-you: Technical Overview](./plugins/as-you/docs/technical-overview.md)** — BM25 relevance scoring, Thompson Sampling exploration-exploitation, SM-2 spaced repetition algorithm

## License

GNU AGPL v3 - [LICENSE](LICENSE)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)
