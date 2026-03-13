# Chat Dashboard テストレポート

| 項目 | 値 |
|------|-----|
| テスト対象 | `app/chat_dashboard/router.py` |
| 実行時刻 | 2026-03-12 20:10:17 |
| カバレッジ目標 | 85% |

| カテゴリ | 総数 | 通過 | 失敗 |
|------|------|------|------|
| 正常系 | 107 | 107 | 0 |
| 異常系 | 63 | 62 | 1 |
| セキュリティテスト | 50 | 43 | 7 |
| **合計** | **220** | **212** | **8** |

**通過率**: 96.4%


## 正常系テスト詳細
| テスト名 | 結果 | 実行時間 |
|---------|------|----------|
| test_basic_auth_chat_success | ✅ | 0.002s |
| test_shared_hmac_auth_chat_success | ✅ | 0.001s |
| test_chat_with_context | ✅ | 0.001s |
| test_chat_with_opensearch_auth | ✅ | 0.001s |
| test_add_and_get_messages | ✅ | 0.000s |
| test_message_limit | ✅ | 0.000s |
| test_decode_basic_auth_success | ✅ | 0.000s |
| test_create_opensearch_client_success | ✅ | 0.001s |
| test_opensearch_client_cache | ✅ | 0.001s |
| test_extract_string_content | ✅ | 0.000s |
| test_extract_list_content | ✅ | 0.000s |
| test_generate_response_without_tool_calls | ✅ | 0.009s |
| test_shared_hmac_auth_direct | ✅ | 0.001s |
| test_llm_not_initialized_guard | ✅ | 0.002s |
| test_generate_final_response_fallback | ✅ | 0.003s |
| test_extract_output_text_content | ✅ | 0.000s |
| test_extract_nested_content | ✅ | 0.000s |
| test_extract_string_items_in_list | ✅ | 0.000s |
| test_extract_non_string_non_list_type | ✅ | 0.000s |
| test_get_message_count | ✅ | 0.000s |
| test_clear_session | ✅ | 0.000s |
| test_enhanced_input_with_comparison_keywords | ✅ | 0.001s |
| test_enhanced_input_with_no_violations | ✅ | 0.001s |
| test_singleton_behavior | ✅ | 0.001s |
| test_refine_policy_success | ✅ | 0.001s |
| test_refine_without_policy | ✅ | 0.001s |
| test_refine_explanation_request | ✅ | 0.001s |
| test_refine_empty_string_policy | ✅ | 0.001s |
| test_agent_aws_policy_generation | ✅ | 0.001s |
| test_agent_azure_policy_generation | ✅ | 0.001s |
| test_agent_gcp_policy_generation | ✅ | 0.001s |
| test_agent_minimal_recommendation | ✅ | 0.001s |
| test_validate_valid_json | ✅ | 0.001s |
| test_validate_valid_yaml | ✅ | 0.001s |
| test_validate_failure_response | ✅ | 0.001s |
| test_validate_success | ✅ | 0.002s |
| test_validate_failure | ✅ | 0.001s |
| test_validate_empty_policy | ✅ | 0.001s |
| test_validate_json_response_structure | ✅ | 0.001s |
| test_schema_success | ✅ | 0.001s |
| test_schema_empty_target | ✅ | 0.001s |
| test_resources_success | ✅ | 0.001s |
| test_resources_invalid_cloud | ✅ | 0.001s |
| test_reference_success | ✅ | 0.002s |
| test_reference_no_results | ✅ | 0.001s |
| test_validate_tool_unavailable | ✅ | 0.001s |
| test_schema_tool_unavailable | ✅ | 0.001s |
| test_resources_tool_unavailable | ✅ | 0.001s |
| test_reference_tool_unavailable | ✅ | 0.001s |
| test_validate_exception | ✅ | 0.002s |
| test_schema_exception | ✅ | 0.001s |
| test_resources_exception | ✅ | 0.001s |
| test_reference_exception | ✅ | 0.001s |
| test_chat_hierarchical_mode | ✅ | 0.002s |
| test_chat_deep_agents_mode | ✅ | 0.001s |
| test_add_server_success | ✅ | 0.001s |
| test_list_servers | ✅ | 0.001s |
| test_list_tools | ✅ | 0.001s |
| test_get_status | ✅ | 0.003s |
| test_connect_server | ✅ | 0.001s |
| test_disconnect_server | ✅ | 0.001s |
| test_remove_server | ✅ | 0.001s |
| test_health_check | ✅ | 0.002s |
| test_sse_streaming_debug_mode | ✅ | 0.002s |
| test_sse_streaming_with_auth | ✅ | 0.001s |
| test_sse_streaming_token_filter | ✅ | 0.001s |
| test_update_session_summary_success | ✅ | 0.001s |
| test_get_session_metadata_success | ✅ | 0.002s |
| test_update_session_name_success | ✅ | 0.001s |
| test_is_meaningful_ai_content_true | ✅ | 0.000s |
| test_is_meaningful_ai_content_false_empty | ✅ | 0.000s |
| test_is_meaningful_ai_content_false_short | ✅ | 0.000s |
| test_is_meaningful_ai_content_false_json | ✅ | 0.000s |
| test_strip_thinking_tags_success | ✅ | 0.000s |
| test_strip_thinking_tags_multiple | ✅ | 0.000s |
| test_strip_thinking_tags_multiline | ✅ | 0.000s |
| test_strip_thinking_tags_empty | ✅ | 0.000s |
| test_get_messages_from_deepagents | ✅ | 0.002s |
| test_convert_langchain_messages | ✅ | 0.000s |
| test_merge_consecutive_messages | ✅ | 0.000s |
| test_extract_ai_content_string | ✅ | 0.000s |
| test_extract_ai_content_list | ✅ | 0.000s |
| test_save_thinking_logs_success | ✅ | 0.001s |
| test_save_thinking_logs_empty | ✅ | 0.000s |
| test_get_thinking_logs_success | ✅ | 0.001s |
| test_save_deep_agents_progress_success | ✅ | 0.001s |
| test_get_deep_agents_progress_success | ✅ | 0.001s |
| test_parse_checkpoint_data_success | ✅ | 0.000s |
| test_get_latest_checkpoint_success | ✅ | 0.001s |
| test_parse_metadata_dict | ✅ | 0.000s |
| test_parse_metadata_json_string | ✅ | 0.000s |
| test_build_request_response_map | ✅ | 0.000s |
| test_build_messages_from_map | ✅ | 0.000s |
| test_merge_agent_messages | ✅ | 0.000s |
| test_merge_agent_messages_dedup | ✅ | 0.000s |
| test_build_session_info | ✅ | 0.001s |
| test_extract_preview_from_checkpoint | ✅ | 0.000s |
| test_extract_preview_truncate | ✅ | 0.000s |
| test_find_session_name_success | ✅ | 0.001s |
| test_find_session_name_none | ✅ | 0.001s |
| test_get_sessions_list | ✅ | 0.003s |
| test_get_session_history | ✅ | 0.002s |
| test_get_storage_status | ✅ | 0.001s |
| test_update_session_success | ✅ | 0.003s |
| test_get_session_detail | ✅ | 0.004s |
| test_delete_session_success | ✅ | 0.003s |
| test_pagination_boundary_values | ✅ | 0.004s |

