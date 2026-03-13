# doc_reader_router テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| 実行日時 | 2026-03-13 16:59:50 |
| 総テスト数 | 32 |
| 通過 | 30 |
| 失敗 | 0 |
| 通過率 | 93.8% |

## 正常系テスト (8)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_structure_success | ✅ | 5.51ms |
| N/A | test_structure_failure_returns_message | ✅ | 3.8ms |
| N/A | test_structure_japanese_text | ✅ | 2.76ms |
| N/A | test_structure_whitespace_preserved | ✅ | 4.31ms |
| N/A | test_chat_success | ✅ | 2.47ms |
| N/A | test_chat_with_source_document | ✅ | 1.92ms |
| N/A | test_chat_with_target_clouds_context | ✅ | 1.17ms |
| N/A | test_chat_long_prompt | ✅ | 1.08ms |

## 異常系テスト (9)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_empty_prompt_returns_400 | ✅ | 3.75ms |
| N/A | test_whitespace_only_prompt_returns_400 | ✅ | 2.78ms |
| N/A | test_missing_prompt_returns_422 | ✅ | 3.04ms |
| N/A | test_structure_llm_exception | ✅ | 4.68ms |
| N/A | test_structure_http_exception_reraised | ✅ | 2.87ms |
| N/A | test_chat_invoke_graph_exception | ✅ | 1.18ms |
| N/A | test_chat_http_exception_reraised | ✅ | 2.78ms |
| N/A | test_chat_missing_session_id | ✅ | 1.51ms |
| N/A | test_chat_empty_prompt | ✅ | 1.11ms |

## セキュリティテスト (15)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_error_id_traceability | ✅ | 4.29ms |
| N/A | test_no_stack_trace_in_response | ✅ | 3.8ms |
| N/A | test_xss_payload_handled | ✅ | 3.78ms |
| N/A | test_sql_injection_input | ✅ | 4.35ms |
| N/A | test_path_traversal_input | ✅ | 4.06ms |
| N/A | test_dos_large_input | ✅ | 28.39ms |
| N/A | test_session_id_guessing_prevention | ✅ | 1.51ms |
| N/A | test_json_injection_chat_request | ✅ | 4.56ms |
| N/A | test_json_injection_docreader_chat_request | ✅ | 2.17ms |
| N/A | test_no_internal_exception_info | ⚠️ | 6.18ms |
| N/A | test_unicode_control_characters | ✅ | 4.68ms |
| N/A | test_no_sensitive_info_leakage | ⚠️ | 6.62ms |
| N/A | test_ssrf_prevention | ✅ | 2.27ms |
| N/A | test_command_injection_prevention | ✅ | 4.97ms |
| N/A | test_deep_nested_json | ✅ | 1.94ms |

---
*生成時刻: 2026-03-13 17:02:27*
