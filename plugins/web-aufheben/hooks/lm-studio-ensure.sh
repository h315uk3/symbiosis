#!/bin/bash
# lm-studio-ensure.sh — LM Studio サーバー + Qwen3-Coder-Next 自動ロード
#
# scan.md の VERIFY フェーズ前に呼び出し、LM Studio の準備を保証する。
# 成功時: "READY:<model_id>" を stdout へ出力
# 失敗時: "UNAVAILABLE:<reason>" を stdout へ出力 (exit 0 — 非ブロッキング)
#
# Usage:
#   MODEL_INFO=$(bash hooks/lm-studio-ensure.sh)
#   case "$MODEL_INFO" in
#     READY:*) MODEL_ID="${MODEL_INFO#READY:}" ;;
#     *)       echo "grep-only fallback" ;;
#   esac

set -uo pipefail

# --- Cleanup on exit ---
LOAD_PID=""
cleanup() {
  if [ -n "$LOAD_PID" ]; then
    kill "$LOAD_PID" 2>/dev/null || true
    wait "$LOAD_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT
trap 'exit 130' INT TERM

# --- Configuration ---
LMS="${LMS_PATH:-${HOME}/.lmstudio/bin/lms}"
MODEL_PATH="qwen/qwen3-coder-next"
MODEL_IDENTIFIER="qwen3-coder-next"
API_BASE="http://localhost:1234"
SERVER_START_TIMEOUT=15    # seconds
MODEL_LOAD_TIMEOUT=120     # seconds (80B model can take time)
HEALTH_CHECK_TIMEOUT=3     # seconds

# --- Helper ---
log() { echo "[lm-studio-ensure] $*" >&2; }

# --- Step 0: CLI existence check ---
if [ ! -x "$LMS" ]; then
  echo "UNAVAILABLE:lms_cli_not_found"
  exit 0
fi

# --- Step 1: Server status ---
SERVER_STATUS=$("$LMS" server status 2>/dev/null) || SERVER_STATUS="not_running"

if echo "$SERVER_STATUS" | grep -q "running"; then
  log "Server already running"
else
  log "Starting LM Studio server..."
  "$LMS" server start >/dev/null 2>&1 &

  # Wait for server readiness
  ELAPSED=0
  while [ $ELAPSED -lt $SERVER_START_TIMEOUT ]; do
    if curl -s --connect-timeout 1 "${API_BASE}/api/v0/models" >/dev/null 2>&1; then
      log "Server ready (${ELAPSED}s)"
      break
    fi
    sleep 1
    ELAPSED=$((ELAPSED + 1))
  done

  if [ $ELAPSED -ge $SERVER_START_TIMEOUT ]; then
    echo "UNAVAILABLE:server_start_timeout"
    exit 0
  fi
fi

# --- Step 2: Check if model is already loaded ---
LOADED=$("$LMS" ps 2>/dev/null) || LOADED=""

if echo "$LOADED" | grep -qi "qwen3-coder-next"; then
  log "Model already loaded"
  # Retrieve model ID from API
  MODEL_ID=$(curl -s --connect-timeout "$HEALTH_CHECK_TIMEOUT" --max-time 10 \
    "${API_BASE}/api/v0/models" 2>/dev/null \
    | jq -r '.data[] | select(.id | test("qwen3.*coder.*next"; "i")) | .id' 2>/dev/null \
    | head -1)
  if [ -z "$MODEL_ID" ] || [ "$MODEL_ID" = "null" ]; then
    log "Warning: could not parse model ID from API response"
  fi

  if [ -n "$MODEL_ID" ] && [ "$MODEL_ID" != "null" ]; then
    echo "READY:${MODEL_ID}"
  else
    echo "READY:${MODEL_IDENTIFIER}"
  fi
  exit 0
fi

# --- Step 3: Load model ---
log "Loading ${MODEL_PATH} (this may take 30-90s)..."
"$LMS" load "$MODEL_PATH" \
  --gpu max \
  --identifier "$MODEL_IDENTIFIER" \
  -y \
  >/dev/null 2>&1 &
LOAD_PID=$!

# Wait for model to appear in loaded list
ELAPSED=0
while [ $ELAPSED -lt $MODEL_LOAD_TIMEOUT ]; do
  # Check via API
  MODELS=$(curl -s --connect-timeout "$HEALTH_CHECK_TIMEOUT" --max-time 10 \
    "${API_BASE}/api/v0/models" 2>/dev/null || true)

  if echo "$MODELS" | jq -e '.data[] | select(.id | test("qwen3.*coder.*next"; "i"))' >/dev/null 2>&1; then
    log "Model loaded successfully (${ELAPSED}s)"
    kill "$LOAD_PID" 2>/dev/null || true
    wait "$LOAD_PID" 2>/dev/null || true
    LOAD_PID=""

    MODEL_ID=$(echo "$MODELS" \
      | jq -r '.data[] | select(.id | test("qwen3.*coder.*next"; "i")) | .id' \
      | head -1)
    echo "READY:${MODEL_ID:-${MODEL_IDENTIFIER}}"
    exit 0
  fi

  sleep 2
  ELAPSED=$((ELAPSED + 2))
done

# Timeout
kill "$LOAD_PID" 2>/dev/null || true
wait "$LOAD_PID" 2>/dev/null || true
LOAD_PID=""
echo "UNAVAILABLE:model_load_timeout"
exit 0
