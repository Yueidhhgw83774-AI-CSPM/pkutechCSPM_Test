# -*- coding: utf-8 -*-
"""
checkpointer.py のテスト。
テスト対象: app/core/checkpointer.py
テスト仕様: checkpointer_tests.md
カバレッジ目標: 75%
このテストファイルは checkpointer_tests.md 仕様書に従って記述されており、
正常系テスト、異常系テスト、セキュリティテストの3カテゴリを含む。
テストカテゴリ:
  - 正常系: 13テスト (CKP-INIT, CKP-001 ~ CKP-012)
  - 異常系: 5テスト (CKP-E01 ~ CKP-E05)
  - セキュリティテスト: 3テスト (CKP-SEC-01 ~ CKP-SEC-03)
注意: 外部依存(PostgreSQL, LangGraph)が多いため、本テストは主にmockを使用する。
"""
import os
import re
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock, PropertyMock

# psycopg_pool モジュールをモックする（ModuleNotFoundError を回避）
# 単体テストでは実際の PostgreSQL 接続は不要
if 'psycopg_pool' not in sys.modules:
    sys.modules['psycopg_pool'] = MagicMock()
    sys.modules['psycopg_pool'].AsyncConnectionPool = MagicMock

# langgraph.checkpoint.postgres モジュールをモックする
if 'langgraph.checkpoint.postgres' not in sys.modules:
    sys.modules['langgraph.checkpoint.postgres'] = MagicMock()
if 'langgraph.checkpoint.postgres.aio' not in sys.modules:
    sys.modules['langgraph.checkpoint.postgres.aio'] = MagicMock()
    sys.modules['langgraph.checkpoint.postgres.aio'].AsyncPostgresSaver = MagicMock

# ─── SourceCodeRoot を .env から読み込む ────────────────────────────────
def _load_source_root() -> str:
    """プロジェクトルートの .env から SourceCodeRoot を読み込む。"""
    # 優先度1: ルート conftest.py が os.environ に設定済みの場合
    from_env = os.environ.get("SourceCodeRoot", "").strip().strip("'\"")
    if from_env:
        return from_env
    # 優先度2: ディレクトリツリーを遡って .env ファイルを検索する
    current = Path(__file__).resolve()
    for directory in [current, *current.parents]:
        env_file = (directory if directory.is_dir() else directory.parent) / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                m = re.match(r"^\s*SourceCodeRoot\s*=\s*['\"]?(.+?)['\"]?\s*$", line)
                if m:
                    return m.group(1).strip()
    return ""

PROJECT_ROOT = _load_source_root()
if PROJECT_ROOT and PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# =============================================================================
# 正常系テスト (CKP-INIT, CKP-001 ~ CKP-012)
# =============================================================================
class TestCheckpointerImport:
    """Checkpointer 模块导入测试"""
    def test_import_checkpointer_module(self):
        """CKP-INIT: モジュールのインポート成功
        验证 checkpointer 模块可以正常导入，并且包含所需的函数和全局变量。
        """
        # Arrange & Act - プリpareとアクte
        from app.core import checkpointer
        # Assert - 結果の検証
        # 関数存在性検証
        assert hasattr(checkpointer, "get_current_storage_mode"), "缺少 get_current_storage_mode"
        assert hasattr(checkpointer, "get_async_checkpointer"), "缺少 get_async_checkpointer"
        assert hasattr(checkpointer, "get_sync_checkpointer"), "缺少 get_sync_checkpointer"
        assert hasattr(checkpointer, "close_checkpointer"), "缺少 close_checkpointer"
        assert hasattr(checkpointer, "reset_checkpointer"), "缺少 reset_checkpointer"
        # 全局変数存在性検証
        assert hasattr(checkpointer, "_checkpointer"), "缺少 _checkpointer 全局变量"
        assert hasattr(checkpointer, "_checkpointer_initialized"), "缺少 _checkpointer_initialized"
        assert hasattr(checkpointer, "_connection_pool"), "缺少 _connection_pool"
        assert hasattr(checkpointer, "_current_storage_mode"), "缺少 _current_storage_mode"
