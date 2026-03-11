# -*- coding: utf-8 -*-
"""
pytest fixtures for permission_checker module tests.
permission_checker 模块测试的 pytest fixtures。

This module provides shared fixtures for testing the permission_checker module.
本模块提供用于测试 permission_checker 模块的共享 fixtures。
"""

import os
import sys
import json
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

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
def reset_permission_checker_module():
    """
    Reset permission_checker module state between tests.
    在测试之间重置 permission_checker 模块状态。

    Ensures test independence by clearing module cache.
    通过清除模块缓存来确保测试独立性。
    """
    yield
    # Clear module cache after test
    # 测试后清除模块缓存
    if "app.core.permission_checker" in sys.modules:
        del sys.modules["app.core.permission_checker"]


# =============================================================================
# Mock Fixtures | 模拟 Fixtures
# =============================================================================

@pytest.fixture
def mock_admin_client():
    """
    Provide AsyncOpenSearch admin client mock.
    提供 AsyncOpenSearch 管理员客户端模拟。

    Returns:
        MagicMock: Mocked AsyncOpenSearch client
    """
    client = MagicMock()
    client.transport = MagicMock()
    client.transport.perform_request = AsyncMock()
    return client


@pytest.fixture
def mock_user_info():
    """
    Provide standard user info mock.
    提供标准用户信息模拟。

    Returns:
        Dict: User information dictionary
    """
    return {
        "backend_roles": ["user_role"],
        "opensearch_security_roles": ["reader"],
        "attributes": {"department": "engineering"}
    }


@pytest.fixture
def mock_role_permissions():
    """
    Provide standard role permissions mock.
    提供标准角色权限模拟。

    Returns:
        Dict: Role permissions dictionary
    """
    return {
        "index_permissions": [
            {
                "index_patterns": ["logs-*", "metrics-*"],
                "allowed_actions": ["read", "write"]
            }
        ],
        "cluster_permissions": ["cluster:monitor/*"]
    }


@pytest.fixture
def mock_admin_role_permissions():
    """
    Provide admin role permissions mock.
    提供管理员角色权限模拟。

    Returns:
        Dict: Admin role permissions dictionary
    """
    return {
        "index_permissions": [
            {
                "index_patterns": ["*"],
                "allowed_actions": ["*"]
            }
        ],
        "cluster_permissions": ["*"]
    }


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
            hasattr(item, '_evalxfail') and item._evalxfail.wasvalid() if hasattr(item, '_evalxfail') else False
        )

        result = {
            "nodeid": item.nodeid,
            "outcome": rep.outcome,
            "duration": rep.duration,
            "longrepr": str(rep.longrepr) if rep.longrepr else "",
            "is_xfail": is_xfail
        }
        _test_results.append(result)


def _get_readable_name(test_name: str) -> str:
    """
    Convert test method name to readable Chinese name.
    将测试方法名转换为可读的中文名称。

    Args:
        test_name: Test method name

    Returns:
        str: Readable test name in Chinese
    """
    # Test ID to readable name mapping
    # 测试 ID 到可读名称的映射
    name_map = {
        # Normal tests - 正常系测试
        "test_init_with_admin_client": "管理员客户端初始化",
        "test_get_user_info_success": "用户信息取得成功",
        "test_get_user_roles_success": "用户角色取得成功",
        "test_get_user_roles_deduplicate": "角色统合（重复除去）",
        "test_get_role_permissions_success": "角色权限取得成功",
        "test_index_access_granted": "索引访问权限许可",
        "test_index_access_denied": "索引访问权限拒绝",
        "test_wildcard_index_pattern_match": "通配符索引模式匹配",
        "test_expand_read_action": "汎用动作展开（read）",
        "test_expand_write_action": "汎用动作展开（write）",
        "test_expand_wildcard_action": "汎用动作展开（通配符）",
        "test_expand_crud_action": "多动作许可（crud）",
        "test_expand_manage_action": "汎用动作展开（manage）",
        "test_expand_index_action": "汎用动作展开（index）",
        "test_expand_delete_action": "汎用动作展开（delete）",
        "test_expand_indices_all_action": "汎用动作展开（indices_all）",
        "test_expand_create_index_action": "汎用动作展开（create_index）",
        "test_fnmatch_wildcard_pattern": "fnmatch通配符模式匹配",
        "test_no_match_action": "不匹配动作",
        "test_multiple_index_access_check": "多索引一括检查",
        "test_get_accessible_indices": "可访问索引取得",
        "test_check_user_index_access_function": "便利函数检查",

        # Error tests - 异常系测试
        "test_get_user_info_not_found": "不存在用户信息取得返回None",
        "test_get_user_info_api_error": "用户信息取得API错误",
        "test_get_roles_user_not_found": "不存在用户的角色取得",
        "test_get_permissions_role_not_found": "不存在角色的权限取得",
        "test_get_permissions_api_error": "角色权限取得API错误",
        "test_role_check_error_skip_continue": "角色检查错误时跳过继续",
        "test_all_roles_check_failed": "全角色检查失败",
        "test_user_roles_fetch_failed": "用户角色取得失败",
        "test_batch_check_partial_role_error": "批量检查中部分角色错误",
        "test_batch_check_user_error": "批量检查中用户取得失败",
        "test_accessible_indices_user_error": "可访问索引取得用户错误",
        "test_accessible_indices_partial_role_error": "部分角色错误时跳过继续",

        # Security tests - 安全测试
        "test_no_permission_user_denied": "无权限用户访问拒绝",
        "test_wildcard_pattern_safety": "通配符模式安全性",
        "test_minimum_privilege_principle": "最小权限原则验证",
        "test_injection_attack_resistance": "注入攻击耐性",
        "test_role_escalation_prevention": "角色提升攻击防止",
        "test_timing_attack_resistance": "时间攻击耐性",
    }

    # Extract test function name
    # 提取测试函数名
    if "::" in test_name:
        test_name = test_name.split("::")[-1]

    return name_map.get(test_name, test_name)


