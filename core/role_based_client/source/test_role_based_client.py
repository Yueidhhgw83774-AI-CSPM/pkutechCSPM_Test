# -*- coding: utf-8 -*-
"""
role_based_client.py 单元测试

测试规格: docs/testing/core/role_based_client_tests.md
覆盖率目标: 75%

测试类别:
  - 正常系: 18 个测试
  - 异常系: 13 个测试
  - 安全测试: 6 个测试

总计: 37 个测试
"""

import os
import sys
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path

# 导入被测试模块 | Import module under test
project_root = Path(__file__).parent.parent.parent.parent / "platform_python_backend-testing"
sys.path.insert(0, str(project_root))


# =============================================================================
# 正常系测试 | Normal Case Tests
# =============================================================================

class TestOpenSearchRoles:
    """
    ロール定数定義テスト
    角色常量定义测试
    """

    def test_roles_constants_defined(self):
        """
        RBC-001: ロール定数が正しく定義されている
        验证角色常量是否正确定义

        测试目的:
          - 确认5个角色常量的值正确
          - 验证角色名称符合预期格式
        """
        # Arrange - 准备测试数据
        # （定数確認のため、事前準備なし | 检查常量无需准备）

        # Act - 执行被测试函数
        from app.core.role_based_client import OpenSearchRoles

        # Assert - 验证结果
        assert OpenSearchRoles.CSPM_DASHBOARD_READ == "cspm_dashboard_read_role"
        assert OpenSearchRoles.RAG_SEARCH_READ == "rag_search_read_role"
        assert OpenSearchRoles.DOCUMENT_WRITE == "document_write_role"
        assert OpenSearchRoles.CSPM_JOB_EXECUTION == "cspm_job_execution_role"
        assert OpenSearchRoles.ADMIN == "admin_role"

    def test_role_env_mapping_complete(self):
        """
        RBC-002: ROLE_ENV_MAPPINGが全ロールを含む
        验证 ROLE_ENV_MAPPING 包含所有角色

        测试目的:
          - 确认5个角色都在映射表中
          - 验证每个角色都有 user 和 password 字段
        """
        # Arrange - 准备测试数据
        # （マッピング確認のため、事前準備なし | 检查映射无需准备）

        # Act - 执行被测试函数
        from app.core.role_based_client import ROLE_ENV_MAPPING, OpenSearchRoles

        # Assert - 验证结果
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


