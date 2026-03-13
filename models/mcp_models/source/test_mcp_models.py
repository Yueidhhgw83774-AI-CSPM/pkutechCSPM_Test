"""
models/mcp.py 单元测试

测试规格: docs/testing/models/mcp_models_tests.md
覆盖率目标: 90%+

测试类别:
  - 正常系: 18 个测试
  - 异常系: 5 个测试
"""

import pytest
import json
from typing import List, Dict
import sys
from pathlib import Path
from datetime import datetime
import os

# 导入被测试模块
project_root = Path(__file__).parent.parent.parent.parent.parent / "platform_python_backend-testing"
sys.path.insert(0, str(project_root))

from app.models.mcp import (
    CloudCredentialsContext,
    MCPToolType,
    SSEEventType,
    MCPToolParameter,
    MCPTool,
    MCPServer,
    MCPToolCall,
    MCPToolResult,
    MCPChatMessage,
    SubTaskResult,
    TodoItem,
    ThinkingLog,
    ValidationResult,
    MCPProgress,
    MCPChatRequest,
    MCPChatStreamRequest,
    MCPChatResponse,
    MCPServerListResponse,
    MCPToolListResponse,
    MCPServerStatus,
    MCPStatusResponse,
    SessionInfo,
    SessionListResponse,
    SessionUpdateRequest
)


class TestCloudCredentialsContextNormal:
    """
    CloudCredentialsContext 正常系测试

    测试ID: MCP-001 ~ MCP-004
    """

    def test_cloud_credentials_context_aws(self):
        """
        MCP-001: CloudCredentialsContext AWS構成
        覆盖代码行: app/models/mcp.py:9-50

        测试目的:
          - 验证 AWS 认证信息的完整配置
        """
        # Arrange
        credentials = CloudCredentialsContext(
            cloud_provider="aws",
            role_arn="arn:aws:iam::123456789012:role/MyRole",
            external_id="external-id-12345",
            regions=["us-east-1", "ap-northeast-1"]
        )

        # Assert
        assert credentials.cloud_provider == "aws"
        assert credentials.role_arn == "arn:aws:iam::123456789012:role/MyRole"
        assert credentials.external_id == "external-id-12345"
        assert len(credentials.regions) == 2
        assert "us-east-1" in credentials.regions

    def test_cloud_credentials_context_azure(self):
        """
        MCP-002: CloudCredentialsContext Azure構成
        覆盖代码行: app/models/mcp.py:9-50

        测试目的:
          - 验证 Azure 认证信息配置
        """
        # Arrange
        credentials = CloudCredentialsContext(
            cloud_provider="azure",
            tenant_id="tenant-id-123",
            client_id="client-id-456",
            subscription_id="subscription-id-789"
        )

        # Assert
        assert credentials.cloud_provider == "azure"
        assert credentials.tenant_id == "tenant-id-123"
        assert credentials.client_id == "client-id-456"
        assert credentials.subscription_id == "subscription-id-789"

    def test_cloud_credentials_context_gcp(self):
        """
        MCP-003: CloudCredentialsContext GCP構成
        覆盖代码行: app/models/mcp.py:9-50

        测试目的:
          - 验证 GCP 认证信息配置
        """
        # Arrange
        credentials = CloudCredentialsContext(
            cloud_provider="gcp",
            project_id="my-gcp-project-123"
        )

        # Assert
        assert credentials.cloud_provider == "gcp"
        assert credentials.project_id == "my-gcp-project-123"

    def test_cloud_credentials_context_minimal(self):
        """
        MCP-004: CloudCredentialsContext 最小構成
        覆盖代码行: app/models/mcp.py:9-50

        测试目的:
          - 验证只有 cloud_provider 的最小配置
        """
        # Arrange
        credentials = CloudCredentialsContext(
            cloud_provider="aws"
        )

        # Assert
        assert credentials.cloud_provider == "aws"
        assert credentials.role_arn is None
        assert credentials.external_id is None
        assert credentials.regions is None


class TestEnumsNormal:
    """
    Enum 类型测试

    测试ID: MCP-005 ~ MCP-006
    """

    def test_mcp_tool_type_enum(self):
        """
        MCP-005: MCPToolType Enum
        覆盖代码行: app/models/mcp.py:53-56

        测试目的:
          - 验证 MCPToolType 枚举值
        """
        # Assert
        assert MCPToolType.FUNCTION == "function"
        assert MCPToolType.RESOURCE == "resource"
        assert MCPToolType.PROMPT == "prompt"

    def test_sse_event_type_enum(self):
        """
        MCP-006: SSEEventType Enum
        覆盖代码行: app/models/mcp.py:59-76

        测试目的:
          - 验证 SSEEventType 枚举值（包含新增的事件类型）
        """
        # Assert - 既存イベント
        assert SSEEventType.ORCHESTRATOR == "orchestrator"
        assert SSEEventType.TASK_START == "task_start"
        assert SSEEventType.TASK_COMPLETE == "task_complete"
        assert SSEEventType.RESPONSE == "response"
        assert SSEEventType.ERROR == "error"
        assert SSEEventType.DONE == "done"

        # Assert - 新規イベント
        assert SSEEventType.RESPONSE_CHUNK == "response_chunk"
        assert SSEEventType.LLM_START == "llm_start"
        assert SSEEventType.LLM_END == "llm_end"
        assert SSEEventType.TOOL_START == "tool_start"
        assert SSEEventType.TOOL_END == "tool_end"


