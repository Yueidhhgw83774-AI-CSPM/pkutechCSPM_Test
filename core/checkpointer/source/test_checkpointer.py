# -*- coding: utf-8 -*-
"""
checkpointer.py 单元测试
测试对象: app/core/checkpointer.py
测试规格: checkpointer_tests.md
覆盖率目标: 75%
本测试文件严格按照 checkpointer_tests.md 测试规格文档编写，
包含正常系测试、异常系测试和安全测试三大类。
测试类别:
  - 正常系: 13 个测试 (CKP-INIT, CKP-001 ~ CKP-012)
  - 异常系: 5 个测试 (CKP-E01 ~ CKP-E05)
  - 安全测试: 3 个测试 (CKP-SEC-01 ~ CKP-SEC-03)
注意: 由于外部依赖(PostgreSQL, LangGraph)较多，本测试主要使用 mock。
"""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock, PropertyMock

# Mock psycopg_pool 模块（避免 ModuleNotFoundError）
# 因为这是单元测试，不需要真实的 PostgreSQL 连接
if 'psycopg_pool' not in sys.modules:
    sys.modules['psycopg_pool'] = MagicMock()
    sys.modules['psycopg_pool'].AsyncConnectionPool = MagicMock

# Mock langgraph.checkpoint.postgres 模块
if 'langgraph.checkpoint.postgres' not in sys.modules:
    sys.modules['langgraph.checkpoint.postgres'] = MagicMock()
if 'langgraph.checkpoint.postgres.aio' not in sys.modules:
    sys.modules['langgraph.checkpoint.postgres.aio'] = MagicMock()
    sys.modules['langgraph.checkpoint.postgres.aio'].AsyncPostgresSaver = MagicMock

