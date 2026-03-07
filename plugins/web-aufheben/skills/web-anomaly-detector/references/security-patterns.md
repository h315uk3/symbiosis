# L7: セキュリティ違和感パターン (Security Anomalies)

OWASP Top 10 2025 + API Security Top 10 2023 + 最新トレンド (2024-2025) から抽出。
grep/glob で検出可能なパターンに特化。

---

## S1: アクセス制御の欠陥 (OWASP A01:2025 — Broken Access Control)

### P7.1: 認可チェックの欠如
APIエンドポイントにユーザー権限チェックがない。
```bash
# サーバーAPI定義で認可ミドルウェアなし
Grep "defineEventHandler" path="server/api/" glob="*.ts"
# → getSession / requireAuth / assertRole 等が同一ファイルに無い場合は違和感
# 対比: 認可チェックのあるファイル
Grep "getSession\|requireAuth\|assertRole\|getServerSession" path="server/api/"
```
重大度: **CRITICAL**

### P7.2: IDOR (Insecure Direct Object Reference)
ユーザー入力のIDを直接DBクエリに使用。
```bash
# パスパラメータを直接DB検索に使用
Grep "params\.\w+.*findOne\|params\.\w+.*findUnique\|params\.\w+.*where" path="server/" glob="*.ts"
# → ユーザーが所有するリソースかの検証なし
```
重大度: **CRITICAL**

### P7.3: CORS 設定の緩さ
```bash
Grep "Access-Control-Allow-Origin.*\*" glob="*.ts,*.js,*.json"
Grep "cors.*origin.*true\|cors.*origin.*\*" glob="*.ts,*.js"
Grep "credentials.*true.*origin.*\*" glob="*.ts,*.js"
```
重大度: **WARNING**

### P7.4: SSRF (Server-Side Request Forgery) — 旧 A10:2021 統合
```bash
# ユーザー入力をURLとして使用
Grep "fetch\(.*req\.body\|fetch\(.*params\.\|fetch\(.*query\." path="server/" glob="*.ts"
Grep "\$fetch\(.*getQuery\|ofetch\(.*getQuery" path="server/" glob="*.ts"
# → URL のホワイトリスト検証なし
```
重大度: **CRITICAL**

---

## S2: セキュリティ設定ミス (OWASP A02:2025 — Security Misconfiguration)

### P7.5: デバッグモードの本番残留
```bash
Grep "debug\s*[:=]\s*true" glob="*.ts,*.js,*.json,*.yaml,*.yml"
Grep "NODE_ENV.*development\|NODE_ENV.*dev" path="server/" glob="*.ts"
Grep "devtools\s*[:=]\s*true" glob="nuxt.config.*"
Grep "sourcemap\s*[:=]\s*true" glob="*.config.*"
```
重大度: **WARNING**

### P7.6: 詳細エラーメッセージの本番露出
```bash
# スタックトレースをレスポンスに含める
Grep "stack.*trace\|\.stack\b" path="server/" glob="*.ts"
Grep "err\.message\|error\.message" path="server/api/" glob="*.ts"
# → 本番環境で内部情報がレスポンスに含まれる
```
重大度: **WARNING**

### P7.7: セキュリティヘッダーの欠如
```bash
# セキュリティヘッダー設定の有無
Grep "X-Content-Type-Options\|X-Frame-Options\|Strict-Transport-Security\|Content-Security-Policy" glob="*.ts,*.js,*.json"
# → 見つからない場合はヘッダー未設定
Grep "helmet\|security.*headers" glob="*.ts,*.js,package.json"
```
重大度: **WARNING**

### P7.8: デフォルトクレデンシャル
```bash
Grep "admin.*admin\|root.*root\|test.*test\|password.*password" glob="*.ts,*.js,*.json,*.yaml,*.env*"
Grep "default.*password\|default.*secret\|default.*key" glob="*.ts,*.js"
```
重大度: **CRITICAL**

---

## S3: サプライチェーン (OWASP A03:2025 — Software Supply Chain Failures)

### P7.9: ロックファイル不一致
```bash
# ロックファイルの存在確認
Glob "pnpm-lock.yaml"
Glob "package-lock.json"
Glob "yarn.lock"
# → 複数のロックファイルが共存 = パッケージマネージャ混在
# → ロックファイルなし = 再現性なし
```
重大度: **WARNING**

### P7.10: 危険な依存スクリプト
```bash
# postinstall / preinstall で任意コマンド実行
Grep "postinstall\|preinstall\|prepare\|prepublish" path="." glob="package.json"
# → curl / wget / sh / bash を含むスクリプトは危険
```
重大度: **WARNING**

