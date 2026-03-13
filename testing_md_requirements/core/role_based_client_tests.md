# role_based_client テストケース

## 1. 概要

ロールベースOpenSearchクライアント管理クラスのテストケースを定義します。最小権限の原則に基づいてOpenSearchアクセスを管理し、5つの定義されたロールに基づいて適切な権限を持つクライアントを提供します。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `OpenSearchRoles` | ロール名の定数定義クラス |
| `RoleBasedOpenSearchClient.get_client_for_role()` | 指定ロール用OpenSearchクライアント取得 |
| `RoleBasedOpenSearchClient._initialize_client_for_role()` | ロール用クライアント初期化（リトライ付き） |
| `RoleBasedOpenSearchClient.get_available_roles()` | 使用可能ロール一覧取得 |
| `RoleBasedOpenSearchClient.check_role_health()` | ロール別ヘルスチェック |
| `get_role_based_client()` | シングルトンインスタンス取得 |
| `get_client_for_role()` | 便利関数（グローバルインスタンス経由） |

### 1.2 カバレッジ目標: 75%

> **注記**: 外部依存（OpenSearch接続）が多く、リトライロジックの全パスをカバーするには時間がかかるため75%を目標とする。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/core/role_based_client.py` |
| テストコード | `test/unit/core/test_role_based_client.py` |

### 1.4 グローバル変数

| 変数名 | 型 | 役割 |
|--------|-----|------|
| `ROLE_ENV_MAPPING` | `dict` | ロール名→環境変数名マッピング |
| `_role_based_client_instance` | `Optional[RoleBasedOpenSearchClient]` | シングルトンインスタンス |

### 1.5 ロール定義

| ロール定数 | 値 | 環境変数（USER/PASSWORD） |
|-----------|-----|--------------------------|
| `CSPM_DASHBOARD_READ` | `cspm_dashboard_read_role` | `CSPM_DASHBOARD_READ_USER/PASSWORD` |
| `RAG_SEARCH_READ` | `rag_search_read_role` | `RAG_SEARCH_READ_USER/PASSWORD` |
| `DOCUMENT_WRITE` | `document_write_role` | `DOCUMENT_WRITE_USER/PASSWORD` |
| `CSPM_JOB_EXECUTION` | `cspm_job_execution_role` | `CSPM_JOB_EXEC_USER/PASSWORD` |
| `ADMIN` | `admin_role` | `OPENSEARCH_USER/PASSWORD` |

### 1.6 主要分岐

| 分岐 | 条件 | 結果 |
|------|------|------|
| ロール検証 | `role_name not in ROLE_ENV_MAPPING` | `None`返却、ログ出力 |
| 初期化済み | `_initialized_roles.get(role_name)` | キャッシュクライアント返却 |
| 初期化エラー | `_initialization_errors.get(role_name)` | `None`返却、スキップ |
| 認証情報未設定 | `not username or not password` | エラー記録、`None` |
| OPENSEARCH_URL未設定 | `not settings.OPENSEARCH_URL` | エラー記録、`None` |
| URL不正形式 | `not parsed_url.scheme or not parsed_url.hostname` | エラー記録、`None` |
| ポート決定 | URL指定 > AWS:443 > 標準:9200 | ポート番号 |
| AWS判定 | `is_aws_opensearch_service()` | SSL証明書設定 |
| CA証明書 | `OPENSEARCH_CA_CERTS_PATH`設定あり＋ファイル存在 | 指定パス使用 |
| CA証明書 | `OPENSEARCH_CA_CERTS_PATH`設定あり＋ファイル不存在 or 未設定 | SSL検証無効（開発環境） |
| リトライ | ping失敗/例外発生、試行回数<max_retries | 2秒待機してリトライ |

### 1.7 補足情報

**モック設計の重要事項:**

| 項目 | 詳細 |
|------|------|
| AsyncOpenSearchのpatchパス | `app.core.role_based_client.AsyncOpenSearch` |
| 理由 | `role_based_client.py:16` で `from opensearchpy import AsyncOpenSearch` としてインポートされるため |
| settingsのpatchパス | `app.core.role_based_client.settings` |
| is_aws_opensearch_serviceのpatchパス | `app.core.role_based_client.is_aws_opensearch_service` |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| RBC-001 | ロール定数が正しく定義されている | `OpenSearchRoles` | 5つのロール定数 |
| RBC-002 | ROLE_ENV_MAPPINGが全ロールを含む | `ROLE_ENV_MAPPING` | 5ロール分のマッピング |
| RBC-003 | 有効なロールでクライアント取得成功 | `ADMIN`ロール | `AsyncOpenSearch`インスタンス |
| RBC-004 | 初期化済みロールはキャッシュ返却 | 2回目の取得 | 同一インスタンス |
| RBC-005 | AWS OpenSearch→ポート443 | AWS URL | `port=443` |
| RBC-006 | 標準OpenSearch→ポート9200 | 非AWS URL、ポート指定なし | `port=9200` |
| RBC-007 | URL指定ポート→そのポート使用 | `https://host:9300` | `port=9300` |
| RBC-008 | AWS OpenSearch→ca_certs=None | AWS URL | `ca_certs=None` |
| RBC-009 | CA_CERTS_PATH設定あり→指定パス使用 | CA_CERTS_PATH設定 | `ca_certs=設定値` |
| RBC-010 | CA_CERTS_PATH未設定→SSL検証無効（開発環境） | CA_CERTS_PATH未設定 | `verify_certs=False` |
| RBC-011 | リトライ成功（1回目失敗、2回目成功） | ping 1回目False | 2回目で成功 |
| RBC-012 | 使用可能ロール一覧取得 | `get_available_roles()` | 5ロールのリスト |
| RBC-013 | ヘルスチェック成功 | 初期化済みロール | `status="healthy"` |
| RBC-014 | シングルトンインスタンス取得 | `get_role_based_client()` | 同一インスタンス |
| RBC-015 | 便利関数でクライアント取得 | `get_client_for_role()` | `AsyncOpenSearch`インスタンス |
| RBC-016 | localhostでホスト名検証無効 | `https://localhost:9200` | `ssl_assert_hostname=False` |
| RBC-017 | non-localhostでホスト名検証有効 | `https://example.com:9200` | `ssl_assert_hostname=True` |
| RBC-018 | CA_CERTS_PATH設定あるがファイル不存在→SSL検証無効化 | CA_CERTS_PATH設定、ファイルなし | `verify_certs=False` |