## 異常系テスト詳細
| テスト名 | 結果 | 実行時間 |
|---------|------|----------|
| test_no_authorization_header | ✅ | 0.001s |
| test_invalid_basic_token | ✅ | 0.001s |
| test_basic_token_no_colon | ✅ | 0.000s |
| test_empty_prompt | ✅ | 0.001s |
| test_missing_session_id | ✅ | 0.001s |
| test_invalid_context_extra_field | ✅ | 0.002s |
| test_llm_initialization_error | ✅ | 0.002s |
| test_llm_response_error | ✅ | 0.002s |
| test_opensearch_client_invalid_url | ✅ | 0.001s |
| test_tool_execution_error | ✅ | 0.002s |
| test_unknown_tool_call | ✅ | 0.002s |
| test_chat_message_unknown_role | ✅ | 0.000s |
| test_decode_basic_auth_error_message_leaks_info | ✅ | 0.000s |
| test_simple_chat_http_exception_reraise | ✅ | 0.001s |
| test_extract_text_no_text_elements | ✅ | 0.000s |
| test_refine_empty_prompt | ✅ | 0.001s |
| test_refine_missing_session_id | ✅ | 0.001s |
| test_refine_unexpected_exception | ✅ | 0.001s |
| test_refine_http_exception_propagation | ✅ | 0.001s |
| test_agent_missing_uid | ✅ | 0.001s |
| test_agent_invalid_cloud | ✅ | 0.001s |
| test_agent_execution_error | ✅ | 0.002s |
| test_agent_http_exception_propagation | ✅ | 0.001s |
| test_validate_empty_policy | ✅ | 0.001s |
| test_validate_whitespace_only_policy | ✅ | 0.001s |
| test_validate_tool_exception | ❌ | 0.001s |
| test_validate_missing_policy_content | ✅ | 0.001s |
| test_schema_missing_target | ✅ | 0.003s |
| test_resources_missing_cloud | ✅ | 0.001s |
| test_reference_missing_query | ✅ | 0.001s |
| test_chat_missing_session_id | ✅ | 0.001s |
| test_chat_missing_message | ✅ | 0.001s |
| test_chat_invalid_session_id | ✅ | 0.001s |
| test_chat_empty_message | ✅ | 0.001s |
| test_chat_nonexistent_server | ✅ | 0.001s |
| test_chat_client_error | ✅ | 0.001s |
| test_chat_timeout | ✅ | 0.001s |
| test_chat_internal_error | ✅ | 0.001s |
| test_add_server_duplicate | ✅ | 0.001s |
| test_add_server_invalid_config | ✅ | 0.001s |
| test_list_tools_nonexistent_server | ✅ | 0.001s |
| test_connect_nonexistent_server | ✅ | 0.001s |
| test_connect_already_connected | ✅ | 0.001s |
| test_disconnect_nonexistent_server | ✅ | 0.001s |
| test_disconnect_not_connected | ✅ | 0.001s |
| test_remove_nonexistent_server | ✅ | 0.001s |
| test_remove_connected_server | ✅ | 0.001s |
| test_server_connection_failure | ✅ | 0.001s |
| test_sse_auth_failure | ✅ | 0.002s |
| test_sse_invalid_auth_hash | ✅ | 0.001s |
| test_sse_missing_user_id | ✅ | 0.001s |
| test_sse_streaming_error | ✅ | 0.003s |
| test_get_session_metadata_not_found | ✅ | 0.001s |
| test_update_session_name_db_error | ✅ | 0.001s |
| test_save_thinking_logs_db_error | ✅ | 0.002s |
| test_get_sessions_user_id_missing | ✅ | 0.001s |
| test_update_session_invalid_data | ✅ | 0.001s |
| test_strip_thinking_tags_malformed | ✅ | 0.000s |
| test_parse_metadata_invalid_json | ✅ | 0.000s |
| test_parse_checkpoint_data_invalid | ✅ | 0.000s |
| test_get_messages_db_error | ✅ | 0.001s |
| test_extract_ai_content_none | ✅ | 0.000s |
| test_merge_consecutive_messages_empty | ✅ | 0.000s |

