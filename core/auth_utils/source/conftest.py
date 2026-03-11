# -*- coding: utf-8 -*-
"""
pytest fixtures for auth_utils module tests.
auth_utils 模块测试的 pytest fixtures。

This module provides shared fixtures for testing the auth_utils module.
本模块提供用于测试 auth_utils 模块的共享 fixtures。
"""

import os
import sys
import json
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

# Add the project root to Python path for imports
# 将项目根目录添加到 Python 路径以便导入
PROJECT_ROOT = r"C:\pythonProject\python_ai_cspm\platform_python_backend-testing"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# =============================================================================
# Module Reset Fixture | 模块重置 Fixture
# =============================================================================

@pytest.fixture(autouse=True)
def reset_auth_utils_module():
    """
    Reset auth_utils module state between tests.
    在测试之间重置 auth_utils 模块状态。

    Ensures test independence by clearing module cache and logger state.
    通过清除模块缓存和日志记录器状态来确保测试独立性。
    """
    yield
    # Clear module cache after test
    # 测试后清除模块缓存
    if "app.core.auth_utils" in sys.modules:
        del sys.modules["app.core.auth_utils"]


# =============================================================================
# Mock Request Fixtures | 模拟请求 Fixtures
# =============================================================================

@pytest.fixture
def mock_request_with_auth():
    """
    Provide a mock request with authentication header.
    提供带有认证头的模拟请求。
    """
    mock_headers = MagicMock()
    mock_headers.get = lambda key: (
        "Basic dXNlcjpwYXNz" if key.lower() == "authorization" else None
    )

    mock_request = MagicMock()
    mock_request.headers = mock_headers
    return mock_request


@pytest.fixture
def mock_request_without_auth():
    """
    Provide a mock request without authentication header.
    提供不带认证头的模拟请求。
    """
    mock_headers = MagicMock()
    mock_headers.get = lambda key: None

    mock_request = MagicMock()
    mock_request.headers = mock_headers
    return mock_request


# =============================================================================
# Test Report Generation | 测试报告生成
# =============================================================================

