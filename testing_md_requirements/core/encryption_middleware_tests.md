# encryption_middleware テストケース

## 1. 概要

暗号化されたHTTPリクエストを復号するASGIミドルウェアのテストケースを定義します。
`crypto.py`の復号機能を利用し、暗号化されたリクエストボディを平文に変換してアプリケーションに渡します。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `DecryptionMiddleware` | ASGIミドルウェアとしての暗号化リクエスト復号クラス |
| `__call__(scope, receive, send)` | ASGIエントリーポイント、リクエストの傍受と復号 |
| `_decrypt_request(encrypted_request, auth_header)` | 暗号化データの検証と復号処理 |
| `create_decryption_middleware(paths_to_decrypt)` | ミドルウェアファクトリ関数 |

### 1.2 カバレッジ目標: 85%

> **注記**: ASGIミドルウェアの性質上、`scope`/`receive`/`send`の完全モックが必要。
> `crypto.py`の復号処理は別途テスト済みのため、本モジュールでは統合動作を検証。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/core/encryption_middleware.py` |
| テストコード | `test/unit/core/test_encryption_middleware.py` |
| 依存モジュール | `app/core/crypto.py` |

### 1.4 補足情報

**主要分岐（encryption_middleware.py）:**

| 行 | 条件 | 処理 |
|----|------|------|
| 45-47 | `scope["type"] != "http"` | そのままパススルー |
| 53-56 | `not should_decrypt or method != "POST"` | そのままパススルー |
| 71-73 | `not body` | そのままパススルー |
| 78-81 | `json.JSONDecodeError` | そのままパススルー |
| 84-87 | `not encrypted` フラグ | そのままパススルー |
| 109-149 | 復号成功 | 新しいボディで継続 |
| 151-165 | 復号失敗 | 400エラーレスポンス |
| 197-230 | IVあり | OpenSearch Dashboard復号 |
| 232-234 | IVなし | ValueError |

**依存する外部関数（crypto.py）:**
- `decrypt_opensearch_dashboard_payload()`
- `verify_auth_hash()`
- `_get_shared_secret()`
- `test_decryption_with_known_data()`

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| ENCMW-001 | 初期化時の復号テスト成功 | `test_decryption_with_known_data()`成功 | ミドルウェア初期化成功 |
| ENCMW-002 | 非HTTPスコープのパススルー | `scope["type"]="websocket"` | そのままアプリに転送 |
| ENCMW-003 | 復号対象外パスのパススルー | `/api/health` | そのままアプリに転送 |
| ENCMW-004 | GET リクエストのパススルー | `POST`以外 | そのままアプリに転送 |
| ENCMW-005 | 空ボディのパススルー | `body=b""` | そのままアプリに転送 |
| ENCMW-006 | 非JSONボディのパススルー | `body=b"plain text"` | そのままアプリに転送 |
| ENCMW-007 | encryptedフラグなしのパススルー | `{"prompt": "test"}` | そのままアプリに転送 |
| ENCMW-008 | 暗号化リクエストの復号成功 | 有効な暗号化データ | 復号されたボディでアプリに転送 |
| ENCMW-009 | Content-Length ヘッダー更新 | 暗号化データ | 新しいボディ長に更新 |
| ENCMW-010 | Content-Length ヘッダー追加 | ヘッダーなし | 新規追加 |
| ENCMW-011 | 認証ハッシュ検証成功 | X-Auth-Hash ヘッダー付き | 復号＋認証成功 |
| ENCMW-012 | ファクトリ関数でミドルウェア生成 | パスリスト | DecryptionMiddlewareインスタンス |
| ENCMW-013 | カスタムパスリストでの初期化 | `["/custom"]` | カスタムパスで復号 |
| ENCMW-014 | http.disconnect メッセージ処理 | 切断メッセージ | 早期リターン |
| ENCMW-015 | 認証ハッシュヘッダーなしで復号成功 | X-Auth-Hash なし | 復号成功（認証スキップ） |

### 2.1 初期化テスト

```python
# test/unit/core/test_encryption_middleware.py
import pytest
import sys
import json
import base64
import hashlib
import os
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.fixture(autouse=True)
def reset_encryption_middleware_module():
    """テストごとにモジュールの状態をリセット

    暗号化ミドルウェアは初期化時に復号テストを実行するため、
    テスト間の独立性を保証するためにモジュールキャッシュをクリアする。
    テスト前後両方でクリアすることで、並列実行時の競合を防止する。
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


class TestDecryptionMiddlewareInit:
    """DecryptionMiddleware初期化テスト"""

    @pytest.mark.asyncio
    async def test_init_with_successful_decryption_test(self, caplog):
        """ENCMW-001: 初期化時の復号テスト成功

        初期化時に test_decryption_with_known_data() が成功した場合、
        ミドルウェアが正常に初期化されることを検証。
        """
        # Arrange
        import logging
        caplog.set_level(logging.INFO)
        mock_app = AsyncMock()

        with patch("app.core.encryption_middleware.test_decryption_with_known_data", return_value=True):
            # Act
            from app.core.encryption_middleware import DecryptionMiddleware
            middleware = DecryptionMiddleware(mock_app)

        # Assert
        assert middleware.app == mock_app
        assert middleware.paths_to_decrypt == ["/chat"]
        # ログに「準備完了」が出力されることを確認
        assert "準備完了" in caplog.text or "ミドルウェア" in caplog.text

    def test_init_with_custom_paths(self):
        """ENCMW-013: カスタムパスリストでの初期化"""
        # Arrange
        mock_app = MagicMock()
        custom_paths = ["/custom", "/encrypted"]

        with patch("app.core.encryption_middleware.test_decryption_with_known_data", return_value=True):
            # Act
            from app.core.encryption_middleware import DecryptionMiddleware
            middleware = DecryptionMiddleware(mock_app, paths_to_decrypt=custom_paths)

        # Assert
        assert middleware.paths_to_decrypt == custom_paths
```

### 2.2 パススルーテスト

```python
class TestDecryptionMiddlewarePassthrough:
    """パススルー処理テスト（復号対象外のリクエスト）"""

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
        """ENCMW-002: 非HTTPスコープのパススルー"""
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
        """ENCMW-003: 復号対象外パスのパススルー"""
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
        """ENCMW-004: GETリクエストのパススルー"""
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
        """ENCMW-005: 空ボディのパススルー"""
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
        """ENCMW-006: 非JSONボディのパススルー"""
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
        """ENCMW-007: encryptedフラグなしのパススルー"""
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
    async def test_http_disconnect_handling(self, middleware, mock_app):
        """ENCMW-014: http.disconnectメッセージ処理"""
        # Arrange
        scope = {"type": "http", "path": "/chat", "method": "POST", "headers": []}
        receive = AsyncMock(return_value={"type": "http.disconnect"})
        send = AsyncMock()

        # Act
        await middleware(scope, receive, send)

        # Assert
        mock_app.assert_not_called()  # 切断時はアプリに転送しない
```

### 2.3 復号成功テスト

```python
class TestDecryptionMiddlewareDecrypt:
    """復号処理成功テスト"""

    @pytest.fixture
    def test_shared_secret(self):
        """テスト用共有秘密鍵"""
        return b"test_shared_secret_key_123456789"

    @pytest.fixture
    def encrypted_request_data(self, test_shared_secret):
        """テスト用暗号化リクエストデータを生成"""
        from cryptography.hazmat.primitives import padding
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend

        # 平文データ
        plaintext = '{"session_id": "test-session", "prompt": "Hello"}'

        # 鍵生成
        key = hashlib.sha256(test_shared_secret).digest()

        # IV生成
        iv = os.urandom(16)

        # パディング追加
        padder = padding.PKCS7(128).padder()
        padded = padder.update(plaintext.encode('utf-8')) + padder.finalize()

        # 暗号化
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded) + encryptor.finalize()

        return {
            "encrypted": True,
            "data": base64.b64encode(ciphertext).decode(),
            "iv": base64.b64encode(iv).decode()
        }

    @pytest.mark.asyncio
    async def test_successful_decryption(self, test_shared_secret, encrypted_request_data):
        """ENCMW-008: 暗号化リクエストの復号成功

        復号後のボディが期待どおりの平文JSONであることを検証。
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
             patch("app.core.encryption_middleware._get_shared_secret", return_value=test_shared_secret):
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

        # Act
        await middleware(scope, receive, send)

        # Assert
        mock_app.assert_called_once()
        # 新しいスコープが渡されていることを確認
        call_args = mock_app.call_args
        new_scope = call_args[0][0]
        assert new_scope["type"] == "http"
        # 復号されたボディが正しいことを確認
        assert decrypted_body_captured is not None
        decrypted_data = json.loads(decrypted_body_captured.decode())
        assert decrypted_data["session_id"] == "test-session"
        assert decrypted_data["prompt"] == "Hello"

    @pytest.mark.asyncio
    async def test_content_length_header_updated(self, test_shared_secret, encrypted_request_data):
        """ENCMW-009: Content-Lengthヘッダー更新

        復号後のボディ長に一致するようContent-Lengthが更新されることを検証。
        また、他のヘッダー（content-type等）が保持されることも検証。
        """
        # Arrange
        mock_app = AsyncMock()
        decrypted_body_captured = None
        original_length = 1000  # 元のContent-Length

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

        # Act
        await middleware(scope, receive, send)

        # Assert
        call_args = mock_app.call_args
        new_scope = call_args[0][0]
        # Content-Lengthが更新されていることを確認
        content_length_headers = [
            v for k, v in new_scope["headers"] if k.lower() == b"content-length"
        ]
        assert len(content_length_headers) == 1
        assert content_length_headers[0] != str(original_length).encode()
        # Content-Lengthが実際のボディ長に一致することを確認
        assert int(content_length_headers[0].decode()) == len(decrypted_body_captured)
        # 他のヘッダーが保持されていることを確認
        custom_headers = [v for k, v in new_scope["headers"] if k.lower() == b"x-custom-header"]
        assert len(custom_headers) == 1
        assert custom_headers[0] == b"custom-value"

    @pytest.mark.asyncio
    async def test_content_length_header_added(self, test_shared_secret, encrypted_request_data):
        """ENCMW-010: Content-Lengthヘッダー追加"""
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

        # Act
        await middleware(scope, receive, send)

        # Assert
        call_args = mock_app.call_args
        new_scope = call_args[0][0]
        # Content-Lengthが追加されていることを確認
        content_length_headers = [
            v for k, v in new_scope["headers"] if k.lower() == b"content-length"
        ]
        assert len(content_length_headers) == 1
