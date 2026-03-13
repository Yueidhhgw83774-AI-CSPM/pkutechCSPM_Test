# llm_factory テストケース

## 0. Enhanced版について

### 0.1 旧版との違い

本ドキュメントは `llm_factory_tests.md`（旧版）を全面的に書き直した改良版です。

| 項目 | 旧版（llm_factory_tests.md） | Enhanced版（本ドキュメント） |
|------|---------------------------|---------------------------|
| テストケース数 | 9件（正常5 + 異常4） | **55件**（正常39 + 異常11 + セキュリティ5） |
| 行数 | 157行 | 約900行 |
| カバレッジ目標 | 85% | **95%** |
| create_llm引数設計 | `provider="openai"` — 実装に存在しない引数 | **model_name/temperature/max_tokens/streaming/use_responses_api/kwargs** |
| エイリアス・モデル設定テスト | なし | **MODEL_ALIASES（15エイリアス）、MODEL_CONFIGS（7モデル）を網羅** |
| 便利関数テスト | なし | **get_llm/get_policy_llm/get_review_llm/get_production_llm** |
| セキュリティテスト | なし | **5件**（APIキー漏洩、エイリアス整合性、base_url統一等） |
| フィクスチャ設計 | 環境変数のみ | **reset_llm_factory_module（autouse）+ mock_chat_openai + mock_settings_env** |
| 既知の制限事項 | なし | **5項目** |

### 0.2 書き直しが必要だった理由

旧版には以下の問題があり、テスト仕様書としての実効性がほぼ0%でした：

1. **存在しない引数の使用**: `create_llm(provider="openai")` — 実装に`provider`引数は存在しない
2. **存在しない関数の参照**: `get_embedding_function()` — 実装に存在しない
3. **存在しない例外型**: `ConfigurationError`, `ModelNotFoundError`, `RateLimitError` — 実際はすべて`ValueError`
4. **存在しないフィールド名**: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` — config.pyに存在しない
5. **Anthropic直接使用の想定**: 実装は全モデルが`ChatOpenAI`経由
6. **MODEL_CONFIGS/MODEL_ALIASES/便利関数が全くカバーされていない**: 415行中の主要ロジックが未テスト

---

## 1. 概要

LLMファクトリー（`llm_factory.py`）のテストケースを定義します。
モデルインスタンス生成の一元管理機能として、エイリアス解決、パラメータ構築、カテゴリ管理、便利関数を網羅的に検証します。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `LLMFactory.create_llm()` | モデル名/エイリアス解決、パラメータ構築、ChatOpenAIインスタンス生成 |
| `LLMFactory.get_model_info()` | エイリアス解決→モデル設定情報を返却 |
| `LLMFactory.list_available_models()` | 全7モデルの名前と説明を取得 |
| `LLMFactory.list_models_by_category()` | カテゴリ別モデルリストアップ（production/development/lightweight） |
| `LLMFactory.get_all_categories()` | 全カテゴリのモデル一覧を取得 |
| `LLMFactory.add_model_config()` | 新規モデル設定を動的追加 |
| `get_llm()` | デフォルトでResponses API使用の簡易関数 |
| `get_policy_llm()` | ポリシー生成用LLM取得（"policy"エイリアス） |
| `get_review_llm()` | ポリシーレビュー用LLM取得（"review"エイリアス） |
| `get_chat_llm()` | チャット用LLM取得（"chat"エイリアス） |
| `get_extraction_llm()` | 抽出・軽量タスク用LLM取得（"extraction"エイリアス） |
| `get_production_llm()` | 本番用高性能LLM取得（"production"エイリアス） |
| `get_development_llm()` | 開発用標準LLM取得（"development"エイリアス） |
| `get_lightweight_llm()` | 軽量作業用LLM取得（"lightweight"エイリアス） |

### 1.2 カバレッジ目標: 95%

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/core/llm_factory.py`（415行） |
| テストコード | `test/unit/core/test_llm_factory.py` |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| LLM-001 | model_name=None時にsettings.MODEL_NAME使用 | model_name=None | settings.MODEL_NAMEが使用される |
| LLM-002 | 全15エイリアス解決（パラメータ化テスト） | 各エイリアス名 | 正しいモデル名に解決される |
| LLM-003 | 直接モデル名指定 "gpt-5.1-chat" | model_name="gpt-5.1-chat" | そのまま使用 |
| LLM-004 | temperature引数優先（config:None, 引数:0.7） | temperature=0.7 | llm_params["temperature"]=0.7 |
| LLM-005 | temperature=None時はconfig値使用（config:0.1） | temperature=None, bedrock-claude-sonnet | llm_params["temperature"]=0.1 |
| LLM-006 | temperature=None・config:None時は省略 | temperature=None, gpt-5.1-chat | "temperature"キーなし |
| LLM-007 | max_completion_tokens使用（GPT-5系） | gpt-5.1-chat | llm_params["max_completion_tokens"]=16000 |
| LLM-008 | max_tokens使用（非GPT-5系） | bedrock-claude-sonnet | llm_params["max_tokens"]=8000 |
| LLM-009 | max_tokens引数で上書き（GPT-5系） | gpt-5.1-chat, max_tokens=5000 | llm_params["max_completion_tokens"]=5000 |
| LLM-010 | max_tokens引数で上書き（非GPT-5系） | bedrock-claude-sonnet, max_tokens=2000 | llm_params["max_tokens"]=2000 |
| LLM-011 | reasoning_effort追加（config値あり） | gpt-5.1-chat | llm_params["reasoning_effort"]="high" |
| LLM-012 | reasoning_effortなし（config未設定） | bedrock-claude-sonnet | "reasoning_effort"キーなし |
| LLM-013 | use_responses_api=True時に追加 | use_responses_api=True | llm_params["use_responses_api"]=True |
| LLM-014 | use_responses_api=False時は追加しない | use_responses_api=False | "use_responses_api"キーなし |
| LLM-015 | streaming=True設定 | streaming=True | llm_params["streaming"]=True |
| LLM-016 | kwargs追加パラメータ伝播 | top_p=0.9 | llm_params["top_p"]=0.9 |
| LLM-017 | get_model_info: エイリアス解決→config返却 | model_name="default" | gpt-5.1-chatのconfig辞書 |
| LLM-018 | list_available_models: 7モデル全列挙 | - | 7件のDict[str, str] |
| LLM-019 | list_models_by_category: "production"→4モデル | category="production" | 4モデル |
| LLM-020 | list_models_by_category: "development"→1モデル | category="development" | 1モデル |
| LLM-021 | list_models_by_category: "lightweight"→2モデル | category="lightweight" | 2モデル |
| LLM-022 | get_all_categories: 3カテゴリ取得 | - | 3カテゴリ辞書 |
| LLM-023 | add_model_config: 新規モデル追加成功 | 有効config | MODEL_CONFIGSに追加 |
| LLM-024 | get_llm: use_responses_api=Trueデフォルト | 引数なし | use_responses_api=True |
| LLM-025 | get_policy_llm: "policy"エイリアス使用 | - | model="gpt-5-mini" + use_responses_api=True |
| LLM-026 | get_review_llm: "review"エイリアス使用 | - | model="gpt-5.1-codex" + use_responses_api=True |
| LLM-027 | get_chat_llm: "chat"エイリアス使用 | - | model="gpt-5-mini" + use_responses_api=True |
| LLM-028 | get_extraction_llm: "extraction"エイリアス使用 | - | model="gpt-5-nano" + use_responses_api=True |
| LLM-029 | get_production_llm: "production"エイリアス | - | model="gpt-5.1-chat" + use_responses_api=True |
| LLM-030 | get_development_llm: "development"エイリアス | - | model="gpt-5-mini" + use_responses_api=True |
| LLM-031 | get_lightweight_llm: "lightweight"エイリアス | - | model="gpt-5-nano" + use_responses_api=True |

