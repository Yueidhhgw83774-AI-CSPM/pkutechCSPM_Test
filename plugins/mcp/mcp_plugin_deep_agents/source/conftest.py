# TestReport/plugins/mcp/mcp_plugin_deep_agents/source/conftest.py
"""
Deep Agents テスト用共通フィクスチャ

テスト要件: mcp_plugin_deep_agents_tests.md
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import pytest
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


@pytest.fixture(autouse=True)
def reset_deep_agents_module():
    """テストごとにdeep_agentsモジュールの状態をリセット"""
    yield
    # グローバル変数をリセット
    try:
        import app.mcp_plugin.deep_agents.agent as agent
        agent.CACHED_MCP_LLM = None
        agent.CACHED_MCP_AGENT = None
        agent.MCP_COMPONENTS_INITIALIZED = False
        agent.response_id_store.clear()
    except (ImportError, AttributeError):
        pass

    # ResultStorageをリセット
    try:
        from app.mcp_plugin.deep_agents.result_storage import ResultStorage
        ResultStorage.get_instance()._results.clear()
    except (ImportError, AttributeError):
        pass

    # モジュールキャッシュをクリア
    modules_to_remove = [
        key for key in sys.modules
        if key.startswith("app.mcp_plugin.deep_agents")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def mock_llm():
    """LLMモック"""
    mock = MagicMock()
    mock.ainvoke = AsyncMock(return_value=MagicMock(content="LLM応答"))
    mock.bind_tools = MagicMock(return_value=mock)
    return mock


@pytest.fixture
def mock_agent_graph():
    """エージェントグラフモック（CompiledGraph互換）"""
    mock = MagicMock()
    mock.ainvoke = AsyncMock(return_value={"messages": []})

    # astream_eventsのデフォルト実装
    async def default_astream_events(*args, **kwargs):
        yield {"event": "on_chat_model_end", "data": {"output": MagicMock(content="応答")}}

    mock.astream_events = default_astream_events
    return mock


@pytest.fixture
def mock_mcp_client():
    """MCPクライアントモック"""
    mock = MagicMock()
    mock.servers = {}
    mock.get_available_tools = MagicMock(return_value=[])
    mock.call_tool = AsyncMock(
        return_value=MagicMock(success=True, content="ツール結果")
    )
    return mock


@pytest.fixture
def mock_existing_message_ids():
    """メッセージID取得のモック（Checkpointer依存を回避）"""
    with patch(
        "app.mcp_plugin.deep_agents.streaming._get_existing_message_ids",
        AsyncMock(return_value=set())
    ):
        yield


# ============================================================================
# テストレポート生成
# ============================================================================

class TestResultCollector:
    """テスト結果を収集してレポートを生成"""
    def __init__(self):
        self.results = {"normal": [], "error": [], "security": []}

    def add_result(self, nodeid: str, outcome: str, duration: float):
        test_name = nodeid.split("::")[-1]
        if "Security" in nodeid:
            cat = "security"
        elif "Error" in nodeid:
            cat = "error"
        else:
            cat = "normal"
        self.results[cat].append({"test_id": test_name, "outcome": outcome, "duration": duration})

    def generate_markdown_report(self, output_path: Path):
        total = sum(len(v) for v in self.results.values())
        passed = sum(1 for cat in self.results.values() for r in cat if r["outcome"] == "passed")
        
        lines = [
            f"# MCP Plugin Deep Agents テストレポート\n",
            f"**生成日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"**通過率**: {passed}/{total} ({(passed/total*100 if total > 0 else 0.0):.1f}%)\n",
            f"\n---\n"
        ]
        
        for cat, label in [("normal", "正常系テスト"), ("error", "異常系テスト"), ("security", "セキュリティテスト")]:
            r = self.results[cat]
            if not r:
                continue
            p = sum(1 for x in r if x["outcome"] == "passed")
            f = len(r) - p
            lines.append(f"\n## {label}: {p}/{len(r)}\n")
            lines.append(f"- ✅ 成功: {p}")
            lines.append(f"- ❌ 失敗: {f}\n")
            
            if f > 0:
                lines.append(f"\n### 失敗したテスト\n")
                for test in r:
                    if test["outcome"] != "passed":
                        lines.append(f"- `{test['test_id']}` ({test['duration']:.3f}s)")
        
        output_path.write_text("\n".join(lines), encoding="utf-8")

    def generate_json_report(self, output_path: Path):
        total = sum(len(v) for v in self.results.values())
        passed = sum(1 for cat in self.results.values() for r in cat if r["outcome"] == "passed")
        report = {
            "summary": {
                "total": total, 
                "passed": passed,
                "failed": total - passed,
                "pass_rate": round(passed/total*100 if total > 0 else 0.0, 2)
            }, 
            "categories": self.results,
            "generated_at": datetime.now().isoformat()
        }
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """各テストの実行結果を収集"""
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call":
        collector = getattr(item.session.config, '_test_collector', None)
        if collector:
            collector.add_result(item.nodeid, rep.outcome, rep.duration)


def pytest_sessionstart(session):
    """テストセッション開始時にコレクターを初期化"""
    session.config._test_collector = TestResultCollector()


def pytest_sessionfinish(session, exitstatus):
    """テストセッション終了時にレポートを生成"""
    collector = getattr(session.config, '_test_collector', None)
    if not collector:
        return
    
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    collector.generate_markdown_report(reports_dir / "TestReport_mcp_plugin_deep_agents.md")
    collector.generate_json_report(reports_dir / "TestReport_mcp_plugin_deep_agents.json")


@pytest.fixture
def mock_result_storage():
    """ResultStorageモック"""
    with patch(
        "app.mcp_plugin.deep_agents.streaming.ResultStorage"
    ) as mock:
        instance = MagicMock()
        instance.store_result = MagicMock()
        instance.get_section_detail = MagicMock(return_value=None)
        instance.clear_session_results = MagicMock()
        mock.get_instance.return_value = instance
        yield instance


@pytest.fixture
def authenticated_client():
    """認証済みクライアントモック（将来のAPI呼び出し用）"""
    mock = MagicMock()
    mock.post = AsyncMock()
    mock.get = AsyncMock()
    return mock

