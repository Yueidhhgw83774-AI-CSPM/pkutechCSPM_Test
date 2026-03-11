# -*- coding: utf-8 -*-
"""
auth_utils.py 单元测试
测试对象: app/core/auth_utils.py
测试规格: docs/testing/core/auth_utils_tests.md
覆盖率目标: 90%
本测试文件严格按照 auth_utils_tests.md 测试规格文档编写，
包含正常系测试、异常系测试和安全测试三大类。
测试命名规则:
- 正常系: test_<function>_<description>  (AUTIL-INIT, AUTIL-001 ~ AUTIL-011)
- 异常系: test_<function>_<error_description>  (AUTIL-E01 ~ AUTIL-E07)
- 安全测试: test_<security_aspect>  (AUTIL-SEC-01 ~ AUTIL-SEC-05)
"""
import os
import sys
import time
import logging
from unittest.mock import MagicMock
import pytest
# Add project root to path
PROJECT_ROOT = r"C:\pythonProject\python_ai_cspm\platform_python_backend-testing"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# Import the module under test
from app.core.auth_utils import (
    extract_basic_auth_token,
    validate_auth_requirements,
    log_auth_debug_info,
)
from fastapi import HTTPException
# =============================================================================
# 正常系测试 (AUTIL-INIT, AUTIL-001 ~ AUTIL-011)
# =============================================================================
class TestExtractBasicAuthToken:
    """extract_basic_auth_token 正常系测试"""
    def test_import_module(self):
        """AUTIL-INIT: 模块导入成功"""
        # Arrange & Act
        from app.core import auth_utils
        # Assert
        assert hasattr(auth_utils, "extract_basic_auth_token")
        assert hasattr(auth_utils, "validate_auth_requirements")
        assert hasattr(auth_utils, "log_auth_debug_info")
    def test_extract_basic_token_with_space(self):
        """AUTIL-001: Basic认证令牌提取（有空格）
        覆盖 auth_utils.py:46-49 分支
        """
        # Arrange
        auth_header = "Basic dXNlcjpwYXNz"
        # Act
        result = extract_basic_auth_token(authorization_header=auth_header)
        # Assert
        assert result == "dXNlcjpwYXNz"
    def test_extract_basic_token_without_space(self):
        """AUTIL-002: Basic认证令牌提取（无空格）
        覆盖 auth_utils.py:50-53 分支
        """
        # Arrange
        auth_header = "BasicdXNlcjpwYXNz"
        # Act
        result = extract_basic_auth_token(authorization_header=auth_header)
        # Assert
        assert result == "dXNlcjpwYXNz"
    def test_extract_shared_hmac_token(self):
        """AUTIL-003: SHARED-HMAC认证头接受
        覆盖 auth_utils.py:54-57 分岐
        """
        # Arrange
        auth_header = "SHARED-HMAC-1234567890-abcdef123456"
        # Act
        result = extract_basic_auth_token(authorization_header=auth_header)
        # Assert
        assert result == "SHARED-HMAC-1234567890-abcdef123456"
    def test_extract_from_request_lowercase(self):
        """AUTIL-004: 从Request对象获取头（小写）
        覆盖 auth_utils.py:32-36 分岐
        """
        # Arrange
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
        """AUTIL-005: 从Request对象获取头（大写）
        覆盖 auth_utils.py:34-35 的 Authorization（大文字）フォールバック
        """
        # Arrange
        mock_headers = MagicMock()
        def get_header(key):
            if key == "Authorization":
                return "Basic dXNlcjpwYXNz"
            return None
        mock_headers.get = get_header
        mock_request = MagicMock()
        mock_request.headers = mock_headers
        # Act
        result = extract_basic_auth_token(authorization_header=None, request=mock_request)
        # Assert
        assert result == "dXNlcjpwYXNz"
