# Detection Patterns — L1-L6 レイヤー別クエリ集

スタック非依存。各パターンにマルチフレームワーク対応の grep/glob クエリを付記。
実例アーカイブは `case-archive.md` を参照。

**重要**: `path="server/"` 等の指定ディレクトリが存在しない場合、
grep は 0 件を返す。0/0 は「問題なし」ではなく「計測不能 (N/A)」として扱うこと。
QAP 算出時に分母=0 の場合は該当パラメーターをスキップし、
残りのパラメーターで重みを再配分する。

---

## L1: 契約不一致 (Contract Mismatch)

### P1.1: ID サフィックス不一致
外部サービスが `:latest` / `v1` 等を付与し、内部設定は省略する。
```bash
# 設定ファイルの ID/名前
Grep "model.*[:=]|name.*[:=]|id.*[:=]" glob="*.config.*,*.json,*.yaml,*.toml,.env*"
# API レスポンスの ID フィールドと突合
# → 文字列の正規化関数が境界にあるか確認
```

### P1.2: 型定義 vs 実データ乖離
```bash
# 型定義ファイルを探索 (マルチフレームワーク)
Glob "types/**/*.ts" OR Glob "shared/types/**/*.ts" OR Glob "src/types/**/*.ts"
Glob "interfaces/**/*.ts" OR Glob "models/**/*.ts"
# interface/type のフィールドを列挙
Grep "export (interface|type) " glob="*.ts"
# API レスポンスの return 型と突合
Grep "return " path="server/" glob="*.ts"
Grep "return " path="api/" glob="*.ts"
Grep "return " path="src/routes/" glob="*.ts"
# → optional (?) がないが実際は undefined になるフィールド
```

### P1.3: ハードコード定数の不一致
```bash
# サーバー側定数
Grep "const\s+\w+\s*=" path="server/" glob="*.ts,*.js"
Grep "const\s+\w+\s*=" path="api/" glob="*.ts,*.js"
Grep "const\s+\w+\s*=" path="src/lib/" glob="*.ts,*.js"
# 同一文字列がフロントにもハードコードされていないか
Grep "'same-value'" glob="*.vue,*.jsx,*.tsx,*.svelte"
```

### P1.4: HTTP ステータスコード不一致
```bash
# サーバーが返すステータスコード (マルチフレームワーク)
Grep "statusCode|status\s*[:=]\s*[0-9]|\.status\([0-9]" path="server/" glob="*.ts,*.js"
Grep "createError|HttpException|BadRequest|NotFound" path="server/" glob="*.ts,*.js"
# フロントが期待するステータスコード
Grep "status\s*===\s*[0-9]|response\.ok|\.status\s*[!=]" glob="*.ts,*.js,*.vue,*.jsx,*.tsx"
```

### P1.5: API エンドポイント不一致
```bash
# サーバー側のルート定義
Glob "server/api/**/*.ts"              # Nitro/Nuxt
Glob "app/api/**/*.ts"                 # Next.js
Glob "src/routes/**/*.ts"              # SvelteKit/Express
Grep "router\.\w+\(['\"]/" glob="*.ts,*.js"  # Manual routing
Grep "app\.\w+\(['\"]/" glob="*.ts,*.js"          # Hono/Express
Grep "fastify\.\w+\(['\"]/" glob="*.ts,*.js"       # Fastify
Grep "\.procedure\.\w+\(" glob="*.ts"               # tRPC
# クライアント側の API 呼び出し
Grep "fetch\(['\"]|ofetch\(['\"]|\$fetch\(['\"]|axios\.\w+\(['\"]" glob="*.ts,*.js,*.vue,*.jsx,*.tsx"
# → サーバーにないパスをクライアントが呼んでいる
```

---

## L2: サイレント失敗 (Silent Failure)