# Global test results storage
# 全局测试结果存储
_test_results = []


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to capture test results.
    捕获测试结果的钩子。
    """
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call":
        # Check if test is marked as xfail
        # 检查测试是否标记为 xfail
        is_xfail = hasattr(rep, "wasxfail") or (
            hasattr(item, '_evalxfail') and item._evalxfail.wasvalid()
        )

        result = {
            "nodeid": item.nodeid,
            "outcome": rep.outcome,
            "duration": rep.duration,
            "longrepr": str(rep.longrepr) if rep.longrepr else "",
            "is_xfail": is_xfail
        }
        _test_results.append(result)


def pytest_sessionfinish(session, exitstatus):
    """
    Pytest hook to generate detailed reports after all tests complete.
    在所有测试完成后生成详细报告的 pytest 钩子。
    """
    report_dir = r"C:\pythonProject\python_ai_cspm\TestReport\auth_utils\reports"
    os.makedirs(report_dir, exist_ok=True)

    # Parse test results
    # 解析测试结果
    normal_tests = []
    error_tests = []
    security_tests = []

    passed = 0
    failed = 0
    xfailed = 0

    for result in _test_results:
        nodeid = result["nodeid"]
        outcome = result["outcome"]
        duration = result["duration"]
        is_xfail = result.get("is_xfail", False)

        # Override outcome for xfail tests
        # 覆盖 xfail 测试的结果
        if is_xfail:
            outcome = "xfailed"

        # Parse test ID and categorize
        # 解析测试 ID 并分类
        if "test_auth_utils.py" in nodeid:
            # Security tests
            # 安全测试
            if "TestAuthUtilsSecurity" in nodeid:
                if "auth_header_not_fully_logged" in nodeid:
                    test_id, test_name = "AUTIL-SEC-01", "认证头不完全输出到日志"
                elif "error_message_does_not_expose_credentials" in nodeid:
                    test_id, test_name = "AUTIL-SEC-02", "错误消息不包含认证信息"
                elif "x_auth_hash_header_masked" in nodeid:
                    test_id, test_name = "AUTIL-SEC-03", "x-auth-hash头被掩码"
                elif "empty_header_value_filtering_safe" in nodeid:
                    test_id, test_name = "AUTIL-SEC-04", "空头值过滤安全性"
                elif "short_auth_header_filtering" in nodeid:
                    test_id, test_name = "AUTIL-SEC-05", "短认证头值过滤"
                else:
                    continue
                security_tests.append({
                    "id": test_id,
                    "name": test_name,
                    "status": outcome,
                    "duration": duration
                })
            # Error tests
            # 异常系测试
            elif "Error" in nodeid:
                if "test_no_auth_header" in nodeid:
                    test_id, test_name = "AUTIL-E01", "无认证头抛出HTTPException"
                elif "test_invalid_auth_format" in nodeid:
                    test_id, test_name = "AUTIL-E02", "无效认证格式抛出HTTPException"
                elif "test_empty_auth_header" in nodeid:
                    test_id, test_name = "AUTIL-E03", "空认证头抛出HTTPException"
                elif "test_request_without_auth_header" in nodeid:
                    test_id, test_name = "AUTIL-E06", "Request获取失败抛出HTTPException"
                elif "test_lowercase_basic_prefix" in nodeid:
                    test_id, test_name = "AUTIL-E07", "小写basic前缀抛出HTTPException"
                elif "test_no_endpoint_auth" in nodeid:
                    test_id, test_name = "AUTIL-E04", "无endpoint认证抛出HTTPException"
                elif "test_empty_endpoint_auth" in nodeid:
                    test_id, test_name = "AUTIL-E05", "空endpoint认证抛出HTTPException"
                else:
                    continue
                error_tests.append({
                    "id": test_id,
                    "name": test_name,
                    "status": outcome,
                    "duration": duration
                })
            # Normal tests
            # 正常系测试
            else:
                if "test_import_module" in nodeid:
                    test_id, test_name = "AUTIL-INIT", "模块导入"
                elif "test_extract_basic_token_with_space" in nodeid:
                    test_id, test_name = "AUTIL-001", "Basic令牌提取（有空格）"
                elif "test_extract_basic_token_without_space" in nodeid:
                    test_id, test_name = "AUTIL-002", "Basic令牌提取（无空格）"
                elif "test_extract_shared_hmac_token" in nodeid:
                    test_id, test_name = "AUTIL-003", "SHARED-HMAC头接受"
                elif "test_extract_from_request_lowercase" in nodeid:
                    test_id, test_name = "AUTIL-004", "从Request获取（小写）"
                elif "test_extract_from_request_uppercase" in nodeid:
                    test_id, test_name = "AUTIL-005", "从Request获取（大写）"
                elif "test_validate_with_opensearch_auth" in nodeid:
                    test_id, test_name = "AUTIL-006", "验证（有OpenSearch）"
                elif "test_validate_without_opensearch_auth" in nodeid:
                    test_id, test_name = "AUTIL-007", "验证（无OpenSearch）"
                elif "test_validate_opensearch_auth_default_none" in nodeid:
                    test_id, test_name = "AUTIL-007-B", "opensearch_auth默认None"
                elif "test_log_with_both_auth" in nodeid:
                    test_id, test_name = "AUTIL-008", "日志（两种认证）"
                elif "test_log_with_header_filtering" in nodeid:
                    test_id, test_name = "AUTIL-009", "日志（头过滤）"
                elif "test_log_without_auth" in nodeid:
                    test_id, test_name = "AUTIL-010", "日志（无认证）"
                elif "test_log_without_request_headers" in nodeid:
                    test_id, test_name = "AUTIL-010-B", "日志（无请求头）"
                elif "test_log_without_debug_level" in nodeid:
                    test_id, test_name = "AUTIL-011", "日志（DEBUG禁用）"
                else:
                    continue
                normal_tests.append({
                    "id": test_id,
                    "name": test_name,
                    "status": outcome,
                    "duration": duration
                })

        # Count outcomes
        # 统计结果
        if outcome == "passed":
            passed += 1
        elif outcome == "failed":
            failed += 1
        elif outcome == "xfailed":
            xfailed += 1

    total = len(_test_results)

    # Generate detailed Markdown report
    # 生成详细的 Markdown 报告
    report_md = f"""# auth_utils.py 测试报告

## 测试概要

| 项目 | 值 |
|------|-----|
| 测试对象 | `app/core/auth_utils.py` |
| 测试规格 | `auth_utils_tests.md` |
| 执行时间 | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} |
| 覆盖率目标 | 90% |

