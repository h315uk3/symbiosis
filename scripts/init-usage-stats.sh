#!/bin/bash
set -euo pipefail
# Initialize skill usage statistics

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
STATS_FILE="$PROJECT_ROOT/.claude/skill-usage-stats.json"
SKILLS_DIR="$PROJECT_ROOT/skills"
AGENTS_DIR="$PROJECT_ROOT/agents"

# Create stats file if not exists
if [ ! -f "$STATS_FILE" ]; then
	echo '{"skills":{},"agents":{},"last_updated":""}' >"$STATS_FILE"
fi

CURRENT_DATE=$(date +%Y-%m-%d)

# Read current stats
STATS=$(cat "$STATS_FILE")

# Scan all skills
if [ -d "$SKILLS_DIR" ]; then
	for skill_dir in "$SKILLS_DIR"/*/; do
		[ -d "$skill_dir" ] || continue
		SKILL_NAME=$(basename "$skill_dir")

		# Add to stats if not exists
		if ! echo "$STATS" | jq -e ".skills.\"$SKILL_NAME\"" >/dev/null 2>&1; then
			STATS=$(echo "$STATS" | jq ".skills.\"$SKILL_NAME\" = {
                \"created\": \"$CURRENT_DATE\",
                \"invocations\": 0,
                \"last_used\": null,
                \"effectiveness\": \"unknown\"
            }")
		fi
	done
fi

# Scan all agents
if [ -d "$AGENTS_DIR" ]; then
	for agent_file in "$AGENTS_DIR"/*.md; do
		[ -f "$agent_file" ] || continue
		AGENT_NAME=$(basename "$agent_file" .md)

		# Skip system agents
		if [[ "$AGENT_NAME" == "memory-analyzer" ]] ||
			[[ "$AGENT_NAME" == "component-generator" ]] ||
			[[ "$AGENT_NAME" == "promotion-reviewer" ]]; then
			continue
		fi

		# Add to stats if not exists
		if ! echo "$STATS" | jq -e ".agents.\"$AGENT_NAME\"" >/dev/null 2>&1; then
			STATS=$(echo "$STATS" | jq ".agents.\"$AGENT_NAME\" = {
                \"created\": \"$CURRENT_DATE\",
                \"invocations\": 0,
                \"last_used\": null,
                \"effectiveness\": \"unknown\"
            }")
		fi
	done
fi

# Update last_updated timestamp
STATS=$(echo "$STATS" | jq ".last_updated = \"$CURRENT_DATE\"")

# Save stats
echo "$STATS" | jq '.' >"$STATS_FILE"

echo "Usage stats initialized: $(echo "$STATS" | jq '.skills | length') skills, $(echo "$STATS" | jq '.agents | length') agents"
