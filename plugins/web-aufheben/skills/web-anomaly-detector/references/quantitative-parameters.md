# Quantitative Anomaly Parameters (QAP)

違和感を**数値**で立証する。主観的な「何かおかしい」を、
grep/glob で計測可能なパラメーターに変換し、閾値で判定する。

## 計測タイプ

| Type | Formula | Healthy | Anomalous |
|------|---------|---------|-----------|
| Ratio | matching / total | -> 1.0 | -> 0.0 |
| Presence | count of anti-patterns | 0 | > 0 |
| Symmetry | \|open - close\| / max(open, 1) | 0.0 | -> 1.0 |
| Scatter | definition_locations / unique_keys | 1.0 | > 1.5 |

---

## Ghost Parameters (L1-L4: 動かないもの)

### G1: Contract Fulfillment Rate (CFR)
型定義と API 実装の一致率。
- **Type**: Ratio
- **Formula**: `types_with_matching_api / total_defined_types`
- **Measurement**:
  ```bash
  # Step 1: 型定義を列挙
  Grep "export (interface|type) " path="types/" glob="*.ts"
  Grep "export (interface|type) " path="shared/" glob="*.ts"
  # Step 2: 対応する API レスポンスの return 型を確認
  Grep "return " path="api/" glob="*.ts"
  # Step 3: 突合 — 型名が API で参照されていないものを検出
  ```
- **Threshold**: >= 0.9 Normal / 0.7-0.9 WARNING / < 0.7 CRITICAL
- **Evidence**: 契約不一致は OWASP API Security #8 に対応。L1 実例: `nomic-embed-text` vs `nomic-embed-text:latest`

### G2: Error Handling Density (EHD)
catch ブロック内の適切なエラー処理率。
- **Type**: Ratio
- **Formula**: `catch_with_log_or_throw / total_catch_blocks`
- **Measurement**:
  ```bash
  # Total catch blocks
  Grep "catch\s*[({]" glob="*.ts,*.js" output_mode="count"
  # Catch with proper handling (log/throw/report within 3 lines)
  Grep "catch" -A 3 glob="*.ts,*.js" output_mode="content"
  # -> 後続3行に console.error / logger / throw / report がない = silent failure
  ```
- **Threshold**: >= 0.8 Normal / 0.5-0.8 WARNING / < 0.5 CRITICAL
- **Evidence**: Google SRE 報告: サイレント失敗は本番障害の28%を占める

### G3: Event Subscription Ratio (ESR)
定義されたイベントの購読率。
- **Type**: Ratio
- **Formula**: `subscribed_events / defined_events`
- **Measurement**:
  ```bash
  # Server-side emits (framework-agnostic)
  Grep "emit\(|broadcast\(|publish\(|\.send\(" path="server/" glob="*.ts,*.js"
  # Client-side subscriptions
  Grep "\.on\(|subscribe\(|addEventListener|useSubscription" glob="*.ts,*.js,*.vue,*.jsx,*.tsx,*.svelte"
  # -> emit されるがどこからも listen されていないイベント = dead path
  ```
- **Threshold**: >= 0.9 Normal / 0.7-0.9 WARNING / < 0.7 CRITICAL
- **Evidence**: 未購読イベント = データ更新の欠落 + デッドコードパス

### G4: Handler Liveness Rate (HLR)
UI イベントハンドラの実装率。
- **Type**: Ratio
- **Formula**: `non_empty_handlers / total_event_handlers`
- **Measurement**:
  ```bash
  # Event handlers (multi-framework)
  Grep "onClick|@click|on:click|\(click\)=" glob="*.vue,*.jsx,*.tsx,*.svelte,*.html"
  # Empty/TODO handlers in same files
  Grep "TODO|FIXME|noop|// implement|\{\s*\}" glob="*.ts,*.js,*.vue,*.jsx"
  # -> ハンドラ定義があるが中身が空/TODO = dead feature
  ```
