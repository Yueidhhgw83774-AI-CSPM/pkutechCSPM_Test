# -*- coding: utf-8 -*-
"""
auth_utils.py のテスト。
テスト対象: app/core/auth_utils.py
テスト仕様: auth_utils_tests.md
カバレッジ目標: 90%
このテストファイルは auth_utils_tests.md 仕様書に従って記述されており、
正常系テスト、異常系テスト、セキュリティテストの3カテゴリを含む。
テスト命名規則:
- 正常系: test_<function>_<description>  (AUTIL-INIT, AUTIL-001 ~ AUTIL-011)
- 異常系: test_<function>_<error_description>  (AUTIL-E01 ~ AUTIL-E07)
- セキュリティテスト: test_<security_aspect>  (AUTIL-SEC-01 ~ AUTIL-SEC-05)
"""
import os
import re
import sys
import time
import logging
from pathlib import Path
from unittest.mock import MagicMock
import pytest

# ─── SourceCodeRoot を .env から読み込む ────────────────────────────────
def _load_source_root() -> str:
    """プロジェクトルートの .env から SourceCodeRoot を読み込む。"""
    # 優先度1: ルート conftest.py が os.environ に設定済みの場合
    from_env = os.environ.get("SourceCodeRoot", "").strip().strip("'\"")
    if from_env:
        return from_env
    # 優先度2: ディレクトリツリーを遡って .env ファイルを検索する
    current = Path(__file__).resolve()
    for directory in [current, *current.parents]:
        env_file = (directory if directory.is_dir() else directory.parent) / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                m = re.match(r"^\s*SourceCodeRoot\s*=\s*['\"]?(.+?)['\"]?\s*$", line)
                if m:
                    return m.group(1).strip()
    return ""

PROJECT_ROOT = _load_source_root()
if PROJECT_ROOT and PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# テスト対象モジュールのインポート
from app.core.auth_utils import (
    extract_basic_auth_token,
    validate_auth_requirements,
    log_auth_debug_info,
)
from fastapi import HTTPException

# =============================================================================
# 正常系テスト (AUTIL-INIT, AUTIL-001 ~ AUTIL-011)
# =============================================================================
class TestExtractBasicAuthToken:
    """extract_basic_auth_token の正常系テスト。"""
    def test_import_module(self):
        """AUTIL-INIT: モジュールのインポート成功。"""
        # Arrange & Act
        from app.core import auth_utils
        # Assert
        assert hasattr(auth_utils, "extract_basic_auth_token")
        assert hasattr(auth_utils, "validate_auth_requirements")
        assert hasattr(auth_utils, "log_auth_debug_info")
    def test_extract_basic_token_with_space(self):
        """AUTIL-001: Basic認証トークンの抽出（スペースあり）。
        
        auth_utils.py:46-49 の分岐をカバーする。
        """
        # Arrange: テストデータを準備する
        auth_header = "Basic dXNlcjpwYXNz"
        # Act: テスト対象を実行する
        result = extract_basic_auth_token(authorization_header=auth_header)
        # Assert: 期待値と比較する
        assert result == "dXNlcjpwYXNz"
    def test_extract_basic_token_without_space(self):
        """AUTIL-002: Basic認証トークンの抽出（スペースなし）。
        
        auth_utils.py:50-53 の分岐をカバーする。
        """
        # Arrange: テストデータを準備する
        auth_header = "BasicdXNlcjpwYXNz"
        # Act: テスト対象を実行する
        result = extract_basic_auth_token(authorization_header=auth_header)
        # Assert: 期待値と比較する
        assert result == "dXNlcjpwYXNz"
    def test_extract_shared_hmac_token(self):
        """AUTIL-003: SHARED-HMAC認証ヘッダーの受け入れ。
        
        auth_utils.py:54-57 の分岐をカバーする。
        """
        # Arrange: テストデータを準備する
        auth_header = "SHARED-HMAC-1234567890-abcdef123456"
        # Act: テスト対象を実行する
        result = extract_basic_auth_token(authorization_header=auth_header)
        # Assert: 期待値と比較する
        assert result == "SHARED-HMAC-1234567890-abcdef123456"
    def test_extract_from_request_lowercase(self):
        """AUTIL-004: Requestオブジェクトからヘッダーを取得（小文字）。
        
        auth_utils.py:32-36 の分岐をカバーする。
        """
        # Arrange: テストデータを準備する
        mock_headers = MagicMock()
        mock_headers.get = lambda key: (
            "Basic dXNlcjpwYXNz" if key == "authorization" else None
        )
        mock_request = MagicMock()
        mock_request.headers = mock_headers
        # Act: テスト対象を実行する
        result = extract_basic_auth_token(authorization_header=None, request=mock_request)
        # Assert: 期待値と比較する
        assert result == "dXNlcjpwYXNz"
    def test_extract_from_request_uppercase(self):
        """AUTIL-005: Requestオブジェクトからヘッダーを取得（大文字）。
        
        auth_utils.py:34-35 の Authorization（大文字）フォールバックをカバーする。
        """
        # Arrange: テストデータを準備する
        mock_headers = MagicMock()
        def get_header(key):
            if key == "Authorization":
                return "Basic dXNlcjpwYXNz"
            return None
        mock_headers.get = get_header
        mock_request = MagicMock()
        mock_request.headers = mock_headers
        # Act: テスト対象を実行する
        result = extract_basic_auth_token(authorization_header=None, request=mock_request)
        # Assert: 期待値と比較する
        assert result == "dXNlcjpwYXNz"
