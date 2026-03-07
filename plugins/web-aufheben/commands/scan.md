---
name: scan
description: "プロジェクト全体をスキャンし、3カテゴリ×10レイヤーの違和感レポートを生成する"
---

# /web-anomaly-detector:scan

プロジェクト全体を 3カテゴリ × 10レイヤーでスキャンし、QAP スコア付きレポートを出力する。
v3.0: LM Studio (Qwen3-Coder-Next) による LLM 検証で偽陽性を削減。

## Usage

```bash
/web-anomaly-detector:scan [scope] [--grep-only]
```

### Arguments

- `scope` (optional): `full` (default) / `diff` (git diff のみ) / `path:src/api` (特定ディレクトリ)
- `--grep-only` (optional): LLM 検証をスキップし、v2.0 互換の grep のみモードで実行

## Execution Flow

```
1. SCOPE   — 対象範囲を特定 (全体 / フロー / git diff)
2. MEASURE — QAP パラメーターを計測 (grep/glob 並列)
3. VERIFY  — LLM で偽陽性を除去 (LM Studio / Qwen3-Coder-Next)
4. TRIAGE  — QAP スコア + confidence + 重要度で分類
5. REPORT  — confidence 付きレポートを出力
```

### 1. SCOPE — プロジェクト偵察 (並列)

以下を並列で実行し、プロジェクトのスタックを自動検出:

```
Glob "package.json"       → Node/TS/JS (pnpm/npm/yarn/bun)
Glob "Cargo.toml"         → Rust
Glob "go.mod"             → Go
Glob "requirements.txt"   → Python
Glob "nuxt.config.*"      → Nuxt
Glob "next.config.*"      → Next.js
Glob "tsconfig.json"      → TypeScript
```

スコープに応じた対象ファイルリストを作成:
- `full`: ソースディレクトリ全体
- `diff`: `git diff --name-only HEAD` の出力
- `path:X`: 指定ディレクトリ配下

### 2. MEASURE + SCAN — 3 Explore エージェント並列

Agent ツールで 3つの Explore エージェントを **並列** 起動:

```
Agent A (Ghost — L1-L4, L10):
  - references/detection-patterns.md の L1-L4, L10 パターンで grep/glob
  - CFR, EHD, ESR, HLR, RRR, ARR を計測
  - 出力: SEVERITY|LAYER|FILE:LINE|SYMPTOM|ROOT_CAUSE|MATCHED_LINE

Agent B (Fragile — L5-L8):
  - references/detection-patterns.md L5-L6 + security-patterns.md L7 + reliability-patterns.md L8
  - NCI, CSS, TCR, AGC, SEC, RPC, MLS, GSS を計測
  - 出力: 同上フォーマット

Agent C (Blind Spot — L9):
  - references/implicit-knowledge.md の 32 パターンで grep
  - TSI, ITCR, BVG, DFS を計測
  - 出力: 同上フォーマット
```

各エージェントのプロンプトに含めるコンテキスト:
- 対象ファイルリスト (Step 1 で取得)
- 該当 references/ ファイルのパス
- QAP 計測方法 (quantitative-parameters.md の該当セクション)

**重要**: 各マッチの `FILE:LINE` と `MATCHED_LINE` を必ず収集。Step 3 の VERIFY で使用する。

### 3. VERIFY — LLM 偽陽性検証

**条件**: `--grep-only` 未指定かつ LM Studio が利用可能な場合のみ実行。
**参照**: `references/llm-verify.md` (完全仕様)

#### 3a. LM Studio 自動準備

```bash
# Bash ツールで実行 — サーバー起動 + モデルロードを自動化
SKILL_DIR=$(dirname "$(dirname "$0")")  # hooks/ の親ディレクトリ
MODEL_INFO=$(bash "${SKILL_DIR}/hooks/lm-studio-ensure.sh")

case "$MODEL_INFO" in
  READY:*)   MODEL_ID="${MODEL_INFO#READY:}" ;;
  *)         # grep-only fallback
             echo "⚠ LM Studio 準備失敗 (${MODEL_INFO})。grep-only モードで実行"
             ;;
esac
```

- `UNAVAILABLE:*` → grep-only モードで Step 4 へ (自動フォールバック)
- `READY:<model_id>` → Step 3b へ (LLM 検証モード)

#### 3b. マッチ優先度ソート

全マッチを QAP 影響度でソート:
```
Priority = QAP_weight × severity_multiplier
  CRITICAL candidate (QAP < 0.50): 3.0
  WARNING candidate  (0.50-0.80):  1.5
  INFO candidate     (>= 0.80):    0.5
```

バッチ上限: マッチ数 ≤50 は全件、51-300 は上位 100 件、300+ は上位 100 件。

