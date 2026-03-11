# doc_reader_structuring テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| 実行日時 | 2026-03-11 15:49:26 |
| 総テスト数 | 38 |
| 通過 | 37 |
| 失敗 | 0 |
| 通過率 | 97.4% |

## 正常系テスト (18)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_basic_text_structuring | ✅ | 2.23ms |
| N/A | test_no_example_text | ✅ | 8.46ms |
| N/A | test_with_example_text | ✅ | 2.33ms |
| N/A | test_whitespace_only_example_text | ✅ | 1.99ms |
| N/A | test_severity_critical_normalization | ✅ | 2.54ms |
| N/A | test_severity_high_normalization | ✅ | 2.38ms |
| N/A | test_severity_medium_normalization | ✅ | 2.25ms |
| N/A | test_severity_low_normalization | ✅ | 2.37ms |
| N/A | test_severity_informational_normalization | ✅ | 1.82ms |
| N/A | test_severity_not_set_defaults_to_medium | ✅ | 2.17ms |
| N/A | test_severity_none_defaults_to_medium | ✅ | 1.62ms |
| N/A | test_severity_unknown_value_fallback_to_medium | ✅ | 1.51ms |
| N/A | test_severity_non_string_type_skip | ✅ | 3.31ms |
| N/A | test_categories_called | ✅ | 2.75ms |
| N/A | test_prompt_template_construction | ✅ | 2.3ms |
| N/A | test_chain_invocation | ✅ | 3.5ms |
| N/A | test_empty_dict_response | ✅ | 2.82ms |
| N/A | test_false_evaluation_response | ✅ | 2.57ms |

## 異常系テスト (9)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_llm_initialization_failure | ✅ | 0.95ms |
| N/A | test_chain_invocation_failure | ✅ | 2.68ms |
| N/A | test_json_parse_error | ✅ | 5.86ms |
| N/A | test_api_error_400 | ✅ | 2.79ms |
| N/A | test_api_error_detail_parsing | ✅ | 2.51ms |
| N/A | test_api_error_detail_parse_failure | ✅ | 1.74ms |
| N/A | test_str_output_parser_failure | ✅ | 1.68ms |
| N/A | test_llm_returns_none | ✅ | 2.52ms |
| N/A | test_status_code_gte_400_skip | ✅ | 2.66ms |

## セキュリティテスト (11)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_prompt_injection_defense | ✅ | 2.65ms |
| N/A | test_api_key_not_exposed_in_log | ✅ | 0.76ms |
| N/A | test_error_returns_none | ✅ | 2.41ms |
| N/A | test_long_text_processing | ✅ | 3.42ms |
| N/A | test_special_characters_processing | ✅ | 2.83ms |
| N/A | test_json_injection_defense | ✅ | 2.32ms |
| N/A | test_example_text_injection_defense | ✅ | 2.25ms |
| N/A | test_severity_value_injection | ✅ | 1.73ms |
| N/A | test_llm_output_sanitization | ⚠️ | 1.39ms |
| N/A | test_large_input_detection | ✅ | 2.27ms |
| N/A | test_example_text_length_check | ✅ | 2.02ms |

---
*生成時刻: 2026-03-11 15:51:56*
