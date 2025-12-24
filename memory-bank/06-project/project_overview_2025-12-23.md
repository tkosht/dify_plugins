# プロジェクト概要: Dify Plugins Project（2025-12-23）

Tags: dify, plugin, sharepoint_list, microsoft_graph, python, docker, tests

## Problem
- 本プロジェクトの概要を、事実に基づいて記録する。

## Research
- `README.md`: プロジェクト名とプラグイン一覧
- `app/sharepoint_list/README.md`: SharePoint List プラグインの用途・設定・注意点
- `app/sharepoint_list/manifest.yaml`: プラグインのメタ情報（version, runner, minimum_dify_version）
- `app/sharepoint_list/requirements.txt`: プラグイン依存
- `pyproject.toml`: Python 依存とツール設定（black/isort/flake8/ruff/pytest）
- `Makefile`: 開発用コマンド（docker compose, webapp, serena）
- `compose.yml`: コンテナ構成
- `tests/sharepoint_list/*`: SharePoint List プラグインのテスト群

## Solution
- **目的**: Dify Plugins Project。現時点のプラグインは `sharepoint_list`。
- **プラグイン概要**: SharePoint List のアイテム操作（作成/更新/参照/一覧/choice 取得）を Microsoft Graph 経由で実施。Delegated OAuth を使用。
- **構成（主要）**:
  - `app/sharepoint_list/`: プラグイン本体（`manifest.yaml`, `main.py`, `provider/`, `tools/`, `requirements.txt`）
  - `tests/sharepoint_list/`: 対応テスト群
  - `docker/`, `compose.yml`, `Makefile`: 開発/実行環境
  - `docs/`, `memory-bank/`: ドキュメントとナレッジ
- **メタ情報**（`manifest.yaml`）:
  - version: 0.0.3
  - runner: python 3.12 / entrypoint: `main`
  - minimum_dify_version: 1.10.0
- **依存**（`requirements.txt`）:
  - `dify-plugin>=0.5.0,<0.7.0`
  - `requests>=2.32.0`
- **注意**（プラグイン README より）:
  - `client_secret` は system credentials のみ使用し、ユーザー credentials に含めない。
  - トークン・シークレットはログ/出力に含めない。
  - SharePoint の未インデックス列フィルタは 400 になる場合がある。
- **実行・開発コマンド例**（`Makefile`/`bin/auto_debug.sh` より）:
  - `make up` / `make down` / `make build`
  - `make webapp` / `make container-webapp`
  - `make serena-up` / `make serena-logs`
  - `poetry run pytest -v .`

## Verification
- 参照ファイル:
  - `README.md`
  - `app/sharepoint_list/README.md`
  - `app/sharepoint_list/manifest.yaml`
  - `app/sharepoint_list/requirements.txt`
  - `pyproject.toml`
  - `Makefile`
  - `compose.yml`
  - `tests/sharepoint_list/`
