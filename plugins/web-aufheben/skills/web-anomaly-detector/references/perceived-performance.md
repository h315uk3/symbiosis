# L10b: 知覚パフォーマンス違和感パターン (Perceived Performance Anomalies)

科学的研究に基づく「遅く感じる」「反応がない」「生きていない」UIの検出。
技術的パフォーマンスではなく **ユーザーの知覚** に焦点を当てる。

---

## 科学的根拠

### 人間の知覚閾値

| 閾値 | 知覚 | 出典 |
|------|------|------|
| 0-50ms | 因果の錯覚 (自分が引き起こした) | Springer: Latency Perception Thresholds (2017) |
| 50-100ms | 即座の反応 (ペン入力では50msで遅延知覚) | ResearchGate: Are 100ms Fast Enough? |
| 100-200ms | 速いが知覚可能。INP Good基準 | web.dev: Interaction to Next Paint |
| 200-400ms | Doherty閾値。超えるとフロー状態が崩壊 | IBM Systems Journal (1982), Laws of UX |

### 知覚トリック効果

| 手法 | 科学的効果 | 出典 |
|------|-----------|------|
| Skeleton Screen | スピナーより20-30%速く感じる | UI Deploy (2025) |
| Optimistic UI | API完了前にUI更新。知覚遅延ゼロ | Web Performance Calendar |
| 流動的トランジション | 待ち時間知覚を半減 (NNGroup) | Nielsen Norman Group |
| 60FPS維持 | 60FPS未満でリテンション27%低下 | NNGroup (2024) |
| 200-300ms遷移 | 「速いが知覚可能」最適レンジ | Material Design研究 |
| 0.1秒モバイル高速化 | コンバージョン最大8.4%向上 | Presta: Performance First UX 2026 |

### INP (Interaction to Next Paint) 3フェーズ

```
User Action ─→ [Input Delay] ─→ [Processing Time] ─→ [Presentation Delay] ─→ Visual Update
              ↑ JSメインスレッド  ↑ イベントハンドラ     ↑ レイアウト/描画
              占有による遅延      実行時間              DOM更新コスト
```

Good: <200ms / Needs Improvement: 200-500ms / Poor: >500ms (p75)

---

## 検出パターン

### 検出 Tier

| Tier | 意味 | パターン |
|------|------|---------|
| **A** | grep 単体で高精度 | P10.13, P10.14, P10.17, P10.18, P10.20 |
| **B** | grep + LLM 検証必須 | P10.15, P10.19, P10.21 |
| **C** | LLM 専用 (grep 不適格) | P10.16, P10.22 |

---

### P10.13: スピナー・アンチパターン `[Tier A]`

2026年においてスピナーは知覚パフォーマンスのアンチパターン。
Skeleton Screen は同一待機時間で20-30%速く知覚される。

```bash
# スピナー/ローディングインジケータの使用
Grep "spinner|Spinner|loading-spinner|LoadingSpinner|v-loading|isSpinning" glob="*.vue,*.jsx,*.tsx,*.svelte"
Grep "animate-spin|fa-spinner|loader.*circle|spin.*animation" glob="*.vue,*.jsx,*.tsx,*.css,*.scss"
Grep "<svg.*animate|CircularProgress|LinearProgress" glob="*.vue,*.jsx,*.tsx"

# Skeleton Screen の使用
Grep "skeleton|Skeleton|animate-pulse|placeholder-glow|shimmer" glob="*.vue,*.jsx,*.tsx,*.css,*.scss"
Grep "USkeleton|SkeletonLoader|ContentLoader" glob="*.vue,*.jsx,*.tsx"

# → スピナー数 vs Skeleton数 の比率
# Healthy: skeleton >= spinner (skeleton主体)
# Anomalous: spinner >> skeleton (スピナー依存)
```
重大度: **WARNING**
科学的根拠: Skeleton Screens feel 20% faster (UI Deploy 2025)

---

### P10.14: Optimistic UI 欠如 `[Tier A]`

Mutation操作後にサーバー応答を待ってからUI更新するパターン。
ユーザーは操作結果を即座に見るべき。

