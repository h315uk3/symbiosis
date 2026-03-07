# LLM Verification Pipeline (v3.0)

grep/glob マッチを LM Studio 経由の Qwen3-Coder-Next で検証し、偽陽性を削減する。

## Architecture

```
MEASURE (grep/glob)
    │
    ▼  GrepMatch[] (50-500 matches)
VERIFY (LM Studio)
    │  ├─ Health Check (3s timeout)
    │  ├─ Priority Sort (QAP impact order)
    │  ├─ Batch Inference (top 100)
    │  │   ├─ Ghost matches → ghost-verify prompt
    │  │   ├─ Fragile matches → fragile-verify prompt
    │  │   └─ Blind Spot matches → blindspot-verify prompt
    │  └─ Confidence Aggregation
    ▼  VerificationResult[] + adjusted QAP
TRIAGE (confidence-aware scoring)
```

## Model Configuration

| Setting | Value | Rationale |
|---------|-------|-----------|
| **Model** | Qwen3-Coder-Next | 80B/3B MoE, SWE-bench 70.6%, 358言語対応 |
| **Format** | MLX 8bit | M3 Ultra 512GB に最適。GGUF Q8_0 も可 |
| **LM Studio ID** | `qwen/qwen3-coder-next` | `lms load` パス / API model ID |
| **Context** | 256K tokens (native) | 十分すぎるほどのコンテキスト |
| **Temperature** | 0.1 | 判定の一貫性重視。創造性は不要 |
| **Max Tokens** | 256 | JSON レスポンスに十分 |
| **Response Format** | `json_schema` | 構造化出力で JSON パース失敗を防止 |

### Alternative Models (fallback order)

1. `Qwen3-Coder-Next` MLX 8bit (推奨)
2. `Qwen3-Coder-Next` GGUF Q8_0 (MLX 不安定時)
3. `Qwen3-Coder-30B-A3B` (軽量版、精度やや低下)

## LM Studio API Usage

### Auto-Ensure (Server + Model)

`hooks/lm-studio-ensure.sh` がサーバー起動からモデルロードまでを自動化する。

**環境変数**: `LMS_PATH` で `lms` CLI のパスを上書き可能 (デフォルト: `$HOME/.lmstudio/bin/lms`)。

```bash
# scan.md の Step 3a で呼び出し
MODEL_INFO=$(bash hooks/lm-studio-ensure.sh)

case "$MODEL_INFO" in
  READY:*)
    MODEL_ID="${MODEL_INFO#READY:}"
    # → LLM 検証モードへ
    ;;
  UNAVAILABLE:*)
    REASON="${MODEL_INFO#UNAVAILABLE:}"
    echo "⚠ LM Studio: ${REASON}。grep-only モードで実行"
    # → grep-only fallback
    ;;
esac
```

**スクリプトの処理フロー:**
1. `lms` CLI の存在確認
2. `lms server status` でサーバー確認 → 未起動なら `lms server start`
3. `lms ps` でモデル確認 → 未ロードなら `lms load qwen/qwen3-coder-next --gpu max -y`
4. API (`/api/v0/models`) でモデル ID を取得
5. `READY:<model_id>` または `UNAVAILABLE:<reason>` を出力

**UNAVAILABLE reasons:**
- `lms_cli_not_found` — LM Studio CLI 未インストール
- `server_start_timeout` — サーバー起動タイムアウト (15s)
- `model_load_timeout` — モデルロードタイムアウト (120s)

### Single Match Verification

```bash
curl -s http://localhost:1234/api/v0/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "'"$MODEL_ID"'",
    "messages": [
      {"role": "system", "content": "'"$SYSTEM_PROMPT"'"},
      {"role": "user", "content": "'"$USER_PROMPT"'"}
    ],
    "temperature": 0.1,
    "max_tokens": 256,
    "stream": false,
    "response_format": {
      "type": "json_schema",
      "json_schema": {
        "name": "verification",
        "schema": {
          "type": "object",
          "properties": {
            "is_anomaly": {"type": "boolean"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "category": {"type": "string", "enum": ["TRUE_POSITIVE", "FALSE_POSITIVE", "UNCERTAIN"]},
            "reasoning": {"type": "string"}
          },
          "required": ["is_anomaly", "confidence", "category", "reasoning"]
        }
      }
    }
  }'
```

### Response Parsing

```bash
# /api/v0/ のレスポンスから抽出
CONTENT=$(echo "$RESPONSE" | jq -r '.choices[0].message.content')
IS_ANOMALY=$(echo "$CONTENT" | jq -r '.is_anomaly')
CONFIDENCE=$(echo "$CONTENT" | jq -r '.confidence')
CATEGORY=$(echo "$CONTENT" | jq -r '.category')

# 推論統計 (v0 API 限定)
TOKENS_PER_SEC=$(echo "$RESPONSE" | jq -r '.stats.tokens_per_second')
TTFT=$(echo "$RESPONSE" | jq -r '.stats.time_to_first_token')
```