- **Threshold**: >= 0.95 Normal / 0.8-0.95 WARNING / < 0.8 CRITICAL

### G5: Route Reachability Rate (RRR)
定義されたルートへのリンク存在率。
- **Type**: Ratio
- **Formula**: `linked_routes / total_defined_routes`
- **Measurement**:
  ```bash
  # Defined routes (detect framework automatically)
  Glob "pages/**/*.vue"             # Nuxt
  Glob "app/**/page.tsx"            # Next.js
  Glob "src/routes/**/*.svelte"     # SvelteKit
  Grep "path:\s*['\"]/" glob="router*.ts,routes*.ts"  # Manual routing
  # Links pointing to routes
  Grep "href=|to=|navigate|router\.push|Link " glob="*.vue,*.jsx,*.tsx,*.svelte"
  # -> 定義はあるがどこからもリンクされていない = orphan route
  ```
- **Threshold**: >= 0.9 Normal / 0.7-0.9 WARNING / < 0.7 CRITICAL

### G6: Action-Response Rate (ARR)
ユーザー操作に対する UI 応答率。Action→Feedback 断絶を検出。
- **Type**: Ratio
- **Formula**: `actions_with_visible_response / total_interactive_actions`
- **Sub-components**:
  ```
  0.40 × revalidation_rate   (mutation 後のデータ再取得率)
  0.30 × feedback_rate       (loading/success/error 表示率)
  0.30 × rollback_rate       (optimistic update の復旧率、該当なしなら N/A → 再配分)
  ```
- **Measurement**:
  ```bash
  # Action handlers (multi-framework)
  Grep "onClick|@click|on:click|\(click\)|onSubmit|@submit" glob="*.vue,*.jsx,*.tsx,*.svelte"
  # State change in same component
  Grep "setState|set[A-Z]|\.value\s*=|store\.\w+|commit\(|\$patch" glob="*.ts,*.js,*.vue,*.jsx,*.tsx"
  # Loading/feedback UI
  Grep "isLoading|isPending|isFetching|pending\.value|disabled" glob="*.ts,*.js,*.vue,*.jsx,*.tsx"
  # Mutation vs revalidation
  Grep "method:\s*['\"]POST|method:\s*['\"]PUT|method:\s*['\"]DELETE" glob="*.ts,*.js,*.vue,*.jsx,*.tsx"
  Grep "invalidateQueries|refreshNuxtData|revalidatePath|mutate\(" glob="*.ts,*.js,*.vue,*.jsx,*.tsx"
  ```
- **Threshold**: >= 0.85 Normal / 0.60-0.85 WARNING / < 0.60 CRITICAL
- **Evidence**: ユーザー体験の直接的指標。操作後の無反応はユーザー離脱の主因
- **Detection detail**: `references/detection-patterns.md` L10

### G7: Perceived Performance Rate (PPR)
知覚パフォーマンスの品質。「遅く感じる」UIパターンの検出。
- **Type**: Ratio (composite)
- **Formula**: `weighted average of 6 sub-components`
- **Sub-components**:
  ```
  0.25 × skeleton_ratio      (P10.13: skeleton数 / (skeleton数 + spinner数))
  0.20 × optimistic_ratio    (P10.14: optimistic mutation / total write mutations)
  0.20 × reactivity_ratio    (P10.17: shallowRef / total array-type ref)
  0.15 × cleanup_ratio       (P10.20: cleanup / realtime connections)
  0.10 × lazy_ratio           (P10.21: lazy components / total heavy components)
  0.10 × animation_quality   (P10.15+P10.18: transitions in optimal range)
  ```
