# config テストケース（Enhanced版）

## 0. Enhanced版について

### 0.1 旧版との違い

本ドキュメントは `config_tests.md`（旧版）を全面的に書き直した改良版です。

| 項目 | 旧版（config_tests.md） | Enhanced版（本ドキュメント） |
|------|------------------------|---------------------------|
| テストケース数 | 6件（正常3 + 異常2 + is_aws 1） | **35件**（正常20 + 異常11 + セキュリティ5） |
| 行数 | 121行 | 約900行 |
| カバレッジ目標 | 85% | **95%** |
| フィールド数の把握 | 未記載（OPENSEARCH_HOST等、存在しないフィールドを参照） | **42フィールド全て**を正確にカバー |
| validation_aliasテスト | なし | **3件**（GEMINI_API, EMBEDDING_3_LARGE_API_KEY, DOCKER_BASE_URL） |
| モジュールレベル初期化テスト | なし | **SystemExit検証**（importlib動的インポート） |
| MIN_INTERVAL_SECONDSテスト | なし | **派生値計算テスト**（RPM_LIMIT=5,60,0の3パターン） |
| セキュリティテスト | なし | **5件**（ログ漏洩、マスク表示、DEBUG_MODE等） |
| フィクスチャ設計 | なし | **REQUIRED_ENV_VARS + reset_config_module（autouse）** |
| 既知の制限事項 | なし | **5項目**（モジュールキャッシュ、load_dotenv等） |
| コードレビュー | なし | **code-reviewer + Codex** 2者LGTM済み |

### 0.2 書き直しが必要だった理由

旧版には以下の問題があり、テスト仕様書としての実効性がほぼ0%でした：

1. **存在しないフィールドの参照**: `OPENSEARCH_HOST`, `OPENSEARCH_PORT`, `LOG_LEVEL` など、実装に存在しないフィールドをテスト対象にしていた
2. **42フィールド中4フィールドしかカバーしていない**: 実質的なカバレッジが極めて低い
3. **モジュールレベル初期化の未考慮**: `config.py`はインポート時に`Settings()`を実行し、失敗時に`SystemExit`を発生させるが、この重要な挙動がテストされていなかった
4. **validation_alias未テスト**: `GEMINI_API` → `GEMINI_API_KEY` 等のエイリアス変換が検証されていなかった
5. **セキュリティ観点の欠如**: APIキーやパスワードのログ出力漏洩チェックが一切なかった
6. **テスト分離の未考慮**: `sys.modules`キャッシュやload_dotenvの影響を考慮したフィクスチャ設計がなかった

### 0.3 レビュー履歴

| レビュアー | ラウンド | 結果 | コミット |
|-----------|---------|------|---------|
| code-reviewer | 1回目 | 85/100（Critical 3件修正） | `3b31091` |
| Codex | 1回目 | 7件指摘（全件修正） | `3e46770` |
| code-reviewer | 2回目 | Minor 2件修正 | `4f780e8` |
| Codex | 2回目 | **LGTM** | - |

---

## 1. 概要

アプリケーション設定管理（`config.py`）のテストケースを定義します。
Pydantic Settings による環境変数読み込み、バリデーション、派生値計算、ヘルパー関数を網羅的に検証します。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `Settings` | Pydantic BaseSettingsベースの設定クラス（42フィールド） |
| `settings` | Settingsインスタンス（モジュールレベル初期化、失敗時SystemExit） |
| `MIN_INTERVAL_SECONDS` | RPM_LIMITから算出されるレート制限間隔（派生値） |
| `is_aws_opensearch_service()` | OpenSearch URLがAWSサービスかを判定するヘルパー関数 |

### 1.2 カバレッジ目標: 95%

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/core/config.py` |
| テストコード | `test/unit/core/test_config.py` |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CFG-001 | 全必須フィールド設定でSettings初期化成功 | 全必須環境変数 | Settingsインスタンス |
| CFG-002 | モデル名フィールドのデフォルト値検証（7フィールド） | 必須のみ設定 | 各デフォルト値 |
| CFG-003 | OpenSearch・Embeddingフィールドのデフォルト値検証 | 必須のみ設定 | OPENSEARCH_INDEX_RAG, EMBEDDING_MODEL_NAME等 |
| CFG-004 | JWT設定のデフォルト値検証 | 必須のみ設定 | HS256, 30分等 |
| CFG-005 | LangGraph設定のデフォルト値検証 | 必須のみ設定 | "memory", None |
| CFG-006 | RPM_LIMIT/DEBUG_MODEのデフォルト値検証 | 必須のみ設定 | 5, False |
| CFG-007 | Optionalフィールド未設定時にNone | 必須のみ設定 | None |
| CFG-008 | 全LLM APIキーの環境変数読み込み | 全キー設定 | 設定値一致 |
| CFG-009 | GEMINI_API_KEYのvalidation_alias動作確認 | GEMINI_API設定 | 値がGEMINI_API_KEYに格納 |
| CFG-010 | EMBEDDING_API_KEYのvalidation_alias動作確認 | EMBEDDING_3_LARGE_API_KEY設定 | 値がEMBEDDING_API_KEYに格納 |
| CFG-011 | EMBEDDING_MODEL_BASE_URLのalias動作確認 | DOCKER_BASE_URL設定 | 同値がEMBEDDING_MODEL_BASE_URLに格納 |
| CFG-012 | AWS設定の読み込み | REGION, SESSION_TOKEN設定 | 設定値一致 |
| CFG-013 | ロールベースOpenSearch認証情報の読み込み（4ロール） | 全ロール設定 | 設定値一致 |
| CFG-014 | MIN_INTERVAL_SECONDS計算（RPM_LIMIT=5→12.0秒） | RPM_LIMIT=5 | 12.0 |
| CFG-015 | MIN_INTERVAL_SECONDS計算（RPM_LIMIT=60→1.0秒） | RPM_LIMIT=60 | 1.0 |
| CFG-016 | is_aws_opensearch_service: AWS ES URLでTrue | .es.amazonaws.com URL | True |
| CFG-017 | is_aws_opensearch_service: AWS AOSS URLでTrue | .aoss.amazonaws.com URL | True |
| CFG-018 | is_aws_opensearch_service: ローカルURLでFalse | localhost URL | False |
| CFG-019 | is_aws_opensearch_service: ポート付きAWS URLでTrue | .es.amazonaws.com:443 URL | True |
| CFG-020 | model_configのcase_sensitive/extra設定確認 | - | case_sensitive=True, extra='ignore' |

### 2.1 Settings初期化テスト

```python
# test/unit/core/test_config.py
import pytest
import os
import math
from unittest.mock import patch
from pydantic import ValidationError