### 2.1 create_llm メソッドテスト

```python
# test/unit/core/test_llm_factory.py
import pytest
import sys
import os
from unittest.mock import patch, MagicMock, call


# テスト用環境変数（全モデルのAPIキーを網羅）
MOCK_SETTINGS_ENV = {
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
    "MODEL_NAME": "gpt-5.1-chat",
}


class TestLLMFactoryCreateLLM:
    """create_llmメソッドのテスト（LLM-001〜LLM-016）"""

    def test_model_name_none_uses_settings(self, mock_chat_openai, mock_settings_env):
        """LLM-001: model_name=None時にsettings.MODEL_NAME使用

        create_llm()をmodel_name=Noneで呼んだ場合、
        settings.MODEL_NAME（デフォルト: "gpt-5.1-chat"）が使用されることを検証。
        """
        from app.core.llm_factory import LLMFactory

        LLMFactory.create_llm(model_name=None)

        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["model"] == "gpt-5.1-chat"

    @pytest.mark.parametrize("alias, expected_model", [
        ("default", "gpt-5.1-chat"),
        ("production", "gpt-5.1-chat"),
        ("high_performance", "gpt-5.1-chat"),
        ("development", "gpt-5-mini"),
        ("standard", "gpt-5-mini"),
        ("lightweight", "gpt-5-nano"),
        ("mini", "gpt-5-mini"),
        ("nano", "gpt-5-nano"),
        ("policy", "gpt-5-mini"),
        ("review", "gpt-5.1-codex"),
        ("chat", "gpt-5-mini"),
        ("extraction", "gpt-5-nano"),
        ("claude", "bedrock-claude-sonnet"),
        ("claude-production", "bedrock-claude-sonnet"),
        ("claude-lightweight", "bedrock-claude-haiku"),
    ])
    def test_all_aliases_resolve_correctly(self, alias, expected_model, mock_chat_openai, mock_settings_env):
        """LLM-002: MODEL_ALIASESの全15エイリアス解決検証（パラメータ化テスト）"""
        from app.core.llm_factory import LLMFactory

        LLMFactory.create_llm(model_name=alias)

        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["model"] == expected_model

    def test_direct_model_name(self, mock_chat_openai, mock_settings_env):
        """LLM-003: 直接モデル名 "gpt-5.1-chat" をそのまま使用"""
        from app.core.llm_factory import LLMFactory

        LLMFactory.create_llm(model_name="gpt-5.1-chat")

        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["model"] == "gpt-5.1-chat"

    def test_temperature_argument_overrides_config(self, mock_chat_openai, mock_settings_env):
        """LLM-004: temperature引数優先（config:None, 引数:0.7）

        gpt-5.1-chatはconfig.temperature=Noneだが、
        引数temperature=0.7を指定した場合、引数が優先されることを検証。
        """
        from app.core.llm_factory import LLMFactory

        LLMFactory.create_llm(model_name="gpt-5.1-chat", temperature=0.7)

        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["temperature"] == 0.7

    def test_temperature_none_uses_config_value(self, mock_chat_openai, mock_settings_env):
        """LLM-005: temperature=None時はconfig値使用（bedrock-claude-sonnet: 0.1）"""
        from app.core.llm_factory import LLMFactory

        LLMFactory.create_llm(model_name="bedrock-claude-sonnet", temperature=None)

        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["temperature"] == 0.1

    def test_temperature_none_and_config_none_omitted(self, mock_chat_openai, mock_settings_env):
        """LLM-006: temperature=None・config:None時はllm_paramsから省略

        gpt-5.1-chatはconfig.temperature=Noneのため、
        引数もNoneの場合はllm_paramsに"temperature"キーが含まれない。
        """
        from app.core.llm_factory import LLMFactory

        LLMFactory.create_llm(model_name="gpt-5.1-chat", temperature=None)

        call_kwargs = mock_chat_openai.call_args[1]
        assert "temperature" not in call_kwargs

    def test_max_completion_tokens_for_gpt5(self, mock_chat_openai, mock_settings_env):
        """LLM-007: GPT-5系はmax_completion_tokensパラメータ使用

        gpt-5.1-chatのconfigに"max_completion_tokens"キーがあるため、
        llm_paramsに"max_completion_tokens"が設定されること（"max_tokens"ではない）。
        """
        from app.core.llm_factory import LLMFactory

        LLMFactory.create_llm(model_name="gpt-5.1-chat")

        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["max_completion_tokens"] == 16000
        assert "max_tokens" not in call_kwargs

    def test_max_tokens_for_non_gpt5(self, mock_chat_openai, mock_settings_env):
        """LLM-008: 非GPT-5系はmax_tokensパラメータ使用

        bedrock-claude-sonnetのconfigには"max_tokens"キーがあるため、
        llm_paramsに"max_tokens"が設定されること（"max_completion_tokens"ではない）。
        """
        from app.core.llm_factory import LLMFactory

        LLMFactory.create_llm(model_name="bedrock-claude-sonnet")

        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["max_tokens"] == 8000
        assert "max_completion_tokens" not in call_kwargs

    def test_max_tokens_arg_overrides_gpt5(self, mock_chat_openai, mock_settings_env):
        """LLM-009: max_tokens引数で上書き（GPT-5系）

        gpt-5.1-chatでmax_tokens=5000を指定した場合、
        max_completion_tokens=5000として設定される。
        """
        from app.core.llm_factory import LLMFactory

        LLMFactory.create_llm(model_name="gpt-5.1-chat", max_tokens=5000)

        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["max_completion_tokens"] == 5000

    def test_max_tokens_arg_overrides_non_gpt5(self, mock_chat_openai, mock_settings_env):
        """LLM-010: max_tokens引数で上書き（非GPT-5系）"""
        from app.core.llm_factory import LLMFactory

        LLMFactory.create_llm(model_name="bedrock-claude-sonnet", max_tokens=2000)

        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["max_tokens"] == 2000

    def test_reasoning_effort_added_when_configured(self, mock_chat_openai, mock_settings_env):
        """LLM-011: reasoning_effort追加（gpt-5.1-chat: "high"）"""
        from app.core.llm_factory import LLMFactory

        LLMFactory.create_llm(model_name="gpt-5.1-chat")

        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["reasoning_effort"] == "high"

    def test_reasoning_effort_not_added_when_absent(self, mock_chat_openai, mock_settings_env):
        """LLM-012: reasoning_effortなし（bedrock-claude-sonnet: config未設定）"""
        from app.core.llm_factory import LLMFactory

        LLMFactory.create_llm(model_name="bedrock-claude-sonnet")

        call_kwargs = mock_chat_openai.call_args[1]
        assert "reasoning_effort" not in call_kwargs

    def test_use_responses_api_true(self, mock_chat_openai, mock_settings_env):
        """LLM-013: use_responses_api=True時にllm_paramsに追加"""
        from app.core.llm_factory import LLMFactory

        LLMFactory.create_llm(model_name="gpt-5.1-chat", use_responses_api=True)

        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["use_responses_api"] is True

    def test_use_responses_api_false(self, mock_chat_openai, mock_settings_env):
        """LLM-014: use_responses_api=False時はllm_paramsに含まない"""
        from app.core.llm_factory import LLMFactory

        LLMFactory.create_llm(model_name="gpt-5.1-chat", use_responses_api=False)

        call_kwargs = mock_chat_openai.call_args[1]
        assert "use_responses_api" not in call_kwargs

    def test_streaming_true(self, mock_chat_openai, mock_settings_env):
        """LLM-015: streaming=True設定"""
        from app.core.llm_factory import LLMFactory

        LLMFactory.create_llm(model_name="gpt-5.1-chat", streaming=True)

        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["streaming"] is True

    def test_kwargs_propagated(self, mock_chat_openai, mock_settings_env):
        """LLM-016: kwargs追加パラメータがChatOpenAIに伝播"""
        from app.core.llm_factory import LLMFactory

        LLMFactory.create_llm(model_name="gpt-5.1-chat", top_p=0.9)

        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["top_p"] == 0.9
```

