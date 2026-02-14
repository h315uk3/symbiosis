#!/usr/bin/env bash
# Stop monitoring stack
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
docker compose -f "$SCRIPT_DIR/docker-compose.yml" down
echo "Monitoring stack stopped."
