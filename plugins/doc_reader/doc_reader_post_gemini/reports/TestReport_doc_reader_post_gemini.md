# doc_reader_post_gemini テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| 実行日時 | 2026-03-13 16:59:50 |
| 総テスト数 | 18 |
| 通過 | 18 |
| 失敗 | 0 |
| 通過率 | 100.0% |

## 正常系テスト (12)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_parse_compliance_normal | ✅ | 0.8ms |
| N/A | test_parse_compliance_with_output_lang | ✅ | 0.64ms |
| N/A | test_get_detail_normal | ✅ | 0.85ms |
| N/A | test_get_detail_multiple_platforms | ✅ | 0.54ms |
| N/A | test_extract_error_message_with_details | ✅ | 0.58ms |
| N/A | test_extract_error_message_without_details | ✅ | 0.29ms |
| N/A | test_delay_client_error_429_retry_allowed | ✅ | 1.54ms |
| N/A | test_delay_client_error_429_with_retry_delay | ✅ | 2.95ms |
| N/A | test_delay_client_error_429_without_retry_delay | ✅ | 2.21ms |
| N/A | test_delay_server_error_500 | ✅ | 1.88ms |
| N/A | test_delay_server_error_503 | ✅ | 1.88ms |
| N/A | test_delay_server_error_other | ✅ | 1.3ms |

## 異常系テスト (4)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_delay_client_error_non_429 | ✅ | 1.41ms |
| N/A | test_delay_client_error_delay_too_long | ✅ | 1.01ms |
| N/A | test_extract_error_message_exception | ✅ | 0.64ms |
| N/A | test_gemini_api_error_with_original_error | ✅ | 0.24ms |

## セキュリティテスト (2)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_prompt_injection_output_lang | ✅ | 0.67ms |
| N/A | test_prompt_injection_categories | ✅ | 0.63ms |

---
*生成時刻: 2026-03-13 17:02:27*
