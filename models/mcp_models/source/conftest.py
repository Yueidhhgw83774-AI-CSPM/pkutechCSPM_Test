"""
models/mcp.py 测试配置文件

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

# 加载环境变量
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# 项目根目录(固定路径)
project_root = Path(__file__).parent.parent.parent.parent.parent / "platform_python_backend-testing"
sys.path.insert(0, str(project_root))


class TestResultCollector:
    """收集测试结果用于生成报告"""

    def __init__(self):
        self.results = {
            "normal": [],    # 正常系测试
            "error": [],     # 异常系测试
            "security": []   # 安全测试
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
        class_name = nodeid.split("::")[-2] if len(nodeid.split("::")) > 2 else ""

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
        if "mcp_" in test_name.lower():
            parts = test_name.split("_")
            for i, part in enumerate(parts):
                if part.lower() == "mcp" and i + 1 < len(parts):
                    num = parts[i+1]
                    if num.isdigit():
                        return f"MCP-{num.zfill(3)}"
        return test_name

    def _get_readable_name(self, test_name: str) -> str:
        """将测试方法名转换为可读名称"""
        name_map = {
            # CloudCredentialsContext
            "test_cloud_credentials_context_aws": "CloudCredentialsContext AWS構成",
            "test_cloud_credentials_context_azure": "Azure構成",
            "test_cloud_credentials_context_gcp": "GCP構成",
            "test_cloud_credentials_context_minimal": "最小構成",

            # Enum
            "test_mcp_tool_type_enum": "MCPToolType Enum",
            "test_sse_event_type_enum": "SSEEventType Enum",

            # MCPTool
            "test_mcp_tool_basic": "MCPTool 基本構成",
            "test_mcp_tool_with_parameters": "パラメータ付き",
            "test_mcp_tool_parameter": "MCPToolParameter",

            # MCPServer
            "test_mcp_server_basic": "MCPServer 基本構成",
            "test_mcp_server_full": "完全構成",

            # MCPChatMessage
            "test_mcp_chat_message_basic": "MCPChatMessage 基本",
            "test_mcp_chat_message_with_tools": "ツール呼び出し付き",

            # SubTaskResult
            "test_sub_task_result_completed": "SubTaskResult 完了",
            "test_sub_task_result_failed": "失敗",

            # TodoItem
            "test_todo_item_pending": "TodoItem pending",
            "test_todo_item_completed": "completed",

            # MCPChatRequest/Response
            "test_mcp_chat_request": "MCPChatRequest",
            "test_mcp_chat_stream_request": "MCPChatStreamRequest",
            "test_mcp_chat_response_basic": "MCPChatResponse 基本",
            "test_mcp_chat_response_full": "完全構成",

            # SessionInfo
            "test_session_info": "SessionInfo",
            "test_session_list_response": "SessionListResponse",

            # 異常系
            "test_cloud_credentials_invalid_provider": "無効なクラウドプロバイダー",
            "test_mcp_chat_request_missing_required": "必須フィールド欠落",
            "test_validation_result_invalid": "無効なValidationResult",
        }
        return name_map.get(test_name, test_name.replace("_", " ").title())

    def generate_reports(self):
        """生成Markdown和JSON报告"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        # 统计
        total = sum(len(v) for v in self.results.values())
        passed = sum(1 for category in self.results.values()
                    for r in category if r["outcome"] == "passed")
        failed = sum(1 for category in self.results.values()
                    for r in category if r["outcome"] == "failed")
        xfailed = sum(1 for category in self.results.values()
                     for r in category if r["outcome"] == "xfailed")

        # 生成 Markdown 报告
        md_report = self._generate_markdown_report(total, passed, failed, xfailed, duration)

        # 生成 JSON 报告
        json_report = self._generate_json_report(total, passed, failed, xfailed)

        # 保存报告
        report_dir = Path(__file__).parent.parent / "reports"
        report_dir.mkdir(exist_ok=True)

        md_path = report_dir / "TestReport_mcp_models.md"
        json_path = report_dir / "TestReport_mcp_models.json"

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_report)

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, ensure_ascii=False, indent=2)

    def _generate_markdown_report(self, total, passed, failed, xfailed, duration):
        """生成 Markdown 格式报告"""
        pass_rate = (passed / total * 100) if total > 0 else 0
        effective_total = total - xfailed
        effective_pass_rate = (passed / effective_total * 100) if effective_total > 0 else 0

        report = f"""# models/mcp.py 测试报告

## 测试概要

| 项目 | 值 |
|------|-----|
| 测试对象 | `app/models/mcp.py` |
| 测试规格 | `docs/testing/models/mcp_models_tests.md` |
| 执行时间 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
| 总耗时 | {duration:.2f}s |
| 覆盖率目标 | 90% |

## 测试结果统计

| 类别 | 总数 | 通过 | 失败 | 预期失败 |
|------|------|------|------|----------|
| 正常系 | {len(self.results['normal'])} | {sum(1 for r in self.results['normal'] if r['outcome']=='passed')} | {sum(1 for r in self.results['normal'] if r['outcome']=='failed')} | {sum(1 for r in self.results['normal'] if r['outcome']=='xfailed')} |
| 异常系 | {len(self.results['error'])} | {sum(1 for r in self.results['error'] if r['outcome']=='passed')} | {sum(1 for r in self.results['error'] if r['outcome']=='failed')} | {sum(1 for r in self.results['error'] if r['outcome']=='xfailed')} |
| 安全测试 | {len(self.results['security'])} | {sum(1 for r in self.results['security'] if r['outcome']=='passed')} | {sum(1 for r in self.results['security'] if r['outcome']=='failed')} | {sum(1 for r in self.results['security'] if r['outcome']=='xfailed')} |
| **合计** | **{total}** | **{passed}** | **{failed}** | **{xfailed}** |

## 测试通过率

- **实际通过率**: {pass_rate:.1f}%
- **有效通过率** (排除预期失败): {effective_pass_rate:.1f}%

---

## 正常系测试详情

| ID | 测试名称 | 结果 | 执行时间 |
|----|---------|------|----------|
"""
        for r in self.results['normal']:
            status = "✅" if r['outcome'] == 'passed' else "❌" if r['outcome'] == 'failed' else "⏭️"
            report += f"| {r['id']} | {r['name']} | {status} | {r['duration']} |\n"

        report += "\n## 异常系测试详情\n\n"
        report += "| ID | 测试名称 | 结果 | 执行时间 |\n"
        report += "|----|---------|------|----------|\n"

        for r in self.results['error']:
            status = "✅" if r['outcome'] == 'passed' else "❌" if r['outcome'] == 'failed' else "⏭️"
            report += f"| {r['id']} | {r['name']} | {status} | {r['duration']} |\n"

        if self.results['security']:
            report += "\n## 安全测试详情\n\n"
            report += "| ID | 测试名称 | 结果 | 执行时间 |\n"
            report += "|----|---------|------|----------|\n"

            for r in self.results['security']:
                status = "✅" if r['outcome'] == 'passed' else "❌" if r['outcome'] == 'failed' else "⏭️"
                report += f"| {r['id']} | {r['name']} | {status} | {r['duration']} |\n"

        report += f"""

---

## 结论

{"✅ 所有测试通过！" if failed == 0 else f"❌ {failed} 个测试失败"}

---

*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return report

    def _generate_json_report(self, total, passed, failed, xfailed):
        """生成 JSON 格式报告"""
        pass_rate = (passed / total * 100) if total > 0 else 0
        effective_total = total - xfailed
        effective_pass_rate = (passed / effective_total * 100) if effective_total > 0 else 0

        return {
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "xfailed": xfailed,
                "pass_rate": f"{pass_rate:.1f}%",
                "effective_pass_rate": f"{effective_pass_rate:.1f}%"
            },
            "categories": {
                "normal": {"results": self.results["normal"]},
                "error": {"results": self.results["error"]},
                "security": {"results": self.results["security"]}
            },
            "execution_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }


# Pytest 钩子
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

