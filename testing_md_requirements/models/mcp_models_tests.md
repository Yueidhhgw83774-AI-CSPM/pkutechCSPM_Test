# models/mcp テストケース

## 1. 概要

MCP (Model Context Protocol) プラグインで使用されるPydanticモデル定義のテストケースを定義します。ツール定義、サーバー設定、チャットリクエスト/レスポンス、セッション管理など24のモデルを包括的にテストします。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `MCPToolType` / `SSEEventType` | ツール種別・SSEイベント種別のEnum定義 |
| `CloudCredentialsContext` | AWS/Azure/GCPクラウド認証情報コンテキスト |
| `MCPToolParameter` / `MCPTool` | MCPツールのパラメータ・定義モデル |
| `MCPServer` / `MCPServerStatus` | MCPサーバー設定・ステータスモデル |
| `MCPChatRequest` / `MCPChatStreamRequest` | チャットリクエストモデル（同期/SSE） |
| `MCPChatResponse` | チャットレスポンスモデル |
| `MCPProgress` / `SubTaskResult` / `TodoItem` | 進捗・タスク管理モデル |
| `ValidationResult` / `ThinkingLog` | ポリシー検証・思考ログモデル |
| `SessionInfo` / `SessionListResponse` | セッション管理モデル |

### 1.2 カバレッジ目標: 85%

> **注記**: Pydanticモデル定義が中心だが、バリデーション制約（`max_length`、`Literal`、必須フィールド）とデフォルト値の検証が重要なため、高めのカバレッジを設定。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/models/mcp.py` |
| テストコード | `test/unit/models/test_mcp_models.py` |
| conftest | `test/unit/models/conftest.py` |

### 1.4 補足情報

**モデル一覧（24モデル）:**

| カテゴリ | モデル名 | 行番号 |
|---------|---------|--------|
| Enum | `MCPToolType` | 54-58 |
| Enum | `SSEEventType` | 61-78 |
| 認証 | `CloudCredentialsContext` | 7-51 |
| ツール | `MCPToolParameter` | 81-87 |
| ツール | `MCPTool` | 90-96 |
| ツール | `MCPToolCall` | 109-112 |
| ツール | `MCPToolResult` | 115-120 |
| サーバー | `MCPServer` | 99-106 |
| サーバー | `MCPServerStatus` | 305-311 |
| サーバー | `MCPServerListResponse` | 294-296 |
| サーバー | `MCPToolListResponse` | 299-302 |
| サーバー | `MCPStatusResponse` | 314-318 |
| チャット | `MCPChatMessage` | 123-129 |
| チャット | `MCPChatRequest` | 211-221 |
| チャット | `MCPChatStreamRequest` | 224-259 |
| チャット | `MCPChatResponse` | 262-291 |
| タスク | `SubTaskResult` | 132-139 |
| タスク | `TodoItem` | 147-165 |
| タスク | `ThinkingLog` | 168-180 |
| 検証 | `ValidationResult` | 183-192 |
| 進捗 | `MCPProgress` | 195-208 |
| セッション | `SessionInfo` | 325-336 |
| セッション | `SessionListResponse` | 339-349 |
| セッション | `SessionUpdateRequest` | 352-361 |

**主要バリデーション制約:**

| モデル | フィールド | 制約 |
|--------|----------|------|
| `CloudCredentialsContext` | `cloud_provider` | `Literal["aws", "azure", "gcp"]` |
| `SessionUpdateRequest` | `name` | `max_length=100` |
| `MCPChatRequest` | `session_id`, `message` | `...` (必須) |
| `MCPChatStreamRequest` | `session_id`, `message` | `...` (必須) |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| MCPMOD-001 | MCPToolType Enum値検証 | - | 3つの値（function/resource/prompt） |
| MCPMOD-002 | SSEEventType Enum値検証 | - | 11個のイベントタイプ |
| MCPMOD-003 | CloudCredentialsContext AWS最小構成 | cloud_provider="aws" | 正常生成 |
| MCPMOD-004 | CloudCredentialsContext AWS完全構成 | 全フィールド指定 | 正常生成 |
| MCPMOD-005 | CloudCredentialsContext Azure構成 | cloud_provider="azure" | 正常生成 |
| MCPMOD-006 | CloudCredentialsContext GCP構成 | cloud_provider="gcp" | 正常生成 |
| MCPMOD-007 | MCPToolParameter デフォルト値 | name, type のみ | required=True, default=None |
| MCPMOD-008 | MCPTool デフォルト値 | name, description のみ | type=FUNCTION, parameters=[] |
| MCPMOD-009 | MCPServer デフォルト値 | name, command のみ | args=[], env={}, enabled=True |
| MCPMOD-010 | MCPToolCall デフォルト値 | tool_name のみ | parameters={} |
| MCPMOD-011 | MCPToolResult 成功ケース | success=True, content="result" | 正常生成 |
| MCPMOD-012 | MCPToolResult 失敗ケース | success=False, error="msg" | 正常生成 |
| MCPMOD-013 | MCPChatMessage 最小構成 | role, content | 正常生成 |
| MCPMOD-014 | MCPChatMessage 完全構成 | 全フィールド | 正常生成 |
| MCPMOD-015 | SubTaskResult 最小構成 | id, description, status | 正常生成 |
| MCPMOD-016 | TodoItem 最小構成 | id, description, status | 正常生成 |
| MCPMOD-017 | ThinkingLog 最小構成 | timestamp, content, source | 正常生成 |
| MCPMOD-018 | ValidationResult デフォルト値 | is_valid のみ | retry_count=0 |
| MCPMOD-019 | MCPProgress デフォルト値 | なし | sub_tasks=[], llm_calls=0 |
| MCPMOD-020 | MCPChatRequest デフォルト値 | session_id, message | use_hierarchical=True |
| MCPMOD-021 | MCPChatStreamRequest デフォルト値 | session_id, message | include_token_stream=False |
| MCPMOD-022 | MCPChatResponse 最小構成 | response, session_id | 正常生成 |
| MCPMOD-023 | MCPChatResponse 完全構成 | 全フィールド | 正常生成 |
| MCPMOD-024 | MCPServerListResponse 空リスト | servers=[] | 正常生成 |
| MCPMOD-025 | MCPServerListResponse 複数サーバー | 3サーバー | 正常生成 |
| MCPMOD-026 | MCPToolListResponse | tools, server_name | 正常生成 |
| MCPMOD-027 | MCPServerStatus デフォルト値 | name, status | available_tools=[] |
| MCPMOD-028 | MCPStatusResponse | servers, total_tools, active_sessions | 正常生成 |
| MCPMOD-029 | SessionInfo デフォルト値 | session_id のみ | checkpoint_count=0 |
| MCPMOD-030 | SessionListResponse デフォルト値 | total のみ | sessions=[], limit=50, offset=0 |
| MCPMOD-031 | SessionUpdateRequest 境界値 | name=100文字 | 正常生成 |
| MCPMOD-032 | model_dump JSON変換検証 | 全モデル | 正しいJSON形式 |
| MCPMOD-033 | model_validate 辞書からの生成 | 辞書データ | 正常生成 |
| MCPMOD-034 | MCPTool パラメータ付き構成 | 複数パラメータ | 正常生成 |
| MCPMOD-035 | MCPServer 完全構成 | 全フィールド指定 | 正常生成 |
| MCPMOD-036 | MCPChatStreamRequest クラウド認証情報付き | CloudCredentials付き | 正常生成 |
| MCPMOD-037 | SubTaskResult ツール実行結果付き | tool, result指定 | 正常生成 |
| MCPMOD-038 | ValidationResult 検証失敗ケース | is_valid=False | 正常生成 |
| MCPMOD-039 | MCPProgress データ付き | sub_tasks付き | 正常生成 |
| MCPMOD-040 | SessionInfo 完全構成 | 全フィールド指定 | 正常生成 |
| MCPMOD-041 | SessionListResponse データ付き | sessions, limit, offset | 正常生成 |
| MCPMOD-042 | JSON往復変換テスト | model_dump_json→model_validate_json | データ一致 |
| MCPMOD-043 | ミュータブルデフォルトの独立性 | 複数インスタンス生成 | 参照共有されない |

### 2.1 Enumテスト

```python
# test/unit/models/test_mcp_models.py
import pytest
from app.models.mcp import (
    MCPToolType, SSEEventType, CloudCredentialsContext,
    MCPToolParameter, MCPTool, MCPServer, MCPToolCall, MCPToolResult,
    MCPChatMessage, SubTaskResult, TodoItem, ThinkingLog, ValidationResult,
    MCPProgress, MCPChatRequest, MCPChatStreamRequest, MCPChatResponse,
    MCPServerListResponse, MCPToolListResponse, MCPServerStatus, MCPStatusResponse,
    SessionInfo, SessionListResponse, SessionUpdateRequest
)


