# doc_reader_ai_pretreatment テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| 実行日時 | 2026-03-12 19:49:27 |
| 総テスト数 | 41 |
| 通過 | 39 |
| 失敗 | 0 |
| 通過率 | 95.1% |

## 正常系テスト (20)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_sleeper_waits_when_elapsed_less_than_min | ✅ | 0.94ms |
| N/A | test_sleeper_no_wait_when_elapsed_exceeds_min | ✅ | 1.2ms |
| N/A | test_sleeper_custom_min_time | ✅ | 0.65ms |
| N/A | test_get_random_elements_partial | ✅ | 0.23ms |
| N/A | test_get_random_elements_all_when_num_exceeds | ✅ | 0.21ms |
| N/A | test_get_random_elements_all_when_num_negative | ✅ | 0.21ms |
| N/A | test_get_elements_partial | ✅ | 0.23ms |
| N/A | test_get_elements_all_when_num_exceeds | ✅ | 0.19ms |
| N/A | test_get_elements_all_when_num_negative | ✅ | 0.22ms |
| N/A | test_ai_pretreatment_random_mode | ✅ | 12020.07ms |
| N/A | test_ai_pretreatment_sequential_mode | ✅ | 6017.69ms |
| N/A | test_ai_pretreatment_max_output_limit | ✅ | 18036.02ms |
| N/A | test_ai_pretreatment_max_output_all | ✅ | 30021.82ms |
| N/A | test_ai_pretreatment_status_tracking_calls | ✅ | 12020.9ms |
| N/A | test_ai_pretreatment_target_clouds_added | ✅ | 6011.23ms |
| N/A | test_ai_pretreatment_related_controls_init | ✅ | 6003.97ms |
| N/A | test_ai_pretreatment_implemented_policies_init | ✅ | 6018.11ms |
| N/A | test_ai_pretreatment_max_output_zero | ✅ | 2.24ms |
| N/A | test_ai_pretreatment_max_output_equals_list_length | ✅ | 18022.21ms |
| N/A | test_ai_pretreatment_max_output_negative_two | ✅ | 3.49ms |

## 異常系テスト (12)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_ai_pretreatment_phase1_gemini_error | ✅ | 1.95ms |
| N/A | test_ai_pretreatment_phase2_gemini_error | ✅ | 2.7ms |
| N/A | test_ai_pretreatment_invalid_base64_pdf | ✅ | 0.36ms |
| N/A | test_ai_pretreatment_phase1_json_parse_error | ✅ | 1.38ms |
| N/A | test_ai_pretreatment_phase2_json_parse_error | ✅ | 1.68ms |
| N/A | test_ai_pretreatment_empty_compliance_list | ✅ | 2.21ms |
| N/A | test_get_random_elements_empty_list | ✅ | 0.23ms |
| N/A | test_get_elements_empty_list | ✅ | 0.22ms |
| N/A | test_ai_pretreatment_pikepdf_password_error | ✅ | 0.52ms |
| N/A | test_ai_pretreatment_pdfplumber_corrupted_error | ✅ | 0.48ms |
| N/A | test_ai_pretreatment_invalid_categories_json | ✅ | 6005.28ms |
| N/A | test_ai_pretreatment_resource_leak_prevention | ⚠️ | 2.56ms |

## セキュリティテスト (9)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_pdf_binary_injection_resistance | ✅ | 0.84ms |
| N/A | test_category_json_injection_resistance | ✅ | 6013.74ms |
| N/A | test_api_key_leakage_prevention | ⚠️ | 2.43ms |
| N/A | test_pdf_content_log_prevention | ✅ | 3.34ms |
| N/A | test_output_language_dos_resistance | ✅ | 6006.31ms |
| N/A | test_platform_parameter_injection_resistance | ✅ | 6024.05ms |
| N/A | test_large_pdf_dos_resistance | ✅ | 28.32ms |
| N/A | test_page_range_path_traversal_resistance | ✅ | 6010.67ms |
| N/A | test_category_json_redos_resistance | ✅ | 1.57ms |

---
*生成時刻: 2026-03-12 19:52:07*