class TestValidateAuthRequirements:
    """validate_auth_requirements の正常系テスト。"""
    def test_validate_with_opensearch_auth(self):
        """AUTIL-006: 認証要件の検証（OpenSearchあり）。"""
        # Arrange: テストデータを準備する
        endpoint_auth = "test_token"
        opensearch_auth = "opensearch_credentials"
        # Act: テスト対象を実行する
        result = validate_auth_requirements(endpoint_auth, opensearch_auth)
        # Assert: 期待値と比較する
        assert result == ("test_token", "opensearch_credentials")
    def test_validate_without_opensearch_auth(self):
        """AUTIL-007: 認証要件の検証（OpenSearchなし）。"""
        # Arrange: テストデータを準備する
        endpoint_auth = "test_token"
        # Act: テスト対象を実行する
        result = validate_auth_requirements(endpoint_auth, None)
        # Assert: 期待値と比較する
        assert result == ("test_token", None)
    def test_validate_opensearch_auth_default_none(self):
        """AUTIL-007-B: opensearch_authのデフォルト値はNone。"""
        # Arrange: テストデータを準備する
        endpoint_auth = "test_token"
        # Act: テスト対象を実行する
        result = validate_auth_requirements(endpoint_auth)
        # Assert: 期待値と比較する
        assert result == ("test_token", None)
