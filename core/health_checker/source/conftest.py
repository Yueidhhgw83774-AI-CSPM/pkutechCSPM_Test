"""
health_checker.py 测试配置文件

包含pytest fixture和测试报告生成逻辑
"""

import pytest
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# 设置测试环境变量(从.env文件读取或使用默认值)
env_file = Path(__file__).parent.parent.parent / ".env"
if env_file.exists():
    # 简单读取.env文件
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                # 移除引号
                value = value.strip().strip('"').strip("'")
                if key and value:
                    os.environ.setdefault(key, value)
    print(f"✅ 已加载环境变量文件: {env_file}")
    opensearch_url = os.getenv("OPENSEARCH_URL")
    if opensearch_url:
        print(f"  OpenSearch URL: {opensearch_url}")
else:
    print(f"⚠️ 环境变量文件不存在: {env_file}")
    # 设置默认值
    os.environ.setdefault('OPENSEARCH_URL', 'https://172.19.75.181:9200/')
    os.environ.setdefault('OPENSEARCH_USER', 'admin')
    os.environ.setdefault('OPENSEARCH_PASSWORD', 'admin')

# 项目根目录(固定路径)
project_root = Path(__file__).parent.parent.parent.parent / "platform_python_backend-testing"
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
        - 包含 "Security" 或测试名包含 "SEC" → security
        - 包含 "Error" 或测试名包含 "_e0" → error
        - 其他 → normal
        """
        test_name = nodeid.split("::")[-1]

        # 确定测试类别
        if "Security" in nodeid or "_sec_" in test_name.lower():
            category = "security"
        elif "Error" in nodeid or "_e0" in test_name:
            category = "error"
        else:
            category = "normal"

        # 添加结果
        self.results[category].append({
            "id": nodeid,
            "name": test_name,
            "outcome": outcome,
            "duration": round(duration * 1000, 2)  # 转换为毫秒
        })


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

    # 计算统计信息
    total_tests = sum(len(results) for results in collector.results.values())
    passed_tests = sum(
        1 for category in collector.results.values()
        for result in category
        if result["outcome"] == "passed"
    )
    failed_tests = sum(
        1 for category in collector.results.values()
        for result in category
        if result["outcome"] == "failed"
    )
    xfailed_tests = sum(
        1 for category in collector.results.values()
        for result in category
        if result["outcome"] == "xfailed"
    )

    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    effective_pass_rate = (passed_tests / (total_tests - xfailed_tests) * 100) if (total_tests - xfailed_tests) > 0 else 0

    execution_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 生成 JSON 报告
    json_report = {
        "summary": {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "xfailed": xfailed_tests,
            "pass_rate": f"{pass_rate:.1f}%",
            "effective_pass_rate": f"{effective_pass_rate:.1f}%"
        },
        "categories": {
            "normal": {
                "total": len(collector.results["normal"]),
                "passed": sum(1 for r in collector.results["normal"] if r["outcome"] == "passed"),
                "failed": sum(1 for r in collector.results["normal"] if r["outcome"] == "failed"),
                "xfailed": sum(1 for r in collector.results["normal"] if r["outcome"] == "xfailed"),
                "results": collector.results["normal"]
            },
            "error": {
                "total": len(collector.results["error"]),
                "passed": sum(1 for r in collector.results["error"] if r["outcome"] == "passed"),
                "failed": sum(1 for r in collector.results["error"] if r["outcome"] == "failed"),
                "xfailed": sum(1 for r in collector.results["error"] if r["outcome"] == "xfailed"),
                "results": collector.results["error"]
            },
            "security": {
                "total": len(collector.results["security"]),
                "passed": sum(1 for r in collector.results["security"] if r["outcome"] == "passed"),
                "failed": sum(1 for r in collector.results["security"] if r["outcome"] == "failed"),
                "xfailed": sum(1 for r in collector.results["security"] if r["outcome"] == "xfailed"),
                "results": collector.results["security"]
            }
        },
        "execution_time": execution_time
    }

    # 保存 JSON 报告
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    json_path = reports_dir / "TestReport_health_checker.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_report, f, ensure_ascii=False, indent=2)

    print(f"\n✅ JSON报告已生成: {json_path}")

    # 生成 Markdown 报告
    md_report = _generate_markdown_report(json_report)
    md_path = reports_dir / "TestReport_health_checker.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_report)

    print(f"✅ Markdown报告已生成: {md_path}")

    print(f"\n✅ 测试报告已生成:")
    print(f"  - {md_path}")
    print(f"  - {json_path}")


def _generate_markdown_report(json_report: dict) -> str:
    """生成Markdown格式的测试报告"""

    summary = json_report["summary"]
    categories = json_report["categories"]
    execution_time = json_report["execution_time"]

    # 确定测试是否通过
    if summary["failed"] == 0:
        conclusion = "✅ **所有测试通过!** 代码质量优秀。"
    else:
        conclusion = f"❌ **有 {summary['failed']} 个测试失败!** 需要修复后再提交代码。"

    md = f"""# health_checker.py 测试报告

## 测试概要

| 项目 | 值 |
|------|-----|
| 测试对象 | `app/core/health_checker.py` |
| 测试规格 | `health_checker_tests.md` |
| 执行时间 | {execution_time} |
| 覆盖率目标 | 90% |

## 测试结果统计

