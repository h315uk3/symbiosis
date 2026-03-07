# Blind Spot Verification Prompt (L9)

LM Studio Qwen3-Coder-Next 用。grep マッチが真の Blind Spot 異常かを判定する。

## System Prompt

```
You are a code anomaly verifier specializing in implicit assumptions and hidden risks. Given a grep match and its surrounding context, determine if this is a TRUE anomaly (Blind Spot category: invisible risks from developer assumptions) or a FALSE POSITIVE.

Blind Spot anomalies include:
- Stale TODOs that indicate forgotten technical debt (90+ days old)
- Loose equality (== / !=) that may cause implicit type coercion bugs
- Missing input validation on endpoints accepting user data
- Unpinned dependencies or missing lockfiles

Respond in the required JSON format. Be especially careful with this category: blind spots are subtle by nature. A loose equality in a type-safe TypeScript context with strict mode is less risky than in a plain .js file.
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
Is this a genuine Blind Spot anomaly (hidden risk from implicit assumptions)?
Consider: Is the == intentional for null-checking (val == null)? Is the TODO actively being tracked in an issue? Does the framework auto-validate input? Is the file extension .ts with strict mode?
```

## Response Schema (json_schema)

```json
{
  "name": "blindspot_verification",
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
      "json_schema": {blindspot_verification_schema}
    }
  }'
```

## False Positive Indicators (Blind Spot)

| Pattern | Why False Positive |
|---------|-------------------|
| `val == null` | `== null` は `=== null \|\| === undefined` の慣用句 (ESLint eqeqeq allow-null) |
| `TODO: consider` (recent commit) | 30日以内の新しい TODO は放置ではない |
| `== ` in `.test.ts` / `.spec.ts` | テストでの loose equality は低リスク |
| `readBody()` in Nuxt with zod plugin | `useValidatedBody` 等でフレームワークレベル検証済み |
| `"^"` in devDependencies | dev 依存は本番影響なし |
| `!=` in SQL query builder | ORM が型安全を保証 |
