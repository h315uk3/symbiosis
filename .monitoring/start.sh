#!/usr/bin/env bash
# Generate .env from plugin versions and start monitoring stack
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Ensure python3 is available
if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is required but not found in PATH." >&2
  exit 1
fi

# Read plugin versions from plugin.json
AS_YOU_VERSION=$(python3 -c "
import json, pathlib
p = pathlib.Path('$PROJECT_ROOT/plugins/as-you/.claude-plugin/plugin.json')
print(json.loads(p.read_text())['version'])
")

WITH_ME_VERSION=$(python3 -c "
import json, pathlib
p = pathlib.Path('$PROJECT_ROOT/plugins/with-me/.claude-plugin/plugin.json')
print(json.loads(p.read_text())['version'])
")

echo "Plugin versions: as-you=$AS_YOU_VERSION, with-me=$WITH_ME_VERSION"

# Write .env for docker-compose
cat > "$SCRIPT_DIR/.env" <<EOF
AS_YOU_VERSION=$AS_YOU_VERSION
WITH_ME_VERSION=$WITH_ME_VERSION
EOF

# Ensure data directories exist with correct permissions for container users
mkdir -p "$SCRIPT_DIR/data/prometheus" "$SCRIPT_DIR/data/grafana" "$SCRIPT_DIR/data/loki"
for dir in "$SCRIPT_DIR/data/prometheus" "$SCRIPT_DIR/data/grafana" "$SCRIPT_DIR/data/loki"; do
  # Skip chmod if already world-writable (container-owned dirs can't be chmod'd)
  perm=""
  if command -v stat >/dev/null 2>&1; then
    case "$(uname -s)" in
      Linux*) perm="$(stat -c '%a' "$dir")" ;;
      Darwin*) perm="$(stat -f '%Lp' "$dir")" ;;
      *) perm="" ;;
    esac
  fi
  if [ "$perm" != "777" ]; then
    chmod 777 "$dir"
  fi
done

# Start containers
docker compose -f "$SCRIPT_DIR/docker-compose.yml" up -d

echo ""
echo "Monitoring stack started:"
echo "  Grafana:    http://localhost:3000"
echo "  Prometheus: http://localhost:9090"
echo "  Loki:       http://localhost:3100"
echo ""
echo "Configure Claude Code with:"
echo "  export CLAUDE_CODE_ENABLE_TELEMETRY=1"
echo "  export OTEL_METRICS_EXPORTER=otlp"
echo "  export OTEL_LOGS_EXPORTER=otlp"
echo "  export OTEL_EXPORTER_OTLP_PROTOCOL=grpc"
echo "  export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317"
echo "  export OTEL_METRIC_EXPORT_INTERVAL=10000"
echo "  export OTEL_LOG_TOOL_DETAILS=1"
echo "  export OTEL_METRICS_INCLUDE_VERSION=true"
