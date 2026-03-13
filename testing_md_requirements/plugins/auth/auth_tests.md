# auth テストケース

## 1. 概要

認証プラグイン（`app/auth/router.py`）と認証コアロジック（`app/core/auth.py`）のテストケースを定義します。
JWT認証、パスワード検証、ロールベースアクセス制御（RBAC）を包括的に検証します。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `verify_password()` | bcryptハッシュとのパスワード照合 |
| `get_password_hash()` | パスワードのbcryptハッシュ化 |
| `get_user()` | ユーザー情報取得（UserInDB） |
| `get_user_with_roles()` | ロール付きユーザー情報取得（UserInDBWithRoles） |
| `authenticate_user()` | ユーザー認証（DB検索+パスワード照合） |
| `authenticate_user_with_roles()` | ロール付きユーザー認証 |
| `create_access_token()` | JWTアクセストークン生成 |
| `create_access_token_with_roles()` | ロール情報付きJWTトークン生成 |
| `get_current_user()` | JWTからユーザー取得（非同期） |
| `get_current_user_with_roles()` | JWTからロール付きユーザー取得（非同期） |
| `get_current_active_user()` | アクティブユーザー検証（非同期） |
| `get_current_active_user_with_roles()` | ロール付きアクティブユーザー検証（非同期） |
| `require_roles()` | 指定ロールのいずれかを要求する依存性関数 |
| `require_all_roles()` | 指定ロール全てを要求する依存性関数 |
| `login_for_access_token()` | POST /auth/token エンドポイント |
| `read_users_me()` | GET /auth/users/me エンドポイント |
| `protected_route()` | GET /auth/protected エンドポイント |

### 1.2 カバレッジ目標: 90%

> **注記**: セキュリティ重要度が高いため、高いカバレッジ目標を設定。
> `fake_users_db` はテスト用のインメモリDBであり、本番環境では実DBに置き換え予定。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象（ルーター） | `app/auth/router.py` |
| テスト対象（コアロジック） | `app/core/auth.py` |
| テスト対象（モデル） | `app/models/auth.py` |
| テストコード | `test/unit/auth/test_auth.py` |

### 1.4 補足情報

**グローバル変数:**

| 変数 | 型 | 説明 |
|------|-----|------|
| `pwd_context` | `CryptContext` | bcryptハッシュコンテキスト |
| `oauth2_scheme` | `OAuth2PasswordBearer` | OAuth2トークン取得スキーム |
| `SECRET_KEY` | `str` | JWT署名鍵（環境変数 `JWT_SECRET_KEY` またはデフォルト） |
| `ALGORITHM` | `str` | JWT署名アルゴリズム（固定: `HS256`） |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `int` | トークン有効期限（固定: 30分） |
| `fake_users_db` | `dict` | テスト用ユーザーDB（4ユーザー） |

**主要分岐:**

| 関数 | 行番号 | 分岐条件 |
|------|--------|---------|
| `authenticate_user()` | L83 | `not user` → None返却 |
| `authenticate_user()` | L85 | `not verify_password(...)` → None返却 |
| `create_access_token()` | L101-104 | `expires_delta` 有無で有効期限設定 |
| `get_current_user()` | L130 | `username is None` → 例外 |
| `get_current_user()` | L133 | `JWTError` → 例外 |
| `get_current_user()` | L137 | `user is None` → 例外 |
| `get_current_user_with_roles()` | L150-152 | `username is None` → 例外 |
| `get_current_user_with_roles()` | L155 | `JWTError` → 例外 |
| `get_current_user_with_roles()` | L158-159 | `user is None` → 例外 |
| `get_current_active_user()` | L175 | `current_user.disabled` → 400 |
| `get_current_active_user_with_roles()` | L181 | `current_user.disabled` → 400 |
| `require_roles()` | L188 | ロール不一致 → 403 |
| `require_all_roles()` | L203 | 全ロール不一致 → 403 |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| AUTH-001 | 有効な認証情報でトークン取得 | valid username/password | access_token + token_type="bearer" |
| AUTH-002 | 認証済みでユーザー情報取得 | valid access_token | User情報（username, email） |
| AUTH-003 | 保護されたルートにアクセス | valid access_token | 成功メッセージ |
| AUTH-004 | パスワード照合成功 | plain_password, hashed_password | True |
| AUTH-005 | パスワードハッシュ化 | plain_password | bcryptハッシュ文字列 |
| AUTH-006 | ユーザー取得成功 | 存在するusername | UserInDBインスタンス |
| AUTH-007 | ロール付きユーザー取得成功 | 存在するusername | UserInDBWithRolesインスタンス |
| AUTH-008 | ロール付き認証成功 | valid username/password | UserInDBWithRolesインスタンス |
| AUTH-009 | トークン生成（有効期限指定あり） | data + expires_delta | JWTトークン文字列 |
| AUTH-010 | トークン生成（有効期限指定なし） | data only | JWTトークン文字列（デフォルト15分、auth.py:104） |
| AUTH-011 | ロール付きトークン生成 | username + roles | ロール含むJWTトークン |
| AUTH-012 | ロール付きトークン生成（有効期限なし） | username + roles | デフォルト30分期限のJWT |

