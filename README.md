# GitHub Pull Request Commits Viewer

OpenSpecのように「1サブタスク＝1コミット」で粒度を揃えて積み上げたGit履歴やPull Requestに対し、**コミット単位の差分・目的（Why / What）・紐づくタスク情報・実行コマンド（Git Trailers）** を1画面（3ペイン構成）で高速に切り替えながら閲覧・レビューできるローカル実行Webアプリケーションです。

---

## 主な特徴

- **完全ゼロ依存（Zero-Dependency）**:
  - バックエンドは **Python 3 標準ライブラリのみ**（`http.server`, `subprocess`, `json`, `re`, `urllib.parse`）で動作し、`pip install` 不要。
  - フロントエンドは **ビルドレス Vanilla JS (ES Modules) + CSS + Diff2Html** で構成され、`npm install` やビルド工程も不要。
  - Ubuntu標準の `python3` や Windows Python 環境で、起動時間0.1秒未満・最小メモリで即座に動作します。
- **3ペイン高速レビューUI**:
  1. **ヘッダー（ターゲット選択）**: 現在のリポジトリ名・ブランチ表示、GitHubオープンPR一覧のドロップダウン選択（`gh` 未認証・オフライン時はローカルの `base` / `head` ブランチ比較へ自動フォールバック）。
  2. **左ペイン（Commit Menu）**:
     - 時系列コミット一覧と変更種別バッジ（`🤖 Command` コマンド一括変更 / `✍️ Manual` 手動実装 / `✅ Test` テスト追加）およびOpenSpecタスクIDの自動表示。
     - キーボードの `j` / `k` または `↓` / `↑` キーによるページリロードなしの瞬時コミット切り替え。
     - コミット単位の「確認済み（Reviewed）」チェック管理（`r` キーまたはチェックボックス、`localStorage` に永続化）。
  3. **中央・右ペイン（Commit Context & Diff Viewer）**:
     - 上部サマリカード：コミットの目的（`Why` / `What`）、OpenSpecタスク（`Task`）、検証内容（`Verification`）、および実行コマンド全文（`Executed-Command`）の強調表示。
     - 下部Diffビューア：変更ファイル一覧（クリックで該当ファイルへスクロール移動）と、**Split（左右分割）/ Unified（統合）** 切替・**空白無視（Ignore Whitespace）** オプション対応のシンタックスハイライト付きDiff表示。

---

## 動作要件

- **Python 3.8 以上**（標準ライブラリのみ使用）
- **Git CLI**（`git` コマンドがPATHに存在すること）
- **GitHub CLI (`gh`)** *(任意)*：インストールおよび認証済みの場合はオープンPR一覧を取得します。未導入・未認証の場合でもローカルブランチ間の比較ビューアとしてそのまま利用可能です。

---

## 起動方法

```bash
# カレントディレクトリのリポジトリを対象に起動（デフォルトポート: 8000）
python3 server.py

# 任意のローカルGitリポジトリとポートを指定して起動
python3 server.py --repo /path/to/your/repo --port 8765

# 環境変数での指定にも対応
REPO_PATH=/path/to/your/repo PORT=8765 python3 server.py

# CLIヘルプの表示
python3 server.py --help
```

起動後、ブラウザで `http://localhost:8000`（または指定したポート）を開きます。

---

## キーボードショートカット

| キー | 動作 |
| :--- | :--- |
| `j` / `↓` | 次のコミットへ移動 |
| `k` / `↑` | 前のコミットへ移動 |
| `r` | 現在選択中のコミットの「確認済み（Reviewed）」をトグル |

---

## 自動解析されるコミットメッセージ形式（Git Trailers）

本ビューアは以下のフォーマットで記述されたコミットメッセージ本文・Git Trailersを自動抽出し、バッジ判定とサマリカード表示に利用します（通常のコミットメッセージもそのまま閲覧可能です）。

```text
feat(parser): add Git Trailers metadata parser

Why: コミットメッセージからタスクIDや実行コマンドを構造化抽出するため
What: viewer_backend/parser.py に正規表現パーサーと変更種別判定関数を実装

Issue: #12
Task: 1.1 [S01-03-02, S01-03-03]
Verification: python3 -m unittest tests/test_parser.py
Executed-Command: manual
```

- `Executed-Command` が `"manual"` 以外（例: `npx eslint --fix .` や `sed -i ...`）の場合、左ペインに **`🤖 Command`** バッジが付与され、サマリカード上部に実行コマンド全文が強調表示されます。

---

## ディレクトリ構成

```text
.
├── README.md                 # プロジェクト概要・利用手順
├── AGENTS.md                 # AIエージェント向け開発・OpenSpec・コミット規約
├── server.py                 # Python標準ライブラリ製 HTTP / APIサーバー
├── viewer_backend/           # バックエンドモジュール
│   ├── __init__.py
│   ├── parser.py             # コミットメッセージ / Git Trailers パーサー
│   └── git_service.py        # git / gh サブプロセス実行サービス
├── static/                   # ビルドレスWebフロントエンド（3ペインUI）
│   ├── index.html
│   ├── style.css
│   └── app.js
├── tests/                    # 標準 unittest による単体・API統合テスト
└── openspec/                 # OpenSpec (USDMスキーマ) 仕様・変更管理
```

## テストの実行

```bash
python3 -m unittest discover -s tests -v
```