### 2.1 OpenSearchRoles テスト

```python
# test/unit/core/test_role_based_client.py
import os
import sys
import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock


class TestOpenSearchRoles:
    """ロール定数定義テスト"""

    def test_roles_constants_defined(self):
        """RBC-001: ロール定数が正しく定義されている"""
        # Arrange
        # （定数確認のため、事前準備なし）

        # Act
        from app.core.role_based_client import OpenSearchRoles

        # Assert
        assert OpenSearchRoles.CSPM_DASHBOARD_READ == "cspm_dashboard_read_role"
        assert OpenSearchRoles.RAG_SEARCH_READ == "rag_search_read_role"
        assert OpenSearchRoles.DOCUMENT_WRITE == "document_write_role"
        assert OpenSearchRoles.CSPM_JOB_EXECUTION == "cspm_job_execution_role"
        assert OpenSearchRoles.ADMIN == "admin_role"

    def test_role_env_mapping_complete(self):
        """RBC-002: ROLE_ENV_MAPPINGが全ロールを含む"""
        # Arrange
        # （マッピング確認のため、事前準備なし）

        # Act
        from app.core.role_based_client import ROLE_ENV_MAPPING, OpenSearchRoles

        # Assert
        expected_roles = [
            OpenSearchRoles.CSPM_DASHBOARD_READ,
            OpenSearchRoles.RAG_SEARCH_READ,
            OpenSearchRoles.DOCUMENT_WRITE,
            OpenSearchRoles.CSPM_JOB_EXECUTION,
            OpenSearchRoles.ADMIN,
        ]
        for role in expected_roles:
            assert role in ROLE_ENV_MAPPING
            assert "user" in ROLE_ENV_MAPPING[role]
            assert "password" in ROLE_ENV_MAPPING[role]
```

### 2.2 RoleBasedOpenSearchClient テスト

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
    "OPENSEARCH_USER": "admin-user",
    "OPENSEARCH_PASSWORD": "admin-password-do-not-use",
    "CSPM_DASHBOARD_READ_USER": "cspm-read-user",
    "CSPM_DASHBOARD_READ_PASSWORD": "cspm-read-pass-do-not-use",
    "RAG_SEARCH_READ_USER": "rag-read-user",
    "RAG_SEARCH_READ_PASSWORD": "rag-read-pass-do-not-use",
    "DOCUMENT_WRITE_USER": "doc-write-user",
    "DOCUMENT_WRITE_PASSWORD": "doc-write-pass-do-not-use",
    "CSPM_JOB_EXEC_USER": "cspm-job-user",
    "CSPM_JOB_EXEC_PASSWORD": "cspm-job-pass-do-not-use",
    "MODEL_NAME": "gpt-5.1-chat",
}


@pytest.fixture(autouse=True)
def reset_role_based_client_module():
    """テストごとにモジュールのグローバル変数をリセット

    role_based_client.pyのグローバル変数（_role_based_client_instance）は
    モジュールレベルで管理されているため、テスト間の独立性を保つために
    sys.modulesからapp.core系モジュールを削除して再読み込みを強制する。
    """
    yield
    # テスト後にモジュールキャッシュをクリア
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
    """AsyncOpenSearchモック（外部接続防止）"""
    with patch("app.core.role_based_client.AsyncOpenSearch") as mock_cls:
        mock_instance = AsyncMock()
        mock_instance.ping = AsyncMock(return_value=True)
        mock_cls.return_value = mock_instance
        yield mock_cls, mock_instance


