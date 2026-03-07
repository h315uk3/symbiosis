# L9: 暗黙知の罠 (Implicit Knowledge Traps)

開発者が「当然正しい」と思い込んでいるが、実は間違っている仮定。
コードに明示されず、テストもされず、ドキュメントにも書かれない。
**気づかなければ必ずバグになる。**

grep/glob で「危険な仮定をしているコード」を検出する。

---

## T1: 時間・日付の罠

### P9.1: タイムゾーンの無視
「サーバーとクライアントは同じタイムゾーン」という仮定。
```bash
# new Date() をタイムゾーン指定なしで使用
Grep "new Date\(\)" glob="*.ts,*.js,*.vue"
# moment() / dayjs() をタイムゾーンなしで使用
Grep "moment\(\)|dayjs\(\)" glob="*.ts,*.js"
# → .toISOString() / .utc() / timezone 指定がないものが危険
# タイムゾーン対応の確認
Grep "timezone|tz\(|utc\(|\.toISOString\(\)" glob="*.ts,*.js"
```
重大度: **WARNING** (国際展開で CRITICAL)

### P9.2: 「1日 = 24時間」の仮定
DST (サマータイム) 切替日は 23h or 25h。
```bash
# 24時間 = 1日のハードコード
Grep "86400|24\s*\*\s*60\s*\*\s*60|24\s*\*\s*3600" glob="*.ts,*.js"
Grep "hours:\s*24|HOURS_PER_DAY" glob="*.ts,*.js"
# → 日付計算に固定秒数を使っている = DST バグ
```
重大度: **WARNING**

### P9.3: タイムスタンプの一意性
「同一ミリ秒のイベントは存在しない」という仮定。
```bash
# Date.now() や toISOString() を一意キーとして使用
Grep "Date\.now\(\)|\.toISOString\(\)" glob="*.ts,*.js"
# → Map のキーや重複チェックに使われていないか
Grep "Map.*Date\.now\|Set.*Date\.now\|===.*timestamp" glob="*.ts,*.js"
```
重大度: **WARNING** (高頻度イベントで CRITICAL)

### P9.4: 日付フォーマットの仮定
「MM/DD/YYYY は世界共通」「月は12個」「年は4桁」。
```bash
# ハードコードされた日付フォーマット
Grep "MM/DD|DD/MM|YYYY-MM-DD" glob="*.ts,*.js"
Grep "\.split\(['\"][-/]['\"]" glob="*.ts,*.js"
# → Intl.DateTimeFormat / locale 対応がないもの
Grep "Intl\.DateTimeFormat|toLocaleDateString|locale" glob="*.ts,*.js"
```
重大度: **INFO** (国際化時 WARNING)

---

## T2: 文字列・Unicode の罠

### P9.5: 「文字列の長さ = 文字数」の仮定
絵文字・結合文字・サロゲートペアで `.length` が不正確。
```bash
# .length で文字数を判定
Grep "\.length\s*[><=!]+\s*\d" glob="*.ts,*.js,*.vue"
# → 入力バリデーションで .length を使っている箇所
# 正しい方法: [...str].length, Intl.Segmenter, grapheme-splitter
Grep "Intl\.Segmenter|\[\.\.\.str\]\.length|grapheme" glob="*.ts,*.js"
```
重大度: **WARNING** (ユーザー入力バリデーションで CRITICAL)

### P9.6: 大文字小文字変換の単純化
「toUpperCase() は可逆」「1文字は1文字に変換される」。
```bash
# toLowerCase/toUpperCase でケース比較
Grep "\.toLowerCase\(\)\s*===|\.toUpperCase\(\)\s*===" glob="*.ts,*.js"
# → トルコ語の i/I 問題、ドイツ語の ß → SS
# locale 指定の確認
Grep "toLocaleLowerCase|toLocaleUpperCase|localeCompare" glob="*.ts,*.js"
```
重大度: **INFO** (多言語対応時 WARNING)

### P9.7: 正規表現の \w と ASCII 仮定
`\w` は ASCII のみ。非ラテン文字を排除する。
```bash
# \w を名前・テキスト検証に使用
Grep '\\w\+|\\w\*|\[a-zA-Z\]' glob="*.ts,*.js"
# → ユーザー名バリデーションに [a-zA-Z] は不十分
# Unicode 対応: /\p{L}/u
Grep '\\p\{L\}|\\p\{Script' glob="*.ts,*.js"
```
重大度: **WARNING** (国際ユーザー向けで CRITICAL)

---

## T3: 名前・個人情報の罠

