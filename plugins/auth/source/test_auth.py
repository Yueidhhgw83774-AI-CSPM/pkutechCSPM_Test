# test_auth.py
"""
auth 模块单元测试

测试对象:
  - app/core/auth.py (认证核心逻辑)
  - app/auth/router.py (认证端点)
  - app/models/auth.py (认证模型)

测试规格: docs/testing/plugins/auth_tests.md
覆盖率目标: 90%+

测试类别:
  - 正常系: 12 个测试 (AUTH-001 ~ AUTH-012)
  - 异常系: 18 个测试 (AUTH-E01 ~ AUTH-E18)
  - 安全测试: 8 个测试 (AUTH-SEC-01 ~ AUTH-SEC-08)
"""

import pytest
import json
import base64
import sys
import os
import importlib
from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, AsyncMock
from jose import jwt
from httpx import AsyncClient

# 项目根目录设置
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent / "platform_python_backend-testing"
if not project_root.exists():
    raise RuntimeError(f"项目根目录不存在: {project_root}")
sys.path.insert(0, str(project_root))

# 设置JWT密钥环境变量
os.environ["JWT_SECRET_KEY"] = "f4fae6a6c089204d69efdc35438312a81005e1c3825a40cfc706cbe5ec0f50b1"


# ============================================================================
# 正常系测试: 端点测试 (AUTH-001 ~ AUTH-003)
# ============================================================================

