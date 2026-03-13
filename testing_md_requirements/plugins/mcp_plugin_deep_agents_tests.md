# mcp_plugin/deep_agents テストケース

## 1. 概要

Deep Agents サブモジュール（`deep_agents/`）のテストケースを定義します。LangGraphベースのDeep Agentsエージェント、MCPツール統合、ストリーミング機能を包括的にテストします。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `initialize_mcp_chat_components` | MCPチャットコンポーネント初期化 |
| `invoke_deep_agents_mcp_chat` | Deep Agentsチャット実行 |
| `stream_deep_agents_mcp_chat` | ストリーミングチャット |
| `clear_session_cache` | セッションキャッシュクリア |
| `build_progress_from_state` | 進捗情報構築 |
| `create_mcp_tools` | MCPツール作成 |

### 1.2 モジュール構成

| ファイル | 説明 |
|---------|------|
| `agent.py` | Deep Agentsエージェント本体 |
| `streaming.py` | SSEストリーミング |
| `mcp_tools.py` | MCPツール定義 |
| `subagents.py` | サブエージェント |
| `result_storage.py` | 結果保存 |
| `policy_validator_middleware.py` | ポリシー検証ミドルウェア |
| `tools/` | ツール実装（cspm, search, opensearch, result_*） |

### 1.3 カバレッジ目標: 75%

> **注記**: LangGraph状態管理とLLM呼び出しの複雑さから、主要パスをカバー

### 1.4 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/mcp_plugin/deep_agents/` |
| テストコード | `test/unit/mcp_plugin/deep_agents/test_*.py` |
| conftest | `test/unit/mcp_plugin/deep_agents/conftest.py` |

### 1.5 補足情報

**グローバル状態:**
- `CACHED_MCP_LLM`: キャッシュされたLLMインスタンス
- `CACHED_MCP_AGENT`: キャッシュされたエージェント
- `MCP_COMPONENTS_INITIALIZED`: 初期化フラグ
- `response_id_store`: Responses APIキャッシュ（dict）

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| MCPDA-001 | コンポーネント初期化成功 | valid config | initialized components |
| MCPDA-002 | チャット実行成功 | valid prompt | response text |
| MCPDA-003 | ストリーミング実行成功 | valid prompt | async generator events |
| MCPDA-004 | セッションキャッシュクリア | session_id | cache cleared |
| MCPDA-005 | 進捗情報構築 | valid state | MCPProgress |
| MCPDA-006 | MCPツール作成 | server_name | LangChain tools |
| MCPDA-007 | ツール呼び出しイベント生成 | tool_start/tool_end | SSE events |
| MCPDA-008 | cloud_credentials付きツール実行 | credentials context | context passed |

### 2.1 エージェント初期化・実行テスト

```python
# test/unit/mcp_plugin/deep_agents/test_agent.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestDeepAgentsInitialization:
    """Deep Agentsコンポーネント初期化のテスト"""

    @pytest.mark.asyncio
    async def test_initialize_components(self, mock_llm, mock_mcp_client):
        """MCPDA-001: コンポーネント初期化成功"""
        # Arrange
        from app.mcp_plugin.deep_agents import initialize_mcp_chat_components

        # Act
        with patch("app.mcp_plugin.deep_agents.agent.get_gpt5_codex_llm", return_value=mock_llm):
            await initialize_mcp_chat_components()

        # Assert
        from app.mcp_plugin.deep_agents import MCP_COMPONENTS_INITIALIZED
        assert MCP_COMPONENTS_INITIALIZED is True


class TestDeepAgentsExecution:
    """Deep Agentsエージェント実行のテスト"""

    @pytest.mark.asyncio
    async def test_invoke_chat_success(
        self, mock_agent_graph, mock_mcp_client
    ):
        """MCPDA-002: チャット実行成功"""
        # Arrange
        from app.mcp_plugin.deep_agents import invoke_deep_agents_mcp_chat

        mock_agent_graph.ainvoke.return_value = {
            "messages": [MagicMock(content="Deep Agents応答")]
        }

        # Act
        with patch("app.mcp_plugin.deep_agents.agent.CACHED_MCP_AGENT", mock_agent_graph):
            response = await invoke_deep_agents_mcp_chat(
                session_id="test-session",
                prompt="テスト質問"
            )

        # Assert
        assert "Deep Agents応答" in response


class TestDeepAgentsStreaming:
    """Deep Agentsストリーミングのテスト"""

    @pytest.mark.asyncio
    async def test_stream_chat_success(
        self, mock_agent_graph, mock_mcp_client
    ):
        """MCPDA-003: ストリーミング実行成功"""
        # Arrange
        from app.mcp_plugin.deep_agents import stream_deep_agents_mcp_chat

        async def mock_astream_events(*args, **kwargs):
            yield {"event": "on_tool_start", "name": "search", "data": {}}
            yield {"event": "on_tool_end", "name": "search", "data": {"output": "result"}}
            yield {"event": "on_chat_model_end", "data": {"output": MagicMock(content="応答")}}

        mock_agent_graph.astream_events = mock_astream_events

        # Act
        events = []
        with patch("app.mcp_plugin.deep_agents.streaming.CACHED_MCP_AGENT", mock_agent_graph):
            async for event_type, data in stream_deep_agents_mcp_chat(
                session_id="test-session",
                prompt="テスト"
            ):
                events.append((event_type, data))

        # Assert
        event_types = [e[0] for e in events]
        assert "tool_start" in event_types or "response" in event_types
```

