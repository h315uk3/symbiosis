---
applyTo: "plugins/**"
---

# Plugin Development

## Structure

Each plugin follows the layout: `plugins/{name}/`

- `{name}/lib/` — Core algorithms and business logic (most important code)
- `{name}/commands/` — CLI command entry points (thin wrappers delegating to lib)
- `commands/*.md` — Claude command definitions (frontmatter with description, allowed-tools)
- `agents/*.md` — Claude agent definitions
- `skills/*/SKILL.md` — Claude skill definitions
- `hooks/hooks.json` — Hook configuration
- `.claude-plugin/plugin.json` — Plugin metadata and version

## Versioning

- Every code change under `plugins/` requires a version bump in `.claude-plugin/plugin.json`
- Follow semver: MAJOR (breaking), MINOR (new feature), PATCH (bug fix)
- Documentation-only changes do not require version bumps

## PYTHONPATH

- Claude Code sets `PYTHONPATH` via `CLAUDE_PLUGIN_ROOT` environment variable
- Do not manipulate `sys.path` manually — it causes linter warnings (E402)
- Import plugin modules directly: `from {plugin_name}.lib.module import func`

## Constraints

- Python standard library only — no external packages
- All processing must be local (no network calls)
- File-based persistence using JSON and Markdown
- Human-readable data formats
