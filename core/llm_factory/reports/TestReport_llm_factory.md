# llm_factory.py テスト報告

## テスト概要

| 項目 | 値 |
|------|-----|
| テスト対象 | `app/core/llm_factory.py` |
| テスト規格 | `llm_factory_tests.md` |
| 執行時間 | 2026-03-13 16:39:10 |
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
| LLM-001 | model_name=None時にsettings使用 | ✅ | 0.21ms |
| LLM-002 | test_all_aliases_resolve_correctly[default-gpt-5.1-chat] | ✅ | 0.46ms |
| LLM-002 | test_all_aliases_resolve_correctly[production-gpt-5.1-chat] | ✅ | 0.23ms |
| LLM-002 | test_all_aliases_resolve_correctly[high_performance-gpt-5.1-chat] | ✅ | 0.44ms |
| LLM-002 | test_all_aliases_resolve_correctly[development-gpt-5-mini] | ✅ | 0.28ms |
| LLM-002 | test_all_aliases_resolve_correctly[standard-gpt-5-mini] | ✅ | 0.22ms |
| LLM-002 | test_all_aliases_resolve_correctly[lightweight-gpt-5-nano] | ✅ | 0.24ms |
| LLM-002 | test_all_aliases_resolve_correctly[mini-gpt-5-mini] | ✅ | 0.34ms |
| LLM-002 | test_all_aliases_resolve_correctly[nano-gpt-5-nano] | ✅ | 0.32ms |
| LLM-002 | test_all_aliases_resolve_correctly[policy-gpt-5-mini] | ✅ | 0.23ms |
| LLM-002 | test_all_aliases_resolve_correctly[review-gpt-5.1-codex] | ✅ | 0.29ms |
| LLM-002 | test_all_aliases_resolve_correctly[chat-gpt-5-mini] | ✅ | 0.21ms |
| LLM-002 | test_all_aliases_resolve_correctly[extraction-gpt-5-nano] | ✅ | 0.24ms |
| LLM-002 | test_all_aliases_resolve_correctly[claude-bedrock-claude-sonnet] | ✅ | 0.29ms |
| LLM-002 | test_all_aliases_resolve_correctly[claude-production-bedrock-claude-sonnet] | ✅ | 0.31ms |
| LLM-002 | test_all_aliases_resolve_correctly[claude-lightweight-bedrock-claude-haiku] | ✅ | 0.34ms |
| LLM-003 | 直接モデル名指定 | ✅ | 0.25ms |
| LLM-004 | temperature引数優先 | ✅ | 0.3ms |
| LLM-005 | temperature=None時はconfig値使用 | ✅ | 0.25ms |
| LLM-006 | temperature省略 | ✅ | 0.25ms |
| LLM-007 | max_completion_tokens使用(GPT-5) | ✅ | 0.23ms |
| LLM-008 | max_tokens使用(非GPT-5) | ✅ | 0.27ms |
| LLM-009 | max_tokens上書き(GPT-5) | ✅ | 0.26ms |
| LLM-010 | max_tokens上書き(非GPT-5) | ✅ | 0.23ms |
| LLM-011 | reasoning_effort追加 | ✅ | 0.23ms |
| LLM-012 | reasoning_effortなし | ✅ | 0.27ms |
| LLM-013 | use_responses_api=True | ✅ | 0.24ms |
| LLM-014 | use_responses_api=False | ✅ | 0.23ms |
| LLM-015 | streaming=True設定 | ✅ | 0.25ms |
| LLM-016 | kwargs追加パラメータ伝播 | ✅ | 0.35ms |
| LLM-017 | エイリアス解決→config返却 | ✅ | 8.09ms |
| LLM-018 | 7モデル全列挙 | ✅ | 7.53ms |
| LLM-019 | productionカテゴリ→4モデル | ✅ | 7.57ms |
| LLM-020 | developmentカテゴリ→1モデル | ✅ | 7.47ms |
| LLM-021 | lightweightカテゴリ→2モデル | ✅ | 8.11ms |
| LLM-022 | 3カテゴリ取得 | ✅ | 9.37ms |
| LLM-023 | 新規モデル追加成功 | ✅ | 8.13ms |
| LLM-024 | get_llm: use_responses_apiデフォルト | ✅ | 0.24ms |
| LLM-025 | get_policy_llm: policyエイリアス | ✅ | 0.3ms |
| LLM-026 | get_review_llm: reviewエイリアス | ✅ | 0.28ms |
| LLM-027 | get_chat_llm: chatエイリアス | ✅ | 0.25ms |
| LLM-028 | get_extraction_llm: extractionエイリアス | ✅ | 0.28ms |
| LLM-029 | get_production_llm: productionエイリアス | ✅ | 0.29ms |
| LLM-030 | get_development_llm: developmentエイリアス | ✅ | 0.27ms |
| LLM-031 | get_lightweight_llm: lightweightエイリアス | ✅ | 0.26ms |
| Unknown | test_mock_works | ✅ | 0.38ms |

## 異常系テスト詳細

| ID | テスト名 | 結果 | 執行時間 |
|----|---------|------|----------|
| LLM-E01 | 未知モデル名でValueError | ✅ | 8.61ms |
| LLM-E02 | 未知エイリアスでValueError | ✅ | 7.54ms |
| LLM-E03 | APIキー欠落(GPT5_1_CHAT) | ✅ | 8.45ms |
| LLM-E04 | APIキー欠落(CLAUDE_SONNET) | ✅ | 8.36ms |
| LLM-E05 | 未知モデルでValueError | ✅ | 9.07ms |
| LLM-E06 | api_key_field欠落 | ✅ | 7.16ms |
| LLM-E07 | model_name欠落 | ✅ | 7.87ms |
| LLM-E08 | 存在しないカテゴリ→空辞書 | ✅ | 7.28ms |
| LLM-E09 | temperature負数(バリデーションなし) | ✅ | 0.23ms |
| LLM-E10 | max_tokens=0(バリデーションなし) | ✅ | 0.25ms |
| LLM-E11 | reasoning_effort不正値(バリデーションなし) | ✅ | 0.49ms |

## セキュリティテスト詳細

| ID | テスト名 | 結果 | 執行時間 |
|----|---------|------|----------|
| LLM-SEC-01 | エラーメッセージにAPIキー値未含有 | ✅ | 11.39ms |
| LLM-SEC-02 | 全エイリアス有効モデル参照 | ✅ | 7.89ms |
| LLM-SEC-03 | デフォルト値の安全性 | ✅ | 7.84ms |
| LLM-SEC-04 | 全モデルにapi_key_field存在 | ✅ | 8.74ms |
| LLM-SEC-05 | base_url統一確認 | ✅ | 0.41ms |

---

## 結論

✅ **全テスト通過** - llm_factoryモジュールは仕様通りに動作しています。

---

*レポート生成時間: 2026-03-13 16:39:10*
