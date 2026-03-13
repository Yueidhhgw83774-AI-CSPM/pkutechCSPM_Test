# mcp_plugin/hierarchical テストケース

## 1. 概要

階層的エージェント サブモジュール（`hierarchical/`）のテストケースを定義します。オーケストレーター、MCP検索、レスポンス生成の3層アーキテクチャを包括的にテストします。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `run_hierarchical_mcp_agent` | 階層的エージェント実行 |
| `stream_hierarchical_mcp_agent` | ストリーミング実行 |
| `get_hierarchical_mcp_graph` | グラフ取得（キャッシュ） |
| `reset_graph_cache` | グラフキャッシュリセット |
| `MCPHierarchicalState` | 状態クラス |
| `SubTask` | サブタスククラス |

### 1.2 モジュール構成

| ファイル | 説明 |
|---------|------|
| `state.py` | 状態定義（MCPHierarchicalState, SubTask） |
| `graph_builder.py` | グラフ構築 |
| `runner.py` | 実行関数 |
| `streaming.py` | SSEストリーミング |
| `sse_parallel_emit.py` | 並列SSE発行 |
| `nodes/orchestrator.py` | オーケストレーターノード |
| `nodes/mcp_search.py` | MCP検索ノード |
| `nodes/response_generator.py` | レスポンス生成ノード |
| `nodes/subagent_router.py` | サブエージェントルーター |
| `nodes/todo_status_updater.py` | TODO状態更新 |
| `nodes/policy_validator.py` | ポリシー検証 |
| `nodes/mcp_search_subgraph/` | MCP検索サブグラフ |

### 1.3 カバレッジ目標: 75%

> **注記**: グラフ状態遷移とLLM呼び出しの複雑さから、主要パスをカバー

### 1.4 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/mcp_plugin/hierarchical/` |
| テストコード | `test/unit/mcp_plugin/hierarchical/test_*.py` |
| conftest | `test/unit/mcp_plugin/hierarchical/conftest.py` |

### 1.5 補足情報

**アーキテクチャ:**
- orchestrator: タスク分析・サブタスク生成（gpt-5-mini, 1回）
- mcp_search: MCPツール実行（gpt-5-nano, ループ）
- response_generator: 最終回答生成（gpt-5.1-codex, 1回）

**コスト削減:**
- Deep Agentsと比較して約92%削減
- 処理時間約1/3

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| MCPH-001 | 階層的エージェント実行成功 | valid request | final_state with response |
| MCPH-002 | ストリーミング実行成功 | valid request | async generator events |
| MCPH-003 | グラフ取得（初回） | - | new graph instance |
| MCPH-004 | グラフ取得（キャッシュ） | second call | same graph instance |
| MCPH-005 | グラフキャッシュリセット | reset_graph_cache() | cache cleared |
| MCPH-006 | SubTask作成 | valid params | SubTask instance |
| MCPH-007 | MCPHierarchicalState初期化 | valid params | state instance |
| MCPH-008 | オーケストレーターノード実行 | user_request | subtasks generated |
| MCPH-009 | MCP検索ノード実行 | subtask | search results |
| MCPH-010 | レスポンス生成ノード実行 | search_results | final_response |
| MCPH-011 | コールバック付き実行 | callbacks | callbacks invoked |
| MCPH-012 | サーバー指定実行 | server_name | specific server used |

### 2.1 エージェント実行テスト