class TestGetCurrentStorageMode:
    """現在のストレージモード取得テスト"""
    def test_initial_storage_mode_is_unknown(self):
        """CKP-001: 初期状態でストレージモードは "unknown"
        覆盖代码行: checkpointer.py:27-35
        验证初始状态下，存储模式为 "unknown"。
        """
        # Arrange & Act - 設定と実行
        from app.core.checkpointer import get_current_storage_mode
        # Assert - 結果の検証
        result = get_current_storage_mode()
        assert result == "unknown", f"期望 'unknown'，实际: {result}"
class TestGetAsyncCheckpointer:
    """非同期Checkpointer取得テスト"""
    @pytest.mark.asyncio
    async def test_memory_saver_init_with_memory_type(self):
        """CKP-002: storage_type=memory で MemorySaver 初期化
        覆盖代码行: checkpointer.py:69-74
        验证当 LANGGRAPH_STORAGE_TYPE=memory 时，返回 MemorySaver 实例。
        """
        # Arrange - テストデータの準備
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LANGGRAPH_STORAGE_TYPE = "memory"
            from app.core.checkpointer import get_async_checkpointer
            import app.core.checkpointer as ckp_module
            # グローバル変数をリセットする
            ckp_module._checkpointer = None
            ckp_module._checkpointer_initialized = False
            # Act - テスト対象の関数を実行する
            result = await get_async_checkpointer()
            # アサート - 結果の検証
            assert result is not None, "返回值不应为 None"
            assert ckp_module._current_storage_mode == "memory", "存储模式应为 memory"
            # 検証対象が MemorySaver クラスである（クラス名から判断）
            assert "MemorySaver" in str(type(result).__name__), f"期望 MemorySaver，实际: {type(result)}"
    @pytest.mark.asyncio
    async def test_memory_saver_fallback_when_unset(self):
        """CKP-003: storage_type 未設定で MemorySaver にフォールバック
        覆盖代码行: checkpointer.py:69-74
        验证当未设置 LANGGRAPH_STORAGE_TYPE 时，默认使用 MemorySaver。
        """
        # Arrange - テストデータの準備
        with patch("app.core.config.settings") as mock_settings:
            # 空文字または設定されていない状態
            mock_settings.LANGGRAPH_STORAGE_TYPE = ""
            from app.core.checkpointer import get_async_checkpointer
            import app.core.checkpointer as ckp_module
            # グローバル変数をリセットする
            ckp_module._checkpointer = None
            ckp_module._checkpointer_initialized = False
            # Act - テスト対象の関数を実行する
            result = await get_async_checkpointer()
            # Assert - 結果の検証
            assert result is not None, "返回值不应为 None"
            assert ckp_module._current_storage_mode == "memory", "存储模式应为 memory"
            assert "MemorySaver" in str(type(result).__name__), "应返回 MemorySaver"
    @pytest.mark.asyncio
    async def test_cached_checkpointer_returned(self):
        """CKP-004: 2回目呼び出しでキャッシュされたインスタンスを返却
        覆盖代码行: checkpointer.py:54-55
        验证第二次调用返回缓存的实例（单例模式）。
        """
        # Arrange - テストデータの準備
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LANGGRAPH_STORAGE_TYPE = "memory"
            from app.core.checkpointer import get_async_checkpointer
            import app.core.checkpointer as ckp_module
            # グローバル変数をリセットする
            ckp_module._checkpointer = None
            ckp_module._checkpointer_initialized = False
            # Act - テスト対象の関数を実行（2回）
            first_result = await get_async_checkpointer()
            second_result = await get_async_checkpointer()
            # アサート - 結果の検証
            assert first_result is second_result, "两次调用应返回相同实例（缓存）"
            assert ckp_module._checkpointer_initialized is True, "初始化标志应为 True"
    @pytest.mark.asyncio
    async def test_postgres_checkpointer_init_success(self):
        """CKP-005: PostgreSQL Checkpointer 初期化成功
        覆盖代码行: checkpointer.py:61-63
        验证当 LANGGRAPH_STORAGE_TYPE=postgres 时，初始化 PostgreSQL Checkpointer。
        """
        # Arrange - テストデータの準備
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LANGGRAPH_STORAGE_TYPE = "postgres"
            mock_settings.LANGGRAPH_POSTGRES_URL = "postgresql://user:pass@localhost/db"
            # Mock PostgreSQL関連コンポーネント
            mock_pool = AsyncMock()
            mock_pool.open = AsyncMock()
            mock_checkpointer = AsyncMock()
            mock_checkpointer.setup = AsyncMock()
            with patch("psycopg_pool.AsyncConnectionPool", return_value=mock_pool):
                with patch("langgraph.checkpoint.postgres.aio.AsyncPostgresSaver", return_value=mock_checkpointer):
                    from app.core.checkpointer import get_async_checkpointer
                    import app.core.checkpointer as ckp_module
                    # グローバル変数をリセットする
                    ckp_module._checkpointer = None
                    ckp_module._checkpointer_initialized = False
                    # Act - テスト対象の関数を実行する
                    result = await get_async_checkpointer()
                    # アサート - 結果の検証
                    assert result is not None, "返回值不应为 None"
                    assert ckp_module._current_storage_mode == "postgres", "存储模式应为 postgres"
                    mock_pool.open.assert_called_once(), "应调用 pool.open()"
                    mock_checkpointer.setup.assert_called_once(), "应调用 checkpointer.setup()"
    @pytest.mark.asyncio
    async def test_opensearch_fallback_to_memory(self, caplog):
        """CKP-010: opensearch 指定時に MemorySaver にフォールバック＋警告
        覆盖代码行: checkpointer.py:64-68
        验证当指定 opensearch 时，输出警告并回退到 MemorySaver。
        """
        # Arrange - テストデータの準備
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LANGGRAPH_STORAGE_TYPE = "opensearch"
            from app.core.checkpointer import get_async_checkpointer
            import app.core.checkpointer as ckp_module
            # 全局変数をリセットする
            ckp_module._checkpointer = None
            ckp_module._checkpointer_initialized = False
            # Act - テスト対象の関数を実行する
            import logging
            caplog.set_level(logging.WARNING)
            result = await get_async_checkpointer()
            # アサート - 結果の検証
            assert result is not None, "返回值不应为 None"
            assert ckp_module._current_storage_mode == "memory", "存储模式应回退为 memory"
            assert "MemorySaver" in str(type(result).__name__), "应回退到 MemorySaver"
            # 警告ログを確認する
            assert any("OpenSearch" in record.message and "未実装" in record.message 
                      for record in caplog.records), "应输出 OpenSearch 未实现警告"
    @pytest.mark.asyncio
    async def test_unknown_storage_fallback_with_warning(self, caplog):
        """CKP-011: 未知のストレージタイプで MemorySaver にフォールバック＋警告
        覆盖代码行: checkpointer.py:69-74
        验证当指定未知存储类型时，输出警告并回退到 MemorySaver。
        """
        # Arrange - テストデータの準備
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LANGGRAPH_STORAGE_TYPE = "unknown_storage_type"
            from app.core.checkpointer import get_async_checkpointer
            import app.core.checkpointer as ckp_module
            # 全局変数をリセットする
            ckp_module._checkpointer = None
            ckp_module._checkpointer_initialized = False
            # Act - テスト対象の関数を実行する
            import logging
            caplog.set_level(logging.WARNING)
            result = await get_async_checkpointer()
            # Assert - 結果の検証
            assert result is not None, "返回值不应为 None"
            assert ckp_module._current_storage_mode == "memory", "存储模式应回退为 memory"
            assert "MemorySaver" in str(type(result).__name__), "应回退到 MemorySaver"
            # 警告ログを確認する
            assert any("未知のストレージタイプ" in record.message or "unknown_storage_type" in record.message 
                      for record in caplog.records), "应输出未知存储类型警告"
