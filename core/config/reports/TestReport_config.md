# config.py 测试报告

## 测试概要

| 项目 | 值 |
|------|-----|
| 测试对象 | `app/core/config.py` |
| 测试规格 | `config_tests.md` |
| 执行时间 | 2026-03-11 19:33:40 |
| 覆盖率目标 | 85% |

## 测试结果统计

| 类别 | 总数 | 通过 | 失败 | 预期失败 |
|------|------|------|------|----------|
| 正常系 | 9 | 9 | 0 | 0 |
| 异常系 | 5 | 3 | 2 | 0 |
| 安全测试 | 0 | 0 | 0 | 0 |
| **合计** | **14** | **12** | **2** | **0** |

## 测试通过率

- **实际通过率**: 85.7%
- **有效通过率** (排除预期失败): 85.7%

---

## 正常系测试详情

| ID | 测试名称 | 结果 | 执行时间 |
|----|---------|------|----------|
| test_import_config_module | Test Import Config Module | ✅ | 0.000s |
| test_load_from_env | 环境变量から設定読み込み | ✅ | 0.000s |
| test_default_values | デフォルト値の適用 | ✅ | 0.000s |
| test_opensearch_url_generation | OpenSearch URL生成 | ✅ | 0.000s |
| test_min_interval_calculation | MIN_INTERVAL_SECONDS計算 | ✅ | 0.000s |
| test_settings_instance_exists | 設定インスタンス存在確認 | ✅ | 0.000s |
| test_is_aws_opensearch_service | AWS OpenSearch Service判定 | ✅ | 0.000s |
| test_settings_and_helper_function_work_together | Test Settings And Helper Function Work Together | ✅ | 0.000s |
| test_min_interval_updates_with_rpm_limit | Test Min Interval Updates With Rpm Limit | ✅ | 0.000s |

## 异常系测试详情

| ID | 测试名称 | 结果 | 执行时间 |
|----|---------|------|----------|
| test_missing_required_fields | 必須設定の欠落 | ✅ | 0.004s |
| test_invalid_rpm_limit_type | Test Invalid Rpm Limit Type | ✅ | 0.002s |
| test_invalid_opensearch_url_format | Test Invalid Opensearch Url Format | ✅ | 0.002s |
| test_invalid_url_format | Test Invalid Url Format | ❌ | 0.000s |
| test_none_url | Test None Url | ❌ | 0.000s |

---

## 结论

❌ **有2个测试失败**, 请检查详细信息并修复问题。

---

*报告生成时间: 2026-03-11 19:33:40*