class TestMCPToolNormal:
    """
    MCPTool 和相关模型测试

    测试ID: MCP-007 ~ MCP-009
    """

    def test_mcp_tool_parameter(self):
        """
        MCP-007: MCPToolParameter
        覆盖代码行: app/models/mcp.py:79-84

        测试目的:
          - 验证工具参数定义
        """
        # Arrange
        param = MCPToolParameter(
            name="query",
            type="string",
            description="検索クエリ",
            required=True
        )

        # Assert
        assert param.name == "query"
        assert param.type == "string"
        assert param.description == "検索クエリ"
        assert param.required is True
        assert param.default is None

    def test_mcp_tool_basic(self):
        """
        MCP-008: MCPTool 基本構成
        覆盖代码行: app/models/mcp.py:87-93

        测试目的:
          - 验证基本的 MCPTool 定义
        """
        # Arrange
        tool = MCPTool(
            name="search_documents",
            description="ドキュメントを検索するツール"
        )

        # Assert
        assert tool.name == "search_documents"
        assert tool.description == "ドキュメントを検索するツール"
        assert tool.type == MCPToolType.FUNCTION
        assert tool.parameters == []
        assert tool.schema is None

    def test_mcp_tool_with_parameters(self):
        """
        MCP-009: MCPTool パラメータ付き
        覆盖代码行: app/models/mcp.py:87-93

        测试目的:
          - 验证带参数的 MCPTool
        """
        # Arrange
        params = [
            MCPToolParameter(name="query", type="string", description="検索クエリ"),
            MCPToolParameter(name="limit", type="integer", description="結果数", required=False, default=10)
        ]

        tool = MCPTool(
            name="search",
            description="検索ツール",
            type=MCPToolType.FUNCTION,
            parameters=params
        )

        # Assert
        assert len(tool.parameters) == 2
        assert tool.parameters[0].name == "query"
        assert tool.parameters[1].default == 10


class TestMCPServerNormal:
    """
    MCPServer 测试

    测试ID: MCP-010 ~ MCP-011
    """

    def test_mcp_server_basic(self):
        """
        MCP-010: MCPServer 基本構成
        覆盖代码行: app/models/mcp.py:96-103

        测试目的:
          - 验证基本的 MCPServer 配置
        """
        # Arrange
        server = MCPServer(
            name="document_server",
            command="/usr/bin/python",
            args=["server.py", "--port", "8000"]
        )

        # Assert
        assert server.name == "document_server"
        assert server.command == "/usr/bin/python"
        assert len(server.args) == 3
        assert server.enabled is True
        assert server.env == {}

    def test_mcp_server_full(self):
        """
        MCP-011: MCPServer 完全構成
        覆盖代码行: app/models/mcp.py:96-103

        测试目的:
          - 验证完整配置的 MCPServer
        """
        # Arrange
        server = MCPServer(
            name="doc_server",
            command="/usr/bin/python",
            args=["server.py"],
            env={"PYTHONPATH": "/app", "DEBUG": "true"},
            enabled=False,
            description="ドキュメントサーバー"
        )

        # Assert
        assert server.enabled is False
        assert server.env["PYTHONPATH"] == "/app"
        assert server.description == "ドキュメントサーバー"


class TestMCPChatModelsNormal:
    """
    MCPChat 相关模型测试

    测试ID: MCP-012 ~ MCP-014
    """

    def test_mcp_chat_message_basic(self):
        """
        MCP-012: MCPChatMessage 基本
        覆盖代码行: app/models/mcp.py:118-125

        测试目的:
          - 验证基本的聊天消息
        """
        # Arrange
        message = MCPChatMessage(
            role="user",
            content="こんにちは"
        )

        # Assert
        assert message.role == "user"
        assert message.content == "こんにちは"
        assert message.tool_calls is None
        assert message.tool_results is None

    def test_mcp_chat_message_with_tools(self):
        """
        MCP-013: MCPChatMessage ツール呼び出し付き
        覆盖代码行: app/models/mcp.py:118-125

        测试目的:
          - 验证带工具调用的消息
        """
        # Arrange
        tool_call = MCPToolCall(
            tool_name="search",
            parameters={"query": "test"}
        )

        tool_result = MCPToolResult(
            success=True,
            content="検索結果"
        )

        message = MCPChatMessage(
            role="assistant",
            content="検索を実行しました",
            tool_calls=[tool_call],
            tool_results=[tool_result]
        )

        # Assert
        assert len(message.tool_calls) == 1
        assert len(message.tool_results) == 1
        assert message.tool_calls[0].tool_name == "search"
        assert message.tool_results[0].success is True

    def test_sub_task_result_completed(self):
        """
        MCP-014: SubTaskResult 完了
        覆盖代码行: app/models/mcp.py:128-134

        测试目的:
          - 验证完成的子任务结果
        """
        # Arrange
        sub_task = SubTaskResult(
            id="task-001",
            description="EC2インスタンスのリスト取得",
            status="completed",
            tool="aws.list_ec2_instances",
            result="5個のインスタンスが見つかりました"
        )

        # Assert
        assert sub_task.id == "task-001"
        assert sub_task.status == "completed"
        assert sub_task.tool == "aws.list_ec2_instances"
        assert sub_task.error is None