# 全必須フィールドを含むテスト用環境変数辞書
REQUIRED_ENV_VARS = {
    "GPT5_1_CHAT_API_KEY": "test-gpt5-1-chat-key",
    "GPT5_1_CODEX_API_KEY": "test-gpt5-1-codex-key",
    "GPT5_2_API_KEY": "test-gpt5-2-key",
    "GPT5_MINI_API_KEY": "test-gpt5-mini-key",
    "GPT5_NANO_API_KEY": "test-gpt5-nano-key",
    "CLAUDE_HAIKU_4_5_KEY": "test-claude-haiku-key",
    "CLAUDE_SONNET_4_5_KEY": "test-claude-sonnet-key",
    "GEMINI_API": "test-gemini-key",  # validation_alias: GEMINI_API
    "DOCKER_BASE_URL": "http://localhost:11434",
    "EMBEDDING_3_LARGE_API_KEY": "test-embedding-key",  # validation_alias: EMBEDDING_3_LARGE_API_KEY
    "OPENSEARCH_URL": "https://localhost:9200",
}


class TestSettingsInitialization:
    """Settings初期化テスト"""

    def test_settings_init_with_all_required_fields(self):
        """CFG-001: 全必須フィールド設定でSettings初期化成功"""
        # Arrange & Act
        with patch.dict(os.environ, REQUIRED_ENV_VARS, clear=True):
            from app.core.config import Settings
            settings = Settings()

        # Assert
        assert settings.GPT5_1_CHAT_API_KEY == "test-gpt5-1-chat-key"
        assert settings.OPENSEARCH_URL == "https://localhost:9200"

    def test_all_llm_api_keys_loaded(self):
        """CFG-008: 全LLM APIキーの環境変数読み込み"""
        # Arrange & Act
        with patch.dict(os.environ, REQUIRED_ENV_VARS, clear=True):
            from app.core.config import Settings
            settings = Settings()

        # Assert - 9個の必須APIキー/URL
        assert settings.GPT5_1_CHAT_API_KEY == "test-gpt5-1-chat-key"
        assert settings.GPT5_1_CODEX_API_KEY == "test-gpt5-1-codex-key"
        assert settings.GPT5_2_API_KEY == "test-gpt5-2-key"
        assert settings.GPT5_MINI_API_KEY == "test-gpt5-mini-key"
        assert settings.GPT5_NANO_API_KEY == "test-gpt5-nano-key"
        assert settings.CLAUDE_HAIKU_4_5_KEY == "test-claude-haiku-key"
        assert settings.CLAUDE_SONNET_4_5_KEY == "test-claude-sonnet-key"
        assert settings.GEMINI_API_KEY == "test-gemini-key"
        assert settings.DOCKER_BASE_URL == "http://localhost:11434"