| 类别 | 总数 | 通过 | 失败 | 预期失败 |
|------|------|------|------|----------|
| 正常系 | {categories['normal']['total']} | {categories['normal']['passed']} | {categories['normal']['failed']} | {categories['normal']['xfailed']} |
| 异常系 | {categories['error']['total']} | {categories['error']['passed']} | {categories['error']['failed']} | {categories['error']['xfailed']} |
| 安全测试 | {categories['security']['total']} | {categories['security']['passed']} | {categories['security']['failed']} | {categories['security']['xfailed']} |
| **合计** | **{summary['total']}** | **{summary['passed']}** | **{summary['failed']}** | **{summary['xfailed']}** |

## 测试通过率

- **实际通过率**: {summary['pass_rate']}
- **有效通过率** (排除预期失败): {summary['effective_pass_rate']}

---

## 正常系测试详情

| ID | 测试名称 | 结果 | 执行时间 |
|----|---------|------|----------|
"""

    for result in categories['normal']['results']:
        status_icon = "✅" if result['outcome'] == "passed" else ("⚠️" if result['outcome'] == "xfailed" else "❌")
        test_name = _get_readable_name(result['name'])
        md += f"| - | {test_name} | {status_icon} | {result['duration']}ms |\n"

    md += "\n## 异常系测试详情\n\n"
    md += "| ID | 测试名称 | 结果 | 执行时间 |\n"
    md += "|----|---------|------|----------|\n"

    for result in categories['error']['results']:
        status_icon = "✅" if result['outcome'] == "passed" else ("⚠️" if result['outcome'] == "xfailed" else "❌")
        test_name = _get_readable_name(result['name'])
        md += f"| - | {test_name} | {status_icon} | {result['duration']}ms |\n"

    md += "\n## 安全测试详情\n\n"
    md += "| ID | 测试名称 | 结果 | 执行时间 |\n"
    md += "|----|---------|------|----------|\n"

    for result in categories['security']['results']:
        status_icon = "✅" if result['outcome'] == "passed" else ("⚠️" if result['outcome'] == "xfailed" else "❌")
        test_name = _get_readable_name(result['name'])
        md += f"| - | {test_name} | {status_icon} | {result['duration']}ms |\n"

    md += f"\n---\n\n## 结论\n\n{conclusion}\n\n---\n\n*报告生成时间: {execution_time}*\n"

    return md


def _get_readable_name(test_name: str) -> str:
    """将测试方法名转换为可读名称"""

    name_map = {
        # 正常系测试
        "test_health_status_init_healthy": "HEALTH-001: HealthStatus初始化(健康状态)",
        "test_health_status_init_unhealthy": "HEALTH-002: HealthStatus初始化(非健康状态)",
        "test_health_status_to_dict": "HEALTH-003: HealthStatus转字典格式",
        "test_perform_health_check_all_healthy": "HEALTH-004: 完整健康检查(全部服务健康)",
        "test_perform_health_check_opensearch_unhealthy": "HEALTH-005: 完整健康检查(OpenSearch不健康)",
        "test_perform_health_check_litellm_unhealthy": "HEALTH-006: 完整健康检查(LiteLLM不健康)",
        "test_perform_health_check_all_unhealthy": "HEALTH-007: 完整健康检查(全部服务不健康)",
        "test_check_opensearch_healthy": "HEALTH-008: OpenSearch连接检查(健康)",
        "test_check_opensearch_unhealthy": "HEALTH-009: OpenSearch连接检查(不健康)",
        "test_check_litellm_healthy": "HEALTH-010: LiteLLM连接检查(健康)",
        "test_check_litellm_unhealthy": "HEALTH-011: LiteLLM连接检查(不健康)",

        # 异常系测试
        "test_health_status_none_message": "HEALTH-E01: HealthStatus message为None",
        "test_health_status_empty_message": "HEALTH-E02: HealthStatus message为空字符串",
        "test_health_status_none_details": "HEALTH-E03: HealthStatus details为None",
        "test_perform_health_check_opensearch_exception": "HEALTH-E04: 健康检查时OpenSearch抛异常",
        "test_perform_health_check_litellm_exception": "HEALTH-E05: 健康检查时LiteLLM抛异常",
        "test_perform_health_check_both_exception": "HEALTH-E06: 健康检查时全部服务抛异常",
        "test_check_opensearch_connection_timeout": "HEALTH-E07: OpenSearch连接超时",
        "test_check_opensearch_authentication_error": "HEALTH-E08: OpenSearch认证失败",
        "test_check_litellm_connection_timeout": "HEALTH-E09: LiteLLM连接超时",
        "test_check_litellm_invalid_response": "HEALTH-E10: LiteLLM返回无效响应",

        # 安全测试
        "test_sec_01_no_credentials_in_error": "HEALTH-SEC-01: 错误信息不包含凭证",
        "test_sec_02_no_internal_paths_in_response": "HEALTH-SEC-02: 响应不包含内部路径",
        "test_sec_03_response_timing_consistent": "HEALTH-SEC-03: 响应时间一致性",
        "test_sec_04_details_structure_consistent": "HEALTH-SEC-04: details结构一致性",
        "test_sec_05_no_stack_trace_in_details": "HEALTH-SEC-05: details不包含堆栈跟踪",
        "test_sec_06_timeout_values_not_exposed": "HEALTH-SEC-06: 超时值不暴露在响应中"
    }

    return name_map.get(test_name, test_name)
