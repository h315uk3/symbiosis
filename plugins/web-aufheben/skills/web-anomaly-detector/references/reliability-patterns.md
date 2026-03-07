# L8: 信頼性違和感パターン (Reliability Anomalies)

SRE / Chaos Engineering / 分散システムの観点から、
コードレビューや grep/glob で検出可能な信頼性アンチパターン。

---

## R1: タイムアウト未設定 (Missing Timeouts)

### P8.1: HTTP リクエストのタイムアウト未設定
外部 API 呼び出しにタイムアウトがないと、応答しないサービスに無限に待ち続ける。
```bash
# fetch / ofetch / axios でタイムアウト設定の有無
Grep "fetch\s*\(" path="server/" glob="*.ts"
Grep "\$fetch\s*\(" path="server/" glob="*.ts"
Grep "ofetch\s*\(" path="server/" glob="*.ts"
Grep "axios\.\w+\s*\(" path="server/" glob="*.ts"
# → 同一呼び出しに timeout / signal / AbortController がないか確認

# AbortController の使用パターン
Grep "AbortController\|AbortSignal\.timeout" path="server/" glob="*.ts"
# → 外部呼び出し数に対して AbortController が少なすぎる場合は問題
```
重大度: **CRITICAL**

### P8.2: データベースクエリのタイムアウト未設定
```bash
# Prisma
Grep "prisma\.\w+\.\w+\(" path="server/" glob="*.ts"
# → Prisma の connection timeout / query timeout が設定されているか
Grep "timeout\|connection_limit" glob="*.prisma,*.env*"

# Drizzle / raw SQL
Grep "db\.\w+\(" path="server/" glob="*.ts"
Grep "pool.*timeout\|connectionTimeout\|queryTimeout" glob="*.ts,*.js"
```
重大度: **WARNING**

### P8.3: WebSocket のタイムアウト/ハートビート欠如
```bash
Grep "WebSocket\|new\s+WS\b\|ws\.\w+\(" path="server/" glob="*.ts"
Grep "ping\|pong\|heartbeat\|keepAlive" path="server/" glob="*.ts"
# → WebSocket 接続にハートビート/ping-pong がないと死んだ接続が残る
```
重大度: **WARNING**

---

## R2: リトライストーム (Retry Storm)

### P8.4: Exponential Backoff なしのリトライ
固定間隔リトライは障害時にサーバーを圧倒する。
```bash
# リトライロジックの存在確認
Grep "retry\|retries\|maxRetries\|retryCount\|retryDelay" glob="*.ts,*.js"
# → backoff / exponential / jitter が同一ファイルにないか確認
Grep "backoff\|exponential\|jitter" glob="*.ts,*.js"

# 固定間隔リトライのパターン
Grep "setTimeout.*retry\|setInterval.*retry" glob="*.ts,*.js"
# → delay が固定値なら問題
```
重大度: **WARNING**

### P8.5: 無制限リトライ
```bash
# while(true) + retry のような無制限ループ
Grep "while\s*\(\s*true\s*\).*retry\|for\s*\(\s*;;\s*\).*retry" glob="*.ts,*.js"
# → maxRetries の上限が設定されているか
Grep "maxRetries\|MAX_RETRIES\|retryLimit" glob="*.ts,*.js"
```
重大度: **WARNING**

### P8.6: リトライ対象の判別なし
```bash
# 全エラーを一律リトライ (4xx もリトライ)
Grep "catch.*retry\|\.catch.*setTimeout" glob="*.ts,*.js"
# → ステータスコード判定なしのリトライは無駄
# → 400, 401, 403, 404 はリトライしても無意味
```
重大度: **INFO**

---

## R3: Circuit Breaker の欠如

### P8.7: 外部サービス呼び出しに Circuit Breaker なし
障害が発生した外部サービスへの呼び出しを制御する仕組みがない。
```bash
# Circuit Breaker ライブラリの使用確認
Grep "circuit[Bb]reaker\|opossum\|cockatiel\|brakes" glob="*.ts,*.js,package.json"
# → 外部 API 呼び出しが多いのに circuit breaker が見つからない場合は問題

# 外部サービス呼び出しの数を確認
Grep "fetch\(.*https?://\|ofetch\(.*https?://\|\$fetch\(.*https?://" path="server/" glob="*.ts"
```
重大度: **WARNING**

---

## R4: Thundering Herd / Cache Stampede

