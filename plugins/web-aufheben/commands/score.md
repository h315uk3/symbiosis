---
name: score
description: "QAPスコアのみを高速計算して表示する (パターン検出なし)"
---

# /web-anomaly-detector:score

QAP 18パラメーターの数値計算のみを実行し、Composite Score を表示する。
パターン検出・レポート生成は行わない軽量版。

## Usage

```bash
/web-anomaly-detector:score [scope] [--verify]
```

### Arguments

- `scope` (optional): `full` (default) / `path:src/api` (特定ディレクトリ)
- `--verify` (optional): LM Studio (Qwen3-Coder-Next) で上位マッチを検証し adjusted QAP を算出

## Execution Flow

### 1. プロジェクト偵察

Glob でプロジェクトスタックを検出し、ソースディレクトリを特定。

### 2. QAP 計測 (直列で高速実行)

Agent を使わず、直接 Grep/Glob で 18 パラメーターを計測する。
参照: `references/quantitative-parameters.md`

**Ghost (G1-G6):**
```bash
# CFR: 型定義 vs API 実装の一致率
Grep "export (interface|type) " glob="*.ts" path="types/"  → total_types
Grep "return.*as " glob="*.ts" path="api/"                 → matched_types
CFR = matched / total

# EHD: catch 内のエラー処理率
Grep "catch\s*[({]" glob="*.ts,*.js" output_mode="count"   → total_catch
Grep "catch" -A 3 glob="*.ts,*.js"                         → check for log/throw
EHD = handled / total_catch

# ESR: イベント定義 vs 購読率
Grep "WS_EVENTS|SOCKET_EVENT|EVENT_" glob="*.ts"           → defined_events
Grep "subscribe|on\(|addEventListener" glob="*.ts"          → subscribed
ESR = subscribed / defined

# HLR: ハンドラの実装率
Grep "@click|onClick|on:click|\(click\)" glob="*.vue,*.tsx,*.svelte"
# → 空関数・TODO・noop を検出
HLR = implemented / total_handlers

# RRR: ルート到達率
Grep "path:|to=" glob="*.ts,*.vue,*.tsx"                    → defined_routes
Grep "href=|<Link|<NuxtLink|<a " glob="*.vue,*.tsx"        → linked_routes
RRR = linked / defined

# ARR: アクション応答率 (L10)
Grep "onClick|@click|on:click|@submit|onSubmit" glob="*.vue,*.tsx,*.svelte,*.jsx"  → total_actions
Grep "setState|ref\\.value|\\$patch|mutate|invalidate|refetch|refresh" glob="*.vue,*.tsx,*.svelte,*.jsx" → with_response
ARR = with_response / total_actions
```

**Fragile (F1-F8):**
```bash
# NCI: 命名一貫性
Grep "[a-z][A-Z]" glob="*.ts" output_mode="count"          → camelCase count
Grep "[a-z]_[a-z]" glob="*.ts" output_mode="count"         → snake_case count
NCI = majority / total

# CSS: 設定散在度
Grep "process\.env\.|import\.meta\.env\." glob="*.ts,*.js" → env references
# → 同一キーの出現箇所数 / ユニークキー数
CSS = locations / unique_keys

# TCR: タイムアウト設定率
Grep "fetch\(|axios\.|http\." glob="*.ts,*.js"             → total_fetches
Grep "timeout|AbortController|signal" glob="*.ts,*.js"     → with_timeout
TCR = with_timeout / total_fetches

# AGC: 認証ガード率
Grep "defineEventHandler|export default" path="api/" glob="*.ts" → total_endpoints
Grep "getServerSession|requireAuth|auth" path="api/" glob="*.ts" → guarded
AGC = guarded / total_endpoints

# SEC: 秘密鍵露出数
Grep "(api[_-]?key|secret|password|token)\s*[:=]\s*['\"]" glob="*.ts,*.js,*.env"
SEC = count (Presence: 0 = healthy)

# RPC: リトライ/サーキットブレーカー率
Grep "retry|circuit.?breaker|backoff" glob="*.ts,*.js"     → resilient
RPC = resilient / total_external_calls

# MLS: メモリリーク対称性
Grep "addEventListener|subscribe|setInterval" glob="*.ts,*.js,*.vue" → open
Grep "removeEventListener|unsubscribe|clearInterval" glob="*.ts,*.js,*.vue" → close
MLS = |open - close| / max(open, 1)

# GSS: グレースフルシャットダウン
Grep "SIGTERM|SIGINT|beforeExit|graceful" glob="*.ts,*.js"
Grep "server\.close|app\.close|drain|keepAliveTimeout" glob="*.ts,*.js"
GSS = 1.0 (both) / 0.5 (signal only) / 0.0 (none)
```