class TestRoleBasedOpenSearchClient:
    """RoleBasedOpenSearchClientテスト"""

    @pytest.mark.asyncio
    async def test_get_client_for_valid_role(self, mock_settings_env, mock_async_opensearch):
        """RBC-003: 有効なロールでクライアント取得成功"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch

        # Act
        from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
        client_manager = RoleBasedOpenSearchClient()
        result = await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

        # Assert
        assert result is not None
        assert result is mock_instance

    @pytest.mark.asyncio
    async def test_cached_client_returned(self, mock_settings_env, mock_async_opensearch):
        """RBC-004: 初期化済みロールはキャッシュ返却"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch

        # Act
        from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
        client_manager = RoleBasedOpenSearchClient()
        result1 = await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)
        result2 = await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

        # Assert
        assert result1 is result2
        # AsyncOpenSearchは1回のみ呼ばれる（キャッシュ使用）
        assert mock_cls.call_count == 1

    @pytest.mark.asyncio
    async def test_aws_opensearch_port_443(self, mock_async_opensearch):
        """RBC-005: AWS OpenSearch→ポート443"""
        # Arrange
        aws_env = MOCK_SETTINGS_ENV.copy()
        aws_env["OPENSEARCH_URL"] = "https://search-domain.us-east-1.es.amazonaws.com"

        with patch.dict("os.environ", aws_env, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            mock_cls, mock_instance = mock_async_opensearch

            # Act
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

            # Assert
            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["hosts"][0]["port"] == 443

    @pytest.mark.asyncio
    async def test_standard_opensearch_port_9200(self, mock_settings_env, mock_async_opensearch):
        """RBC-006: 標準OpenSearch→ポート9200"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch

        # Act
        from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
        client_manager = RoleBasedOpenSearchClient()
        await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

        # Assert
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["hosts"][0]["port"] == 9200

    @pytest.mark.asyncio
    async def test_url_specified_port(self, mock_async_opensearch):
        """RBC-007: URL指定ポート→そのポート使用"""
        # Arrange
        env_with_port = MOCK_SETTINGS_ENV.copy()
        env_with_port["OPENSEARCH_URL"] = "https://localhost:9300"

        with patch.dict("os.environ", env_with_port, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            mock_cls, mock_instance = mock_async_opensearch

            # Act
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

            # Assert
            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["hosts"][0]["port"] == 9300

    @pytest.mark.asyncio
    async def test_aws_opensearch_ca_certs_none(self, mock_async_opensearch):
        """RBC-008: AWS OpenSearch→ca_certs=None"""
        # Arrange
        aws_env = MOCK_SETTINGS_ENV.copy()
        aws_env["OPENSEARCH_URL"] = "https://search-domain.us-east-1.es.amazonaws.com"

        with patch.dict("os.environ", aws_env, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            mock_cls, mock_instance = mock_async_opensearch

            # Act
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

            # Assert
            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["ca_certs"] is None

    @pytest.mark.asyncio
    async def test_ca_certs_path_configured(self, mock_async_opensearch):
        """RBC-009: CA_CERTS_PATH設定あり→指定パス使用"""
        # Arrange
        env_with_ca = MOCK_SETTINGS_ENV.copy()
        env_with_ca["OPENSEARCH_CA_CERTS_PATH"] = "/path/to/ca-cert.pem"

        with patch.dict("os.environ", env_with_ca, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            mock_cls, mock_instance = mock_async_opensearch

            # os.path.existsをモックしてパスが存在するようにする
            with patch("os.path.exists", return_value=True):
                # Act
                from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
                client_manager = RoleBasedOpenSearchClient()
                await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

            # Assert
            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["ca_certs"] == "/path/to/ca-cert.pem"

    @pytest.mark.asyncio
    async def test_no_ca_certs_path_ssl_verification_disabled(self, mock_settings_env, mock_async_opensearch):
        """RBC-010: CA_CERTS_PATH未設定→SSL検証無効（開発環境）"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch

        # Act（MOCK_SETTINGS_ENVにはOPENSEARCH_CA_CERTS_PATHが設定されていない）
        from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
        client_manager = RoleBasedOpenSearchClient()
        await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

        # Assert
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["verify_certs"] is False
        assert call_kwargs["ssl_show_warn"] is False

    @pytest.mark.asyncio
    async def test_retry_success_on_second_attempt(self, mock_settings_env, mock_async_opensearch):
        """RBC-011: リトライ成功（1回目失敗、2回目ping成功）"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch
        mock_instance.ping = AsyncMock(side_effect=[False, True])

        # Act
        with patch("asyncio.sleep", new_callable=AsyncMock):
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            result = await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

        # Assert
        assert result is not None
        assert mock_instance.ping.call_count == 2

    @pytest.mark.asyncio
    async def test_get_available_roles(self, mock_settings_env):
        """RBC-012: 使用可能ロール一覧取得"""
        # Arrange
        from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles

        # Act
        client_manager = RoleBasedOpenSearchClient()
        roles = await client_manager.get_available_roles()

        # Assert
        assert len(roles) == 5
        assert OpenSearchRoles.ADMIN in roles
        assert OpenSearchRoles.CSPM_DASHBOARD_READ in roles
        assert OpenSearchRoles.RAG_SEARCH_READ in roles
        assert OpenSearchRoles.DOCUMENT_WRITE in roles
        assert OpenSearchRoles.CSPM_JOB_EXECUTION in roles

    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_settings_env, mock_async_opensearch):
        """RBC-013: ヘルスチェック成功"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch

        # Act
        from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
        client_manager = RoleBasedOpenSearchClient()
        # まずクライアントを初期化
        await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)
        # ヘルスチェック
        health = await client_manager.check_role_health(OpenSearchRoles.ADMIN)

        # Assert
        assert health["status"] == "healthy"
        assert health["initialized"] is True
        assert health["ping_success"] is True
        assert health["error"] is None

    @pytest.mark.asyncio
    async def test_localhost_hostname_verification_disabled(self, mock_settings_env, mock_async_opensearch):
        """RBC-016: localhostでホスト名検証無効"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch

        # Act（MOCK_SETTINGS_ENVのOPENSEARCH_URLはhttps://localhost:9200）
        from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
        client_manager = RoleBasedOpenSearchClient()
        await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

        # Assert
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["ssl_assert_hostname"] is False

    @pytest.mark.asyncio
    async def test_non_localhost_hostname_verification_enabled(self, mock_async_opensearch):
        """RBC-017: non-localhostでホスト名検証有効"""
        # Arrange
        env_remote = MOCK_SETTINGS_ENV.copy()
        env_remote["OPENSEARCH_URL"] = "https://opensearch.example.com:9200"

        with patch.dict("os.environ", env_remote, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            mock_cls, mock_instance = mock_async_opensearch

            # Act
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

            # Assert
            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["ssl_assert_hostname"] is True

    @pytest.mark.asyncio
    async def test_ca_certs_path_file_not_exists(self, mock_async_opensearch):
        """RBC-018: CA_CERTS_PATH設定あるがファイル不存在→SSL検証無効化

        role_based_client.py:169 の os.path.exists() 分岐をカバーする。
        CA_CERTS_PATHが設定されていてもファイルが存在しない場合は
        SSL検証が無効化される（開発環境向けのフォールバック）。
        """
        # Arrange
        env_with_invalid_ca = MOCK_SETTINGS_ENV.copy()
        env_with_invalid_ca["OPENSEARCH_CA_CERTS_PATH"] = "/path/to/nonexistent.pem"

        with patch.dict("os.environ", env_with_invalid_ca, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            mock_cls, mock_instance = mock_async_opensearch

            # os.path.existsをモックしてファイルが存在しないようにする
            with patch("os.path.exists", return_value=False):
                # Act
                from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
                client_manager = RoleBasedOpenSearchClient()
                await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

            # Assert - ファイルが存在しない場合はSSL検証無効化
            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["verify_certs"] is False
            assert call_kwargs["ssl_show_warn"] is False
```

### 2.3 グローバル関数テスト

```python
class TestGlobalFunctions:
    """グローバル関数テスト"""

    def test_singleton_instance(self, mock_settings_env):
        """RBC-014: シングルトンインスタンス取得"""
        # Arrange
        # （シングルトン確認のため、事前準備なし）

        # Act
        from app.core.role_based_client import get_role_based_client
        instance1 = get_role_based_client()
        instance2 = get_role_based_client()

        # Assert
        assert instance1 is instance2

    @pytest.mark.asyncio
    async def test_convenience_function(self, mock_settings_env, mock_async_opensearch):
        """RBC-015: 便利関数でクライアント取得"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch

        # Act
        from app.core.role_based_client import get_client_for_role, OpenSearchRoles
        result = await get_client_for_role(OpenSearchRoles.ADMIN)

        # Assert
        assert result is not None
        assert result is mock_instance
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| RBC-E01 | 未知のロール名→None | `"unknown_role"` | `None`返却 |
| RBC-E02 | 認証情報未設定（USERNAME） | 環境変数未設定 | エラー記録、`None` |
| RBC-E03 | 認証情報未設定（PASSWORD） | 環境変数未設定 | エラー記録、`None` |
| RBC-E04 | OPENSEARCH_URL未設定 | `OPENSEARCH_URL=""` | エラー記録、`None` |
| RBC-E05 | OPENSEARCH_URL不正形式 | `"not-a-url"` | エラー記録、`None` |
| RBC-E06 | ping全失敗（max_retries回） | ping→全てFalse | エラー記録、`None` |
| RBC-E07 | 接続例外（max_retries回） | Exception発生 | エラー記録、`None` |
| RBC-E08 | 過去の初期化エラー→スキップ | エラー記録済み | `None`返却（再試行なし） |
| RBC-E09 | ヘルスチェック: 未知のロール | `"unknown_role"` | `status="invalid_role"` |
| RBC-E10 | ヘルスチェック: 初期化エラー状態 | 初期化エラー記録済み | `status="initialization_error"` |
| RBC-E11 | ヘルスチェック: ping全失敗後の初期化エラー状態 | 初期化失敗 | `status="initialization_error"`（ping全失敗でエラー記録されるため） |
| RBC-E12 | ヘルスチェック: ping失敗 | ping→False | `status="ping_failed"` |
| RBC-E13 | ヘルスチェック: 例外発生 | ping例外 | `status="error"` |