class TestLogAuthDebugInfo:
    """log_auth_debug_info の正常系テスト。"""
    def test_log_with_both_auth(self, caplog):
        """AUTIL-008: デバッグログ出力（両方の認証あり）。"""
        # Arrange: テストデータを準備する
        caplog.set_level(logging.DEBUG)
        # Act: テスト対象を実行する
        log_auth_debug_info(
            session_id="session-123",
            has_endpoint_auth=True,
            has_opensearch_auth=True
        )
        # Assert: 期待値と比較する
        assert "session-123" in caplog.text
        assert "エンドポイント認証: あり" in caplog.text
        assert "OpenSearch認証: あり" in caplog.text
    def test_log_with_header_filtering(self, caplog):
        """AUTIL-009: デバッグログ出力（ヘッダーフィルタリング）。
        
        auth_utils.py:113-120 の分岐をカバーし、認証ヘッダーがマスクされることを検証する。
        """
        # Arrange: テストデータを準備する
        caplog.set_level(logging.DEBUG)
        request_headers = {
            "authorization": "Basic dXNlcjpwYXNzd29yZA==",
            "x-auth-hash": "SHARED-HMAC-12345-abcdef",
            "content-type": "application/json"
        }
        # Act: テスト対象を実行する
        log_auth_debug_info(
            session_id="session-456",
            has_endpoint_auth=True,
            has_opensearch_auth=False,
            request_headers=request_headers
        )
        # Assert: 期待値と比較する
        log_text = caplog.text
        assert "session-456" in log_text
        # 認証ヘッダーはマスクされているべき
        assert "dXNlcjpwYXNzd29yZA==" not in log_text
        assert "SHARED-HMAC-12345-abcdef" not in log_text
        # content-typeは通常通り出力
        assert "application/json" in log_text
    def test_log_without_auth(self, caplog):
        """AUTIL-010: デバッグログ出力（認証なし）。"""
        # Arrange: テストデータを準備する
        caplog.set_level(logging.DEBUG)
        # Act: テスト対象を実行する
        log_auth_debug_info(
            session_id="session-789",
            has_endpoint_auth=False,
            has_opensearch_auth=False
        )
        # Assert: 期待値と比較する
        assert "session-789" in caplog.text
        assert "エンドポイント認証: なし" in caplog.text
        assert "OpenSearch認証: なし" in caplog.text
    def test_log_without_request_headers(self, caplog):
        """AUTIL-010-B: リクエストヘッダーなしでのログ出力。"""
        # Arrange: テストデータを準備する
        caplog.set_level(logging.DEBUG)
        # Act: テスト対象を実行する
        log_auth_debug_info(
            session_id="session-abc",
            has_endpoint_auth=True,
            has_opensearch_auth=True,
            request_headers=None
        )
        # Assert: 期待値と比較する
        assert "session-abc" in caplog.text
        assert "リクエストヘッダー" not in caplog.text
    def test_log_without_debug_level(self, caplog):
        """AUTIL-011: DEBUGレベル無効時のログ出力。
        
        auth_utils.py:113 の logger.isEnabledFor(logging.DEBUG) が False の場合をカバーする。
        """
        # Arrange: テストデータを準備する
        caplog.set_level(logging.INFO)  # DEBUG無効化する
        request_headers = {
            "authorization": "Basic dXNlcjpwYXNz",
            "content-type": "application/json"
        }
        # Act: テスト対象を実行する
        log_auth_debug_info(
            session_id="session-xyz",
            has_endpoint_auth=True,
            has_opensearch_auth=True,
            request_headers=request_headers
        )
        # Assert: 期待値と比較する
        log_text = caplog.text
        assert "session-xyz" in log_text
        # DEBUGレベルが無効なので、リクエストヘッダーは出力されない
        assert "リクエストヘッダー" not in log_text
        assert "dXNlcjpwYXNz" not in log_text
