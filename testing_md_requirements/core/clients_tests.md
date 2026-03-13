# clients テストケース

## 1. 概要

OpenSearchクライアント・Embedding関数の初期化・取得機能のテストケースを定義します。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `extract_aws_region_from_url()` | OpenSearch URLからAWSリージョンを推定 |
| `initialize_opensearch_client()` | 非同期OpenSearchクライアント初期化（リトライ付き） |
| `initialize_embedding_function()` | OpenAIEmbeddings初期化（同期） |
| `get_opensearch_client()` | グローバル初期化済みOpenSearchクライアント取得 |
| `get_opensearch_client_with_auth()` | 指定認証情報でOpenSearchクライアント作成 |
| `get_embedding_function()` | グローバル初期化済みEmbedding関数取得 |

### 1.2 カバレッジ目標: 80%

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/core/clients.py` |
| テストコード | `test/unit/core/test_clients.py` |

### 1.4 グローバル変数

| 変数名 | 型 | 役割 |
|--------|-----|------|
| `os_client` | `Optional[AsyncOpenSearch]` | 初期化済みOpenSearchクライアント |
| `OS_CLIENT_INIT_ERROR` | `Optional[Exception]` | 初期化エラー情報 |
| `OS_CLIENT_INITIALIZED` | `bool` | 初期化完了フラグ |
| `embedding_function` | `Optional[OpenAIEmbeddings]` | 初期化済みEmbedding関数 |
| `EMBEDDING_INIT_ERROR` | `Optional[Exception]` | 初期化エラー情報 |
| `EMBEDDING_INITIALIZED` | `bool` | 初期化完了フラグ |

### 1.5 主要分岐

| 分岐 | 条件 | 結果 |
|------|------|------|
| AWS判定 | `is_aws_opensearch_service()` | AWS用設定 or 自前OS設定 |
| Basic認証 | `OPENSEARCH_USER + OPENSEARCH_PASSWORD` | http_auth設定 |
| ポート決定 | URL指定 > AWS:443 > 標準:9200 | ポート番号 |
| SSL証明書 | AWS→None / 自前→CA_CERTS_PATH or certifi | ca_certs設定 |
| Embeddingモデル | text-embedding-3-large/small/その他 | dimensions値 |
| Embedding BASE_URL | 設定あり/OpenAIモデル/それ以外 | BASE_URL or None or ValueError |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CLI-001 | es.amazonaws.com URLからリージョン抽出 | `https://search-xxx.us-east-1.es.amazonaws.com` | `"us-east-1"` |
| CLI-002 | aoss.amazonaws.com URLからリージョン抽出 | `https://xxx.us-west-2.aoss.amazonaws.com` | `"us-west-2"` |
| CLI-003 | 非AWS URL→デフォルトリージョン | `https://localhost:9200` | `"us-east-1"` |
| CLI-004 | hostname無し→デフォルトリージョン | `""` | `"us-east-1"` |
| CLI-005 | 正常初期化（ping成功、1回目） | 正常設定 | `OS_CLIENT_INITIALIZED=True` |
| CLI-006 | リトライ成功（1回目失敗、2回目成功） | ping 1回目False | 2回目で成功 |
| CLI-007 | 既に初期化済み→スキップ | `OS_CLIENT_INITIALIZED=True` | 即return |
| CLI-008 | 既にエラー済み→スキップ | `OS_CLIENT_INIT_ERROR`設定済み | 即return |
| CLI-009 | Basic認証（USER+PASSWORD設定） | 認証情報あり | `http_auth=(user,pass)` |
| CLI-010 | AWS OpenSearch→ポート443 | AWS URL、ポート指定なし | `port=443` |
| CLI-011 | 標準OpenSearch→ポート9200 | 非AWS URL、ポート指定なし | `port=9200` |
| CLI-012 | URL指定ポート→そのポート使用 | `https://host:9300` | `port=9300` |
| CLI-013 | AWS OpenSearch→ca_certs=None | AWS URL | `ca_certs=None` |
| CLI-014 | 自前OS＋CA_CERTS_PATH設定→指定パス使用 | CA_CERTS_PATH設定 | `ca_certs=設定値` |
| CLI-015 | text-embedding-3-large→dimensions=3072 | モデル名指定 | `dimensions=3072` |
| CLI-016 | text-embedding-3-small→dimensions=1536 | モデル名指定 | `dimensions=1536` |
| CLI-017 | その他モデル→dimensions=None | 未知モデル名 | `dimensions=None` |
| CLI-018 | BASE_URL未設定＋OpenAIモデル→エラーなし | OpenAIモデル名 | 正常初期化 |
| CLI-019 | Embedding既に初期化済み→スキップ | `EMBEDDING_INITIALIZED=True` | 即return |
| CLI-020 | 初期化成功後→クライアント返却 | 初期化済み状態 | `AsyncOpenSearch`インスタンス |
| CLI-021 | 初期化未完了→None返却 | 未初期化状態 | `None` |
| CLI-022 | 正常認証情報→クライアント作成成功 | `"user:pass"` | `AsyncOpenSearch`インスタンス |
| CLI-023 | AWS OpenSearch認証付き→ポート443+ca_certs=None | AWS URL + 認証情報 | AWS用設定 |
| CLI-024 | 自前OS認証付き→CA証明書設定 | 非AWS URL + 認証情報 | certifiまたは指定パス |
| CLI-025 | 初期化成功後→embedding返却 | 初期化済み状態 | `OpenAIEmbeddings`インスタンス |
| CLI-026 | localhostでホスト名検証無効 | `https://localhost:9200` | `ssl_assert_hostname=False` |
| CLI-027 | Embedding既にエラー済み→スキップ | `EMBEDDING_INIT_ERROR`設定済み | 即return |
| CLI-028 | Embedding未初期化→None返却 | 未初期化状態 | `None` |
| CLI-029 | リトライ途中例外→その後成功 | 1回目例外、2回目ping成功 | `OS_CLIENT_INITIALIZED=True` |

### 2.1 extract_aws_region_from_url テスト

```python
# test/unit/core/test_clients.py
import os
import pytest
import sys
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock


class TestExtractAwsRegion:
    """AWSリージョン抽出テスト"""

    def test_es_amazonaws_url(self):
        """CLI-001: es.amazonaws.com URLからリージョン抽出"""
        # Arrange
        url = "https://search-mydomain-abc123.us-east-1.es.amazonaws.com"

        # Act
        from app.core.clients import extract_aws_region_from_url
        result = extract_aws_region_from_url(url)

        # Assert
        assert result == "us-east-1"

    def test_aoss_amazonaws_url(self):
        """CLI-002: aoss.amazonaws.com URLからリージョン抽出"""
        # Arrange
        url = "https://collection-id.us-west-2.aoss.amazonaws.com"

        # Act
        from app.core.clients import extract_aws_region_from_url
        result = extract_aws_region_from_url(url)

        # Assert
        assert result == "us-west-2"

    def test_non_aws_url_returns_default(self):
        """CLI-003: 非AWS URL→デフォルトリージョン"""
        # Arrange
        url = "https://localhost:9200"

        # Act
        from app.core.clients import extract_aws_region_from_url
        result = extract_aws_region_from_url(url)

        # Assert
        assert result == "us-east-1"

    def test_empty_url_returns_default(self):
        """CLI-004: hostname無し→デフォルトリージョン"""
        # Arrange
        url = ""

        # Act
        from app.core.clients import extract_aws_region_from_url
        result = extract_aws_region_from_url(url)

        # Assert
        assert result == "us-east-1"
```

### 2.2 initialize_opensearch_client テスト

