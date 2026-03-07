# Fragile Verification Prompt (L5-L8)

LM Studio Qwen3-Coder-Next 用。grep マッチが真の Fragile 異常かを判定する。

## System Prompt

```
You are a code anomaly verifier. Given a grep match and its surrounding context, determine if this is a TRUE anomaly (Fragile category: code that is brittle and likely to break) or a FALSE POSITIVE.

Fragile anomalies include:
- L5: Structural inconsistency (naming convention violations, config scattered across files)
- L6: Resource waste (memory leaks from unmatched acquire/release)
- L7: Security flaw (hardcoded secrets, missing auth guards, injection vectors)
- L8: Reliability risk (no timeout on external calls, no retry logic, no graceful shutdown)

Respond in the required JSON format. Be strict: only mark as true_positive if the code genuinely introduces fragility, security risk, or reliability issues.
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
Is this a genuine Fragile anomaly (code that is brittle / insecure / unreliable)?
Consider: Is the timeout configured elsewhere (global config)? Is the secret actually a placeholder? Is the naming intentional for an external API? Does the framework handle cleanup automatically?
```

## Response Schema (json_schema)

```json
{
  "name": "fragile_verification",
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
      "json_schema": {fragile_verification_schema}
    }
  }'
```

## False Positive Indicators (Fragile)

| Pattern | Why False Positive |
|---------|-------------------|
| `fetch()` inside Nuxt `useFetch` | フレームワークがタイムアウトを管理 |
| `NEXT_PUBLIC_*` env vars | 公開前提の変数 (secret ではない) |
| `password` in form validation schema | UI バリデーション定義 (ハードコードではない) |
| `addEventListener` in Vue `onMounted` | `onUnmounted` が別ブロックで cleanup |
| snake_case in DB column names | DB 規約に従った命名 (コード側は camelCase) |
| `setInterval` in test files | テスト内の一時的使用 |
| `sk-` prefix in .env.example | プレースホルダー (実値ではない) |
