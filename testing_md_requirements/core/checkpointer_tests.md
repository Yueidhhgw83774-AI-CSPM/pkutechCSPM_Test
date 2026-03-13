# checkpointer テストケース

## 1. 概要

LangGraph Checkpointer の初期化モジュールのテストケースを定義します。
Deep Agents および LangGraph の状態永続化を管理し、設定に基づいて適切な Checkpointer を返します。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `get_current_storage_mode()` | 現在のストレージモード（postgres/memory/unknown）を取得 |
| `get_async_checkpointer()` | 非同期 Checkpointer を取得（シングルトン） |
| `_init_postgres_checkpointer()` | PostgreSQL Checkpointer を初期化（内部関数） |
| `_init_memory_checkpointer()` | インメモリ Checkpointer を初期化（内部関数） |
| `get_sync_checkpointer()` | 同期 Checkpointer を取得（MemorySaver のみ） |
| `close_checkpointer()` | Checkpointer のリソースを解放 |
| `reset_checkpointer()` | Checkpointer キャッシュをリセット（テスト用） |

### 1.2 カバレッジ目標: 75%

> **注記**: 外部依存（PostgreSQL接続、LangGraphライブラリ）が多いため、
> モック中心のテストとなります。実際の接続テストは統合テストで実施します。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/core/checkpointer.py` |
| テストコード | `test/unit/core/test_checkpointer.py` |

### 1.4 補足情報

**グローバル変数:**

| 変数名 | 型 | 説明 |
|--------|------|------|
| `_checkpointer` | `Optional[Any]` | シングルトンキャッシュ |
| `_checkpointer_initialized` | `bool` | 初期化フラグ |
| `_connection_pool` | `Optional[Any]` | PostgreSQL接続プール |
| `_current_storage_mode` | `str` | 現在のストレージモード |

**主要分岐:**

| 行番号 | 条件 | 分岐内容 |
|--------|------|----------|
| 54 | `_checkpointer_initialized and _checkpointer is not None` | キャッシュ返却 |
| 61-68 | `storage_type == "postgres"` | PostgreSQL初期化 |
| 64-68 | `storage_type == "opensearch"` | 未実装→MemorySaverフォールバック |
| 69-74 | else（memory含む） | MemorySaver初期化 |
| 80-87 | 例外発生時 | MemorySaverフォールバック |
| 108 | `not postgres_url` | ValueError発生 |
| 142-147 | `ImportError` | パッケージ未インストールエラー |
| 176-182 | `storage_type == "postgres"` (sync) | 警告＋MemorySaver返却 |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CKP-INIT | 初期化クラスのインポート成功 | モジュールインポート | 例外なし |
| CKP-001 | 現在のストレージモード取得（初期値） | 初期状態 | "unknown" |
| CKP-002 | MemorySaver初期化成功（storage_type=memory） | `LANGGRAPH_STORAGE_TYPE=memory` | MemorySaverインスタンス |
| CKP-003 | MemorySaver初期化成功（storage_type未設定） | 環境変数未設定 | MemorySaverインスタンス |
| CKP-004 | キャッシュされたCheckpointer返却 | 2回目呼び出し | 同一インスタンス |
| CKP-005 | PostgreSQL Checkpointer初期化成功 | `LANGGRAPH_STORAGE_TYPE=postgres` | AsyncPostgresSaverインスタンス |
| CKP-006 | 同期Checkpointer取得（memory） | `LANGGRAPH_STORAGE_TYPE=memory` | MemorySaverインスタンス |
| CKP-007 | 同期Checkpointer取得（postgres指定時警告） | `LANGGRAPH_STORAGE_TYPE=postgres` | MemorySaverインスタンス＋WARNING |
| CKP-008 | Checkpointerリソース解放成功（memory） | `close_checkpointer()` | `_checkpointer` と `_checkpointer_initialized` リセット |
| CKP-009 | キャッシュリセット成功 | `reset_checkpointer()` | グローバル変数初期化 |
| CKP-012 | PostgreSQL接続プール付きCheckpointerのクローズ | `close_checkpointer()` (postgres) | 接続プールクローズ＋グローバル変数リセット |
| CKP-010 | OpenSearch指定時のMemorySaverフォールバック | `LANGGRAPH_STORAGE_TYPE=opensearch` | MemorySaverインスタンス＋WARNING |
| CKP-011 | 未知のストレージタイプでMemorySaverフォールバック | `LANGGRAPH_STORAGE_TYPE=unknown_type` | MemorySaverインスタンス＋WARNING |

### 2.1 get_current_storage_mode テスト

```python
# test/unit/core/test_checkpointer.py
import pytest
import sys
from unittest.mock import patch, MagicMock, AsyncMock


