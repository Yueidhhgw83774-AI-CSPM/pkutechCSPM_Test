# crypto テストケース

## 1. 概要

暗号化・復号機能のテストケースを定義します。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `_get_shared_secret()` | 環境変数/ファイル/デフォルトから共有秘密鍵を取得 |
| `verify_auth_hash()` | HMAC-SHA256認証ハッシュ検証 |
| `decrypt_opensearch_dashboard_payload()` | AES-CBC + PKCS7パディングでペイロード復号 |
| `decrypt_credentials_field()` | 認証情報フィールドの復号（Base64） |
| `test_decryption_with_known_data()` | 既知データによる復号処理の動作確認 |

### 1.2 カバレッジ目標: 90%

> **注記**: `crypto.py`冒頭コメントは「AES-GCM暗号化方式」と記載されていますが、
> 実装は**AES-CBC + PKCS7パディング**方式です。コメントの修正が必要です。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/core/crypto.py` |
| テストコード | `test/unit/core/test_crypto.py` |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CRYPTO-001 | 環境変数から共有鍵取得 | SHARED_SECRET設定済み | 環境変数値のbytes |
| CRYPTO-002 | ファイルから共有鍵取得 | 有効な鍵ファイル | ファイル内容のbytes |
| CRYPTO-003 | デフォルト開発用鍵のフォールバック | 環境変数未設定＋ファイル未存在 | デフォルト鍵のbytes |
| CRYPTO-004 | strip_whitespace=Falseで空白保持 | 空白含む鍵データ | 空白保持されたbytes |
| CRYPTO-005 | 有効なHMAC認証ハッシュの検証成功 | 正しいHMACヘッダー | True |
| CRYPTO-006 | 有効なペイロードのAES-CBC復号成功 | 暗号化データ+IV | 復号されたbytes |
| CRYPTO-007 | 復号後のJSON正常パース | JSON暗号化データ | dict |
| CRYPTO-008 | 認証情報フィールドのBase64復号 | Base64エンコードデータ | 復号文字列 |
| CRYPTO-009 | test_decryption_with_known_dataの成功 | 既知テストデータ | True |
| CRYPTO-010 | 時刻ずれが許容範囲内での検証成功 | 300秒以内のずれ | True |

### 2.1 _get_shared_secret テスト

```python
# test/unit/core/test_crypto.py
import pytest
import os
import hashlib
import hmac
import time
import base64
import json
from unittest.mock import patch, mock_open


class TestGetSharedSecret:
    """共有秘密鍵取得テスト"""

    def test_get_from_env_variable(self):
        """CRYPTO-001: 環境変数SHARED_SECRETから鍵取得"""
        # Arrange
        test_secret = "my_test_secret_key"

        # Act
        with patch.dict(os.environ, {"SHARED_SECRET": test_secret}):
            from app.core.crypto import _get_shared_secret
            result = _get_shared_secret()

        # Assert
        assert result == test_secret.encode('utf-8')

    def test_get_from_file(self, tmp_path):
        """CRYPTO-002: ファイルから鍵取得"""
        # Arrange
        secret_file = tmp_path / "shared_secret"
        secret_file.write_bytes(b"file_secret_key_12345")

        env = os.environ.copy()
        env.pop("SHARED_SECRET", None)  # 環境変数を未設定にする
        env["SHARED_SECRET_FILE"] = str(secret_file)

        # Act
        with patch.dict(os.environ, env, clear=True):
            from app.core.crypto import _get_shared_secret
            result = _get_shared_secret()

        # Assert
        assert result == b"file_secret_key_12345"

    def test_fallback_to_default_key(self):
        """CRYPTO-003: デフォルト開発用鍵のフォールバック"""
        # Arrange - 環境変数未設定、ファイル未存在
        env = os.environ.copy()
        env.pop("SHARED_SECRET", None)
        env.pop("SHARED_SECRET_FILE", None)

        # Act
        with patch.dict(os.environ, env, clear=True):
            with patch("os.path.exists", return_value=False):
                from app.core.crypto import _get_shared_secret
                result = _get_shared_secret()

        # Assert
        expected = "default_shared_secret_for_development_only".encode('utf-8')
        assert result == expected

    def test_strip_whitespace_false(self, tmp_path):
        """CRYPTO-004: strip_whitespace=Falseで空白保持"""
        # Arrange
        secret_with_whitespace = b"  secret_with_spaces  \n"
        secret_file = tmp_path / "shared_secret"
        secret_file.write_bytes(secret_with_whitespace)

        env = os.environ.copy()
        env.pop("SHARED_SECRET", None)
        env["SHARED_SECRET_FILE"] = str(secret_file)

        # Act
        with patch.dict(os.environ, env, clear=True):
            from app.core.crypto import _get_shared_secret
            result = _get_shared_secret(strip_whitespace=False)

        # Assert
        assert result == secret_with_whitespace  # 空白がそのまま保持される
