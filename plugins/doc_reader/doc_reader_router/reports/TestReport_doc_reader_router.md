# doc_reader_router テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| 実行日時 | 2026-03-11 15:49:26 |
| 総テスト数 | 32 |
| 通過 | 30 |
| 失敗 | 0 |
| 通過率 | 93.8% |

## 正常系テスト (8)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_structure_success | ✅ | 66.89ms |
| N/A | test_structure_failure_returns_message | ✅ | 6.3ms |
| N/A | test_structure_japanese_text | ✅ | 4.76ms |
| N/A | test_structure_whitespace_preserved | ✅ | 4.83ms |
| N/A | test_chat_success | ✅ | 2.65ms |
| N/A | test_chat_with_source_document | ✅ | 1.61ms |
| N/A | test_chat_with_target_clouds_context | ✅ | 1.83ms |
| N/A | test_chat_long_prompt | ✅ | 2.05ms |

## 異常系テスト (9)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_empty_prompt_returns_400 | ✅ | 4.51ms |
| N/A | test_whitespace_only_prompt_returns_400 | ✅ | 3.2ms |
| N/A | test_missing_prompt_returns_422 | ✅ | 3.82ms |
| N/A | test_structure_llm_exception | ✅ | 6.62ms |
| N/A | test_structure_http_exception_reraised | ✅ | 4.85ms |
| N/A | test_chat_invoke_graph_exception | ✅ | 1.11ms |
| N/A | test_chat_http_exception_reraised | ✅ | 0.81ms |
| N/A | test_chat_missing_session_id | ✅ | 2.01ms |
| N/A | test_chat_empty_prompt | ✅ | 2.47ms |

## セキュリティテスト (15)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_error_id_traceability | ✅ | 6.27ms |
| N/A | test_no_stack_trace_in_response | ✅ | 7.57ms |
| N/A | test_xss_payload_handled | ✅ | 5.11ms |
| N/A | test_sql_injection_input | ✅ | 5.23ms |
| N/A | test_path_traversal_input | ✅ | 4.87ms |
| N/A | test_dos_large_input | ✅ | 185.4ms |
| N/A | test_session_id_guessing_prevention | ✅ | 1.42ms |
| N/A | test_json_injection_chat_request | ✅ | 4.79ms |
| N/A | test_json_injection_docreader_chat_request | ✅ | 2.04ms |
| N/A | test_no_internal_exception_info | ⚠️ | 6.76ms |
| N/A | test_unicode_control_characters | ✅ | 5.52ms |
| N/A | test_no_sensitive_info_leakage | ⚠️ | 6.04ms |
| N/A | test_ssrf_prevention | ✅ | 2.17ms |
| N/A | test_command_injection_prevention | ✅ | 4.36ms |
| N/A | test_deep_nested_json | ✅ | 2.07ms |

---
*生成時刻: 2026-03-11 15:51:56*
