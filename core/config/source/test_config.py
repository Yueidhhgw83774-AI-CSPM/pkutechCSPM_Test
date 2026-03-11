"""
config.py 単元テスト

测试规格: config_tests.md
覆盖率目标: 85%+

测试类别:
  - 正常系: 6 个测试
  - 异常系: 3 个测试
  - 安全测试: 0 个测试
"""

import pytest
import os
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
from pydantic import ValidationError
from dotenv import load_dotenv

# ✅ 首先加载.env文件(在导入config模块之前)
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path, override=True)
    print(f"✅ Loaded .env from: {env_path}")
else:
    print(f"⚠️ Warning: .env file not found at: {env_path}")
    # 如果.env不存在,设置最小必需的环境变量以防止import失败
    os.environ.setdefault('GPT5_1_CHAT_API_KEY', 'test-key')
    os.environ.setdefault('GPT5_1_CODEX_API_KEY', 'test-key')
    os.environ.setdefault('GPT5_2_API_KEY', 'test-key')
    os.environ.setdefault('GPT5_MINI_API_KEY', 'test-key')
    os.environ.setdefault('GPT5_NANO_API_KEY', 'test-key')
    os.environ.setdefault('CLAUDE_HAIKU_4_5_KEY', 'test-key')
    os.environ.setdefault('CLAUDE_SONNET_4_5_KEY', 'test-key')
    os.environ.setdefault('GEMINI_API', 'test-key')
    os.environ.setdefault('DOCKER_BASE_URL', 'http://localhost:4000')
    os.environ.setdefault('EMBEDDING_3_LARGE_API_KEY', 'test-key')
    os.environ.setdefault('OPENSEARCH_URL', 'https://localhost:9200')

# 导入被测试模块
project_root = Path(__file__).parent.parent.parent.parent / "platform_python_backend-testing"
sys.path.insert(0, str(project_root))


# ==================== 模块导入测试 ====================

class TestConfigImport:
    """
    config模块导入测试
    """

    def test_import_config_module(self):
        """
        测试config模块能否正常导入

        验证内容:
          - Settings类可以导入
          - is_aws_opensearch_service函数可以导入
        """
        # Act & Assert
        try:
            from app.core.config import Settings, is_aws_opensearch_service, settings
            assert Settings is not None
            assert is_aws_opensearch_service is not None
            assert settings is not None
        except ImportError as e:
            pytest.fail(f"模块导入失败: {e}")


# ==================== Settings 正常系测试 ====================

