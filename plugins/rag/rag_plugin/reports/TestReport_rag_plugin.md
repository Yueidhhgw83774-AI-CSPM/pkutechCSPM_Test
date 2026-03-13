# CSPM Plugin Router 测试报告

| 项目 | 值 |
|------|-----|
| 测试对象 | `app/cspm_plugin/router.py` |
| 执行时间 | 2026-03-13 16:58:29 |
| 覆盖率目标 | 90% |

| 类别 | 总数 | 通过 | 失败 |
|------|------|------|------|
| 正常系 | 65 | 65 | 0 |
| 异常系 | 24 | 24 | 0 |
| 安全测试 | 14 | 13 | 1 |
| **合计** | **103** | **102** | **1** |

**通过率**: 99.0%


## 正常系测试详情
| 测试名称 | 结果 | 执行时间 |
|---------|------|----------|
| test_refine_policy_success | ✅ | 0.002s |
| test_refine_without_policy | ✅ | 0.001s |
| test_refine_explanation_request | ✅ | 0.001s |
| test_refine_empty_string_policy | ✅ | 0.001s |
| test_agent_aws_policy_generation | ✅ | 0.001s |
| test_agent_azure_policy_generation | ✅ | 0.002s |
| test_agent_gcp_policy_generation | ✅ | 0.002s |
| test_agent_minimal_recommendation | ✅ | 0.001s |
| test_validate_valid_json | ✅ | 0.001s |
| test_validate_valid_yaml | ✅ | 0.002s |
| test_validate_failure_response | ✅ | 0.001s |
| test_rag_001_initialize_success | ✅ | 0.002s |
| test_rag_002_already_initialized | ✅ | 0.000s |
| test_rag_003_vectorstore_initialization | ✅ | 0.001s |
| test_rag_004_chat_model_initialization | ✅ | 0.000s |
| test_rag_005_aws_iam_auth | ✅ | 0.001s |
| test_rag_006_basic_auth_fallback | ✅ | 0.001s |
| test_rag_007_local_opensearch_auth | ✅ | 0.001s |
| test_rag_008_search_documents | ✅ | 0.001s |
| test_rag_009_search_with_scores | ✅ | 0.001s |
| test_rag_010_search_with_filters | ✅ | 0.001s |
| test_rag_011_get_chat_model | ✅ | 0.001s |
| test_rag_012_health_check_success | ✅ | 0.000s |
| test_rag_013_get_index_info | ✅ | 0.000s |
| test_rag_015_build_filter_cloud | ✅ | 0.000s |
| test_rag_016_build_filter_multiple | ✅ | 0.000s |
| test_rag_017_build_filter_none | ✅ | 0.000s |
| test_rag_046_build_filter_empty | ✅ | 0.000s |
| test_rag_018_convert_documents | ✅ | 0.000s |
| test_rag_019_convert_documents_with_scores | ✅ | 0.000s |
| test_rag_020_basic_search | ✅ | 0.000s |
| test_rag_021_filter_only_search | ✅ | 0.000s |
| test_rag_022_action_only_search | ✅ | 0.000s |
| test_rag_023_code_example_search | ✅ | 0.000s |
| test_rag_024_qa_search_with_sources | ✅ | 0.000s |
| test_rag_025_qa_search_without_sources | ✅ | 0.001s |
| test_rag_026_health_check_healthy | ✅ | 0.000s |
| test_rag_028_get_index_info | ✅ | 0.000s |
| test_rag_029_get_instance_first_call | ✅ | 0.000s |
| test_rag_030_get_instance_second_call | ✅ | 0.000s |
| test_rag_032_is_initialized | ✅ | 0.000s |
| test_rag_034_get_enhanced_rag_search | ✅ | 0.003s |
| test_rag_035_initialize_global_rag_system | ✅ | 0.001s |
| test_rag_036_search_endpoint | ✅ | 0.002s |
| test_rag_037_filter_search_endpoint | ✅ | 0.001s |
| test_rag_038_action_search_endpoint | ✅ | 0.001s |
| test_rag_039_code_example_endpoint | ✅ | 0.001s |
| test_rag_040_qa_endpoint | ✅ | 0.002s |
| test_rag_041_health_endpoint | ✅ | 0.001s |
| test_rag_042_index_info_endpoint | ✅ | 0.001s |
| test_rag_043_aws_ec2_search | ✅ | 0.001s |
| test_rag_044_aws_s3_search | ✅ | 0.001s |
| test_rag_045_security_search | ✅ | 0.001s |
| test_rag_perf_001_search_response_time | ✅ | 0.001s |
| test_rag_perf_002_qa_response_time | ✅ | 0.001s |
| test_rag_perf_003_concurrent_searches | ✅ | 0.005s |
| test_rag_perf_004_large_result_set | ✅ | 0.001s |
| test_rag_perf_005_health_check_response_time | ✅ | 0.001s |
| test_rag_perf_006_index_info_response_time | ✅ | 0.001s |
| test_rag_perf_007_repeated_searches | ✅ | 0.001s |
| test_rag_int_001_full_search_flow | ✅ | 0.002s |
| test_rag_int_002_full_qa_flow | ✅ | 0.001s |
| test_rag_int_003_filter_action_code_search | ✅ | 0.002s |
| test_rag_int_004_service_specific_searches | ✅ | 0.003s |
| test_rag_int_005_health_and_info_endpoints | ✅ | 0.001s |