# Add project root to path
# 添加项目根目录到路径
PROJECT_ROOT = r"C:\pythonProject\python_ai_cspm\platform_python_backend-testing"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# =============================================================================
# 正常系测试 (CKP-INIT, CKP-001 ~ CKP-012)
# =============================================================================
class TestCheckpointerImport:
    """Checkpointer 模块导入测试"""
    def test_import_checkpointer_module(self):
        """CKP-INIT: モジュールのインポート成功
        验证 checkpointer 模块可以正常导入，并且包含所需的函数和全局变量。
        """
        # Arrange & Act - 准备并执行
        from app.core import checkpointer
        # Assert - 验证结果
        # 函数存在性验证
        assert hasattr(checkpointer, "get_current_storage_mode"), "缺少 get_current_storage_mode"
        assert hasattr(checkpointer, "get_async_checkpointer"), "缺少 get_async_checkpointer"
        assert hasattr(checkpointer, "get_sync_checkpointer"), "缺少 get_sync_checkpointer"
        assert hasattr(checkpointer, "close_checkpointer"), "缺少 close_checkpointer"
        assert hasattr(checkpointer, "reset_checkpointer"), "缺少 reset_checkpointer"
        # 全局变量存在性验证
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
        # Arrange & Act - 准备并执行
        from app.core.checkpointer import get_current_storage_mode
        # Assert - 验证结果
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
        # Arrange - 准备测试数据
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LANGGRAPH_STORAGE_TYPE = "memory"
            from app.core.checkpointer import get_async_checkpointer
            import app.core.checkpointer as ckp_module
            # 重置全局变量
            ckp_module._checkpointer = None
            ckp_module._checkpointer_initialized = False
            # Act - 执行被测试函数
            result = await get_async_checkpointer()
            # Assert - 验证结果
            assert result is not None, "返回值不应为 None"
            assert ckp_module._current_storage_mode == "memory", "存储模式应为 memory"
            # 验证是 MemorySaver 类型（通过类名）
            assert "MemorySaver" in str(type(result).__name__), f"期望 MemorySaver，实际: {type(result)}"
    @pytest.mark.asyncio
    async def test_memory_saver_fallback_when_unset(self):
        """CKP-003: storage_type 未設定で MemorySaver にフォールバック
        覆盖代码行: checkpointer.py:69-74
        验证当未设置 LANGGRAPH_STORAGE_TYPE 时，默认使用 MemorySaver。
        """
        # Arrange - 准备测试数据
        with patch("app.core.config.settings") as mock_settings:
            # 空字符串或未设置
            mock_settings.LANGGRAPH_STORAGE_TYPE = ""
            from app.core.checkpointer import get_async_checkpointer
            import app.core.checkpointer as ckp_module
            # 重置全局变量
            ckp_module._checkpointer = None
            ckp_module._checkpointer_initialized = False
            # Act - 执行被测试函数
            result = await get_async_checkpointer()
            # Assert - 验证结果
            assert result is not None, "返回值不应为 None"
            assert ckp_module._current_storage_mode == "memory", "存储模式应为 memory"
            assert "MemorySaver" in str(type(result).__name__), "应返回 MemorySaver"
    @pytest.mark.asyncio
    async def test_cached_checkpointer_returned(self):
        """CKP-004: 2回目呼び出しでキャッシュされたインスタンスを返却
        覆盖代码行: checkpointer.py:54-55
        验证第二次调用返回缓存的实例（单例模式）。
        """
        # Arrange - 准备测试数据
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LANGGRAPH_STORAGE_TYPE = "memory"
            from app.core.checkpointer import get_async_checkpointer
            import app.core.checkpointer as ckp_module
            # 重置全局变量
            ckp_module._checkpointer = None
            ckp_module._checkpointer_initialized = False
            # Act - 执行被测试函数（两次）
            first_result = await get_async_checkpointer()
            second_result = await get_async_checkpointer()
            # Assert - 验证结果
            assert first_result is second_result, "两次调用应返回相同实例（缓存）"
            assert ckp_module._checkpointer_initialized is True, "初始化标志应为 True"
    @pytest.mark.asyncio
    async def test_postgres_checkpointer_init_success(self):
        """CKP-005: PostgreSQL Checkpointer 初期化成功
        覆盖代码行: checkpointer.py:61-63
        验证当 LANGGRAPH_STORAGE_TYPE=postgres 时，初始化 PostgreSQL Checkpointer。
        """
        # Arrange - 准备测试数据
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LANGGRAPH_STORAGE_TYPE = "postgres"
            mock_settings.LANGGRAPH_POSTGRES_URL = "postgresql://user:pass@localhost/db"
            # Mock PostgreSQL 相关组件
            mock_pool = AsyncMock()
            mock_pool.open = AsyncMock()
            mock_checkpointer = AsyncMock()
            mock_checkpointer.setup = AsyncMock()
            with patch("psycopg_pool.AsyncConnectionPool", return_value=mock_pool):
                with patch("langgraph.checkpoint.postgres.aio.AsyncPostgresSaver", return_value=mock_checkpointer):
                    from app.core.checkpointer import get_async_checkpointer
                    import app.core.checkpointer as ckp_module
                    # 重置全局变量
                    ckp_module._checkpointer = None
                    ckp_module._checkpointer_initialized = False
                    # Act - 执行被测试函数
                    result = await get_async_checkpointer()
                    # Assert - 验证结果
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
        # Arrange - 准备测试数据
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LANGGRAPH_STORAGE_TYPE = "opensearch"
            from app.core.checkpointer import get_async_checkpointer
            import app.core.checkpointer as ckp_module
            # 重置全局变量
            ckp_module._checkpointer = None
            ckp_module._checkpointer_initialized = False
            # Act - 执行被测试函数
            import logging
            caplog.set_level(logging.WARNING)
            result = await get_async_checkpointer()
            # Assert - 验证结果
            assert result is not None, "返回值不应为 None"
            assert ckp_module._current_storage_mode == "memory", "存储模式应回退为 memory"
            assert "MemorySaver" in str(type(result).__name__), "应回退到 MemorySaver"
            # 验证警告日志
            assert any("OpenSearch" in record.message and "未実装" in record.message 
                      for record in caplog.records), "应输出 OpenSearch 未实现警告"
    @pytest.mark.asyncio
    async def test_unknown_storage_fallback_with_warning(self, caplog):
        """CKP-011: 未知のストレージタイプで MemorySaver にフォールバック＋警告
        覆盖代码行: checkpointer.py:69-74
        验证当指定未知存储类型时，输出警告并回退到 MemorySaver。
        """
        # Arrange - 准备测试数据
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LANGGRAPH_STORAGE_TYPE = "unknown_storage_type"
            from app.core.checkpointer import get_async_checkpointer
            import app.core.checkpointer as ckp_module
            # 重置全局变量
            ckp_module._checkpointer = None
            ckp_module._checkpointer_initialized = False
            # Act - 执行被测试函数
            import logging
            caplog.set_level(logging.WARNING)
            result = await get_async_checkpointer()
            # Assert - 验证结果
            assert result is not None, "返回值不应为 None"
            assert ckp_module._current_storage_mode == "memory", "存储模式应回退为 memory"
            assert "MemorySaver" in str(type(result).__name__), "应回退到 MemorySaver"
            # 验证警告日志
            assert any("未知のストレージタイプ" in record.message or "unknown_storage_type" in record.message 
                      for record in caplog.records), "应输出未知存储类型警告"