```

### 2.2 verify_auth_hash テスト

```python
class TestVerifyAuthHash:
    """HMAC認証ハッシュ検証テスト"""

    @pytest.fixture
    def test_shared_secret(self):
        """テスト用共有秘密鍵"""
        return b"test_shared_secret_for_hmac"

    def _create_valid_auth_header(self, session_id: str, shared_secret: bytes, timestamp: int = None) -> str:
        """テスト用の有効な認証ヘッダーを生成"""
        if timestamp is None:
            timestamp = int(time.time())
        message = f"{session_id}:{timestamp}"
        hash_value = hmac.new(shared_secret, message.encode(), hashlib.sha256).hexdigest()
        return f"SHARED-HMAC-{timestamp}-{hash_value}"

    def test_valid_auth_hash(self, test_shared_secret):
        """CRYPTO-005: 有効なHMAC認証ハッシュの検証成功"""
        # Arrange
        session_id = "test-session-123"
        auth_header = self._create_valid_auth_header(session_id, test_shared_secret)

        # Act
        from app.core.crypto import verify_auth_hash
        result = verify_auth_hash(auth_header, session_id, test_shared_secret)

        # Assert
        assert result is True

    def test_valid_hash_within_time_drift(self, test_shared_secret):
        """CRYPTO-010: 時刻ずれが許容範囲内での検証成功"""
        # Arrange
        session_id = "test-session-456"
        past_timestamp = int(time.time()) - 300  # 300秒前
        auth_header = self._create_valid_auth_header(
            session_id, test_shared_secret, timestamp=past_timestamp
        )

        # Act
        from app.core.crypto import verify_auth_hash
        result = verify_auth_hash(auth_header, session_id, test_shared_secret, allowed_time_drift=600)

        # Assert
        assert result is True
```

### 2.3 decrypt_opensearch_dashboard_payload テスト

```python
class TestDecryptOpensearchDashboardPayload:
    """OSDペイロード復号テスト"""

    @pytest.fixture
    def test_shared_secret(self):
        """テスト用共有秘密鍵"""
        return b"test_shared_secret_key_123456789"

    @pytest.fixture
    def encrypted_payload(self, test_shared_secret):
        """テスト用暗号化ペイロード（IV付き）"""
        from cryptography.hazmat.primitives import padding
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend

        # テスト用平文JSON
        plaintext = '{"session_id": "test_123", "prompt": "テストメッセージ"}'

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
            "encrypted_data": base64.b64encode(ciphertext).decode(),
            "iv": base64.b64encode(iv).decode(),
            "expected": json.loads(plaintext)
        }

    def test_decrypt_valid_payload(self, test_shared_secret, encrypted_payload):
        """CRYPTO-006: 有効なペイロードのAES-CBC復号成功"""
        # Act
        from app.core.crypto import decrypt_opensearch_dashboard_payload
        result = decrypt_opensearch_dashboard_payload(
            encrypted_payload["encrypted_data"],
            encrypted_payload["iv"],
            test_shared_secret
        )

        # Assert
        assert isinstance(result, dict)

    def test_decrypt_returns_valid_json(self, test_shared_secret, encrypted_payload):
        """CRYPTO-007: 復号後のJSON正常パース"""
        # Act
        from app.core.crypto import decrypt_opensearch_dashboard_payload
        result = decrypt_opensearch_dashboard_payload(
            encrypted_payload["encrypted_data"],
            encrypted_payload["iv"],
            test_shared_secret
        )

        # Assert
        assert result == encrypted_payload["expected"]
        assert result["session_id"] == "test_123"
        assert result["prompt"] == "テストメッセージ"
