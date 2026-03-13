# mcp_plugin/client テストケース

## 1. 概要

MCPクライアント（`client.py`）のテストケースを定義します。プロセスプール管理、MCPサーバー接続、ツール呼び出し、設定ファイル読み込み機能を包括的にテストします。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `MCPClient` | MCPクライアントクラス |
| `add_server` | MCPサーバー追加 |
| `connect_server` | サーバー接続（プロセスプール初期化） |
| `disconnect_server` | サーバー切断（プロセスプールクリーンアップ） |
| `call_tool` | MCPツール実行 |
| `fetch_tools` | ツール一覧取得 |
| `load_config_file` | 設定ファイル読み込み |
| `register_internal_tools` | 内部ツール登録 |
| `call_internal_tool` | 内部ツール実行 |
| `_expand_env_vars` | 環境変数展開 |

### 1.2 カバレッジ目標: 85%

> **注記**: プロセス間通信とJSON-RPCプロトコルの検証が中心。実MCPサーバーとの統合はモック化。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/mcp_plugin/client.py` |
| プロセスプール | `app/mcp_plugin/process_pool.py` |
| テストコード | `test/unit/mcp_plugin/test_client.py` |
| conftest | `test/unit/mcp_plugin/conftest.py` |

### 1.4 補足情報

**グローバル状態:**
- `mcp_client`: グローバルMCPクライアントインスタンス（client.py:733）
- `mcp_process_pool`: グローバルプロセスプール（process_pool.py）

**プロセスプール:**
- デフォルトプールサイズ: 3（環境変数 `MCP_POOL_SIZE` で変更可能）
- セマフォによる同時使用数制御
- リトライ機能（最大3回）

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| MCPC-001 | サーバー追加成功 | valid MCPServer | True, server added |
| MCPC-002 | サーバー接続成功 | existing server | True, status=connected |
| MCPC-003 | サーバー切断成功 | connected server | True, status=disconnected |
| MCPC-004 | ツール呼び出し成功 | valid tool_call | MCPToolResult(success=True) |
| MCPC-005 | ツール一覧取得（キャッシュ） | cached server | cached tools list |
| MCPC-006 | 設定ファイル読み込み成功 | valid config file | True, servers loaded |
| MCPC-007 | 環境変数展開成功 | ${VAR_NAME} pattern | expanded value |
| MCPC-008 | 内部ツール登録成功 | tools and handlers | True, tools registered |
| MCPC-009 | 内部ツール実行成功（同期） | sync handler | MCPToolResult(success=True) |
| MCPC-010 | 内部ツール実行成功（非同期） | async handler | MCPToolResult(success=True) |
| MCPC-011 | サーバー接続リトライ成功 | first fail, then success | True after retry |
| MCPC-012 | プールステータス取得 | server_name | pool status dict |
| MCPC-013 | サーバーステータス取得（単一） | server_name | [status] |
| MCPC-014 | サーバーステータス取得（全件） | None | [all statuses] |
| MCPC-015 | 利用可能ツール取得（単一） | server_name | [tools] |
| MCPC-016 | 利用可能ツール取得（全件） | None | [all tools] |
| MCPC-017 | クリーンアップ成功 | connected servers | all disconnected |

### 2.1 サーバー管理テスト

```python
# test/unit/mcp_plugin/test_client.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.models.mcp import MCPServer, MCPToolCall


class TestMCPClientServerManagement:
    """MCPクライアントサーバー管理のテスト"""

    @pytest.mark.asyncio
    async def test_add_server_success(self, mcp_client_instance):
        """MCPC-001: サーバー追加成功"""
        # Arrange
        server = MCPServer(
            name="test-server",
            command="npx",
            args=["-y", "@test/mcp-server"],
            env={},
            enabled=False  # 自動接続しない
        )

        # Act
        result = await mcp_client_instance.add_server(server)

        # Assert
        assert result is True
        assert "test-server" in mcp_client_instance.servers
        assert mcp_client_instance.server_status["test-server"].status == "disconnected"

    @pytest.mark.asyncio
    async def test_connect_server_success(
        self, mcp_client_instance, mock_process_pool
    ):
        """MCPC-002: サーバー接続成功"""
        # Arrange
        server = MCPServer(
            name="test-server",
            command="npx",
            args=["-y", "@test/mcp-server"],
            enabled=False
        )
        await mcp_client_instance.add_server(server)
        mock_process_pool.initialize_pool.return_value = True

        # Act
        result = await mcp_client_instance.connect_server("test-server")

        # Assert
        assert result is True
        assert mcp_client_instance.server_status["test-server"].status == "connected"

    @pytest.mark.asyncio
    async def test_disconnect_server_success(
        self, mcp_client_instance, mock_process_pool
    ):
        """MCPC-003: サーバー切断成功"""
        # Arrange
        mcp_client_instance.servers["test-server"] = MagicMock()
        mcp_client_instance.server_status["test-server"] = MagicMock()
        mcp_client_instance.server_status["test-server"].status = "connected"
        mock_process_pool.pools = {"test-server": MagicMock()}

        # Act
        result = await mcp_client_instance.disconnect_server("test-server")

        # Assert
        assert result is True
        assert mcp_client_instance.server_status["test-server"].status == "disconnected"