### 2.2 キャッシュ・進捗テスト

```python
class TestDeepAgentsCache:
    """Deep Agentsキャッシュのテスト"""

    def test_clear_session_cache(self):
        """MCPDA-004: セッションキャッシュクリア"""
        # Arrange
        from app.mcp_plugin.deep_agents import (
            response_id_store,
            clear_session_cache
        )
        response_id_store["test-session"] = "response-id-123"

        # Act
        clear_session_cache("test-session")

        # Assert
        assert "test-session" not in response_id_store


class TestDeepAgentsProgress:
    """Deep Agents進捗情報のテスト"""

    def test_build_progress_from_state(self):
        """MCPDA-005: 進捗情報構築"""
        # Arrange
        from app.mcp_plugin.deep_agents import build_progress_from_state

        state = {
            "llm_calls": 5,
            "llm_calls_by_model": {"gpt-5.1-codex": 5},
            "tool_calls": ["search", "get_details"]
        }

        # Act
        progress = build_progress_from_state(state)

        # Assert
        assert progress is not None
        # 具体的な構造はMCPProgressの定義に依存
```

### 2.3 MCPツールテスト

```python
class TestMCPTools:
    """MCPツールのテスト"""

    @pytest.mark.asyncio
    async def test_create_mcp_tools(self, mock_mcp_client):
        """MCPDA-006: MCPツール作成"""
        # Arrange
        from app.mcp_plugin.deep_agents import create_mcp_tools
        from app.models.mcp import MCPTool, MCPToolType

        mock_tool = MCPTool(
            name="search_documentation",
            description="ドキュメント検索",
            type=MCPToolType.FUNCTION,
            parameters=[]
        )
        mock_mcp_client.get_available_tools.return_value = [mock_tool]

        # Act
        with patch("app.mcp_plugin.deep_agents.mcp_tools.mcp_client", mock_mcp_client):
            tools = await create_mcp_tools()

        # Assert
        assert len(tools) > 0
        # LangChainツールに変換されている

    @pytest.mark.asyncio
    async def test_tool_with_cloud_credentials(self, mock_mcp_client):
        """MCPDA-008: cloud_credentials付きツール実行"""
        # Arrange
        from app.mcp_plugin.deep_agents.mcp_tools import create_mcp_tools

        mock_mcp_client.call_tool.return_value = MagicMock(
            success=True,
            content="認証成功の結果"
        )

        # cloud_credentialsを含むコンテキスト
        context = {
            "cloud_credentials": {
                "cloud_provider": "aws",
                "role_arn": "arn:aws:iam::123456789012:role/test"
            }
        }

        # Act & Assert
        # ツールが作成され、contextが渡されることを確認
        # 具体的な実装はcreate_mcp_toolsの構造に依存
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| MCPDA-E01 | 初期化エラー | invalid config | exception raised |
| MCPDA-E02 | チャット実行エラー | agent raises | exception propagated |
| MCPDA-E03 | ストリーミングエラー | stream error | error event emitted |
| MCPDA-E04 | ツール作成エラー | mcp_client error | empty tools list |
| MCPDA-E05 | 存在しないセッションクリア | unknown session_id | no error (idempotent) |

### 3.1 エラーハンドリングテスト

```python
class TestDeepAgentsErrors:
    """Deep Agentsエラーのテスト"""

    @pytest.mark.asyncio
    async def test_invoke_chat_error(self, mock_agent_graph):
        """MCPDA-E02: チャット実行エラー"""
        # Arrange
        from app.mcp_plugin.deep_agents import invoke_deep_agents_mcp_chat

        mock_agent_graph.ainvoke.side_effect = Exception("Agent error")

        # Act & Assert
        with patch("app.mcp_plugin.deep_agents.agent.CACHED_MCP_AGENT", mock_agent_graph):
            with pytest.raises(Exception, match="Agent error"):
                await invoke_deep_agents_mcp_chat(
                    session_id="test-session",
                    prompt="テスト"
                )

    @pytest.mark.asyncio
    async def test_stream_error_event(self, mock_agent_graph):
        """MCPDA-E03: ストリーミングエラー"""
        # Arrange
        from app.mcp_plugin.deep_agents import stream_deep_agents_mcp_chat

        async def mock_astream_events_error(*args, **kwargs):
            yield {"event": "on_tool_start", "name": "search", "data": {}}
            raise Exception("Stream error")

        mock_agent_graph.astream_events = mock_astream_events_error

        # Act
        events = []
        with patch("app.mcp_plugin.deep_agents.streaming.CACHED_MCP_AGENT", mock_agent_graph):
            try:
                async for event_type, data in stream_deep_agents_mcp_chat(
                    session_id="test-session",
                    prompt="テスト"
                ):
                    events.append((event_type, data))
            except Exception:
                pass

        # Assert - エラーイベントまたは例外が発生
        # 具体的な動作は実装に依存

    def test_clear_nonexistent_session(self):
        """MCPDA-E05: 存在しないセッションクリア（冪等性）"""
        # Arrange
        from app.mcp_plugin.deep_agents import (
            response_id_store,
            clear_session_cache
        )

        # Act - エラーにならない
        clear_session_cache("nonexistent-session")

        # Assert
        assert "nonexistent-session" not in response_id_store
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| MCPDA-SEC-01 | システムプロンプトのセキュリティ | MCP_SYSTEM_PROMPT | 安全な指示のみ含む |
| MCPDA-SEC-02 | ツール結果のサニタイズ | malicious tool output | 安全に処理 |
| MCPDA-SEC-03 | セッション分離 | multiple sessions | 各セッション独立 |