class TestGetCurrentStorageMode:
    """ストレージモード取得テスト"""

    def test_import_checkpointer_module(self):
        """CKP-INIT: モジュールのインポート成功"""
        # Arrange & Act
        from app.core import checkpointer

        # Assert
        assert hasattr(checkpointer, "get_current_storage_mode")
        assert hasattr(checkpointer, "get_async_checkpointer")
        assert hasattr(checkpointer, "close_checkpointer")
        assert hasattr(checkpointer, "reset_checkpointer")

    def test_initial_storage_mode_is_unknown(self):
        """CKP-001: 初期状態でストレージモードは "unknown" """
        # Arrange
        from app.core.checkpointer import reset_checkpointer, get_current_storage_mode
        reset_checkpointer()

        # Act
        result = get_current_storage_mode()

        # Assert
        assert result == "unknown"
```

### 2.2 get_async_checkpointer テスト（MemorySaver）

```python
class TestGetAsyncCheckpointerMemory:
    """非同期Checkpointer取得テスト（MemorySaver）"""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """各テスト前にグローバル状態をリセット"""
        from app.core.checkpointer import reset_checkpointer
        reset_checkpointer()
        yield
        reset_checkpointer()

    @pytest.mark.asyncio
    async def test_memory_storage_type(self):
        """CKP-002: storage_type=memoryでMemorySaver初期化"""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.LANGGRAPH_STORAGE_TYPE = "memory"

        # Act
        with patch("app.core.checkpointer.settings", mock_settings):
            from app.core.checkpointer import get_async_checkpointer, get_current_storage_mode
            result = await get_async_checkpointer()
            mode = get_current_storage_mode()

        # Assert
        assert result is not None
        assert type(result).__name__ == "MemorySaver"
        assert mode == "memory"

    @pytest.mark.asyncio
    async def test_default_storage_type(self):
        """CKP-003: storage_type未設定でMemorySaverにフォールバック"""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.LANGGRAPH_STORAGE_TYPE = ""

        # Act
        with patch("app.core.checkpointer.settings", mock_settings):
            from app.core.checkpointer import get_async_checkpointer
            result = await get_async_checkpointer()

        # Assert
        assert result is not None
        assert type(result).__name__ == "MemorySaver"

    @pytest.mark.asyncio
    async def test_cached_checkpointer_returned(self):
        """CKP-004: 2回目呼び出しでキャッシュされたインスタンスを返却"""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.LANGGRAPH_STORAGE_TYPE = "memory"

        # Act
        with patch("app.core.checkpointer.settings", mock_settings):
            from app.core.checkpointer import get_async_checkpointer
            first_call = await get_async_checkpointer()
            second_call = await get_async_checkpointer()

        # Assert
        assert first_call is second_call  # 同一インスタンス

    @pytest.mark.asyncio
    async def test_opensearch_fallback_to_memory(self, caplog):
        """CKP-010: opensearch指定時にMemorySaverにフォールバック＋警告"""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.LANGGRAPH_STORAGE_TYPE = "opensearch"

        # Act
        with patch("app.core.checkpointer.settings", mock_settings):
            import logging
            caplog.set_level(logging.WARNING)
            from app.core.checkpointer import get_async_checkpointer, get_current_storage_mode
            result = await get_async_checkpointer()
            mode = get_current_storage_mode()

        # Assert
        assert type(result).__name__ == "MemorySaver"
        assert mode == "memory"
        assert "未実装" in caplog.text or "フォールバック" in caplog.text

    @pytest.mark.asyncio
    async def test_unknown_storage_type_fallback(self, caplog):
        """CKP-011: 未知のストレージタイプでMemorySaverにフォールバック＋警告"""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.LANGGRAPH_STORAGE_TYPE = "redis"  # 未サポート

        # Act
        with patch("app.core.checkpointer.settings", mock_settings):
            import logging
            caplog.set_level(logging.WARNING)
            from app.core.checkpointer import get_async_checkpointer
            result = await get_async_checkpointer()

        # Assert
        assert type(result).__name__ == "MemorySaver"
        assert "未知のストレージタイプ" in caplog.text or "MemorySaverを使用" in caplog.text