### P2.1: 空 catch ブロック
```bash
Grep "catch\s*\(\s*\)\s*\{" glob="*.ts,*.js"       # catch() {}
Grep "catch\s*\{" glob="*.ts,*.js"                  # catch {} (TS/Swift)
Grep "\.catch\(\s*\(\s*\)\s*=>" glob="*.ts,*.js"    # .catch(() =>
Grep "\.catch\(\s*\(\s*_?\s*\)\s*=>\s*\{\s*\}\)" glob="*.ts,*.js"  # .catch((_) => {})
# Python
Grep "except.*:\s*$|except.*:.*pass" glob="*.py"
# Go
Grep "if err != nil \{" -A 1 glob="*.go"            # → 次行が return nil なら隠蔽
# Rust
Grep "\.unwrap_or|\.ok\(\)" glob="*.rs"
```

### P2.2: fire-and-forget 非同期
```bash
# await なしの非同期呼び出し (JS/TS)
Grep "^\s+fetch\(" glob="*.ts,*.js"
Grep "^\s+\$fetch\(" glob="*.ts,*.js"
Grep "^\s+ofetch\(" glob="*.ts,*.js"
# Python の fire-and-forget
Grep "asyncio\.create_task\(|\.delay\(" glob="*.py"
# → 結果を await/then で受け取っていないもの
```

### P2.3: エラーログなし catch
```bash
# catch 後の3行を確認 — ログ/throw/report がないブロック
Grep "catch" -A 3 glob="*.ts,*.js" output_mode="content"
# → console.error / logger / throw / report がない = silent
# Python
Grep "except" -A 3 glob="*.py" output_mode="content"
```

### P2.4: フォールバック隠蔽
```bash
# try-catch で代替値を返すが元のエラーを記録しない
Grep "catch.*return.*\[\]" glob="*.ts,*.js"          # 空配列
Grep "catch.*return.*null" glob="*.ts,*.js"           # null
Grep "catch.*return.*false" glob="*.ts,*.js"          # false
Grep "catch.*return.*\{\}" glob="*.ts,*.js"           # 空オブジェクト
Grep "catch.*return.*undefined" glob="*.ts,*.js"      # undefined
Grep "catch.*return.*''" glob="*.ts,*.js"             # 空文字列
```

---

## L3: 状態同期バグ (State Sync Bug)

### P3.1: イベント定義 vs 購読 (マルチフレームワーク)
```bash
# イベント定義/送信側 (サーバー)
Grep "emit\(|broadcast\(|publish\(|\.send\(|\.write\(" path="server/" glob="*.ts,*.js"
Grep "io\.emit|socket\.emit|ws\.send" path="server/" glob="*.ts,*.js"
# イベント購読側 (クライアント)
Grep "\.on\(|subscribe\(|addEventListener|useSubscription" glob="*.ts,*.js,*.vue,*.jsx,*.tsx,*.svelte"
# → emit されるがどこからも listen されていないイベント = dead path
```

### P3.2: サーバー送信 vs クライアント受信
```bash
# Server-Sent Events
Grep "res\.write\(|event:" path="server/" glob="*.ts,*.js"
# WebSocket メッセージタイプ
Grep "type.*[:=].*['\"]|event.*[:=].*['\"]" path="server/" glob="*.ts,*.js"
# クライアント側の受信フィルタ
Grep "\.on\(.*type|addEventListener.*message|onmessage" glob="*.ts,*.js,*.vue,*.jsx,*.tsx"
# → サーバーが送信するタイプのうちクライアントが listen していないもの
```

### P3.3: 重複検知ロジックの脆弱性
```bash
# タイムスタンプ・ID による重複チェック
Grep "lastProcessed|lastTimestamp|dedup|===.*timestamp|duplicate" glob="*.ts,*.js"
# Date.now() を一意キーとして使用
Grep "Date\.now\(\)|\.toISOString\(\)" glob="*.ts,*.js"
# → Map/Set のキーに使われていないか確認
```

### P3.4: ポーリングと push の競合
```bash
# ポーリング
Grep "setInterval|usePolling|polling|refetch.*interval|refreshInterval" glob="*.ts,*.js,*.vue,*.jsx,*.tsx"
# WebSocket/SSE リアルタイム更新
Grep "WebSocket|EventSource|socket\.on|useSubscription" glob="*.ts,*.js,*.vue,*.jsx,*.tsx"
# → 同じデータを両方で更新している場合 = 競合
```