### P8.8: キャッシュ失効時の同時リクエスト
```bash
# キャッシュの TTL 設定
Grep "ttl\|maxAge\|expir\|cache.*time" path="server/" glob="*.ts"
# → stale-while-revalidate / lock / mutex パターンがないか
Grep "lock\|mutex\|singleflight\|coalesce" path="server/" glob="*.ts"

# Redis / in-memory キャッシュの使用
Grep "redis\|lru-cache\|node-cache\|cacache" glob="*.ts,*.js,package.json"
```
重大度: **WARNING**

### P8.9: 起動時の同時初期化
```bash
# アプリ起動時に全サービスを同時に初期化
Grep "Promise\.all\(.*init\|Promise\.all\(.*connect\|Promise\.all\(.*setup" glob="*.ts,*.js"
# → 全サービスが同時にDBやAPIに接続 = thundering herd
```
重大度: **INFO**

---

## R5: Connection Pool 枯渇

### P8.10: DB接続プールのサイズ/設定不備
```bash
# プール設定
Grep "pool\s*[:=]\s*\{?\s*\d\|connection_limit\|pool_size\|max_connections" glob="*.ts,*.js,*.env*,*.prisma"
# → プールサイズが小さすぎる or 設定なし
# → connectionTimeoutMillis の未設定
```
重大度: **WARNING**

### P8.11: 接続の未解放
```bash
# 手動接続管理で close / release / end がない
Grep "\.connect\(\)" path="server/" glob="*.ts"
# → 同一関数に .close() / .release() / .end() / .disconnect() がないか
Grep "\.release\(\)\|\.close\(\)\|\.end\(\)\|\.disconnect\(\)" path="server/" glob="*.ts"
# → finally ブロック内での解放が理想
```
重大度: **WARNING**

---

## R6: メモリリーク

### P8.12: イベントリスナーの未解除
```bash
# addEventListener / on の呼び出し
Grep "addEventListener\s*\(" glob="*.ts,*.js,*.vue"
Grep "\.on\s*\(['\"]" glob="*.ts,*.js"
# → removeEventListener / .off / cleanup が対応して存在するか
Grep "removeEventListener\|\.off\s*\(['\"]" glob="*.ts,*.js,*.vue"

# Vue の onMounted 内で登録して onUnmounted で解除しない
Grep "onMounted.*addEventListener\|onMounted.*\.on\(" glob="*.vue"
Grep "onUnmounted\|onBeforeUnmount" glob="*.vue"
# → onMounted でリスナー登録して cleanup がない
```
重大度: **WARNING**

### P8.13: setInterval の未クリア
```bash
Grep "setInterval\s*\(" glob="*.ts,*.js,*.vue"
Grep "clearInterval\s*\(" glob="*.ts,*.js,*.vue"
# → setInterval の数 > clearInterval の数 = リーク可能性
```
重大度: **WARNING**

### P8.14: 無制限のバッファ/キュー
```bash
# 配列への無制限 push
Grep "\.push\s*\(" path="server/" glob="*.ts"
# → 同一配列に対して length チェック / shift / splice / 上限がないか
# → メモリが無制限に成長する
Grep "maxSize\|maxLength\|MAX_QUEUE\|capacity" glob="*.ts,*.js"
```
重大度: **WARNING**

### P8.15: ストリーム/ファイルハンドルの未クローズ
```bash
Grep "createReadStream\|createWriteStream\|fs\.open" path="server/" glob="*.ts"
# → .close() / .destroy() / .end() が対応して存在するか
# → try-finally または using 文でクローズ保証されているか
```
重大度: **WARNING**

---

## R7: Cascading Failure

### P8.16: 単一依存の障害が全体に波及
```bash
# 起動時の必須チェック (一つ失敗で全停止)
Grep "throw.*connect\|throw.*init\|process\.exit" path="server/" glob="*.ts"
# → 非必須サービスの障害でアプリ全体が停止しないか
```
重大度: **WARNING**

### P8.17: Bulkhead パターンの欠如
```bash
# サービス間の分離
Grep "bulkhead\|semaphore\|concurrency.*limit\|pLimit\|p-limit" glob="*.ts,*.js,package.json"
# → 一つのサービスが全リソースを消費 → 他も巻き添え
```
重大度: **INFO**

---

## R8: Health Check の不備