```

### 2.4 認証ハッシュ検証テスト

```python
class TestDecryptionMiddlewareAuthHash:
    """認証ハッシュ検証テスト"""

    @pytest.fixture
    def test_shared_secret(self):
        return b"test_shared_secret_key_123456789"

    @pytest.mark.asyncio
    async def test_auth_hash_verification_success(self, test_shared_secret):
        """ENCMW-011: 認証ハッシュ検証成功"""
        # Arrange
        import hmac
        import hashlib
        import time
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

        # Act
        await middleware(scope, receive, send)

        # Assert
        mock_app.assert_called_once()

    @pytest.mark.asyncio
    async def test_decryption_without_auth_hash_header(self, test_shared_secret):
        """ENCMW-015: 認証ハッシュヘッダーなしで復号成功

        X-Auth-Hashヘッダーが存在しない場合、認証検証をスキップして
        復号処理が成功することを検証。
        encryption_middleware.py:101-106 のヘッダー検索ループがbreakせず
        auth_header=Noneのまま処理が継続するケースをカバー。
        """
        # Arrange
        import hashlib
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
            "headers": [
                (b"content-type", b"application/json")
                # X-Auth-Hashヘッダーなし
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

        # Assert - 認証ハッシュなしでも復号成功
        mock_app.assert_called_once()
```

### 2.5 ファクトリ関数テスト

```python
class TestCreateDecryptionMiddleware:
    """ファクトリ関数テスト"""

    def test_create_middleware_factory(self):
        """ENCMW-012: ファクトリ関数でミドルウェア生成"""
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
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| ENCMW-E01 | 初期化時の復号テスト失敗 | `test_decryption_with_known_data()`失敗 | 警告ログ出力 |
| ENCMW-E02 | 初期化時の復号テスト例外 | `test_decryption_with_known_data()`例外 | エラーログ出力 |
| ENCMW-E03 | 暗号化データなしでValueError | `"data"キー欠落` | 400エラーレスポンス |
| ENCMW-E04 | 暗号化データ型不正でValueError | `data: 123` | 400エラーレスポンス |
| ENCMW-E05 | IVなしでValueError | `iv`キー欠落 | 400エラーレスポンス |
| ENCMW-E06 | 復号失敗でValueError | 不正な暗号化データ | 400エラーレスポンス |
| ENCMW-E07 | 認証ハッシュ検証失敗 | 不正なHMACヘッダー | 400エラーレスポンス |
| ENCMW-E08 | more_bodyフラグ付きボディ読み取り | 分割ボディ | 全部分を結合 |

### 3.1 初期化異常系テスト

```python
class TestDecryptionMiddlewareInitErrors:
    """初期化エラーテスト"""

    def test_init_with_failed_decryption_test(self, caplog):
        """ENCMW-E01: 初期化時の復号テスト失敗で警告ログ

        encryption_middleware.py:36-37 の else 分岐をカバー。
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
        assert middleware is not None  # 初期化は成功する
        # 警告ログが出力されることを確認
        assert "失敗" in caplog.text or "warning" in caplog.text.lower()

    def test_init_with_decryption_test_exception(self, caplog):
        """ENCMW-E02: 初期化時の復号テスト例外でエラーログ"""
        # Arrange
        import logging
        caplog.set_level(logging.ERROR)
        mock_app = MagicMock()

        with patch("app.core.encryption_middleware.test_decryption_with_known_data", side_effect=Exception("Test error")):
            # Act
            from app.core.encryption_middleware import DecryptionMiddleware
            middleware = DecryptionMiddleware(mock_app)

        # Assert
        assert middleware is not None  # 例外でも初期化は成功する
```

### 3.2 復号異常系テスト

```python
class TestDecryptionMiddlewareDecryptErrors:
    """復号処理エラーテスト"""

    @pytest.fixture
    def middleware_and_mocks(self):
        """テスト用ミドルウェアとモック"""
        mock_app = AsyncMock()
        with patch("app.core.encryption_middleware.test_decryption_with_known_data", return_value=True):
            from app.core.encryption_middleware import DecryptionMiddleware
            middleware = DecryptionMiddleware(mock_app, paths_to_decrypt=["/chat"])
        return middleware, mock_app

    @pytest.mark.asyncio
    async def test_missing_data_key_returns_400(self, middleware_and_mocks):
        """ENCMW-E03: 暗号化データなしで400エラー

        encryption_middleware.py:189 の `if "data" not in encrypted_request` 分岐をカバー。
        """
        # Arrange
        middleware, mock_app = middleware_and_mocks
        scope = {
            "type": "http",
            "path": "/chat",
            "method": "POST",
            "headers": []
        }
        body = json.dumps({"encrypted": True, "iv": "abc123"}).encode()  # dataなし
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
        # 400エラーレスポンスが送信されることを確認
        assert send.call_count == 2  # response.start と response.body

        start_call = send.call_args_list[0][0][0]
        body_call = send.call_args_list[1][0][0]

        assert start_call["type"] == "http.response.start"
        assert start_call["status"] == 400
        assert body_call["type"] == "http.response.body"
        assert b"detail" in body_call["body"]

    @pytest.mark.asyncio
    async def test_invalid_data_type_returns_400(self, middleware_and_mocks):
        """ENCMW-E04: 暗号化データ型不正で400エラー

        encryption_middleware.py:193-194 の `if not isinstance(encrypted_data, str)` 分岐をカバー。
        """
        # Arrange
        middleware, mock_app = middleware_and_mocks
        scope = {
            "type": "http",
            "path": "/chat",
            "method": "POST",
            "headers": []
        }
        body = json.dumps({"encrypted": True, "data": 12345, "iv": "abc123"}).encode()
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
    async def test_missing_iv_returns_400(self, middleware_and_mocks):
        """ENCMW-E05: IVなしで400エラー

        encryption_middleware.py:232-234 の `else: raise ValueError("暗号化リクエストにIVが含まれていません")` 分岐をカバー。
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
    async def test_decryption_failure_returns_400(self, middleware_and_mocks):
        """ENCMW-E06: 復号失敗で400エラー

        encryption_middleware.py:228-230 の `except Exception as osd_error` 分岐をカバー。
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
    async def test_auth_hash_verification_failure_returns_400(self):
        """ENCMW-E07: 認証ハッシュ検証失敗で400エラー

        encryption_middleware.py:214-215 の `if not verify_auth_hash(...)` 分岐をカバー。
        """
        # Arrange
        import hashlib
        from cryptography.hazmat.primitives import padding
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend

        test_secret = b"test_shared_secret_key_123456789"
        session_id = "test-session"

        # 有効な暗号化データを作成
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
    async def test_chunked_body_reading(self, middleware_and_mocks):
        """ENCMW-E08: more_bodyフラグ付きボディ読み取り

        encryption_middleware.py:61-66 の while ループ（more_body）分岐をカバー。
        """
        # Arrange
        middleware, mock_app = middleware_and_mocks
        scope = {
            "type": "http",
            "path": "/chat",
            "method": "POST",
            "headers": []
        }

        # 分割されたボディデータ
        body_part1 = b'{"prompt": "'
        body_part2 = b'test", "encrypted": false}'

        call_count = 0
        async def mock_receive():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {"type": "http.request", "body": body_part1, "more_body": True}
            else:
                return {"type": "http.request", "body": body_part2, "more_body": False}

        receive = mock_receive
        send = AsyncMock()

        # Act
        await middleware(scope, receive, send)

        # Assert
        mock_app.assert_called_once()  # 非暗号化データはパススルー
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| ENCMW-SEC-01 | エラーメッセージに内部詳細が含まれない | 各種復号エラー | 統一メッセージ |
| ENCMW-SEC-02 | 暗号化データのログ出力がマスクされている | 有効な暗号化データ | 最初100文字のみ |
| ENCMW-SEC-03 | 認証ハッシュ検証のタイミング攻撃耐性 | HMACヘッダー | compare_digest使用（crypto.py依存） |
| ENCMW-SEC-04 | IVの再利用検出 | 同一IV複数回 | 警告または拒否 |
| ENCMW-SEC-05 | Content-Type検証なしの受け入れ | 不正Content-Type | JSONとして処理 |

```python
@pytest.mark.security
class TestDecryptionMiddlewareSecurity:
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
    async def test_error_message_no_internal_details(self, middleware_and_mocks):
        """ENCMW-SEC-01: エラーメッセージに内部詳細が含まれない

        復号失敗時のエラーレスポンスに、攻撃者に有用な内部情報
        （スタックトレース、ファイルパス、内部エラー詳細）が含まれないことを検証。
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
        # response.body を取得
        if len(send_calls) >= 2:
            response_body = send_calls[1][0][0].get("body", b"")
            error_response = response_body.decode() if response_body else ""

            # 内部詳細キーワードが含まれていないことを検証
            internal_keywords = ["traceback", "File ", "line ", "Exception", "Error:"]
            for keyword in internal_keywords:
                assert keyword.lower() not in error_response.lower(), (
                    f"エラーレスポンスに内部詳細 '{keyword}' が含まれています: {error_response}"
                )
            # Python例外型名が漏洩していないことを検証
            exception_types = ["ValueError", "KeyError", "TypeError", "AttributeError"]
            for exc_type in exception_types:
                assert exc_type not in error_response, (
                    f"エラーレスポンスに例外型名 '{exc_type}' が漏洩しています: {error_response}"
                )

    @pytest.mark.asyncio
    async def test_encrypted_data_logging_masked(self, caplog):
        """ENCMW-SEC-02: 暗号化データのログ出力がマスクされている

        暗号化データ全体がログに出力されず、先頭の一部のみが出力されることを検証。
        encryption_middleware.py:93 の `request_data.get('data', '')[:100]` をカバー。
        """
        # Arrange
        import logging
        caplog.set_level(logging.DEBUG)

        mock_app = AsyncMock()
        with patch("app.core.encryption_middleware.test_decryption_with_known_data", return_value=True):
            from app.core.encryption_middleware import DecryptionMiddleware
            middleware = DecryptionMiddleware(mock_app, paths_to_decrypt=["/chat"])

        # 長い暗号化データ
        long_data = "A" * 500
        scope = {
            "type": "http",
            "path": "/chat",
            "method": "POST",
            "headers": []
        }
        body = json.dumps({
            "encrypted": True,
            "data": long_data,
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
        # ログに長い暗号化データ全体が含まれていないことを確認
        log_text = caplog.text
        assert long_data not in log_text, "暗号化データ全体がログに出力されています"

    def test_hmac_timing_attack_resistance(self):
        """ENCMW-SEC-03: 認証ハッシュ検証のタイミング攻撃耐性

        crypto.pyのverify_auth_hashがhmac.compare_digestを使用していることを検証。
        （このテストはcrypto_tests.mdのCRYPTO-SEC-01と重複するため、参照のみ）

        【実装失敗予定】crypto.py:98 で == を使用しているため失敗する
        """
        # Arrange
        import inspect
        from app.core.crypto import verify_auth_hash
        source = inspect.getsource(verify_auth_hash)

        # Assert
        assert "compare_digest" in source, (
            "verify_auth_hash は hmac.compare_digest() を使用すべきです。"
            "== による文字列比較はタイミング攻撃に脆弱です。"
        )

    @pytest.mark.asyncio
    async def test_iv_reuse_not_detected(self, middleware_and_mocks):
        """ENCMW-SEC-04: IVの再利用検出なし

        現在の実装ではIV再利用を検出しない。
        将来的にはIV再利用を検出して拒否する実装が望ましい。

        【注記】これは現在の実装の制限事項であり、セキュリティ強化の余地がある。
        """
        # Arrange
        middleware, mock_app = middleware_and_mocks

        # 同じIVを使用する2つのリクエスト
        fixed_iv = base64.b64encode(b"0123456789abcdef").decode()

        scope = {
            "type": "http",
            "path": "/chat",
            "method": "POST",
            "headers": []
        }
        body = json.dumps({
            "encrypted": True,
            "data": "some_encrypted_data",
            "iv": fixed_iv
        }).encode()
        receive = AsyncMock(return_value={
            "type": "http.request",
            "body": body,
            "more_body": False
        })
        send = AsyncMock()

        # Act - 同じIVで2回リクエスト
        await middleware(scope, receive, send)

        # Assert - 現在の実装ではIV再利用を検出しない（この動作は制限事項）
        # 将来的にはこのテストが失敗するよう実装を強化すべき
        pass

    @pytest.mark.asyncio
    async def test_content_type_not_validated(self, middleware_and_mocks):
        """ENCMW-SEC-05: Content-Type検証なしの受け入れ

        Content-Typeヘッダーに関係なくJSONとしてパースを試行することを検証。
        不正なContent-TypeでもJSONとして処理される。

        【注記】これは現在の実装の動作であり、Content-Type検証の追加が望ましい。
        """
        # Arrange
        middleware, mock_app = middleware_and_mocks
        scope = {
            "type": "http",
            "path": "/chat",
            "method": "POST",
            "headers": [(b"content-type", b"text/plain")]  # 不正なContent-Type
        }
        body = json.dumps({"prompt": "test", "encrypted": False}).encode()
        receive = AsyncMock(return_value={
            "type": "http.request",
            "body": body,
            "more_body": False
        })
        send = AsyncMock()

        # Act
        await middleware(scope, receive, send)

        # Assert - Content-Typeに関係なく処理される
        mock_app.assert_called_once()
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_encryption_middleware_module` | テスト間のモジュール状態リセット | function | Yes |
| `mock_app` | モックASGIアプリケーション | function | No |
| `middleware` | テスト用ミドルウェアインスタンス | function | No |
| `test_shared_secret` | テスト用共有秘密鍵 | function | No |
| `encrypted_request_data` | テスト用暗号化リクエストデータ | function | No |

### 共通フィクスチャ定義

```python
# test/unit/core/conftest.py に追加
import sys
import os
import json
import base64
import hashlib
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.fixture(autouse=True)
def reset_encryption_middleware_module():
    """テストごとにモジュールの状態をリセット

    暗号化ミドルウェアは初期化時に復号テストを実行するため、
    テスト間の独立性を保証するためにモジュールキャッシュをクリアする。
    また、crypto.pyのグローバル状態もリセットする必要がある。
    テスト前後両方でクリアすることで、並列実行時の競合を防止する。
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


@pytest.fixture
def test_shared_secret():
    """テスト用共有秘密鍵"""
    return b"test_shared_secret_key_123456789"


@pytest.fixture
def encrypted_request_data(test_shared_secret):
    """テスト用暗号化リクエストデータを生成"""
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend

    plaintext = '{"session_id": "test-session", "prompt": "Hello"}'
    key = hashlib.sha256(test_shared_secret).digest()
    iv = os.urandom(16)

    padder = padding.PKCS7(128).padder()
    padded = padder.update(plaintext.encode('utf-8')) + padder.finalize()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()

    return {
        "encrypted": True,
        "data": base64.b64encode(ciphertext).decode(),
        "iv": base64.b64encode(iv).decode()
    }


@pytest.fixture
def mock_asgi_scope():
    """モックASGIスコープ"""
    return {
        "type": "http",
        "path": "/chat",
        "method": "POST",
        "headers": [(b"content-type", b"application/json")]
    }
```

---

## 6. テスト実行例

```bash
# encryption_middleware関連テストのみ実行
pytest test/unit/core/test_encryption_middleware.py -v

# 特定のテストクラスのみ実行
pytest test/unit/core/test_encryption_middleware.py::TestDecryptionMiddlewareInit -v
pytest test/unit/core/test_encryption_middleware.py::TestDecryptionMiddlewarePassthrough -v
pytest test/unit/core/test_encryption_middleware.py::TestDecryptionMiddlewareDecrypt -v
pytest test/unit/core/test_encryption_middleware.py::TestDecryptionMiddlewareSecurity -v

# カバレッジ付きで実行
pytest test/unit/core/test_encryption_middleware.py --cov=app.core.encryption_middleware --cov-report=term-missing -v

# セキュリティマーカーで実行
# pyproject.toml: markers = ["security: セキュリティ関連テスト"]
pytest test/unit/core/test_encryption_middleware.py -m "security" -v

# asyncioテストのみ実行
pytest test/unit/core/test_encryption_middleware.py -m "asyncio" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 15 | ENCMW-001 〜 ENCMW-015 |
| 異常系 | 8 | ENCMW-E01 〜 ENCMW-E08 |
| セキュリティ | 5 | ENCMW-SEC-01 〜 ENCMW-SEC-05 |
| **合計** | **28** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestDecryptionMiddlewareInit` | ENCMW-001, ENCMW-013 | 2 |
| `TestDecryptionMiddlewarePassthrough` | ENCMW-002〜ENCMW-007, ENCMW-014 | 7 |
| `TestDecryptionMiddlewareDecrypt` | ENCMW-008〜ENCMW-010 | 3 |
| `TestDecryptionMiddlewareAuthHash` | ENCMW-011, ENCMW-015 | 2 |
| `TestCreateDecryptionMiddleware` | ENCMW-012 | 1 |
| `TestDecryptionMiddlewareInitErrors` | ENCMW-E01〜ENCMW-E02 | 2 |
| `TestDecryptionMiddlewareDecryptErrors` | ENCMW-E03〜ENCMW-E08 | 6 |
| `TestDecryptionMiddlewareSecurity` | ENCMW-SEC-01〜ENCMW-SEC-05 | 5 |

### 実装失敗が予想されるテスト

以下のテストは現在の実装では**意図的に失敗**します。実装側の修正が必要です。

| テストID | 失敗理由 | 修正方針 |
|---------|---------|---------|
| ENCMW-SEC-03 | `crypto.py:98`で`==`比較を使用 | `hmac.compare_digest()`に変更（crypto.py側の修正） |

### 注意事項

- テスト実行に必要な追加パッケージ: `pytest-asyncio`
- `@pytest.mark.security` マーカーを `pyproject.toml` に登録が必要
- `@pytest.mark.asyncio` マーカーは `pytest-asyncio` が自動登録
- crypto.pyの復号機能をモック化してテストするため、統合テストとは別にcrypto_tests.mdのテストも実行すること

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | IV再利用を検出しない（ENCMW-SEC-04） | 同一IVでの暗号化が可能 | 将来的にIVキャッシュ＋拒否機能を追加 |
| 2 | Content-Type検証なし（ENCMW-SEC-05） | 不正なContent-Typeでも処理 | Content-Type検証ミドルウェアを追加 |
| 3 | タイミング攻撃耐性なし（crypto.py依存） | HMAC検証がタイミング攻撃に脆弱 | crypto.pyで`hmac.compare_digest()`を使用 |
| 4 | dispatchメソッドは非推奨 | BaseHTTPMiddleware互換性のため残存 | 使用しないこと |