- **Measurement**:
  ```bash
  # P10.13: Skeleton vs Spinner
  Grep "skeleton|Skeleton|animate-pulse|shimmer" glob="*.vue,*.jsx,*.tsx" output_mode="count"
  Grep "spinner|Spinner|animate-spin|fa-spinner" glob="*.vue,*.jsx,*.tsx" output_mode="count"

  # P10.17: shallowRef vs ref (array/collection types)
  Grep "shallowRef|shallowReactive" glob="*.ts,*.vue" output_mode="count"
  Grep "ref\s*<\s*\w+\[\]|ref\s*\(\s*\[\s*\]\s*\)" glob="*.ts,*.vue" output_mode="count"

  # P10.20: Realtime cleanup
  Grep "EventSource|useEventSource|WebSocket|useWebSocket" glob="*.ts,*.vue" output_mode="count"
  Grep "onScopeDispose|onUnmounted|tryOnScopeDispose" glob="*.ts,*.vue" output_mode="count"
  ```
- **Threshold**: >= 0.70 Normal / 0.40-0.70 WARNING / < 0.40 CRITICAL
- **Evidence**: 科学的根拠多数。Skeleton Screen 20-30%速く知覚 (UI Deploy 2025)、
  Doherty閾値 400ms (IBM 1982)、INP <200ms (web.dev)、60FPS未満でリテンション27%低下 (NNGroup 2024)
- **Detection detail**: `references/perceived-performance.md`

---

## Fragile Parameters (L5-L8: 壊れやすいもの)

### F1: Naming Consistency Index (NCI)
命名規則の一貫性。同一スコープ内での規則混在を検出。
- **Type**: Ratio
- **Formula**: `dominant_convention_count / total_measured_identifiers`
- **Measurement**:
  ```bash
  # snake_case identifiers in types
  Grep "[a-z]+_[a-z]+" path="types/" glob="*.ts"
  Grep "[a-z]+_[a-z]+" path="shared/" glob="*.ts"
  # camelCase identifiers in same scope
  Grep "[a-z]+[A-Z][a-z]+" path="types/" glob="*.ts"
  # -> 同一スコープに両方存在 = 命名不一致
  # -> 多数派の比率を NCI とする
  ```
- **Threshold**: >= 0.9 Normal / 0.75-0.9 WARNING / < 0.75 CRITICAL
- **Evidence**: 命名不一致は CBO (結合度) 上昇と相関。CK metrics 研究: CBO > 7 で障害率増加

### F2: Configuration Scatter Score (CSS)
同一設定値の散在度。
- **Type**: Scatter
- **Formula**: `total_definition_locations / unique_config_keys`
- **Measurement**:
  ```bash
  # Environment variable usage across codebase
  Grep "process\.env\.|import\.meta\.env\.|Deno\.env" glob="*.ts,*.js"
  # Config file definitions
  Grep "VARIABLE_NAME" glob=".env*,*.config.ts,*.config.js,docker-compose.yml"
  # Hardcoded values (same string in multiple places)
  Grep "'http://localhost|\"http://localhost" glob="*.ts,*.js"
  # -> 同じ設定値が .env + config + hardcode に散在 = scatter
  ```
- **Threshold**: 1.0 Normal / 1.5-2.0 WARNING / > 2.0 CRITICAL

### F3: Timeout Coverage Rate (TCR)
外部呼び出しのタイムアウト設定率。
- **Type**: Ratio
- **Formula**: `calls_with_timeout / total_external_calls`
- **Measurement**:
  ```bash
  # External HTTP calls (framework-agnostic)
  Grep "fetch\(|axios\.|ofetch\(|\$fetch\(|got\(|ky\." path="server/" glob="*.ts,*.js"
  # Timeout/abort configuration
  Grep "timeout|AbortController|AbortSignal\.timeout|signal:" path="server/" glob="*.ts,*.js"
  # -> 外部呼び出し数 vs timeout 設定数の比率
  ```
- **Threshold**: >= 0.9 Normal / 0.5-0.9 WARNING / < 0.5 CRITICAL
- **Evidence**: Reliability Pattern R1 (CRITICAL)。タイムアウト未設定 = 無限待機 = cascading failure

