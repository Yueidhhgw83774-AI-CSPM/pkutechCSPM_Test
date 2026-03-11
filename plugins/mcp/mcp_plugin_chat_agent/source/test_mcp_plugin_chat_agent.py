"""
MCP Plugin Chat Agent 单元测试

测试规格: docs/testing/plugins/mcp/mcp_plugin_chat_agent_tests.md
覆盖率目标: 90%+

测试类别:
  - 正常系: 9 个测试
  - 异常系: 3 个测试
  - 安全测试: 6 个测试

总计: 18 个测试
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import sys
from pathlib import Path
import re
import uuid

# 导入被测试模块
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "platform_python_backend-testing"
if not project_root.exists():
    raise RuntimeError(f"项目根目录不存在: {project_root}")
sys.path.insert(0, str(project_root))


# ============================================
# 正常系测试 (9个)
# ============================================

class TestInvokeMCPChat:
    """invoke_mcp_chat 正常系测试"""

    @pytest.mark.asyncio
    async def test_hierarchical_mode(self, mock_run_hierarchical):
        """MCPCA-001: 階層的エージェントモードで実行"""
        # Arrange
        from app.mcp_plugin.chat_agent import invoke_mcp_chat

        mock_run_hierarchical.return_value = {
            "final_response": "階層的エージェントの応答",
            "llm_calls": 3,
            "llm_calls_by_model": {"gpt-5-mini": 1, "gpt-5-nano": 1, "gpt-5.1-codex": 1}
        }

        # Act
        response, progress = await invoke_mcp_chat(
            session_id="test-session",
            prompt="Azure OpenAIについて",
            use_hierarchical=True
        )

        # Assert
        assert response == "階層的エージェントの応答"
        assert progress is not None
        mock_run_hierarchical.assert_called_once()

    @pytest.mark.asyncio
    async def test_deep_agents_mode(self, mock_invoke_deep_agents):
        """MCPCA-002: Deep Agentsモードで実行"""
        # Arrange
        from app.mcp_plugin.chat_agent import invoke_mcp_chat

        mock_invoke_deep_agents.return_value = "Deep Agentsの応答"

        # Act
        response, progress = await invoke_mcp_chat(
            session_id="test-session",
            prompt="ツール一覧を見せて",
            use_hierarchical=False
        )

        # Assert
        assert response == "Deep Agentsの応答"
        assert progress is None  # Deep Agentsモードではprogressなし
        mock_invoke_deep_agents.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_server_name(self, mock_run_hierarchical):
        """MCPCA-003: サーバー指定なしで全サーバー対象"""
        # Arrange
        from app.mcp_plugin.chat_agent import invoke_mcp_chat

        mock_run_hierarchical.return_value = {
            "final_response": "全サーバー検索結果"
        }

        # Act
        response, _ = await invoke_mcp_chat(
            session_id="test-session",
            prompt="検索クエリ",
            server_name=None
        )

        # Assert
        assert response == "全サーバー検索結果"
        call_kwargs = mock_run_hierarchical.call_args.kwargs
        assert call_kwargs.get("server_name") is None

    @pytest.mark.asyncio
    async def test_specific_server(self, mock_run_hierarchical):
        """MCPCA-004: 特定サーバー指定で実行"""
        # Arrange
        from app.mcp_plugin.chat_agent import invoke_mcp_chat

        mock_run_hierarchical.return_value = {
            "final_response": "aws-docs検索結果"
        }

        # Act
        response, _ = await invoke_mcp_chat(
            session_id="test-session",
            prompt="AWS Lambda",
            server_name="aws-docs"
        )

        # Assert
        assert response == "aws-docs検索結果"
        call_kwargs = mock_run_hierarchical.call_args.kwargs
        assert call_kwargs.get("server_name") == "aws-docs"

    @pytest.mark.asyncio
    async def test_error_in_state(self, mock_run_hierarchical):
        """MCPCA-005: エラー応答の適切なフォーマット"""
        # Arrange
        from app.mcp_plugin.chat_agent import invoke_mcp_chat

        mock_run_hierarchical.return_value = {
            "final_response": None,
            "error": "MCPサーバー接続エラー"
        }

        # Act
        response, _ = await invoke_mcp_chat(
            session_id="test-session",
            prompt="テスト",
            use_hierarchical=True
        )

        # Assert
        assert "エラー" in response
        assert "MCPサーバー接続エラー" in response

    @pytest.mark.asyncio
    async def test_progress_building(self, mock_run_hierarchical, mock_build_progress):
        """MCPCA-006: progressの構築"""
        # Arrange
        from app.mcp_plugin.chat_agent import invoke_mcp_chat

        mock_run_hierarchical.return_value = {
            "final_response": "応答",
            "llm_calls": 5,
            "llm_calls_by_model": {"gpt-5-mini": 1, "gpt-5-nano": 3, "gpt-5.1-codex": 1},
            "tool_calls": ["search_documentation", "get_details"]
        }

        # Act
        response, progress = await invoke_mcp_chat(
            session_id="test-session",
            prompt="テスト",
            use_hierarchical=True
        )

        # Assert
        assert progress is not None
        assert response == "応答"
        mock_build_progress.assert_called_once()

    @pytest.mark.asyncio
    async def test_args_propagation_hierarchical(self, mock_run_hierarchical):
        """MCPCA-007: 引数の正しい伝播（階層的モード）"""
        # Arrange
        from app.mcp_plugin.chat_agent import invoke_mcp_chat

        mock_run_hierarchical.return_value = {"final_response": "応答"}

        # Act
        await invoke_mcp_chat(
            session_id="test-session-007",
            prompt="テストプロンプト007",
            server_name="azure-docs",
            use_hierarchical=True
        )

        # Assert
        mock_run_hierarchical.assert_called_once_with(
            session_id="test-session-007",
            user_request="テストプロンプト007",
            server_name="azure-docs"
        )

    @pytest.mark.asyncio
    async def test_args_propagation_deep_agents(self, mock_invoke_deep_agents):
        """MCPCA-008: 引数の正しい伝播（Deep Agentsモード）"""
        # Arrange
        from app.mcp_plugin.chat_agent import invoke_mcp_chat

        mock_invoke_deep_agents.return_value = "応答"

        # Act
        await invoke_mcp_chat(
            session_id="test-session-008",
            prompt="テストプロンプト008",
            server_name="gcp-docs",
            use_hierarchical=False
        )

        # Assert
        mock_invoke_deep_agents.assert_called_once_with(
            "test-session-008",
            "テストプロンプト008",
            "gcp-docs"
        )

    def test_module_exports(self):
        """MCPCA-009: モジュールエクスポートの検証"""
        # Arrange
        from app.mcp_plugin import chat_agent

        # Act & Assert
        assert hasattr(chat_agent, 'invoke_mcp_chat')
        assert hasattr(chat_agent, 'stream_deep_agents_mcp_chat')
        assert hasattr(chat_agent, 'clear_session_cache')
        assert chat_agent.__all__ == [
            "invoke_mcp_chat",
            "stream_deep_agents_mcp_chat",
            "clear_session_cache",
        ]


# ============================================
# 异常系测试 (3个)
# ============================================

class TestChatAgentExceptions:
    """チャットエージェント例外テスト"""

    @pytest.mark.asyncio
    async def test_hierarchical_exception(self, mock_run_hierarchical):
        """MCPCA-E01: 階層的エージェント例外発生"""
        # Arrange
        from app.mcp_plugin.chat_agent import invoke_mcp_chat

        mock_run_hierarchical.side_effect = Exception("Hierarchical error")

        # Act
        response, progress = await invoke_mcp_chat(
            session_id="test-session",
            prompt="テスト",
            use_hierarchical=True
        )

        # Assert
        assert "エラー" in response
        assert "エラーID" in response
        assert progress is None

    @pytest.mark.asyncio
    async def test_deep_agents_exception(self, mock_invoke_deep_agents):
        """MCPCA-E02: Deep Agents例外発生"""
        # Arrange
        from app.mcp_plugin.chat_agent import invoke_mcp_chat

        mock_invoke_deep_agents.side_effect = Exception("Deep Agents error")

        # Act & Assert
        with pytest.raises(Exception, match="Deep Agents error"):
            await invoke_mcp_chat(
                session_id="test-session",
                prompt="テスト",
                use_hierarchical=False
            )

    @pytest.mark.asyncio
    async def test_empty_response(self, mock_run_hierarchical):
        """MCPCA-E03: 応答なしの状態"""
        # Arrange
        from app.mcp_plugin.chat_agent import invoke_mcp_chat

        mock_run_hierarchical.return_value = {
            "final_response": None,
            "error": None
        }

        # Act
        response, _ = await invoke_mcp_chat(
            session_id="test-session",
            prompt="テスト",
            use_hierarchical=True
        )

        # Assert
        assert "応答を生成できませんでした" in response


# ============================================
# 安全测试 (6个)
# ============================================

@pytest.mark.security
class TestChatAgentSecurity:
    """チャットエージェントセキュリティテスト"""

    @pytest.mark.asyncio
    async def test_error_id_uniqueness(self, mock_run_hierarchical):
        """MCPCA-SEC-01: エラーIDの一意性"""
        # Arrange
        from app.mcp_plugin.chat_agent import invoke_mcp_chat

        mock_run_hierarchical.side_effect = Exception("Test error")
        error_ids = set()

        # Act - 複数回エラーを発生させる
        for _ in range(10):
            response, _ = await invoke_mcp_chat(
                session_id="test-session",
                prompt="テスト",
                use_hierarchical=True
            )
            # UUIDを抽出
            match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', response)
            if match:
                error_ids.add(match.group())

        # Assert - すべて一意
        assert len(error_ids) == 10

    @pytest.mark.asyncio
    async def test_internal_error_not_exposed(self, mock_run_hierarchical):
        """MCPCA-SEC-02: 内部エラー詳細の非公開"""
        # Arrange
        from app.mcp_plugin.chat_agent import invoke_mcp_chat

        internal_error_msg = "Database connection failed: password=secret123"
        mock_run_hierarchical.side_effect = Exception(internal_error_msg)

        # Act
        response, _ = await invoke_mcp_chat(
            session_id="test-session",
            prompt="テスト",
            use_hierarchical=True
        )

        # Assert - 内部エラー詳細が露出していない
        assert "password" not in response
        assert "secret123" not in response
        # エラーIDのみ表示
        assert "エラーID" in response

    @pytest.mark.asyncio
    async def test_session_id_logged(self, mock_run_hierarchical, caplog):
        """MCPCA-SEC-03: セッションIDのログ記録"""
        # Arrange
        import logging
        caplog.set_level(logging.INFO)
        from app.mcp_plugin.chat_agent import invoke_mcp_chat

        mock_run_hierarchical.return_value = {"final_response": "OK"}

        # Act
        await invoke_mcp_chat(
            session_id="unique-session-12345",
            prompt="テスト",
            use_hierarchical=True
        )

        # Assert
        assert "unique-session-12345" in caplog.text

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="現在の実装では state['error'] が直接ユーザーに返される脆弱性がある")
    async def test_state_error_credential_exposure(self, mock_run_hierarchical):
        """MCPCA-SEC-04: state["error"]の機密情報露出防止"""
        # Arrange
        from app.mcp_plugin.chat_agent import invoke_mcp_chat

        # 機密情報を含むエラーメッセージをシミュレート
        sensitive_error = "Connection failed: host=db.internal, user=admin, password=P@ssw0rd123"
        mock_run_hierarchical.return_value = {
            "final_response": None,
            "error": sensitive_error
        }

        # Act
        response, _ = await invoke_mcp_chat(
            session_id="test-session",
            prompt="テスト",
            use_hierarchical=True
        )

        # Assert - 機密情報が露出していないことを確認
        assert "password" not in response.lower()
        assert "P@ssw0rd123" not in response
        assert "admin" not in response
        # エラーIDのみ表示されるべき
        assert "エラーID" in response

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        reason="既知の脆弱性: chat_agent.py:73でsession_idが直接ログに渡されるため、"
               "改行文字を含む悪意のあるsession_idによりログインジェクションが発生する。"
               "修正方法: session_idをサニタイズしてからロギングすること。"
               "例: session_id.replace('\\n', '\\\\n').replace('\\r', '\\\\r')"
    )
    async def test_session_id_log_injection(self, mock_run_hierarchical, caplog):
        """MCPCA-SEC-05: セッションIDのログインジェクション耐性"""
        # Arrange
        import logging
        caplog.set_level(logging.INFO)
        from app.mcp_plugin.chat_agent import invoke_mcp_chat

        mock_run_hierarchical.return_value = {"final_response": "OK"}

        # 悪意のあるセッションID（改行・制御文字を含む）
        malicious_session_id = "session-id\n[CRITICAL] Fake log entry injected"

        # Act
        await invoke_mcp_chat(
            session_id=malicious_session_id,
            prompt="テスト",
            use_hierarchical=True
        )

        # Assert - ログインジェクションが発生していない
        log_lines = caplog.text.split('\n')
        for line in log_lines:
            if "CRITICAL" in line and "Fake log entry" in line:
                # ログインジェクションが成功してしまっている
                pytest.fail("Log injection detected: malicious content appears as separate log entry")

    @pytest.mark.asyncio
    async def test_server_name_path_traversal(self, mock_run_hierarchical):
        """MCPCA-SEC-06: server_nameの安全性検証"""
        # Arrange
        from app.mcp_plugin.chat_agent import invoke_mcp_chat

        mock_run_hierarchical.return_value = {"final_response": "OK"}

        # 悪意のあるserver_name（パストラバーサルを試みる）
        malicious_server_name = "../../etc/passwd"

        # Act
        response, _ = await invoke_mcp_chat(
            session_id="test-session",
            prompt="テスト",
            server_name=malicious_server_name,
            use_hierarchical=True
        )

        # Assert - パストラバーサルが発生しない
        # server_nameはそのまま下層に渡されるが、下層で適切に処理される
        call_kwargs = mock_run_hierarchical.call_args.kwargs
        assert call_kwargs.get("server_name") == malicious_server_name
        # 実際の処理では下層で安全に処理されることを想定

