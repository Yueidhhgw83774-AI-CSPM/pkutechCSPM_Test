"""
llm_factory.py 単元テスト

テスト規格: llm_factory_tests.md
カバレッジ目標: 95%+

テスト類別:
  - 正常系: 39 個テスト (LLM-001〜LLM-031, うちLLM-002は15パラメータ化)
  - 異常系: 11 個テスト (LLM-E01〜LLM-E11)
  - セキュリティ: 5 個テスト (LLM-SEC-01〜LLM-SEC-05)

合計: 55 テストケース
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# テスト対象のモジュールをインポートする
project_root = Path(__file__).parent.parent.parent.parent / "platform_python_backend-testing"
sys.path.insert(0, str(project_root))


# ==================== 正常系テスト ====================

class TestLLMFactoryCreateLLM:
    """create_llmメソッドのテスト (LLM-001〜LLM-016)

    テストID: LLM-001 〜 LLM-016
    """

    def test_model_name_none_uses_settings(self, mock_chat_openai, mock_settings_env):
        """
        LLM-001: model_name=None時にsettings.MODEL_NAME使用
        覆盖代码行: llm_factory.py:128-129

        テスト目的:
          - create_llm()をmodel_name=Noneで呼んだ場合、
            settings.MODEL_NAME(デフォルト: "gpt-5.1-chat")が使用されることを検証
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # Act - テスト対象の関数を実行する
        result = LLMFactory.create_llm(model_name=None)

        # Assert - 結果が予期したものと一致することを確認する
        assert mock_chat_openai.called, "mock_chat_openai was not called!"
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["model"] == "gpt-5.1-chat"  # settings.MODEL_NAMEのデフォルト値

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
        """
        LLM-002: MODEL_ALIASESの全15エイリアス解決検証 (パラメータ化テスト)
        覆盖代码行: llm_factory.py:132-133

        テスト目的:
          - 全15エイリアスが正しいモデル名に解決されることを検証
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # Act - テスト対象の関数を実行する
        LLMFactory.create_llm(model_name=alias)

        # Assert - 結果が期待されるものと一致することを確認する
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["model"] == expected_model

    def test_direct_model_name(self, mock_chat_openai, mock_settings_env):
        """
        LLM-003: 直接モデル名 "gpt-5.1-chat" をそのまま使用
        覆盖代码行: llm_factory.py:132-140

        テスト目的:
          - エイリアスではなく直接モデル名を指定した場合、そのまま使用される
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # Act - テスト対象の関数を実行する
        LLMFactory.create_llm(model_name="gpt-5.1-chat")

        # Assert - 結果が予期したものと一致することを確認する
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["model"] == "gpt-5.1-chat"

    def test_temperature_argument_overrides_config(self, mock_chat_openai, mock_settings_env):
        """
        LLM-004: temperature引数優先 (config:None, 引数:0.7)
        覆盖代码行: llm_factory.py:157-158

        テスト目的:
          - gpt-5.1-chatはconfig.temperature=Noneだが、
            引数temperature=0.7を指定した場合、引数が優先される
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # Act - テスト対象の関数を実行する
        LLMFactory.create_llm(model_name="gpt-5.1-chat", temperature=0.7)

        # Assert - 結果が予期したものと一致することを確認する
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["temperature"] == 0.7

    def test_temperature_none_uses_config_value(self, mock_chat_openai, mock_settings_env):
        """
        LLM-005: temperature=None時はconfig値使用 (bedrock-claude-sonnet: 0.1)
        覆盖代码行: llm_factory.py:157-158

        テスト目的:
          - bedrock-claude-sonnetのconfig.temperature=0.1が使用される
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # Act - テスト対象の関数を実行する
        LLMFactory.create_llm(model_name="bedrock-claude-sonnet", temperature=None)

        # Assert - 結果が期待されるものと一致することを確認する
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["temperature"] == 0.1

    def test_temperature_none_and_config_none_omitted(self, mock_chat_openai, mock_settings_env):
        """
        LLM-006: temperature=None・config:None時はllm_paramsから省略
        覆盖代码行: llm_factory.py:201-203

        テスト目的:
          - gpt-5.1-chatはconfig.temperature=Noneのため、
            引数もNoneの場合はllm_paramsに"temperature"キーが含まれない
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # Act - テスト対象の関数を実行する
        LLMFactory.create_llm(model_name="gpt-5.1-chat", temperature=None)

        # Assert - 結果が期待されるものと一致することを確認する
        call_kwargs = mock_chat_openai.call_args[1]
        assert "temperature" not in call_kwargs

    def test_max_completion_tokens_for_gpt5(self, mock_chat_openai, mock_settings_env):
        """
        LLM-007: GPT-5系はmax_completion_tokensパラメータ使用
        覆盖代码行: llm_factory.py:161-165, 206-208

        テスト目的:
          - gpt-5.1-chatのconfigに"max_completion_tokens"キーがあるため、
            llm_paramsに"max_completion_tokens"が設定される ("max_tokens"ではない)
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # Act - テスト対象の関数を実行する
        LLMFactory.create_llm(model_name="gpt-5.1-chat")

        # Assert - 結果が予期したものと一致することを確認する
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["max_completion_tokens"] == 16000
        assert "max_tokens" not in call_kwargs

    def test_max_tokens_for_non_gpt5(self, mock_chat_openai, mock_settings_env):
        """
        LLM-008: 非GPT-5系はmax_tokensパラメータ使用
        覆盖代码行: llm_factory.py:161-165, 209-211

        テスト目的:
          - bedrock-claude-sonnetのconfigには"max_tokens"キーがあるため、
            llm_paramsに"max_tokens"が設定される ("max_completion_tokens"ではない)
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # Act - テスト対象の関数を実行する
        LLMFactory.create_llm(model_name="bedrock-claude-sonnet")

        # Assert - 結果が予期したものと一致することを確認する
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["max_tokens"] == 8000
        assert "max_completion_tokens" not in call_kwargs

    def test_max_tokens_arg_overrides_gpt5(self, mock_chat_openai, mock_settings_env):
        """
        LLM-009: max_tokens引数で上書き (GPT-5系)
        覆盖代码行: llm_factory.py:161-165, 206-208

        テスト目的:
          - gpt-5.1-chatでmax_tokens=5000を指定した場合、
            max_completion_tokens=5000として設定される
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # Act - テスト対象の関数を実行する
        LLMFactory.create_llm(model_name="gpt-5.1-chat", max_tokens=5000)

        # Assert - 結果が予期したものと一致することを確認する
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["max_completion_tokens"] == 5000

    def test_max_tokens_arg_overrides_non_gpt5(self, mock_chat_openai, mock_settings_env):
        """
        LLM-010: max_tokens引数で上書き (非GPT-5系)
        覆盖代码行: llm_factory.py:161-165, 209-211

        テスト目的:
          - bedrock-claude-sonnetでmax_tokens=2000を指定した場合、
            max_tokens=2000として設定される
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # Act - テスト対象の関数を実行する
        LLMFactory.create_llm(model_name="bedrock-claude-sonnet", max_tokens=2000)

        # Assert - 結果が予期したものと一致することを確認する
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["max_tokens"] == 2000

    def test_reasoning_effort_added_when_configured(self, mock_chat_openai, mock_settings_env):
        """
        LLM-011: reasoning_effort追加 (gpt-5.1-chat: "high")
        覆盖代码行: llm_factory.py:219-222

        テスト目的:
          - gpt-5.1-chatのconfigにreasoning_effort="high"があるため、
            llm_paramsに追加される
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # Act - テスト対象の関数を実行する
        LLMFactory.create_llm(model_name="gpt-5.1-chat")

        # Assert - 結果が予期したものと一致することを確認する
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["reasoning_effort"] == "high"

    def test_reasoning_effort_not_added_when_absent(self, mock_chat_openai, mock_settings_env):
        """
        LLM-012: reasoning_effortなし (bedrock-claude-sonnet: config未設定)
        覆盖代码行: llm_factory.py:219-222

        テスト目的:
          - bedrock-claude-sonnetのconfigにreasoning_effortがないため、
            llm_paramsに含まれない
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # Act - テスト対象の関数を実行する
        LLMFactory.create_llm(model_name="bedrock-claude-sonnet")

        # Assert - 結果が予期したものと一致することを確認する
        call_kwargs = mock_chat_openai.call_args[1]
        assert "reasoning_effort" not in call_kwargs

    def test_use_responses_api_true(self, mock_chat_openai, mock_settings_env):
        """
        LLM-013: use_responses_api=True時にllm_paramsに追加
        覆盖代码行: llm_factory.py:214-216

        テスト目的:
          - use_responses_api=Trueを指定した場合、llm_paramsに追加される
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # Act - テスト対象の関数を実行する
        LLMFactory.create_llm(model_name="gpt-5.1-chat", use_responses_api=True)

        # Assert - 結果が予期したものと一致することを確認する
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["use_responses_api"] is True

    def test_use_responses_api_false(self, mock_chat_openai, mock_settings_env):
        """
        LLM-014: use_responses_api=False時はllm_paramsに含まない
        覆盖代码行: llm_factory.py:214-216

        テスト目的:
          - use_responses_api=Falseの場合、llm_paramsに含まれない
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # Act - テスト対象の関数を実行する
        LLMFactory.create_llm(model_name="gpt-5.1-chat", use_responses_api=False)

        # Assert - 結果が予期したものと一致することを確認する
        call_kwargs = mock_chat_openai.call_args[1]
        assert "use_responses_api" not in call_kwargs

    def test_streaming_true(self, mock_chat_openai, mock_settings_env):
        """
        LLM-015: streaming=True設定
        覆盖代码行: llm_factory.py:189-196

        テスト目的:
          - streaming=Trueを指定した場合、llm_paramsに設定される
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # Act - テスト対象の関数を実行する
        LLMFactory.create_llm(model_name="gpt-5.1-chat", streaming=True)

        # Assert - 結果が期待されるものと一致することを確認する
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["streaming"] is True

    def test_kwargs_propagated(self, mock_chat_openai, mock_settings_env):
        """
        LLM-016: kwargs追加パラメータがChatOpenAIに伝播
        覆盖代码行: llm_factory.py:189-196

        テスト目的:
          - kwargs経由で追加されたパラメータ(top_p=0.9など)が
            ChatOpenAI初期化時に正しく伝播される
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # Act - テスト対象の関数を実行する
        LLMFactory.create_llm(model_name="gpt-5.1-chat", top_p=0.9)

        # Assert - 結果が予期したものと一致することを確認する
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["top_p"] == 0.9


class TestLLMFactoryModelInfo:
    """モデル情報取得系テスト (LLM-017〜LLM-022)

    テストID: LLM-017 〜 LLM-022
    """

    def test_get_model_info_with_alias(self, mock_settings_env):
        """
        LLM-017: get_model_info: エイリアス解決→config辞書返却
        覆盖代码行: llm_factory.py:226-235

        テスト目的:
          - "default"エイリアス → "gpt-5.1-chat" に解決され、
            そのconfig辞書(コピー)が返されることを検証
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # Act - テスト対象の関数を実行する
        info = LLMFactory.get_model_info("default")

        # Assert - 結果が予期したものと一致することを確認する
        assert info["model_name"] == "gpt-5.1-chat"
        assert info["api_key_field"] == "GPT5_1_CHAT_API_KEY"
        assert info["category"] == "production"

    def test_list_available_models_returns_7(self, mock_settings_env):
        """
        LLM-018: list_available_models: 7モデル全列挙
        覆盖代码行: llm_factory.py:237-242

        テスト目的:
          - MODEL_CONFIGSに定義された全7モデルが返されることを検証
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # Act - テスト対象の関数を実行する
        models = LLMFactory.list_available_models()

        # Assert - 結果が予期したものと一致することを確認する
        assert len(models) == 7
        expected_models = [
            "gpt-5.1-chat", "gpt-5.1-codex", "bedrock-claude-sonnet",
            "gpt-5.2", "gpt-5-mini", "gpt-5-nano", "bedrock-claude-haiku"
        ]
        for model in expected_models:
            assert model in models

    def test_list_models_by_category_production(self, mock_settings_env):
        """
        LLM-019: list_models_by_category: "production" → 4モデル
        覆盖代码行: llm_factory.py:244-263

        テスト目的:
          - "production"カテゴリに4モデルが含まれることを検証
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # Act - テスト対象の関数を実行する
        models = LLMFactory.list_models_by_category("production")

        # Assert - 結果が予期したものと一致することを確認する
        assert len(models) == 4
        assert "gpt-5.1-chat" in models
        assert "gpt-5.1-codex" in models
        assert "bedrock-claude-sonnet" in models
        assert "gpt-5.2" in models

    def test_list_models_by_category_development(self, mock_settings_env):
        """
        LLM-020: list_models_by_category: "development" → 1モデル
        覆盖代码行: llm_factory.py:244-263

        テスト目的:
          - "development"カテゴリに1モデル(gpt-5-mini)が含まれることを検証
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # Act - テスト対象の関数を実行する
        models = LLMFactory.list_models_by_category("development")

        # Assert - 結果が予期したものと一致することを確認する
        assert len(models) == 1
        assert "gpt-5-mini" in models

    def test_list_models_by_category_lightweight(self, mock_settings_env):
        """
        LLM-021: list_models_by_category: "lightweight" → 2モデル
        覆盖代码行: llm_factory.py:244-263

        テスト目的:
          - "lightweight"カテゴリに2モデル(gpt-5-nano, bedrock-claude-haiku)が
            含まれることを検証
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # Act - テスト対象の関数を実行する
        models = LLMFactory.list_models_by_category("lightweight")

        # Assert - 結果が予期したものと一致することを確認する
        assert len(models) == 2
        assert "gpt-5-nano" in models
        assert "bedrock-claude-haiku" in models

    def test_get_all_categories_returns_3(self, mock_settings_env):
        """
        LLM-022: get_all_categories: 3カテゴリ取得
        覆盖代码行: llm_factory.py:265-287

        テスト目的:
          - 全カテゴリ(production, development, lightweight)が返され、
            各カテゴリに正しい数のモデルが含まれることを検証
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # Act - テスト対象の関数を実行する
        categories = LLMFactory.get_all_categories()

        # Assert - 結果が予期したものと一致することを確認する
        assert len(categories) == 3
        assert "production" in categories
        assert "development" in categories
        assert "lightweight" in categories
        assert len(categories["production"]) == 4
        assert len(categories["development"]) == 1
        assert len(categories["lightweight"]) == 2


class TestLLMFactoryAddModelConfig:
    """動的モデル追加テスト (LLM-023)

    テストID: LLM-023
    """

    def test_add_model_config_success(self, mock_settings_env):
        """
        LLM-023: add_model_config: 新規モデル追加成功
        覆盖代码行: llm_factory.py:289-310

        テスト目的:
          - 有効なconfig辞書を渡した場合、MODEL_CONFIGSに追加され、
            デフォルト値(max_tokens, temperature, description)が設定されることを検証
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        new_config = {
            "api_key_field": "NEW_MODEL_API_KEY",
            "model_name": "new-model-v1",
        }

        # Act - テスト対象の関数を実行する
        LLMFactory.add_model_config("new-model-v1", new_config)

        # Assert - 結果が予期したものと一致することを確認する
        assert "new-model-v1" in LLMFactory.MODEL_CONFIGS
        added = LLMFactory.MODEL_CONFIGS["new-model-v1"]
        assert added["api_key_field"] == "NEW_MODEL_API_KEY"
        assert added["max_tokens"] == 4096       # デフォルト値
        assert added["temperature"] == 0.1       # デフォルト値
        assert added["description"] == "Custom model"  # デフォルト値


