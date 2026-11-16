# Design

## Context

現在のリポジトリには、旧リモートリポジトリ名 `local-PR-and-MR-commits-viewer` に由来するプロジェクト名称（`Local PR and MR Commits Viewer` / `Local PR &amp; MR Commits Viewer`）および `localStorage` キー（`local-pr-viewer:reviewed-commits`）が複数箇所に残っている。変更の背景・対象範囲は `proposal.md` を参照（本変更は `skip_specs: true` のため `usdm.md` / `specs/` は作成しない）。

## Goals / Non-Goals

**Goals:**
- ドキュメント（`README.md`, `AGENTS.md`）、バックエンド CLI（`server.py`, `viewer_backend/__init__.py`）、Web UI（`static/index.html`, `static/app.js`）、E2Eテスト（`tests/test_e2e_cli.py`）のプロジェクト名称を `GitHub Pull Request Commits Viewer` へ統一する。
- `localStorage` キーの変更時に、旧キーへ保存されていた既存の「確認済み（Reviewed）」状態を失わずに引き継ぐ。
- ゼロ依存アーキテクチャおよび既存の API / CLI インターフェースを維持する。

**Non-Goals:**
- Python パッケージ名（`viewer_backend`）やディレクトリ構成の変更（既存 import パスや起動コマンドへの破壊的変更を避けるため）。
- 過去のアーカイブ済み OpenSpec 変更（`openspec/changes/archive/**`）の歴史的記録の書き換え。
- GitHub 以外のプラットフォーム対応や API 仕様・UI 機能の追加・削除。

## Decisions

1. **公式表示名の統一**
   - 採用案: `GitHub Pull Request Commits Viewer`（HTML上では `&` を含まないためエスケープ不要でそのまま表記）。
   - 代替案: `GitHub PR Commits Viewer` 等の略称。リポジトリ名 `github-pull-request-commits-viewer` との1対1の対応性と視認性を優先し、正式名称を採用した。

2. **`viewer_backend` パッケージ名の維持**
   - 採用案: モジュール名 `viewer_backend` は変更せず、`viewer_backend/__init__.py` の docstring のみ更新する。
   - 代替案: `github_pr_viewer_backend` 等へのリネーム。機能変更を伴わない名称見直しにおいて import パス変更のコスト・リスクが高いため据え置く。

3. **`localStorage` キーの移行方式**
   - 採用案: `static/app.js` で新キー `REVIEWED_STORAGE_KEY = "github-pr-viewer:reviewed-commits"` と旧キー `LEGACY_REVIEWED_STORAGE_KEY = "local-pr-viewer:reviewed-commits"` を定義し、`loadReviewedMap()` 時に新キーが未設定かつ旧キーに有効な JSON オブジェクトが存在する場合は旧キーを読み込んで新キーへ保存する（フォールバック移行）。
   - 代替案: キーを旧名称のまま据え置く案、または旧キーを切り捨てる案。名称統一の徹底と既存ユーザーの確認済み状態保護を両立するため、軽量なフォールバック移行を採用する。

4. **各サブタスクでの Green State 維持**
   - `tests/test_e2e_cli.py` が `static/index.html` のタイトル文字列を直接アサートしているため、`static/index.html` と `tests/test_e2e_cli.py` の更新は同一サブタスク（同一コミット）にまとめ、すべてのコミット単体で全テストがパスする状態を維持する。

## Risks / Trade-offs

- [ローカル環境の `git remote` URL 不一致] → 本リポジトリ内のファイル変更では各開発者の `.git/config` は更新されないため、必要に応じて `git remote set-url origin https://github.com/FukayaLearning/github-pull-request-commits-viewer.git` を実行する旨を案内する。
- [過去のロードマップやアーカイブとの表記差異] → アーカイブ（`openspec/changes/archive/**`）は当時の記録として保持し、現行ドキュメントのみを更新する。
