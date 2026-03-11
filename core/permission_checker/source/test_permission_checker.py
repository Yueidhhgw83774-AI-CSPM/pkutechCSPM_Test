# -*- coding: utf-8 -*-
"""
permission_checker.py 单元测试

测试规格: docs/testing/core/permission_checker_tests.md
覆盖率目标: 85%+

测试类别:
  - 正常系: 22 个测试
  - 异常系: 12 个测试
  - 安全测试: 6 个测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path
import time

# 导入被测试模块
# Import test target module
project_root = Path(__file__).parent.parent.parent.parent / "platform_python_backend-testing"
sys.path.insert(0, str(project_root))


# =============================================================================
# 正常系测试 | Normal Tests
# =============================================================================

class TestOpenSearchPermissionCheckerInit:
    """
    OpenSearchPermissionChecker 初期化测试
    OpenSearchPermissionChecker initialization tests

    测试ID: PERM-INIT
    """

    def test_init_with_admin_client(self, mock_admin_client):
        """
        PERM-INIT: 管理者クライアントで初期化
        使用管理员客户端初始化

        覆盖代码行: permission_checker.py:24-31

        测试目的:
          - 验证 OpenSearchPermissionChecker 可以正确初始化
          - 验证管理员客户端正确存储
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker

        # Act - 执行被测试函数
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Assert - 验证结果
        assert checker.admin_client is mock_admin_client


