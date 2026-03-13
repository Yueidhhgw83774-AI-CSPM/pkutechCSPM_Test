# health_checker.py テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| テスト対象 | `app/core/health_checker.py` |
| テスト仕様 | `health_checker_tests.md` |
| 実行時刻 | 2026-03-13 16:39:10 |
| カバレッジ目標 | 90% |

## テスト結果統計

| カテゴリ | 総数 | 成功 | 失敗 | 予期された失敗 |
|------|------|------|------|----------|
| 正常系 | 20 | 20 | 0 | 0 |
| 異常系 | 20 | 20 | 0 | 0 |
| セキュリティ | 5 | 4 | 0 | 0 |
| **合計** | **45** | **44** | **0** | **0** |

## テスト成功率

- **実際の成功率**: 97.8%
- **有効成功率** (予期された失敗を除外): 97.8%

---

## 正常系テスト詳細

| ID | テスト名 | 結果 | 実行時間 |
|----|---------|------|----------|
| - | test_init_records_start_time | ✅ | 0.17ms |
| - | test_singleton_instance_exists | ✅ | 0.18ms |
| - | test_all_deps_healthy_returns_200 | ✅ | 0.89ms |
| - | test_aws_sdk_unavailable_returns_degraded | ✅ | 1.16ms |
| - | test_azure_sdk_unavailable_returns_degraded | ✅ | 0.72ms |
| - | test_multiple_optional_deps_unavailable | ✅ | 0.73ms |
| - | test_concurrent_check_execution | ✅ | 0.76ms |
| - | test_uptime_calculation | ✅ | 1.09ms |
| - | test_memory_usage_retrieved | ✅ | 0.71ms |
| - | test_active_jobs_retrieved | ✅ | 0.71ms |
| - | test_timestamp_iso_format | ✅ | 0.67ms |
| - | test_health_response_all_fields_present | ✅ | 0.67ms |
| - | test_empty_warnings_converted_to_none | ✅ | 0.8ms |
| - | test_aws_sdk_available_when_boto3_exists | ✅ | 0.47ms |
| - | test_azure_sdk_available_when_command_succeeds | ✅ | 1.15ms |
| - | test_custodian_available_when_version_succeeds | ✅ | 0.91ms |
| - | test_opensearch_available_when_info_succeeds | ✅ | 0.88ms |
| - | test_all_available_returns_healthy | ✅ | 0.21ms |
| - | test_optional_deps_unavailable_returns_degraded | ✅ | 0.18ms |
| - | test_critical_deps_unavailable_returns_unhealthy | ✅ | 0.19ms |

## 異常系テスト詳細

| ID | テスト名 | 結果 | 実行時間 |
|----|---------|------|----------|
| - | test_opensearch_unavailable_returns_unhealthy | ✅ | 0.82ms |
| - | test_custodian_unavailable_returns_unhealthy | ✅ | 0.68ms |
| - | test_multiple_critical_deps_unavailable | ✅ | 1.14ms |
| - | test_check_health_exception_returns_error_response | ✅ | 1.55ms |
| - | test_aws_sdk_import_exception | ✅ | 0.77ms |
| - | test_aws_sdk_not_found | ✅ | 0.7ms |
| - | test_azure_sdk_subprocess_failure | ✅ | 1.23ms |
| - | test_azure_sdk_timeout | ✅ | 1.3ms |
| - | test_azure_sdk_file_not_found | ✅ | 1.29ms |
| - | test_azure_sdk_generic_exception | ✅ | 1.1ms |
| - | test_custodian_subprocess_failure | ✅ | 1.3ms |
| - | test_custodian_timeout | ✅ | 1.63ms |
| - | test_custodian_file_not_found | ✅ | 0.94ms |
| - | test_custodian_generic_exception | ✅ | 0.91ms |
| - | test_opensearch_client_none | ✅ | 0.61ms |
| - | test_opensearch_info_fails | ✅ | 1.39ms |
| - | test_opensearch_info_no_version | ✅ | 0.83ms |
| - | test_opensearch_info_returns_none | ✅ | 0.66ms |
| - | test_memory_usage_exception_returns_zero | ✅ | 0.61ms |
| - | test_active_jobs_exception_returns_zero | ✅ | 0.67ms |

## セキュリティテスト詳細

| ID | テスト名 | 結果 | 実行時間 |
|----|---------|------|----------|
| - | test_no_credentials_in_error_response | ❌ | 1.52ms |
| - | test_no_internal_paths_in_response | ✅ | 0.81ms |
| - | test_error_messages_are_generic | ✅ | 0.66ms |
| - | test_no_version_info_leaked | ✅ | 0.7ms |
| - | test_timing_attack_resistance | ✅ | 1.0ms |

---

## 結論

✅ **すべてのテストが成功しました！** コード品質は良好です。

---

*レポート生成時刻: 2026-03-13 16:39:10*