### 2.2 モデル情報取得テスト

```python
class TestLLMFactoryModelInfo:
    """モデル情報取得系テスト（LLM-017〜LLM-022）"""

    def test_get_model_info_with_alias(self, mock_settings_env):
        """LLM-017: get_model_info: エイリアス解決→config辞書返却

        "default"エイリアス → "gpt-5.1-chat" に解決され、
        そのconfig辞書（コピー）が返されることを検証。
        """
        from app.core.llm_factory import LLMFactory

        # Act
        info = LLMFactory.get_model_info("default")

        # Assert
        assert info["model_name"] == "gpt-5.1-chat"
        assert info["api_key_field"] == "GPT5_1_CHAT_API_KEY"
        assert info["category"] == "production"

    def test_list_available_models_returns_7(self, mock_settings_env):
        """LLM-018: list_available_models: 7モデル全列挙"""
        from app.core.llm_factory import LLMFactory

        # Act
        models = LLMFactory.list_available_models()

        # Assert
        assert len(models) == 7
        expected_models = [
            "gpt-5.1-chat", "gpt-5.1-codex", "bedrock-claude-sonnet",
            "gpt-5.2", "gpt-5-mini", "gpt-5-nano", "bedrock-claude-haiku"
        ]
        for model in expected_models:
            assert model in models

    def test_list_models_by_category_production(self, mock_settings_env):
        """LLM-019: list_models_by_category: "production" → 4モデル"""
        from app.core.llm_factory import LLMFactory

        # Act
        models = LLMFactory.list_models_by_category("production")

        # Assert
        assert len(models) == 4
        assert "gpt-5.1-chat" in models
        assert "gpt-5.1-codex" in models
        assert "bedrock-claude-sonnet" in models
        assert "gpt-5.2" in models

    def test_list_models_by_category_development(self, mock_settings_env):
        """LLM-020: list_models_by_category: "development" → 1モデル"""
        from app.core.llm_factory import LLMFactory

        # Act
        models = LLMFactory.list_models_by_category("development")

        # Assert
        assert len(models) == 1
        assert "gpt-5-mini" in models

    def test_list_models_by_category_lightweight(self, mock_settings_env):
        """LLM-021: list_models_by_category: "lightweight" → 2モデル"""
        from app.core.llm_factory import LLMFactory

        # Act
        models = LLMFactory.list_models_by_category("lightweight")

        # Assert
        assert len(models) == 2
        assert "gpt-5-nano" in models
        assert "bedrock-claude-haiku" in models

    def test_get_all_categories_returns_3(self, mock_settings_env):
        """LLM-022: get_all_categories: 3カテゴリ取得"""
        from app.core.llm_factory import LLMFactory

        # Act
        categories = LLMFactory.get_all_categories()

        # Assert
        assert len(categories) == 3
        assert "production" in categories
        assert "development" in categories
        assert "lightweight" in categories
        assert len(categories["production"]) == 4
        assert len(categories["development"]) == 1
        assert len(categories["lightweight"]) == 2
```

