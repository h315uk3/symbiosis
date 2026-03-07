# Ghost Verification Prompt (L1-L4)

LM Studio Qwen3-Coder-Next 用。grep マッチが真の Ghost 異常かを判定する。

## System Prompt

```
You are a code anomaly verifier. Given a grep match and its surrounding context, determine if this is a TRUE anomaly (Ghost category: code that doesn't actually work) or a FALSE POSITIVE.

Ghost anomalies include:
- L1: Contract mismatch (type definition vs actual API response differs)
- L2: Silent failure (catch block swallows errors without logging/throwing)
- L3: State sync bug (event emitted but never subscribed, or vice versa)
- L4: Dead feature (handler/route defined but empty or unreachable)
- L10: UI Responsiveness (action handler without visible feedback, mutation without revalidation, async operation without loading/error UI)

Respond in the required JSON format. Be strict: only mark as true_positive if the code genuinely fails silently, has dead paths, breaks contracts, or leaves users without feedback after actions.
```

## User Prompt Template

```
## Grep Match
- **File**: {file_path}
- **Line**: {line_number}
- **Pattern**: {pattern_id} ({pattern_description})
- **QAP Parameter**: {qap_param}

## Matched Line
```
{matched_line}
```

## Context (±10 lines)
```
{context}
```

## Question
Is this a genuine Ghost anomaly (code that doesn't work / silently fails / is unreachable)?
Consider: Is the catch block actually handling the error properly? Is the handler truly empty or does it delegate? Is the event subscribed elsewhere in the codebase?
```

## Response Schema (json_schema)

```json
{
  "name": "ghost_verification",
  "schema": {
    "type": "object",
    "properties": {
      "is_anomaly": {
        "type": "boolean",
        "description": "true if this is a genuine anomaly, false if false positive"
      },
      "confidence": {
        "type": "number",
        "minimum": 0.0,
        "maximum": 1.0,
        "description": "Confidence in the judgment (0.0=uncertain, 1.0=certain)"
      },
      "category": {
        "type": "string",
        "enum": ["TRUE_POSITIVE", "FALSE_POSITIVE", "UNCERTAIN"]
      },
      "reasoning": {
        "type": "string",
        "description": "One-sentence explanation (max 50 words)"
      }
    },
    "required": ["is_anomaly", "confidence", "category", "reasoning"]
  }
}
```

## LM Studio API Call

```bash
curl -s http://localhost:1234/api/v0/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "{model_id}",
    "messages": [
      {"role": "system", "content": "{system_prompt}"},
      {"role": "user", "content": "{user_prompt}"}
    ],
    "temperature": 0.1,
    "max_tokens": 256,
    "response_format": {
      "type": "json_schema",
      "json_schema": {ghost_verification_schema}
    }
  }'
```

## False Positive Indicators (Ghost)

判定時に考慮すべき偽陽性パターン:

| Pattern | Why False Positive |
|---------|-------------------|
| `catch(e) { logger.error(e); throw e; }` | re-throw しているので silent failure ではない |
| `catch(e) { errorHandler.report(e) }` | 外部エラーハンドラに委譲 |
| `// @ts-expect-error` + 次行 valid code | 意図的な型抑制 |
| テストファイル内の空ハンドラ | テスト用のスタブ |
| `_placeholder` / `noop` in storybook | UI カタログ用 |
| Framework の auto-generated handler | Nuxt/Next のデフォルト |
| Global error handler で一括処理 | toast/snackbar が別コンポーネントにある |
| Navigation 自体がフィードバック | ページ遷移で結果を表示 |
| Debounce/throttle による意図的遅延 | 連打防止の設計 |
| Framework の自動 revalidation | Next.js revalidatePath や SWR の自動 refetch |
