# doc_reader_ai_pretreatment テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| 実行日時 | 2026-03-11 15:49:24 |
| 総テスト数 | 41 |
| 通過 | 39 |
| 失敗 | 0 |
| 通過率 | 95.1% |

## 正常系テスト (20)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_sleeper_waits_when_elapsed_less_than_min | ✅ | 1725.53ms |
| N/A | test_sleeper_no_wait_when_elapsed_exceeds_min | ✅ | 2.32ms |
| N/A | test_sleeper_custom_min_time | ✅ | 1.28ms |
| N/A | test_get_random_elements_partial | ✅ | 0.65ms |
| N/A | test_get_random_elements_all_when_num_exceeds | ✅ | 0.47ms |
| N/A | test_get_random_elements_all_when_num_negative | ✅ | 0.16ms |
| N/A | test_get_elements_partial | ✅ | 0.36ms |
| N/A | test_get_elements_all_when_num_exceeds | ✅ | 0.35ms |
| N/A | test_get_elements_all_when_num_negative | ✅ | 0.46ms |
| N/A | test_ai_pretreatment_random_mode | ✅ | 12018.4ms |
| N/A | test_ai_pretreatment_sequential_mode | ✅ | 6014.11ms |
| N/A | test_ai_pretreatment_max_output_limit | ✅ | 18024.89ms |
| N/A | test_ai_pretreatment_max_output_all | ✅ | 30051.21ms |
| N/A | test_ai_pretreatment_status_tracking_calls | ✅ | 12034.68ms |
| N/A | test_ai_pretreatment_target_clouds_added | ✅ | 6009.46ms |
| N/A | test_ai_pretreatment_related_controls_init | ✅ | 6015.73ms |
| N/A | test_ai_pretreatment_implemented_policies_init | ✅ | 6010.77ms |
| N/A | test_ai_pretreatment_max_output_zero | ✅ | 4.17ms |
| N/A | test_ai_pretreatment_max_output_equals_list_length | ✅ | 18032.11ms |
| N/A | test_ai_pretreatment_max_output_negative_two | ✅ | 1.73ms |

## 異常系テスト (12)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_ai_pretreatment_phase1_gemini_error | ✅ | 2.66ms |
| N/A | test_ai_pretreatment_phase2_gemini_error | ✅ | 3.63ms |
| N/A | test_ai_pretreatment_invalid_base64_pdf | ✅ | 0.48ms |
| N/A | test_ai_pretreatment_phase1_json_parse_error | ✅ | 1.22ms |
| N/A | test_ai_pretreatment_phase2_json_parse_error | ✅ | 2.45ms |
| N/A | test_ai_pretreatment_empty_compliance_list | ✅ | 1.46ms |
| N/A | test_get_random_elements_empty_list | ✅ | 0.13ms |
| N/A | test_get_elements_empty_list | ✅ | 0.13ms |
| N/A | test_ai_pretreatment_pikepdf_password_error | ✅ | 0.42ms |
| N/A | test_ai_pretreatment_pdfplumber_corrupted_error | ✅ | 0.74ms |
| N/A | test_ai_pretreatment_invalid_categories_json | ✅ | 6015.39ms |
| N/A | test_ai_pretreatment_resource_leak_prevention | ⚠️ | 3.59ms |

## セキュリティテスト (9)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_pdf_binary_injection_resistance | ✅ | 0.87ms |
| N/A | test_category_json_injection_resistance | ✅ | 6011.04ms |
| N/A | test_api_key_leakage_prevention | ⚠️ | 4.9ms |
| N/A | test_pdf_content_log_prevention | ✅ | 2.51ms |
| N/A | test_output_language_dos_resistance | ✅ | 6009.16ms |
| N/A | test_platform_parameter_injection_resistance | ✅ | 6009.99ms |
| N/A | test_large_pdf_dos_resistance | ✅ | 28.84ms |
| N/A | test_page_range_path_traversal_resistance | ✅ | 6019.16ms |
| N/A | test_category_json_redos_resistance | ✅ | 1.33ms |

---
*生成時刻: 2026-03-11 15:51:56*