### 2.3 動的モデル追加テスト

```python
class TestLLMFactoryAddModelConfig:
    """動的モデル追加テスト（LLM-023）"""

    def test_add_model_config_success(self, mock_settings_env):
        """LLM-023: add_model_config: 新規モデル追加成功

        有効なconfig辞書を渡した場合、MODEL_CONFIGSに追加され、
        デフォルト値（max_tokens, temperature, description）が設定されること。
        """
        from app.core.llm_factory import LLMFactory

        # Arrange
        new_config = {
            "api_key_field": "NEW_MODEL_API_KEY",
            "model_name": "new-model-v1",
        }

        # Act
        LLMFactory.add_model_config("new-model-v1", new_config)

        # Assert
        assert "new-model-v1" in LLMFactory.MODEL_CONFIGS
        added = LLMFactory.MODEL_CONFIGS["new-model-v1"]
        assert added["api_key_field"] == "NEW_MODEL_API_KEY"
        assert added["max_tokens"] == 4096       # デフォルト値
        assert added["temperature"] == 0.1        # デフォルト値
        assert added["description"] == "Custom model"  # デフォルト値
```

### 2.4 便利関数テスト

```python
class TestConvenienceFunctions:
    """便利関数テスト（LLM-024〜LLM-031）

    全便利関数はget_llm()経由でcreate_llm()を呼ぶ2段階チェーン。
    get_llm()はデフォルトでuse_responses_api=Trueを追加するため、
    各テストでモデル名とuse_responses_apiの両方を検証する。
    """

    def test_get_llm_default_uses_responses_api(self, mock_chat_openai, mock_settings_env):
        """LLM-024: get_llm: デフォルトでuse_responses_api=True

        get_llm()はkwargsにuse_responses_apiが未指定の場合、
        自動的にuse_responses_api=Trueを追加してcreate_llmを呼ぶ。
        """
        from app.core.llm_factory import get_llm

        get_llm()

        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["use_responses_api"] is True

    def test_get_policy_llm_uses_policy_alias(self, mock_chat_openai, mock_settings_env):
        """LLM-025: get_policy_llm: "policy"エイリアス（→gpt-5-mini）を使用

        get_llm() -> create_llm() の呼び出しチェーンを検証。
        get_llm()で自動追加されるuse_responses_api=Trueも確認。
        """
        from app.core.llm_factory import get_policy_llm

        get_policy_llm()

        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["model"] == "gpt-5-mini"
        assert call_kwargs.get("use_responses_api") is True

    def test_get_review_llm_uses_review_alias(self, mock_chat_openai, mock_settings_env):
        """LLM-026: get_review_llm: "review"エイリアス（→gpt-5.1-codex）を使用"""
        from app.core.llm_factory import get_review_llm

        get_review_llm()

        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["model"] == "gpt-5.1-codex"
        assert call_kwargs.get("use_responses_api") is True

    def test_get_chat_llm_uses_chat_alias(self, mock_chat_openai, mock_settings_env):
        """LLM-027: get_chat_llm: "chat"エイリアス（→gpt-5-mini）を使用"""
        from app.core.llm_factory import get_chat_llm

        get_chat_llm()

        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["model"] == "gpt-5-mini"
        assert call_kwargs.get("use_responses_api") is True

    def test_get_extraction_llm_uses_extraction_alias(self, mock_chat_openai, mock_settings_env):
        """LLM-028: get_extraction_llm: "extraction"エイリアス（→gpt-5-nano）を使用"""
        from app.core.llm_factory import get_extraction_llm

        get_extraction_llm()

        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["model"] == "gpt-5-nano"
        assert call_kwargs.get("use_responses_api") is True

    def test_get_production_llm_uses_production_alias(self, mock_chat_openai, mock_settings_env):
        """LLM-029: get_production_llm: "production"エイリアス（→gpt-5.1-chat）を使用"""
        from app.core.llm_factory import get_production_llm

        get_production_llm()

        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["model"] == "gpt-5.1-chat"
        assert call_kwargs.get("use_responses_api") is True

    def test_get_development_llm_uses_development_alias(self, mock_chat_openai, mock_settings_env):
        """LLM-030: get_development_llm: "development"エイリアス（→gpt-5-mini）を使用"""
        from app.core.llm_factory import get_development_llm

        get_development_llm()

        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["model"] == "gpt-5-mini"
        assert call_kwargs.get("use_responses_api") is True

    def test_get_lightweight_llm_uses_lightweight_alias(self, mock_chat_openai, mock_settings_env):
        """LLM-031: get_lightweight_llm: "lightweight"エイリアス（→gpt-5-nano）を使用"""
        from app.core.llm_factory import get_lightweight_llm

        get_lightweight_llm()

        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["model"] == "gpt-5-nano"
        assert call_kwargs.get("use_responses_api") is True
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| LLM-E01 | 未知モデル名でValueError | model_name="unknown-model" | ValueError("Unknown model: unknown-model. ...") |
| LLM-E02 | 未知エイリアスでValueError | model_name="nonexistent-alias" | ValueError("Unknown model: ...") |
| LLM-E03 | APIキー欠落でValueError（GPT5_1_CHAT_API_KEY） | キー未設定 | ValueError("API key not found: GPT5_1_CHAT_API_KEY. ...") |
| LLM-E04 | APIキー欠落でValueError（別モデル） | CLAUDE_SONNET_4_5_KEY未設定 | ValueError("API key not found: ...") |
| LLM-E05 | get_model_info: 未知モデルでValueError | model_name="unknown" | ValueError("Unknown model: unknown") |
| LLM-E06 | add_model_config: api_key_field欠落 | api_key_fieldなし | ValueError("Missing required fields") |
| LLM-E07 | add_model_config: model_name欠落 | model_nameなし | ValueError("Missing required fields") |
| LLM-E08 | list_models_by_category: 存在しないカテゴリ→空辞書 | category="premium" | {} |
| LLM-E09 | temperature=負数（値チェックなし） | temperature=-1.0 | そのまま格納（バリデーションなし） |
| LLM-E10 | max_tokens=0（値チェックなし） | max_tokens=0 | そのまま格納（バリデーションなし） |
| LLM-E11 | reasoning_effort不正値（値チェックなし） | configに"invalid" | そのまま格納（バリデーションなし） |

```python
class TestLLMFactoryErrors:
    """異常系テスト（LLM-E01〜LLM-E11）"""

    def test_unknown_model_raises_value_error(self, mock_settings_env):
        """LLM-E01: 未知モデル名でValueError"""
        from app.core.llm_factory import LLMFactory

        with pytest.raises(ValueError, match="Unknown model: unknown-model"):
            LLMFactory.create_llm(model_name="unknown-model")

    def test_unknown_alias_raises_value_error(self, mock_settings_env):
        """LLM-E02: 未知エイリアスでValueError

        MODEL_ALIASESに存在しない名前は、MODEL_CONFIGSにも存在しないため、
        ValueErrorが発生する。
        """
        from app.core.llm_factory import LLMFactory

        with pytest.raises(ValueError, match="Unknown model"):
            LLMFactory.create_llm(model_name="nonexistent-alias")

    def test_missing_api_key_gpt51_chat(self, mock_settings_env):
        """LLM-E03: APIキー欠落でValueError（GPT5_1_CHAT_API_KEY）

        settings.GPT5_1_CHAT_API_KEYがNone/空の場合にValueErrorが発生。
        エラーメッセージにはフィールド名が含まれるが、キー値は含まれない。
        """
        from app.core.llm_factory import LLMFactory

        # settingsのAPIキーをNoneに設定
        with patch("app.core.llm_factory.settings") as mock_settings:
            mock_settings.MODEL_NAME = "gpt-5.1-chat"
            mock_settings.GPT5_1_CHAT_API_KEY = None
            mock_settings.DOCKER_BASE_URL = "http://localhost:11434"

            with pytest.raises(ValueError, match="API key not found: GPT5_1_CHAT_API_KEY"):
                LLMFactory.create_llm(model_name="gpt-5.1-chat")

    def test_missing_api_key_claude_sonnet(self, mock_settings_env):
        """LLM-E04: APIキー欠落でValueError（CLAUDE_SONNET_4_5_KEY）"""
        from app.core.llm_factory import LLMFactory

        with patch("app.core.llm_factory.settings") as mock_settings:
            mock_settings.MODEL_NAME = "gpt-5.1-chat"
            mock_settings.CLAUDE_SONNET_4_5_KEY = None
            mock_settings.DOCKER_BASE_URL = "http://localhost:11434"

            with pytest.raises(ValueError, match="API key not found: CLAUDE_SONNET_4_5_KEY"):
                LLMFactory.create_llm(model_name="bedrock-claude-sonnet")

    def test_get_model_info_unknown_raises(self, mock_settings_env):
        """LLM-E05: get_model_info: 未知モデルでValueError"""
        from app.core.llm_factory import LLMFactory

        with pytest.raises(ValueError, match="Unknown model: unknown"):
            LLMFactory.get_model_info("unknown")

    def test_add_model_config_missing_api_key_field(self, mock_settings_env):
        """LLM-E06: add_model_config: api_key_field欠落でValueError"""
        from app.core.llm_factory import LLMFactory

        with pytest.raises(ValueError, match="Missing required fields"):
            LLMFactory.add_model_config("bad-model", {
                "model_name": "bad-model",
                # api_key_fieldがない
            })

    def test_add_model_config_missing_model_name(self, mock_settings_env):
        """LLM-E07: add_model_config: model_name欠落でValueError"""
        from app.core.llm_factory import LLMFactory

        with pytest.raises(ValueError, match="Missing required fields"):
            LLMFactory.add_model_config("bad-model", {
                "api_key_field": "SOME_KEY",
                # model_nameがない
            })

    def test_list_models_by_nonexistent_category(self, mock_settings_env):
        """LLM-E08: list_models_by_category: 存在しないカテゴリ→空辞書"""
        from app.core.llm_factory import LLMFactory

        # Act
        result = LLMFactory.list_models_by_category("premium")

        # Assert
        assert result == {}

    def test_negative_temperature_no_validation(self, mock_chat_openai, mock_settings_env):
        """LLM-E09: temperature=負数は値チェックなしでそのまま格納

        llm_factory.pyにはtemperatureのバリデーションがないため、
        負数がそのままChatOpenAIに渡される（バリデーション不在の確認）。
        """
        from app.core.llm_factory import LLMFactory

        LLMFactory.create_llm(model_name="gpt-5.1-chat", temperature=-1.0)

        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["temperature"] == -1.0

    def test_zero_max_tokens_no_validation(self, mock_chat_openai, mock_settings_env):
        """LLM-E10: max_tokens=0は値チェックなしでそのまま格納"""
        from app.core.llm_factory import LLMFactory

        LLMFactory.create_llm(model_name="gpt-5.1-chat", max_tokens=0)

        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["max_completion_tokens"] == 0

    def test_invalid_reasoning_effort_no_validation(self, mock_chat_openai, mock_settings_env):
        """LLM-E11: reasoning_effort不正値は値チェックなしでそのまま格納

        MODEL_CONFIGSのreasoning_effortを一時的に不正値に変更して検証。
        """
        from app.core.llm_factory import LLMFactory

        # Arrange - configのreasoning_effortを一時的に変更
        original = LLMFactory.MODEL_CONFIGS["gpt-5.1-chat"]["reasoning_effort"]
        try:
            LLMFactory.MODEL_CONFIGS["gpt-5.1-chat"]["reasoning_effort"] = "invalid"

            # Act
            LLMFactory.create_llm(model_name="gpt-5.1-chat")

            # Assert
            call_kwargs = mock_chat_openai.call_args[1]
            assert call_kwargs["reasoning_effort"] == "invalid"
        finally:
            # Teardown - 元の値に復元
            LLMFactory.MODEL_CONFIGS["gpt-5.1-chat"]["reasoning_effort"] = original
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| LLM-SEC-01 | エラーメッセージにAPIキー値が未含有 | APIキー欠落（None） | ValueErrorメッセージにAPIキーの実値が含まれないこと |
| LLM-SEC-02 | MODEL_ALIASES整合性（全エイリアスが有効モデルを指す） | 15エイリアス全て | 全エイリアスがMODEL_CONFIGSに存在するモデルを参照 |
| LLM-SEC-03 | add_model_config: デフォルト値の安全性 | 最小config（api_key_field, model_nameのみ） | max_tokens=4096, temperature=0.1, description="Custom model" |
| LLM-SEC-04 | APIキーフィールド名の命名規則一貫性 | 全7モデル | 全モデルにapi_key_fieldが存在し、空でないこと |
| LLM-SEC-05 | ChatOpenAI初期化時のbase_url統一確認 | 複数モデル | 全モデルがsettings.DOCKER_BASE_URLを使用すること |