def pytest_sessionfinish(session, exitstatus):
    """
    Pytest hook to generate detailed reports after all tests complete.
    在所有测试完成后生成详细报告的 pytest 钩子。
    """
    report_dir = r"C:\pythonProject\python_ai_cspm\TestReport\permission_checker\reports"
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

        # Count outcomes
        # 统计结果
        if outcome == "passed":
            passed += 1
        elif outcome == "failed":
            failed += 1
        elif outcome == "xfailed":
            xfailed += 1

        # Parse test ID and categorize
        # 解析测试 ID 并分类
        if "test_permission_checker.py" in nodeid:
            test_name = nodeid.split("::")[-1] if "::" in nodeid else nodeid
            readable_name = _get_readable_name(test_name)

            test_entry = {
                "name": readable_name,
                "status": "✅ 通过" if outcome == "passed" else ("❌ 失败" if outcome == "failed" else "⚠️ 预期失败"),
                "duration": f"{duration*1000:.2f}ms"
            }

            # Categorize by test class
            # 按测试类分类
            if "Security" in nodeid:
                # Assign security test IDs
                # 分配安全测试 ID
                security_id_map = {
                    "test_no_permission_user_denied": "PERM-SEC-01",
                    "test_wildcard_pattern_safety": "PERM-SEC-02",
                    "test_minimum_privilege_principle": "PERM-SEC-05",
                    "test_injection_attack_resistance": "PERM-SEC-04",
                    "test_role_escalation_prevention": "PERM-SEC-03",
                    "test_timing_attack_resistance": "PERM-SEC-06",
                }
                test_entry["id"] = security_id_map.get(test_name, "PERM-SEC-XX")
                security_tests.append(test_entry)
            elif "Error" in nodeid:
                # Assign error test IDs
                # 分配异常系测试 ID
                error_id_map = {
                    "test_get_user_info_not_found": "PERM-E01",
                    "test_get_user_info_api_error": "PERM-E02",
                    "test_get_roles_user_not_found": "PERM-E03",
                    "test_get_permissions_role_not_found": "PERM-E04",
                    "test_get_permissions_api_error": "PERM-E05",
                    "test_role_check_error_skip_continue": "PERM-E06",
                    "test_all_roles_check_failed": "PERM-E07",
                    "test_user_roles_fetch_failed": "PERM-E09",
                    "test_batch_check_partial_role_error": "PERM-E08",
                    "test_batch_check_user_error": "PERM-E08-B",
                    "test_accessible_indices_user_error": "PERM-E10",
                    "test_accessible_indices_partial_role_error": "PERM-E10-B",
                }
                test_entry["id"] = error_id_map.get(test_name, "PERM-EXX")
                error_tests.append(test_entry)
            else:
                # Assign normal test IDs
                # 分配正常系测试 ID
                normal_id_map = {
                    "test_init_with_admin_client": "PERM-INIT",
                    "test_get_user_info_success": "PERM-001",
                    "test_get_user_roles_success": "PERM-002",
                    "test_get_user_roles_deduplicate": "PERM-012",
                    "test_get_role_permissions_success": "PERM-003",
                    "test_index_access_granted": "PERM-004",
                    "test_index_access_denied": "PERM-005",
                    "test_wildcard_index_pattern_match": "PERM-013",
                    "test_expand_read_action": "PERM-006",
                    "test_expand_write_action": "PERM-007",
                    "test_expand_wildcard_action": "PERM-008",
                    "test_expand_crud_action": "PERM-014",
                    "test_expand_manage_action": "PERM-006-B",
                    "test_expand_index_action": "PERM-006-C",
                    "test_expand_delete_action": "PERM-006-D",
                    "test_expand_indices_all_action": "PERM-006-E",
                    "test_expand_create_index_action": "PERM-006-F",
                    "test_fnmatch_wildcard_pattern": "PERM-006-G",
                    "test_no_match_action": "PERM-006-H",
                    "test_multiple_index_access_check": "PERM-009",
                    "test_get_accessible_indices": "PERM-010",
                    "test_check_user_index_access_function": "PERM-011",
                }
                test_entry["id"] = normal_id_map.get(test_name, "PERM-XXX")
                normal_tests.append(test_entry)

    # Calculate totals
    # 计算总数
    total = passed + failed + xfailed
    pass_rate = (passed / total * 100) if total > 0 else 0
    effective_pass_rate = (passed / (passed + failed) * 100) if (passed + failed) > 0 else 0

    # Generate Markdown report
    # 生成 Markdown 报告
    md_report = f"""# permission_checker.py 测试报告

## 测试概要

| 项目 | 值 |
|------|-----|
| 测试对象 | `app/core/permission_checker.py` |
| 测试规格 | `docs/testing/core/permission_checker_tests.md` |
| 执行时间 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
| 覆盖率目标 | 85% |

## 测试结果统计

| 类别 | 总数 | 通过 | 失败 | 预期失败 |
|------|------|------|------|----------|
| 正常系 | {len(normal_tests)} | {sum(1 for t in normal_tests if '✅' in t['status'])} | {sum(1 for t in normal_tests if '❌' in t['status'])} | {sum(1 for t in normal_tests if '⚠️' in t['status'])} |
| 异常系 | {len(error_tests)} | {sum(1 for t in error_tests if '✅' in t['status'])} | {sum(1 for t in error_tests if '❌' in t['status'])} | {sum(1 for t in error_tests if '⚠️' in t['status'])} |
| 安全测试 | {len(security_tests)} | {sum(1 for t in security_tests if '✅' in t['status'])} | {sum(1 for t in security_tests if '❌' in t['status'])} | {sum(1 for t in security_tests if '⚠️' in t['status'])} |
| **合计** | **{total}** | **{passed}** | **{failed}** | **{xfailed}** |

## 测试通过率

- **实际通过率**: {pass_rate:.1f}%
- **有效通过率** (排除预期失败): {effective_pass_rate:.1f}%

---

## 正常系测试详情

| ID | 测试名称 | 结果 | 执行时间 |
|----|---------|------|----------|
"""

    for test in normal_tests:
        md_report += f"| {test['id']} | {test['name']} | {test['status']} | {test['duration']} |\n"

    md_report += f"""
## 异常系测试详情

| ID | 测试名称 | 结果 | 执行时间 |
|----|---------|------|----------|
"""

    for test in error_tests:
        md_report += f"| {test['id']} | {test['name']} | {test['status']} | {test['duration']} |\n"

    md_report += f"""
## 安全测试详情

| ID | 测试名称 | 结果 | 执行时间 |
|----|---------|------|----------|
"""

    for test in security_tests:
        md_report += f"| {test['id']} | {test['name']} | {test['status']} | {test['duration']} |\n"

    md_report += f"""
---

## 结论

"""

    if failed == 0:
        md_report += "✅ **所有测试通过** - permission_checker 模块功能正常\n"
    else:
        md_report += f"⚠️ **存在 {failed} 个失败测试** - 需要进一步检查\n"

    if xfailed > 0:
        md_report += f"\n📝 **{xfailed} 个预期失败测试** - 这些是已知的限制或待实现功能\n"

    md_report += f"""
---

*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    # Write Markdown report
    # 写入 Markdown 报告
    md_path = os.path.join(report_dir, "TestReport_permission_checker.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_report)

    print(f"\n✅ Markdown 报告已生成: {md_path}")

    # Generate JSON report
    # 生成 JSON 报告
    json_report = {
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "xfailed": xfailed,
            "pass_rate": f"{pass_rate:.1f}%",
            "effective_pass_rate": f"{effective_pass_rate:.1f}%"
        },
        "categories": {
            "normal": {
                "total": len(normal_tests),
                "results": normal_tests
            },
            "error": {
                "total": len(error_tests),
                "results": error_tests
            },
            "security": {
                "total": len(security_tests),
                "results": security_tests
            }
        },
        "execution_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # Write JSON report
    # 写入 JSON 报告
    json_path = os.path.join(report_dir, "TestReport_permission_checker.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_report, f, ensure_ascii=False, indent=2)

    print(f"✅ JSON 报告已生成: {json_path}\n")
