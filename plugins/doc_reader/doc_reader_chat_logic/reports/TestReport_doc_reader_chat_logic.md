# doc_reader_chat_logic テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| 実行日時 | 2026-03-11 15:49:24 |
| 総テスト数 | 28 |
| 通過 | 26 |
| 失敗 | 0 |
| 通過率 | 92.9% |

## 正常系テスト (13)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_string_input | ✅ | 0.26ms |
| N/A | test_list_with_type_text | ✅ | 0.14ms |
| N/A | test_list_with_content_key_single_level | ✅ | 0.12ms |
| N/A | test_list_with_content_key_multi_level | ✅ | 0.13ms |
| N/A | test_list_with_string_elements | ✅ | 0.16ms |
| N/A | test_other_type | ✅ | 0.27ms |
| N/A | test_empty_list | ✅ | 0.26ms |
| N/A | test_mixed_list | ✅ | 0.34ms |
| N/A | test_chat_llm_node_normal_execution | ✅ | 10.68ms |
| N/A | test_chat_llm_node_context_key_exists_value_none | ✅ | 4.93ms |
| N/A | test_chat_llm_node_context_key_not_exists | ✅ | 3.49ms |
| N/A | test_invoke_chat_graph_normal_execution | ✅ | 1.11ms |
| N/A | test_invoke_chat_graph_with_all_parameters | ✅ | 0.96ms |

## 異常系テスト (7)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_chat_llm_node_llm_not_initialized | ✅ | 0.41ms |
| N/A | test_chat_llm_node_chain_execution_exception | ✅ | 4.6ms |
| N/A | test_invoke_chat_graph_llm_not_initialized | ✅ | 0.43ms |
| N/A | test_invoke_chat_graph_graph_execution_exception | ✅ | 3.94ms |
| N/A | test_invoke_chat_graph_unexpected_message_type | ✅ | 2.71ms |
| N/A | test_invoke_chat_graph_no_messages | ✅ | 1.34ms |
| N/A | test_invoke_chat_graph_http_exception_rewrap | ⚠️ | 3.11ms |

## セキュリティテスト (8)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | test_error_id_traceability | ✅ | 2.0ms |
| N/A | test_no_stack_trace_in_response | ✅ | 1.49ms |
| N/A | test_exception_detail_exposure | ⚠️ | 3.19ms |
| N/A | test_xss_payload | ✅ | 1.04ms |
| N/A | test_sql_injection_input | ✅ | 0.81ms |
| N/A | test_prompt_injection_basic | ✅ | 0.71ms |
| N/A | test_prompt_injection_json_extraction | ✅ | 0.76ms |
| N/A | test_large_input | ✅ | 2.18ms |

---
*生成時刻: 2026-03-11 15:51:56*