class TestGetSyncCheckpointer:
    """同期Checkpointer取得テスト"""
    def test_sync_checkpointer_returns_memory(self):
        """CKP-006: 同期環境で MemorySaver を返却 (storage_type=memory)
        覆盖代码行: checkpointer.py:169-185
        验证同步环境下返回 MemorySaver。
        """
        # Arrange - テストデータの準備
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LANGGRAPH_STORAGE_TYPE = "memory"
            from app.core.checkpointer import get_sync_checkpointer
            # Act - テスト対象の関数を実行する
            result = get_sync_checkpointer()
            # Assert - 結果の検証
            assert result is not None, "返回值不应为 None"
            assert "MemorySaver" in str(type(result).__name__), "应返回 MemorySaver"
    def test_sync_checkpointer_postgres_warning(self, caplog):
        """CKP-007: 同期環境で postgres 指定時に警告＋MemorySaver 返却
        覆盖代码行: checkpointer.py:176-182
        验证同步环境下指定 postgres 时，输出警告并返回 MemorySaver。
        """
        # Arrange - テストデータの準備
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LANGGRAPH_STORAGE_TYPE = "postgres"
            from app.core.checkpointer import get_sync_checkpointer
            # Act - テスト対象の関数を実行する
            import logging
            caplog.set_level(logging.WARNING)
            result = get_sync_checkpointer()
            # Assert - 結果の検証
            assert result is not None, "返回值不应为 None"
            assert "MemorySaver" in str(type(result).__name__), "应返回 MemorySaver"
            # 警告ログを確認する
            assert any("同期環境" in record.message and "PostgreSQL" in record.message 
                      for record in caplog.records), "应输出同步环境不支持 PostgreSQL 警告"