class TestConvenienceFunctions:
    """便利関数テスト (LLM-024〜LLM-031)

    テストID: LLM-024 〜 LLM-031

    注意:
    全便利関数はget_llm()経由でcreate_llm()を呼ぶ2段階チェーン。
    get_llm()はデフォルトでuse_responses_api=Trueを追加するため、
    各テストでモデル名とuse_responses_apiの両方を検証する。
    """

    def test_get_llm_default_uses_responses_api(self, mock_chat_openai, mock_settings_env):
        """
        LLM-024: get_llm: デフォルトでuse_responses_api=True
        覆盖代码行: llm_factory.py:329-344

        テスト目的:
          - get_llm()はkwargsにuse_responses_apiが未指定の場合、
            自動的にuse_responses_api=Trueを追加してcreate_llmを呼ぶ
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import get_llm

        # Act - テスト対象の関数を実行する
        get_llm()

        # Assert - 結果が予期したものと一致することを確認する
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["use_responses_api"] is True

    def test_get_policy_llm_uses_policy_alias(self, mock_chat_openai, mock_settings_env):
        """
        LLM-025: get_policy_llm: "policy"エイリアス (→gpt-5-mini) を使用
        覆盖代码行: llm_factory.py:347-349

        テスト目的:
          - get_llm() -> create_llm() の呼び出しチェーンを検証
          - get_llm()で自動追加されるuse_responses_api=Trueも確認
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import get_policy_llm

        # Act - テスト対象の関数を実行する
        get_policy_llm()

        # Assert - 結果が予期したものと一致することを確認する
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["model"] == "gpt-5-mini"
        assert call_kwargs.get("use_responses_api") is True

    def test_get_review_llm_uses_review_alias(self, mock_chat_openai, mock_settings_env):
        """
        LLM-026: get_review_llm: "review"エイリアス (→gpt-5.1-codex) を使用
        覆盖代码行: llm_factory.py:352-354

        テスト目的:
          - get_review_llm()が"review"エイリアス経由でgpt-5.1-codexを使用することを検証
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import get_review_llm

        # Act - テスト対象の関数を実行する
        get_review_llm()

        # Assert - 結果が予期したものと一致することを確認する
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["model"] == "gpt-5.1-codex"
        assert call_kwargs.get("use_responses_api") is True

    def test_get_chat_llm_uses_chat_alias(self, mock_chat_openai, mock_settings_env):
        """
        LLM-027: get_chat_llm: "chat"エイリアス (→gpt-5-mini) を使用
        覆盖代码行: llm_factory.py:357-359

        テスト目的:
          - get_chat_llm()が"chat"エイリアス経由でgpt-5-miniを使用することを検証
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import get_chat_llm

        # Act - テスト対象の関数を実行する
        get_chat_llm()

        # Assert - 結果が期待されるものと一致することを確認する
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["model"] == "gpt-5-mini"
        assert call_kwargs.get("use_responses_api") is True

    def test_get_extraction_llm_uses_extraction_alias(self, mock_chat_openai, mock_settings_env):
        """
        LLM-028: get_extraction_llm: "extraction"エイリアス (→gpt-5-nano) を使用
        覆盖代码行: llm_factory.py:362-364

        テスト目的:
          - get_extraction_llm()が"extraction"エイリアス経由でgpt-5-nanoを使用することを検証
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import get_extraction_llm

        # Act - テスト対象の関数を実行する
        get_extraction_llm()

        # Assert - 結果が予期したものと一致することを確認する
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["model"] == "gpt-5-nano"
        assert call_kwargs.get("use_responses_api") is True

    def test_get_production_llm_uses_production_alias(self, mock_chat_openai, mock_settings_env):
        """
        LLM-029: get_production_llm: "production"エイリアス (→gpt-5.1-chat) を使用
        覆盖代码行: llm_factory.py:370-385

        テスト目的:
          - get_production_llm()が"production"エイリアス経由でgpt-5.1-chatを使用することを検証
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import get_production_llm

        # Act - テスト対象の関数を実行する
        get_production_llm()

        # Assert - 結果が予期したものと一致することを確認する
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["model"] == "gpt-5.1-chat"
        assert call_kwargs.get("use_responses_api") is True

    def test_get_development_llm_uses_development_alias(self, mock_chat_openai, mock_settings_env):
        """
        LLM-030: get_development_llm: "development"エイリアス (→gpt-5-mini) を使用
        覆盖代码行: llm_factory.py:388-403

        テスト目的:
          - get_development_llm()が"development"エイリアス経由でgpt-5-miniを使用することを検証
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import get_development_llm

        # Act - テスト対象の関数を実行する
        get_development_llm()

        # Assert - 結果が期待されるものと一致することを確認する
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["model"] == "gpt-5-mini"
        assert call_kwargs.get("use_responses_api") is True

    def test_get_lightweight_llm_uses_lightweight_alias(self, mock_chat_openai, mock_settings_env):
        """
        LLM-031: get_lightweight_llm: "lightweight"エイリアス (→gpt-5-nano) を使用
        覆盖代码行: llm_factory.py:406-423

        テスト目的:
          - get_lightweight_llm()が"lightweight"エイリアス経由でgpt-5-nanoを使用することを検証
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import get_lightweight_llm

        # Act - テスト対象の関数を実行する
        get_lightweight_llm()

        # Assert - 結果が期待されるものと一致することを確認する
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["model"] == "gpt-5-nano"
        assert call_kwargs.get("use_responses_api") is True