class TestValidateAuthRequirements:
    """validate_auth_requirements 正常系测试"""
    def test_validate_with_opensearch_auth(self):
        """AUTIL-006: 认证要求验证（有OpenSearch）"""
        # Arrange
        endpoint_auth = "test_token"
        opensearch_auth = "opensearch_credentials"
        # Act
        result = validate_auth_requirements(endpoint_auth, opensearch_auth)
        # Assert
        assert result == ("test_token", "opensearch_credentials")
    def test_validate_without_opensearch_auth(self):
        """AUTIL-007: 认证要求验证（无OpenSearch）"""
        # Arrange
        endpoint_auth = "test_token"
        # Act
        result = validate_auth_requirements(endpoint_auth, None)
        # Assert
        assert result == ("test_token", None)
    def test_validate_opensearch_auth_default_none(self):
        """AUTIL-007-B: opensearch_auth默认为None"""
        # Arrange
        endpoint_auth = "test_token"
        # Act
        result = validate_auth_requirements(endpoint_auth)
        # Assert
        assert result == ("test_token", None)
class TestLogAuthDebugInfo:
    """log_auth_debug_info 正常系测试"""
    def test_log_with_both_auth(self, caplog):
        """AUTIL-008: 日志输出（两种认证）"""
        # Arrange
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
        """AUTIL-009: 日志输出（头过滤）
        覆盖 auth_utils.py:113-120 分岐，验证认证头被掩码
        """
        # Arrange
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
        # 认证头应被掩码
        assert "dXNlcjpwYXNzd29yZA==" not in log_text
        assert "SHARED-HMAC-12345-abcdef" not in log_text
        # content-type正常输出
        assert "application/json" in log_text
    def test_log_without_auth(self, caplog):
        """AUTIL-010: 日志输出（无认证）"""
        # Arrange
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
        """AUTIL-010-B: 日志输出（无请求头）"""
        # Arrange
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
        assert "リクエストヘッダー" not in caplog.text
    def test_log_without_debug_level(self, caplog):
        """AUTIL-011: 日志输出（DEBUG禁用）
        覆盖 auth_utils.py:113 的 logger.isEnabledFor(logging.DEBUG) 为 False
        """
        # Arrange
        caplog.set_level(logging.INFO)  # DEBUG禁用
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
        # DEBUG禁用，不输出请求头
        assert "リクエストヘッダー" not in log_text
        assert "dXNlcjpwYXNz" not in log_text
# =============================================================================
# 异常系测试 (AUTIL-E01 ~ AUTIL-E07)
# =============================================================================
class TestExtractBasicAuthTokenErrors:
    """extract_basic_auth_token 异常系测试"""
    def test_no_auth_header_raises_http_exception(self):
        """AUTIL-E01: 无认证头抛出HTTPException
        覆盖 auth_utils.py:38-43 分岐
        """
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            extract_basic_auth_token(authorization_header=None, request=None)
        assert exc_info.value.status_code == 401
        assert "認証が必要です" in exc_info.value.detail
    def test_invalid_auth_format_raises_http_exception(self):
        """AUTIL-E02: 无效认证格式抛出HTTPException
        覆盖 auth_utils.py:58-63 分岐
        """
        # Arrange
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
        """AUTIL-E03: 空认证头抛出HTTPException
        覆盖 auth_utils.py:38 的空字符串情况
        """
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            extract_basic_auth_token(authorization_header="")
        assert exc_info.value.status_code == 401
        assert "認証が必要です" in exc_info.value.detail
    def test_request_without_auth_header_raises_http_exception(self):
        """AUTIL-E06: Request也获取失败抛出HTTPException"""
        # Arrange
        mock_headers = MagicMock()
        mock_headers.get = lambda key: None
        mock_request = MagicMock()
        mock_request.headers = mock_headers
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            extract_basic_auth_token(authorization_header=None, request=mock_request)
        assert exc_info.value.status_code == 401
        assert "認証が必要です" in exc_info.value.detail
    def test_lowercase_basic_prefix_raises_http_exception(self):
        """AUTIL-E07: 小写basic前缀抛出HTTPException
        .startswith("Basic") 区分大小写，小写会被拒绝
        """
        # Arrange
        lowercase_headers = [
            "basic dXNlcjpwYXNz",
            "basicdXNlcjpwYXNz",
            "BASIC dXNlcjpwYXNz",
        ]
        # Act & Assert
        for header in lowercase_headers:
            with pytest.raises(HTTPException) as exc_info:
                extract_basic_auth_token(authorization_header=header)
            assert exc_info.value.status_code == 401
            assert "認証形式が不正です" in exc_info.value.detail
