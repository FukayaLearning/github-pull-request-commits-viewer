# Proposal

## Why

リモートリポジトリ名が `local-PR-and-MR-commits-viewer` から `github-pull-request-commits-viewer` へ変更された。現状のコードベース、Web UI、CLIメッセージ、およびドキュメントには旧名称の「Local PR and MR Commits Viewer」が残っており、本ツールが実際には GitHub CLI (`gh`) を用いた GitHub Pull Request を主対象としている実態とも乖離している。リポジトリ名とプロジェクト表示名を統一し、利用者と開発者の混乱を防ぐため、関連表記を一括で見直す。

## What Changes

- プロジェクトの公式名称を **GitHub Pull Request Commits Viewer**（リポジトリスラッグ: `github-pull-request-commits-viewer`）へ統一する。
- ドキュメント（`README.md`、`AGENTS.md`）内のプロジェクト名表記および検証コマンド例を更新する。
- バックエンド CLI / サーバー起動メッセージ（`server.py`、`viewer_backend/__init__.py`）の名称表記を更新する。
- フロントエンド UI（`static/index.html` の `<title>` および `.brand-title`）の表示名を更新する。
- フロントエンドの `localStorage` キー（`static/app.js` の `REVIEWED_STORAGE_KEY`）を新名称に合わせて整理し、旧キーに保存済みの「確認済み（Reviewed）」状態が失われないよう読み込み時のフォールバック移行を設ける。
- E2Eテスト（`tests/test_e2e_cli.py`）のタイトル検証アサーションを更新し、新規名称での起動・表示を検証する。

## Capabilities

### New Capabilities

なし（本変更はプロジェクト名称・ドキュメント・表示文字列の見直しであり、機能仕様の追加はないため `.openspec.yaml` に `skip_specs: true` を設定）。

### Modified Capabilities

なし（既存の API / Web UI 仕様の振る舞いは変更しない）。

## Impact

- 影響ファイル: `README.md`, `AGENTS.md`, `server.py`, `viewer_backend/__init__.py`, `static/index.html`, `static/app.js`, `tests/test_e2e_cli.py`
- 後方互換性:
  - Python パッケージ名（`viewer_backend`）およびエンドポイント（`/api/*`）、CLI オプション（`--repo`, `--port`, `--host`）は変更しないため、既存の起動スクリプトや API クライアントへの破壊的変更はない。
  - ブラウザの `localStorage` キー変更に対しては旧キー（`local-pr-viewer:reviewed-commits`）からの読み込みフォールバックを実装し、既存の確認済みチェック状態を保持する。
- 運用面: ローカル開発環境の `git remote` URL（`origin`）が旧リポジトリ名のままになっている場合は、必要に応じて `git remote set-url origin` での更新を案内する。
