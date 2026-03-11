# llm_factory.py テスト報告

## テスト概要

| 項目 | 値 |
|------|-----|
| テスト対象 | `app/core/llm_factory.py` |
| テスト規格 | `llm_factory_tests.md` |
| 執行時間 | 2026-03-11 19:33:40 |
| カバレッジ目標 | 95% |

## テスト結果統計

| 類別 | 総数 | 通過 | 失敗 | 予期失敗 |
|------|------|------|------|----------|
| 正常系 | 46 | 46 | 0 | 0 |
| 異常系 | 11 | 11 | 0 | 0 |
| セキュリティ | 5 | 5 | 0 | 0 |
| **合計** | **62** | **62** | **0** | **0** |

## テスト通過率

- **実際通過率**: 100.0%
- **有効通過率** (予期失敗を除外): 100.0%

---

## 正常系テスト詳細

| ID | テスト名 | 結果 | 執行時間 |
|----|---------|------|----------|
| LLM-001 | model_name=None時にsettings使用 | ✅ | 0.2ms |
| LLM-002 | test_all_aliases_resolve_correctly[default-gpt-5.1-chat] | ✅ | 0.19ms |
| LLM-002 | test_all_aliases_resolve_correctly[production-gpt-5.1-chat] | ✅ | 0.29ms |
| LLM-002 | test_all_aliases_resolve_correctly[high_performance-gpt-5.1-chat] | ✅ | 0.17ms |
| LLM-002 | test_all_aliases_resolve_correctly[development-gpt-5-mini] | ✅ | 0.17ms |
| LLM-002 | test_all_aliases_resolve_correctly[standard-gpt-5-mini] | ✅ | 0.18ms |
| LLM-002 | test_all_aliases_resolve_correctly[lightweight-gpt-5-nano] | ✅ | 0.2ms |
| LLM-002 | test_all_aliases_resolve_correctly[mini-gpt-5-mini] | ✅ | 0.19ms |
| LLM-002 | test_all_aliases_resolve_correctly[nano-gpt-5-nano] | ✅ | 0.17ms |
| LLM-002 | test_all_aliases_resolve_correctly[policy-gpt-5-mini] | ✅ | 0.24ms |
| LLM-002 | test_all_aliases_resolve_correctly[review-gpt-5.1-codex] | ✅ | 0.19ms |
| LLM-002 | test_all_aliases_resolve_correctly[chat-gpt-5-mini] | ✅ | 0.19ms |
| LLM-002 | test_all_aliases_resolve_correctly[extraction-gpt-5-nano] | ✅ | 0.24ms |
| LLM-002 | test_all_aliases_resolve_correctly[claude-bedrock-claude-sonnet] | ✅ | 0.21ms |
| LLM-002 | test_all_aliases_resolve_correctly[claude-production-bedrock-claude-sonnet] | ✅ | 0.2ms |
| LLM-002 | test_all_aliases_resolve_correctly[claude-lightweight-bedrock-claude-haiku] | ✅ | 0.2ms |
| LLM-003 | 直接モデル名指定 | ✅ | 0.2ms |
| LLM-004 | temperature引数優先 | ✅ | 0.18ms |
| LLM-005 | temperature=None時はconfig値使用 | ✅ | 0.2ms |
| LLM-006 | temperature省略 | ✅ | 0.22ms |
| LLM-007 | max_completion_tokens使用(GPT-5) | ✅ | 0.2ms |
| LLM-008 | max_tokens使用(非GPT-5) | ✅ | 0.22ms |
| LLM-009 | max_tokens上書き(GPT-5) | ✅ | 0.18ms |
| LLM-010 | max_tokens上書き(非GPT-5) | ✅ | 0.19ms |
| LLM-011 | reasoning_effort追加 | ✅ | 0.17ms |
| LLM-012 | reasoning_effortなし | ✅ | 0.19ms |
| LLM-013 | use_responses_api=True | ✅ | 0.17ms |
| LLM-014 | use_responses_api=False | ✅ | 0.2ms |
| LLM-015 | streaming=True設定 | ✅ | 0.2ms |
| LLM-016 | kwargs追加パラメータ伝播 | ✅ | 0.19ms |
| LLM-017 | エイリアス解決→config返却 | ✅ | 7.23ms |
| LLM-018 | 7モデル全列挙 | ✅ | 7.17ms |
| LLM-019 | productionカテゴリ→4モデル | ✅ | 6.54ms |
| LLM-020 | developmentカテゴリ→1モデル | ✅ | 7.46ms |
| LLM-021 | lightweightカテゴリ→2モデル | ✅ | 7.34ms |
| LLM-022 | 3カテゴリ取得 | ✅ | 6.74ms |
| LLM-023 | 新規モデル追加成功 | ✅ | 6.57ms |
| LLM-024 | get_llm: use_responses_apiデフォルト | ✅ | 0.2ms |
| LLM-025 | get_policy_llm: policyエイリアス | ✅ | 0.18ms |
| LLM-026 | get_review_llm: reviewエイリアス | ✅ | 0.17ms |
| LLM-027 | get_chat_llm: chatエイリアス | ✅ | 0.19ms |
| LLM-028 | get_extraction_llm: extractionエイリアス | ✅ | 0.19ms |
| LLM-029 | get_production_llm: productionエイリアス | ✅ | 0.18ms |
| LLM-030 | get_development_llm: developmentエイリアス | ✅ | 0.18ms |
| LLM-031 | get_lightweight_llm: lightweightエイリアス | ✅ | 0.4ms |
| Unknown | test_mock_works | ✅ | 0.32ms |

## 異常系テスト詳細

| ID | テスト名 | 結果 | 執行時間 |
|----|---------|------|----------|
| LLM-E01 | 未知モデル名でValueError | ✅ | 7.79ms |
| LLM-E02 | 未知エイリアスでValueError | ✅ | 7.75ms |
| LLM-E03 | APIキー欠落(GPT5_1_CHAT) | ✅ | 8.12ms |
| LLM-E04 | APIキー欠落(CLAUDE_SONNET) | ✅ | 6.87ms |
| LLM-E05 | 未知モデルでValueError | ✅ | 7.34ms |
| LLM-E06 | api_key_field欠落 | ✅ | 6.67ms |
| LLM-E07 | model_name欠落 | ✅ | 6.8ms |
| LLM-E08 | 存在しないカテゴリ→空辞書 | ✅ | 6.89ms |
| LLM-E09 | temperature負数(バリデーションなし) | ✅ | 0.17ms |
| LLM-E10 | max_tokens=0(バリデーションなし) | ✅ | 0.3ms |
| LLM-E11 | reasoning_effort不正値(バリデーションなし) | ✅ | 0.19ms |

## セキュリティテスト詳細

| ID | テスト名 | 結果 | 執行時間 |
|----|---------|------|----------|
| LLM-SEC-01 | エラーメッセージにAPIキー値未含有 | ✅ | 8.64ms |
| LLM-SEC-02 | 全エイリアス有効モデル参照 | ✅ | 7.74ms |
| LLM-SEC-03 | デフォルト値の安全性 | ✅ | 7.36ms |
| LLM-SEC-04 | 全モデルにapi_key_field存在 | ✅ | 8.07ms |
| LLM-SEC-05 | base_url統一確認 | ✅ | 0.58ms |

---

## 結論

✅ **全テスト通過** - llm_factoryモジュールは仕様通りに動作しています。

---

*レポート生成時間: 2026-03-11 19:33:40*
