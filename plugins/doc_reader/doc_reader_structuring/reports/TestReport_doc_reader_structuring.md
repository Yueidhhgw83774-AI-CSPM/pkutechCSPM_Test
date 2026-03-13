# doc_reader_structuring テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| 実行日時 | 2026-03-13 16:59:50 |
| 総テスト数 | 38 |
| 通過 | 37 |
| 失敗 | 0 |
| 通過率 | 97.4% |

## 正常系テスト (18)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_basic_text_structuring | ✅ | 2.18ms |
| N/A | test_no_example_text | ✅ | 1.47ms |
| N/A | test_with_example_text | ✅ | 4.01ms |
| N/A | test_whitespace_only_example_text | ✅ | 1.74ms |
| N/A | test_severity_critical_normalization | ✅ | 4.42ms |
| N/A | test_severity_high_normalization | ✅ | 3.13ms |
| N/A | test_severity_medium_normalization | ✅ | 2.08ms |
| N/A | test_severity_low_normalization | ✅ | 1.96ms |
| N/A | test_severity_informational_normalization | ✅ | 2.87ms |
| N/A | test_severity_not_set_defaults_to_medium | ✅ | 1.3ms |
| N/A | test_severity_none_defaults_to_medium | ✅ | 1.92ms |
| N/A | test_severity_unknown_value_fallback_to_medium | ✅ | 2.31ms |
| N/A | test_severity_non_string_type_skip | ✅ | 1.35ms |
| N/A | test_categories_called | ✅ | 1.95ms |
| N/A | test_prompt_template_construction | ✅ | 1.61ms |
| N/A | test_chain_invocation | ✅ | 2.79ms |
| N/A | test_empty_dict_response | ✅ | 2.36ms |
| N/A | test_false_evaluation_response | ✅ | 1.54ms |

## 異常系テスト (9)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_llm_initialization_failure | ✅ | 0.55ms |
| N/A | test_chain_invocation_failure | ✅ | 1.87ms |
| N/A | test_json_parse_error | ✅ | 2.79ms |
| N/A | test_api_error_400 | ✅ | 1.83ms |
| N/A | test_api_error_detail_parsing | ✅ | 1.71ms |
| N/A | test_api_error_detail_parse_failure | ✅ | 4.19ms |
| N/A | test_str_output_parser_failure | ✅ | 1.73ms |
| N/A | test_llm_returns_none | ✅ | 1.62ms |
| N/A | test_status_code_gte_400_skip | ✅ | 1.88ms |

## セキュリティテスト (11)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_prompt_injection_defense | ✅ | 1.88ms |
| N/A | test_api_key_not_exposed_in_log | ✅ | 0.91ms |
| N/A | test_error_returns_none | ✅ | 1.55ms |
| N/A | test_long_text_processing | ✅ | 1.98ms |
| N/A | test_special_characters_processing | ✅ | 1.99ms |
| N/A | test_json_injection_defense | ✅ | 1.62ms |
| N/A | test_example_text_injection_defense | ✅ | 1.88ms |
| N/A | test_severity_value_injection | ✅ | 2.29ms |
| N/A | test_llm_output_sanitization | ⚠️ | 2.73ms |
| N/A | test_large_input_detection | ✅ | 2.2ms |
| N/A | test_example_text_length_check | ✅ | 3.12ms |

---
*生成時刻: 2026-03-13 17:02:27*
