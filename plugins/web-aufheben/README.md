<div align="center">

[![Buy Me A Coffee](https://img.shields.io/badge/Buy_Me_A_Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/hitakay123u)
[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-EA4AAA?style=for-the-badge&logo=github-sponsors&logoColor=white)](https://github.com/sponsors/ohyesiamy)
[![Star](https://img.shields.io/badge/Star-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/ohyesiamy/web-anomaly-detector)

<br>

# Web Anomaly Detector

### コードの「違和感」を数値で暴く — Claude Code Skill

<br>

[![Version](https://img.shields.io/badge/version-3.4.0-8b5cf6?style=flat-square)](https://github.com/ohyesiamy/web-anomaly-detector/releases)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Skill-3b82f6?style=flat-square&logo=anthropic&logoColor=white)](https://claude.ai/code)
[![License](https://img.shields.io/badge/SACL--1.0-22c55e?style=flat-square)](LICENSE)
[![Patterns](https://img.shields.io/badge/140_patterns-f97316?style=flat-square)]()
[![QAP](https://img.shields.io/badge/18_parameters-ef4444?style=flat-square)]()

</div>

<br>

```mermaid
graph LR
    subgraph Input["あなたのコード"]
        A1["Vue / React / Svelte\nNode / Go / Rust / Python"]
    end

    subgraph Engine["Web Anomaly Detector"]
        direction TB
        B1["140 Patterns\n3 Categories × 10 Layers"] --> B2["18 QAP\nQuantitative Parameters"]
        B2 --> B3["LLM Verify\nQwen3-Coder-Next"]
    end

    subgraph Output["レポート"]
        C1["Overall: 0.64 WARNING\nCRITICAL 2 / WARNING 5\nconfidence 0.84"]
    end

    Input --> Engine --> Output

    style Input fill:#1e3a5f,stroke:#3b82f6,color:#e2e8f0
    style Engine fill:#2d1b69,stroke:#8b5cf6,color:#e2e8f0
    style Output fill:#4a1d1d,stroke:#ef4444,color:#e2e8f0
```

---

## なぜ必要か — 既存ツールの死角

```mermaid
graph TB
    subgraph Tools["既存ツール"]
        ESLint["ESLint\n構文 + ルール"]
        TS["TypeScript\n型の整合"]
        Test["テスト\n入出力の対応"]
    end

    subgraph Gap["検出できない領域"]
        G1["空の catch — エラー握り潰し"]
        G2["型と実装の乖離"]
        G3["認証なし API"]
        G4["mutation 後の再取得漏れ"]
        G5["addEventListener 解除忘れ"]
        G6["ハードコード API キー"]
        G7["月の 0-indexing バグ"]
    end

    subgraph WAD["Web Anomaly Detector"]
        W1["L2 EHD = 0.30"]
        W2["L1 CFR = 0.60"]
        W3["L7 AGC = 0.70"]
        W4["L10 ARR = 0.55"]
        W5["L8 MLS = 0.40"]
        W6["L7 SEC = 3"]
        W7["L9 ITCR = 5"]
    end

    Tools -.->|"見逃す"| Gap
    Gap -->|"数値化"| WAD

    style Tools fill:#374151,stroke:#6b7280,color:#9ca3af
    style Gap fill:#4a1d1d,stroke:#ef4444,color:#fca5a5
    style WAD fill:#14532d,stroke:#22c55e,color:#bbf7d0
```

**ESLint がパスし、TypeScript がコンパイルし、テストが通る** のに **本番で壊れる** コード。
それが本スキルの守備範囲。

---

## Quick Start

```bash
# 1. インストール (git clone するだけ)
git clone https://github.com/ohyesiamy/web-anomaly-detector.git \
  ~/.claude/skills/web-anomaly-detector

# 2. Claude Code に話しかけるだけ
```

```mermaid
graph LR
    U["「違和感を探して」"] --> Auto["スタック自動検出\nVue? React? Go?"]
    Auto --> Scan["140パターン\n並列スキャン"]
    Scan --> Report["スコア付き\nレポート出力"]

    style U fill:#1e3a5f,stroke:#3b82f6,color:#e2e8f0
    style Auto fill:#581c87,stroke:#a855f7,color:#f3e8ff
    style Scan fill:#1a4731,stroke:#22c55e,color:#e2e8f0
    style Report fill:#7c2d12,stroke:#f97316,color:#fff7ed
```

```
「このプロジェクトの違和感を探して」     → フルスキャン
「システム監査して」                     → フルスキャン
/web-anomaly-detector:score             → スコアのみ (高速)
/web-anomaly-detector:scan diff         → git diff のみ
「アウフヘーベンして」                   → 検出 + 修正まで一気通貫
```

---

## 検出例 — 4つの実例

### 例1: 空の catch ブロック (L2 サイレント失敗)

```mermaid
graph LR
    subgraph Before["現状"]
        B1["try { fetch('/api/orders') }\ncatch(e) { /* TODO */ }"]
    end
    subgraph Problem["問題"]
        P1["ネットワーク障害時\nユーザーに空画面\nエラーログなし\n誰も気づかない"]
    end
    subgraph Detect["検出結果"]
        D1["CRITICAL\nL2 EHD = 0.30\nconfidence: 0.92"]
    end

    Before --> Problem --> Detect

    style Before fill:#374151,stroke:#6b7280,color:#9ca3af
    style Problem fill:#4a1d1d,stroke:#ef4444,color:#fca5a5
    style Detect fill:#581c87,stroke:#a855f7,color:#f3e8ff
```

### 例2: 認証なし API (L7 セキュリティ)

```mermaid
graph LR
    subgraph API["10 個の API エンドポイント"]
        A1["GET /api/users ✓ 認証あり"]
        A2["POST /api/users ✓ 認証あり"]
        A3["GET /api/admin ✗ 認証なし"]
        A4["DELETE /api/users ✗ 認証なし"]
    end
    subgraph Score["検出結果"]
        S1["WARNING\nL7 AGC = 0.70\n3/10 エンドポイントが\n認証で保護されていない"]
    end

    API --> Score

    style A3 fill:#4a1d1d,stroke:#ef4444,color:#fca5a5
    style A4 fill:#4a1d1d,stroke:#ef4444,color:#fca5a5
    style Score fill:#7c2d12,stroke:#f97316,color:#fff7ed
```

### 例3: ボタンを押しても何も起きない (L10 UI応答性)

```mermaid
sequenceDiagram
    participant U as ユーザー
    participant UI as 画面
    participant API as サーバー

    U->>UI: 「削除」ボタンクリック
    UI->>API: DELETE /api/items/42
    API-->>UI: 200 OK
    Note over UI: ← ここで何も起きない
    Note over UI: loading 表示なし
    Note over UI: リスト更新なし
    Note over UI: 成功メッセージなし
    U->>U: 「...消えてない？」
    U->>UI: ページリロード
    Note over UI: やっとリストから消える

    rect rgb(74, 29, 29)
        Note over U,API: 検出: WARNING L10 ARR = 0.55
    end
```

### 例4: addEventListener の解除忘れ (L8 信頼性)

```mermaid
graph LR
    subgraph Open["開いた (onMounted)"]
        O1["addEventListener('resize')"]
        O2["addEventListener('scroll')"]
        O3["setInterval(poll, 5000)"]
    end
    subgraph Close["閉じた (onUnmounted)"]
        C1["なし"]
    end
    subgraph Leak["結果"]
        L1["メモリリーク\nMLS = 1.0\n(3 open / 0 close)"]
    end

    Open -->|"対称性"| Close -->|"不均衡"| Leak

    style Open fill:#14532d,stroke:#22c55e,color:#bbf7d0
    style Close fill:#4a1d1d,stroke:#ef4444,color:#fca5a5
    style Leak fill:#7c2d12,stroke:#f97316,color:#fff7ed
```

---

## 検出パイプライン — 2-Stage Architecture

```mermaid
graph TB
    subgraph S1["Stage 1: grep/glob — 金属探知機"]
        direction LR
        A["Agent A\nGhost\nL1-L4, L10"]
        B["Agent B\nFragile\nL5-L8"]
        C["Agent C\nBlind Spot\nL9"]
    end

    subgraph S2["Stage 2: LLM — 鑑定士"]
        direction LR
        D["LM Studio\nQwen3-Coder-Next\nlocalhost:1234"]
        E["confidence\nscoring"]
    end

    subgraph S3["Optional: DOM 検証"]
        F["agent-browser\nclick → snapshot diff"]
    end

    S1 -->|"候補リスト\n0 tokens"| S2
    S2 -->|"偽陽性除去"| G["REPORT\nOverall: 0.64 WARNING"]
    S1 -.->|"L10 候補あり\n+ アプリ起動中"| S3
    S3 -.->|"JSON report"| G

    style S1 fill:#1e3a5f,stroke:#3b82f6,color:#e2e8f0
    style S2 fill:#581c87,stroke:#a855f7,color:#f3e8ff
    style S3 fill:#374151,stroke:#6b7280,color:#9ca3af
    style G fill:#14532d,stroke:#22c55e,color:#bbf7d0
```

| Stage | 動作 | トークン消費 | 速度 |
|:---:|:---|:---:|:---:|
| **Stage 1** | 3 Explore エージェントが 140 パターンを並列 grep | **0** | ~5s |
| **Stage 2** | Qwen3-Coder-Next が偽陽性を除去 + confidence 付与 | **最小限** (ローカル) | ~20s |
| **DOM** | agent-browser が実際にクリック → accessibility diff | **0** | ~200ms/要素 |

- **LM Studio 自動化**: `lm-studio-ensure.sh` がサーバー起動→モデルロード→ヘルスチェックを**全自動**
- **フォールバック**: LM Studio 未インストール → 自動で grep-only (非ブロッキング)
- **データ送信先**: なし。全て localhost で完結

---

## 3カテゴリ × 10レイヤー

```mermaid
graph TB
    Q["何かおかしい..."] --> G["Ghost 👻\n動かないもの"]
    Q --> F["Fragile 🔨\n壊れやすいもの"]
    Q --> B["Blind Spot 🕳️\n見えないリスク"]

    G --> L1["L1 契約不一致\n型と実装のズレ"]
    G --> L2["L2 サイレント失敗\nエラー握り潰し"]
    G --> L3["L3 状態同期バグ\nemit/on 不一致"]
    G --> L4["L4 死んだ機能\nTODO ハンドラ"]
    G --> L10["L10 UI応答性\n操作後に無反応"]

    F --> L5["L5 構造矛盾\n設定の不整合"]
    F --> L6["L6 リソース浪費\nN+1, 巨大payload"]
    F --> L7["L7 セキュリティ\nOWASP 2025"]
    F --> L8["L8 信頼性\nSRE パターン"]

    B --> L9["L9 暗黙知の罠\n12ドメイン 32パターン"]

    style Q fill:#374151,stroke:#9ca3af,color:#f9fafb
    style G fill:#581c87,stroke:#a855f7,color:#f3e8ff
    style F fill:#7c2d12,stroke:#f97316,color:#fff7ed
    style B fill:#1e3a5f,stroke:#3b82f6,color:#eff6ff
    style L1 fill:#3b1f6e,stroke:#a855f7,color:#e9d5ff
    style L2 fill:#3b1f6e,stroke:#a855f7,color:#e9d5ff
    style L3 fill:#3b1f6e,stroke:#a855f7,color:#e9d5ff
    style L4 fill:#3b1f6e,stroke:#a855f7,color:#e9d5ff
    style L10 fill:#3b1f6e,stroke:#a855f7,color:#e9d5ff
    style L5 fill:#5c2610,stroke:#f97316,color:#fed7aa
    style L6 fill:#5c2610,stroke:#f97316,color:#fed7aa
    style L7 fill:#5c2610,stroke:#f97316,color:#fed7aa
    style L8 fill:#5c2610,stroke:#f97316,color:#fed7aa
    style L9 fill:#172554,stroke:#3b82f6,color:#bfdbfe
```

### Ghost — 動かないもの

ユーザーから見て「機能が動いていない」。コードはあるのに、期待通りに動作しない。

| Layer | 何を見つけるか | アナロジー | QAP |
|:---|:---|:---|:---|
| **L1** 契約不一致 | `interface User { email }` だが API は `mail` を返す | 地図にない道路 | **CFR** |
| **L2** サイレント失敗 | `catch(e) {}` — エラーが闇に消える | 電池の抜けた火災報知器 | **EHD** |
| **L3** 状態同期バグ | `emit('user:updated')` / `on('user:update')` | 留守番電話に話し続ける | **ESR** |
| **L4** 死んだ機能 | `onClick={handleDelete}` が TODO のみ | 商品のないボタン | **HLR, RRR** |
| **L10** UI応答性 | 削除押下→リスト更新なし→リロードで消える | 注文後に無言のウェイター | **ARR** |

### Fragile — 壊れやすいもの

今は動いている。変更・負荷・攻撃で容易に壊れる。

| Layer | 何を見つけるか | アナロジー | QAP |
|:---|:---|:---|:---|
| **L5** 構造矛盾 | base URL が `.env` と `config.ts` で違う | 2つの時計が違う時刻 | **NCI, CSS** |
| **L6** リソース浪費 | N+1 クエリ、100KB の未使用 import | 1品ずつレジに並ぶ | — |
| **L7** セキュリティ | 認証なし API、ハードコード秘密鍵、SQLi | 鍵をドアマットの下に | **AGC, SEC** |
| **L8** 信頼性リスク | タイムアウトなし、リトライなし、リソース解放忘れ | ブレーキのない車 | **TCR, RPC, MLS, GSS** |

### Blind Spot — 見えないリスク

コードは正しく「見える」が、暗黙の前提に依存している。

| Layer | 何を見つけるか | アナロジー | QAP |
|:---|:---|:---|:---|
| **L9** 暗黙知の罠 | `getMonth()` = 0始まり、`"👨‍👩‍👧".length` = 8 | 常識とコンピュータの溝 | **TSI, ITCR, BVG, DFS** |

> **L9 の 12 ドメイン**: 時間 / Unicode / 浮動小数点 / 金額 / ネットワーク / DB / 認証 / 並行処理 / ファイルシステム / 暗号 / 正規表現 / ブラウザ API

---

## 18 QAP — 全てを数値化する

```mermaid
graph LR
    subgraph Types["4つの計測タイプ"]
        R["Ratio\n何割がちゃんとしてるか\n→ 1.0 が健全"]
        P["Presence\nあってはいけないものの数\n= 0 が健全"]
        S["Symmetry\n開けたら閉めたか\n→ 0.0 が健全"]
        Sc["Scatter\n情報が散らばっていないか\n= 1.0 が健全"]
    end

    R --> R1["EHD = 0.30\ncatch 処理率 30%\n→ 70% がエラー握り潰し"]
    P --> P1["SEC = 3\nハードコード秘密鍵 3個"]
    S --> S1["MLS = 0.40\naddEventListener 5\nremoveEventListener 2"]
    Sc --> Sc1["CSS = 2.5\n同一 URL が\n4ファイルに散在"]

    style R fill:#14532d,stroke:#22c55e,color:#bbf7d0
    style P fill:#4a1d1d,stroke:#ef4444,color:#fca5a5
    style S fill:#1e3a5f,stroke:#3b82f6,color:#eff6ff
    style Sc fill:#78350f,stroke:#f59e0b,color:#fef3c7
```

<details>
<summary><b>全18パラメーター一覧</b></summary>

| # | QAP | 名前 | タイプ | Cat | 何を計測するか |
|:---:|:---:|:---|:---:|:---:|:---|
| 1 | **CFR** | 契約一致率 | Ratio | Ghost | 型定義 vs API 実装の一致率 |
| 2 | **EHD** | エラー処理率 | Ratio | Ghost | catch 内でエラーを適切に処理している率 |
| 3 | **ESR** | イベント購読率 | Ratio | Ghost | 定義イベント vs 実際の購読率 |
| 4 | **HLR** | ハンドラ実装率 | Ratio | Ghost | UI ハンドラが実装済み (TODO/空でない) の率 |
| 5 | **RRR** | ルート到達率 | Ratio | Ghost | 定義ルート vs リンクから到達可能な率 |
| 6 | **ARR** | UI応答率 | Ratio | Ghost | アクション後に visible response がある率 |
| 7 | **NCI** | 命名一貫性 | Ratio | Fragile | camelCase/snake_case の混在度 |
| 8 | **CSS** | 設定散在度 | Scatter | Fragile | 同一設定値が何箇所に散在しているか |
| 9 | **TCR** | タイムアウト率 | Ratio | Fragile | HTTP リクエストにタイムアウトが設定されている率 |
| 10 | **AGC** | 認証保護率 | Ratio | Fragile | API エンドポイントが認証で保護されている率 |
| 11 | **SEC** | 秘密鍵露出 | Presence | Fragile | ソースコード内のハードコード秘密鍵の数 |
| 12 | **RPC** | 耐障害率 | Ratio | Fragile | 外部呼び出しにリトライ/CB がある率 |
| 13 | **MLS** | リソース対称性 | Symmetry | Fragile | open/close ペアの対称性 (リーク検出) |
| 14 | **GSS** | シャットダウン | Presence | Fragile | SIGTERM/graceful shutdown の実装有無 |
| 15 | **TSI** | TODO放置率 | Ratio | BlindSpot | 90日以上放置された TODO の比率 |
| 16 | **ITCR** | 暗黙型変換 | Presence | BlindSpot | `==` / `!=` (非厳密比較) の使用数 |
| 17 | **BVG** | バリデーション欠落 | Ratio | BlindSpot | サーバー入力にバリデーションがある率 |
| 18 | **DFS** | 依存管理品質 | Ratio | BlindSpot | lockfile + pinned deps + 安全な scripts |

</details>

### Composite Score

```mermaid
graph LR
    subgraph Params["18 QAP"]
        G["Ghost\nCFR, EHD, ESR\nHLR, RRR, ARR"]
        F["Fragile\nNCI, CSS, TCR, AGC\nSEC, RPC, MLS, GSS"]
        B["Blind Spot\nTSI, ITCR\nBVG, DFS"]
    end

    G -->|"× 0.40"| O["Overall Score"]
    F -->|"× 0.35"| O
    B -->|"× 0.25"| O

    O --> H{">= 0.80"}
    O --> W{"0.50 - 0.80"}
    O --> C{"< 0.50"}

    H --> HL["Healthy ✓"]
    W --> WL["Warning ⚠"]
    C --> CL["Critical ✗"]

    style G fill:#581c87,stroke:#a855f7,color:#f3e8ff
    style F fill:#7c2d12,stroke:#f97316,color:#fff7ed
    style B fill:#1e3a5f,stroke:#3b82f6,color:#eff6ff
    style O fill:#374151,stroke:#9ca3af,color:#f9fafb
    style HL fill:#14532d,stroke:#22c55e,color:#bbf7d0
    style WL fill:#78350f,stroke:#f59e0b,color:#fef3c7
    style CL fill:#4a1d1d,stroke:#ef4444,color:#fca5a5
```

LLM 検証後の補正: `adjusted_QAP = raw_QAP × (0.5 + 0.5 × avg_confidence)`

---

## 出力例

```
## 違和感レポート: my-nuxt-app

### Mode
LLM-verified (Qwen3-Coder-Next / 47件検証)

### Scores
| Category    | Raw  | Adjusted | Status   |
|-------------|------|----------|----------|
| Ghost       | 0.72 | 0.68     | WARNING  |
| Fragile     | 0.85 | 0.83     | Healthy  |
| Blind Spot  | 0.45 | 0.41     | CRITICAL |
| **Overall** | **0.68** | **0.64** | **WARNING** |

### CRITICAL (2件)
| # | Cat | Layer | QAP      | Conf | Location               | Symptom              |
|---|-----|-------|----------|------|------------------------|----------------------|
| 1 | BS  | L9    | BVG=0.40 | 0.88 | server/api/user.ts:17  | バリデーションなし      |
| 2 | G   | L2    | EHD=0.30 | 0.92 | lib/api-client.ts:42   | 空 catch             |

### WARNING (5件)
| # | Cat | Layer | QAP      | Conf | Location               | Symptom              |
|---|-----|-------|----------|------|------------------------|----------------------|
| 1 | G   | L10   | ARR=0.55 | 0.85 | pages/items.vue:31     | 削除後リスト未更新     |
| 2 | F   | L7    | AGC=0.70 | 0.90 | server/api/admin.ts:5  | 認証ガードなし         |
| 3 | F   | L8    | MLS=0.40 | 0.78 | composables/useWS.ts:8 | listener 解除忘れ     |

### LLM Verification Summary
| Metric                 | Value |
|------------------------|-------|
| Total grep matches     | 127   |
| LLM verified           | 47    |
| True positives         | 38    |
| False positives removed | 9    |
| Avg confidence         | 0.84  |
```

---

## 140 検出パターン

```mermaid
pie title Detection Patterns by Layer
    "L7 Security — OWASP 2025" : 42
    "L9 Implicit Knowledge — 12 domains" : 32
    "L8 Reliability — SRE" : 28
    "L1-L6 General" : 28
    "L10 UI Responsiveness" : 10
```

### Tier 分類 — 検出精度の階層

```mermaid
graph LR
    subgraph A["Tier A — grep 高精度"]
        A1["catch(e) { }\nハードコード秘密鍵\n== 非厳密比較"]
    end
    subgraph B["Tier B — grep + LLM"]
        B1["意図的な空 catch？\n認証不要な public API？"]
    end
    subgraph C["Tier C — LLM 専用"]
        C1["状態管理の適切性\nUX フローの整合性"]
    end

    A -->|"高速・確実"| R["検出結果"]
    B -->|"候補→判定"| R
    C -->|"文脈理解"| R

    style A fill:#14532d,stroke:#22c55e,color:#bbf7d0
    style B fill:#78350f,stroke:#f59e0b,color:#fef3c7
    style C fill:#581c87,stroke:#a855f7,color:#f3e8ff
```

L10 の 10 パターンは **5A / 3B / 2C** — 半数が grep だけで高精度検出可能。

---

## コマンド一覧

| コマンド | 説明 | 速度 |
|:---|:---|:---:|
| `/web-anomaly-detector:scan` | 全体スキャン (3並列 + LLM検証) | ~30s |
| `/web-anomaly-detector:scan diff` | git diff のみ | ~10s |
| `/web-anomaly-detector:scan path:src/api` | 特定ディレクトリ | ~10s |
| `/web-anomaly-detector:scan --grep-only` | LLM 検証なし (v2互換) | ~5s |
| `/web-anomaly-detector:score` | QAP 数値のみ (軽量) | ~3s |
| `/web-anomaly-detector:score --verify` | QAP + LLM 検証 | ~15s |

自然言語でも起動:

```
「違和感を探して」「矛盾がないか確認」「システム監査」「何かおかしい」
```

---

## Aufheben Agent — 検出から修正まで

```mermaid
graph LR
    R["RECON\nStack検出"] --> D["DETECT\n3並列スキャン"]
    D --> T["TRIAGE\nAUTO/MANUAL/SKIP"]
    T --> F["FIX\nN並列修正"]
    F --> V["VERIFY\nBuild + Test"]
    V --> Rep["REPORT\nBefore → After"]

    style R fill:#1e3a5f,stroke:#3b82f6,color:#e2e8f0
    style D fill:#581c87,stroke:#a855f7,color:#f3e8ff
    style T fill:#78350f,stroke:#f59e0b,color:#fef3c7
    style F fill:#14532d,stroke:#22c55e,color:#bbf7d0
    style V fill:#7c2d12,stroke:#f97316,color:#fff7ed
    style Rep fill:#374151,stroke:#9ca3af,color:#f9fafb
```

```
「アウフヘーベンして」→ 検出→分類→並列修正→検証を一気通貫で実行
```

**安全装置**: `git stash` → `fix/aufheben-{timestamp}` ブランチ → ビルド失敗時 revert → 最大 20件/回

---

## パッシブ検出フック

```mermaid
graph LR
    Edit["ファイル編集"] -->|"PostToolUse:Edit"| Hook["passive-detect.sh"]
    Hook --> L2["L2 チェック\n空 catch 追加？"]
    Hook --> L7["L7 チェック\n秘密鍵ハードコード？"]
    L2 --> W["警告表示\n(非ブロッキング)"]
    L7 --> W

    style Edit fill:#374151,stroke:#6b7280,color:#9ca3af
    style Hook fill:#581c87,stroke:#a855f7,color:#f3e8ff
    style W fill:#78350f,stroke:#f59e0b,color:#fef3c7
```

編集するたびに **L2 (サイレント失敗)** と **L7 (セキュリティ)** を自動チェック。編集は止めない。

---

## 対応フレームワーク

```mermaid
graph TB
    subgraph FE["Frontend"]
        Vue["Vue / Nuxt 3-4"]
        React["React / Next.js"]
        Svelte["Svelte / Kit"]
        Angular["Angular"]
    end
    subgraph BE["Backend"]
        Node["Node / Express / Nitro"]
        Hono["Hono / Fastify / tRPC"]
        Python["FastAPI / Django"]
        Go["Go / Rust"]
    end
    subgraph Build["Build"]
        pnpm["pnpm / npm / yarn / bun"]
        cargo["cargo / go build / pip"]
    end

    FE & BE & Build --> Auto["自動検出\npackage.json / Cargo.toml\ngo.mod / requirements.txt"]

    style Auto fill:#14532d,stroke:#22c55e,color:#bbf7d0
```

スタック非依存。プロジェクト構成ファイルから自動検出してパターンを適応。

---

## LLM 検証 — 完全ローカル

```mermaid
graph LR
    subgraph Local["localhost (データ外部送信なし)"]
        direction TB
        LMS["LM Studio\nlocalhost:1234"]
        Model["Qwen3-Coder-Next\n自動ロード"]
        Script["lm-studio-ensure.sh\nサーバー + モデル自動管理"]
    end

    Grep["grep 候補"] --> Local --> Result["confidence 付き結果"]
    Local -.->|"未インストール時"| Fallback["grep-only\n自動フォールバック"]

    style Local fill:#1e3a5f,stroke:#3b82f6,color:#e2e8f0
    style Fallback fill:#374151,stroke:#6b7280,color:#9ca3af
```

---

## File Structure

```
web-anomaly-detector/
├── SKILL.md                        # エントリポイント (~100行)
├── ABSTRACT.md                     # 哲学的考察 — 違和感の認識論
├── .claude-plugin/plugin.json      # プラグインマニフェスト
├── marketplace.json                # マーケットプレイス情報
│
├── commands/
│   ├── scan.md                     # /scan — 全体スキャン + レポート
│   └── score.md                    # /score — QAP 数値のみ (軽量)
│
├── hooks/
│   ├── passive-detect.sh           # Edit 後の L2+L7 パッシブ検出
│   ├── lm-studio-ensure.sh         # LM Studio 自動管理
│   └── dom-verify.sh               # agent-browser DOM 検証
│
└── references/
    ├── quantitative-parameters.md  # 18 QAP 定義・公式・閾値
    ├── detection-patterns.md       # L1-L6, L10 パターン
    ├── uiux-semiotics.md           # L10: 哲学/記号論/認知心理/行動経済
    ├── security-patterns.md        # L7: OWASP 2025 (42 patterns)
    ├── reliability-patterns.md     # L8: SRE (28 patterns)
    ├── implicit-knowledge.md       # L9: 12 domains (32 patterns)
    ├── llm-verify.md               # LLM 検証パイプライン
    ├── prompts/                    # カテゴリ別 LLM 検証プロンプト
    └── case-archive.md             # 実例: 12件の本番障害
```

---

## Research

| Source | 貢献 |
|:---|:---|
| CK Metrics (Chidamber & Kemerer 1994) | CBO/WMC/RFC 複雑度閾値 |
| Shannon Entropy (2025 Springer) | 情報理論ベース異常検出 |
| OWASP Top 10 (2025) + API Security (2023) | セキュリティパターン・閾値 |
| Google SRE Handbook (2024) | 信頼性パターン・重大度 |
| Bayesian Defect Prediction (Fenton 2012) | 欠陥予測の統計モデル |

> **[違和感について — ひとつの哲学的考察](ABSTRACT.md)**: 感覚的確信の貧困、因果の幻影、生活世界の地盤、判断停止、止揚 — 「違和感」の認識論を8章で考察。

---

<div align="center">

<sub>Source Available Commercial License (SACL-1.0) — Personal use free / Commercial use requires license</sub>

<sub>語りえぬものを、数えられるものに変換する。</sub>

</div>