class TestGetSyncCheckpointer:
    """同期Checkpointer取得テスト"""
    def test_sync_checkpointer_returns_memory(self):
        """CKP-006: 同期環境で MemorySaver を返却 (storage_type=memory)
        覆盖代码行: checkpointer.py:169-185
        验证同步环境下返回 MemorySaver。
        """
        # Arrange - 准备测试数据
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LANGGRAPH_STORAGE_TYPE = "memory"
            from app.core.checkpointer import get_sync_checkpointer
            # Act - 执行被测试函数
            result = get_sync_checkpointer()
            # Assert - 验证结果
            assert result is not None, "返回值不应为 None"
            assert "MemorySaver" in str(type(result).__name__), "应返回 MemorySaver"
    def test_sync_checkpointer_postgres_warning(self, caplog):
        """CKP-007: 同期環境で postgres 指定時に警告＋MemorySaver 返却
        覆盖代码行: checkpointer.py:176-182
        验证同步环境下指定 postgres 时，输出警告并返回 MemorySaver。
        """
        # Arrange - 准备测试数据
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LANGGRAPH_STORAGE_TYPE = "postgres"
            from app.core.checkpointer import get_sync_checkpointer
            # Act - 执行被测试函数
            import logging
            caplog.set_level(logging.WARNING)
            result = get_sync_checkpointer()
            # Assert - 验证结果
            assert result is not None, "返回值不应为 None"
            assert "MemorySaver" in str(type(result).__name__), "应返回 MemorySaver"
            # 验证警告日志
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
        # Arrange - 准备测试数据
        from app.core.checkpointer import close_checkpointer
        import app.core.checkpointer as ckp_module
        # 设置全局变量（模拟已初始化状态）
        ckp_module._checkpointer = MagicMock()
        ckp_module._checkpointer_initialized = True
        ckp_module._connection_pool = None
        # Act - 执行被测试函数
        await close_checkpointer()
        # Assert - 验证结果
        assert ckp_module._checkpointer is None, "_checkpointer 应被重置为 None"
        assert ckp_module._checkpointer_initialized is False, "_checkpointer_initialized 应为 False"
    @pytest.mark.asyncio
    async def test_close_with_postgres_pool(self):
        """CKP-012: PostgreSQL 接続プール付き Checkpointer のクローズ
        覆盖代码行: checkpointer.py:194-200
        验证关闭时正确关闭 PostgreSQL 连接池。
        """
        # Arrange - 准备测试数据
        from app.core.checkpointer import close_checkpointer
        import app.core.checkpointer as ckp_module
        # 设置全局变量（模拟 PostgreSQL 连接池）
        mock_pool = AsyncMock()
        mock_pool.close = AsyncMock()
        ckp_module._checkpointer = MagicMock()
        ckp_module._checkpointer_initialized = True
        ckp_module._connection_pool = mock_pool
        # Act - 执行被测试函数
        await close_checkpointer()
        # Assert - 验证结果
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
        # Arrange - 准备测试数据
        from app.core.checkpointer import reset_checkpointer
        import app.core.checkpointer as ckp_module
        # 设置全局变量（模拟已初始化状态）
        ckp_module._checkpointer = MagicMock()
        ckp_module._checkpointer_initialized = True
        ckp_module._current_storage_mode = "postgres"
        # Act - 执行被测试函数
        reset_checkpointer()
        # Assert - 验证结果
        assert ckp_module._checkpointer is None, "_checkpointer 应被重置"
        assert ckp_module._checkpointer_initialized is False, "_checkpointer_initialized 应为 False"
        assert ckp_module._current_storage_mode == "unknown", "_current_storage_mode 应为 unknown"
