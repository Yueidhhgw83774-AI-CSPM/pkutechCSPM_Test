# test_auth.py
"""
authモジュールのユニットテスト

テスト対象:
  - app/core/auth.py (認証のコアロジック)
  - app/auth/router.py (認証エンドポイント)
  - app/models/auth.py (認証モデル)

テスト仕様: docs/testing/plugins/auth_tests.md
カバレッジ目標: 90%+

テストカテゴリ:
  - 正常系: 12のテスト (AUTH-001 ~ AUTH-012)
  - 異常系: 18のテスト (AUTH-E01 ~ AUTH-E18)
  - セキュリティテスト: 8のテスト (AUTH-SEC-01 ~ AUTH-SEC-08)
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

# プロジェクトルートディレクトリの設定
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent / "platform_python_backend-testing"
if not project_root.exists():
    raise RuntimeError(f"项目根目录不存在: {project_root}")
sys.path.insert(0, str(project_root))

# JWTキーの環境変数を設定する
os.environ["JWT_SECRET_KEY"] = "f4fae6a6c089204d69efdc35438312a81005e1c3825a40cfc706cbe5ec0f50b1"


# ============================================================================
# 正常系テスト: エンドポイントテスト (AUTH-001 ~ AUTH-003)
# ============================================================================

class TestAuthEndpoints:
    """
    認証エンドポイント正常系テスト

    テストID: AUTH-001 ~ AUTH-003
    テスト対象: app/auth/router.py
    """

    @pytest.mark.asyncio
    async def test_login_success(self, async_client: AsyncClient):
        """
        AUTH-001: 有効な認証情報でToken取得に成功

                覆盖コード行: router.py:16-40

                テスト目的:
                  - 正しいユーザー名とパスワードでaccess_tokenが取得できることを確認する
                  - 返されるtoken_typeが"bearer"であることを確認する
        """
        # Arrange - テストデータの準備
        form_data = {
            "username": "testuser",
            "password": "secret"
        }

        # アクション - テスト対象の関数を実行する
        response = await async_client.post(
            "/auth/token",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # アサート - 結果の検証
        assert response.status_code == 200  # 検証ステータスコードが正しいことを確認する
        data = response.json()
        assert "access_token" in data  # 検証結果がaccess_tokenを含むことを確認します
        assert data["token_type"] == "bearer"  # トークンタイプがbearerであることを確認する

    @pytest.mark.asyncio
    async def test_get_current_user(self, async_client: AsyncClient, valid_token: str):
        """
        AUTH-002: 認証後にユーザー情報を取得に成功

                覆盖コード行: router.py:42-52

                テスト目的:
                  - 有効なTokenを使用してユーザー情報を取得できるかを確認する
                  - 返されるユーザー情報にusernameとemailが含まれているかを確認する
        """
        # Arrange - 認証ヘッダーの準備
        headers = {"Authorization": f"Bearer {valid_token}"}

        # アクション - リクエストの実行
        response = await async_client.get("/auth/users/me", headers=headers)

        # Assert - 結果の検証
        assert response.status_code == 200  # 検証ステータスコードが正しいことを確認する
        data = response.json()
        assert "username" in data  # 検証結果がusernameを含むことを確認する
        assert "email" in data  # 検証結果がemailを含むことを確認する

    @pytest.mark.asyncio
    async def test_protected_route(self, async_client: AsyncClient, valid_token: str):
        """
        AUTH-003: 保護されたルートへのアクセスに成功

                カバレッジコード行: router.py:54-67

                テスト目的:
                  - 有効なTokenを使用して保護されたエンドポイントにアクセスできるかどうかを検証する
                  - 返信メッセージにユーザー名が含まれていることを検証する
        """
        # Arrange - 認証ヘッダーの準備
        headers = {"Authorization": f"Bearer {valid_token}"}

        # アクション - リクエストの実行
        response = await async_client.get("/auth/protected", headers=headers)

        # アサート - 結果の検証
        assert response.status_code == 200  # 検証ステータスコードが正しいことを確認する
        data = response.json()
        assert "message" in data  # 検証結果がメッセージを含むことを確認する


# ============================================================================
# 正常系テスト: コアロジックテスト (AUTH-004 ~ AUTH-008)
# ============================================================================

class TestAuthCoreLogic:
    """
    認証コアロジック正常系テスト

    テストID: AUTH-004 ~ AUTH-008
    テスト対象: app/core/auth.py
    """

    def test_verify_password_success(self):
        """
        AUTH-004: 正しい平文パスワードの検証に成功

                カバレッジコード行: auth.py:58-60

                テスト目的:
                  - 正しい平文パスワードとハッシュ化されたパスワードが一致することを確認し、Trueを返す

                注意: bcrypt/passlibの互換性問題を回避するためにmockを使用する
        """
        # Arrange - テストデータの準備
        from app.core.auth import verify_password
        plain = "secret"
        # 任意のハッシュ値（mockは無視し、パスワードが"secret"であるかどうかだけをチェックします）
        hashed = "$2b$12$anyhashvalue"

        # アクション - 認定検証実行
        result = verify_password(plain, hashed)

        # アサート - 結果の検証
        assert result is True  # パスワードが一致しました

    def test_get_password_hash(self):
        """
        AUTH-005: パスワードのハッシュ化成功

                覆盖コード行: auth.py:62-64

                テスト目的:
                  - パスワードが正しくハッシュ化されることを確認する
                  - ハッシュ化されたパスワードが検証できることを確認する

                注意: bcrypt/passlibの互換性問題を回避するためにmockを使用する
        """
        # Arrange - テストデータの準備
        from app.core.auth import get_password_hash, verify_password
        password = "secret"

        # アクション - ハッシュ化を実行する
        hashed = get_password_hash(password)

        # Assert - 結果の検証
        assert hashed.startswith("$2b$")  # 検証はbcrypt形式（mockが$2b$で始まる形式を返す）です
        assert verify_password(password, hashed) is True  # ハッシュを検証できる

    def test_get_user_found(self):
        """
        AUTH-006: 存在するユーザーのクエリ成功

                覆盖コード行: auth.py:66-71

                テスト目的:
                  - 存在するユーザー名でUserInDBインスタンスを取得できるか検証する
                  - 返却されるユーザー情報が正しいか検証する
        """
        # Arrange - テストデータの準備
        from app.core.auth import get_user, fake_users_db

        # アクション - クエリの実行
        user = get_user(fake_users_db, "testuser")

        # Assert - 結果の検証
        assert user is not None  # ユーザー存在確認
        assert user.username == "testuser"  # ユーザー名が正しいことを確認する
        assert user.email == "test@example.com"  # メールアドレスの正しさを確認する

    def test_get_user_with_roles_found(self):
        """
        AUTH-007: ロール付きユーザー検索成功

                覆盖コード行: auth.py:73-78

                テスト目的:
                  - ロール情報を含むユーザーを取得できるか確認する
                  - ロールリストが空でないことを確認する
        """
        # Arrange - テストデータの準備
        from app.core.auth import get_user_with_roles, fake_users_db

        # アクション - クエリの実行
        user = get_user_with_roles(fake_users_db, "admin")

        # Assert - 結果の検証
        assert user is not None  # ユーザー存在確認
        assert user.username == "admin"  # ユーザー名が正しいことを確認します
        assert "cspm_dashboard_read_role" in user.roles  # 期待する役割を含むことを検証する

    def test_authenticate_user_with_roles_success(self):
        """
        AUTH-008: ロール付き認証成功

                覆盖コード行: auth.py:89-95

                テスト目的:
                  - 正しい資格情報を使用してUserInDBWithRolesインスタンスが返されることを確認する
                  - ロールリストが空でないことを確認する
        """
        # Arrange - テストデータの準備
        from app.core.auth import authenticate_user_with_roles, fake_users_db

        # Act - 認証を実行する
        user = authenticate_user_with_roles(fake_users_db, "admin", "secret")

        # アサート - 結果の検証
        assert user is not None  # 認証成功を確認する
        assert user.username == "admin"  # ユーザー名が正しいことを確認する
        assert len(user.roles) > 0  # 役割の検証がある


# ============================================================================
# 正常系テスト: Token生成テスト (AUTH-009 ~ AUTH-012)
# ============================================================================

class TestTokenCreation:
    """
    JWTトークン生成正常系テスト

    テストID: AUTH-009 ~ AUTH-012
    テスト対象: app/core/auth.py
    """

    def test_create_access_token_with_expiry(self):
        """
        AUTH-009: 指定有効期限のToken生成に成功

                覆盖コード行: auth.py:97-107 (expires_deltaがTrueの場合のif分岐)

                テスト目的:
                  - 指定有効期限で生成されたTokenに正しいsubが含まれていることを確認する
                  - Tokenにexpフィールドが含まれていることを確認する
        """
        # Arrange - テストデータの準備
        from app.core.auth import create_access_token, SECRET_KEY, ALGORITHM
        data = {"sub": "testuser"}
        expires = timedelta(minutes=60)

        # Act - Token生成を実行
        token = create_access_token(data=data, expires_delta=expires)

        # アサート - 結果の検証
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser"  # subの検証が正しく行われていることを確認する
        assert "exp" in payload  # 有効期限を含む検証を行う

    def test_create_access_token_default_expiry(self):
        """
        AUTH-010: デフォルト有効期限のToken生成成功

                覆盖コード行: auth.py:97-107 (elseブランチ、デフォルト15分)

                テスト目的:
                  - 有効期限を指定しない場合にデフォルト値が使用されることを確認する
                  - Tokenが正しいsubとexpを含んでいることを確認する
        """
        # Arrange - テストデータの準備
        from app.core.auth import create_access_token, SECRET_KEY, ALGORITHM
        data = {"sub": "testuser"}

        # Act - Token生成の実行（expires_delta未指定）
        token = create_access_token(data=data)

        # Assert - 結果の検証
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser"  # subの検証が正しく行われていることを確認する
        assert "exp" in payload  # 有効期限を含む検証を行う

    def test_create_access_token_with_roles_and_expiry(self):
        """
        AUTH-011: ロール付きToken生成成功（有効期限指定）

                覆盖コード行: auth.py:109-118 (expires_delta分支がTrueの場合)

                テスト目的:
                  - Tokenがrolesフィールドを持つことを確認する
                  - ロールリストが正しいことを確認する
        """
        # Arrange - テストデータの準備
        from app.core.auth import create_access_token_with_roles, SECRET_KEY, ALGORITHM
        roles = ["cspm_dashboard_read_role"]

        # Act - Token生成を実行
        token = create_access_token_with_roles(
            "admin", roles, expires_delta=timedelta(minutes=60)
        )

        # アサート - 結果の検証
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "admin"  # subの検証が正しく行われていることを確認する
        assert payload["roles"] == roles  # 役割の検証が正しく行われていることを確認してください。

    def test_create_access_token_with_roles_default_expiry(self):
        """
        AUTH-012: ロール付きToken生成成功（デフォルト30分有効期限）

                覆盖コード行: auth.py:109-118 (elseブランチ、デフォルト30分)

                テスト目的:
                  - 有効期限を指定しない場合にACCESS_TOKEN_EXPIRE_MINUTES(30分)が使用されることを確認する
                  - Tokenに正しいrolesが含まれていることを確認する
        """
        # Arrange - テストデータの準備
        from app.core.auth import create_access_token_with_roles, SECRET_KEY, ALGORITHM
        roles = ["rag_search_read_role"]

        # Act - Token生成の実行（expires_delta未指定）
        token = create_access_token_with_roles("testuser", roles)

        # Assert - 結果の検証
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser"  # subの検証が正しく行われていることを確認する
        assert payload["roles"] == roles  # 役割の検証が正しく行われていることを確認してください。


# ============================================================================
# 異常系テスト: エンドポイントエラーテスト (AUTH-E01 ~ AUTH-E07)
# ============================================================================

class TestAuthEndpointErrors:
    """
    認証エンドポイント異常系テスト

    テストID: AUTH-E01 ~ AUTH-E07
    テスト対象: app/auth/router.py
    """

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, async_client: AsyncClient):
        """
        AUTH-E01: 無効なパスワードの場合401を返す

                覆盖コード行: router.py:31-36 (if not user分支)

                テスト目的:
                  - 無効なパスワードで401ステータスコードが返されることを確認する
                  - エラーメッセージにヒントが含まれていることを確認する
        """
        # Arrange - 無効なパスワードのリクエストデータを準備する
        form_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }

        # アクション - リクエストの実行
        response = await async_client.post(
            "/auth/token",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # アサート - 結果の検証
        assert response.status_code == 401  # 401ステータスコードを検証する
        assert "ユーザー名またはパスワード" in response.json()["detail"]  # 検証エラーメッセージ

    @pytest.mark.asyncio
    async def test_login_unknown_user(self, async_client: AsyncClient):
        """
        AUTH-E02: ユーザが存在しない場合401を返す

                被覆行: auth.py:83 (not user分支)

                テスト目的:
                  - 存在しないユーザ名が返す401を検証する
        """
        # Arrange - 不存在するユーザーのリクエストデータを準備する
        form_data = {
            "username": "unknownuser",
            "password": "secret"
        }

        # アクション - リクエストの実行
        response = await async_client.post(
            "/auth/token",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # アサート - 結果の検証
        assert response.status_code == 401  # 401ステータスコードを検証する

    @pytest.mark.asyncio
    async def test_expired_token(self, async_client: AsyncClient, expired_token: str):
        """
        AUTH-E03: 有効期限切れのTokenは401を返す

                覆盖コード行: auth.py:133 (JWTErrorブランチ)

                テスト目的:
                  - 有効期限切れのTokenが正しく拒否されることを確認する
        """
        # Arrange - 有効期限切れのTokenを使用する
        headers = {"Authorization": f"Bearer {expired_token}"}

        # アクション - リクエストの実行
        response = await async_client.get("/auth/users/me", headers=headers)

        # アサート - 結果の検証
        assert response.status_code == 401  # 401ステータスコードを検証する

    @pytest.mark.asyncio
    async def test_malformed_token(self, async_client: AsyncClient):
        """
        AUTH-E04: 無効なToken形式の場合401を返す

                覆盖コード行: auth.py:133 (JWTError分支)

                テスト目的:
                  - フォーマットが正しくないTokenが拒否されることを確認する
        """
        # Arrange - フォーマットが正しくないTokenを使用する
        headers = {"Authorization": "Bearer invalid.token.format"}

        # アクション - リクエストの実行
        response = await async_client.get("/auth/users/me", headers=headers)

        # Assert - 結果の検証
        assert response.status_code == 401  # 401ステータスコードを検証する

    @pytest.mark.asyncio
    async def test_no_auth_header(self, async_client: AsyncClient):
        """
        AUTH-E05: Authorizationヘッダーがない場合401が返る

                テスト目的:
                  - Authorizationヘッダーが欠如している場合に401が返されることを確認する
        """
        # アクション - 認証ヘッダー無しでリクエストを実行する
        response = await async_client.get("/auth/users/me")

        # Assert - 結果の検証
        assert response.status_code == 401  # 401ステータスコードを検証する

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
        # Arrange - 無効ユーザー用のTokenを作成する
        from app.core.auth import create_access_token
        token = create_access_token(
            data={"sub": "disabled-user"},
            expires_delta=timedelta(hours=1)
        )
        headers = {"Authorization": f"Bearer {token}"}

        # アクション - リクエストの実行
        response = await async_client.get("/auth/users/me", headers=headers)

        # Assert - 結果の検証
        assert response.status_code == 400  # 400ステータスコードの検証
        assert "無効なユーザー" in response.json()["detail"]  # 検証エラーメッセージ

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
        # Arrange - rag_search_read_roleのみのユーザーTokenを使用する
        headers = {"Authorization": f"Bearer {testuser_token}"}

        # Act - cspm_dashboard_read_roleが必要なエンドポイントへのアクセスを試行します
        response = await async_client.get(
            "/protected-dashboard",
            headers=headers
        )

        # Assert - 結果の検証
        assert response.status_code == 403  # 403ステータスコードを検証する
        assert "必要なロール権限がありません" in response.json()["detail"]  # 検証エラーメッセージ


# ============================================================================
# 異常系テスト: コアロジックエラーテスト (AUTH-E08 ~ AUTH-E13)
# ============================================================================

class TestAuthCoreLogicErrors:
    """
    認証コアロジック異常系テスト

    テストID: AUTH-E08 ~ AUTH-E13
    テスト対象: app/core/auth.py
    """

    def test_verify_password_failure(self):
        """
        AUTH-E08: エラーパスワード検証失敗

                カバレッジコード行: auth.py:60 (verify_password失敗パス)

                テスト目的:
                  - エラーなパスワードが返却される場合Falseを返すことを確認する

                注意: bcrypt/passlib互換性問題を回避するためにmockを使用する
        """
        # Arrange - テストデータの準備
        from app.core.auth import verify_password
        # mockは正しいパスワードとしてのみ"secret"を接受する
        hashed = "$2b$12$anyhashvalue"

        # アクション - 異なるパスワードで認証を行う
        result = verify_password("wrongpassword", hashed)

        # アサート - 結果の検証
        assert result is False  # パスワードが一致しません

    def test_get_user_not_found(self):
        """
        AUTH-E09: 存在しないユーザーのクエリはNoneを返す

                被覆コード行: auth.py:71 (return None支流)

                テスト目的:
                  - 存在しないユーザー名がNoneを返すことを確認する
        """
        # Arrange - テストデータの準備
        from app.core.auth import get_user, fake_users_db

        # アクション - クエリの実行
        user = get_user(fake_users_db, "nonexistent")

        # Assert - 結果の検証
        assert user is None  # 検証がNoneを返す

    def test_authenticate_user_with_roles_unknown(self):
        """
        AUTH-E10: ロール付き認証-ユーザーが存在しない場合Noneを返す

                対象コード行: auth.py:92 (not user分支)

                テスト目的:
                  - 存在しないユーザーの認証がNoneを返すことを確認する
        """
        # Arrange - テストデータの準備
        from app.core.auth import authenticate_user_with_roles, fake_users_db

        # Act - 認証を実行する
        user = authenticate_user_with_roles(fake_users_db, "unknown", "secret")

        # Assert - 結果の検証
        assert user is None  # 検証がNoneを返す

    def test_authenticate_user_with_roles_wrong_password(self):
        """
        AUTH-E11: ロール付き認証-パスワードが間違っている場合Noneを返す

                覆盖コード行: auth.py:94 (not verify_password分支)

                テスト目的:
                  - パスワードが間違っている場合、認証がNoneを返すことを確認する
        """
        # Arrange - テストデータの準備
        from app.core.auth import authenticate_user_with_roles, fake_users_db

        # Act - 認証を実行する
        user = authenticate_user_with_roles(fake_users_db, "admin", "wrong")

        # Assert - 結果の検証
        assert user is None  # 検証がNoneを返す

    @pytest.mark.asyncio
    async def test_get_current_user_no_sub(self):
        """
        AUTH-E12: subフィールドのないTokenに対して401を返す

                被覆コード行: auth.py:130 (usernameがNoneの場合のブランチ)

                テスト目的:
                  - Tokenにsubフィールドがない場合に401例外が送出されることを確認する
        """
        # Arrange - subフィールドのないTokenを作成する
        from app.core.auth import get_current_user, SECRET_KEY, ALGORITHM
        from fastapi import HTTPException
        token = jwt.encode({"data": "no-sub"}, SECRET_KEY, algorithm=ALGORITHM)

        # アクション & アサート - 例外の_THROW验证
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token)
        assert exc_info.value.status_code == 401  # 401ステータスコードを検証する

    @pytest.mark.asyncio
    async def test_get_current_user_unknown_sub(self):
        """
        AUTH-E13: DBにsubが存在しない場合、401を返す

                被覆行: auth.py:137 (userがNoneの場合の分岐)

                テスト目的:
                  - Token内のsubユーザーがDBに存在しない場合、401例外を投げる事を確認する
        """
        # Arrange - 存在しないユーザーのTokenを含むものを作成する
        from app.core.auth import get_current_user, SECRET_KEY, ALGORITHM
        from fastapi import HTTPException
        token = jwt.encode({"sub": "ghost-user"}, SECRET_KEY, algorithm=ALGORITHM)

        # アクション & アサート - 例外の_THROW验证
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token)
        assert exc_info.value.status_code == 401  # 401ステータスコードを検証する


# ============================================================================
# 異常系テスト: get_current_user_with_roles エラーテスト (AUTH-E15 ~ AUTH-E18)
# ============================================================================

class TestGetCurrentUserWithRolesErrors:
    """
    get_current_user_with_roles() の例外系テスト

        テストID: AUTH-E15 ~ AUTH-E18
        テスト対象: app/core/auth.py
    """

    @pytest.mark.asyncio
    async def test_get_current_user_with_roles_no_sub(self):
        """
        AUTH-E15: ロール付きでユーザー取得- subが返らない場合401

                被覆コード行: auth.py:152 (usernameがNoneの分支)

                テスト目的:
                  - Token中にsubフィールドがない場合に401例外を投げるかどうかを検証する
        """
        # Arrange - ロールのみ含みサブを含まないTokenを作成する
        from app.core.auth import get_current_user_with_roles, SECRET_KEY, ALGORITHM
        from fastapi import HTTPException
        token = jwt.encode({"roles": ["admin"]}, SECRET_KEY, algorithm=ALGORITHM)

        # アクションとアサート - 例外の投.throwを検証する
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_with_roles(token=token)
        assert exc_info.value.status_code == 401  # 401ステータスコードを検証する

    @pytest.mark.asyncio
    async def test_get_current_user_with_roles_jwt_error(self):
        """
        AUTH-E16: ロール付きユーザー取得-無効なTokenは401を返す

                覆盖コード行: auth.py:156 (JWTError分支)

                テスト目的:
                  - 無効なToken形式の場合、401例外を投げる事を確認する
        """
        # Arrange - 無効なTokenを使用する
        from app.core.auth import get_current_user_with_roles
        from fastapi import HTTPException

        # アクションとアサート - 例外の投.throwを検証する
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_with_roles(token="invalid.token.here")
        assert exc_info.value.status_code == 401  # 401ステータスコードを検証する

    @pytest.mark.asyncio
    async def test_get_current_user_with_roles_unknown_user(self):
        """
        AUTH-E17: ロール付きでユーザーを取得-ユーザーが存在しない場合401を返す

                覆盖コード行: auth.py:159 (user is Noneのブランチ)

                テスト目的:
                  - Token内のユーザーがDBに存在しない場合、401例外を投げる事を確認する
        """
        # Arrange - 存在しないユーザーのTokenを含むものを作成する
        from app.core.auth import get_current_user_with_roles, SECRET_KEY, ALGORITHM
        from fastapi import HTTPException
        token = jwt.encode(
            {"sub": "ghost-user", "roles": []}, SECRET_KEY, algorithm=ALGORITHM
        )

        # アクションとアサート - 例外の投.throwを検証する
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_with_roles(token=token)
        assert exc_info.value.status_code == 401  # 401ステータスコードを検証する

    @pytest.mark.asyncio
    async def test_disabled_user_with_roles(self):
        """
        AUTH-E18: 無効化されたユーザーを含む場合、400が返される

                覆盖コード行: auth.py:181 (current_user.disabled支流)

                テスト目的:
                  - 無効化されたユーザーがget_current_active_user_with_roles時に400例外を投げる事を確認する
        """
        # Arrange - 無効ユーザー オブジェクトの作成
        from app.core.auth import get_current_active_user_with_roles
        from app.models.auth import UserWithRoles
        from fastapi import HTTPException

        disabled_user = UserWithRoles(
            username="disabled-user",
            email="disabled@example.com",
            disabled=True,
            roles=["rag_search_read_role"]
        )

        # アクション & アサート - 例外の_THROW验证
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user_with_roles(current_user=disabled_user)
        assert exc_info.value.status_code == 400  # 400ステータスコードの検証
        assert "無効なユーザー" in exc_info.value.detail  # 検証エラーメッセージ


# ============================================================================
# 異常系テスト: RBACエラーテスト (AUTH-E14)
# ============================================================================

class TestRBACErrors:
    """
    RBAC（役割ベースアクセス制御）異常系テスト

    テストID: AUTH-E14
    テスト対象: app/core/auth.py
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
        # Arrange - 一部の役割のみを持つユーザーの準備を行う
        from app.core.auth import require_all_roles
        from app.models.auth import UserWithRoles
        from fastapi import HTTPException

        checker = require_all_roles(["cspm_dashboard_read_role", "cspm_job_execution_role"])
        user = UserWithRoles(
            username="dashboard-user",
            roles=["cspm_dashboard_read_role"]  # cspm_job_execution_roleが欠缺しています
        )

        # アクション & アサート - 例外の_THROW验证
        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=user)
        assert exc_info.value.status_code == 403  # 403ステータスコードを検証する
        assert "不足ロール" in exc_info.value.detail  # 検証エラーメッセージに不足する文字数のヒントが含まれていることを確認します。