### P7.11: バージョン固定なし
```bash
# package.json で ^ や ~ や * を使った緩いバージョン指定
Grep '"\^|"~|"\*' glob="package.json"
# → 意図しないバージョンアップでの破壊リスク
```
重大度: **INFO**

---

## S4: 暗号化の欠陥 (OWASP A04:2025 — Cryptographic Failures)

### P7.12: ハードコードされたシークレット
```bash
# API キー / トークン / パスワードのハードコード
Grep "(?i)(api[_-]?key|api[_-]?secret|access[_-]?token|auth[_-]?token|secret[_-]?key)\s*[:=]\s*['\"][^'\"]{8,}" glob="*.ts,*.js,*.json,*.yaml,*.env"
Grep "(?i)password\s*[:=]\s*['\"][^'\"]{4,}" glob="*.ts,*.js,*.json,*.yaml"
Grep "(?i)(sk[-_]live|pk[-_]live|sk[-_]test)" glob="*.ts,*.js"  # Stripe
Grep "AKIA[0-9A-Z]{16}" glob="*.ts,*.js,*.json,*.env"          # AWS
Grep "-----BEGIN (RSA |EC )?PRIVATE KEY-----" glob="*"          # 秘密鍵
Grep "ghp_[a-zA-Z0-9]{36}" glob="*.ts,*.js,*.json,*.env"       # GitHub PAT
Grep "xox[bpas]-[0-9a-zA-Z]+" glob="*.ts,*.js,*.json,*.env"    # Slack token
```
重大度: **CRITICAL**

### P7.13: 弱い暗号化アルゴリズム
```bash
Grep "createHash\(['\"]md5['\"]\)" glob="*.ts,*.js"
Grep "createHash\(['\"]sha1['\"]\)" glob="*.ts,*.js"
Grep "DES\b\|RC4\b\|ECB\b" glob="*.ts,*.js"
Grep "Math\.random\(\)" path="server/" glob="*.ts"  # 暗号用途は危険
```
重大度: **WARNING**

### P7.14: HTTP での機密データ送信
```bash
Grep "http://" path="server/" glob="*.ts"   # HTTPS でない外部通信
Grep "secure\s*:\s*false" glob="*.ts,*.js"  # Cookie の secure フラグなし
Grep "httpOnly\s*:\s*false" glob="*.ts,*.js" # httpOnly なし
```
重大度: **WARNING**

---

## S5: インジェクション (OWASP A05:2025 — Injection)

