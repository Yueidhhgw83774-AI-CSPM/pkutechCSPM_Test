# doc_reader_chat_logic テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| 実行日時 | 2026-03-13 16:59:48 |
| 総テスト数 | 28 |
| 通過 | 26 |
| 失敗 | 0 |
| 通過率 | 92.9% |

## 正常系テスト (13)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_string_input | ✅ | 0.21ms |
| N/A | test_list_with_type_text | ✅ | 0.21ms |
| N/A | test_list_with_content_key_single_level | ✅ | 0.2ms |
| N/A | test_list_with_content_key_multi_level | ✅ | 0.22ms |
| N/A | test_list_with_string_elements | ✅ | 0.2ms |
| N/A | test_other_type | ✅ | 0.21ms |
| N/A | test_empty_list | ✅ | 0.26ms |
| N/A | test_mixed_list | ✅ | 0.22ms |
| N/A | test_chat_llm_node_normal_execution | ✅ | 3.99ms |
| N/A | test_chat_llm_node_context_key_exists_value_none | ✅ | 2.56ms |
| N/A | test_chat_llm_node_context_key_not_exists | ✅ | 2.59ms |
| N/A | test_invoke_chat_graph_normal_execution | ✅ | 1.2ms |
| N/A | test_invoke_chat_graph_with_all_parameters | ✅ | 1.16ms |

## 異常系テスト (7)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_chat_llm_node_llm_not_initialized | ✅ | 0.3ms |
| N/A | test_chat_llm_node_chain_execution_exception | ✅ | 2.49ms |
| N/A | test_invoke_chat_graph_llm_not_initialized | ✅ | 0.67ms |
| N/A | test_invoke_chat_graph_graph_execution_exception | ✅ | 1.65ms |
| N/A | test_invoke_chat_graph_unexpected_message_type | ✅ | 1.34ms |
| N/A | test_invoke_chat_graph_no_messages | ✅ | 1.98ms |
| N/A | test_invoke_chat_graph_http_exception_rewrap | ⚠️ | 2.15ms |

## セキュリティテスト (8)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_error_id_traceability | ✅ | 1.66ms |
| N/A | test_no_stack_trace_in_response | ✅ | 1.65ms |
| N/A | test_exception_detail_exposure | ⚠️ | 2.15ms |
| N/A | test_xss_payload | ✅ | 1.21ms |
| N/A | test_sql_injection_input | ✅ | 1.3ms |
| N/A | test_prompt_injection_basic | ✅ | 1.12ms |
| N/A | test_prompt_injection_json_extraction | ✅ | 1.07ms |
| N/A | test_large_input | ✅ | 2.28ms |

---
*生成時刻: 2026-03-13 17:02:27*
