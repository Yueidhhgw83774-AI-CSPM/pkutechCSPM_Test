# conftest.py 設計

## 1. 概要

本ドキュメントでは、python-fastapiプロジェクトの `conftest.py` 設計を説明します。

## 2. conftest.py の階層構造

```
test/
├── conftest.py                    # グローバル設定・共通フィクスチャ
├── unit/
│   ├── conftest.py               # ユニットテスト用フィクスチャ
│   ├── cspm_plugin/
│   │   └── conftest.py           # CSPMプラグイン専用フィクスチャ
│   └── mcp_plugin/
│       └── conftest.py           # MCPプラグイン専用フィクスチャ
├── integration/
│   └── conftest.py               # 統合テスト用フィクスチャ
└── e2e/
    └── conftest.py               # E2Eテスト用フィクスチャ
```

## 3. グローバル conftest.py

### 3.1 完全なコード例

```python
# test/conftest.py
"""
グローバルテスト設定とフィクスチャ

このファイルは全てのテストで使用される共通設定を提供します。
"""
import os
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dotenv import load_dotenv
from httpx import AsyncClient, ASGITransport

# アプリケーションインポート
from app.main import app


# =============================================================================
# pytest 設定フック
# =============================================================================

def pytest_configure(config):
    """
    pytest設定時のフック

    - 環境変数の読み込み
    - カスタムマーカーの登録
    """
    # テスト用環境変数を読み込み
    env_file = os.getenv("ENV_FILE", ".env.test")
    if os.path.exists(env_file):
        load_dotenv(env_file, override=True)

    # 必須環境変数のデフォルト設定
    os.environ.setdefault("APP_ENV", "test")
    os.environ.setdefault("LOG_LEVEL", "WARNING")


def pytest_collection_modifyitems(config, items):
    """
    テスト収集後のフック

    - マーカーに基づく自動スキップ
    """
    skip_opensearch = pytest.mark.skip(reason="OpenSearch not available")
    skip_llm = pytest.mark.skip(reason="LLM API not configured")

    for item in items:
        # OpenSearchテストのスキップ判定
        if "opensearch" in item.keywords:
            if not os.getenv("OPENSEARCH_HOST"):
                item.add_marker(skip_opensearch)

        # LLMテストのスキップ判定
        if "llm" in item.keywords:
            if not (os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
                item.add_marker(skip_llm)


# =============================================================================
# イベントループ設定
# =============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    セッションスコープのイベントループ

    全ての非同期テストで共有されるイベントループを提供します。
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# HTTPクライアント フィクスチャ
# =============================================================================

@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    非同期HTTPテストクライアント

    FastAPIアプリケーションに対するHTTPリクエストをテストします。

    使用例:
        async def test_endpoint(async_client):
            response = await async_client.get("/api/health")
            assert response.status_code == 200
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
async def authenticated_client(async_client: AsyncClient, test_auth_token: str) -> AsyncClient:
    """
    認証済みHTTPクライアント

    Authorizationヘッダーが設定されたクライアントを提供します。
    """
    async_client.headers.update({"Authorization": f"Bearer {test_auth_token}"})
    return async_client


# =============================================================================
# 認証 フィクスチャ
# =============================================================================

@pytest.fixture
def test_auth_token() -> str:
    """
    テスト用JWTトークン

    モックされた認証トークンを返します。
    """
    return "test-jwt-token-for-testing"


@pytest.fixture
def mock_jwt_verification():
    """
    JWT検証のモック

    認証をバイパスしてテストを実行します。
    """
    with patch("app.core.auth.verify_token") as mock:
        mock.return_value = {
            "sub": "test-user",
            "roles": ["admin"],
            "exp": 9999999999
        }
        yield mock


# =============================================================================
# LLM モック フィクスチャ
# =============================================================================

@pytest.fixture
def mock_llm_response():
    """
    LLMレスポンスのモック

    LLM APIの呼び出しをモックして固定レスポンスを返します。
    """
    mock_response = MagicMock()
    mock_response.content = "This is a mocked LLM response."

    with patch("langchain_openai.ChatOpenAI") as mock_openai:
        mock_instance = AsyncMock()
        mock_instance.ainvoke.return_value = mock_response
        mock_openai.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_llm_streaming():
    """
    LLMストリーミングレスポンスのモック
    """
    async def mock_stream():
        chunks = ["Hello", " ", "World", "!"]
        for chunk in chunks:
            mock_chunk = MagicMock()
            mock_chunk.content = chunk
            yield mock_chunk

    with patch("langchain_openai.ChatOpenAI") as mock_openai:
        mock_instance = AsyncMock()
        mock_instance.astream.return_value = mock_stream()
        mock_openai.return_value = mock_instance
        yield mock_instance


# =============================================================================
# OpenSearch モック フィクスチャ
# =============================================================================

@pytest.fixture
def mock_opensearch_client():
    """
    OpenSearchクライアントのモック

    OpenSearch操作をモックします。
    """
    with patch("app.core.clients.get_opensearch_client") as mock:
        mock_client = AsyncMock()

        # 検索結果のモック
        mock_client.search.return_value = {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_id": "test-doc-1",
                        "_source": {"field": "value"}
                    }
                ]
            }
        }

        # インデックス操作のモック
        mock_client.index.return_value = {"result": "created", "_id": "test-id"}
        mock_client.delete.return_value = {"result": "deleted"}

        mock.return_value = mock_client
        yield mock_client


# =============================================================================
# テストデータ フィクスチャ
# =============================================================================

@pytest.fixture
def sample_policy_yaml() -> str:
    """
    サンプルのCloud Custodianポリシー（YAML形式）
    """
    return """
policies:
  - name: s3-encryption-check
    resource: s3
    description: S3バケットの暗号化をチェック
    filters:
      - type: value
        key: BucketEncryption
        value: absent
    actions:
      - type: notify
        subject: "S3 Bucket without encryption found"
"""


@pytest.fixture
def sample_recommendation_data() -> dict:
    """
    サンプルの推奨事項データ
    """
    return {
        "uid": "rec-001",
        "title": "S3バケットの暗号化を有効化",
        "description": "セキュリティのためにS3バケットのサーバーサイド暗号化を有効にしてください",
        "severity": "high",
        "resource_type": "s3",
        "cloud_provider": "aws"
    }


@pytest.fixture
def sample_chat_request() -> dict:
    """
    サンプルのチャットリクエスト
    """
    return {
        "prompt": "S3バケットの暗号化チェックポリシーを作成してください",
        "policy_context": None
    }


# =============================================================================
# クリーンアップ フィクスチャ
# =============================================================================

@pytest.fixture(autouse=True)
async def cleanup_test_data():
    """
    テスト後の自動クリーンアップ

    各テスト終了後に実行されます。
    """
    yield
    # ここにクリーンアップ処理を追加
    # 例: テストで作成されたファイルの削除など


# =============================================================================
# ユーティリティ関数
# =============================================================================

def create_mock_response(status_code: int = 200, json_data: dict = None) -> MagicMock:
    """
    モックHTTPレスポンスを作成するユーティリティ

    Args:
        status_code: HTTPステータスコード
        json_data: レスポンスJSONデータ

    Returns:
        モックされたレスポンスオブジェクト
    """
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data or {}
    return mock_response
```

