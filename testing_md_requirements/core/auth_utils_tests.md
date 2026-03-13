# auth_utils テストケース

## 1. 概要

認証に関するユーティリティ関数のテストケースを定義します。
Basic認証トークンの抽出、認証要件の検証、デバッグログ出力機能を提供します。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `extract_basic_auth_token()` | Authorizationヘッダーからbasic認証トークンを抽出 |
| `validate_auth_requirements()` | 認証要件を検証し、正規化された認証情報を返す |
| `log_auth_debug_info()` | 認証関連のデバッグ情報をログ出力 |

### 1.2 カバレッジ目標: 90%

> **注記**: 認証関連のユーティリティ関数であり、セキュリティ上重要なため高いカバレッジを目標とします。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/core/auth_utils.py` |
| テストコード | `test/unit/core/test_auth_utils.py` |

### 1.4 補足情報

**主要分岐:**

| 行番号 | 条件 | 分岐内容 |
|--------|------|----------|
| 32 | `not auth_value and request` | リクエストから認証ヘッダー取得 |
| 38 | `not auth_value` | 認証ヘッダーなしでHTTPException |
| 46 | `auth_value.startswith("Basic ")` | "Basic " プレフィックス除去（スペースあり） |
| 50 | `auth_value.startswith("Basic")` | "Basic" プレフィックス除去（スペースなし） |
| 54 | `auth_value.startswith("SHARED-HMAC")` | SHARED-HMAC形式をそのまま返却 |
| 58 | else | 無効な形式でHTTPException |
| 83 | `not endpoint_auth` | エンドポイント認証なしでHTTPException |
| 113 | `request_headers and logger.isEnabledFor(logging.DEBUG)` | ヘッダーフィルタリング |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| AUTIL-INIT | モジュールインポート成功 | モジュールインポート | 例外なし |
| AUTIL-001 | Basic認証トークン抽出（スペースあり） | `"Basic dXNlcjpwYXNz"` | `"dXNlcjpwYXNz"` |
| AUTIL-002 | Basic認証トークン抽出（スペースなし） | `"BasicdXNlcjpwYXNz"` | `"dXNlcjpwYXNz"` |
| AUTIL-003 | SHARED-HMAC認証ヘッダー受け入れ | `"SHARED-HMAC-123-abc"` | `"SHARED-HMAC-123-abc"` |
| AUTIL-004 | リクエストオブジェクトからヘッダー取得 | `request.headers["authorization"]` | トークン抽出成功 |
| AUTIL-005 | リクエストオブジェクトからヘッダー取得（大文字） | `request.headers["Authorization"]` | トークン抽出成功 |
| AUTIL-006 | 認証要件検証成功（OpenSearchあり） | `(token, os_auth)` | `(token, os_auth)` |
| AUTIL-007 | 認証要件検証成功（OpenSearchなし） | `(token, None)` | `(token, None)` |
| AUTIL-007-B | opensearch_auth引数省略時はNone | `endpoint_auth` のみ | `(token, None)` |
| AUTIL-008 | デバッグログ出力（両認証あり） | `session_id, True, True` | ログ出力成功 |
| AUTIL-009 | デバッグログ出力（ヘッダーフィルタリング） | `request_headers` 指定 | 認証ヘッダー部分マスク |
| AUTIL-010 | デバッグログ出力（認証なし） | `session_id, False, False` | ログ出力成功 |
| AUTIL-010-B | リクエストヘッダーなしでのログ出力 | `request_headers=None` | ヘッダーログなし |
| AUTIL-011 | DEBUGレベル無効時のログ出力 | `logging.INFO`, ヘッダーあり | ヘッダー出力なし |

### 2.1 extract_basic_auth_token テスト

```python
# test/unit/core/test_auth_utils.py
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException


class TestExtractBasicAuthToken:
    """Basic認証トークン抽出テスト"""

    def test_import_module(self):
        """AUTIL-INIT: モジュールのインポート成功"""
        # Arrange & Act
        from app.core import auth_utils

        # Assert
        assert hasattr(auth_utils, "extract_basic_auth_token")
        assert hasattr(auth_utils, "validate_auth_requirements")
        assert hasattr(auth_utils, "log_auth_debug_info")

    def test_extract_basic_token_with_space(self):
        """AUTIL-001: Basic認証トークン抽出（スペースあり）

        auth_utils.py:46-49 の分岐をカバーする。
        """
        # Arrange
        from app.core.auth_utils import extract_basic_auth_token
        auth_header = "Basic dXNlcjpwYXNz"

        # Act
        result = extract_basic_auth_token(authorization_header=auth_header)

        # Assert
        assert result == "dXNlcjpwYXNz"

    def test_extract_basic_token_without_space(self):
        """AUTIL-002: Basic認証トークン抽出（スペースなし）

        auth_utils.py:50-53 の分岐をカバーする。
        """
        # Arrange
        from app.core.auth_utils import extract_basic_auth_token
        auth_header = "BasicdXNlcjpwYXNz"

        # Act
        result = extract_basic_auth_token(authorization_header=auth_header)

        # Assert
        assert result == "dXNlcjpwYXNz"

    def test_extract_shared_hmac_token(self):
        """AUTIL-003: SHARED-HMAC認証ヘッダー受け入れ

        auth_utils.py:54-57 の分岐をカバーする。
        """
        # Arrange
        from app.core.auth_utils import extract_basic_auth_token
        auth_header = "SHARED-HMAC-1234567890-abcdef123456"

        # Act
        result = extract_basic_auth_token(authorization_header=auth_header)

        # Assert
        assert result == "SHARED-HMAC-1234567890-abcdef123456"

    def test_extract_from_request_lowercase(self):
        """AUTIL-004: リクエストオブジェクトからヘッダー取得（小文字）

        auth_utils.py:32-36 の分岐をカバーする。
        """
        # Arrange
        from app.core.auth_utils import extract_basic_auth_token

        # FastAPIのHeadersオブジェクトを模倣
        mock_headers = MagicMock()
        mock_headers.get = lambda key: (
            "Basic dXNlcjpwYXNz" if key == "authorization" else None
        )

        mock_request = MagicMock()
        mock_request.headers = mock_headers

        # Act
        result = extract_basic_auth_token(authorization_header=None, request=mock_request)

        # Assert
        assert result == "dXNlcjpwYXNz"

    def test_extract_from_request_uppercase(self):
        """AUTIL-005: リクエストオブジェクトからヘッダー取得（大文字）

        auth_utils.py:34-35 の Authorization（大文字）フォールバックをカバーする。

        実装は `request.headers.get("authorization") or request.headers.get("Authorization")`
        という or 演算子で繋がれているため、小文字が None/空文字の場合のみ
        大文字にフォールバックする。このテストでは小文字で None を返すことで
        フォールバック動作を検証している。
        """
        # Arrange
        from app.core.auth_utils import extract_basic_auth_token

        mock_headers = MagicMock()
        # 小文字では見つからず（None）、大文字で見つかるケース → フォールバック検証
        def get_header(key):
            if key == "Authorization":
                return "Basic dXNlcjpwYXNz"
            return None  # "authorization" は None を返す
        mock_headers.get = get_header

        mock_request = MagicMock()
        mock_request.headers = mock_headers

        # Act
        result = extract_basic_auth_token(authorization_header=None, request=mock_request)

        # Assert
        assert result == "dXNlcjpwYXNz"