```bash
# Mutation 操作 (POST/PUT/DELETE)
Grep "method:\s*['\"]POST|method:\s*['\"]PUT|method:\s*['\"]DELETE" glob="*.ts,*.js,*.vue,*.jsx,*.tsx"
Grep "\$fetch\(.*method.*POST|\$fetch\(.*method.*PUT|\$fetch\(.*method.*DELETE" glob="*.ts,*.js,*.vue"

# Optimistic Update パターン
Grep "optimistic|\.unshift\(|\.splice\(.*0.*0|tempId|pendingId" glob="*.ts,*.js,*.vue,*.jsx,*.tsx"
Grep "previousData|rollback|onError.*previous|revert" glob="*.ts,*.js,*.vue,*.jsx,*.tsx"

# await → UI更新 パターン (非楽観的)
Grep "await.*\$fetch.*\n.*\.value\s*=" glob="*.vue,*.ts" multiline=true
# → await の後にUI更新 = サーバー待ち = 非楽観的

# → mutation数 vs optimistic更新数 の比率
# 全mutationが楽観的である必要はない (読み取り専用APIは対象外)
# 目安: ユーザー起点のwrite操作の50%以上に楽観的更新があるべき
```
重大度: **WARNING**
科学的根拠: Instagram方式。API完了前のUI更新で知覚遅延ゼロ

---

### P10.15: トランジション・タイミング違反 `[Tier B]`

200-300msの遷移が「速いが知覚可能」の最適レンジ。
100ms未満は知覚できず無意味、500ms超は遅く感じる。

```bash
# CSS トランジション duration
Grep "transition.*duration|transition:\s*\w+\s+\d+" glob="*.css,*.scss,*.vue,*.jsx,*.tsx"
Grep "transition-duration:\s*\d+ms" glob="*.css,*.scss,*.vue"

# JS アニメーション duration
Grep "duration:\s*\d+" glob="*.ts,*.js,*.vue,*.jsx,*.tsx"
Grep "setTimeout.*\d{4,}" glob="*.ts,*.js,*.vue"  # 1000ms以上のタイマー

# Tailwind duration classes
Grep "duration-\[?\d+" glob="*.vue,*.jsx,*.tsx"

# → duration値を抽出して閾値チェック:
# < 100ms: 知覚不能 (無駄)
# 100-500ms: 正常レンジ
# 200-300ms: 最適 (NNGroup研究)
# > 500ms: 遅延知覚 (要検討)
# > 1000ms: ほぼ確実に問題

# ⚠ Tier B: 値のコンテキスト (ホバー効果 vs ページ遷移) でLLM検証必須
```
重大度: **INFO** (500ms超で WARNING)
科学的根拠: NNGroup: 200-300ms transitions rated "fast, but perceivable"

---

### P10.16: View Transitions API 未使用 `[Tier C — LLM専用]`

ブラウザネイティブのGPU加速遷移。2025年にBaseline到達。
SPA内のページ遷移がスムーズでないと「カクつく」印象。

```bash
# Nuxt: View Transitions 設定
Grep "viewTransition" glob="nuxt.config.*"
# → experimental.viewTransition が設定されているか

# 汎用: View Transitions API使用
Grep "startViewTransition|view-transition-name|::view-transition" glob="*.ts,*.js,*.vue,*.css,*.scss"

# ページ遷移コンポーネント (フレームワーク別)
Grep "pageTransition|layoutTransition" glob="nuxt.config.*,*.vue"
Grep "NuxtPage.*transition|Transition.*name" glob="*.vue"

# → SPA構成でページ遷移アニメーションが完全に未設定 = 知覚パフォーマンス損失
# ⚠ Tier C: SSG/静的サイトでは不要。アプリ形態によりLLM判断必須
```
重大度: **INFO**
科学的根拠: View Transitions apps feel 2-3x snappier on low-end devices

---

### P10.17: 大規模データの深いリアクティビティ `[Tier A]`

Vue の ref() は深いリアクティビティ (Proxy traverse) を適用。
大量データ (100+項目) に ref() を使うとProcessing Timeが爆発し INP悪化。

```bash
# ref() で大規模データを保持する可能性のあるパターン
Grep "ref\s*<\s*\w+\[\]" glob="*.ts,*.vue"           # ref<SomeType[]>
Grep "ref\s*\(\s*\[\s*\]\s*\)" glob="*.ts,*.vue"     # ref([])
Grep "ref\s*<.*Map|ref\s*<.*Set" glob="*.ts,*.vue"   # ref<Map> / ref<Set>

# shallowRef の使用
Grep "shallowRef|shallowReactive|shallowReadonly" glob="*.ts,*.vue"
Grep "triggerRef" glob="*.ts,*.vue"

# markRaw の使用
Grep "markRaw" glob="*.ts,*.vue"

# → 配列/Map/Set型の ref() 数 vs shallowRef 数
# 目安: 配列型ref の30%以上が shallowRef であるべき (大規模データ想定)

# SSE/WebSocket 経由のリアルタイムデータは特にshallowRef推奨
Grep "EventSource|useEventSource|WebSocket|useWebSocket" glob="*.ts,*.vue"
# → 同一composable内にshallowRefがあるか確認
```
重大度: **WARNING**
科学的根拠: INP Processing Time直結。shallowRef で Proxy traverse 完全スキップ