class TestTaskManagementModelsNormal:
    """
    タスク管理モデルテスト

    測試ID: MCP-015 ~ MCP-017
    """

    def test_todo_item_pending(self):
        """
        MCP-015: TodoItem pending
        覆盖代码行: app/models/mcp.py:144-155

        测试目的:
          - 验证 pending 状态的 TodoItem
        """
        # Arrange
        todo = TodoItem(
            id="todo-001",
            description="データベースの設定を確認",
            status="pending",
            tool="database.check_config"
        )

        # Assert
        assert todo.id == "todo-001"
        assert todo.status == "pending"
        assert todo.result is None
        assert todo.error is None

    def test_todo_item_completed(self):
        """
        MCP-016: TodoItem completed
        覆盖代码行: app/models/mcp.py:144-155

        测试目的:
          - 验证 completed 状态的 TodoItem
        """
        # Arrange
        todo = TodoItem(
            id="todo-002",
            description="ログを分析",
            status="completed",
            tool="log.analyze",
            result="エラーは見つかりませんでした"
        )

        # Assert
        assert todo.status == "completed"
        assert todo.result == "エラーは見つかりませんでした"

    def test_thinking_log(self):
        """
        MCP-017: ThinkingLog
        覆盖代码行: app/models/mcp.py:158-168

        测试目的:
          - 验证思考过程日志
        """
        # Arrange
        log = ThinkingLog(
            timestamp="2026-03-10T12:00:00Z",
            content="ユーザーはEC2インスタンスの情報を求めている",
            source="orchestrator"
        )

        # Assert
        assert log.timestamp == "2026-03-10T12:00:00Z"
        assert log.content == "ユーザーはEC2インスタンスの情報を求めている"
        assert log.source == "orchestrator"


class TestMCPRequestResponseNormal:
    """
    MCP リクエスト/レスポンスモデルテスト

    測試ID: MCP-018 ~ MCP-020
    """

    def test_mcp_chat_request(self):
        """
        MCP-018: MCPChatRequest
        覆盖代码行: app/models/mcp.py:208-219

        测试目的:
          - 验证 MCPChatRequest 基本配置
        """
        # Arrange
        request = MCPChatRequest(
            session_id="user123:session-001",
            message="EC2インスタンスを教えてください",
            server_name="aws",
            use_hierarchical=True
        )

        # Assert
        assert request.session_id == "user123:session-001"
        assert request.message == "EC2インスタンスを教えてください"
        assert request.server_name == "aws"
        assert request.use_hierarchical is True

    def test_mcp_chat_stream_request(self):
        """
        MCP-019: MCPChatStreamRequest
        覆盖代码行: app/models/mcp.py:222-254

        测试目的:
          - 验证 SSE 流式请求配置（包含认证信息）
        """
        # Arrange
        credentials = CloudCredentialsContext(
            cloud_provider="aws",
            role_arn="arn:aws:iam::123456789012:role/MyRole"
        )

        request = MCPChatStreamRequest(
            session_id="user123:session-001",
            message="テスト",
            user_id="user123",
            auth_hash="SHARED-HMAC-1234567890-hash123",
            include_token_stream=True,
            cloud_credentials=credentials
        )

        # Assert
        assert request.user_id == "user123"
        assert request.auth_hash.startswith("SHARED-HMAC-")
        assert request.include_token_stream is True
        assert request.cloud_credentials.cloud_provider == "aws"

    def test_mcp_chat_response_full(self):
        """
        MCP-020: MCPChatResponse 完全構成
        覆盖代码行: app/models/mcp.py:257-289

        测试目的:
          - 验证完整的 MCPChatResponse（包含新增字段）
        """
        # Arrange
        todo = TodoItem(
            id="todo-001",
            description="タスク1",
            status="completed",
            result="完了"
        )

        thinking = ThinkingLog(
            timestamp="2026-03-10T12:00:00Z",
            content="分析中",
            source="orchestrator"
        )

        validation = ValidationResult(
            is_valid=True,
            retry_count=0,
            message="ポリシーは有効です"
        )

        response = MCPChatResponse(
            response="回答です",
            session_id="session-001",
            todos=[todo],
            thinking_logs=[thinking],
            validation_result=validation
        )

        # Assert
        assert response.response == "回答です"
        assert len(response.todos) == 1
        assert len(response.thinking_logs) == 1
        assert response.validation_result.is_valid is True


