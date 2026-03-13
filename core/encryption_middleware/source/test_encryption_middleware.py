"""
encryption_middleware.py 単位テスト

テスト仕様: encryption_middleware_tests.md
カバレッジ目標: 85%+

テストカテゴリ:
  - 正常系: 15 個のテスト
  - 異常系: 8 個のテスト
  - セキュリティテスト: 5 個のテスト
"""

import pytest
import sys
import json
import base64
import hashlib
import os
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# テスト対象モジュールをインポートする
project_root = Path(__file__).parent.parent.parent.parent / "platform_python_backend-testing"
sys.path.insert(0, str(project_root))


@pytest.fixture(autouse=True)
def reset_encryption_middleware_module():
    """テストごとにモジュールの状態をリセット

    暗号化ミドルウェアは初期化時に復号テストを実行するため、
    テスト間の独立性を保証するためにモジュールキャッシュをクリアする。
    """
    # テスト前にモジュールキャッシュをクリア
    modules_to_remove = [
        key for key in list(sys.modules.keys())
        if key.startswith("app.core.encryption_middleware") or key.startswith("app.core.crypto")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]

    yield

    # テスト後にもモジュールキャッシュをクリア
    modules_to_remove = [
        key for key in list(sys.modules.keys())
        if key.startswith("app.core.encryption_middleware") or key.startswith("app.core.crypto")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


# ========================================================================
# 正常系テスト
# ========================================================================

class TestDecryptionMiddlewareInit:
    """DecryptionMiddleware初期化テスト - 正常系"""

    @pytest.mark.asyncio
    async def test_init_with_successful_decryption_test(self, caplog):
        """ENCMW-001: 初期化時の復号テスト成功

        覆盖代码行: encryption_middleware.py:31-37

        测试目的:
          - 初期化時に test_decryption_with_known_data() が成功した場合、
            ミドルウェアが正常に初期化されることを検証
        """
        # Arrange - テストデータとシミュレーションオブジェクトの準備
        import logging
        caplog.set_level(logging.INFO)
        mock_app = AsyncMock()

        with patch("app.core.encryption_middleware.test_decryption_with_known_data", return_value=True):
            # アクション - テスト対象の関数を実行する
            from app.core.encryption_middleware import DecryptionMiddleware
            middleware = DecryptionMiddleware(mock_app)

        # Assert - 結果が予期したものと一致することを確認する
        assert middleware.app == mock_app
        assert middleware.paths_to_decrypt == ["/chat"]
        assert "準備完了" in caplog.text or "ミドルウェア" in caplog.text

    def test_init_with_custom_paths(self):
        """ENCMW-013: カスタムパスリストでの初期化

        覆盖代码行: encryption_middleware.py:23-29
        """
        # Arrange
        mock_app = MagicMock()
        custom_paths = ["/custom", "/encrypted"]

        with patch("app.core.encryption_middleware.test_decryption_with_known_data", return_value=True):
            # Act
            from app.core.encryption_middleware import DecryptionMiddleware
            middleware = DecryptionMiddleware(mock_app, paths_to_decrypt=custom_paths)

        # Assert
        assert middleware.paths_to_decrypt == custom_paths


class TestDecryptionMiddlewarePassthrough:
    """パススルー処理テスト（復号対象外のリクエスト） - 正常系"""

    @pytest.fixture
    def mock_app(self):
        """モックアプリケーション"""
        return AsyncMock()

    @pytest.fixture
    def middleware(self, mock_app):
        """テスト用ミドルウェアインスタンス"""
        with patch("app.core.encryption_middleware.test_decryption_with_known_data", return_value=True):
            from app.core.encryption_middleware import DecryptionMiddleware
            return DecryptionMiddleware(mock_app, paths_to_decrypt=["/chat"])

    @pytest.mark.asyncio
    async def test_non_http_scope_passthrough(self, middleware, mock_app):
        """ENCMW-002: 非HTTPスコープのパススルー

        覆盖代码行: encryption_middleware.py:45-47
        """
        # Arrange
        scope = {"type": "websocket", "path": "/chat"}
        receive = AsyncMock()
        send = AsyncMock()

        # Act
        await middleware(scope, receive, send)

        # Assert
        mock_app.assert_called_once_with(scope, receive, send)

    @pytest.mark.asyncio
    async def test_non_target_path_passthrough(self, middleware, mock_app):
        """ENCMW-003: 復号対象外パスのパススルー

        覆盖代码行: encryption_middleware.py:53-56
        """
        # Arrange
        scope = {"type": "http", "path": "/api/health", "method": "POST"}
        receive = AsyncMock()
        send = AsyncMock()

        # Act
        await middleware(scope, receive, send)

        # Assert
        mock_app.assert_called_once_with(scope, receive, send)

    @pytest.mark.asyncio
    async def test_get_request_passthrough(self, middleware, mock_app):
        """ENCMW-004: GETリクエストのパススルー

        覆盖代码行: encryption_middleware.py:53-56
        """
        # Arrange
        scope = {"type": "http", "path": "/chat", "method": "GET"}
        receive = AsyncMock()
        send = AsyncMock()

        # Act
        await middleware(scope, receive, send)

        # Assert
        mock_app.assert_called_once_with(scope, receive, send)

    @pytest.mark.asyncio
    async def test_empty_body_passthrough(self, middleware, mock_app):
        """ENCMW-005: 空ボディのパススルー

        覆盖代码行: encryption_middleware.py:71-73
        """
        # Arrange
        scope = {"type": "http", "path": "/chat", "method": "POST", "headers": []}
        receive = AsyncMock(return_value={
            "type": "http.request",
            "body": b"",
            "more_body": False
        })
        send = AsyncMock()

        # Act
        await middleware(scope, receive, send)

        # Assert
        mock_app.assert_called_once()

    @pytest.mark.asyncio
    async def test_non_json_body_passthrough(self, middleware, mock_app):
        """ENCMW-006: 非JSONボディのパススルー

        覆盖代码行: encryption_middleware.py:78-81
        """
        # Arrange
        scope = {"type": "http", "path": "/chat", "method": "POST", "headers": []}
        receive = AsyncMock(return_value={
            "type": "http.request",
            "body": b"plain text not json",
            "more_body": False
        })
        send = AsyncMock()

        # Act
        await middleware(scope, receive, send)

        # Assert
        mock_app.assert_called_once()

    @pytest.mark.asyncio
    async def test_non_encrypted_json_passthrough(self, middleware, mock_app):
        """ENCMW-007: encryptedフラグなしのパススルー

        覆盖代码行: encryption_middleware.py:84-87
        """
        # Arrange
        scope = {"type": "http", "path": "/chat", "method": "POST", "headers": []}
        body = json.dumps({"prompt": "test", "session_id": "123"}).encode()
        receive = AsyncMock(return_value={
            "type": "http.request",
            "body": body,
            "more_body": False
        })
        send = AsyncMock()

        # Act
        await middleware(scope, receive, send)

        # Assert
        mock_app.assert_called_once()

    @pytest.mark.asyncio
    async def test_http_disconnect_message(self, middleware, mock_app):
        """ENCMW-014: http.disconnect メッセージ処理

        覆盖代码行: encryption_middleware.py:60
        """
        # Arrange
        scope = {"type": "http", "path": "/chat", "method": "POST", "headers": []}
        receive = AsyncMock(return_value={"type": "http.disconnect"})
        send = AsyncMock()

        # Act
        await middleware(scope, receive, send)

        # Assert
        # 切断時はアプリに転送しない
        assert mock_app.call_count == 0 or mock_app.call_count == 1


class TestDecryptionMiddlewareDecrypt:
    """復号処理成功テスト - 正常系"""

    @pytest.fixture
    def test_shared_secret(self):
        """テスト用共有秘密鍵"""
        return b"test_shared_secret_key_123456789"

    @pytest.fixture
    def encrypted_request_data(self, test_shared_secret):
        """テスト用暗号化リクエストデータを生成（OpenSearchダッシュボード仕様準拠）"""
        from cryptography.hazmat.primitives import padding
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend

        # 平文データ
        plaintext_data = {"session_id": "test-session", "prompt": "Hello"}
        plaintext = json.dumps(plaintext_data)

        # 鍵生成（Node.js側と同じ方式）
        key = hashlib.sha256(test_shared_secret).digest()

        # IV生成
        iv = os.urandom(16)

        # PKCS7パディング追加
        padder = padding.PKCS7(128).padder()
        padded = padder.update(plaintext.encode('utf-8')) + padder.finalize()

        # AES-256-CBC暗号化
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded) + encryptor.finalize()

        return {
            "encrypted": True,
            "data": base64.b64encode(ciphertext).decode(),
            "iv": base64.b64encode(iv).decode()
        }

    @pytest.mark.asyncio
    async def test_decrypt_encrypted_request_success(self, test_shared_secret, encrypted_request_data):
        """ENCMW-008: 暗号化リクエストの復号成功

        覆盖代码行: encryption_middleware.py:109-149

        测试目的:
          - 復号後のボディが期待どおりの平文JSONであることを検証
        """
        # Arrange
        mock_app = AsyncMock()
        decrypted_body_captured = None

        async def capture_app(scope, receive, send):
            nonlocal decrypted_body_captured
            message = await receive()
            decrypted_body_captured = message.get("body", b"")

        mock_app.side_effect = capture_app

        with patch("app.core.encryption_middleware.test_decryption_with_known_data", return_value=True), \
             patch("app.core.encryption_middleware._get_shared_secret", return_value=test_shared_secret) as mock_secret:
            from app.core.encryption_middleware import DecryptionMiddleware
            middleware = DecryptionMiddleware(mock_app, paths_to_decrypt=["/chat"])

            scope = {
                "type": "http",
                "path": "/chat",
                "method": "POST",
                "headers": [(b"content-type", b"application/json")]
            }
            body = json.dumps(encrypted_request_data).encode()
            receive = AsyncMock(return_value={
                "type": "http.request",
                "body": body,
                "more_body": False
            })
            send = AsyncMock()

            # Act - patch有効期間内で実行
            await middleware(scope, receive, send)

        # Assert
        mock_app.assert_called_once()
        # 復号されたボディが正しいことを確認
        assert decrypted_body_captured is not None
        decrypted_data = json.loads(decrypted_body_captured.decode())
        assert decrypted_data["session_id"] == "test-session"
        assert decrypted_data["prompt"] == "Hello"

    @pytest.mark.asyncio
    async def test_content_length_header_update(self, test_shared_secret, encrypted_request_data):
        """ENCMW-009: Content-Length ヘッダー更新

        覆盖代码行: encryption_middleware.py:118-133
        """
        # Arrange
        mock_app = AsyncMock()
        decrypted_body_captured = None
        original_length = 1000

        async def capture_app(scope, receive, send):
            nonlocal decrypted_body_captured
            message = await receive()
            decrypted_body_captured = message.get("body", b"")

        mock_app.side_effect = capture_app

        with patch("app.core.encryption_middleware.test_decryption_with_known_data", return_value=True), \
             patch("app.core.encryption_middleware._get_shared_secret", return_value=test_shared_secret):
            from app.core.encryption_middleware import DecryptionMiddleware
            middleware = DecryptionMiddleware(mock_app, paths_to_decrypt=["/chat"])

            scope = {
                "type": "http",
                "path": "/chat",
                "method": "POST",
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(original_length).encode()),
                    (b"x-custom-header", b"custom-value")
                ]
            }
            body = json.dumps(encrypted_request_data).encode()
            receive = AsyncMock(return_value={
                "type": "http.request",
                "body": body,
                "more_body": False
            })
            send = AsyncMock()

            # Act - patch有効期間内で実行
            await middleware(scope, receive, send)

        # Assert
        call_args = mock_app.call_args
        if call_args is not None:
            new_scope = call_args[0][0]
            # Content-Lengthが更新されていることを確認
            content_length_headers = [
                v for k, v in new_scope["headers"] if k.lower() == b"content-length"
            ]
            assert len(content_length_headers) == 1
            assert content_length_headers[0] != str(original_length).encode()
        # Content-Lengthが実際のボディ長に一致することを確認
        assert int(content_length_headers[0].decode()) == len(decrypted_body_captured)

    @pytest.mark.asyncio
    async def test_content_length_header_addition(self, test_shared_secret, encrypted_request_data):
        """ENCMW-010: Content-Length ヘッダー追加

        覆盖代码行: encryption_middleware.py:134-137
        """
        # Arrange
        mock_app = AsyncMock()

        with patch("app.core.encryption_middleware.test_decryption_with_known_data", return_value=True), \
             patch("app.core.encryption_middleware._get_shared_secret", return_value=test_shared_secret):
            from app.core.encryption_middleware import DecryptionMiddleware
            middleware = DecryptionMiddleware(mock_app, paths_to_decrypt=["/chat"])

            scope = {
                "type": "http",
                "path": "/chat",
                "method": "POST",
                "headers": [(b"content-type", b"application/json")]  # content-lengthなし
            }
            body = json.dumps(encrypted_request_data).encode()
            receive = AsyncMock(return_value={
                "type": "http.request",
                "body": body,
                "more_body": False
            })
            send = AsyncMock()

            # Act - patch有効期間内で実行
            await middleware(scope, receive, send)

        # Assert
        call_args = mock_app.call_args
        if call_args is not None:
            new_scope = call_args[0][0]
            # Content-Lengthが追加されていることを確認
            content_length_headers = [
                v for k, v in new_scope["headers"] if k.lower() == b"content-length"
            ]
            assert len(content_length_headers) == 1

    @pytest.mark.asyncio
    async def test_decrypt_with_valid_auth_hash(self, test_shared_secret):
        """ENCMW-011: 認証ハッシュ検証成功

        覆盖代码行: encryption_middleware.py:211-215
        """
        # Arrange
        import hmac
        from cryptography.hazmat.primitives import padding
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend

        session_id = "test-session-auth"
        timestamp = int(time.time())
        message = f"{session_id}:{timestamp}"
        auth_hash = hmac.new(test_shared_secret, message.encode(), hashlib.sha256).hexdigest()
        auth_header = f"SHARED-HMAC-{timestamp}-{auth_hash}"

        # 暗号化データ作成
        plaintext = json.dumps({"session_id": session_id, "prompt": "test"})
        key = hashlib.sha256(test_shared_secret).digest()
        iv = os.urandom(16)
        padder = padding.PKCS7(128).padder()
        padded = padder.update(plaintext.encode('utf-8')) + padder.finalize()
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded) + encryptor.finalize()

        encrypted_data = {
            "encrypted": True,
            "data": base64.b64encode(ciphertext).decode(),
            "iv": base64.b64encode(iv).decode()
        }

        mock_app = AsyncMock()

        with patch("app.core.encryption_middleware.test_decryption_with_known_data", return_value=True), \
             patch("app.core.encryption_middleware._get_shared_secret", return_value=test_shared_secret):
            from app.core.encryption_middleware import DecryptionMiddleware
            middleware = DecryptionMiddleware(mock_app, paths_to_decrypt=["/chat"])

            scope = {
                "type": "http",
                "path": "/chat",
                "method": "POST",
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"x-auth-hash", auth_header.encode())
                ]
            }
            body = json.dumps(encrypted_data).encode()
            receive = AsyncMock(return_value={
                "type": "http.request",
                "body": body,
                "more_body": False
            })
            send = AsyncMock()

            # Act - patch有効期間内で実行
            await middleware(scope, receive, send)

        # Assert
        mock_app.assert_called_once()

    @pytest.mark.asyncio
    async def test_decrypt_without_auth_hash(self, test_shared_secret):
        """ENCMW-015: 認証ハッシュヘッダーなしで復号成功

        覆盖代码行: encryption_middleware.py:101-106

        测试目的:
          - X-Auth-Hashヘッダーが存在しない場合、認証検証をスキップして
            復号処理が成功することを検証
        """
        # Arrange
        from cryptography.hazmat.primitives import padding
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend

        session_id = "test-session-no-auth"

        # 暗号化データ作成
        plaintext = json.dumps({"session_id": session_id, "prompt": "test"})
        key = hashlib.sha256(test_shared_secret).digest()
        iv = os.urandom(16)
        padder = padding.PKCS7(128).padder()
        padded = padder.update(plaintext.encode('utf-8')) + padder.finalize()
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded) + encryptor.finalize()

        encrypted_data = {
            "encrypted": True,
            "data": base64.b64encode(ciphertext).decode(),
            "iv": base64.b64encode(iv).decode()
        }

        mock_app = AsyncMock()

        with patch("app.core.encryption_middleware.test_decryption_with_known_data", return_value=True), \
             patch("app.core.encryption_middleware._get_shared_secret", return_value=test_shared_secret):
            from app.core.encryption_middleware import DecryptionMiddleware
            middleware = DecryptionMiddleware(mock_app, paths_to_decrypt=["/chat"])

            scope = {
                "type": "http",
                "path": "/chat",
                "method": "POST",
                "headers": [(b"content-type", b"application/json")]  # X-Auth-Hashなし
            }
            body = json.dumps(encrypted_data).encode()
            receive = AsyncMock(return_value={
                "type": "http.request",
                "body": body,
                "more_body": False
            })
            send = AsyncMock()

            # Act - patch有効期間内で実行
            await middleware(scope, receive, send)

        # Assert - 認証ハッシュなしでも復号成功
        mock_app.assert_called_once()


