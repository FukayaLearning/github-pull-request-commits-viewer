# Tasks

<!-- ============================================================
  タスク分解・実装（apply-change）・アーカイブ（archive-change）ルール
  1. 1サブタスク（チェックボックス1項目）＝ 1コミット（変更ファイル1〜5個程度、単独でビルド・既存テストが通る Green State）
  2. 機械的変更（フォーマッタ、Linter自動修正、マイグレーション生成、sed一括置換、パッケージ追加等）は手動のロジック変更とは別の独立したサブタスク（＝別コミット）に切り出すこと
  3. apply-change 実行時は、チェックボックス1項目の遂行都度 tasks.md の [x] 更新を含めて以下の規約で即座にコミットすること:
     <type>(<scope>): <サブタスクの要約>

     Why: <なぜこの変更が必要か（目的・背景）>
     What: <何を変更したか>

     Issue: #<Issue番号>
     Task: <サブタスクの識別子または名称>
     Verification: <ビルド・テスト成功を確認したコマンド>
     Executed-Command: <機械的変更の場合のみ、実行したコマンド全文を記載（手動変更時は "manual"）>
  4. すべてのチェックボックス項目の実装・コミットが完了したら、最後にプロジェクト全体のテストを実行すること
============================================================ -->

## 1. バックエンド・CLI表記の更新

- [x] 1.1 `server.py`（モジュールdocstring、`argparse` の `description`、起動時出力メッセージ）および `viewer_backend/__init__.py`（パッケージdocstring）のプロジェクト名称を `GitHub Pull Request Commits Viewer` へ更新する。検証: `python3 server.py --help` および `python3 -m unittest discover -s tests -v` がすべてパスすること。

## 2. フロントエンドUIとE2Eテストの更新

- [ ] 2.1 `static/index.html` の `<title>` と `.brand-title`、および `tests/test_e2e_cli.py` のタイトル検証アサーションを `GitHub Pull Request Commits Viewer` へ更新する。検証: `python3 -m unittest discover -s tests -v` がすべてパスすること。
- [ ] 2.2 `static/app.js` の `REVIEWED_STORAGE_KEY` を `"github-pr-viewer:reviewed-commits"` へ変更し、`loadReviewedMap()` に旧キー `"local-pr-viewer:reviewed-commits"` からの読み込み・新キーへの移行フォールバックを実装する。検証: `python3 -m unittest discover -s tests -v` がすべてパスし、`static/app.js` に構文エラーがないこと。

## 3. ドキュメント表記の更新

- [ ] 3.1 `README.md` のタイトル・説明表記および `AGENTS.md` のリポジトリ名・`openspec validate` コマンド例を新名称に合わせて更新する。検証: `python3 -m unittest discover -s tests -v` および `openspec validate rename-to-github-pr-commits-viewer --strict` がパスすること。

## Workflow follow-up

- `apply-change` で全サブタスクの実装・個別コミット完了後、プロジェクト全体のテストスイート（`python3 -m unittest discover -s tests -v`）を実行してすべてパスすることを確認する。
- 本変更は `.openspec.yaml` で `skip_specs: true` を設定し `usdm.md` / `specs/` をスキップしているため、`archive-change` 時は通常のアーカイブ手順（`openspec archive rename-to-github-pr-commits-viewer`）を実行する。
