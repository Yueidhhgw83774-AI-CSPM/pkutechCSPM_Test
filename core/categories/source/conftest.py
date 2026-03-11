# -*- coding: utf-8 -*-
"""
pytest fixtures for categories module tests.
categories 模块测试的 pytest fixtures。

This module provides shared fixtures and test result collection for testing categories module.
本模块提供用于测试 categories 模块的共享 fixtures 和测试结果收集。
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

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
def reset_categories_module():
    """
    Reset categories module state between tests.
    在测试之间重置 categories 模块状态。

    categories.py 使用全局变量缓存数据，需要在测试间重置以确保独立性。
    """
    # 测试前清除模块缓存
    modules_to_remove = [
        key for key in list(sys.modules.keys())
        if key.startswith("app.core.categories")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]

    yield

    # 测试后清理
    try:
        import app.core.categories as cat_module
        cat_module._categories_data = []
        cat_module._categories_for_prompt_str = ""
    except ImportError:
        pass

    # 再次清除模块缓存
    modules_to_remove = [
        key for key in list(sys.modules.keys())
        if key.startswith("app.core.categories")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


# =============================================================================
# Test Data Fixtures | 测试数据 Fixtures
# =============================================================================

@pytest.fixture
def valid_categories_json(tmp_path):
    """
    Create a valid categories JSON file for testing.
    创建有效的测试用 categories JSON 文件。
    """
    categories = [
        {
            "name": "Identity and Access Management",
            "description": "IAM related controls"
        },
        {
            "name": "Data Security",
            "description": "Data protection controls"
        },
        {
            "name": "Network Security",
            "description": "Network related controls"
        }
    ]
    json_file = tmp_path / "categories.json"
    json_file.write_text(json.dumps(categories), encoding="utf-8")
    return str(json_file)


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
    report_dir = r"C:\pythonProject\python_ai_cspm\TestReport\categories\reports"
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
        if "test_categories.py" in nodeid:
            # Security tests
            # 安全测试
            if "TestCategoriesSecurity" in nodeid or "Security" in nodeid:
                if "path_traversal" in nodeid:
                    test_id, test_name = "CAT-SEC-01", "路径遍历攻击防护"
                elif "large_categories" in nodeid or "dos_resistance" in nodeid:
                    test_id, test_name = "CAT-SEC-02", "大量数据DoS防护"
                elif "malicious_json" in nodeid:
                    test_id, test_name = "CAT-SEC-03", "恶意JSON内容处理"
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
            elif "Error" in nodeid or "Errors" in nodeid:
                if "file_not_found" in nodeid:
                    test_id, test_name = "CAT-E01", "文件不存在处理"
                elif "invalid_json" in nodeid:
                    test_id, test_name = "CAT-E02", "无效JSON处理"
                elif "unexpected_exception" in nodeid:
                    test_id, test_name = "CAT-E03", "预期外异常处理"
                elif "permission_error" in nodeid:
                    test_id, test_name = "CAT-E04", "权限错误处理"
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
                if "import_categories_module" in nodeid:
                    test_id, test_name = "CAT-001", "模块导入"
                elif "load_valid_categories" in nodeid:
                    test_id, test_name = "CAT-002", "有效JSON读取"
                elif "prompt_string_format" in nodeid:
                    test_id, test_name = "CAT-003", "提示字符串格式"
                elif "auto_load_when_not_loaded" in nodeid:
                    test_id, test_name = "CAT-004", "未加载时自动加载"
                elif "cached_data_returned" in nodeid:
                    test_id, test_name = "CAT-005", "缓存数据返回"
                elif "empty_categories_list" in nodeid:
                    test_id, test_name = "CAT-006", "空列表回退"
                elif "category_without_description" in nodeid:
                    test_id, test_name = "CAT-007", "无描述处理"
                elif "category_without_name_skipped" in nodeid:
                    test_id, test_name = "CAT-008", "无名称跳过"
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
    report_md = f"""# categories.py 测试报告

## 测试概要

| 项目 | 值 |
|------|-----|
| 测试对象 | `app/core/categories.py` |
| 测试规格 | `categories_tests.md` |
| 执行时间 | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} |
| 覆盖率目标 | 60% |

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
    md_path = os.path.join(report_dir, "TestReport_categories.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    # Generate JSON report
    # 生成 JSON 报告
    json_report = {
        "metadata": {
            "test_target": "app/core/categories.py",
            "test_spec": "categories_tests.md",
            "execution_time": datetime.now().isoformat(),
            "coverage_target": "60%"
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

    json_path = os.path.join(report_dir, "TestReport_categories.json")
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
    report_path = r"C:\pythonProject\python_ai_cspm\TestReport\categories\reports"
    os.makedirs(report_path, exist_ok=True)
    return report_path