### F4: Auth Guard Coverage (AGC)
API エンドポイントの認証保護率。
- **Type**: Ratio
- **Formula**: `auth_protected_endpoints / total_api_endpoints`
- **Measurement**:
  ```bash
  # Total API endpoints
  Glob "server/api/**/*.ts"           # Nitro/Nuxt
  Glob "app/api/**/*.ts"              # Next.js
  Glob "src/routes/api/**/*.ts"       # SvelteKit
  # Auth middleware/guard
  Grep "auth|session|requireAuth|protect|middleware|guard|jwt|token" path="server/api/" glob="*.ts"
  # -> public endpoints を除外した後の保護率
  ```
- **Threshold**: >= 0.95 Normal / 0.8-0.95 WARNING / < 0.8 CRITICAL
- **Evidence**: OWASP 2025 A01 (Broken Access Control) + API Security Top 10 #1 (BOLA)

### F5: Secret Exposure Count (SEC)
ハードコードされたシークレットの数。
- **Type**: Presence
- **Formula**: `count of detected hardcoded secrets`
- **Measurement**:
  ```bash
  # AWS Access Key
  Grep "AKIA[0-9A-Z]{16}" glob="*.ts,*.js,*.env,*.json"
  # OpenAI / Stripe secret key
  Grep "sk-[a-zA-Z0-9]{20,}" glob="*.ts,*.js"
  # GitHub personal access token
  Grep "ghp_[a-zA-Z0-9]{36}" glob="*.ts,*.js"
  # Slack bot token
  Grep "xoxb-[0-9]+" glob="*.ts,*.js"
  # Generic password assignment
  Grep "password\s*[:=]\s*['\"][^'\"]{4,}['\"]" glob="*.ts,*.js,*.py"
  # Private key
  Grep "-----BEGIN (RSA |EC )?PRIVATE KEY" glob="*.ts,*.js,*.pem,*.key"
  ```
- **Threshold**: 0 Normal / > 0 CRITICAL (例外なし)
- **Evidence**: OWASP 2025 A02 (Cryptographic Failures) + API Security #9

### F6: Resilience Pair Coverage (RPC)
外部サービス呼び出しのリトライ/サーキットブレーカー実装率。
- **Type**: Ratio
- **Formula**: `(calls_with_retry_or_cb) / total_external_service_calls`
- **Measurement**:
  ```bash
  # External service calls
  Grep "fetch\(.*https?://|ofetch\(.*https?://" path="server/" glob="*.ts"
  # Retry logic
  Grep "retry|retries|maxRetries|retryDelay" glob="*.ts,*.js"
  # Backoff (must accompany retry)
  Grep "backoff|exponential|jitter" glob="*.ts,*.js"
  # Circuit breaker
  Grep "circuitBreaker|opossum|cockatiel|brakes" glob="*.ts,*.js,package.json"
  ```
- **Threshold**: >= 0.5 Normal / 0.2-0.5 WARNING / < 0.2 CRITICAL
- **Evidence**: Reliability Pattern R2 (Retry Storm) + R3 (Circuit Breaker)

### F7: Memory Leak Symmetry (MLS)
リソース確保/解放の対称性。
- **Type**: Symmetry
- **Formula**: `|acquire_count - release_count| / max(acquire_count, 1)`
- **Measurement**:
  ```bash
  # === Pair 1: Event Listeners ===
  Grep "addEventListener\(" glob="*.ts,*.js,*.vue,*.jsx,*.tsx" output_mode="count"
  Grep "removeEventListener\(" glob="*.ts,*.js,*.vue,*.jsx,*.tsx" output_mode="count"

  # === Pair 2: Intervals ===
  Grep "setInterval\(" glob="*.ts,*.js,*.vue,*.jsx,*.tsx" output_mode="count"
  Grep "clearInterval\(" glob="*.ts,*.js,*.vue,*.jsx,*.tsx" output_mode="count"

  # === Pair 3: Connections ===
  Grep "\.connect\(\)" path="server/" glob="*.ts" output_mode="count"
  Grep "\.close\(\)|\.release\(\)|\.disconnect\(\)|\.end\(\)" path="server/" glob="*.ts" output_mode="count"

  # === Pair 4: Streams ===
  Grep "createReadStream|createWriteStream" path="server/" glob="*.ts" output_mode="count"
  Grep "\.destroy\(\)|\.close\(\)|\.end\(\)" path="server/" glob="*.ts" output_mode="count"

  # -> 各ペアの非対称度を計算し、最悪値を MLS とする
  ```
