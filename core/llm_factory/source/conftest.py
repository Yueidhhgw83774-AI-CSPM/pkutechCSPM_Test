"""
llm_factory テストのpytest設定とフィクスチャ

このモジュールは以下を提供します:
- テスト結果収集とレポート生成
- ChatOpenAIモック
- 環境変数モック
- モジュール状態リセット
"""

import pytest
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv


def _load_source_root():
    """.env ファイルから SourceCodeRoot を読み込む

    Returns:
        str: SourceCodeRoot の絶対パス

    Raises:
        FileNotFoundError: .env ファイルが見つからない場合
        KeyError: SourceCodeRoot キーが .env に存在しない場合
    """
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if not env_path.exists():
        raise FileNotFoundError(f".env ファイルが見つかりません: {env_path}")

    load_dotenv(env_path)
    source_root = os.getenv("SourceCodeRoot")

    if not source_root:
        raise KeyError(".env ファイルに SourceCodeRoot キーが存在しません")

    return source_root


# ★★★ 重要: プロジェクトルートを動的に取得（絶対にハードコードしない） ★★★
project_root = _load_source_root()
sys.path.insert(0, project_root)

# レポート出力ディレクトリ
REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# .env ファイルから本物の環境変数を読み込む
env_file = Path(__file__).parent.parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"✅ 環境変数ファイルを読み込みました: {env_file}")
else:
    print(f"⚠️ 環境変数ファイルが存在しません: {env_file}")


# ===== テスト用環境変数 (.env ファイルから読み込み) =====
MOCK_SETTINGS_ENV = {
    "GPT5_1_CHAT_API_KEY": os.getenv("GPT5_1_CHAT_API_KEY", "sk-h6zKpdRQoYKEcj6vhTHMPg"),
    "GPT5_1_CODEX_API_KEY": os.getenv("GPT5_1_CODEX_API_KEY", "sk-h6zKpdRQoYKEcj6vhTHMPg"),
    "GPT5_2_API_KEY": os.getenv("GPT5_2_API_KEY", "sk-h6zKpdRQoYKEcj6vhTHMPg"),
    "GPT5_MINI_API_KEY": os.getenv("GPT5_MINI_API_KEY", "sk-EAt8QXSUBIdDJnXV4ROHrA"),
    "GPT5_NANO_API_KEY": os.getenv("GPT5_NANO_API_KEY", "sk-KbU6B0qXqUc2bru0rQ49vg"),
    "CLAUDE_HAIKU_4_5_KEY": os.getenv("CLAUDE_HAIKU_4_5_KEY", "sk-AZ2Y4zi06RkkiQ9IVnrw-g"),
    "CLAUDE_SONNET_4_5_KEY": os.getenv("CLAUDE_SONNET_4_5_KEY", "sk-ddGysRLuQbS68TPNdBnZDQ"),
    "GEMINI_API": os.getenv("GEMINI_API", "sk-6voS6352n0aLHWV3k_jFew"),
    "GEMINI_2_5_FLASH_API_KEY": os.getenv("GEMINI_2_5_FLASH_API_KEY", "sk-WjTxmZXCciVrbcuojoZ-zg"),
    "DOCKER_BASE_URL": os.getenv("DOCKER_BASE_URL", "https://172.19.75.181:8000"),
    "BASE_URL": os.getenv("BASE_URL", "https://172.19.75.181:8000"),
    "EMBEDDING_3_LARGE_API_KEY": os.getenv("EMBEDDING_3_LARGE_API_KEY", "sk-CVqmdwNwI9y0nHSVeDwwpA"),
    "EMBEDDING_3_SMALL_API_KEY": os.getenv("EMBEDDING_3_SMALL_API_KEY", "sk-S-I_qAHCPMJHlLCKAhOY9A"),
    "OPENSEARCH_URL": os.getenv("OPENSEARCH_URL", "https://172.19.75.181:9200/"),
    "LITELLM_MASTERKEY": os.getenv("LITELLM_MASTERKEY", "sk-123456"),
    "GPT4_1_API_KEY": os.getenv("GPT4_1_API_KEY", "sk-h6zKpdRQoYKEcj6vhTHMPg"),
    "GPT4_1_mini_API_KEY": os.getenv("GPT4_1_mini_API_KEY", "sk-EAt8QXSUBIdDJnXV4ROHrA"),
    "GPT4_1_nano_API_KEY": os.getenv("GPT4_1_nano_API_KEY", "sk-KbU6B0qXqUc2bru0rQ49vg"),
    "MODEL_NAME": "gpt-5.1-chat",
}