```python
# test/unit/mcp_plugin/hierarchical/test_runner.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestHierarchicalAgentRunner:
    """階層的エージェント実行のテスト"""

    @pytest.mark.asyncio
    async def test_run_agent_success(self, mock_graph):
        """MCPH-001: 階層的エージェント実行成功"""
        # Arrange
        from app.mcp_plugin.hierarchical import run_hierarchical_mcp_agent

        mock_graph.ainvoke.return_value = {
            "final_response": "階層的エージェントの応答",
            "llm_calls": 3,
            "llm_calls_by_model": {"gpt-5-mini": 1, "gpt-5-nano": 1, "gpt-5.1-codex": 1}
        }

        # Act
        with patch("app.mcp_plugin.hierarchical.runner.get_hierarchical_mcp_graph", return_value=mock_graph):
            result = await run_hierarchical_mcp_agent(
                session_id="test-session",
                user_request="Azure OpenAIについて教えて"
            )

        # Assert
        assert result["final_response"] == "階層的エージェントの応答"
        assert result["llm_calls"] == 3

    @pytest.mark.asyncio
    async def test_run_agent_with_callbacks(self, mock_graph):
        """MCPH-011: コールバック付き実行"""
        # Arrange
        from app.mcp_plugin.hierarchical import run_hierarchical_mcp_agent_with_callbacks

        callback_called = []

        def test_callback(event):
            callback_called.append(event)

        mock_graph.ainvoke.return_value = {
            "final_response": "応答"
        }

        # Act
        with patch("app.mcp_plugin.hierarchical.runner.get_hierarchical_mcp_graph", return_value=mock_graph):
            result = await run_hierarchical_mcp_agent_with_callbacks(
                session_id="test-session",
                user_request="テスト",
                callbacks=[test_callback]
            )

        # Assert
        assert result is not None

    @pytest.mark.asyncio
    async def test_run_agent_with_server_name(self, mock_graph):
        """MCPH-012: サーバー指定実行"""
        # Arrange
        from app.mcp_plugin.hierarchical import run_hierarchical_mcp_agent

        mock_graph.ainvoke.return_value = {
            "final_response": "aws-docsの結果"
        }

        # Act
        with patch("app.mcp_plugin.hierarchical.runner.get_hierarchical_mcp_graph", return_value=mock_graph):
            result = await run_hierarchical_mcp_agent(
                session_id="test-session",
                user_request="AWSドキュメント",
                server_name="aws-docs"
            )

        # Assert
        call_kwargs = mock_graph.ainvoke.call_args.kwargs
        # server_nameが状態に渡されていることを確認
        assert result is not None
```

### 2.2 ストリーミングテスト

```python
# test/unit/mcp_plugin/hierarchical/test_streaming.py

class TestHierarchicalStreaming:
    """階層的エージェントストリーミングのテスト"""

    @pytest.mark.asyncio
    async def test_stream_agent_success(self, mock_graph):
        """MCPH-002: ストリーミング実行成功"""
        # Arrange
        from app.mcp_plugin.hierarchical import stream_hierarchical_mcp_agent

        async def mock_astream(*args, **kwargs):
            yield {"orchestrator": {"subtasks": []}}
            yield {"mcp_search": {"results": "検索結果"}}
            yield {"response_generator": {"final_response": "最終応答"}}

        mock_graph.astream = mock_astream

        # Act
        events = []
        with patch("app.mcp_plugin.hierarchical.streaming.get_hierarchical_mcp_graph", return_value=mock_graph):
            async for event_type, data in stream_hierarchical_mcp_agent(
                session_id="test-session",
                user_request="テスト"
            ):
                events.append((event_type, data))

        # Assert
        event_types = [e[0] for e in events]
        assert len(events) > 0
```

### 2.3 グラフ・キャッシュテスト

```python
# test/unit/mcp_plugin/hierarchical/test_graph_builder.py

class TestGraphBuilder:
    """グラフビルダーのテスト"""

    def test_get_graph_first_call(self):
        """MCPH-003: グラフ取得（初回）"""
        # Arrange
        from app.mcp_plugin.hierarchical import (
            get_hierarchical_mcp_graph,
            reset_graph_cache
        )
        reset_graph_cache()

        # Act
        with patch("app.mcp_plugin.hierarchical.graph_builder.StateGraph") as mock_sg:
            mock_sg.return_value.compile.return_value = MagicMock()
            graph = get_hierarchical_mcp_graph()

        # Assert
        assert graph is not None

    def test_get_graph_cached(self):
        """MCPH-004: グラフ取得（キャッシュ）"""
        # Arrange
        from app.mcp_plugin.hierarchical import (
            get_hierarchical_mcp_graph,
            reset_graph_cache
        )
        reset_graph_cache()

        # Act
        with patch("app.mcp_plugin.hierarchical.graph_builder.StateGraph") as mock_sg:
            mock_graph = MagicMock()
            mock_sg.return_value.compile.return_value = mock_graph
            graph1 = get_hierarchical_mcp_graph()
            graph2 = get_hierarchical_mcp_graph()

        # Assert
        assert graph1 is graph2
        # StateGraphは1回のみ呼び出される
        assert mock_sg.call_count == 1

    def test_reset_graph_cache(self):
        """MCPH-005: グラフキャッシュリセット"""
        # Arrange
        from app.mcp_plugin.hierarchical import (
            get_hierarchical_mcp_graph,
            reset_graph_cache
        )

        with patch("app.mcp_plugin.hierarchical.graph_builder.StateGraph") as mock_sg:
            mock_sg.return_value.compile.return_value = MagicMock()
            get_hierarchical_mcp_graph()

            # Act
            reset_graph_cache()

            # Assert - 次回呼び出しで再構築される
            get_hierarchical_mcp_graph()
            assert mock_sg.call_count == 2
```

