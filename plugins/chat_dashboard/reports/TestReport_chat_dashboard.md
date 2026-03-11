# Chat Dashboard 测试报告

| 项目 | 值 |
|------|-----|
| 测试对象 | `app/chat_dashboard/router.py` |
| 执行时间 | 2026-03-11 11:30:49 |
| 覆盖率目标 | 85% |

| 类别 | 总数 | 通过 | 失败 |
|------|------|------|------|
| 正常系 | 24 | 24 | 0 |
| 异常系 | 15 | 15 | 0 |
| 安全测试 | 16 | 11 | 5 |
| **合计** | **55** | **50** | **5** |

**通过率**: 90.9%


## 正常系测试详情
| 测试名称 | 结果 | 执行时间 |
|---------|------|----------|
| test_basic_auth_chat_success | ✅ | 0.003s |
| test_shared_hmac_auth_chat_success | ✅ | 0.002s |
| test_chat_with_context | ✅ | 0.001s |
| test_chat_with_opensearch_auth | ✅ | 0.001s |
| test_add_and_get_messages | ✅ | 0.000s |
| test_message_limit | ✅ | 0.001s |
| test_decode_basic_auth_success | ✅ | 0.000s |
| test_create_opensearch_client_success | ✅ | 0.001s |
| test_opensearch_client_cache | ✅ | 0.001s |
| test_extract_string_content | ✅ | 0.000s |
| test_extract_list_content | ✅ | 0.000s |
| test_generate_response_without_tool_calls | ✅ | 0.011s |
| test_shared_hmac_auth_direct | ✅ | 0.001s |
| test_llm_not_initialized_guard | ✅ | 0.003s |
| test_generate_final_response_fallback | ✅ | 0.004s |
| test_extract_output_text_content | ✅ | 0.000s |
| test_extract_nested_content | ✅ | 0.000s |
| test_extract_string_items_in_list | ✅ | 0.000s |
| test_extract_non_string_non_list_type | ✅ | 0.000s |
| test_get_message_count | ✅ | 0.000s |
| test_clear_session | ✅ | 0.000s |
| test_enhanced_input_with_comparison_keywords | ✅ | 0.001s |
| test_enhanced_input_with_no_violations | ✅ | 0.001s |
| test_singleton_behavior | ✅ | 0.001s |

## 异常系测试详情
| 测试名称 | 结果 | 执行时间 |
|---------|------|----------|
| test_no_authorization_header | ✅ | 0.001s |
| test_invalid_basic_token | ✅ | 0.001s |
| test_basic_token_no_colon | ✅ | 0.000s |
| test_empty_prompt | ✅ | 0.001s |
| test_missing_session_id | ✅ | 0.001s |
| test_invalid_context_extra_field | ✅ | 0.001s |
| test_llm_initialization_error | ✅ | 0.003s |
| test_llm_response_error | ✅ | 0.002s |
| test_opensearch_client_invalid_url | ✅ | 0.001s |
| test_tool_execution_error | ✅ | 0.005s |
| test_unknown_tool_call | ✅ | 0.002s |
| test_chat_message_unknown_role | ✅ | 0.000s |
| test_decode_basic_auth_error_message_leaks_info | ✅ | 0.000s |
| test_simple_chat_http_exception_reraise | ✅ | 0.001s |
| test_extract_text_no_text_elements | ✅ | 0.000s |

## 安全测试测试详情
| 测试名称 | 结果 | 执行时间 |
|---------|------|----------|
| test_credentials_not_logged | ✅ | 0.002s |
| test_opensearch_auth_not_in_response | ✅ | 0.002s |
| test_xss_in_prompt | ✅ | 0.001s |
| test_sql_injection_in_prompt | ✅ | 0.001s |
| test_large_prompt_handling | ❌ | 0.002s |
| test_session_isolation | ✅ | 0.000s |
| test_invalid_shared_hmac_format | ❌ | 0.191s |
| test_client_cache_size_limit | ✅ | 0.006s |
| test_prompt_injection_attempt | ✅ | 0.001s |
| test_unicode_normalization_attack | ✅ | 0.001s |
| test_null_byte_injection | ✅ | 0.001s |
| test_basic_auth_decode_valid_and_invalid | ✅ | 0.000s |
| test_session_fixation_prevention | ✅ | 0.002s |
| test_cache_key_contains_plaintext_password | ❌ | 0.001s |
| test_opensearch_query_injection | ❌ | 0.002s |
| test_session_cross_access | ❌ | 0.001s |

---
*报告生成时间: 2026-03-11 11:30:49*