class TestCloseCheckpointer:
    """Checkpointer リソース解放テスト"""
    @pytest.mark.asyncio
    async def test_close_checkpointer_memory(self):
        """CKP-008: Checkpointer リソース解放成功 (memory)
        覆盖代码行: checkpointer.py:188-206
        验证关闭 Checkpointer 时正确重置全局变量。
        """
        # Arrange - テストデータの準備
        from app.core.checkpointer import close_checkpointer
        import app.core.checkpointer as ckp_module
        # 全局変数を設定（初期化状態を模拟する）
        ckp_module._checkpointer = MagicMock()
        ckp_module._checkpointer_initialized = True
        ckp_module._connection_pool = None
        # Act - テスト対象の関数を実行する
        await close_checkpointer()
        # Assert - 結果の検証
        assert ckp_module._checkpointer is None, "_checkpointer 应被重置为 None"
        assert ckp_module._checkpointer_initialized is False, "_checkpointer_initialized 应为 False"
    @pytest.mark.asyncio
    async def test_close_with_postgres_pool(self):
        """CKP-012: PostgreSQL 接続プール付き Checkpointer のクローズ
        覆盖代码行: checkpointer.py:194-200
        验证关闭时正确关闭 PostgreSQL 连接池。
        """
        # Arrange - テストデータの準備
        from app.core.checkpointer import close_checkpointer
        import app.core.checkpointer as ckp_module
        # 全局変数を設定（PostgreSQL接続プールを模擬）
        mock_pool = AsyncMock()
        mock_pool.close = AsyncMock()
        ckp_module._checkpointer = MagicMock()
        ckp_module._checkpointer_initialized = True
        ckp_module._connection_pool = mock_pool
        # Act - テスト対象の関数を実行する
        await close_checkpointer()
        # Assert - 結果の検証
        mock_pool.close.assert_called_once(), "应调用连接池的 close 方法"
        assert ckp_module._connection_pool is None, "_connection_pool 应被重置为 None"
        assert ckp_module._checkpointer is None, "_checkpointer 应被重置为 None"
class TestResetCheckpointer:
    """Checkpointer キャッシュリセットテスト"""
    def test_reset_checkpointer_clears_cache(self):
        """CKP-009: キャッシュリセット成功
        覆盖代码行: checkpointer.py:209-215
        验证 reset_checkpointer 正确重置所有全局变量（测试用）。
        """
        # Arrange - テストデータの準備
        from app.core.checkpointer import reset_checkpointer
        import app.core.checkpointer as ckp_module
        # 全局変数を設定（初期化状態を模拟する）
        ckp_module._checkpointer = MagicMock()
        ckp_module._checkpointer_initialized = True
        ckp_module._current_storage_mode = "postgres"
        # Act - テスト対象の関数を実行する
        reset_checkpointer()
        # アサート - 結果の検証
        assert ckp_module._checkpointer is None, "_checkpointer 应被重置"
        assert ckp_module._checkpointer_initialized is False, "_checkpointer_initialized 应为 False"
        assert ckp_module._current_storage_mode == "unknown", "_current_storage_mode 应为 unknown"
