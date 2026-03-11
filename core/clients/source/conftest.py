"""
conftest.py - clients.py 测试配置

功能:
  1. 测试结果收集
  2. 自动生成 Markdown 和 JSON 测试报告
  3. 测试ID到可读名称的映射
"""

import pytest
import json
import sys
from pathlib import Path
from datetime import datetime

# 项目根目录配置
project_root = Path(__file__).parent.parent.parent.parent / "platform_python_backend-testing"
sys.path.insert(0, str(project_root))


class TestResultCollector:
    """测试结果收集器 - 用于生成测试报告"""

    def __init__(self):
        self.results = {
            "normal": [],    # 正常系测试
            "error": [],     # 异常系测试
            "security": []   # 安全测试
        }
        self.start_time = datetime.now()

    def add_result(self, nodeid: str, outcome: str, duration: float):
        """
        添加测试结果

        分类规则:
        - 包含 "Security" 或 "_sec_" → security
        - 包含 "Error" 或 "_e0" → error
        - 其他 → normal
        """
        category = "normal"

        if "Security" in nodeid or "_sec_" in nodeid.lower():
            category = "security"
        elif "Error" in nodeid or "_e0" in nodeid:
            category = "error"

        result = {
            "nodeid": nodeid,
            "status": outcome,
            "duration": duration
        }

        self.results[category].append(result)


# 全局收集器实例
collector = TestResultCollector()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """捕获每个测试的执行结果"""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        nodeid = item.nodeid
        test_outcome = report.outcome  # passed, failed, skipped
        duration = report.duration

        collector.add_result(nodeid, test_outcome, duration)