---

## L4: 死んだ機能 (Dead Feature)

### P4.1: 空ハンドラ (マルチフレームワーク)
```bash
# Vue
Grep "@click=\"|@submit=\"|@change=\"" glob="*.vue"
# React/Next
Grep "onClick=\{|onSubmit=\{|onChange=\{" glob="*.jsx,*.tsx"
# Svelte
Grep "on:click=\{|on:submit=\{" glob="*.svelte"
# Angular
Grep "\(click\)=\"|\(submit\)=\"" glob="*.html,*.component.ts"
# → ハンドラ関数が空 / TODO / noop か確認
Grep "TODO|FIXME|noop|\{\s*\}|function\s*\(\s*\)\s*\{\s*\}" glob="*.ts,*.js"
```

### P4.2: 常時非表示の UI
```bash
# Vue
Grep "v-if=\"|v-show=\"" glob="*.vue"
# React
Grep "\{.*&&|.*\?.*:.*null|isVisible|isHidden|display.*none" glob="*.jsx,*.tsx"
# Svelte
Grep "\{#if " glob="*.svelte"
# → 条件が常に false になるかを追跡 (初期値 false で変更なし)
```

### P4.3: 到達不能ルート
```bash
# ファイルベースルーティング (フレームワーク自動検出)
Glob "pages/**/*.vue"                  # Nuxt
Glob "app/**/page.tsx"                 # Next.js App Router
Glob "pages/**/*.tsx"                  # Next.js Pages Router
Glob "src/routes/**/*.svelte"          # SvelteKit
# 設定ベースルーティング
Grep "path:\s*['\"]/" glob="router*.ts,routes*.ts,*routing*.ts"
# リンク元 (マルチフレームワーク)
Grep "to=\"|href=\"|navigateTo|router\.push|navigate\(|Link " glob="*.vue,*.jsx,*.tsx,*.svelte,*.html"
# → 定義はあるがどこからもリンクされていない = orphan route
```

### P4.4: 未使用モジュール/フック
```bash
# 定義されたカスタムフック/composable
Glob "composables/use*.ts"             # Nuxt/Vue
Glob "hooks/use*.ts"                   # React
Glob "hooks/use*.tsx"                  # React
Glob "lib/use*.ts"                     # Generic
# import されているか確認
Grep "from.*composables/use|from.*hooks/use|import.*use[A-Z]" glob="*.ts,*.js,*.vue,*.jsx,*.tsx"
# → 定義はあるが import されていない = dead module
```

### P4.5: 未使用エクスポート
```bash
# export された関数/定数
Grep "export (const|function|class|enum) " glob="*.ts,*.js"
# → 同名が他ファイルで import されているか
# 注: 正確な検出は knip / ts-prune 等のツールが有効
```

---

## L5: 構造矛盾 (Structural Contradiction)

### P5.1: コメント vs 実装の乖離
```bash
# TODO / FIXME / HACK / DEPRECATED コメント
Grep "TODO|FIXME|HACK|DEPRECATED|XXX|WORKAROUND" glob="*.ts,*.js,*.py,*.go,*.rs,*.vue,*.jsx,*.tsx"
# → 古い TODO が放置されていないか (git blame で日付確認)
```

### P5.2: 設定値の散在
```bash
# 環境変数の使用箇所 (マルチフレームワーク)
Grep "process\.env\." glob="*.ts,*.js"
Grep "import\.meta\.env\." glob="*.ts,*.js,*.vue"
Grep "Deno\.env" glob="*.ts,*.js"
Grep "os\.environ|os\.getenv" glob="*.py"
Grep "os\.Getenv" glob="*.go"
Grep "std::env::var" glob="*.rs"
# 環境変数の定義箇所
Grep "^\w+=" glob=".env*"
Grep "environment:" glob="docker-compose.yml,docker-compose.yaml"
# → 使われているが未定義、または定義されているが未使用
```