class TestMCPEnums:
    """MCP Enum型のテスト"""

    def test_mcp_tool_type_values(self):
        """MCPMOD-001: MCPToolType Enum値検証"""
        # Arrange & Act
        values = [e.value for e in MCPToolType]

        # Assert
        assert len(values) == 3
        assert "function" in values
        assert "resource" in values
        assert "prompt" in values
        # .value を使って文字列比較
        assert MCPToolType.FUNCTION.value == "function"
        assert MCPToolType.RESOURCE.value == "resource"
        assert MCPToolType.PROMPT.value == "prompt"

    def test_sse_event_type_values(self):
        """MCPMOD-002: SSEEventType Enum値検証"""
        # Arrange & Act
        values = [e.value for e in SSEEventType]

        # Assert
        assert len(values) == 11
        # 既存イベント
        assert "orchestrator" in values
        assert "task_start" in values
        assert "task_complete" in values
        assert "response" in values
        assert "error" in values
        assert "done" in values
        # トークンストリーミング用
        assert "response_chunk" in values
        assert "llm_start" in values
        assert "llm_end" in values
        # Deep Agents用
        assert "tool_start" in values
        assert "tool_end" in values
        # .value を使った文字列比較
        assert SSEEventType.DONE.value == "done"
        assert SSEEventType.ERROR.value == "error"
```

### 2.2 CloudCredentialsContextテスト

```python
class TestCloudCredentialsContext:
    """クラウド認証情報コンテキストのテスト"""

    def test_aws_minimal_config(self):
        """MCPMOD-003: CloudCredentialsContext AWS最小構成"""
        # Arrange & Act
        creds = CloudCredentialsContext(cloud_provider="aws")

        # Assert
        assert creds.cloud_provider == "aws"
        assert creds.role_arn is None
        assert creds.external_id is None
        assert creds.regions is None

    def test_aws_full_config(self):
        """MCPMOD-004: CloudCredentialsContext AWS完全構成"""
        # Arrange
        data = {
            "cloud_provider": "aws",
            "role_arn": "arn:aws:iam::123456789012:role/TestRole",
            "external_id": "ext-123",
            "regions": ["us-east-1", "ap-northeast-1"]
        }

        # Act
        creds = CloudCredentialsContext(**data)

        # Assert
        assert creds.cloud_provider == "aws"
        assert creds.role_arn == "arn:aws:iam::123456789012:role/TestRole"
        assert creds.external_id == "ext-123"
        assert creds.regions == ["us-east-1", "ap-northeast-1"]

    def test_azure_config(self):
        """MCPMOD-005: CloudCredentialsContext Azure構成"""
        # Arrange
        data = {
            "cloud_provider": "azure",
            "tenant_id": "tenant-123",
            "client_id": "client-456",
            "subscription_id": "sub-789"
        }

        # Act
        creds = CloudCredentialsContext(**data)

        # Assert
        assert creds.cloud_provider == "azure"
        assert creds.tenant_id == "tenant-123"
        assert creds.client_id == "client-456"
        assert creds.subscription_id == "sub-789"

    def test_gcp_config(self):
        """MCPMOD-006: CloudCredentialsContext GCP構成"""
        # Arrange
        data = {
            "cloud_provider": "gcp",
            "project_id": "my-project-123"
        }

        # Act
        creds = CloudCredentialsContext(**data)

        # Assert
        assert creds.cloud_provider == "gcp"
        assert creds.project_id == "my-project-123"
