"""
MCP Plugin Sessions テスト設定

テスト仕様: docs/testing/plugins/mcp/mcp_plugin_sessions_tests.md
テスト数量: 74 (正常系:41, 異常系:11, セキュリティ:22)
"""

import sys, os, pytest, pytest_asyncio, json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

# プロジェクトルート設定（env_loader を使用）
try:
    from env_loader import PROJECT_ROOT
except ImportError:
    _here = Path(__file__).resolve()
    for _p in [_here, *_here.parents]:
        if (_p / "env_loader.py").exists():
            sys.path.insert(0, str(_p))
            from env_loader import PROJECT_ROOT
            break
    else:
        raise ImportError("env_loader.py が見つかりません")

project_root = PROJECT_ROOT / "platform_python_backend-testing"
sys.path.insert(0, str(project_root))

# Mock weasyprint
from unittest.mock import MagicMock as _M
for _m in ["weasyprint"]+[f"weasyprint.{x}" for x in ["CSS","HTML","css","text","text.fonts","text.ffi","text.constants"]]:
    sys.modules.setdefault(_m, _M())


# ============================================
# PostgreSQL モック Fixtures
# ============================================

def create_pg_mock(fetchall_return=None, fetchone_return=None):
    """PostgreSQL 接続プールの正しい mock 構造を作成するヘルパー

    RecursionError を防ぐため、spec を使用して属性を制限
    """
    # カーソル Mockを作成する
    mock_cursor = MagicMock(spec=['execute', 'fetchone', 'fetchall', '__aenter__', '__aexit__'])
    mock_cursor.execute = AsyncMock()
    if fetchall_return is not None:
        mock_cursor.fetchall = AsyncMock(return_value=fetchall_return)
    else:
        mock_cursor.fetchall = AsyncMock(return_value=[])
    if fetchone_return is not None:
        mock_cursor.fetchone = AsyncMock(return_value=fetchone_return)
    else:
        mock_cursor.fetchone = AsyncMock(return_value=None)
    mock_cursor.__aenter__ = AsyncMock(return_value=mock_cursor)
    mock_cursor.__aexit__ = AsyncMock(return_value=None)

    # connection mockを作成する
    mock_conn = MagicMock(spec=['cursor', '__aenter__', '__aexit__'])
    mock_conn.cursor = MagicMock(return_value=mock_cursor)
    mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn.__aexit__ = AsyncMock(return_value=None)

    # プールのモックを作成 - キーポイント：spec を使用して属性を制限し、再帰を防止する
    mock_pool = MagicMock(spec=['connection'])
    # side_effectを使用してreturn_valueを使用せずに再帰を避ける
    mock_pool.connection = MagicMock(return_value=mock_conn, spec=['return_value'])

    return mock_pool


@pytest.fixture
def mock_postgres_pool():
    """PostgreSQL接続プールのモック (廃止予定、create_pg_mock を使用)"""
    return create_pg_mock(fetchall_return=[], fetchone_return=None)


@pytest.fixture
def mock_checkpoint_data():
    """チェックポイントデータのサンプル"""
    return {
        "session_id": "test-session-001",
        "checkpoint_id": "ckpt-001",
        "checkpoint_ns": "",
        "metadata": {"session_name": "テストセッション"},
        "checkpoint": {"channel_values": {"messages": []}}
    }


@pytest.fixture
def app():
    """FastAPI アプリケーションインスタンス"""
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
    """FastAPI 非同期テストクライアント"""
    from httpx import AsyncClient, ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ============================================
# テスト結果コレktor
# ============================================

class TestResultCollector:
    def __init__(self):
        self.results = {"normal": [], "error": [], "security": []}

    def add_result(self, nodeid, outcome, duration):
        t = nodeid.split("::")[-1]
        cat = "security" if "Security" in nodeid else ("error" if "Error" in nodeid else "normal")
        self.results[cat].append({"test_id": t, "outcome": outcome, "duration": duration})

    def generate_markdown_report(self, path):
        total = sum(len(v) for v in self.results.values())
        passed = sum(1 for c in self.results.values() for r in c if r["outcome"] == "passed")
        lines = [f"# MCP Plugin Sessions 测试报告\n", f"**通過率**: {passed}/{total}\n"]
        for cat, label in [("normal","正常系"),("error","異常系"),("security","セキュリティ")]:
            r = self.results[cat]
            p = sum(1 for x in r if x["outcome"] == "passed")
            lines.append(f"\n## {label}: {p}/{len(r)}\n")
        path.write_text("\n".join(lines), encoding="utf-8")

    def generate_json_report(self, path):
        total = sum(len(v) for v in self.results.values())
        passed = sum(1 for c in self.results.values() for r in c if r["outcome"] == "passed")
        report = {"summary": {"total": total, "passed": passed}, "categories": self.results}
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call":
        collector = getattr(item.session.config, '_test_collector', None)
        if collector:
            collector.add_result(item.nodeid, rep.outcome, rep.duration)


def pytest_sessionstart(session): session.config._test_collector = TestResultCollector()


def pytest_sessionfinish(session, exitstatus):
    c = getattr(session.config, '_test_collector', None)
    if not c:
        return
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    c.generate_markdown_report(reports_dir / "TestReport_mcp_plugin_sessions.md")
    c.generate_json_report(reports_dir / "TestReport_mcp_plugin_sessions.json")

