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
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `mcp_client_instance` | MCPClientインスタンス | function | No |
| `mock_process_pool` | プロセスプールモック | function | No |

### 共通フィクスチャ定義

```python
# test/unit/mcp_plugin/conftest.py に追加

@pytest.fixture
def mcp_client_instance():
    """MCPClientインスタンス（テスト用）"""
    from app.mcp_plugin.client import MCPClient
    client = MCPClient()
    # プロセスプールをモックで置き換え
    client.process_pool = MagicMock()
    return client


@pytest.fixture
def mock_process_pool():
    """プロセスプールモック"""
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

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 12 | MCPC-001 〜 MCPC-012 |
| 異常系 | 10 | MCPC-E01 〜 MCPC-E10 |
| セキュリティ | 5 | MCPC-SEC-01 〜 MCPC-SEC-05 |
| **合計** | **27** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestMCPClientServerManagement` | MCPC-001〜MCPC-003 | 3 |
| `TestMCPClientToolCalls` | MCPC-004〜MCPC-005 | 2 |
| `TestMCPClientConfig` | MCPC-006〜MCPC-007 | 2 |
| `TestMCPClientInternalTools` | MCPC-008〜MCPC-010 | 3 |
| `TestMCPClientConnectionErrors` | MCPC-E01〜MCPC-E02 | 2 |
| `TestMCPClientToolCallErrors` | MCPC-E03〜MCPC-E04, MCPC-E10 | 3 |
| `TestMCPClientConfigErrors` | MCPC-E05〜MCPC-E06 | 2 |
| `TestMCPClientInternalToolErrors` | MCPC-E07〜MCPC-E09 | 3 |
| `TestMCPClientSecurity` | MCPC-SEC-01〜MCPC-SEC-05 | 5 |

### 実装失敗が予想されるテスト

現時点で失敗が予想されるテストはありません。

### 注意事項

- プロセス間通信のモックが複雑なため、実装に注意が必要
- `asyncio.wait_for` のモックはタイムアウトテストで特に重要
- 環境変数テストは `os.environ` の状態を変更するため、クリーンアップ必須

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | 実MCPサーバープロセスのテスト不可 | プロセス起動・通信の検証困難 | モック使用、統合テストで別途検証 |
| 2 | プロセスプールの並列性テスト困難 | セマフォ動作の検証が限定的 | 負荷テストで別途検証 |
| 3 | 複数行JSON応答のテスト | `_read_complete_json_response` の完全テスト困難 | 代表的なケースのみカバー |

---

## 関連ドキュメント

- [mcp_plugin_router_tests.md](./mcp_plugin_router_tests.md) - APIルーターのテスト
- [mcp_plugin_chat_agent_tests.md](./mcp_plugin_chat_agent_tests.md) - チャットエージェントのテスト
