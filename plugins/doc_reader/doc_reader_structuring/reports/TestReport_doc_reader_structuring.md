# doc_reader_structuring テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| 実行日時 | 2026-03-12 19:49:29 |
| 総テスト数 | 38 |
| 通過 | 37 |
| 失敗 | 0 |
| 通過率 | 97.4% |

## 正常系テスト (18)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_basic_text_structuring | ✅ | 1.95ms |
| N/A | test_no_example_text | ✅ | 1.37ms |
| N/A | test_with_example_text | ✅ | 8.19ms |
| N/A | test_whitespace_only_example_text | ✅ | 1.65ms |
| N/A | test_severity_critical_normalization | ✅ | 2.29ms |
| N/A | test_severity_high_normalization | ✅ | 1.81ms |
| N/A | test_severity_medium_normalization | ✅ | 1.36ms |
| N/A | test_severity_low_normalization | ✅ | 1.56ms |
| N/A | test_severity_informational_normalization | ✅ | 1.47ms |
| N/A | test_severity_not_set_defaults_to_medium | ✅ | 4.16ms |
| N/A | test_severity_none_defaults_to_medium | ✅ | 1.7ms |
| N/A | test_severity_unknown_value_fallback_to_medium | ✅ | 3.45ms |
| N/A | test_severity_non_string_type_skip | ✅ | 1.26ms |
| N/A | test_categories_called | ✅ | 2.11ms |
| N/A | test_prompt_template_construction | ✅ | 1.52ms |
| N/A | test_chain_invocation | ✅ | 1.68ms |
| N/A | test_empty_dict_response | ✅ | 1.6ms |
| N/A | test_false_evaluation_response | ✅ | 1.86ms |

## 異常系テスト (9)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_llm_initialization_failure | ✅ | 0.46ms |
| N/A | test_chain_invocation_failure | ✅ | 1.95ms |
| N/A | test_json_parse_error | ✅ | 1.78ms |
| N/A | test_api_error_400 | ✅ | 1.61ms |
| N/A | test_api_error_detail_parsing | ✅ | 1.39ms |
| N/A | test_api_error_detail_parse_failure | ✅ | 1.55ms |
| N/A | test_str_output_parser_failure | ✅ | 2.19ms |
| N/A | test_llm_returns_none | ✅ | 1.56ms |
| N/A | test_status_code_gte_400_skip | ✅ | 1.58ms |

## セキュリティテスト (11)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_prompt_injection_defense | ✅ | 1.42ms |
| N/A | test_api_key_not_exposed_in_log | ✅ | 1.62ms |
| N/A | test_error_returns_none | ✅ | 1.44ms |
| N/A | test_long_text_processing | ✅ | 2.01ms |
| N/A | test_special_characters_processing | ✅ | 7.41ms |
| N/A | test_json_injection_defense | ✅ | 1.82ms |
| N/A | test_example_text_injection_defense | ✅ | 2.27ms |
| N/A | test_severity_value_injection | ✅ | 1.65ms |
| N/A | test_llm_output_sanitization | ⚠️ | 1.74ms |
| N/A | test_large_input_detection | ✅ | 2.47ms |
| N/A | test_example_text_length_check | ✅ | 1.97ms |

---
*生成時刻: 2026-03-12 19:52:07*