### 3.1 get_client_for_role 異常系

```python
class TestRoleBasedClientErrors:
    """RoleBasedOpenSearchClientエラーテスト"""

    @pytest.mark.asyncio
    async def test_unknown_role_returns_none(self, mock_settings_env):
        """RBC-E01: 未知のロール名→None"""
        # Arrange
        from app.core.role_based_client import RoleBasedOpenSearchClient

        # Act
        client_manager = RoleBasedOpenSearchClient()
        result = await client_manager.get_client_for_role("unknown_role")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_missing_username(self, mock_async_opensearch):
        """RBC-E02: 認証情報未設定（USERNAME）"""
        # Arrange
        env_no_user = MOCK_SETTINGS_ENV.copy()
        env_no_user["OPENSEARCH_USER"] = ""  # ADMINロールのユーザー名を空に

        with patch.dict("os.environ", env_no_user, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            # Act
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            result = await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

            # Assert
            assert result is None
            assert client_manager._initialization_errors.get(OpenSearchRoles.ADMIN) is not None

    @pytest.mark.asyncio
    async def test_missing_password(self, mock_async_opensearch):
        """RBC-E03: 認証情報未設定（PASSWORD）"""
        # Arrange
        env_no_pass = MOCK_SETTINGS_ENV.copy()
        env_no_pass["OPENSEARCH_PASSWORD"] = ""  # ADMINロールのパスワードを空に

        with patch.dict("os.environ", env_no_pass, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            # Act
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            result = await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

            # Assert
            assert result is None
            assert client_manager._initialization_errors.get(OpenSearchRoles.ADMIN) is not None

    @pytest.mark.asyncio
    async def test_opensearch_url_empty(self, mock_async_opensearch):
        """RBC-E04: OPENSEARCH_URL未設定"""
        # Arrange
        env_no_url = MOCK_SETTINGS_ENV.copy()
        env_no_url["OPENSEARCH_URL"] = ""

        with patch.dict("os.environ", env_no_url, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            # Act
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            result = await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

            # Assert
            assert result is None
            error = client_manager._initialization_errors.get(OpenSearchRoles.ADMIN)
            assert error is not None
            assert isinstance(error, ValueError)

    @pytest.mark.asyncio
    async def test_opensearch_url_invalid_format(self, mock_async_opensearch):
        """RBC-E05: OPENSEARCH_URL不正形式"""
        # Arrange
        env_bad_url = MOCK_SETTINGS_ENV.copy()
        env_bad_url["OPENSEARCH_URL"] = "not-a-url"

        with patch.dict("os.environ", env_bad_url, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            # Act
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            result = await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

            # Assert
            assert result is None
            error = client_manager._initialization_errors.get(OpenSearchRoles.ADMIN)
            assert error is not None
            assert isinstance(error, ValueError)

    @pytest.mark.asyncio
    async def test_ping_all_failures(self, mock_settings_env, mock_async_opensearch):
        """RBC-E06: ping全失敗（max_retries回）"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch
        mock_instance.ping = AsyncMock(return_value=False)

        # Act
        with patch("asyncio.sleep", new_callable=AsyncMock):
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            result = await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

        # Assert
        assert result is None
        assert mock_instance.ping.call_count == 3  # デフォルトmax_retries=3
        error = client_manager._initialization_errors.get(OpenSearchRoles.ADMIN)
        assert error is not None

    @pytest.mark.asyncio
    async def test_connection_exception_all_retries(self, mock_settings_env, mock_async_opensearch):
        """RBC-E07: 接続例外（max_retries回）"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch
        mock_instance.ping = AsyncMock(side_effect=Exception("Connection refused"))

        # Act
        with patch("asyncio.sleep", new_callable=AsyncMock):
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            result = await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

        # Assert
        assert result is None
        error = client_manager._initialization_errors.get(OpenSearchRoles.ADMIN)
        assert error is not None

    @pytest.mark.asyncio
    async def test_skip_on_previous_error(self, mock_settings_env, mock_async_opensearch):
        """RBC-E08: 過去の初期化エラー→スキップ"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch

        from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
        client_manager = RoleBasedOpenSearchClient()
        # 事前にエラーを設定
        client_manager._initialization_errors[OpenSearchRoles.ADMIN] = ValueError("previous error")

        # Act
        result = await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

        # Assert
        assert result is None
        # AsyncOpenSearchが呼ばれないことを確認（スキップ）
        mock_cls.assert_not_called()
```