## 异常系测试详情
| 测试名称 | 结果 | 执行时间 |
|---------|------|----------|
| test_refine_empty_prompt | ✅ | 0.001s |
| test_refine_missing_session_id | ✅ | 0.001s |
| test_refine_unexpected_exception | ✅ | 0.003s |
| test_refine_http_exception_propagation | ✅ | 0.001s |
| test_agent_missing_uid | ✅ | 0.002s |
| test_agent_invalid_cloud | ✅ | 0.002s |
| test_agent_execution_error | ✅ | 0.002s |
| test_agent_http_exception_propagation | ✅ | 0.001s |
| test_validate_empty_policy | ✅ | 0.001s |
| test_validate_whitespace_only_policy | ✅ | 0.001s |
| test_validate_tool_exception | ✅ | 0.005s |
| test_rag_e03_search_empty_query | ✅ | 0.001s |
| test_rag_e04_search_invalid_k | ✅ | 0.001s |
| test_rag_e06_qa_search_llm_error | ✅ | 0.001s |
| test_rag_e07_search_timeout | ✅ | 0.000s |
| test_rag_e08_invalid_filter_values | ✅ | 0.000s |
| test_rag_e09_opensearch_index_not_found | ✅ | 0.000s |
| test_rag_e11_api_endpoint_not_initialized | ✅ | 0.001s |
| test_rag_e13_search_result_parsing_error | ✅ | 0.001s |
| test_rag_e14_empty_search_results | ✅ | 0.001s |
| test_rag_e15_qa_no_context | ✅ | 0.000s |
| test_rag_e17_large_query_handling | ✅ | 0.001s |
| test_rag_e18_invalid_k_value_api | ✅ | 0.001s |
| test_rag_e19_malformed_request_body | ✅ | 0.001s |

## 安全测试测试详情
| 测试名称 | 结果 | 执行时间 |
|---------|------|----------|
| test_refine_error_no_stacktrace | ✅ | 0.002s |
| test_agent_error_no_internal_details | ❌ | 0.003s |
| test_policy_content_injection | ✅ | 0.002s |
| test_large_policy_context_handling | ✅ | 0.006s |
| test_rag_sec_001_query_injection_prevention | ✅ | 0.001s |
| test_rag_sec_002_filter_injection_prevention | ✅ | 0.000s |
| test_rag_sec_003_xss_prevention_in_response | ✅ | 0.002s |
| test_rag_sec_004_prompt_injection_prevention | ✅ | 0.002s |
| test_rag_sec_005_credential_masking_in_logs | ✅ | 0.001s |
| test_rag_sec_006_rate_limiting_simulation | ✅ | 0.004s |
| test_rag_sec_007_unauthorized_access_prevention | ✅ | 0.001s |
| test_rag_sec_008_input_size_limit | ✅ | 0.004s |
| test_rag_sec_009_path_traversal_prevention | ✅ | 0.001s |
| test_rag_sec_010_sensitive_data_exposure_prevention | ✅ | 0.001s |

---
*报告生成时间: 2026-03-13 16:58:29*