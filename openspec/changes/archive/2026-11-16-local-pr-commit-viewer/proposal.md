# Proposal

## Why

GitHubのPull Request画面（Files changed）は全コミット合算の差分を確認するには適しているが、OpenSpecのように「1タスク＝1コミット」で粒度を揃えて履歴を積み上げた開発スタイルでは、コミット間の画面遷移が重く、前後の文脈や「どのタスクに対応するコミットか」「コマンドによる機械的な一括変更か手動実装か」を連続して追跡・レビューすることが困難である。この課題を解決するため、外部パッケージ依存ゼロのPython 3標準ライブラリとビルドレスなWebフロントエンド（Vanilla JS + Diff2Html）を組み合わせ、ローカルのGitリポジトリおよびGitHub CLI（`gh`）と直接連携して1画面（3ペイン構成）でコミット単位の差分・目的・実行コマンドを瞬時に切り替えながら検査できる軽量ローカル実行Webアプリケーション（Local PR and MR Commits Viewer）を構築する。

## What Changes

- **ゼロ依存ローカルAPIサーバーの追加**: Python 3標準ライブラリ（`http.server`, `subprocess`, `json`, `re`, `urllib.parse`）のみを用い、ローカルの `git` および `gh` コマンドを実行してリポジトリ情報、オープンPR一覧、構造化コミット履歴、コミット単位のUnified Diffを返すHTTPサーバーを実装する。
- **コミットメタデータ・Git Trailers自動パーサーの追加**: コミットメッセージ本文から `Task:`, `Why:`, `Executed-Command:`, `Verification:` 等のトレーラーおよびOpenSpecタスク情報を正規表現で抽出し、変更種別バッジ（コマンド一括変更・手動実装・テスト追加等）を判定できるようにする。
- **3ペイン構成のビルドレスWeb UIの追加**:
  - **ヘッダー（ターゲット選択）**: カレントリポジトリ名・ブランチ名の表示、およびオープンPR選択または比較元ベースブランチ（`main` 等）の直接指定UI。
  - **左ペイン（Commit Menu）**: 時系列コミット一覧、変更種別バッジ表示、`j`/`k` キーおよび上下矢印キーによる即時コミット切り替え、`localStorage` を用いたコミットSHA単位の「確認済み（Reviewed）」チェック進捗管理。
  - **中央・右ペイン（Commit Context & Diff Viewer）**: コミットの目的（Why/What）・OpenSpecタスク・実行コマンド全文の強調サマリカード、変更ファイルツリー、およびDiff2HtmlによるSplit（左右分割）/ Unified（統合）・空白無視（`-w`）切替対応のシンタックスハイライト付きDiffビューア。
- **即時起動CLIエントリポイントの追加**: 任意のローカルGitリポジトリパスを引数（`--repo`）または環境変数で指定し、`python3 server.py` の1コマンドでサーバー起動からブラウザ閲覧まで完結する起動スクリプトを整備する。

## Capabilities

### New Capabilities
- `git-pr-inspection-api`: ローカルGitリポジトリおよび `gh` CLIと連携し、リポジトリ情報、PR一覧（未認証・未作成時のローカルブランチ比較フォールバック含む）、Git Trailers解析済みコミット一覧、およびコミット単位の変更ファイル統計・Unified Diffを提供するバックエンドAPI機能
- `commit-review-webui`: 3ペインレイアウトでPR/ブランチ選択、バッジ付きコミット一覧とキーボード高速ナビゲーション、`localStorage` によるレビュー進捗管理、コミット文脈カード、およびSplit/Unified切替対応Diffビューアを提供するフロントエンドUI機能

### Modified Capabilities

## Impact

- **Backend (`server.py` / `viewer_backend/`)**: Python 3標準ライブラリのみで新規実装（`pip install` 不要、Ubuntu標準 `python3` およびWindows Python対応）。ローカルの `git` CLI（必須）および `gh` CLI（任意・フォールバックあり）をサブプロセス呼び出しする。
- **Frontend (`static/`)**: `index.html`, `app.js`, `style.css` によるビルドレス構成（`npm install` 不要）。シンタックスハイライトおよびSplit/Unified Diffレンダリングに軽量アセット（`diff2html`）を利用する。
- **Documentation & Agent Rules (`README.md`, `AGENTS.md`)**: プロジェクト構成・起動方法およびAIエージェント向けの開発・コミット規約（1サブタスク＝1コミット、Git Trailers規約）を定義する。
