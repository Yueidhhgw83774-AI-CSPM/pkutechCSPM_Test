# doc_reader_output_models テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| 実行日時 | 2026-03-11 15:49:26 |
| 総テスト数 | 46 |
| 通過 | 46 |
| 失敗 | 0 |
| 通過率 | 100.0% |

## 正常系テスト (24)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_valid_instance_creation | ✅ | 0.22ms |
| N/A | test_field_metadata | ✅ | 0.26ms |
| N/A | test_all_fields_specified | ✅ | 0.52ms |
| N/A | test_page_range_continuous | ✅ | 0.49ms |
| N/A | test_page_range_multiple | ✅ | 0.39ms |
| N/A | test_critical_value | ✅ | 0.15ms |
| N/A | test_high_value | ✅ | 0.35ms |
| N/A | test_medium_value | ✅ | 0.16ms |
| N/A | test_low_value | ✅ | 0.3ms |
| N/A | test_information_value | ✅ | 0.22ms |
| N/A | test_string_to_enum_conversion | ✅ | 0.15ms |
| N/A | test_all_values_exist | ✅ | 0.15ms |
| N/A | test_required_fields_only | ✅ | 0.2ms |
| N/A | test_all_fields_specified | ✅ | 0.18ms |
| N/A | test_audit_empty_list | ✅ | 0.16ms |
| N/A | test_audit_multiple_items | ✅ | 0.16ms |
| N/A | test_remediation_empty_list | ✅ | 0.16ms |
| N/A | test_remediation_multiple_items | ✅ | 0.15ms |
| N/A | test_default_value_specified | ✅ | 0.15ms |
| N/A | test_default_value_none | ✅ | 0.21ms |
| N/A | test_category_multiple | ✅ | 0.16ms |
| N/A | test_model_dump_to_dict | ✅ | 0.22ms |
| N/A | test_model_json_schema | ✅ | 1.57ms |
| N/A | test_model_dump_json_mode | ✅ | 0.21ms |

## 異常系テスト (12)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_discription_missing | ✅ | 0.2ms |
| N/A | test_discription_type_coercion | ✅ | 0.21ms |
| N/A | test_required_fields_missing | ✅ | 0.29ms |
| N/A | test_page_type_coercion | ✅ | 0.44ms |
| N/A | test_invalid_value | ✅ | 0.57ms |
| N/A | test_case_sensitive | ✅ | 0.29ms |
| N/A | test_required_fields_missing | ✅ | 0.6ms |
| N/A | test_severity_invalid_value | ✅ | 0.21ms |
| N/A | test_audit_type_error | ✅ | 0.16ms |
| N/A | test_remediation_type_error | ✅ | 0.18ms |
| N/A | test_category_type_error | ✅ | 0.2ms |
| N/A | test_title_empty_string | ✅ | 0.29ms |

## セキュリティテスト (10)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_xss_payload_resistance | ✅ | 0.16ms |
| N/A | test_sql_injection_resistance | ✅ | 0.17ms |
| N/A | test_large_string_dos_resistance | ✅ | 0.5ms |
| N/A | test_unicode_control_characters_resistance | ✅ | 0.18ms |
| N/A | test_null_byte_injection_resistance | ✅ | 0.16ms |
| N/A | test_no_sensitive_fields | ✅ | 0.19ms |
| N/A | test_type_coercion_bypass_prevention | ✅ | 0.44ms |
| N/A | test_page_field_redos_resistance | ✅ | 0.23ms |
| N/A | test_path_traversal_payload_storage | ✅ | 0.14ms |
| N/A | test_severity_error_message_safety | ✅ | 0.16ms |

---
*生成時刻: 2026-03-11 15:51:56*