```

### 2.4 decrypt_credentials_field テスト

```python
class TestDecryptCredentialsField:
    """認証情報フィールド復号テスト"""

    def test_decrypt_base64_encoded_data(self):
        """CRYPTO-008: 認証情報フィールドのBase64復号"""
        # Arrange
        original_data = '{"access_key": "AKIA...", "secret_key": "xxx"}'
        encoded_data = base64.b64encode(original_data.encode('utf-8')).decode()

        # Act
        from app.core.crypto import decrypt_credentials_field
        result = decrypt_credentials_field(encoded_data)

        # Assert
        assert result == original_data
```

### 2.5 test_decryption_with_known_data テスト

```python
class TestDecryptionWithKnownData:
    """既知データによる復号テスト"""

    def test_known_data_decryption_success(self):
        """CRYPTO-009: test_decryption_with_known_dataの成功"""
        # Act
        from app.core.crypto import test_decryption_with_known_data
        result = test_decryption_with_known_data()

        # Assert
        assert result is True
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CRYPTO-E01 | 鍵ファイルが空でValueError | 空ファイル | ValueError |
| CRYPTO-E02 | 不正なHMAC形式でFalse返却 | 不正形式文字列 | False |
| CRYPTO-E03 | 時刻ずれ超過でFalse返却 | 期限切れタイムスタンプ | False |
| CRYPTO-E04 | 不正なHMACハッシュ値でFalse返却 | 改ざんハッシュ | False |
| CRYPTO-E05 | 無効なIVサイズでValueError | 8バイトIV | ValueError |
| CRYPTO-E06 | 無効なPKCS7パディングでValueError | 不正パディング | ValueError |
| CRYPTO-E07 | 空の暗号化入力でValueError | 空文字列の暗号化データ＋IV | ValueError |
| CRYPTO-E08 | UTF-8デコード不可でValueError | 非UTF-8バイト列 | ValueError |
| CRYPTO-E09 | JSON解析失敗でValueError | 不正JSON文字列 | ValueError |
| CRYPTO-E10 | 不正なBase64データでValueError | 非Base64文字列 | ValueError |
| CRYPTO-E11 | auth_header=NoneでFalse返却 | None | False |
| CRYPTO-E12 | padded_dataがパディング長より短い | 短い暗号化データ | ValueError |
| CRYPTO-E13 | パディングバイト不一致でValueError | 値が不均一なパディング | ValueError |

### 3.1 _get_shared_secret 異常系

```python
class TestGetSharedSecretErrors:
    """共有秘密鍵取得エラーテスト"""

    def test_empty_secret_file_raises_error(self, tmp_path):
        """CRYPTO-E01: 鍵ファイルが空でValueError"""
        # Arrange
        empty_file = tmp_path / "empty_secret"
        empty_file.write_bytes(b"")

        env = os.environ.copy()
        env.pop("SHARED_SECRET", None)
        env["SHARED_SECRET_FILE"] = str(empty_file)

        # Act & Assert
        with patch.dict(os.environ, env, clear=True):
            from app.core.crypto import _get_shared_secret
            with pytest.raises(ValueError, match="共有鍵ファイルが空です"):
                _get_shared_secret()
```

### 3.2 verify_auth_hash 異常系