# ============================================================================
# セキュリティテスト (AUTH-SEC-01 ～ AUTH-SEC-08)
# ============================================================================

@pytest.mark.security
class TestAuthSecurity:
    """
    認証セキュリティテスト

    テストID: AUTH-SEC-01 ~ AUTH-SEC-08
    テスト対象: app/core/auth.py
    """

    def test_password_is_hashed(self):
        """
        AUTH-SEC-01: パスワードのbcryptハッシュ検証

                テスト目的:
                  - fake_users_dbのすべてのユーザーのパスワードがbcryptハッシュ形式であることを確認する
        """
        # Arrange - ユーザーデータベースを取得する
        from app.core.auth import fake_users_db

        # アクション & アサート - すべてのパスワードがbcrypt形式であることを確認する
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
        AUTH-SEC-02: 編造されたTokenは拒否される

                テスト目的:
                  - 編造されたTokenが署名検証で拒否されることを確認する
        """
        # Arrange - Tokenの改ざん（最後の5文字を変更）
        modified_token = valid_token[:-5] + "xxxxx"
        headers = {"Authorization": f"Bearer {modified_token}"}

        # アクション - 改ざんされたTokenを使用したリクエスト
        response = await async_client.get("/auth/users/me", headers=headers)

        # Assert - 確認が拒否されました
        assert response.status_code == 401  # 401ステータスコードを検証する

    @pytest.mark.asyncio
    async def test_password_not_in_response(
        self,
        async_client: AsyncClient,
        valid_token: str
    ):
        """
        AUTH-SEC-03: レスポンスにはパスワード情報が含まれていない

                テスト目的:
                  - APIのレスポンスにpasswordまたはhashedに関連するフィールドが含まれていないことを確認する
        """
        # Arrange - 認証ヘッダーの準備
        headers = {"Authorization": f"Bearer {valid_token}"}

        # アクション - ユーザ情報取得
        response = await async_client.get("/auth/users/me", headers=headers)

        # Assert - レスポンスにパスワード情報が含まれていないことを確認する
        response_text = str(response.json()).lower()
        assert "password" not in response_text  # パスワードを含まないことを確認する
        assert "hashed" not in response_text  # ハッシュされたものが含まれていないことを確認する

    @pytest.mark.asyncio
    async def test_token_expiry_enforced(
        self,
        async_client: AsyncClient,
        expired_token: str
    ):
        """
        AUTH-SEC-04: Token有効期限の強制実行

                テスト目的:
                  - 过期Tokenが正しく拒否されることを確認する
        """
        # Arrange - 有効期限切れのTokenを使用する
        headers = {"Authorization": f"Bearer {expired_token}"}

        # アクション - 有効期限切れのトークンを使用して保護されたルートにリクエストを行う
        response = await async_client.get("/auth/protected", headers=headers)

        # アサートチェックが拒否されました
        assert response.status_code == 401  # 401ステータスコードを検証する

    def test_default_secret_key_warning(self):
        """
        AUTH-SEC-05: デフォルトのSECRET_KEY警告

                覆盖コード行: auth.py:18 (JWT_SECRET_KEY環境変数が設定されていない場合)

                テスト目的:
                  - JWT_SECRET_KEYが設定されていない場合、デフォルト値を使用することを確認する
                  - 【セキュリティ推奨】本番環境では環境変数の設定を強制すること

                注意: このテストは、ソースコード中のデフォルト値のロジックを確認するために実施します。
        """
        # Arrange - auth.pyのデフォルト値の論理をチェックする
        import inspect
        from app.core import auth

        # モジュールのソースコードを取得する
        source = inspect.getsource(auth)

        # Assert - デフォルト値の設定が存在することをソースコードで確認する
        # "os.getenv("JWT_SECRET_KEY", "your-secret-key...") の形式のコードがあるかどうかをチェックします
        assert 'os.getenv("JWT_SECRET_KEY"' in source or "os.getenv('JWT_SECRET_KEY'" in source, \
            "auth.py应该从环境变量读取JWT_SECRET_KEY"

        assert "your-secret-key-here-please-change-in-production" in source, \
            "auth.py应该有默认SECRET_KEY值（用于警示需要更改）"

    @pytest.mark.asyncio
    async def test_jwt_alg_none_attack_rejected(self):
        """
        AUTH-SEC-06: JWT alg=none攻撃防御

                テスト目的:
                  - alg=noneのTokenがjose.jwt.decode()で拒否されることを確認する
                  - アルゴリズム降格攻撃を防止する
        """
        # Arrange - 手動でalg=NoneのJWTを作成する
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

        # alg=noneの場合は、署名部分は空となる
        fake_token = f"{header_b64}.{payload_b64}."

        # アクション & アサート - リクエストが拒否されました
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=fake_token)
        assert exc_info.value.status_code == 401  # 401ステータスコードを検証する

    @pytest.mark.asyncio
    async def test_jwt_role_tampering_rejected(self):
        """
        AUTH-SEC-07: JWTロール改ざん検出

                テスト目的:
                  - JWTペイロードを改ざんした後に署名検証が失敗することを確認する
                  - ロールインジェクション攻撃を防止する
        """
        # Arrange - 有効なTokenを作成した後、payloadを改ざんする
        from app.core.auth import get_current_user_with_roles, SECRET_KEY, ALGORITHM
        from fastapi import HTTPException

        # 有効なトークンを作成する
        valid_payload = {"sub": "testuser", "roles": ["rag_search_read_role"]}
        valid_token = jwt.encode(valid_payload, SECRET_KEY, algorithm=ALGORITHM)

        # ペイロードを改ざん（管理者役割を追加）
        parts = valid_token.split(".")
        tampered_payload = {"sub": "testuser", "roles": ["cspm_job_execution_role"]}
        tampered_payload_b64 = base64.urlsafe_b64encode(
            json.dumps(tampered_payload).encode()
        ).decode().rstrip("=")

        # 署名は元のまま保持される（改ざんされたペイロードとマッチングしない）
        tampered_token = f"{parts[0]}.{tampered_payload_b64}.{parts[2]}"

        # アクション & アサート - リクエストが拒否されました
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_with_roles(token=tampered_token)
        assert exc_info.value.status_code == 401  # 401ステータスコードを検証する

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="当前实现存在安全漏洞：auth.py:163会合并JWT和DB角色，允许角色提权")
    async def test_role_escalation_prevented(self):
        """
        AUTH-SEC-08: ロールの昇格防止

                対象コード行: auth.py:163 (combined_rolesの合併ロジック)

                テスト目的:
                  - JWT内の悪意のあるロールがユーザー権限に追加されないことを確認する
                  - DBで定義されたロールのみが有効であることを確認する

                【セキュリティ脆弱性の説明】
                現在の実装(auth.py:163)は、JWT内のrolesとDB内のrolesを合併します:
                  combined_roles = list(set(token_data.roles + user.roles))

                これにより、攻撃者がJWTに任意のロールを注入し、権限を昇格させることができます。

                【修正の提案】
                DB内のrolesのみを使用し、JWT内のrolesを無視するべきです:
                  return UserWithRoles(..., roles=user.roles)
        """
        # Arrange - マルウェアを含むTokenを作成する
        from app.core.auth import get_current_user_with_roles, SECRET_KEY, ALGORITHM

        # testuserはDBで seulement rag_search_read_role を持っています
        # しかし、JWTには悪意のある注入であるcspm_job_execution_roleが含まれています
        malicious_payload = {
            "sub": "testuser",
            "roles": ["cspm_job_execution_role"],  # DBに存在しない役割
            "exp": 9999999999
        }
        malicious_token = jwt.encode(malicious_payload, SECRET_KEY, algorithm=ALGORITHM)

        # アクション - ユーザ取得
        user = await get_current_user_with_roles(token=malicious_token)

        # Assert - DBに役割が存在することを確認する
        assert "rag_search_read_role" in user.roles, \
            "DB中定义的角色应该存在"

        # Assert - JWTに悪意のあるロールが存在しないことを確認する
        # 【注意】現在の実装はこのアサーションで失敗します因为它存在セキュリティ上の脆弱性
        assert "cspm_job_execution_role" not in user.roles, \
            "【安全漏洞】JWT中注入的角色不应该被接受。" \
            "请修改auth.py:163，只使用DB中的roles。"