```

### 2.2 デフォルト値テスト

```python
class TestDefaultValues:
    """デフォルト値検証テスト"""

    @pytest.fixture
    def settings_with_defaults(self):
        """必須フィールドのみ設定したSettingsインスタンス"""
        with patch.dict(os.environ, REQUIRED_ENV_VARS, clear=True):
            from app.core.config import Settings
            return Settings()

    def test_model_name_defaults(self, settings_with_defaults):
        """CFG-002: モデル名フィールドのデフォルト値検証（7フィールド）"""
        s = settings_with_defaults
        assert s.MODEL_NAME == "gpt-5.1-chat"
        assert s.MINI_MODEL_NAME == "gpt-5-mini"
        assert s.NANO_MODEL_NAME == "gpt-5-nano"
        assert s.CLAUDE_MODEL_NAME == "bedrock-claude-sonnet"
        assert s.CLAUDE_MINI_MODEL_NAME == "bedrock-claude-haiku"
        assert s.GEMINI_MODEL_NAME == "gemini-2.5-flash"
        assert s.MCP_AGENT_MODEL == "gpt-5-mini"

    def test_opensearch_and_embedding_defaults(self, settings_with_defaults):
        """CFG-003: OpenSearch・Embeddingフィールドのデフォルト値検証"""
        s = settings_with_defaults
        assert s.OPENSEARCH_INDEX_RAG == "cloudcustodian-enhanced-docs"
        assert s.OPENSEARCH_USER is None
        assert s.OPENSEARCH_PASSWORD is None
        assert s.OPENSEARCH_CA_CERTS_PATH is None
        assert s.EMBEDDING_MODEL_NAME == "text-embedding-3-large"

    def test_jwt_defaults(self, settings_with_defaults):
        """CFG-004: JWT設定のデフォルト値検証"""
        s = settings_with_defaults
        assert s.JWT_SECRET_KEY is None
        assert s.JWT_ALGORITHM == "HS256"
        assert s.JWT_EXPIRE_MINUTES == 30

    def test_langgraph_defaults(self, settings_with_defaults):
        """CFG-005: LangGraph設定のデフォルト値検証"""
        s = settings_with_defaults
        assert s.LANGGRAPH_STORAGE_TYPE == "memory"
        assert s.LANGGRAPH_POSTGRES_URL is None

    def test_rate_debug_defaults(self, settings_with_defaults):
        """CFG-006: RPM_LIMIT/DEBUG_MODEのデフォルト値検証"""
        s = settings_with_defaults
        assert s.RPM_LIMIT == 5
        assert s.DEBUG_MAX_ITEMS is None
        assert s.DEBUG_MODE is False

    def test_optional_fields_none_when_unset(self, settings_with_defaults):
        """CFG-007: Optionalフィールド未設定時にNone"""
        s = settings_with_defaults
        assert s.AWS_REGION is None
        assert s.AWS_SESSION_TOKEN is None
        assert s.CSPM_DASHBOARD_READ_USER is None
        assert s.CSPM_DASHBOARD_READ_PASSWORD is None
        assert s.RAG_SEARCH_READ_USER is None
        assert s.RAG_SEARCH_READ_PASSWORD is None
        assert s.DOCUMENT_WRITE_USER is None
        assert s.DOCUMENT_WRITE_PASSWORD is None
        assert s.CSPM_JOB_EXEC_USER is None
        assert s.CSPM_JOB_EXEC_PASSWORD is None
```

### 2.3 validation_aliasテスト

```python
class TestValidationAlias:
    """validation_alias（環境変数エイリアス）テスト

    各テストでは、REQUIRED_ENV_VARSがエイリアス名（正式フィールド名とは異なる名前）
    で値を設定していることを利用してエイリアス機能を検証する。
    - GEMINI_API_KEY ← GEMINI_API（環境変数名）で設定
    - EMBEDDING_API_KEY ← EMBEDDING_3_LARGE_API_KEY（環境変数名）で設定
    """

    def test_gemini_api_key_alias(self):
        """CFG-009: GEMINI_API_KEYのvalidation_alias（GEMINI_API）動作確認

        環境変数名は "GEMINI_API" だが、Settingsフィールド名は "GEMINI_API_KEY"。
        REQUIRED_ENV_VARSには "GEMINI_API" のみ設定されているため、
        このテストが成功すればエイリアスが正しく機能している。
        """
        # Arrange - GEMINI_APIという名前で環境変数を設定（GEMINI_API_KEYではない）
        env = REQUIRED_ENV_VARS.copy()
        assert "GEMINI_API" in env, "REQUIRED_ENV_VARSにはエイリアス名で設定されている"
        assert "GEMINI_API_KEY" not in env, "正式フィールド名では設定されていない"

        # Act
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings
            settings = Settings()

        # Assert - エイリアス経由でGEMINI_API_KEYに読み込まれている
        assert settings.GEMINI_API_KEY == "test-gemini-key"

    def test_embedding_api_key_alias(self):
        """CFG-010: EMBEDDING_API_KEYのvalidation_alias（EMBEDDING_3_LARGE_API_KEY）動作確認

        環境変数名は "EMBEDDING_3_LARGE_API_KEY" だが、
        Settingsフィールド名は "EMBEDDING_API_KEY"。
        """
        # Arrange
        env = REQUIRED_ENV_VARS.copy()
        assert "EMBEDDING_3_LARGE_API_KEY" in env, "エイリアス名で設定されている"
        assert "EMBEDDING_API_KEY" not in env, "正式フィールド名では設定されていない"

        # Act
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings
            settings = Settings()

        # Assert - エイリアス経由でEMBEDDING_API_KEYに読み込まれている
        assert settings.EMBEDDING_API_KEY == "test-embedding-key"

    def test_embedding_model_base_url_alias(self):
        """CFG-011: EMBEDDING_MODEL_BASE_URLのalias（DOCKER_BASE_URL）動作確認

        EMBEDDING_MODEL_BASE_URLとDOCKER_BASE_URLは同じvalidation_alias
        （DOCKER_BASE_URL）を持つため、同じ値が格納される。
        """
        # Arrange & Act
        with patch.dict(os.environ, REQUIRED_ENV_VARS, clear=True):
            from app.core.config import Settings
            settings = Settings()

        # Assert - DOCKER_BASE_URLの値がEMBEDDING_MODEL_BASE_URLにも格納される
        assert settings.EMBEDDING_MODEL_BASE_URL == "http://localhost:11434"
        assert settings.DOCKER_BASE_URL == settings.EMBEDDING_MODEL_BASE_URL