```python
class TestVerifyAuthHashErrors:
    """HMAC認証ハッシュ検証エラーテスト"""

    @pytest.fixture
    def test_shared_secret(self):
        return b"test_shared_secret_for_hmac"

    def test_invalid_format_returns_false(self, test_shared_secret):
        """CRYPTO-E02: 不正なHMAC形式でFalse返却"""
        # Arrange
        invalid_headers = [
            "INVALID-FORMAT",
            "SHARED-HMAC-notanumber-abc123",
            "SHARED-HMAC--abcdef",
            "",
            "Bearer token123",
        ]

        from app.core.crypto import verify_auth_hash

        # Act & Assert
        for header in invalid_headers:
            result = verify_auth_hash(header, "session-id", test_shared_secret)
            assert result is False, f"ヘッダー '{header}' でFalseが期待された"

    def test_expired_timestamp_returns_false(self, test_shared_secret):
        """CRYPTO-E03: 時刻ずれ超過でFalse返却"""
        # Arrange
        session_id = "test-session"
        old_timestamp = int(time.time()) - 1200  # 1200秒前（許容600秒超過）
        message = f"{session_id}:{old_timestamp}"
        hash_value = hmac.new(test_shared_secret, message.encode(), hashlib.sha256).hexdigest()
        auth_header = f"SHARED-HMAC-{old_timestamp}-{hash_value}"

        # Act
        from app.core.crypto import verify_auth_hash
        result = verify_auth_hash(auth_header, session_id, test_shared_secret)

        # Assert
        assert result is False

    def test_none_auth_header_returns_false(self, test_shared_secret):
        """CRYPTO-E11: auth_header=NoneでFalse返却

        verify_auth_hashにNoneを渡した場合、例外ではなくFalseを返すことを検証。
        実装のexcept節（crypto.py:103-105）の例外パスをカバーする。
        """
        from app.core.crypto import verify_auth_hash

        # Act
        result = verify_auth_hash(None, "session-id", test_shared_secret)

        # Assert
        assert result is False

    def test_tampered_hash_returns_false(self, test_shared_secret):
        """CRYPTO-E04: 不正なHMACハッシュ値でFalse返却"""
        # Arrange
        timestamp = int(time.time())
        tampered_hash = "a" * 64  # 改ざんされたハッシュ値

        auth_header = f"SHARED-HMAC-{timestamp}-{tampered_hash}"

        # Act
        from app.core.crypto import verify_auth_hash
        result = verify_auth_hash(auth_header, "session-id", test_shared_secret)

        # Assert
        assert result is False
```

### 3.3 decrypt_opensearch_dashboard_payload 異常系

