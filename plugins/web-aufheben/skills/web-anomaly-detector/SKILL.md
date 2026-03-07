---
name: web-anomaly-detector
description: コードの「違和感」を定量的に検出 — Ghost(動かない)/Fragile(壊れやすい)/Blind Spot(見えないリスク)を数値で立証する
---
<!-- auto-load: 違和感, anomaly, 矛盾, 不整合, audit, 健全性, ヘルスチェック, system-check, security-audit, セキュリティ監査, reliability, 知覚パフォーマンス, perceived-performance, UX監査, 体感速度, spinner, skeleton -->

# Web Anomaly Detector

コードの「違和感」を **3カテゴリ × 10レイヤー** で検出し、**定量パラメーター (QAP)** で立証する。
修正提案ではなく **発見・計測・分類** に特化。L10は **UI応答性 + 知覚パフォーマンス** を科学的根拠で検出。

## 起動条件

「違和感を探して」「矛盾がないか確認」「システム監査」「何かおかしい」等の意図表明時。

## 3カテゴリ × 10レイヤー

| Category | 意味 | Layer | 代表 QAP |
|----------|------|-------|----------|
| **Ghost** | 動かないもの | L1 契約不一致 | CFR (Contract Fulfillment Rate) |
| | | L2 サイレント失敗 | EHD (Error Handling Density) |
| | | L3 状態同期バグ | ESR (Event Subscription Ratio) |
| | | L4 死んだ機能 | HLR, RRR (Handler/Route Liveness) |
| | | L10a UI応答性 | ARR (Action-Response Rate) |
| | | L10b 知覚パフォーマンス | PPR (Perceived Performance Rate) |
| **Fragile** | 壊れやすいもの | L5 構造矛盾 | NCI, CSS (Naming/Config Consistency) |
| | | L6 リソース浪費 | — (N+1, 巨大ペイロード, 不要再計算) |
| | | L7 セキュリティ欠陥 | AGC, SEC (Auth Guard/Secret Exposure) |
| | | L8 信頼性リスク | TCR, RPC, MLS, GSS (Timeout/Resilience/Symmetry) |
| **Blind Spot** | 見えないリスク | L9 暗黙知の罠 | BVG, TSI, ITCR, DFS (Validation/Staleness/Coercion) |

## QAP (定量パラメーター)

4つの計測タイプで「何かおかしい」を数値化:

| Type | Healthy | Anomalous | 例 |
|------|---------|-----------|-----|
| Ratio | -> 1.0 | -> 0.0 | catch 処理率、認証保護率 |
| Presence | 0 | > 0 | ハードコード秘密鍵の数 |
| Symmetry | 0.0 | -> 1.0 | addEventListener vs removeEventListener |
| Scatter | 1.0 | > 1.5 | 同一設定値の散在度 |

**Composite Scores**: 各カテゴリの重み付きスコア → Overall (0.40 Ghost + 0.35 Fragile + 0.25 BlindSpot)
判定: >= 0.80 Healthy / 0.50-0.80 Warning / < 0.50 Critical
*(公式詳細: `references/quantitative-parameters.md` Composite Scores セクション)*

## 実行ワークフロー

```
1. SCOPE   — 対象範囲を特定 (全体 / フロー / git diff)
2. MEASURE — QAP パラメーターを計測 (grep/glob 並列)
3. VERIFY  — LLM で偽陽性除去 [デフォルト] ← 必ず試行する
4. TRIAGE  — adjusted QAP + confidence + 重要度で分類
5. REPORT  — confidence 付きレポートを出力
```

**LLM 検証がデフォルト**: LM Studio (localhost:1234) + Qwen3-Coder-Next を**常に第一選択**として試行。
`lm-studio-ensure.sh` がサーバー起動→モデルロードを自動化。
失敗時のみ grep-only に**自動フォールバック** (非ブロッキング)。
`--grep-only` フラグで明示的に v2.0 互換モードを強制することも可能。

### Step 1: SCOPE
```
- 全体監査: types/, api/, components/, config を全走査
- フロー監査: 特定ユーザーフローのファイル群
- 差分監査: git diff で変更ファイルのみ
```

### Step 2-3: MEASURE + SCAN (並列実行)
QAP 18パラメーターの計測と、10レイヤー別パターン検出を並列実行。
各レイヤーの grep/glob クエリ詳細は references/ を参照。

### Step 4: TRIAGE
```
CRITICAL: QAP < 0.50 / データ消失・セキュリティ・完全非動作
WARNING:  QAP 0.50-0.80 / 部分的非動作・一貫性欠如
INFO:     QAP >= 0.80 だが改善余地あり
```

### Step 5: REPORT
```markdown
## 違和感レポート: [対象]

### Scores
| Category | Score | Status |
|----------|-------|--------|
| Ghost | 0.72 | WARNING |
| Fragile | 0.85 | Healthy |
| Blind Spot | 0.45 | CRITICAL |
| **Overall** | **0.68** | **WARNING** |

### CRITICAL (N件)
| # | Cat | Layer | QAP | Location | Symptom | Root Cause |
|---|-----|-------|-----|----------|---------|------------|
| 1 | Ghost | L1 | CFR=0.6 | file:line | ... | ... |

### WARNING (N件) ...
### INFO (N件) ...
```

## 判断基準

**検出対象**: 動かない / エラー隠蔽 / データ断絶 / 操作後無反応 / 表示矛盾 / セキュリティ脆弱性 / 耐障害性欠如 / 暗黙知の罠 / **知覚パフォーマンス劣化** (スピナー依存・楽観更新欠如・深いリアクティビティ・遷移欠如・メインスレッドブロッキング)
**除外**: コードスタイル / テストカバレッジ / ドキュメント不備

## 参照

- `references/quantitative-parameters.md` — 18個の QAP 定義・計測方法・閾値・Composite Score・Confidence 統合
- `references/llm-verify.md` — LLM 検証パイプライン仕様 (LM Studio API, Qwen3-Coder-Next, バッチ処理)
- `references/prompts/` — カテゴリ別 LLM 検証プロンプト (ghost/fragile/blindspot)
- `references/detection-patterns.md` — L1-L6, L10a スタック非依存 grep/glob クエリ集
- `references/perceived-performance.md` — L10b: 知覚パフォーマンス (科学的根拠 + P10.13-P10.22 検出パターン)
- `references/security-patterns.md` — L7: OWASP 2025 + API Security 2023 (42パターン)
- `references/reliability-patterns.md` — L8: SRE/Chaos Engineering (28パターン)
- `references/implicit-knowledge.md` — L9: 暗黙知の罠 12ドメイン32パターン (時間/Unicode/金額/ネットワーク/DB/認証/並行処理等)
- `references/uiux-semiotics.md` — L10: UI/UX 違和感の多元的分析 (論理哲学/記号論/認知心理/行動経済 → 統合検査項目)
- `references/case-archive.md` — 実例集: 本番障害 (CrowdStrike/Cloudflare/OpenAI等) + 開発事例