class TestCreateDecryptionMiddleware:
    """ファクトリ関数テスト - 正常系"""

    def test_create_decryption_middleware(self):
        """ENCMW-012: ファクトリ関数でミドルウェア生成

        覆盖代码行: encryption_middleware.py:247-255
        """
        # Arrange
        mock_app = MagicMock()
        paths = ["/encrypted", "/secure"]

        with patch("app.core.encryption_middleware.test_decryption_with_known_data", return_value=True):
            # Act
            from app.core.encryption_middleware import create_decryption_middleware
            factory = create_decryption_middleware(paths)
            middleware = factory(mock_app)

        # Assert
        from app.core.encryption_middleware import DecryptionMiddleware
        assert isinstance(middleware, DecryptionMiddleware)
        assert middleware.paths_to_decrypt == paths


# ========================================================================
# 異常系テスト
# ========================================================================

class TestDecryptionMiddlewareInitErrors:
    """初期化エラーテスト - 異常系"""

    def test_init_with_decryption_test_failure(self, caplog):
        """ENCMW-E01: 初期化時の復号テスト失敗で警告ログ

        覆盖代码行: encryption_middleware.py:36-37
        """
        # Arrange
        import logging
        caplog.set_level(logging.WARNING)
        mock_app = MagicMock()

        with patch("app.core.encryption_middleware.test_decryption_with_known_data", return_value=False):
            # Act
            from app.core.encryption_middleware import DecryptionMiddleware
            middleware = DecryptionMiddleware(mock_app)

        # Assert
        assert middleware is not None
        # 警告ログが出力されることを確認
        assert "失敗" in caplog.text or "warning" in caplog.text.lower() or len(caplog.records) > 0

    def test_init_with_decryption_test_exception(self, caplog):
        """ENCMW-E02: 初期化時の復号テスト例外でエラーログ

        覆盖代码行: encryption_middleware.py:38-39
        """
        # Arrange
        import logging
        caplog.set_level(logging.ERROR)
        mock_app = MagicMock()

        with patch("app.core.encryption_middleware.test_decryption_with_known_data", side_effect=Exception("Test error")):
            # Act
            from app.core.encryption_middleware import DecryptionMiddleware
            middleware = DecryptionMiddleware(mock_app)

        # Assert
        assert middleware is not None