# =============================================================================
# 異常系テスト (CKP-E01 ~ CKP-E05)
# =============================================================================
class TestInitPostgresCheckpointerErrors:
    """PostgreSQL Checkpointer 初期化エラーテスト"""
    @pytest.mark.asyncio
    async def test_postgres_url_not_set_raises_value_error(self):
        """CKP-E01: PostgreSQL URL 未設定で ValueError
        覆盖代码行: checkpointer.py:108-113
        验证当 PostgreSQL URL 未设置时，抛出 ValueError 并回退到 MemorySaver。
        """
        # Arrange - テストデータの準備
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LANGGRAPH_STORAGE_TYPE = "postgres"
            mock_settings.LANGGRAPH_POSTGRES_URL = ""  # 設定されていません
            from app.core.checkpointer import get_async_checkpointer
            import app.core.checkpointer as ckp_module
            # グローバル変数をリセットする
            ckp_module._checkpointer = None
            ckp_module._checkpointer_initialized = False
            # Act - テスト対象の関数を実行する
            result = await get_async_checkpointer()
            # Assert - 結果の検証（MemorySaver に回退すべき）
            assert result is not None, "返回值不应为 None"
            assert ckp_module._current_storage_mode == "memory", "应回退到 memory 模式"
            assert "MemorySaver" in str(type(result).__name__), "应返回 MemorySaver"
    @pytest.mark.asyncio
    async def test_psycopg_not_installed_import_error(self, caplog):
        """CKP-E02: psycopg_pool 未インストールで ImportError
        覆盖代码行: checkpointer.py:142-147
        验证当 psycopg_pool 未安装时，捕获 ImportError 并回退。
        """
        # Arrange - テストデータの準備
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LANGGRAPH_STORAGE_TYPE = "postgres"
            mock_settings.LANGGRAPH_POSTGRES_URL = "postgresql://user:pass@localhost/db"
            # ImportErrorを模拟 - 修正: psycopg_pool.AsyncConnectionPoolをpatchする
            with patch("psycopg_pool.AsyncConnectionPool", side_effect=ImportError("No module named psycopg_pool")):
                from app.core.checkpointer import get_async_checkpointer
                import app.core.checkpointer as ckp_module
                # 全局変数をリセットする
                ckp_module._checkpointer = None
                ckp_module._checkpointer_initialized = False
                # Act - テスト対象の関数を実行する
                import logging
                caplog.set_level(logging.ERROR)
                result = await get_async_checkpointer()
                # Assert - 結果の検証（回復が必要）
                assert result is not None, "返回值不应为 None"
                assert ckp_module._current_storage_mode == "memory", "应回退到 memory 模式"
                # エラーログを確認する
                assert any("エラー" in record.message for record in caplog.records), "应输出错误日志"
    @pytest.mark.asyncio
    async def test_postgres_connection_error_fallback(self, caplog):
        """CKP-E03: PostgreSQL 接続エラー時に MemorySaver へフォールバック
        覆盖代码行: checkpointer.py:80-87
        验证连接错误时回退到 MemorySaver。
        """
        # Arrange - テストデータの準備
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LANGGRAPH_STORAGE_TYPE = "postgres"
            mock_settings.LANGGRAPH_POSTGRES_URL = "postgresql://user:pass@localhost/db"
            # 接続模拟失败
            mock_pool = AsyncMock()
            mock_pool.open = AsyncMock(side_effect=Exception("Connection timeout"))
            with patch("psycopg_pool.AsyncConnectionPool", return_value=mock_pool):
                from app.core.checkpointer import get_async_checkpointer
                import app.core.checkpointer as ckp_module
                # グローバル変数をリセットする
                ckp_module._checkpointer = None
                ckp_module._checkpointer_initialized = False
                # Act - テスト対象の関数を実行する
                import logging
                caplog.set_level(logging.ERROR)
                result = await get_async_checkpointer()
                # Assert - 結果の検証（回復が必要）
                assert result is not None, "返回值不应为 None"
                assert ckp_module._current_storage_mode == "memory", "应回退到 memory 模式"
                assert "MemorySaver" in str(type(result).__name__), "应回退到 MemorySaver"
                # エラーログを確認する
                assert any("エラー" in record.message for record in caplog.records), "应输出错误日志"
    @pytest.mark.asyncio
    async def test_setup_fails_fallback(self, caplog):
        """CKP-E05: setup() 失敗時に MemorySaver へフォールバック
        覆盖代码行: checkpointer.py:80-87
        验证 setup() 失败时回退到 MemorySaver。
        """
        # Arrange - テストデータの準備
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LANGGRAPH_STORAGE_TYPE = "postgres"
            mock_settings.LANGGRAPH_POSTGRES_URL = "postgresql://user:pass@localhost/db"
            # シミュレーションセットアップ失敗
            mock_pool = AsyncMock()
            mock_pool.open = AsyncMock()
            mock_checkpointer = AsyncMock()
            mock_checkpointer.setup = AsyncMock(side_effect=Exception("Table creation failed"))
            with patch("psycopg_pool.AsyncConnectionPool", return_value=mock_pool):
                with patch("langgraph.checkpoint.postgres.aio.AsyncPostgresSaver", return_value=mock_checkpointer):
                    from app.core.checkpointer import get_async_checkpointer
                    import app.core.checkpointer as ckp_module
                    # グローバル変数をリセットする
                    ckp_module._checkpointer = None
                    ckp_module._checkpointer_initialized = False
                    # Act - テスト対象の関数を実行する
                    import logging
                    caplog.set_level(logging.ERROR)
                    result = await get_async_checkpointer()
                    # Assert - 結果の検証（回復が必要）
                    assert result is not None, "返回值不应为 None"
                    assert ckp_module._current_storage_mode == "memory", "应回退到 memory 模式"
                    # エラーログを確認する
                    assert any("エラー" in record.message for record in caplog.records), "应输出错误日志"