class TestValidateAuthRequirementsErrors:
    """validate_auth_requirements 异常系测试"""
    def test_no_endpoint_auth_raises_http_exception(self):
        """AUTIL-E04: 无endpoint认证抛出HTTPException
        覆盖 auth_utils.py:83-88 分岐
        """
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            validate_auth_requirements(endpoint_auth=None, opensearch_auth="os_auth")
        assert exc_info.value.status_code == 401
        assert "認証トークンが必要です" in exc_info.value.detail
    def test_empty_endpoint_auth_raises_http_exception(self):
        """AUTIL-E05: 空endpoint认证抛出HTTPException"""
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            validate_auth_requirements(endpoint_auth="", opensearch_auth="os_auth")
        assert exc_info.value.status_code == 401
        assert "認証トークンが必要です" in exc_info.value.detail
# =============================================================================
# 安全测试 (AUTIL-SEC-01 ~ AUTIL-SEC-05)
# =============================================================================
@pytest.mark.security
class TestAuthUtilsSecurity:
    """认证工具安全测试"""
    def test_auth_header_not_fully_logged(self, caplog):
        """AUTIL-SEC-01: 认证头不完全输出到日志
        覆盖 auth_utils.py:117-118，验证authorization头被掩码
        """
        # Arrange
        caplog.set_level(logging.DEBUG)
        secret_token = "dXNlcjpzdXBlcl9zZWNyZXRfcGFzc3dvcmQ="
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
        # 完整令牌不应出现
        assert secret_token not in log_text
        assert "super_secret_password" not in log_text
        # 应该有掩码标记
        assert "..." in log_text
    def test_error_message_does_not_expose_credentials(self):
        """AUTIL-SEC-02: 错误消息不包含认证信息
        覆盖 auth_utils.py:59-63，验证错误不泄露认证信息
        """
        # Arrange
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
            # 错误消息不应包含敏感信息
            assert "secret_payload" not in error_detail
            assert "password123" not in error_detail
            assert "sensitive_api_key_12345" not in error_detail
            # 应该是通用错误消息
            assert "認証形式が不正です" in error_detail
    def test_x_auth_hash_header_masked(self, caplog):
        """AUTIL-SEC-03: x-auth-hash头被掩码
        覆盖 auth_utils.py:117，验证x-auth-hash也被掩码
        """
        # Arrange
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
        # 完整HMAC值不应出现
        assert hmac_value not in log_text
        assert "abcdef123456789012345678901234567890" not in log_text
    def test_empty_header_value_filtering_safe(self, caplog):
        """AUTIL-SEC-04: 空头值过滤安全性
        覆盖 auth_utils.py:118，验证空值不引发异常
        """
        # Arrange
        caplog.set_level(logging.DEBUG)
        request_headers = {
            "authorization": "",
            "x-auth-hash": None,
            "content-type": "application/json"
        }
        # Act - 不应抛出异常
        log_auth_debug_info(
            session_id="sec-test-04",
            has_endpoint_auth=False,
            has_opensearch_auth=False,
            request_headers=request_headers
        )
        # Assert
        log_text = caplog.text
        assert "sec-test-04" in log_text
        # content-type正常输出
        assert "application/json" in log_text
    def test_short_auth_header_filtering(self, caplog):
        """AUTIL-SEC-05: 短认证头值过滤
        覆盖 auth_utils.py:118，验证短值安全切片
        """
        # Arrange
        caplog.set_level(logging.DEBUG)
        short_token = "abc"
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
        # 短令牌应显示为 "abc..."
        assert "abc..." in log_text
# =============================================================================
# Main Entry Point
# =============================================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