### P8.18: Shallow Health Check
依存サービスをチェックしない200返すだけのヘルスチェック。
```bash
# ヘルスチェックエンドポイント
Grep "health\|healthz\|readyz\|livez\|readiness\|liveness" path="server/" glob="*.ts"
# → DB接続/Redis接続/外部API疎通を確認しているか
# → 単に { status: 'ok' } を返すだけなら shallow
```
重大度: **WARNING**

### P8.19: Readiness vs Liveness の未分離
```bash
# 単一の /health しかない場合
Glob "server/api/health*"
Glob "server/routes/health*"
# → /healthz (liveness) と /readyz (readiness) を分けるべき
# → liveness: プロセス生存確認
# → readiness: リクエスト受付可能かの確認
```
重大度: **INFO**

---

## R9: Graceful Shutdown の欠如

### P8.20: シグナルハンドリングの未実装
```bash
Grep "SIGTERM\|SIGINT\|beforeExit\|graceful.*shutdown" glob="*.ts,*.js"
# → process.on('SIGTERM') が実装されていない場合、
#    デプロイ時にリクエスト処理中の接続が即断される
```
重大度: **WARNING**

### P8.21: 進行中リクエストの待機なし
```bash
Grep "server\.close\|app\.close\|httpServer\.close" glob="*.ts,*.js"
# → close 時に既存リクエストの完了を待つ drain ロジックがあるか
Grep "drain\|keepAliveTimeout\|closeAllConnections" glob="*.ts,*.js"
```
重大度: **WARNING**

---

## R10: N+1 クエリ

### P8.22: ループ内の DB クエリ
```bash
# for/forEach/map 内でDBクエリ
Grep "for.*\{" -A 10 path="server/" glob="*.ts"
# → ループ内に prisma. / db. / await が含まれるか

# 個別 findOne の連続
Grep "findUnique\|findFirst\|findOne" path="server/" glob="*.ts"
# → 同一ファイルで findMany に置換すべきパターン
```
重大度: **WARNING**

### P8.23: GraphQL の N+1
```bash
Grep "fieldResolver\|resolve\s*:" glob="*.ts,*.js"
Grep "dataloader\|DataLoader" glob="*.ts,*.js,package.json"
# → DataLoader なしの resolver は N+1 の温床
```
重大度: **WARNING**

---

## R11: 監視・可観測性の欠如

### P8.24: メトリクス収集なし
```bash
Grep "prometheus\|prom-client\|opentelemetry\|@opentelemetry\|dd-trace\|newrelic" glob="package.json"
Grep "histogram\|counter\|gauge\|meter" glob="*.ts,*.js"
# → メトリクスライブラリが使われていない = 障害検知不能
```
重大度: **WARNING**

### P8.25: 分散トレーシングなし
```bash
Grep "trace\|span\|propagat" glob="*.ts,*.js"
Grep "opentelemetry\|jaeger\|zipkin\|x-trace-id\|x-request-id" glob="*.ts,*.js,*.json"
# → マイクロサービス構成でトレーシングなし = デバッグ不能
```
重大度: **INFO**

### P8.26: 構造化ログの不使用
```bash
Grep "console\.log\|console\.error\|console\.warn" path="server/" glob="*.ts"
Grep "pino\|winston\|bunyan\|logger\.\w+\(" path="server/" glob="*.ts"
# → console.log が多くて構造化ロガーが少ない = 本番ログが使い物にならない
```
重大度: **INFO**

---

## R12: デプロイ・運用の罠

### P8.27: 環境間の差異 (Environment Parity)
```bash
# docker-compose で dev と prod の差異
Glob "docker-compose*.yml"
Glob "docker-compose*.yaml"
# → dev 用と prod 用の設定差異が大きいとバグの温床

# 環境依存のハードコード
Grep "localhost\|127\.0\.0\.1\|0\.0\.0\.0" path="server/" glob="*.ts"
# → 本番で動かないアドレスのハードコード
```
重大度: **WARNING**

### P8.28: データベースマイグレーションの安全性
```bash
# 破壊的マイグレーション
Grep "DROP TABLE\|DROP COLUMN\|ALTER.*DROP\|TRUNCATE" glob="*.sql,*.ts"
# → ロールバック不能な破壊的変更
```
重大度: **WARNING**

---

## 重要度判定ガイド

| 条件 | 重大度 |
|------|--------|
| データ消失・サービス全停止・セキュリティ侵害 | **CRITICAL** |
| 部分障害・性能劣化・運用困難 | **WARNING** |
| 将来的リスク・ベストプラクティス違反 | **INFO** |