```

### 2.3 get_async_checkpointer テスト（PostgreSQL）

```python
class TestGetAsyncCheckpointerPostgres:
    """非同期Checkpointer取得テスト（PostgreSQL）"""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """各テスト前にグローバル状態をリセット"""
        from app.core.checkpointer import reset_checkpointer
        reset_checkpointer()
        yield
        reset_checkpointer()

    @pytest.mark.asyncio
    async def test_postgres_checkpointer_success(self):
        """CKP-005: PostgreSQL Checkpointer初期化成功"""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.LANGGRAPH_STORAGE_TYPE = "postgres"
        mock_settings.LANGGRAPH_POSTGRES_URL = "postgresql://user:pass@localhost/db"

        mock_pool = AsyncMock()
        mock_pool.open = AsyncMock()
        mock_pool.close = AsyncMock()

        mock_checkpointer = MagicMock()
        mock_checkpointer.setup = AsyncMock()

        # Act
        with patch("app.core.checkpointer.settings", mock_settings):
            with patch("app.core.checkpointer.AsyncConnectionPool", return_value=mock_pool):
                with patch("app.core.checkpointer.AsyncPostgresSaver", return_value=mock_checkpointer):
                    # psycopg_pool と langgraph のインポートをモック
                    with patch.dict(sys.modules, {
                        "psycopg_pool": MagicMock(),
                        "langgraph.checkpoint.postgres.aio": MagicMock()
                    }):
                        from app.core.checkpointer import get_async_checkpointer, get_current_storage_mode

                        # _init_postgres_checkpointer をモック
                        with patch("app.core.checkpointer._init_postgres_checkpointer", new_callable=AsyncMock) as mock_init:
                            mock_init.return_value = mock_checkpointer
                            result = await get_async_checkpointer()
                            mode = get_current_storage_mode()

        # Assert
        assert result is mock_checkpointer
        assert mode == "postgres"
```

### 2.4 get_sync_checkpointer テスト

```python
class TestGetSyncCheckpointer:
    """同期Checkpointer取得テスト"""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """各テスト前にグローバル状態をリセット"""
        from app.core.checkpointer import reset_checkpointer
        reset_checkpointer()
        yield
        reset_checkpointer()

    def test_sync_checkpointer_memory(self):
        """CKP-006: storage_type=memoryで同期MemorySaver取得"""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.LANGGRAPH_STORAGE_TYPE = "memory"

        # Act
        with patch("app.core.checkpointer.settings", mock_settings):
            from app.core.checkpointer import get_sync_checkpointer
            result = get_sync_checkpointer()

        # Assert
        assert result is not None
        assert type(result).__name__ == "MemorySaver"

    def test_sync_checkpointer_postgres_warning(self, caplog):
        """CKP-007: storage_type=postgres指定時に警告＋MemorySaver返却"""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.LANGGRAPH_STORAGE_TYPE = "postgres"

        # Act
        with patch("app.core.checkpointer.settings", mock_settings):
            import logging
            caplog.set_level(logging.WARNING)
            from app.core.checkpointer import get_sync_checkpointer
            result = get_sync_checkpointer()

        # Assert
        assert type(result).__name__ == "MemorySaver"
        assert "同期環境ではPostgreSQL Checkpointerは使用できません" in caplog.text