```python
@pytest.mark.security
class TestLLMFactorySecurity:
    """セキュリティテスト（LLM-SEC-01〜LLM-SEC-05）"""

    def test_error_message_no_api_key_value(self, mock_settings_env):
        """LLM-SEC-01: エラーメッセージにAPIキー値が未含有

        APIキー欠落時のValueErrorメッセージに、
        テスト用のAPIキー値（"test-gpt5-1-chat-key"等）が含まれないことを検証。
        エラーメッセージにはフィールド名のみが表示されるべき。
        """
        from app.core.llm_factory import LLMFactory

        with patch("app.core.llm_factory.settings") as mock_settings:
            mock_settings.MODEL_NAME = "gpt-5.1-chat"
            mock_settings.GPT5_1_CHAT_API_KEY = None
            mock_settings.DOCKER_BASE_URL = "http://localhost:11434"

            with pytest.raises(ValueError) as exc_info:
                LLMFactory.create_llm(model_name="gpt-5.1-chat")

            error_msg = str(exc_info.value)
            # フィールド名は含まれるが、キー値は含まれない
            assert "GPT5_1_CHAT_API_KEY" in error_msg
            # テスト用APIキー値が含まれていないこと
            for key_value in MOCK_SETTINGS_ENV.values():
                assert key_value not in error_msg

    def test_all_aliases_point_to_valid_models(self, mock_settings_env):
        """LLM-SEC-02: MODEL_ALIASES整合性 - 全エイリアスが有効モデルを指す

        15個のエイリアス全てがMODEL_CONFIGSに存在するモデルを
        参照していることを検証。孤立したエイリアスはセキュリティリスク。
        """
        from app.core.llm_factory import LLMFactory

        for alias, target_model in LLMFactory.MODEL_ALIASES.items():
            assert target_model in LLMFactory.MODEL_CONFIGS, (
                f"エイリアス '{alias}' が存在しないモデル '{target_model}' を参照しています"
            )

    def test_add_model_config_defaults_are_safe(self, mock_settings_env):
        """LLM-SEC-03: add_model_config: デフォルト値の安全性

        add_model_config()が設定するデフォルト値が安全であることを検証。
        - max_tokens: 4096（過大でない）
        - temperature: 0.1（安定出力）
        - description: "Custom model"（情報漏洩なし）
        """
        from app.core.llm_factory import LLMFactory

        new_config = {
            "api_key_field": "SAFE_TEST_KEY",
            "model_name": "safe-test-model",
        }

        LLMFactory.add_model_config("safe-test-model", new_config)

        added = LLMFactory.MODEL_CONFIGS["safe-test-model"]
        assert added["max_tokens"] == 4096
        assert added["temperature"] == 0.1
        assert added["description"] == "Custom model"

    def test_all_models_have_api_key_field(self, mock_settings_env):
        """LLM-SEC-04: 全モデルにapi_key_fieldが存在し、空でないこと

        MODEL_CONFIGSの全7モデルにapi_key_fieldが定義され、
        空文字列やNoneでないことを検証。
        """
        from app.core.llm_factory import LLMFactory

        for model_name, config in LLMFactory.MODEL_CONFIGS.items():
            assert "api_key_field" in config, (
                f"モデル '{model_name}' にapi_key_fieldが定義されていません"
            )
            assert config["api_key_field"], (
                f"モデル '{model_name}' のapi_key_fieldが空です"
            )

    def test_base_url_unified_across_models(self, mock_chat_openai, mock_settings_env):
        """LLM-SEC-05: ChatOpenAI初期化時のbase_url統一確認

        全モデルがsettings.DOCKER_BASE_URLを使用してChatOpenAIを初期化すること。
        モデルごとに異なるbase_urlが設定されるとセキュリティリスクになる。
        """
        from app.core.llm_factory import LLMFactory

        test_models = ["gpt-5.1-chat", "bedrock-claude-sonnet", "gpt-5-mini"]
        expected_base_url = "http://localhost:11434"

        for model in test_models:
            mock_chat_openai.reset_mock()
            LLMFactory.create_llm(model_name=model)

            call_kwargs = mock_chat_openai.call_args[1]
            assert call_kwargs["base_url"] == expected_base_url, (
                f"モデル '{model}' のbase_urlが '{call_kwargs.get('base_url')}' です。"
                f"期待値: '{expected_base_url}'"
            )
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_llm_factory_module` | sys.modulesからconfig+llm_factoryを削除してモジュール状態リセット | function | **Yes** |
| `mock_chat_openai` | ChatOpenAIモック（外部API呼び出し防止） | function | No |
| `mock_settings_env` | 環境変数設定+モジュールリセット | function | No |