```

### 2.4 AWS・ロールベース認証情報テスト

```python
class TestAWSAndRoleBasedAuth:
    """AWS設定・ロールベース認証情報テスト"""

    def test_aws_settings_loaded(self):
        """CFG-012: AWS設定（REGION, SESSION_TOKEN）の読み込み"""
        # Arrange
        env = {
            **REQUIRED_ENV_VARS,
            "AWS_REGION": "ap-northeast-1",
            "AWS_SESSION_TOKEN": "test-session-token",
        }

        # Act
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings
            settings = Settings()

        # Assert
        assert settings.AWS_REGION == "ap-northeast-1"
        assert settings.AWS_SESSION_TOKEN == "test-session-token"

    def test_role_based_opensearch_credentials(self):
        """CFG-013: ロールベースOpenSearch認証情報の読み込み（4ロール全て）"""
        # Arrange
        env = {
            **REQUIRED_ENV_VARS,
            "CSPM_DASHBOARD_READ_USER": "dashboard-reader",
            "CSPM_DASHBOARD_READ_PASSWORD": "dashboard-pass",
            "RAG_SEARCH_READ_USER": "rag-reader",
            "RAG_SEARCH_READ_PASSWORD": "rag-pass",
            "DOCUMENT_WRITE_USER": "doc-writer",
            "DOCUMENT_WRITE_PASSWORD": "doc-pass",
            "CSPM_JOB_EXEC_USER": "job-executor",
            "CSPM_JOB_EXEC_PASSWORD": "job-pass",
        }

        # Act
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings
            settings = Settings()

        # Assert - 4ロール全て検証
        assert settings.CSPM_DASHBOARD_READ_USER == "dashboard-reader"
        assert settings.CSPM_DASHBOARD_READ_PASSWORD == "dashboard-pass"
        assert settings.RAG_SEARCH_READ_USER == "rag-reader"
        assert settings.RAG_SEARCH_READ_PASSWORD == "rag-pass"
        assert settings.DOCUMENT_WRITE_USER == "doc-writer"
        assert settings.DOCUMENT_WRITE_PASSWORD == "doc-pass"
        assert settings.CSPM_JOB_EXEC_USER == "job-executor"
        assert settings.CSPM_JOB_EXEC_PASSWORD == "job-pass"
```

### 2.5 MIN_INTERVAL_SECONDS 派生値テスト

```python
class TestMinIntervalSeconds:
    """MIN_INTERVAL_SECONDS 派生値計算テスト

    注意: MIN_INTERVAL_SECONDSはモジュールレベルで一度だけ評価される変数のため、
    テストではSettings.RPM_LIMITから期待値を再計算して検証する。
    モジュール変数の直接テストも併せて実施する。
    """

    def test_rpm_limit_5_gives_12_seconds(self):
        """CFG-014: MIN_INTERVAL_SECONDS計算（RPM_LIMIT=5→12.0秒）"""
        # Arrange & Act
        # デフォルトRPM_LIMIT=5の場合: 60.0 / 5 = 12.0
        with patch.dict(os.environ, REQUIRED_ENV_VARS, clear=True):
            from app.core.config import Settings
            settings = Settings()
            min_interval = 60.0 / settings.RPM_LIMIT if settings.RPM_LIMIT > 0 else float('inf')

        # Assert
        assert settings.RPM_LIMIT == 5
        assert min_interval == 12.0

        # モジュール変数の直接確認（モジュールが既にロード済みの場合の実値）
        from app.core.config import MIN_INTERVAL_SECONDS, settings as module_settings
        expected = 60.0 / module_settings.RPM_LIMIT if module_settings.RPM_LIMIT > 0 else float('inf')
        assert MIN_INTERVAL_SECONDS == expected

    def test_rpm_limit_60_gives_1_second(self):
        """CFG-015: MIN_INTERVAL_SECONDS計算（RPM_LIMIT=60→1.0秒）"""
        # Arrange
        env = {**REQUIRED_ENV_VARS, "RPM_LIMIT": "60"}

        # Act
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings
            settings = Settings()
            min_interval = 60.0 / settings.RPM_LIMIT if settings.RPM_LIMIT > 0 else float('inf')

        # Assert
        assert settings.RPM_LIMIT == 60
        assert min_interval == 1.0
```

### 2.6 is_aws_opensearch_service テスト

```python
class TestIsAWSOpenSearchService:
    """AWS OpenSearch判定ヘルパー関数テスト"""

    def test_aws_es_url_returns_true(self):
        """CFG-016: is_aws_opensearch_service: AWS ES URLでTrue"""
        from app.core.config import is_aws_opensearch_service
        assert is_aws_opensearch_service("https://search-domain.es.amazonaws.com") is True

    def test_aws_aoss_url_returns_true(self):
        """CFG-017: is_aws_opensearch_service: AWS AOSS URLでTrue"""
        from app.core.config import is_aws_opensearch_service
        assert is_aws_opensearch_service("https://collection-id.aoss.amazonaws.com") is True

    def test_local_url_returns_false(self):
        """CFG-018: is_aws_opensearch_service: ローカルURLでFalse"""
        from app.core.config import is_aws_opensearch_service
        assert is_aws_opensearch_service("https://localhost:9200") is False
        assert is_aws_opensearch_service("https://opensearch.example.com") is False

    def test_aws_url_with_port_returns_true(self):
        """CFG-019: is_aws_opensearch_service: ポート付きAWS URLでTrue"""
        from app.core.config import is_aws_opensearch_service
        assert is_aws_opensearch_service("https://search-domain.es.amazonaws.com:443") is True
