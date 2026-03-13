# doc_reader_chat_logic テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| 実行日時 | 2026-03-12 19:49:27 |
| 総テスト数 | 28 |
| 通過 | 26 |
| 失敗 | 0 |
| 通過率 | 92.9% |

## 正常系テスト (13)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_string_input | ✅ | 0.5ms |
| N/A | test_list_with_type_text | ✅ | 0.45ms |
| N/A | test_list_with_content_key_single_level | ✅ | 0.23ms |
| N/A | test_list_with_content_key_multi_level | ✅ | 0.53ms |
| N/A | test_list_with_string_elements | ✅ | 0.25ms |
| N/A | test_other_type | ✅ | 0.2ms |
| N/A | test_empty_list | ✅ | 0.2ms |
| N/A | test_mixed_list | ✅ | 0.2ms |
| N/A | test_chat_llm_node_normal_execution | ✅ | 3.01ms |
| N/A | test_chat_llm_node_context_key_exists_value_none | ✅ | 4.98ms |
| N/A | test_chat_llm_node_context_key_not_exists | ✅ | 2.05ms |
| N/A | test_invoke_chat_graph_normal_execution | ✅ | 0.85ms |
| N/A | test_invoke_chat_graph_with_all_parameters | ✅ | 0.76ms |

## 異常系テスト (7)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_chat_llm_node_llm_not_initialized | ✅ | 0.25ms |
| N/A | test_chat_llm_node_chain_execution_exception | ✅ | 3.03ms |
| N/A | test_invoke_chat_graph_llm_not_initialized | ✅ | 0.38ms |
| N/A | test_invoke_chat_graph_graph_execution_exception | ✅ | 1.42ms |
| N/A | test_invoke_chat_graph_unexpected_message_type | ✅ | 1.19ms |
| N/A | test_invoke_chat_graph_no_messages | ✅ | 1.07ms |
| N/A | test_invoke_chat_graph_http_exception_rewrap | ⚠️ | 1.9ms |

## セキュリティテスト (8)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_error_id_traceability | ✅ | 1.55ms |
| N/A | test_no_stack_trace_in_response | ✅ | 1.37ms |
| N/A | test_exception_detail_exposure | ⚠️ | 1.67ms |
| N/A | test_xss_payload | ✅ | 1.12ms |
| N/A | test_sql_injection_input | ✅ | 0.89ms |
| N/A | test_prompt_injection_basic | ✅ | 0.78ms |
| N/A | test_prompt_injection_json_extraction | ✅ | 0.8ms |
| N/A | test_large_input | ✅ | 0.79ms |

---
*生成時刻: 2026-03-12 19:52:07*