# =============================================================================
# 異常系テスト (AUTIL-E01 ~ AUTIL-E07)
# =============================================================================
class TestExtractBasicAuthTokenErrors:
    """extract_basic_auth_token の異常系テスト。"""
    def test_no_auth_header_raises_http_exception(self):
        """AUTIL-E01: 認証ヘッダーなしでHTTPExceptionが発生する。
        
        auth_utils.py:38-43 の分岐をカバーする。
        """
        # Act & Assert: 例外を検証する
        with pytest.raises(HTTPException) as exc_info:
            extract_basic_auth_token(authorization_header=None, request=None)
        assert exc_info.value.status_code == 401
        assert "認証が必要です" in exc_info.value.detail
    def test_invalid_auth_format_raises_http_exception(self):
        """AUTIL-E02: 無効な認証形式でHTTPExceptionが発生する。
        
        auth_utils.py:58-63 の分岐をカバーする。
        """
        # Arrange: テストデータを準備する
        invalid_headers = [
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "Digest username=test",
            "OAuth oauth_consumer_key=xxx",
            "CustomAuth token123",
        ]
        # Act & Assert: 例外を検証する
        for header in invalid_headers:
            with pytest.raises(HTTPException) as exc_info:
                extract_basic_auth_token(authorization_header=header)
            assert exc_info.value.status_code == 401
            assert "認証形式が不正です" in exc_info.value.detail
    def test_empty_auth_header_raises_http_exception(self):
        """AUTIL-E03: 空の認証ヘッダーでHTTPExceptionが発生する。
        
        auth_utils.py:38 の空文字列の場合をカバーする。
        """
        # Act & Assert: 例外を検証する
        with pytest.raises(HTTPException) as exc_info:
            extract_basic_auth_token(authorization_header="")
        assert exc_info.value.status_code == 401
        assert "認証が必要です" in exc_info.value.detail
    def test_request_without_auth_header_raises_http_exception(self):
        """AUTIL-E06: Requestからの取得も失敗した場合にHTTPExceptionが発生する。"""
        # Arrange: テストデータを準備する
        mock_headers = MagicMock()
        mock_headers.get = lambda key: None
        mock_request = MagicMock()
        mock_request.headers = mock_headers
        # Act & Assert: 例外を検証する
        with pytest.raises(HTTPException) as exc_info:
            extract_basic_auth_token(authorization_header=None, request=mock_request)
        assert exc_info.value.status_code == 401
        assert "認証が必要です" in exc_info.value.detail
    def test_lowercase_basic_prefix_raises_http_exception(self):
        """AUTIL-E07: 小文字のbasicプレフィックスでHTTPExceptionが発生する。
        
        .startswith("Basic") は大文字小文字を区別するため、小文字は拒否される。
        """
        # Arrange: テストデータを準備する
        lowercase_headers = [
            "basic dXNlcjpwYXNz",
            "basicdXNlcjpwYXNz",
            "BASIC dXNlcjpwYXNz",
        ]
        # Act & Assert: 例外を検証する
        for header in lowercase_headers:
            with pytest.raises(HTTPException) as exc_info:
                extract_basic_auth_token(authorization_header=header)
            assert exc_info.value.status_code == 401
            assert "認証形式が不正です" in exc_info.value.detail
class TestValidateAuthRequirementsErrors:
    """validate_auth_requirements の異常系テスト。"""
    def test_no_endpoint_auth_raises_http_exception(self):
        """AUTIL-E04: エンドポイント認証なしでHTTPExceptionが発生する。
        
        auth_utils.py:83-88 の分岐をカバーする。
        """
        # Act & Assert: 例外を検証する
        with pytest.raises(HTTPException) as exc_info:
            validate_auth_requirements(endpoint_auth=None, opensearch_auth="os_auth")
        assert exc_info.value.status_code == 401
        assert "認証トークンが必要です" in exc_info.value.detail
    def test_empty_endpoint_auth_raises_http_exception(self):
        """AUTIL-E05: 空のエンドポイント認証でHTTPExceptionが発生する。"""
        # Act & Assert: 例外を検証する
        with pytest.raises(HTTPException) as exc_info:
            validate_auth_requirements(endpoint_auth="", opensearch_auth="os_auth")
        assert exc_info.value.status_code == 401
        assert "認証トークンが必要です" in exc_info.value.detail