```python
class TestDecryptPayloadErrors:
    """OSDペイロード復号エラーテスト"""

    @pytest.fixture
    def test_shared_secret(self):
        return b"test_shared_secret_key_123456789"

    def test_invalid_iv_size_raises_error(self, test_shared_secret):
        """CRYPTO-E05: 無効なIVサイズ（16バイト以外）でValueError"""
        # Arrange
        invalid_iv = base64.b64encode(b"short_iv").decode()  # 8バイト
        encrypted_data = base64.b64encode(b"dummy_encrypted_data_16").decode()

        # Act & Assert
        from app.core.crypto import decrypt_opensearch_dashboard_payload
        with pytest.raises(ValueError, match="無効なIVサイズ|復号に失敗"):
            decrypt_opensearch_dashboard_payload(encrypted_data, invalid_iv, test_shared_secret)

    def test_invalid_pkcs7_padding_raises_error(self, test_shared_secret):
        """CRYPTO-E06: 無効なPKCS7パディングでValueError"""
        # Arrange - パディングが不正なデータを暗号化
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend

        key = hashlib.sha256(test_shared_secret).digest()
        iv = os.urandom(16)

        # 不正なパディングのデータ（16バイトのブロック、最後のバイトが不正）
        bad_padded = b"invalid_padding!" # 16バイトだがパディングが不正
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(bad_padded) + encryptor.finalize()

        encrypted_data = base64.b64encode(ciphertext).decode()
        iv_b64 = base64.b64encode(iv).decode()

        # Act & Assert
        from app.core.crypto import decrypt_opensearch_dashboard_payload
        with pytest.raises(ValueError, match="復号に失敗"):
            decrypt_opensearch_dashboard_payload(encrypted_data, iv_b64, test_shared_secret)

    def test_empty_encrypted_input_raises_error(self, test_shared_secret):
        """CRYPTO-E07: 空の暗号化入力でValueError"""
        # 空文字列の暗号化データとIVを渡した場合のテスト
        from app.core.crypto import decrypt_opensearch_dashboard_payload

        # Act & Assert
        with pytest.raises(ValueError, match="復号に失敗"):
            decrypt_opensearch_dashboard_payload("", "", test_shared_secret)

    def test_non_utf8_decrypted_data_raises_error(self, test_shared_secret):
        """CRYPTO-E08: UTF-8デコード不可でValueError"""
        # Arrange - 正しくパディングされているが、UTF-8ではないバイト列
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives import padding as crypto_padding
        from cryptography.hazmat.backends import default_backend

        key = hashlib.sha256(test_shared_secret).digest()
        iv = os.urandom(16)

        # 不正なUTF-8バイト列にPKCS7パディングを適用
        non_utf8_data = bytes([0xFF, 0xFE, 0x80, 0x81, 0x82, 0x83, 0x84, 0x85])
        padder = crypto_padding.PKCS7(128).padder()
        padded = padder.update(non_utf8_data) + padder.finalize()

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded) + encryptor.finalize()

        encrypted_data = base64.b64encode(ciphertext).decode()
        iv_b64 = base64.b64encode(iv).decode()

        # Act & Assert
        from app.core.crypto import decrypt_opensearch_dashboard_payload
        with pytest.raises(ValueError, match="復号に失敗"):
            decrypt_opensearch_dashboard_payload(encrypted_data, iv_b64, test_shared_secret)

    def test_data_shorter_than_padding_length_raises_error(self, test_shared_secret):
        """CRYPTO-E12: padded_dataがパディング長より短いでValueError

        復号後データのサイズがパディング長より短い場合のエラーを検証。
        crypto.py:146-147 の分岐をカバーする。
        """
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        from app.core.crypto import decrypt_opensearch_dashboard_payload

        key = hashlib.sha256(test_shared_secret).digest()
        iv = os.urandom(16)

        # パディング値が実データ長より大きいデータ（例: 16バイト中最後が\x10=16）
        # これは正当なPKCS7「全バイトが\x10」と解釈される可能性があるため、
        # \x0F（15）にして15バイト分のパディングチェックで不一致を誘発
        bad_data = b"X" + b"\x0F" * 15  # 先頭1バイトが0x0Fでないため不一致
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(bad_data) + encryptor.finalize()

        encrypted_b64 = base64.b64encode(ciphertext).decode()
        iv_b64 = base64.b64encode(iv).decode()

        # Act & Assert
        with pytest.raises(ValueError, match="復号に失敗"):
            decrypt_opensearch_dashboard_payload(encrypted_b64, iv_b64, test_shared_secret)

    def test_inconsistent_padding_bytes_raises_error(self, test_shared_secret):
        """CRYPTO-E13: パディングバイト不一致でValueError

        パディング長は妥当（1〜16）だが、パディングバイトが不均一な場合のエラーを検証。
        crypto.py:149-152 の「無効なPKCS7パディング」分岐をカバーする。
        """
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        from app.core.crypto import decrypt_opensearch_dashboard_payload

        key = hashlib.sha256(test_shared_secret).digest()
        iv = os.urandom(16)

        # パディング長=3だが、パディングバイトが不均一: \x03\x03\x02
        bad_data = b"A" * 13 + b"\x03\x03\x02"
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(bad_data) + encryptor.finalize()

        encrypted_b64 = base64.b64encode(ciphertext).decode()
        iv_b64 = base64.b64encode(iv).decode()

        # Act & Assert
        with pytest.raises(ValueError, match="復号に失敗"):
            decrypt_opensearch_dashboard_payload(encrypted_b64, iv_b64, test_shared_secret)

    def test_invalid_json_after_decrypt_raises_error(self, test_shared_secret):
        """CRYPTO-E09: JSON解析失敗でValueError"""
        # Arrange - 有効なUTF-8だがJSON形式ではないデータ
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives import padding as crypto_padding
        from cryptography.hazmat.backends import default_backend

        key = hashlib.sha256(test_shared_secret).digest()
        iv = os.urandom(16)

        not_json = "this is not json data at all"
        padder = crypto_padding.PKCS7(128).padder()
        padded = padder.update(not_json.encode('utf-8')) + padder.finalize()

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded) + encryptor.finalize()

        encrypted_data = base64.b64encode(ciphertext).decode()
        iv_b64 = base64.b64encode(iv).decode()

        # Act & Assert
        from app.core.crypto import decrypt_opensearch_dashboard_payload
        with pytest.raises(ValueError, match="復号に失敗"):
            decrypt_opensearch_dashboard_payload(encrypted_data, iv_b64, test_shared_secret)
```