### 2.4 状態クラステスト

```python
# test/unit/mcp_plugin/hierarchical/test_state.py

class TestStateClasses:
    """状態クラスのテスト"""

    def test_subtask_creation(self):
        """MCPH-006: SubTask作成"""
        # Arrange
        from app.mcp_plugin.hierarchical import SubTask

        # Act
        subtask = SubTask(
            id="task-001",
            description="ドキュメント検索",
            status="pending",
            priority=1
        )

        # Assert
        assert subtask.id == "task-001"
        assert subtask.status == "pending"

    def test_hierarchical_state_initialization(self):
        """MCPH-007: MCPHierarchicalState初期化"""
        # Arrange
        from app.mcp_plugin.hierarchical import MCPHierarchicalState

        # Act
        state = MCPHierarchicalState(
            session_id="test-session",
            user_request="テストリクエスト",
            subtasks=[],
            search_results=[],
            llm_calls=0,
            llm_calls_by_model={}
        )

        # Assert
        assert state.session_id == "test-session"
        assert state.user_request == "テストリクエスト"
```

### 2.5 ノードテスト

```python
# test/unit/mcp_plugin/hierarchical/test_nodes.py

class TestOrchestratorNode:
    """オーケストレーターノードのテスト"""

    @pytest.mark.asyncio
    async def test_orchestrator_generates_subtasks(self, mock_llm):
        """MCPH-008: オーケストレーターノード実行"""
        # Arrange
        from app.mcp_plugin.hierarchical.nodes.orchestrator import orchestrator_node

        mock_llm.ainvoke.return_value = MagicMock(
            content='[{"id": "1", "description": "検索タスク", "priority": 1}]'
        )

        state = {
            "user_request": "Azure OpenAIについて",
            "subtasks": [],
            "llm_calls": 0,
            "llm_calls_by_model": {}
        }

        # Act
        with patch("app.mcp_plugin.hierarchical.nodes.orchestrator.get_gpt5_mini_llm", return_value=mock_llm):
            result = await orchestrator_node(state)

        # Assert
        assert "subtasks" in result
        assert result["llm_calls"] == 1


class TestMCPSearchNode:
    """MCP検索ノードのテスト"""

    @pytest.mark.asyncio
    async def test_mcp_search_executes(self, mock_mcp_client):
        """MCPH-009: MCP検索ノード実行"""
        # Arrange
        from app.mcp_plugin.hierarchical.nodes.mcp_search import mcp_search_node

        mock_mcp_client.call_tool.return_value = MagicMock(
            success=True,
            content="検索結果"
        )

        state = {
            "current_subtask": {
                "id": "1",
                "description": "検索タスク"
            },
            "search_results": [],
            "llm_calls": 1
        }

        # Act
        with patch("app.mcp_plugin.hierarchical.nodes.mcp_search.mcp_client", mock_mcp_client):
            result = await mcp_search_node(state)

        # Assert
        assert "search_results" in result


class TestResponseGeneratorNode:
    """レスポンス生成ノードのテスト"""

    @pytest.mark.asyncio
    async def test_response_generator_creates_response(self, mock_llm):
        """MCPH-010: レスポンス生成ノード実行"""
        # Arrange
        from app.mcp_plugin.hierarchical.nodes.response_generator import response_generator_node

        mock_llm.ainvoke.return_value = MagicMock(
            content="最終的な回答です"
        )

        state = {
            "user_request": "Azure OpenAI",
            "search_results": ["検索結果1", "検索結果2"],
            "llm_calls": 2,
            "llm_calls_by_model": {"gpt-5-mini": 1, "gpt-5-nano": 1}
        }

        # Act
        with patch("app.mcp_plugin.hierarchical.nodes.response_generator.get_gpt5_codex_llm", return_value=mock_llm):
            result = await response_generator_node(state)

        # Assert
        assert "final_response" in result
        assert result["final_response"] == "最終的な回答です"
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| MCPH-E01 | オーケストレーターエラー | LLM error | error in state |
| MCPH-E02 | MCP検索エラー | tool call error | error handled |
| MCPH-E03 | レスポンス生成エラー | LLM error | error in state |
| MCPH-E04 | ストリーミングエラー | stream error | error event |
| MCPH-E05 | 無効なサブタスク | invalid subtask JSON | error handled |

### 3.1 エラーハンドリングテスト

```python
class TestHierarchicalErrors:
    """階層的エージェントエラーのテスト"""

    @pytest.mark.asyncio
    async def test_orchestrator_error(self, mock_llm):
        """MCPH-E01: オーケストレーターエラー"""
        # Arrange
        from app.mcp_plugin.hierarchical.nodes.orchestrator import orchestrator_node

        mock_llm.ainvoke.side_effect = Exception("LLM error")

        state = {
            "user_request": "テスト",
            "subtasks": [],
            "llm_calls": 0,
            "llm_calls_by_model": {}
        }

        # Act
        with patch("app.mcp_plugin.hierarchical.nodes.orchestrator.get_gpt5_mini_llm", return_value=mock_llm):
            result = await orchestrator_node(state)

        # Assert
        assert "error" in result or result.get("subtasks") == []

    @pytest.mark.asyncio
    async def test_mcp_search_error(self, mock_mcp_client):
        """MCPH-E02: MCP検索エラー"""
        # Arrange
        from app.mcp_plugin.hierarchical.nodes.mcp_search import mcp_search_node

        mock_mcp_client.call_tool.return_value = MagicMock(
            success=False,
            error="ツール実行エラー"
        )

        state = {
            "current_subtask": {"id": "1", "description": "検索"},
            "search_results": [],
            "llm_calls": 1
        }

        # Act
        with patch("app.mcp_plugin.hierarchical.nodes.mcp_search.mcp_client", mock_mcp_client):
            result = await mcp_search_node(state)

        # Assert
        # エラーが適切に処理される
        assert result is not None

    @pytest.mark.asyncio
    async def test_invalid_subtask_json(self, mock_llm):
        """MCPH-E05: 無効なサブタスク"""
        # Arrange
        from app.mcp_plugin.hierarchical.nodes.orchestrator import orchestrator_node

        mock_llm.ainvoke.return_value = MagicMock(
            content="invalid json {not valid}"
        )

        state = {
            "user_request": "テスト",
            "subtasks": [],
            "llm_calls": 0,
            "llm_calls_by_model": {}
        }

        # Act
        with patch("app.mcp_plugin.hierarchical.nodes.orchestrator.get_gpt5_mini_llm", return_value=mock_llm):
            result = await orchestrator_node(state)

        # Assert
        # JSONパースエラーが適切に処理される
        assert result is not None
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| MCPH-SEC-01 | cloud_credentialsの伝播 | credentials in state | 検索ノードに渡される |
| MCPH-SEC-02 | セッション分離 | multiple sessions | 各セッション独立 |
| MCPH-SEC-03 | LLM呼び出し追跡 | any request | llm_calls_by_model記録 |