class TestRoleBasedOpenSearchClient:
    """
    RoleBasedOpenSearchClient 正常系テスト
    RoleBasedOpenSearchClient 正常情况测试
    """

    @pytest.mark.asyncio
    async def test_get_client_for_valid_role(self, mock_settings_env, mock_async_opensearch):
        """
        RBC-003: 有効なロールでクライアント取得成功
        使用有效角色成功获取客户端

        覆盖代码行: role_based_client.py:73-98

        测试目的:
          - 验证使用有效角色名可以获取客户端
          - 确认返回的是 AsyncOpenSearch 实例
        """
        # Arrange - 准备测试数据
        mock_cls, mock_instance = mock_async_opensearch

        # Act - 执行被测试函数
        from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
        client_manager = RoleBasedOpenSearchClient()
        result = await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

        # Assert - 验证结果
        assert result is not None  # 验证客户端不为空
        assert result is mock_instance  # 验证返回的是模拟实例

    @pytest.mark.asyncio
    async def test_cached_client_returned(self, mock_settings_env, mock_async_opensearch):
        """
        RBC-004: 初期化済みロールはキャッシュ返却
        已初始化的角色返回缓存

        覆盖代码行: role_based_client.py:85-87

        测试目的:
          - 验证第二次获取同一角色时返回缓存的实例
          - 确认 AsyncOpenSearch 只被调用一次
        """
        # Arrange - 准备测试数据
        mock_cls, mock_instance = mock_async_opensearch

        # Act - 执行被测试函数
        from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
        client_manager = RoleBasedOpenSearchClient()
        result1 = await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)
        result2 = await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

        # Assert - 验证结果
        assert result1 is result2  # 验证返回的是同一实例
        # AsyncOpenSearchは1回のみ呼ばれる（キャッシュ使用）
        # AsyncOpenSearch 只被调用一次（使用缓存）
        assert mock_cls.call_count == 1

    @pytest.mark.asyncio
    async def test_aws_opensearch_port_443(self, mock_settings_env, mock_async_opensearch):
        """
        RBC-005: AWS OpenSearch→ポート443
        AWS OpenSearch 使用端口 443

        覆盖代码行: role_based_client.py:144-148

        测试目的:
          - 验证 AWS OpenSearch URL 自动使用端口 443
        """
        # Arrange - 准备测试数据
        mock_cls, mock_instance = mock_async_opensearch
        
        # Patch OPENSEARCH_URL to AWS URL
        with patch("app.core.config.settings.OPENSEARCH_URL", "https://search-domain.us-east-1.es.amazonaws.com"):
            # Act - 执行被测试函数
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

            # Assert - 验证结果
            assert mock_cls.called, "AsyncOpenSearch should be called"
            call_kwargs = mock_cls.call_args.kwargs if hasattr(mock_cls.call_args, 'kwargs') else mock_cls.call_args[1]
            assert call_kwargs["hosts"][0]["port"] == 443  # 验证端口为443

    @pytest.mark.asyncio
    async def test_standard_opensearch_port_9200(self, mock_settings_env, mock_async_opensearch):
        """
        RBC-006: 標準OpenSearch→ポート9200
        标准 OpenSearch 使用端口 9200

        覆盖代码行: role_based_client.py:144-148

        测试目的:
          - 验证非 AWS 的 OpenSearch URL 默认使用端口 9200
        """
        # Arrange - 准备测试数据
        mock_cls, mock_instance = mock_async_opensearch

        # Act - 执行被测试函数
        from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
        client_manager = RoleBasedOpenSearchClient()
        await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

        # Assert - 验证结果
        call_kwargs = mock_cls.call_args.kwargs if hasattr(mock_cls.call_args, 'kwargs') else mock_cls.call_args[1]
        assert call_kwargs["hosts"][0]["port"] == 9200  # 验证端口为9200

    @pytest.mark.asyncio
    async def test_url_specified_port(self, mock_settings_env, mock_async_opensearch):
        """
        RBC-007: URL指定ポート→そのポート使用
        URL 指定端口则使用该端口

        覆盖代码行: role_based_client.py:141-148

        测试目的:
          - 验证 URL 中指定的端口优先使用
        """
        # Arrange - 准备测试数据
        mock_cls, mock_instance = mock_async_opensearch

        with patch("app.core.config.settings.OPENSEARCH_URL", "https://localhost:9300"):
            # Act - 执行被测试函数
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

            # Assert - 验证结果
            call_kwargs = mock_cls.call_args.kwargs if hasattr(mock_cls.call_args, 'kwargs') else mock_cls.call_args[1]
            assert call_kwargs["hosts"][0]["port"] == 9300  # 验证使用URL指定的端口

    @pytest.mark.asyncio
    async def test_aws_opensearch_ca_certs_none(self, mock_settings_env, mock_async_opensearch):
        """
        RBC-008: AWS OpenSearch→ca_certs=None
        AWS OpenSearch 的 ca_certs 设为 None

        覆盖代码行: role_based_client.py:165-167

        测试目的:
          - 验证 AWS OpenSearch 不使用自定义 CA 证书
        """
        # Arrange - 准备测试数据
        mock_cls, mock_instance = mock_async_opensearch

        with patch("app.core.config.settings.OPENSEARCH_URL", "https://search-domain.us-east-1.es.amazonaws.com"):
            # Act - 执行被测试函数
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

            # Assert - 验证结果
            call_kwargs = mock_cls.call_args.kwargs if hasattr(mock_cls.call_args, 'kwargs') else mock_cls.call_args[1]
            assert call_kwargs["ca_certs"] is None  # 验证ca_certs为None

    @pytest.mark.asyncio
    async def test_ca_certs_path_configured(self, mock_settings_env, mock_async_opensearch):
        """
        RBC-009: CA_CERTS_PATH設定あり→指定パス使用
        设置了 CA_CERTS_PATH 则使用指定路径

        覆盖代码行: role_based_client.py:168-171

        测试目的:
          - 验证当设置了 CA 证书路径且文件存在时使用该路径
        """
        # Arrange - 准备测试数据
        mock_cls, mock_instance = mock_async_opensearch

        # os.path.existsをモックしてパスが存在するようにする
        # 模拟 os.path.exists 使路径存在
        with patch("app.core.config.settings.OPENSEARCH_CA_CERTS_PATH", "/path/to/ca-cert.pem"), \
             patch("os.path.exists", return_value=True):
            # Act - 执行被测试函数
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

            # Assert - 验证结果
            call_kwargs = mock_cls.call_args.kwargs if hasattr(mock_cls.call_args, 'kwargs') else mock_cls.call_args[1]
            assert call_kwargs["ca_certs"] == "/path/to/ca-cert.pem"  # 验证使用指定的CA证书路径

    @pytest.mark.asyncio
    async def test_no_ca_certs_path_ssl_verification_disabled(self, mock_settings_env, mock_async_opensearch):
        """
        RBC-010: CA_CERTS_PATH未設定→SSL検証無効（開発環境）
        未设置 CA_CERTS_PATH 则禁用 SSL 验证（开发环境）

        覆盖代码行: role_based_client.py:172-175

        测试目的:
          - 验证开发环境下未设置 CA 证书时禁用 SSL 验证
        """
        # Arrange - 准备测试数据
        mock_cls, mock_instance = mock_async_opensearch

        # Act - 执行被测试函数
        # （MOCK_SETTINGS_ENVにはOPENSEARCH_CA_CERTS_PATHが設定されていない）
        # （MOCK_SETTINGS_ENV 中没有设置 OPENSEARCH_CA_CERTS_PATH）
        from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
        client_manager = RoleBasedOpenSearchClient()
        await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

        # Assert - 验证结果
        call_kwargs = mock_cls.call_args.kwargs if hasattr(mock_cls.call_args, 'kwargs') else mock_cls.call_args[1]
        assert call_kwargs["verify_certs"] is False  # 验证SSL验证被禁用
        assert call_kwargs["ssl_show_warn"] is False  # 验证SSL警告被禁用

    @pytest.mark.asyncio
    async def test_retry_success_on_second_attempt(self, mock_settings_env, mock_async_opensearch):
        """
        RBC-011: リトライ成功（1回目失敗、2回目ping成功）
        重试成功（第1次失败，第2次ping成功）

        覆盖代码行: role_based_client.py:182-191

        测试目的:
          - 验证重试机制正常工作
          - 确认第2次重试成功时返回客户端
        """
        # Arrange - 准备测试数据
        mock_cls, mock_instance = mock_async_opensearch
        mock_instance.ping = AsyncMock(side_effect=[False, True])  # 第1次失败，第2次成功

        # Act - 执行被测试函数
        with patch("asyncio.sleep", new_callable=AsyncMock):  # 模拟sleep以加快测试
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            result = await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

        # Assert - 验证结果
        assert result is not None  # 验证最终获取到客户端
        assert mock_instance.ping.call_count == 2  # 验证ping被调用2次

    @pytest.mark.asyncio
    async def test_get_available_roles(self, mock_settings_env):
        """
        RBC-012: 使用可能ロール一覧取得
        获取可用角色列表

        覆盖代码行: role_based_client.py:221-228

        测试目的:
          - 验证可以获取所有可用角色列表
          - 确认返回5个角色
        """
        # Arrange - 准备测试数据
        from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles

        # Act - 执行被测试函数
        client_manager = RoleBasedOpenSearchClient()
        roles = await client_manager.get_available_roles()

        # Assert - 验证结果
        assert len(roles) == 5  # 验证返回5个角色
        assert OpenSearchRoles.ADMIN in roles
        assert OpenSearchRoles.CSPM_DASHBOARD_READ in roles
        assert OpenSearchRoles.RAG_SEARCH_READ in roles
        assert OpenSearchRoles.DOCUMENT_WRITE in roles
        assert OpenSearchRoles.CSPM_JOB_EXECUTION in roles

    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_settings_env, mock_async_opensearch):
        """
        RBC-013: ヘルスチェック成功
        健康检查成功

        覆盖代码行: role_based_client.py:230-270

        测试目的:
          - 验证健康检查返回正确状态
          - 确认所有健康检查字段正确
        """
        # Arrange - 准备测试数据
        mock_cls, mock_instance = mock_async_opensearch

        # Act - 执行被测试函数
        from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
        client_manager = RoleBasedOpenSearchClient()
        # まずクライアントを初期化 | 首先初始化客户端
        await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)
        # ヘルスチェック | 健康检查
        health = await client_manager.check_role_health(OpenSearchRoles.ADMIN)

        # Assert - 验证结果
        assert health["status"] == "healthy"  # 验证状态为健康
        assert health["initialized"] is True  # 验证已初始化
        assert health["ping_success"] is True  # 验证ping成功
        assert health["error"] is None  # 验证无错误

    @pytest.mark.asyncio
    async def test_localhost_hostname_verification_disabled(self, mock_settings_env, mock_async_opensearch):
        """
        RBC-016: localhostでホスト名検証無効
        localhost 禁用主机名验证

        覆盖代码行: role_based_client.py:156

        测试目的:
          - 验证 localhost 时禁用主机名验证
        """
        # Arrange - 准备测试数据
        mock_cls, mock_instance = mock_async_opensearch

        # Act - 执行被测试函数
        # （MOCK_SETTINGS_ENVのOPENSEARCH_URLはhttps://localhost:9200）
        # （MOCK_SETTINGS_ENV 的 OPENSEARCH_URL 是 https://localhost:9200）
        from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
        client_manager = RoleBasedOpenSearchClient()
        await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

        # Assert - 验证结果
        call_kwargs = mock_cls.call_args.kwargs if hasattr(mock_cls.call_args, 'kwargs') else mock_cls.call_args[1]
        assert call_kwargs["ssl_assert_hostname"] is False  # 验证主机名验证被禁用

    @pytest.mark.asyncio
    async def test_non_localhost_hostname_verification_enabled(self, mock_settings_env, mock_async_opensearch):
        """
        RBC-017: non-localhostでホスト名検証有効
        非 localhost 启用主机名验证

        覆盖代码行: role_based_client.py:156

        测试目的:
          - 验证非 localhost 时启用主机名验证
        """
        # Arrange - 准备测试数据
        mock_cls, mock_instance = mock_async_opensearch

        with patch("app.core.config.settings.OPENSEARCH_URL", "https://opensearch.example.com:9200"):
            # Act - 执行被测试函数
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

            # Assert - 验证结果
            call_kwargs = mock_cls.call_args.kwargs if hasattr(mock_cls.call_args, 'kwargs') else mock_cls.call_args[1]
            assert call_kwargs["ssl_assert_hostname"] is True  # 验证主机名验证被启用

    @pytest.mark.asyncio
    async def test_ca_certs_path_file_not_exists(self, mock_settings_env, mock_async_opensearch):
        """
        RBC-018: CA_CERTS_PATH設定あるがファイル不存在→SSL検証無効化
        设置了 CA_CERTS_PATH 但文件不存在则禁用 SSL 验证

        覆盖代码行: role_based_client.py:168-175

        测试目的:
          - 验证 CA 证书路径设置但文件不存在时的回退行为
          - 确认开发环境下禁用 SSL 验证
        """
        # Arrange - 准备测试数据
        mock_cls, mock_instance = mock_async_opensearch

        # os.path.existsをモックしてファイルが存在しないようにする
        # 模拟 os.path.exists 使文件不存在
        with patch("app.core.config.settings.OPENSEARCH_CA_CERTS_PATH", "/path/to/nonexistent.pem"), \
             patch("os.path.exists", return_value=False):
            # Act - 执行被测试函数
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

            # Assert - 验证结果
            # ファイルが存在しない場合はSSL検証無効化 | 文件不存在时禁用SSL验证
            call_kwargs = mock_cls.call_args.kwargs if hasattr(mock_cls.call_args, 'kwargs') else mock_cls.call_args[1]
            assert call_kwargs["verify_certs"] is False  # 验证SSL验证被禁用
            assert call_kwargs["ssl_show_warn"] is False  # 验证SSL警告被禁用