## 测试结果统计

| 类别 | 总数 | 通过 | 失败 | 预期失败 |
|------|------|------|------|---------|
| 正常系 | {len(normal_tests)} | {sum(1 for t in normal_tests if t['status']=='passed')} | {sum(1 for t in normal_tests if t['status']=='failed')} | {sum(1 for t in normal_tests if t['status']=='xfailed')} |
| 异常系 | {len(error_tests)} | {sum(1 for t in error_tests if t['status']=='passed')} | {sum(1 for t in error_tests if t['status']=='failed')} | {sum(1 for t in error_tests if t['status']=='xfailed')} |
| 安全测试 | {len(security_tests)} | {sum(1 for t in security_tests if t['status']=='passed')} | {sum(1 for t in security_tests if t['status']=='failed')} | {sum(1 for t in security_tests if t['status']=='xfailed')} |
| **合计** | **{total}** | **{passed}** | **{failed}** | **{xfailed}** |

## 测试通过率

- **实际通过率**: {(passed/total*100) if total>0 else 0:.1f}%
- **有效通过率** (排除预期失败): {(passed/(total-xfailed)*100) if (total-xfailed)>0 else 0:.1f}%

---

## 正常系测试详情

| ID | 测试名称 | 结果 | 执行时间 |
|----|---------|------|---------|
"""

    for t in sorted(normal_tests, key=lambda x: x['id']):
        status_icon = "✅ 通过" if t['status'] == "passed" else ("⚠️ 预期失败" if t['status'] == "xfailed" else "❌ 失败")
        report_md += f"| {t['id']} | {t['name']} | {status_icon} | {t['duration']*1000:.2f}ms |\n"

    report_md += """
---

## 异常系测试详情

| ID | 测试名称 | 结果 | 执行时间 |
|----|---------|------|---------|
"""

    for t in sorted(error_tests, key=lambda x: x['id']):
        status_icon = "✅ 通过" if t['status'] == "passed" else ("⚠️ 预期失败" if t['status'] == "xfailed" else "❌ 失败")
        report_md += f"| {t['id']} | {t['name']} | {status_icon} | {t['duration']*1000:.2f}ms |\n"

    report_md += """
---

## 安全测试详情

| ID | 测试名称 | 结果 | 执行时间 |
|----|---------|------|---------|
"""

    for t in sorted(security_tests, key=lambda x: x['id']):
        status_icon = "✅ 通过" if t['status'] == "passed" else ("⚠️ 预期失败" if t['status'] == "xfailed" else "❌ 失败")
        report_md += f"| {t['id']} | {t['name']} | {status_icon} | {t['duration']*1000:.2f}ms |\n"

    report_md += """
---

## 结论

"""

    if failed == 0:
        report_md += "✅ **所有非预期失败的测试均已通过。**\n\n"
    else:
        report_md += f"❌ **有 {failed} 个测试未通过。**\n\n"

    if xfailed > 0:
        report_md += f"⚠️ **有 {xfailed} 个预期失败的测试（已知问题）。**\n"

    report_md += f"""
---

*报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

    # Write Markdown report
    # 写入 Markdown 报告
    md_path = os.path.join(report_dir, "TestReport_auth_utils.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    # Generate JSON report
    # 生成 JSON 报告
    json_report = {
        "metadata": {
            "test_target": "app/core/auth_utils.py",
            "test_spec": "auth_utils_tests.md",
            "execution_time": datetime.now().isoformat(),
            "coverage_target": "90%"
        },
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "xfailed": xfailed,
            "pass_rate": (passed/total*100) if total>0 else 0
        },
        "results": {
            "normal": normal_tests,
            "error": error_tests,
            "security": security_tests
        }
    }

    json_path = os.path.join(report_dir, "TestReport_auth_utils.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_report, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 测试报告已生成:")
    print(f"  - {md_path}")
    print(f"  - {json_path}")


# =============================================================================
# Report Configuration | 报告配置
# =============================================================================

@pytest.fixture(scope="session")
def report_dir() -> str:
    """
    Provide the report output directory path.
    提供报告输出目录路径。
    """
    report_path = r"C:\pythonProject\python_ai_cspm\TestReport\auth_utils\reports"
    os.makedirs(report_path, exist_ok=True)
    return report_path