class TestSessionModelsNormal:
    """
    セッション管理モデルテスト

    測試ID: MCP-021 ~ MCP-022
    """

    def test_session_info(self):
        """
        MCP-021: SessionInfo
        覆盖代码行: app/models/mcp.py:320-327

        测试目的:
          - 验证会话信息模型
        """
        # Arrange
        session = SessionInfo(
            session_id="user123:20260310_abc123",
            name="AWSインフラ調査",
            checkpoint_count=5,
            last_updated="2026-03-10T12:00:00Z",
            preview="EC2インスタンスについて質問しました"
        )

        # Assert
        assert session.session_id == "user123:20260310_abc123"
        assert session.name == "AWSインフラ調査"
        assert session.checkpoint_count == 5

    def test_session_list_response(self):
        """
        MCP-022: SessionListResponse
        覆盖代码行: app/models/mcp.py:330-342

        测试目的:
          - 验证会话列表响应
        """
        # Arrange
        sessions = [
            SessionInfo(
                session_id=f"user123:session-{i}",
                name=f"セッション{i}",
                checkpoint_count=i
            )
            for i in range(1, 4)
        ]

        response = SessionListResponse(
            total=10,
            sessions=sessions,
            limit=50,
            offset=0
        )

        # Assert
        assert response.total == 10
        assert len(response.sessions) == 3
        assert response.limit == 50
        assert response.offset == 0


class TestCloudCredentialsContextErrors:
    """
    CloudCredentialsContext 異常系テスト

    測試ID: MCP-E01
    """

    def test_cloud_credentials_invalid_provider(self):
        """
        MCP-E01: CloudCredentialsContext 無効なクラウドプロバイダー
        覆盖代码行: app/models/mcp.py:9-50

        测试目的:
          - 验证无效的 cloud_provider 会抛出 ValidationError
        """
        # Arrange & Act & Assert
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            CloudCredentialsContext(
                cloud_provider="invalid_cloud"
            )

        assert "cloud_provider" in str(exc_info.value)


class TestMCPChatRequestErrors:
    """
    MCPChatRequest 異常系テスト

    測試ID: MCP-E02 ~ MCP-E03
    """

    def test_mcp_chat_request_missing_required(self):
        """
        MCP-E02: MCPChatRequest 必須フィールド欠落
        覆盖代码行: app/models/mcp.py:208-219

        测试目的:
          - 验证缺少必填字段时抛出 ValidationError
        """
        # Arrange & Act & Assert
        from pydantic import ValidationError

        # session_id 欠落
        with pytest.raises(ValidationError) as exc_info:
            MCPChatRequest(
                message="テスト"
            )
        assert "session_id" in str(exc_info.value)

        # message 欠落
        with pytest.raises(ValidationError) as exc_info:
            MCPChatRequest(
                session_id="session-001"
            )
        assert "message" in str(exc_info.value)

    def test_mcp_chat_stream_request_invalid_type(self):
        """
        MCP-E03: MCPChatStreamRequest 無効な型
        覆盖代码行: app/models/mcp.py:222-254

        测试目的:
          - 验证 Pydantic 的类型转换行为
          - 字符串 "true" 会被转换为 bool True
        """
        # Arrange & Act
        from pydantic import ValidationError

        # include_token_stream が文字列 - Pydantic は bool に変換
        request = MCPChatStreamRequest(
            session_id="session-001",
            message="テスト",
            include_token_stream="true"  # Pydantic v2 会转换为 True
        )

        # Assert - 验证转换成功
        assert request.include_token_stream is True


class TestValidationResultErrors:
    """
    ValidationResult 異常系テスト

    測試ID: MCP-E04 ~ MCP-E05
    """

    def test_validation_result_missing_required(self):
        """
        MCP-E04: ValidationResult 必須フィールド欠落
        覆盖代码行: app/models/mcp.py:171-177

        测试目的:
          - 验证缺少 is_valid 字段时抛出错误
        """
        # Arrange & Act & Assert
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            ValidationResult(
                retry_count=0
            )
        assert "is_valid" in str(exc_info.value)

    def test_session_update_request_name_too_long(self):
        """
        MCP-E05: SessionUpdateRequest 名前が長すぎる
        覆盖代码行: app/models/mcp.py:345-354

        测试目的:
          - 验证 name 字段的 max_length 限制
        """
        # Arrange & Act & Assert
        from pydantic import ValidationError

        # 100文字を超える名前
        with pytest.raises(ValidationError) as exc_info:
            SessionUpdateRequest(
                name="a" * 101
            )
        assert "String should have at most 100 characters" in str(exc_info.value)