```

### 2.7 model_config設定テスト

```python
class TestModelConfig:
    """model_config（SettingsConfigDict）テスト"""

    def test_model_config_settings(self):
        """CFG-020: model_configのcase_sensitive/extra設定確認"""
        # Arrange
        from app.core.config import Settings

        # Assert
        config = Settings.model_config
        assert config.get("case_sensitive") is True
        assert config.get("extra") == "ignore"
        assert config.get("env_file") == ".env"
        assert config.get("env_file_encoding") == "utf-8"
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CFG-E01 | 必須フィールド欠落でValidationError | 環境変数なし | ValidationError |
| CFG-E02 | RPM_LIMIT=0でMIN_INTERVAL_SECONDS=inf | RPM_LIMIT=0 | float('inf') |
| CFG-E03 | RPM_LIMITに文字列でValidationError | RPM_LIMIT="abc" | ValidationError |
| CFG-E04 | JWT_EXPIRE_MINUTESに負数 | JWT_EXPIRE_MINUTES=-1 | 負数が格納される（バリデーションなし） |
| CFG-E05 | 初期化失敗時にSystemExit発生 | 必須未設定でモジュールimport | SystemExit |
| CFG-E06 | is_aws: 空文字列URLでFalse | "" | False |
| CFG-E07 | is_aws: hostnameなしURL（"not-a-url"）でFalse | "not-a-url" | False |
| CFG-E08 | is_aws: .es.あるが.amazonaws.comなしでFalse | .es.example.com URL | False |
| CFG-E09 | is_aws: プロトコルなしURLでFalse | domain.es.amazonaws.com（httpsなし） | False |
| CFG-E10 | extra='ignore'で未知フィールドが無視される | 未知の環境変数追加 | エラーなし |

### 3.1 Settings初期化異常系

```python
class TestSettingsErrors:
    """Settings初期化エラーテスト"""

    def test_missing_required_field_raises_validation_error(self):
        """CFG-E01: 必須フィールド欠落でValidationError"""
        # Arrange - 必須フィールドを一切設定しない
        with patch.dict(os.environ, {}, clear=True):
            from app.core.config import Settings

            # Act & Assert
            with pytest.raises(ValidationError):
                Settings()

    def test_rpm_limit_zero_gives_infinity(self):
        """CFG-E02: RPM_LIMIT=0でMIN_INTERVAL_SECONDS=inf

        Settings.RPM_LIMITからの再計算検証に加え、
        importlib.reloadでモジュール変数MIN_INTERVAL_SECONDSを直接検証する。
        """
        import sys
        import importlib

        # Arrange
        env = {**REQUIRED_ENV_VARS, "RPM_LIMIT": "0"}

        # Act - Settingsインスタンスからの再計算
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings
            settings = Settings()
            min_interval = 60.0 / settings.RPM_LIMIT if settings.RPM_LIMIT > 0 else float('inf')

        # Assert - 再計算による検証
        assert settings.RPM_LIMIT == 0
        assert math.isinf(min_interval)

        # モジュール変数の直接検証（RPM_LIMIT=0でreloadした場合）
        saved_modules = {}
        for mod_name in list(sys.modules):
            if mod_name == 'app.core.config' or mod_name.startswith('app.core.config.'):
                saved_modules[mod_name] = sys.modules.pop(mod_name)
        try:
            with patch.dict(os.environ, env, clear=True):
                config_module = importlib.import_module('app.core.config')
                assert math.isinf(config_module.MIN_INTERVAL_SECONDS)
        finally:
            for mod_name in list(sys.modules):
                if mod_name.startswith('app.core.config'):
                    del sys.modules[mod_name]
            sys.modules.update(saved_modules)

    def test_rpm_limit_string_raises_validation_error(self):
        """CFG-E03: RPM_LIMITに文字列でValidationError"""
        # Arrange
        env = {**REQUIRED_ENV_VARS, "RPM_LIMIT": "not-a-number"}

        # Act & Assert
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings
            with pytest.raises(ValidationError):
                Settings()

    def test_jwt_expire_minutes_negative(self):
        """CFG-E04: JWT_EXPIRE_MINUTESに負数

        現在の実装では値の範囲バリデーションがないため、負数がそのまま格納される。
        本番運用では正の値のバリデーションを追加すべき。
        """
        # Arrange
        env = {**REQUIRED_ENV_VARS, "JWT_EXPIRE_MINUTES": "-1"}

        # Act
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings
            settings = Settings()

        # Assert - 負数がそのまま格納される（バリデーションなし）
        assert settings.JWT_EXPIRE_MINUTES == -1

    def test_settings_init_failure_raises_system_exit(self):
        """CFG-E05: 初期化失敗時にSystemExit発生

        config.pyのモジュールレベルで Settings() 初期化が失敗した場合、
        except節でSystemExitが発生することを検証（config.py:115-118）。

        importlibで動的にモジュールをロードし、モジュールレベルの
        try-except → SystemExit パスを直接テストする。
        """
        import sys
        import importlib

        # Arrange - 既存のモジュールキャッシュを退避・削除
        saved_modules = {}
        for mod_name in list(sys.modules):
            if mod_name.startswith('app.core.config') or mod_name == 'app.core.config':
                saved_modules[mod_name] = sys.modules.pop(mod_name)

        try:
            # Act & Assert - 必須フィールド欠落状態でモジュールをインポート
            with patch.dict(os.environ, {}, clear=True):
                with pytest.raises(SystemExit) as exc_info:
                    importlib.import_module('app.core.config')

                assert "Configuration error" in str(exc_info.value)
        finally:
            # Cleanup - 元のモジュールキャッシュを復元
            for mod_name in list(sys.modules):
                if mod_name.startswith('app.core.config'):
                    del sys.modules[mod_name]
            sys.modules.update(saved_modules)

    def test_extra_ignore_unknown_fields(self):
        """CFG-E10: extra='ignore'で未知フィールドが無視される"""
        # Arrange - 未知の環境変数を追加
        env = {
            **REQUIRED_ENV_VARS,
            "UNKNOWN_SETTING": "should-be-ignored",
            "ANOTHER_UNKNOWN": "also-ignored",
        }

        # Act - エラーなく初期化できること
        with patch.dict(os.environ, env, clear=True):
            from app.core.config import Settings
            settings = Settings()

        # Assert - 未知フィールドはSettingsオブジェクトに含まれない
        assert not hasattr(settings, "UNKNOWN_SETTING")
        assert not hasattr(settings, "ANOTHER_UNKNOWN")
```