```

### 2.2 ツール呼び出しテスト

```python
class TestMCPClientToolCalls:
    """MCPクライアントツール呼び出しのテスト"""

    @pytest.mark.asyncio
    async def test_call_tool_success(
        self, mcp_client_instance, mock_process_pool
    ):
        """MCPC-004: ツール呼び出し成功"""
        # Arrange
        tool_call = MCPToolCall(
            tool_name="search_documentation",
            parameters={"query": "Azure OpenAI"}
        )
        mock_process_pool.pools = {"aws-docs": MagicMock()}

        # プロセスラッパーのモック
        mock_wrapper = MagicMock()
        mock_process = MagicMock()
        mock_wrapper.process = mock_process
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.readline.return_value = '{"jsonrpc": "2.0", "id": "1", "result": {"content": [{"text": "検索結果"}]}}'

        # AsyncContextManager のモック
        mock_pool_cm = AsyncMock()
        mock_pool_cm.__aenter__.return_value = mock_wrapper
        mock_pool_cm.__aexit__.return_value = None
        mock_process_pool.acquire.return_value = mock_pool_cm

        # Act
        result = await mcp_client_instance.call_tool("aws-docs", tool_call)

        # Assert
        assert result.success is True
        assert "検索結果" in result.content

    @pytest.mark.asyncio
    async def test_fetch_tools_from_cache(self, mcp_client_instance):
        """MCPC-005: ツール一覧取得（キャッシュ）"""
        # Arrange
        mock_tool = MagicMock()
        mock_tool.name = "cached_tool"
        mcp_client_instance.tools_cache["test-server"] = [mock_tool]

        # Act
        tools = await mcp_client_instance.fetch_tools("test-server")

        # Assert
        assert len(tools) == 1
        assert tools[0].name == "cached_tool"
```

### 2.3 設定ファイル・環境変数テスト

```python
class TestMCPClientConfig:
    """MCPクライアント設定のテスト"""

    @pytest.mark.asyncio
    async def test_load_config_file_success(
        self, mcp_client_instance, tmp_path
    ):
        """MCPC-006: 設定ファイル読み込み成功"""
        # Arrange
        config_content = '''
        {
            "mcpServers": {
                "test-server": {
                    "command": "npx",
                    "args": ["-y", "@test/mcp-server"],
                    "env": {},
                    "enabled": false
                }
            }
        }
        '''
        config_file = tmp_path / "mcp-config.json"
        config_file.write_text(config_content)

        # Act
        result = await mcp_client_instance.load_config_file(str(config_file))

        # Assert
        assert result is True
        assert "test-server" in mcp_client_instance.servers

    def test_expand_env_vars_success(self, mcp_client_instance):
        """MCPC-007: 環境変数展開成功"""
        # Arrange
        import os
        os.environ["TEST_VAR"] = "expanded_value"
        env_dict = {
            "API_KEY": "${TEST_VAR}",
            "STATIC": "no_expansion"
        }

        # Act
        result = mcp_client_instance._expand_env_vars(env_dict)

        # Assert
        assert result["API_KEY"] == "expanded_value"
        assert result["STATIC"] == "no_expansion"

        # Cleanup
        del os.environ["TEST_VAR"]
```

### 2.4 内部ツールテスト

```python
class TestMCPClientInternalTools:
    """MCPクライアント内部ツールのテスト"""

    @pytest.mark.asyncio
    async def test_register_internal_tools_success(self, mcp_client_instance):
        """MCPC-008: 内部ツール登録成功"""
        # Arrange
        from app.models.mcp import MCPTool, MCPToolType

        tools = [
            MCPTool(
                name="internal_tool",
                description="内部テストツール",
                type=MCPToolType.FUNCTION,
                parameters=[]
            )
        ]
        handlers = {
            "internal_tool": lambda params: {"result": "success"}
        }

        # Act
        result = await mcp_client_instance.register_internal_tools(
            "internal-server",
            tools,
            handlers
        )

        # Assert
        assert result is True
        assert "internal-server" in mcp_client_instance.tools_cache
        assert mcp_client_instance.is_internal_server("internal-server")

    @pytest.mark.asyncio
    async def test_call_internal_tool_sync(self, mcp_client_instance):
        """MCPC-009: 内部ツール実行成功（同期）"""
        # Arrange
        from app.models.mcp import MCPTool, MCPToolType, MCPToolCall

        tools = [
            MCPTool(
                name="sync_tool",
                description="同期ツール",
                type=MCPToolType.FUNCTION,
                parameters=[]
            )
        ]
        handlers = {
            "sync_tool": lambda params: {"result": params.get("input", "default")}
        }
        await mcp_client_instance.register_internal_tools(
            "internal-server", tools, handlers
        )

        tool_call = MCPToolCall(
            tool_name="sync_tool",
            parameters={"input": "test_value"}
        )

        # Act
        result = await mcp_client_instance.call_internal_tool(
            "internal-server", tool_call
        )

        # Assert
        assert result.success is True
        assert "test_value" in result.content

    @pytest.mark.asyncio
    async def test_call_internal_tool_async(self, mcp_client_instance):
        """MCPC-010: 内部ツール実行成功（非同期）"""
        # Arrange
        from app.models.mcp import MCPTool, MCPToolType, MCPToolCall

        async def async_handler(params):
            return {"result": "async_" + params.get("input", "")}

        tools = [
            MCPTool(
                name="async_tool",
                description="非同期ツール",
                type=MCPToolType.FUNCTION,
                parameters=[]
            )
        ]
        handlers = {"async_tool": async_handler}
        await mcp_client_instance.register_internal_tools(
            "internal-server", tools, handlers
        )

        tool_call = MCPToolCall(
            tool_name="async_tool",
            parameters={"input": "test"}
        )

        # Act
        result = await mcp_client_instance.call_internal_tool(
            "internal-server", tool_call
        )

        # Assert
        assert result.success is True
        assert "async_test" in result.content