**Blind Spot (B1-B4):**
```bash
# TSI: TODO 放置指標
Grep "TODO|FIXME|HACK|XXX" glob="*.ts,*.js,*.vue,*.jsx,*.tsx,*.py"
# → git blame で各 TODO の最終更新日を取得 (90日超過 = stale)
TSI = stale_todos / total_todos (Ratio, inverted: 低い方が健全)

# ITCR: 暗黙型変換リスク
Grep "[^!=!]==[^=]" glob="*.ts,*.js"           # == (非厳密等値)
Grep "[^!]!=[^=]" glob="*.ts,*.js"             # != (非厳密不等値)
ITCR = count (Presence: 0 = healthy)

# BVG: 入力バリデーション欠落率
Grep "getQuery\(|readBody\(|req\.body|req\.query|req\.params" path="server/" glob="*.ts,*.js"
Grep "zod|joi|yup|validate|schema|z\.\w+" path="server/" glob="*.ts,*.js"
BVG = validated_endpoints / total_input_endpoints

# DFS: 依存管理品質
Glob "pnpm-lock.yaml" OR Glob "package-lock.json" OR Glob "yarn.lock"
Grep '"\\^|"~' glob="package.json"
DFS = (has_lockfile × 0.4) + (pinned_ratio × 0.3) + (no_dangerous_scripts × 0.3)
```

### 3. Composite Score 算出

`references/quantitative-parameters.md` の Composite Scores セクションに従い算出。
`'` 付きパラメーターは反転変換済み (同ファイル参照)。
Overall = 0.40×Ghost + 0.35×Fragile + 0.25×BlindSpot

### 4. スコア表示

```markdown
## QAP Score: [プロジェクト名]

### Mode: raw / verified (Qwen3-Coder-Next)

| Category | Raw | Adjusted | Status | Key Factors |
|----------|-----|----------|--------|-------------|
| Ghost | 0.XX | 0.XX | STATUS | CFR=0.XX, EHD=0.XX |
| Fragile | 0.XX | 0.XX | STATUS | AGC=0.XX, TCR=0.XX |
| Blind Spot | 0.XX | 0.XX | STATUS | BVG=0.XX, TSI=0.XX |
| **Overall** | **0.XX** | **0.XX** | **STATUS** | |

### 個別パラメーター
| Param | Raw | Adjusted | Conf | Type | Status |
|-------|-----|----------|------|------|--------|
| CFR | 0.XX | 0.XX | 0.XX | Ratio | OK/WARN/CRIT |
| EHD | 0.XX | 0.XX | 0.XX | Ratio | OK/WARN/CRIT |
| ... | ... | ... | ... | ... | ... |

判定: >= 0.80 Healthy / 0.50-0.80 Warning / < 0.50 Critical
Adjusted = Raw × (0.5 + 0.5 × avg_confidence) — 詳細: quantitative-parameters.md
```

`--verify` なしの場合: Raw = Adjusted (confidence カラムは `—` 表示)

## Tool Coordination

| Tool | 用途 |
|------|------|
| **Glob** | プロジェクト偵察 |
| **Grep** | QAP パラメーター計測 (全18個) |
| **Read** | quantitative-parameters.md 参照 |

## Boundaries

**Will:**
- 18 QAP パラメーターの数値計測
- Composite Score 算出
- スコアテーブル出力

**Will Not:**
- パターン検出 (scan の責務)
- レイヤー別の詳細レポート生成
- コード修正
- ファイル書き出し