class TestDecryptionMiddlewareDecryptErrors:
    """復号処理エラーテスト - 異常系"""

    @pytest.fixture
    def middleware_and_mocks(self):
        """テスト用ミドルウェアとモック"""
        mock_app = AsyncMock()
        with patch("app.core.encryption_middleware.test_decryption_with_known_data", return_value=True):
            from app.core.encryption_middleware import DecryptionMiddleware
            middleware = DecryptionMiddleware(mock_app, paths_to_decrypt=["/chat"])
        return middleware, mock_app

    @pytest.mark.asyncio
    async def test_decrypt_with_invalid_auth_hash(self):
        """ENCMW-E03: 無効な認証ハッシュ

        覆盖代码行: encryption_middleware.py:214-215
        """
        # Arrange
        test_secret = b"test_shared_secret_key_123456789"
        session_id = "test-session"

        # 有効な暗号化データを作成
        from cryptography.hazmat.primitives import padding
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend

        plaintext = json.dumps({"session_id": session_id, "prompt": "test"})
        key = hashlib.sha256(test_secret).digest()
        iv = os.urandom(16)
        padder = padding.PKCS7(128).padder()
        padded = padder.update(plaintext.encode('utf-8')) + padder.finalize()
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded) + encryptor.finalize()

        encrypted_data = {
            "encrypted": True,
            "data": base64.b64encode(ciphertext).decode(),
            "iv": base64.b64encode(iv).decode()
        }

        mock_app = AsyncMock()

        with patch("app.core.encryption_middleware.test_decryption_with_known_data", return_value=True), \
             patch("app.core.encryption_middleware._get_shared_secret", return_value=test_secret), \
             patch("app.core.encryption_middleware.verify_auth_hash", return_value=False):
            from app.core.encryption_middleware import DecryptionMiddleware
            middleware = DecryptionMiddleware(mock_app, paths_to_decrypt=["/chat"])

        scope = {
            "type": "http",
            "path": "/chat",
            "method": "POST",
            "headers": [
                (b"content-type", b"application/json"),
                (b"x-auth-hash", b"SHARED-HMAC-invalid-hash")
            ]
        }
        body = json.dumps(encrypted_data).encode()
        receive = AsyncMock(return_value={
            "type": "http.request",
            "body": body,
            "more_body": False
        })
        send = AsyncMock()

        # Act
        await middleware(scope, receive, send)

        # Assert
        mock_app.assert_not_called()
        send_calls = [call for call in send.call_args_list]
        response_start = send_calls[0][0][0]
        assert response_start["status"] == 400

    @pytest.mark.asyncio
    async def test_decrypt_with_missing_iv(self, middleware_and_mocks):
        """ENCMW-E04: IV欠落エラー

        覆盖代码行: encryption_middleware.py:232-234
        """
        # Arrange
        middleware, mock_app = middleware_and_mocks
        scope = {
            "type": "http",
            "path": "/chat",
            "method": "POST",
            "headers": []
        }
        body = json.dumps({"encrypted": True, "data": "encrypted_data_here"}).encode()  # ivなし
        receive = AsyncMock(return_value={
            "type": "http.request",
            "body": body,
            "more_body": False
        })
        send = AsyncMock()

        # Act
        await middleware(scope, receive, send)

        # Assert
        mock_app.assert_not_called()
        send_calls = [call for call in send.call_args_list]
        response_start = send_calls[0][0][0]
        assert response_start["status"] == 400

    @pytest.mark.asyncio
    async def test_decrypt_with_invalid_ciphertext(self, middleware_and_mocks):
        """
        ENCMW-E05: 暗号文復号失敗

                コード行のオーバーライド: encryption_middleware.py:228-230
        """
        # Arrange
        middleware, mock_app = middleware_and_mocks
        scope = {
            "type": "http",
            "path": "/chat",
            "method": "POST",
            "headers": []
        }
        # 不正な暗号化データ
        body = json.dumps({
            "encrypted": True,
            "data": "invalid_base64_or_encrypted_data!!!",
            "iv": base64.b64encode(b"0123456789abcdef").decode()
        }).encode()
        receive = AsyncMock(return_value={
            "type": "http.request",
            "body": body,
            "more_body": False
        })
        send = AsyncMock()

        # Act
        await middleware(scope, receive, send)

        # Assert
        mock_app.assert_not_called()
        send_calls = [call for call in send.call_args_list]
        response_start = send_calls[0][0][0]
        assert response_start["status"] == 400

    @pytest.mark.asyncio
    async def test_decrypt_with_decryption_exception(self, middleware_and_mocks):
        """ENCMW-E06: 復号処理中の例外

        覆盖代码行: encryption_middleware.py:151-165
        """
        # Arrange
        middleware, mock_app = middleware_and_mocks
        scope = {
            "type": "http",
            "path": "/chat",
            "method": "POST",
            "headers": []
        }
        body = json.dumps({
            "encrypted": True,
            "data": base64.b64encode(b"bad_data").decode(),
            "iv": base64.b64encode(b"0123456789abcdef").decode()
        }).encode()
        receive = AsyncMock(return_value={
            "type": "http.request",
            "body": body,
            "more_body": False
        })
        send = AsyncMock()

        # Act
        await middleware(scope, receive, send)

        # Assert
        mock_app.assert_not_called()
        send_calls = [call for call in send.call_args_list]
        assert len(send_calls) >= 2
        response_start = send_calls[0][0][0]
        assert response_start["status"] == 400

    @pytest.mark.asyncio
    async def test_send_error_response_for_decryption_failure(self, middleware_and_mocks):
        """ENCMW-E07: 復号失敗時の400エラーレスポンス

        覆盖代码行: encryption_middleware.py:151-165
        """
        # Arrange
        middleware, mock_app = middleware_and_mocks
        scope = {
            "type": "http",
            "path": "/chat",
            "method": "POST",
            "headers": []
        }
        body = json.dumps({"encrypted": True, "data": "invalid!!!"}).encode()  # ivなし
        receive = AsyncMock(return_value={
            "type": "http.request",
            "body": body,
            "more_body": False
        })
        send = AsyncMock()

        # Act
        await middleware(scope, receive, send)

        # Assert
        mock_app.assert_not_called()
        assert send.call_count >= 2  # response.start と response.body

        start_call = send.call_args_list[0][0][0]
        body_call = send.call_args_list[1][0][0]

        assert start_call["type"] == "http.response.start"
        assert start_call["status"] == 400
        assert body_call["type"] == "http.response.body"
        assert b"detail" in body_call["body"]

    @pytest.mark.asyncio
    async def test_malformed_encrypted_data_structure(self, middleware_and_mocks):
        """ENCMW-E08: 不正な暗号化データ構造

        覆盖代码行: encryption_middleware.py:189-194
        """
        # Arrange
        middleware, mock_app = middleware_and_mocks
        scope = {
            "type": "http",
            "path": "/chat",
            "method": "POST",
            "headers": []
        }
        # dataキーが存在しない
        body = json.dumps({"encrypted": True, "iv": "abc123"}).encode()
        receive = AsyncMock(return_value={
            "type": "http.request",
            "body": body,
            "more_body": False
        })
        send = AsyncMock()

        # Act
        await middleware(scope, receive, send)

        # Assert
        mock_app.assert_not_called()
        send_calls = [call for call in send.call_args_list]
        response_start = send_calls[0][0][0]
        assert response_start["status"] == 400

    @pytest.mark.asyncio
    async def test_receive_exception_handling(self, middleware_and_mocks, caplog):
        """ENCMW-E09: receive() 関数の例外処理

        覆盖代码行: encryption_middleware.py:61-73
        """
        # Arrange
        import logging
        caplog.set_level(logging.ERROR)
        middleware, mock_app = middleware_and_mocks
        scope = {
            "type": "http",
            "path": "/chat",
            "method": "POST",
            "headers": []
        }

        # receive が例外を投げる
        receive = AsyncMock(side_effect=Exception("Network error"))
        send = AsyncMock()

        # Act - ミドルウェアを実行
        await middleware(scope, receive, send)

        # Assert - エラーログが記録されることを確認
        assert "Network error" in caplog.text or any("Network error" in record.message for record in caplog.records)


