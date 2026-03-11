"""
config.py 测试配置文件

pytest配置和钩子函数,用于:
  - 设置测试环境
  - 收集测试结果
  - 生成测试报告(Markdown + JSON)
"""

import pytest
import json
import sys
from pathlib import Path
from datetime import datetime

# 项目根目录(固定路径)
project_root = Path(__file__).parent.parent.parent.parent / "platform_python_backend-testing"
sys.path.insert(0, str(project_root))


class TestResultCollector:
    """收集测试结果用于生成报告"""

    def __init__(self):
        self.results = {
            "normal": [],    # 正常系测试
            "error": [],     # 异常系测试
            "security": []   # 安全测试(如有)
        }
        self.start_time = datetime.now()

    def add_result(self, nodeid: str, outcome: str, duration: float):
        """添加测试结果

        分类规则:
        - 包含 "Security" → security
        - 包含 "Error" 或 "_e0" → error
        - 其他 → normal
        """
        test_name = nodeid.split("::")[-1]
        class_name = nodeid.split("::")[-2] if "::" in nodeid else ""

        result = {
            "id": self._extract_test_id(test_name),
            "name": self._get_readable_name(test_name),
            "outcome": outcome,
            "duration": f"{duration:.3f}s"
        }

        # 分类
        if "Security" in class_name:
            self.results["security"].append(result)
        elif "Error" in class_name or "_e0" in test_name:
            self.results["error"].append(result)
        else:
            self.results["normal"].append(result)

    def _extract_test_id(self, test_name: str) -> str:
        """从测试方法名提取测试ID"""
        # 尝试从docstring或测试名称提取ID
        if "cfg_" in test_name.lower():
            parts = test_name.split("_")
            for i, part in enumerate(parts):
                if part.lower() == "cfg" and i + 1 < len(parts):
                    return f"CFG-{parts[i+1].upper()}"
        return test_name

    def _get_readable_name(self, test_name: str) -> str:
        """将测试方法名转换为可读名称"""
        name_map = {
            # 正常系测试
            "test_load_from_env": "环境变量から設定読み込み",
            "test_default_values": "デフォルト値の適用",
            "test_opensearch_url_generation": "OpenSearch URL生成",
            "test_aws_opensearch_url": "AWS OpenSearch判定",
            "test_min_interval_calculation": "MIN_INTERVAL_SECONDS計算",
            "test_settings_instance_exists": "設定インスタンス存在確認",

            # 異常系测试
            "test_missing_required_fields": "必須設定の欠落",
            "test_invalid_port_type": "無効な型",
            "test_invalid_opensearch_url": "無効なOpenSearch URL",

            # AWS判定测试
            "test_is_aws_opensearch_service": "AWS OpenSearch Service判定",
        }
        return name_map.get(test_name, test_name.replace("_", " ").title())

    def generate_reports(self):
        """生成Markdown和JSON报告"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        # 统计
        total = sum(len(results) for results in self.results.values())
        passed = sum(1 for cat in self.results.values() for r in cat if r["outcome"] == "passed")
        failed = sum(1 for cat in self.results.values() for r in cat if r["outcome"] == "failed")
        xfailed = sum(1 for cat in self.results.values() for r in cat if r["outcome"] == "xfailed")

        pass_rate = (passed / total * 100) if total > 0 else 0
        effective_pass_rate = (passed / (total - xfailed) * 100) if (total - xfailed) > 0 else 0

        # 生成Markdown报告
        self._generate_markdown_report(total, passed, failed, xfailed, pass_rate, effective_pass_rate, end_time)

        # 生成JSON报告
        self._generate_json_report(total, passed, failed, xfailed, pass_rate, effective_pass_rate, end_time)

    def _generate_markdown_report(self, total, passed, failed, xfailed, pass_rate, effective_pass_rate, end_time):
        """生成Markdown格式的测试报告"""
        report_path = Path(__file__).parent.parent / "reports" / "TestReport_config.md"

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# config.py 测试报告\n\n")

            # 测试概要
            f.write("## 测试概要\n\n")
            f.write("| 项目 | 值 |\n")
            f.write("|------|-----|\n")
            f.write("| 测试对象 | `app/core/config.py` |\n")
            f.write("| 测试规格 | `config_tests.md` |\n")
            f.write(f"| 执行时间 | {end_time.strftime('%Y-%m-%d %H:%M:%S')} |\n")
            f.write("| 覆盖率目标 | 85% |\n\n")

            # 测试结果统计
            f.write("## 测试结果统计\n\n")
            f.write("| 类别 | 总数 | 通过 | 失败 | 预期失败 |\n")
            f.write("|------|------|------|------|----------|\n")

            normal_count = len(self.results["normal"])
            normal_passed = sum(1 for r in self.results["normal"] if r["outcome"] == "passed")
            normal_failed = sum(1 for r in self.results["normal"] if r["outcome"] == "failed")
            normal_xfailed = sum(1 for r in self.results["normal"] if r["outcome"] == "xfailed")

            error_count = len(self.results["error"])
            error_passed = sum(1 for r in self.results["error"] if r["outcome"] == "passed")
            error_failed = sum(1 for r in self.results["error"] if r["outcome"] == "failed")
            error_xfailed = sum(1 for r in self.results["error"] if r["outcome"] == "xfailed")

            security_count = len(self.results["security"])
            security_passed = sum(1 for r in self.results["security"] if r["outcome"] == "passed")
            security_failed = sum(1 for r in self.results["security"] if r["outcome"] == "failed")
            security_xfailed = sum(1 for r in self.results["security"] if r["outcome"] == "xfailed")

            f.write(f"| 正常系 | {normal_count} | {normal_passed} | {normal_failed} | {normal_xfailed} |\n")
            f.write(f"| 异常系 | {error_count} | {error_passed} | {error_failed} | {error_xfailed} |\n")
            f.write(f"| 安全测试 | {security_count} | {security_passed} | {security_failed} | {security_xfailed} |\n")
            f.write(f"| **合计** | **{total}** | **{passed}** | **{failed}** | **{xfailed}** |\n\n")

            # 测试通过率
            f.write("## 测试通过率\n\n")
            f.write(f"- **实际通过率**: {pass_rate:.1f}%\n")
            f.write(f"- **有效通过率** (排除预期失败): {effective_pass_rate:.1f}%\n\n")

            f.write("---\n\n")

            # 正常系测试详情
            if self.results["normal"]:
                f.write("## 正常系测试详情\n\n")
                f.write("| ID | 测试名称 | 结果 | 执行时间 |\n")
                f.write("|----|---------|------|----------|\n")
                for r in self.results["normal"]:
                    status = "✅" if r["outcome"] == "passed" else "❌" if r["outcome"] == "failed" else "⚠️"
                    f.write(f"| {r['id']} | {r['name']} | {status} | {r['duration']} |\n")
                f.write("\n")

            # 异常系测试详情
            if self.results["error"]:
                f.write("## 异常系测试详情\n\n")
                f.write("| ID | 测试名称 | 结果 | 执行时间 |\n")
                f.write("|----|---------|------|----------|\n")
                for r in self.results["error"]:
                    status = "✅" if r["outcome"] == "passed" else "❌" if r["outcome"] == "failed" else "⚠️"
                    f.write(f"| {r['id']} | {r['name']} | {status} | {r['duration']} |\n")
                f.write("\n")

            # 安全测试详情
            if self.results["security"]:
                f.write("## 安全测试详情\n\n")
                f.write("| ID | 测试名称 | 结果 | 执行时间 |\n")
                f.write("|----|---------|------|----------|\n")
                for r in self.results["security"]:
                    status = "✅" if r["outcome"] == "passed" else "❌" if r["outcome"] == "failed" else "⚠️"
                    f.write(f"| {r['id']} | {r['name']} | {status} | {r['duration']} |\n")
                f.write("\n")

            f.write("---\n\n")

            # 结论
            f.write("## 结论\n\n")
            if failed == 0:
                f.write("✅ **所有测试通过!** config.py模块功能正常。\n\n")
            else:
                f.write(f"❌ **有{failed}个测试失败**, 请检查详细信息并修复问题。\n\n")

            f.write("---\n\n")
            f.write(f"*报告生成时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}*\n")

        print(f"✅ Markdown报告已生成: {report_path}")

    def _generate_json_report(self, total, passed, failed, xfailed, pass_rate, effective_pass_rate, end_time):
        """生成JSON格式的测试报告"""
        report_path = Path(__file__).parent.parent / "reports" / "TestReport_config.json"

        report_data = {
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "xfailed": xfailed,
                "pass_rate": f"{pass_rate:.1f}%",
                "effective_pass_rate": f"{effective_pass_rate:.1f}%"
            },
            "categories": self.results,
            "execution_time": end_time.strftime("%Y-%m-%d %H:%M:%S")
        }

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON报告已生成: {report_path}")


# 全局收集器实例
collector = TestResultCollector()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """捕获每个测试的结果"""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        collector.add_result(
            nodeid=item.nodeid,
            outcome=report.outcome,
            duration=report.duration
        )


def pytest_sessionfinish(session, exitstatus):
    """测试会话结束时生成报告"""
    collector.generate_reports()
    print("\n✅ 测试报告已生成:")
    print("  - C:\\pythonProject\\python_ai_cspm\\TestReport\\config\\reports\\TestReport_config.md")
    print("  - C:\\pythonProject\\python_ai_cspm\\TestReport\\config\\reports\\TestReport_config.json")