```

### 2.2 validate_auth_requirements テスト

```python
class TestValidateAuthRequirements:
    """認証要件検証テスト"""

    def test_validate_with_opensearch_auth(self):
        """AUTIL-006: 認証要件検証成功（OpenSearchあり）"""
        # Arrange
        from app.core.auth_utils import validate_auth_requirements
        endpoint_auth = "test_token"
        opensearch_auth = "opensearch_credentials"

        # Act
        result = validate_auth_requirements(endpoint_auth, opensearch_auth)

        # Assert
        assert result == ("test_token", "opensearch_credentials")

    def test_validate_without_opensearch_auth(self):
        """AUTIL-007: 認証要件検証成功（OpenSearchなし）"""
        # Arrange
        from app.core.auth_utils import validate_auth_requirements
        endpoint_auth = "test_token"

        # Act
        result = validate_auth_requirements(endpoint_auth, None)

        # Assert
        assert result == ("test_token", None)

    def test_validate_opensearch_auth_default_none(self):
        """AUTIL-007-B: opensearch_auth引数省略時はNone"""
        # Arrange
        from app.core.auth_utils import validate_auth_requirements
        endpoint_auth = "test_token"

        # Act
        result = validate_auth_requirements(endpoint_auth)

        # Assert
        assert result == ("test_token", None)
```

### 2.3 log_auth_debug_info テスト

```python
class TestLogAuthDebugInfo:
    """認証デバッグログ出力テスト"""

    def test_log_with_both_auth(self, caplog):
        """AUTIL-008: デバッグログ出力（両認証あり）"""
        # Arrange
        from app.core.auth_utils import log_auth_debug_info
        import logging
        caplog.set_level(logging.DEBUG)

        # Act
        log_auth_debug_info(
            session_id="session-123",
            has_endpoint_auth=True,
            has_opensearch_auth=True
        )

        # Assert
        assert "session-123" in caplog.text
        assert "エンドポイント認証: あり" in caplog.text
        assert "OpenSearch認証: あり" in caplog.text

    def test_log_with_header_filtering(self, caplog):
        """AUTIL-009: デバッグログ出力（ヘッダーフィルタリング）

        auth_utils.py:113-120 の分岐をカバーする。
        認証ヘッダーは部分的にマスクされることを検証。
        """
        # Arrange
        from app.core.auth_utils import log_auth_debug_info
        import logging
        caplog.set_level(logging.DEBUG)

        request_headers = {
            "authorization": "Basic dXNlcjpwYXNzd29yZA==",
            "x-auth-hash": "SHARED-HMAC-12345-abcdef",
            "content-type": "application/json"
        }

        # Act
        log_auth_debug_info(
            session_id="session-456",
            has_endpoint_auth=True,
            has_opensearch_auth=False,
            request_headers=request_headers
        )

        # Assert
        log_text = caplog.text
        assert "session-456" in log_text
        # 認証ヘッダーはマスクされているはず
        assert "dXNlcjpwYXNzd29yZA==" not in log_text
        assert "SHARED-HMAC-12345-abcdef" not in log_text
        # content-typeはそのまま出力
        assert "application/json" in log_text

    def test_log_without_auth(self, caplog):
        """AUTIL-010: デバッグログ出力（認証なし）"""
        # Arrange
        from app.core.auth_utils import log_auth_debug_info
        import logging
        caplog.set_level(logging.DEBUG)

        # Act
        log_auth_debug_info(
            session_id="session-789",
            has_endpoint_auth=False,
            has_opensearch_auth=False
        )

        # Assert
        assert "session-789" in caplog.text
        assert "エンドポイント認証: なし" in caplog.text
        assert "OpenSearch認証: なし" in caplog.text

    def test_log_without_request_headers(self, caplog):
        """AUTIL-010-B: リクエストヘッダーなしでのログ出力"""
        # Arrange
        from app.core.auth_utils import log_auth_debug_info
        import logging
        caplog.set_level(logging.DEBUG)

        # Act
        log_auth_debug_info(
            session_id="session-abc",
            has_endpoint_auth=True,
            has_opensearch_auth=True,
            request_headers=None
        )

        # Assert
        assert "session-abc" in caplog.text
        assert "リクエストヘッダー" not in caplog.text  # ヘッダーログは出力されない

    def test_log_without_debug_level(self, caplog):
        """AUTIL-011: DEBUGレベル無効時のログ出力

        auth_utils.py:113 で logger.isEnabledFor(logging.DEBUG) が False の場合をカバー。
        ヘッダーフィルタリング処理がスキップされることを検証。
        """
        # Arrange
        from app.core.auth_utils import log_auth_debug_info
        import logging
        caplog.set_level(logging.INFO)  # DEBUG無効

        request_headers = {
            "authorization": "Basic dXNlcjpwYXNz",
            "content-type": "application/json"
        }

        # Act
        log_auth_debug_info(
            session_id="session-xyz",
            has_endpoint_auth=True,
            has_opensearch_auth=True,
            request_headers=request_headers
        )

        # Assert
        log_text = caplog.text
        assert "session-xyz" in log_text
        # DEBUGレベルが無効なので、リクエストヘッダーは出力されない
        assert "リクエストヘッダー" not in log_text
        assert "dXNlcjpwYXNz" not in log_text
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| AUTIL-E01 | 認証ヘッダーなしでHTTPException | `None`, `None` | HTTPException 401 |
| AUTIL-E02 | 無効な認証形式でHTTPException | `"Bearer token"` | HTTPException 401 |
| AUTIL-E03 | 空文字の認証ヘッダーでHTTPException | `""` | HTTPException 401 |
| AUTIL-E04 | エンドポイント認証なしでHTTPException | `None`, `os_auth` | HTTPException 401 |
| AUTIL-E05 | 空文字のエンドポイント認証でHTTPException | `""` | HTTPException 401 |
| AUTIL-E06 | リクエストからもヘッダー取得失敗 | `request.headers` 空 | HTTPException 401 |
| AUTIL-E07 | 小文字basicプレフィックスでHTTPException | `"basic token"` | HTTPException 401 |