### 3.4 decrypt_credentials_field 異常系

```python
class TestDecryptCredentialsFieldErrors:
    """認証情報フィールド復号エラーテスト"""

    def test_invalid_base64_raises_error(self):
        """CRYPTO-E10: 不正なBase64データでValueError"""
        # Arrange
        invalid_base64 = "!!!not-valid-base64!!!"

        # Act & Assert
        from app.core.crypto import decrypt_credentials_field
        with pytest.raises(ValueError, match="復号化に失敗"):
            decrypt_credentials_field(invalid_base64)
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CRYPTO-SEC-01 | HMAC比較にhmac.compare_digest使用を検証 | ソースコード検査 | compare_digest使用 |
| CRYPTO-SEC-02 | タイムスタンプ改ざん検出 | 改ざんタイムスタンプ | False |
| CRYPTO-SEC-03 | パディングオラクル攻撃対策検証 | 不正パディング各種 | 一律同一メッセージのValueError（内部詳細なし） |
| CRYPTO-SEC-04 | デフォルト鍵使用時の警告出力確認 | ファイル未存在 | WARNING出力 |
| CRYPTO-SEC-05 | 1ビット異なるHMACハッシュでFalse | 微小改ざんハッシュ | False |
| CRYPTO-SEC-06 | エラーメッセージに内部詳細が含まれない | 各種復号エラー | 統一メッセージのみ |

```python
import inspect

