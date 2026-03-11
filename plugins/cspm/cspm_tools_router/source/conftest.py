"""
CSPM Tools Router 测试配置

测试规格: cspm_tools_router_tests.md
测试数量: 29 (正常:10, 異常:12, セキュリティ:7)
"""

import sys, os, pytest, pytest_asyncio, json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from dotenv import load_dotenv

_env = Path(__file__).resolve().parents[5] / ".env"
if _env.exists(): load_dotenv(_env)
_root = os.environ.get("soure_root", "").strip().strip('"').strip("'")
project_root = Path(_root) if _root and Path(_root).exists() else Path(__file__).resolve().parents[5] / "platform_python_backend-testing"
sys.path.insert(0, str(project_root))


# Mock weasyprint
from unittest.mock import MagicMock as _M
for _m in ["weasyprint"]+[f"weasyprint.{x}" for x in ["CSS","HTML","css","text","text.fonts","text.ffi","text.constants"]]:
    sys.modules.setdefault(_m, _M())

@pytest.fixture
def app():
    from contextlib import asynccontextmanager
    import importlib
    @asynccontextmanager
    async def _noop_lifespan(app): yield
    main_mod = importlib.import_module("app.main")
    fastapi_app = main_mod.app.app if hasattr(main_mod.app, "app") else main_mod.app
    fastapi_app.router.lifespan_context = _noop_lifespan
    return fastapi_app

@pytest_asyncio.fixture
async def async_client(app):
    from httpx import AsyncClient, ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest.fixture
def mock_tools_available():
    with patch("app.cspm_plugin.tools_router.validate_policy") as mv, \
         patch("app.cspm_plugin.tools_router.get_custodian_schema") as ms, \
         patch("app.cspm_plugin.tools_router.list_available_resources") as mr, \
         patch("app.cspm_plugin.tools_router.retrieve_reference") as mref:
        mv.invoke = MagicMock(return_value="Validation successful.")
        ms.invoke = MagicMock(return_value='{"resources":{}}')
        mr.invoke = MagicMock(return_value="s3, ec2")
        mref.ainvoke = AsyncMock(return_value="Reference doc")
        yield {"validate": mv, "schema": ms, "resources": mr, "reference": mref}

class TestResultCollector:
    def __init__(self): self.results = {"normal": [], "error": [], "security": []}
    def add_result(self, nodeid, outcome, duration):
        t = nodeid.split("::")[-1]
        cat = "security" if "Security" in nodeid else ("error" if "Error" in nodeid or "Unavailable" in nodeid or "Exception" in nodeid else "normal")
        self.results[cat].append({"test_id": t, "outcome": outcome, "duration": duration})
    def generate_markdown_report(self, path):
        total = sum(len(v) for v in self.results.values())
        passed = sum(1 for c in self.results.values() for r in c if r["outcome"] == "passed")
        path.write_text(f"# CSPM Tools Router\n**通過率**: {passed}/{total}\n", encoding="utf-8")
    def generate_json_report(self, path):
        total = sum(len(v) for v in self.results.values())
        passed = sum(1 for c in self.results.values() for r in c if r["outcome"] == "passed")
        path.write_text(json.dumps({"summary": {"total": total, "passed": passed}, "categories": self.results}, indent=2), encoding="utf-8")

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call": item.session.config._test_collector.add_result(item.nodeid, rep.outcome, rep.duration)

def pytest_sessionstart(session): session.config._test_collector = TestResultCollector()

def pytest_sessionfinish(session, exitstatus):
    c = session.config._test_collector
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    c.generate_markdown_report(reports_dir / "TestReport_cspm_tools_router.md")
    c.generate_json_report(reports_dir / "TestReport_cspm_tools_router.json")