## セキュリティテストテスト詳細
| テスト名 | 結果 | 実行時間 |
|---------|------|----------|
| test_credentials_not_logged | ✅ | 0.002s |
| test_opensearch_auth_not_in_response | ✅ | 0.001s |
| test_xss_in_prompt | ✅ | 0.001s |
| test_sql_injection_in_prompt | ✅ | 0.001s |
| test_large_prompt_handling | ❌ | 0.002s |
| test_session_isolation | ✅ | 0.000s |
| test_invalid_shared_hmac_format | ❌ | 0.127s |
| test_client_cache_size_limit | ✅ | 0.005s |
| test_prompt_injection_attempt | ✅ | 0.001s |
| test_unicode_normalization_attack | ✅ | 0.001s |
| test_null_byte_injection | ✅ | 0.001s |
| test_basic_auth_decode_valid_and_invalid | ✅ | 0.000s |
| test_session_fixation_prevention | ✅ | 0.002s |
| test_cache_key_contains_plaintext_password | ❌ | 0.001s |
| test_opensearch_query_injection | ❌ | 0.001s |
| test_session_cross_access | ❌ | 0.000s |
| test_refine_error_no_stacktrace | ✅ | 0.001s |
| test_agent_error_no_internal_details | ❌ | 0.002s |
| test_policy_content_injection | ✅ | 0.001s |
| test_large_policy_context_handling | ✅ | 0.006s |
| test_validate_error_no_internal_details | ❌ | 0.001s |
| test_validate_xss_in_policy_content | ✅ | 0.001s |
| test_schema_command_injection | ✅ | 0.001s |
| test_resources_sql_injection | ✅ | 0.001s |
| test_reference_query_injection | ✅ | 0.001s |
| test_validate_log_injection | ✅ | 0.001s |
| test_schema_unicode_normalization | ✅ | 0.001s |
| test_sec_jwt_validation | ✅ | 0.438s |
| test_sec_hmac_validation | ✅ | 0.002s |
| test_sec_injection_prevention | ✅ | 0.001s |
| test_sec_path_traversal_prevention | ✅ | 0.001s |
| test_sec_rate_limiting | ✅ | 0.001s |
| test_sec_sensitive_data_protection | ✅ | 0.001s |
| test_sec_cors_validation | ✅ | 0.002s |
| test_sec_error_message_safety | ✅ | 0.001s |
| test_session_id_validation | ✅ | 0.001s |
| test_user_id_sql_injection | ✅ | 0.003s |
| test_session_name_xss_prevention | ✅ | 0.004s |
| test_thinking_logs_data_leakage | ✅ | 0.001s |
| test_session_isolation | ✅ | 0.002s |
| test_strip_thinking_tags_nested_attack | ✅ | 0.000s |
| test_metadata_json_injection | ✅ | 0.001s |
| test_checkpoint_data_size_limit | ✅ | 0.001s |
| test_session_deletion_cleanup | ✅ | 0.003s |
| test_parse_metadata_unicode_normalization | ✅ | 0.000s |
| test_deep_agents_progress_validation | ✅ | 0.001s |
| test_history_pagination_limit | ✅ | 0.003s |
| test_message_content_sanitization | ✅ | 0.000s |
| test_session_name_length_limit | ✅ | 0.003s |
| test_thinking_tags_recursive_removal | ✅ | 0.000s |

---
*レポート生成時刻: 2026-03-12 20:10:17*