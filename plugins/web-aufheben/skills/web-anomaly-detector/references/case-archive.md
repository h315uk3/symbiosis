# Case Archive — 違和感の実例集

実際のバグ修正・本番障害から抽出した事例。
各事例を Ghost/Fragile/Blind Spot カテゴリと L1-L9 レイヤーに分類。

---

## Ghost (動かないもの)

### Case G1: Ollama モデル ID 不一致 (2026-02)
- **Layer**: L1 (契約不一致) | **QAP**: CFR
- **症状**: embedding モデルが「未インストール」と表示される
- **原因**: routing config は `nomic-embed-text`、Ollama API は `nomic-embed-text:latest` を返す
- **修正**: `normalizeModelId()` で `:latest` サフィックスを正規化
- **検出クエリ**: `Grep "model.*[:=]" → API レスポンスの ID と突合`
- **教訓**: 外部サービスの ID 正規化は境界で必ず行う

### Case G2: WebSocket メッセージ欠落 (2026-02)
- **Layer**: L3 (状態同期バグ) | **QAP**: ESR
- **症状**: モデル pull の進捗が UI に表示されない
- **原因**: 重複チェックに `new Date().toISOString()` を使用。ミリ秒精度のため高速チャンクが同一タイムスタンプになり、最初の1件以降が全て無視された
- **修正**: タイムスタンプ比較 → オブジェクト参照比較
- **検出クエリ**: `Grep "Date.now()|toISOString()" → 一意キーとして使用`
- **教訓**: タイムスタンプは一意キーとして信頼できない (L9 P9.3)

### Case G3: Fire-and-Forget Pull (2026-02)
- **Layer**: L2 (サイレント失敗) | **QAP**: EHD
- **症状**: モデル pull ボタンを押しても進捗不明
- **原因**: `fetch(...).catch(() => {})` でエラーが消え、`stream: false` で進捗情報なし
- **修正**: `stream: true` + NDJSON パース + WebSocket ブロードキャスト
- **検出クエリ**: `Grep ".catch(() =>" → 空 catch の検出`
- **教訓**: catch ブロック内のエラー処理を必ず確認

---

## Fragile (壊れやすいもの) — 本番障害事例

### Case F1: CrowdStrike Falcon アップデート障害 (2024-07-19)
- **Layer**: L8 (信頼性リスク) | **QAP**: GSS, RPC
- **症状**: 世界中の Windows マシンが BSOD (約850万台)
- **原因**: カーネルレベルドライバの自動アップデートにカナリアリリースなし。テンプレート定義ファイル (Channel 291) のバリデーション不備で NULL ポインタ参照
- **grep 検出可能な前兆**:
  - `Grep "SIGTERM|graceful" glob="*.ts,*.js"` → GSS=0.0 (シャットダウン制御なし = ロールバック困難)
  - `Grep "zod|joi|validate|schema" path="server/" glob="*.ts"` → BVG 低下 (入力バリデーション欠如が根本原因)
- **教訓**: カーネル/インフラレベルの変更は段階的ロールアウト必須。バリデーション (L9 B3) の欠如が直接原因

### Case F2: Cloudflare 1.1.1.1 障害 (2024-10-04)
- **Layer**: L8 (信頼性リスク) | **QAP**: TCR
- **症状**: Cloudflare の DNS リゾルバ (1.1.1.1) が断続的に応答不能
- **原因**: BGP の設定変更がルーティングテーブルの不整合を引き起こし、Internal DNS バックエンドへの接続がタイムアウト。Circuit Breaker の欠如で障害が拡大
- **grep 検出可能な前兆**:
  - `Grep "timeout|AbortController" path="server/" glob="*.ts"` → TCR 低下 (タイムアウト未設定)
  - `Grep "circuitBreaker|opossum" glob="*.ts,package.json"` → RPC 低下 (CB 不在)
- **教訓**: TCR (Timeout Coverage Rate) の重要性。依存サービスの障害を想定した設計

### Case F3: GitHub Actions 暗号化キー漏洩 (2024-12)
- **Layer**: L7 (セキュリティ欠陥) | **QAP**: SEC
- **症状**: GitHub Actions のログにシークレットが平文で出力される脆弱性
- **原因**: ログマスキング処理のバイパスパス。特定のエンコーディング (Base64 等) でシークレットが出力されるとマスクが適用されない
- **grep 検出可能な前兆**:
  - `Grep "console.log.*password|logger.*token|log.*secret" glob="*.ts,*.js"` → P7.29 (機密情報のログ出力)
  - `Grep "AKIA|sk-|ghp_|xox" glob="*.ts,*.js,*.env"` → SEC > 0 (ハードコード秘密鍵)
- **教訓**: シークレットのマスキングは出力箇所全てで必要。SEC > 0 は即 CRITICAL

