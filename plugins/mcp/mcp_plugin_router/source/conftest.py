"""
MCP Plugin Router 测试配置

测试规格: docs/testing/plugins/mcp/mcp_plugin_router_tests.md
覆盖率目标: 80%+

测试类别:
  - 正常系: 13 个测试
  - 异常系: 22 个测试
  - 安全测试: 8 个测试
"""

import pytest
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# 项目根目录
# 从 TestReport/plugins/mcp/mcp_plugin_router/source 到项目根目录
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "platform_python_backend-testing"
if not project_root.exists():
    raise RuntimeError(f"项目根目录不存在: {project_root}")
sys.path.insert(0, str(project_root))

# 测试结果收集器
class TestResultCollector:
    """收集测试结果用于生成报告"""

    def __init__(self):
        self.results = {
            "normal": [],
            "error": [],
            "security": []
        }
        self.start_time = datetime.now()

    def add_result(self, nodeid: str, outcome: str, duration: float):
        """添加测试结果"""
        test_name = nodeid.split("::")[-1]

        # 分类规则
        if "Security" in nodeid or "_sec_" in test_name.lower():
            category = "security"
        elif "Error" in nodeid or "_error_" in test_name.lower() or "test_chat_missing" in test_name or "test_auth_" in test_name:
            category = "error"
        else:
            category = "normal"

        self.results[category].append({
            "test_id": test_name,
            "outcome": outcome,
            "duration": duration
        })

    def generate_markdown_report(self, output_path: Path):
        """生成 Markdown 测试报告"""
        total = sum(len(v) for v in self.results.values())
        passed = sum(1 for cat in self.results.values() for r in cat if r["outcome"] == "passed")
        failed = sum(1 for cat in self.results.values() for r in cat if r["outcome"] == "failed")

        # 安全计算通过率
        if total > 0:
            pass_rate_str = f"{passed / total * 100:.1f}% ({passed}/{total})"
        else:
            pass_rate_str = "N/A (0/0)"

        report = f"""# MCP Plugin Router 测试报告

## 测试概要

| 项目 | 值 |
|------|-----|
| 测试对象 | `app/mcp_plugin/router.py` |
| 测试规格 | `docs/testing/plugins/mcp/mcp_plugin_router_tests.md` |
| 执行时间 | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} |
| 覆盖率目标 | 80% |

## 测试结果统计

| 类别 | 总数 | 通过 | 失败 |
|------|------|------|------|
| 正常系 | {len(self.results['normal'])} | {sum(1 for r in self.results['normal'] if r['outcome'] == 'passed')} | {sum(1 for r in self.results['normal'] if r['outcome'] == 'failed')} |
| 异常系 | {len(self.results['error'])} | {sum(1 for r in self.results['error'] if r['outcome'] == 'passed')} | {sum(1 for r in self.results['error'] if r['outcome'] == 'failed')} |
| 安全测试 | {len(self.results['security'])} | {sum(1 for r in self.results['security'] if r['outcome'] == 'passed')} | {sum(1 for r in self.results['security'] if r['outcome'] == 'failed')} |
| **合计** | **{total}** | **{passed}** | **{failed}** |

## 测试通过率

- **通过率**: {pass_rate_str}

---

## 正常系测试详情

| 测试名称 | 结果 | 执行时间 |
|---------|------|----------|
"""
        for r in self.results["normal"]:
            status = "✅" if r["outcome"] == "passed" else "❌"
            report += f"| {r['test_id']} | {status} | {r['duration']:.3f}s |\n"

        report += "\n## 异常系测试详情\n\n| 测试名称 | 结果 | 执行时间 |\n|---------|------|----------|\n"
        for r in self.results["error"]:
            status = "✅" if r["outcome"] == "passed" else "❌"
            report += f"| {r['test_id']} | {status} | {r['duration']:.3f}s |\n"

        report += "\n## 安全测试详情\n\n| 测试名称 | 结果 | 执行时间 |\n|---------|------|----------|\n"
        for r in self.results["security"]:
            status = "✅" if r["outcome"] == "passed" else "❌"
            report += f"| {r['test_id']} | {status} | {r['duration']:.3f}s |\n"

        report += f"\n---\n\n*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"

        output_path.write_text(report, encoding="utf-8")

    def generate_json_report(self, output_path: Path):
        """生成 JSON 测试报告"""
        total = sum(len(v) for v in self.results.values())
        passed = sum(1 for cat in self.results.values() for r in cat if r["outcome"] == "passed")

        # 安全计算通过率
        pass_rate = f"{passed / total * 100:.1f}%" if total > 0 else "N/A"

        report = {
            "summary": {
                "total": total,
                "passed": passed,
                "failed": total - passed,
                "pass_rate": pass_rate
            },
            "categories": self.results,
            "execution_time": datetime.now().isoformat()
        }

        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


# Pytest 配置
@pytest.fixture(scope="session")
def test_collector():
    """测试结果收集器"""
    return TestResultCollector()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """捕获每个测试的结果"""
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call":
        collector = item.session.config._test_collector
        collector.add_result(
            nodeid=item.nodeid,
            outcome=rep.outcome,
            duration=rep.duration
        )


def pytest_sessionstart(session):
    """测试会话开始"""
    session.config._test_collector = TestResultCollector()


def pytest_sessionfinish(session, exitstatus):
    """测试会话结束，生成报告"""
    collector = session.config._test_collector

    # 生成报告
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    collector.generate_markdown_report(reports_dir / "TestReport_mcp_plugin_router.md")
    collector.generate_json_report(reports_dir / "TestReport_mcp_plugin_router.json")