### 3.2 is_aws_opensearch_service 異常系

```python
class TestIsAWSOpenSearchServiceErrors:
    """AWS OpenSearch判定ヘルパー関数エラーテスト"""

    def test_empty_string_returns_false(self):
        """CFG-E06: is_aws: 空文字列URLでFalse"""
        from app.core.config import is_aws_opensearch_service
        assert is_aws_opensearch_service("") is False

    def test_no_hostname_url_returns_false(self):
        """CFG-E07: is_aws: hostnameなしURL（スキームなし/相対パス）でFalse

        urlparse()はスキーム（https://等）がない場合、URL全体をpathとして解釈し、
        hostname=Noneを返す。これによりconfig.py:130の条件1（parsed_url.hostname）
        でショートサーキットされFalseとなる。
        """
        from app.core.config import is_aws_opensearch_service
        assert is_aws_opensearch_service("not-a-url") is False

    def test_es_without_amazonaws_returns_false(self):
        """CFG-E08: is_aws: .es.あるが.amazonaws.comなしでFalse"""
        from app.core.config import is_aws_opensearch_service
        assert is_aws_opensearch_service("https://search.es.example.com") is False

    def test_amazonaws_without_es_or_aoss_returns_false(self):
        """CFG-E08b: is_aws: .amazonaws.comあるが.es./.aoss.なしでFalse

        hostname に .amazonaws.com を含むが、.es. も .aoss. も含まないケース。
        config.py:131 の '.es.' in hostname or '.aoss.' in hostname 分岐をカバーする。
        """
        from app.core.config import is_aws_opensearch_service
        assert is_aws_opensearch_service("https://amazonaws.com") is False
        assert is_aws_opensearch_service("https://s3.amazonaws.com") is False
        assert is_aws_opensearch_service("https://lambda.amazonaws.com") is False

    def test_no_protocol_url_returns_false(self):
        """CFG-E09: is_aws: プロトコルなしURLでFalse

        urlparse("domain.es.amazonaws.com")はscheme="domain.es.amazonaws.com"、
        hostname=Noneとなるため、Falseが返る。
        """
        from app.core.config import is_aws_opensearch_service
        assert is_aws_opensearch_service("domain.es.amazonaws.com") is False
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CFG-SEC-01 | 初期化ログにAPIキー/パスワードが出力されない | 全フィールド設定 | ログに機密値なし |
| CFG-SEC-02 | OPENSEARCH_USER設定時にマスク表示（********） | OPENSEARCH_USER設定 | "********"表示 |
| CFG-SEC-03 | DEBUG_MODEのデフォルト値がFalse（本番安全） | 未設定 | False |
| CFG-SEC-04 | JWT_SECRET_KEY未設定時の挙動確認 | JWT_SECRET_KEY未設定 | None |
| CFG-SEC-05 | is_aws: 大文字小文字混在URLの挙動確認 | 大文字混在URL | True（urlparse hostname小文字正規化） |

### 4.1 機密情報漏洩防止テスト

```python
@pytest.mark.security
class TestConfigSecurity:
    """設定セキュリティテスト"""

    def test_init_log_does_not_expose_secrets(self, capsys):
        """CFG-SEC-01: 初期化ログにAPIキー/パスワードが出力されない

        config.pyのモジュールレベル初期化時のprint出力（config.py:111-114）に
        APIキーやパスワードの値が含まれないことを検証。

        注意: config.pyはインポート時にモジュールレベルでprint()を実行するため、
        sys.modulesから削除して再インポートすることで実際のログ出力をキャプチャする。
        """
        import sys
        import importlib

        # Arrange
        env = {
            **REQUIRED_ENV_VARS,
            "OPENSEARCH_USER": "admin-user",
            "OPENSEARCH_PASSWORD": "super-secret-password",
        }

        # 既存のモジュールキャッシュを退避・削除
        saved_modules = {}
        for mod_name in list(sys.modules):
            if mod_name.startswith('app.core.config') or mod_name == 'app.core.config':
                saved_modules[mod_name] = sys.modules.pop(mod_name)

        try:
            # Act - モジュール再インポートで実際のprint出力をキャプチャ
            with patch.dict(os.environ, env, clear=True):
                importlib.import_module('app.core.config')

            # Assert - キャプチャした出力に機密値が含まれないこと
            captured = capsys.readouterr()
            secret_values = [
                "test-gpt5-1-chat-key", "test-gpt5-1-codex-key",
                "test-gpt5-2-key", "test-gpt5-mini-key",
                "test-gpt5-nano-key", "test-claude-haiku-key",
                "test-claude-sonnet-key", "test-gemini-key",
                "test-embedding-key", "super-secret-password",
            ]
            for secret in secret_values:
                assert secret not in captured.out, (
                    f"初期化ログに機密値 '{secret}' が出力されています"
                )
        finally:
            # Cleanup - 元のモジュールキャッシュを復元
            for mod_name in list(sys.modules):
                if mod_name.startswith('app.core.config'):
                    del sys.modules[mod_name]
            sys.modules.update(saved_modules)

    def test_opensearch_user_masked_in_log(self, capsys):
        """CFG-SEC-02: OPENSEARCH_USER設定時にマスク表示（********）

        config.py:114 の条件分岐で、OPENSEARCH_USER設定時に
        "********" が表示されることを検証。
        sys.modules再インポートで実際のprint出力をキャプチャする。
        """
        import sys
        import importlib

        # Arrange
        env = {
            **REQUIRED_ENV_VARS,
            "OPENSEARCH_USER": "admin-user",
        }

        # 既存のモジュールキャッシュを退避・削除
        saved_modules = {}
        for mod_name in list(sys.modules):
            if mod_name.startswith('app.core.config') or mod_name == 'app.core.config':
                saved_modules[mod_name] = sys.modules.pop(mod_name)

        try:
            # Act - モジュール再インポートで実際のprint出力をキャプチャ
            with patch.dict(os.environ, env, clear=True):
                importlib.import_module('app.core.config')

            # Assert - "********" がログに含まれ、"admin-user" は含まれない
            captured = capsys.readouterr()
            assert "********" in captured.out, (
                "OPENSEARCH_USER設定時にマスク表示されていません"
            )
            assert "admin-user" not in captured.out, (
                "OPENSEARCH_USERの実値がログに出力されています"
            )
        finally:
            # Cleanup
            for mod_name in list(sys.modules):
                if mod_name.startswith('app.core.config'):
                    del sys.modules[mod_name]
            sys.modules.update(saved_modules)

    def test_debug_mode_default_is_false(self):
        """CFG-SEC-03: DEBUG_MODEのデフォルト値がFalse（本番安全）

        DEBUG_MODE=Trueは認証スキップを意味するため、
        デフォルトがFalse（本番安全）であることは重要。
        """
        # Arrange & Act
        with patch.dict(os.environ, REQUIRED_ENV_VARS, clear=True):
            from app.core.config import Settings
            settings = Settings()

        # Assert
        assert settings.DEBUG_MODE is False

    def test_jwt_secret_key_none_when_unset(self):
        """CFG-SEC-04: JWT_SECRET_KEY未設定時の挙動確認

        JWT_SECRET_KEY=Noneの場合、JWT認証が動作しない可能性がある。
        アプリケーション側で適切にチェックする必要がある。
        """
        # Arrange & Act
        with patch.dict(os.environ, REQUIRED_ENV_VARS, clear=True):
            from app.core.config import Settings
            settings = Settings()

        # Assert
        assert settings.JWT_SECRET_KEY is None

    def test_is_aws_case_sensitivity(self):
        """CFG-SEC-05: is_aws: 大文字小文字混在URLの挙動確認

        URLのhostname部分はPython標準のurlparse()により小文字に正規化されるため、
        大文字混在でもAWS OpenSearchサービスとして正しく判定されることを検証。
        セキュリティ観点: 大文字混在によるバイパスが不可能であることを確認。
        """
        from app.core.config import is_aws_opensearch_service

        # urlparse はhostnameを小文字に正規化する（Python 3.x標準動作）
        assert is_aws_opensearch_service("https://Search-Domain.ES.AMAZONAWS.COM") is True
        assert is_aws_opensearch_service("https://Collection.AOSS.AMAZONAWS.COM") is True
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ |
|--------------|------|---------|
| `REQUIRED_ENV_VARS` | 全必須フィールドを含むテスト用環境変数辞書（モジュール定数） | - |
| `reset_config_module` | 各テスト前後でconfig moduleのsys.modulesキャッシュをリセット | function |
| `settings_with_defaults` | 必須フィールドのみ設定したSettingsインスタンス | function |
| `capsys` | pytest組み込み（stdout/stderrキャプチャ） | function |