---

### P10.18: 数値変化の断絶 `[Tier A]`

残高・価格・カウンターが瞬時に切り替わると「テレポート感」。
数値補間 (tweening) で連続的な変化を演出すべき。

```bash
# 数値表示 (金額・カウント・パーセンテージ)
Grep "price|balance|amount|total|count|percentage|progress" glob="*.vue,*.jsx,*.tsx" -i
Grep "toLocaleString|formatCurrency|formatNumber|Intl\.NumberFormat" glob="*.ts,*.js,*.vue"

# 数値アニメーション/補間
Grep "useTransition|TransitionPresets|useTween|countUp|AnimatedNumber|useSpring" glob="*.ts,*.js,*.vue,*.jsx,*.tsx"
Grep "lerp|interpolate|tween|easing|ease[A-Z]" glob="*.ts,*.js,*.vue"

# → 数値表示コンポーネント数 vs 数値アニメーション数
# 主要な金額/残高表示にアニメーションがないのは知覚パフォーマンス損失
```
重大度: **INFO** (金融UIでWARNING)
科学的根拠: NNGroup: fluid transitions halve perceived wait times

---

### P10.19: メインスレッド・ブロッキング `[Tier B]`

重い計算をメインスレッドで同期実行するとINP悪化。
requestAnimationFrame / Web Worker / requestIdleCallback への委譲が必要。

```bash
# 重い計算の兆候
Grep "\.sort\(|\.filter\(.*\.map\(|\.reduce\(" glob="*.vue,*.ts,*.js"
Grep "JSON\.parse\(.*JSON\.stringify" glob="*.ts,*.js,*.vue"  # 深いクローン
Grep "for\s*\(.*\.length" glob="*.ts,*.js,*.vue"              # 大量ループ

# 非同期化/オフロードパターン
Grep "requestAnimationFrame|requestIdleCallback|useRafFn" glob="*.ts,*.js,*.vue"
Grep "Worker|SharedWorker|useWebWorkerFn" glob="*.ts,*.js,*.vue"
Grep "queueMicrotask|nextTick|setTimeout\(\s*\(\)\s*=>" glob="*.ts,*.js,*.vue"

# Computed の重い計算
Grep "computed\(\(\)\s*=>" -A 5 glob="*.vue,*.ts"
# → computed 内に .sort/.filter/.map チェーンがある = 毎回再計算

# ⚠ Tier B: ループ/ソートがUIスレッドかサーバーかでLLM判断必須
```
重大度: **WARNING** (描画ブロック確認時 CRITICAL)
科学的根拠: INP Input Delay + Processing Time. 60FPS未満でリテンション27%低下

---

### P10.20: リアルタイム接続のクリーンアップ欠如 `[Tier A]`

SSE/WebSocket/EventSource の接続がコンポーネント破棄時に解放されない。
SPA遷移のたびに接続が蓄積し、メモリリーク + 重複イベント処理。

```bash
# SSE/EventSource の使用
Grep "EventSource|useEventSource|evtSource" glob="*.ts,*.js,*.vue"
Grep "sse\.on\(|eventSource\.on\(" glob="*.ts,*.js,*.vue"

# WebSocket の使用
Grep "WebSocket|useWebSocket|ws\.on\(" glob="*.ts,*.js,*.vue"

# クリーンアップ
Grep "onScopeDispose|onUnmounted|onBeforeUnmount" glob="*.ts,*.js,*.vue"
Grep "\.close\(\)|\.disconnect\(\)|cleanup\(\)|unsubscribe\(\)" glob="*.ts,*.js,*.vue"
Grep "tryOnScopeDispose|tryOnUnmounted" glob="*.ts,*.vue"  # VueUse パターン

# → リアルタイム接続開始数 vs クリーンアップ数
# R8 (MLS) との重複: こちらはリアルタイム特化
```
重大度: **WARNING** (SPA構成で CRITICAL)
科学的根拠: L8 R6 (メモリリーク) の知覚パフォーマンス版。重複リスナー = 重複処理 = INP悪化

---

### P10.21: Lazy Component 欠如 `[Tier B]`