### 共通フィクスチャ定義

```python
# test/unit/core/conftest.py に追加

import pytest
import sys
import os
from unittest.mock import patch, MagicMock


# テスト用環境変数
MOCK_SETTINGS_ENV = {
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
    "MODEL_NAME": "gpt-5.1-chat",
}


@pytest.fixture(autouse=True)
def reset_llm_factory_module():
    """各テスト前後にllm_factoryモジュールの状態をリセット

    【リセット対象】
    - LLMFactoryクラスのクラス変数（MODEL_CONFIGS, MODEL_ALIASES）
    - モジュールレベル変数（llm_factory = LLMFactory()）

    【リセット方法】
    sys.modulesからモジュールを削除することで、次回import時にモジュールが再実行され、
    クラス変数が初期状態に戻る。

    【必要性】
    - add_model_config()でMODEL_CONFIGSを変更するテストが他テストに影響しないようにする
    - mock_settings_envで環境変数を変更した場合、config.settingsの再初期化が必要

    【注意】
    mock_settings_envもsetup時にモジュールクリアを行う。autouseの本フィクスチャは
    teardown時（yield後）にクリアするため、処理は重複しない（setup前クリア + teardown後クリア）。
    """
    yield
    # テスト後にモジュールキャッシュをクリア
    modules_to_remove = [
        key for key in sys.modules
        if key.startswith("app.core.config") or key.startswith("app.core.llm_factory")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def mock_chat_openai():
    """ChatOpenAIモック（外部API呼び出しを防止）

    create_llm()が返すChatOpenAIインスタンスをモック化。
    call_argsで渡されたパラメータを検証可能にする。
    """
    with patch("app.core.llm_factory.ChatOpenAI") as mock_cls:
        mock_cls.return_value = MagicMock()
        yield mock_cls


@pytest.fixture
def mock_settings_env():
    """環境変数をテスト用値で設定し、モジュールをリロード

    MOCK_SETTINGS_ENVの全キーを環境変数に設定した上で、
    config + llm_factoryモジュールを再インポートする。
    """
    # モジュールキャッシュをクリア
    modules_to_remove = [
        key for key in sys.modules
        if key.startswith("app.core.config") or key.startswith("app.core.llm_factory")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]

    with patch.dict(os.environ, MOCK_SETTINGS_ENV, clear=False):
        yield
```