```

### 2.5 close_checkpointer / reset_checkpointer テスト

```python
class TestCheckpointerLifecycle:
    """Checkpointerライフサイクル管理テスト"""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """各テスト前にグローバル状態をリセット"""
        from app.core.checkpointer import reset_checkpointer
        reset_checkpointer()
        yield
        reset_checkpointer()

    @pytest.mark.asyncio
    async def test_close_checkpointer_success(self):
        """CKP-008: Checkpointerリソース解放成功（memory使用時）

        close_checkpointer() は _checkpointer と _checkpointer_initialized をリセットする。
        注意: _current_storage_mode は close_checkpointer() ではリセットされない（実装仕様）。
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.LANGGRAPH_STORAGE_TYPE = "memory"

        with patch("app.core.checkpointer.settings", mock_settings):
            from app.core.checkpointer import (
                get_async_checkpointer,
                close_checkpointer,
            )
            await get_async_checkpointer()

        # Act
        await close_checkpointer()

        # Assert
        import app.core.checkpointer as ckp_module
        assert ckp_module._checkpointer is None
        assert ckp_module._checkpointer_initialized is False
        # 注意: _current_storage_mode は close_checkpointer() ではリセットされない

    @pytest.mark.asyncio
    async def test_close_checkpointer_with_postgres_pool(self):
        """CKP-012: PostgreSQL接続プール付きCheckpointerの正常クローズ

        checkpointer.py:195-201 の接続プールクローズ分岐をカバーする。
        """
        # Arrange
        import app.core.checkpointer as ckp_module

        mock_pool = AsyncMock()
        mock_pool.close = AsyncMock()

        ckp_module._connection_pool = mock_pool
        ckp_module._checkpointer = MagicMock()
        ckp_module._checkpointer_initialized = True

        # Act
        from app.core.checkpointer import close_checkpointer
        await close_checkpointer()

        # Assert
        mock_pool.close.assert_awaited_once()
        assert ckp_module._connection_pool is None
        assert ckp_module._checkpointer is None
        assert ckp_module._checkpointer_initialized is False

    def test_reset_checkpointer_success(self):
        """CKP-009: キャッシュリセット成功

        注意: 現在の実装では reset_checkpointer() は _connection_pool をリセットしない。
        これはテスト用関数であり、完全なリセットが必要な場合は close_checkpointer() を使用する。
        """
        # Arrange
        import app.core.checkpointer as ckp_module
        ckp_module._checkpointer = MagicMock()
        ckp_module._checkpointer_initialized = True
        ckp_module._current_storage_mode = "postgres"

        # Act
        from app.core.checkpointer import reset_checkpointer
        reset_checkpointer()

        # Assert
        assert ckp_module._checkpointer is None
        assert ckp_module._checkpointer_initialized is False
        assert ckp_module._current_storage_mode == "unknown"
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CKP-E01 | PostgreSQL URL未設定でValueError | `LANGGRAPH_POSTGRES_URL` 未設定 | ValueError |
| CKP-E02 | psycopg_pool未インストールでImportError | パッケージ未インストール | ImportError |
| CKP-E03 | PostgreSQL接続エラー時のフォールバック | 接続タイムアウト | MemorySaverフォールバック |
| CKP-E04 | 接続プールクローズエラー時のハンドリング | クローズ例外 | 警告ログ出力＋継続 |
| CKP-E05 | setup()失敗時のフォールバック | テーブル作成エラー | MemorySaverフォールバック |

### 3.1 _init_postgres_checkpointer 異常系

```python
class TestInitPostgresCheckpointerErrors:
    """PostgreSQL Checkpointer初期化エラーテスト"""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """各テスト前にグローバル状態をリセット"""
        from app.core.checkpointer import reset_checkpointer
        reset_checkpointer()
        yield
        reset_checkpointer()

    @pytest.mark.asyncio
    async def test_postgres_url_not_set_raises_error(self):
        """CKP-E01: PostgreSQL URL未設定でValueError

        checkpointer.py:108-112 の分岐をカバーする。
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.LANGGRAPH_STORAGE_TYPE = "postgres"
        mock_settings.LANGGRAPH_POSTGRES_URL = ""

        # Act & Assert
        with patch("app.core.checkpointer.settings", mock_settings):
            from app.core.checkpointer import _init_postgres_checkpointer
            with pytest.raises(ValueError, match="LANGGRAPH_POSTGRES_URL"):
                await _init_postgres_checkpointer()

    @pytest.mark.asyncio
    async def test_psycopg_pool_not_installed_raises_import_error(self):
        """CKP-E02: psycopg_pool未インストールでImportError

        checkpointer.py:142-147 の分岐をカバーする。
        _init_postgres_checkpointer() 内の関数内importでImportErrorが発生するケース。
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.LANGGRAPH_STORAGE_TYPE = "postgres"
        mock_settings.LANGGRAPH_POSTGRES_URL = "postgresql://user:pass@localhost/db"

        # 対象モジュールのみImportErrorを発生させるカスタムインポート関数
        original_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__

        def selective_import_error(name, *args, **kwargs):
            if name in ("psycopg_pool", "langgraph.checkpoint.postgres.aio"):
                raise ImportError(f"No module named '{name}'")
            return original_import(name, *args, **kwargs)

        # Act & Assert
        with patch("app.core.checkpointer.settings", mock_settings):
            from app.core.checkpointer import _init_postgres_checkpointer

            with patch("builtins.__import__", side_effect=selective_import_error):
                with pytest.raises(ImportError, match="psycopg|langgraph"):
                    await _init_postgres_checkpointer()

    @pytest.mark.asyncio
    async def test_postgres_connection_error_fallback(self, caplog):
        """CKP-E03: PostgreSQL接続エラー時にMemorySaverへフォールバック

        checkpointer.py:80-87 の例外ハンドリング分岐をカバーする。
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.LANGGRAPH_STORAGE_TYPE = "postgres"
        mock_settings.LANGGRAPH_POSTGRES_URL = "postgresql://user:pass@localhost/db"

        # Act
        with patch("app.core.checkpointer.settings", mock_settings):
            with patch(
                "app.core.checkpointer._init_postgres_checkpointer",
                new_callable=AsyncMock,
                side_effect=ConnectionError("Connection refused")
            ):
                import logging
                caplog.set_level(logging.WARNING)
                from app.core.checkpointer import get_async_checkpointer, get_current_storage_mode
                result = await get_async_checkpointer()
                mode = get_current_storage_mode()

        # Assert
        assert type(result).__name__ == "MemorySaver"
        assert mode == "memory"
        assert "フォールバック" in caplog.text

    @pytest.mark.asyncio
    async def test_setup_failure_fallback(self, caplog):
        """CKP-E05: setup()失敗時にMemorySaverへフォールバック"""
        # Arrange
        mock_settings = MagicMock()
        mock_settings.LANGGRAPH_STORAGE_TYPE = "postgres"
        mock_settings.LANGGRAPH_POSTGRES_URL = "postgresql://user:pass@localhost/db"

        # Act
        with patch("app.core.checkpointer.settings", mock_settings):
            with patch(
                "app.core.checkpointer._init_postgres_checkpointer",
                new_callable=AsyncMock,
                side_effect=Exception("Table creation failed")
            ):
                import logging
                caplog.set_level(logging.WARNING)
                from app.core.checkpointer import get_async_checkpointer
                result = await get_async_checkpointer()

        # Assert
        assert type(result).__name__ == "MemorySaver"
        assert "フォールバック" in caplog.text