### P9.8: 名前のバリデーション過剰制限
「名前は英字のみ」「姓と名の2パート」「空白を含まない」。
```bash
# 名前の厳しすぎるバリデーション
Grep "name.*\[a-zA-Z\]|name.*[A-Z][a-z]" glob="*.ts,*.js,*.vue"
# 名前を firstName/lastName に強制分割
Grep "firstName|lastName|first_name|last_name" glob="*.ts,*.js,*.vue"
# → 単一名 (モノニム)、4パート以上の名前、ハイフン名に対応できない
```
重大度: **INFO** (国際サービスで WARNING)

### P9.9: メールアドレスの誤ったバリデーション
「@ の前は英数字のみ」「+ は無効」「大文字不可」。
```bash
# メール正規表現のバリデーション
Grep "email.*regex|email.*pattern|email.*match\(" glob="*.ts,*.js"
# → RFC 5321/5322 に準拠しているか
# 簡易チェック: /.+@.+\..+/ 程度が安全
# 最善: ライブラリ使用 (zod email, validator.js)
Grep "z\.string\(\)\.email\(\)|isEmail\(" glob="*.ts,*.js"
```
重大度: **WARNING**

---

## T4: 数値・通貨の罠

### P9.10: 浮動小数点での金額計算
`0.1 + 0.2 !== 0.3` — IEEE 754 の根本問題。
```bash
# 金額を float/number で計算
Grep "price\s*\*|amount\s*\*|total\s*\+|cost\s*[-+*/]" glob="*.ts,*.js"
Grep "parseFloat.*price|parseFloat.*amount" glob="*.ts,*.js"
# → Decimal / BigInt / 整数(セント単位) を使うべき
Grep "Decimal|BigInt|dinero|currency\.js|big\.js" glob="*.ts,*.js,package.json"
```
重大度: **CRITICAL** (金融系で必須)

### P9.11: 通貨の仮定
「通貨は2桁小数」「通貨記号は1文字」「$ = USD」。
```bash
# 小数点以下2桁のハードコード
Grep "\.toFixed\(2\)" glob="*.ts,*.js"
# → JPY は小数なし、BHD は3桁、暗号通貨は8桁以上
# Intl.NumberFormat の使用確認
Grep "Intl\.NumberFormat|toLocaleString.*currency" glob="*.ts,*.js"
```
重大度: **WARNING** (多通貨対応時 CRITICAL)

### P9.12: 整数の安全範囲
JavaScript の `Number.MAX_SAFE_INTEGER` は 2^53-1。DB の bigint やスノーフレーク ID で溢れる。
```bash
# ID を number 型で扱っている
Grep "parseInt\(.*id|Number\(.*id" glob="*.ts,*.js"
# → Snowflake ID (Twitter/Discord) は 64bit → string で扱うべき
Grep "BigInt|bigint|\.toString\(\).*id" glob="*.ts,*.js"
```
重大度: **WARNING**

---

## T5: ネットワーク・HTTP の罠

### P9.13: 「リクエストは必ず1回届く」の仮定
ネットワークは at-most-once でも at-least-once でもない。
```bash
# 冪等性チェックなしの書き込み API
Grep "POST|PUT|PATCH" path="server/api/" glob="*.ts"
# → 同一リクエストの再送で二重処理されないか
# 冪等性キーの使用確認
Grep "idempotency|idempotent|request-id|X-Request-Id" glob="*.ts,*.js"
```
重大度: **WARNING** (決済・注文系で CRITICAL)

### P9.14: DNS・ホスト名の仮定
「localhost は常に 127.0.0.1」「DNS は不変」「内部ネットワークは安全」。
```bash
# ハードコードされた IP/ホスト名
Grep "127\.0\.0\.1|localhost|0\.0\.0\.0" path="server/" glob="*.ts,*.js"
Grep "10\.\d+\.\d+\.\d+|192\.168\.\d+" path="server/" glob="*.ts,*.js"
# → 環境変数化されていないネットワークアドレス
```
重大度: **WARNING**

### P9.15: Content-Type の信頼
「Content-Type ヘッダーは正確」「ファイル拡張子 = MIME タイプ」。
```bash
# ファイルアップロードでの Content-Type 信頼
Grep "content-type|mimetype|mime_type" path="server/" glob="*.ts,*.js"
# → マジックバイト検証なしのファイル受付
Grep "file-type|magic-bytes|mmmagic" glob="*.ts,*.js,package.json"
```
重大度: **WARNING** (ファイルアップロード機能で CRITICAL)

---

## T6: ファイルシステムの罠