---

## 6. テスト実行例

```bash
# llm_factory関連テストのみ実行
pytest test/unit/core/test_llm_factory.py -v

# 特定のテストクラスのみ実行
pytest test/unit/core/test_llm_factory.py::TestLLMFactoryCreateLLM -v
pytest test/unit/core/test_llm_factory.py::TestLLMFactoryModelInfo -v
pytest test/unit/core/test_llm_factory.py::TestLLMFactoryAddModelConfig -v
pytest test/unit/core/test_llm_factory.py::TestConvenienceFunctions -v
pytest test/unit/core/test_llm_factory.py::TestLLMFactoryErrors -v
pytest test/unit/core/test_llm_factory.py::TestLLMFactorySecurity -v

# カバレッジ付きで実行
pytest test/unit/core/test_llm_factory.py --cov=app.core.llm_factory --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/core/test_llm_factory.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 | 備考 |
|---------|------|--------|------|
| 正常系 | 31+8パラメータ化 | LLM-001 〜 LLM-031 | LLM-002は15エイリアスのパラメータ化テスト |
| 異常系 | 11 | LLM-E01 〜 LLM-E11 | |
| セキュリティ | 5 | LLM-SEC-01 〜 LLM-SEC-05 | |
| **合計** | **55** | - | パラメータ化展開後: 16+6+1+8+11+5+8(パラメータ化追加分) |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestLLMFactoryCreateLLM` | LLM-001〜LLM-016 | 16（LLM-002は15パラメータ化） |
| `TestLLMFactoryModelInfo` | LLM-017〜LLM-022 | 6 |
| `TestLLMFactoryAddModelConfig` | LLM-023 | 1 |
| `TestConvenienceFunctions` | LLM-024〜LLM-031 | 8 |
| `TestLLMFactoryErrors` | LLM-E01〜LLM-E11 | 11 |
| `TestLLMFactorySecurity` | LLM-SEC-01〜LLM-SEC-05 | 5 |

