# -*- coding: utf-8 -*-
"""
pytest fixtures for checkpointer module tests.
checkpointer 模块测试的 pytest fixtures。

This module provides shared fixtures and test result collection for testing checkpointer module.
本模块提供用于测试 checkpointer 模块的共享 fixtures 和测试结果收集。
"""

import os
import sys

# Set required environment variables BEFORE any imports to prevent config validation errors
# 在任何导入之前设置必需的环境变量以防止配置验证错误
# Using actual values from .env file for testing
os.environ.setdefault("GPT5_1_CHAT_API_KEY", "sk-h6zKpdRQoYKEcj6vhTHMPg")
os.environ.setdefault("GPT5_1_CODEX_API_KEY", "sk-h6zKpdRQoYKEcj6vhTHMPg")
os.environ.setdefault("GPT5_2_API_KEY", "sk-h6zKpdRQoYKEcj6vhTHMPg")
os.environ.setdefault("GPT5_MINI_API_KEY", "sk-EAt8QXSUBIdDJnXV4ROHrA")
os.environ.setdefault("GPT5_NANO_API_KEY", "sk-KbU6B0qXqUc2bru0rQ49vg")
os.environ.setdefault("CLAUDE_HAIKU_4_5_KEY", "sk-AZ2Y4zi06RkkiQ9IVnrw-g")
os.environ.setdefault("CLAUDE_SONNET_4_5_KEY", "sk-ddGysRLuQbS68TPNdBnZDQ")
os.environ.setdefault("GEMINI_API", "sk-6voS6352n0aLHWV3k_jFew")
os.environ.setdefault("DOCKER_BASE_URL", "http://litellm:4000")
os.environ.setdefault("EMBEDDING_3_LARGE_API_KEY", "sk-CVqmdwNwI9y0nHSVeDwwpA")
os.environ.setdefault("OPENSEARCH_URL", "https://opensearch-node:9200")
os.environ.setdefault("LANGGRAPH_STORAGE_TYPE", "memory")
os.environ.setdefault("LANGGRAPH_POSTGRES_URL", "")

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
def reset_checkpointer_module():
    """
    Reset checkpointer module state between tests.
    在测试之间重置 checkpointer 模块状态。

    checkpointer.py 使用全局变量缓存，需要在测试间重置以确保独立性。
    """
    # 测试前清除模块缓存
    modules_to_remove = [
        key for key in list(sys.modules.keys())
        if key.startswith("app.core.checkpointer")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]

    yield

    # 测试后重置全局变量
    try:
        import app.core.checkpointer as ckp_module
        ckp_module._checkpointer = None
        ckp_module._checkpointer_initialized = False
        ckp_module._connection_pool = None
        ckp_module._current_storage_mode = "unknown"
    except (ImportError, AttributeError):
        pass

    # 再次清除模块缓存
    modules_to_remove = [
        key for key in list(sys.modules.keys())
        if key.startswith("app.core.checkpointer")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


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
    report_dir = r"C:\pythonProject\python_ai_cspm\TestReport\checkpointer\reports"
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
        if "test_checkpointer.py" in nodeid:
            # Security tests
            # 安全测试
            if "TestCheckpointerSecurity" in nodeid or "Security" in nodeid:
                if "postgres_url_not_logged" in nodeid:
                    test_id, test_name = "CKP-SEC-01", "PostgreSQL URL不输出日志"
                elif "credentials_not_exposed" in nodeid:
                    test_id, test_name = "CKP-SEC-02", "认证信息不泄露"
                elif "connection_pool_max_size" in nodeid:
                    test_id, test_name = "CKP-SEC-03", "连接池大小限制"
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
                if "postgres_url_not_set" in nodeid:
                    test_id, test_name = "CKP-E01", "PostgreSQL URL未设置"
                elif "psycopg_not_installed" in nodeid:
                    test_id, test_name = "CKP-E02", "psycopg未安装"
                elif "postgres_connection_error" in nodeid:
                    test_id, test_name = "CKP-E03", "PostgreSQL连接错误"
                elif "close_pool_error" in nodeid:
                    test_id, test_name = "CKP-E04", "连接池关闭错误"
                elif "setup_fails" in nodeid:
                    test_id, test_name = "CKP-E05", "setup失败"
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
                if "import_checkpointer_module" in nodeid:
                    test_id, test_name = "CKP-INIT", "模块导入"
                elif "initial_storage_mode" in nodeid:
                    test_id, test_name = "CKP-001", "初始存储模式"
                elif "memory_saver_init_with_memory_type" in nodeid:
                    test_id, test_name = "CKP-002", "MemorySaver初始化(memory)"
                elif "memory_saver_fallback_unset" in nodeid:
                    test_id, test_name = "CKP-003", "MemorySaver回退(未设置)"
                elif "cached_checkpointer_returned" in nodeid:
                    test_id, test_name = "CKP-004", "缓存Checkpointer返回"
                elif "postgres_checkpointer_init" in nodeid:
                    test_id, test_name = "CKP-005", "PostgreSQL初始化"
                elif "sync_checkpointer_memory" in nodeid:
                    test_id, test_name = "CKP-006", "同步Checkpointer(memory)"
                elif "sync_checkpointer_postgres_warning" in nodeid:
                    test_id, test_name = "CKP-007", "同步Checkpointer(postgres警告)"
                elif "close_checkpointer_memory" in nodeid:
                    test_id, test_name = "CKP-008", "关闭Checkpointer(memory)"
                elif "reset_checkpointer_clears_cache" in nodeid:
                    test_id, test_name = "CKP-009", "重置缓存"
                elif "opensearch_fallback_to_memory" in nodeid:
                    test_id, test_name = "CKP-010", "OpenSearch回退"
                elif "unknown_storage_fallback" in nodeid:
                    test_id, test_name = "CKP-011", "未知存储回退"
                elif "close_with_postgres_pool" in nodeid:
                    test_id, test_name = "CKP-012", "关闭PostgreSQL连接池"
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
    report_md = f"""# checkpointer.py 测试报告

## 测试概要

| 项目 | 值 |
|------|-----|
| 测试对象 | `app/core/checkpointer.py` |
| 测试规格 | `checkpointer_tests.md` |
| 执行时间 | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} |
| 覆盖率目标 | 75% |

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
    md_path = os.path.join(report_dir, "TestReport_checkpointer.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    # Generate JSON report
    # 生成 JSON 报告
    json_report = {
        "metadata": {
            "test_target": "app/core/checkpointer.py",
            "test_spec": "checkpointer_tests.md",
            "execution_time": datetime.now().isoformat(),
            "coverage_target": "75%"
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

    json_path = os.path.join(report_dir, "TestReport_checkpointer.json")
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
    report_path = r"C:\pythonProject\python_ai_cspm\TestReport\checkpointer\reports"
    os.makedirs(report_path, exist_ok=True)
    return report_path