```python
# モジュール定数: テスト用環境変数
MOCK_SETTINGS_ENV = {
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
    "OPENSEARCH_USER": "test-user-do-not-use",
    "OPENSEARCH_PASSWORD": "test-password-do-not-use",
    "MODEL_NAME": "gpt-5.1-chat",
}


@pytest.fixture(autouse=True)
def reset_clients_module():
    """テストごとにclientsモジュールのグローバル変数をリセット"""
    yield
    # テスト後にモジュールキャッシュをクリア
    modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def mock_settings_env():
    """テスト用環境変数設定＋モジュールリセット"""
    with patch.dict("os.environ", MOCK_SETTINGS_ENV, clear=False):
        # モジュールキャッシュをクリアして再読み込みを強制
        modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
        for mod in modules_to_remove:
            del sys.modules[mod]
        yield


@pytest.fixture
def mock_async_opensearch():
    """AsyncOpenSearchモック（外部接続防止）"""
    with patch("app.core.clients.AsyncOpenSearch") as mock_cls:
        mock_instance = AsyncMock()
        mock_instance.ping = AsyncMock(return_value=True)
        mock_cls.return_value = mock_instance
        yield mock_cls, mock_instance


@pytest.fixture
def mock_openai_embeddings():
    """OpenAIEmbeddingsモック"""
    with patch("app.core.clients.OpenAIEmbeddings") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        yield mock_cls, mock_instance


class TestInitializeOpensearchClient:
    """OpenSearchクライアント初期化テスト"""

    @pytest.mark.asyncio
    async def test_successful_initialization(self, mock_settings_env, mock_async_opensearch):
        """CLI-005: 正常初期化（ping成功、1回目）"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch

        # Act
        import app.core.clients as clients_mod
        await clients_mod.initialize_opensearch_client(max_retries=1, retry_delay=0)

        # Assert
        assert clients_mod.OS_CLIENT_INITIALIZED is True
        assert clients_mod.OS_CLIENT_INIT_ERROR is None
        assert clients_mod.os_client is not None

    @pytest.mark.asyncio
    async def test_retry_success_on_second_attempt(self, mock_settings_env, mock_async_opensearch):
        """CLI-006: リトライ成功（1回目失敗、2回目ping成功）"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch
        mock_instance.ping = AsyncMock(side_effect=[False, True])

        # Act
        with patch("app.core.clients.asyncio.sleep", new_callable=AsyncMock):
            import app.core.clients as clients_mod
            await clients_mod.initialize_opensearch_client(max_retries=2, retry_delay=0)

        # Assert
        assert clients_mod.OS_CLIENT_INITIALIZED is True
        assert mock_instance.ping.call_count == 2

    @pytest.mark.asyncio
    async def test_skip_when_already_initialized(self, mock_settings_env, mock_async_opensearch):
        """CLI-007: 既に初期化済み→スキップ"""
        # Arrange
        import app.core.clients as clients_mod
        clients_mod.OS_CLIENT_INITIALIZED = True

        # Act
        await clients_mod.initialize_opensearch_client()

        # Assert - AsyncOpenSearchが呼ばれないことを確認
        mock_cls, _ = mock_async_opensearch
        mock_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_skip_when_already_errored(self, mock_settings_env, mock_async_opensearch):
        """CLI-008: 既にエラー済み→スキップ"""
        # Arrange
        import app.core.clients as clients_mod
        clients_mod.OS_CLIENT_INIT_ERROR = ValueError("previous error")

        # Act
        await clients_mod.initialize_opensearch_client()

        # Assert - AsyncOpenSearchが呼ばれないことを確認
        mock_cls, _ = mock_async_opensearch
        mock_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_basic_auth_with_credentials(self, mock_settings_env, mock_async_opensearch):
        """CLI-009: Basic認証（USER+PASSWORD設定）"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch

        # Act
        import app.core.clients as clients_mod
        await clients_mod.initialize_opensearch_client(max_retries=1, retry_delay=0)

        # Assert - AsyncOpenSearchに渡された引数を検証
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["http_auth"] == ("test-user-do-not-use", "test-password-do-not-use")

    @pytest.mark.asyncio
    async def test_aws_opensearch_port_443(self, mock_async_opensearch):
        """CLI-010: AWS OpenSearch→ポート443"""
        # Arrange
        aws_env = MOCK_SETTINGS_ENV.copy()
        aws_env["OPENSEARCH_URL"] = "https://search-domain.us-east-1.es.amazonaws.com"

        with patch.dict("os.environ", aws_env, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            mock_cls, mock_instance = mock_async_opensearch

            # Act
            import app.core.clients as clients_mod
            await clients_mod.initialize_opensearch_client(max_retries=1, retry_delay=0)

            # Assert
            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["hosts"][0]["port"] == 443

    @pytest.mark.asyncio
    async def test_standard_opensearch_port_9200(self, mock_settings_env, mock_async_opensearch):
        """CLI-011: 標準OpenSearch→ポート9200"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch

        # Act
        import app.core.clients as clients_mod
        await clients_mod.initialize_opensearch_client(max_retries=1, retry_delay=0)

        # Assert
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["hosts"][0]["port"] == 9200

    @pytest.mark.asyncio
    async def test_url_specified_port(self, mock_async_opensearch):
        """CLI-012: URL指定ポート→そのポート使用"""
        # Arrange
        env_with_port = MOCK_SETTINGS_ENV.copy()
        env_with_port["OPENSEARCH_URL"] = "https://localhost:9300"

        with patch.dict("os.environ", env_with_port, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            mock_cls, mock_instance = mock_async_opensearch

            # Act
            import app.core.clients as clients_mod
            await clients_mod.initialize_opensearch_client(max_retries=1, retry_delay=0)

            # Assert
            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["hosts"][0]["port"] == 9300

    @pytest.mark.asyncio
    async def test_aws_opensearch_ca_certs_none(self, mock_async_opensearch):
        """CLI-013: AWS OpenSearch→ca_certs=None"""
        # Arrange
        aws_env = MOCK_SETTINGS_ENV.copy()
        aws_env["OPENSEARCH_URL"] = "https://search-domain.us-east-1.es.amazonaws.com"

        with patch.dict("os.environ", aws_env, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            mock_cls, mock_instance = mock_async_opensearch

            # Act
            import app.core.clients as clients_mod
            await clients_mod.initialize_opensearch_client(max_retries=1, retry_delay=0)

            # Assert
            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["ca_certs"] is None

    @pytest.mark.asyncio
    async def test_self_hosted_ca_certs_path(self, mock_async_opensearch):
        """CLI-014: 自前OS＋CA_CERTS_PATH設定→指定パス使用"""
        # Arrange
        env_with_ca = MOCK_SETTINGS_ENV.copy()
        env_with_ca["OPENSEARCH_CA_CERTS_PATH"] = "/path/to/ca-cert.pem"

        with patch.dict("os.environ", env_with_ca, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            mock_cls, mock_instance = mock_async_opensearch

            # Act
            import app.core.clients as clients_mod
            await clients_mod.initialize_opensearch_client(max_retries=1, retry_delay=0)

            # Assert
            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["ca_certs"] == "/path/to/ca-cert.pem"

    @pytest.mark.asyncio
    async def test_localhost_hostname_verification_disabled(self, mock_settings_env, mock_async_opensearch):
        """CLI-026: localhostでホスト名検証無効"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch

        # Act（MOCK_SETTINGS_ENVのOPENSEARCH_URLはhttps://localhost:9200）
        import app.core.clients as clients_mod
        await clients_mod.initialize_opensearch_client(max_retries=1, retry_delay=0)

        # Assert
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["ssl_assert_hostname"] is False

    @pytest.mark.asyncio
    async def test_retry_exception_then_success(self, mock_settings_env, mock_async_opensearch):
        """CLI-029: リトライ途中例外→その後成功"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch
        # 1回目: 例外発生、2回目: ping成功
        mock_instance.ping = AsyncMock(
            side_effect=[Exception("Connection refused"), True]
        )

        # Act
        with patch("app.core.clients.asyncio.sleep", new_callable=AsyncMock):
            import app.core.clients as clients_mod
            await clients_mod.initialize_opensearch_client(max_retries=2, retry_delay=0)

        # Assert
        assert clients_mod.OS_CLIENT_INITIALIZED is True
        assert clients_mod.OS_CLIENT_INIT_ERROR is None
        assert mock_instance.ping.call_count == 2
```