```

### 2.3 ツール関連モデルテスト

```python
class TestMCPToolModels:
    """MCPツール関連モデルのテスト"""

    def test_mcp_tool_parameter_defaults(self):
        """MCPMOD-007: MCPToolParameter デフォルト値"""
        # Arrange & Act
        param = MCPToolParameter(name="query", type="string")

        # Assert
        assert param.name == "query"
        assert param.type == "string"
        assert param.description is None
        assert param.required is True
        assert param.default is None

    def test_mcp_tool_defaults(self):
        """MCPMOD-008: MCPTool デフォルト値"""
        # Arrange & Act
        tool = MCPTool(name="search", description="Search documents")

        # Assert
        assert tool.name == "search"
        assert tool.description == "Search documents"
        assert tool.type == MCPToolType.FUNCTION
        assert tool.parameters == []
        assert tool.schema is None

    def test_mcp_tool_with_parameters(self):
        """MCPMOD-034: MCPTool パラメータ付き構成"""
        # Arrange
        params = [
            MCPToolParameter(name="query", type="string", description="検索クエリ"),
            MCPToolParameter(name="limit", type="integer", required=False, default=10)
        ]

        # Act
        tool = MCPTool(
            name="search",
            description="Search documents",
            type=MCPToolType.FUNCTION,
            parameters=params
        )

        # Assert
        assert len(tool.parameters) == 2
        assert tool.parameters[0].name == "query"
        assert tool.parameters[1].default == 10

    def test_mcp_tool_call_defaults(self):
        """MCPMOD-010: MCPToolCall デフォルト値"""
        # Arrange & Act
        call = MCPToolCall(tool_name="search")

        # Assert
        assert call.tool_name == "search"
        assert call.parameters == {}

    def test_mcp_tool_result_success(self):
        """MCPMOD-011: MCPToolResult 成功ケース"""
        # Arrange & Act
        result = MCPToolResult(success=True, content="Found 5 documents")

        # Assert
        assert result.success is True
        assert result.content == "Found 5 documents"
        assert result.error is None
        assert result.metadata is None

    def test_mcp_tool_result_failure(self):
        """MCPMOD-012: MCPToolResult 失敗ケース"""
        # Arrange & Act
        result = MCPToolResult(success=False, error="Connection timeout")

        # Assert
        assert result.success is False
        assert result.content is None
        assert result.error == "Connection timeout"
```

### 2.4 サーバー関連モデルテスト

```python
class TestMCPServerModels:
    """MCPサーバー関連モデルのテスト"""

    def test_mcp_server_defaults(self):
        """MCPMOD-009: MCPServer デフォルト値"""
        # Arrange & Act
        server = MCPServer(name="aws-docs", command="npx")

        # Assert
        assert server.name == "aws-docs"
        assert server.command == "npx"
        assert server.args == []
        assert server.env == {}
        assert server.enabled is True
        assert server.description is None

    def test_mcp_server_full_config(self):
        """MCPMOD-035: MCPServer 完全構成"""
        # Arrange & Act
        server = MCPServer(
            name="aws-docs",
            command="npx",
            args=["-y", "@aws/mcp-server"],
            env={"AWS_REGION": "us-east-1"},
            enabled=True,
            description="AWS Documentation Server"
        )

        # Assert
        assert server.args == ["-y", "@aws/mcp-server"]
        assert server.env == {"AWS_REGION": "us-east-1"}
        assert server.description == "AWS Documentation Server"

    def test_mutable_defaults_are_isolated(self):
        """MCPMOD-043: ミュータブルデフォルトの独立性

        list/dict のデフォルト値がインスタンス間で共有されないことを確認。
        """
        # Arrange
        server_a = MCPServer(name="server-a", command="cmd")
        server_b = MCPServer(name="server-b", command="cmd")
        tool_a = MCPTool(name="tool-a", description="desc")
        tool_b = MCPTool(name="tool-b", description="desc")
        call_a = MCPToolCall(tool_name="call-a")
        call_b = MCPToolCall(tool_name="call-b")
        status_a = MCPServerStatus(name="status-a", status="connected")
        status_b = MCPServerStatus(name="status-b", status="connected")

        # Act
        server_a.args.append("--foo")
        server_a.env["KEY"] = "VALUE"
        tool_a.parameters.append(MCPToolParameter(name="q", type="string"))
        call_a.parameters["limit"] = 10
        status_a.available_tools.append("tool-x")

        # Assert
        assert server_b.args == []
        assert server_b.env == {}
        assert tool_b.parameters == []
        assert call_b.parameters == {}
        assert status_b.available_tools == []

    def test_mcp_server_list_response_empty(self):
        """MCPMOD-024: MCPServerListResponse 空リスト"""
        # Arrange & Act
        response = MCPServerListResponse(servers=[])

        # Assert
        assert response.servers == []

    def test_mcp_server_list_response_multiple(self):
        """MCPMOD-025: MCPServerListResponse 複数サーバー"""
        # Arrange
        servers = [
            MCPServer(name="server1", command="cmd1"),
            MCPServer(name="server2", command="cmd2"),
            MCPServer(name="server3", command="cmd3"),
        ]

        # Act
        response = MCPServerListResponse(servers=servers)

        # Assert
        assert len(response.servers) == 3
        assert response.servers[0].name == "server1"

    def test_mcp_tool_list_response(self):
        """MCPMOD-026: MCPToolListResponse"""
        # Arrange
        tools = [MCPTool(name="tool1", description="desc1")]

        # Act
        response = MCPToolListResponse(tools=tools, server_name="test-server")

        # Assert
        assert len(response.tools) == 1
        assert response.server_name == "test-server"

    def test_mcp_server_status_defaults(self):
        """MCPMOD-027: MCPServerStatus デフォルト値"""
        # Arrange & Act
        status = MCPServerStatus(name="aws-docs", status="connected")

        # Assert
        assert status.name == "aws-docs"
        assert status.status == "connected"
        assert status.last_connected is None
        assert status.error_message is None
        assert status.available_tools == []

    def test_mcp_status_response(self):
        """MCPMOD-028: MCPStatusResponse"""
        # Arrange
        server_status = MCPServerStatus(name="server1", status="connected")

        # Act
        response = MCPStatusResponse(
            servers=[server_status],
            total_tools=5,
            active_sessions=3
        )

        # Assert
        assert len(response.servers) == 1
        assert response.total_tools == 5
        assert response.active_sessions == 3