### P5.3: 命名不一致
```bash
# camelCase vs snake_case 混在 (型定義内)
Grep "[a-z]+_[a-z]+" path="types/" glob="*.ts"
Grep "[a-z]+[A-Z][a-z]+" path="types/" glob="*.ts"
# → 同じスコープ内に両方の命名規則が混在
# 同一概念の複数命名
Grep "user_id|userId|user\.id" glob="*.ts,*.js"
```

### P5.4: import の循環
```bash
# 相互 import の検出 (同一ディレクトリ内)
Grep "from ['\"]\./" path="server/utils/" glob="*.ts"
Grep "from ['\"]\./" path="src/lib/" glob="*.ts"
Grep "from ['\"]\./" path="src/utils/" glob="*.ts"
# → A → B → A の循環パターン
# 注: 正確な検出は madge / dpdm 等のツールが有効
```

### P5.5: デッドコード参照
```bash
# コメントアウトされたコード (import/関数呼び出し)
Grep "//\s*import|//\s*const|//\s*function|#\s*import|#\s*def " glob="*.ts,*.js,*.py"
# → 削除すべきか復活すべきか不明なコメントアウト
```

---

## L6: リソース浪費 (Resource Waste)

### P6.1: ループ内 fetch (N+1 問題)
```bash
# ループ内の HTTP/DB 呼び出し
Grep "for.*\{" -A 10 path="server/" glob="*.ts,*.js"
# → ループ内に fetch / await / query が含まれるか
# Python
Grep "for.*:" -A 5 glob="*.py"
# → ループ内に requests.get / await / session.query が含まれるか
```

### P6.2: 巨大ペイロード
```bash
# 一覧 API がフィルタなしで全件返す
Grep "return.*\.map\(|return.*\.filter\(" path="server/" glob="*.ts,*.js"
Grep "return.*\.map\(|return.*\.filter\(" path="api/" glob="*.ts,*.js"
# → map/filter 前に limit / pagination / select がないか
Grep "limit|offset|skip|take|cursor|select\(" path="server/" glob="*.ts,*.js"
```

### P6.3: 不要な再計算 (マルチフレームワーク)
```bash
# Vue computed
Grep "computed\(\(\) =>" glob="*.vue,*.ts"
# React useMemo / useCallback 欠如
Grep "useMemo|useCallback" glob="*.jsx,*.tsx"
# → 大きなリストを毎回 .map() で再生成していないか
Grep "\.map\(.*\.map\(|\.filter\(.*\.map\(" glob="*.ts,*.js,*.vue,*.jsx,*.tsx"
```

### P6.4: 不要な再レンダリング
```bash
# React: インライン関数/オブジェクトを props として渡す
Grep "onClick=\{\(\) =>|style=\{\{" glob="*.jsx,*.tsx"
# Vue: リアクティブオブジェクトの不要な展開
Grep "toRefs\(|\.value\." glob="*.vue,*.ts"
# → レンダリング最適化の欠如
```

### P6.5: バンドルサイズ肥大化
```bash
# 巨大ライブラリの全インポート
Grep "import.*from ['\"]lodash['\"]" glob="*.ts,*.js"       # lodash 全体
Grep "import.*from ['\"]moment['\"]" glob="*.ts,*.js"        # moment (重い)
Grep "import \* as" glob="*.ts,*.js"                         # namespace import
# → lodash/get, date-fns 等の tree-shakeable 代替を使うべき
```

---

## L10: UI Responsiveness (UI応答性)

Action→Feedback 断絶の検出。ユーザーが操作しても UI が変わらない状態。

### 検出 Tier

実世界テスト (kenchiku: Nuxt 4 + Nuxt UI v3) の結果に基づく分類:

| Tier | 意味 | 実行方法 | パターン |
|------|------|---------|---------|
| **A** | grep 単体で高精度検出 | grep → 直接レポート | P10.1-P10.4, P10.9 |
| **B** | grep で候補抽出 → LLM 検証必須 | grep → LLM verify | P10.5, P10.7, P10.8 |
| **C** | grep 不適格 → LLM 検証フェーズ専用 | LLM のみ | P10.6, P10.10 |