### 3.2 check_role_health 異常系

```python
    # --- TestRoleBasedClientErrors クラスの続き ---

    @pytest.mark.asyncio
    async def test_health_check_unknown_role(self, mock_settings_env):
        """RBC-E09: ヘルスチェック: 未知のロール"""
        # Arrange
        from app.core.role_based_client import RoleBasedOpenSearchClient

        # Act
        client_manager = RoleBasedOpenSearchClient()
        health = await client_manager.check_role_health("unknown_role")

        # Assert
        assert health["status"] == "invalid_role"
        assert health["error"] == "未知のロール名: unknown_role"

    @pytest.mark.asyncio
    async def test_health_check_initialization_error(self, mock_settings_env):
        """RBC-E10: ヘルスチェック: 初期化エラー状態"""
        # Arrange
        from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles

        client_manager = RoleBasedOpenSearchClient()
        # 事前にエラーを設定
        client_manager._initialization_errors[OpenSearchRoles.ADMIN] = ValueError("init error")

        # Act
        health = await client_manager.check_role_health(OpenSearchRoles.ADMIN)

        # Assert
        assert health["status"] == "initialization_error"
        assert "init error" in health["error"]

    @pytest.mark.asyncio
    async def test_health_check_initialization_error_after_ping_failures(self, mock_settings_env, mock_async_opensearch):
        """RBC-E11: ヘルスチェック: ping全失敗後の初期化エラー状態

        ping全失敗でget_client_for_roleが失敗した後、check_role_healthを呼び出すと
        _initialization_errorsにエラーが記録されているため"initialization_error"になる。
        role_based_client.py:250-253 の分岐をカバーする。
        """
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch
        mock_instance.ping = AsyncMock(return_value=False)

        # Act
        with patch("asyncio.sleep", new_callable=AsyncMock):
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            # クライアント取得失敗（ping全失敗→_initialization_errorsに記録）
            await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)
            # ヘルスチェック
            health = await client_manager.check_role_health(OpenSearchRoles.ADMIN)

        # Assert - ping全失敗後は_initialization_errorsに記録されるため"initialization_error"
        assert health["status"] == "initialization_error"

    @pytest.mark.asyncio
    async def test_health_check_ping_failed(self, mock_settings_env, mock_async_opensearch):
        """RBC-E12: ヘルスチェック: ping失敗"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch
        # 初期化時は成功、ヘルスチェック時は失敗
        mock_instance.ping = AsyncMock(side_effect=[True, False])

        # Act
        from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
        client_manager = RoleBasedOpenSearchClient()
        await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)
        health = await client_manager.check_role_health(OpenSearchRoles.ADMIN)

        # Assert
        assert health["status"] == "ping_failed"
        assert health["ping_success"] is False

    @pytest.mark.asyncio
    async def test_health_check_exception(self, mock_settings_env, mock_async_opensearch):
        """RBC-E13: ヘルスチェック: 例外発生"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch
        # 初期化時は成功、ヘルスチェック時は例外
        mock_instance.ping = AsyncMock(side_effect=[True, Exception("Connection timeout")])

        # Act
        from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
        client_manager = RoleBasedOpenSearchClient()
        await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)
        health = await client_manager.check_role_health(OpenSearchRoles.ADMIN)

        # Assert
        assert health["status"] == "error"
        assert "Connection timeout" in health["error"]
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| RBC-SEC-01 | パスワードがログに出力されない | 正常初期化 | パスワード文字列なし |
| RBC-SEC-02 | SSL常時有効 | 任意の設定 | `use_ssl=True` |
| RBC-SEC-03 | 認証情報エラーメッセージに環境変数名のみ含む | 認証情報未設定 | 環境変数名のみ、パスワード値なし |
| RBC-SEC-04 | ヘルスチェックエラーにパスワードが含まれない | 例外発生 | 【実装失敗予定】パスワード未露出（現状は漏洩する） |
| RBC-SEC-05 | traceback出力に認証情報が含まれない | 接続例外 | パスワード未露出 |
| RBC-SEC-06 | 各ロールの認証情報が分離されている | 複数ロール初期化 | 各ロール固有の認証情報 |

```python
@pytest.mark.security
class TestRoleBasedClientSecurity:
    """RoleBasedOpenSearchClientセキュリティテスト"""

    @pytest.mark.asyncio
    async def test_password_not_in_logs(self, mock_settings_env, mock_async_opensearch, caplog):
        """RBC-SEC-01: パスワードがログに出力されない"""
        # Arrange
        import logging
        mock_cls, mock_instance = mock_async_opensearch

        # Act
        with caplog.at_level(logging.DEBUG):
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

        # Assert - ログにパスワードが含まれないことを確認
        password = MOCK_SETTINGS_ENV["OPENSEARCH_PASSWORD"]
        for record in caplog.records:
            msg = record.getMessage()
            record_str = str(record.__dict__)
            assert password not in msg, (
                f"ログメッセージにパスワードが含まれています: {msg}"
            )
            assert password not in record_str, (
                f"ログレコード属性にパスワードが含まれています: {record_str}"
            )

    @pytest.mark.asyncio
    async def test_ssl_always_enabled(self, mock_settings_env, mock_async_opensearch):
        """RBC-SEC-02: SSL常時有効"""
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch

        # Act
        from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
        client_manager = RoleBasedOpenSearchClient()
        await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

        # Assert
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["use_ssl"] is True

    @pytest.mark.asyncio
    async def test_credential_error_message_only_contains_env_var_names(
        self, mock_async_opensearch, caplog
    ):
        """RBC-SEC-03: 認証情報エラーメッセージに環境変数名のみ含む

        role_based_client.py:114でエラーメッセージに環境変数名が含まれるが、
        パスワードの値自体は含まれないことを検証。
        """
        # Arrange
        import logging
        env_no_pass = MOCK_SETTINGS_ENV.copy()
        env_no_pass["OPENSEARCH_PASSWORD"] = ""

        with patch.dict("os.environ", env_no_pass, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            # Act
            with caplog.at_level(logging.DEBUG):
                from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
                client_manager = RoleBasedOpenSearchClient()
                await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

            # Assert - エラーメッセージに環境変数名は含まれるがパスワード値は含まれない
            error = client_manager._initialization_errors.get(OpenSearchRoles.ADMIN)
            assert error is not None
            error_str = str(error)
            # 環境変数名は含まれることを確認
            assert "OPENSEARCH_USER" in error_str or "OPENSEARCH_PASSWORD" in error_str
            # 元のパスワード値は含まれないことを確認
            assert "admin-password-do-not-use" not in error_str

    @pytest.mark.asyncio
    async def test_health_check_error_no_password(self, mock_settings_env, mock_async_opensearch):
        """RBC-SEC-04: ヘルスチェックエラーにパスワードが含まれない

        【実装失敗予定】role_based_client.py:268 で str(e) をそのままエラーに
        格納するため、外部ライブラリが認証情報を含む例外メッセージを生成した場合に漏洩する。
        """
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch
        password = MOCK_SETTINGS_ENV["OPENSEARCH_PASSWORD"]
        # ヘルスチェック時にパスワードを含む例外を発生させる
        mock_instance.ping = AsyncMock(
            side_effect=[True, Exception(f"Auth failed for password: {password}")]
        )

        # Act
        from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
        client_manager = RoleBasedOpenSearchClient()
        await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)
        health = await client_manager.check_role_health(OpenSearchRoles.ADMIN)

        # Assert - str(e)がそのままエラーに含まれるため、漏洩する可能性がある
        # 現在の実装（role_based_client.py:268）ではstr(e)をそのまま格納
        if password in health.get("error", ""):
            pytest.fail(
                "ヘルスチェックエラーにパスワードが含まれています。"
                "実装改善（エラーメッセージのサニタイズ）を推奨。"
            )

    @pytest.mark.asyncio
    async def test_traceback_no_credentials(
        self, mock_settings_env, mock_async_opensearch, capsys
    ):
        """RBC-SEC-05: traceback出力に認証情報が含まれない

        実装のtraceback.print_exc()（role_based_client.py:210）がstderrに
        パスワードを含むスタックトレースを出力しないことを検証。
        """
        # Arrange
        mock_cls, mock_instance = mock_async_opensearch
        mock_instance.ping = AsyncMock(side_effect=Exception("Connection refused"))

        # Act
        with patch("asyncio.sleep", new_callable=AsyncMock):
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

        # Assert - stderrのtraceback出力を検証
        captured = capsys.readouterr()
        password = MOCK_SETTINGS_ENV["OPENSEARCH_PASSWORD"]
        if password in captured.err:
            pytest.fail(
                f"traceback出力にパスワードが含まれています"
            )

    @pytest.mark.asyncio
    async def test_role_credentials_isolation(self, mock_async_opensearch):
        """RBC-SEC-06: 各ロールの認証情報が分離されている

        各ロールが固有の認証情報を使用することを検証。
        """
        # Arrange
        with patch.dict("os.environ", MOCK_SETTINGS_ENV, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            mock_cls, mock_instance = mock_async_opensearch
            http_auth_calls = []

            def capture_http_auth(**kwargs):
                http_auth_calls.append(kwargs.get("http_auth"))
                return mock_instance

            mock_cls.side_effect = capture_http_auth

            # Act - 複数ロールを初期化
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)
            await client_manager.get_client_for_role(OpenSearchRoles.CSPM_DASHBOARD_READ)

        # Assert - 各ロールが異なる認証情報を使用
        assert len(http_auth_calls) == 2
        assert http_auth_calls[0] != http_auth_calls[1]
        # ADMINロール
        assert http_auth_calls[0] == ("admin-user", "admin-password-do-not-use")
        # CSPM_DASHBOARD_READロール
        assert http_auth_calls[1] == ("cspm-read-user", "cspm-read-pass-do-not-use")
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_role_based_client_module` | テスト間のグローバル変数リセット（sys.modulesクリア） | function | Yes |
| `mock_settings_env` | テスト用環境変数設定＋モジュールリセット | function | No |
| `mock_async_opensearch` | AsyncOpenSearchモック（外部接続防止） | function | No |

### 共通フィクスチャ定義

```python
# test/unit/core/conftest.py に追加（または test_role_based_client.py に直接記述）
import sys
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