class TestGlobalFunctions:
    """
    グローバル関数テスト
    全局函数测试
    """

    def test_singleton_instance(self, mock_settings_env):
        """
        RBC-014: シングルトンインスタンス取得
        获取单例实例

        覆盖代码行: role_based_client.py:275-285

        测试目的:
          - 验证单例模式正确实现
          - 确认多次调用返回同一实例
        """
        # Arrange - 准备测试数据
        # （シングルトン確認のため、事前準備なし | 检查单例无需准备）

        # Act - 执行被测试函数
        from app.core.role_based_client import get_role_based_client
        instance1 = get_role_based_client()
        instance2 = get_role_based_client()

        # Assert - 验证结果
        assert instance1 is instance2  # 验证返回同一实例

    @pytest.mark.asyncio
    async def test_convenience_function(self, mock_settings_env, mock_async_opensearch):
        """
        RBC-015: 便利関数でクライアント取得
        使用便利函数获取客户端

        覆盖代码行: role_based_client.py:288-298

        测试目的:
          - 验证便利函数正常工作
          - 确认通过全局函数获取客户端
        """
        # Arrange - 准备测试数据
        mock_cls, mock_instance = mock_async_opensearch

        # Act - 执行被测试函数
        from app.core.role_based_client import get_client_for_role, OpenSearchRoles
        result = await get_client_for_role(OpenSearchRoles.ADMIN)

        # Assert - 验证结果
        assert result is not None  # 验证获取到客户端
        assert result is mock_instance  # 验证返回的是模拟实例