# ===== テスト結果収集器 =====
class TestResultCollector:
    """テスト結果を収集してレポート生成"""

    def __init__(self):
        self.results = {
            "normal": [],     # 正常系テスト
            "error": [],      # 異常系テスト
            "security": []    # セキュリティテスト
        }
        self.start_time = datetime.now()

    def add_result(self, nodeid: str, outcome: str, duration: float):
        """テスト結果を追加

        分類規則:
        - "Security" または "security" マーカー → security
        - "Errors" クラス名 または "_e0" → error
        - その他 → normal
        """
        # テスト名から読みやすい名前を取得
        test_name = nodeid.split("::")[-1]
        readable_name = _get_readable_name(test_name)

        result = {
            "id": _extract_test_id(nodeid),
            "name": readable_name,
            "outcome": outcome,
            "duration": round(duration * 1000, 2)  # ミリ秒
        }

        # カテゴリ分類
        if "Security" in nodeid or "security" in test_name.lower():
            self.results["security"].append(result)
        elif "Errors" in nodeid or "_e0" in test_name:
            self.results["error"].append(result)
        else:
            self.results["normal"].append(result)


def _extract_test_id(nodeid: str) -> str:
    """nodeIDからテストIDを抽出"""
    test_name = nodeid.split("::")[-1]

    # テストID命名パターン
    if "test_model_name_none" in test_name:
        return "LLM-001"
    elif "test_all_aliases_resolve" in test_name:
        return "LLM-002"
    elif "test_direct_model_name" in test_name:
        return "LLM-003"
    elif "test_temperature_argument_overrides" in test_name:
        return "LLM-004"
    elif "test_temperature_none_uses_config" in test_name:
        return "LLM-005"
    elif "test_temperature_none_and_config_none" in test_name:
        return "LLM-006"
    elif "test_max_completion_tokens_for_gpt5" in test_name:
        return "LLM-007"
    elif "test_max_tokens_for_non_gpt5" in test_name:
        return "LLM-008"
    elif "test_max_tokens_arg_overrides_gpt5" in test_name:
        return "LLM-009"
    elif "test_max_tokens_arg_overrides_non_gpt5" in test_name:
        return "LLM-010"
    elif "test_reasoning_effort_added" in test_name:
        return "LLM-011"
    elif "test_reasoning_effort_not_added" in test_name:
        return "LLM-012"
    elif "test_use_responses_api_true" in test_name:
        return "LLM-013"
    elif "test_use_responses_api_false" in test_name:
        return "LLM-014"
    elif "test_streaming_true" in test_name:
        return "LLM-015"
    elif "test_kwargs_propagated" in test_name:
        return "LLM-016"
    elif "test_get_model_info_with_alias" in test_name:
        return "LLM-017"
    elif "test_list_available_models" in test_name:
        return "LLM-018"
    elif "test_list_models_by_category_production" in test_name:
        return "LLM-019"
    elif "test_list_models_by_category_development" in test_name:
        return "LLM-020"
    elif "test_list_models_by_category_lightweight" in test_name:
        return "LLM-021"
    elif "test_get_all_categories" in test_name:
        return "LLM-022"
    elif "test_add_model_config_success" in test_name:
        return "LLM-023"
    elif "test_get_llm_default" in test_name:
        return "LLM-024"
    elif "test_get_policy_llm" in test_name:
        return "LLM-025"
    elif "test_get_review_llm" in test_name:
        return "LLM-026"
    elif "test_get_chat_llm" in test_name:
        return "LLM-027"
    elif "test_get_extraction_llm" in test_name:
        return "LLM-028"
    elif "test_get_production_llm" in test_name:
        return "LLM-029"
    elif "test_get_development_llm" in test_name:
        return "LLM-030"
    elif "test_get_lightweight_llm" in test_name:
        return "LLM-031"
    elif "test_unknown_model_raises" in test_name:
        return "LLM-E01"
    elif "test_unknown_alias_raises" in test_name:
        return "LLM-E02"
    elif "test_missing_api_key_gpt51" in test_name:
        return "LLM-E03"
    elif "test_missing_api_key_claude" in test_name:
        return "LLM-E04"
    elif "test_get_model_info_unknown" in test_name:
        return "LLM-E05"
    elif "test_add_model_config_missing_api_key_field" in test_name:
        return "LLM-E06"
    elif "test_add_model_config_missing_model_name" in test_name:
        return "LLM-E07"
    elif "test_list_models_by_nonexistent" in test_name:
        return "LLM-E08"
    elif "test_negative_temperature" in test_name:
        return "LLM-E09"
    elif "test_zero_max_tokens" in test_name:
        return "LLM-E10"
    elif "test_invalid_reasoning_effort" in test_name:
        return "LLM-E11"
    elif "test_error_message_no_api_key" in test_name:
        return "LLM-SEC-01"
    elif "test_all_aliases_point_to_valid" in test_name:
        return "LLM-SEC-02"
    elif "test_add_model_config_defaults_are_safe" in test_name:
        return "LLM-SEC-03"
    elif "test_all_models_have_api_key_field" in test_name:
        return "LLM-SEC-04"
    elif "test_base_url_unified" in test_name:
        return "LLM-SEC-05"
    else:
        return "Unknown"