### 3.1 extract_basic_auth_token 異常系

```python
class TestExtractBasicAuthTokenErrors:
    """Basic認証トークン抽出エラーテスト"""

    def test_no_auth_header_raises_http_exception(self):
        """AUTIL-E01: 認証ヘッダーなしでHTTPException

        auth_utils.py:38-43 の分岐をカバーする。
        """
        # Arrange
        from app.core.auth_utils import extract_basic_auth_token

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            extract_basic_auth_token(authorization_header=None, request=None)

        assert exc_info.value.status_code == 401
        assert "認証が必要です" in exc_info.value.detail

    def test_invalid_auth_format_raises_http_exception(self):
        """AUTIL-E02: 無効な認証形式でHTTPException

        auth_utils.py:58-63 の分岐をカバーする。
        """
        # Arrange
        from app.core.auth_utils import extract_basic_auth_token

        invalid_headers = [
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "Digest username=test",
            "OAuth oauth_consumer_key=xxx",
            "CustomAuth token123",
        ]

        # Act & Assert
        for header in invalid_headers:
            with pytest.raises(HTTPException) as exc_info:
                extract_basic_auth_token(authorization_header=header)

            assert exc_info.value.status_code == 401
            assert "認証形式が不正です" in exc_info.value.detail

    def test_empty_auth_header_raises_http_exception(self):
        """AUTIL-E03: 空文字の認証ヘッダーでHTTPException

        auth_utils.py:38 の `if not auth_value` は空文字 "" も falsy として
        True を返すため、このテストケースでカバーされる。
        """
        # Arrange
        from app.core.auth_utils import extract_basic_auth_token

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            extract_basic_auth_token(authorization_header="")

        assert exc_info.value.status_code == 401
        assert "認証が必要です" in exc_info.value.detail

    def test_request_without_auth_header_raises_http_exception(self):
        """AUTIL-E06: リクエストからもヘッダー取得失敗でHTTPException"""
        # Arrange
        from app.core.auth_utils import extract_basic_auth_token

        mock_headers = MagicMock()
        mock_headers.get = lambda key: None  # 常にNoneを返す

        mock_request = MagicMock()
        mock_request.headers = mock_headers

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            extract_basic_auth_token(authorization_header=None, request=mock_request)

        assert exc_info.value.status_code == 401
        assert "認証が必要です" in exc_info.value.detail

    def test_lowercase_basic_prefix_raises_http_exception(self):
        """AUTIL-E07: 小文字basicプレフィックスでHTTPException

        実装の .startswith("Basic") は大文字小文字を区別するため、
        小文字の "basic" は認識されず HTTPException が発生する。
        HTTPヘッダーは一般に大文字小文字を区別しないが、Basic認証の
        プレフィックスは RFC 7617 で "Basic" と定義されている。
        """
        # Arrange
        from app.core.auth_utils import extract_basic_auth_token

        lowercase_headers = [
            "basic dXNlcjpwYXNz",  # 小文字 + スペースあり
            "basicdXNlcjpwYXNz",   # 小文字 + スペースなし
            "BASIC dXNlcjpwYXNz",  # 大文字 + スペースあり
        ]

        # Act & Assert
        for header in lowercase_headers:
            with pytest.raises(HTTPException) as exc_info:
                extract_basic_auth_token(authorization_header=header)

            assert exc_info.value.status_code == 401
            assert "認証形式が不正です" in exc_info.value.detail
```