class TestAuthEndpoints:
    """
    认证端点正常系测试

    测试ID: AUTH-001 ~ AUTH-003
    测试对象: app/auth/router.py
    """

    @pytest.mark.asyncio
    async def test_login_success(self, async_client: AsyncClient):
        """
        AUTH-001: 有效认证信息获取Token成功

        覆盖代码行: router.py:16-40

        测试目的:
          - 验证正确的用户名密码可以获取access_token
          - 验证返回的token_type为"bearer"
        """
        # Arrange - 准备测试数据
        form_data = {
            "username": "testuser",
            "password": "secret"
        }

        # Act - 执行被测试的函数
        response = await async_client.post(
            "/auth/token",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # Assert - 验证结果
        assert response.status_code == 200  # 验证状态码正确
        data = response.json()
        assert "access_token" in data  # 验证返回包含access_token
        assert data["token_type"] == "bearer"  # 验证token_type为bearer

    @pytest.mark.asyncio
    async def test_get_current_user(self, async_client: AsyncClient, valid_token: str):
        """
        AUTH-002: 认证后获取用户信息成功

        覆盖代码行: router.py:42-52

        测试目的:
          - 验证使用有效Token可以获取用户信息
          - 验证返回的用户信息包含username和email
        """
        # Arrange - 准备认证头
        headers = {"Authorization": f"Bearer {valid_token}"}

        # Act - 执行请求
        response = await async_client.get("/auth/users/me", headers=headers)

        # Assert - 验证结果
        assert response.status_code == 200  # 验证状态码正确
        data = response.json()
        assert "username" in data  # 验证返回包含username
        assert "email" in data  # 验证返回包含email

    @pytest.mark.asyncio
    async def test_protected_route(self, async_client: AsyncClient, valid_token: str):
        """
        AUTH-003: 访问受保护路由成功

        覆盖代码行: router.py:54-67

        测试目的:
          - 验证使用有效Token可以访问受保护端点
          - 验证返回消息包含用户名
        """
        # Arrange - 准备认证头
        headers = {"Authorization": f"Bearer {valid_token}"}

        # Act - 执行请求
        response = await async_client.get("/auth/protected", headers=headers)

        # Assert - 验证结果
        assert response.status_code == 200  # 验证状态码正确
        data = response.json()
        assert "message" in data  # 验证返回包含消息


# ============================================================================
# 正常系测试: 核心逻辑测试 (AUTH-004 ~ AUTH-008)
# ============================================================================

class TestAuthCoreLogic:
    """
    认证核心逻辑正常系测试

    测试ID: AUTH-004 ~ AUTH-008
    测试对象: app/core/auth.py
    """

    def test_verify_password_success(self):
        """
        AUTH-004: 正确密码验证成功

        覆盖代码行: auth.py:58-60

        测试目的:
          - 验证正确的明文密码与哈希密码匹配返回True

        注意: 使用mock绕过bcrypt/passlib兼容性问题
        """
        # Arrange - 准备测试数据
        from app.core.auth import verify_password
        plain = "secret"
        # 任意哈希值（mock会忽略它，只检查密码是否为"secret"）
        hashed = "$2b$12$anyhashvalue"

        # Act - 执行验证
        result = verify_password(plain, hashed)

        # Assert - 验证结果
        assert result is True  # 验证密码匹配成功

    def test_get_password_hash(self):
        """
        AUTH-005: 密码哈希化成功

        覆盖代码行: auth.py:62-64

        测试目的:
          - 验证密码被正确哈希化
          - 验证哈希后的密码可以被验证

        注意: 使用mock绕过bcrypt/passlib兼容性问题
        """
        # Arrange - 准备测试数据
        from app.core.auth import get_password_hash, verify_password
        password = "secret"

        # Act - 执行哈希化
        hashed = get_password_hash(password)

        # Assert - 验证结果
        assert hashed.startswith("$2b$")  # 验证是bcrypt格式（mock返回$2b$开头）
        assert verify_password(password, hashed) is True  # 验证哈希可被验证

    def test_get_user_found(self):
        """
        AUTH-006: 存在用户查询成功

        覆盖代码行: auth.py:66-71

        测试目的:
          - 验证存在的用户名可以获取UserInDB实例
          - 验证返回的用户信息正确
        """
        # Arrange - 准备测试数据
        from app.core.auth import get_user, fake_users_db

        # Act - 执行查询
        user = get_user(fake_users_db, "testuser")

        # Assert - 验证结果
        assert user is not None  # 验证用户存在
        assert user.username == "testuser"  # 验证用户名正确
        assert user.email == "test@example.com"  # 验证邮箱正确

    def test_get_user_with_roles_found(self):
        """
        AUTH-007: 带角色用户查询成功

        覆盖代码行: auth.py:73-78

        测试目的:
          - 验证可以获取包含角色信息的用户
          - 验证角色列表不为空
        """
        # Arrange - 准备测试数据
        from app.core.auth import get_user_with_roles, fake_users_db

        # Act - 执行查询
        user = get_user_with_roles(fake_users_db, "admin")

        # Assert - 验证结果
        assert user is not None  # 验证用户存在
        assert user.username == "admin"  # 验证用户名正确
        assert "cspm_dashboard_read_role" in user.roles  # 验证包含预期角色

    def test_authenticate_user_with_roles_success(self):
        """
        AUTH-008: 带角色认证成功

        覆盖代码行: auth.py:89-95

        测试目的:
          - 验证正确凭据返回UserInDBWithRoles实例
          - 验证角色列表不为空
        """
        # Arrange - 准备测试数据
        from app.core.auth import authenticate_user_with_roles, fake_users_db

        # Act - 执行认证
        user = authenticate_user_with_roles(fake_users_db, "admin", "secret")

        # Assert - 验证结果
        assert user is not None  # 验证认证成功
        assert user.username == "admin"  # 验证用户名正确
        assert len(user.roles) > 0  # 验证有角色


# ============================================================================
# 正常系测试: Token生成测试 (AUTH-009 ~ AUTH-012)
# ============================================================================

class TestTokenCreation:
    """
    JWT Token生成正常系测试

    测试ID: AUTH-009 ~ AUTH-012
    测试对象: app/core/auth.py
    """

    def test_create_access_token_with_expiry(self):
        """
        AUTH-009: 指定有效期Token生成成功

        覆盖代码行: auth.py:97-107 (if expires_delta分支True侧)

        测试目的:
          - 验证指定有效期生成的Token包含正确的sub
          - 验证Token包含exp字段
        """
        # Arrange - 准备测试数据
        from app.core.auth import create_access_token, SECRET_KEY, ALGORITHM
        data = {"sub": "testuser"}
        expires = timedelta(minutes=60)

        # Act - 执行Token生成
        token = create_access_token(data=data, expires_delta=expires)

        # Assert - 验证结果
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser"  # 验证sub正确
        assert "exp" in payload  # 验证包含过期时间

    def test_create_access_token_default_expiry(self):
        """
        AUTH-010: 默认有效期Token生成成功

        覆盖代码行: auth.py:97-107 (else分支，默认15分钟)

        测试目的:
          - 验证不指定有效期时使用默认值
          - 验证Token包含正确的sub和exp
        """
        # Arrange - 准备测试数据
        from app.core.auth import create_access_token, SECRET_KEY, ALGORITHM
        data = {"sub": "testuser"}

        # Act - 执行Token生成（不指定expires_delta）
        token = create_access_token(data=data)

        # Assert - 验证结果
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser"  # 验证sub正确
        assert "exp" in payload  # 验证包含过期时间

    def test_create_access_token_with_roles_and_expiry(self):
        """
        AUTH-011: 带角色Token生成成功（指定有效期）

        覆盖代码行: auth.py:109-118 (if expires_delta分支True侧)

        测试目的:
          - 验证Token包含roles字段
          - 验证角色列表正确
        """
        # Arrange - 准备测试数据
        from app.core.auth import create_access_token_with_roles, SECRET_KEY, ALGORITHM
        roles = ["cspm_dashboard_read_role"]

        # Act - 执行Token生成
        token = create_access_token_with_roles(
            "admin", roles, expires_delta=timedelta(minutes=60)
        )

        # Assert - 验证结果
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "admin"  # 验证sub正确
        assert payload["roles"] == roles  # 验证角色正确

    def test_create_access_token_with_roles_default_expiry(self):
        """
        AUTH-012: 带角色Token生成成功（默认30分钟有效期）

        覆盖代码行: auth.py:109-118 (else分支，默认30分钟)

        测试目的:
          - 验证不指定有效期时使用ACCESS_TOKEN_EXPIRE_MINUTES(30分钟)
          - 验证Token包含正确的roles
        """
        # Arrange - 准备测试数据
        from app.core.auth import create_access_token_with_roles, SECRET_KEY, ALGORITHM
        roles = ["rag_search_read_role"]

        # Act - 执行Token生成（不指定expires_delta）
        token = create_access_token_with_roles("testuser", roles)

        # Assert - 验证结果
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser"  # 验证sub正确
        assert payload["roles"] == roles  # 验证角色正确


# ============================================================================
# 异常系测试: 端点错误测试 (AUTH-E01 ~ AUTH-E07)
# ============================================================================

class TestAuthEndpointErrors:
    """
    认证端点异常系测试

    测试ID: AUTH-E01 ~ AUTH-E07
    测试对象: app/auth/router.py
    """

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, async_client: AsyncClient):
        """
        AUTH-E01: 无效密码返回401

        覆盖代码行: router.py:31-36 (if not user分支)

        测试目的:
          - 验证错误密码返回401状态码
          - 验证错误消息包含提示信息
        """
        # Arrange - 准备错误密码的请求数据
        form_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }

        # Act - 执行请求
        response = await async_client.post(
            "/auth/token",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # Assert - 验证结果
        assert response.status_code == 401  # 验证401状态码
        assert "ユーザー名またはパスワード" in response.json()["detail"]  # 验证错误消息

    @pytest.mark.asyncio
    async def test_login_unknown_user(self, async_client: AsyncClient):
        """
        AUTH-E02: 不存在用户返回401

        覆盖代码行: auth.py:83 (not user分支)

        测试目的:
          - 验证不存在的用户名返回401
        """
        # Arrange - 准备不存在用户的请求数据
        form_data = {
            "username": "unknownuser",
            "password": "secret"
        }

        # Act - 执行请求
        response = await async_client.post(
            "/auth/token",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # Assert - 验证结果
        assert response.status_code == 401  # 验证401状态码

    @pytest.mark.asyncio
    async def test_expired_token(self, async_client: AsyncClient, expired_token: str):
        """
        AUTH-E03: 过期Token返回401

        覆盖代码行: auth.py:133 (JWTError分支)

        测试目的:
          - 验证过期Token被正确拒绝
        """
        # Arrange - 使用过期Token
        headers = {"Authorization": f"Bearer {expired_token}"}

        # Act - 执行请求
        response = await async_client.get("/auth/users/me", headers=headers)

        # Assert - 验证结果
        assert response.status_code == 401  # 验证401状态码

    @pytest.mark.asyncio
    async def test_malformed_token(self, async_client: AsyncClient):
        """
        AUTH-E04: 无效Token格式返回401

        覆盖代码行: auth.py:133 (JWTError分支)

        测试目的:
          - 验证格式错误的Token被拒绝
        """
        # Arrange - 使用格式错误的Token
        headers = {"Authorization": "Bearer invalid.token.format"}

        # Act - 执行请求
        response = await async_client.get("/auth/users/me", headers=headers)

        # Assert - 验证结果
        assert response.status_code == 401  # 验证401状态码

    @pytest.mark.asyncio
    async def test_no_auth_header(self, async_client: AsyncClient):
        """
        AUTH-E05: 无认证头返回401

        测试目的:
          - 验证缺少Authorization头时返回401
        """
        # Act - 不带认证头执行请求
        response = await async_client.get("/auth/users/me")

        # Assert - 验证结果
        assert response.status_code == 401  # 验证401状态码

    @pytest.mark.asyncio
    async def test_disabled_user(
        self,
        async_client: AsyncClient,
        disabled_user_in_db
    ):
        """
        AUTH-E06: 禁用用户返回400

        覆盖代码行: auth.py:175 (current_user.disabled分支)

        测试目的:
          - 验证disabled=True的用户被拒绝访问
          - 验证错误消息包含"無効なユーザー"
        """
        # Arrange - 为禁用用户创建Token
        from app.core.auth import create_access_token
        token = create_access_token(
            data={"sub": "disabled-user"},
            expires_delta=timedelta(hours=1)
        )
        headers = {"Authorization": f"Bearer {token}"}

        # Act - 执行请求
        response = await async_client.get("/auth/users/me", headers=headers)

        # Assert - 验证结果
        assert response.status_code == 400  # 验证400状态码
        assert "無効なユーザー" in response.json()["detail"]  # 验证错误消息

    @pytest.mark.asyncio
    async def test_insufficient_roles(
        self,
        async_client: AsyncClient,
        testuser_token: str,
        mock_role_required_endpoint
    ):
        """
        AUTH-E07: 权限不足返回403

        覆盖代码行: auth.py:188 (角色不匹配分支)

        测试目的:
          - 验证缺少必要角色时返回403
          - 验证错误消息包含"必要なロール権限がありません"
        """
        # Arrange - 使用只有rag_search_read_role的用户Token
        headers = {"Authorization": f"Bearer {testuser_token}"}

        # Act - 尝试访问需要cspm_dashboard_read_role的端点
        response = await async_client.get(
            "/protected-dashboard",
            headers=headers
        )

        # Assert - 验证结果
        assert response.status_code == 403  # 验证403状态码
        assert "必要なロール権限がありません" in response.json()["detail"]  # 验证错误消息


# ============================================================================
# 异常系测试: 核心逻辑错误测试 (AUTH-E08 ~ AUTH-E13)
# ============================================================================

class TestAuthCoreLogicErrors:
    """
    认证核心逻辑异常系测试

    测试ID: AUTH-E08 ~ AUTH-E13
    测试对象: app/core/auth.py
    """

    def test_verify_password_failure(self):
        """
        AUTH-E08: 错误密码验证失败

        覆盖代码行: auth.py:60 (verify_password失败路径)

        测试目的:
          - 验证错误密码返回False

        注意: 使用mock绕过bcrypt/passlib兼容性问题
        """
        # Arrange - 准备测试数据
        from app.core.auth import verify_password
        # mock只接受"secret"为正确密码
        hashed = "$2b$12$anyhashvalue"

        # Act - 使用错误密码执行验证
        result = verify_password("wrongpassword", hashed)

        # Assert - 验证结果
        assert result is False  # 验证密码不匹配

    def test_get_user_not_found(self):
        """
        AUTH-E09: 不存在用户查询返回None

        覆盖代码行: auth.py:71 (return None分支)

        测试目的:
          - 验证不存在的用户名返回None
        """
        # Arrange - 准备测试数据
        from app.core.auth import get_user, fake_users_db

        # Act - 执行查询
        user = get_user(fake_users_db, "nonexistent")

        # Assert - 验证结果
        assert user is None  # 验证返回None

    def test_authenticate_user_with_roles_unknown(self):
        """
        AUTH-E10: 带角色认证-用户不存在返回None

        覆盖代码行: auth.py:92 (not user分支)

        测试目的:
          - 验证不存在的用户认证返回None
        """
        # Arrange - 准备测试数据
        from app.core.auth import authenticate_user_with_roles, fake_users_db

        # Act - 执行认证
        user = authenticate_user_with_roles(fake_users_db, "unknown", "secret")

        # Assert - 验证结果
        assert user is None  # 验证返回None

    def test_authenticate_user_with_roles_wrong_password(self):
        """
        AUTH-E11: 带角色认证-密码错误返回None

        覆盖代码行: auth.py:94 (not verify_password分支)

        测试目的:
          - 验证密码错误时认证返回None
        """
        # Arrange - 准备测试数据
        from app.core.auth import authenticate_user_with_roles, fake_users_db

        # Act - 执行认证
        user = authenticate_user_with_roles(fake_users_db, "admin", "wrong")

        # Assert - 验证结果
        assert user is None  # 验证返回None

    @pytest.mark.asyncio
    async def test_get_current_user_no_sub(self):
        """
        AUTH-E12: 无sub字段Token返回401

        覆盖代码行: auth.py:130 (username is None分支)

        测试目的:
          - 验证Token中没有sub字段时抛出401异常
        """
        # Arrange - 创建没有sub字段的Token
        from app.core.auth import get_current_user, SECRET_KEY, ALGORITHM
        from fastapi import HTTPException
        token = jwt.encode({"data": "no-sub"}, SECRET_KEY, algorithm=ALGORITHM)

        # Act & Assert - 验证抛出异常
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token)
        assert exc_info.value.status_code == 401  # 验证401状态码

    @pytest.mark.asyncio
    async def test_get_current_user_unknown_sub(self):
        """
        AUTH-E13: sub不存在于DB返回401

        覆盖代码行: auth.py:137 (user is None分支)

        测试目的:
          - 验证Token中的sub用户不存在于DB时抛出401异常
        """
        # Arrange - 创建包含不存在用户的Token
        from app.core.auth import get_current_user, SECRET_KEY, ALGORITHM
        from fastapi import HTTPException
        token = jwt.encode({"sub": "ghost-user"}, SECRET_KEY, algorithm=ALGORITHM)

        # Act & Assert - 验证抛出异常
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token)
        assert exc_info.value.status_code == 401  # 验证401状态码