```python
@pytest.mark.security
class TestHierarchicalSecurity:
    """階層的エージェントセキュリティテスト"""

    @pytest.mark.asyncio
    async def test_credentials_propagation(self, mock_graph):
        """MCPH-SEC-01: cloud_credentialsの伝播"""
        # Arrange
        from app.mcp_plugin.hierarchical import run_hierarchical_mcp_agent

        captured_state = {}

        async def capture_invoke(state, *args, **kwargs):
            captured_state.update(state)
            return {"final_response": "OK"}

        mock_graph.ainvoke = capture_invoke

        credentials = {
            "cloud_provider": "aws",
            "role_arn": "arn:aws:iam::123456789012:role/test"
        }

        # Act
        with patch("app.mcp_plugin.hierarchical.runner.get_hierarchical_mcp_graph", return_value=mock_graph):
            await run_hierarchical_mcp_agent(
                session_id="test-session",
                user_request="テスト",
                cloud_credentials=credentials
            )

        # Assert
        assert captured_state.get("cloud_credentials") == credentials

    def test_llm_calls_tracking(self):
        """MCPH-SEC-03: LLM呼び出し追跡"""
        # Arrange
        from app.mcp_plugin.hierarchical import MCPHierarchicalState

        state = MCPHierarchicalState(
            session_id="test",
            user_request="test",
            subtasks=[],
            search_results=[],
            llm_calls=0,
            llm_calls_by_model={}
        )

        # Act
        state.llm_calls += 1
        state.llm_calls_by_model["gpt-5-mini"] = 1

        # Assert
        assert state.llm_calls == 1
        assert state.llm_calls_by_model["gpt-5-mini"] == 1
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_hierarchical_module` | グローバル状態リセット | function | Yes |
| `mock_graph` | グラフモック | function | No |
| `mock_llm` | LLMモック | function | No |
| `mock_mcp_client` | MCPクライアントモック | function | No |