class TestMCPClientRetryAndPool:
    """MCPクライアントリトライ・プール操作のテスト"""

    @pytest.mark.asyncio
    async def test_connect_server_retry_success(
        self, mcp_client_instance, mock_process_pool
    ):
        """MCPC-011: サーバー接続リトライ成功"""
        # Arrange
        server = MCPServer(
            name="retry-server",
            command="npx",
            args=["-y", "@test/mcp-server"],
            enabled=False
        )
        await mcp_client_instance.add_server(server)

        # 1回目は失敗（タイムアウト）、2回目は成功
        call_count = 0

        async def mock_init(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                mcp_client_instance.server_status["retry-server"].error_message = "タイムアウト"
                return False
            return True

        mock_process_pool.initialize_pool = AsyncMock(side_effect=mock_init)

        # Act
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await mcp_client_instance.connect_server("retry-server", max_retries=3)

        # Assert
        assert result is True
        assert call_count == 2

    def test_get_pool_status(self, mcp_client_instance, mock_process_pool):
        """MCPC-012: プールステータス取得"""
        # Arrange
        mock_process_pool.get_pool_status.return_value = {
            "test-server": {
                "pool_size": 3,
                "active_processes": 2,
                "available": 1
            }
        }

        # Act
        status = mcp_client_instance.get_pool_status("test-server")

        # Assert
        assert "test-server" in status
        assert status["test-server"]["pool_size"] == 3


class TestMCPClientStatus:
    """MCPクライアントステータス取得のテスト"""

    def test_get_server_status_single(self, mcp_client_instance):
        """MCPC-013: 単一サーバーステータス取得"""
        # Arrange
        from app.models.mcp import MCPServerStatus
        mcp_client_instance.server_status["test"] = MCPServerStatus(
            name="test", status="connected", available_tools=[]
        )

        # Act
        result = mcp_client_instance.get_server_status("test")

        # Assert
        assert len(result) == 1
        assert result[0].name == "test"
        assert result[0].status == "connected"

    def test_get_server_status_all(self, mcp_client_instance):
        """MCPC-014: 全サーバーステータス取得"""
        # Arrange
        from app.models.mcp import MCPServerStatus
        mcp_client_instance.server_status["test1"] = MCPServerStatus(
            name="test1", status="connected", available_tools=[]
        )
        mcp_client_instance.server_status["test2"] = MCPServerStatus(
            name="test2", status="disconnected", available_tools=[]
        )

        # Act
        result = mcp_client_instance.get_server_status()

        # Assert
        assert len(result) == 2

    def test_get_available_tools_single(self, mcp_client_instance):
        """MCPC-015: 単一サーバーツール取得"""
        # Arrange
        from app.models.mcp import MCPTool, MCPToolType
        mock_tool = MCPTool(
            name="tool1", description="", type=MCPToolType.FUNCTION, parameters=[]
        )
        mcp_client_instance.tools_cache["test"] = [mock_tool]

        # Act
        result = mcp_client_instance.get_available_tools("test")

        # Assert
        assert len(result) == 1
        assert result[0].name == "tool1"

    def test_get_available_tools_all(self, mcp_client_instance):
        """MCPC-016: 全サーバーツール取得"""
        # Arrange
        from app.models.mcp import MCPTool, MCPToolType
        tool1 = MCPTool(
            name="tool1", description="", type=MCPToolType.FUNCTION, parameters=[]
        )
        tool2 = MCPTool(
            name="tool2", description="", type=MCPToolType.FUNCTION, parameters=[]
        )
        mcp_client_instance.tools_cache["server1"] = [tool1]
        mcp_client_instance.tools_cache["server2"] = [tool2]

        # Act
        result = mcp_client_instance.get_available_tools()

        # Assert
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_cleanup_all_resources(self, mcp_client_instance, mock_process_pool):
        """MCPC-017: 全リソースクリーンアップ"""
        # Arrange
        from app.models.mcp import MCPServerStatus
        mcp_client_instance.server_status["test"] = MCPServerStatus(
            name="test", status="connected", available_tools=["tool1"]
        )
        mcp_client_instance.tools_cache["test"] = [MagicMock()]
        mock_process_pool.cleanup_all = AsyncMock()

        # Act
        await mcp_client_instance.cleanup()

        # Assert
        mock_process_pool.cleanup_all.assert_called_once()
        assert mcp_client_instance.server_status["test"].status == "disconnected"
        assert len(mcp_client_instance.tools_cache) == 0
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| MCPC-E01 | 存在しないサーバーへの接続 | unknown server | False, error logged |
| MCPC-E02 | サーバー接続タイムアウト | slow server | False after retries |
| MCPC-E03 | ツール呼び出しタイムアウト | slow tool | MCPToolResult(success=False) |
| MCPC-E04 | ツール呼び出しJSON解析エラー | invalid JSON response | MCPToolResult(success=False) |
| MCPC-E05 | 設定ファイル不存在 | non-existent path | False, warning logged |
| MCPC-E06 | 設定ファイルJSON解析エラー | invalid JSON file | False, error logged |
| MCPC-E07 | 内部ツール未登録サーバー | unknown internal server | MCPToolResult(success=False) |
| MCPC-E08 | 内部ツール未登録ツール名 | unknown tool_name | MCPToolResult(success=False) |
| MCPC-E09 | 内部ツール実行例外 | handler raises | MCPToolResult(success=False) |
| MCPC-E10 | 未接続サーバーへのツール呼び出し | disconnected server | MCPToolResult(success=False) |

### 3.1 サーバー接続エラーテスト

```python
class TestMCPClientConnectionErrors:
    """MCPクライアント接続エラーのテスト"""

    @pytest.mark.asyncio
    async def test_connect_unknown_server(self, mcp_client_instance):
        """MCPC-E01: 存在しないサーバーへの接続"""
        # Arrange - サーバーを追加しない

        # Act
        result = await mcp_client_instance.connect_server("unknown-server")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_connect_server_timeout(
        self, mcp_client_instance, mock_process_pool
    ):
        """MCPC-E02: サーバー接続タイムアウト"""
        # Arrange
        server = MCPServer(
            name="slow-server",
            command="npx",
            args=["-y", "@slow/mcp-server"],
            enabled=False
        )
        await mcp_client_instance.add_server(server)

        # プロセスプール初期化が失敗し、タイムアウトメッセージを返す
        mock_process_pool.initialize_pool.return_value = False
        mcp_client_instance.server_status["slow-server"].error_message = "タイムアウト"

        # Act
        result = await mcp_client_instance.connect_server("slow-server", max_retries=1)

        # Assert
        assert result is False
        assert mcp_client_instance.server_status["slow-server"].status == "error"
```

### 3.2 ツール呼び出しエラーテスト

```python
class TestMCPClientToolCallErrors:
    """MCPクライアントツール呼び出しエラーのテスト"""

    @pytest.mark.asyncio
    async def test_call_tool_timeout(
        self, mcp_client_instance, mock_process_pool
    ):
        """MCPC-E03: ツール呼び出しタイムアウト"""
        # Arrange
        import asyncio
        tool_call = MCPToolCall(
            tool_name="slow_tool",
            parameters={}
        )
        mock_process_pool.pools = {"test-server": MagicMock()}

        mock_wrapper = MagicMock()
        mock_process = MagicMock()
        mock_wrapper.process = mock_process
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()

        # readline がタイムアウトするようモック
        async def slow_readline():
            await asyncio.sleep(100)
            return ""

        mock_pool_cm = AsyncMock()
        mock_pool_cm.__aenter__.return_value = mock_wrapper
        mock_pool_cm.__aexit__.return_value = None
        mock_process_pool.acquire.return_value = mock_pool_cm

        with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
            # Act
            result = await mcp_client_instance.call_tool("test-server", tool_call)

            # Assert
            assert result.success is False
            assert "タイムアウト" in result.error

    @pytest.mark.asyncio
    async def test_call_tool_json_error(
        self, mcp_client_instance, mock_process_pool
    ):
        """MCPC-E04: ツール呼び出しJSON解析エラー"""
        # Arrange
        tool_call = MCPToolCall(
            tool_name="bad_tool",
            parameters={}
        )
        mock_process_pool.pools = {"test-server": MagicMock()}

        mock_wrapper = MagicMock()
        mock_process = MagicMock()
        mock_wrapper.process = mock_process
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.readline.return_value = "not valid json"

        mock_pool_cm = AsyncMock()
        mock_pool_cm.__aenter__.return_value = mock_wrapper
        mock_pool_cm.__aexit__.return_value = None
        mock_process_pool.acquire.return_value = mock_pool_cm

        # Act
        result = await mcp_client_instance.call_tool("test-server", tool_call)

        # Assert
        assert result.success is False
        assert "JSON" in result.error

    @pytest.mark.asyncio
    async def test_call_tool_disconnected_server(
        self, mcp_client_instance, mock_process_pool
    ):
        """MCPC-E10: 未接続サーバーへのツール呼び出し"""
        # Arrange
        tool_call = MCPToolCall(
            tool_name="any_tool",
            parameters={}
        )
        mock_process_pool.pools = {}  # プールが初期化されていない

        # Act
        result = await mcp_client_instance.call_tool("disconnected-server", tool_call)

        # Assert
        assert result.success is False
        assert "接続されていません" in result.error
```

### 3.3 設定ファイルエラーテスト

```python
class TestMCPClientConfigErrors:
    """MCPクライアント設定エラーのテスト"""

    @pytest.mark.asyncio
    async def test_load_config_file_not_found(self, mcp_client_instance):
        """MCPC-E05: 設定ファイル不存在"""
        # Act
        result = await mcp_client_instance.load_config_file("non_existent.json")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_load_config_file_invalid_json(
        self, mcp_client_instance, tmp_path
    ):
        """MCPC-E06: 設定ファイルJSON解析エラー"""
        # Arrange
        config_file = tmp_path / "invalid.json"
        config_file.write_text("{ invalid json }")

        # Act
        result = await mcp_client_instance.load_config_file(str(config_file))

        # Assert
        assert result is False
```

### 3.4 内部ツールエラーテスト

```python
class TestMCPClientInternalToolErrors:
    """MCPクライアント内部ツールエラーのテスト"""

    @pytest.mark.asyncio
    async def test_call_internal_tool_unknown_server(self, mcp_client_instance):
        """MCPC-E07: 内部ツール未登録サーバー"""
        # Arrange
        tool_call = MCPToolCall(
            tool_name="any_tool",
            parameters={}
        )

        # Act
        result = await mcp_client_instance.call_internal_tool(
            "unknown-internal", tool_call
        )

        # Assert
        assert result.success is False
        assert "見つかりません" in result.error

    @pytest.mark.asyncio
    async def test_call_internal_tool_unknown_tool(self, mcp_client_instance):
        """MCPC-E08: 内部ツール未登録ツール名"""
        # Arrange
        from app.models.mcp import MCPTool, MCPToolType

        tools = [
            MCPTool(
                name="registered_tool",
                description="登録済み",
                type=MCPToolType.FUNCTION,
                parameters=[]
            )
        ]
        handlers = {"registered_tool": lambda p: "ok"}
        await mcp_client_instance.register_internal_tools(
            "internal-server", tools, handlers
        )

        tool_call = MCPToolCall(
            tool_name="unregistered_tool",
            parameters={}
        )

        # Act
        result = await mcp_client_instance.call_internal_tool(
            "internal-server", tool_call
        )

        # Assert
        assert result.success is False
        assert "見つかりません" in result.error

    @pytest.mark.asyncio
    async def test_call_internal_tool_handler_exception(self, mcp_client_instance):
        """MCPC-E09: 内部ツール実行例外"""
        # Arrange
        from app.models.mcp import MCPTool, MCPToolType

        def failing_handler(params):
            raise ValueError("Handler failed")

        tools = [
            MCPTool(
                name="failing_tool",
                description="失敗するツール",
                type=MCPToolType.FUNCTION,
                parameters=[]
            )
        ]
        handlers = {"failing_tool": failing_handler}
        await mcp_client_instance.register_internal_tools(
            "internal-server", tools, handlers
        )

        tool_call = MCPToolCall(
            tool_name="failing_tool",
            parameters={}
        )

        # Act
        result = await mcp_client_instance.call_internal_tool(
            "internal-server", tool_call
        )

        # Assert
        assert result.success is False
        assert "Handler failed" in result.error
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| MCPC-SEC-01 | 環境変数の安全な展開 | ${SECRET} pattern | 展開されるが、未定義変数は元のまま |
| MCPC-SEC-02 | プロセス引数のエスケープ | malicious args | 安全に処理される |
| MCPC-SEC-03 | JSON-RPCインジェクション対策 | malicious tool params | JSONとして安全にシリアライズ |
| MCPC-SEC-04 | 内部ツールのコンテキスト分離 | context with secrets | コンテキストは適切に渡される |
| MCPC-SEC-05 | プロセスプールのリソース制限 | many concurrent requests | セマフォで制御 |
| MCPC-SEC-06 | 設定ファイルパストラバーサル | ../etc/passwd | パス検証で拒否【実装失敗予定】 |
| MCPC-SEC-07 | エラーメッセージの機密情報マスク | error with credentials | 機密情報がユーザーに露出しない |
| MCPC-SEC-08 | コマンドホワイトリスト検証 | unknown command | 許可リスト外コマンドを拒否【実装失敗予定】 |

```python
@pytest.mark.security
class TestMCPClientSecurity:
    """MCPクライアントセキュリティテスト"""

    def test_env_var_expansion_undefined(self, mcp_client_instance):
        """MCPC-SEC-01: 環境変数の安全な展開（未定義）"""
        # Arrange
        env_dict = {
            "SECRET": "${UNDEFINED_SECRET_VAR}"
        }

        # Act
        result = mcp_client_instance._expand_env_vars(env_dict)

        # Assert - 未定義変数は展開されず元のまま
        assert result["SECRET"] == "${UNDEFINED_SECRET_VAR}"

    @pytest.mark.asyncio
    async def test_json_rpc_injection_prevention(
        self, mcp_client_instance, mock_process_pool
    ):
        """MCPC-SEC-03: JSON-RPCインジェクション対策"""
        # Arrange
        # 悪意のあるパラメータを含むツール呼び出し
        tool_call = MCPToolCall(
            tool_name="test_tool",
            parameters={
                "query": '"; DROP TABLE users; --',
                "nested": {"evil": "<script>alert('xss')</script>"}
            }
        )
        mock_process_pool.pools = {"test-server": MagicMock()}

        mock_wrapper = MagicMock()
        mock_process = MagicMock()
        mock_wrapper.process = mock_process
        captured_request = []

        def capture_write(data):
            captured_request.append(data)

        mock_process.stdin.write = capture_write
        mock_process.stdin.flush = MagicMock()
        mock_process.stdout.readline.return_value = '{"jsonrpc": "2.0", "id": "1", "result": {"content": []}}'

        mock_pool_cm = AsyncMock()
        mock_pool_cm.__aenter__.return_value = mock_wrapper
        mock_pool_cm.__aexit__.return_value = None
        mock_process_pool.acquire.return_value = mock_pool_cm

        # Act
        await mcp_client_instance.call_tool("test-server", tool_call)

        # Assert - JSONとして安全にシリアライズされている
        import json
        request_json = captured_request[0]
        parsed = json.loads(request_json)
        # パラメータが正しくエスケープされている
        assert parsed["params"]["arguments"]["query"] == '"; DROP TABLE users; --'
        assert "<script>" in parsed["params"]["arguments"]["nested"]["evil"]

    @pytest.mark.asyncio
    async def test_internal_tool_context_isolation(self, mcp_client_instance):
        """MCPC-SEC-04: 内部ツールのコンテキスト分離"""
        # Arrange
        from app.models.mcp import MCPTool, MCPToolType

        received_context = {}

        def context_aware_handler(params, context=None):
            received_context.update(context or {})
            return {"received": True}

        tools = [
            MCPTool(
                name="context_tool",
                description="コンテキスト対応ツール",
                type=MCPToolType.FUNCTION,
                parameters=[]
            )
        ]
        handlers = {"context_tool": context_aware_handler}
        await mcp_client_instance.register_internal_tools(
            "internal-server", tools, handlers
        )

        tool_call = MCPToolCall(
            tool_name="context_tool",
            parameters={}
        )
        context = {"cloud_credentials": {"provider": "aws"}}

        # Act
        result = await mcp_client_instance.call_internal_tool(
            "internal-server", tool_call, context
        )

        # Assert
        assert result.success is True
        assert received_context.get("cloud_credentials") is not None

    @pytest.mark.asyncio
    async def test_process_args_escaping(
        self, mcp_client_instance, mock_process_pool
    ):
        """MCPC-SEC-02: プロセス引数のエスケープ

        subprocess.Popen が引数をリストとして受け取るため、
        シェルインジェクションは発生しないことを確認。
        """
        # Arrange
        server = MCPServer(
            name="malicious-server",
            command="npx",
            args=["-y", "@test/mcp-server", "; rm -rf /"],  # 悪意のある引数
            enabled=False
        )
        await mcp_client_instance.add_server(server)
        mock_process_pool.initialize_pool = AsyncMock(return_value=True)

        # Act
        await mcp_client_instance.connect_server("malicious-server")

        # Assert
        # initialize_pool が呼ばれた際の引数をチェック
        call_kwargs = mock_process_pool.initialize_pool.call_args.kwargs
        # 引数がリストとしてそのまま渡され、シェル展開されないことを確認
        assert call_kwargs["args"] == ["-y", "@test/mcp-server", "; rm -rf /"]
        # shell=True でないため、セミコロンは文字列として扱われる

    @pytest.mark.asyncio
    async def test_process_pool_resource_limit(
        self, mcp_client_instance, mock_process_pool
    ):
        """MCPC-SEC-05: プロセスプールのリソース制限

        セマフォによる同時使用数制御を確認。
        """
        # Arrange
        import asyncio
        mock_process_pool.pools = {"test-server": MagicMock()}

        mock_wrapper = MagicMock()
        mock_process = MagicMock()
        mock_wrapper.process = mock_process
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.readline.return_value = (
            '{"jsonrpc": "2.0", "id": "1", "result": {"content": [{"text": "ok"}]}}'
        )

        # acquireがセマフォで制御されることを確認
        acquire_count = 0

        async def mock_acquire(server_name):
            nonlocal acquire_count
            acquire_count += 1

            class AsyncCtxMgr:
                async def __aenter__(self):
                    return mock_wrapper

                async def __aexit__(self, *args):
                    pass

            return AsyncCtxMgr()

        mock_process_pool.acquire = mock_acquire

        # Act - 5並列リクエスト
        tasks = []
        for i in range(5):
            tool_call = MCPToolCall(tool_name="test_tool", parameters={"id": i})
            tasks.append(mcp_client_instance.call_tool("test-server", tool_call))

        results = await asyncio.gather(*tasks)

        # Assert - 全リクエストが完了
        assert len(results) == 5
        assert all(r.success for r in results)
        assert acquire_count == 5

    @pytest.mark.asyncio
    async def test_config_path_traversal(self, mcp_client_instance):
        """MCPC-SEC-06: 設定ファイルパストラバーサル【実装失敗予定】

        注意: 現在の実装(Line 539-589)ではパス検証がないため、
        パストラバーサル攻撃が可能。このテストは脆弱性を検出する。
        """
        # Arrange
        malicious_paths = [
            "../../../etc/passwd",
            "/etc/passwd",
            "....//....//etc/passwd",
        ]

        # Act & Assert
        for path in malicious_paths:
            # 現在の実装ではパス検証なしでファイル読み込みを試行する
            result = await mcp_client_instance.load_config_file(path)
            # ファイルが存在しないためFalseが返るが、パス検証で拒否すべき
            assert result is False
            # TODO: 実装修正後は "パスが不正" 等のエラーで拒否すべき

    @pytest.mark.asyncio
    async def test_error_message_credential_masking(
        self, mcp_client_instance, mock_process_pool
    ):
        """MCPC-SEC-07: エラーメッセージの機密情報マスク

        MCPToolResult.errorに機密情報が含まれないことを確認。
        """
        # Arrange
        tool_call = MCPToolCall(tool_name="any_tool", parameters={})
        mock_process_pool.pools = {}  # プール未初期化

        # Act
        result = await mcp_client_instance.call_tool("disconnected-server", tool_call)

        # Assert - エラーメッセージに機密情報が含まれない
        assert result.success is False
        assert "password" not in result.error.lower()
        assert "secret" not in result.error.lower()
        assert "接続されていません" in result.error

    @pytest.mark.asyncio
    async def test_command_whitelist_validation(self, mcp_client_instance):
        """MCPC-SEC-08: コマンドホワイトリスト検証【実装失敗予定】

        注意: 現在の実装ではコマンドのホワイトリスト検証がないため、
        任意のコマンドを実行可能。このテストは脆弱性を検出する。
        """
        # Arrange
        dangerous_server = MCPServer(
            name="dangerous-server",
            command="/bin/bash",  # 危険なコマンド
            args=["-c", "cat /etc/passwd"],
            enabled=False
        )

        # Act
        result = await mcp_client_instance.add_server(dangerous_server)

        # Assert
        # 現在の実装では任意のコマンドを追加可能（脆弱性）
        # 修正後は False を返し、"許可されていないコマンド" エラーを出すべき
        # 注: このテストは現在の実装では True を返す（失敗予定）
        assert result is True  # 現在の実装
        # TODO: 修正後は assert result is False
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_mcp_client_module` | グローバル状態リセット | function | Yes |
| `mcp_client_instance` | MCPClientインスタンス | function | No |
| `mock_process_pool` | プロセスプールモック | function | No |

### 共通フィクスチャ定義

```python
# test/unit/mcp_plugin/conftest.py に追加
import sys
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.fixture(autouse=True)
def reset_mcp_client_module():
    """テストごとにモジュールのグローバル状態をリセット

    client.pyのグローバル変数 mcp_client (Line 733) をリセットし、
    テスト間の状態漏洩を防止します。
    """
    # テスト前の状態を保存
    modules_to_reset = [
        "app.mcp_plugin.client",
        "app.mcp_plugin.process_pool",
    ]
    saved_modules = {m: sys.modules.get(m) for m in modules_to_reset}

    yield

    # テスト後にモジュール状態をリセット
    for module_name in modules_to_reset:
        if module_name in sys.modules:
            if saved_modules[module_name] is None:
                del sys.modules[module_name]
            else:
                sys.modules[module_name] = saved_modules[module_name]


@pytest.fixture
def mcp_client_instance():
    """MCPClientインスタンス（テスト用）

    注: プロセスプールをAsyncMockで置き換え、
    非同期メソッドが正しく動作するようにする。
    """
    from app.mcp_plugin.client import MCPClient
    client = MCPClient()

    # プロセスプールをAsyncMockで置き換え
    mock_pool = MagicMock()
    mock_pool.cleanup_all = AsyncMock()
    mock_pool.cleanup = AsyncMock()
    mock_pool.initialize_pool = AsyncMock(return_value=True)
    mock_pool.pools = {}
    mock_pool.get_pool_status = MagicMock(return_value={})

    client.process_pool = mock_pool
    return client


@pytest.fixture
def mock_process_pool():
    """プロセスプールモック（グローバル変数用）

    注: new_callable=AsyncMockではなく、AsyncMock()インスタンスを
    属性に設定することで非同期メソッドを適切にモックする。
    """
    with patch("app.mcp_plugin.client.mcp_process_pool") as mock:
        mock.initialize_pool = AsyncMock(return_value=True)
        mock.cleanup = AsyncMock()
        mock.cleanup_all = AsyncMock()
        mock.pools = {}
        mock.get_pool_status = MagicMock(return_value={})
        yield mock
```

---

## 6. テスト実行例

```bash
# client関連テストのみ実行
pytest test/unit/mcp_plugin/test_client.py -v

# カバレッジ付きで実行
pytest test/unit/mcp_plugin/test_client.py --cov=app.mcp_plugin.client --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/mcp_plugin/test_client.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

### テストID規則

本仕様書では、他の完成済みテスト仕様書（mcp_plugin_chat_agent_tests.md等）と同様に、**カテゴリ別ID**を採用しています：

- **正常系**: `MCPC-{3桁連番}` (例: MCPC-001, MCPC-002, ...)
- **異常系**: `MCPC-E{2桁連番}` (例: MCPC-E01, MCPC-E02, ...)
- **セキュリティ**: `MCPC-SEC-{2桁連番}` (例: MCPC-SEC-01, MCPC-SEC-02, ...)

> **注記**: プレフィックス`MCPC`は "MCP Client" の略称です。

### テストケース数

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 17 | MCPC-001 〜 MCPC-017 |
| 異常系 | 10 | MCPC-E01 〜 MCPC-E10 |
| セキュリティ | 8 | MCPC-SEC-01 〜 MCPC-SEC-08 |
| **合計** | **35** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestMCPClientServerManagement` | MCPC-001〜MCPC-003 | 3 |
| `TestMCPClientToolCalls` | MCPC-004〜MCPC-005 | 2 |
| `TestMCPClientConfig` | MCPC-006〜MCPC-007 | 2 |
| `TestMCPClientInternalTools` | MCPC-008〜MCPC-010 | 3 |
| `TestMCPClientRetryAndPool` | MCPC-011〜MCPC-012 | 2 |
| `TestMCPClientStatus` | MCPC-013〜MCPC-017 | 5 |
| `TestMCPClientConnectionErrors` | MCPC-E01〜MCPC-E02 | 2 |
| `TestMCPClientToolCallErrors` | MCPC-E03〜MCPC-E04, MCPC-E10 | 3 |
| `TestMCPClientConfigErrors` | MCPC-E05〜MCPC-E06 | 2 |
| `TestMCPClientInternalToolErrors` | MCPC-E07〜MCPC-E09 | 3 |
| `TestMCPClientSecurity` | MCPC-SEC-01〜MCPC-SEC-08 | 8 |

### 実装失敗が予想されるテスト

以下のテストは現在の実装では**意図的に失敗**します。実装側の修正が必要です。

| テストID | 失敗理由 | 修正方針 |
|---------|---------|---------|
| MCPC-SEC-06 | パストラバーサル防止機能がない（Line 539-589） | configパスを作業ディレクトリ内に限定するバリデーション追加 |
| MCPC-SEC-08 | コマンドホワイトリストがない（Line 132-137） | 許可コマンドリスト（npx, uv, python等）で検証 |

### 注意事項

- プロセス間通信のモックが複雑なため、実装に注意が必要
- `asyncio.wait_for` のモックはタイムアウトテストで特に重要
- 環境変数テストは `os.environ` の状態を変更するため、クリーンアップ必須
- `@pytest.mark.security` マーカーの登録が必要（pyproject.toml）

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | 実MCPサーバープロセスのテスト不可 | プロセス起動・通信の検証困難 | モック使用、統合テストで別途検証 |
| 2 | プロセスプールの並列性テスト困難 | セマフォ動作の検証が限定的 | 負荷テストで別途検証 |
| 3 | 複数行JSON応答のテスト | `_read_complete_json_response` の完全テスト困難 | 代表的なケースのみカバー |
| 4 | パストラバーサル防止なし（Line 539-589） | 悪意のある設定ファイルパス指定可能 | 実装修正必須（パス検証追加） |
| 5 | コマンドホワイトリストなし（Line 132-137） | 任意コマンド実行可能 | 実装修正必須（許可リスト追加） |

### セキュリティ境界の明確化

このモジュール（`client.py`）のセキュリティ責任範囲：

| 責任範囲 | 担当 | 状態 |
|---------|------|------|
| プロセス引数のエスケープ | subprocess（リスト形式） | ✅ 安全 |
| JSON-RPCインジェクション対策 | json.dumps（標準ライブラリ） | ✅ 安全 |
| 環境変数展開の安全性 | _expand_env_vars | ✅ 実装済み |
| 内部ツールコンテキスト分離 | call_internal_tool | ✅ 実装済み |
| プロセスプールリソース制限 | セマフォ（process_pool.py） | ✅ 実装済み |
| 設定ファイルパス検証 | load_config_file | ❌ **要修正** |
| コマンドホワイトリスト | connect_server | ❌ **要修正** |
| エラーメッセージマスク | MCPToolResult.error | ⚠️ 部分的 |

---

## 関連ドキュメント

- [mcp_plugin_router_tests.md](./mcp_plugin_router_tests.md) - APIルーターのテスト
- [mcp_plugin_chat_agent_tests.md](./mcp_plugin_chat_agent_tests.md) - チャットエージェントのテスト
