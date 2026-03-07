#!/bin/bash
# PostToolUse:Edit — パッシブ違和感検出フック
#
# ファイル編集後に軽量チェックを実行し、明らかな違和感を即時通知する。
# 全レイヤースキャンではなく、高速で検出可能な L2 (サイレント失敗) と
# L7 (セキュリティ) の2レイヤーに限定。
#
# データ取得: stdin JSON (Claude Code 方式)
#   { "tool_input": { "file_path": "...", "new_string": "..." } }

set -uo pipefail

# stdin から JSON を読み取り
STDIN_JSON=$(cat)

# jq 存在チェック — なければサイレント終了
if ! command -v jq &>/dev/null; then
  exit 0
fi

FILE_PATH=$(printf '%s' "$STDIN_JSON" | jq -r '.tool_input.file_path // empty')
NEW_STRING=$(printf '%s' "$STDIN_JSON" | jq -r '.tool_input.new_string // empty')

# ファイルパスが空なら終了
[ -z "$FILE_PATH" ] && exit 0

# 対象拡張子のフィルタ (スタック非依存: Web/Backend/Systems)
EXT="${FILE_PATH##*.}"
case "$EXT" in
  ts|js|vue|tsx|jsx|svelte|html|py|go|rs|rb|java|kt|php) ;;
  *) exit 0 ;;
esac

WARNINGS=""

# --- L2: サイレント失敗チェック ---

# 空 catch ブロック検出 (JS/TS) — single-line
if printf '%s' "$NEW_STRING" | grep -qE 'catch\s*\([^)]*\)\s*\{\s*\}'; then
  WARNINGS="${WARNINGS}[L2] Empty catch block detected — errors will be silently swallowed\n"
fi

# 空 catch ブロック検出 (JS/TS) — multi-line: catch(...) { のみで次行に処理なし
if printf '%s' "$NEW_STRING" | grep -qE 'catch\s*\([^)]*\)\s*\{\s*$'; then
  # catch 開始行を検出 → 後続行が } のみ (空白除く) なら空 catch
  CATCH_BODY=$(printf '%s' "$NEW_STRING" | sed -n '/catch\s*([^)]*)\s*{\s*$/,/}/p' | sed '1d;$d' | tr -d '[:space:]')
  if [ -z "$CATCH_BODY" ]; then
    WARNINGS="${WARNINGS}[L2] Multi-line empty catch block detected — errors will be silently swallowed\n"
  fi
fi

# .catch(() => {}) パターン
if printf '%s' "$NEW_STRING" | grep -qE '\.catch\(\s*\([^)]*\)\s*=>\s*\{\s*\}\s*\)'; then
  WARNINGS="${WARNINGS}[L2] Silent .catch() — promise errors will be lost\n"
fi

# except: pass (Python)
if printf '%s' "$NEW_STRING" | grep -qE 'except.*:\s*pass\s*$'; then
  WARNINGS="${WARNINGS}[L2] except: pass — Python errors silently ignored\n"
fi

# --- L7: セキュリティチェック ---

# ハードコードされた秘密鍵/トークン (シングルクォート・ダブルクォート両対応)
if printf '%s' "$NEW_STRING" | grep -qEi '(api[_-]?key|secret|password|token|credential)\s*[:=]\s*["'"'"'][A-Za-z0-9+/=_-]{8,}'; then
  WARNINGS="${WARNINGS}[L7] Possible hardcoded secret detected — use environment variables\n"
fi

# eval() 使用
if printf '%s' "$NEW_STRING" | grep -qE '\beval\s*\('; then
  WARNINGS="${WARNINGS}[L7] eval() usage detected — potential code injection risk\n"
fi

# innerHTML 直接代入
if printf '%s' "$NEW_STRING" | grep -qE '\.innerHTML\s*='; then
  WARNINGS="${WARNINGS}[L7] innerHTML assignment — potential XSS vulnerability\n"
fi

# SQL 文字列結合
if printf '%s' "$NEW_STRING" | grep -qEi '(SELECT|INSERT|UPDATE|DELETE).*\+.*["'"'"'`]'; then
  WARNINGS="${WARNINGS}[L7] SQL string concatenation — use parameterized queries\n"
fi

# --- 結果出力 ---

if [ -n "$WARNINGS" ]; then
  printf '%s\n' "⚠ web-anomaly-detector passive check:"
  printf '%b\n' "$WARNINGS"
  # 非ブロッキング — exit 0 で編集を止めない
fi

exit 0