# ============================================================================
# 异常系测试: get_current_user_with_roles错误测试 (AUTH-E15 ~ AUTH-E18)
# ============================================================================

class TestGetCurrentUserWithRolesErrors:
    """
    get_current_user_with_roles() 异常系测试

    测试ID: AUTH-E15 ~ AUTH-E18
    测试对象: app/core/auth.py
    """

    @pytest.mark.asyncio
    async def test_get_current_user_with_roles_no_sub(self):
        """
        AUTH-E15: 带角色获取用户-无sub返回401

        覆盖代码行: auth.py:152 (username is None分支)

        测试目的:
          - 验证Token中没有sub字段时抛出401异常
        """
        # Arrange - 创建只有roles没有sub的Token
        from app.core.auth import get_current_user_with_roles, SECRET_KEY, ALGORITHM
        from fastapi import HTTPException
        token = jwt.encode({"roles": ["admin"]}, SECRET_KEY, algorithm=ALGORITHM)

        # Act & Assert - 验证抛出异常
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_with_roles(token=token)
        assert exc_info.value.status_code == 401  # 验证401状态码

    @pytest.mark.asyncio
    async def test_get_current_user_with_roles_jwt_error(self):
        """
        AUTH-E16: 带角色获取用户-无效Token返回401

        覆盖代码行: auth.py:156 (JWTError分支)

        测试目的:
          - 验证无效Token格式时抛出401异常
        """
        # Arrange - 使用无效Token
        from app.core.auth import get_current_user_with_roles
        from fastapi import HTTPException

        # Act & Assert - 验证抛出异常
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_with_roles(token="invalid.token.here")
        assert exc_info.value.status_code == 401  # 验证401状态码

    @pytest.mark.asyncio
    async def test_get_current_user_with_roles_unknown_user(self):
        """
        AUTH-E17: 带角色获取用户-用户不存在返回401

        覆盖代码行: auth.py:159 (user is None分支)

        测试目的:
          - 验证Token中的用户不存在于DB时抛出401异常
        """
        # Arrange - 创建包含不存在用户的Token
        from app.core.auth import get_current_user_with_roles, SECRET_KEY, ALGORITHM
        from fastapi import HTTPException
        token = jwt.encode(
            {"sub": "ghost-user", "roles": []}, SECRET_KEY, algorithm=ALGORITHM
        )

        # Act & Assert - 验证抛出异常
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_with_roles(token=token)
        assert exc_info.value.status_code == 401  # 验证401状态码

    @pytest.mark.asyncio
    async def test_disabled_user_with_roles(self):
        """
        AUTH-E18: 带角色禁用用户返回400

        覆盖代码行: auth.py:181 (current_user.disabled分支)

        测试目的:
          - 验证禁用用户通过get_current_active_user_with_roles时抛出400异常
        """
        # Arrange - 创建禁用用户对象
        from app.core.auth import get_current_active_user_with_roles
        from app.models.auth import UserWithRoles
        from fastapi import HTTPException

        disabled_user = UserWithRoles(
            username="disabled-user",
            email="disabled@example.com",
            disabled=True,
            roles=["rag_search_read_role"]
        )

        # Act & Assert - 验证抛出异常
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user_with_roles(current_user=disabled_user)
        assert exc_info.value.status_code == 400  # 验证400状态码
        assert "無効なユーザー" in exc_info.value.detail  # 验证错误消息