### 共通フィクスチャ定義

```python
# test/unit/core/conftest.py に追加
import sys
import os
import pytest
from unittest.mock import patch

# 全必須フィールドを含むテスト用環境変数辞書
REQUIRED_ENV_VARS = {
    "GPT5_1_CHAT_API_KEY": "test-gpt5-1-chat-key",
    "GPT5_1_CODEX_API_KEY": "test-gpt5-1-codex-key",
    "GPT5_2_API_KEY": "test-gpt5-2-key",
    "GPT5_MINI_API_KEY": "test-gpt5-mini-key",
    "GPT5_NANO_API_KEY": "test-gpt5-nano-key",
    "CLAUDE_HAIKU_4_5_KEY": "test-claude-haiku-key",
    "CLAUDE_SONNET_4_5_KEY": "test-claude-sonnet-key",
    "GEMINI_API": "test-gemini-key",
    "DOCKER_BASE_URL": "http://localhost:11434",
    "EMBEDDING_3_LARGE_API_KEY": "test-embedding-key",
    "OPENSEARCH_URL": "https://localhost:9200",
}

@pytest.fixture(autouse=True)
def reset_config_module():
    """各テスト前後でconfig moduleのsys.modulesキャッシュをリセット

    config.pyはモジュールレベルでsettingsインスタンスを作成するため、
    環境変数を変更するテストでは既存のキャッシュを削除して
    再インポートする必要がある。

    注意: autouse=Trueにより、全テストで自動適用される。
    """
    yield
    # テスト後にクリーンアップ（次のテストに影響を与えない）
    for mod_name in list(sys.modules):
        if mod_name == 'app.core.config' or mod_name.startswith('app.core.config.'):
            del sys.modules[mod_name]

@pytest.fixture
def settings_with_defaults():
    """必須フィールドのみ設定したSettingsインスタンス"""
    with patch.dict(os.environ, REQUIRED_ENV_VARS, clear=True):
        from app.core.config import Settings
        return Settings()
```