```

### 2.5 チャット関連モデルテスト

```python
class TestMCPChatModels:
    """MCPチャット関連モデルのテスト"""

    def test_mcp_chat_message_minimal(self):
        """MCPMOD-013: MCPChatMessage 最小構成"""
        # Arrange & Act
        msg = MCPChatMessage(role="user", content="Hello")

        # Assert
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.tool_calls is None
        assert msg.tool_results is None
        assert msg.timestamp is None

    def test_mcp_chat_message_full(self):
        """MCPMOD-014: MCPChatMessage 完全構成"""
        # Arrange
        tool_calls = [MCPToolCall(tool_name="search", parameters={"q": "test"})]
        tool_results = [MCPToolResult(success=True, content="result")]

        # Act
        msg = MCPChatMessage(
            role="assistant",
            content="Here are the results",
            tool_calls=tool_calls,
            tool_results=tool_results,
            timestamp="2026-02-04T10:00:00Z"
        )

        # Assert
        assert msg.role == "assistant"
        assert len(msg.tool_calls) == 1
        assert len(msg.tool_results) == 1
        assert msg.timestamp == "2026-02-04T10:00:00Z"

    def test_mcp_chat_request_defaults(self):
        """MCPMOD-020: MCPChatRequest デフォルト値"""
        # Arrange & Act
        request = MCPChatRequest(session_id="session-123", message="Hello")

        # Assert
        assert request.session_id == "session-123"
        assert request.message == "Hello"
        assert request.server_name is None
        assert request.available_tools is None
        assert request.context is None
        assert request.use_hierarchical is True

    def test_mcp_chat_stream_request_defaults(self):
        """MCPMOD-021: MCPChatStreamRequest デフォルト値"""
        # Arrange & Act
        request = MCPChatStreamRequest(session_id="session-123", message="Hello")

        # Assert
        assert request.session_id == "session-123"
        assert request.message == "Hello"
        assert request.server_name is None
        assert request.user_id is None
        assert request.auth_hash is None
        assert request.include_token_stream is False
        assert request.use_hierarchical is True
        assert request.cloud_credentials is None

    def test_mcp_chat_stream_request_with_credentials(self):
        """MCPMOD-036: MCPChatStreamRequest クラウド認証情報付き"""
        # Arrange
        creds = CloudCredentialsContext(
            cloud_provider="aws",
            role_arn="arn:aws:iam::123456789012:role/Test"
        )

        # Act
        request = MCPChatStreamRequest(
            session_id="user123:session-456",
            message="Query",
            user_id="user123",
            auth_hash="SHARED-HMAC-1234567890-hash",
            cloud_credentials=creds
        )

        # Assert
        assert request.user_id == "user123"
        assert request.auth_hash == "SHARED-HMAC-1234567890-hash"
        assert request.cloud_credentials.cloud_provider == "aws"

    def test_mcp_chat_response_minimal(self):
        """MCPMOD-022: MCPChatResponse 最小構成"""
        # Arrange & Act
        response = MCPChatResponse(response="Hello", session_id="session-123")

        # Assert
        assert response.response == "Hello"
        assert response.session_id == "session-123"
        assert response.tool_calls is None
        assert response.tool_results is None
        assert response.available_tools is None
        assert response.progress is None
        assert response.todos is None
        assert response.thinking_logs is None
        assert response.validation_result is None

    def test_mcp_chat_response_full(self):
        """MCPMOD-023: MCPChatResponse 完全構成"""
        # Arrange
        progress = MCPProgress(task_analysis="Analyzing...", llm_calls=5)
        todos = [TodoItem(id="1", description="Task 1", status="completed")]
        thinking_logs = [ThinkingLog(
            timestamp="2026-02-04T10:00:00Z",
            content="Processing",
            source="orchestrator"
        )]
        validation = ValidationResult(is_valid=True, message="Valid")

        # Act
        response = MCPChatResponse(
            response="Done",
            session_id="session-123",
            progress=progress,
            todos=todos,
            thinking_logs=thinking_logs,
            validation_result=validation
        )

        # Assert
        assert response.progress.llm_calls == 5
        assert len(response.todos) == 1
        assert len(response.thinking_logs) == 1
        assert response.validation_result.is_valid is True
```

### 2.6 タスク/進捗モデルテスト

```python
class TestMCPTaskModels:
    """MCPタスク/進捗関連モデルのテスト"""

    def test_sub_task_result_minimal(self):
        """MCPMOD-015: SubTaskResult 最小構成"""
        # Arrange & Act
        result = SubTaskResult(
            id="task-1",
            description="Search documents",
            status="completed"
        )

        # Assert
        assert result.id == "task-1"
        assert result.description == "Search documents"
        assert result.status == "completed"
        assert result.tool is None
        assert result.result is None
        assert result.error is None

    def test_sub_task_result_with_tool(self):
        """MCPMOD-037: SubTaskResult ツール実行結果付き"""
        # Arrange & Act
        result = SubTaskResult(
            id="task-1",
            description="Search documents",
            status="completed",
            tool="aws-docs.search_documentation",
            result="Found 10 documents"
        )

        # Assert
        assert result.tool == "aws-docs.search_documentation"
        assert result.result == "Found 10 documents"

    def test_todo_item_minimal(self):
        """MCPMOD-016: TodoItem 最小構成"""
        # Arrange & Act
        todo = TodoItem(
            id="todo-1",
            description="Review code",
            status="pending"
        )

        # Assert
        assert todo.id == "todo-1"
        assert todo.description == "Review code"
        assert todo.status == "pending"
        assert todo.tool is None
        assert todo.result is None
        assert todo.error is None

    def test_thinking_log_minimal(self):
        """MCPMOD-017: ThinkingLog 最小構成"""
        # Arrange & Act
        log = ThinkingLog(
            timestamp="2026-02-04T10:00:00Z",
            content="Analyzing user request",
            source="orchestrator"
        )

        # Assert
        assert log.timestamp == "2026-02-04T10:00:00Z"
        assert log.content == "Analyzing user request"
        assert log.source == "orchestrator"

    def test_validation_result_defaults(self):
        """MCPMOD-018: ValidationResult デフォルト値"""
        # Arrange & Act
        result = ValidationResult(is_valid=True)

        # Assert
        assert result.is_valid is True
        assert result.retry_count == 0
        assert result.message is None
        assert result.error is None

    def test_validation_result_failure(self):
        """MCPMOD-038: ValidationResult 検証失敗ケース"""
        # Arrange & Act
        result = ValidationResult(
            is_valid=False,
            retry_count=3,
            error="Invalid YAML syntax"
        )

        # Assert
        assert result.is_valid is False
        assert result.retry_count == 3
        assert result.error == "Invalid YAML syntax"

    def test_mcp_progress_defaults(self):
        """MCPMOD-019: MCPProgress デフォルト値"""
        # Arrange & Act
        progress = MCPProgress()

        # Assert
        assert progress.task_analysis is None
        assert progress.sub_tasks == []
        assert progress.llm_calls == 0
        assert progress.llm_calls_by_model == {}
        assert progress.completed_tools is None

    def test_mcp_progress_with_data(self):
        """MCPMOD-039: MCPProgress データ付き"""
        # Arrange
        sub_tasks = [SubTaskResult(id="1", description="Task", status="done")]

        # Act
        progress = MCPProgress(
            task_analysis="Analyzing...",
            sub_tasks=sub_tasks,
            llm_calls=10,
            llm_calls_by_model={"gpt-4": 5, "claude-3": 5},
            completed_tools=["search", "fetch"]
        )

        # Assert
        assert progress.task_analysis == "Analyzing..."
        assert len(progress.sub_tasks) == 1
        assert progress.llm_calls == 10
        assert progress.llm_calls_by_model["gpt-4"] == 5
        assert progress.completed_tools == ["search", "fetch"]
