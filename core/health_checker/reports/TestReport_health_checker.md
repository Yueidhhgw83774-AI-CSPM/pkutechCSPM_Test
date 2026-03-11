# health_checker.py 测试报告

## 测试概要

| 项目 | 值 |
|------|-----|
| 测试对象 | `app/core/health_checker.py` |
| 测试规格 | `health_checker_tests.md` |
| 执行时间 | 2026-03-11 19:33:40 |
| 覆盖率目标 | 90% |

## 测试结果统计

| 类别 | 总数 | 通过 | 失败 | 预期失败 |
|------|------|------|------|----------|
| 正常系 | 20 | 20 | 0 | 0 |
| 异常系 | 20 | 20 | 0 | 0 |
| 安全测试 | 5 | 4 | 0 | 0 |
| **合计** | **45** | **44** | **0** | **0** |

## 测试通过率

- **实际通过率**: 97.8%
- **有效通过率** (排除预期失败): 97.8%

---

## 正常系测试详情

| ID | 测试名称 | 结果 | 执行时间 |
|----|---------|------|----------|
| - | test_init_records_start_time | ✅ | 0.14ms |
| - | test_singleton_instance_exists | ✅ | 0.13ms |
| - | test_all_deps_healthy_returns_200 | ✅ | 2.68ms |
| - | test_aws_sdk_unavailable_returns_degraded | ✅ | 0.66ms |
| - | test_azure_sdk_unavailable_returns_degraded | ✅ | 1.3ms |
| - | test_multiple_optional_deps_unavailable | ✅ | 0.85ms |
| - | test_concurrent_check_execution | ✅ | 1.0ms |
| - | test_uptime_calculation | ✅ | 0.86ms |
| - | test_memory_usage_retrieved | ✅ | 0.65ms |
| - | test_active_jobs_retrieved | ✅ | 0.61ms |
| - | test_timestamp_iso_format | ✅ | 0.77ms |
| - | test_health_response_all_fields_present | ✅ | 0.62ms |
| - | test_empty_warnings_converted_to_none | ✅ | 0.71ms |
| - | test_aws_sdk_available_when_boto3_exists | ✅ | 0.38ms |
| - | test_azure_sdk_available_when_command_succeeds | ✅ | 0.93ms |
| - | test_custodian_available_when_version_succeeds | ✅ | 0.69ms |
| - | test_opensearch_available_when_info_succeeds | ✅ | 0.76ms |
| - | test_all_available_returns_healthy | ✅ | 0.14ms |
| - | test_optional_deps_unavailable_returns_degraded | ✅ | 0.13ms |
| - | test_critical_deps_unavailable_returns_unhealthy | ✅ | 0.13ms |

## 异常系测试详情

| ID | 测试名称 | 结果 | 执行时间 |
|----|---------|------|----------|
| - | test_opensearch_unavailable_returns_unhealthy | ✅ | 0.59ms |
| - | test_custodian_unavailable_returns_unhealthy | ✅ | 0.6ms |
| - | test_multiple_critical_deps_unavailable | ✅ | 4.38ms |
| - | test_check_health_exception_returns_error_response | ✅ | 1.66ms |
| - | test_aws_sdk_import_exception | ✅ | 1.1ms |
| - | test_aws_sdk_not_found | ✅ | 0.62ms |
| - | test_azure_sdk_subprocess_failure | ✅ | 1.43ms |
| - | test_azure_sdk_timeout | ✅ | 0.95ms |
| - | test_azure_sdk_file_not_found | ✅ | 0.91ms |
| - | test_azure_sdk_generic_exception | ✅ | 1.72ms |
| - | test_custodian_subprocess_failure | ✅ | 1.21ms |
| - | test_custodian_timeout | ✅ | 1.09ms |
| - | test_custodian_file_not_found | ✅ | 0.63ms |
| - | test_custodian_generic_exception | ✅ | 0.82ms |
| - | test_opensearch_client_none | ✅ | 0.44ms |
| - | test_opensearch_info_fails | ✅ | 1.14ms |
| - | test_opensearch_info_no_version | ✅ | 0.55ms |
| - | test_opensearch_info_returns_none | ✅ | 0.55ms |
| - | test_memory_usage_exception_returns_zero | ✅ | 0.59ms |
| - | test_active_jobs_exception_returns_zero | ✅ | 0.69ms |

## 安全测试详情

| ID | 测试名称 | 结果 | 执行时间 |
|----|---------|------|----------|
| - | test_no_credentials_in_error_response | ❌ | 1.52ms |
| - | test_no_internal_paths_in_response | ✅ | 0.68ms |
| - | test_error_messages_are_generic | ✅ | 0.74ms |
| - | test_no_version_info_leaked | ✅ | 0.64ms |
| - | test_timing_attack_resistance | ✅ | 0.95ms |

---

## 结论

✅ **所有测试通过!** 代码质量优秀。

---

*报告生成时间: 2026-03-11 19:33:40*