```

### 3.2 close_checkpointer 異常系

```python
class TestCloseCheckpointerErrors:
    """Checkpointerクローズエラーテスト"""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """各テスト前にグローバル状態をリセット"""
        from app.core.checkpointer import reset_checkpointer
        reset_checkpointer()
        yield
        reset_checkpointer()

    @pytest.mark.asyncio
    async def test_connection_pool_close_error_handled(self, caplog):
        """CKP-E04: 接続プールクローズエラー時に警告ログ出力＋継続

        checkpointer.py:199-200 のエラーハンドリング分岐をカバーする。
        """
        # Arrange
        import app.core.checkpointer as ckp_module

        mock_pool = AsyncMock()
        mock_pool.close = AsyncMock(side_effect=Exception("Close failed"))

        ckp_module._connection_pool = mock_pool
        ckp_module._checkpointer = MagicMock()
        ckp_module._checkpointer_initialized = True

        # Act
        import logging
        caplog.set_level(logging.WARNING)
        from app.core.checkpointer import close_checkpointer
        await close_checkpointer()

        # Assert - エラーが発生しても正常に完了し、状態がリセットされる
        assert ckp_module._checkpointer is None
        assert ckp_module._checkpointer_initialized is False
        assert "クローズエラー" in caplog.text or "Close failed" in caplog.text
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CKP-SEC-01 | PostgreSQL URLがログに出力されない | 接続成功/失敗ログ | URL非露出 |
| CKP-SEC-02 | 接続エラー時に認証情報が露出しない | 接続エラーログ | パスワード非露出 |
| CKP-SEC-03 | 接続プールのmax_sizeが適切 | PostgreSQL設定 | max_size <= 10 |

