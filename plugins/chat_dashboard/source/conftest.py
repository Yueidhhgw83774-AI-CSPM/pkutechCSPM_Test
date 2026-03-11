"""
Chat Dashboard 测试配置和Fixtures

测试规格: docs/testing/plugins/chat_dashboard/chat_dashboard_tests.md
覆盖率目标: 85%+
"""

import sys
import os
import pytest
import pytest_asyncio
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from dotenv import load_dotenv

# 读取 .env 配置
_env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

# project_root: 优先从 .env 的 soure_root 读取，否则自动推断
_source_root_env = os.environ.get("soure_root", "").strip().strip('"').strip("'")
if _source_root_env and Path(_source_root_env).exists():
    project_root = Path(_source_root_env)
else:
    project_root = Path(__file__).resolve().parent.parent.parent.parent.parent / "platform_python_backend-testing"

if not project_root.exists():
    raise RuntimeError(f"项目根目录不存在: {project_root}")
sys.path.insert(0, str(project_root))

# weasyprint は libpango 等の OS 依存ライブラリが必要なため
# テスト環境では sys.modules に mock を事前注入して ImportError を回避する
from unittest.mock import MagicMock as _MagicMock
for _mod in [
    "weasyprint",
    "weasyprint.CSS",
    "weasyprint.HTML",
    "weasyprint.css",
    "weasyprint.text",
    "weasyprint.text.fonts",
    "weasyprint.text.ffi",
    "weasyprint.text.constants",
]:
    sys.modules.setdefault(_mod, _MagicMock())


# ============================================
# モジュール状態リセット（autouse）
# ============================================

@pytest.fixture(autouse=True)
def reset_chat_dashboard_module():
    """テストごとにchat_dashboardモジュールのグローバル状態をリセット

    注意: router モジュールは削除しない。
    router は app.main 起動時に登録済みであり、削除すると
    次テストで authenticated_client の patch ターゲットが見つからなくなる。
    状態リセットは _simple_chatbot と _basic_client_cache のみ行う。
    """
    yield
    # グローバル変数のみリセット（モジュール自体は削除しない）
    try:
        import app.chat_dashboard.simple_chat_handler as handler
        handler._simple_chatbot = None
    except (ImportError, AttributeError):
        pass

    try:
        import app.chat_dashboard.basic_auth_logic as bal
        bal._basic_client_cache.clear()
    except (ImportError, AttributeError):
        pass



# ============================================
# アプリ・クライアント Fixtures
# ============================================

@pytest.fixture
def app():
    """FastAPIアプリケーションインスタンス

    main.py の最終 app は DecryptionMiddleware(fastapi_app, ...) でラップされている。
    テストでは内部の FastAPI インスタンスを直接使用し、
    lifespan を空の noop に差し替えて接続待ちによるカードを回避する。
    """
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _noop_lifespan(app):
        yield

    import app as app_module
    # main モジュールをリロードしないよう、既にインポート済みなら再利用
    import importlib
    main_mod = importlib.import_module("app.main")

    # DecryptionMiddleware の内部 FastAPI インスタンスを取得
    # DecryptionMiddleware(fastapi_app, ...) → middleware.app が FastAPI インスタンス
    outer = main_mod.app
    if hasattr(outer, "app"):
        fastapi_app = outer.app  # ミドルウェアから内部 FastAPI を取り出す
    else:
        fastapi_app = outer  # 既に FastAPI インスタンスの場合

    # lifespan を noop に差し替えてネットワーク接続をスキップ
    fastapi_app.router.lifespan_context = _noop_lifespan
    return fastapi_app


@pytest_asyncio.fixture
async def client(app):
    """非認証HTTPクライアント"""
    from httpx import AsyncClient, ASGITransport
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as c:
        yield c


@pytest_asyncio.fixture
async def authenticated_client(app, mock_simple_chatbot):
    """認証済みHTTPクライアント（simple_chat_with_basic_authモック付き）"""
    from httpx import AsyncClient, ASGITransport
    with patch("app.chat_dashboard.router.extract_basic_auth_token") as mock_extract, \
         patch("app.chat_dashboard.router.validate_auth_requirements"):
        mock_extract.return_value = "test-token"
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as c:
            yield c


# ============================================
# モック Fixtures
# ============================================

@pytest.fixture
def mock_simple_chatbot():
    """simple_chat_with_basic_auth 関数全体の AsyncMock"""
    with patch(
        "app.chat_dashboard.router.simple_chat_with_basic_auth",
        new_callable=AsyncMock
    ) as mock_func:
        mock_func.return_value = "モック応答"
        yield mock_func


@pytest.fixture
def mock_llm():
    """LLMモック"""
    mock = MagicMock()
    mock.ainvoke = AsyncMock()
    mock.bind_tools = MagicMock(return_value=mock)
    return mock


@pytest.fixture
def mock_llm_with_tool_calls():
    """ツール呼び出し付きLLMモック"""
    mock = MagicMock()
    tool_response = MagicMock()
    tool_response.content = ""
    tool_response.tool_calls = [
        {
            "name": "compare_scan_violations",
            "args": {"current_scan_id": "scan-001", "time_reference": "前回"},
            "id": "tool-call-001"
        }
    ]
    mock.ainvoke = AsyncMock(return_value=tool_response)
    mock.bind_tools = MagicMock(return_value=mock)
    return mock


