# git-pr-inspection-api Specification

## Purpose

ローカルのGitリポジトリおよびGitHub CLI（`gh`）をPython 3標準ライブラリのみで呼び出し、リポジトリ状態、オープンPR一覧、Git Trailers解析済みの構造化コミット履歴、およびコミット単位のUnified DiffをフロントエンドへJSON APIとして提供する。

## Requirements

### Requirement: リポジトリ情報およびブランチ一覧の取得API
**USDM**: R01-01
システムは `GET /api/repo-info` エンドポイントを提供し、対象ローカルGitリポジトリのリポジトリ名、現在のチェックアウトブランチ名、デフォルトベースブランチ候補、およびブランチ一覧をJSON形式で返却しなければならない（SHALL）。対象ディレクトリが有効なGitリポジトリでない場合はエラーステータスを返却しなければならない（SHALL）。

#### Scenario: [S01-01-01] 有効なGitリポジトリの情報取得
- **WHEN** クライアントが有効なGitリポジトリを対象として `GET /api/repo-info` を要求する
- **THEN** サーバーはHTTP 200でリポジトリ名、現在のブランチ名、デフォルトベースブランチ候補（`main` または `master` 等）、およびローカル・リモートブランチ一覧を含むJSONを返却する

#### Scenario: [S01-01-02] 非Gitディレクトリ指定時のエラー応答
- **WHEN** 対象ディレクトリが有効なGitリポジトリではない状態で `GET /api/repo-info` が要求される
- **THEN** サーバーはHTTP 400または500ステータスとともにエラー理由を含むJSONオブジェクトを返却する

### Requirement: オープンPR一覧の取得とローカル比較フォールバックAPI
**USDM**: R01-02
システムは `GET /api/prs` エンドポイントを提供し、`gh pr list` を用いてオープンPR一覧を取得しなければならない（SHALL）。`gh` CLIが未導入・未認証またはPRが存在しない場合でもエラー停止せず、ローカルブランチ比較へフォールバック可能な応答を返却しなければならない（SHALL）。

#### Scenario: [S01-02-01] GitHub CLI連携によるオープンPR一覧の取得
- **WHEN** `gh` CLIが利用可能かつ認証済みの環境でクライアントが `GET /api/prs` を要求する
- **THEN** サーバーは各PRの `number`, `title`, `headRefName`, `baseRefName` を含むJSON配列を返却する

#### Scenario: [S01-02-02] GitHub CLI未認証またはPR未作成時のフォールバック応答
- **WHEN** `gh` CLIが未導入・未認証・オフライン、またはオープンPRが0件の状態で `GET /api/prs` が要求される
- **THEN** サーバーはHTTP 200でフォールバック状態フラグ、空のPR配列、およびローカル比較用のデフォルト `base` / `head` ブランチ候補を含むJSONを返却する

### Requirement: コミット一覧の取得とGit Trailersメタデータの構造化抽出API
**USDM**: R01-03
システムは `GET /api/commits?base=<base>&head=<head>` エンドポイントを提供し、指定範囲のコミット一覧を時系列で取得するとともに、コミットメッセージ本文から `Issue:`, `Task:`, `Why:`, `What:`, `Executed-Command:`, `Verification:` を正規表現で抽出し、変更種別分類を付与して返却しなければならない（SHALL）。

#### Scenario: [S01-03-01] 指定ブランチ範囲のコミット一覧取得
- **WHEN** クライアントが `GET /api/commits?base=main&head=HEAD` を要求する
- **THEN** サーバーは `main..HEAD` 範囲の各コミットのSHA、短縮SHA、件名、本文、作成者、日時を含むJSON配列を時系列順で返却する

#### Scenario: [S01-03-02] コミットメッセージからのGit Trailers抽出
- **WHEN** コミットメッセージ本文に `Issue:`, `Task:`, `Why:`, `What:`, `Executed-Command:`, `Verification:` のいずれかが含まれるコミットを解析する
- **THEN** サーバーは各キーの値を構造化メタデータオブジェクトとして抽出して該当コミットのJSONフィールドに含める

#### Scenario: [S01-03-03] 変更種別バッジ用のコミット分類判定
- **WHEN** コミット一覧の各コミットオブジェクトを生成する
- **THEN** `Executed-Command` が存在し `"manual"` 以外である場合は `command`（コマンド一括変更）、テスト関連コミットの場合は `test`（テスト追加）、それ以外は `manual`（手動実装）として分類フィールドを付与する

### Requirement: コミット単位の変更ファイル統計およびUnified Diff取得API
**USDM**: R01-04
システムは `GET /api/commits/<sha>/diff` エンドポイントを提供し、指定コミットの変更ファイル一覧（ステータス・追加行数・削除行数）とUnified Diff文字列を返却しなければならない（SHALL）。また空白無視オプションに対応しなければならない（SHALL）。

#### Scenario: [S01-04-01] 指定コミットの変更ファイル一覧とDiff全文の取得
- **WHEN** クライアントが有効なコミットSHAに対して `GET /api/commits/<sha>/diff` を要求する
- **THEN** サーバーは変更ファイル一覧（パス、ステータス、追加行数、削除行数）およびUnified Diff文字列を含むJSONを返却する

#### Scenario: [S01-04-02] 空白変更を無視したDiffの取得
- **WHEN** クライアントが `GET /api/commits/<sha>/diff?ignore_whitespace=true` を要求する
- **THEN** サーバーは `git show -w` 相当の空白変更を無視したUnified Diff文字列を生成して返却する

### Requirement: ゼロ依存のPython標準ライブラリ起動とCLI設定
**USDM**: R03
システムは外部パッケージの事前インストール（`pip install` や `npm install`）を必要とせず、Python 3標準ライブラリのみで起動でき、引数または環境変数で対象リポジトリパスとポートを指定できなければならない（SHALL）。

#### Scenario: [S03-01] 標準Python環境での外部パッケージ不要起動
- **WHEN** ユーザーが `pip install` や `npm install` を実行していない環境で `python3 server.py` を実行する
- **THEN** サーバーは外部モジュール不足エラーを起こすことなくHTTP待受を開始し、APIと静的UIアセットの両方を配信する

#### Scenario: [S03-02] 引数および環境変数による対象リポジトリとポートの指定
- **WHEN** ユーザーが `--repo /path/to/repo --port 8765` 引数または `REPO_PATH` / `PORT` 環境変数を指定して起動する
- **THEN** サーバーは指定されたパスのGitリポジトリを検査対象とし、指定されたポート番号でリクエストを受け付ける