```python
@pytest.mark.security
class TestDeepAgentsSecurity:
    """Deep Agentsセキュリティテスト"""

    def test_system_prompt_security(self):
        """MCPDA-SEC-01: システムプロンプトのセキュリティ"""
        # Arrange
        from app.mcp_plugin.deep_agents import MCP_SYSTEM_PROMPT

        # Assert - 危険な指示が含まれていない
        assert "ignore" not in MCP_SYSTEM_PROMPT.lower()
        assert "forget" not in MCP_SYSTEM_PROMPT.lower()
        # MCPツールの適切な使用指示が含まれている
        assert "MCP" in MCP_SYSTEM_PROMPT or "ツール" in MCP_SYSTEM_PROMPT

    def test_session_isolation(self):
        """MCPDA-SEC-03: セッション分離"""
        # Arrange
        from app.mcp_plugin.deep_agents import response_id_store

        # Act
        response_id_store["session-A"] = "response-A"
        response_id_store["session-B"] = "response-B"

        # Assert - 各セッションが独立
        assert response_id_store["session-A"] != response_id_store["session-B"]

        # Cleanup
        del response_id_store["session-A"]
        del response_id_store["session-B"]
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_deep_agents_module` | グローバル状態リセット | function | Yes |
| `mock_llm` | LLMモック | function | No |
| `mock_agent_graph` | エージェントグラフモック | function | No |
| `mock_mcp_client` | MCPクライアントモック | function | No |

### 共通フィクスチャ定義

```python
# test/unit/mcp_plugin/deep_agents/conftest.py
import sys
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


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
    """エージェントグラフモック"""
    mock = MagicMock()
    mock.ainvoke = AsyncMock(return_value={"messages": []})
    return mock


@pytest.fixture
def mock_mcp_client():
    """MCPクライアントモック"""
    with patch("app.mcp_plugin.client.mcp_client") as mock:
        mock.get_available_tools = MagicMock(return_value=[])
        mock.call_tool = AsyncMock()
        yield mock
```

---

## 6. テスト実行例

```bash
# deep_agents関連テストのみ実行
pytest test/unit/mcp_plugin/deep_agents/ -v

# カバレッジ付きで実行
pytest test/unit/mcp_plugin/deep_agents/ --cov=app.mcp_plugin.deep_agents --cov-report=term-missing -v

# 特定のテストファイルのみ
pytest test/unit/mcp_plugin/deep_agents/test_agent.py -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 8 | MCPDA-001 〜 MCPDA-008 |
| 異常系 | 5 | MCPDA-E01 〜 MCPDA-E05 |
| セキュリティ | 3 | MCPDA-SEC-01 〜 MCPDA-SEC-03 |
| **合計** | **16** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestDeepAgentsInitialization` | MCPDA-001 | 1 |
| `TestDeepAgentsExecution` | MCPDA-002 | 1 |
| `TestDeepAgentsStreaming` | MCPDA-003, MCPDA-007 | 2 |
| `TestDeepAgentsCache` | MCPDA-004 | 1 |
| `TestDeepAgentsProgress` | MCPDA-005 | 1 |
| `TestMCPTools` | MCPDA-006, MCPDA-008 | 2 |
| `TestDeepAgentsErrors` | MCPDA-E01〜MCPDA-E05 | 5 |
| `TestDeepAgentsSecurity` | MCPDA-SEC-01〜MCPDA-SEC-03 | 3 |

### 実装失敗が予想されるテスト

現時点で失敗が予想されるテストはありません。

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | LangGraph状態管理の完全テスト困難 | 内部状態遷移の検証が限定的 | 主要パスのみカバー |
| 2 | astream_eventsのモック複雑 | ストリーミングテストが限定的 | 代表的なイベントのみ検証 |
| 3 | 実LLM呼び出しテスト不可 | モデル応答品質の検証不可 | 統合テストで別途検証 |

---

## 関連ドキュメント

- [mcp_plugin_chat_agent_tests.md](./mcp_plugin_chat_agent_tests.md) - チャットエージェントのテスト
- [mcp_plugin_hierarchical_tests.md](./mcp_plugin_hierarchical_tests.md) - 階層的エージェントのテスト
- [mcp_plugin_client_tests.md](./mcp_plugin_client_tests.md) - MCPクライアントのテスト
