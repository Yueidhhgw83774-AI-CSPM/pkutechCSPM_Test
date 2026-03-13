# doc_reader_router テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| 実行日時 | 2026-03-12 19:49:29 |
| 総テスト数 | 32 |
| 通過 | 30 |
| 失敗 | 0 |
| 通過率 | 93.8% |

## 正常系テスト (8)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_structure_success | ✅ | 3.87ms |
| N/A | test_structure_failure_returns_message | ✅ | 4.79ms |
| N/A | test_structure_japanese_text | ✅ | 2.86ms |
| N/A | test_structure_whitespace_preserved | ✅ | 2.65ms |
| N/A | test_chat_success | ✅ | 1.58ms |
| N/A | test_chat_with_source_document | ✅ | 3.06ms |
| N/A | test_chat_with_target_clouds_context | ✅ | 1.28ms |
| N/A | test_chat_long_prompt | ✅ | 1.17ms |

## 異常系テスト (9)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_empty_prompt_returns_400 | ✅ | 3.26ms |
| N/A | test_whitespace_only_prompt_returns_400 | ✅ | 2.74ms |
| N/A | test_missing_prompt_returns_422 | ✅ | 2.82ms |
| N/A | test_structure_llm_exception | ✅ | 3.04ms |
| N/A | test_structure_http_exception_reraised | ✅ | 4.43ms |
| N/A | test_chat_invoke_graph_exception | ✅ | 1.27ms |
| N/A | test_chat_http_exception_reraised | ✅ | 1.57ms |
| N/A | test_chat_missing_session_id | ✅ | 1.21ms |
| N/A | test_chat_empty_prompt | ✅ | 1.56ms |

## セキュリティテスト (15)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_error_id_traceability | ✅ | 3.48ms |
| N/A | test_no_stack_trace_in_response | ✅ | 3.28ms |
| N/A | test_xss_payload_handled | ✅ | 2.89ms |
| N/A | test_sql_injection_input | ✅ | 3.05ms |
| N/A | test_path_traversal_input | ✅ | 2.75ms |
| N/A | test_dos_large_input | ✅ | 37.07ms |
| N/A | test_session_id_guessing_prevention | ✅ | 1.42ms |
| N/A | test_json_injection_chat_request | ✅ | 2.68ms |
| N/A | test_json_injection_docreader_chat_request | ✅ | 1.2ms |
| N/A | test_no_internal_exception_info | ⚠️ | 4.22ms |
| N/A | test_unicode_control_characters | ✅ | 3.84ms |
| N/A | test_no_sensitive_info_leakage | ⚠️ | 4.2ms |
| N/A | test_ssrf_prevention | ✅ | 1.5ms |
| N/A | test_command_injection_prevention | ✅ | 4.9ms |
| N/A | test_deep_nested_json | ✅ | 1.73ms |

---
*生成時刻: 2026-03-12 19:52:07*