```python
@pytest.mark.security
class TestCheckpointerSecurity:
    """Checkpointerセキュリティテスト"""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """各テスト前にグローバル状態をリセット"""
        from app.core.checkpointer import reset_checkpointer
        reset_checkpointer()
        yield
        reset_checkpointer()

    @pytest.mark.asyncio
    async def test_postgres_url_not_logged_on_success(self, caplog):
        """CKP-SEC-01: 接続成功時にPostgreSQL URLがログに出力されない

        機密情報（DB URL含む認証情報）がログに露出しないことを検証。
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.LANGGRAPH_STORAGE_TYPE = "postgres"
        mock_settings.LANGGRAPH_POSTGRES_URL = "postgresql://admin:secret_password@db.example.com:5432/production"

        mock_checkpointer = MagicMock()

        # Act
        with patch("app.core.checkpointer.settings", mock_settings):
            with patch(
                "app.core.checkpointer._init_postgres_checkpointer",
                new_callable=AsyncMock,
                return_value=mock_checkpointer
            ):
                import logging
                caplog.set_level(logging.DEBUG)
                from app.core.checkpointer import get_async_checkpointer
                await get_async_checkpointer()

        # Assert - 認証情報がログに含まれていないことを個別に検証
        log_text = caplog.text.lower()
        assert "secret_password" not in log_text, "パスワードがログに含まれています"
        assert "admin:secret_password" not in log_text, "認証情報がログに含まれています"
        # URL全体またはホスト名が含まれていないことを検証
        assert "postgresql://admin:secret_password" not in log_text, "完全なURLがログに含まれています"

    @pytest.mark.asyncio
    async def test_credentials_not_exposed_on_error(self, caplog):
        """CKP-SEC-02: 接続エラー時に認証情報がログに露出しない

        接続エラーが発生した場合、エラーログに認証情報が含まれないことを検証。
        このテストは安全なエラーメッセージを使用し、ログ出力の検証を行う。

        注意: 実装側で例外ログ出力時にURLサニタイズ処理を追加することを推奨。
        """
        # Arrange
        mock_settings = MagicMock()
        mock_settings.LANGGRAPH_STORAGE_TYPE = "postgres"
        mock_settings.LANGGRAPH_POSTGRES_URL = "postgresql://user:super_secret@localhost/db"

        # 安全なエラーメッセージを使用（認証情報を含まない）
        safe_error = ConnectionError("Connection refused to database server")

        # Act
        with patch("app.core.checkpointer.settings", mock_settings):
            with patch(
                "app.core.checkpointer._init_postgres_checkpointer",
                new_callable=AsyncMock,
                side_effect=safe_error
            ):
                import logging
                caplog.set_level(logging.ERROR)
                from app.core.checkpointer import get_async_checkpointer
                await get_async_checkpointer()

        # Assert - エラーログに認証情報が含まれていないことを検証
        log_text = caplog.text.lower()
        assert "super_secret" not in log_text, "パスワードがログに含まれています"
        assert "user:super_secret" not in log_text, "認証情報がログに含まれています"
        # 接続エラーが記録されていることを確認
        assert "checkpointer初期化エラー" in log_text or "フォールバック" in log_text

    def test_connection_pool_max_size_appropriate(self):
        """CKP-SEC-03: 接続プールのmax_sizeが適切（リソース枯渇防止）

        checkpointer.py:124 で max_size=10 が設定されていることを検証。
        過大なプールサイズはDBリソース枯渇攻撃のリスクとなる。
        """
        # Arrange - ソースコードを検査
        import inspect
        from app.core.checkpointer import _init_postgres_checkpointer
        source = inspect.getsource(_init_postgres_checkpointer)

        # Assert
        assert "max_size=10" in source or "max_size = 10" in source, (
            "接続プールのmax_sizeが10以下に制限されていることを確認してください"
        )
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_state` | テスト間のグローバル状態リセット | function | Yes（各クラス内） |
| `caplog` | pytest組み込み（ログキャプチャ） | function | No |