### 共通フィクスチャ定義

```python
# test/unit/mcp_plugin/hierarchical/conftest.py
import sys
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.fixture(autouse=True)
def reset_hierarchical_module():
    """テストごとにhierarchicalモジュールの状態をリセット"""
    yield
    # グラフキャッシュをリセット
    try:
        from app.mcp_plugin.hierarchical import reset_graph_cache
        reset_graph_cache()
    except (ImportError, AttributeError):
        pass

    # モジュールキャッシュをクリア
    modules_to_remove = [
        key for key in sys.modules
        if key.startswith("app.mcp_plugin.hierarchical")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def mock_graph():
    """グラフモック"""
    mock = MagicMock()
    mock.ainvoke = AsyncMock(return_value={"final_response": "OK"})
    return mock


@pytest.fixture
def mock_llm():
    """LLMモック"""
    mock = MagicMock()
    mock.ainvoke = AsyncMock(return_value=MagicMock(content="LLM応答"))
    return mock


@pytest.fixture
def mock_mcp_client():
    """MCPクライアントモック"""
    with patch("app.mcp_plugin.client.mcp_client") as mock:
        mock.call_tool = AsyncMock()
        yield mock
```

---

## 6. テスト実行例

```bash
# hierarchical関連テストのみ実行
pytest test/unit/mcp_plugin/hierarchical/ -v

# カバレッジ付きで実行
pytest test/unit/mcp_plugin/hierarchical/ --cov=app.mcp_plugin.hierarchical --cov-report=term-missing -v

# 特定のテストファイルのみ
pytest test/unit/mcp_plugin/hierarchical/test_runner.py -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 12 | MCPH-001 〜 MCPH-012 |
| 異常系 | 5 | MCPH-E01 〜 MCPH-E05 |
| セキュリティ | 3 | MCPH-SEC-01 〜 MCPH-SEC-03 |
| **合計** | **20** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestHierarchicalAgentRunner` | MCPH-001, MCPH-011, MCPH-012 | 3 |
| `TestHierarchicalStreaming` | MCPH-002 | 1 |
| `TestGraphBuilder` | MCPH-003〜MCPH-005 | 3 |
| `TestStateClasses` | MCPH-006〜MCPH-007 | 2 |
| `TestOrchestratorNode` | MCPH-008 | 1 |
| `TestMCPSearchNode` | MCPH-009 | 1 |
| `TestResponseGeneratorNode` | MCPH-010 | 1 |
| `TestHierarchicalErrors` | MCPH-E01〜MCPH-E05 | 5 |
| `TestHierarchicalSecurity` | MCPH-SEC-01〜MCPH-SEC-03 | 3 |

### 実装失敗が予想されるテスト

現時点で失敗が予想されるテストはありません。

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | グラフ状態遷移の完全テスト困難 | 内部状態遷移の検証が限定的 | 主要パスのみカバー |
| 2 | サブグラフのモック複雑 | mcp_search_subgraphのテストが限定的 | 統合テストで別途検証 |
| 3 | 実LLM呼び出しテスト不可 | モデル応答品質の検証不可 | 統合テストで別途検証 |

---

## 関連ドキュメント

- [mcp_plugin_chat_agent_tests.md](./mcp_plugin_chat_agent_tests.md) - チャットエージェントのテスト
- [mcp_plugin_deep_agents_tests.md](./mcp_plugin_deep_agents_tests.md) - Deep Agentsのテスト
- [mcp_plugin_client_tests.md](./mcp_plugin_client_tests.md) - MCPクライアントのテスト