**フレームワーク検出**: scan 開始時に `package.json` から UI ライブラリを特定する。
```bash
# フレームワーク検出
Grep "@nuxt/ui|radix-vue|headless-ui|@headlessui|@chakra-ui" glob="package.json"
# → 検出されたライブラリが内部処理するパターンを Tier B→C に降格
# 例: Nuxt UI 検出 → P10.6 (disabled), P10.8 (focus-trap) は内部処理済み
```

### P10.1: Action-Feedback 断絶 `[Tier A]`
アクションハンドラに状態更新・フィードバック UI がないケース。
```bash
# アクションハンドラ (マルチフレームワーク)
Grep "onClick=\{|@click=\"|on:click=\{|\(click\)=\"" glob="*.vue,*.jsx,*.tsx,*.svelte,*.html"
Grep "onSubmit=\{|@submit=\"|on:submit=\{" glob="*.vue,*.jsx,*.tsx,*.svelte"
# 同一コンポーネント内の状態更新
Grep "setState|set[A-Z]|\.value\s*=|store\.\w+\s*=|\$patch|commit\(" glob="*.ts,*.js,*.vue,*.jsx,*.tsx"
# → ハンドラ定義数 vs 状態更新数の比率 = ARR の一部
```

### P10.2: Mutation-Revalidation 欠如 `[Tier A]`
POST/PUT/DELETE 後にデータ再取得がないケース。
```bash
# Mutation 呼び出し (マルチフレームワーク)
Grep "method:\s*['\"]POST|method:\s*['\"]PUT|method:\s*['\"]DELETE" glob="*.ts,*.js,*.vue,*.jsx,*.tsx"
Grep "\$fetch\(.*method|useFetch\(.*method|fetch\(.*method" glob="*.ts,*.js,*.vue,*.jsx,*.tsx"
# Revalidation / Invalidation
Grep "invalidateQueries|refetchQueries|refreshNuxtData|clearNuxtData|revalidatePath|mutate\(" glob="*.ts,*.js,*.vue,*.jsx,*.tsx"
Grep "router\.refresh\(\)|await refresh\(\)" glob="*.ts,*.js,*.vue,*.jsx,*.tsx"
# → mutation 数 vs revalidation 数の比率
```

### P10.3: Loading/Error UI 欠如 `[Tier A]`
非同期操作に loading/error 表示がないケース。
```bash
# 非同期データフェッチ (マルチフレームワーク)
Grep "useQuery|useSWR|useAsyncData|useFetch|useLazyFetch" glob="*.ts,*.js,*.vue,*.jsx,*.tsx"
Grep "useQuery" glob="*.ts,*.js,*.vue,*.jsx,*.tsx"
# Loading/Error 状態参照
Grep "isLoading|isPending|isFetching|status.*loading|pending\.value" glob="*.ts,*.js,*.vue,*.jsx,*.tsx"
Grep "isError|error\.value|status.*error|fetchError" glob="*.ts,*.js,*.vue,*.jsx,*.tsx"
# → async 操作数 vs loading/error 参照数の比率
```

### P10.4: Optimistic Rollback 欠如 `[Tier A]`
楽観的更新に失敗時ロールバックがないケース。
```bash
# Optimistic update (React Query / TanStack)
Grep "onMutate|optimisticUpdate|optimistic" glob="*.ts,*.js,*.vue,*.jsx,*.tsx"
# Rollback on error
Grep "onError.*context|onError.*rollback|onError.*previous" glob="*.ts,*.js,*.vue,*.jsx,*.tsx"
# → onMutate 数 vs onError rollback 数の比率 (該当なしなら N/A)
```

### P10.5: 空状態の写像欠落 [Tractatus: T3] `[Tier B]`
データリスト表示に空状態のハンドリングがないケース。
```bash
# リスト/配列レンダリング (マルチフレームワーク)
Grep "v-for=|\.map\(|{#each|ngFor" glob="*.vue,*.jsx,*.tsx,*.svelte,*.html"
# 空状態チェック
Grep "v-if.*length|\.length\s*===?\s*0|isEmpty|no-data|empty-state" glob="*.vue,*.jsx,*.tsx,*.svelte"
# → リスト描画数 vs 空状態チェック数の比率

# ⚠ 除外フィルタ (偽陽性削減):
# Skeleton/Placeholder コンポーネントの v-for は空状態不要 (ローディング表現)
# → USkeleton, Skeleton, Placeholder を含む行は候補から除外
# 実測: フィルタなし精度 25% → フィルタあり精度 75%+ (kenchiku プロジェクト)
```