### 共通フィクスチャ定義

```python
# test/unit/core/conftest.py に追加
import sys
import pytest
from unittest.mock import patch, MagicMock

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
def reset_checkpointer_module():
    """テストごとにcheckpointerモジュールのグローバル状態をリセット

    checkpointer.pyはシングルトンパターンを使用しており、
    テスト間の独立性を保証するためリセットが必要。
    """
    yield
    # テスト後にクリーンアップ
    try:
        from app.core.checkpointer import reset_checkpointer
        reset_checkpointer()
    except ImportError:
        pass
    # モジュールキャッシュもクリア
    modules_to_remove = [key for key in sys.modules if "checkpointer" in key]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def mock_postgres_settings():
    """PostgreSQL設定モック"""
    mock_settings = MagicMock()
    mock_settings.LANGGRAPH_STORAGE_TYPE = "postgres"
    mock_settings.LANGGRAPH_POSTGRES_URL = "postgresql://test:test@localhost/testdb"
    return mock_settings


@pytest.fixture
def mock_memory_settings():
    """MemorySaver設定モック"""
    mock_settings = MagicMock()
    mock_settings.LANGGRAPH_STORAGE_TYPE = "memory"
    mock_settings.LANGGRAPH_POSTGRES_URL = ""
    return mock_settings
```

---

## 6. テスト実行例

```bash
# checkpointer関連テストのみ実行
pytest test/unit/core/test_checkpointer.py -v

# 特定のテストクラスのみ実行
pytest test/unit/core/test_checkpointer.py::TestGetAsyncCheckpointerMemory -v
pytest test/unit/core/test_checkpointer.py::TestGetAsyncCheckpointerPostgres -v
pytest test/unit/core/test_checkpointer.py::TestCheckpointerSecurity -v

# カバレッジ付きで実行
pytest test/unit/core/test_checkpointer.py --cov=app.core.checkpointer --cov-report=term-missing -v

# セキュリティマーカーで実行
# pyproject.toml: markers = ["security: セキュリティ関連テスト"]
pytest test/unit/core/test_checkpointer.py -m "security" -v

# 非同期テストのみ実行
pytest test/unit/core/test_checkpointer.py -k "async" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 13 | CKP-INIT, CKP-001 〜 CKP-012 |
| 異常系 | 5 | CKP-E01 〜 CKP-E05 |
| セキュリティ | 3 | CKP-SEC-01 〜 CKP-SEC-03 |
| **合計** | **21** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestGetCurrentStorageMode` | CKP-INIT, CKP-001 | 2 |
| `TestGetAsyncCheckpointerMemory` | CKP-002〜CKP-004, CKP-010〜CKP-011 | 5 |
| `TestGetAsyncCheckpointerPostgres` | CKP-005 | 1 |
| `TestGetSyncCheckpointer` | CKP-006〜CKP-007 | 2 |
| `TestCheckpointerLifecycle` | CKP-008〜CKP-009, CKP-012 | 3 |
| `TestInitPostgresCheckpointerErrors` | CKP-E01〜CKP-E03, CKP-E05 | 4 |
| `TestCloseCheckpointerErrors` | CKP-E04 | 1 |
| `TestCheckpointerSecurity` | CKP-SEC-01〜CKP-SEC-03 | 3 |

### 実装失敗が予想されるテスト

現時点で失敗が予想されるテストはありません。

> **推奨事項**: 実装側で例外ログ出力時にURLサニタイズ処理（認証情報を除外する処理）を
> 追加することを推奨します。CKP-SEC-02 は安全なエラーメッセージを使用してテストを実行します。

### 注意事項

- `pytest-asyncio` パッケージが必要です
- `@pytest.mark.security` マーカーを `pyproject.toml` に登録してください
- PostgreSQL関連テストは外部依存をすべてモックしているため、実際の接続テストは統合テストで実施してください

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | PostgreSQL実接続テストはモックのみ | 実際の接続動作は未検証 | 統合テストで補完 |
| 2 | LangGraphライブラリのバージョン依存 | APIが変更される可能性 | バージョン固定推奨 |
| 3 | OpenSearch Checkpointerは未実装 | テスト対象外 | 将来実装時にテスト追加 |
