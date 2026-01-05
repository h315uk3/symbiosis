#!/bin/bash
set -euo pipefail
# Post-edit formatting hook example
# Triggered after Edit tool use

# This is a simple example hook that logs edit operations
# In a real scenario, you might run formatters, linters, etc.

echo "File edited: $CLAUDE_TOOL_INPUT" >&2
echo "Hook executed successfully"