class TestCloseCheckpointerErrors:
    """Checkpointer クローズエラーテスト"""
    @pytest.mark.asyncio
    async def test_close_pool_error_warning(self, caplog):
        """CKP-E04: 接続プールクローズエラー時に警告ログ出力＋継続
        覆盖代码行: checkpointer.py:197-199
        验证连接池关闭错误时输出警告并继续执行。
        """
        # Arrange - テストデータの準備
        from app.core.checkpointer import close_checkpointer
        import app.core.checkpointer as ckp_module
        # 接続プールのシャットダウンに失敗しました
        mock_pool = AsyncMock()
        mock_pool.close = AsyncMock(side_effect=Exception("Close failed"))
        ckp_module._checkpointer = MagicMock()
        ckp_module._checkpointer_initialized = True
        ckp_module._connection_pool = mock_pool
        # Act - テスト対象の関数を実行する
        import logging
        caplog.set_level(logging.WARNING)
        await close_checkpointer()  # 例外を投げないでください
        # Assert - 結果の検証
        # 警告ログを確認する
        assert any("クローズエラー" in record.message or "エラー" in record.message 
                  for record in caplog.records), "应输出警告日志"
        # 検証を繼續執行（全局変数がリセットされる）
        assert ckp_module._connection_pool is None, "应重置 _connection_pool"
        assert ckp_module._checkpointer is None, "应重置 _checkpointer"