# =============================================================================
# 异常系测试 (CKP-E01 ~ CKP-E05)
# =============================================================================
class TestInitPostgresCheckpointerErrors:
    """PostgreSQL Checkpointer 初期化エラーテスト"""
    @pytest.mark.asyncio
    async def test_postgres_url_not_set_raises_value_error(self):
        """CKP-E01: PostgreSQL URL 未設定で ValueError
        覆盖代码行: checkpointer.py:108-113
        验证当 PostgreSQL URL 未设置时，抛出 ValueError 并回退到 MemorySaver。
        """
        # Arrange - 准备测试数据
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LANGGRAPH_STORAGE_TYPE = "postgres"
            mock_settings.LANGGRAPH_POSTGRES_URL = ""  # 未设置
            from app.core.checkpointer import get_async_checkpointer
            import app.core.checkpointer as ckp_module
            # 重置全局变量
            ckp_module._checkpointer = None
            ckp_module._checkpointer_initialized = False
            # Act - 执行被测试函数
            result = await get_async_checkpointer()
            # Assert - 验证结果（应回退到 MemorySaver）
            assert result is not None, "返回值不应为 None"
            assert ckp_module._current_storage_mode == "memory", "应回退到 memory 模式"
            assert "MemorySaver" in str(type(result).__name__), "应返回 MemorySaver"
    @pytest.mark.asyncio
    async def test_psycopg_not_installed_import_error(self, caplog):
        """CKP-E02: psycopg_pool 未インストールで ImportError
        覆盖代码行: checkpointer.py:142-147
        验证当 psycopg_pool 未安装时，捕获 ImportError 并回退。
        """
        # Arrange - 准备测试数据
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LANGGRAPH_STORAGE_TYPE = "postgres"
            mock_settings.LANGGRAPH_POSTGRES_URL = "postgresql://user:pass@localhost/db"
            # 模拟 ImportError - 修复: patch psycopg_pool.AsyncConnectionPool
            with patch("psycopg_pool.AsyncConnectionPool", side_effect=ImportError("No module named psycopg_pool")):
                from app.core.checkpointer import get_async_checkpointer
                import app.core.checkpointer as ckp_module
                # 重置全局变量
                ckp_module._checkpointer = None
                ckp_module._checkpointer_initialized = False
                # Act - 执行被测试函数
                import logging
                caplog.set_level(logging.ERROR)
                result = await get_async_checkpointer()
                # Assert - 验证结果（应回退）
                assert result is not None, "返回值不应为 None"
                assert ckp_module._current_storage_mode == "memory", "应回退到 memory 模式"
                # 验证错误日志
                assert any("エラー" in record.message for record in caplog.records), "应输出错误日志"
    @pytest.mark.asyncio
    async def test_postgres_connection_error_fallback(self, caplog):
        """CKP-E03: PostgreSQL 接続エラー時に MemorySaver へフォールバック
        覆盖代码行: checkpointer.py:80-87
        验证连接错误时回退到 MemorySaver。
        """
        # Arrange - 准备测试数据
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LANGGRAPH_STORAGE_TYPE = "postgres"
            mock_settings.LANGGRAPH_POSTGRES_URL = "postgresql://user:pass@localhost/db"
            # 模拟连接失败
            mock_pool = AsyncMock()
            mock_pool.open = AsyncMock(side_effect=Exception("Connection timeout"))
            with patch("psycopg_pool.AsyncConnectionPool", return_value=mock_pool):
                from app.core.checkpointer import get_async_checkpointer
                import app.core.checkpointer as ckp_module
                # 重置全局变量
                ckp_module._checkpointer = None
                ckp_module._checkpointer_initialized = False
                # Act - 执行被测试函数
                import logging
                caplog.set_level(logging.ERROR)
                result = await get_async_checkpointer()
                # Assert - 验证结果（应回退）
                assert result is not None, "返回值不应为 None"
                assert ckp_module._current_storage_mode == "memory", "应回退到 memory 模式"
                assert "MemorySaver" in str(type(result).__name__), "应回退到 MemorySaver"
                # 验证错误日志
                assert any("エラー" in record.message for record in caplog.records), "应输出错误日志"
    @pytest.mark.asyncio
    async def test_setup_fails_fallback(self, caplog):
        """CKP-E05: setup() 失敗時に MemorySaver へフォールバック
        覆盖代码行: checkpointer.py:80-87
        验证 setup() 失败时回退到 MemorySaver。
        """
        # Arrange - 准备测试数据
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LANGGRAPH_STORAGE_TYPE = "postgres"
            mock_settings.LANGGRAPH_POSTGRES_URL = "postgresql://user:pass@localhost/db"
            # 模拟 setup 失败
            mock_pool = AsyncMock()
            mock_pool.open = AsyncMock()
            mock_checkpointer = AsyncMock()
            mock_checkpointer.setup = AsyncMock(side_effect=Exception("Table creation failed"))
            with patch("psycopg_pool.AsyncConnectionPool", return_value=mock_pool):
                with patch("langgraph.checkpoint.postgres.aio.AsyncPostgresSaver", return_value=mock_checkpointer):
                    from app.core.checkpointer import get_async_checkpointer
                    import app.core.checkpointer as ckp_module
                    # 重置全局变量
                    ckp_module._checkpointer = None
                    ckp_module._checkpointer_initialized = False
                    # Act - 执行被测试函数
                    import logging
                    caplog.set_level(logging.ERROR)
                    result = await get_async_checkpointer()
                    # Assert - 验证结果（应回退）
                    assert result is not None, "返回值不应为 None"
                    assert ckp_module._current_storage_mode == "memory", "应回退到 memory 模式"
                    # 验证错误日志
                    assert any("エラー" in record.message for record in caplog.records), "应输出错误日志"
