# permission_checker テストケース

## 1. 概要

OpenSearch動的権限チェック機能のテストケースを定義します。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `PermissionError` | 権限チェック関連のカスタム例外 |
| `OpenSearchPermissionChecker.__init__()` | 管理者クライアントを受け取る初期化 |
| `get_user_info()` | 指定ユーザーの詳細情報取得 |
| `get_user_roles()` | ユーザーに割り当てられたロール一覧取得 |
| `get_role_permissions()` | 指定ロールの権限情報取得 |
| `check_index_access_permission()` | インデックスアクセス権限チェック |
| `_expand_generic_action()` | 汎用アクション（read/write等）を具体的アクションに展開 |
| `_check_role_index_access()` | ロール別インデックスアクセスチェック（非同期） |
| `_check_role_index_access_sync()` | ロール別インデックスアクセスチェック（同期） |
| `check_multiple_index_access()` | 複数インデックス一括チェック |
| `get_user_accessible_indices()` | アクセス可能インデックスパターン取得 |
| `check_user_index_access()` | インデックスアクセス権限チェック便利関数 |

### 1.2 カバレッジ目標: 85%

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/core/permission_checker.py` |
| テストコード | `test/unit/core/test_permission_checker.py` |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| PERM-INIT | OpenSearchPermissionChecker初期化 | admin_client | checkerインスタンス |
| PERM-001 | ユーザー情報取得成功 | 存在するユーザー名 | ユーザー情報dict |
| PERM-002 | ユーザーロール取得成功 | 存在するユーザー名 | ロール名リスト |
| PERM-003 | ロール権限取得成功 | 存在するロール名 | 権限情報dict |
| PERM-004 | インデックスアクセス権限あり | 権限を持つユーザー | True |
| PERM-005 | インデックスアクセス権限なし | 権限を持たないユーザー | False |
| PERM-006 | 汎用アクション展開（read） | "read", "indices:data/read/search" | True |
| PERM-007 | 汎用アクション展開（write） | "write", "indices:data/write/index" | True |
| PERM-008 | 汎用アクション展開（ワイルドカード） | "*", 任意のアクション | True |
| PERM-009 | 複数インデックス一括チェック | 複数インデックス名 | インデックス別結果dict |
| PERM-010 | アクセス可能インデックス取得 | ユーザー名 | パターンリスト |
| PERM-011 | 便利関数でのチェック | admin_client, username, index_name | bool |
| PERM-012 | backend_rolesとopensearch_security_rolesの統合 | 両方にロールを持つユーザー | 重複なしリスト |
| PERM-013 | ワイルドカードインデックスパターンマッチ | "logs-*"パターン | True（マッチ時） |
| PERM-014 | 複数アクション許可のロール | crud許可ロール | read/write両方True |

### 2.1 OpenSearchPermissionChecker 初期化テスト

```python
# test/unit/core/test_permission_checker.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestOpenSearchPermissionCheckerInit:
    """OpenSearchPermissionChecker初期化テスト"""

    def test_init_with_admin_client(self, mock_admin_client):
        """PERM-INIT: 管理者クライアントで初期化"""
        # Act
        from app.core.permission_checker import OpenSearchPermissionChecker
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Assert
        assert checker.admin_client is mock_admin_client
```

### 2.2 get_user_info テスト

```python
class TestGetUserInfo:
    """ユーザー情報取得テスト"""

    @pytest.mark.asyncio
    async def test_get_user_info_success(self, mock_admin_client):
        """PERM-001: ユーザー情報取得成功"""
        # Arrange
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

        # Act
        result = await checker.get_user_info("test_user")

        # Assert
        assert result == expected_user_info
        mock_admin_client.transport.perform_request.assert_called_once_with(
            "GET",
            "/_plugins/_security/api/internalusers/test_user",
            headers={"Content-Type": "application/json"}
        )