@pytest.mark.security
class TestCryptoSecurity:
    """セキュリティテスト"""

    @pytest.fixture
    def test_shared_secret(self):
        return b"test_shared_secret_for_security"

    def test_hmac_uses_compare_digest(self):
        """CRYPTO-SEC-01: HMAC比較にhmac.compare_digest使用を検証（タイミング攻撃耐性）

        現在の実装は == 比較を使用しておりタイミング攻撃に脆弱。
        hmac.compare_digest() を使用するよう実装を修正する必要がある。

        【実装失敗予定】crypto.py:98 で == を使用しているため失敗する
        """
        # Arrange - verify_auth_hashのソースコードを検査
        from app.core.crypto import verify_auth_hash
        source = inspect.getsource(verify_auth_hash)

        # Assert - hmac.compare_digestが使用されていることを検証
        assert "compare_digest" in source, (
            "verify_auth_hash は hmac.compare_digest() を使用すべきです。"
            "== による文字列比較はタイミング攻撃に脆弱です。"
            "修正: received_hash == expected_hash → hmac.compare_digest(received_hash, expected_hash)"
        )

    def test_timestamp_tampering_detection(self, test_shared_secret):
        """CRYPTO-SEC-02: タイムスタンプ改ざん検出"""
        # Arrange - 正しいタイムスタンプでハッシュを生成し、タイムスタンプだけ変更
        session_id = "session-sec-02"
        original_timestamp = int(time.time())
        message = f"{session_id}:{original_timestamp}"
        hash_value = hmac.new(test_shared_secret, message.encode(), hashlib.sha256).hexdigest()

        # タイムスタンプを改ざん（ハッシュはそのまま）
        tampered_timestamp = original_timestamp + 1
        auth_header = f"SHARED-HMAC-{tampered_timestamp}-{hash_value}"

        # Act
        from app.core.crypto import verify_auth_hash
        result = verify_auth_hash(auth_header, session_id, test_shared_secret)

        # Assert
        assert result is False

    def test_padding_oracle_no_detail_leak(self, test_shared_secret):
        """CRYPTO-SEC-03: パディングオラクル攻撃対策 - エラーメッセージに内部詳細が含まれない

        異なる不正パディングパターンが全て完全に同一のエラーメッセージを返すことを検証。
        内部例外の詳細（パディング長、データ長など）がメッセージに含まれてはならない。

        【実装失敗予定】crypto.py:165 で元例外のstr(e)を含めているため、
        パターンごとに異なるメッセージになり失敗する
        """
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        from app.core.crypto import decrypt_opensearch_dashboard_payload

        key = hashlib.sha256(test_shared_secret).digest()

        # 異なる不正パディングパターンを用意
        bad_padding_patterns = [
            b"\x00" * 16,                  # パディング値が0
            b"A" * 15 + b"\x11",           # パディング値が17（>16）
            b"A" * 14 + b"\x02\x01",       # 不一致パディング
        ]

        errors = []
        for pattern in bad_padding_patterns:
            iv = os.urandom(16)
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(pattern) + encryptor.finalize()

            encrypted_b64 = base64.b64encode(ciphertext).decode()
            iv_b64 = base64.b64encode(iv).decode()

            with pytest.raises(ValueError) as exc_info:
                decrypt_opensearch_dashboard_payload(encrypted_b64, iv_b64, test_shared_secret)
            errors.append(str(exc_info.value))

        # 全てのエラーメッセージが完全に同一であること（詳細漏洩なし）
        unique_messages = set(errors)
        assert len(unique_messages) == 1, (
            f"パディングオラクル情報漏洩: 異なるエラーパターンで異なるメッセージが返されています。\n"
            f"検出されたメッセージ: {unique_messages}\n"
            f"修正: 復号失敗時は一律同一のメッセージを返すこと"
        )
        # かつ内部詳細が含まれないこと
        error_msg = errors[0]
        assert "パディング" not in error_msg, (
            f"エラーメッセージにパディング詳細が含まれています: {error_msg}"
        )

    def test_default_key_warning_output(self, capsys):
        """CRYPTO-SEC-04: デフォルト鍵使用時の警告出力確認"""
        # Arrange
        env = os.environ.copy()
        env.pop("SHARED_SECRET", None)
        env.pop("SHARED_SECRET_FILE", None)

        # Act
        with patch.dict(os.environ, env, clear=True):
            with patch("os.path.exists", return_value=False):
                from app.core.crypto import _get_shared_secret
                _get_shared_secret()

        # Assert
        captured = capsys.readouterr()
        assert "WARNING" in captured.out
        assert "デフォルト開発用共有鍵" in captured.out

    def test_hmac_single_bit_difference(self, test_shared_secret):
        """CRYPTO-SEC-05: 1ビット異なるHMACハッシュでFalse"""
        # Arrange
        session_id = "session-sec-05"
        timestamp = int(time.time())
        message = f"{session_id}:{timestamp}"
        correct_hash = hmac.new(test_shared_secret, message.encode(), hashlib.sha256).hexdigest()

        # 1ビットだけ異なるハッシュを生成
        tampered_hash = list(correct_hash)
        tampered_hash[-1] = 'a' if tampered_hash[-1] != 'a' else 'b'
        tampered_hash = ''.join(tampered_hash)

        auth_header = f"SHARED-HMAC-{timestamp}-{tampered_hash}"

        # Act
        from app.core.crypto import verify_auth_hash
        result = verify_auth_hash(auth_header, session_id, test_shared_secret)

        # Assert
        assert result is False

    def test_error_message_no_internal_details(self, test_shared_secret):
        """CRYPTO-SEC-06: エラーメッセージに内部詳細が含まれない

        復号失敗時のエラーメッセージに、攻撃者に有用な内部情報
        （パディング長、データサイズ、具体的な失敗箇所）が含まれないことを検証。

        【実装失敗予定】crypto.py:165 で f"...{str(e)}" としており内部詳細が漏洩する
        """
        from app.core.crypto import decrypt_opensearch_dashboard_payload
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend

        key = hashlib.sha256(test_shared_secret).digest()
        iv = os.urandom(16)

        # パディング長が不正なデータ（17 > 16）
        bad_data = b"A" * 15 + b"\x11"
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(bad_data) + encryptor.finalize()

        encrypted_b64 = base64.b64encode(ciphertext).decode()
        iv_b64 = base64.b64encode(iv).decode()

        with pytest.raises(ValueError) as exc_info:
            decrypt_opensearch_dashboard_payload(encrypted_b64, iv_b64, test_shared_secret)

        error_msg = str(exc_info.value)

        # 内部詳細キーワードが含まれていないことを検証
        internal_detail_keywords = ["パディング長", "データ長", "バイト"]
        for keyword in internal_detail_keywords:
            assert keyword not in error_msg, (
                f"エラーメッセージに内部詳細 '{keyword}' が含まれています: {error_msg}\n"
                f"修正: 復号失敗時は 'OpenSearchダッシュボード復号に失敗しました' のみ返すこと"
            )
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ |
|--------------|------|---------|
| `test_shared_secret` | テスト用共有秘密鍵（bytes） | function |
| `encrypted_payload` | テスト用暗号化ペイロード（IV付き） | function |
| `tmp_path` | pytest組み込み（一時ディレクトリ） | function |
| `capsys` | pytest組み込み（stdout/stderrキャプチャ） | function |