### 注意事項

- **LLM-E09〜LLM-E11** はバリデーション不在の確認テストです。現在の`llm_factory.py`にはtemperature/max_tokens/reasoning_effortの値バリデーションがないため、不正値がそのまま`ChatOpenAI`に渡されます。将来バリデーションを追加する場合はテストの期待結果を更新してください。
- **LLM-E03〜LLM-E04** のAPIキー欠落テストは`settings`オブジェクト自体をモックする必要があります（環境変数モックだけでは不十分）。
- **LLM-023** の`add_model_config`テストは`MODEL_CONFIGS`を変更するため、`reset_llm_factory_module`フィクスチャによるクリーンアップが必須です。

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対策 |
|---|---------|------|------|
| 1 | **モジュール初期化の副作用**: `llm_factory.py`はインポート時に`config.settings`を参照し、`llm_factory = LLMFactory()`をグローバルに生成する | テスト間で状態が共有される可能性 | `reset_llm_factory_module`フィクスチャでsys.modulesから削除 |
| 2 | **ChatOpenAIモック**: `mock_chat_openai`はChatOpenAIクラス全体をモックするため、`__init__`の引数バリデーション・型チェック・接続検証が全てスキップされる | 不正なパラメータ（例: temperature=999）でもテストは成功する | 統合テストで実際のChatOpenAI初期化を検証 |
| 3 | **config.py依存**: `settings`オブジェクトの属性アクセス（`getattr(settings, api_key_field, None)`）はconfig.pyの初期化に依存 | config.pyの変更がllm_factoryテストに影響 | 環境変数モック+モジュールリセットで分離 |
| 4 | **MODEL_CONFIGS状態変更**: `add_model_config()`はクラス変数を直接変更するため、テスト実行順序に依存しうる | 並列テスト実行時に競合の可能性 | `reset_llm_factory_module`でモジュールごと再ロード |
| 5 | **パラメータバリデーション不在**: temperature/max_tokens/reasoning_effortに値バリデーションがないため、不正値がそのままChatOpenAIに渡される | 実行時にChatOpenAI側でエラーになる可能性 | LLM-E09〜LLM-E11で不在を明示的に文書化 |