```

### 2.7 セッション管理モデルテスト

```python
class TestSessionModels:
    """セッション管理モデルのテスト"""

    def test_session_info_defaults(self):
        """MCPMOD-029: SessionInfo デフォルト値"""
        # Arrange & Act
        info = SessionInfo(session_id="user123:session-456")

        # Assert
        assert info.session_id == "user123:session-456"
        assert info.name is None
        assert info.checkpoint_count == 0
        assert info.last_updated is None
        assert info.preview is None

    def test_session_info_full(self):
        """MCPMOD-040: SessionInfo 完全構成"""
        # Arrange & Act
        info = SessionInfo(
            session_id="user123:session-456",
            name="My Chat Session",
            checkpoint_count=15,
            last_updated="2026-02-04T10:00:00Z",
            preview="最後のメッセージ..."
        )

        # Assert
        assert info.name == "My Chat Session"
        assert info.checkpoint_count == 15
        assert info.last_updated == "2026-02-04T10:00:00Z"
        assert info.preview == "最後のメッセージ..."

    def test_session_list_response_defaults(self):
        """MCPMOD-030: SessionListResponse デフォルト値"""
        # Arrange & Act
        response = SessionListResponse(total=0)

        # Assert
        assert response.total == 0
        assert response.sessions == []
        assert response.limit == 50
        assert response.offset == 0

    def test_session_list_response_with_data(self):
        """MCPMOD-041: SessionListResponse データ付き"""
        # Arrange
        sessions = [
            SessionInfo(session_id="session-1"),
            SessionInfo(session_id="session-2")
        ]

        # Act
        response = SessionListResponse(
            total=100,
            sessions=sessions,
            limit=10,
            offset=20
        )

        # Assert
        assert response.total == 100
        assert len(response.sessions) == 2
        assert response.limit == 10
        assert response.offset == 20

    def test_session_update_request_boundary(self):
        """MCPMOD-031: SessionUpdateRequest 境界値"""
        # Arrange
        name_100_chars = "A" * 100

        # Act
        request = SessionUpdateRequest(name=name_100_chars)

        # Assert
        assert len(request.name) == 100
```

### 2.8 JSON変換テスト

```python
class TestModelSerialization:
    """モデルのシリアライズ/デシリアライズテスト"""

    def test_model_dump_json(self):
        """MCPMOD-032: model_dump JSON変換検証"""
        # Arrange
        creds = CloudCredentialsContext(cloud_provider="aws")
        request = MCPChatRequest(session_id="session-1", message="Hello")
        response = MCPChatResponse(response="Hi", session_id="session-1")

        # Act
        creds_dict = creds.model_dump()
        request_dict = request.model_dump()
        response_dict = response.model_dump()

        # Assert
        assert creds_dict["cloud_provider"] == "aws"
        assert request_dict["session_id"] == "session-1"
        assert response_dict["response"] == "Hi"

    def test_model_validate_from_dict(self):
        """MCPMOD-033: model_validate 辞書からの生成"""
        # Arrange
        data = {
            "session_id": "session-123",
            "message": "Test message",
            "use_hierarchical": False
        }

        # Act
        request = MCPChatRequest.model_validate(data)

        # Assert
        assert request.session_id == "session-123"
        assert request.message == "Test message"
        assert request.use_hierarchical is False

    def test_model_json_round_trip(self):
        """MCPMOD-042: JSON往復変換テスト"""
        # Arrange
        original = MCPChatResponse(
            response="Test response",
            session_id="session-123",
            progress=MCPProgress(llm_calls=5)
        )

        # Act
        json_str = original.model_dump_json()
        restored = MCPChatResponse.model_validate_json(json_str)

        # Assert
        assert restored.response == original.response
        assert restored.session_id == original.session_id
        assert restored.progress.llm_calls == 5
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| MCPMOD-E01 | CloudCredentialsContext 無効なcloud_provider | "invalid" | ValidationError |
| MCPMOD-E02 | CloudCredentialsContext cloud_provider欠落 | なし | ValidationError |
| MCPMOD-E03 | MCPChatRequest session_id欠落 | message のみ | ValidationError |
| MCPMOD-E04 | MCPChatRequest message欠落 | session_id のみ | ValidationError |
| MCPMOD-E05 | MCPChatStreamRequest 必須フィールド欠落 | なし | ValidationError |
| MCPMOD-E06 | MCPChatResponse response欠落 | session_id のみ | ValidationError |
| MCPMOD-E07 | MCPChatResponse session_id欠落 | response のみ | ValidationError |
| MCPMOD-E08 | SessionUpdateRequest name超過 | 101文字 | ValidationError |
| MCPMOD-E09 | SubTaskResult 必須フィールド欠落 | id のみ | ValidationError |
| MCPMOD-E10 | TodoItem 必須フィールド欠落 | id のみ | ValidationError |
| MCPMOD-E11 | ThinkingLog 必須フィールド欠落 | timestamp のみ | ValidationError |
| MCPMOD-E12 | ValidationResult is_valid欠落 | なし | ValidationError |
| MCPMOD-E13 | MCPTool 必須フィールド欠落 | name のみ | ValidationError |
| MCPMOD-E14 | MCPToolParameter 必須フィールド欠落 | name のみ | ValidationError |
| MCPMOD-E15 | MCPServerStatus 必須フィールド欠落 | name のみ | ValidationError |
| MCPMOD-E16 | MCPStatusResponse 必須フィールド欠落 | servers のみ | ValidationError |
| MCPMOD-E17 | SessionListResponse total欠落 | sessions のみ | ValidationError |

### 3.1 バリデーションエラーテスト

