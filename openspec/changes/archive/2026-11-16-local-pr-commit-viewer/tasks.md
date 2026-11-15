# Tasks

## 1. バックエンド基盤とGit/PR情報・コミット解析APIの実装

- [x] 1.1 [S01-03-02, S01-03-03] `viewer_backend/parser.py` と単体テスト `tests/test_parser.py` を作成し、コミットメッセージ本文から `Issue:`, `Task:`, `Why:`, `What:`, `Executed-Command:`, `Verification:` を正規表現で抽出する関数および変更種別（`Executed-Command` が `"manual"` 以外の時は `command`、テスト時は `test`、それ以外は `manual`）判定ロジックを実装する（検証: `python3 -m unittest tests/test_parser.py` がパスすること）。
- [x] 1.2 [S01-01-01, S01-01-02, S01-02-01, S01-02-02] `viewer_backend/git_service.py` と単体テスト `tests/test_git_service.py` を作成し、リポジトリ名・現在ブランチ・ブランチ一覧取得（非Git時はエラー送出）および `gh pr list` 連携（未認証・オフライン・PR 0件時のローカル比較フォールバック付き）を実装する（検証: `python3 -m unittest tests/test_git_service.py` がパスすること）。
- [x] 1.3 [S01-03-01, S01-04-01, S01-04-02] `viewer_backend/git_service.py` に `base..head` 範囲の時系列コミット一覧取得と、指定コミットSHAの変更ファイル統計（`--numstat`）およびUnified Diff取得（`ignore_whitespace=true` 時の `-w` 対応含む）を追加し、テストを拡充する（検証: `python3 -m unittest tests/test_git_service.py` がパスすること）。
- [x] 1.4 [S01-01-01, S01-02-01, S01-03-01, S01-04-01, S03-01] Python標準ライブラリ `http.server.ThreadingHTTPServer` を用いた `server.py` とAPI統合テスト `tests/test_server_api.py` を作成し、`GET /api/repo-info`, `GET /api/prs`, `GET /api/commits`, `GET /api/commits/<sha>/diff` および `static/` 配信を実装する（検証: `python3 -m unittest tests/test_server_api.py` がパスすること）。

## 2. フロントエンドUI（3ペイン構成・ビルドレスWeb UI）の実装

- [x] 2.1 [S02-01-01, S02-01-02] `static/index.html`, `static/style.css`, `static/app.js` の3ペイン基本骨格とヘッダー（リポジトリ・ブランチ表示、PRドロップダウン選択、および `base` / `head` ブランチ直接指定による非同期コミット一覧切り替え）を実装する（検証: サーバー経由で `/` を取得し、ヘッダーDOM要素と `/api/repo-info`・`/api/prs` 連携スクリプトが正しく構成されていることを確認する）。
- [x] 2.2 [S02-02-01, S02-02-02, S02-02-03, S02-02-04] 左ペイン（Commit Menu）に時系列コミット一覧、変更種別バッジ（🤖 Command / ✍️ Manual / ✅ Test）とOpenSpecタスク表示、`j`/`k` および `↑`/`↓` キーによる即時切り替え、`r` キーおよびチェックボックスによる `localStorage` 永続化付き「確認済み（Reviewed）」進捗管理を実装する（検証: `static/app.js` のキーボードイベント・`localStorage` 制御と左ペイン描画をテスト検証する）。
- [x] 2.3 [S02-03-01, S02-03-02, S02-04-01, S02-04-02, S02-04-03] メインペイン上部のコミットサマリカード（`Why` / `What` / `Task` / `Verification` と `Executed-Command` 等幅強調表示）および下部の変更ファイル一覧（クリックで該当ファイルDiffへスクロール移動）とDiff2HtmlによるSplit/Unified切替・空白無視（`ignore_whitespace`）切替対応Diffビューアを実装する（検証: コミット選択時に `/api/commits/<sha>/diff` が呼び出され、サマリカード・ファイル一覧・Split/Unified切替・空白無視トグルが機能することを検証する）。

## 3. CLI起動オプションとエンドツーエンド検証の整備

- [x] 3.1 [S03-01, S03-02] `server.py` に `--repo` / `--port` 引数および `REPO_PATH` / `PORT` 環境変数による設定機能と `README.md` の起動手順を追加し、テスト用コミット履歴を用いたE2E検証テストを実行する（検証: `python3 -m unittest discover -s tests -v` および `python3 server.py --help` が正常終了すること）。

## Workflow follow-up

- `apply-change` で全サブタスクの実装・個別コミット完了後、プロジェクト全体のテストスイート（`python3 -m unittest discover -s tests -v`）を実行してすべてパスすることを確認する。
- `archive-change` 実行時、完了して閉じるタスク（`- [x]`）に対応する `usdm.md` 内の各仕様（`[Sxx-yy-zz]`）について、要件のレビュー・実装・テストの完了状態に応じたUSDM仕様ラベルのチェック（`□□□` → `■□□` レビュー済み / `■■□` 実装済み / `■■■` テスト済み）を入れて `usdm.md` を更新・コミットしてからアーカイブする。