```

### 2.3 get_user_roles テスト

```python
class TestGetUserRoles:
    """ユーザーロール取得テスト"""

    @pytest.mark.asyncio
    async def test_get_user_roles_success(self, mock_admin_client):
        """PERM-002: ユーザーロール取得成功"""
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker

        user_info = {
            "backend_roles": ["admin", "developer"],
            "opensearch_security_roles": ["all_access"]
        }
        mock_admin_client.transport.perform_request = AsyncMock(
            return_value={"test_user": user_info}
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act
        result = await checker.get_user_roles("test_user")

        # Assert
        assert set(result) == {"admin", "developer", "all_access"}

    @pytest.mark.asyncio
    async def test_get_user_roles_deduplicate(self, mock_admin_client):
        """PERM-012: backend_rolesとopensearch_security_rolesの統合（重複除去）"""
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker

        user_info = {
            "backend_roles": ["admin", "shared_role"],
            "opensearch_security_roles": ["shared_role", "reader"]
        }
        mock_admin_client.transport.perform_request = AsyncMock(
            return_value={"test_user": user_info}
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act
        result = await checker.get_user_roles("test_user")

        # Assert
        assert len(result) == len(set(result))  # 重複なし
        assert set(result) == {"admin", "shared_role", "reader"}
```

### 2.4 get_role_permissions テスト

```python
class TestGetRolePermissions:
    """ロール権限取得テスト"""

    @pytest.mark.asyncio
    async def test_get_role_permissions_success(self, mock_admin_client):
        """PERM-003: ロール権限取得成功"""
        # Arrange
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

        # Act
        result = await checker.get_role_permissions("test_role")

        # Assert
        assert result == expected_permissions
```

### 2.5 check_index_access_permission テスト

```python
class TestCheckIndexAccessPermission:
    """インデックスアクセス権限チェックテスト"""

    @pytest.mark.asyncio
    async def test_index_access_granted(self, mock_admin_client):
        """PERM-004: インデックスアクセス権限あり"""
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker

        # ユーザー情報
        user_info = {
            "backend_roles": ["reader_role"],
            "opensearch_security_roles": []
        }
        # ロール権限
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

        # Act
        result = await checker.check_index_access_permission(
            "test_user",
            "logs-2024",
            "indices:data/read/search"
        )

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_index_access_denied(self, mock_admin_client):
        """PERM-005: インデックスアクセス権限なし"""
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker

        user_info = {
            "backend_roles": ["reader_role"],
            "opensearch_security_roles": []
        }
        role_permissions = {
            "index_permissions": [
                {
                    "index_patterns": ["other-*"],  # マッチしないパターン
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

        # Act
        result = await checker.check_index_access_permission(
            "test_user",
            "logs-2024",
            "indices:data/read/search"
        )

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_wildcard_index_pattern_match(self, mock_admin_client):
        """PERM-013: ワイルドカードインデックスパターンマッチ"""
        # Arrange
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

        # Act
        result = await checker.check_index_access_permission(
            "test_user",
            "logs-2024-01-30",
            "indices:data/read/search"
        )

        # Assert
        assert result is True
```

### 2.6 _expand_generic_action テスト

```python
class TestExpandGenericAction:
    """汎用アクション展開テスト"""

    def test_expand_read_action(self, mock_admin_client):
        """PERM-006: 汎用アクション展開（read）"""
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert
        assert checker._expand_generic_action("read", "indices:data/read/search") is True
        assert checker._expand_generic_action("read", "indices:data/read/get") is True
        assert checker._expand_generic_action("read", "indices:data/read/mget") is True
        assert checker._expand_generic_action("read", "indices:admin/get") is True

    def test_expand_write_action(self, mock_admin_client):
        """PERM-007: 汎用アクション展開（write）"""
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert
        assert checker._expand_generic_action("write", "indices:data/write/index") is True
        assert checker._expand_generic_action("write", "indices:data/write/update") is True
        assert checker._expand_generic_action("write", "indices:data/write/bulk") is True
        assert checker._expand_generic_action("write", "indices:data/write/delete") is True

    def test_expand_wildcard_action(self, mock_admin_client):
        """PERM-008: 汎用アクション展開（ワイルドカード）"""
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert
        assert checker._expand_generic_action("*", "indices:data/read/search") is True
        assert checker._expand_generic_action("*", "indices:data/write/index") is True
        assert checker._expand_generic_action("*", "cluster:admin/settings") is True

    def test_expand_crud_action(self, mock_admin_client):
        """PERM-014: 複数アクション許可のロール（crud）"""
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert - crud は read/* と write/* をカバー
        assert checker._expand_generic_action("crud", "indices:data/read/search") is True
        assert checker._expand_generic_action("crud", "indices:data/write/index") is True

    def test_expand_manage_action(self, mock_admin_client):
        """PERM-006-B: 汎用アクション展開（manage）"""
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert
        assert checker._expand_generic_action("manage", "indices:admin/create") is True
        assert checker._expand_generic_action("manage", "indices:admin/delete") is True
        assert checker._expand_generic_action("manage", "indices:admin/mappings/put") is True

    def test_expand_index_action(self, mock_admin_client):
        """PERM-006-C: 汎用アクション展開（index）"""
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert
        assert checker._expand_generic_action("index", "indices:data/write/index") is True
        assert checker._expand_generic_action("index", "indices:data/write/update") is True
        assert checker._expand_generic_action("index", "indices:data/write/bulk") is True

    def test_expand_delete_action(self, mock_admin_client):
        """PERM-006-D: 汎用アクション展開（delete）"""
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert
        assert checker._expand_generic_action("delete", "indices:data/write/delete") is True
        assert checker._expand_generic_action("delete", "indices:admin/delete") is True

    def test_expand_indices_all_action(self, mock_admin_client):
        """PERM-006-E: 汎用アクション展開（indices_all）"""
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert - indices_all は * にマッピング
        assert checker._expand_generic_action("indices_all", "indices:data/read/search") is True
        assert checker._expand_generic_action("indices_all", "indices:admin/delete") is True

    def test_expand_create_index_action(self, mock_admin_client):
        """PERM-006-F: 汎用アクション展開（create_index）"""
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert
        assert checker._expand_generic_action("create_index", "indices:admin/create") is True

    def test_fnmatch_wildcard_pattern(self, mock_admin_client):
        """PERM-006-G: fnmatchワイルドカードパターンマッチ"""
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert
        assert checker._expand_generic_action("indices:data/read/*", "indices:data/read/search") is True
        assert checker._expand_generic_action("indices:admin/*", "indices:admin/create") is True

    def test_no_match_action(self, mock_admin_client):
        """PERM-006-H: マッチしないアクション"""
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert
        assert checker._expand_generic_action("read", "indices:data/write/index") is False
        assert checker._expand_generic_action("write", "indices:data/read/search") is False
        assert checker._expand_generic_action("unknown_action", "indices:data/read/search") is False
```

### 2.7 check_multiple_index_access テスト

```python
class TestCheckMultipleIndexAccess:
    """複数インデックス一括チェックテスト"""

    @pytest.mark.asyncio
    async def test_multiple_index_access_check(self, mock_admin_client):
        """PERM-009: 複数インデックス一括チェック"""
        # Arrange
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

        # Act
        result = await checker.check_multiple_index_access(
            "test_user",
            ["logs-2024", "metrics-2024", "logs-2023"],
            "indices:data/read/search"
        )

        # Assert
        assert result["logs-2024"] is True
        assert result["metrics-2024"] is False  # パターンにマッチしない
        assert result["logs-2023"] is True
```

### 2.8 get_user_accessible_indices テスト

```python
class TestGetUserAccessibleIndices:
    """アクセス可能インデックス取得テスト"""

    @pytest.mark.asyncio
    async def test_get_accessible_indices(self, mock_admin_client):
        """PERM-010: アクセス可能インデックス取得"""
        # Arrange
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
                    "allowed_actions": ["write"]  # read権限なし
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

        # Act
        result = await checker.get_user_accessible_indices(
            "test_user",
            "indices:data/read/search"
        )

        # Assert
        assert set(result) == {"logs-*", "metrics-*"}
        assert "audit-*" not in result  # write権限のみなので含まれない
```

### 2.9 便利関数テスト

```python
class TestCheckUserIndexAccess:
    """便利関数テスト"""

    @pytest.mark.asyncio
    async def test_check_user_index_access_function(self, mock_admin_client):
        """PERM-011: 便利関数でのチェック"""
        # Arrange
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

        # Act
        result = await check_user_index_access(
            mock_admin_client,
            "test_user",
            "any-index",
            "indices:data/read/search"
        )

        # Assert
        assert result is True
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| PERM-E01 | 存在しないユーザー情報取得でNone | 存在しないユーザー名 | None |
| PERM-E02 | ユーザー情報取得APIエラー | APIエラー発生 | PermissionError |
| PERM-E03 | 存在しないユーザーのロール取得 | 存在しないユーザー名 | PermissionError |
| PERM-E04 | 存在しないロールの権限取得 | 存在しないロール名 | PermissionError |
| PERM-E05 | ロール権限取得APIエラー | APIエラー発生 | PermissionError |
| PERM-E06 | ロールチェックエラー時のスキップ継続 | 一部ロールでエラー | 他ロールでチェック継続 |
| PERM-E07 | 全ロールチェック失敗時 | 全ロールでエラー | False |
| PERM-E08 | バッチチェック中のロール取得失敗 | 一部ロールでAPIエラー | エラーロールはスキップ |
| PERM-E09 | ユーザーロール取得失敗時 | get_user_roles失敗 | False |
| PERM-E10 | アクセス可能インデックス取得でユーザーエラー | 存在しないユーザー | 空リスト |

### 3.1 get_user_info 異常系

```python
class TestGetUserInfoErrors:
    """ユーザー情報取得エラーテスト"""

    @pytest.mark.asyncio
    async def test_get_user_info_not_found(self, mock_admin_client):
        """PERM-E01: 存在しないユーザー情報取得でNone"""
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker

        mock_admin_client.transport.perform_request = AsyncMock(
            return_value={}  # ユーザーが含まれないレスポンス
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act
        result = await checker.get_user_info("nonexistent_user")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_info_api_error(self, mock_admin_client):
        """PERM-E02: ユーザー情報取得APIエラー"""
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker, PermissionError

        mock_admin_client.transport.perform_request = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert
        with pytest.raises(PermissionError, match="ユーザー情報取得エラー"):
            await checker.get_user_info("test_user")
```

### 3.2 get_user_roles 異常系

```python
class TestGetUserRolesErrors:
    """ユーザーロール取得エラーテスト"""

    @pytest.mark.asyncio
    async def test_get_roles_user_not_found(self, mock_admin_client):
        """PERM-E03: 存在しないユーザーのロール取得"""
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker, PermissionError

        mock_admin_client.transport.perform_request = AsyncMock(
            return_value={}  # ユーザーが見つからない
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert
        with pytest.raises(PermissionError, match="ユーザー.*が存在しません"):
            await checker.get_user_roles("nonexistent_user")
```

### 3.3 get_role_permissions 異常系

```python
class TestGetRolePermissionsErrors:
    """ロール権限取得エラーテスト"""

    @pytest.mark.asyncio
    async def test_get_permissions_role_not_found(self, mock_admin_client):
        """PERM-E04: 存在しないロールの権限取得"""
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker, PermissionError

        mock_admin_client.transport.perform_request = AsyncMock(
            return_value={}  # ロールが見つからない
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert
        with pytest.raises(PermissionError, match="ロール.*が存在しません"):
            await checker.get_role_permissions("nonexistent_role")

    @pytest.mark.asyncio
    async def test_get_permissions_api_error(self, mock_admin_client):
        """PERM-E05: ロール権限取得APIエラー"""
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker, PermissionError

        mock_admin_client.transport.perform_request = AsyncMock(
            side_effect=Exception("API timeout")
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert
        with pytest.raises(PermissionError, match="ロール権限取得エラー"):
            await checker.get_role_permissions("test_role")
```

### 3.4 check_index_access_permission 異常系

```python
class TestCheckIndexAccessPermissionErrors:
    """インデックスアクセス権限チェックエラーテスト"""

    @pytest.mark.asyncio
    async def test_role_check_error_skip_continue(self, mock_admin_client):
        """PERM-E06: ロールチェックエラー時のスキップ継続"""
        # Arrange
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

        # パスベースモック（ロール順序に依存しない）
        async def path_based_side_effect(method, path, **kwargs):
            if "internalusers/test_user" in path:
                return {"test_user": user_info}
            elif "roles/error_role" in path:
                raise Exception("Role API error")  # このロールでエラー
            elif "roles/valid_role" in path:
                return {"valid_role": valid_role_permissions}
            return {}

        mock_admin_client.transport.perform_request = AsyncMock(side_effect=path_based_side_effect)
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act
        result = await checker.check_index_access_permission(
            "test_user",
            "logs-2024",
            "indices:data/read/search"
        )

        # Assert - エラーのロールをスキップして次のロールでチェック成功
        assert result is True

    @pytest.mark.asyncio
    async def test_all_roles_check_failed(self, mock_admin_client):
        """PERM-E07: 全ロールチェック失敗時"""
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker

        user_info = {
            "backend_roles": ["role1", "role2"],
            "opensearch_security_roles": []
        }

        # パスベースモック（ロール順序に依存しない）
        async def path_based_side_effect(method, path, **kwargs):
            if "internalusers/test_user" in path:
                return {"test_user": user_info}
            elif "/roles/" in path:
                raise Exception("Role API error")  # 全ロールでエラー
            return {}

        mock_admin_client.transport.perform_request = AsyncMock(side_effect=path_based_side_effect)
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act
        result = await checker.check_index_access_permission(
            "test_user",
            "logs-2024",
            "indices:data/read/search"
        )

        # Assert - 全ロール失敗でFalse
        assert result is False

    @pytest.mark.asyncio
    async def test_user_roles_fetch_failed(self, mock_admin_client):
        """PERM-E09: ユーザーロール取得失敗時"""
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker

        mock_admin_client.transport.perform_request = AsyncMock(
            return_value={}  # ユーザーが見つからない
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act
        result = await checker.check_index_access_permission(
            "nonexistent_user",
            "logs-2024",
            "indices:data/read/search"
        )

        # Assert - ユーザー取得失敗でFalse
        assert result is False
```

### 3.5 check_multiple_index_access 異常系

```python
class TestCheckMultipleIndexAccessErrors:
    """複数インデックス一括チェックエラーテスト"""

    @pytest.mark.asyncio
    async def test_batch_check_partial_role_error(self, mock_admin_client):
        """PERM-E08: バッチチェック中のロール取得失敗（スキップ継続）"""
        # Arrange
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

        # パスベースモック（ロール順序に依存しない）
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

        # Act
        result = await checker.check_multiple_index_access(
            "test_user",
            ["logs-2024", "metrics-2024"],
            "indices:data/read/search"
        )

        # Assert - エラーロールをスキップして有効なロールでチェック
        assert result["logs-2024"] is True
        assert result["metrics-2024"] is False

    @pytest.mark.asyncio
    async def test_batch_check_user_error(self, mock_admin_client):
        """PERM-E08-B: バッチチェック中のユーザー取得失敗"""
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker

        mock_admin_client.transport.perform_request = AsyncMock(
            return_value={}  # ユーザーが見つからない
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act
        result = await checker.check_multiple_index_access(
            "nonexistent_user",
            ["logs-2024", "metrics-2024"],
            "indices:data/read/search"
        )

        # Assert - 全インデックスが拒否
        assert result["logs-2024"] is False
        assert result["metrics-2024"] is False
```

### 3.6 get_user_accessible_indices 異常系

```python
class TestGetUserAccessibleIndicesErrors:
    """アクセス可能インデックス取得エラーテスト"""

    @pytest.mark.asyncio
    async def test_accessible_indices_user_error(self, mock_admin_client):
        """PERM-E10: アクセス可能インデックス取得でユーザーエラー"""
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker

        mock_admin_client.transport.perform_request = AsyncMock(
            return_value={}  # ユーザーが見つからない
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act
        result = await checker.get_user_accessible_indices(
            "nonexistent_user",
            "indices:data/read/search"
        )

        # Assert - 空リスト
        assert result == []

    @pytest.mark.asyncio
    async def test_accessible_indices_partial_role_error(self, mock_admin_client):
        """PERM-E10-B: 一部ロールでエラー時のスキップ継続"""
        # Arrange
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

        # パスベースモック（ロール順序に依存しない）
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

        # Act
        result = await checker.get_user_accessible_indices(
            "test_user",
            "indices:data/read/search"
        )

        # Assert - エラーロールをスキップして有効なロールからパターン取得
        assert "logs-*" in result
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| PERM-SEC-01 | 権限なしユーザーのアクセス拒否 | 権限なしユーザー | False |
| PERM-SEC-02 | ワイルドカードパターンの挙動確認 | "*"パターン | 全インデックスにマッチ（注意必要） |
| PERM-SEC-03 | ロール昇格攻撃の防止 | 権限外インデックスへのアクセス | False（アクセス拒否） |
| PERM-SEC-04 | インジェクション攻撃への耐性 | 特殊文字を含むユーザー名 | OpenSearch APIに転送（サニタイズはOS側） |
| PERM-SEC-05 | 最小権限の原則検証 | 特定アクションのみ許可ロール | 他アクション拒否 |
| PERM-SEC-06 | 権限チェック時のタイミング攻撃耐性 | 存在/非存在ユーザー | 同等の処理時間 |

```python
@pytest.mark.security
class TestPermissionSecurity:
    """セキュリティテスト"""

    @pytest.mark.asyncio
    async def test_no_permission_user_denied(self, mock_admin_client):
        """PERM-SEC-01: 権限なしユーザーのアクセス拒否"""
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker

        user_info = {
            "backend_roles": [],
            "opensearch_security_roles": []
        }

        mock_admin_client.transport.perform_request = AsyncMock(
            return_value={"no_role_user": user_info}
        )
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act
        result = await checker.check_index_access_permission(
            "no_role_user",
            "sensitive-data",
            "indices:data/read/search"
        )

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_wildcard_pattern_safety(self, mock_admin_client):
        """PERM-SEC-02: ワイルドカードパターンの安全性"""
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker

        user_info = {
            "backend_roles": ["limited_admin"],
            "opensearch_security_roles": []
        }
        # "*" パターンを持つロール - 全インデックスにアクセス可能
        role_permissions = {
            "index_permissions": [
                {
                    "index_patterns": ["*"],
                    "allowed_actions": ["read"]
                }
            ]
        }

        # パスベースモック（ロール順序に依存しない）
        async def path_based_side_effect(method, path, **kwargs):
            if "internalusers/test_user" in path:
                return {"test_user": user_info}
            elif "roles/limited_admin" in path:
                return {"limited_admin": role_permissions}
            return {}

        mock_admin_client.transport.perform_request = AsyncMock(side_effect=path_based_side_effect)
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act
        result = await checker.check_index_access_permission(
            "test_user",
            ".security",  # セキュリティ関連インデックス
            "indices:data/read/search"
        )

        # Assert - "*"パターンは全てにマッチするため True
        # 注: 本番環境では.security等をexcludeするべき
        assert result is True

    @pytest.mark.asyncio
    async def test_minimum_privilege_principle(self, mock_admin_client):
        """PERM-SEC-05: 最小権限の原則検証"""
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker

        user_info = {
            "backend_roles": ["read_only_role"],
            "opensearch_security_roles": []
        }
        role_permissions = {
            "index_permissions": [
                {
                    "index_patterns": ["logs-*"],
                    "allowed_actions": ["read"]  # readのみ
                }
            ]
        }

        # パスベースモック（ロール順序に依存しない、複数回呼び出し対応）
        async def path_based_side_effect(method, path, **kwargs):
            if "internalusers/test_user" in path:
                return {"test_user": user_info}
            elif "roles/read_only_role" in path:
                return {"read_only_role": role_permissions}
            return {}

        mock_admin_client.transport.perform_request = AsyncMock(side_effect=path_based_side_effect)
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act
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

        # Assert
        assert read_result is True  # read許可
        assert write_result is False  # write拒否

    @pytest.mark.asyncio
    async def test_injection_attack_resistance(self, mock_admin_client):
        """PERM-SEC-04: インジェクション攻撃への耐性

        悪意のあるユーザー名がAPIパスに渡されても、
        適切にOpenSearch Security APIに転送されることを検証。
        実際のサニタイズはOpenSearch側が担当。
        """
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker

        malicious_usernames = [
            "user'; DROP TABLE users;--",
            "user\x00admin",
            "../../../etc/passwd",
            "user<script>alert('xss')</script>"
        ]

        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act & Assert - 各悪意のあるユーザー名でAPIが呼び出されることを確認
        for username in malicious_usernames:
            mock_admin_client.transport.perform_request = AsyncMock(return_value={})

            await checker.get_user_info(username)

            # APIが正しいパスで呼び出されていることを検証
            called_args = mock_admin_client.transport.perform_request.call_args
            called_path = called_args[0][1]
            expected_path = f"/_plugins/_security/api/internalusers/{username}"
            assert called_path == expected_path, f"パス不一致: {called_path}"

    @pytest.mark.asyncio
    async def test_role_escalation_prevention(self, mock_admin_client):
        """PERM-SEC-03: ロール昇格攻撃の防止

        ユーザーが自身に割り当てられていないロールの権限を
        取得できないことを検証。
        """
        # Arrange
        from app.core.permission_checker import OpenSearchPermissionChecker

        # ユーザーには限定的なロールのみ割り当て
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

        # パスベースモック（ロール順序に依存しない）
        async def path_based_side_effect(method, path, **kwargs):
            if "internalusers/test_user" in path:
                return {"test_user": user_info}
            elif "roles/limited_role" in path:
                return {"limited_role": limited_role_permissions}
            return {}

        mock_admin_client.transport.perform_request = AsyncMock(side_effect=path_based_side_effect)
        checker = OpenSearchPermissionChecker(mock_admin_client)

        # Act - adminロールが必要なインデックスへのアクセスを試みる
        result = await checker.check_index_access_permission(
            "test_user",
            "admin-secrets",  # 明らかに権限外のインデックス
            "indices:data/read/search"
        )

        # Assert - 割り当てられていないロールの権限は取得できない
        assert result is False

    @pytest.mark.asyncio
    async def test_timing_attack_resistance(self, mock_admin_client):
        """PERM-SEC-06: 権限チェック時のタイミング攻撃耐性

        存在するユーザーと存在しないユーザーで
        処理時間に大きな差がないことを検証。
        注: 厳密なタイミング検証ではなく、
        早期リターンによる情報漏洩がないことの確認。
        """
        # Arrange
        import time
        from app.core.permission_checker import OpenSearchPermissionChecker

        # 存在するユーザー
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

        # 存在するユーザーのチェック時間（パスベースモック）
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

        # 存在しないユーザーのチェック時間（パスベースモック）
        async def nonexistent_user_side_effect(method, path, **kwargs):
            if "internalusers/" in path:
                return {}  # ユーザーが見つからない
            return {}

        mock_admin_client.transport.perform_request = AsyncMock(side_effect=nonexistent_user_side_effect)
        start = time.perf_counter()
        await checker.check_index_access_permission(
            "nonexistent_user", "logs-2024", "indices:data/read/search"
        )
        nonexistent_time = time.perf_counter() - start

        # Assert - 処理時間が極端に異ならないこと
        # 注: モック環境では厳密な検証は難しいため、
        # 早期リターンによる極端な差（100倍以上）がないことのみ確認
        ratio = max(existing_time, nonexistent_time) / max(min(existing_time, nonexistent_time), 0.0001)
        assert ratio < 100, f"処理時間の差が大きすぎます: {existing_time:.6f}s vs {nonexistent_time:.6f}s"
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ |
|--------------|------|---------|
| `mock_admin_client` | AsyncOpenSearch管理者クライアントモック | function |
| `mock_user_info` | ユーザー情報モック | function |
| `mock_role_permissions` | ロール権限情報モック | function |
| `mock_admin_role_permissions` | 管理者ロール権限モック | function |

### 共通フィクスチャ定義

```python
# test/unit/core/conftest.py に追加
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_admin_client():
    """AsyncOpenSearch管理者クライアントモック"""
    client = MagicMock()
    client.transport = MagicMock()
    client.transport.perform_request = AsyncMock()
    return client


@pytest.fixture
def mock_user_info():
    """標準ユーザー情報モック"""
    return {
        "backend_roles": ["user_role"],
        "opensearch_security_roles": ["reader"],
        "attributes": {"department": "engineering"}
    }


@pytest.fixture
def mock_role_permissions():
    """標準ロール権限モック"""
    return {
        "index_permissions": [
            {
                "index_patterns": ["logs-*", "metrics-*"],
                "allowed_actions": ["read", "write"]
            }
        ],
        "cluster_permissions": ["cluster:monitor/*"]
    }


@pytest.fixture
def mock_admin_role_permissions():
    """管理者ロール権限モック"""
    return {
        "index_permissions": [
            {
                "index_patterns": ["*"],
                "allowed_actions": ["*"]
            }
        ],
        "cluster_permissions": ["*"]
    }
```

---

## 6. テスト実行例

```bash
# permission_checker関連テストのみ実行
pytest test/unit/core/test_permission_checker.py -v

# 特定のテストクラスのみ実行
pytest test/unit/core/test_permission_checker.py::TestGetUserInfo -v
pytest test/unit/core/test_permission_checker.py::TestCheckIndexAccessPermission -v
pytest test/unit/core/test_permission_checker.py::TestExpandGenericAction -v
pytest test/unit/core/test_permission_checker.py::TestPermissionSecurity -v

# カバレッジ付きで実行
pytest test/unit/core/test_permission_checker.py --cov=app.core.permission_checker --cov-report=term-missing -v

# セキュリティマーカーで実行（pytest.iniまたはpyproject.tomlにマーカー登録が必要）
# [tool.pytest.ini_options]
# markers = ["security: セキュリティ関連テスト"]
pytest test/unit/core/test_permission_checker.py -m "security" -v

# 非同期テストのみ実行
pytest test/unit/core/test_permission_checker.py -k "async" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 15+ | PERM-INIT, PERM-001 〜 PERM-014 |
| 異常系 | 10 | PERM-E01 〜 PERM-E10 |
| セキュリティ | 6 | PERM-SEC-01 〜 PERM-SEC-06 |
| **合計** | **31+** | - |

> **注記**: 一部のテストはサブID（PERM-006-B〜H, PERM-E08-B, PERM-E10-B 等）を持ちます。
> これらは同一機能の追加バリエーションテストです。

### 注意事項

- 非同期メソッドのテストは `@pytest.mark.asyncio` で実行（`_expand_generic_action` 等の同期メソッドは除く）
- OpenSearch Security APIのモックが必要
- 実際のOpenSearch環境での統合テストは別途必要
- ワイルドカードパターン（`*`）を持つロールのセキュリティリスクに注意（PERM-SEC-02 参照）

### ロール順序に関する注意

`get_user_roles()` は `list(set(...))` を返すため、**ロールの順序は不定**です。
`side_effect` リストで呼び出し順を固定するテストは不安定になる可能性があります。

本仕様書では、複数ロールを扱うテストにおいて**パスベースモック**を採用しています：

```python
# 呼び出しパスで分岐する堅牢なモック（ロール順序に依存しない）
async def path_based_side_effect(method, path, **kwargs):
    if "internalusers/test_user" in path:
        return {"test_user": user_info}
    elif "roles/role1" in path:
        return {"role1": role1_permissions}
    elif "roles/role2" in path:
        return {"role2": role2_permissions}
    return {}

mock_admin_client.transport.perform_request = AsyncMock(side_effect=path_based_side_effect)
```

この設計により、ロールのチェック順序に関わらずテストが安定して動作します。

---

## 8. 関連ドキュメント

- [core_tests_status.md](./core_tests_status.md) - Coreテスト仕様書状況管理
- [remaining_core_template.md](./remaining_core_template.md) - 残りのCoreテストテンプレート
- [clients_tests.md](./clients_tests.md) - OpenSearchクライアントテスト仕様書
- [plugins/auth_tests.md](../plugins/auth_tests.md) - 認証・認可テスト仕様書
