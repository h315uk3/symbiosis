# Test Scenario: /as-you:help Command

Test the help command: display plugin documentation and command reference.

## Scenario 1: Display Help Information

### Prerequisites
- [ ] Claude Code session active
- [ ] as-you plugin installed

### Test Steps

#### Step 1.1: Execute Help Command
```
/as-you:help
```

**Expected behavior:**
- [ ] Displays plugin information:
  - Plugin name and version (e.g., "As You v0.3.2")
  - Brief description
- [ ] Lists all available commands with usage:
  - `/as-you:learn [note]`
  - `/as-you:memory`
  - `/as-you:apply [workflow]`
  - `/as-you:active [on|off|status]`
  - `/as-you:help`
- [ ] For each command shows:
  - Brief description
  - Usage syntax
  - Key features or modes
- [ ] Shows data location information:
  - `.claude/as_you/` directory
  - Key files (session_notes, pattern_tracker, etc.)
- [ ] Mentions privacy: "All data stays local"
- [ ] References to config files or additional documentation
- [ ] No errors occur
- [ ] Output is well-formatted and readable

**Verification:**
- [ ] All 5 commands are documented
- [ ] Syntax examples are correct
- [ ] Information matches actual command behavior

---

## Scenario 2: Help After Other Commands

### Prerequisites
- [ ] Some plugin usage history (notes, patterns, workflows)

### Test Steps

#### Step 2.1: Use Help in Context
After using several commands, run:
```
/as-you:help
```

**Expected behavior:**
- [ ] Help information displayed same as Scenario 1
- [ ] No state-dependent information (help is static)
- [ ] Previous command history doesn't affect help output

---

## Edge Cases

### EC1: Help with Arguments (should ignore)
```
/as-you:help some-argument
```

**Expected behavior:**
- [ ] Arguments ignored (help has no arguments)
- [ ] Standard help information displayed
- [ ] No errors

### EC2: Help When Plugin Data Missing
Delete plugin data directory:
```bash
rm -rf .claude/as_you/
```

Run:
```
/as-you:help
```

**Expected behavior:**
- [ ] Help displays normally
- [ ] Help command doesn't depend on plugin data
- [ ] No errors

---

## Verification Checklist

### Command Documentation Completeness

Verify help includes these details for each command:

**`/as-you:learn`:**
- [ ] With argument: adds note (auto-translated to English)
- [ ] Without argument: interactive dashboard
- [ ] Mentions modes: add/view/analyze notes

**`/as-you:memory`:**
- [ ] Pattern analysis dashboard
- [ ] Mentions features: top patterns, confidence, promotion candidates, SM-2

**`/as-you:apply`:**
- [ ] With argument: saves workflow
- [ ] Without argument: browse and execute workflows
- [ ] Mentions pattern context retrieval

**`/as-you:active`:**
- [ ] Toggle automatic capture
- [ ] Mentions arguments: on/off/status
- [ ] States default: OFF

**`/as-you:help`:**
- [ ] This guide

### Data Location Information

- [ ] Mentions `.claude/as_you/` directory
- [ ] Lists key files:
  - `session_notes.local.md`
  - `session_archive/*.md`
  - `pattern_tracker.json`
  - `active_learning.json`
  - `workflows/*.md`
- [ ] States "All data stays local"

### References

- [ ] Links or mentions config files
- [ ] References to schema files (if applicable)

---

## Output Format Verification

### Step 1: Check Markdown Rendering
Help should be formatted with:
- [ ] Headers (# ## ###)
- [ ] Code blocks for commands
- [ ] Lists (bullet or numbered)
- [ ] Proper spacing and readability

### Step 2: Check Accuracy
- [ ] Version number matches plugin.json
- [ ] Command syntax matches actual implementation
- [ ] File paths are correct
- [ ] No outdated information

---

## Related Tests

This is a standalone test with no dependencies. Help command can be tested independently at any time.

However, to verify help content accuracy, cross-reference with:
- [learn.md](./learn.md) - `/as-you:learn` command behavior
- [apply.md](./apply.md) - `/as-you:apply` command behavior
- [memory.md](./memory.md) - `/as-you:memory` command behavior
- [active.md](./active.md) - `/as-you:active` command behavior