### 3.2 validate_auth_requirements 異常系

```python
class TestValidateAuthRequirementsErrors:
    """認証要件検証エラーテスト"""

    def test_no_endpoint_auth_raises_http_exception(self):
        """AUTIL-E04: エンドポイント認証なしでHTTPException

        auth_utils.py:83-88 の分岐をカバーする。
        """
        # Arrange
        from app.core.auth_utils import validate_auth_requirements

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            validate_auth_requirements(endpoint_auth=None, opensearch_auth="os_auth")

        assert exc_info.value.status_code == 401
        assert "認証トークンが必要です" in exc_info.value.detail

    def test_empty_endpoint_auth_raises_http_exception(self):
        """AUTIL-E05: 空文字のエンドポイント認証でHTTPException"""
        # Arrange
        from app.core.auth_utils import validate_auth_requirements

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            validate_auth_requirements(endpoint_auth="", opensearch_auth="os_auth")

        assert exc_info.value.status_code == 401
        assert "認証トークンが必要です" in exc_info.value.detail
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| AUTIL-SEC-01 | 認証ヘッダーがログに完全出力されない | Basic認証ヘッダー | 部分マスク出力 |
| AUTIL-SEC-02 | エラーメッセージに認証情報が含まれない | 無効な認証ヘッダー | 認証情報非露出 |
| AUTIL-SEC-03 | x-auth-hashヘッダーがログにマスクされる | SHARED-HMACヘッダー | 部分マスク出力 |
| AUTIL-SEC-04 | 空ヘッダー値でのフィルタリング安全性 | 空文字/None値 | 例外なし |
| AUTIL-SEC-05 | 短い認証ヘッダー値のフィルタリング | 10文字未満のトークン | 安全なスライス処理 |

```python
@pytest.mark.security
class TestAuthUtilsSecurity:
    """認証ユーティリティセキュリティテスト"""

    def test_auth_header_not_fully_logged(self, caplog):
        """AUTIL-SEC-01: 認証ヘッダーがログに完全出力されない

        auth_utils.py:117-118 でauthorizationヘッダーがマスクされることを検証。
        """
        # Arrange
        from app.core.auth_utils import log_auth_debug_info
        import logging
        caplog.set_level(logging.DEBUG)

        secret_token = "dXNlcjpzdXBlcl9zZWNyZXRfcGFzc3dvcmQ="  # user:super_secret_password
        request_headers = {
            "authorization": f"Basic {secret_token}",
            "content-type": "application/json"
        }

        # Act
        log_auth_debug_info(
            session_id="sec-test-01",
            has_endpoint_auth=True,
            has_opensearch_auth=False,
            request_headers=request_headers
        )

        # Assert
        log_text = caplog.text
        # 完全なトークンが出力されていないことを検証
        assert secret_token not in log_text
        assert "super_secret_password" not in log_text
        # 部分マスク（先頭10文字 + "..."）が出力されていることを検証
        assert "..." in log_text

    def test_error_message_does_not_expose_credentials(self):
        """AUTIL-SEC-02: エラーメッセージに認証情報が含まれない

        auth_utils.py:59-63 でエラーメッセージに認証情報の詳細が含まれないことを検証。
        """
        # Arrange
        from app.core.auth_utils import extract_basic_auth_token

        # 攻撃者が送信する可能性のある様々な認証ヘッダー
        malicious_headers = [
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.secret_payload",
            "CustomAuth user:password123",
            "Token sensitive_api_key_12345",
        ]

        for header in malicious_headers:
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                extract_basic_auth_token(authorization_header=header)

            error_detail = exc_info.value.detail
            # エラーメッセージに送信された認証情報が含まれていないことを検証
            assert "secret_payload" not in error_detail
            assert "password123" not in error_detail
            assert "sensitive_api_key_12345" not in error_detail
            # 一般的なエラーメッセージのみ
            assert "認証形式が不正です" in error_detail

    def test_x_auth_hash_header_masked(self, caplog):
        """AUTIL-SEC-03: x-auth-hashヘッダーがログにマスクされる

        auth_utils.py:117 で x-auth-hash ヘッダーもマスクされることを検証。
        """
        # Arrange
        from app.core.auth_utils import log_auth_debug_info
        import logging
        caplog.set_level(logging.DEBUG)

        hmac_value = "SHARED-HMAC-1234567890-abcdef123456789012345678901234567890"
        request_headers = {
            "x-auth-hash": hmac_value,
            "content-type": "application/json"
        }

        # Act
        log_auth_debug_info(
            session_id="sec-test-03",
            has_endpoint_auth=True,
            has_opensearch_auth=True,
            request_headers=request_headers
        )

        # Assert
        log_text = caplog.text
        # 完全なHMAC値が出力されていないことを検証
        assert hmac_value not in log_text
        assert "abcdef123456789012345678901234567890" not in log_text

    def test_empty_header_value_filtering_safe(self, caplog):
        """AUTIL-SEC-04: 空ヘッダー値でのフィルタリング安全性

        auth_utils.py:118 で value が空文字やNoneの場合に例外が発生しないことを検証。
        三項演算子 `if value` が正しく機能することを確認。
        """
        # Arrange
        from app.core.auth_utils import log_auth_debug_info
        import logging
        caplog.set_level(logging.DEBUG)

        request_headers = {
            "authorization": "",  # 空文字
            "x-auth-hash": None,  # None
            "content-type": "application/json"
        }

        # Act - 例外が発生しないことを検証
        log_auth_debug_info(
            session_id="sec-test-04",
            has_endpoint_auth=False,
            has_opensearch_auth=False,
            request_headers=request_headers
        )

        # Assert
        log_text = caplog.text
        assert "sec-test-04" in log_text
        # 空文字/Noneは falsy なので、value[:10] は実行されず None として処理される
        # ログに空文字や None のスライス結果が出力されていないことを確認
        assert "'authorization': None" in log_text or "'authorization': ''" in log_text
        # content-type は通常通り出力される
        assert "application/json" in log_text

    def test_short_auth_header_filtering(self, caplog):
        """AUTIL-SEC-05: 短い認証ヘッダー値のフィルタリング

        auth_utils.py:118 で value が10文字未満の場合に安全にスライスされることを検証。
        Pythonのスライスは範囲外でもエラーにならないが、動作を明示的に確認。
        """
        # Arrange
        from app.core.auth_utils import log_auth_debug_info
        import logging
        caplog.set_level(logging.DEBUG)

        short_token = "abc"  # 3文字
        request_headers = {
            "authorization": short_token,
            "content-type": "application/json"
        }

        # Act
        log_auth_debug_info(
            session_id="sec-test-05",
            has_endpoint_auth=True,
            has_opensearch_auth=False,
            request_headers=request_headers
        )

        # Assert
        log_text = caplog.text
        assert "sec-test-05" in log_text
        # 短いトークンは "abc..." として出力される（スライス + "..."）
        assert "abc..." in log_text
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `caplog` | pytest組み込み（ログキャプチャ） | function | No |