### 2.1 エンドポイントテスト

```python
# test/unit/auth/test_auth.py
import pytest
from httpx import AsyncClient


class TestAuthEndpoints:
    """認証エンドポイントのテスト"""

    @pytest.mark.asyncio
    async def test_login_success(self, async_client: AsyncClient):
        """AUTH-001: 有効な認証情報でトークン取得成功"""
        # Arrange
        form_data = {
            "username": "testuser",
            "password": "secret"
        }

        # Act
        response = await async_client.post(
            "/auth/token",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_get_current_user(self, async_client: AsyncClient, valid_token: str):
        """AUTH-002: 認証済みでユーザー情報取得"""
        # Arrange
        headers = {"Authorization": f"Bearer {valid_token}"}

        # Act
        response = await async_client.get("/auth/users/me", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "email" in data

    @pytest.mark.asyncio
    async def test_protected_route(self, async_client: AsyncClient, valid_token: str):
        """AUTH-003: 保護されたルートにアクセス成功"""
        # Arrange
        headers = {"Authorization": f"Bearer {valid_token}"}

        # Act
        response = await async_client.get("/auth/protected", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
```

### 2.2 コアロジックテスト

```python
class TestAuthCoreLogic:
    """認証コアロジック（app/core/auth.py）のテスト"""

    def test_verify_password_success(self):
        """AUTH-004: 正しいパスワードの照合成功

        auth.py:58 verify_password() の正常パスをカバー。
        """
        # Arrange
        from app.core.auth import verify_password
        plain = "secret"
        hashed = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"

        # Act
        result = verify_password(plain, hashed)

        # Assert
        assert result is True

    def test_get_password_hash(self):
        """AUTH-005: パスワードのハッシュ化

        auth.py:62 get_password_hash() をカバー。
        """
        # Arrange
        from app.core.auth import get_password_hash, verify_password
        password = "test-password"

        # Act
        hashed = get_password_hash(password)

        # Assert
        assert hashed.startswith("$2b$")
        assert verify_password(password, hashed) is True

    def test_get_user_found(self):
        """AUTH-006: 存在するユーザーの取得成功

        auth.py:68 の if username in db 分岐をカバー。
        """
        # Arrange
        from app.core.auth import get_user, fake_users_db

        # Act
        user = get_user(fake_users_db, "testuser")

        # Assert
        assert user is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"

    def test_get_user_with_roles_found(self):
        """AUTH-007: ロール付きユーザーの取得成功

        auth.py:73 get_user_with_roles() をカバー。
        """
        # Arrange
        from app.core.auth import get_user_with_roles, fake_users_db

        # Act
        user = get_user_with_roles(fake_users_db, "admin")

        # Assert
        assert user is not None
        assert user.username == "admin"
        assert "cspm_dashboard_read_role" in user.roles

    def test_authenticate_user_with_roles_success(self):
        """AUTH-008: ロール付き認証成功

        auth.py:89 authenticate_user_with_roles() の正常パスをカバー。
        """
        # Arrange
        from app.core.auth import authenticate_user_with_roles, fake_users_db

        # Act
        user = authenticate_user_with_roles(fake_users_db, "admin", "secret")

        # Assert
        assert user is not None
        assert user.username == "admin"
        assert len(user.roles) > 0
```

### 2.3 トークン生成テスト