class TestCloseCheckpointerErrors:
    """Checkpointer クローズエラーテスト"""
    @pytest.mark.asyncio
    async def test_close_pool_error_warning(self, caplog):
        """CKP-E04: 接続プールクローズエラー時に警告ログ出力＋継続
        覆盖代码行: checkpointer.py:197-199
        验证连接池关闭错误时输出警告并继续执行。
        """
        # Arrange - 准备测试数据
        from app.core.checkpointer import close_checkpointer
        import app.core.checkpointer as ckp_module
        # 模拟连接池关闭失败
        mock_pool = AsyncMock()
        mock_pool.close = AsyncMock(side_effect=Exception("Close failed"))
        ckp_module._checkpointer = MagicMock()
        ckp_module._checkpointer_initialized = True
        ckp_module._connection_pool = mock_pool
        # Act - 执行被测试函数
        import logging
        caplog.set_level(logging.WARNING)
        await close_checkpointer()  # 不应抛出异常
        # Assert - 验证结果
        # 验证警告日志
        assert any("クローズエラー" in record.message or "エラー" in record.message 
                  for record in caplog.records), "应输出警告日志"
        # 验证继续执行（全局变量被重置）
        assert ckp_module._connection_pool is None, "应重置 _connection_pool"
        assert ckp_module._checkpointer is None, "应重置 _checkpointer"
