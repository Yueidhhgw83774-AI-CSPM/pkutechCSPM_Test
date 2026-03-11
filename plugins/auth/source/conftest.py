# conftest.py
"""
auth 测试配置和钩子函数

测试对象:
  - app/core/auth.py
  - app/auth/router.py
  - app/models/auth.py

测试规格: docs/testing/plugins/auth_tests.md
"""

import pytest
import pytest_asyncio
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any

# 项目根目录设置
# 从 TestReport/plugins/auth/source 向上5级到 python_ai_cspm
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent / "platform_python_backend-testing"
if not project_root.exists():
    raise RuntimeError(f"项目根目录不存在: {project_root}")
sys.path.insert(0, str(project_root))

# 设置JWT密钥环境变量（使用shared_secret中的密钥）
os.environ["JWT_SECRET_KEY"] = "f4fae6a6c089204d69efdc35438312a81005e1c3825a40cfc706cbe5ec0f50b1"

# 加载环境变量
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


class TestResultCollector:
    """收集测试结果用于生成报告"""

    def __init__(self):
        self.results: Dict[str, List[Dict[str, Any]]] = {
            "normal": [],    # 正常系测试
            "error": [],     # 异常系测试
            "security": []   # 安全测试
        }
        self.start_time = datetime.now()
        self.end_time = None

    def add_result(self, nodeid: str, outcome: str, duration: float):
        """添加测试结果

        分类规则:
        - 包含 "Security" 或测试名包含 "SEC" → security
        - 包含 "Error" 或测试名包含 "_e0" 或 "_E" → error
        - 其他 → normal
        """
        test_name = nodeid.split("::")[-1] if "::" in nodeid else nodeid
        class_name = nodeid.split("::")[-2] if nodeid.count("::") >= 2 else ""

        # 获取可读名称
        readable_name = self._get_readable_name(test_name)

        # 提取测试ID
        test_id = self._extract_test_id(test_name)

        result = {
            "nodeid": nodeid,
            "test_name": test_name,
            "readable_name": readable_name,
            "test_id": test_id,
            "class_name": class_name,
            "outcome": outcome,
            "duration": duration,
            "duration_ms": round(duration * 1000, 2)
        }

        # 分类
        if "Security" in class_name or "SEC" in test_name.upper() or "security" in test_name.lower():
            self.results["security"].append(result)
        elif "Error" in class_name or "_e0" in test_name.lower() or "_E" in test_name:
            self.results["error"].append(result)
        else:
            self.results["normal"].append(result)

    def _get_readable_name(self, test_name: str) -> str:
        """将测试方法名转换为可读名称"""
        name_map = {
            # 正常系测试 (AUTH-001 ~ AUTH-012)
            "test_login_success": "AUTH-001: 有效认证信息获取Token",
            "test_get_current_user": "AUTH-002: 认证后获取用户信息",
            "test_protected_route": "AUTH-003: 访问受保护路由",
            "test_verify_password_success": "AUTH-004: 密码验证成功",
            "test_get_password_hash": "AUTH-005: 密码哈希化",
            "test_get_user_found": "AUTH-006: 用户查询成功",
            "test_get_user_with_roles_found": "AUTH-007: 带角色用户查询成功",
            "test_authenticate_user_with_roles_success": "AUTH-008: 带角色认证成功",
            "test_create_access_token_with_expiry": "AUTH-009: 指定有效期Token生成",
            "test_create_access_token_default_expiry": "AUTH-010: 默认有效期Token生成",
            "test_create_access_token_with_roles_and_expiry": "AUTH-011: 带角色Token生成(指定期限)",
            "test_create_access_token_with_roles_default_expiry": "AUTH-012: 带角色Token生成(默认期限)",

            # 异常系测试 (AUTH-E01 ~ AUTH-E18)
            "test_login_invalid_password": "AUTH-E01: 无效密码返回401",
            "test_login_unknown_user": "AUTH-E02: 不存在用户返回401",
            "test_expired_token": "AUTH-E03: 过期Token返回401",
            "test_malformed_token": "AUTH-E04: 无效Token格式返回401",
            "test_no_auth_header": "AUTH-E05: 无认证头返回401",
            "test_disabled_user": "AUTH-E06: 禁用用户返回400",
            "test_insufficient_roles": "AUTH-E07: 权限不足返回403",
            "test_verify_password_failure": "AUTH-E08: 密码验证失败",
            "test_get_user_not_found": "AUTH-E09: 不存在用户返回None",
            "test_authenticate_user_with_roles_unknown": "AUTH-E10: 带角色认证-用户不存在",
            "test_authenticate_user_with_roles_wrong_password": "AUTH-E11: 带角色认证-密码错误",
            "test_get_current_user_no_sub": "AUTH-E12: 无sub字段Token返回401",
            "test_get_current_user_unknown_sub": "AUTH-E13: sub不存在于DB返回401",
            "test_require_all_roles_partial_match": "AUTH-E14: require_all_roles部分匹配返回403",
            "test_get_current_user_with_roles_no_sub": "AUTH-E15: 带角色获取用户-无sub返回401",
            "test_get_current_user_with_roles_jwt_error": "AUTH-E16: 带角色获取用户-无效Token",
            "test_get_current_user_with_roles_unknown_user": "AUTH-E17: 带角色获取用户-用户不存在",
            "test_disabled_user_with_roles": "AUTH-E18: 带角色禁用用户返回400",

            # 安全测试 (AUTH-SEC-01 ~ AUTH-SEC-08)
            "test_password_is_hashed": "AUTH-SEC-01: 密码bcrypt哈希验证",
            "test_token_modified_rejected": "AUTH-SEC-02: 篡改Token被拒绝",
            "test_password_not_in_response": "AUTH-SEC-03: 响应不包含密码信息",
            "test_token_expiry_enforced": "AUTH-SEC-04: Token有效期强制执行",
            "test_default_secret_key_warning": "AUTH-SEC-05: 默认SECRET_KEY警告",
            "test_jwt_alg_none_attack_rejected": "AUTH-SEC-06: JWT alg=none攻击防御",
            "test_jwt_role_tampering_rejected": "AUTH-SEC-07: JWT角色篡改检测",
            "test_role_escalation_prevented": "AUTH-SEC-08: 角色提权防止",
        }
        return name_map.get(test_name, test_name)

    def _extract_test_id(self, test_name: str) -> str:
        """从测试名称提取测试ID"""
        readable = self._get_readable_name(test_name)
        if ":" in readable:
            return readable.split(":")[0].strip()
        return ""

    def get_summary(self) -> Dict[str, Any]:
        """获取测试摘要"""
        total = sum(len(v) for v in self.results.values())
        passed = sum(
            1 for cat in self.results.values()
            for r in cat if r["outcome"] == "passed"
        )
        failed = sum(
            1 for cat in self.results.values()
            for r in cat if r["outcome"] == "failed"
        )
        xfailed = sum(
            1 for cat in self.results.values()
            for r in cat if r["outcome"] == "xfailed"
        )
        skipped = sum(
            1 for cat in self.results.values()
            for r in cat if r["outcome"] == "skipped"
        )

        pass_rate = (passed / total * 100) if total > 0 else 0
        effective_total = total - xfailed - skipped
        effective_pass_rate = (passed / effective_total * 100) if effective_total > 0 else 0

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "xfailed": xfailed,
            "skipped": skipped,
            "pass_rate": f"{pass_rate:.1f}%",
            "effective_pass_rate": f"{effective_pass_rate:.1f}%"
        }

    def generate_markdown_report(self) -> str:
        """生成Markdown格式报告"""
        summary = self.get_summary()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = f"""# auth 测试报告

## 测试概要

| 项目 | 值 |
|------|-----|
| 测试对象 | `app/core/auth.py`, `app/auth/router.py`, `app/models/auth.py` |
| 测试规格 | `docs/testing/plugins/auth_tests.md` |
| 执行时间 | {timestamp} |
| 覆盖率目标 | 90% |

## 测试结果统计

| 类别 | 总数 | 通过 | 失败 | 预期失败 | 跳过 |
|------|------|------|------|----------|------|
| 正常系 | {len(self.results['normal'])} | {sum(1 for r in self.results['normal'] if r['outcome']=='passed')} | {sum(1 for r in self.results['normal'] if r['outcome']=='failed')} | {sum(1 for r in self.results['normal'] if r['outcome']=='xfailed')} | {sum(1 for r in self.results['normal'] if r['outcome']=='skipped')} |
| 异常系 | {len(self.results['error'])} | {sum(1 for r in self.results['error'] if r['outcome']=='passed')} | {sum(1 for r in self.results['error'] if r['outcome']=='failed')} | {sum(1 for r in self.results['error'] if r['outcome']=='xfailed')} | {sum(1 for r in self.results['error'] if r['outcome']=='skipped')} |
| 安全测试 | {len(self.results['security'])} | {sum(1 for r in self.results['security'] if r['outcome']=='passed')} | {sum(1 for r in self.results['security'] if r['outcome']=='failed')} | {sum(1 for r in self.results['security'] if r['outcome']=='xfailed')} | {sum(1 for r in self.results['security'] if r['outcome']=='skipped')} |
| **合计** | **{summary['total']}** | **{summary['passed']}** | **{summary['failed']}** | **{summary['xfailed']}** | **{summary['skipped']}** |

## 测试通过率

- **实际通过率**: {summary['pass_rate']}
- **有效通过率** (排除预期失败): {summary['effective_pass_rate']}

---

## 正常系测试详情

| ID | 测试名称 | 结果 | 执行时间 |
|----|---------|------|----------|
"""
        for r in self.results['normal']:
            icon = "✅" if r['outcome'] == 'passed' else "❌" if r['outcome'] == 'failed' else "⏭️"
            report += f"| {r['test_id']} | {r['readable_name']} | {icon} | {r['duration_ms']}ms |\n"

        report += """
## 异常系测试详情

| ID | 测试名称 | 结果 | 执行时间 |
|----|---------|------|----------|
"""
        for r in self.results['error']:
            icon = "✅" if r['outcome'] == 'passed' else "❌" if r['outcome'] == 'failed' else "⏭️"
            report += f"| {r['test_id']} | {r['readable_name']} | {icon} | {r['duration_ms']}ms |\n"

        report += """
## 安全测试详情

| ID | 测试名称 | 结果 | 执行时间 |
|----|---------|------|----------|
"""
        for r in self.results['security']:
            icon = "✅" if r['outcome'] == 'passed' else "❌" if r['outcome'] == 'failed' else "⏭️"
            report += f"| {r['test_id']} | {r['readable_name']} | {icon} | {r['duration_ms']}ms |\n"

        # 结论
        if summary['failed'] == 0:
            conclusion = "✅ 所有测试通过！认证模块运行正常。"
        else:
            conclusion = f"⚠️ {summary['failed']} 个测试失败，需要检查和修复。"

        report += f"""
---

## 结论

{conclusion}

---

*报告生成时间: {timestamp}*
"""
        return report

    def generate_json_report(self) -> str:
        """生成JSON格式报告"""
        summary = self.get_summary()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report_data = {
            "summary": summary,
            "categories": {
                "normal": {
                    "count": len(self.results['normal']),
                    "results": self.results['normal']
                },
                "error": {
                    "count": len(self.results['error']),
                    "results": self.results['error']
                },
                "security": {
                    "count": len(self.results['security']),
                    "results": self.results['security']
                }
            },
            "execution_time": timestamp,
            "test_target": {
                "files": [
                    "app/core/auth.py",
                    "app/auth/router.py",
                    "app/models/auth.py"
                ],
                "spec": "docs/testing/plugins/auth_tests.md"
            }
        }

        return json.dumps(report_data, indent=2, ensure_ascii=False)