## Batch Processing Strategy

### Priority Sort

全 grep マッチを QAP 影響度でソートし、上位 N 件のみ LLM 検証する。

```
Priority = QAP_weight × severity_multiplier

severity_multiplier:
  CRITICAL candidate (QAP < 0.50):  3.0
  WARNING candidate  (0.50-0.80):   1.5
  INFO candidate     (>= 0.80):     0.5
```

### Batch Limits

| Match Count | LLM Verified | Remaining |
|-------------|-------------|-----------|
| 0-50 | 全件 | — |
| 51-100 | 上位 50 | confidence=0.5 |
| 101-300 | 上位 100 | confidence=0.5 |
| 300+ | 上位 100 | confidence=0.5 |

### Sequential Execution (NOT parallel)

LM Studio はシングルモデル推論のため、並列リクエストは待機列に入る。
順次実行の方が TTFT が安定し、全体のスループットも変わらない。

```
for match in sorted_matches[:BATCH_LIMIT]:
    prompt = build_prompt(match.category, match)
    result = call_lm_studio(prompt)
    match.confidence = result.confidence
    match.verified = True
```

## Confidence Integration

### Damped Multiplication (緩和乗算)

```
adjusted_QAP = raw_QAP × (0.5 + 0.5 × avg_confidence)
```

| avg_confidence | Effect on QAP |
|---------------|--------------|
| 1.0 | 100% (変化なし) |
| 0.8 | 90% |
| 0.5 | 75% |
| 0.3 | 65% |
| 0.0 | 50% (完全否定でも半分は保持) |

### Aggregation per QAP Parameter

```
For each QAP parameter (e.g., EHD):
  matches = all grep matches contributing to this parameter
  verified = matches where .verified == true

  if len(verified) > 0:
    avg_confidence = mean([m.confidence for m in verified if m.is_anomaly])
    adjusted = raw_value × (0.5 + 0.5 × avg_confidence)
  else:
    adjusted = raw_value  # no verification data → use raw
```

### Unverified Matches

LLM 検証されなかったマッチ (バッチ上限超過) には `confidence=0.5` を付与。
これにより `(0.5 + 0.5 × 0.5) = 0.75` — QAP の 75% が保持される。

## Fallback Behavior

| Condition | Behavior | User Message |
|-----------|----------|-------------|
| `--grep-only` flag | grep-only mode | `ℹ grep-only モード (LLM 検証スキップ)` |
| `UNAVAILABLE:lms_cli_not_found` | grep-only mode | `⚠ LM Studio CLI 未検出。grep-only モードで実行` |
| `UNAVAILABLE:server_start_timeout` | grep-only mode | `⚠ LM Studio サーバー起動失敗。grep-only モードで実行` |
| `UNAVAILABLE:model_load_timeout` | grep-only mode | `⚠ モデルロードタイムアウト。grep-only モードで実行` |
| LLM 途中クラッシュ | 処理済み保持 + 残りは confidence=0.5 | `⚠ LLM 検証が中断。N/M 件検証済み` |
| JSON パース失敗 | 1回リトライ → 失敗で confidence=0.5 | (サイレント) |
| タイムアウト (10s/match) | skip → confidence=0.5 | (サイレント) |

## Report Format Extension

v3.0 のレポートには confidence カラムが追加される:

```markdown
### CRITICAL (N件)
| # | Cat | Layer | QAP | Conf | Location | Symptom | Root Cause |
|---|-----|-------|-----|------|----------|---------|------------|
| 1 | Ghost | L2 | EHD=0.3 | 0.92 | file:42 | empty catch | silent failure |
```

- **Conf** カラム: LLM 検証の信頼度 (0.0-1.0)
- `—` 表示: LLM 未検証 (grep-only mode or batch limit exceeded)

## Performance Expectations (M3 Ultra)

| Metric | Expected | Notes |
|--------|----------|-------|
| Health check | < 100ms | localhost roundtrip |
| Per-match inference | 200-500ms | Qwen3-Coder-Next 3B active, 256 max_tokens |
| 50 matches total | 10-25s | Sequential execution |
| 100 matches total | 20-50s | Batch limit default |
| Tokens/sec | 40-60 tok/s | MLX 8bit on 80-core GPU |

## Prompt Files

| Category | Prompt File | Layers |
|----------|------------|--------|
| Ghost | `references/prompts/ghost-verify.md` | L1-L4 |
| Fragile | `references/prompts/fragile-verify.md` | L5-L8 |
| Blind Spot | `references/prompts/blindspot-verify.md` | L9 |