#### 3c. LLM バッチ検証

上位 N 件を順次 LM Studio に送信:

```bash
# 各マッチに対して:
# 1. Read ツールで FILE:LINE の前後 10 行を取得
# 2. カテゴリ別プロンプトを構築 (references/prompts/ 参照)
# 3. curl で LM Studio API に送信

curl -s http://localhost:1234/api/v0/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "'"$MODEL_ID"'",
    "messages": [
      {"role": "system", "content": "...category-specific system prompt..."},
      {"role": "user", "content": "...match + context..."}
    ],
    "temperature": 0.1,
    "max_tokens": 256,
    "stream": false,
    "response_format": {
      "type": "json_schema",
      "json_schema": { ...verification_schema... }
    }
  }'
```

レスポンス解析:
```bash
RESULT=$(echo "$RESPONSE" | jq -r '.choices[0].message.content')
IS_ANOMALY=$(echo "$RESULT" | jq -r '.is_anomaly')
CONFIDENCE=$(echo "$RESULT" | jq -r '.confidence')
CATEGORY=$(echo "$RESULT" | jq -r '.category')  # TRUE_POSITIVE / FALSE_POSITIVE / UNCERTAIN
```

#### 3d. Confidence 集約

```
For each QAP parameter:
  verified_matches = matches with LLM results
  avg_confidence = mean(confidence where is_anomaly=true)
  adjusted_QAP = raw_QAP × (0.5 + 0.5 × avg_confidence)
```

未検証マッチ (バッチ上限超過) は `confidence=0.5` を付与。

### 4. TRIAGE — 集約・分類

3 エージェントの結果 + VERIFY の confidence を統合し、分類:

```
CRITICAL: adjusted_QAP < 0.50 / データ消失・セキュリティ・完全非動作
WARNING:  adjusted_QAP 0.50-0.80 / 部分的非動作・一貫性欠如
INFO:     adjusted_QAP >= 0.80 だが改善余地あり
```

LLM 検証で `FALSE_POSITIVE` 判定 (confidence >= 0.8) のマッチは降格:
- CRITICAL → WARNING (confirmed false positive)
- WARNING → INFO (confirmed false positive)

### 5. REPORT — レポート出力

以下のフォーマットで直接出力 (ファイル保存はしない):

```markdown
## 違和感レポート: [プロジェクト名]

### Mode
LLM-verified (Qwen3-Coder-Next / N件検証) / grep-only

### Scores
| Category | Raw | Adjusted | Status |
|----------|-----|----------|--------|
| Ghost | 0.XX | 0.XX | STATUS |
| Fragile | 0.XX | 0.XX | STATUS |
| Blind Spot | 0.XX | 0.XX | STATUS |
| **Overall** | **0.XX** | **0.XX** | **STATUS** |

### CRITICAL (N件)
| # | Cat | Layer | QAP | Conf | Location | Symptom | Root Cause |
|---|-----|-------|-----|------|----------|---------|------------|

### WARNING (N件)
| # | Cat | Layer | QAP | Conf | Location | Symptom | Root Cause |
|---|-----|-------|-----|------|----------|---------|------------|

### INFO (N件)
| # | Cat | Layer | QAP | Conf | Location | Symptom | Root Cause |
|---|-----|-------|-----|------|----------|---------|------------|

### LLM Verification Summary (v3.0)
| Metric | Value |
|--------|-------|
| Total grep matches | N |
| LLM verified | N |
| True positives | N |
| False positives removed | N |
| Uncertain | N |
| Avg confidence | 0.XX |
| Avg inference speed | XX tok/s |
```

**Conf カラム**: `0.92` = LLM 高確信, `0.50` = 未検証/中立, `—` = grep-only mode

## Tool Coordination

| Tool | 用途 |
|------|------|
| **Glob** | プロジェクト偵察・ファイル検索 |
| **Grep** | パターン検出・QAP 計測 |
| **Read** | references/ ファイルロード + コンテキスト取得 (±10行) |
| **Agent (Explore)** | 3カテゴリ並列スキャン |
| **Bash** | `git diff` (差分スコープ時) + LM Studio API 呼び出し |

## Boundaries

**Will:**
- 3カテゴリ × 10レイヤーの全パターンスキャン (140パターン)
- 18 QAP パラメーターの計測
- LLM による偽陽性検証 (LM Studio 利用可能時)
- Confidence-adjusted Composite Score の算出
- 重要度別レポート出力 (confidence 付き)

**Will Not:**
- コードの修正 (修正は `/web-aufheben` エージェントの責務)
- テスト実行
- ファイル書き出し (レポートは画面出力のみ)
- 外部 API への送信 (LM Studio は localhost のみ)