def pytest_sessionfinish(session, exitstatus):
    """
    测试会话结束时生成报告

    生成两种格式:
    1. Markdown 报告 (人类可读)
    2. JSON 报告 (机器可读)
    """
    results = collector.results

    # 计算统计数据
    normal_tests = results["normal"]
    error_tests = results["error"]
    security_tests = results["security"]

    total = len(normal_tests) + len(error_tests) + len(security_tests)
    passed = sum(1 for t in normal_tests + error_tests + security_tests if t["status"] == "passed")
    failed = sum(1 for t in normal_tests + error_tests + security_tests if t["status"] == "failed")
    xfailed = sum(1 for t in normal_tests + error_tests + security_tests if t["status"] == "xfailed")

    pass_rate = (passed / total * 100) if total > 0 else 0
    effective_pass_rate = (passed / (total - xfailed) * 100) if (total - xfailed) > 0 else 0

    # 生成 Markdown 报告
    report_dir = Path(__file__).parent.parent / "reports"
    report_dir.mkdir(exist_ok=True)

    md_report_path = report_dir / "TestReport_clients.md"
    json_report_path = report_dir / "TestReport_clients.json"

    # Markdown 报告内容
    md_content = f"""# clients.py 测试报告

## 测试概要

| 项目 | 值 |
|------|-----|
| 测试对象 | `app/core/clients.py` |
| 测试规格 | `clients_tests.md` |
| 执行时间 | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} |
| 覆盖率目标 | 90% |

## 测试结果统计

| 类别 | 总数 | 通过 | 失败 | 预期失败 |
|------|------|------|------|----------|
| 正常系 | {len(normal_tests)} | {sum(1 for t in normal_tests if t['status']=='passed')} | {sum(1 for t in normal_tests if t['status']=='failed')} | {sum(1 for t in normal_tests if t['status']=='xfailed')} |
| 异常系 | {len(error_tests)} | {sum(1 for t in error_tests if t['status']=='passed')} | {sum(1 for t in error_tests if t['status']=='failed')} | {sum(1 for t in error_tests if t['status']=='xfailed')} |
| 安全测试 | {len(security_tests)} | {sum(1 for t in security_tests if t['status']=='passed')} | {sum(1 for t in security_tests if t['status']=='failed')} | {sum(1 for t in security_tests if t['status']=='xfailed')} |
| **合计** | **{total}** | **{passed}** | **{failed}** | **{xfailed}** |

## 测试通过率

- **实际通过率**: {pass_rate:.1f}%
- **有效通过率** (排除预期失败): {effective_pass_rate:.1f}%

---

## 正常系测试详情

| 测试ID | 测试名称 | 结果 | 执行时间 |
|--------|---------|------|----------|
"""

    # 添加正常系测试详情
    for idx, test in enumerate(normal_tests, 1):
        test_name = _get_readable_name(test["nodeid"])
        status_icon = "✅" if test["status"] == "passed" else "❌" if test["status"] == "failed" else "⚠️"
        md_content += f"| CLT-{idx:03d} | {test_name} | {status_icon} | {test['duration']:.3f}s |\n"

    md_content += "\n---\n\n## 异常系测试详情\n\n"
    md_content += "| 测试ID | 测试名称 | 结果 | 执行时间 |\n"
    md_content += "|--------|---------|------|----------|\n"

    # 添加异常系测试详情
    for idx, test in enumerate(error_tests, 1):
        test_name = _get_readable_name(test["nodeid"])
        status_icon = "✅" if test["status"] == "passed" else "❌" if test["status"] == "failed" else "⚠️"
        md_content += f"| CLT-E{idx:02d} | {test_name} | {status_icon} | {test['duration']:.3f}s |\n"

    md_content += "\n---\n\n## 安全测试详情\n\n"
    md_content += "| 测试ID | 测试名称 | 结果 | 执行时间 |\n"
    md_content += "|--------|---------|------|----------|\n"

    # 添加安全测试详情
    for idx, test in enumerate(security_tests, 1):
        test_name = _get_readable_name(test["nodeid"])
        status_icon = "✅" if test["status"] == "passed" else "❌" if test["status"] == "failed" else "⚠️"
        md_content += f"| CLT-SEC-{idx:02d} | {test_name} | {status_icon} | {test['duration']:.3f}s |\n"

    # 添加结论
    if failed == 0:
        conclusion = "✅ **所有测试通过!** clients.py 模块测试完全通过,代码质量优秀。"
    else:
        conclusion = f"❌ **存在 {failed} 个失败测试**,请检查并修复相关问题。"

    md_content += f"\n---\n\n## 结论\n\n{conclusion}\n\n---\n\n*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"

    # 写入 Markdown 报告
    with open(md_report_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    # JSON 报告内容
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
                "passed": sum(1 for t in normal_tests if t["status"] == "passed"),
                "failed": sum(1 for t in normal_tests if t["status"] == "failed"),
                "results": normal_tests
            },
            "error": {
                "total": len(error_tests),
                "passed": sum(1 for t in error_tests if t["status"] == "passed"),
                "failed": sum(1 for t in error_tests if t["status"] == "failed"),
                "results": error_tests
            },
            "security": {
                "total": len(security_tests),
                "passed": sum(1 for t in security_tests if t["status"] == "passed"),
                "failed": sum(1 for t in security_tests if t["status"] == "failed"),
                "results": security_tests
            }
        },
        "execution_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # 写入 JSON 报告
    with open(json_report_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 测试报告已生成:")
    print(f"  - {md_report_path}")
    print(f"  - {json_report_path}\n")


def _get_readable_name(test_name: str) -> str:
    """将测试方法名转换为可读的中文名称"""

    name_map = {
        # 正常系测试 (CLT-001 ~ CLT-014)
        "test_extract_aws_region_from_url_standard": "标准AWS域名区域提取",
        "test_extract_aws_region_from_url_serverless": "Serverless域名区域提取",
        "test_extract_aws_region_from_url_fallback": "无效URL默认区域回退",
        "test_initialize_opensearch_success": "OpenSearch客户端初始化成功",
        "test_initialize_opensearch_with_basic_auth": "Basic认证OpenSearch初始化",
        "test_initialize_opensearch_aws_service": "AWS服务OpenSearch初始化",
        "test_initialize_opensearch_retry_success": "连接重试后成功",
        "test_get_opensearch_client_success": "获取已初始化的客户端",
        "test_get_opensearch_client_with_auth_success": "创建自定义认证客户端",
        "test_initialize_embedding_function_success": "Embedding函数初始化成功",
        "test_initialize_embedding_openai_model": "OpenAI Embedding模型初始化",
        "test_initialize_embedding_with_dimensions": "指定维度Embedding初始化",
        "test_get_embedding_function_success": "获取已初始化的Embedding函数",
        "test_module_import": "模块导入测试",

        # 异常系测试 (CLT-E01 ~ CLT-E16)
        "test_initialize_opensearch_e01_missing_url": "缺少OPENSEARCH_URL配置",
        "test_initialize_opensearch_e02_invalid_url": "无效的OPENSEARCH_URL格式",
        "test_initialize_opensearch_e03_missing_credentials": "缺少认证凭据",
        "test_initialize_opensearch_e04_connection_timeout": "连接超时失败",
        "test_initialize_opensearch_e05_max_retries_exceeded": "超过最大重试次数",
        "test_initialize_opensearch_e06_ping_failure": "Ping操作失败",
        "test_initialize_opensearch_e07_ssl_cert_error": "SSL证书验证错误",
        "test_get_opensearch_client_e08_not_initialized": "客户端未初始化时获取",
        "test_get_opensearch_client_e09_init_error_state": "初始化错误状态下获取",
        "test_get_opensearch_client_with_auth_e10_invalid_format": "无效认证格式",
        "test_get_opensearch_client_with_auth_e11_missing_url": "缺少URL配置",
        "test_get_opensearch_client_with_auth_e12_ping_failure": "自定义认证Ping失败",
        "test_initialize_embedding_e13_missing_api_key": "缺少Embedding API密钥",
        "test_initialize_embedding_e14_missing_model_name": "缺少Embedding模型名称",
        "test_get_embedding_function_e15_not_initialized": "Embedding未初始化时获取",
        "test_get_embedding_function_e16_init_error_state": "Embedding错误状态下获取",

        # 安全测试 (CLT-SEC-01 ~ CLT-SEC-06)
        "test_sec_01_credentials_not_logged": "认证凭据不被日志记录",
        "test_sec_02_api_key_not_exposed": "API密钥不暴露在错误消息中",
        "test_sec_03_ssl_verification_enabled": "SSL证书验证强制启用",
        "test_sec_04_connection_timeout_reasonable": "连接超时设置合理",
        "test_sec_05_error_messages_sanitized": "错误消息已清理敏感信息",
        "test_sec_06_auth_header_not_exposed": "认证头信息不暴露",
    }

    # 从 nodeid 提取测试方法名
    if "::" in test_name:
        test_name = test_name.split("::")[-1]

    return name_map.get(test_name, test_name)


# Pytest fixtures
@pytest.fixture
def mock_settings():
    """模拟 settings 配置对象"""
    from unittest.mock import MagicMock
    settings = MagicMock()
    settings.OPENSEARCH_URL = "https://test.us-east-1.es.amazonaws.com:443"
    settings.OPENSEARCH_USER = "admin"
    settings.OPENSEARCH_PASSWORD = "admin123"
    settings.OPENSEARCH_CA_CERTS_PATH = None
    settings.EMBEDDING_API_KEY = "sk-test123"
    settings.EMBEDDING_MODEL_NAME = "text-embedding-3-large"
    settings.EMBEDDING_MODEL_BASE_URL = "http://litellm:4000"
    return settings


@pytest.fixture
def reset_global_state():
    """重置全局状态"""
    import app.core.clients as clients_module

    # 重置全局变量
    clients_module.os_client = None
    clients_module.OS_CLIENT_INIT_ERROR = None
    clients_module.OS_CLIENT_INITIALIZED = False
    clients_module.embedding_function = None
    clients_module.EMBEDDING_INIT_ERROR = None
    clients_module.EMBEDDING_INITIALIZED = False

    yield

    # 测试后清理
    clients_module.os_client = None
    clients_module.OS_CLIENT_INIT_ERROR = None
    clients_module.OS_CLIENT_INITIALIZED = False
    clients_module.embedding_function = None
    clients_module.EMBEDDING_INIT_ERROR = None
    clients_module.EMBEDDING_INITIALIZED = False