### 2.3 initialize_embedding_function テスト

```python
class TestInitializeEmbeddingFunction:
    """Embedding関数初期化テスト"""

    def test_large_model_dimensions_3072(self, mock_settings_env, mock_openai_embeddings):
        """CLI-015: text-embedding-3-large→dimensions=3072"""
        # Arrange
        mock_cls, _ = mock_openai_embeddings

        with patch.dict("os.environ", {"EMBEDDING_MODEL_NAME": "text-embedding-3-large"}, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            # Act
            import app.core.clients as clients_mod
            clients_mod.initialize_embedding_function()

            # Assert
            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["dimensions"] == 3072

    def test_small_model_dimensions_1536(self, mock_settings_env, mock_openai_embeddings):
        """CLI-016: text-embedding-3-small→dimensions=1536"""
        # Arrange
        mock_cls, _ = mock_openai_embeddings

        with patch.dict("os.environ", {"EMBEDDING_MODEL_NAME": "text-embedding-3-small"}, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            # Act
            import app.core.clients as clients_mod
            clients_mod.initialize_embedding_function()

            # Assert
            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["dimensions"] == 1536

    def test_other_model_dimensions_none(self, mock_settings_env, mock_openai_embeddings):
        """CLI-017: その他モデル→dimensions=None

        注意: EMBEDDING_MODEL_BASE_URLはconfig.py:44で
        validation_alias='DOCKER_BASE_URL'として定義されるため、
        環境変数はDOCKER_BASE_URLを操作する必要がある。
        """
        # Arrange
        mock_cls, _ = mock_openai_embeddings

        with patch.dict("os.environ", {
            "EMBEDDING_MODEL_NAME": "text-embedding-ada-002",
            "DOCKER_BASE_URL": "https://api.example.com",
        }, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            # Act
            import app.core.clients as clients_mod
            clients_mod.initialize_embedding_function()

            # Assert
            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["dimensions"] is None

    def test_openai_model_without_base_url(self, mock_openai_embeddings):
        """CLI-018: BASE_URL未設定＋OpenAIモデル→エラーなし

        注意: config.py:44 で EMBEDDING_MODEL_BASE_URL は DOCKER_BASE_URL から
        読み込まれる（validation_alias='DOCKER_BASE_URL'）。
        DOCKER_BASE_URLはconfig.py:28でField(...)（必須）のため、
        環境変数から除外するとSettings初期化でValidationErrorになる。
        BASE_URL未設定（falsy）を再現するにはDOCKER_BASE_URLを空文字に設定する。
        """
        # Arrange
        mock_cls, _ = mock_openai_embeddings
        env = MOCK_SETTINGS_ENV.copy()
        env["EMBEDDING_MODEL_NAME"] = "text-embedding-3-large"
        env["DOCKER_BASE_URL"] = ""  # 空文字でBASE_URL未設定（falsy）を再現

        with patch.dict("os.environ", env, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            # Act
            import app.core.clients as clients_mod
            clients_mod.initialize_embedding_function()

            # Assert
            assert clients_mod.EMBEDDING_INITIALIZED is True
            assert clients_mod.EMBEDDING_INIT_ERROR is None

    def test_skip_when_already_initialized(self, mock_settings_env, mock_openai_embeddings):
        """CLI-019: 既に初期化済み→スキップ"""
        # Arrange
        import app.core.clients as clients_mod
        clients_mod.EMBEDDING_INITIALIZED = True

        # Act
        clients_mod.initialize_embedding_function()

        # Assert - OpenAIEmbeddingsが呼ばれないことを確認
        mock_cls, _ = mock_openai_embeddings
        mock_cls.assert_not_called()

    def test_skip_when_already_errored(self, mock_settings_env, mock_openai_embeddings):
        """CLI-027: Embedding既にエラー済み→スキップ"""
        # Arrange
        import app.core.clients as clients_mod
        clients_mod.EMBEDDING_INIT_ERROR = ValueError("previous error")

        # Act
        clients_mod.initialize_embedding_function()

        # Assert - OpenAIEmbeddingsが呼ばれないことを確認
        mock_cls, _ = mock_openai_embeddings
        mock_cls.assert_not_called()
```

### 2.4 get_opensearch_client テスト

```python
class TestGetOpensearchClient:
    """OpenSearchクライアント取得テスト"""

    @pytest.mark.asyncio
    async def test_returns_client_when_initialized(self, mock_settings_env):
        """CLI-020: 初期化成功後→クライアント返却"""
        # Arrange
        import app.core.clients as clients_mod
        mock_client = AsyncMock()
        clients_mod.os_client = mock_client
        clients_mod.OS_CLIENT_INITIALIZED = True
        clients_mod.OS_CLIENT_INIT_ERROR = None

        # Act
        result = await clients_mod.get_opensearch_client()

        # Assert
        assert result is mock_client

    @pytest.mark.asyncio
    async def test_returns_none_when_not_initialized(self, mock_settings_env):
        """CLI-021: 初期化未完了→None返却"""
        # Arrange
        import app.core.clients as clients_mod
        clients_mod.OS_CLIENT_INITIALIZED = False
        clients_mod.OS_CLIENT_INIT_ERROR = None

        # Act
        result = await clients_mod.get_opensearch_client()

        # Assert
        assert result is None
```

### 2.5 get_opensearch_client_with_auth テスト

```python
class TestGetOpensearchClientWithAuth:
    """認証付きOpenSearchクライアント取得テスト"""

    @pytest.mark.asyncio
    async def test_successful_creation(self, mock_settings_env, mock_async_opensearch):
        """CLI-022: 正常認証情報→クライアント作成成功"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch

        # Act
        import app.core.clients as clients_mod
        result = await clients_mod.get_opensearch_client_with_auth("testuser:testpass")

        # Assert
        assert result is not None
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["http_auth"] == ("testuser", "testpass")

    @pytest.mark.asyncio
    async def test_aws_opensearch_settings(self, mock_async_opensearch):
        """CLI-023: AWS OpenSearch認証付き→ポート443+ca_certs=None"""
        # Arrange
        aws_env = MOCK_SETTINGS_ENV.copy()
        aws_env["OPENSEARCH_URL"] = "https://search-domain.us-east-1.es.amazonaws.com"

        with patch.dict("os.environ", aws_env, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            mock_cls, mock_instance = mock_async_opensearch

            # Act
            import app.core.clients as clients_mod
            result = await clients_mod.get_opensearch_client_with_auth("user:pass")

            # Assert
            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["hosts"][0]["port"] == 443
            assert call_kwargs["ca_certs"] is None

    @pytest.mark.asyncio
    async def test_self_hosted_ca_certs(self, mock_settings_env, mock_async_opensearch):
        """CLI-024: 自前OS認証付き→CA証明書設定"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch

        # Act
        import app.core.clients as clients_mod
        result = await clients_mod.get_opensearch_client_with_auth("user:pass")

        # Assert
        call_kwargs = mock_cls.call_args[1]
        # 自前OSの場合、certifi.where()またはCA_CERTS_PATH設定値
        assert call_kwargs["ca_certs"] is not None
```

### 2.6 get_embedding_function テスト