```python
from pydantic import ValidationError


class TestMCPValidationErrors:
    """MCPモデルのバリデーションエラーテスト"""

    def test_cloud_credentials_invalid_provider(self):
        """MCPMOD-E01: CloudCredentialsContext 無効なcloud_provider"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            CloudCredentialsContext(cloud_provider="invalid")

        # バリデーションエラーの詳細確認
        errors = exc_info.value.errors()
        assert len(errors) >= 1
        assert "cloud_provider" in str(errors)

    def test_cloud_credentials_missing_provider(self):
        """MCPMOD-E02: CloudCredentialsContext cloud_provider欠落"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            CloudCredentialsContext()

        errors = exc_info.value.errors()
        assert any("cloud_provider" in str(e) for e in errors)

    def test_mcp_chat_request_missing_session_id(self):
        """MCPMOD-E03: MCPChatRequest session_id欠落"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            MCPChatRequest(message="Hello")

        errors = exc_info.value.errors()
        assert any("session_id" in str(e) for e in errors)

    def test_mcp_chat_request_missing_message(self):
        """MCPMOD-E04: MCPChatRequest message欠落"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            MCPChatRequest(session_id="session-123")

        errors = exc_info.value.errors()
        assert any("message" in str(e) for e in errors)

    def test_mcp_chat_stream_request_missing_required(self):
        """MCPMOD-E05: MCPChatStreamRequest 必須フィールド欠落"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            MCPChatStreamRequest()

    def test_mcp_chat_response_missing_response(self):
        """MCPMOD-E06: MCPChatResponse response欠落"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            MCPChatResponse(session_id="session-123")

        errors = exc_info.value.errors()
        assert any("response" in str(e) for e in errors)

    def test_mcp_chat_response_missing_session_id(self):
        """MCPMOD-E07: MCPChatResponse session_id欠落"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            MCPChatResponse(response="Hello")

        errors = exc_info.value.errors()
        assert any("session_id" in str(e) for e in errors)

    def test_session_update_request_name_too_long(self):
        """MCPMOD-E08: SessionUpdateRequest name超過"""
        # Arrange
        name_101_chars = "A" * 101

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            SessionUpdateRequest(name=name_101_chars)

        errors = exc_info.value.errors()
        assert any("name" in str(e) for e in errors)

    def test_sub_task_result_missing_required(self):
        """MCPMOD-E09: SubTaskResult 必須フィールド欠落"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            SubTaskResult(id="task-1")  # description, status欠落

    def test_todo_item_missing_required(self):
        """MCPMOD-E10: TodoItem 必須フィールド欠落"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            TodoItem(id="todo-1")  # description, status欠落

    def test_thinking_log_missing_required(self):
        """MCPMOD-E11: ThinkingLog 必須フィールド欠落"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            ThinkingLog(timestamp="2026-02-04T10:00:00Z")  # content, source欠落

    def test_validation_result_missing_is_valid(self):
        """MCPMOD-E12: ValidationResult is_valid欠落"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            ValidationResult()

    def test_mcp_tool_missing_description(self):
        """MCPMOD-E13: MCPTool 必須フィールド欠落"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            MCPTool(name="tool")  # description欠落

    def test_mcp_tool_parameter_missing_type(self):
        """MCPMOD-E14: MCPToolParameter 必須フィールド欠落"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            MCPToolParameter(name="param")  # type欠落

    def test_mcp_server_status_missing_status(self):
        """MCPMOD-E15: MCPServerStatus 必須フィールド欠落"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            MCPServerStatus(name="server")  # status欠落

    def test_mcp_status_response_missing_fields(self):
        """MCPMOD-E16: MCPStatusResponse 必須フィールド欠落"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            MCPStatusResponse(servers=[])  # total_tools, active_sessions欠落

    def test_session_list_response_missing_total(self):
        """MCPMOD-E17: SessionListResponse total欠落"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            SessionListResponse(sessions=[])  # total欠落
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| MCPMOD-SEC-01 | 認証情報のシリアライズ検証 | CloudCredentialsContext | 全フィールドがシリアライズされる（注意喚起） |
| MCPMOD-SEC-02 | auth_hashフォーマット受け入れ | SHARED-HMAC形式 | 正常受け入れ |
| MCPMOD-SEC-03 | SQLインジェクション文字列格納 | SQLインジェクション文字列 | 文字列として格納（上位層でサニタイズ必要） |
| MCPMOD-SEC-04 | XSSペイロード格納 | scriptタグ | 文字列として格納（上位層でエスケープ必要） |
| MCPMOD-SEC-05 | 巨大文字列入力受け入れ確認 | 1MB文字列 | 文字列として受け入れ（サイズ制限は上位層） |
| MCPMOD-SEC-06 | ネストされた認証情報の扱い | 深いネスト構造 | 正常処理 |
| MCPMOD-SEC-07 | role_arnフォーマット検証 | 不正なARN形式 | 文字列として受け入れ（フォーマット検証は上位層推奨） |
| MCPMOD-SEC-08 | external_id長さ境界値 | 1224文字（AWS上限） | 正常受け入れ |
| MCPMOD-SEC-09 | リージョン名パストラバーサル | "../../../etc/passwd" | 文字列として格納（上位層で検証必要） |
| MCPMOD-SEC-10 | パラメータネスト深度 | 深いネスト構造 | 正常処理（再帰深度制限は上位層推奨） |

```python
import sys