### Case F4: OpenAI API 障害 (2024-12-11)
- **Layer**: L8 (信頼性リスク) | **QAP**: RPC
- **症状**: ChatGPT と API が数時間ダウン
- **原因**: 新サービスデプロイ時の Kubernetes クラスター自動スケーリングが DNS 解決パフォーマンスを低下させ、カスケード障害に発展
- **grep 検出可能な前兆**:
  - `Grep "bulkhead|pLimit|concurrency.*limit" glob="*.ts,package.json"` → P8.17 (Bulkhead 欠如)
  - `Grep "retry.*backoff|exponential" glob="*.ts"` → P8.4 (バックオフなしリトライ)
- **教訓**: スケーリングイベント時の DNS 負荷を考慮。Cascading Failure 防止

### Case F5: Zoom 全面ダウン (2024-04-17)
- **Layer**: L5 (構造矛盾) + L8 (信頼性) | **QAP**: CSS, GSS
- **症状**: Zoom のビデオ/音声/チャットが全世界でダウン
- **原因**: ドメイン更新の管理プロセスの不備で DNS 設定が失効。設定が複数箇所に散在し、更新漏れが発生
- **grep 検出可能な前兆**:
  - `Grep "process\.env\.|import\.meta\.env\." glob="*.ts,*.js"` → CSS > 2.0 (同一設定の散在)
  - `Grep "localhost|127\.0\.0\.1" path="server/" glob="*.ts"` → P8.27 (ハードコードアドレス)
- **教訓**: インフラ設定の Single Source of Truth が必要

---

## Blind Spot (見えないリスク) — 暗黙知の罠

### Case B1: AWS S3 リージョンのデフォルト仮定 (2024 recurring)
- **Layer**: L9 (暗黙知の罠) | **QAP**: BVG
- **Pattern**: P9.14 (DNS・ホスト名の仮定)
- **症状**: S3 バケットのアクセスが特定リージョンから遅い/失敗する
- **原因**: `s3.amazonaws.com` のデフォルトが `us-east-1` を仮定。リージョン明示なしで他リージョンのバケットにアクセスし、307 リダイレクトが発生
- **教訓**: クラウドサービスのリージョンは常に明示。デフォルト仮定は危険

### Case B2: JavaScript Date コンストラクタの月 (perennial)
- **Layer**: L9 (暗黙知の罠) | **QAP**: ITCR
- **Pattern**: P9.4 (日付フォーマットの仮定)
- **症状**: `new Date(2024, 1, 1)` が1月ではなく2月を返す
- **原因**: JavaScript の月は 0-indexed (0=Jan, 11=Dec)。他言語から来た開発者が直感的に 1=Jan と仮定
- **検出クエリ**: `Grep "new Date\(\d+,\s*\d+" glob="*.ts,*.js"`
- **教訓**: L9 P9.4 — 日付ライブラリ (date-fns, dayjs) の使用を推奨

### Case B3: UTF-8 BOM によるパースエラー (2024 recurring)
- **Layer**: L9 (暗黙知の罠) | **QAP**: BVG
- **Pattern**: P9.5 (文字列の罠)
- **症状**: CSV/JSON のパースが特定ファイルでのみ失敗
- **原因**: Windows で保存されたファイルに UTF-8 BOM (0xEF 0xBB 0xBF) が付与。JSON.parse や CSV パーサーが先頭バイトを処理できない
- **検出クエリ**: `Grep "JSON.parse|readFile.*parse" path="server/"` → BOM ストリッピングの有無を確認
- **教訓**: ファイル入力は常に BOM を考慮。バリデーション (B3) の不備

### Case B4: Floating Point 通貨計算の丸め誤差 (perennial)
- **Layer**: L9 (暗黙知の罠) | **QAP**: ITCR
- **Pattern**: P9.10 (浮動小数点での金額計算)
- **症状**: 合計金額が1円/1セント合わない。複利計算で差額が蓄積
- **原因**: `0.1 + 0.2 = 0.30000000000000004`。float で金額を扱うと丸め誤差が蓄積
- **検出クエリ**: `Grep "price.*\*|amount.*\+|total.*[-+*/]" glob="*.ts,*.js"`
- **教訓**: 金額は整数 (セント単位) または Decimal ライブラリで扱う

---

## レイヤー別統計

| Layer | Cases | 最多原因 |
|-------|-------|---------|
| L1 契約不一致 | 1 | ID 正規化漏れ |
| L2 サイレント失敗 | 1 | 空 catch ブロック |
| L3 状態同期バグ | 1 | タイムスタンプ重複 |
| L5 構造矛盾 | 1 | 設定散在 |
| L7 セキュリティ | 1 | シークレットのログ出力 |
| L8 信頼性 | 4 | タイムアウト未設定 / Circuit Breaker 欠如 |
| L9 暗黙知 | 4 | 型変換 / 浮動小数点 / BOM / リージョン仮定 |

**観察**: L8 (信頼性) と L9 (暗黙知) の事例が最多。
大規模障害はほぼ全て Fragile/Blind Spot カテゴリに属する。
Ghost (動かないもの) は開発中に発見されやすいが、Fragile/Blind Spot は本番まで潜伏する。