class TestModelOperations:
    """
    モデル操作テスト (Pydantic v2 API)

    測試ID: MCP-023
    """

    def test_model_dump_and_validate(self):
        """
        MCP-023: model_dump と model_validate
        覆盖代码行: app/models/mcp.py (全体)

        测试目的:
          - 验证 Pydantic v2 的序列化/反序列化
        """
        # Arrange
        original = MCPChatRequest(
            session_id="session-001",
            message="テストメッセージ",
            use_hierarchical=True
        )

        # Act - 辞書に変換
        data_dict = original.model_dump()

        # 辞書から復元
        restored = MCPChatRequest.model_validate(data_dict)

        # Assert
        assert restored.session_id == original.session_id
        assert restored.message == original.message
        assert restored.use_hierarchical == original.use_hierarchical


# ============================================
# 补充缺失的正常系测试 (25个)
# ============================================

class TestMCPToolModels:
    """MCP 工具相关模型测试 (补充)"""

    def test_mcp_tool_call_defaults(self):
        """
        MCPMOD-010: MCPToolCall デフォルト値

        测试目的:
          - 验证 MCPToolCall 的默认值
          - tool_name 为必填, parameters 默认为空字典
        """
        # Arrange & Act
        tool_call = MCPToolCall(tool_name="search_files")

        # Assert
        assert tool_call.tool_name == "search_files"
        assert tool_call.parameters == {}

    def test_mcp_tool_result_success(self):
        """
        MCPMOD-011: MCPToolResult 成功ケース

        测试目的:
          - 验证成功的工具执行结果
        """
        # Arrange & Act
        result = MCPToolResult(
            success=True,
            content="Tool executed successfully"
        )

        # Assert
        assert result.success is True
        assert result.content == "Tool executed successfully"
        assert result.error is None

    def test_mcp_tool_result_failure(self):
        """
        MCPMOD-012: MCPToolResult 失敗ケース

        测试目的:
          - 验证失败的工具执行结果
        """
        # Arrange & Act
        result = MCPToolResult(
            success=False,
            error="Connection timeout"
        )

        # Assert
        assert result.success is False
        assert result.error == "Connection timeout"
        assert result.content is None


class TestMCPValidationProgress:
    """MCP 验证和进度模型测试 (补充)"""

    def test_validation_result_defaults(self):
        """
        MCPMOD-018: ValidationResult デフォルト値

        测试目的:
          - 验证 ValidationResult 的默认值
          - retry_count 默认为 0
        """
        # Arrange & Act
        validation = ValidationResult(is_valid=True)

        # Assert
        assert validation.is_valid is True
        assert validation.retry_count == 0
        assert validation.message is None

    def test_mcp_progress_defaults(self):
        """
        MCPMOD-019: MCPProgress デフォルト値

        测试目的:
          - 验证 MCPProgress 的默认值
          - sub_tasks 默认为空列表, llm_calls 默认为 0
        """
        # Arrange & Act
        progress = MCPProgress()

        # Assert
        assert progress.sub_tasks == []
        assert progress.llm_calls == 0
        assert progress.task_analysis is None
        assert progress.completed_tools is None  # 使用实际存在的字段

    def test_validation_result_failure_case(self):
        """
        MCPMOD-038: ValidationResult 検証失敗ケース

        测试目的:
          - 验证失败的验证结果
        """
        # Arrange & Act
        validation = ValidationResult(
            is_valid=False,
            message="Schema validation failed",
            retry_count=3
        )

        # Assert
        assert validation.is_valid is False
        assert validation.message == "Schema validation failed"
        assert validation.retry_count == 3

    def test_mcp_progress_with_data(self):
        """
        MCPMOD-039: MCPProgress データ付き

        测试目的:
          - 验证带数据的进度信息
        """
        # Arrange
        sub_tasks = [
            SubTaskResult(
                id="task-1",
                description="Analyze policy",
                status="completed"
            )
        ]

        # Act
        progress = MCPProgress(
            task_analysis="Analyzing AWS policies",
            completed_tools=["search_files", "list_resources"],  # 使用实际存在的字段
            sub_tasks=sub_tasks,
            llm_calls=10
        )

        # Assert
        assert progress.task_analysis == "Analyzing AWS policies"
        assert progress.completed_tools == ["search_files", "list_resources"]
        assert len(progress.sub_tasks) == 1
        assert progress.llm_calls == 10


