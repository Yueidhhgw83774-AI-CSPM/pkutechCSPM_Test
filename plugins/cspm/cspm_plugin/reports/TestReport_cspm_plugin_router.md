# CSPM Plugin Router 测试报告

| 项目 | 值 |
|------|-----|
| 测试对象 | `app/cspm_plugin/router.py` |
| 执行时间 | 2026-03-11 11:31:10 |
| 覆盖率目标 | 90% |

| 类别 | 总数 | 通过 | 失败 |
|------|------|------|------|
| 正常系 | 11 | 11 | 0 |
| 异常系 | 11 | 10 | 1 |
| 安全测试 | 4 | 3 | 1 |
| **合计** | **26** | **24** | **2** |

**通过率**: 92.3%


## 正常系测试详情
| 测试名称 | 结果 | 执行时间 |
|---------|------|----------|
| test_refine_policy_success | ✅ | 0.002s |
| test_refine_without_policy | ✅ | 0.002s |
| test_refine_explanation_request | ✅ | 0.001s |
| test_refine_empty_string_policy | ✅ | 0.001s |
| test_agent_aws_policy_generation | ✅ | 0.002s |
| test_agent_azure_policy_generation | ✅ | 0.001s |
| test_agent_gcp_policy_generation | ✅ | 0.001s |
| test_agent_minimal_recommendation | ✅ | 0.001s |
| test_validate_valid_json | ✅ | 0.001s |
| test_validate_valid_yaml | ✅ | 0.001s |
| test_validate_failure_response | ✅ | 0.001s |

## 异常系测试详情
| 测试名称 | 结果 | 执行时间 |
|---------|------|----------|
| test_refine_empty_prompt | ✅ | 0.001s |
| test_refine_missing_session_id | ✅ | 0.001s |
| test_refine_unexpected_exception | ✅ | 0.005s |
| test_refine_http_exception_propagation | ✅ | 0.001s |
| test_agent_missing_uid | ✅ | 0.001s |
| test_agent_invalid_cloud | ✅ | 0.001s |
| test_agent_execution_error | ✅ | 0.002s |
| test_agent_http_exception_propagation | ✅ | 0.001s |
| test_validate_empty_policy | ✅ | 0.001s |
| test_validate_whitespace_only_policy | ✅ | 0.001s |
| test_validate_tool_exception | ❌ | 0.001s |

## 安全测试测试详情
| 测试名称 | 结果 | 执行时间 |
|---------|------|----------|
| test_refine_error_no_stacktrace | ✅ | 0.002s |
| test_agent_error_no_internal_details | ❌ | 0.002s |
| test_policy_content_injection | ✅ | 0.001s |
| test_large_policy_context_handling | ✅ | 0.006s |

---
*报告生成时间: 2026-03-11 11:31:10*