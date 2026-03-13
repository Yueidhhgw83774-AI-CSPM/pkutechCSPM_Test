# コアサービステストケーステンプレート

## 概要

`app/core/` ディレクトリ内の全モジュールのテスト仕様書が**完成**しました。

このファイルは当初、未作成のテスト仕様書の基本テンプレートとして使用されていましたが、
現在は全てのテスト仕様書が作成済みです。

---

## 完成済みテスト仕様書一覧

| モジュール | テスト仕様書 | テストID | 件数 |
|-----------|------------|---------|------|
| `config.py` | [config_tests.md](./config_tests.md) | CFG-* | - |
| `llm_factory.py` | [llm_factory_tests.md](./llm_factory_tests.md) | LLM-* | - |
| `clients.py` | [clients_tests.md](./clients_tests.md) | CLI-* | - |
| `auth.py` | [../plugins/auth_tests.md](../plugins/auth_tests.md) | AUTH-* | - |
| `permission_checker.py` | [permission_checker_tests.md](./permission_checker_tests.md) | PERM-* | - |
| `checkpointer.py` | [checkpointer_tests.md](./checkpointer_tests.md) | CKP-* | - |
| `crypto.py` | [crypto_tests.md](./crypto_tests.md) | CRYPTO-* | - |
| `auth_utils.py` | [auth_utils_tests.md](./auth_utils_tests.md) | AUTIL-* | - |
| `encryption_middleware.py` | [encryption_middleware_tests.md](./encryption_middleware_tests.md) | ENCMW-* | - |
| `categories.py` | [categories_tests.md](./categories_tests.md) | CAT-* | - |
| `rag_manager.py` | [rag_manager_tests.md](./rag_manager_tests.md) | RAG-* | - |
| `role_based_client.py` | [role_based_client_tests.md](./role_based_client_tests.md) | RBC-* | - |
| `health_checker.py` | [health_checker_tests.md](./health_checker_tests.md) | HC-* | 54 |
| `error_handlers.py` | [error_handlers_tests.md](./error_handlers_tests.md) | ERH-* | 39 |

---

## 共通フィクスチャ

以下のフィクスチャは `test/unit/core/conftest.py` で定義し、複数のテストで共有できます。

```python
# test/unit/core/conftest.py
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import jwt
from datetime import datetime, timedelta

# テスト用定数（config.pyバリデーション通過に必要な最小環境変数セット）
REQUIRED_ENV_VARS = {
    "GPT5_1_CHAT_API_KEY": "test-key",
    "GPT5_1_CODEX_API_KEY": "test-key",
    "GPT5_2_API_KEY": "test-key",
    "GPT5_MINI_API_KEY": "test-key",
    "GPT5_NANO_API_KEY": "test-key",
    "CLAUDE_HAIKU_4_5_KEY": "test-key",
    "CLAUDE_SONNET_4_5_KEY": "test-key",
    "GEMINI_API": "test-key",
    "DOCKER_BASE_URL": "http://localhost:11434",
    "EMBEDDING_3_LARGE_API_KEY": "test-embedding-key",
    "OPENSEARCH_URL": "https://localhost:9200",
}


@pytest.fixture(autouse=True)
def reset_core_modules():
    """テストごとにcoreモジュールの状態をリセット

    シングルトンインスタンスやモジュールレベルの変数が
    テスト間で共有されないように、モジュールを再読み込みする。
    """
    yield

    # テスト後にクリーンアップ
    modules_to_remove = [
        key for key in sys.modules
        if key.startswith("app.core")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def mock_opensearch_config():
    """OpenSearch設定のモック"""
    with patch.dict("os.environ", {
        "OPENSEARCH_HOST": "localhost",
        "OPENSEARCH_PORT": "9200",
        "OPENSEARCH_USER": "admin",
        "OPENSEARCH_PASSWORD": "admin"
    }):
        yield


@pytest.fixture
def mock_opensearch_client():
    """OpenSearchクライアントのモック"""
    mock_client = AsyncMock()
    mock_client.info = AsyncMock(return_value={'version': {'number': '2.0.0'}})
    mock_client.search = AsyncMock(return_value={'hits': {'hits': []}})
    mock_client.index = AsyncMock(return_value={'result': 'created'})
    return mock_client


@pytest.fixture
def mock_storage():
    """ストレージのモック"""
    storage = AsyncMock()
    storage.get = AsyncMock(return_value=None)
    storage.set = AsyncMock(return_value=True)
    storage.delete = AsyncMock(return_value=True)
    return storage


@pytest.fixture
def valid_token():
    """有効なJWTトークン"""
    secret = "test-secret"
    payload = {
        "sub": "user-001",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "roles": ["user"]
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture
def expired_token():
    """期限切れJWTトークン"""
    secret = "test-secret"
    payload = {
        "sub": "user-001",
        "exp": datetime.utcnow() - timedelta(hours=1),
        "roles": ["user"]
    }
    return jwt.encode(payload, secret, algorithm="HS256")
```

---

## テスト実行例

```bash
# コアサービスの全テスト
pytest test/unit/core/ -v

# 特定モジュールのテスト
pytest test/unit/core/test_error_handlers.py -v
pytest test/unit/core/test_health_checker.py -v
pytest test/unit/core/test_clients.py -v

# カバレッジ付き
pytest test/unit/core/ --cov=app/core --cov-report=term-missing

# セキュリティテストのみ
pytest test/unit/core/ -m "security" -v

# xfailを含めた詳細表示
pytest test/unit/core/ -v --tb=short
```

---

## pyproject.toml 設定

テスト実行に必要な設定:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
markers = [
    "security: セキュリティテスト",
    "integration: 統合テスト",
]
```

---

## 進捗状況

**全14モジュールのテスト仕様書が完成しました。** (2026-01-30)

詳細な進捗は [core_tests_status.md](./core_tests_status.md) を参照してください。