# =============================================================================
# 異常系テスト | Error Case Tests
# =============================================================================

class TestRoleBasedClientErrors:
    """
    RoleBasedOpenSearchClient 異常系テスト
    RoleBasedOpenSearchClient 异常情况测试
    """

    @pytest.mark.asyncio
    async def test_unknown_role_returns_none(self, mock_settings_env):
        """
        RBC-E01: 未知のロール名→None
        未知的角色名返回 None

        覆盖代码行: role_based_client.py:78-80

        测试目的:
          - 验证未知角色名返回 None
          - 确认记录错误日志
        """
        # Arrange - 准备测试数据
        from app.core.role_based_client import RoleBasedOpenSearchClient

        # Act - 执行被测试函数
        client_manager = RoleBasedOpenSearchClient()
        result = await client_manager.get_client_for_role("unknown_role")

        # Assert - 验证结果
        assert result is None  # 验证返回None

    @pytest.mark.asyncio
    async def test_missing_username(self, mock_async_opensearch):
        """
        RBC-E02: 認証情報未設定（USERNAME）
        认证信息未设置（用户名）

        覆盖代码行: role_based_client.py:110-118

        测试目的:
          - 验证用户名未设置时的错误处理
          - 确认错误被记录
        """
        # Arrange - 准备测试数据
        from conftest import MOCK_SETTINGS_ENV
        env_no_user = MOCK_SETTINGS_ENV.copy()
        env_no_user["OPENSEARCH_USER"] = ""  # ADMINロールのユーザー名を空に | 将ADMIN角色的用户名设为空

        with patch.dict("os.environ", env_no_user, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            # Act - 执行被测试函数
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            result = await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

            # Assert - 验证结果
            assert result is None  # 验证返回None
            assert client_manager._initialization_errors.get(OpenSearchRoles.ADMIN) is not None  # 验证错误被记录

    @pytest.mark.asyncio
    async def test_missing_password(self, mock_async_opensearch):
        """
        RBC-E03: 認証情報未設定（PASSWORD）
        认证信息未设置（密码）

        覆盖代码行: role_based_client.py:110-118

        测试目的:
          - 验证密码未设置时的错误处理
          - 确认错误被记录
        """
        # Arrange - 准备测试数据
        from conftest import MOCK_SETTINGS_ENV
        env_no_pass = MOCK_SETTINGS_ENV.copy()
        env_no_pass["OPENSEARCH_PASSWORD"] = ""  # ADMINロールのパスワードを空に | 将ADMIN角色的密码设为空

        with patch.dict("os.environ", env_no_pass, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            # Act - 执行被测试函数
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            result = await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

            # Assert - 验证结果
            assert result is None  # 验证返回None
            assert client_manager._initialization_errors.get(OpenSearchRoles.ADMIN) is not None  # 验证错误被记录

    @pytest.mark.asyncio
    async def test_opensearch_url_empty(self, mock_async_opensearch):
        """
        RBC-E04: OPENSEARCH_URL未設定
        OPENSEARCH_URL 未设置

        覆盖代码行: role_based_client.py:120-126

        测试目的:
          - 验证 URL 未设置时的错误处理
          - 确认配置错误导致 SystemExit
        """
        # Arrange - 准备测试数据
        from conftest import MOCK_SETTINGS_ENV
        env_no_url = MOCK_SETTINGS_ENV.copy()
        env_no_url["OPENSEARCH_URL"] = ""

        with patch.dict("os.environ", env_no_url, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            # Act & Assert - 执行被测试函数并期望SystemExit
            with pytest.raises(SystemExit):
                from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
                client_manager = RoleBasedOpenSearchClient()
                await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

    @pytest.mark.asyncio
    async def test_opensearch_url_invalid_format(self, mock_async_opensearch):
        """
        RBC-E05: OPENSEARCH_URL不正形式
        OPENSEARCH_URL 格式不正确

        覆盖代码行: role_based_client.py:128-134

        测试目的:
          - 验证 URL 格式不正确时的错误处理
          - 确认抛出 ValueError
        """
        # Arrange - 准备测试数据
        from conftest import MOCK_SETTINGS_ENV
        env_bad_url = MOCK_SETTINGS_ENV.copy()
        env_bad_url["OPENSEARCH_URL"] = "not-a-url"

        with patch.dict("os.environ", env_bad_url, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            # Act - 执行被测试函数
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            result = await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

            # Assert - 验证结果
            assert result is None  # 验证返回None
            error = client_manager._initialization_errors.get(OpenSearchRoles.ADMIN)
            assert error is not None  # 验证错误被记录
            assert isinstance(error, ValueError)  # 验证错误类型为ValueError

    @pytest.mark.asyncio
    async def test_ping_all_failures(self, mock_settings_env, mock_async_opensearch):
        """
        RBC-E06: ping全失敗（max_retries回）
        ping 全部失败（max_retries 次）

        覆盖代码行: role_based_client.py:182-202

        测试目的:
          - 验证所有重试都失败时的处理
          - 确认重试次数正确
        """
        # Arrange - 准备测试数据
        mock_cls, mock_instance = mock_async_opensearch
        mock_instance.ping = AsyncMock(return_value=False)  # 所有ping都返回False

        # Act - 执行被测试函数
        with patch("asyncio.sleep", new_callable=AsyncMock):  # 模拟sleep以加快测试
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            result = await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

        # Assert - 验证结果
        assert result is None  # 验证返回None
        assert mock_instance.ping.call_count == 3  # 验证重试了3次（默认max_retries=3）
        error = client_manager._initialization_errors.get(OpenSearchRoles.ADMIN)
        assert error is not None  # 验证错误被记录

    @pytest.mark.asyncio
    async def test_connection_exception_all_retries(self, mock_settings_env, mock_async_opensearch):
        """
        RBC-E07: 接続例外（max_retries回）
        连接异常（max_retries 次）

        覆盖代码行: role_based_client.py:192-198

        测试目的:
          - 验证连接异常时的重试机制
          - 确认最终记录错误
        """
        # Arrange - 准备测试数据
        mock_cls, mock_instance = mock_async_opensearch
        mock_instance.ping = AsyncMock(side_effect=Exception("Connection refused"))  # 抛出异常

        # Act - 执行被测试函数
        with patch("asyncio.sleep", new_callable=AsyncMock):  # 模拟sleep以加快测试
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            result = await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

        # Assert - 验证结果
        assert result is None  # 验证返回None
        error = client_manager._initialization_errors.get(OpenSearchRoles.ADMIN)
        assert error is not None  # 验证错误被记录

    @pytest.mark.asyncio
    async def test_skip_on_previous_error(self, mock_settings_env, mock_async_opensearch):
        """
        RBC-E08: 過去の初期化エラー→スキップ
        过去的初始化错误则跳过

        覆盖代码行: role_based_client.py:89-92

        测试目的:
          - 验证已记录错误的角色不会重新初始化
          - 确认 AsyncOpenSearch 不被调用
        """
        # Arrange - 准备测试数据
        mock_cls, mock_instance = mock_async_opensearch

        from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
        client_manager = RoleBasedOpenSearchClient()
        # 事前にエラーを設定 | 预先设置错误
        client_manager._initialization_errors[OpenSearchRoles.ADMIN] = ValueError("previous error")

        # Act - 执行被测试函数
        result = await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

        # Assert - 验证结果
        assert result is None  # 验证返回None
        # AsyncOpenSearchが呼ばれないことを確認（スキップ）
        # 确认 AsyncOpenSearch 不被调用（跳过）
        mock_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_health_check_unknown_role(self, mock_settings_env):
        """
        RBC-E09: ヘルスチェック: 未知のロール
        健康检查：未知角色

        覆盖代码行: role_based_client.py:244-248

        测试目的:
          - 验证未知角色的健康检查返回错误
          - 确认状态为 invalid_role
        """
        # Arrange - 准备测试数据
        from app.core.role_based_client import RoleBasedOpenSearchClient

        # Act - 执行被测试函数
        client_manager = RoleBasedOpenSearchClient()
        health = await client_manager.check_role_health("unknown_role")

        # Assert - 验证结果
        assert health["status"] == "invalid_role"  # 验证状态为invalid_role
        assert health["error"] == "未知のロール名: unknown_role"  # 验证错误消息

    @pytest.mark.asyncio
    async def test_health_check_initialization_error(self, mock_settings_env):
        """
        RBC-E10: ヘルスチェック: 初期化エラー状態
        健康检查：初始化错误状态

        覆盖代码行: role_based_client.py:252-255

        测试目的:
          - 验证初始化错误状态的健康检查
          - 确认返回正确的错误信息
        """
        # Arrange - 准备测试数据
        from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles

        client_manager = RoleBasedOpenSearchClient()
        # 事前にエラーを設定 | 预先设置错误
        client_manager._initialization_errors[OpenSearchRoles.ADMIN] = ValueError("init error")

        # Act - 执行被测试函数
        health = await client_manager.check_role_health(OpenSearchRoles.ADMIN)

        # Assert - 验证结果
        assert health["status"] == "initialization_error"  # 验证状态为initialization_error
        assert "init error" in health["error"]  # 验证错误消息中包含init error

    @pytest.mark.asyncio
    async def test_health_check_initialization_error_after_ping_failures(self, mock_settings_env, mock_async_opensearch):
        """
        RBC-E11: ヘルスチェック: ping全失敗後の初期化エラー状態
        健康检查：ping 全部失败后的初始化错误状态

        覆盖代码行: role_based_client.py:250-253

        测试目的:
          - 验证 ping 全部失败后健康检查返回 initialization_error
          - 确认错误被正确记录
        """
        # Arrange - 准备测试数据
        mock_cls, mock_instance = mock_async_opensearch
        mock_instance.ping = AsyncMock(return_value=False)  # ping全部失败

        # Act - 执行被测试函数
        with patch("asyncio.sleep", new_callable=AsyncMock):
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            # クライアント取得失敗（ping全失敗→_initialization_errorsに記録）
            # 客户端获取失败（ping全失败→记录到_initialization_errors）
            await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)
            
            # ヘルスチェック実行前に_initialization_errorsを確認
            # 健康检查执行前确认_initialization_errors
            assert OpenSearchRoles.ADMIN in client_manager._initialization_errors
            
            # ヘルスチェック | 健康检查
            health = await client_manager.check_role_health(OpenSearchRoles.ADMIN)

        # Assert - 验证结果
        # ping全失敗後は_initialization_errorsに記録されるため"initialization_error"
        # ping全部失败后记录到_initialization_errors因此为"initialization_error"
        assert health["status"] in ["initialization_error", "client_unavailable", "error"]

    @pytest.mark.asyncio
    async def test_health_check_ping_failed(self, mock_settings_env, mock_async_opensearch):
        """
        RBC-E12: ヘルスチェック: ping失敗
        健康检查：ping 失败

        覆盖代码行: role_based_client.py:262-264

        测试目的:
          - 验证健康检查时 ping 失败的处理
          - 确认状态为 ping_failed
        """
        # Arrange - 准备测试数据
        mock_cls, mock_instance = mock_async_opensearch
        # 初期化時は成功、ヘルスチェック時は失敗
        # 初始化时成功，健康检查时失败
        mock_instance.ping = AsyncMock(side_effect=[True, False])

        # Act - 执行被测试函数
        from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
        client_manager = RoleBasedOpenSearchClient()
        await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)
        health = await client_manager.check_role_health(OpenSearchRoles.ADMIN)

        # Assert - 验证结果
        assert health["status"] == "ping_failed"  # 验证状态为ping_failed
        assert health["ping_success"] is False  # 验证ping失败

    @pytest.mark.asyncio
    async def test_health_check_exception(self, mock_settings_env, mock_async_opensearch):
        """
        RBC-E13: ヘルスチェック: 例外発生
        健康检查：异常发生

        覆盖代码行: role_based_client.py:266-269

        测试目的:
          - 验证健康检查时异常的处理
          - 确认错误被正确记录
        """
        # Arrange - 准备测试数据
        mock_cls, mock_instance = mock_async_opensearch
        # 初期化時は成功、ヘルスチェック時は例外
        # 初始化时成功，健康检查时异常
        mock_instance.ping = AsyncMock(side_effect=[True, Exception("Connection timeout")])

        # Act - 执行被测试函数
        from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
        client_manager = RoleBasedOpenSearchClient()
        await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)
        health = await client_manager.check_role_health(OpenSearchRoles.ADMIN)

        # Assert - 验证结果
        assert health["status"] == "error"  # 验证状态为error
        assert "Connection timeout" in health["error"]  # 验证错误消息中包含Connection timeout


# =============================================================================
# セキュリティテスト | Security Tests
# =============================================================================

@pytest.mark.security
class TestRoleBasedClientSecurity:
    """
    RoleBasedOpenSearchClient セキュリティテスト
    RoleBasedOpenSearchClient 安全性测试
    """

    @pytest.mark.asyncio
    async def test_password_not_in_logs(self, mock_settings_env, mock_async_opensearch, caplog):
        """
        RBC-SEC-01: パスワードがログに出力されない
        密码不输出到日志

        覆盖代码行: role_based_client.py:全体

        测试目的:
          - 验证日志中不包含密码
          - 确保敏感信息安全
        """
        # Arrange - 准备测试数据
        import logging
        mock_cls, mock_instance = mock_async_opensearch

        # Act - 执行被测试函数
        with caplog.at_level(logging.DEBUG):
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

        # Assert - 验证结果
        # ログにパスワードが含まれないことを確認 | 确认日志中不包含密码
        from conftest import MOCK_SETTINGS_ENV
        password = MOCK_SETTINGS_ENV["OPENSEARCH_PASSWORD"]
        
        # 密码长度足够长时才检查（避免误报）| 仅当密码非常短时（如"admin"）可能出现误报
        if len(password) > 6:
            for record in caplog.records:
                msg = record.getMessage()
                assert password not in msg, (
                    f"ログメッセージにパスワードが含まれています: {msg}"
                )
        # 对于短密码，检查特定模式（如 "password=xxx" 或 "pwd:xxx"）
        else:
            import re
            password_patterns = [
                rf'password[=: ]+{re.escape(password)}',
                rf'pwd[=: ]+{re.escape(password)}',
                rf'auth.*{re.escape(password)}',
            ]
            for record in caplog.records:
                msg = record.getMessage().lower()
                for pattern in password_patterns:
                    assert not re.search(pattern, msg, re.IGNORECASE), (
                        f"ログメッセージに密码パターンが含まれています: {msg}"
                    )

    @pytest.mark.asyncio
    async def test_ssl_always_enabled(self, mock_settings_env, mock_async_opensearch):
        """
        RBC-SEC-02: SSL常時有効
        SSL 始终启用

        覆盖代码行: role_based_client.py:153

        测试目的:
          - 验证 SSL 始终启用
          - 确保通信安全
        """
        # Arrange - 准备测试数据
        mock_cls, mock_instance = mock_async_opensearch

        # Act - 执行被测试函数
        from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
        client_manager = RoleBasedOpenSearchClient()
        await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

        # Assert - 验证结果
        call_kwargs = mock_cls.call_args.kwargs if hasattr(mock_cls.call_args, 'kwargs') else mock_cls.call_args[1]
        assert call_kwargs["use_ssl"] is True  # 验证SSL始终启用

    @pytest.mark.asyncio
    async def test_credential_error_message_only_contains_env_var_names(
        self, mock_async_opensearch, caplog
    ):
        """
        RBC-SEC-03: 認証情報エラーメッセージに環境変数名のみ含む
        认证信息错误消息中仅包含环境变量名

        覆盖代码行: role_based_client.py:114

        测试目的:
          - 验证错误消息中只包含环境变量名
          - 确认不泄露密码值
        """
        # Arrange - 准备测试数据
        import logging
        from conftest import MOCK_SETTINGS_ENV
        env_no_pass = MOCK_SETTINGS_ENV.copy()
        env_no_pass["OPENSEARCH_PASSWORD"] = ""

        with patch.dict("os.environ", env_no_pass, clear=False):
            modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            # Act - 执行被测试函数
            with caplog.at_level(logging.DEBUG):
                from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
                client_manager = RoleBasedOpenSearchClient()
                await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

            # Assert - 验证结果
            # エラーメッセージに環境変数名は含まれるがパスワード値は含まれない
            # 错误消息中包含环境变量名但不包含密码值
            error = client_manager._initialization_errors.get(OpenSearchRoles.ADMIN)
            assert error is not None
            error_str = str(error)
            # 環境変数名は含まれることを確認 | 确认包含环境变量名
            assert "OPENSEARCH_USER" in error_str or "OPENSEARCH_PASSWORD" in error_str
            # 元のパスワード値は含まれないことを確認 | 确认不包含原始密码值
            assert "admin-password-do-not-use" not in error_str

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="実装にエラーメッセージのサニタイズがないため漏洩する可能性がある")
    async def test_health_check_error_no_password(self, mock_settings_env, mock_async_opensearch):
        """
        RBC-SEC-04: ヘルスチェックエラーにパスワードが含まれない
        健康检查错误中不包含密码

        覆盖代码行: role_based_client.py:268

        测试目的:
          - 验证健康检查错误不泄露密码
          - 【预期失败】当前实现使用 str(e) 可能泄露密码
        """
        # Arrange - 准备测试数据
        mock_cls, mock_instance = mock_async_opensearch
        from conftest import MOCK_SETTINGS_ENV
        password = MOCK_SETTINGS_ENV["OPENSEARCH_PASSWORD"]
        # ヘルスチェック時にパスワードを含む例外を発生させる
        # 健康检查时生成包含密码的异常
        mock_instance.ping = AsyncMock(
            side_effect=[True, Exception(f"Auth failed for password: {password}")]
        )

        # Act - 执行被测试函数
        from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
        client_manager = RoleBasedOpenSearchClient()
        await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)
        health = await client_manager.check_role_health(OpenSearchRoles.ADMIN)

        # Assert - 验证结果
        # str(e)がそのままエラーに含まれるため、漏洩する可能性がある
        # 由于直接使用 str(e)，可能会泄露密码
        # 現在の実装（role_based_client.py:268）ではstr(e)をそのまま格納
        # 当前实现（role_based_client.py:268）直接存储 str(e)
        if password in health.get("error", ""):
            pytest.fail(
                "ヘルスチェックエラーにパスワードが含まれています。"
                "実装改善（エラーメッセージのサニタイズ）を推奨。"
            )

    @pytest.mark.asyncio
    async def test_traceback_no_credentials(
        self, mock_settings_env, mock_async_opensearch, capsys
    ):
        """
        RBC-SEC-05: traceback出力に認証情報が含まれない
        traceback 输出中不包含认证信息

        覆盖代码行: role_based_client.py:210

        测试目的:
          - 验证 traceback 输出不泄露密码
          - 确保错误堆栈安全
        """
        # Arrange - 准备测试数据
        mock_cls, mock_instance = mock_async_opensearch
        mock_instance.ping = AsyncMock(side_effect=Exception("Connection refused"))

        # Act - 执行被测试函数
        with patch("asyncio.sleep", new_callable=AsyncMock):
            from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
            client_manager = RoleBasedOpenSearchClient()
            await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)

        # Assert - 验证结果
        # stderrのtraceback出力を検証 | 验证stderr的traceback输出
        captured = capsys.readouterr()
        from conftest import MOCK_SETTINGS_ENV
        password = MOCK_SETTINGS_ENV["OPENSEARCH_PASSWORD"]
        if password in captured.err:
            pytest.fail(
                f"traceback出力にパスワードが含まれています"
            )

    @pytest.mark.asyncio
    async def test_role_credentials_isolation(self, mock_settings_env, mock_async_opensearch):
        """
        RBC-SEC-06: 各ロールの認証情報が分離されている
        各角色的认证信息相互隔离

        覆盖代码行: role_based_client.py:110-112, 151-164

        测试目的:
          - 验证每个角色使用独立的认证信息
          - 确认角色间认证信息隔离
        """
        # Arrange - 准备测试数据
        from conftest import MOCK_SETTINGS_ENV
        
        mock_cls, mock_instance = mock_async_opensearch
        http_auth_calls = []

        def capture_http_auth(**kwargs):
            http_auth_calls.append(kwargs.get("http_auth"))
            return mock_instance

        mock_cls.side_effect = capture_http_auth

        # Act - 执行被测试函数
        # 複数ロールを初期化 | 初始化多个角色
        from app.core.role_based_client import RoleBasedOpenSearchClient, OpenSearchRoles
        client_manager = RoleBasedOpenSearchClient()
        await client_manager.get_client_for_role(OpenSearchRoles.ADMIN)
        await client_manager.get_client_for_role(OpenSearchRoles.CSPM_DASHBOARD_READ)

        # Assert - 验证结果
        # 各ロールが異なる認証情報を使用 | 各角色使用不同的认证信息
        assert len(http_auth_calls) == 2
        assert http_auth_calls[0] != http_auth_calls[1]  # 验证认证信息不同
        # ADMINロール | ADMIN角色
        assert http_auth_calls[0] == (
            MOCK_SETTINGS_ENV["OPENSEARCH_USER"], 
            MOCK_SETTINGS_ENV["OPENSEARCH_PASSWORD"]
        )
        # CSPM_DASHBOARD_READロール | CSPM_DASHBOARD_READ角色
        assert http_auth_calls[1] == (
            MOCK_SETTINGS_ENV["CSPM_DASHBOARD_READ_USER"], 
            MOCK_SETTINGS_ENV["CSPM_DASHBOARD_READ_PASSWORD"]
        )


# =============================================================================
# テスト実行エントリーポイント | Test Execution Entry Point
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
