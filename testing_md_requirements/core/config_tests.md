# config テストケース

## 1. 概要

設定管理サービスのテストケースを定義します。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `settings` | Pydanticベースの設定オブジェクト |
| 環境変数読み込み | .envファイルからの設定読み込み |
| 設定バリデーション | 必須設定の検証 |

### 1.2 カバレッジ目標: 85%

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CFG-001 | 環境変数から設定読み込み | valid env vars | 設定オブジェクト |
| CFG-002 | デフォルト値の適用 | missing optional vars | デフォルト値使用 |
| CFG-003 | OpenSearch URL生成 | host + port | 正しいURL |
| CFG-004 | AWS OpenSearch判定 | .es.amazonaws.com | True |

```python
# test/unit/core/test_config.py
import pytest
import os
from unittest.mock import patch

class TestSettings:
    """設定テスト"""

    def test_load_from_env(self):
        """CFG-001: 環境変数から設定読み込み"""
        # Arrange
        env_vars = {
            "OPENSEARCH_HOST": "localhost",
            "OPENSEARCH_PORT": "9200",
            "OPENAI_API_KEY": "test-key"
        }

        # Act
        with patch.dict(os.environ, env_vars):
            from app.core.config import Settings
            settings = Settings()

        # Assert
        assert settings.OPENSEARCH_HOST == "localhost"
        assert settings.OPENSEARCH_PORT == 9200

    def test_default_values(self):
        """CFG-002: デフォルト値の適用"""
        # Arrange & Act
        from app.core.config import Settings
        settings = Settings()

        # Assert
        assert settings.LOG_LEVEL is not None  # デフォルト値が設定されている

    def test_opensearch_url_generation(self):
        """CFG-003: OpenSearch URL生成"""
        # Arrange
        with patch.dict(os.environ, {
            "OPENSEARCH_HOST": "localhost",
            "OPENSEARCH_PORT": "9200"
        }):
            from app.core.config import settings

        # Assert
        assert "localhost" in settings.OPENSEARCH_URL
        assert "9200" in settings.OPENSEARCH_URL
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CFG-E01 | 必須設定の欠落 | missing required | ValidationError |
| CFG-E02 | 無効な型 | port="invalid" | ValidationError |

```python
class TestSettingsErrors:
    """設定エラーテスト"""

    def test_invalid_port_type(self):
        """CFG-E02: 無効な型でエラー"""
        # Arrange
        with patch.dict(os.environ, {"OPENSEARCH_PORT": "not-a-number"}):
            from app.core.config import Settings

            # Act & Assert
            with pytest.raises(Exception):
                Settings()
```

---

## 4. is_aws_opensearch_service テスト

```python
class TestIsAWSOpenSearchService:
    """AWS OpenSearch判定テスト"""

    def test_aws_opensearch_url(self):
        """CFG-004: AWS OpenSearch URL判定"""
        from app.core.config import is_aws_opensearch_service

        # AWS OpenSearch Service
        assert is_aws_opensearch_service("https://xxx.es.amazonaws.com") is True
        assert is_aws_opensearch_service("https://xxx.aoss.amazonaws.com") is True

        # ローカル/その他
        assert is_aws_opensearch_service("https://localhost:9200") is False
        assert is_aws_opensearch_service("https://opensearch.example.com") is False
```