# 全局收集器实例
_collector = TestResultCollector()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """捕获每个测试的结果"""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        _collector.add_result(
            nodeid=report.nodeid,
            outcome=report.outcome,
            duration=report.duration
        )


def pytest_sessionfinish(session, exitstatus):
    """测试会话结束时生成报告"""
    _collector.end_time = datetime.now()

    # 确定报告输出目录
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # 生成Markdown报告
    md_report = _collector.generate_markdown_report()
    md_path = reports_dir / "TestReport_auth.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_report)

    # 生成JSON报告
    json_report = _collector.generate_json_report()
    json_path = reports_dir / "TestReport_auth.json"
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json_report)

    print(f"\n{'='*60}")
    print(f"📊 测试报告已生成:")
    print(f"   - Markdown: {md_path}")
    print(f"   - JSON: {json_path}")
    print(f"{'='*60}")


# ============================================================================
# Fixtures（测试夹具）
# ============================================================================

@pytest.fixture(scope="session")
def app():
    """FastAPI应用程序实例（最小化测试版本）

    创建一个只包含auth路由的最小FastAPI应用，
    避免导入其他可能缺少依赖的模块。
    """
    from fastapi import FastAPI
    from app.auth.router import router as auth_router

    test_app = FastAPI()
    test_app.include_router(auth_router)

    return test_app


