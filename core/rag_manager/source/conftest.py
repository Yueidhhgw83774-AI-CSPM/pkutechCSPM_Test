# -*- coding: utf-8 -*-
"""
pytest fixtures for rag_manager module tests.
rag_manager 模块测试的 pytest fixtures。

This module provides shared fixtures for testing the rag_manager module,
including environment setup, mock objects, and test result collection.
本模块提供用于测试 rag_manager 模块的共享 fixtures，
包括环境设置、模拟对象和测试结果收集。
"""

import os
import sys
import json
import pytest
from datetime import datetime
from pathlib import Path
from typing import Generator
from unittest.mock import patch, MagicMock, AsyncMock

# Add the project root to Python path for imports
# 将项目根目录添加到 Python 路径以便导入
PROJECT_ROOT = r"C:\pythonProject\python_ai_cspm\platform_python_backend-testing"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# =============================================================================
# Module Reset Fixture | 模块重置 Fixture
# =============================================================================

@pytest.fixture(autouse=True)
def reset_rag_manager_module():
    """
    Reset rag_manager module global state between tests.
    在测试之间重置 rag_manager 模块的全局状态。

    rag_manager.py uses singleton pattern and global variables,
    so we need to reset them between tests to ensure test independence.
    rag_manager.py 使用单例模式和全局变量，
    因此需要在测试之间重置它们以确保测试独立性。
    """
    # Clear module cache before test | 测试前清除模块缓存
    modules_to_remove = [
        key for key in list(sys.modules.keys())
        if key.startswith("app.core.rag_manager") or key.startswith("app.rag")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]

    yield

    # Cleanup after test | 测试后清理
    try:
        import app.core.rag_manager as rag_module
        # Reset global variables | 重置全局变量
        rag_module._global_rag_manager = None
        # Reset class variables | 重置类变量
        rag_module.RAGManager._instance = None
    except (ImportError, AttributeError):
        pass

    # Clear module cache again | 再次清除模块缓存
    modules_to_remove = [
        key for key in list(sys.modules.keys())
        if key.startswith("app.core.rag_manager") or key.startswith("app.rag")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


# =============================================================================
# Mock Fixtures | 模拟对象 Fixtures
# =============================================================================

@pytest.fixture
def mock_enhanced_rag_search():
    """
    Provide a mock EnhancedRAGSearch object.
    提供模拟的 EnhancedRAGSearch 对象。

    This prevents external dependencies during testing.
    这可以防止测试期间的外部依赖。
    """
    mock_rag = MagicMock()
    mock_rag.initialize = AsyncMock(return_value=True)
    mock_rag.get_health = AsyncMock(return_value={"status": "healthy"})
    return mock_rag


# =============================================================================
# Test Result Collection | 测试结果收集
# =============================================================================

# Global test results storage | 全局测试结果存储
_test_results = []


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to capture test results.
    捕获测试结果的钩子。

    This hook captures the result of each test (passed, failed, xfailed)
    and stores it for report generation.
    此钩子捕获每个测试的结果（通过、失败、预期失败）并存储以生成报告。
    """
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call":
        # Check if test is marked as xfail | 检查测试是否标记为 xfail
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
    Generate detailed reports after all tests complete.
    在所有测试完成后生成详细报告。

    This function is called by pytest after all tests have run.
    It generates both Markdown and JSON reports.
    pytest 在所有测试运行后调用此函数。
    它会生成 Markdown 和 JSON 两种格式的报告。
    """
    report_dir = r"C:\pythonProject\python_ai_cspm\TestReport\rag_manager\reports"
    os.makedirs(report_dir, exist_ok=True)

    # Parse test results | 解析测试结果
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

        # Override outcome for xfail tests | 覆盖 xfail 测试的结果
        if is_xfail:
            outcome = "xfailed"

        # Categorize tests | 分类测试
        test_info = _parse_test_info(nodeid, outcome, duration)

        if "Security" in nodeid:
            security_tests.append(test_info)
        elif "Error" in nodeid:
            error_tests.append(test_info)
        else:
            normal_tests.append(test_info)

        # Count results | 统计结果
        if outcome == "passed":
            passed += 1
        elif outcome == "xfailed":
            xfailed += 1
        else:
            failed += 1

    # Generate reports | 生成报告
    _generate_markdown_report(report_dir, normal_tests, error_tests, security_tests, passed, failed, xfailed)
    _generate_json_report(report_dir, normal_tests, error_tests, security_tests, passed, failed, xfailed)


def _parse_test_info(nodeid: str, outcome: str, duration: float) -> dict:
    """
    Parse test information from nodeid.
    从 nodeid 解析测试信息。
    """
    # Extract test ID and name | 提取测试 ID 和名称
    test_id, test_name = _get_test_id_and_name(nodeid)

    # Format status emoji | 格式化状态表情
    if outcome == "passed":
        status = "✅ 通过"
    elif outcome == "xfailed":
        status = "⚠️ 预期失败"
    else:
        status = "❌ 失败"

    return {
        "id": test_id,
        "name": test_name,
        "status": status,
        "outcome": outcome,
        "duration": f"{duration*1000:.2f}ms"
    }


def _get_test_id_and_name(nodeid: str) -> tuple:
    """
    Get test ID and readable name from nodeid.
    从 nodeid 获取测试 ID 和可读名称。
    """
    # Test ID to name mapping | 测试 ID 到名称的映射
    name_map = {
        "test_import_rag_manager_module": ("RAG-001", "モジュールインポート成功"),
        "test_get_instance_returns_rag_manager": ("RAG-002", "シングルトンインスタンス取得"),
        "test_get_instance_returns_same_instance": ("RAG-003", "シングルトン一貫性"),
        "test_initialize_success": ("RAG-004", "初期化成功"),
        "test_initialize_already_initialized_returns_true": ("RAG-005", "初期化済みで再度initialize"),
        "test_initialize_double_checked_locking": ("RAG-006", "double-checked locking動作確認"),
        "test_get_enhanced_rag_search_success": ("RAG-007", "get_enhanced_rag_search成功"),
        "test_get_enhanced_rag_search_auto_initialize": ("RAG-008", "get_enhanced_rag_search自動初期化"),
        "test_is_initialized_false_initially": ("RAG-009", "is_initialized確認（未初期化）"),
        "test_is_initialized_true_after_init": ("RAG-010", "is_initialized確認（初期化済み）"),
        "test_health_check_success": ("RAG-011", "ヘルスチェック成功"),
        "test_get_global_rag_manager": ("RAG-012", "グローバルマネージャー取得"),
        "test_initialize_global_rag_system_success": ("RAG-013", "グローバルシステム初期化成功"),
        "test_module_level_get_enhanced_rag_search": ("RAG-014", "DI用get_enhanced_rag_search成功"),
        "test_initialize_rag_returns_false": ("RAG-E01", "EnhancedRAGSearch初期化失敗"),
        "test_initialize_exception": ("RAG-E02", "初期化中の例外"),
        "test_get_enhanced_rag_search_init_failure": ("RAG-E03", "get_enhanced_rag_search初期化失敗"),
        "test_health_check_uninitialized": ("RAG-E04", "ヘルスチェック未初期化"),
        "test_health_check_no_rag_search": ("RAG-E05", "ヘルスチェックRAG無し"),
        "test_health_check_exception": ("RAG-E06", "ヘルスチェック例外"),
        "test_initialize_global_rag_system_exception": ("RAG-E07", "グローバル初期化例外"),
        "test_error_log_no_sensitive_info": ("RAG-SEC-01", "エラーログに機密情報が含まれない"),
        "test_health_check_no_stack_trace_leak": ("RAG-SEC-02", "ヘルスチェックに内部エラー詳細が漏洩しない"),
        "test_singleton_thread_safety": ("RAG-SEC-03", "シングルトンのスレッドセーフ性"),
    }

    # Extract test method name | 提取测试方法名
    for method_name, (test_id, test_name) in name_map.items():
        if method_name in nodeid:
            return test_id, test_name

    return "UNKNOWN", nodeid.split("::")[-1]


def _generate_markdown_report(report_dir: str, normal_tests: list, error_tests: list,
                              security_tests: list, passed: int, failed: int, xfailed: int):
    """
    Generate Markdown format test report.
    生成 Markdown 格式测试报告。
    """
    total = passed + failed + xfailed
    pass_rate = (passed / total * 100) if total > 0 else 0
    effective_pass_rate = (passed / (passed + failed) * 100) if (passed + failed) > 0 else 0

    md_content = f"""# rag_manager.py 测试报告

## 测试概要

| 项目 | 值 |
|------|-----|
| 测试对象 | `app/core/rag_manager.py` |
| 测试规格 | `docs/testing/core/rag_manager_tests.md` |
| 执行时间 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
| 覆盖率目标 | 75% |

## 测试结果统计

| 类别 | 总数 | 通过 | 失败 | 预期失败 |
|------|------|------|------|----------|
| 正常系 | {len(normal_tests)} | {sum(1 for t in normal_tests if t['outcome']=='passed')} | {sum(1 for t in normal_tests if t['outcome']=='failed')} | {sum(1 for t in normal_tests if t['outcome']=='xfailed')} |
| 异常系 | {len(error_tests)} | {sum(1 for t in error_tests if t['outcome']=='passed')} | {sum(1 for t in error_tests if t['outcome']=='failed')} | {sum(1 for t in error_tests if t['outcome']=='xfailed')} |
| 安全测试 | {len(security_tests)} | {sum(1 for t in security_tests if t['outcome']=='passed')} | {sum(1 for t in security_tests if t['outcome']=='failed')} | {sum(1 for t in security_tests if t['outcome']=='xfailed')} |
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
        md_content += f"| {test['id']} | {test['name']} | {test['status']} | {test['duration']} |\n"

    md_content += "\n## 异常系测试详情\n\n"
    md_content += "| ID | 测试名称 | 结果 | 执行时间 |\n"
    md_content += "|----|---------|------|----------|\n"

    for test in error_tests:
        md_content += f"| {test['id']} | {test['name']} | {test['status']} | {test['duration']} |\n"

    md_content += "\n## 安全测试详情\n\n"
    md_content += "| ID | 测试名称 | 结果 | 执行时间 |\n"
    md_content += "|----|---------|------|----------|\n"

    for test in security_tests:
        md_content += f"| {test['id']} | {test['name']} | {test['status']} | {test['duration']} |\n"

    md_content += "\n---\n\n## 结论\n\n"

    if failed == 0:
        md_content += "✅ **所有测试通过！** RAGマネージャーモジュールは期待通りに動作しています。\n"
    else:
        md_content += f"⚠️ **{failed}個のテストが失敗しました。** 詳細を確認して修正してください。\n"

    if xfailed > 0:
        md_content += f"\n📌 **{xfailed}個のテストは予期された失敗です** (実装側の修正が必要)。\n"

    md_content += "\n---\n\n"
    md_content += f"*報告生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"

    # Write to file | 写入文件
    report_path = os.path.join(report_dir, "TestReport_rag_manager.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md_content)


def _generate_json_report(report_dir: str, normal_tests: list, error_tests: list,
                         security_tests: list, passed: int, failed: int, xfailed: int):
    """
    Generate JSON format test report.
    生成 JSON 格式测试报告。
    """
    total = passed + failed + xfailed
    pass_rate = (passed / total * 100) if total > 0 else 0
    effective_pass_rate = (passed / (passed + failed) * 100) if (passed + failed) > 0 else 0

    json_data = {
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

    # Write to file | 写入文件
    report_path = os.path.join(report_dir, "TestReport_rag_manager.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