### 共通フィクスチャ定義

```python
# test/unit/core/conftest.py に追加
import os
import pytest
from unittest.mock import patch

@pytest.fixture
def test_shared_secret():
    """テスト用共有秘密鍵"""
    return b"test_shared_secret_for_hmac"

@pytest.fixture
def mock_env_shared_secret():
    """環境変数SHARED_SECRETモック"""
    with patch.dict(os.environ, {"SHARED_SECRET": "env_secret_key"}):
        yield "env_secret_key"

@pytest.fixture
def mock_secret_file(tmp_path):
    """秘密鍵ファイルモック"""
    secret_file = tmp_path / "shared_secret"
    secret_file.write_bytes(b"file_secret_key_12345")
    return str(secret_file)
```

---

## 6. テスト実行例

```bash
# crypto関連テストのみ実行
pytest test/unit/core/test_crypto.py -v

# 特定のテストクラスのみ実行
pytest test/unit/core/test_crypto.py::TestGetSharedSecret -v
pytest test/unit/core/test_crypto.py::TestVerifyAuthHash -v
pytest test/unit/core/test_crypto.py::TestDecryptOpensearchDashboardPayload -v
pytest test/unit/core/test_crypto.py::TestCryptoSecurity -v

# カバレッジ付きで実行
pytest test/unit/core/test_crypto.py --cov=app.core.crypto --cov-report=term-missing -v

# セキュリティマーカーで実行（pytest.iniまたはpyproject.tomlにマーカー登録が必要）
# [tool.pytest.ini_options]
# markers = ["security: セキュリティ関連テスト"]
pytest test/unit/core/test_crypto.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 10 | CRYPTO-001 〜 CRYPTO-010 |
| 異常系 | 13 | CRYPTO-E01 〜 CRYPTO-E13 |
| セキュリティ | 6 | CRYPTO-SEC-01 〜 CRYPTO-SEC-06 |
| **合計** | **29** | - |

### 実装失敗が予想されるテスト

以下のテストは現在の `crypto.py` の実装では**意図的に失敗**します。
実装側の修正が必要です。

| テストID | 失敗理由 | 修正方針 |
|---------|---------|---------|
| CRYPTO-SEC-01 | `verify_auth_hash`で`==`比較を使用（`crypto.py:98`） | `hmac.compare_digest()`に変更 |
| CRYPTO-SEC-03 | 復号エラー時に`str(e)`で内部詳細が漏洩（`crypto.py:165`） | 固定メッセージのみ返すよう修正 |
| CRYPTO-SEC-06 | 同上 - パディング長等の内部情報がエラーに含まれる | 同上 |