---

## 6. テスト実行例

```bash
# config関連テストのみ実行
pytest test/unit/core/test_config.py -v

# 特定のテストクラスのみ実行
pytest test/unit/core/test_config.py::TestSettingsInitialization -v
pytest test/unit/core/test_config.py::TestDefaultValues -v
pytest test/unit/core/test_config.py::TestValidationAlias -v
pytest test/unit/core/test_config.py::TestIsAWSOpenSearchService -v
pytest test/unit/core/test_config.py::TestConfigSecurity -v

# カバレッジ付きで実行
pytest test/unit/core/test_config.py --cov=app.core.config --cov-report=term-missing -v

# セキュリティマーカーで実行（pytest.iniまたはpyproject.tomlにマーカー登録が必要）
# [tool.pytest.ini_options]
# markers = ["security: セキュリティ関連テスト"]
pytest test/unit/core/test_config.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 20 | CFG-001 〜 CFG-020 |
| 異常系 | 10 | CFG-E01 〜 CFG-E10 |
| セキュリティ | 5 | CFG-SEC-01 〜 CFG-SEC-05 |
| **合計** | **35** | - |

### テスト実行時の注意事項

以下のテストは環境依存やモジュールキャッシュの影響を受けやすいため、注意が必要です。

| テストID | 注意点 | 対策 |
|---------|--------|------|
| CFG-SEC-01 | モジュール再インポート+capsysキャプチャのため、テスト実行順序やload_dotenv()の影響を受ける | `reset_config_module`フィクスチャで毎回リセット。必要に応じて`load_dotenv`をno-op化 |
| CFG-SEC-02 | 同上（モジュール再インポートによるログキャプチャ） | 同上 |
| CFG-E05 | importlibで動的インポートするため、`.env`ファイルの存在に影響される | `load_dotenv`をno-op化するか、テスト環境に`.env`を配置しない |
| CFG-SEC-05 | `urlparse().hostname`の小文字正規化に依存。Python標準動作として通常は成功する | Python 3.x の`urlparse`仕様に基づき成功を期待 |

---

## 8. 既知の制限事項

### 8.1 モジュールレベル初期化の制約

`config.py` はインポート時に `settings = Settings()` をモジュールレベルで実行する。
そのため、環境変数を変更する各テストでは `sys.modules` からキャッシュを削除して
再インポートする必要がある。

- **対策**: `conftest.py` に `reset_config_module` フィクスチャ（`autouse=True`）を追加
- 各テスト終了後にキャッシュを自動クリーンアップする

### 8.2 モジュール変数のテスト制約

`MIN_INTERVAL_SECONDS` はモジュールレベルで一度だけ評価される。
異なる `RPM_LIMIT` 値でのテストは、`Settings` インスタンスから再計算して検証する。

- CFG-014: モジュール変数の直接参照テストも併せて実施
- CFG-E02: `RPM_LIMIT=0` の分岐は `Settings` インスタンスから再計算で検証

### 8.3 ログ出力のテスト制約

モジュールレベルの `print()` 文（`config.py:111-114`）は一度だけ実行される。
`capsys` でキャプチャするには、`sys.modules` からモジュールを削除して再インポートする必要がある。

- CFG-SEC-01: `importlib.import_module()` で再インポートし、実際のログ出力をテスト
- テスト実行順序の影響を受けないよう `reset_config_module` フィクスチャで保護

### 8.4 load_dotenv()による.env依存

`config.py:7` の `load_dotenv()` により、インポート時に `.env` ファイルが存在すると
その内容が環境変数に読み込まれる。テスト環境に `.env` が存在する場合、
`patch.dict(os.environ, ..., clear=True)` で環境変数をクリアしても、
モジュール再インポート時に `load_dotenv()` が再実行され `.env` の値が復活する。

- **対策**: `load_dotenv` を無効化する（例: `patch("app.core.config.load_dotenv")` で no-op 化）
- テスト環境では `.env` ファイルを配置しないか、テスト用 `.env.test` を使用する
- 特に CFG-E05（SystemExit）・CFG-SEC-01（ログキャプチャ）で影響が大きい

```python
# load_dotenv無効化の例
# config.py で from dotenv import load_dotenv としているため、
# パッチ対象はモジュール内の名前空間にある load_dotenv
with patch("app.core.config.load_dotenv"):  # no-op化
    with patch.dict(os.environ, env, clear=True):
        importlib.import_module('app.core.config')
```

### 8.5 validation_aliasのテスト方針

`REQUIRED_ENV_VARS` はエイリアス名（環境変数で実際に使用する名前）で値を設定している。
テストコード内でエイリアス名と正式フィールド名の不一致を `assert` で明示的に確認し、
エイリアスが正しく機能していることを検証する（CFG-009, CFG-010）。