def _get_readable_name(test_name: str) -> str:
    """テスト関数名を読みやすい名前に変換"""
    name_map = {
        # create_llmテスト (LLM-001〜LLM-016)
        "test_model_name_none_uses_settings": "model_name=None時にsettings使用",
        "test_all_aliases_resolve_correctly": "全エイリアス解決検証",
        "test_direct_model_name": "直接モデル名指定",
        "test_temperature_argument_overrides_config": "temperature引数優先",
        "test_temperature_none_uses_config_value": "temperature=None時はconfig値使用",
        "test_temperature_none_and_config_none_omitted": "temperature省略",
        "test_max_completion_tokens_for_gpt5": "max_completion_tokens使用(GPT-5)",
        "test_max_tokens_for_non_gpt5": "max_tokens使用(非GPT-5)",
        "test_max_tokens_arg_overrides_gpt5": "max_tokens上書き(GPT-5)",
        "test_max_tokens_arg_overrides_non_gpt5": "max_tokens上書き(非GPT-5)",
        "test_reasoning_effort_added_when_configured": "reasoning_effort追加",
        "test_reasoning_effort_not_added_when_absent": "reasoning_effortなし",
        "test_use_responses_api_true": "use_responses_api=True",
        "test_use_responses_api_false": "use_responses_api=False",
        "test_streaming_true": "streaming=True設定",
        "test_kwargs_propagated": "kwargs追加パラメータ伝播",

        # モデル情報テスト (LLM-017〜LLM-022)
        "test_get_model_info_with_alias": "エイリアス解決→config返却",
        "test_list_available_models_returns_7": "7モデル全列挙",
        "test_list_models_by_category_production": "productionカテゴリ→4モデル",
        "test_list_models_by_category_development": "developmentカテゴリ→1モデル",
        "test_list_models_by_category_lightweight": "lightweightカテゴリ→2モデル",
        "test_get_all_categories_returns_3": "3カテゴリ取得",

        # 動的モデル追加 (LLM-023)
        "test_add_model_config_success": "新規モデル追加成功",

        # 便利関数テスト (LLM-024〜LLM-031)
        "test_get_llm_default_uses_responses_api": "get_llm: use_responses_apiデフォルト",
        "test_get_policy_llm_uses_policy_alias": "get_policy_llm: policyエイリアス",
        "test_get_review_llm_uses_review_alias": "get_review_llm: reviewエイリアス",
        "test_get_chat_llm_uses_chat_alias": "get_chat_llm: chatエイリアス",
        "test_get_extraction_llm_uses_extraction_alias": "get_extraction_llm: extractionエイリアス",
        "test_get_production_llm_uses_production_alias": "get_production_llm: productionエイリアス",
        "test_get_development_llm_uses_development_alias": "get_development_llm: developmentエイリアス",
        "test_get_lightweight_llm_uses_lightweight_alias": "get_lightweight_llm: lightweightエイリアス",

        # 異常系テスト (LLM-E01〜LLM-E11)
        "test_unknown_model_raises_value_error": "未知モデル名でValueError",
        "test_unknown_alias_raises_value_error": "未知エイリアスでValueError",
        "test_missing_api_key_gpt51_chat": "APIキー欠落(GPT5_1_CHAT)",
        "test_missing_api_key_claude_sonnet": "APIキー欠落(CLAUDE_SONNET)",
        "test_get_model_info_unknown_raises": "未知モデルでValueError",
        "test_add_model_config_missing_api_key_field": "api_key_field欠落",
        "test_add_model_config_missing_model_name": "model_name欠落",
        "test_list_models_by_nonexistent_category": "存在しないカテゴリ→空辞書",
        "test_negative_temperature_no_validation": "temperature負数(バリデーションなし)",
        "test_zero_max_tokens_no_validation": "max_tokens=0(バリデーションなし)",
        "test_invalid_reasoning_effort_no_validation": "reasoning_effort不正値(バリデーションなし)",

        # セキュリティテスト (LLM-SEC-01〜LLM-SEC-05)
        "test_error_message_no_api_key_value": "エラーメッセージにAPIキー値未含有",
        "test_all_aliases_point_to_valid_models": "全エイリアス有効モデル参照",
        "test_add_model_config_defaults_are_safe": "デフォルト値の安全性",
        "test_all_models_have_api_key_field": "全モデルにapi_key_field存在",
        "test_base_url_unified_across_models": "base_url統一確認",
    }
    return name_map.get(test_name, test_name)