@pytest.fixture
def mock_tools():
    """チャットツールモック"""
    with patch("app.chat_dashboard.chat_tools.compare_scan_violations") as mock_compare, \
         patch("app.chat_dashboard.chat_tools.get_scan_info") as mock_info, \
         patch("app.chat_dashboard.chat_tools.get_resource_details") as mock_details, \
         patch("app.chat_dashboard.chat_tools.get_policy_recommendations") as mock_recs:
        mock_compare.ainvoke = AsyncMock(return_value="比較結果")
        mock_info.ainvoke = AsyncMock(return_value="スキャン情報")
        mock_details.ainvoke = AsyncMock(return_value="リソース詳細")
        mock_recs.ainvoke = AsyncMock(return_value="推奨事項")
        yield {
            "compare_scan_violations": mock_compare,
            "get_scan_info": mock_info,
            "get_resource_details": mock_details,
            "get_policy_recommendations": mock_recs
        }


@pytest.fixture
def chat_history():
    """ChatHistoryインスタンス"""
    from app.chat_dashboard.simple_chat_handler import ChatHistory
    return ChatHistory()


@pytest.fixture
def chat_history_with_limit():
    """制限付きChatHistory（max_messages=20）"""
    from app.chat_dashboard.simple_chat_handler import ChatHistory
    return ChatHistory(max_messages=20)


@pytest.fixture
def mock_opensearch_settings():
    """OpenSearch設定モック"""
    with patch("app.chat_dashboard.basic_auth_logic.settings") as mock_settings:
        mock_settings.OPENSEARCH_URL = "https://localhost:9200"
        mock_settings.OPENSEARCH_CA_CERTS_PATH = None
        with patch("app.chat_dashboard.basic_auth_logic.is_aws_opensearch_service") as mock_aws:
            mock_aws.return_value = False
            yield mock_settings


# ============================================
# 测试结果收集器
# ============================================

class TestResultCollector:
    def __init__(self):
        self.results = {"normal": [], "error": [], "security": []}
        self.start_time = datetime.now()

    def add_result(self, nodeid: str, outcome: str, duration: float):
        test_name = nodeid.split("::")[-1]
        if "Security" in nodeid or "_sec_" in test_name.lower():
            cat = "security"
        elif "Error" in nodeid or "error" in test_name.lower() or "E0" in test_name:
            cat = "error"
        else:
            cat = "normal"
        self.results[cat].append({"test_id": test_name, "outcome": outcome, "duration": duration})

    def generate_markdown_report(self, output_path: Path):
        total = sum(len(v) for v in self.results.values())
        passed = sum(1 for cat in self.results.values() for r in cat if r["outcome"] == "passed")
        failed = total - passed
        rate = f"{passed/total*100:.1f}%" if total > 0 else "N/A"
        lines = [
            "# Chat Dashboard 测试报告\n",
            "| 项目 | 值 |",
            "|------|-----|",
            f"| 测试对象 | `app/chat_dashboard/router.py` |",
            f"| 执行时间 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |",
            f"| 覆盖率目标 | 85% |\n",
            "| 类别 | 总数 | 通过 | 失败 |",
            "|------|------|------|------|",
        ]
        for cat, label in [("normal","正常系"),("error","异常系"),("security","安全测试")]:
            r = self.results[cat]
            p = sum(1 for x in r if x["outcome"] == "passed")
            lines.append(f"| {label} | {len(r)} | {p} | {len(r)-p} |")
        lines.append(f"| **合计** | **{total}** | **{passed}** | **{failed}** |\n")
        lines.append(f"**通过率**: {rate}\n")
        for cat, label in [("normal","正常系"),("error","异常系"),("security","安全测试")]:
            lines.append(f"\n## {label}测试详情\n| 测试名称 | 结果 | 执行时间 |\n|---------|------|----------|")
            for r in self.results[cat]:
                s = "✅" if r["outcome"] == "passed" else "❌"
                lines.append(f"| {r['test_id']} | {s} | {r['duration']:.3f}s |")
        lines.append(f"\n---\n*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        output_path.write_text("\n".join(lines), encoding="utf-8")

    def generate_json_report(self, output_path: Path):
        total = sum(len(v) for v in self.results.values())
        passed = sum(1 for cat in self.results.values() for r in cat if r["outcome"] == "passed")
        report = {
            "summary": {"total": total, "passed": passed, "failed": total-passed,
                        "pass_rate": f"{passed/total*100:.1f}%" if total > 0 else "N/A"},
            "categories": self.results,
            "execution_time": datetime.now().isoformat()
        }
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call":
        item.session.config._test_collector.add_result(item.nodeid, rep.outcome, rep.duration)


def pytest_sessionstart(session):
    session.config._test_collector = TestResultCollector()


def pytest_sessionfinish(session, exitstatus):
    collector = session.config._test_collector
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    collector.generate_markdown_report(reports_dir / "TestReport_chat_dashboard.md")
    collector.generate_json_report(reports_dir / "TestReport_chat_dashboard.json")