```python
from datetime import timedelta
from jose import jwt


class TestTokenCreation:
    """JWTトークン生成のテスト"""

    def test_create_access_token_with_expiry(self):
        """AUTH-009: 有効期限指定ありでトークン生成

        auth.py:101 の if expires_delta 分岐（True側）をカバー。
        """
        # Arrange
        from app.core.auth import create_access_token, SECRET_KEY, ALGORITHM
        data = {"sub": "testuser"}
        expires = timedelta(minutes=60)

        # Act
        token = create_access_token(data=data, expires_delta=expires)

        # Assert
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser"
        assert "exp" in payload

    def test_create_access_token_default_expiry(self):
        """AUTH-010: 有効期限指定なしでデフォルト15分のトークン生成

        auth.py:104 の else 分岐（expires_delta=None）をカバー。
        注: create_access_token() のデフォルトは15分（L104）。
        create_access_token_with_roles() のデフォルトは30分（L115, ACCESS_TOKEN_EXPIRE_MINUTES）。
        """
        # Arrange
        from app.core.auth import create_access_token, SECRET_KEY, ALGORITHM
        data = {"sub": "testuser"}

        # Act
        token = create_access_token(data=data)

        # Assert
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser"
        assert "exp" in payload

    def test_create_access_token_with_roles_and_expiry(self):
        """AUTH-011: ロール情報付きトークン生成（有効期限あり）

        auth.py:112 の if expires_delta 分岐（True側）をカバー。
        """
        # Arrange
        from app.core.auth import create_access_token_with_roles, SECRET_KEY, ALGORITHM
        roles = ["cspm_dashboard_read_role"]

        # Act
        token = create_access_token_with_roles(
            "admin", roles, expires_delta=timedelta(minutes=60)
        )

        # Assert
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "admin"
        assert payload["roles"] == roles

    def test_create_access_token_with_roles_default_expiry(self):
        """AUTH-012: ロール情報付きトークン生成（デフォルト30分期限）

        auth.py:115 の else 分岐（expires_delta=None）をカバー。
        """
        # Arrange
        from app.core.auth import create_access_token_with_roles, SECRET_KEY, ALGORITHM
        roles = ["rag_search_read_role"]

        # Act
        token = create_access_token_with_roles("testuser", roles)

        # Assert
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser"
        assert payload["roles"] == roles
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| AUTH-E01 | 無効なパスワードで401 | wrong password | 401 + エラーメッセージ |
| AUTH-E02 | 存在しないユーザーで401 | unknown user | 401 |
| AUTH-E03 | 期限切れトークンで401 | expired token | 401 |
| AUTH-E04 | 無効なトークン形式で401 | malformed token | 401 |
| AUTH-E05 | トークンなしで401 | no auth header | 401 |
| AUTH-E06 | 無効化ユーザーで400 | disabled user | 400 + "無効なユーザー" |
| AUTH-E07 | 権限不足で403 | token without required role | 403 + エラーメッセージ |
| AUTH-E08 | パスワード照合失敗 | wrong plain_password | False |
| AUTH-E09 | 存在しないユーザー検索 | unknown username | None |
| AUTH-E10 | ロール付き認証でユーザー不存在 | unknown username | None |
| AUTH-E11 | ロール付き認証でパスワード不一致 | wrong password | None |
| AUTH-E12 | subなしトークンで401 | token without sub | 401 |
| AUTH-E13 | DB上に存在しないsub値で401 | valid JWT, unknown sub | 401 |
| AUTH-E14 | require_all_roles でロール不足 | 一部ロールのみ | 403 |
| AUTH-E15 | get_current_user_with_roles でsubなし | token without sub | 401 |
| AUTH-E16 | get_current_user_with_roles で無効トークン | malformed token | 401 |
| AUTH-E17 | get_current_user_with_roles でDB不在ユーザー | valid JWT, unknown sub | 401 |
| AUTH-E18 | ロール付き無効化ユーザーで400 | disabled user with roles | 400 |

### 3.1 エンドポイント異常系

```python
class TestAuthEndpointErrors:
    """認証エンドポイントのエラーテスト"""

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, async_client: AsyncClient):
        """AUTH-E01: 無効なパスワードで401

        router.py:31-36 の if not user 分岐をカバー。
        """
        # Arrange
        form_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }

        # Act
        response = await async_client.post(
            "/auth/token",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # Assert
        assert response.status_code == 401
        assert "ユーザー名またはパスワード" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_unknown_user(self, async_client: AsyncClient):
        """AUTH-E02: 存在しないユーザーで401

        auth.py:83 の not user 分岐をカバー。
        """
        # Arrange
        form_data = {
            "username": "unknownuser",
            "password": "secret"
        }

        # Act
        response = await async_client.post(
            "/auth/token",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_expired_token(self, async_client: AsyncClient, expired_token: str):
        """AUTH-E03: 期限切れトークンで401

        auth.py:133 の JWTError 分岐をカバー。
        """
        # Arrange
        headers = {"Authorization": f"Bearer {expired_token}"}

        # Act
        response = await async_client.get("/auth/users/me", headers=headers)

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_malformed_token(self, async_client: AsyncClient):
        """AUTH-E04: 無効なトークン形式で401

        auth.py:133 の JWTError 分岐をカバー。
        """
        # Arrange
        headers = {"Authorization": "Bearer invalid.token.format"}

        # Act
        response = await async_client.get("/auth/users/me", headers=headers)

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_no_auth_header(self, async_client: AsyncClient):
        """AUTH-E05: 認証ヘッダーなしで401"""
        # Act
        response = await async_client.get("/auth/users/me")

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_disabled_user(
        self,
        async_client: AsyncClient,
        disabled_user_in_db
    ):
        """AUTH-E06: 無効化されたユーザーで400

        auth.py:175 の current_user.disabled 分岐をカバー。

        disabled_user_in_db フィクスチャにより、テスト中のみ
        無効化ユーザーがfake_users_dbに存在する。
        """
        # Arrange
        from app.core.auth import create_access_token
        from datetime import timedelta
        token = create_access_token(
            data={"sub": "disabled-user"},
            expires_delta=timedelta(hours=1)
        )
        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = await async_client.get("/auth/users/me", headers=headers)

        # Assert
        assert response.status_code == 400
        assert "無効なユーザー" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_insufficient_roles(
        self,
        async_client: AsyncClient,
        testuser_token: str,
        mock_role_required_endpoint
    ):
        """AUTH-E07: 権限不足で403

        auth.py:188 の ロール不一致分岐をカバー。
        """
        # Arrange
        headers = {"Authorization": f"Bearer {testuser_token}"}

        # Act
        response = await async_client.get(
            "/protected-dashboard",
            headers=headers
        )

        # Assert
        assert response.status_code == 403
        assert "必要なロール権限がありません" in response.json()["detail"]
```

### 3.2 コアロジック異常系

```python
class TestAuthCoreLogicErrors:
    """認証コアロジックのエラーテスト"""

    def test_verify_password_failure(self):
        """AUTH-E08: 不正なパスワードの照合失敗

        auth.py:60 verify_password() の失敗パスをカバー。
        """
        # Arrange
        from app.core.auth import verify_password
        hashed = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"

        # Act
        result = verify_password("wrongpassword", hashed)

        # Assert
        assert result is False

    def test_get_user_not_found(self):
        """AUTH-E09: 存在しないユーザーの検索でNone返却

        auth.py:71 の return None 分岐をカバー。
        """
        # Arrange
        from app.core.auth import get_user, fake_users_db

        # Act
        user = get_user(fake_users_db, "nonexistent")

        # Assert
        assert user is None

    def test_authenticate_user_with_roles_unknown(self):
        """AUTH-E10: ロール付き認証で存在しないユーザー

        auth.py:92 の not user 分岐をカバー。
        """
        # Arrange
        from app.core.auth import authenticate_user_with_roles, fake_users_db

        # Act
        user = authenticate_user_with_roles(fake_users_db, "unknown", "secret")

        # Assert
        assert user is None

    def test_authenticate_user_with_roles_wrong_password(self):
        """AUTH-E11: ロール付き認証でパスワード不一致

        auth.py:94 の not verify_password 分岐をカバー。
        """
        # Arrange
        from app.core.auth import authenticate_user_with_roles, fake_users_db

        # Act
        user = authenticate_user_with_roles(fake_users_db, "admin", "wrong")

        # Assert
        assert user is None

    @pytest.mark.asyncio
    async def test_get_current_user_no_sub(self):
        """AUTH-E12: subフィールドなしトークンで401

        auth.py:130 の username is None 分岐をカバー。
        """
        # Arrange
        from app.core.auth import get_current_user, SECRET_KEY, ALGORITHM
        from jose import jwt
        from fastapi import HTTPException
        token = jwt.encode({"data": "no-sub"}, SECRET_KEY, algorithm=ALGORITHM)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_unknown_sub(self):
        """AUTH-E13: DB上に存在しないsub値で401

        auth.py:137 の user is None 分岐をカバー。
        """
        # Arrange
        from app.core.auth import get_current_user, SECRET_KEY, ALGORITHM
        from jose import jwt
        from fastapi import HTTPException
        token = jwt.encode({"sub": "ghost-user"}, SECRET_KEY, algorithm=ALGORITHM)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token)
        assert exc_info.value.status_code == 401
```

### 3.3 get_current_user_with_roles 異常系

```python
class TestGetCurrentUserWithRolesErrors:
    """get_current_user_with_roles() の分岐テスト"""

    @pytest.mark.asyncio
    async def test_get_current_user_with_roles_no_sub(self):
        """AUTH-E15: get_current_user_with_roles でsubフィールドなし

        auth.py:152 の username is None 分岐をカバー。
        """
        # Arrange
        from app.core.auth import get_current_user_with_roles, SECRET_KEY, ALGORITHM
        from jose import jwt
        from fastapi import HTTPException
        token = jwt.encode({"roles": ["admin"]}, SECRET_KEY, algorithm=ALGORITHM)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_with_roles(token=token)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_with_roles_jwt_error(self):
        """AUTH-E16: get_current_user_with_roles で無効トークン

        auth.py:156 の JWTError 分岐をカバー。
        """
        # Arrange
        from app.core.auth import get_current_user_with_roles
        from fastapi import HTTPException

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_with_roles(token="invalid.token.here")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_with_roles_unknown_user(self):
        """AUTH-E17: get_current_user_with_roles でDB上に存在しないユーザー

        auth.py:159 の user is None 分岐をカバー。
        """
        # Arrange
        from app.core.auth import get_current_user_with_roles, SECRET_KEY, ALGORITHM
        from jose import jwt
        from fastapi import HTTPException
        token = jwt.encode(
            {"sub": "ghost-user", "roles": []}, SECRET_KEY, algorithm=ALGORITHM
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_with_roles(token=token)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_disabled_user_with_roles(self):
        """AUTH-E18: ロール付き無効化ユーザーで400

        auth.py:181 の current_user.disabled 分岐をカバー。

        【実装失敗予定】get_current_active_user_with_roles() は
        FastAPI DI経由で呼ばれるため、直接テストにはDIバイパスが必要。
        """
        # Arrange
        from app.core.auth import get_current_active_user_with_roles
        from app.models.auth import UserWithRoles
        from fastapi import HTTPException

        disabled_user = UserWithRoles(
            username="disabled-user",
            email="disabled@example.com",
            disabled=True,
            roles=["rag_search_read_role"]
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user_with_roles(current_user=disabled_user)
        assert exc_info.value.status_code == 400
        assert "無効なユーザー" in exc_info.value.detail
```

### 3.4 RBAC異常系

```python
class TestRBACErrors:
    """ロールベースアクセス制御のエラーテスト"""

    @pytest.mark.asyncio
    async def test_require_all_roles_partial_match(self):
        """AUTH-E14: require_all_roles で一部ロールのみ所持の場合403

        auth.py:203 の not all(...) 分岐をカバー。

        【実装失敗予定】テスト環境でのエンドポイント登録が必要なため、
        直接 role_checker 関数を呼び出す方式で検証。
        """
        # Arrange
        from app.core.auth import require_all_roles
        from app.models.auth import UserWithRoles
        from fastapi import HTTPException

        checker = require_all_roles(["cspm_dashboard_read_role", "cspm_job_execution_role"])
        user = UserWithRoles(
            username="dashboard-user",
            roles=["cspm_dashboard_read_role"]  # job_execution_role が不足
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            # require_all_roles の内部関数を直接テスト
            # 注: 実際のDI注入をバイパスするためモンキーパッチが必要
            await checker(current_user=user)
        assert exc_info.value.status_code == 403
        assert "不足ロール" in exc_info.value.detail
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| AUTH-SEC-01 | パスワードはbcryptハッシュ化 | fake_users_db全ユーザー | 全て$2b$で始まる |
| AUTH-SEC-02 | 改ざんトークンが拒否される | modified token | 401 |
| AUTH-SEC-03 | レスポンスにパスワード非露出 | /auth/users/me | password/hashed含まない |
| AUTH-SEC-04 | トークン有効期限の検証 | 期限切れトークン | 401 |
| AUTH-SEC-05 | SECRET_KEY未設定時のデフォルト値警告 | JWT_SECRET_KEY未設定 | デフォルト鍵使用 |
| AUTH-SEC-06 | JWT alg=none攻撃が防御される | alg=noneトークン | 401 |
| AUTH-SEC-07 | JWTロール改ざんが検出される | 署名不正トークン | 401 |
| AUTH-SEC-08 | ロールエスカレーション防止 | JWT内に不正ロール | DB上のロールのみ有効 |

```python
@pytest.mark.security
class TestAuthSecurity:
    """認証セキュリティテスト"""

    def test_password_is_hashed(self):
        """AUTH-SEC-01: パスワードがbcryptでハッシュ化されている"""
        # Arrange
        from app.core.auth import fake_users_db

        # Act & Assert
        for username, user_data in fake_users_db.items():
            assert user_data["hashed_password"].startswith("$2b$"), \
                f"ユーザー {username} のパスワードがbcryptハッシュではありません"

    @pytest.mark.asyncio
    async def test_token_modified_rejected(
        self,
        async_client: AsyncClient,
        valid_token: str
    ):
        """AUTH-SEC-02: 改ざんされたトークンが拒否される"""
        # Arrange
        modified_token = valid_token[:-5] + "xxxxx"
        headers = {"Authorization": f"Bearer {modified_token}"}

        # Act
        response = await async_client.get("/auth/users/me", headers=headers)

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_password_not_in_response(
        self,
        async_client: AsyncClient,
        valid_token: str
    ):
        """AUTH-SEC-03: レスポンスにパスワード情報が含まれない"""
        # Arrange
        headers = {"Authorization": f"Bearer {valid_token}"}

        # Act
        response = await async_client.get("/auth/users/me", headers=headers)

        # Assert
        response_text = str(response.json()).lower()
        assert "password" not in response_text
        assert "hashed" not in response_text

    @pytest.mark.asyncio
    async def test_token_expiry_enforced(
        self,
        async_client: AsyncClient,
        expired_token: str
    ):
        """AUTH-SEC-04: トークン有効期限が正しく強制される"""
        # Arrange
        headers = {"Authorization": f"Bearer {expired_token}"}

        # Act
        response = await async_client.get("/auth/protected", headers=headers)

        # Assert
        assert response.status_code == 401

    def test_default_secret_key_warning(self):
        """AUTH-SEC-05: SECRET_KEYが環境変数未設定時にデフォルト値が使われる

        【実装失敗予定】auth.py:18 で JWT_SECRET_KEY 未設定時にデフォルト値が使われるが、
        本番環境では環境変数を必須にすべき。現実装ではデフォルト値が存在する。

        このテストはJWT_SECRET_KEYを環境変数から削除し、
        モジュールを再読み込みしてSECRET_KEYを検証する。
        """
        # Arrange
        import importlib
        import os
        import sys

        # 元のJWT_SECRET_KEY値を保存（テスト後に復元するため）
        original_key = os.environ.get("JWT_SECRET_KEY")

        try:
            # Act: JWT_SECRET_KEYを環境変数から削除してモジュールを再読み込み
            if "JWT_SECRET_KEY" in os.environ:
                del os.environ["JWT_SECRET_KEY"]

            # モジュールキャッシュをクリア
            if "app.core.auth" in sys.modules:
                del sys.modules["app.core.auth"]

            # 再読み込み
            from app.core import auth
            importlib.reload(auth)
            actual_key = auth.SECRET_KEY

            # Assert
            # デフォルト値が使われることを確認（本番では環境変数必須にすべき）
            assert actual_key == "your-secret-key-here-please-change-in-production"

        finally:
            # 元の環境変数を復元
            if original_key is not None:
                os.environ["JWT_SECRET_KEY"] = original_key
            # モジュールキャッシュをクリアして次のテストに影響しないようにする
            if "app.core.auth" in sys.modules:
                del sys.modules["app.core.auth"]

    @pytest.mark.asyncio
    async def test_jwt_alg_none_attack_rejected(self):
        """AUTH-SEC-06: JWT alg=none攻撃が防御される

        alg=noneのヘッダーを持つトークンがjose.jwt.decode()で
        拒否されることを検証する。
        """
        # Arrange
        import json
        import base64
        from app.core.auth import get_current_user
        from fastapi import HTTPException

        # alg=noneのJWTを手動で作成
        header = {"alg": "none", "typ": "JWT"}
        payload = {"sub": "admin", "exp": 9999999999}

        header_b64 = base64.urlsafe_b64encode(
            json.dumps(header).encode()
        ).decode().rstrip("=")
        payload_b64 = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).decode().rstrip("=")

        # alg=noneでは署名部分が空
        fake_token = f"{header_b64}.{payload_b64}."

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=fake_token)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_jwt_role_tampering_rejected(self):
        """AUTH-SEC-07: JWTロール改ざんが署名検証で検出される

        正当なトークンのペイロード部分を改ざんした場合、
        署名検証で拒否されることを検証する。
        """
        # Arrange
        import json
        import base64
        from app.core.auth import get_current_user_with_roles, SECRET_KEY, ALGORITHM
        from jose import jwt
        from fastapi import HTTPException

        # 正当なトークンを生成
        valid_payload = {"sub": "testuser", "roles": ["rag_search_read_role"]}
        valid_token = jwt.encode(valid_payload, SECRET_KEY, algorithm=ALGORITHM)

        # ペイロード部分を改ざん（管理者ロールを追加）
        parts = valid_token.split(".")
        tampered_payload = {"sub": "testuser", "roles": ["cspm_job_execution_role"]}
        tampered_payload_b64 = base64.urlsafe_b64encode(
            json.dumps(tampered_payload).encode()
        ).decode().rstrip("=")

        # 署名は元のまま（改ざんされたペイロードと不整合）
        tampered_token = f"{parts[0]}.{tampered_payload_b64}.{parts[2]}"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_with_roles(token=tampered_token)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_role_escalation_prevented(self):
        """AUTH-SEC-08: JWT内の不正ロールがDB上のロールに優先されない

        【重要な脆弱性指摘】現在の実装（auth.py:163）では
        JWTのロールとDBのロールをマージしているため、
        JWT改ざんによるロールエスカレーションが可能。

        このテストは現在の実装では失敗する可能性があり、
        DB上のロールのみを信頼するよう実装修正が必要。
        """
        # Arrange
        from app.core.auth import get_current_user_with_roles, SECRET_KEY, ALGORITHM
        from jose import jwt

        # testuser（DB上はrag_search_read_roleのみ）に対して
        # JWT内でcspm_job_execution_roleを不正に追加
        malicious_payload = {
            "sub": "testuser",
            "roles": ["cspm_job_execution_role"],  # DB上にないロール
            "exp": 9999999999
        }
        malicious_token = jwt.encode(malicious_payload, SECRET_KEY, algorithm=ALGORITHM)

        # Act
        user = await get_current_user_with_roles(token=malicious_token)

        # Assert
        # 期待: DB上のロール（rag_search_read_role）のみが有効
        # 現実装では失敗する可能性（JWTとDBがマージされる）
        assert "rag_search_read_role" in user.roles, \
            "DB上のロールが含まれていません"

        # 【脆弱性検証】JWT内の不正ロールが含まれていないことを確認
        # 現実装（L163）ではこのアサーションが失敗する
        assert "cspm_job_execution_role" not in user.roles, \
            "【脆弱性】JWT内の不正ロールがエスカレーションされています。" \
            "auth.py:163のロールマージロジックを修正し、DB上のロールのみを信頼すべきです。"
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `app` | FastAPIアプリケーションインスタンス | session | No |
| `async_client` | 非同期HTTPテストクライアント | function | No |
| `valid_token` | 有効なJWTトークン（testuser用、アプリのSECRET_KEYで署名） | function | No |
| `admin_token` | 管理者用JWTトークン | function | No |
| `testuser_token` | 一般ユーザー用JWTトークン（限定ロール） | function | No |
| `dashboard_user_token` | ダッシュボードユーザー用トークン | function | No |
| `expired_token` | 期限切れトークン | function | No |
| `disabled_user_in_db` | 無効化ユーザーをDBに一時追加 | function | No |
| `mock_role_required_endpoint` | ロール必須テスト用エンドポイント登録 | function | No |

### 共通フィクスチャ定義

```python
# test/unit/auth/conftest.py
import sys
import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient, ASGITransport
from jose import jwt


@pytest.fixture(scope="session")
def app():
    """FastAPIアプリケーションインスタンス"""
    from app.main import app
    return app


@pytest_asyncio.fixture
async def async_client(app):
    """非同期HTTPテストクライアント

    ASGITransportを使用してFastAPIアプリに直接接続する。
    実際のHTTPサーバーを起動せずにテスト可能。
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def valid_token():
    """有効なJWTトークン（testuser用）

    注意: アプリのSECRET_KEYを使用して署名する。
    これにより、エンドポイントテストで認証が正しく機能する。
    """
    from app.core.auth import SECRET_KEY, ALGORITHM
    payload = {
        "sub": "testuser",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def admin_token():
    """管理者用JWTトークン（全ロール付き）"""
    from app.core.auth import SECRET_KEY, ALGORITHM
    payload = {
        "sub": "admin",
        "roles": [
            "cspm_dashboard_read_role",
            "rag_search_read_role",
            "document_write_role",
            "cspm_job_execution_role"
        ],
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def testuser_token():
    """一般ユーザー用JWTトークン（限定ロール）"""
    from app.core.auth import SECRET_KEY, ALGORITHM
    payload = {
        "sub": "testuser",
        "roles": ["rag_search_read_role"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def dashboard_user_token():
    """ダッシュボードユーザー用トークン"""
    from app.core.auth import SECRET_KEY, ALGORITHM
    payload = {
        "sub": "dashboard-user",
        "roles": ["cspm_dashboard_read_role"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def expired_token():
    """期限切れトークン"""
    from app.core.auth import SECRET_KEY, ALGORITHM
    payload = {
        "sub": "testuser",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def disabled_user_in_db():
    """無効化ユーザーをfake_users_dbに一時追加するフィクスチャ

    テスト終了後にクリーンアップを行う。
    """
    from app.core.auth import fake_users_db

    disabled_user_data = {
        "username": "disabled-user",
        "full_name": "無効ユーザー",
        "email": "disabled@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": True,
        "roles": []
    }

    # 追加
    fake_users_db["disabled-user"] = disabled_user_data
    yield disabled_user_data

    # クリーンアップ
    if "disabled-user" in fake_users_db:
        del fake_users_db["disabled-user"]


@pytest.fixture
def mock_role_required_endpoint(app):
    """ロール必須のテスト用エンドポイントを登録するフィクスチャ

    テスト時にFastAPIアプリにcspm_dashboard_read_role必須の
    一時エンドポイントを追加する。

    注意: FastAPIではルーター削除が難しいため、
    テスト専用のパスを使用して競合を回避する。
    """
    from fastapi import APIRouter, Depends
    from app.core.auth import require_roles

    test_router = APIRouter(tags=["test"])

    @test_router.get("/protected-dashboard")
    async def protected_dashboard_endpoint(
        user=Depends(require_roles(["cspm_dashboard_read_role"]))
    ):
        return {"status": "ok", "user": user.username}

    # ルーターを追加
    app.include_router(test_router)
    yield

    # 注: FastAPIではルート削除が困難なため、
    # テスト終了後もルートは残るが、テスト専用パスのため影響なし
```

---

## 6. テスト実行例

```bash
# auth関連テストのみ実行
pytest test/unit/auth/test_auth.py -v

# 特定のテストクラスのみ実行
pytest test/unit/auth/test_auth.py::TestAuthEndpoints -v
pytest test/unit/auth/test_auth.py::TestAuthCoreLogic -v
pytest test/unit/auth/test_auth.py::TestAuthSecurity -v

# カバレッジ付きで実行
pytest test/unit/auth/test_auth.py --cov=app.auth --cov=app.core.auth --cov-report=term-missing -v

# セキュリティマーカーで実行
# pyproject.toml: markers = ["security: セキュリティ関連テスト"]
pytest test/unit/auth/test_auth.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 12 | AUTH-001 〜 AUTH-012 |
| 異常系 | 18 | AUTH-E01 〜 AUTH-E18 |
| セキュリティ | 8 | AUTH-SEC-01 〜 AUTH-SEC-08 |
| **合計** | **38** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestAuthEndpoints` | AUTH-001〜AUTH-003 | 3 |
| `TestAuthCoreLogic` | AUTH-004〜AUTH-008 | 5 |
| `TestTokenCreation` | AUTH-009〜AUTH-012 | 4 |
| `TestAuthEndpointErrors` | AUTH-E01〜AUTH-E07 | 7 |
| `TestAuthCoreLogicErrors` | AUTH-E08〜AUTH-E13 | 6 |
| `TestGetCurrentUserWithRolesErrors` | AUTH-E15〜AUTH-E18 | 4 |
| `TestRBACErrors` | AUTH-E14 | 1 |
| `TestAuthSecurity` | AUTH-SEC-01〜AUTH-SEC-08 | 8 |

### 実装失敗が予想されるテスト

| テストID | 失敗理由 | 修正方針 |
|---------|---------|---------|
| AUTH-E06 | `fake_users_db` に disabled ユーザーが存在しない（`auth.py:175`） | `disabled_user_in_db` フィクスチャで一時的にユーザーを追加 |
| AUTH-E14 | `require_all_roles` 内部関数のDI注入バイパスが必要（`auth.py:202`） | テスト用にFastAPI依存性を直接注入するヘルパーを作成 |
| AUTH-E18 | `get_current_active_user_with_roles` のDI注入バイパスが必要（`auth.py:181`） | 直接関数呼び出しでテスト |
| AUTH-SEC-05 | `auth.py:18` でデフォルトSECRET_KEYが存在する。本番ではバリデーション必須にすべき | `config.py` で `JWT_SECRET_KEY` を必須環境変数に追加 |
| AUTH-SEC-08 | `auth.py:163` でJWTとDBのロールをマージしており、JWT内の不正ロールが有効になる | **実装修正必須**: DB上のロールのみを信頼するよう変更 |

### 注意事項

- `pytest-asyncio` と `httpx` が必要（非同期テスト用）
- `@pytest.mark.security` マーカーを `pyproject.toml` に登録が必要
- トークンフィクスチャはアプリの `SECRET_KEY` を使用して署名（テスト環境での整合性確保）
- `fake_users_db` のパスワードは全ユーザー共通（`secret`）でbcryptハッシュ済み
- `datetime.utcnow()` は非推奨のため、フィクスチャでは `datetime.now(timezone.utc)` を使用

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `fake_users_db` はインメモリのため、DB操作テスト不可 | CRUD操作のテストができない | 本番DB移行時にリポジトリパターンでテスト分離 |
| 2 | `require_roles` / `require_all_roles` はFastAPI DIに依存 | 単体テストでの直接呼び出しが困難 | `mock_role_required_endpoint` フィクスチャでテスト用ルートを追加 |
| 3 | `SECRET_KEY` がモジュールレベルで評価される | テスト間での環境変数パッチが効かない場合がある | トークンフィクスチャでアプリの `SECRET_KEY` を直接使用 |
| 4 | `datetime.utcnow()` はdeprecated（Python 3.12+） | 将来的にWarningが出る可能性 | 実装・テストともに `datetime.now(timezone.utc)` への移行を推奨 |
| 5 | ~~JWT `alg` 混同攻撃テスト未実装~~ | ~~`alg=none` トークン受入リスク~~ | **AUTH-SEC-06で実装済み** |
| 6 | **【脆弱性】ロール権限エスカレーション** | `auth.py:163` でJWTとDBのロールをマージ、JWT改ざんでロール追加の可能性 | **AUTH-SEC-08で検証**。**実装修正必須**: `combined_roles` ではなく `user.roles` のみを使用 |
| 7 | タイミング攻撃への対策テスト未実装 | ユーザー存在確認の処理時間差による情報漏洩 | 将来的にAUTH-SEC-09として追加を検討 |
| 8 | ブルートフォース攻撃対策テスト未実装 | 無制限のログイン試行が可能 | 将来的にAUTH-SEC-10として追加を検討（レート制限実装が必要） |