初期バンドルに全コンポーネントを含めるとFCP/LCP悪化。
画面外・低優先コンポーネントは遅延ロードすべき。

```bash
# Nuxt: Lazy プレフィックス
Grep "Lazy[A-Z]" glob="*.vue"
# → 全コンポーネント数に対する Lazy 比率

# React: lazy/Suspense
Grep "React\.lazy|lazy\(\(\)\s*=>" glob="*.jsx,*.tsx"
Grep "<Suspense" glob="*.jsx,*.tsx"

# 汎用: dynamic import
Grep "import\(\s*['\"]" glob="*.ts,*.js,*.vue,*.jsx,*.tsx"
Grep "defineAsyncComponent" glob="*.ts,*.vue"

# 重いライブラリの静的import (バンドル肥大化)
Grep "import.*from ['\"]chart\.js|import.*from ['\"]d3|import.*from ['\"]three" glob="*.ts,*.js,*.vue"
Grep "import.*from ['\"]monaco-editor|import.*from ['\"]@codemirror" glob="*.ts,*.js,*.vue"

# → 画面外の重いコンポーネントが即座にロードされている = FCP/LCP悪化
# ⚠ Tier B: 「重い」の判断にはLLM検証必須
```
重大度: **WARNING**
科学的根拠: Doherty閾値 (<400ms) 遵守にはバンドル最適化が前提

---

### P10.22: リソース優先度ヒント欠如 `[Tier C — LLM専用]`

LCP要素 (ヒーロー画像、メインコンテンツ) に fetch-priority/preload がない。
逆に低優先リソースがeager loadされるとLCP悪化。

```bash
# 画像の優先度ヒント
Grep "fetchPriority|fetch-priority|loading=\"eager\"|loading=\"lazy\"" glob="*.vue,*.jsx,*.tsx,*.html"
Grep "NuxtImg|next/image|Image.*priority" glob="*.vue,*.jsx,*.tsx"
Grep "<link.*preload|<link.*prefetch" glob="*.vue,*.html"

# フォントのプリロード
Grep "preload.*font|font-display" glob="*.css,*.vue,*.html"

# → LCP候補の画像/テキストに優先度ヒントがないケース
# ⚠ Tier C: LCP要素の特定はページ構造依存でgrep不適格
```
重大度: **INFO**
科学的根拠: web.dev LCP optimization. 0.1秒の改善でコンバージョン8.4%向上

---

## 知覚パフォーマンス4層モデル

検出パターンは4つの知覚レイヤーに対応:

```
Layer 1: Instant (<50ms)   — P10.14 Optimistic UI
                             ボタン状態変化、タッチフィードバック
Layer 2: Fast (<200ms)     — P10.13 Skeleton, P10.16 View Transitions
                             P10.18 数値補間開始
Layer 3: Perceived (<400ms) — P10.15 Animation Timing
                             P10.21 Lazy Component (FCP)
Layer 4: Background         — P10.17 shallowRef, P10.19 Main Thread
                             P10.20 Cleanup, P10.22 Resource Hints
```

---

## PPR (Perceived Performance Rate) サブコンポーネント

```
PPR = 0.25 × skeleton_ratio           (P10.13: skeleton vs spinner)
    + 0.20 × optimistic_ratio         (P10.14: optimistic update率)
    + 0.20 × reactivity_ratio         (P10.17: shallowRef使用率)
    + 0.15 × cleanup_ratio            (P10.20: リアルタイム接続クリーンアップ率)
    + 0.10 × lazy_ratio               (P10.21: Lazy Component率)
    + 0.10 × animation_quality        (P10.15+P10.18: アニメーション品質)
```

該当パターンがないカテゴリ (例: WebSocket未使用でP10.20がN/A) は
N/A Weight Redistribution で残存パラメーターへ再配分。

---

## 重要度判定ガイド

| 条件 | 重大度 |
|------|--------|
| SPA構成でリアルタイム接続リーク (P10.20) | **CRITICAL** |
| 全UIがスピナー依存 + Skeleton皆無 (P10.13) | **WARNING** |
| 大規模配列にref()使用 + INP悪化兆候 (P10.17) | **WARNING** |
| メインスレッドブロッキング確認 (P10.19) | **WARNING→CRITICAL** |
| 金融UIで数値アニメーション欠如 (P10.18) | **WARNING** |
| アニメーション > 500ms (P10.15) | **WARNING** |
| View Transitions未設定 (P10.16) | **INFO** |
| リソース優先度ヒント欠如 (P10.22) | **INFO** |