## 4. ユニットテスト用 conftest.py

### 4.1 基本構造

```python
# test/unit/conftest.py
"""
ユニットテスト用フィクスチャ

外部依存を全てモック化したテスト用の設定を提供します。
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture(autouse=True)
def mock_all_external_dependencies():
    """
    全ての外部依存を自動的にモック化

    ユニットテストでは外部サービスへのアクセスを完全に遮断します。
    """
    with patch.multiple(
        "app.core.clients",
        get_opensearch_client=AsyncMock(),
        get_redis_client=MagicMock(),
    ):
        with patch("langchain_openai.ChatOpenAI") as mock_llm:
            mock_llm.return_value = AsyncMock()
            yield


@pytest.fixture
def mock_yaml_parser():
    """
    YAMLパーサーのモック
    """
    with patch("yaml.safe_load") as mock:
        yield mock


@pytest.fixture
def mock_file_system(tmp_path):
    """
    ファイルシステム操作のモック

    一時ディレクトリを使用してファイル操作をテストします。
    """
    return tmp_path
```

## 5. 統合テスト用 conftest.py

### 5.1 基本構造

```python
# test/integration/conftest.py
"""
統合テスト用フィクスチャ

実際のサービス（テスト環境）に接続するテスト用の設定を提供します。
"""
import pytest
from opensearchpy import AsyncOpenSearch


@pytest.fixture(scope="module")
async def opensearch_client():
    """
    テスト用OpenSearchクライアント

    テスト環境のOpenSearchに接続します。
    """
    client = AsyncOpenSearch(
        hosts=[{
            "host": "localhost",
            "port": 9200
        }],
        http_auth=("admin", "admin"),
        use_ssl=True,
        verify_certs=False,
    )

    yield client

    await client.close()


@pytest.fixture(scope="function")
async def test_index(opensearch_client):
    """
    テスト用インデックス

    各テストで使用する一時的なインデックスを作成・削除します。
    """
    import uuid
    index_name = f"test_index_{uuid.uuid4().hex[:8]}"

    # インデックス作成
    await opensearch_client.indices.create(index=index_name)

    yield index_name

    # クリーンアップ
    await opensearch_client.indices.delete(index=index_name, ignore=[404])
```

## 6. ベストプラクティス

### 6.1 フィクスチャのスコープ

| スコープ | 用途 | 例 |
|---------|------|-----|
| function | 各テストで独立 | テストデータ |
| class | クラス内で共有 | 設定オブジェクト |
| module | モジュール内で共有 | DBクライアント |
| session | 全テストで共有 | イベントループ |

### 6.2 命名規則

```python
# モックフィクスチャ: mock_<対象>
@pytest.fixture
def mock_opensearch_client(): ...

# サンプルデータ: sample_<データ種類>
@pytest.fixture
def sample_policy_yaml(): ...

# テスト用オブジェクト: test_<オブジェクト>
@pytest.fixture
def test_auth_token(): ...
```

### 6.3 依存関係の管理

```python
# 良い例: 依存関係を明示的に注入
@pytest.fixture
def authenticated_client(async_client, test_auth_token):
    async_client.headers["Authorization"] = f"Bearer {test_auth_token}"
    return async_client

# 悪い例: グローバル状態に依存
@pytest.fixture
def bad_client():
    global_token = get_global_token()  # 避けるべき
    return create_client(global_token)
```