class TestMCPServerModels:
    """MCP 服务器相关模型测试 (补充)"""

    def test_mcp_server_list_response_empty(self):
        """
        MCPMOD-024: MCPServerListResponse 空リスト

        测试目的:
          - 验证空服务器列表
        """
        # Arrange & Act
        response = MCPServerListResponse(servers=[])

        # Assert
        assert response.servers == []
        assert len(response.servers) == 0

    def test_mcp_server_list_response_multiple(self):
        """
        MCPMOD-025: MCPServerListResponse 複数サーバー

        测试目的:
          - 验证多个服务器的列表
        """
        # Arrange
        servers = [
            MCPServer(name="server1", command="mcp-server-1"),
            MCPServer(name="server2", command="mcp-server-2"),
            MCPServer(name="server3", command="mcp-server-3")
        ]

        # Act
        response = MCPServerListResponse(servers=servers)

        # Assert
        assert len(response.servers) == 3
        assert response.servers[0].name == "server1"
        assert response.servers[1].name == "server2"
        assert response.servers[2].name == "server3"

    def test_mcp_tool_list_response(self):
        """
        MCPMOD-026: MCPToolListResponse

        测试目的:
          - 验证工具列表响应
        """
        # Arrange
        tools = [
            MCPTool(name="tool1", description="Tool 1"),
            MCPTool(name="tool2", description="Tool 2")
        ]

        # Act
        response = MCPToolListResponse(
            tools=tools,
            server_name="test-server"
        )

        # Assert
        assert len(response.tools) == 2
        assert response.server_name == "test-server"
        assert response.tools[0].name == "tool1"

    def test_mcp_server_status_defaults(self):
        """
        MCPMOD-027: MCPServerStatus デフォルト値

        测试目的:
          - 验证服务器状态的默认值
          - available_tools 默认为空列表
        """
        # Arrange & Act
        status = MCPServerStatus(
            name="test-server",
            status="running"
        )

        # Assert
        assert status.name == "test-server"
        assert status.status == "running"
        assert status.available_tools == []

    def test_mcp_status_response(self):
        """
        MCPMOD-028: MCPStatusResponse

        测试目的:
          - 验证完整的状态响应
        """
        # Arrange
        servers = [
            MCPServerStatus(name="server1", status="running"),
            MCPServerStatus(name="server2", status="stopped")
        ]

        # Act
        response = MCPStatusResponse(
            servers=servers,
            total_tools=10,
            active_sessions=5
        )

        # Assert
        assert len(response.servers) == 2
        assert response.total_tools == 10
        assert response.active_sessions == 5


class TestMCPChatModels:
    """MCP 聊天模型测试 (补充)"""

    def test_mcp_chat_response_minimal(self):
        """
        MCPMOD-022: MCPChatResponse 最小構成

        测试目的:
          - 验证最小配置的聊天响应
        """
        # Arrange & Act
        response = MCPChatResponse(
            response="Hello, how can I help?",
            session_id="session-123"
        )

        # Assert
        assert response.response == "Hello, how can I help?"
        assert response.session_id == "session-123"
        assert response.tool_calls is None
        assert response.tool_results is None
        assert response.available_tools is None
        assert response.progress is None
        assert response.todos is None
        assert response.thinking_logs is None
        assert response.validation_result is None

    def test_mcp_chat_stream_request_with_credentials(self):
        """
        MCPMOD-036: MCPChatStreamRequest クラウド認証情報付き

        测试目的:
          - 验证带云认证信息的流式请求
        """
        # Arrange
        creds = CloudCredentialsContext(
            cloud_provider="aws",
            role_arn="arn:aws:iam::123456789012:role/TestRole",
            external_id="test-external-id"
        )

        # Act
        request = MCPChatStreamRequest(
            session_id="user123:session-456",
            message="Analyze AWS resources",
            user_id="user123",
            auth_hash="SHARED-HMAC-hash",
            cloud_credentials=creds
        )

        # Assert
        assert request.user_id == "user123"
        assert request.auth_hash == "SHARED-HMAC-hash"
        assert request.cloud_credentials is not None
        assert request.cloud_credentials.cloud_provider == "aws"
        assert request.cloud_credentials.role_arn == "arn:aws:iam::123456789012:role/TestRole"


class TestMCPTaskModels:
    """MCP 任务模型测试 (补充)"""

    def test_sub_task_result_with_tool_result(self):
        """
        MCPMOD-037: SubTaskResult ツール実行結果付き

        测试目的:
          - 验证带工具执行结果的子任务
          - result 字段是字符串类型，存储执行结果摘要
        """
        # Arrange - result 是字符串，而不是 MCPToolResult 对象
        result_summary = "File found: config.yaml"

        # Act
        sub_task = SubTaskResult(
            id="subtask-1",
            description="Search configuration file",
            status="completed",
            tool="search_files",
            result=result_summary  # 字符串类型
        )

        # Assert
        assert sub_task.id == "subtask-1"
        assert sub_task.tool == "search_files"
        assert sub_task.result is not None
        assert sub_task.result == "File found: config.yaml"
        assert isinstance(sub_task.result, str)