### P10.6: disabled+clickable 矛盾 [Tractatus: T4] `[Tier C — LLM専用]`
disabled 属性と click ハンドラが同一要素に共存するケース。
```bash
# disabled 属性を持つ要素
Grep "disabled.*@click|disabled.*onClick|:disabled.*@click" glob="*.vue,*.jsx,*.tsx,*.svelte"
Grep "aria-disabled.*onClick|aria-disabled.*@click" glob="*.vue,*.jsx,*.tsx,*.svelte"
# → 共存パターンの存在検出 (Presence)

# ⚠ Tier C 理由: Nuxt UI, Radix UI, Headless UI 等の主要フレームワークは
# disabled 属性設定時に内部的に click イベントを無効化する。
# 実測: kenchiku (Nuxt UI v3) で 100% 偽陽性。
# → grep ではなく LLM 検証フェーズで「カスタム要素にのみ」チェック。
```

### P10.7: 偽アフォーダンス [Cognitive: C1] `[Tier B]`
クリックできないのにクリックできるように見える要素。
```bash
# cursor:pointer を持つ非インタラクティブ要素
Grep "cursor:\s*pointer" glob="*.css,*.scss,*.vue,*.jsx,*.tsx"
# span/div に cursor:pointer だが onClick/href がない
# → CSS cursor:pointer 数 vs interactive handler 数の比率
```

### P10.8: フォーカス管理欠如 [Cognitive: C4] `[Tier B]`
モーダル/ダイアログにフォーカストラップがないケース。
**注意**: Nuxt UI (UModal), Radix UI, Headless UI は内部で focus-trap を実装。
フレームワーク検出で該当ライブラリが見つかった場合、フレームワークコンポーネント
使用箇所は候補から除外し、カスタム実装のみを検査する。
```bash
# ダイアログ/モーダルコンポーネント
Grep "dialog|modal|drawer|sheet|popover" glob="*.vue,*.jsx,*.tsx,*.svelte" -i
# フォーカス管理
Grep "focus-trap|FocusTrap|useFocusTrap|trapFocus|createFocusTrap|inert" glob="*.vue,*.jsx,*.tsx,*.ts,*.js"
# → dialog 数 vs focus-trap 数の比率
```

### P10.9: 破壊的操作の保護欠如 [Behavioral: B3] `[Tier A]`
削除・解除などの不可逆操作に確認がないケース。
**実測**: kenchiku プロジェクトで実バグ発見 (removeNodeByIndex, removeOption, emit('delete')
が既存 ConfirmDialog.vue を使用していない)。L10 で最も信頼性の高いパターン。
```bash
# 破壊的操作ハンドラ
Grep "delete|remove|destroy|revoke|unsubscribe|cancel.*subscription" glob="*.vue,*.jsx,*.tsx,*.ts,*.js" -i
# 確認ダイアログ
Grep "confirm\(|AlertDialog|ConfirmDialog|useConfirm|window\.confirm" glob="*.vue,*.jsx,*.tsx,*.ts,*.js"
# → 破壊的操作数 vs 確認ダイアログ数の比率
```

### P10.10: 操作的デフォルト [Behavioral: B2] `[Tier C — LLM専用]`
マーケティング同意等がデフォルトでチェック済みのケース。
```bash
# デフォルトチェック済み
Grep "defaultChecked|:checked=\"true\"|checked=\"checked\"|v-model.*=.*true" glob="*.vue,*.jsx,*.tsx,*.html"
# 文脈キーワード (consent, marketing, newsletter, notification)
Grep "newsletter|marketing|consent|subscribe|notification" glob="*.vue,*.jsx,*.tsx,*.html" -i
# → defaultChecked + marketing系キーワード共存 (Presence)
```