```python
class TestGetEmbeddingFunction:
    """Embedding関数取得テスト"""

    def test_returns_embedding_when_initialized(self, mock_settings_env):
        """CLI-025: 初期化成功後→embedding返却"""
        # Arrange
        import app.core.clients as clients_mod
        mock_embedding = MagicMock()
        clients_mod.embedding_function = mock_embedding
        clients_mod.EMBEDDING_INITIALIZED = True
        clients_mod.EMBEDDING_INIT_ERROR = None

        # Act
        result = clients_mod.get_embedding_function()

        # Assert
        assert result is mock_embedding

    def test_returns_none_when_not_initialized(self, mock_settings_env):
        """CLI-028: Embedding未初期化→None返却"""
        # Arrange
        import app.core.clients as clients_mod
        clients_mod.EMBEDDING_INITIALIZED = False
        clients_mod.EMBEDDING_INIT_ERROR = None

        # Act
        result = clients_mod.get_embedding_function()

        # Assert
        assert result is None
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CLI-E01 | OPENSEARCH_URL未設定 | `URL=""` | `OS_CLIENT_INIT_ERROR=ValueError` |
| CLI-E02 | OPENSEARCH_URL不正形式 | `URL="not-a-url"` | `OS_CLIENT_INIT_ERROR=ValueError` |
| CLI-E03 | Basic認証未設定（AWS） | USER/PASS未設定、AWS URL | `OS_CLIENT_INIT_ERROR`に例外設定、`os_client=None` |
| CLI-E04 | Basic認証未設定（自前OS） | USER/PASS未設定、非AWS URL | `OS_CLIENT_INIT_ERROR`に例外設定、`os_client=None` |
| CLI-E05 | ping全失敗（max_retries回） | ping→全てFalse | `OS_CLIENT_INIT_ERROR=ConnectionError` |
| CLI-E06 | 接続例外（max_retries回） | Exception発生 | `OS_CLIENT_INIT_ERROR=Exception` |
| CLI-E07 | Embedding APIキー未設定 | `EMBEDDING_API_KEY=""` | `EMBEDDING_INIT_ERROR=ValueError` |
| CLI-E08 | Embedding モデル名未設定 | `EMBEDDING_MODEL_NAME=""` | `EMBEDDING_INIT_ERROR=ValueError` |
| CLI-E09 | Embedding BASE_URL未設定＋非OpenAIモデル | `BASE_URL=None` | `EMBEDDING_INIT_ERROR=ValueError` |
| CLI-E10 | get_opensearch_client: エラー状態→None | `INIT_ERROR`設定済み | `None` |
| CLI-E11 | get_opensearch_client_with_auth: 不正形式 | `"no-colon"` | `None` |
| CLI-E12 | get_opensearch_client_with_auth: ping失敗 | ping→False | `None` |
| CLI-E13 | get_opensearch_client_with_auth: URL未設定 | `OPENSEARCH_URL=""` | `None` |
| CLI-E14 | get_opensearch_client_with_auth: URL不正形式 | `OPENSEARCH_URL="not-a-url"` | `None` |
| CLI-E15 | get_embedding_function: エラー状態→None | `EMBEDDING_INIT_ERROR`設定済み | `None` |
| CLI-E16 | OpenAIEmbeddingsコンストラクタ例外 | コンストラクタでRuntimeError | `EMBEDDING_INIT_ERROR=RuntimeError` |
| CLI-E17 | get_opensearch_client_with_auth: 接続例外 | Exception発生 | `None` |

### 3.1 initialize_opensearch_client 異常系

```python
class TestClientsErrors:
    """クライアント初期化エラーテスト"""

    @pytest.mark.asyncio
    async def test_opensearch_url_empty(self, mock_async_opensearch):
        """CLI-E01: OPENSEARCH_URL未設定"""
        # Arrange
        env_no_url = MOCK_SETTINGS_ENV.copy()
        env_no_url["OPENSEARCH_URL"] = ""

        with patch.dict("os.environ", env_no_url, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            # Act
            import app.core.clients as clients_mod
            await clients_mod.initialize_opensearch_client(max_retries=1, retry_delay=0)

            # Assert
            assert isinstance(clients_mod.OS_CLIENT_INIT_ERROR, ValueError)
            assert "Missing OpenSearch config" in str(clients_mod.OS_CLIENT_INIT_ERROR)
            assert clients_mod.OS_CLIENT_INITIALIZED is False
            assert clients_mod.os_client is None

    @pytest.mark.asyncio
    async def test_opensearch_url_invalid_format(self, mock_async_opensearch):
        """CLI-E02: OPENSEARCH_URL不正形式"""
        # Arrange
        env_bad_url = MOCK_SETTINGS_ENV.copy()
        env_bad_url["OPENSEARCH_URL"] = "not-a-url"

        with patch.dict("os.environ", env_bad_url, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            # Act
            import app.core.clients as clients_mod
            await clients_mod.initialize_opensearch_client(max_retries=1, retry_delay=0)

            # Assert
            assert isinstance(clients_mod.OS_CLIENT_INIT_ERROR, ValueError)
            assert "OPENSEARCH_URL is invalid" in str(clients_mod.OS_CLIENT_INIT_ERROR)
            assert clients_mod.os_client is None

    @pytest.mark.asyncio
    async def test_aws_no_basic_auth(self, mock_async_opensearch):
        """CLI-E03: Basic認証未設定（AWS）"""
        # Arrange
        env_aws_no_auth = MOCK_SETTINGS_ENV.copy()
        env_aws_no_auth["OPENSEARCH_URL"] = "https://search-domain.us-east-1.es.amazonaws.com"
        env_aws_no_auth.pop("OPENSEARCH_USER", None)
        env_aws_no_auth.pop("OPENSEARCH_PASSWORD", None)
        env_aws_no_auth["OPENSEARCH_USER"] = ""
        env_aws_no_auth["OPENSEARCH_PASSWORD"] = ""

        with patch.dict("os.environ", env_aws_no_auth, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            # Act
            with patch("app.core.clients.asyncio.sleep", new_callable=AsyncMock):
                import app.core.clients as clients_mod
                await clients_mod.initialize_opensearch_client(max_retries=1, retry_delay=0)

            # Assert
            assert clients_mod.OS_CLIENT_INIT_ERROR is not None
            assert clients_mod.os_client is None

    @pytest.mark.asyncio
    async def test_self_hosted_no_basic_auth(self, mock_async_opensearch):
        """CLI-E04: Basic認証未設定（自前OS）"""
        # Arrange
        env_no_auth = MOCK_SETTINGS_ENV.copy()
        env_no_auth["OPENSEARCH_URL"] = "https://localhost:9200"
        env_no_auth["OPENSEARCH_USER"] = ""
        env_no_auth["OPENSEARCH_PASSWORD"] = ""

        with patch.dict("os.environ", env_no_auth, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            # Act
            with patch("app.core.clients.asyncio.sleep", new_callable=AsyncMock):
                import app.core.clients as clients_mod
                await clients_mod.initialize_opensearch_client(max_retries=1, retry_delay=0)

            # Assert
            assert clients_mod.OS_CLIENT_INIT_ERROR is not None
            assert clients_mod.os_client is None

    @pytest.mark.asyncio
    async def test_ping_all_failures(self, mock_settings_env, mock_async_opensearch):
        """CLI-E05: ping全失敗（max_retries回）"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch
        mock_instance.ping = AsyncMock(return_value=False)

        # Act
        with patch("app.core.clients.asyncio.sleep", new_callable=AsyncMock):
            import app.core.clients as clients_mod
            await clients_mod.initialize_opensearch_client(max_retries=3, retry_delay=0)

        # Assert
        assert clients_mod.OS_CLIENT_INIT_ERROR is not None
        assert clients_mod.OS_CLIENT_INITIALIZED is False
        assert clients_mod.os_client is None
        assert mock_instance.ping.call_count == 3

    @pytest.mark.asyncio
    async def test_connection_exception_all_retries(self, mock_settings_env, mock_async_opensearch):
        """CLI-E06: 接続例外（max_retries回）"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch
        mock_instance.ping = AsyncMock(side_effect=Exception("Connection refused"))

        # Act
        with patch("app.core.clients.asyncio.sleep", new_callable=AsyncMock):
            import app.core.clients as clients_mod
            await clients_mod.initialize_opensearch_client(max_retries=3, retry_delay=0)

        # Assert
        assert clients_mod.OS_CLIENT_INIT_ERROR is not None
        assert clients_mod.os_client is None
```

### 3.2 initialize_embedding_function 異常系

> **注**: 以下のテストメソッドは全て `TestClientsErrors` クラスに属します（セクション3.1で定義）。

```python
    # --- TestClientsErrors クラスの続き ---

    def test_embedding_api_key_empty(self):
        """CLI-E07: Embedding APIキー未設定"""
        # Arrange
        env_no_key = MOCK_SETTINGS_ENV.copy()
        env_no_key["EMBEDDING_3_LARGE_API_KEY"] = ""

        with patch.dict("os.environ", env_no_key, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            # Act
            import app.core.clients as clients_mod
            clients_mod.initialize_embedding_function()

            # Assert
            assert clients_mod.EMBEDDING_INIT_ERROR is not None
            assert clients_mod.EMBEDDING_INITIALIZED is False
            assert clients_mod.embedding_function is None

    def test_embedding_model_name_empty(self):
        """CLI-E08: Embedding モデル名未設定"""
        # Arrange
        env_no_model = MOCK_SETTINGS_ENV.copy()
        env_no_model["EMBEDDING_MODEL_NAME"] = ""

        with patch.dict("os.environ", env_no_model, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            # Act
            import app.core.clients as clients_mod
            clients_mod.initialize_embedding_function()

            # Assert
            assert clients_mod.EMBEDDING_INIT_ERROR is not None
            assert clients_mod.embedding_function is None

    def test_embedding_base_url_missing_non_openai(self):
        """CLI-E09: Embedding BASE_URL未設定＋非OpenAIモデル

        注意: config.py:44 で EMBEDDING_MODEL_BASE_URL は DOCKER_BASE_URL から
        読み込まれる（validation_alias='DOCKER_BASE_URL'）。
        DOCKER_BASE_URLはconfig.py:28でField(...)（必須）のため、
        環境変数から除外するとSettings初期化でValidationErrorになる。
        BASE_URL未設定（falsy）を再現するにはDOCKER_BASE_URLを空文字に設定する。
        """
        # Arrange
        env_no_base = MOCK_SETTINGS_ENV.copy()
        env_no_base["EMBEDDING_MODEL_NAME"] = "custom-model-v1"
        env_no_base["DOCKER_BASE_URL"] = ""  # 空文字でBASE_URL未設定（falsy）を再現

        with patch.dict("os.environ", env_no_base, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            # Act
            import app.core.clients as clients_mod
            clients_mod.initialize_embedding_function()

            # Assert
            assert clients_mod.EMBEDDING_INIT_ERROR is not None
            assert isinstance(clients_mod.EMBEDDING_INIT_ERROR, ValueError)

    def test_embedding_constructor_exception(self, mock_settings_env, mock_openai_embeddings):
        """CLI-E16: OpenAIEmbeddingsコンストラクタ例外"""
        # Arrange
        mock_cls, _ = mock_openai_embeddings
        mock_cls.side_effect = RuntimeError("API connection failed")

        # Act
        import app.core.clients as clients_mod
        clients_mod.initialize_embedding_function()

        # Assert
        assert clients_mod.EMBEDDING_INIT_ERROR is not None
        assert isinstance(clients_mod.EMBEDDING_INIT_ERROR, RuntimeError)
        assert clients_mod.EMBEDDING_INITIALIZED is False
        assert clients_mod.embedding_function is None
```

### 3.3 get_opensearch_client / get_opensearch_client_with_auth 異常系

> **注**: 以下のテストメソッドは全て `TestClientsErrors` クラスに属します（セクション3.1で定義）。

```python
    # --- TestClientsErrors クラスの続き ---

    @pytest.mark.asyncio
    async def test_get_client_returns_none_on_error_state(self, mock_settings_env):
        """CLI-E10: get_opensearch_client: エラー状態→None"""
        # Arrange
        import app.core.clients as clients_mod
        clients_mod.OS_CLIENT_INIT_ERROR = ValueError("init failed")
        clients_mod.OS_CLIENT_INITIALIZED = False

        # Act
        result = await clients_mod.get_opensearch_client()

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_auth_client_invalid_format(self, mock_settings_env):
        """CLI-E11: get_opensearch_client_with_auth: 不正形式"""
        # Act
        import app.core.clients as clients_mod
        result = await clients_mod.get_opensearch_client_with_auth("no-colon")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_auth_client_ping_failure(self, mock_settings_env, mock_async_opensearch):
        """CLI-E12: get_opensearch_client_with_auth: ping失敗"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch
        mock_instance.ping = AsyncMock(return_value=False)

        # Act
        import app.core.clients as clients_mod
        result = await clients_mod.get_opensearch_client_with_auth("user:pass")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_auth_client_url_empty(self, mock_async_opensearch):
        """CLI-E13: get_opensearch_client_with_auth: URL未設定"""
        # Arrange
        env_no_url = MOCK_SETTINGS_ENV.copy()
        env_no_url["OPENSEARCH_URL"] = ""

        with patch.dict("os.environ", env_no_url, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            # Act
            import app.core.clients as clients_mod
            result = await clients_mod.get_opensearch_client_with_auth("user:pass")

            # Assert
            assert result is None

    @pytest.mark.asyncio
    async def test_auth_client_url_invalid(self, mock_async_opensearch):
        """CLI-E14: get_opensearch_client_with_auth: URL不正形式"""
        # Arrange
        env_bad_url = MOCK_SETTINGS_ENV.copy()
        env_bad_url["OPENSEARCH_URL"] = "not-a-url"

        with patch.dict("os.environ", env_bad_url, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            # Act
            import app.core.clients as clients_mod
            result = await clients_mod.get_opensearch_client_with_auth("user:pass")

            # Assert
            assert result is None

    def test_get_embedding_returns_none_on_error_state(self, mock_settings_env):
        """CLI-E15: get_embedding_function: エラー状態→None"""
        # Arrange
        import app.core.clients as clients_mod
        clients_mod.EMBEDDING_INIT_ERROR = ValueError("init failed")
        clients_mod.EMBEDDING_INITIALIZED = False

        # Act
        result = clients_mod.get_embedding_function()

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_auth_client_connection_exception(self, mock_settings_env, mock_async_opensearch):
        """CLI-E17: get_opensearch_client_with_auth: 接続例外"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch
        mock_instance.ping = AsyncMock(side_effect=Exception("Connection timeout"))

        # Act
        import app.core.clients as clients_mod
        result = await clients_mod.get_opensearch_client_with_auth("user:pass")

        # Assert
        assert result is None
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CLI-SEC-01 | パスワードがログに出力されない | Basic認証設定 | パスワード文字列なし |
| CLI-SEC-02 | SSL常時有効 | 任意の設定 | `use_ssl=True` |
| CLI-SEC-03 | 証明書検証常時有効 | 任意の設定 | `verify_certs=True` |
| CLI-SEC-04 | localhost以外でホスト名検証有効 | hostname≠localhost | `ssl_assert_hostname=True` |
| CLI-SEC-05 | エラーメッセージに認証情報が含まれない | 接続失敗 | 認証情報未露出 |
| CLI-SEC-06 | get_opensearch_client_with_authのエラーログに認証情報なし | 接続例外 | パスワード未露出 |
| CLI-SEC-07 | get_opensearch_client_with_authでSSL設定が適用される | 認証付き接続 | `use_ssl=True`, `verify_certs=True` |
| CLI-SEC-08 | traceback出力に認証情報が含まれない | 接続例外+traceback | パスワード未露出 |
| CLI-SEC-09 | Embedding初期化traceback出力にAPIキーが含まれない | コンストラクタ例外+traceback | APIキー未露出 |
| CLI-SEC-10 | URL埋め込み認証情報がログに出力されない | `https://user:pass@host` | パスワード未露出 |
| CLI-SEC-11 | 例外メッセージに認証情報が含まれるケースのtraceback検証 | 認証情報含む例外メッセージ | パスワード未露出 |
| CLI-SEC-12 | Embedding初期化ログにAPIキーが含まれない | Embedding正常初期化 | APIキー文字列なし |
| CLI-SEC-13 | get_opensearch_client_with_authでnon-localhostホスト名検証有効 | hostname≠localhost + 認証情報 | `ssl_assert_hostname=True` |
| CLI-SEC-14 | URL不正形式エラーにURL埋め込み認証情報が含まれない | `https://user:pass@not-valid` | エラーオブジェクト/ログにパスワード未露出 |

```python
@pytest.mark.security
class TestClientsSecurity:
    """クライアントセキュリティテスト"""

    @pytest.mark.asyncio
    async def test_password_not_in_logs(self, mock_settings_env, mock_async_opensearch, caplog):
        """CLI-SEC-01: パスワード・ユーザー名がログに出力されない"""
        # Arrange
        import logging
        mock_cls, mock_instance = mock_async_opensearch

        # Act
        with caplog.at_level(logging.DEBUG):
            import app.core.clients as clients_mod
            await clients_mod.initialize_opensearch_client(max_retries=1, retry_delay=0)

        # Assert - ログにパスワード・ユーザー名が含まれないことを確認（DEBUGレベル含む）
        password = MOCK_SETTINGS_ENV["OPENSEARCH_PASSWORD"]
        username = MOCK_SETTINGS_ENV["OPENSEARCH_USER"]
        for record in caplog.records:
            msg = record.getMessage()
            # record.__dict__にもパスワードが含まれないことを確認
            record_str = str(record.__dict__)
            assert password not in msg, (
                f"ログメッセージにパスワードが含まれています: {msg}"
            )
            assert password not in record_str, (
                f"ログレコード属性にパスワードが含まれています: {record_str}"
            )
            assert username not in msg, (
                f"ログメッセージにユーザー名が含まれています: {msg}"
            )
            assert username not in record_str, (
                f"ログレコード属性にユーザー名が含まれています: {record_str}"
            )

    @pytest.mark.asyncio
    async def test_ssl_always_enabled(self, mock_settings_env, mock_async_opensearch):
        """CLI-SEC-02: SSL常時有効"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch

        # Act
        import app.core.clients as clients_mod
        await clients_mod.initialize_opensearch_client(max_retries=1, retry_delay=0)

        # Assert
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["use_ssl"] is True

    @pytest.mark.asyncio
    async def test_cert_verification_always_enabled(self, mock_settings_env, mock_async_opensearch):
        """CLI-SEC-03: 証明書検証常時有効"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch

        # Act
        import app.core.clients as clients_mod
        await clients_mod.initialize_opensearch_client(max_retries=1, retry_delay=0)

        # Assert
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["verify_certs"] is True

    @pytest.mark.asyncio
    async def test_hostname_verification_non_localhost(self, mock_async_opensearch):
        """CLI-SEC-04: localhost以外でホスト名検証有効"""
        # Arrange
        env_remote = MOCK_SETTINGS_ENV.copy()
        env_remote["OPENSEARCH_URL"] = "https://opensearch.example.com:9200"

        with patch.dict("os.environ", env_remote, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            mock_cls, mock_instance = mock_async_opensearch

            # Act
            import app.core.clients as clients_mod
            await clients_mod.initialize_opensearch_client(max_retries=1, retry_delay=0)

            # Assert
            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["ssl_assert_hostname"] is True

    @pytest.mark.asyncio
    async def test_error_message_no_credentials(self, mock_async_opensearch):
        """CLI-SEC-05: エラーメッセージに認証情報が含まれない"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch
        mock_instance.ping = AsyncMock(side_effect=Exception("Connection refused"))

        with patch.dict("os.environ", MOCK_SETTINGS_ENV, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            # Act
            with patch("app.core.clients.asyncio.sleep", new_callable=AsyncMock):
                import app.core.clients as clients_mod
                await clients_mod.initialize_opensearch_client(max_retries=1, retry_delay=0)

            # Assert - エラーメッセージに認証情報が含まれないことを確認
            error = clients_mod.OS_CLIENT_INIT_ERROR
            assert error is not None
            password = MOCK_SETTINGS_ENV["OPENSEARCH_PASSWORD"]
            username = MOCK_SETTINGS_ENV["OPENSEARCH_USER"]
            # str(), repr(), argsの全表現で検証
            for representation in [str(error), repr(error), str(error.args)]:
                assert password not in representation, (
                    f"エラー表現に認証情報が含まれています: {representation}"
                )
                assert username not in representation, (
                    f"エラー表現にユーザー名が含まれています: {representation}"
                )

    @pytest.mark.asyncio
    async def test_auth_client_error_log_no_credentials(
        self, mock_settings_env, mock_async_opensearch, caplog
    ):
        """CLI-SEC-06: get_opensearch_client_with_authのエラーログに認証情報なし"""
        # Arrange
        import logging
        mock_cls, mock_instance = mock_async_opensearch
        mock_instance.ping = AsyncMock(side_effect=Exception("Connection timeout"))

        # Act
        with caplog.at_level(logging.ERROR):
            import app.core.clients as clients_mod
            result = await clients_mod.get_opensearch_client_with_auth(
                "testuser:testpass"
            )

        # Assert - ログにパスワードが含まれないことを確認
        assert result is None
        for record in caplog.records:
            msg = record.getMessage()
            # record.__dict__にもパスワードが含まれないことを確認
            record_str = str(record.__dict__)
            assert "testpass" not in msg, (
                f"エラーログにパスワードが含まれています: {msg}"
            )
            assert "testpass" not in record_str, (
                f"ログレコード属性にパスワードが含まれています: {record_str}"
            )
            # 注意: 現在の実装（clients.py:344,347）はusernameをログ出力している。
            # セキュリティポリシーとしてユーザー名もログ出力不可とする場合は
            # 以下のアサーションを有効化し、実装側を修正する。
            # assert "testuser" not in msg, (
            #     f"エラーログにユーザー名が含まれています: {msg}"
            # )

    @pytest.mark.asyncio
    async def test_auth_client_ssl_settings(self, mock_settings_env, mock_async_opensearch):
        """CLI-SEC-07: get_opensearch_client_with_authでSSL設定が適用される"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch

        # Act
        import app.core.clients as clients_mod
        result = await clients_mod.get_opensearch_client_with_auth("user:pass")

        # Assert - SSL設定が適用されていることを確認
        assert result is not None
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["use_ssl"] is True
        assert call_kwargs["verify_certs"] is True
        assert call_kwargs["ssl_assert_hostname"] is False  # localhost

    @pytest.mark.asyncio
    async def test_traceback_no_credentials(
        self, mock_settings_env, mock_async_opensearch, capsys
    ):
        """CLI-SEC-08: traceback出力に認証情報が含まれない

        実装のtraceback.print_exc()（clients.py:196, 254）がstderrに
        パスワードやAPIキーを含むスタックトレースを出力しないことを検証。
        """
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch
        mock_instance.ping = AsyncMock(side_effect=Exception("Connection refused"))

        # Act
        with patch("app.core.clients.asyncio.sleep", new_callable=AsyncMock):
            import app.core.clients as clients_mod
            await clients_mod.initialize_opensearch_client(max_retries=1, retry_delay=0)

        # Assert - stderrにtracebackが出力されていることを確認
        captured = capsys.readouterr()
        assert "Traceback" in captured.err, (
            "traceback.print_exc()が呼ばれていません"
        )
        # パスワードが含まれないことを確認
        password = MOCK_SETTINGS_ENV["OPENSEARCH_PASSWORD"]
        assert password not in captured.err, (
            f"traceback出力にパスワードが含まれています"
        )

    @pytest.mark.asyncio
    async def test_embedding_traceback_no_api_key(
        self, mock_settings_env, mock_openai_embeddings, capsys
    ):
        """CLI-SEC-09: Embedding初期化時のtraceback出力にAPIキーが含まれない

        実装のtraceback.print_exc()（clients.py:254）がstderrに
        APIキーを含むスタックトレースを出力しないことを検証。

        制約: このテストはtraceback出力のみを検証する。APIキーは
        OpenAIEmbeddingsコンストラクタの引数として渡されるため、
        例外のスタックトレースにローカル変数として表示される可能性がある。
        ただし、テスト環境ではOpenAIEmbeddingsがモックされており、
        side_effect=RuntimeErrorの例外メッセージ自体にはAPIキーを含まない。
        実際の運用環境での漏洩リスクはCLI-SEC-11と同様に
        traceback.print_exc()のlogger.exception()への置き換えで軽減可能。
        """
        # Arrange
        mock_cls, _ = mock_openai_embeddings
        mock_cls.side_effect = RuntimeError("API connection failed")

        # Act
        import app.core.clients as clients_mod
        clients_mod.initialize_embedding_function()

        # Assert - stderrのtraceback出力にAPIキーが含まれないことを確認
        captured = capsys.readouterr()
        assert "Traceback" in captured.err, (
            "traceback.print_exc()が呼ばれていません"
        )
        api_key = MOCK_SETTINGS_ENV["EMBEDDING_3_LARGE_API_KEY"]
        assert api_key not in captured.err, (
            "Embedding初期化のtraceback出力にAPIキーが含まれています"
        )

    @pytest.mark.asyncio
    async def test_url_embedded_credentials_not_logged(
        self, mock_async_opensearch, caplog
    ):
        """CLI-SEC-10: URL埋め込み認証情報がログに出力されない

        OPENSEARCH_URLに認証情報が埋め込まれた形式（https://user:pass@host）の
        場合、ログ出力にパスワード部分が含まれないことを検証。
        clients.py:75でsettings.OPENSEARCH_URLがそのままログ出力されるため、
        URL内の認証情報漏洩リスクがある。
        """
        # Arrange
        import logging
        env_with_creds_url = MOCK_SETTINGS_ENV.copy()
        env_with_creds_url["OPENSEARCH_URL"] = "https://secret-user:secret-pass@opensearch.example.com:9200"

        with patch.dict("os.environ", env_with_creds_url, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            mock_cls, mock_instance = mock_async_opensearch

            # Act
            with caplog.at_level(logging.DEBUG):
                import app.core.clients as clients_mod
                await clients_mod.initialize_opensearch_client(max_retries=1, retry_delay=0)

        # Assert - ログにURL埋め込みパスワードが含まれないことを確認
        for record in caplog.records:
            msg = record.getMessage()
            assert "secret-pass" not in msg, (
                f"ログメッセージにURL埋め込みパスワードが含まれています: {msg}"
            )

    @pytest.mark.asyncio
    async def test_exception_message_with_credentials_not_in_traceback(
        self, mock_settings_env, mock_async_opensearch, capsys
    ):
        """CLI-SEC-11: 認証情報を含む例外メッセージのtraceback検証

        外部ライブラリが認証情報を含むエラーメッセージを生成した場合、
        traceback.print_exc()の出力にパスワードが含まれるリスクを検証。
        """
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch
        password = MOCK_SETTINGS_ENV["OPENSEARCH_PASSWORD"]
        # ライブラリが認証情報を含むエラーメッセージを生成するケースを想定
        mock_instance.ping = AsyncMock(
            side_effect=Exception(f"Connection refused to https://user:{password}@host:9200")
        )

        # Act
        with patch("app.core.clients.asyncio.sleep", new_callable=AsyncMock):
            import app.core.clients as clients_mod
            await clients_mod.initialize_opensearch_client(max_retries=1, retry_delay=0)

        # Assert - traceback出力の検証
        # 注意: 現在の実装ではtraceback.print_exc()が例外メッセージをそのまま
        # 出力するため、外部ライブラリが認証情報を含むメッセージを生成した場合は
        # 漏洩する。このテストは現在の実装では失敗する可能性がある。
        # 実装側でlogger.exception()への置き換えとメッセージのサニタイズを検討。
        captured = capsys.readouterr()
        assert "Traceback" in captured.err, (
            "traceback.print_exc()が呼ばれていません"
        )
        # tracebackに認証情報が含まれていないことを検証
        # 現在の実装では漏洩する可能性が高い（既知の制限事項）
        if password in captured.err:
            pytest.fail(
                "traceback出力に認証情報が含まれています。"
                "実装改善（logger.exception()への置き換え＋メッセージサニタイズ）を推奨。"
                "この失敗は既知の制限事項です（セクション8参照）。"
            )

    def test_embedding_init_logs_no_api_key(
        self, mock_settings_env, mock_openai_embeddings, caplog
    ):
        """CLI-SEC-12: Embedding初期化ログにAPIキーが含まれない

        initialize_embedding_function()のログ出力にAPIキー文字列が
        含まれないことを検証。clients.py:232-233でモデル名とBASE_URLは
        ログ出力されるが、APIキーは出力されないことを確認する。
        """
        # Arrange
        import logging
        mock_cls, _ = mock_openai_embeddings

        # Act
        with caplog.at_level(logging.DEBUG):
            import app.core.clients as clients_mod
            clients_mod.initialize_embedding_function()

        # Assert - ログにAPIキーが含まれないことを確認
        api_key = MOCK_SETTINGS_ENV["EMBEDDING_3_LARGE_API_KEY"]
        for record in caplog.records:
            msg = record.getMessage()
            record_str = str(record.__dict__)
            assert api_key not in msg, (
                f"Embedding初期化ログにAPIキーが含まれています: {msg}"
            )
            assert api_key not in record_str, (
                f"Embeddingログレコード属性にAPIキーが含まれています: {record_str}"
            )

    @pytest.mark.asyncio
    async def test_auth_client_hostname_verification_non_localhost(
        self, mock_async_opensearch
    ):
        """CLI-SEC-13: get_opensearch_client_with_authでnon-localhostホスト名検証有効

        get_opensearch_client_with_authでlocalhost以外のホストに接続する場合、
        ssl_assert_hostname=Trueが設定されることを検証。
        CLI-SEC-04（initialize_opensearch_client）との対称性を確保。
        """
        # Arrange
        env_remote = MOCK_SETTINGS_ENV.copy()
        env_remote["OPENSEARCH_URL"] = "https://opensearch.example.com:9200"

        with patch.dict("os.environ", env_remote, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            mock_cls, mock_instance = mock_async_opensearch

            # Act
            import app.core.clients as clients_mod
            result = await clients_mod.get_opensearch_client_with_auth("user:pass")

            # Assert
            assert result is not None
            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["ssl_assert_hostname"] is True

    @pytest.mark.asyncio
    async def test_url_invalid_format_error_no_embedded_credentials(
        self, mock_async_opensearch, caplog
    ):
        """CLI-SEC-14: URL不正形式エラーにURL埋め込み認証情報が含まれない

        clients.py:87でValueError(f"OPENSEARCH_URL is invalid: {settings.OPENSEARCH_URL}")
        が設定され、clients.py:88でlogger.errorにも出力される。
        URLに認証情報が埋め込まれている場合、エラーオブジェクトとログの両方で
        パスワードが漏洩するリスクを検証する。
        同様にclients.py:304のget_opensearch_client_with_authでも検証。
        """
        # Arrange
        import logging
        env_bad_url = MOCK_SETTINGS_ENV.copy()
        env_bad_url["OPENSEARCH_URL"] = "not-a-url-with-secret-pass"

        with patch.dict("os.environ", env_bad_url, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            # Act - initialize_opensearch_client経由
            with caplog.at_level(logging.DEBUG):
                import app.core.clients as clients_mod
                await clients_mod.initialize_opensearch_client(max_retries=1, retry_delay=0)

            # Assert - エラーオブジェクトの検証
            error = clients_mod.OS_CLIENT_INIT_ERROR
            assert error is not None
            # 注意: 現在の実装ではOPENSEARCH_URLの値がエラーメッセージに含まれる。
            # URL自体に認証情報が含まれている場合は漏洩する（既知のリスク）。
            # ここではエラーオブジェクトにパスワードが含まれうることを検知する。
            if "secret-pass" in str(error):
                pytest.fail(
                    "URL不正形式エラーにURL文字列がそのまま含まれています。"
                    "URL埋め込み認証情報がある場合に漏洩します。"
                    "実装側でURLのサニタイズを検討してください。"
                )

            # Assert - ログの検証
            for record in caplog.records:
                msg = record.getMessage()
                if "secret-pass" in msg:
                    pytest.fail(
                        f"エラーログにURL埋め込みパスワードが含まれています: {msg}"
                    )
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_clients_module` | テスト間のグローバル変数リセット（sys.modulesクリア） | function | Yes |
| `mock_settings_env` | テスト用環境変数設定＋モジュールリセット | function | No |
| `mock_async_opensearch` | AsyncOpenSearchモック（外部接続防止） | function | No |
| `mock_openai_embeddings` | OpenAIEmbeddingsモック | function | No |

### 共通フィクスチャ定義

```python
# test/unit/core/conftest.py に追加
import sys
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

# テスト用環境変数（config.pyのバリデーション通過に必要な最小セット）
MOCK_SETTINGS_ENV = {
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
    "OPENSEARCH_USER": "test-user-do-not-use",
    "OPENSEARCH_PASSWORD": "test-password-do-not-use",
    "MODEL_NAME": "gpt-5.1-chat",
}


@pytest.fixture(autouse=True)
def reset_clients_module():
    """テストごとにclientsモジュールのグローバル変数をリセット

    clients.pyのグローバル変数（os_client, OS_CLIENT_INITIALIZED等）は
    モジュールレベルで管理されているため、テスト間の独立性を保つために
    sys.modulesからapp.core系モジュールを削除して再読み込みを強制する。
    """
    yield
    modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def mock_settings_env():
    """テスト用環境変数設定＋モジュールリセット"""
    with patch.dict("os.environ", MOCK_SETTINGS_ENV, clear=False):
        modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
        for mod in modules_to_remove:
            del sys.modules[mod]
        yield


@pytest.fixture
def mock_async_opensearch():
    """AsyncOpenSearchモック（外部接続防止）

    全テストで実際のOpenSearch接続を防止するために使用。
    pingはデフォルトでTrueを返す。
    """
    with patch("app.core.clients.AsyncOpenSearch") as mock_cls:
        mock_instance = AsyncMock()
        mock_instance.ping = AsyncMock(return_value=True)
        mock_cls.return_value = mock_instance
        yield mock_cls, mock_instance


@pytest.fixture
def mock_openai_embeddings():
    """OpenAIEmbeddingsモック"""
    with patch("app.core.clients.OpenAIEmbeddings") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        yield mock_cls, mock_instance
```

---

## 6. テスト実行例

```bash
# clients関連テストのみ実行
pytest test/unit/core/test_clients.py -v

# 特定のテストクラスのみ実行
pytest test/unit/core/test_clients.py::TestExtractAwsRegion -v
pytest test/unit/core/test_clients.py::TestInitializeOpensearchClient -v
pytest test/unit/core/test_clients.py::TestInitializeEmbeddingFunction -v
pytest test/unit/core/test_clients.py::TestGetOpensearchClient -v
pytest test/unit/core/test_clients.py::TestGetOpensearchClientWithAuth -v
pytest test/unit/core/test_clients.py::TestGetEmbeddingFunction -v
pytest test/unit/core/test_clients.py::TestClientsErrors -v
pytest test/unit/core/test_clients.py::TestClientsSecurity -v

# カバレッジ付きで実行
pytest test/unit/core/test_clients.py --cov=app.core.clients --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/core/test_clients.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 29 | CLI-001 〜 CLI-029 |
| 異常系 | 17 | CLI-E01 〜 CLI-E17 |
| セキュリティ | 14 | CLI-SEC-01 〜 CLI-SEC-14 |
| **合計** | **60** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestExtractAwsRegion` | CLI-001〜CLI-004 | 4 |
| `TestInitializeOpensearchClient` | CLI-005〜CLI-014, CLI-026, CLI-029 | 12 |
| `TestInitializeEmbeddingFunction` | CLI-015〜CLI-019, CLI-027 | 6 |
| `TestGetOpensearchClient` | CLI-020〜CLI-021 | 2 |
| `TestGetOpensearchClientWithAuth` | CLI-022〜CLI-024 | 3 |
| `TestGetEmbeddingFunction` | CLI-025, CLI-028 | 2 |
| `TestClientsErrors` | CLI-E01〜CLI-E17 | 17 |
| `TestClientsSecurity` | CLI-SEC-01〜CLI-SEC-14 | 14 |

### 注意が必要なテスト

以下のテストは実装状況によって結果が変わる可能性があります。

| テストID | 特記事項 | 現在の評価 |
|---------|---------|----------|
| CLI-SEC-01 | 実装（`clients.py:81`）は`"Basic auth credentials prepared."`のみログ出力し、パスワード・ユーザー名自体は含まない。INFOレベルでは`http_auth`タプルは出力されないため、テストはパスする見込み。ユーザー名チェックにより将来のログ形式変更を検知可能 | パスする見込み |
| CLI-SEC-06 | 現在の実装（`clients.py:344,347`）は`username`をログ出力している。ユーザー名チェックはコメントアウト状態。セキュリティポリシー次第で有効化を検討 | パスする（ユーザー名チェック無効状態） |
| CLI-SEC-10 | 実装（`clients.py:75`）は`settings.OPENSEARCH_URL`をそのままログ出力する。URL埋め込み認証情報（`https://user:pass@host`形式）がある場合は漏洩する | 失敗する見込み（実装改善が必要） |
| CLI-SEC-11 | 外部ライブラリが認証情報を含む例外メッセージを生成した場合、`traceback.print_exc()`がそのまま出力する。`pytest.fail`で明示的に失敗として記録 | 失敗する見込み（実装改善推奨） |
| CLI-SEC-14 | `clients.py:87`で`ValueError`にURL文字列がそのまま含まれる。URL埋め込み認証情報がある場合はエラーオブジェクト・ログ経由で漏洩する | 失敗する見込み（実装改善が必要） |

### 注意事項

- テストは `pytest-asyncio` が必要（非同期テスト用）。`pyproject.toml`に以下の設定を推奨:
  ```toml
  [tool.pytest.ini_options]
  asyncio_mode = "auto"
  markers = ["security: セキュリティテスト"]
  ```
- `@pytest.mark.security` マーカーの使用には上記の `markers` 登録が必要
- `os.environ` のパッチは `import` **前**に適用しないと `config.py` のバリデーションに影響する
- `MOCK_SETTINGS_ENV` とフィクスチャはセクション5の `conftest.py` に一元管理する。セクション2〜4のテストコード内にも同内容を記載しているが、説明の便宜上であり、実装時は `conftest.py` からの参照に統一すること
- `config.py:112-114` の `print()` 出力にセンシティブ情報が含まれないかの検証は、本仕様書（clients_tests.md）のスコープ外。別途 `config_tests.md` で検討すること
- `traceback.print_exc()` は構造化ログと一貫性がない。将来的に `logger.exception()` への置き換えを推奨（CLI-SEC-11参照）

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | グローバル変数リセット | テスト間の独立性 | `sys.modules`クリア＋`reset_clients_module`フィクスチャ（autouse） |
| 2 | 非同期テスト | `initialize_opensearch_client`等は`async` | `pytest-asyncio`使用、`@pytest.mark.asyncio`デコレータ |
| 3 | config.py依存 | `settings`はモジュールロード時に生成 | 環境変数パッチをimport前に適用 |
| 4 | 外部接続モック | 実際のOpenSearch/OpenAI接続防止 | `AsyncOpenSearch`, `OpenAIEmbeddings`を必ずモック |
| 5 | `is_aws_opensearch_service`依存 | config.pyの関数をclientsが使用 | URL文字列でAWS判定が自動で行われることを前提にテスト |
| 6 | リトライの`asyncio.sleep` | テスト実行時間の増大 | `asyncio.sleep`をAsyncMockでモック |
| 7 | テストディレクトリ未作成 | `test/unit/core/`が未作成 | テスト実装時に`test/unit/core/`ディレクトリと`conftest.py`を作成する |
| 8 | `DOCKER_BASE_URL`必須制約 | `config.py:28`で`Field(...)`のため除外不可 | BASE_URL未設定テストでは空文字`""`で代用 |
| 9 | `validation_alias`共有 | `config.py:28`と`config.py:44`が同一の`DOCKER_BASE_URL`環境変数から値を読み込むため、一方の変更が他方に影響する | テスト時は両フィールドへの影響を考慮する |