class TestMCPSessionModels:
    """MCP 会话模型测试 (补充)"""

    def test_session_update_request_boundary(self):
        """
        MCPMOD-031: SessionUpdateRequest 境界値 (100文字)

        测试目的:
          - 验证名称长度边界值 (max_length=100)
        """
        # Arrange
        name_100_chars = "A" * 100

        # Act
        request = SessionUpdateRequest(name=name_100_chars)

        # Assert
        assert len(request.name) == 100
        assert request.name == name_100_chars

    def test_session_info_full(self):
        """
        MCPMOD-040: SessionInfo 完全構成

        测试目的:
          - 验证完整配置的会话信息
        """
        # Arrange & Act
        session = SessionInfo(
            session_id="session-full-001",
            name="Complete Session",
            last_updated="2026-03-10T15:30:00Z",  # 使用实际存在的字段
            checkpoint_count=15,
            preview="Last message preview..."
        )

        # Assert
        assert session.session_id == "session-full-001"
        assert session.name == "Complete Session"
        assert session.last_updated == "2026-03-10T15:30:00Z"
        assert session.checkpoint_count == 15
        assert session.preview == "Last message preview..."

    def test_session_list_response_with_data(self):
        """
        MCPMOD-041: SessionListResponse データ付き

        测试目的:
          - 验证带数据的会话列表响应
        """
        # Arrange
        sessions = [
            SessionInfo(session_id="s1", checkpoint_count=5),
            SessionInfo(session_id="s2", checkpoint_count=10),
            SessionInfo(session_id="s3", checkpoint_count=3)
        ]

        # Act
        response = SessionListResponse(
            total=3,
            sessions=sessions,
            limit=10,
            offset=0
        )

        # Assert
        assert response.total == 3
        assert len(response.sessions) == 3
        assert response.limit == 10
        assert response.offset == 0
        assert response.sessions[1].checkpoint_count == 10


class TestMCPModelOperations:
    """MCP 模型操作测试 (补充)"""

    def test_json_round_trip(self):
        """
        MCPMOD-042: JSON往復変換テスト

        测试目的:
          - 验证 JSON 序列化和反序列化的数据一致性
        """
        # Arrange
        original = MCPChatResponse(
            response="Test response",
            session_id="session-roundtrip",
            progress=MCPProgress(
                task_analysis="Processing",
                llm_calls=5
            )
        )

        # Act - JSON 序列化
        json_str = original.model_dump_json()

        # JSON 反序列化
        restored = MCPChatResponse.model_validate_json(json_str)

        # Assert - 验证数据一致
        assert restored.response == original.response
        assert restored.session_id == original.session_id
        assert restored.progress is not None
        assert restored.progress.task_analysis == "Processing"
        assert restored.progress.llm_calls == 5

    def test_mutable_default_independence(self):
        """
        MCPMOD-043: ミュータブルデフォルトの独立性

        测试目的:
          - 验证可变默认值不会在实例间共享
          - 确保每个实例有独立的列表/字典
        """
        # Arrange & Act - 创建两个实例
        progress1 = MCPProgress()
        progress2 = MCPProgress()

        # 修改第一个实例
        progress1.sub_tasks.append(
            SubTaskResult(
                id="task-1",
                description="Task 1",
                status="pending"
            )
        )

        # Assert - 第二个实例不应受影响
        assert len(progress1.sub_tasks) == 1
        assert len(progress2.sub_tasks) == 0
        assert progress1.sub_tasks is not progress2.sub_tasks

        # 测试 MCPServer 的可变默认值
        server1 = MCPServer(name="s1", command="cmd1")
        server2 = MCPServer(name="s2", command="cmd2")

        server1.args.append("--verbose")
        server1.env["KEY"] = "value"

        assert len(server1.args) == 1
        assert len(server2.args) == 0
        assert server1.args is not server2.args
        assert server1.env is not server2.env


# ============================================
# 补充缺失的异常系测试 (12个)
# ============================================

