# テスト環境設定

## 1. 概要

本ドキュメントでは、python-fastapiプロジェクトのテスト環境セットアップ手順を説明します。

> **重要**: APIキー未設定でテストを実行するには`TESTING_MODE`環境変数の設定が必要です。
> 詳細は [テストモード設定ガイド](./testing-mode-configuration.md) を参照してください。

## 2. 必要条件

### 2.1 システム要件

| 項目 | 要件 |
|------|------|
| Python | 3.11以上 |
| パッケージマネージャー | uv（推奨）または pip |
| OS | Linux / macOS / Windows (WSL) |

### 2.2 必要なサービス（統合テスト用）

| サービス | 用途 | ポート |
|---------|------|--------|
| OpenSearch | データストア | 9200 |
| Docker | コンテナ実行 | - |

## 3. ローカル環境セットアップ

### 3.1 依存関係のインストール

```bash
# プロジェクトディレクトリに移動
cd /usr/share/osd/python-fastapi

# uvを使用する場合（推奨）
uv sync

# pipを使用する場合
pip install -e ".[dev]"
```

### 3.2 テスト用依存関係

`pyproject.toml` のテスト依存関係：

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.10.0",
    "httpx>=0.24.0",
    "moto>=4.0.0",       # AWS モック
    "fakeredis>=2.0.0",  # Redis モック（必要な場合）
]
```

### 3.3 環境変数設定

テスト用の環境変数を `.env.test` に設定：

```bash
# .env.test

# アプリケーション設定
APP_ENV=test
DEBUG=true
LOG_LEVEL=DEBUG

# OpenSearch設定（テスト用）
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200
OPENSEARCH_USER=admin
OPENSEARCH_PASSWORD=admin
OPENSEARCH_USE_SSL=true
OPENSEARCH_VERIFY_CERTS=false

# テスト用インデックスプレフィックス
TEST_INDEX_PREFIX=test_

# LLM設定（モック使用時は不要）
# OPENAI_API_KEY=test-key
# ANTHROPIC_API_KEY=test-key

# AWS設定（モック使用時は不要）
# AWS_ACCESS_KEY_ID=test
# AWS_SECRET_ACCESS_KEY=test
# AWS_DEFAULT_REGION=ap-northeast-1
```

### 3.4 環境変数の読み込み

```python
# conftest.py で環境変数を読み込む
import os
from dotenv import load_dotenv

def pytest_configure(config):
    """pytest設定時に環境変数を読み込む"""
    env_file = os.getenv("ENV_FILE", ".env.test")
    load_dotenv(env_file, override=True)
```

## 4. テスト実行方法

### 4.1 基本的な実行

```bash
# すべてのテストを実行
pytest

# 特定のディレクトリのテストを実行
pytest test/unit/

# 特定のファイルのテストを実行
pytest test/unit/cspm_plugin/test_policy_validation.py

# 特定のテスト関数を実行
pytest test/unit/cspm_plugin/test_policy_validation.py::test_valid_yaml
```

### 4.2 オプション付き実行

```bash
# 詳細出力
pytest -v

# 最初の失敗で停止
pytest -x

# 失敗したテストを再実行
pytest --lf

# 並列実行（pytest-xdistが必要）
pytest -n auto

# カバレッジ付き実行
pytest --cov=app --cov-report=html
```

### 4.3 マーカーによるフィルタリング

```bash
# ユニットテストのみ
pytest -m unit

# 統合テストを除外
pytest -m "not integration"

# LLM不要なテストのみ
pytest -m "not llm"
```

## 5. pytest設定

### 5.1 pyproject.toml設定

```toml
[tool.pytest.ini_options]
# テストディレクトリ
testpaths = ["test"]

# 非同期モード
asyncio_mode = "auto"

# マーカー定義
markers = [
    "unit: ユニットテスト",
    "integration: 統合テスト",
    "e2e: E2Eテスト",
    "slow: 実行時間が長いテスト",
    "llm: LLM連携が必要なテスト",
    "opensearch: OpenSearch接続が必要なテスト",
    "aws: AWS接続が必要なテスト",
]

# カバレッジ設定
addopts = [
    "--strict-markers",
    "-ra",
]

# 警告フィルタ
filterwarnings = [
    "ignore::DeprecationWarning",
    "ignore::PendingDeprecationWarning",
]
```

### 5.2 pytest.ini（代替）

```ini
[pytest]
testpaths = test
asyncio_mode = auto
addopts = --strict-markers -ra
```

## 6. Docker環境でのテスト

### 6.1 docker-compose.test.yml

```yaml
version: '3.8'

services:
  # テスト用OpenSearch
  opensearch-test:
    image: opensearchproject/opensearch:2.11.0
    environment:
      - discovery.type=single-node
      - DISABLE_SECURITY_PLUGIN=false
      - OPENSEARCH_INITIAL_ADMIN_PASSWORD=Admin123!
    ports:
      - "9201:9200"  # 本番と異なるポートを使用
    healthcheck:
      test: ["CMD", "curl", "-k", "-u", "admin:Admin123!", "https://localhost:9200"]
      interval: 10s
      timeout: 5s
      retries: 5

  # テスト実行コンテナ
  test-runner:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - OPENSEARCH_HOST=opensearch-test
      - OPENSEARCH_PORT=9200
      - APP_ENV=test
    depends_on:
      opensearch-test:
        condition: service_healthy
    command: pytest --cov=app
    volumes:
      - .:/app
      - ./test-results:/app/test-results
```

### 6.2 Docker環境でのテスト実行

```bash
# テスト環境起動とテスト実行
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

# クリーンアップ
docker-compose -f docker-compose.test.yml down -v
```

## 7. IDE設定

### 7.1 VS Code設定

`.vscode/settings.json`:

```json
{
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "test",
        "-v"
    ],
    "python.envFile": "${workspaceFolder}/.env.test"
}
```

### 7.2 PyCharm設定

1. Settings → Tools → Python Integrated Tools
2. Default test runner: pytest
3. Environment variables: `.env.test` を参照

## 8. トラブルシューティング

### 8.1 よくある問題

| 問題 | 原因 | 解決策 |
|------|------|--------|
| ModuleNotFoundError | パッケージ未インストール | `uv sync` または `pip install -e .` |
| OpenSearch接続エラー | サービス未起動 | `docker-compose up opensearch` |
| 非同期テストエラー | asyncio_mode未設定 | `asyncio_mode = "auto"` を追加 |
| 環境変数未設定 | .env.test未読み込み | conftest.pyで`load_dotenv`確認 |

### 8.2 デバッグモード

```bash
# pdbでデバッグ
pytest --pdb

# 失敗時のみpdb起動
pytest --pdb-first

# ログ出力を表示
pytest -s --log-cli-level=DEBUG
```
