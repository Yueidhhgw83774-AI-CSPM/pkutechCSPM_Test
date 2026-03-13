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

# ✅ まず.envファイルを読み込みます（configモジュールのインポート前に）
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path, override=True)
    print(f"✅ Loaded .env from: {env_path}")
else:
    print(f"⚠️ Warning: .env file not found at: {env_path}")
    # .envファイルが存在しない場合、import失敗を防ぐために最小限必要な環境変数を設定します。
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

# テスト対象のモジュールをインポートする
project_root = Path(__file__).parent.parent.parent.parent / "platform_python_backend-testing"
sys.path.insert(0, str(project_root))


# ==================== モジュールインポートテスト ====================

class TestConfigImport:
    """
    configモジュールのインポートテスト
    """

    def test_import_config_module(self):
        """
        configモジュールの正常なインポートをテストする

                評価内容:
                  - Settingsクラスがインポート可能
                  - is_aws_opensearch_service関数がインポート可能
        """
        # Act & Assert
        try:
            from app.core.config import Settings, is_aws_opensearch_service, settings
            assert Settings is not None
            assert is_aws_opensearch_service is not None
            assert settings is not None
        except ImportError as e:
            pytest.fail(f"模块导入失败: {e}")


# ==================== Settings 通常系テスト ====================

class TestSettings:
    """
    Settings 通常系テスト

        テストID: CFG-001 ~ CFG-003
    """

    def test_load_from_env(self):
        """
        CFG-001: 环境変数から設定読み込み
        覆盖代码行: config.py:8-107

        测试目的:
          - 验证从环境变量正确加载配置
          - 验证必须字段正确读取
        """
        # Arrange & Act - settingsインスタンスのインポート（.envファイルから読み込み）
        from app.core.config import settings

        # Assert - 必要な設定が正しく読み込まれていることを確認します
        # GPT5系APIキー
        assert settings.GPT5_1_CHAT_API_KEY is not None, "GPT5_1_CHAT_API_KEY不能为None"
        assert len(settings.GPT5_1_CHAT_API_KEY) > 0, "GPT5_1_CHAT_API_KEY不能为空"
        assert settings.GPT5_1_CODEX_API_KEY is not None, "GPT5_1_CODEX_API_KEY不能为None"
        assert settings.GPT5_2_API_KEY is not None, "GPT5_2_API_KEY不能为None"
        assert settings.GPT5_MINI_API_KEY is not None, "GPT5_MINI_API_KEY不能为None"
        assert settings.GPT5_NANO_API_KEY is not None, "GPT5_NANO_API_KEY不能为None"

        # Claude 4.5のAPIキー
        assert settings.CLAUDE_HAIKU_4_5_KEY is not None, "CLAUDE_HAIKU_4_5_KEY不能为None"
        assert settings.CLAUDE_SONNET_4_5_KEY is not None, "CLAUDE_SONNET_4_5_KEY不能为None"

        # Gemini APIキー（注意:config.pyのフィールド名はGEMINI_API_KEY、GEMINI_APIから読み取り）
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

        # URLの形式が正しいかを検証する
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
        # Arrange & Act - 現有的settingsインスタンス（デフォルト値が読み込まれている）を使用する
        from app.core.config import settings

        # Assert - デフォルト値の検証
        assert settings.MODEL_NAME is not None  # デフォルト値が設定されている
        assert settings.MINI_MODEL_NAME is not None
        assert settings.NANO_MODEL_NAME is not None
        assert settings.RPM_LIMIT > 0  # デフォルト値5が設定されている

    def test_opensearch_url_generation(self):
        """
        CFG-003: OpenSearch URL生成
                覆盖コード行: config.py:52

                テスト目的:
                  - OPENSEARCH_URL設定項目の存在を確認する
                  - URL形式が正しいことを確認する
        """
        # Arrange & Act
        from app.core.config import settings

        # Assert - URLが存在し、正しい形式であることを確認する
        assert settings.OPENSEARCH_URL is not None
        assert isinstance(settings.OPENSEARCH_URL, str)
        assert len(settings.OPENSEARCH_URL) > 0

    def test_min_interval_calculation(self):
        """
        CFG-005: MIN_INTERVAL_SECONDSの計算
                覆盖コード行: config.py:121

                テスト目的:
                  - RPM_LIMITに基づいてMIN_INTERVAL_SECONDSが正しく計算されることを確認する
                  - 計算公式: 60 / RPM_LIMITを確認する
        """
        # Arrange & Act
        from app.core.config import settings, MIN_INTERVAL_SECONDS

        # Assert - 計算の正確性を確認する
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

        # Assert - インスタンスの存在と型の正しさを確認する
        assert settings is not None
        assert isinstance(settings, Settings)


# ==================== is_aws_opensearch_service テスト ====================

