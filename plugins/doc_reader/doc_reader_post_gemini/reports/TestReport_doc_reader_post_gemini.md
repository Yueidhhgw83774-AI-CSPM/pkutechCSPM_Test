# doc_reader_post_gemini テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| 実行日時 | 2026-03-11 15:49:26 |
| 総テスト数 | 18 |
| 通過 | 18 |
| 失敗 | 0 |
| 通過率 | 100.0% |

## 正常系テスト (12)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_parse_compliance_normal | ✅ | 0.8ms |
| N/A | test_parse_compliance_with_output_lang | ✅ | 0.55ms |
| N/A | test_get_detail_normal | ✅ | 0.93ms |
| N/A | test_get_detail_multiple_platforms | ✅ | 0.81ms |
| N/A | test_extract_error_message_with_details | ✅ | 0.62ms |
| N/A | test_extract_error_message_without_details | ✅ | 0.48ms |
| N/A | test_delay_client_error_429_retry_allowed | ✅ | 2.27ms |
| N/A | test_delay_client_error_429_with_retry_delay | ✅ | 6.6ms |
| N/A | test_delay_client_error_429_without_retry_delay | ✅ | 1.99ms |
| N/A | test_delay_server_error_500 | ✅ | 2.73ms |
| N/A | test_delay_server_error_503 | ✅ | 2.88ms |
| N/A | test_delay_server_error_other | ✅ | 2.73ms |

## 異常系テスト (4)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_delay_client_error_non_429 | ✅ | 3.07ms |
| N/A | test_delay_client_error_delay_too_long | ✅ | 2.96ms |
| N/A | test_extract_error_message_exception | ✅ | 0.4ms |
| N/A | test_gemini_api_error_with_original_error | ✅ | 0.22ms |

## セキュリティテスト (2)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_prompt_injection_output_lang | ✅ | 1.14ms |
| N/A | test_prompt_injection_categories | ✅ | 1.38ms |

---
*生成時刻: 2026-03-11 15:51:56*