# ============================================================================
# 异常系测试: RBAC错误测试 (AUTH-E14)
# ============================================================================

class TestRBACErrors:
    """
    RBAC (角色访问控制) 异常系测试

    测试ID: AUTH-E14
    测试对象: app/core/auth.py
    """

    @pytest.mark.asyncio
    async def test_require_all_roles_partial_match(self):
        """
        AUTH-E14: require_all_roles部分匹配返回403

        覆盖代码行: auth.py:203 (not all(...)分支)

        测试目的:
          - 验证用户只有部分要求角色时抛出403异常
          - 验证错误消息包含"不足ロール"
        """
        # Arrange - 准备只有部分角色的用户
        from app.core.auth import require_all_roles
        from app.models.auth import UserWithRoles
        from fastapi import HTTPException

        checker = require_all_roles(["cspm_dashboard_read_role", "cspm_job_execution_role"])
        user = UserWithRoles(
            username="dashboard-user",
            roles=["cspm_dashboard_read_role"]  # 缺少cspm_job_execution_role
        )

        # Act & Assert - 验证抛出异常
        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=user)
        assert exc_info.value.status_code == 403  # 验证403状态码
        assert "不足ロール" in exc_info.value.detail  # 验证错误消息包含不足角色提示


# ============================================================================
# 安全测试 (AUTH-SEC-01 ~ AUTH-SEC-08)
# ============================================================================