# =============================================================================
# セキュリティテスト (AUTIL-SEC-01 ~ AUTIL-SEC-05)
# =============================================================================
@pytest.mark.security
class TestAuthUtilsSecurity:
    """認証ユーティリティのセキュリティテスト。"""
    def test_auth_header_not_fully_logged(self, caplog):
        """AUTIL-SEC-01: 認証ヘッダーがログに完全出力されない。
        
        auth_utils.py:117-118 でauthorizationヘッダーがマスクされることを検証する。
        """
        # Arrange: テストデータを準備する
        caplog.set_level(logging.DEBUG)
        secret_token = "dXNlcjpzdXBlcl9zZWNyZXRfcGFzc3dvcmQ="
        request_headers = {
            "authorization": f"Basic {secret_token}",
            "content-type": "application/json"
        }
        # Act: テスト対象を実行する
        log_auth_debug_info(
            session_id="sec-test-01",
            has_endpoint_auth=True,
            has_opensearch_auth=False,
            request_headers=request_headers
        )
        # Assert: 期待値と比較する
        log_text = caplog.text
        # 完全なトークンが出力されていないことを検証
        assert secret_token not in log_text
        assert "super_secret_password" not in log_text
        # マスク標記があることを検証
        assert "..." in log_text
    def test_error_message_does_not_expose_credentials(self):
        """AUTIL-SEC-02: エラーメッセージに認証情報が含まれない。
        
        auth_utils.py:59-63 でエラーに認証情報が含まれないことを検証する。
        """
        # Arrange: テストデータを準備する
        malicious_headers = [
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.secret_payload",
            "CustomAuth user:password123",
            "Token sensitive_api_key_12345",
        ]
        for header in malicious_headers:
            # Act & Assert: 例外を検証する
            with pytest.raises(HTTPException) as exc_info:
                extract_basic_auth_token(authorization_header=header)
            error_detail = exc_info.value.detail
            # エラーメッセージに敏感情報が含まれていないことを検証
            assert "secret_payload" not in error_detail
            assert "password123" not in error_detail
            assert "sensitive_api_key_12345" not in error_detail
            # 一般的なエラーメッセージのみ
            assert "認証形式が不正です" in error_detail
    def test_x_auth_hash_header_masked(self, caplog):
        """AUTIL-SEC-03: x-auth-hashヘッダーがログにマスクされる。
        
        auth_utils.py:117 で x-auth-hash ヘッダーもマスクされることを検証する。
        """
        # Arrange: テストデータを準備する
        caplog.set_level(logging.DEBUG)
        hmac_value = "SHARED-HMAC-1234567890-abcdef123456789012345678901234567890"
        request_headers = {
            "x-auth-hash": hmac_value,
            "content-type": "application/json"
        }
        # Act: テスト対象を実行する
        log_auth_debug_info(
            session_id="sec-test-03",
            has_endpoint_auth=True,
            has_opensearch_auth=True,
            request_headers=request_headers
        )
        # Assert: 期待値と比較する
        log_text = caplog.text
        # 完全なHMAC値が出力されていないことを検証
        assert hmac_value not in log_text
        assert "abcdef123456789012345678901234567890" not in log_text
    def test_empty_header_value_filtering_safe(self, caplog):
        """AUTIL-SEC-04: 空ヘッダー値のフィルタリングが安全に処理される。
        
        auth_utils.py:118 で value が空文字やNoneの場合に例外が発生しないことを検証する。
        """
        # Arrange: テストデータを準備する
        caplog.set_level(logging.DEBUG)
        request_headers = {
            "authorization": "",
            "x-auth-hash": None,
            "content-type": "application/json"
        }
        # Act: テスト対象を実行する（例外が発生しないことを検証）
        log_auth_debug_info(
            session_id="sec-test-04",
            has_endpoint_auth=False,
            has_opensearch_auth=False,
            request_headers=request_headers
        )
        # Assert: 期待値と比較する
        log_text = caplog.text
        assert "sec-test-04" in log_text
        # content-typeは通常通り出力される
        assert "application/json" in log_text
    def test_short_auth_header_filtering(self, caplog):
        """AUTIL-SEC-05: 短い認証ヘッダー値のフィルタリング。
        
        auth_utils.py:118 で value が10文字未満の場合に安全にスライスされることを検証する。
        """
        # Arrange: テストデータを準備する
        caplog.set_level(logging.DEBUG)
        short_token = "abc"
        request_headers = {
            "authorization": short_token,
            "content-type": "application/json"
        }
        # Act: テスト対象を実行する
        log_auth_debug_info(
            session_id="sec-test-05",
            has_endpoint_auth=True,
            has_opensearch_auth=False,
            request_headers=request_headers
        )
        # Assert: 期待値と比較する
        log_text = caplog.text
        assert "sec-test-05" in log_text
        # 短いトークンは "abc..." として出力される
        assert "abc..." in log_text
# =============================================================================
# Main Entry Point
# =============================================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