### P9.16: パス区切りの仮定
「/ は常にパス区切り」— Windows は `\`。
```bash
# ハードコードされたパス区切り
Grep "path.*'/'|split\(['\"]/" path="server/" glob="*.ts,*.js"
# → path.join / path.resolve を使うべき
Grep "path\.join|path\.resolve|path\.sep" path="server/" glob="*.ts,*.js"
```
重大度: **INFO** (クロスプラットフォーム時 WARNING)

### P9.17: ファイル名の安全性
「ファイル名に特殊文字は含まれない」「長さ制限は十分」。
```bash
# ユーザー入力をファイル名に直接使用
Grep "writeFile.*req\.|createWriteStream.*user" path="server/" glob="*.ts,*.js"
# → パストラバーサル (../) やヌル文字インジェクション
# サニタイズの確認
Grep "sanitize.*filename|slugify|path\.basename" glob="*.ts,*.js"
```
重大度: **CRITICAL** (セキュリティ — L7 にも関連)

---

## T7: データベースの罠

### P9.18: AUTO_INCREMENT の連続性
「ID は連続する」「ID は常に増加する」「欠番はない」。
```bash
# ID の連続性に依存するロジック
Grep "id\s*\+\s*1|nextId|lastId\s*\+" glob="*.ts,*.js"
Grep "ORDER BY id|sort.*\bid\b" glob="*.ts,*.js"
# → ギャップ、ロールバック、レプリケーションで仮定が崩れる
```
重大度: **WARNING**

### P9.19: トランザクション分離の誤解
「READ COMMITTED で十分」「2つの SELECT は同じ結果を返す」。
```bash
# トランザクション制御
Grep "transaction|BEGIN|COMMIT|ROLLBACK" path="server/" glob="*.ts,*.js,*.sql"
# → 分離レベルの明示的設定がない = デフォルト依存
Grep "isolation|SERIALIZABLE|REPEATABLE READ|READ COMMITTED" path="server/" glob="*.ts,*.js"
```
重大度: **WARNING** (競合状態が起きうるデータで CRITICAL)

### P9.20: NULL の三値論理
「NULL = NULL は true」— SQL では NULL = NULL は UNKNOWN。
```bash
# NULL 比較のアンチパターン
Grep "=\s*NULL|!=\s*NULL|<>\s*NULL" glob="*.sql,*.ts,*.js"
# → IS NULL / IS NOT NULL を使うべき
Grep "IS NULL|IS NOT NULL|COALESCE|IFNULL|NULLIF" glob="*.sql,*.ts,*.js"
```
重大度: **WARNING**

---

## T8: 認証・認可の罠

### P9.21: クライアント側の認可チェック
「フロントで非表示にすれば十分」。
```bash
# フロント側のみの権限チェック (サーバー側がない)
Grep "v-if.*admin|v-if.*role|isAdmin|hasPermission" glob="*.vue,*.jsx,*.tsx"
# → 同じ API エンドポイントにサーバー側チェックがあるか
Grep "requireRole|checkPermission|authorize|isAdmin" path="server/" glob="*.ts,*.js"
# → フロントにあってサーバーにない = 認可バイパス
```
重大度: **CRITICAL**

### P9.22: JWT の誤った信頼
「JWT は暗号化されている」— JWT は署名のみ、ペイロードは Base64。
```bash
# JWT ペイロードに機密情報
Grep "jwt\.sign.*password|jwt\.sign.*secret|jwt\.sign.*ssn" glob="*.ts,*.js"
# → ペイロードに機密データを含めてはいけない
# alg: none の脆弱性
Grep "algorithms.*none|verify.*algorithms" glob="*.ts,*.js"
```
重大度: **CRITICAL**

### P9.23: セッション固定の見落とし
「ログイン後もセッションID は同じでよい」。
```bash
# ログイン処理
Grep "login|authenticate|signIn" path="server/" glob="*.ts,*.js"
# → ログイン成功後にセッション再生成があるか
Grep "regenerate|destroy.*create|newSession" path="server/" glob="*.ts,*.js"
```
重大度: **WARNING**

---

## T9: ページネーション・検索の罠

### P9.24: OFFSET ページネーションの前提
「データは変わらない」— ページ間でデータが挿入/削除されると重複/欠落する。
```bash
# OFFSET ベースのページネーション
Grep "OFFSET|skip\s*:|\.skip\(" path="server/" glob="*.ts,*.js"
# → カーソルベース (cursor/keyset) が安全
Grep "cursor|after:|before:|lastId|nextCursor" path="server/" glob="*.ts,*.js"
```
重大度: **WARNING** (大規模データで CRITICAL)

### P9.25: 検索入力のサニタイズ欠如
「検索クエリは安全」— SQL/NoSQL/Elasticsearch インジェクション。
```bash
# 検索クエリの直接使用
Grep "search.*req\.query|q.*req\.query|keyword.*req" path="server/" glob="*.ts,*.js"
# → パラメータバインディングの確認
Grep "parameterized|prepared|bind|placeholder|\$\d" path="server/" glob="*.ts,*.js"
```
重大度: **CRITICAL** (L7 にも関連)

---

## T10: キャッシュの罠

### P9.26: キャッシュの一貫性仮定
「キャッシュされたデータは最新」「TTL 内は安全」。
```bash
# キャッシュ設定
Grep "cache|Cache|ttl|maxAge|stale" glob="*.ts,*.js"
# → cache invalidation のロジックがあるか
Grep "invalidate|purge|bust|revalidate|stale-while" glob="*.ts,*.js"
# → write-through / write-behind 戦略の有無
```
重大度: **WARNING**

### P9.27: Cache-Control の誤設定
「no-cache = キャッシュしない」— 実際は「再検証なしでは使わない」。
```bash
# Cache-Control ヘッダー設定
Grep "Cache-Control|cache-control|s-maxage|no-store|no-cache|private|public" path="server/" glob="*.ts,*.js"
# → 機密データに public キャッシュを設定していないか
# → API レスポンスに適切な Cache-Control があるか
```
重大度: **WARNING** (機密データで CRITICAL)

---

## T11: 並行処理の罠

### P9.28: 「シングルスレッドだから安全」
Node.js はシングルスレッドだが非同期I/Oで競合状態は起きる。
```bash
# read-modify-write パターン (非アトミック)
Grep "await.*get.*await.*set|await.*find.*await.*update" path="server/" glob="*.ts,*.js"
# → 2つの await 間でデータが変更される可能性
# アトミック操作の確認
Grep "atomic|compareAndSwap|findAndModify|\.inc\(|\.update\(" path="server/" glob="*.ts,*.js"
```
重大度: **WARNING** (高並行で CRITICAL)

### P9.29: Promise.all の部分失敗
「Promise.all は全部成功するか全部失敗する」— 1つ失敗で全部 reject、他は放置。
```bash
# Promise.all の使用
Grep "Promise\.all\(" glob="*.ts,*.js"
# → Promise.allSettled の方が安全な場合が多い
Grep "Promise\.allSettled\(" glob="*.ts,*.js"
# → Promise.all 内の個別エラーハンドリングがないか確認
```
重大度: **WARNING**

---

## T12: 環境・デプロイの罠

### P9.30: 環境変数の存在仮定
「環境変数は常にセットされている」。
```bash
# 環境変数のデフォルト値なし使用
Grep "process\.env\.\w+[^?|]" path="server/" glob="*.ts,*.js"
Grep "import\.meta\.env\.\w+[^?|]" glob="*.ts,*.js,*.vue"
# → ?? / || でデフォルト値を設定しているか
# → 起動時のバリデーション (zod env, envalid) があるか
Grep "envalid|createEnv|z\.string\(\)|env.*schema" glob="*.ts,*.js"
```
重大度: **WARNING**

### P9.31: ファイルシステムの書き込み可能性
「一時ファイルはいつでも書ける」— コンテナの read-only FS、Lambda の /tmp 制限。
```bash
# ファイル書き込み
Grep "writeFile|writeFileSync|createWriteStream" path="server/" glob="*.ts,*.js"
# → /tmp 以外への書き込み、サイズ制限の考慮
# → サーバーレス環境では永続化に S3/GCS 等を使うべき
```
重大度: **WARNING** (サーバーレスで CRITICAL)

### P9.32: 「ローカルで動いたから本番でも動く」
環境差異: OS、Node バージョン、メモリ、ネットワーク、DNS。
```bash
# Node.js バージョン指定
Grep "engines.*node|\.nvmrc|\.node-version|\.tool-versions" glob="package.json,.nvmrc,.node-version,.tool-versions"
# → バージョン指定がない = 環境差異バグの温床
# Docker の使用確認
Glob "Dockerfile" OR Glob "docker-compose.yml"
```
重大度: **INFO**

---

## 重要度判定ガイド

| 条件 | 重大度 |
|------|--------|
| データ破壊・セキュリティ侵害・金銭損失 | **CRITICAL** |
| 特定条件で不正動作・データ不整合 | **WARNING** |
| 将来的リスク・国際化時の問題 | **INFO** |

## QAP パラメーターとの対応

| QAP | 検出する暗黙知の罠 |
|-----|-------------------|
| B1 (TSI) | 放置された TODO = 解決されない暗黙の問題 |
| B2 (ITCR) | P9.5 (文字列長), P9.10 (浮動小数点), P9.12 (整数範囲) |
| B3 (BVG) | P9.9 (メール), P9.15 (Content-Type), P9.25 (検索), P9.30 (環境変数) |
| B4 (DFS) | P9.32 (環境差異) — バージョン未固定が暗黙知依存を生む |
