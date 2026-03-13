# doc_reader_ai_pretreatment テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| 実行日時 | 2026-03-13 16:59:47 |
| 総テスト数 | 41 |
| 通過 | 39 |
| 失敗 | 0 |
| 通過率 | 95.1% |

## 正常系テスト (20)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_sleeper_waits_when_elapsed_less_than_min | ✅ | 1.05ms |
| N/A | test_sleeper_no_wait_when_elapsed_exceeds_min | ✅ | 0.81ms |
| N/A | test_sleeper_custom_min_time | ✅ | 0.67ms |
| N/A | test_get_random_elements_partial | ✅ | 0.21ms |
| N/A | test_get_random_elements_all_when_num_exceeds | ✅ | 0.21ms |
| N/A | test_get_random_elements_all_when_num_negative | ✅ | 0.2ms |
| N/A | test_get_elements_partial | ✅ | 0.23ms |
| N/A | test_get_elements_all_when_num_exceeds | ✅ | 0.19ms |
| N/A | test_get_elements_all_when_num_negative | ✅ | 0.24ms |
| N/A | test_ai_pretreatment_random_mode | ✅ | 12025.99ms |
| N/A | test_ai_pretreatment_sequential_mode | ✅ | 6010.78ms |
| N/A | test_ai_pretreatment_max_output_limit | ✅ | 18041.0ms |
| N/A | test_ai_pretreatment_max_output_all | ✅ | 30027.15ms |
| N/A | test_ai_pretreatment_status_tracking_calls | ✅ | 12011.43ms |
| N/A | test_ai_pretreatment_target_clouds_added | ✅ | 6004.81ms |
| N/A | test_ai_pretreatment_related_controls_init | ✅ | 6012.55ms |
| N/A | test_ai_pretreatment_implemented_policies_init | ✅ | 6011.88ms |
| N/A | test_ai_pretreatment_max_output_zero | ✅ | 2.19ms |
| N/A | test_ai_pretreatment_max_output_equals_list_length | ✅ | 18018.57ms |
| N/A | test_ai_pretreatment_max_output_negative_two | ✅ | 1.97ms |

## 異常系テスト (12)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_ai_pretreatment_phase1_gemini_error | ✅ | 1.95ms |
| N/A | test_ai_pretreatment_phase2_gemini_error | ✅ | 2.78ms |
| N/A | test_ai_pretreatment_invalid_base64_pdf | ✅ | 0.34ms |
| N/A | test_ai_pretreatment_phase1_json_parse_error | ✅ | 2.02ms |
| N/A | test_ai_pretreatment_phase2_json_parse_error | ✅ | 1.51ms |
| N/A | test_ai_pretreatment_empty_compliance_list | ✅ | 2.69ms |
| N/A | test_get_random_elements_empty_list | ✅ | 0.25ms |
| N/A | test_get_elements_empty_list | ✅ | 0.22ms |
| N/A | test_ai_pretreatment_pikepdf_password_error | ✅ | 0.73ms |
| N/A | test_ai_pretreatment_pdfplumber_corrupted_error | ✅ | 1.1ms |
| N/A | test_ai_pretreatment_invalid_categories_json | ✅ | 6006.05ms |
| N/A | test_ai_pretreatment_resource_leak_prevention | ⚠️ | 3.1ms |

## セキュリティテスト (9)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_pdf_binary_injection_resistance | ✅ | 1.04ms |
| N/A | test_category_json_injection_resistance | ✅ | 6010.53ms |
| N/A | test_api_key_leakage_prevention | ⚠️ | 2.52ms |
| N/A | test_pdf_content_log_prevention | ✅ | 1.91ms |
| N/A | test_output_language_dos_resistance | ✅ | 6007.11ms |
| N/A | test_platform_parameter_injection_resistance | ✅ | 6013.72ms |
| N/A | test_large_pdf_dos_resistance | ✅ | 26.04ms |
| N/A | test_page_range_path_traversal_resistance | ✅ | 6013.87ms |
| N/A | test_category_json_redos_resistance | ✅ | 2.05ms |

---
*生成時刻: 2026-03-13 17:02:27*