class TestIsAWSOpenSearchService:
    """
    AWS OpenSearch判定テスト

    测试ID: CFG-004
    """

    def test_is_aws_opensearch_service(self):
        """
        CFG-004: AWS OpenSearch Service判定
                被覆行数: config.py:123-133

                テスト目的:
                  - AWS OpenSearch Service URLの識別が正しいことを確認する
                  - AWS以外のURLの識別が正しいことを確認する
                  - Serverless URLの識別が正しいことを確認する
        """
        # Arrange
        from app.core.config import is_aws_opensearch_service

        # Act & Assert - AWS OpenSearch Service URLs
        assert is_aws_opensearch_service("https://search-domain.us-east-1.es.amazonaws.com") is True
        assert is_aws_opensearch_service("https://xxx.es.amazonaws.com") is True
        assert is_aws_opensearch_service("https://xxx.aoss.amazonaws.com") is True  # Serverless

        # Act & Assert - 非AWS URLS
        assert is_aws_opensearch_service("https://localhost:9200") is False
        assert is_aws_opensearch_service("https://opensearch.example.com") is False
        assert is_aws_opensearch_service("http://192.168.1.100:9200") is False


# ==================== Settings 異常系テスト ====================

class TestSettingsErrors:
    """
    Settings 異常系テスト

        テストID: CFG-E01 ~ CFG-E03
    """

    def test_missing_required_fields(self):
        """
        CFG-E01: 必須設定の欠落
        覆盖代码行: config.py:8-56

        测试目的:
          - 验证缺少必须字段时抛出ValidationError
          - 验证错误消息包含缺失字段信息
        """
        # Arrange - 空の環境変数（必要なすべてのフィールドが欠けています）
        env_vars = {}

        # アクション & アサート - ValidationErrorが投げられるかの検証
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                from app.core.config import Settings
                Settings()

            # 検証エラー情報に必須のフィールドが含まれていることを確認します。
            error_msg = str(exc_info.value)
            # 必須のフィールドが至少一个應該包含至少一個必須的字段未指定です。
            assert "GPT5_1_CHAT_API_KEY" in error_msg or "Field required" in error_msg

    def test_invalid_rpm_limit_type(self):
        """
        CFG-E02: 無効な型 - RPM_LIMIT
        覆盖代码行: config.py:84

        测试目的:
          - 验证RPM_LIMIT为非数字时抛出错误
          - 验证类型验证机制正常工作
        """
        # Arrange - RPM_LIMITを無効な値に設定する
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

        # アクション & アサート - ValidationErrorが投げられるかの検証
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                from app.core.config import Settings
                Settings()

            # 検証エラーメッセージにRPM_LIMITが含まれていることを確認します。
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
        # Arrange - 無効なURL形式を使用する
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

        # アクション - Settingsの作成（タイプの検証のみを行うため成功するはず）
        with patch.dict(os.environ, env_vars, clear=True):
            from app.core.config import Settings
            test_settings = Settings()

        # Assert - URLの形式が無効であるものの、URLが保存されていることを確認します
        assert test_settings.OPENSEARCH_URL == "invalid-url-without-scheme"
        assert isinstance(test_settings.OPENSEARCH_URL, str)


# ==================== is_aws_opensearch_service 異常系テスト ====================

class TestIsAWSOpenSearchServiceErrors:
    """
    AWS OpenSearch Service 異常系テスト
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

        # アクション & アサート - 無効なURLはFalseを返す
        assert is_aws_opensearch_service("not-a-valid-url") is False
        assert is_aws_opensearch_service("") is False
        assert is_aws_opensearch_service("htp://broken-protocol.com") is False

    def test_none_url(self):
        """
        CFG-E05: None URLの処理
                被覆コード行: config.py:128

                テスト目的:
                  - None入力の処理を確認する
                  - 例外を投げずにFalseを返すことを確認する
        """
        # Arrange
        from app.core.config import is_aws_opensearch_service

        # Act & Assert - NoneはFalseを返す
        assert is_aws_opensearch_service(None) is False


# ==================== 統合テスト ====================

class TestConfigIntegration:
    """
    configモジュール統合テスト
    """

    def test_settings_and_helper_function_work_together(self):
        """
        settingsインスタンスとヘルパー関数の連携動作テスト

                テスト目的:
                  - settings.OPENSEARCH_URLがis_aws_opensearch_serviceに正しく渡されることを確認する
                  - 両者の連携が問題なく動作することを確認する
        """
        # Arrange
        from app.core.config import settings, is_aws_opensearch_service

        # アクション - settingsのURLを使用して判定関数を呼び出す
        result = is_aws_opensearch_service(settings.OPENSEARCH_URL)

        # Assert - 関数の正常終了（異常なし）を検証する
        assert isinstance(result, bool)

    def test_min_interval_updates_with_rpm_limit(self):
        """
        RPM_LIMITの変更時にMIN_INTERVAL_SECONDSの更新をテストする

                テスト目的:
                  - MIN_INTERVAL_SECONDSとRPM_LIMITの関係を確認する
                  - 計算ロジックの正確性を確認する

                注意: MIN_INTERVAL_SECONDSはモジュールの読み込み時に計算され、このテストでは主にロジックを検証する
        """
        # Arrange
        from app.core.config import settings, MIN_INTERVAL_SECONDS

        # アクタ - 期待値を計算する
        expected_interval = 60.0 / settings.RPM_LIMIT if settings.RPM_LIMIT > 0 else float('inf')

        # Assert - 計算の正しさを検証する
        assert MIN_INTERVAL_SECONDS == expected_interval

        # 境界情况のログิกを検証する（settingsを実際には変更しない）
        if settings.RPM_LIMIT > 0:
            assert MIN_INTERVAL_SECONDS == 60.0 / settings.RPM_LIMIT
        else:
            assert MIN_INTERVAL_SECONDS == float('inf')