### 共通フィクスチャ定義

```python
# test/unit/core/conftest.py に追加（既存のものと統合）
import sys
import pytest
from unittest.mock import MagicMock


@pytest.fixture(autouse=True)
def reset_auth_utils_module():
    """テストごとにauth_utilsモジュールの状態をリセット

    auth_utils.py 自体にモジュールレベルの状態はないが、
    以下の理由でモジュールキャッシュをクリアする:
    1. テスト間の独立性を保証
    2. loggerインスタンスのハンドラー状態をリセット
    3. 将来的にモジュールレベル変数が追加された場合の安全策

    対象は `app.core.auth_utils` に限定し、副作用を防止する。
    """
    yield
    # テスト後にモジュールキャッシュをクリア（対象を限定）
    if "app.core.auth_utils" in sys.modules:
        del sys.modules["app.core.auth_utils"]


@pytest.fixture
def mock_request_with_auth():
    """認証ヘッダー付きリクエストモック"""
    mock_headers = MagicMock()
    mock_headers.get = lambda key: (
        "Basic dXNlcjpwYXNz" if key.lower() == "authorization" else None
    )

    mock_request = MagicMock()
    mock_request.headers = mock_headers
    return mock_request


@pytest.fixture
def mock_request_without_auth():
    """認証ヘッダーなしリクエストモック"""
    mock_headers = MagicMock()
    mock_headers.get = lambda key: None

    mock_request = MagicMock()
    mock_request.headers = mock_headers
    return mock_request
```