@pytest.mark.security
class TestMCPModelsSecurity:
    """MCPモデルのセキュリティテスト"""

    def test_credentials_serialization_exposure(self):
        """MCPMOD-SEC-01: 認証情報のシリアライズ検証

        目的: CloudCredentialsContextをシリアライズした際に
        機密情報が含まれることを確認し、ログ出力時の注意を喚起する。
        """
        # Arrange
        creds = CloudCredentialsContext(
            cloud_provider="aws",
            role_arn="arn:aws:iam::123456789012:role/SecretRole",
            external_id="super-secret-id-12345"
        )

        # Act
        serialized = creds.model_dump()
        json_str = creds.model_dump_json()

        # Assert - 機密情報がシリアライズされることを確認
        # 注意: ログ出力時はこれらの情報をマスクする必要がある
        assert "SecretRole" in str(serialized)
        assert "super-secret-id" in json_str
        # このテストは「機密情報が露出しうる」ことの文書化として機能する

    def test_auth_hash_format_acceptance(self):
        """MCPMOD-SEC-02: auth_hashフォーマット受け入れ"""
        # Arrange
        valid_hash = "SHARED-HMAC-1707033600-a1b2c3d4e5f6g7h8i9j0"

        # Act
        request = MCPChatStreamRequest(
            session_id="user123:session-456",
            message="Test",
            auth_hash=valid_hash
        )

        # Assert
        assert request.auth_hash == valid_hash
        # 注意: フォーマット検証はルーター層で行われる

    def test_sql_injection_pattern_storage(self):
        """MCPMOD-SEC-03: SQLインジェクション文字列格納

        Note: Pydanticモデルは入力サニタイズを行わない。
        SQLインジェクション対策はDB層（パラメータ化クエリ）で行う。
        """
        # Arrange
        sql_injection = "'; DROP TABLE users; --"

        # Act
        request = MCPChatRequest(
            session_id="session-123",
            message=sql_injection
        )

        # Assert - Pydanticは文字列をそのまま受け入れる
        assert request.message == sql_injection
        # 重要: アプリケーション層でのサニタイズが必要

    def test_xss_payload_storage(self):
        """MCPMOD-SEC-04: XSSペイロード格納

        Note: Pydanticモデルは入力サニタイズを行わない。
        XSS対策はフロントエンド/レスポンス生成時に行う。
        """
        # Arrange
        xss_payload = "<script>alert('XSS')</script>"

        # Act
        response = MCPChatResponse(
            response=xss_payload,
            session_id="session-123"
        )

        # Assert - Pydanticは文字列をそのまま受け入れる
        assert response.response == xss_payload
        # 重要: レスポンス時にHTMLエスケープが必要

    def test_large_string_memory_consumption(self):
        """MCPMOD-SEC-05: 巨大文字列入力

        Note: 大きな文字列入力によるメモリ消費を確認。
        本番環境ではリクエストサイズ制限をミドルウェアで設定すべき。
        """
        # Arrange
        # 1MBの文字列（10MBはテスト時間がかかりすぎるため縮小）
        large_string = "A" * (1 * 1024 * 1024)
        initial_memory = sys.getsizeof(large_string)

        # Act
        request = MCPChatRequest(
            session_id="session-123",
            message=large_string
        )

        # Assert
        assert len(request.message) == 1 * 1024 * 1024
        # 注意: FastAPIのRequestBodySizeLimitMiddlewareで制限すべき

    def test_nested_credentials_handling(self):
        """MCPMOD-SEC-06: ネストされた認証情報の扱い"""
        # Arrange
        creds = CloudCredentialsContext(
            cloud_provider="aws",
            role_arn="arn:aws:iam::123456789012:role/Test",
            external_id="ext-123",
            regions=["us-east-1", "ap-northeast-1"]
        )

        # Act
        request = MCPChatStreamRequest(
            session_id="user123:session-456",
            message="Test",
            cloud_credentials=creds
        )

        # Assert
        assert request.cloud_credentials is not None
        assert request.cloud_credentials.role_arn is not None
        # シリアライズ時にネスト構造が正しく処理されることを確認
        serialized = request.model_dump()
        assert serialized["cloud_credentials"]["role_arn"] == creds.role_arn

    def test_role_arn_format_no_validation(self):
        """MCPMOD-SEC-07: role_arnフォーマット検証

        【実装改善提案】現在の実装ではrole_arnのフォーマット検証がない。
        正規表現によるARNフォーマット検証の追加を推奨。
        """
        # Arrange
        invalid_arn = "not-a-valid-arn"

        # Act - 現状は任意の文字列を受け入れる
        creds = CloudCredentialsContext(
            cloud_provider="aws",
            role_arn=invalid_arn
        )

        # Assert - 現状はバリデーションなし
        assert creds.role_arn == invalid_arn
        # 推奨: Field(..., pattern=r"^arn:aws:iam::\d{12}:role/[\w+=,.@-]+$")

    def test_external_id_length_boundary(self):
        """MCPMOD-SEC-08: external_id長さ境界値

        AWS External IDの長さ制限は2-1224文字。
        現状Pydanticでは制限していないため、上位層での検証を推奨。
        """
        # Arrange
        max_length_external_id = "x" * 1224  # AWS上限

        # Act
        creds = CloudCredentialsContext(
            cloud_provider="aws",
            external_id=max_length_external_id
        )

        # Assert - Pydanticは文字列長制限なし
        assert len(creds.external_id) == 1224
        # 推奨: Field(..., min_length=2, max_length=1224)

    def test_region_path_traversal_storage(self):
        """MCPMOD-SEC-09: リージョン名パストラバーサル

        regions配列に不正なパス文字列を含めても格納される。
        AWS API呼び出し前にリージョン名の検証が必要。
        """
        # Arrange
        malicious_regions = [
            "us-east-1",
            "../../../etc/passwd",
            "ap-northeast-1; rm -rf /"
        ]

        # Act
        creds = CloudCredentialsContext(
            cloud_provider="aws",
            regions=malicious_regions
        )

        # Assert - Pydanticは文字列内容を検証しない
        assert creds.regions == malicious_regions
        # 推奨: リージョン名の正規表現検証を上位層で実装
        # pattern: r"^[a-z]{2}-[a-z]+-\d$"

    def test_parameters_deep_nesting(self):
        """MCPMOD-SEC-10: パラメータネスト深度

        MCPToolCall.parametersは深いネスト構造を受け入れる。
        再帰深度制限は上位層で検討が必要。
        """
        # Arrange - 深いネスト構造を作成
        deep_nested = {"level_0": {}}
        current = deep_nested["level_0"]
        for i in range(1, 50):  # 50レベルのネスト
            current[f"level_{i}"] = {}
            current = current[f"level_{i}"]
        current["value"] = "deep_value"

        # Act
        from app.models.mcp import MCPToolCall
        tool_call = MCPToolCall(
            tool_name="test_tool",
            parameters=deep_nested
        )

        # Assert - Pydanticは深いネストも受け入れる
        assert "level_0" in tool_call.parameters
        # 推奨: 再帰深度制限またはサイズ制限を上位層で実装
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_mcp_models_module` | テスト間のモジュール状態リセット | function | Yes |
| `sample_cloud_credentials` | AWS認証情報サンプル | function | No |
| `sample_mcp_chat_request` | チャットリクエストサンプル | function | No |
| `sample_mcp_progress` | 進捗情報サンプル | function | No |

### 共通フィクスチャ定義

```python
# test/unit/models/conftest.py
import sys
import pytest
from app.models.mcp import (
    CloudCredentialsContext, MCPChatRequest, MCPProgress,
    SubTaskResult, TodoItem
)


