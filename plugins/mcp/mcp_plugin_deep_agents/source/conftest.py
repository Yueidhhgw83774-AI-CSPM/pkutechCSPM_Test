# TestReport/plugins/mcp/mcp_plugin_deep_agents/source/conftest.py
"""
Deep Agents テスト用共通フィクスチャ

テスト要件: mcp_plugin_deep_agents_tests.md
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# Add platform_python_backend-testing to Python path
# conftest.py -> source -> mcp_plugin_deep_agents -> mcp -> plugins -> TestReport -> python_ai_cspm
backend_path = Path(__file__).resolve().parents[5] / "platform_python_backend-testing"
if backend_path.exists() and str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))


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