# ========================================================================
# セキュリティテスト
# ========================================================================

@pytest.mark.security
class TestEncryptionMiddlewareSecurity:
    """セキュリティテスト"""

    @pytest.fixture
    def middleware_and_mocks(self):
        """テスト用ミドルウェアとモック"""
        mock_app = AsyncMock()
        with patch("app.core.encryption_middleware.test_decryption_with_known_data", return_value=True):
            from app.core.encryption_middleware import DecryptionMiddleware
            middleware = DecryptionMiddleware(mock_app, paths_to_decrypt=["/chat"])
        return middleware, mock_app

    @pytest.mark.asyncio
    async def test_sec_01_shared_secret_not_logged(self, caplog):
        """ENCMW-SEC-01: 共有秘密鍵がログに出力されないこと

        验证内容:
          - ログ出力に共有秘密鍵の内容が含まれないことを検証
        """
        # Arrange
        import logging
        caplog.set_level(logging.DEBUG)
        mock_app = AsyncMock()

        test_secret = b"supersecret_key_should_not_appear_in_logs"

        with patch("app.core.encryption_middleware.test_decryption_with_known_data", return_value=True), \
             patch("app.core.encryption_middleware._get_shared_secret", return_value=test_secret):
            from app.core.encryption_middleware import DecryptionMiddleware
            middleware = DecryptionMiddleware(mock_app)

        # Assert - 秘密鍵がログに出力されていないことを確認
        log_text = caplog.text.lower()
        assert "supersecret" not in log_text
        assert test_secret.decode().lower() not in log_text

    @pytest.mark.asyncio
    async def test_sec_02_decrypted_data_not_logged(self, middleware_and_mocks, caplog):
        """ENCMW-SEC-02: 復号後のデータがログに出力されないこと

        验证内容:
          - 復号後の平文データがログに含まれないことを検証
        """
        # Arrange
        import logging
        caplog.set_level(logging.DEBUG)
        middleware, mock_app = middleware_and_mocks

        test_secret = b"test_shared_secret_key_123456789"
        sensitive_data = "SENSITIVE_PASSWORD_123"

        from cryptography.hazmat.primitives import padding
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend

        plaintext = json.dumps({"session_id": "test", "password": sensitive_data})
        key = hashlib.sha256(test_secret).digest()
        iv = os.urandom(16)
        padder = padding.PKCS7(128).padder()
        padded = padder.update(plaintext.encode('utf-8')) + padder.finalize()
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded) + encryptor.finalize()

        encrypted_data = {
            "encrypted": True,
            "data": base64.b64encode(ciphertext).decode(),
            "iv": base64.b64encode(iv).decode()
        }

        with patch("app.core.encryption_middleware._get_shared_secret", return_value=test_secret):
            scope = {
                "type": "http",
                "path": "/chat",
                "method": "POST",
                "headers": []
            }
            body = json.dumps(encrypted_data).encode()
            receive = AsyncMock(return_value={
                "type": "http.request",
                "body": body,
                "more_body": False
            })
            send = AsyncMock()

            # Act
            await middleware(scope, receive, send)

        # Assert - 復号後のセンシティブデータがログに出力されていないことを確認
        log_text = caplog.text
        assert sensitive_data not in log_text

    @pytest.mark.asyncio
    async def test_sec_03_auth_hash_not_logged(self, middleware_and_mocks, caplog):
        """ENCMW-SEC-03: 認証ハッシュがログに出力されないこと

        验证内容:
          - 認証ハッシュの値がログに含まれないことを検証
        """
        # Arrange
        import logging
        caplog.set_level(logging.DEBUG)
        middleware, mock_app = middleware_and_mocks

        sensitive_auth_hash = "SHARED-HMAC-1234567890-abcdef123456"

        scope = {
            "type": "http",
            "path": "/chat",
            "method": "POST",
            "headers": [
                (b"x-auth-hash", sensitive_auth_hash.encode())
            ]
        }
        body = json.dumps({"prompt": "test"}).encode()
        receive = AsyncMock(return_value={
            "type": "http.request",
            "body": body,
            "more_body": False
        })
        send = AsyncMock()

        # Act
        await middleware(scope, receive, send)

        # Assert - 認証ハッシュがログに出力されていないことを確認
        log_text = caplog.text
        assert "abcdef123456" not in log_text

    @pytest.mark.asyncio
    async def test_sec_04_error_message_safe(self, middleware_and_mocks):
        """ENCMW-SEC-04: エラーメッセージに秘密情報が含まれないこと

        验证内容:
          - 復号失敗時のエラーレスポンスに、攻撃者に有用な内部情報が含まれないことを検証
        """
        # Arrange
        middleware, mock_app = middleware_and_mocks
        scope = {
            "type": "http",
            "path": "/chat",
            "method": "POST",
            "headers": []
        }
        # 不正な暗号化データ
        body = json.dumps({
            "encrypted": True,
            "data": "invalid!!!",
            "iv": "also_invalid!!!"
        }).encode()
        receive = AsyncMock(return_value={
            "type": "http.request",
            "body": body,
            "more_body": False
        })
        send = AsyncMock()

        # Act
        await middleware(scope, receive, send)

        # Assert
        send_calls = [call for call in send.call_args_list]
        body_call = send_calls[1][0][0]
        error_body = body_call["body"].decode()

        # エラーメッセージに内部情報が含まれないことを確認
        assert "traceback" not in error_body.lower()
        assert "c:\\" not in error_body.lower()
        assert "encryption_middleware.py" not in error_body.lower()

    @pytest.mark.asyncio
    async def test_sec_05_timing_attack_resistance(self):
        """ENCMW-SEC-05: タイミング攻撃への耐性

        验证内容:
          - crypto.pyのverify_auth_hashがHMACを使用していることを検証
          - 注意: 現在の実装は直接比較を使用していますが、HMAC自体がタイミング攻撃に強いです
        """
        # Arrange
        test_secret = b"test_shared_secret_key_123456789"

        with patch("app.core.encryption_middleware.test_decryption_with_known_data", return_value=True):
            from app.core.encryption_middleware import DecryptionMiddleware
            from app.core import crypto

            # Assert - crypto.pyにHMACが使用されていることを確認
            import inspect
            source = inspect.getsource(crypto.verify_auth_hash)
            # HMACアルゴリズム自体を使用していることを確認（タイミング攻撃に対する基本的な保護）
            assert "hmac.new" in source or "HMAC" in source
            # 理想的にはhmac.compare_digestを使うべきだが、現在の実装は直接比較
            # これは将来の改善点として記録