---

## 6. テスト実行例

```bash
# auth_utils関連テストのみ実行
pytest test/unit/core/test_auth_utils.py -v

# 特定のテストクラスのみ実行
pytest test/unit/core/test_auth_utils.py::TestExtractBasicAuthToken -v
pytest test/unit/core/test_auth_utils.py::TestValidateAuthRequirements -v
pytest test/unit/core/test_auth_utils.py::TestLogAuthDebugInfo -v
pytest test/unit/core/test_auth_utils.py::TestAuthUtilsSecurity -v

# カバレッジ付きで実行
pytest test/unit/core/test_auth_utils.py --cov=app.core.auth_utils --cov-report=term-missing -v

# セキュリティマーカーで実行
# pyproject.toml: markers = ["security: セキュリティ関連テスト"]
pytest test/unit/core/test_auth_utils.py -m "security" -v

# 異常系テストのみ実行
pytest test/unit/core/test_auth_utils.py -k "Error" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 14 | AUTIL-INIT, AUTIL-001〜007, AUTIL-007-B, AUTIL-008〜010, AUTIL-010-B, AUTIL-011 |
| 異常系 | 7 | AUTIL-E01 〜 AUTIL-E07 |
| セキュリティ | 5 | AUTIL-SEC-01 〜 AUTIL-SEC-05 |
| **合計** | **26** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestExtractBasicAuthToken` | AUTIL-INIT, AUTIL-001〜AUTIL-005 | 6 |
| `TestValidateAuthRequirements` | AUTIL-006, AUTIL-007, AUTIL-007-B | 3 |
| `TestLogAuthDebugInfo` | AUTIL-008〜AUTIL-010, AUTIL-010-B, AUTIL-011 | 5 |
| `TestExtractBasicAuthTokenErrors` | AUTIL-E01〜AUTIL-E03, AUTIL-E06〜AUTIL-E07 | 5 |
| `TestValidateAuthRequirementsErrors` | AUTIL-E04〜AUTIL-E05 | 2 |
| `TestAuthUtilsSecurity` | AUTIL-SEC-01〜AUTIL-SEC-05 | 5 |

### 実装失敗が予想されるテスト

現時点で失敗が予想されるテストはありません。

### 注意事項

- `@pytest.mark.security` マーカーを `pyproject.toml` に登録してください
- ログ検証テストは `caplog` フィクスチャを使用します
- FastAPIの `HTTPException` をインポートする必要があります

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | 実際のFastAPIリクエストオブジェクトではなくモック使用 | 統合動作は未検証 | 統合テストで補完 |
| 2 | ログレベル依存のテスト | DEBUG無効時はヘッダーフィルタリング未実行 | テスト時はDEBUG有効化 |
| 3 | 認証ヘッダーのマスク長（10文字）はハードコード | 変更時テスト修正必要 | 定数化を推奨 |
