# 今後の改善ロードマップ（OpenSpec / USDM 化前準備）

本ドキュメントは、初回リリース（PR #1）のレビューで提示された運用面・UX面の改善提案を、次回 `/opsx-propose` 実行時にスムーズに USDM 要求仕様（上位要求・下位要求・仕様項目）へ落とし込めるよう整理した前準備メモです。

---

## 1. 巨大 Diff・多数ファイル変更の保護と分割表示

- **対象 Capability**: `git-pr-inspection-api`, `commit-review-webui`
- **要求**: ファイル数や差分サイズが大きいコミットでも、ブラウザがフリーズせず段階的に差分を確認できるようにする。
- **理由**: 巨大コミット（生成ファイル・ロックファイル・大規模リファクタ等）を一度に Diff2Html で描画すると、UI 応答性が著しく低下するため。
- **仕様候補**:
  - API (`/api/commits/<sha>/diff`) が Diff 総バイト数（`diff_size_bytes`）および大規模判定フラグ（例: `is_large: true`）を返却する、またはファイル単位での個別 Diff 取得エンドポイント（例: `GET /api/commits/<sha>/diff?path=<file>`）を提供する。
  - UI 側で閾値（例: 500KB 超または変更ファイル 50 件超）を超えた場合に警告バナーを表示し、全展開ではなくファイル単位のオンデマンド展開（またはプレーン表示への自動フォールバック）を選択できるようにする。

---

## 2. バイナリファイルおよび Rename / Copy の明確な表示

- **対象 Capability**: `git-pr-inspection-api`, `commit-review-webui`
- **要求**: バイナリファイルの変更、およびファイルのリネーム（Rename）・コピー（Copy）を通常のテキスト追加・削除と明確に区別して表示する。
- **理由**: バイナリやリネームの扱いが曖昧だと、レビュアーが「新規作成」「内容削除」「変更なし」と誤解する原因になるため。
- **仕様候補**:
  - バックエンドで `git show --numstat -z` および `git show --name-status -z -M -C` を使用し、リネーム元パス（`old_path`）・類似度（`similarity`）・バイナリフラグ（`binary: true`）を正確に抽出する（`{old => new}` 表記によるパス不一致を防止）。
  - フロントエンドの変更ファイル一覧および Diff ヘッダーに `Binary`、`Renamed (old → new)`、`Copied (src → dst)` 等の視覚的バッジを表示し、バイナリファイル選択時は「バイナリファイルのためテキスト差分はありません」と明示する。

---

## 3. `gh` 認証失敗時のユーザー向け案内・再試行 UX とエラー診断情報の詳細化

- **対象 Capability**: `git-pr-inspection-api`, `commit-review-webui`
- **要求**: GitHub CLI（`gh`）の未認証・オフライン等でローカル比較へフォールバックした理由をユーザーに分かりやすく提示し、再試行操作およびサブプロセスエラー時の詳細な診断情報を提供する。
- **理由**: 現状のフォールバックは安全に動作する一方、「なぜ PR 一覧が出ないのか」「どうすれば解消するか」や、`git`/`gh` エラー時の原因切り分けが画面から把握しづらいため。
- **仕様候補**:
  - `GET /api/prs` のフォールバック応答に理由コード（`fallback_code`: `"not_installed"` | `"unauthenticated"` | `"network_error"` | `"no_open_prs"` 等）と対処ヒントを含める。
  - UI 上に「ローカル比較モードで表示中」の理由バッジ／案内メッセージ（例: `gh auth login` の案内）と「PR 再取得（Retry）」ボタンを配置する。
  - `git` / `gh` サブプロセス失敗（HTTP 500 等）時に、エラー JSON へ構造化された診断情報（`detail`, `command`, `exit_code` 等、機密情報を含まない範囲）を付与し、UI のエラーバナーから折りたたみ展開して確認できるようにする。

---

## 次回 `/opsx-propose` 実行時の入力例

```text
/opsx-propose operational-hardening
openspec/roadmap.md に記載された3つの改善項目（巨大Diff保護・バイナリ/Rename表示・gh認証/エラー診断UX改善）を対象に、USDM要求仕様と実装タスクを作成してください。
```