### P7.15: SQL インジェクション
```bash
# 文字列結合による SQL 構築
Grep "query\s*\(\s*[`'\"].*\$\{" path="server/" glob="*.ts"     # テンプレートリテラル
Grep "query\s*\(\s*['\"].*\+\s*" path="server/" glob="*.ts"     # 文字列結合
Grep "raw\s*\(\s*[`'\"].*\$\{" path="server/" glob="*.ts"       # Prisma raw query
Grep "execute\s*\(\s*[`'\"].*\$\{" path="server/" glob="*.ts"   # 直接実行
```
重大度: **CRITICAL**

### P7.16: NoSQL インジェクション
```bash
Grep "\$where\|\.find\(\{.*req\.\|\.findOne\(\{.*req\." path="server/" glob="*.ts"
Grep "\$gt\|\\$lt\|\$ne\|\$regex" path="server/" glob="*.ts"
# → ユーザー入力を直接 MongoDB クエリに渡す
```
重大度: **CRITICAL**

### P7.17: OS コマンドインジェクション
```bash
Grep "exec\s*\(" path="server/" glob="*.ts"          # child_process.exec
Grep "execSync\s*\(" path="server/" glob="*.ts"
Grep "spawn\s*\(.*shell\s*:\s*true" path="server/" glob="*.ts"
# Python
Grep "os\.system\s*\(" glob="*.py"
Grep "subprocess\.call\(.*shell\s*=\s*True" glob="*.py"
Grep "subprocess\.Popen\(.*shell\s*=\s*True" glob="*.py"
```
重大度: **CRITICAL**

### P7.18: XSS (Cross-Site Scripting)
```bash
# React
Grep "dangerouslySetInnerHTML" glob="*.tsx,*.jsx"
# Vue
Grep "v-html" glob="*.vue"
# 汎用
Grep "innerHTML\s*=" glob="*.ts,*.js,*.vue"
Grep "document\.write\s*\(" glob="*.ts,*.js"
Grep "\.html\s*\(" glob="*.ts,*.js"  # jQuery .html()
```
重大度: **CRITICAL**

### P7.19: eval 系の危険関数
```bash
# JavaScript / TypeScript
Grep "\beval\s*\(" glob="*.ts,*.js,*.vue"
Grep "new\s+Function\s*\(" glob="*.ts,*.js"
Grep "setTimeout\s*\(\s*['\"]" glob="*.ts,*.js"    # 文字列を渡す setTimeout
Grep "setInterval\s*\(\s*['\"]" glob="*.ts,*.js"   # 文字列を渡す setInterval
# Python
Grep "\beval\s*\(" glob="*.py"
Grep "\bexec\s*\(" glob="*.py"
Grep "compile\s*\(.*['\"]exec['\"]" glob="*.py"
```
重大度: **CRITICAL**

### P7.20: テンプレートインジェクション (SSTI)
```bash
Grep "render.*string\|template.*compile\|Handlebars\.compile\|ejs\.render" glob="*.ts,*.js"
# → ユーザー入力をテンプレートとしてコンパイル
```
重大度: **CRITICAL**

### P7.21: パストラバーサル
```bash
Grep "path\.join\(.*req\.\|path\.resolve\(.*req\." path="server/" glob="*.ts"
Grep "readFile.*req\.\|readFileSync.*req\." path="server/" glob="*.ts"
Grep "fs\.\w+\(.*params\." path="server/" glob="*.ts"
# → ユーザー入力をファイルパスに使用
```
重大度: **CRITICAL**

---

## S6: 安全でない設計 (OWASP A06:2025 — Insecure Design)

### P7.22: レート制限の欠如
```bash
# レート制限ミドルウェアの有無
Grep "rateLimit\|rate-limit\|throttle\|rateLimiter" glob="*.ts,*.js,package.json"
# → API エンドポイントにレート制限なし
```
重大度: **WARNING**

### P7.23: Mass Assignment
```bash
# リクエストボディを直接モデルに渡す
Grep "\.create\(.*req\.body\|\.update\(.*req\.body\|Object\.assign\(.*req\.body" path="server/" glob="*.ts"
Grep "\.create\(.*readBody\|\.update\(.*readBody" path="server/" glob="*.ts"
# → ホワイトリスト/DTO なしでユーザー入力を直接永続化
```
重大度: **WARNING**

---

## S7: 認証の欠陥 (OWASP A07:2025 — Authentication Failures)

### P7.24: JWT の不適切な実装
```bash
Grep "algorithm.*none\|alg.*none" glob="*.ts,*.js"           # none アルゴリズム
Grep "verify\s*:\s*false\|ignoreExpiration\s*:\s*true" glob="*.ts,*.js"
Grep "jwt\.decode\b" glob="*.ts,*.js"  # verify でなく decode のみ = 検証なし
```
重大度: **CRITICAL**

### P7.25: セッション管理の脆弱性
```bash
Grep "sameSite\s*[:=]\s*['\"]none['\"]" glob="*.ts,*.js"   # SameSite=None
Grep "maxAge\s*[:=]\s*\d{10,}" glob="*.ts,*.js"            # 極端に長いセッション有効期限
```
重大度: **WARNING**

---

## S8: 整合性の欠陥 (OWASP A08:2025 — Software/Data Integrity Failures)

### P7.26: 安全でないデシリアライゼーション
```bash
# JavaScript
Grep "JSON\.parse\s*\(" path="server/" glob="*.ts"  # 入力検証なしの parse
Grep "unserialize\|deserialize" path="server/" glob="*.ts"
# Python
Grep "pickle\.load\|pickle\.loads\|cPickle" glob="*.py"
Grep "yaml\.load\s*\(" glob="*.py"           # yaml.safe_load でない
Grep "marshal\.loads\|shelve\.open" glob="*.py"
```
重大度: **CRITICAL**

### P7.27: Subresource Integrity の欠如
```bash
# 外部 CDN スクリプトに integrity 属性がない
Grep "<script.*src=.*http" glob="*.html,*.vue"
# → integrity="sha384-..." が付いていないか確認
```
重大度: **INFO**

---

## S9: ログ・監視の欠陥 (OWASP A09:2025 — Security Logging and Alerting Failures)

### P7.28: 認証イベントのログ不足
```bash
# ログイン/ログアウト処理でログ出力がない
Grep "login\|signIn\|authenticate" path="server/" glob="*.ts"
# → 同一ファイルに logger / console.log / audit がないか確認
```
重大度: **WARNING**

### P7.29: 機密情報のログ出力
```bash
Grep "console\.log.*password\|console\.log.*token\|console\.log.*secret" glob="*.ts,*.js"
Grep "console\.log.*Authorization\|console\.log.*cookie" glob="*.ts,*.js"
Grep "logger.*password\|logger.*token\|logger.*secret" glob="*.ts,*.js"
```
重大度: **CRITICAL**

---

## S10: 例外処理の不備 (OWASP A10:2025 — Mishandling of Exceptional Conditions)

### P7.30: unhandledRejection / uncaughtException の放置
```bash
Grep "unhandledRejection\|uncaughtException" glob="*.ts,*.js"
# → process.on('unhandledRejection') が存在しなければ問題
# → 存在しても process.exit() を呼ばないなら問題
```
重大度: **WARNING**

### P7.31: 包括的 catch の乱用
```bash
Grep "catch\s*\(\s*\w*\s*\)\s*\{" -A 1 glob="*.ts"
# → catch 内が空 or console.log のみ → 例外を握り潰し
```
重大度: **WARNING**

---

## API セキュリティ固有 (OWASP API Security Top 10 2023)

### P7.32: BOLA (Broken Object Level Authorization)
```bash
# GET/PUT/DELETE で :id パラメータを使うが所有者チェックなし
Grep "getRouterParam\|params\.\w+Id\|params\.id" path="server/api/" glob="*.ts"
# → 同一ファイル内に userId / session / ownership の検証がないか
```
重大度: **CRITICAL**

### P7.33: 過剰なデータ公開
```bash
# DBオブジェクトをそのままレスポンスに返す
Grep "return.*findMany\|return.*findFirst\|return.*findUnique" path="server/api/" glob="*.ts"
# → select / omit / DTO 変換なしで全フィールド露出
```
重大度: **WARNING**

### P7.34: 無制限のリソース消費
```bash
# ページネーションなしの全件取得
Grep "findMany\s*\(\s*\)" path="server/" glob="*.ts"
Grep "find\s*\(\s*\{\s*\}\s*\)" path="server/" glob="*.ts"
# → take / limit / pagination なし
```
重大度: **WARNING**

---

## 最新トレンド (2024-2025)

### P7.35: LLM / AI 統合のセキュリティ
```bash
# ユーザー入力を直接プロンプトに埋め込み
Grep "prompt.*\$\{.*req\.\|prompt.*\$\{.*body\.\|prompt.*\$\{.*query\." path="server/" glob="*.ts"
Grep "messages.*role.*user.*content.*\$\{" path="server/" glob="*.ts"
# → サニタイズなしのプロンプトインジェクション脆弱性
# → system prompt と user input の境界が不明確
```
重大度: **CRITICAL**

### P7.36: MCP (Model Context Protocol) 設定の露出
```bash
Grep "mcp.*server\|mcpServers" glob=".mcp.json,*.json"
# → APIキーや認証情報が平文で含まれていないか
# → 不要なツールアクセス権限がないか
```
重大度: **WARNING**

### P7.37: .env ファイルの Git 追跡
```bash
# .gitignore に .env が含まれているか
Grep "\.env" glob=".gitignore"
# .env ファイルの存在確認
Glob "**/.env"
Glob "**/.env.local"
Glob "**/.env.production"
```
重大度: **CRITICAL**

### P7.38: Container セキュリティ
```bash
# Dockerfile で root ユーザー実行
Grep "^USER root" glob="Dockerfile*"
# USER 命令がない (= root で実行)
Grep "^USER " glob="Dockerfile*"   # → 存在しなければ root
# 特権モード
Grep "privileged\s*:\s*true" glob="docker-compose*.yml,*.yaml"
# Docker ソケットのマウント
Grep "/var/run/docker.sock" glob="docker-compose*.yml,*.yaml,Dockerfile*"
# latest タグの使用
Grep "FROM.*:latest" glob="Dockerfile*"
```
重大度: **WARNING**

### P7.39: CDN / Edge 設定ミス
```bash
# キャッシュ設定で認証付きレスポンスをキャッシュ
Grep "Cache-Control.*public.*max-age" path="server/" glob="*.ts"
# → 認証が必要なエンドポイントで public キャッシュ
Grep "s-maxage\|stale-while-revalidate" path="server/api/" glob="*.ts"
```
重大度: **WARNING**

---

## 設定の罠 (Configuration Traps)

### P7.40: Feature Flag の残骸
```bash
Grep "FEATURE_\|FF_\|feature[Ff]lag\|featureToggle\|isEnabled" glob="*.ts,*.js,*.vue"
# → 使われなくなった feature flag が残っている
# → 常に true/false の feature flag は技術的負債
```
重大度: **INFO**

### P7.41: 未使用の環境変数
```bash
# 定義された環境変数
Grep "^[A-Z_]+=\|export\s+[A-Z_]+=" glob=".env*,docker-compose*.yml"
# 使用されている環境変数
Grep "process\.env\.\|import\.meta\.env\.\|useRuntimeConfig" glob="*.ts,*.js,*.vue"
# → 定義済みだが未使用、または使用済みだが未定義
```
重大度: **INFO**

### P7.42: 依存関係の既知脆弱性
```bash
# package.json を検査対象として特定
Glob "**/package.json"
# → pnpm audit で脆弱性チェックを推奨
# → 最終更新が1年以上前の依存は要確認
```
重大度: **WARNING**