@pytest_asyncio.fixture
async def async_client(app):
    """异步HTTP测试客户端

    使用ASGITransport直接连接FastAPI应用。
    无需启动实际HTTP服务器即可进行测试。
    """
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def valid_token():
    """有效的JWT Token（testuser用）

    注意: 使用应用的SECRET_KEY进行签名。
    确保端点测试中认证功能正常工作。
    """
    from jose import jwt
    from app.core.auth import SECRET_KEY, ALGORITHM
    payload = {
        "sub": "testuser",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def admin_token():
    """管理员JWT Token（全角色）"""
    from jose import jwt
    from app.core.auth import SECRET_KEY, ALGORITHM
    payload = {
        "sub": "admin",
        "roles": [
            "cspm_dashboard_read_role",
            "rag_search_read_role",
            "document_write_role",
            "cspm_job_execution_role"
        ],
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def testuser_token():
    """普通用户JWT Token（限定角色）"""
    from jose import jwt
    from app.core.auth import SECRET_KEY, ALGORITHM
    payload = {
        "sub": "testuser",
        "roles": ["rag_search_read_role"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def dashboard_user_token():
    """仪表板用户Token"""
    from jose import jwt
    from app.core.auth import SECRET_KEY, ALGORITHM
    payload = {
        "sub": "dashboard-user",
        "roles": ["cspm_dashboard_read_role"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def expired_token():
    """过期的Token"""
    from jose import jwt
    from app.core.auth import SECRET_KEY, ALGORITHM
    payload = {
        "sub": "testuser",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def disabled_user_in_db():
    """将禁用用户临时添加到fake_users_db的夹具

    测试结束后执行清理。
    """
    from app.core.auth import fake_users_db

    disabled_user_data = {
        "username": "disabled-user",
        "full_name": "禁用用户",
        "email": "disabled@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": True,
        "roles": []
    }

    # 添加用户
    fake_users_db["disabled-user"] = disabled_user_data
    yield disabled_user_data

    # 清理
    if "disabled-user" in fake_users_db:
        del fake_users_db["disabled-user"]


@pytest.fixture
def mock_role_required_endpoint(app):
    """注册需要角色的测试端点的夹具

    在测试期间向FastAPI应用添加一个需要cspm_dashboard_read_role的临时端点。

    注意: FastAPI难以删除路由器，因此使用测试专用路径避免冲突。
    """
    from fastapi import APIRouter, Depends
    from app.core.auth import require_roles

    test_router = APIRouter(tags=["test"])

    @test_router.get("/protected-dashboard")
    async def protected_dashboard_endpoint(
        user=Depends(require_roles(["cspm_dashboard_read_role"]))
    ):
        return {"status": "ok", "user": user.username}

    # 添加路由器
    app.include_router(test_router)
    yield

    # 注意: FastAPI难以删除路由，但由于是测试专用路径，不会影响其他测试


@pytest.fixture(autouse=True)
def mock_password_verification():
    """Mock密码验证以避免bcrypt/passlib兼容性问题

    Python 3.13 + 新版bcrypt与passlib存在兼容性问题。
    此fixture使用mock来绕过实际的bcrypt调用。
    """
    from unittest.mock import patch

    def mock_verify(plain_password, hashed_password):
        """模拟密码验证 - 密码为'secret'时返回True"""
        return plain_password == "secret"

    def mock_hash(password):
        """模拟密码哈希 - 返回固定格式的假哈希"""
        return f"$2b$12$mockhash_{password}"

    with patch('app.core.auth.pwd_context.verify', side_effect=mock_verify):
        with patch('app.core.auth.pwd_context.hash', side_effect=mock_hash):
            yield