class TestSettings:
    """
    Settings 正常系测试

    测试ID: CFG-001 ~ CFG-003
    """

    def test_load_from_env(self):
        """
        CFG-001: 环境変数から設定読み込み
        覆盖代码行: config.py:8-107

        测试目的:
          - 验证从环境变量正确加载配置
          - 验证必须字段正确读取
        """
        # Arrange & Act - 导入settings实例(从.env文件加载)
        from app.core.config import settings

        # Assert - 验证所有必需配置已正确加载
        # GPT5系API Key
        assert settings.GPT5_1_CHAT_API_KEY is not None, "GPT5_1_CHAT_API_KEY不能为None"
        assert len(settings.GPT5_1_CHAT_API_KEY) > 0, "GPT5_1_CHAT_API_KEY不能为空"
        assert settings.GPT5_1_CODEX_API_KEY is not None, "GPT5_1_CODEX_API_KEY不能为None"
        assert settings.GPT5_2_API_KEY is not None, "GPT5_2_API_KEY不能为None"
        assert settings.GPT5_MINI_API_KEY is not None, "GPT5_MINI_API_KEY不能为None"
        assert settings.GPT5_NANO_API_KEY is not None, "GPT5_NANO_API_KEY不能为None"

        # Claude 4.5系API Key
        assert settings.CLAUDE_HAIKU_4_5_KEY is not None, "CLAUDE_HAIKU_4_5_KEY不能为None"
        assert settings.CLAUDE_SONNET_4_5_KEY is not None, "CLAUDE_SONNET_4_5_KEY不能为None"

        # Gemini API Key (注意:config.py中字段名为GEMINI_API_KEY,从GEMINI_API读取)
        assert settings.GEMINI_API_KEY is not None, "GEMINI_API_KEY不能为None"
        assert len(settings.GEMINI_API_KEY) > 0, "GEMINI_API_KEY不能为空"

        # Base URL
        assert settings.DOCKER_BASE_URL is not None, "DOCKER_BASE_URL不能为None"
        assert len(settings.DOCKER_BASE_URL) > 0, "DOCKER_BASE_URL不能为空"

        # Embedding API Key
        assert settings.EMBEDDING_API_KEY is not None, "EMBEDDING_API_KEY不能为None"
        assert len(settings.EMBEDDING_API_KEY) > 0, "EMBEDDING_API_KEY不能为空"

        # OpenSearch URL
        assert settings.OPENSEARCH_URL is not None, "OPENSEARCH_URL不能为None"
        assert len(settings.OPENSEARCH_URL) > 0, "OPENSEARCH_URL不能为空"

        # 验证URL格式正确
        assert settings.OPENSEARCH_URL.startswith("http"), f"OPENSEARCH_URL格式错误: {settings.OPENSEARCH_URL}"
        assert settings.DOCKER_BASE_URL.startswith("http"), f"DOCKER_BASE_URL格式错误: {settings.DOCKER_BASE_URL}"

        print(f"✅ 所有必需配置项均已正确加载")

    def test_default_values(self):
        """
        CFG-002: デフォルト値の適用
        覆盖代码行: config.py:31-41

        测试目的:
          - 验证可选配置项使用默认值
          - 验证模型名称默认值正确
        """
        # Arrange & Act - 使用现有settings实例(已加载默认值)
        from app.core.config import settings

        # Assert - 验证默认值
        assert settings.MODEL_NAME is not None  # デフォルト値が設定されている
        assert settings.MINI_MODEL_NAME is not None
        assert settings.NANO_MODEL_NAME is not None
        assert settings.RPM_LIMIT > 0  # デフォルト値5が設定されている

    def test_opensearch_url_generation(self):
        """
        CFG-003: OpenSearch URL生成
        覆盖代码行: config.py:52

        测试目的:
          - 验证OPENSEARCH_URL配置项存在
          - 验证URL格式正确
        """
        # Arrange & Act
        from app.core.config import settings

        # Assert - 验证URL存在且格式正确
        assert settings.OPENSEARCH_URL is not None
        assert isinstance(settings.OPENSEARCH_URL, str)
        assert len(settings.OPENSEARCH_URL) > 0

    def test_min_interval_calculation(self):
        """
        CFG-005: MIN_INTERVAL_SECONDS計算
        覆盖代码行: config.py:121

        测试目的:
          - 验证MIN_INTERVAL_SECONDS根据RPM_LIMIT正确计算
          - 验证计算公式: 60 / RPM_LIMIT
        """
        # Arrange & Act
        from app.core.config import settings, MIN_INTERVAL_SECONDS

        # Assert - 验证计算正确
        expected_interval = 60.0 / settings.RPM_LIMIT if settings.RPM_LIMIT > 0 else float('inf')
        assert MIN_INTERVAL_SECONDS == expected_interval
        assert MIN_INTERVAL_SECONDS > 0

    def test_settings_instance_exists(self):
        """
        CFG-006: 設定インスタンス存在確認
        覆盖代码行: config.py:110-118

        测试目的:
          - 验证settings实例已创建
          - 验证settings是Settings类的实例
        """
        # Arrange & Act
        from app.core.config import settings, Settings

        # Assert - 验证实例存在且类型正确
        assert settings is not None
        assert isinstance(settings, Settings)


# ==================== is_aws_opensearch_service 测试 ====================