# =============================================================================
# セキュリティテスト (CKP-SEC-01 ～ CKP-SEC-03)
# =============================================================================
@pytest.mark.security
class TestCheckpointerSecurity:
    """Checkpointer セキュリティテスト"""
    @pytest.mark.asyncio
    async def test_postgres_url_not_logged(self, caplog):
        """CKP-SEC-01: 接続成功時に PostgreSQL URL がログに出力されない
        验证 PostgreSQL URL（包含密码）不会出现在日志中。
        """
        # Arrange - テストデータの準備
        sensitive_url = "postgresql://user:SecretP@ssw0rd@localhost/db"
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LANGGRAPH_STORAGE_TYPE = "postgres"
            mock_settings.LANGGRAPH_POSTGRES_URL = sensitive_url
            # Mock PostgreSQL コンポーネント
            mock_pool = AsyncMock()
            mock_pool.open = AsyncMock()
            mock_checkpointer = AsyncMock()
            mock_checkpointer.setup = AsyncMock()
            with patch("psycopg_pool.AsyncConnectionPool", return_value=mock_pool):
                with patch("langgraph.checkpoint.postgres.aio.AsyncPostgresSaver", return_value=mock_checkpointer):
                    from app.core.checkpointer import get_async_checkpointer
                    import app.core.checkpointer as ckp_module
                    # グローバル変数をリセットする
                    ckp_module._checkpointer = None
                    ckp_module._checkpointer_initialized = False
                    # Act - テスト対象の関数を実行する
                    import logging
                    caplog.set_level(logging.DEBUG)
                    result = await get_async_checkpointer()
                    # Assert - 結果の検証
                    # URLがログに出てこないことを確認する
                    log_text = "\n".join([record.message for record in caplog.records])
                    assert "SecretP@ssw0rd" not in log_text, "密码不应出现在日志中"
                    assert sensitive_url not in log_text, "完整URL不应出现在日志中"
    @pytest.mark.asyncio
    async def test_credentials_not_exposed_on_error(self, caplog):
        """CKP-SEC-02: 接続エラー時に認証情報がログに露出しない
        验证连接错误时，认证信息不会泄露到日志中。
        """
        # Arrange - テストデータの準備
        sensitive_url = "postgresql://admin:TopSecret123@db.example.com/production"
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LANGGRAPH_STORAGE_TYPE = "postgres"
            mock_settings.LANGGRAPH_POSTGRES_URL = sensitive_url
            # 接続模拟失败
            mock_pool = AsyncMock()
            mock_pool.open = AsyncMock(side_effect=Exception("Authentication failed"))
            with patch("psycopg_pool.AsyncConnectionPool", return_value=mock_pool):
                from app.core.checkpointer import get_async_checkpointer
                import app.core.checkpointer as ckp_module
                # 全局変数をリセットする
                ckp_module._checkpointer = None
                ckp_module._checkpointer_initialized = False
                # Act - テスト対象の関数を実行する
                import logging
                caplog.set_level(logging.ERROR)
                result = await get_async_checkpointer()
                # Assert - 結果の検証
                # 敏感情報がログに出ていないことを確認する
                log_text = "\n".join([record.message for record in caplog.records])
                assert "TopSecret123" not in log_text, "密码不应出现在错误日志中"
                assert "admin" not in log_text or "admin@" not in log_text, "用户名不应与密码一起出现"
                assert sensitive_url not in log_text, "完整URL不应出现在错误日志中"
    @pytest.mark.asyncio
    async def test_connection_pool_max_size_limit(self):
        """CKP-SEC-03: 接続プールの max_size が適切（リソース枯渇防止）
        验证连接池的 max_size 限制在合理范围内（防止资源耗尽）。
        """
        # Arrange - テストデータの準備
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LANGGRAPH_STORAGE_TYPE = "postgres"
            mock_settings.LANGGRAPH_POSTGRES_URL = "postgresql://user:pass@localhost/db"
            # AsyncConnectionPoolの呼び出しパラメータをキャプチャする
            actual_max_size = None
            def capture_pool_args(*args, **kwargs):
                nonlocal actual_max_size
                actual_max_size = kwargs.get("max_size")
                mock_pool = AsyncMock()
                mock_pool.open = AsyncMock()
                return mock_pool
            mock_checkpointer = AsyncMock()
            mock_checkpointer.setup = AsyncMock()
            with patch("psycopg_pool.AsyncConnectionPool", side_effect=capture_pool_args):
                with patch("langgraph.checkpoint.postgres.aio.AsyncPostgresSaver", return_value=mock_checkpointer):
                    from app.core.checkpointer import get_async_checkpointer
                    import app.core.checkpointer as ckp_module
                    # グローバル変数をリセットする
                    ckp_module._checkpointer = None
                    ckp_module._checkpointer_initialized = False
                    # Act - テスト対象の関数を実行する
                    result = await get_async_checkpointer()
                    # Assert - 結果の検証
                    assert actual_max_size is not None, "应设置 max_size"
                    assert actual_max_size <= 10, f"max_size 应 <= 10（防止资源耗尽），实际: {actual_max_size}"
                    assert actual_max_size > 0, f"max_size 应 > 0，实际: {actual_max_size}"
# =============================================================================
# Main Entry Point
# =============================================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