# ==================== 異常系テスト ====================

class TestLLMFactoryErrors:
    """異常系テスト (LLM-E01〜LLM-E11)

    テストID: LLM-E01 〜 LLM-E11
    """

    def test_unknown_model_raises_value_error(self, mock_settings_env):
        """
        LLM-E01: 未知モデル名でValueError
        覆盖代码行: llm_factory.py:136-140

        テスト目的:
          - MODEL_CONFIGSに存在しないモデル名を指定した場合、
            適切なエラーメッセージを含むValueErrorが発生することを検証
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # アクション & アサート - 異常の実行と検証
        with pytest.raises(ValueError, match="Unknown model: unknown-model"):
            LLMFactory.create_llm(model_name="unknown-model")

    def test_unknown_alias_raises_value_error(self, mock_settings_env):
        """
        LLM-E02: 未知エイリアスでValueError
        覆盖代码行: llm_factory.py:132-140

        テスト目的:
          - MODEL_ALIASESに存在しない名前は、MODEL_CONFIGSにも存在しないため、
            ValueErrorが発生することを検証
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # アクション & アサート - 例外の発生と検証
        with pytest.raises(ValueError, match="Unknown model"):
            LLMFactory.create_llm(model_name="nonexistent-alias")

    def test_missing_api_key_gpt51_chat(self, mock_settings_env):
        """
        LLM-E03: APIキー欠落でValueError (GPT5_1_CHAT_API_KEY)
        覆盖代码行: llm_factory.py:143-154

        テスト目的:
          - settings.GPT5_1_CHAT_API_KEYがNone/空の場合にValueErrorが発生
          - エラーメッセージにはフィールド名が含まれるが、キー値は含まれない
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # settingsのAPIキーをNoneに設定
        with patch("app.core.llm_factory.settings") as mock_settings:
            mock_settings.MODEL_NAME = "gpt-5.1-chat"
            mock_settings.GPT5_1_CHAT_API_KEY = None
            mock_settings.DOCKER_BASE_URL = "http://localhost:11434"

            # アクション & アサート - 異常の実行と検証
            with pytest.raises(ValueError, match="API key not found: GPT5_1_CHAT_API_KEY"):
                LLMFactory.create_llm(model_name="gpt-5.1-chat")

    def test_missing_api_key_claude_sonnet(self, mock_settings_env):
        """
        LLM-E04: APIキー欠落でValueError (CLAUDE_SONNET_4_5_KEY)
        覆盖代码行: llm_factory.py:143-154

        テスト目的:
          - 別のモデル(bedrock-claude-sonnet)でもAPIキー欠落時にValueErrorが発生することを検証
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        with patch("app.core.llm_factory.settings") as mock_settings:
            mock_settings.MODEL_NAME = "gpt-5.1-chat"
            mock_settings.CLAUDE_SONNET_4_5_KEY = None
            mock_settings.DOCKER_BASE_URL = "http://localhost:11434"

            # アクション & アサート - 異常の実行と検証
            with pytest.raises(ValueError, match="API key not found: CLAUDE_SONNET_4_5_KEY"):
                LLMFactory.create_llm(model_name="bedrock-claude-sonnet")

    def test_get_model_info_unknown_raises(self, mock_settings_env):
        """
        LLM-E05: get_model_info: 未知モデルでValueError
        覆盖代码行: llm_factory.py:226-235

        テスト目的:
          - get_model_info()に未知モデル名を渡した場合、ValueErrorが発生することを検証
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # アクション & アサート - 異常の実行と検証
        with pytest.raises(ValueError, match="Unknown model: unknown"):
            LLMFactory.get_model_info("unknown")

    def test_add_model_config_missing_api_key_field(self, mock_settings_env):
        """
        LLM-E06: add_model_config: api_key_field欠落でValueError
        覆盖代码行: llm_factory.py:289-299

        テスト目的:
          - 必須フィールド(api_key_field)が欠落している場合、ValueErrorが発生することを検証
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # アクション & アサート - 異常の実行と検証
        with pytest.raises(ValueError, match="Missing required fields"):
            LLMFactory.add_model_config("bad-model", {
                "model_name": "bad-model",
                # api_key_fieldがない
            })

    def test_add_model_config_missing_model_name(self, mock_settings_env):
        """
        LLM-E07: add_model_config: model_name欠落でValueError
        覆盖代码行: llm_factory.py:289-299

        テスト目的:
          - 必須フィールド(model_name)が欠落している場合、ValueErrorが発生することを検証
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # アクション & アサート - 例外の発生と検証
        with pytest.raises(ValueError, match="Missing required fields"):
            LLMFactory.add_model_config("bad-model", {
                "api_key_field": "SOME_KEY",
                # model_nameがない
            })

    def test_list_models_by_nonexistent_category(self, mock_settings_env):
        """
        LLM-E08: list_models_by_category: 存在しないカテゴリ→空辞書
        覆盖代码行: llm_factory.py:244-263

        テスト目的:
          - 存在しないカテゴリ名を指定した場合、空辞書が返されることを検証
          (エラーは発生しない)
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # Act - テスト対象の関数を実行する
        result = LLMFactory.list_models_by_category("premium")

        # Assert - 結果が予期したものと一致することを確認する
        assert result == {}

    def test_negative_temperature_no_validation(self, mock_chat_openai, mock_settings_env):
        """
        LLM-E09: temperature=負数は値チェックなしでそのまま格納
        覆盖代码行: llm_factory.py:157-203

        テスト目的:
          - llm_factory.pyにはtemperatureのバリデーションがないため、
            負数がそのままChatOpenAIに渡される(バリデーション不在の確認)
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # Act - テスト対象の関数を実行する
        LLMFactory.create_llm(model_name="gpt-5.1-chat", temperature=-1.0)

        # Assert - 結果が予期したものと一致することを確認（負の数が受け入れられる）
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["temperature"] == -1.0

    def test_zero_max_tokens_no_validation(self, mock_chat_openai, mock_settings_env):
        """
        LLM-E10: max_tokens=0は値チェックなしでそのまま格納
        覆盖代码行: llm_factory.py:161-211

        テスト目的:
          - max_tokensのバリデーションがないため、0がそのまま渡される
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # Act - テスト対象の関数を実行する
        LLMFactory.create_llm(model_name="gpt-5.1-chat", max_tokens=0)

        # Assert - 結果が予期したものと一致することを確認 (0が受け入れられる)
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["max_completion_tokens"] == 0

    def test_invalid_reasoning_effort_no_validation(self, mock_chat_openai, mock_settings_env):
        """
        LLM-E11: reasoning_effort不正値は値チェックなしでそのまま格納
        覆盖代码行: llm_factory.py:219-222

        テスト目的:
          - MODEL_CONFIGSのreasoning_effortを一時的に不正値に変更して検証
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # configのreasoning_effortを一時的に変更
        original = LLMFactory.MODEL_CONFIGS["gpt-5.1-chat"]["reasoning_effort"]
        try:
            LLMFactory.MODEL_CONFIGS["gpt-5.1-chat"]["reasoning_effort"] = "invalid"

            # Act - テスト対象の関数を実行する
            LLMFactory.create_llm(model_name="gpt-5.1-chat")

            # Assert - 验证结果符合预期 (不正値が受け入れられる)
            call_kwargs = mock_chat_openai.call_args[1]
            assert call_kwargs["reasoning_effort"] == "invalid"
        finally:
            # Teardown - 元の値に復元
            LLMFactory.MODEL_CONFIGS["gpt-5.1-chat"]["reasoning_effort"] = original


# ==================== セキュリティテスト ====================

@pytest.mark.security
class TestLLMFactorySecurity:
    """セキュリティテスト (LLM-SEC-01〜LLM-SEC-05)

    テストID: LLM-SEC-01 〜 LLM-SEC-05
    """

    def test_error_message_no_api_key_value(self, mock_settings_env):
        """
        LLM-SEC-01: エラーメッセージにAPIキー値が未含有
        覆盖代码行: llm_factory.py:143-154

        テスト目的:
          - APIキー欠落時のValueErrorメッセージに、
            テスト用のAPIキー値(test-gpt5-1-chat-key等)が含まれないことを検証
          - エラーメッセージにはフィールド名のみが表示されるべき
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory
        from conftest import MOCK_SETTINGS_ENV

        with patch("app.core.llm_factory.settings") as mock_settings:
            mock_settings.MODEL_NAME = "gpt-5.1-chat"
            mock_settings.GPT5_1_CHAT_API_KEY = None
            mock_settings.DOCKER_BASE_URL = "http://localhost:11434"

            # アクション & アサート - 異常の実行と検証
            with pytest.raises(ValueError) as exc_info:
                LLMFactory.create_llm(model_name="gpt-5.1-chat")

            error_msg = str(exc_info.value)
            # フィールド名は含まれるが、キー値は含まれない
            assert "GPT5_1_CHAT_API_KEY" in error_msg
            # テスト用APIキー値が含まれていないこと
            for key_value in MOCK_SETTINGS_ENV.values():
                assert key_value not in error_msg

    def test_all_aliases_point_to_valid_models(self, mock_settings_env):
        """
        LLM-SEC-02: MODEL_ALIASES整合性 - 全エイリアスが有効モデルを指す
        覆盖代码行: llm_factory.py:99-117

        テスト目的:
          - 15個のエイリアス全てがMODEL_CONFIGSに存在するモデルを
            参照していることを検証
          - 孤立したエイリアスはセキュリティリスク
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # アク & アサート - すべてのエイリアスを検証する
        for alias, target_model in LLMFactory.MODEL_ALIASES.items():
            assert target_model in LLMFactory.MODEL_CONFIGS, (
                f"エイリアス '{alias}' が存在しないモデル '{target_model}' を参照しています"
            )

    def test_add_model_config_defaults_are_safe(self, mock_settings_env):
        """
        LLM-SEC-03: add_model_config: デフォルト値の安全性
        覆盖代码行: llm_factory.py:301-310

        テスト目的:
          - add_model_config()が設定するデフォルト値が安全であることを検証
          - max_tokens: 4096 (過大でない)
          - temperature: 0.1 (安定出力)
          - description: "Custom model" (情報漏洩なし)
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        new_config = {
            "api_key_field": "SAFE_TEST_KEY",
            "model_name": "safe-test-model",
        }

        # Act - テスト対象の関数を実行する
        LLMFactory.add_model_config("safe-test-model", new_config)

        # Assert - 安全なデフォルト値の検証
        added = LLMFactory.MODEL_CONFIGS["safe-test-model"]
        assert added["max_tokens"] == 4096
        assert added["temperature"] == 0.1
        assert added["description"] == "Custom model"

    def test_all_models_have_api_key_field(self, mock_settings_env):
        """
        LLM-SEC-04: 全モデルにapi_key_fieldが存在し、空でないこと
        覆盖代码行: llm_factory.py:15-96

        テスト目的:
          - MODEL_CONFIGSの全7モデルにapi_key_fieldが定義され、
            空文字列やNoneでないことを検証
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory

        # アクション & アサート - すべてのモデルの検証
        for model_name, config in LLMFactory.MODEL_CONFIGS.items():
            assert "api_key_field" in config, (
                f"モデル '{model_name}' にapi_key_fieldが定義されていません"
            )
            assert config["api_key_field"], (
                f"モデル '{model_name}' のapi_key_fieldが空です"
            )

    def test_base_url_unified_across_models(self, mock_chat_openai, mock_settings_env):
        """
        LLM-SEC-05: ChatOpenAI初期化時のbase_url統一確認
        覆盖代码行: llm_factory.py:189-196

        テスト目的:
          - 全モデルがsettings.DOCKER_BASE_URLを使用してChatOpenAIを初期化すること
          - モデルごとに異なるbase_urlが設定されるとセキュリティリスクになる
        """
        # Arrange - テストデータの準備
        from app.core.llm_factory import LLMFactory
        from app.core.config import settings

        test_models = ["gpt-5.1-chat", "bedrock-claude-sonnet", "gpt-5-mini"]
        expected_base_url = settings.DOCKER_BASE_URL  # 実際の設定値を使用

        # Act & Assert - 各モデルが同じ base_url を使用することを確認する
        base_urls_used = []
        for model in test_models:
            mock_chat_openai.reset_mock()
            LLMFactory.create_llm(model_name=model)

            call_kwargs = mock_chat_openai.call_args[1]
            base_urls_used.append(call_kwargs.get("base_url"))
            assert call_kwargs["base_url"] == expected_base_url, (
                f"モデル '{model}' のbase_urlが '{call_kwargs.get('base_url')}' です。"
                f"期待値: '{expected_base_url}'"
            )

        # 全モデルが同じbase_urlを使用していることを確認
        assert len(set(base_urls_used)) == 1, (
            f"異なるbase_urlが使用されています: {set(base_urls_used)}"
        )