- **Threshold**: 0.0-0.1 Normal / 0.1-0.3 WARNING / > 0.3 CRITICAL
- **Evidence**: Reliability Pattern R6。非対称 = メモリリーク/接続枯渇の兆候

### F8: Graceful Shutdown Score (GSS)
プロセスのシグナルハンドリング実装。
- **Type**: Presence (binary 0 or 1)
- **Formula**: `has_SIGTERM_handler AND has_drain_logic`
- **Measurement**:
  ```bash
  # Signal handling
  Grep "SIGTERM|SIGINT|beforeExit|graceful" glob="*.ts,*.js"
  # Drain logic (wait for in-flight requests)
  Grep "server\.close|app\.close|drain|keepAliveTimeout|closeAllConnections" glob="*.ts,*.js"
  # -> 両方あれば 1.0、signal のみ 0.5、なし 0.0
  ```
- **Threshold**: 1.0 Normal / 0.5 WARNING / 0.0 CRITICAL (本番サービスの場合)
- **Evidence**: Reliability Pattern R9。欠如 = デプロイ時のリクエスト断

---

## Blind Spot Parameters (L9: 見えないリスク)

### B1: TODO Staleness Index (TSI)
放置された TODO/FIXME の古さ。
- **Type**: Ratio (age-based)
- **Formula**: `todo_older_than_90d / total_todos`
- **Measurement**:
  ```bash
  # All TODOs
  Grep "TODO|FIXME|HACK|XXX" glob="*.ts,*.js,*.vue,*.jsx,*.tsx,*.py"
  # -> 各行を git blame で最終更新日を取得
  # -> 90日以上前 = stale
  ```
- **Threshold**: < 0.2 Normal / 0.2-0.5 WARNING / > 0.5 CRITICAL
- **Note**: git blame 必要 (grep 単体では日付不明)

### B2: Implicit Type Coercion Risk (ITCR)
暗黙的型変換リスクのある演算の数。
- **Type**: Presence
- **Formula**: `count of loose equality (== / !=) usages`
- **Measurement**:
  ```bash
  # Loose equality (non-strict)
  Grep "[^!=!]==[^=]" glob="*.ts,*.js"   # == but not === or !==
  Grep "[^!]!=[^=]" glob="*.ts,*.js"     # != but not !==
  # Dangerous concatenation
  Grep '"\s*\+\s*[a-z]|[a-z]\s*\+\s*"' glob="*.ts,*.js"  # string + variable
  ```
- **Threshold**: 0 Normal / 1-10 WARNING / > 10 CRITICAL
- **Note**: TypeScript strict mode で大部分は防げるが、`.js` ファイルや `any` 型に潜む

### B3: Boundary Validation Gap (BVG)
入力バリデーションの欠落率。
- **Type**: Ratio
- **Formula**: `validated_input_endpoints / total_input_endpoints`
- **Measurement**:
  ```bash
  # Endpoints accepting user input (framework-agnostic)
  Grep "getQuery\(|readBody\(|req\.body|req\.query|req\.params|request\.json\(\)" path="server/" glob="*.ts,*.js,*.py"
  # Validation library usage
  Grep "zod|joi|yup|validate|schema|z\.\w+|class-validator|pydantic" path="server/" glob="*.ts,*.js,*.py"
  # -> input を受け取るエンドポイントのうち、validation がないもの = gap
  ```