# =============================================================================
# 安全测试 (CKP-SEC-01 ~ CKP-SEC-03)
# =============================================================================
@pytest.mark.security
class TestCheckpointerSecurity:
    """Checkpointer セキュリティテスト"""
    @pytest.mark.asyncio
    async def test_postgres_url_not_logged(self, caplog):
        """CKP-SEC-01: 接続成功時に PostgreSQL URL がログに出力されない
        验证 PostgreSQL URL（包含密码）不会出现在日志中。
        """
        # Arrange - 准备测试数据
        sensitive_url = "postgresql://user:SecretP@ssw0rd@localhost/db"
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LANGGRAPH_STORAGE_TYPE = "postgres"
            mock_settings.LANGGRAPH_POSTGRES_URL = sensitive_url
            # Mock PostgreSQL 组件
            mock_pool = AsyncMock()
            mock_pool.open = AsyncMock()
            mock_checkpointer = AsyncMock()
            mock_checkpointer.setup = AsyncMock()
            with patch("psycopg_pool.AsyncConnectionPool", return_value=mock_pool):
                with patch("langgraph.checkpoint.postgres.aio.AsyncPostgresSaver", return_value=mock_checkpointer):
                    from app.core.checkpointer import get_async_checkpointer
                    import app.core.checkpointer as ckp_module
                    # 重置全局变量
                    ckp_module._checkpointer = None
                    ckp_module._checkpointer_initialized = False
                    # Act - 执行被测试函数
                    import logging
                    caplog.set_level(logging.DEBUG)
                    result = await get_async_checkpointer()
                    # Assert - 验证结果
                    # 验证URL不出现在日志中
                    log_text = "\n".join([record.message for record in caplog.records])
                    assert "SecretP@ssw0rd" not in log_text, "密码不应出现在日志中"
                    assert sensitive_url not in log_text, "完整URL不应出现在日志中"
    @pytest.mark.asyncio
    async def test_credentials_not_exposed_on_error(self, caplog):
        """CKP-SEC-02: 接続エラー時に認証情報がログに露出しない
        验证连接错误时，认证信息不会泄露到日志中。
        """
        # Arrange - 准备测试数据
        sensitive_url = "postgresql://admin:TopSecret123@db.example.com/production"
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LANGGRAPH_STORAGE_TYPE = "postgres"
            mock_settings.LANGGRAPH_POSTGRES_URL = sensitive_url
            # 模拟连接失败
            mock_pool = AsyncMock()
            mock_pool.open = AsyncMock(side_effect=Exception("Authentication failed"))
            with patch("psycopg_pool.AsyncConnectionPool", return_value=mock_pool):
                from app.core.checkpointer import get_async_checkpointer
                import app.core.checkpointer as ckp_module
                # 重置全局变量
                ckp_module._checkpointer = None
                ckp_module._checkpointer_initialized = False
                # Act - 执行被测试函数
                import logging
                caplog.set_level(logging.ERROR)
                result = await get_async_checkpointer()
                # Assert - 验证结果
                # 验证敏感信息不出现在日志中
                log_text = "\n".join([record.message for record in caplog.records])
                assert "TopSecret123" not in log_text, "密码不应出现在错误日志中"
                assert "admin" not in log_text or "admin@" not in log_text, "用户名不应与密码一起出现"
                assert sensitive_url not in log_text, "完整URL不应出现在错误日志中"
    @pytest.mark.asyncio
    async def test_connection_pool_max_size_limit(self):
        """CKP-SEC-03: 接続プールの max_size が適切（リソース枯渇防止）
        验证连接池的 max_size 限制在合理范围内（防止资源耗尽）。
        """
        # Arrange - 准备测试数据
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.LANGGRAPH_STORAGE_TYPE = "postgres"
            mock_settings.LANGGRAPH_POSTGRES_URL = "postgresql://user:pass@localhost/db"
            # 捕获 AsyncConnectionPool 的调用参数
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
                    # 重置全局变量
                    ckp_module._checkpointer = None
                    ckp_module._checkpointer_initialized = False
                    # Act - 执行被测试函数
                    result = await get_async_checkpointer()
                    # Assert - 验证结果
                    assert actual_max_size is not None, "应设置 max_size"
                    assert actual_max_size <= 10, f"max_size 应 <= 10（防止资源耗尽），实际: {actual_max_size}"
                    assert actual_max_size > 0, f"max_size 应 > 0，实际: {actual_max_size}"
# =============================================================================
# Main Entry Point
# =============================================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