class TestIsAWSOpenSearchService:
    """
    AWS OpenSearch判定テスト

    测试ID: CFG-004
    """

    def test_is_aws_opensearch_service(self):
        """
        CFG-004: AWS OpenSearch Service判定
        覆盖代码行: config.py:123-133

        测试目的:
          - 验证AWS OpenSearch Service URL识别正确
          - 验证非AWS URL识别正确
          - 验证Serverless URL识别正确
        """
        # Arrange
        from app.core.config import is_aws_opensearch_service

        # Act & Assert - AWS OpenSearch Service URLs
        assert is_aws_opensearch_service("https://search-domain.us-east-1.es.amazonaws.com") is True
        assert is_aws_opensearch_service("https://xxx.es.amazonaws.com") is True
        assert is_aws_opensearch_service("https://xxx.aoss.amazonaws.com") is True  # Serverless

        # Act & Assert - 非AWS URLs
        assert is_aws_opensearch_service("https://localhost:9200") is False
        assert is_aws_opensearch_service("https://opensearch.example.com") is False
        assert is_aws_opensearch_service("http://192.168.1.100:9200") is False


# ==================== Settings 異常系测试 ====================

class TestSettingsErrors:
    """
    Settings 異常系测试

    测试ID: CFG-E01 ~ CFG-E03
    """

    def test_missing_required_fields(self):
        """
        CFG-E01: 必須設定の欠落
        覆盖代码行: config.py:8-56

        测试目的:
          - 验证缺少必须字段时抛出ValidationError
          - 验证错误消息包含缺失字段信息
        """
        # Arrange - 空环境变量(缺少所有必须字段)
        env_vars = {}

        # Act & Assert - 验证抛出ValidationError
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                from app.core.config import Settings
                Settings()

            # 验证错误信息包含必须字段
            error_msg = str(exc_info.value)
            # 至少应该包含一个必须字段的错误
            assert "GPT5_1_CHAT_API_KEY" in error_msg or "Field required" in error_msg

    def test_invalid_rpm_limit_type(self):
        """
        CFG-E02: 無効な型 - RPM_LIMIT
        覆盖代码行: config.py:84

        测试目的:
          - 验证RPM_LIMIT为非数字时抛出错误
          - 验证类型验证机制正常工作
        """
        # Arrange - RPM_LIMIT设为无效值
        env_vars = {
            "GPT5_1_CHAT_API_KEY": "test-key-chat",
            "GPT5_1_CODEX_API_KEY": "test-key-codex",
            "GPT5_2_API_KEY": "test-key-52",
            "GPT5_MINI_API_KEY": "test-key-mini",
            "GPT5_NANO_API_KEY": "test-key-nano",
            "CLAUDE_HAIKU_4_5_KEY": "test-key-haiku",
            "CLAUDE_SONNET_4_5_KEY": "test-key-sonnet",
            "GEMINI_API": "test-key-gemini",
            "DOCKER_BASE_URL": "http://localhost:4000",
            "EMBEDDING_3_LARGE_API_KEY": "test-key-embedding",
            "OPENSEARCH_URL": "https://localhost:9200",
            "RPM_LIMIT": "not-a-number"  # 無効な型
        }

        # Act & Assert - 验证抛出ValidationError
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                from app.core.config import Settings
                Settings()

            # 验证错误消息包含RPM_LIMIT
            error_msg = str(exc_info.value)
            assert "RPM_LIMIT" in error_msg or "int" in error_msg.lower()

    def test_invalid_opensearch_url_format(self):
        """
        CFG-E03: 無効なOpenSearch URL形式

        测试目的:
          - 验证虽然URL格式无效,但Settings仍可创建(Pydantic只验证类型)
          - 验证URL存储为字符串

        注意: Pydantic的Field验证主要是类型验证,不进行URL格式验证
        """
        # Arrange - 使用无效的URL格式
        env_vars = {
            "GPT5_1_CHAT_API_KEY": "test-key-chat",
            "GPT5_1_CODEX_API_KEY": "test-key-codex",
            "GPT5_2_API_KEY": "test-key-52",
            "GPT5_MINI_API_KEY": "test-key-mini",
            "GPT5_NANO_API_KEY": "test-key-nano",
            "CLAUDE_HAIKU_4_5_KEY": "test-key-haiku",
            "CLAUDE_SONNET_4_5_KEY": "test-key-sonnet",
            "GEMINI_API": "test-key-gemini",
            "DOCKER_BASE_URL": "http://localhost:4000",
            "EMBEDDING_3_LARGE_API_KEY": "test-key-embedding",
            "OPENSEARCH_URL": "invalid-url-without-scheme",  # 無効なURL
        }

        # Act - 创建Settings(应该成功,因为只验证类型)
        with patch.dict(os.environ, env_vars, clear=True):
            from app.core.config import Settings
            test_settings = Settings()

        # Assert - 验证URL虽然格式无效但已存储
        assert test_settings.OPENSEARCH_URL == "invalid-url-without-scheme"
        assert isinstance(test_settings.OPENSEARCH_URL, str)