class TestGetUserInfo:
    """
    ユーザー情報取得テスト
    用户信息获取测试

    测试ID: PERM-001
    """

    @pytest.mark.asyncio
    async def test_get_user_info_success(self, mock_admin_client):
        """
        PERM-001: ユーザー情報取得成功
        用户信息获取成功

        覆盖代码行: permission_checker.py:33-61

        测试目的:
          - 验证能够成功获取存在的用户信息
          - 验证返回正确的用户数据结构
          - 验证 API 调用参数正确
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker

        expected_user_info = {
            "backend_roles": ["admin"],
            "opensearch_security_roles": ["all_access"],
            "attributes": {}
        }
        mock_admin_client.transport.perform_request = AsyncMock(
            return_value={"test_user": expected_user_info}
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act - 执行被测试函数
        result = await checker.get_user_info("test_user")

        # Assert - 验证结果
        assert result == expected_user_info  # 验证返回的用户信息正确
        mock_admin_client.transport.perform_request.assert_called_once_with(
            "GET",
            "/_plugins/_security/api/internalusers/test_user",
            headers={"Content-Type": "application/json"}
        )  # 验证 API 调用正确


class TestGetUserRoles:
    """
    ユーザーロール取得テスト
    用户角色获取测试

    测试ID: PERM-002, PERM-012
    """

    @pytest.mark.asyncio
    async def test_get_user_roles_success(self, mock_admin_client):
        """
        PERM-002: ユーザーロール取得成功
        用户角色获取成功

        覆盖代码行: permission_checker.py:66-88

        测试目的:
          - 验证能够获取用户的角色列表
          - 验证 backend_roles 和 opensearch_security_roles 正确合并
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker

        user_info = {
            "backend_roles": ["admin", "developer"],
            "opensearch_security_roles": ["all_access"]
        }
        mock_admin_client.transport.perform_request = AsyncMock(
            return_value={"test_user": user_info}
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act - 执行被测试函数
        result = await checker.get_user_roles("test_user")

        # Assert - 验证结果
        assert set(result) == {"admin", "developer", "all_access"}  # 验证角色合并正确

    @pytest.mark.asyncio
    async def test_get_user_roles_deduplicate(self, mock_admin_client):
        """
        PERM-012: backend_rolesとopensearch_security_rolesの統合（重複除去）
        backend_roles 和 opensearch_security_roles 的统合（去重）

        覆盖代码行: permission_checker.py:77-84

        测试目的:
          - 验证重复的角色会被去重
          - 验证返回列表中不包含重复项
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker

        user_info = {
            "backend_roles": ["admin", "shared_role"],
            "opensearch_security_roles": ["shared_role", "reader"]
        }
        mock_admin_client.transport.perform_request = AsyncMock(
            return_value={"test_user": user_info}
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act - 执行被测试函数
        result = await checker.get_user_roles("test_user")

        # Assert - 验证结果
        assert len(result) == len(set(result))  # 验证没有重复
        assert set(result) == {"admin", "shared_role", "reader"}  # 验证所有角色都存在


class TestGetRolePermissions:
    """
    ロール権限取得テスト
    角色权限获取测试

    测试ID: PERM-003
    """

    @pytest.mark.asyncio
    async def test_get_role_permissions_success(self, mock_admin_client):
        """
        PERM-003: ロール権限取得成功
        角色权限获取成功

        覆盖代码行: permission_checker.py:92-120

        测试目的:
          - 验证能够获取指定角色的权限信息
          - 验证返回正确的权限数据结构
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker

        expected_permissions = {
            "index_permissions": [
                {
                    "index_patterns": ["logs-*"],
                    "allowed_actions": ["read", "write"]
                }
            ],
            "cluster_permissions": ["cluster:monitor/*"]
        }
        mock_admin_client.transport.perform_request = AsyncMock(
            return_value={"test_role": expected_permissions}
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act - 执行被测试函数
        result = await checker.get_role_permissions("test_role")

        # Assert - 验证结果
        assert result == expected_permissions  # 验证权限信息正确


class TestCheckIndexAccessPermission:
    """
    インデックスアクセス権限チェックテスト
    索引访问权限检查测试

    测试ID: PERM-004, PERM-005, PERM-013
    """

    @pytest.mark.asyncio
    async def test_index_access_granted(self, mock_admin_client):
        """
        PERM-004: インデックスアクセス権限あり
        索引访问权限许可

        覆盖代码行: permission_checker.py:124-170

        测试目的:
          - 验证有权限的用户可以访问索引
          - 验证索引模式匹配正确
          - 验证动作权限检查正确
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker

        # 用户信息
        user_info = {
            "backend_roles": ["reader_role"],
            "opensearch_security_roles": []
        }
        # 角色权限
        role_permissions = {
            "index_permissions": [
                {
                    "index_patterns": ["logs-*"],
                    "allowed_actions": ["read"]
                }
            ]
        }

        mock_admin_client.transport.perform_request = AsyncMock(
            side_effect=[
                {"test_user": user_info},
                {"reader_role": role_permissions}
            ]
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act - 执行被测试函数
        result = await checker.check_index_access_permission(
            "test_user",
            "logs-2024",
            "indices:data/read/search"
        )

        # Assert - 验证结果
        assert result is True  # 验证有访问权限

    @pytest.mark.asyncio
    async def test_index_access_denied(self, mock_admin_client):
        """
        PERM-005: インデックスアクセス権限なし
        索引访问权限拒绝

        覆盖代码行: permission_checker.py:124-170

        测试目的:
          - 验证没有权限的用户无法访问索引
          - 验证索引模式不匹配时返回 False
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker

        user_info = {
            "backend_roles": ["reader_role"],
            "opensearch_security_roles": []
        }
        role_permissions = {
            "index_permissions": [
                {
                    "index_patterns": ["other-*"],  # 不匹配的模式
                    "allowed_actions": ["read"]
                }
            ]
        }

        mock_admin_client.transport.perform_request = AsyncMock(
            side_effect=[
                {"test_user": user_info},
                {"reader_role": role_permissions}
            ]
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act - 执行被测试函数
        result = await checker.check_index_access_permission(
            "test_user",
            "logs-2024",
            "indices:data/read/search"
        )

        # Assert - 验证结果
        assert result is False  # 验证没有访问权限

    @pytest.mark.asyncio
    async def test_wildcard_index_pattern_match(self, mock_admin_client):
        """
        PERM-013: ワイルドカードインデックスパターンマッチ
        通配符索引模式匹配

        覆盖代码行: permission_checker.py:236-272

        测试目的:
          - 验证通配符模式（logs-*）能正确匹配索引
          - 验证多个模式的匹配逻辑
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker

        user_info = {
            "backend_roles": ["logs_reader"],
            "opensearch_security_roles": []
        }
        role_permissions = {
            "index_permissions": [
                {
                    "index_patterns": ["logs-*", "metrics-*"],
                    "allowed_actions": ["read"]
                }
            ]
        }

        mock_admin_client.transport.perform_request = AsyncMock(
            side_effect=[
                {"test_user": user_info},
                {"logs_reader": role_permissions}
            ]
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act - 执行被测试函数
        result = await checker.check_index_access_permission(
            "test_user",
            "logs-2024-01-30",
            "indices:data/read/search"
        )

        # Assert - 验证结果
        assert result is True  # 验证通配符匹配成功


class TestExpandGenericAction:
    """
    汎用アクション展開テスト
    通用动作展开测试

    测试ID: PERM-006 ~ PERM-008, PERM-014, PERM-006-B ~ PERM-006-H
    """

    def test_expand_read_action(self, mock_admin_client):
        """
        PERM-006: 汎用アクション展開（read）
        通用动作展开（read）

        覆盖代码行: permission_checker.py:174-232

        测试目的:
          - 验证 "read" 可以展开为多个具体的读取动作
          - 验证读取相关的动作都能匹配
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert - 执行并验证
        assert checker._expand_generic_action("read", "indices:data/read/search") is True
        assert checker._expand_generic_action("read", "indices:data/read/get") is True
        assert checker._expand_generic_action("read", "indices:data/read/mget") is True
        assert checker._expand_generic_action("read", "indices:admin/get") is True

    def test_expand_write_action(self, mock_admin_client):
        """
        PERM-007: 汎用アクション展開（write）
        通用动作展开（write）

        覆盖代码行: permission_checker.py:174-232

        测试目的:
          - 验证 "write" 可以展开为多个具体的写入动作
          - 验证写入相关的动作都能匹配
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert - 执行并验证
        assert checker._expand_generic_action("write", "indices:data/write/index") is True
        assert checker._expand_generic_action("write", "indices:data/write/update") is True
        assert checker._expand_generic_action("write", "indices:data/write/bulk") is True
        assert checker._expand_generic_action("write", "indices:data/write/delete") is True

    def test_expand_wildcard_action(self, mock_admin_client):
        """
        PERM-008: 汎用アクション展開（ワイルドカード）
        通用动作展开（通配符）

        覆盖代码行: permission_checker.py:220-222

        测试目的:
          - 验证 "*" 通配符匹配所有动作
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert - 执行并验证
        assert checker._expand_generic_action("*", "indices:data/read/search") is True
        assert checker._expand_generic_action("*", "indices:data/write/index") is True
        assert checker._expand_generic_action("*", "cluster:admin/settings") is True

    def test_expand_crud_action(self, mock_admin_client):
        """
        PERM-014: 複数アクション許可のロール（crud）
        多动作许可的角色（crud）

        覆盖代码行: permission_checker.py:174-232

        测试目的:
          - 验证 "crud" 动作覆盖 read 和 write
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert - 执行并验证
        assert checker._expand_generic_action("crud", "indices:data/read/search") is True
        assert checker._expand_generic_action("crud", "indices:data/write/index") is True

    def test_expand_manage_action(self, mock_admin_client):
        """
        PERM-006-B: 汎用アクション展開（manage）
        通用动作展开（manage）

        覆盖代码行: permission_checker.py:174-232

        测试目的:
          - 验证 "manage" 动作覆盖管理相关操作
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert - 执行并验证
        assert checker._expand_generic_action("manage", "indices:admin/create") is True
        assert checker._expand_generic_action("manage", "indices:admin/delete") is True
        assert checker._expand_generic_action("manage", "indices:admin/mappings/put") is True

    def test_expand_index_action(self, mock_admin_client):
        """
        PERM-006-C: 汎用アクション展開（index）
        通用动作展开（index）

        覆盖代码行: permission_checker.py:174-232

        测试目的:
          - 验证 "index" 动作覆盖索引写入操作
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert - 执行并验证
        assert checker._expand_generic_action("index", "indices:data/write/index") is True
        assert checker._expand_generic_action("index", "indices:data/write/update") is True
        assert checker._expand_generic_action("index", "indices:data/write/bulk") is True

    def test_expand_delete_action(self, mock_admin_client):
        """
        PERM-006-D: 汎用アクション展開（delete）
        通用动作展开（delete）

        覆盖代码行: permission_checker.py:174-232

        测试目的:
          - 验证 "delete" 动作覆盖删除操作
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert - 执行并验证
        assert checker._expand_generic_action("delete", "indices:data/write/delete") is True
        assert checker._expand_generic_action("delete", "indices:admin/delete") is True

    def test_expand_indices_all_action(self, mock_admin_client):
        """
        PERM-006-E: 汎用アクション展開（indices_all）
        通用动作展开（indices_all）

        覆盖代码行: permission_checker.py:174-232

        测试目的:
          - 验证 "indices_all" 动作映射到 "*"
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert - 执行并验证
        assert checker._expand_generic_action("indices_all", "indices:data/read/search") is True
        assert checker._expand_generic_action("indices_all", "indices:admin/delete") is True

    def test_expand_create_index_action(self, mock_admin_client):
        """
        PERM-006-F: 汎用アクション展開（create_index）
        通用动作展开（create_index）

        覆盖代码行: permission_checker.py:174-232

        测试目的:
          - 验证 "create_index" 动作匹配索引创建
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert - 执行并验证
        assert checker._expand_generic_action("create_index", "indices:admin/create") is True

    def test_fnmatch_wildcard_pattern(self, mock_admin_client):
        """
        PERM-006-G: fnmatchワイルドカードパターンマッチ
        fnmatch 通配符模式匹配

        覆盖代码行: permission_checker.py:220-222

        测试目的:
          - 验证 fnmatch 通配符模式匹配逻辑
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert - 执行并验证
        assert checker._expand_generic_action("indices:data/read/*", "indices:data/read/search") is True
        assert checker._expand_generic_action("indices:admin/*", "indices:admin/create") is True

    def test_no_match_action(self, mock_admin_client):
        """
        PERM-006-H: マッチしないアクション
        不匹配的动作

        覆盖代码行: permission_checker.py:174-232

        测试目的:
          - 验证不匹配的动作返回 False
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert - 执行并验证
        assert checker._expand_generic_action("read", "indices:data/write/index") is False
        assert checker._expand_generic_action("write", "indices:data/read/search") is False
        assert checker._expand_generic_action("unknown_action", "indices:data/read/search") is False


class TestCheckMultipleIndexAccess:
    """
    複数インデックス一括チェックテスト
    多索引一次检查测试

    测试ID: PERM-009
    """

    @pytest.mark.asyncio
    async def test_multiple_index_access_check(self, mock_admin_client):
        """
        PERM-009: 複数インデックス一括チェック
        多索引一次检查

        覆盖代码行: permission_checker.py:278-350

        测试目的:
          - 验证能够批量检查多个索引的访问权限
          - 验证返回正确的索引权限映射
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker

        user_info = {
            "backend_roles": ["logs_reader"],
            "opensearch_security_roles": []
        }
        role_permissions = {
            "index_permissions": [
                {
                    "index_patterns": ["logs-*"],
                    "allowed_actions": ["read"]
                }
            ]
        }

        mock_admin_client.transport.perform_request = AsyncMock(
            side_effect=[
                {"test_user": user_info},
                {"logs_reader": role_permissions}
            ]
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act - 执行被测试函数
        result = await checker.check_multiple_index_access(
            "test_user",
            ["logs-2024", "metrics-2024", "logs-2023"],
            "indices:data/read/search"
        )

        # Assert - 验证结果
        assert result["logs-2024"] is True  # 验证匹配的索引有权限
        assert result["metrics-2024"] is False  # 验证不匹配的索引无权限
        assert result["logs-2023"] is True  # 验证另一个匹配的索引有权限


class TestGetUserAccessibleIndices:
    """
    アクセス可能インデックス取得テスト
    可访问索引获取测试

    测试ID: PERM-010
    """

    @pytest.mark.asyncio
    async def test_get_accessible_indices(self, mock_admin_client):
        """
        PERM-010: アクセス可能インデックス取得
        可访问索引获取

        覆盖代码行: permission_checker.py:356-403

        测试目的:
          - 验证能够获取用户可访问的索引模式列表
          - 验证只返回有指定动作权限的索引模式
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker

        user_info = {
            "backend_roles": ["multi_role"],
            "opensearch_security_roles": []
        }
        role_permissions = {
            "index_permissions": [
                {
                    "index_patterns": ["logs-*", "metrics-*"],
                    "allowed_actions": ["read"]
                },
                {
                    "index_patterns": ["audit-*"],
                    "allowed_actions": ["write"]  # 没有 read 权限
                }
            ]
        }

        mock_admin_client.transport.perform_request = AsyncMock(
            side_effect=[
                {"test_user": user_info},
                {"multi_role": role_permissions}
            ]
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act - 执行被测试函数
        result = await checker.get_user_accessible_indices(
            "test_user",
            "indices:data/read/search"
        )

        # Assert - 验证结果
        assert set(result) == {"logs-*", "metrics-*"}  # 验证返回有 read 权限的模式
        assert "audit-*" not in result  # 验证没有 read 权限的模式不返回


class TestCheckUserIndexAccess:
    """
    便利関数テスト
    便利函数测试

    测试ID: PERM-011
    """

    @pytest.mark.asyncio
    async def test_check_user_index_access_function(self, mock_admin_client):
        """
        PERM-011: 便利関数でのチェック
        便利函数检查

        覆盖代码行: permission_checker.py:406-425

        测试目的:
          - 验证便利函数正确调用 OpenSearchPermissionChecker
          - 验证便利函数返回正确的权限检查结果
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import check_user_index_access

        user_info = {
            "backend_roles": ["reader"],
            "opensearch_security_roles": []
        }
        role_permissions = {
            "index_permissions": [
                {
                    "index_patterns": ["*"],
                    "allowed_actions": ["read"]
                }
            ]
        }

        mock_admin_client.transport.perform_request = AsyncMock(
            side_effect=[
                {"test_user": user_info},
                {"reader": role_permissions}
            ]
        )

        # Act - 执行被测试函数
        result = await check_user_index_access(
            mock_admin_client,
            "test_user",
            "any-index",
            "indices:data/read/search"
        )

        # Assert - 验证结果
        assert result is True  # 验证通过便利函数获得正确结果


# =============================================================================
# 異常系测试 | Error Tests
# =============================================================================

class TestGetUserInfoErrors:
    """
    ユーザー情報取得エラーテスト
    用户信息获取错误测试

    测试ID: PERM-E01, PERM-E02
    """

    @pytest.mark.asyncio
    async def test_get_user_info_not_found(self, mock_admin_client):
        """
        PERM-E01: 存在しないユーザー情報取得でNone
        不存在用户信息获取返回 None

        覆盖代码行: permission_checker.py:54-57

        测试目的:
          - 验证不存在的用户返回 None 而非抛出异常
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker

        mock_admin_client.transport.perform_request = AsyncMock(
            return_value={}  # 用户不存在
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act - 执行被测试函数
        result = await checker.get_user_info("nonexistent_user")

        # Assert - 验证结果
        assert result is None  # 验证返回 None

    @pytest.mark.asyncio
    async def test_get_user_info_api_error(self, mock_admin_client):
        """
        PERM-E02: ユーザー情報取得APIエラー
        用户信息获取 API 错误

        覆盖代码行: permission_checker.py:59-61

        测试目的:
          - 验证 API 错误时抛出 PermissionError
          - 验证错误消息包含用户名信息
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker, PermissionError

        mock_admin_client.transport.perform_request = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert - 执行并验证异常
        with pytest.raises(PermissionError, match="ユーザー情報取得エラー"):
            await checker.get_user_info("test_user")


class TestGetUserRolesErrors:
    """
    ユーザーロール取得エラーテスト
    用户角色获取错误测试

    测试ID: PERM-E03
    """

    @pytest.mark.asyncio
    async def test_get_roles_user_not_found(self, mock_admin_client):
        """
        PERM-E03: 存在しないユーザーのロール取得
        不存在用户的角色获取

        覆盖代码行: permission_checker.py:66-88

        测试目的:
          - 验证不存在用户时抛出 PermissionError
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker, PermissionError

        mock_admin_client.transport.perform_request = AsyncMock(
            return_value={}  # 用户不存在
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert - 执行并验证异常
        with pytest.raises(PermissionError, match="ユーザー.*が存在しません"):
            await checker.get_user_roles("nonexistent_user")


class TestGetRolePermissionsErrors:
    """
    ロール権限取得エラーテスト
    角色权限获取错误测试

    测试ID: PERM-E04, PERM-E05
    """

    @pytest.mark.asyncio
    async def test_get_permissions_role_not_found(self, mock_admin_client):
        """
        PERM-E04: 存在しないロールの権限取得
        不存在角色的权限获取

        覆盖代码行: permission_checker.py:115-117

        测试目的:
          - 验证不存在角色时抛出 PermissionError
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker, PermissionError

        mock_admin_client.transport.perform_request = AsyncMock(
            return_value={}  # 角色不存在
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert - 执行并验证异常
        with pytest.raises(PermissionError, match="ロール.*が存在しません"):
            await checker.get_role_permissions("nonexistent_role")

    @pytest.mark.asyncio
    async def test_get_permissions_api_error(self, mock_admin_client):
        """
        PERM-E05: ロール権限取得APIエラー
        角色权限获取 API 错误

        覆盖代码行: permission_checker.py:119-122

        测试目的:
          - 验证 API 错误时抛出 PermissionError
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker, PermissionError

        mock_admin_client.transport.perform_request = AsyncMock(
            side_effect=Exception("API timeout")
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert - 执行并验证异常
        with pytest.raises(PermissionError, match="ロール権限取得エラー"):
            await checker.get_role_permissions("test_role")


class TestCheckIndexAccessPermissionErrors:
    """
    インデックスアクセス権限チェックエラーテスト
    索引访问权限检查错误测试

    测试ID: PERM-E06, PERM-E07, PERM-E09
    """

    @pytest.mark.asyncio
    async def test_role_check_error_skip_continue(self, mock_admin_client):
        """
        PERM-E06: ロールチェックエラー時のスキップ継続
        角色检查错误时跳过继续

        覆盖代码行: permission_checker.py:158-161

        测试目的:
          - 验证某个角色检查失败时，继续检查其他角色
          - 验证有效角色可以提供访问权限
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker

        user_info = {
            "backend_roles": ["error_role", "valid_role"],
            "opensearch_security_roles": []
        }
        valid_role_permissions = {
            "index_permissions": [
                {
                    "index_patterns": ["logs-*"],
                    "allowed_actions": ["read"]
                }
            ]
        }

        # 基于路径的模拟（不依赖角色顺序）
        async def path_based_side_effect(method, path, **kwargs):
            if "internalusers/test_user" in path:
                return {"test_user": user_info}
            elif "roles/error_role" in path:
                raise Exception("Role API error")  # 此角色出错
            elif "roles/valid_role" in path:
                return {"valid_role": valid_role_permissions}
            return {}

        mock_admin_client.transport.perform_request = AsyncMock(side_effect=path_based_side_effect)
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act - 执行被测试函数
        result = await checker.check_index_access_permission(
            "test_user",
            "logs-2024",
            "indices:data/read/search"
        )

        # Assert - 验证结果
        assert result is True  # 跳过错误角色后，使用有效角色检查成功

    @pytest.mark.asyncio
    async def test_all_roles_check_failed(self, mock_admin_client):
        """
        PERM-E07: 全ロールチェック失敗時
        全角色检查失败时

        覆盖代码行: permission_checker.py:163-165

        测试目的:
          - 验证所有角色检查失败时返回 False
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker

        user_info = {
            "backend_roles": ["role1", "role2"],
            "opensearch_security_roles": []
        }

        # 基于路径的模拟（不依赖角色顺序）
        async def path_based_side_effect(method, path, **kwargs):
            if "internalusers/test_user" in path:
                return {"test_user": user_info}
            elif "/roles/" in path:
                raise Exception("Role API error")  # 所有角色都出错
            return {}

        mock_admin_client.transport.perform_request = AsyncMock(side_effect=path_based_side_effect)
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act - 执行被测试函数
        result = await checker.check_index_access_permission(
            "test_user",
            "logs-2024",
            "indices:data/read/search"
        )

        # Assert - 验证结果
        assert result is False  # 所有角色失败返回 False

    @pytest.mark.asyncio
    async def test_user_roles_fetch_failed(self, mock_admin_client):
        """
        PERM-E09: ユーザーロール取得失敗時
        用户角色获取失败时

        覆盖代码行: permission_checker.py:167-170

        测试目的:
          - 验证用户获取失败时返回 False
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker

        mock_admin_client.transport.perform_request = AsyncMock(
            return_value={}  # 用户不存在
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act - 执行被测试函数
        result = await checker.check_index_access_permission(
            "nonexistent_user",
            "logs-2024",
            "indices:data/read/search"
        )

        # Assert - 验证结果
        assert result is False  # 用户获取失败返回 False


class TestCheckMultipleIndexAccessErrors:
    """
    複数インデックス一括チェックエラーテスト
    多索引一次检查错误测试

    测试ID: PERM-E08, PERM-E08-B
    """

    @pytest.mark.asyncio
    async def test_batch_check_partial_role_error(self, mock_admin_client):
        """
        PERM-E08: バッチチェック中のロール取得失敗（スキップ継続）
        批量检查中部分角色获取失败（跳过继续）

        覆盖代码行: permission_checker.py:301-304

        测试目的:
          - 验证批量检查时角色错误会被跳过
          - 验证有效角色可以提供权限检查
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker

        user_info = {
            "backend_roles": ["error_role", "valid_role"],
            "opensearch_security_roles": []
        }
        valid_role_permissions = {
            "index_permissions": [
                {
                    "index_patterns": ["logs-*"],
                    "allowed_actions": ["read"]
                }
            ]
        }

        # 基于路径的模拟（不依赖角色顺序）
        async def path_based_side_effect(method, path, **kwargs):
            if "internalusers/test_user" in path:
                return {"test_user": user_info}
            elif "roles/error_role" in path:
                raise Exception("Role API error")
            elif "roles/valid_role" in path:
                return {"valid_role": valid_role_permissions}
            return {}

        mock_admin_client.transport.perform_request = AsyncMock(side_effect=path_based_side_effect)
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act - 执行被测试函数
        result = await checker.check_multiple_index_access(
            "test_user",
            ["logs-2024", "metrics-2024"],
            "indices:data/read/search"
        )

        # Assert - 验证结果
        assert result["logs-2024"] is True  # 跳过错误角色后，使用有效角色检查
        assert result["metrics-2024"] is False  # 不匹配的索引拒绝

    @pytest.mark.asyncio
    async def test_batch_check_user_error(self, mock_admin_client):
        """
        PERM-E08-B: バッチチェック中のユーザー取得失敗
        批量检查中用户获取失败

        覆盖代码行: permission_checker.py:344-348

        测试目的:
          - 验证用户获取失败时所有索引都被拒绝
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker

        mock_admin_client.transport.perform_request = AsyncMock(
            return_value={}  # 用户不存在
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act - 执行被测试函数
        result = await checker.check_multiple_index_access(
            "nonexistent_user",
            ["logs-2024", "metrics-2024"],
            "indices:data/read/search"
        )

        # Assert - 验证结果
        assert result["logs-2024"] is False  # 所有索引都被拒绝
        assert result["metrics-2024"] is False  # 所有索引都被拒绝


class TestGetUserAccessibleIndicesErrors:
    """
    アクセス可能インデックス取得エラーテスト
    可访问索引获取错误测试

    测试ID: PERM-E10, PERM-E10-B
    """

    @pytest.mark.asyncio
    async def test_accessible_indices_user_error(self, mock_admin_client):
        """
        PERM-E10: アクセス可能インデックス取得でユーザーエラー
        可访问索引获取时用户错误

        覆盖代码行: permission_checker.py:396-399

        测试目的:
          - 验证用户获取失败时返回空列表
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker

        mock_admin_client.transport.perform_request = AsyncMock(
            return_value={}  # 用户不存在
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act - 执行被测试函数
        result = await checker.get_user_accessible_indices(
            "nonexistent_user",
            "indices:data/read/search"
        )

        # Assert - 验证结果
        assert result == []  # 返回空列表

    @pytest.mark.asyncio
    async def test_accessible_indices_partial_role_error(self, mock_admin_client):
        """
        PERM-E10-B: 一部ロールでエラー時のスキップ継続
        部分角色错误时跳过继续

        覆盖代码行: permission_checker.py:381-384

        测试目的:
          - 验证部分角色错误时跳过继续
          - 验证从有效角色获取索引模式
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker

        user_info = {
            "backend_roles": ["error_role", "valid_role"],
            "opensearch_security_roles": []
        }
        valid_role_permissions = {
            "index_permissions": [
                {
                    "index_patterns": ["logs-*"],
                    "allowed_actions": ["read"]
                }
            ]
        }

        # 基于路径的模拟（不依赖角色顺序）
        async def path_based_side_effect(method, path, **kwargs):
            if "internalusers/test_user" in path:
                return {"test_user": user_info}
            elif "roles/error_role" in path:
                raise Exception("Role API error")
            elif "roles/valid_role" in path:
                return {"valid_role": valid_role_permissions}
            return {}

        mock_admin_client.transport.perform_request = AsyncMock(side_effect=path_based_side_effect)
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act - 执行被测试函数
        result = await checker.get_user_accessible_indices(
            "test_user",
            "indices:data/read/search"
        )

        # Assert - 验证结果
        assert "logs-*" in result  # 跳过错误角色后，从有效角色获取模式


# =============================================================================
# セキュリティ测试 | Security Tests
# =============================================================================

@pytest.mark.security
class TestPermissionSecurity:
    """
    セキュリティテスト
    安全测试

    测试ID: PERM-SEC-01 ~ PERM-SEC-06
    """

    @pytest.mark.asyncio
    async def test_no_permission_user_denied(self, mock_admin_client):
        """
        PERM-SEC-01: 権限なしユーザーのアクセス拒否
        无权限用户的访问拒绝

        覆盖代码行: permission_checker.py:124-170

        测试目的:
          - 验证没有任何角色的用户无法访问任何索引
          - 验证安全默认行为（默认拒绝）
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker

        user_info = {
            "backend_roles": [],
            "opensearch_security_roles": []
        }

        mock_admin_client.transport.perform_request = AsyncMock(
            return_value={"no_role_user": user_info}
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act - 执行被测试函数
        result = await checker.check_index_access_permission(
            "no_role_user",
            "sensitive-data",
            "indices:data/read/search"
        )

        # Assert - 验证结果
        assert result is False  # 无权限用户被拒绝访问

    @pytest.mark.asyncio
    async def test_wildcard_pattern_safety(self, mock_admin_client):
        """
        PERM-SEC-02: ワイルドカードパターンの安全性
        通配符模式的安全性

        覆盖代码行: permission_checker.py:256-265

        测试目的:
          - 验证 "*" 模式的行为（匹配所有索引）
          - 警告：生产环境应排除 .security 等系统索引
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker

        user_info = {
            "backend_roles": ["limited_admin"],
            "opensearch_security_roles": []
        }
        # "*" 模式 - 可以访问所有索引
        role_permissions = {
            "index_permissions": [
                {
                    "index_patterns": ["*"],
                    "allowed_actions": ["read"]
                }
            ]
        }

        # 基于路径的模拟（不依赖角色顺序）
        async def path_based_side_effect(method, path, **kwargs):
            if "internalusers/test_user" in path:
                return {"test_user": user_info}
            elif "roles/limited_admin" in path:
                return {"limited_admin": role_permissions}
            return {}

        mock_admin_client.transport.perform_request = AsyncMock(side_effect=path_based_side_effect)
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act - 执行被测试函数
        result = await checker.check_index_access_permission(
            "test_user",
            ".security",  # 安全相关索引
            "indices:data/read/search"
        )

        # Assert - 验证结果
        assert result is True  # "*" 模式匹配所有索引（包括系统索引）
        # 注：生产环境应该在 OpenSearch 配置中排除系统索引

    @pytest.mark.asyncio
    async def test_minimum_privilege_principle(self, mock_admin_client):
        """
        PERM-SEC-05: 最小権限の原則検証
        最小权限原则验证

        覆盖代码行: permission_checker.py:174-232, 236-272

        测试目的:
          - 验证只有 read 权限的角色无法执行 write 操作
          - 验证最小权限原则的实现
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker

        user_info = {
            "backend_roles": ["read_only_role"],
            "opensearch_security_roles": []
        }
        role_permissions = {
            "index_permissions": [
                {
                    "index_patterns": ["logs-*"],
                    "allowed_actions": ["read"]  # 只有 read 权限
                }
            ]
        }

        # 基于路径的模拟（不依赖角色顺序，支持多次调用）
        async def path_based_side_effect(method, path, **kwargs):
            if "internalusers/test_user" in path:
                return {"test_user": user_info}
            elif "roles/read_only_role" in path:
                return {"read_only_role": role_permissions}
            return {}

        mock_admin_client.transport.perform_request = AsyncMock(side_effect=path_based_side_effect)
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act - 执行被测试函数（两次调用）
        read_result = await checker.check_index_access_permission(
            "test_user",
            "logs-2024",
            "indices:data/read/search"
        )
        write_result = await checker.check_index_access_permission(
            "test_user",
            "logs-2024",
            "indices:data/write/index"
        )

        # Assert - 验证结果
        assert read_result is True  # read 权限许可
        assert write_result is False  # write 权限拒绝

    @pytest.mark.asyncio
    async def test_injection_attack_resistance(self, mock_admin_client):
        """
        PERM-SEC-04: インジェクション攻撃への耐性
        注入攻击的耐性

        覆盖代码行: permission_checker.py:44-52

        测试目的:
          - 验证恶意用户名会被正确传递给 OpenSearch API
          - 实际的清理由 OpenSearch 负责
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker

        malicious_usernames = [
            "user'; DROP TABLE users;--",
            "user\x00admin",
            "../../../etc/passwd",
            "user<script>alert('xss')</script>"
        ]

        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert - 对每个恶意用户名验证 API 调用
        for username in malicious_usernames:
            mock_admin_client.transport.perform_request = AsyncMock(return_value={})

            await checker.get_user_info(username)

            # 验证 API 使用正确路径调用
            called_args = mock_admin_client.transport.perform_request.call_args
            called_path = called_args[0][1]
            expected_path = f"/_plugins/_security/api/internalusers/{username}"
            assert called_path == expected_path, f"路径不匹配: {called_path}"

    @pytest.mark.asyncio
    async def test_role_escalation_prevention(self, mock_admin_client):
        """
        PERM-SEC-03: ロール昇格攻撃の防止
        角色提升攻击的防止

        覆盖代码行: permission_checker.py:124-170

        测试目的:
          - 验证用户无法访问未分配角色的权限
          - 验证权限提升攻击被正确阻止
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker

        # 用户只有有限的角色
        user_info = {
            "backend_roles": ["limited_role"],
            "opensearch_security_roles": []
        }
        limited_role_permissions = {
            "index_permissions": [
                {
                    "index_patterns": ["public-*"],
                    "allowed_actions": ["read"]
                }
            ]
        }

        # 基于路径的模拟（不依赖角色顺序）
        async def path_based_side_effect(method, path, **kwargs):
            if "internalusers/test_user" in path:
                return {"test_user": user_info}
            elif "roles/limited_role" in path:
                return {"limited_role": limited_role_permissions}
            return {}

        mock_admin_client.transport.perform_request = AsyncMock(side_effect=path_based_side_effect)
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act - 尝试访问需要 admin 角色的索引
        result = await checker.check_index_access_permission(
            "test_user",
            "admin-secrets",  # 明显超出权限的索引
            "indices:data/read/search"
        )

        # Assert - 验证结果
        assert result is False  # 无法获取未分配角色的权限

    @pytest.mark.asyncio
    async def test_timing_attack_resistance(self, mock_admin_client):
        """
        PERM-SEC-06: 権限チェック時のタイミング攻撃耐性
        权限检查时的时间攻击耐性

        覆盖代码行: permission_checker.py:124-170

        测试目的:
          - 验证存在和不存在的用户处理时间没有极端差异
          - 防止通过时间差异推断用户存在性
        """
        # Arrange - 准备测试数据
        from app.core.permission_checker import OpenSearchPermissionChecker

        # 存在的用户
        existing_user_info = {
            "backend_roles": ["role1"],
            "opensearch_security_roles": []
        }
        role_permissions = {
            "index_permissions": [
                {"index_patterns": ["logs-*"], "allowed_actions": ["read"]}
            ]
        }

        checker = OpenSearchPermissionChecker(mock_admin_client)

        # 存在用户的检查时间（基于路径的模拟）
        async def existing_user_side_effect(method, path, **kwargs):
            if "internalusers/existing_user" in path:
                return {"existing_user": existing_user_info}
            elif "roles/role1" in path:
                return {"role1": role_permissions}
            return {}

        mock_admin_client.transport.perform_request = AsyncMock(side_effect=existing_user_side_effect)
        start = time.perf_counter()
        await checker.check_index_access_permission(
            "existing_user", "logs-2024", "indices:data/read/search"
        )
        existing_time = time.perf_counter() - start

        # 不存在用户的检查时间（基于路径的模拟）
        async def nonexistent_user_side_effect(method, path, **kwargs):
            if "internalusers/" in path:
                return {}  # 用户不存在
            return {}

        mock_admin_client.transport.perform_request = AsyncMock(side_effect=nonexistent_user_side_effect)
        start = time.perf_counter()
        await checker.check_index_access_permission(
            "nonexistent_user", "logs-2024", "indices:data/read/search"
        )
        nonexistent_time = time.perf_counter() - start

        # Assert - 验证处理时间没有极端差异
        # 注：模拟环境下严格验证困难，只检查没有极端差异（100倍以上）
        ratio = max(existing_time, nonexistent_time) / max(min(existing_time, nonexistent_time), 0.0001)
        assert ratio < 100, f"处理时间差异过大: {existing_time:.6f}s vs {nonexistent_time:.6f}s"