@pytest.fixture(autouse=True)
def reset_mcp_models_module():
    """テストごとにmodelsモジュールの状態をリセット

    Note: Pydanticモデルは通常グローバル状態を持たないが、
    将来のキャッシュ機構追加に備えてリセットを行う。
    """
    yield
    # テスト後にモジュールキャッシュをクリア
    modules_to_remove = [
        key for key in sys.modules
        if key.startswith("app.models.mcp")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def sample_cloud_credentials():
    """AWS認証情報サンプル"""
    return CloudCredentialsContext(
        cloud_provider="aws",
        role_arn="arn:aws:iam::123456789012:role/TestRole",
        external_id="ext-123",
        regions=["us-east-1", "ap-northeast-1"]
    )


@pytest.fixture
def sample_mcp_chat_request():
    """チャットリクエストサンプル"""
    return MCPChatRequest(
        session_id="test-session-001",
        message="テストメッセージ",
        server_name="aws-docs",
        use_hierarchical=True
    )


@pytest.fixture
def sample_mcp_progress():
    """進捗情報サンプル"""
    sub_tasks = [
        SubTaskResult(
            id="task-1",
            description="Search documentation",
            status="completed",
            tool="aws-docs.search",
            result="Found 5 documents"
        ),
        SubTaskResult(
            id="task-2",
            description="Analyze results",
            status="pending"
        )
    ]
    return MCPProgress(
        task_analysis="Analyzing user query...",
        sub_tasks=sub_tasks,
        llm_calls=3,
        llm_calls_by_model={"gpt-4": 2, "claude-3": 1}
    )
```

---

## 6. テスト実行例

```bash
# models/mcp関連テストのみ実行
pytest test/unit/models/test_mcp_models.py -v

# 特定のテストクラスのみ実行
pytest test/unit/models/test_mcp_models.py::TestMCPEnums -v
pytest test/unit/models/test_mcp_models.py::TestCloudCredentialsContext -v

# カバレッジ付きで実行
pytest test/unit/models/test_mcp_models.py --cov=app.models.mcp --cov-report=term-missing -v

# 分岐カバレッジ付きで実行
pytest test/unit/models/test_mcp_models.py --cov=app.models.mcp --cov-branch --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/models/test_mcp_models.py -m "security" -v

# 失敗したテストのみ再実行
pytest test/unit/models/test_mcp_models.py --lf -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 43 | MCPMOD-001 〜 MCPMOD-043 |
| 異常系 | 17 | MCPMOD-E01 〜 MCPMOD-E17 |
| セキュリティ | 10 | MCPMOD-SEC-01 〜 MCPMOD-SEC-10 |
| **合計** | **70** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestMCPEnums` | MCPMOD-001〜MCPMOD-002 | 2 |
| `TestCloudCredentialsContext` | MCPMOD-003〜MCPMOD-006 | 4 |
| `TestMCPToolModels` | MCPMOD-007, 008, 010〜012, 034 | 6 |
| `TestMCPServerModels` | MCPMOD-009, MCPMOD-024〜MCPMOD-028, MCPMOD-035, MCPMOD-043 | 8 |
| `TestMCPChatModels` | MCPMOD-013〜MCPMOD-014, MCPMOD-020〜MCPMOD-023, MCPMOD-036 | 7 |
| `TestMCPTaskModels` | MCPMOD-015〜MCPMOD-019, MCPMOD-037〜MCPMOD-039 | 8 |
| `TestSessionModels` | MCPMOD-029〜MCPMOD-031, MCPMOD-040〜MCPMOD-041 | 5 |
| `TestModelSerialization` | MCPMOD-032〜MCPMOD-033, MCPMOD-042 | 3 |
| `TestMCPValidationErrors` | MCPMOD-E01〜MCPMOD-E17 | 17 |
| `TestMCPModelsSecurity` | MCPMOD-SEC-01〜MCPMOD-SEC-10 | 10 |

### 実装失敗が予想されるテスト

現時点で失敗が予想されるテストはありません。

> **注記**: セキュリティテスト（MCPMOD-SEC-01〜MCPMOD-SEC-10）は現在の実装で「パスする」が、これらはPydanticモデルレベルでのセキュリティ制限がないことを文書化するためのものです。入力サニタイズやフォーマット検証は上位層（ルーター、サービス）での実装を推奨しています。

### 注意事項

- Pydanticモデルのテストのため、`pytest-asyncio` は不要
- `@pytest.mark.security` マーカーの登録要（`pyproject.toml` に追加）
- セキュリティテストは「Pydanticがサニタイズしない」ことを文書化するもの
- 入力サニタイズはアプリケーション層（ルーター、サービス）で実装すべき

### 実装時の検討事項

以下はセキュリティ観点から推奨される将来の改善項目です：

1. **role_arnのフォーマット検証追加**
   ```python
   role_arn: Optional[str] = Field(
       None,
       pattern=r"^arn:aws:iam::\d{12}:role/[\w+=,.@-]+$"
   )
   ```

2. **session_idのフォーマット検証追加**
   ```python
   session_id: str = Field(
       ...,
       pattern=r"^[\w-]+:[\w-]+$"
   )
   ```

3. **auth_hashのフォーマット検証追加**
   ```python
   auth_hash: Optional[str] = Field(
       None,
       pattern=r"^SHARED-HMAC-\d+-[a-f0-9]+$"
   )
   ```

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | Pydanticは入力サニタイズを行わない | SQLi/XSSペイロードがそのまま格納される | アプリ層でサニタイズ |
| 2 | role_arnのフォーマット検証なし | 不正なARNが受け入れられる | 将来的にpattern追加推奨 |
| 3 | session_idのフォーマット検証なし | 不正な形式が受け入れられる | ルーター層で検証 |
| 4 | 大きな文字列のサイズ制限なし | メモリ消費リスク | FastAPIミドルウェアで制限 |
| 5 | auth_hashのフォーマット検証なし | 任意の文字列が受け入れられる | ルーター層で検証 |

---

## 関連ドキュメント

- [mcp_plugin_router_tests.md](../plugins/mcp/mcp_plugin_router_tests.md) - MCPルーターのテスト
- [mcp_plugin_client_tests.md](../plugins/mcp/mcp_plugin_client_tests.md) - MCPクライアントのテスト
- [TEMPLATE_test_spec.md](../TEMPLATE_test_spec.md) - テスト仕様書テンプレート