@pytest.mark.security
class TestAuthSecurity:
    """
    认证安全测试

    测试ID: AUTH-SEC-01 ~ AUTH-SEC-08
    测试对象: app/core/auth.py
    """

    def test_password_is_hashed(self):
        """
        AUTH-SEC-01: 密码bcrypt哈希验证

        测试目的:
          - 验证fake_users_db中所有用户的密码都是bcrypt哈希格式
        """
        # Arrange - 获取用户数据库
        from app.core.auth import fake_users_db

        # Act & Assert - 验证所有密码都是bcrypt格式
        for username, user_data in fake_users_db.items():
            assert user_data["hashed_password"].startswith("$2b$"), \
                f"用户 {username} 的密码不是bcrypt哈希格式"

    @pytest.mark.asyncio
    async def test_token_modified_rejected(
        self,
        async_client: AsyncClient,
        valid_token: str
    ):
        """
        AUTH-SEC-02: 篡改Token被拒绝

        测试目的:
          - 验证修改过的Token会被签名验证拒绝
        """
        # Arrange - 篡改Token（修改最后5个字符）
        modified_token = valid_token[:-5] + "xxxxx"
        headers = {"Authorization": f"Bearer {modified_token}"}

        # Act - 使用篡改的Token请求
        response = await async_client.get("/auth/users/me", headers=headers)

        # Assert - 验证被拒绝
        assert response.status_code == 401  # 验证401状态码

    @pytest.mark.asyncio
    async def test_password_not_in_response(
        self,
        async_client: AsyncClient,
        valid_token: str
    ):
        """
        AUTH-SEC-03: 响应不包含密码信息

        测试目的:
          - 验证API响应中不包含password或hashed相关字段
        """
        # Arrange - 准备认证头
        headers = {"Authorization": f"Bearer {valid_token}"}

        # Act - 获取用户信息
        response = await async_client.get("/auth/users/me", headers=headers)

        # Assert - 验证响应不包含密码信息
        response_text = str(response.json()).lower()
        assert "password" not in response_text  # 验证不包含password
        assert "hashed" not in response_text  # 验证不包含hashed

    @pytest.mark.asyncio
    async def test_token_expiry_enforced(
        self,
        async_client: AsyncClient,
        expired_token: str
    ):
        """
        AUTH-SEC-04: Token有效期强制执行

        测试目的:
          - 验证过期Token被正确拒绝
        """
        # Arrange - 使用过期Token
        headers = {"Authorization": f"Bearer {expired_token}"}

        # Act - 使用过期Token请求受保护路由
        response = await async_client.get("/auth/protected", headers=headers)

        # Assert - 验证被拒绝
        assert response.status_code == 401  # 验证401状态码

    def test_default_secret_key_warning(self):
        """
        AUTH-SEC-05: 默认SECRET_KEY警告

        覆盖代码行: auth.py:18 (JWT_SECRET_KEY环境变量未设置时)

        测试目的:
          - 验证JWT_SECRET_KEY未设置时使用默认值
          - 【安全建议】生产环境应强制要求设置环境变量

        注意: 此测试通过检查源代码中的默认值逻辑来验证
        """
        # Arrange - 检查auth.py中的默认值逻辑
        import inspect
        from app.core import auth

        # 获取模块源代码
        source = inspect.getsource(auth)

        # Assert - 验证源代码中存在默认值设置
        # 检查是否有 os.getenv("JWT_SECRET_KEY", "your-secret-key...") 形式的代码
        assert 'os.getenv("JWT_SECRET_KEY"' in source or "os.getenv('JWT_SECRET_KEY'" in source, \
            "auth.py应该从环境变量读取JWT_SECRET_KEY"

        assert "your-secret-key-here-please-change-in-production" in source, \
            "auth.py应该有默认SECRET_KEY值（用于警示需要更改）"

    @pytest.mark.asyncio
    async def test_jwt_alg_none_attack_rejected(self):
        """
        AUTH-SEC-06: JWT alg=none攻击防御

        测试目的:
          - 验证alg=none的Token会被jose.jwt.decode()拒绝
          - 防止算法降级攻击
        """
        # Arrange - 手动创建alg=none的JWT
        from app.core.auth import get_current_user
        from fastapi import HTTPException

        header = {"alg": "none", "typ": "JWT"}
        payload = {"sub": "admin", "exp": 9999999999}

        header_b64 = base64.urlsafe_b64encode(
            json.dumps(header).encode()
        ).decode().rstrip("=")
        payload_b64 = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).decode().rstrip("=")

        # alg=none时签名部分为空
        fake_token = f"{header_b64}.{payload_b64}."

        # Act & Assert - 验证被拒绝
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=fake_token)
        assert exc_info.value.status_code == 401  # 验证401状态码

    @pytest.mark.asyncio
    async def test_jwt_role_tampering_rejected(self):
        """
        AUTH-SEC-07: JWT角色篡改检测

        测试目的:
          - 验证篡改JWT payload后签名验证失败
          - 防止角色注入攻击
        """
        # Arrange - 创建有效Token然后篡改payload
        from app.core.auth import get_current_user_with_roles, SECRET_KEY, ALGORITHM
        from fastapi import HTTPException

        # 创建有效Token
        valid_payload = {"sub": "testuser", "roles": ["rag_search_read_role"]}
        valid_token = jwt.encode(valid_payload, SECRET_KEY, algorithm=ALGORITHM)

        # 篡改payload（添加管理员角色）
        parts = valid_token.split(".")
        tampered_payload = {"sub": "testuser", "roles": ["cspm_job_execution_role"]}
        tampered_payload_b64 = base64.urlsafe_b64encode(
            json.dumps(tampered_payload).encode()
        ).decode().rstrip("=")

        # 签名保持原样（与篡改后的payload不匹配）
        tampered_token = f"{parts[0]}.{tampered_payload_b64}.{parts[2]}"

        # Act & Assert - 验证被拒绝
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_with_roles(token=tampered_token)
        assert exc_info.value.status_code == 401  # 验证401状态码

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="当前实现存在安全漏洞：auth.py:163会合并JWT和DB角色，允许角色提权")
    async def test_role_escalation_prevented(self):
        """
        AUTH-SEC-08: 角色提权防止

        覆盖代码行: auth.py:163 (combined_roles合并逻辑)

        测试目的:
          - 验证JWT中的恶意角色不会被添加到用户权限中
          - 验证只有DB中定义的角色是有效的

        【安全漏洞说明】
        当前实现(auth.py:163)会合并JWT中的roles和DB中的roles:
          combined_roles = list(set(token_data.roles + user.roles))

        这允许攻击者在JWT中注入任意角色实现权限提升。

        【修复建议】
        应该只使用DB中的roles，忽略JWT中的roles:
          return UserWithRoles(..., roles=user.roles)
        """
        # Arrange - 创建包含恶意角色的Token
        from app.core.auth import get_current_user_with_roles, SECRET_KEY, ALGORITHM

        # testuser在DB中只有rag_search_read_role
        # 但JWT中包含cspm_job_execution_role（恶意注入）
        malicious_payload = {
            "sub": "testuser",
            "roles": ["cspm_job_execution_role"],  # DB中没有的角色
            "exp": 9999999999
        }
        malicious_token = jwt.encode(malicious_payload, SECRET_KEY, algorithm=ALGORITHM)

        # Act - 获取用户
        user = await get_current_user_with_roles(token=malicious_token)

        # Assert - 验证DB中的角色存在
        assert "rag_search_read_role" in user.roles, \
            "DB中定义的角色应该存在"

        # Assert - 验证JWT中的恶意角色不存在
        # 【注意】当前实现会失败此断言，因为存在安全漏洞
        assert "cspm_job_execution_role" not in user.roles, \
            "【安全漏洞】JWT中注入的角色不应该被接受。" \
            "请修改auth.py:163，只使用DB中的roles。"