- **Threshold**: >= 0.9 Normal / 0.6-0.9 WARNING / < 0.6 CRITICAL
- **Evidence**: OWASP 2025 A03 (Injection)。バリデーションは第一防御線

### B4: Dependency Freshness Score (DFS)
依存パッケージの管理品質。
- **Type**: Ratio (multi-factor)
- **Formula**: `(has_lockfile × 0.4) + (pinned_ratio × 0.3) + (no_dangerous_scripts × 0.3)`
- **Measurement**:
  ```bash
  # Lockfile presence (基本条件)
  Glob "pnpm-lock.yaml" OR Glob "package-lock.json" OR Glob "yarn.lock"
  # Unpinned versions (^ or ~ prefix)
  Grep '"\\^|"~' glob="package.json"
  # Dangerous postinstall scripts
  Grep '"postinstall"|"preinstall"' glob="node_modules/*/package.json" head_limit=20
  ```
- **Threshold**: >= 0.8 Normal / 0.5-0.8 WARNING / < 0.5 CRITICAL
- **Evidence**: OWASP 2025 A03 (Software Supply Chain) + Security Pattern S6

---

## Composite Scores

### Ghost Score (動作確実性)
```
Ghost = 0.20 × CFR
      + 0.20 × EHD
      + 0.10 × ESR
      + 0.15 × ARR
      + 0.15 × PPR      ← NEW: 知覚パフォーマンス
      + 0.10 × HLR
      + 0.10 × RRR
```
**v3.3 変更**: reserve枠 (0.05) をPPR新設に統合。CFR/EHD を 0.25→0.20 に再配分。
PPR が N/A の場合は残存パラメーターに比例再配分 (旧計算式と同等)。

### Fragile Score (耐障害性)
```
Fragile = 0.15 × NCI
        + 0.10 × (1/max(CSS, 1.0))  # scatter の逆数 (1.0 が最良, CSS=0 ガード)
        + 0.20 × TCR
        + 0.20 × AGC
        + 0.10 × (1-SEC_norm)  # SEC_norm = min(1, SEC/3)
        + 0.10 × RPC
        + 0.10 × (1-MLS)      # symmetry の逆 (0.0 が最良)
        + 0.05 × GSS
```

### Blind Spot Score (潜在リスク)
```
BlindSpot = 0.25 × (1-TSI)        # staleness の逆
          + 0.20 × ITCR_norm      # ITCR_norm = max(0, 1 - ITCR/20)
          + 0.30 × BVG            # 20 = 中規模プロジェクト (~50ファイル) での経験的上限。
          + 0.25 × DFS            # 大規模プロジェクトでは適応的閾値で調整。
```

### Overall Anomaly Score (OAS)
```
OAS = 0.40 × Ghost + 0.35 × Fragile + 0.25 × BlindSpot
```
Ghost が最重 (0.40) — 動作しないコードが最も致命的。

| Score Range | Status | Action |
|-------------|--------|--------|
| >= 0.80 | Healthy | 軽微な改善のみ |
| 0.50-0.80 | Warning | 計画的に対処 |
| < 0.50 | Critical | 即座に対処 |

---

## 適応的閾値

| Context | Healthy | Warning | Critical |
|---------|---------|---------|----------|
| MVP/Prototype | >= 0.65 | 0.35-0.65 | < 0.35 |
| Production | >= 0.80 | 0.50-0.80 | < 0.50 |
| Financial/Medical | >= 0.85 | 0.55-0.85 | < 0.55 |

アーキテクチャ調整: Microservices → TCR/RPC/GSS 厳格化, SSG → L3/L8 スキップ

### 適用例
```
Production Microservices: TCR >= 0.95, RPC >= 0.6, GSS 必須 (厳格化)
MVP/Prototype: AGC >= 0.76, EHD >= 0.64 (緩和)
```

---

## LLM Confidence Integration (v3.0)