# ==================== is_aws_opensearch_service 異常系测试 ====================

class TestIsAWSOpenSearchServiceErrors:
    """
    is_aws_opensearch_service 異常系测试
    """

    def test_invalid_url_format(self):
        """
        CFG-E04: 無効なURL形式の処理
        覆盖代码行: config.py:123-133

        测试目的:
          - 验证对无效URL格式的健壮处理
          - 验证不会抛出异常,返回False
        """
        # Arrange
        from app.core.config import is_aws_opensearch_service

        # Act & Assert - 无效URL应返回False
        assert is_aws_opensearch_service("not-a-valid-url") is False
        assert is_aws_opensearch_service("") is False
        assert is_aws_opensearch_service("htp://broken-protocol.com") is False

    def test_none_url(self):
        """
        CFG-E05: None URL的処理
        覆盖代码行: config.py:128

        测试目的:
          - 验证None输入的处理
          - 验证返回False而不是抛出异常
        """
        # Arrange
        from app.core.config import is_aws_opensearch_service

        # Act & Assert - None应返回False
        assert is_aws_opensearch_service(None) is False


# ==================== 集成测试 ====================

class TestConfigIntegration:
    """
    config模块集成测试
    """

    def test_settings_and_helper_function_work_together(self):
        """
        测试settings实例和辅助函数协同工作

        测试目的:
          - 验证settings.OPENSEARCH_URL可以传递给is_aws_opensearch_service
          - 验证两者配合使用无问题
        """
        # Arrange
        from app.core.config import settings, is_aws_opensearch_service

        # Act - 使用settings的URL调用判定函数
        result = is_aws_opensearch_service(settings.OPENSEARCH_URL)

        # Assert - 验证函数正常执行(无异常)
        assert isinstance(result, bool)

    def test_min_interval_updates_with_rpm_limit(self):
        """
        测试RPM_LIMIT变化时MIN_INTERVAL_SECONDS的更新

        测试目的:
          - 验证MIN_INTERVAL_SECONDS与RPM_LIMIT的关系
          - 验证计算逻辑正确

        注意: MIN_INTERVAL_SECONDS在模块加载时计算,这个测试主要验证逻辑
        """
        # Arrange
        from app.core.config import settings, MIN_INTERVAL_SECONDS

        # Act - 计算期望值
        expected_interval = 60.0 / settings.RPM_LIMIT if settings.RPM_LIMIT > 0 else float('inf')

        # Assert - 验证计算正确
        assert MIN_INTERVAL_SECONDS == expected_interval

        # 验证边界情况的逻辑(不实际修改settings)
        if settings.RPM_LIMIT > 0:
            assert MIN_INTERVAL_SECONDS == 60.0 / settings.RPM_LIMIT
        else:
            assert MIN_INTERVAL_SECONDS == float('inf')