# テスト用環境変数（config.pyのバリデーション通過に必要な最小セット + ロール認証情報）
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
    "OPENSEARCH_USER": "admin-user",
    "OPENSEARCH_PASSWORD": "admin-password-do-not-use",
    "CSPM_DASHBOARD_READ_USER": "cspm-read-user",
    "CSPM_DASHBOARD_READ_PASSWORD": "cspm-read-pass-do-not-use",
    "RAG_SEARCH_READ_USER": "rag-read-user",
    "RAG_SEARCH_READ_PASSWORD": "rag-read-pass-do-not-use",
    "DOCUMENT_WRITE_USER": "doc-write-user",
    "DOCUMENT_WRITE_PASSWORD": "doc-write-pass-do-not-use",
    "CSPM_JOB_EXEC_USER": "cspm-job-user",
    "CSPM_JOB_EXEC_PASSWORD": "cspm-job-pass-do-not-use",
    "MODEL_NAME": "gpt-5.1-chat",
}


@pytest.fixture(autouse=True)
def reset_role_based_client_module():
    """テストごとにモジュールのグローバル変数をリセット

    role_based_client.pyのグローバル変数（_role_based_client_instance）は
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
    with patch("app.core.role_based_client.AsyncOpenSearch") as mock_cls:
        mock_instance = AsyncMock()
        mock_instance.ping = AsyncMock(return_value=True)
        mock_cls.return_value = mock_instance
        yield mock_cls, mock_instance
```

---

## 6. テスト実行例

```bash
# role_based_client関連テストのみ実行
pytest test/unit/core/test_role_based_client.py -v

# 特定のテストクラスのみ実行
pytest test/unit/core/test_role_based_client.py::TestOpenSearchRoles -v
pytest test/unit/core/test_role_based_client.py::TestRoleBasedOpenSearchClient -v
pytest test/unit/core/test_role_based_client.py::TestGlobalFunctions -v
pytest test/unit/core/test_role_based_client.py::TestRoleBasedClientErrors -v
pytest test/unit/core/test_role_based_client.py::TestRoleBasedClientSecurity -v

# カバレッジ付きで実行
pytest test/unit/core/test_role_based_client.py --cov=app.core.role_based_client --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/core/test_role_based_client.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 18 | RBC-001 〜 RBC-018 |
| 異常系 | 13 | RBC-E01 〜 RBC-E13 |
| セキュリティ | 6 | RBC-SEC-01 〜 RBC-SEC-06 |
| **合計** | **37** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestOpenSearchRoles` | RBC-001〜RBC-002 | 2 |
| `TestRoleBasedOpenSearchClient` | RBC-003〜RBC-013, RBC-016〜RBC-018 | 14 |
| `TestGlobalFunctions` | RBC-014〜RBC-015 | 2 |
| `TestRoleBasedClientErrors` | RBC-E01〜RBC-E13 | 13 |
| `TestRoleBasedClientSecurity` | RBC-SEC-01〜RBC-SEC-06 | 6 |

### 実装失敗が予想されるテスト

以下のテストは現在の実装では**意図的に失敗**する可能性があります。

| テストID | 失敗理由 | 修正方針 |
|---------|---------|---------|
| RBC-SEC-04 | `role_based_client.py:268`で`str(e)`をそのままエラーに格納するため、外部ライブラリが認証情報を含む例外メッセージを生成した場合に漏洩する | エラーメッセージのサニタイズを実装 |

### 注意事項

- テストは `pytest-asyncio` が必要（非同期テスト用）。`pyproject.toml`に以下の設定を推奨:
  ```toml
  [tool.pytest.ini_options]
  asyncio_mode = "auto"
  markers = ["security: セキュリティテスト"]
  ```
- `@pytest.mark.security` マーカーの使用には上記の `markers` 登録が必要
- `os.environ` のパッチは `import` **前**に適用しないと `config.py` のバリデーションに影響する
- `MOCK_SETTINGS_ENV` とフィクスチャはセクション5の `conftest.py` に一元管理する
- ロール認証情報のテストでは、各ロール固有の環境変数を正しく設定すること
- `asyncio.sleep`はリトライ待機に使用されるため、テスト時はモックして高速化する

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | グローバル変数リセット | テスト間の独立性 | `sys.modules`クリア＋`reset_role_based_client_module`フィクスチャ（autouse） |
| 2 | 非同期テスト | `get_client_for_role`等は`async` | `pytest-asyncio`使用、`@pytest.mark.asyncio`デコレータ |
| 3 | config.py依存 | `settings`はモジュールロード時に生成 | 環境変数パッチをimport前に適用 |
| 4 | 外部接続モック | 実際のOpenSearch接続防止 | `AsyncOpenSearch`を必ずモック |
| 5 | `is_aws_opensearch_service`依存 | config.pyの関数を使用 | URL文字列でAWS判定が自動で行われることを前提にテスト |
| 6 | リトライの`asyncio.sleep` | テスト実行時間の増大 | `asyncio.sleep`をAsyncMockでモック |
| 7 | テストディレクトリ未作成 | `test/unit/core/`が未作成の場合 | テスト実装時にディレクトリと`conftest.py`を作成する |
| 8 | 複数ロール用環境変数 | 5ロール分の認証情報が必要 | `MOCK_SETTINGS_ENV`に全ロールの認証情報を含める |
| 9 | `traceback.print_exc()`使用 | 構造化ログと不整合 | 将来的に`logger.exception()`への置き換えを推奨 |
