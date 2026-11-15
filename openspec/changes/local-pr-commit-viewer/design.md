# Design

## Context

`proposal.md` に示した背景と `usdm.md` / `specs/` の要求仕様に基づき、ローカルのGitリポジトリおよびGitHub CLI（`gh`）と連携してコミット単位の差分・目的・実行コマンドを高速に閲覧するWebアプリケーションを設計する。
ローカル開発環境（Ubuntu標準Python、WSL2、Windows Python）において、仮想環境の構築やパッケージインストール（`pip install` / `npm install`）、Dockerコンテナへの認証情報引き渡しといったオーバーヘッドを一切排除し、単一コマンドで即座に起動できる軽量アーキテクチャを採用する。

## Goals / Non-Goals

**Goals:**
- Python 3標準ライブラリ（`http.server.ThreadingHTTPServer`, `urllib.parse`, `subprocess`, `json`, `re`, `pathlib`, `argparse`, `unittest`）のみでバックエンドAPIおよび静的ファイル配信を実現する。
- フロントエンドをビルドレスな静的ファイル群（`static/index.html`, `static/app.js`, `static/style.css`）で構成し、軽量な `diff2html` を用いてSplit / Unified切替およびシンタックスハイライト付きDiff描画を実現する。
- `git` / `gh` サブプロセス呼び出し時の引数安全性（シェルを経由しないリスト渡し）と、`gh` 未認証・オフライン時のローカルブランチ比較へのシームレスなフォールバックを保証する。
- 1サブタスク＝1コミットの粒度で実装を進められるモジュール分割（Git/PRデータ取得・メタデータ解析ロジックとHTTPルーティングの分離）とする。

**Non-Goals:**
- GitHub APIトークンの独自管理やOAuth認証フローの実装（既存の `gh` CLI認証状態をそのまま利用する）。
- Web UI上からの `git commit`、`git rebase`、PRマージ等の書き込み操作（読み取り・レビュー専用に特化する）。
- Node.js / Vite / Webpack 等のフロントエンドバンドルツールチェーンの導入。

## Decisions

### 1. バックエンド基盤: Python 3 標準ライブラリ (`http.server`) の採用
- **決定**: 外部フレームワーク（FastAPI / Flask / Express）やDockerコンテナを使用せず、Python 3標準ライブラリの `http.server.ThreadingHTTPServer` + `SimpleHTTPRequestHandler` 拡張でAPIと静的配信を統合する。
- **理由**:
  - `pip install` が不要となり、UbuntuやWindowsの標準Python環境で起動時間0.1秒未満・メモリ消費十数MBで即動作する。
  - ホスト上の `git` 設定（`.gitconfig`、SSH鍵）や `gh auth` の認証状態をそのままサブプロセスが継承できるため、Dockerマウント時の `safe.directory` エラーやトークン注入の煩雑さを完全に回避できる。
- **代替案**:
  - *Docker + Go*: 単一コンテナ化は可能だが、`git` / `gh` バイナリ同梱によるイメージ肥大化、ホストの `~/.config/gh` マウントやUID不一致による権限問題が生じるため不採用。
  - *FastAPI / Node.js (Hono)*: `uv` や `npm` による依存パッケージ導入が必要となるため、ゼロ依存要件に対してオーバースペックとして不採用。

### 2. フロントエンド構成: ビルドレス Vanilla JS (ES Modules) + Diff2Html
- **決定**: React / Vite 等のビルド工程を省き、ネイティブ ES Modules (`static/app.js`) とCSS Grid/Flexboxによる3ペインレイアウト、および `Diff2HtmlUI`（CDN読み込み＋オフライン時フォールバック用プレーンDiff表示）を採用する。
- **理由**:
  - 状態管理の対象が「選択中のPR/ブランチ」「コミット配列」「選択中コミットSHA」「表示モード（Split/Unified・空白無視）」「`localStorage` のReviewed辞書」と明確であり、Vanilla JSで200〜300行程度で明快かつ高速に記述できる。
  - 選択コミット切り替え時にDOMの部分更新のみを行うため、`j` / `k` キー連打時にもフレーム落ちなく動作する。
- **代替案**:
  - *React + Vite + Tailwind*: 開発・実行時にNode.jsとビルドステップが必須となり、リポジトリの軽量性を損なうため不採用。
  - *Monaco Diff Editor*: バンドルサイズが大きく（数MB〜十数MB）、初期ロードが重いため不採用。

### 3. Git操作およびコミットメタデータ抽出のモジュール設計
- **決定**:
  - `viewer_backend/git_service.py`: `subprocess.run(..., shell=False, capture_output=True, text=True, encoding="utf-8", errors="replace")` を用いて `git` / `gh` コマンドを安全に実行する。
    - コミット一覧は `git log --reverse --format=... <base>..<head>`（ヌル文字 `\x00` / 制御文字区切り）で一括取得し、本文中の改行や記号でパースが壊れないようにする。
    - コミット単位Diffは `git show --patch --numstat <sha>`（空白無視時は `-w` 追加）から変更ファイル統計（追加・削除行数）とUnified Diffを抽出する。
  - `viewer_backend/parser.py`: コミットメッセージ本文から正規表現で `Task:`, `Why:`, `What:`, `Executed-Command:`, `Verification:`（およびOpenSpecタスク表記 `[Sxx-yy-zz]` 等）を抽出し、変更種別（`command` / `test` / `manual`）を判定する純粋関数を提供する。
- **理由**:
  - パーサーとGitサービスをHTTPハンドラ（`server.py`）から分離することで、Python標準の `unittest` で単体テストを高速かつ確実に実行できる。

## Risks / Trade-offs

- **[Risk] コミットメッセージ内に区切り文字が含まれることによる `git log` パース崩れ** → **Mitigation**: `git log --format` のフィールド区切りに `%x1f`（Unit Separator）、レコード区切りに `%x1e`（Record Separator）を使用し、任意のマルチライン本文や記号を安全に分割する。
- **[Risk] `gh` CLI未導入環境やオフライン環境でのエラー** → **Mitigation**: `shutil.which("gh")` および `subprocess` の終了コード・タイムアウト（5秒）をハンドリングし、失敗時は例外を送出せず `{ "prs": [], "fallback": true, "reason": "..." }` を返してUI側でローカルブランチ選択モードをデフォルト表示する。
- **[Risk] 巨大コミットやバイナリ変更を含むDiffによるブラウザ描画遅延** → **Mitigation**: Diff文字列のサイズ上限（例: 500KB超の場合は警告表示＋個別ファイル展開）を設け、UIフリーズを防止する。
- **[Risk] 不正なリファレンス文字列によるコマンドインジェクションやオプション誤認** → **Mitigation**: `shell=False` を徹底し、`base` / `head` / `sha` パラメータが `-` で始まらないことおよび許容文字パターン（英数字・記号 `._/-~^`）であることをバリデーションする。

## Migration Plan

1. 新規アプリケーションのため既存データの移行は不要。
2. `server.py`, `viewer_backend/`, `static/`, `tests/` を追加し、`python3 -m unittest discover -s tests` で全単体・API統合テストをパスさせる。
3. ロールバックが必要な場合は該当ディレクトリ・ファイルを削除するだけで環境への副作用は残らない。