grep/glob 計測の raw QAP に、LM Studio (Qwen3-Coder-Next) の検証結果を統合する。

### Damped Multiplication Formula

```
adjusted_QAP = raw_QAP × (0.5 + 0.5 × avg_confidence)
```

| avg_confidence | Multiplier | QAP Effect |
|---------------|-----------|------------|
| 1.0 | 1.00 | 変化なし (全件が真の異常) |
| 0.8 | 0.90 | 10% 緩和 |
| 0.5 | 0.75 | 25% 緩和 (未検証デフォルト) |
| 0.3 | 0.65 | 35% 緩和 |
| 0.0 | 0.50 | 50% に低下 (完全否定でも半分保持) |

**設計意図**: 完全乗算 (`raw × confidence`) は confidence=0.3 で QAP が 70% 減少し過剰補正になる。
緩和乗算は最低でも 50% を保持し、grep 検出の価値を完全に否定しない。

### Per-Parameter Aggregation

```
For QAP parameter P (e.g., EHD):
  matches_P = grep matches contributing to P
  verified_P = matches where LLM verification was performed

  if |verified_P| > 0:
    anomaly_confs = [m.confidence for m in verified_P where m.is_anomaly == true]
    if |anomaly_confs| > 0:
      avg_confidence_P = mean(anomaly_confs)
    else:
      avg_confidence_P = 0.0  # all verified as FALSE_POSITIVE
    adjusted_P = raw_P × (0.5 + 0.5 × avg_confidence_P)
  else:
    adjusted_P = raw_P  # no LLM data → use raw
```

### Unverified Match Default

バッチ上限超過で LLM 検証されなかったマッチ: `confidence = 0.5`
→ `(0.5 + 0.5 × 0.5) = 0.75` → QAP の 75% が保持される。

### N/A Weight Redistribution

分母が 0 (計測不能) の QAP パラメーターは、スコア算出から除外し、
その重みを同一カテゴリ内の残存パラメーターへ **比例配分** する。

```
For category C with parameters [P1, P2, ..., Pn] and weights [w1, w2, ..., wn]:

  measurable = {Pi | denominator(Pi) > 0}
  skipped    = {Pi | denominator(Pi) == 0}

  if |measurable| == 0:
    C_score = N/A  # カテゴリ全体が計測不能 → レポートに "N/A" と明記

  else:
    total_skipped_weight = sum(wi for Pi in skipped)
    redistribution_factor = 1 / (1 - total_skipped_weight)

    C_score = sum(wi × redistribution_factor × value(Pi) for Pi in measurable)
```

**例: Ghost Score で ESR (w=0.10), reserve (w=0.05) が N/A の場合**
```
残存: CFR(0.25), EHD(0.25), ARR(0.15), HLR(0.10), RRR(0.10)  →  合計 0.85
redistribution_factor = 1 / (1 - 0.15) = 1.176
Ghost = 0.294×CFR + 0.294×EHD + 0.176×ARR + 0.118×HLR + 0.118×RRR  →  合計 1.000 ✓
```

**レポート表記**: N/A パラメーターは `—` 表示し、注釈に理由を記載。

### Adjusted Composite Scores

Composite Score 算出時は `adjusted_QAP` を使用。`--grep-only` 時は `adjusted = raw`。

### Model Specification

詳細: `references/llm-verify.md` (Qwen3-Coder-Next, LM Studio API, temperature 0.1, json_schema)

---

## Research Backing

| Source | Contribution |
|--------|-------------|
| CK Metrics (1994) | CBO/WMC/RFC 閾値基準 |
| Shannon Entropy (2025) | 情報理論ベース異常検出 60%+ precision |
| OWASP Top 10 (2025) | セキュリティ閾値根拠 |
| Google SRE (2024) | 信頼性パターンの重大度根拠 |

適応的閾値が固定閾値より効果的。文脈に応じた調整が検出精度を最大化する。