class TestMCPValidationErrorsExtended:
    """MCP 模型验证错误测试 (补充)"""

    def test_cloud_credentials_missing_provider(self):
        """
        MCPMOD-E02: CloudCredentialsContext cloud_provider欠落

        测试目的:
          - 验证缺少必填字段 cloud_provider 时抛出错误
        """
        # Arrange & Act & Assert
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            CloudCredentialsContext()

        errors = exc_info.value.errors()
        assert any("cloud_provider" in str(e) for e in errors)

    def test_mcp_chat_stream_request_missing_required(self):
        """
        MCPMOD-E05: MCPChatStreamRequest 必須フィールド欠落

        测试目的:
          - 验证缺少必填字段时抛出错误
        """
        # Arrange & Act & Assert
        from pydantic import ValidationError

        # 缺少 session_id 和 message
        with pytest.raises(ValidationError) as exc_info:
            MCPChatStreamRequest()

        errors = exc_info.value.errors()
        assert len(errors) >= 2
        error_fields = {e['loc'][0] for e in errors}
        assert 'session_id' in error_fields
        assert 'message' in error_fields

    def test_mcp_chat_response_missing_response(self):
        """
        MCPMOD-E06: MCPChatResponse response欠落

        测试目的:
          - 验证缺少 response 字段时抛出错误
        """
        # Arrange & Act & Assert
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            MCPChatResponse(session_id="session-123")

        errors = exc_info.value.errors()
        assert any("response" in str(e) for e in errors)

    def test_mcp_chat_response_missing_session_id(self):
        """
        MCPMOD-E07: MCPChatResponse session_id欠落

        测试目的:
          - 验证缺少 session_id 字段时抛出错误
        """
        # Arrange & Act & Assert
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            MCPChatResponse(response="Hello")

        errors = exc_info.value.errors()
        assert any("session_id" in str(e) for e in errors)

    def test_sub_task_result_missing_required(self):
        """
        MCPMOD-E09: SubTaskResult 必須フィールド欠落

        测试目的:
          - 验证缺少必填字段时抛出错误
        """
        # Arrange & Act & Assert
        from pydantic import ValidationError

        # 只提供 id, 缺少 description 和 status
        with pytest.raises(ValidationError) as exc_info:
            SubTaskResult(id="task-1")

        errors = exc_info.value.errors()
        assert len(errors) >= 2

    def test_todo_item_missing_required(self):
        """
        MCPMOD-E10: TodoItem 必須フィールド欠落

        测试目的:
          - 验证缺少必填字段时抛出错误
        """
        # Arrange & Act & Assert
        from pydantic import ValidationError

        # 只提供 id
        with pytest.raises(ValidationError) as exc_info:
            TodoItem(id="todo-1")

        errors = exc_info.value.errors()
        assert len(errors) >= 2

    def test_thinking_log_missing_required(self):
        """
        MCPMOD-E11: ThinkingLog 必須フィールド欠落

        测试目的:
          - 验证缺少必填字段时抛出错误
        """
        # Arrange & Act & Assert
        from pydantic import ValidationError

        # 只提供 timestamp
        with pytest.raises(ValidationError) as exc_info:
            ThinkingLog(timestamp="2026-03-10T10:00:00Z")

        errors = exc_info.value.errors()
        assert len(errors) >= 2

    def test_mcp_tool_missing_required(self):
        """
        MCPMOD-E13: MCPTool 必須フィールド欠落

        测试目的:
          - 验证缺少必填字段时抛出错误
        """
        # Arrange & Act & Assert
        from pydantic import ValidationError

        # 只提供 name, 缺少 description
        with pytest.raises(ValidationError) as exc_info:
            MCPTool(name="tool1")

        errors = exc_info.value.errors()
        assert any("description" in str(e) for e in errors)

    def test_mcp_tool_parameter_missing_required(self):
        """
        MCPMOD-E14: MCPToolParameter 必須フィールド欠落

        测试目的:
          - 验证缺少必填字段时抛出错误
        """
        # Arrange & Act & Assert
        from pydantic import ValidationError

        # 只提供 name, 缺少 type
        with pytest.raises(ValidationError) as exc_info:
            MCPToolParameter(name="param1")

        errors = exc_info.value.errors()
        assert any("type" in str(e) for e in errors)

    def test_mcp_server_status_missing_required(self):
        """
        MCPMOD-E15: MCPServerStatus 必須フィールド欠落

        测试目的:
          - 验证缺少必填字段时抛出错误
        """
        # Arrange & Act & Assert
        from pydantic import ValidationError

        # 只提供 name, 缺少 status
        with pytest.raises(ValidationError) as exc_info:
            MCPServerStatus(name="server1")

        errors = exc_info.value.errors()
        assert any("status" in str(e) for e in errors)

    def test_mcp_status_response_missing_required(self):
        """
        MCPMOD-E16: MCPStatusResponse 必須フィールド欠落

        测试目的:
          - 验证缺少必填字段时抛出错误
        """
        # Arrange & Act & Assert
        from pydantic import ValidationError

        # 只提供 servers
        with pytest.raises(ValidationError) as exc_info:
            MCPStatusResponse(servers=[])

        errors = exc_info.value.errors()
        assert len(errors) >= 2  # total_tools 和 active_sessions

    def test_session_list_response_missing_total(self):
        """
        MCPMOD-E17: SessionListResponse total欠落

        测试目的:
          - 验证缺少必填字段 total 时抛出错误
        """
        # Arrange & Act & Assert
        from pydantic import ValidationError

        # 只提供 sessions
        with pytest.raises(ValidationError) as exc_info:
            SessionListResponse(sessions=[])

        errors = exc_info.value.errors()
        assert any("total" in str(e) for e in errors)