# グローバルコレクター
collector = TestResultCollector()


# ===== pytest フィクスチャ =====

@pytest.fixture(autouse=True)
def reset_llm_factory_module():
    """各テスト前後にllm_factoryモジュールの状態をリセット

    【リセット対象】
    - LLMFactoryクラスのクラス変数(MODEL_CONFIGS, MODEL_ALIASES)
    - モジュールレベル変数(llm_factory = LLMFactory())

    【必要性】
    - add_model_config()でMODEL_CONFIGSを変更するテストが他テストに影響しないようにする
    - mock_settings_envで環境変数を変更した場合、config.settingsの再初期化が必要
    """
    # テスト前にモジュールキャッシュをクリア
    modules_to_remove = [
        key for key in list(sys.modules.keys())
        if key.startswith("app.core.config") or key.startswith("app.core.llm_factory")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]

    yield

    # テスト後にもモジュールキャッシュをクリア
    modules_to_remove = [
        key for key in list(sys.modules.keys())
        if key.startswith("app.core.config") or key.startswith("app.core.llm_factory")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def mock_chat_openai():
    """ChatOpenAIモック(外部API呼び出しを防止)

    create_llm()が返すChatOpenAIインスタンスをモック化。
    call_argsで渡されたパラメータを検証可能にする。

    重要: patch を適用する前に llm_factory モジュールをクリアする必要がある
    """
    # まずモジュールキャッシュをクリア
    modules_to_remove = [
        key for key in list(sys.modules.keys())
        if key.startswith("app.core.llm_factory")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]

    with patch("app.core.llm_factory.ChatOpenAI") as mock_cls:
        mock_cls.return_value = MagicMock()
        yield mock_cls


@pytest.fixture
def mock_settings_env():
    """環境変数をテスト用値で設定

    MOCK_SETTINGS_ENVの全キーを環境変数に設定する。
    config + llm_factoryモジュールはautouseフィクスチャでリセット済み。
    """

    with patch.dict(os.environ, MOCK_SETTINGS_ENV, clear=False):
        yield


# ===== pytest フック =====

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """各テストの結果をキャプチャ"""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        collector.add_result(
            nodeid=item.nodeid,
            outcome=report.outcome,
            duration=report.duration
        )


def pytest_sessionfinish(session, exitstatus):
    """テストセッション終了時にレポート生成"""

    # 統計計算
    all_results = (
        collector.results["normal"] +
        collector.results["error"] +
        collector.results["security"]
    )

    total = len(all_results)
    passed = sum(1 for r in all_results if r["outcome"] == "passed")
    failed = sum(1 for r in all_results if r["outcome"] == "failed")
    xfailed = sum(1 for r in all_results if r["outcome"] == "xfailed")

    pass_rate = (passed / total * 100) if total > 0 else 0
    effective_pass_rate = (passed / (total - xfailed) * 100) if (total - xfailed) > 0 else 0

    # Markdownレポート生成
    _generate_markdown_report(collector.results, passed, failed, xfailed, pass_rate, effective_pass_rate)

    # JSONレポート生成
    _generate_json_report(collector.results, total, passed, failed, xfailed, pass_rate, effective_pass_rate)


def _generate_markdown_report(results, passed, failed, xfailed, pass_rate, effective_pass_rate):
    """Markdownレポート生成"""
    md_path = REPORTS_DIR / "TestReport_llm_factory.md"

    total = passed + failed + xfailed

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# llm_factory.py テスト報告\n\n")
        f.write("## テスト概要\n\n")
        f.write("| 項目 | 値 |\n")
        f.write("|------|-----|\n")
        f.write("| テスト対象 | `app/core/llm_factory.py` |\n")
        f.write("| テスト規格 | `llm_factory_tests.md` |\n")
        f.write(f"| 執行時間 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |\n")
        f.write("| カバレッジ目標 | 95% |\n\n")

        f.write("## テスト結果統計\n\n")
        f.write("| 類別 | 総数 | 通過 | 失敗 | 予期失敗 |\n")
        f.write("|------|------|------|------|----------|\n")

        def count_by_outcome(category_results):
            cat_passed = sum(1 for r in category_results if r["outcome"] == "passed")
            cat_failed = sum(1 for r in category_results if r["outcome"] == "failed")
            cat_xfailed = sum(1 for r in category_results if r["outcome"] == "xfailed")
            return len(category_results), cat_passed, cat_failed, cat_xfailed

        normal_total, normal_passed, normal_failed, normal_xfailed = count_by_outcome(results["normal"])
        error_total, error_passed, error_failed, error_xfailed = count_by_outcome(results["error"])
        security_total, security_passed, security_failed, security_xfailed = count_by_outcome(results["security"])

        f.write(f"| 正常系 | {normal_total} | {normal_passed} | {normal_failed} | {normal_xfailed} |\n")
        f.write(f"| 異常系 | {error_total} | {error_passed} | {error_failed} | {error_xfailed} |\n")
        f.write(f"| セキュリティ | {security_total} | {security_passed} | {security_failed} | {security_xfailed} |\n")
        f.write(f"| **合計** | **{total}** | **{passed}** | **{failed}** | **{xfailed}** |\n\n")

        f.write("## テスト通過率\n\n")
        f.write(f"- **実際通過率**: {pass_rate:.1f}%\n")
        f.write(f"- **有効通過率** (予期失敗を除外): {effective_pass_rate:.1f}%\n\n")

        f.write("---\n\n")

        # 詳細テスト結果
        for category, label in [("normal", "正常系"), ("error", "異常系"), ("security", "セキュリティ")]:
            if results[category]:
                f.write(f"## {label}テスト詳細\n\n")
                f.write("| ID | テスト名 | 結果 | 執行時間 |\n")
                f.write("|----|---------|------|----------|\n")

                for result in results[category]:
                    status = "✅" if result["outcome"] == "passed" else "❌" if result["outcome"] == "failed" else "⚠️"
                    f.write(f"| {result['id']} | {result['name']} | {status} | {result['duration']}ms |\n")
                f.write("\n")

        f.write("---\n\n")
        f.write("## 結論\n\n")
        if failed == 0:
            f.write("✅ **全テスト通過** - llm_factoryモジュールは仕様通りに動作しています。\n\n")
        else:
            f.write(f"❌ **{failed}件のテストが失敗** - 修正が必要です。\n\n")

        f.write("---\n\n")
        f.write(f"*レポート生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")

    print(f"\n✅ Markdownレポートを生成しました: {md_path}")


def _generate_json_report(results, total, passed, failed, xfailed, pass_rate, effective_pass_rate):
    """JSONレポート生成"""
    json_path = REPORTS_DIR / "TestReport_llm_factory.json"

    report = {
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "xfailed": xfailed,
            "pass_rate": f"{pass_rate:.1f}%",
            "effective_pass_rate": f"{effective_pass_rate:.1f}%"
        },
        "categories": {
            "normal": {"results": results["normal"]},
            "error": {"results": results["error"]},
            "security": {"results": results["security"]}
        },
        "execution_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"✅ JSONレポートを生成しました: {json_path}")
    print(f"\n✅ テストレポートを生成しました:")
    print(f"  - {REPORTS_DIR / 'TestReport_llm_factory.md'}")
    print(f"  - {REPORTS_DIR / 'TestReport_llm_factory.json'}")
    print()
