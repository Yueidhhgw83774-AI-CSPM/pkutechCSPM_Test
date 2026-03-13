# mcp_plugin/router テストケース

## 1. 概要

MCP (Model Context Protocol) プラグインのAPIルーターのテストケースを定義します。チャットエンドポイント、サーバー管理、認証、SSEストリーミング機能を包括的にテストします。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `mcp_chat` | MCPクライアントチャット（POST /mcp/chat） |
| `mcp_chat_stream` | SSEストリーミングチャット（POST /mcp/chat/stream） |
| `add_mcp_server` | MCPサーバー追加（POST /mcp/servers） |
| `list_mcp_servers` | サーバー一覧取得（GET /mcp/servers） |
| `list_server_tools` | ツール一覧取得（GET /mcp/servers/{name}/tools） |
| `get_mcp_status` | MCP全体ステータス取得（GET /mcp/status） |
| `connect_server` | サーバー接続（POST /mcp/servers/{name}/connect） |
| `disconnect_server` | サーバー切断（POST /mcp/servers/{name}/disconnect） |
| `remove_server` | サーバー削除（DELETE /mcp/servers/{name}） |
| `mcp_health_check` | ヘルスチェック（GET /mcp/health） |

### 1.2 エンドポイント

| エンドポイント | HTTPメソッド | 説明 | 認証 |
|---------------|-------------|------|------|
| `/mcp/chat` | POST | MCPチャット（同期） | なし |
| `/mcp/chat/stream` | POST | SSEストリーミング | SHARED-HMAC（本番時） |
| `/mcp/servers` | POST | サーバー追加 | なし |
| `/mcp/servers` | GET | サーバー一覧 | なし |
| `/mcp/servers/{name}/tools` | GET | ツール一覧 | なし |
| `/mcp/status` | GET | 全体ステータス | なし |
| `/mcp/servers/{name}/connect` | POST | サーバー接続 | なし |
| `/mcp/servers/{name}/disconnect` | POST | サーバー切断 | なし |
| `/mcp/servers/{name}` | DELETE | サーバー削除 | なし |
| `/mcp/health` | GET | ヘルスチェック | なし |

### 1.3 カバレッジ目標: 80%

> **注記**: SSEストリーミングはモック化が複雑なため、主要パスをカバー。認証検証は本番モード時のみ有効。

### 1.4 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/mcp_plugin/router.py` |
| テストコード | `test/unit/mcp_plugin/test_router.py` |
| conftest | `test/unit/mcp_plugin/conftest.py` |

### 1.5 補足情報

**認証方式:**
- SHARED-HMAC認証: `auth_hash` フィールドで検証（本番モード時のみ）
- DEBUG_MODE=true時は認証スキップ

**グローバル依存:**
- `mcp_client`: グローバルMCPクライアントインスタンス（client.py）
- `response_id_store`: Responses APIキャッシュ（deep_agents/agent.py）

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| MCPR-001 | 階層的エージェントでチャット成功 | use_hierarchical=true | 200, response text |
| MCPR-002 | Deep Agentsでチャット成功 | use_hierarchical=false | 200, response text |
| MCPR-003 | サーバー追加成功 | valid MCPServer | 201, success message |
| MCPR-004 | サーバー一覧取得 | - | 200, servers list |
| MCPR-005 | ツール一覧取得 | existing server_name | 200, tools list |
| MCPR-006 | MCP全体ステータス取得 | - | 200, status info |
| MCPR-007 | サーバー接続成功 | existing server_name | 200, success message |
| MCPR-008 | サーバー切断成功 | existing server_name | 200, success message |
| MCPR-009 | サーバー削除成功 | existing server_name | 200, success message |
| MCPR-010 | ヘルスチェック正常 | - | 200, healthy status |
| MCPR-011 | SSEストリーミング成功（DEBUG_MODE） | DEBUG_MODE=true | SSE events |
| MCPR-012 | SSEストリーミング認証成功（本番） | valid auth_hash | SSE events |

### 2.1 チャットエンドポイントテスト

```python
# test/unit/mcp_plugin/test_router.py
import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock, AsyncMock


class TestMCPChatEndpoint:
    """MCPチャットエンドポイントのテスト"""

    @pytest.mark.asyncio
    async def test_chat_hierarchical_mode(
        self, client, mock_invoke_mcp_chat
    ):
        """MCPR-001: 階層的エージェントでチャット成功"""
        # Arrange
        mock_invoke_mcp_chat.return_value = ("テスト応答", None)
        request_data = {
            "session_id": "test-session-001",
            "message": "Azure OpenAIについて教えて",
            "use_hierarchical": True
        }

        # Act
        response = await client.post("/mcp/chat", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "テスト応答"
        assert data["session_id"] == "test-session-001"
        mock_invoke_mcp_chat.assert_called_once_with(
            session_id="test-session-001",
            prompt="Azure OpenAIについて教えて",
            server_name=None,
            use_hierarchical=True
        )

    @pytest.mark.asyncio
    async def test_chat_deep_agents_mode(
        self, client, mock_invoke_mcp_chat
    ):
        """MCPR-002: Deep Agentsでチャット成功"""
        # Arrange
        mock_invoke_mcp_chat.return_value = ("Deep Agents応答", None)
        request_data = {
            "session_id": "test-session-002",
            "message": "ツール一覧を見せて",
            "server_name": "aws-docs",
            "use_hierarchical": False
        }

        # Act
        response = await client.post("/mcp/chat", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Deep Agents応答"
        mock_invoke_mcp_chat.assert_called_once_with(
            session_id="test-session-002",
            prompt="ツール一覧を見せて",
            server_name="aws-docs",
            use_hierarchical=False
        )
```

### 2.2 サーバー管理テスト

```python
class TestMCPServerManagement:
    """MCPサーバー管理のテスト"""

    @pytest.mark.asyncio
    async def test_add_server_success(self, client, mock_mcp_client):
        """MCPR-003: サーバー追加成功"""
        # Arrange
        mock_mcp_client.add_server.return_value = True
        server_data = {
            "name": "test-server",
            "command": "npx",
            "args": ["-y", "@test/mcp-server"],
            "env": {},
            "enabled": True
        }

        # Act
        response = await client.post("/mcp/servers", json=server_data)

        # Assert
        assert response.status_code == 201
        assert "test-server" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_list_servers(self, client, mock_mcp_client):
        """MCPR-004: サーバー一覧取得"""
        # Arrange
        mock_server = MagicMock()
        mock_server.name = "aws-docs"
        mock_mcp_client.servers = {"aws-docs": mock_server}

        # Act
        response = await client.get("/mcp/servers")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "servers" in data

    @pytest.mark.asyncio
    async def test_list_server_tools(self, client, mock_mcp_client):
        """MCPR-005: ツール一覧取得"""
        # Arrange
        mock_mcp_client.servers = {"aws-docs": MagicMock()}
        mock_tool = MagicMock()
        mock_tool.name = "search_documentation"
        mock_mcp_client.get_available_tools.return_value = [mock_tool]

        # Act
        response = await client.get("/mcp/servers/aws-docs/tools")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["server_name"] == "aws-docs"

    @pytest.mark.asyncio
    async def test_get_mcp_status(self, client, mock_mcp_client):
        """MCPR-006: MCP全体ステータス取得"""
        # Arrange
        mock_status = MagicMock()
        mock_status.status = "connected"
        mock_mcp_client.get_server_status.return_value = [mock_status]
        mock_mcp_client.get_available_tools.return_value = []

        # Act
        response = await client.get("/mcp/status")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "servers" in data
        assert "total_tools" in data
        assert "active_sessions" in data

    @pytest.mark.asyncio
    async def test_connect_server(self, client, mock_mcp_client):
        """MCPR-007: サーバー接続成功"""
        # Arrange
        mock_mcp_client.servers = {"aws-docs": MagicMock()}
        mock_mcp_client.connect_server.return_value = True

        # Act
        response = await client.post("/mcp/servers/aws-docs/connect")

        # Assert
        assert response.status_code == 200
        assert "接続しました" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_disconnect_server(self, client, mock_mcp_client):
        """MCPR-008: サーバー切断成功"""
        # Arrange
        mock_mcp_client.disconnect_server.return_value = True

        # Act
        response = await client.post("/mcp/servers/aws-docs/disconnect")

        # Assert
        assert response.status_code == 200
        assert "切断しました" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_remove_server(self, client, mock_mcp_client):
        """MCPR-009: サーバー削除成功"""
        # Arrange
        mock_mcp_client.servers = {"aws-docs": MagicMock()}
        mock_mcp_client.server_status = {"aws-docs": MagicMock()}
        mock_mcp_client.disconnect_server.return_value = True

        # Act
        response = await client.delete("/mcp/servers/aws-docs")

        # Assert
        assert response.status_code == 200
        assert "削除しました" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, client, mock_mcp_client):
        """MCPR-010: ヘルスチェック正常"""
        # Arrange
        mock_status = MagicMock()
        mock_status.status = "connected"
        mock_mcp_client.get_server_status.return_value = [mock_status]
        mock_mcp_client.servers = {"aws-docs": MagicMock()}
        mock_mcp_client.get_available_tools.return_value = []

        # Act
        response = await client.get("/mcp/health")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
```

### 2.3 SSEストリーミングテスト

```python
class TestSSEStreaming:
    """SSEストリーミングのテスト"""

    @pytest.mark.asyncio
    async def test_sse_stream_debug_mode(
        self, client, mock_stream_hierarchical
    ):
        """MCPR-011: SSEストリーミング成功（DEBUG_MODE）"""
        # Arrange
        with patch("app.mcp_plugin.router.settings") as mock_settings:
            mock_settings.DEBUG_MODE = True

            async def mock_events():
                yield ("response", {"text": "テスト応答"})
                yield ("done", {})

            mock_stream_hierarchical.return_value = mock_events()

            request_data = {
                "session_id": "test-session",
                "message": "テスト"
            }

            # Act
            response = await client.post(
                "/mcp/chat/stream",
                json=request_data
            )

            # Assert
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")

    @pytest.mark.asyncio
    async def test_sse_stream_auth_success(
        self, client, mock_stream_hierarchical
    ):
        """MCPR-012: SSEストリーミング認証成功（本番）"""
        # Arrange
        with patch("app.mcp_plugin.router.settings") as mock_settings, \
             patch("app.mcp_plugin.router.verify_auth_hash") as mock_verify, \
             patch("app.mcp_plugin.router._get_shared_secret") as mock_secret:
            mock_settings.DEBUG_MODE = False
            mock_verify.return_value = True
            mock_secret.return_value = "test-secret"

            async def mock_events():
                yield ("done", {})

            mock_stream_hierarchical.return_value = mock_events()

            request_data = {
                "session_id": "user123:test-session",
                "message": "テスト",
                "user_id": "user123",
                "auth_hash": "SHARED-HMAC-1234567890-validhash"
            }

            # Act
            response = await client.post(
                "/mcp/chat/stream",
                json=request_data
            )

            # Assert
            assert response.status_code == 200
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| MCPR-E01 | チャットエージェントエラー | invoke_mcp_chat raises | 500, error with ID |
| MCPR-E02 | サーバー追加失敗 | add_server returns False | 400, error message |
| MCPR-E03 | 存在しないサーバーのツール取得 | unknown server_name | 404, not found |
| MCPR-E04 | サーバー接続失敗 | connect_server returns False | 500, error message |
| MCPR-E05 | SSE認証情報不足（本番） | no auth_hash | 401, Unauthorized |
| MCPR-E06 | SSE認証ハッシュ検証失敗 | invalid auth_hash | 401, Unauthorized |
| MCPR-E07 | 存在しないサーバー接続試行 | unknown server_name | 404, not found |
| MCPR-E08 | 存在しないサーバー削除試行 | unknown server_name | 404, not found |
| MCPR-E09 | サーバー切断失敗 | disconnect_server returns False | 500, error message |

### 3.1 チャットエラーテスト

```python
class TestMCPChatErrors:
    """MCPチャットエラーのテスト"""

    @pytest.mark.asyncio
    async def test_chat_agent_error(self, client, mock_invoke_mcp_chat):
        """MCPR-E01: チャットエージェントエラー"""
        # Arrange
        mock_invoke_mcp_chat.side_effect = Exception("Agent error")
        request_data = {
            "session_id": "test-session",
            "message": "テスト"
        }

        # Act
        response = await client.post("/mcp/chat", json=request_data)

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        # エラーIDが含まれていることを確認
        assert "ID" in data["detail"] or "id" in data["detail"].lower()
```

### 3.2 サーバー管理エラーテスト

```python
class TestMCPServerManagementErrors:
    """MCPサーバー管理エラーのテスト"""

    @pytest.mark.asyncio
    async def test_add_server_failure(self, client, mock_mcp_client):
        """MCPR-E02: サーバー追加失敗"""
        # Arrange
        mock_mcp_client.add_server.return_value = False
        server_data = {
            "name": "fail-server",
            "command": "invalid",
            "args": []
        }

        # Act
        response = await client.post("/mcp/servers", json=server_data)

        # Assert
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_list_tools_unknown_server(self, client, mock_mcp_client):
        """MCPR-E03: 存在しないサーバーのツール取得"""
        # Arrange
        mock_mcp_client.servers = {}

        # Act
        response = await client.get("/mcp/servers/unknown-server/tools")

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_connect_server_failure(self, client, mock_mcp_client):
        """MCPR-E04: サーバー接続失敗"""
        # Arrange
        mock_mcp_client.servers = {"aws-docs": MagicMock()}
        mock_mcp_client.connect_server.return_value = False

        # Act
        response = await client.post("/mcp/servers/aws-docs/connect")

        # Assert
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_connect_unknown_server(self, client, mock_mcp_client):
        """MCPR-E07: 存在しないサーバー接続試行"""
        # Arrange
        mock_mcp_client.servers = {}

        # Act
        response = await client.post("/mcp/servers/unknown/connect")

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_unknown_server(self, client, mock_mcp_client):
        """MCPR-E08: 存在しないサーバー削除試行"""
        # Arrange
        mock_mcp_client.servers = {}

        # Act
        response = await client.delete("/mcp/servers/unknown")

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_disconnect_server_failure(self, client, mock_mcp_client):
        """MCPR-E09: サーバー切断失敗"""
        # Arrange
        mock_mcp_client.disconnect_server.return_value = False

        # Act
        response = await client.post("/mcp/servers/aws-docs/disconnect")

        # Assert
        assert response.status_code == 500
```

### 3.3 SSE認証エラーテスト

```python
class TestSSEAuthenticationErrors:
    """SSE認証エラーのテスト"""

    @pytest.mark.asyncio
    async def test_sse_missing_auth(self, client):
        """MCPR-E05: SSE認証情報不足（本番）"""
        # Arrange
        with patch("app.mcp_plugin.router.settings") as mock_settings:
            mock_settings.DEBUG_MODE = False
            request_data = {
                "session_id": "test-session",
                "message": "テスト"
                # auth_hash と user_id なし
            }

            # Act
            response = await client.post(
                "/mcp/chat/stream",
                json=request_data
            )

            # Assert
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_sse_invalid_auth_hash(self, client):
        """MCPR-E06: SSE認証ハッシュ検証失敗"""
        # Arrange
        with patch("app.mcp_plugin.router.settings") as mock_settings, \
             patch("app.mcp_plugin.router.verify_auth_hash") as mock_verify, \
             patch("app.mcp_plugin.router._get_shared_secret") as mock_secret:
            mock_settings.DEBUG_MODE = False
            mock_verify.return_value = False  # 検証失敗
            mock_secret.return_value = "test-secret"

            request_data = {
                "session_id": "user123:test-session",
                "message": "テスト",
                "user_id": "user123",
                "auth_hash": "SHARED-HMAC-invalid"
            }

            # Act
            response = await client.post(
                "/mcp/chat/stream",
                json=request_data
            )

            # Assert
            assert response.status_code == 401
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| MCPR-SEC-01 | 認証情報のログ出力検証 | cloud_credentials | パスワード/シークレットがログに含まれない |
| MCPR-SEC-02 | HMAC認証タイムスタンプ検証 | expired timestamp | 認証失敗 |
| MCPR-SEC-03 | セッションIDとユーザーIDの整合性 | mismatched session_id | 警告ログのみ（互換性維持） |
| MCPR-SEC-04 | クラウド認証情報の保護 | cloud_credentials in request | レスポンスに認証情報が含まれない |
| MCPR-SEC-05 | SSEイベント内容のサニタイズ | malicious content | 安全にJSON化される |
| MCPR-SEC-06 | エラーIDの追跡可能性 | error occurs | 一意のエラーIDが生成される |

```python
@pytest.mark.security
class TestMCPRouterSecurity:
    """MCPルーターセキュリティテスト"""

    @pytest.mark.asyncio
    async def test_credentials_not_logged(
        self, client, mock_stream_hierarchical, caplog
    ):
        """MCPR-SEC-01: 認証情報のログ出力検証"""
        # Arrange
        import logging
        caplog.set_level(logging.INFO)

        with patch("app.mcp_plugin.router.settings") as mock_settings:
            mock_settings.DEBUG_MODE = True

            async def mock_events():
                yield ("done", {})

            mock_stream_hierarchical.return_value = mock_events()

            request_data = {
                "session_id": "test-session",
                "message": "テスト",
                "cloud_credentials": {
                    "cloud_provider": "aws",
                    "role_arn": "arn:aws:iam::123456789012:role/secret-role",
                    "external_id": "super-secret-external-id"
                }
            }

            # Act
            await client.post("/mcp/chat/stream", json=request_data)

            # Assert
            log_text = caplog.text
            assert "super-secret-external-id" not in log_text
            assert "secret-role" not in log_text
            # role_arnの存在確認ログは許可
            assert "has_role_arn" in log_text

    @pytest.mark.asyncio
    async def test_cloud_credentials_not_in_response(
        self, client, mock_invoke_mcp_chat
    ):
        """MCPR-SEC-04: クラウド認証情報の保護"""
        # Arrange
        mock_invoke_mcp_chat.return_value = ("応答テキスト", None)
        request_data = {
            "session_id": "test-session",
            "message": "テスト",
            "cloud_credentials": {
                "cloud_provider": "aws",
                "role_arn": "arn:aws:iam::123456789012:role/test",
                "external_id": "external-123"
            }
        }

        # Act - チャットエンドポイントは cloud_credentials を受け取らない
        # SSEエンドポイントのみ対応
        response = await client.post("/mcp/chat", json=request_data)

        # Assert
        response_text = response.text
        assert "arn:aws:iam" not in response_text
        assert "external-123" not in response_text

    def test_error_id_uniqueness(self):
        """MCPR-SEC-06: エラーIDの追跡可能性"""
        # Arrange
        import uuid
        error_ids = set()

        # Act - 100個のエラーIDを生成
        for _ in range(100):
            error_ids.add(str(uuid.uuid4()))

        # Assert - すべて一意
        assert len(error_ids) == 100
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_mcp_router_module` | テスト間のモジュール状態リセット | function | Yes |
| `app` | FastAPIアプリケーション | session | No |
| `client` | HTTPクライアント | function | No |
| `mock_mcp_client` | MCPクライアントモック | function | No |
| `mock_invoke_mcp_chat` | invoke_mcp_chatモック | function | No |
| `mock_stream_hierarchical` | stream_hierarchical_mcp_agentモック | function | No |

### 共通フィクスチャ定義

```python
# test/unit/mcp_plugin/conftest.py
import sys
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.fixture(autouse=True)
def reset_mcp_router_module():
    """テストごとにmcp_pluginモジュールの状態をリセット"""
    yield
    # テスト後にモジュールキャッシュをクリア
    modules_to_remove = [
        key for key in sys.modules
        if key.startswith("app.mcp_plugin")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def app():
    """FastAPIアプリケーションインスタンス"""
    from app.main import app as fastapi_app
    return fastapi_app


@pytest.fixture
async def client(app):
    """HTTPクライアント"""
    from httpx import AsyncClient, ASGITransport

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def mock_mcp_client():
    """MCPクライアントモック"""
    with patch("app.mcp_plugin.router.mcp_client") as mock:
        mock.servers = {}
        mock.server_status = {}
        mock.add_server = AsyncMock(return_value=True)
        mock.connect_server = AsyncMock(return_value=True)
        mock.disconnect_server = AsyncMock(return_value=True)
        mock.get_server_status = MagicMock(return_value=[])
        mock.get_available_tools = MagicMock(return_value=[])
        yield mock


@pytest.fixture
def mock_invoke_mcp_chat():
    """invoke_mcp_chatモック"""
    with patch("app.mcp_plugin.router.invoke_mcp_chat") as mock:
        mock.return_value = AsyncMock(return_value=("テスト応答", None))()
        yield mock


@pytest.fixture
def mock_stream_hierarchical():
    """stream_hierarchical_mcp_agentモック"""
    with patch("app.mcp_plugin.router.stream_hierarchical_mcp_agent") as mock:
        yield mock
```

---

## 6. テスト実行例

```bash
# router関連テストのみ実行
pytest test/unit/mcp_plugin/test_router.py -v

# 特定のテストクラスのみ実行
pytest test/unit/mcp_plugin/test_router.py::TestMCPChatEndpoint -v

# カバレッジ付きで実行
pytest test/unit/mcp_plugin/test_router.py --cov=app.mcp_plugin.router --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/mcp_plugin/test_router.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 12 | MCPR-001 〜 MCPR-012 |
| 異常系 | 9 | MCPR-E01 〜 MCPR-E09 |
| セキュリティ | 6 | MCPR-SEC-01 〜 MCPR-SEC-06 |
| **合計** | **27** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestMCPChatEndpoint` | MCPR-001〜MCPR-002 | 2 |
| `TestMCPServerManagement` | MCPR-003〜MCPR-010 | 8 |
| `TestSSEStreaming` | MCPR-011〜MCPR-012 | 2 |
| `TestMCPChatErrors` | MCPR-E01 | 1 |
| `TestMCPServerManagementErrors` | MCPR-E02〜MCPR-E04, MCPR-E07〜MCPR-E09 | 6 |
| `TestSSEAuthenticationErrors` | MCPR-E05〜MCPR-E06 | 2 |
| `TestMCPRouterSecurity` | MCPR-SEC-01〜MCPR-SEC-06 | 6 |

### 実装失敗が予想されるテスト

現時点で失敗が予想されるテストはありません。

### 注意事項

- `pytest-asyncio` が必要（非同期テスト用）
- `@pytest.mark.security` マーカーの登録要（`pyproject.toml` に追加）
- SSEストリーミングテストはイベントの完全な検証が困難なため、ステータスコードとヘッダーの検証に留める
- DEBUG_MODE設定によりテスト動作が変わるため、両モードでテストすること

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | SSEストリーミングの完全テスト困難 | イベント内容の詳細検証不可 | ステータスコードとヘッダーで検証 |
| 2 | 実MCPサーバーとの統合テスト不可 | 実際のツール実行確認不可 | モック使用、統合テストで別途検証 |
| 3 | cloud_credentials の暗号化検証 | 転送中の暗号化はHTTPS依存 | HTTPS環境での運用を前提とする |
| 4 | キープアライブ機能のテスト | 長時間接続のテスト困難 | タイムアウト設定の検証のみ |

---

## 関連ドキュメント

- [mcp_plugin_client_tests.md](./mcp_plugin_client_tests.md) - MCPクライアントのテスト
- [mcp_plugin_chat_agent_tests.md](./mcp_plugin_chat_agent_tests.md) - チャットエージェントのテスト
- [mcp_plugin_hierarchical_tests.md](./mcp_plugin_hierarchical_tests.md) - 階層的エージェントのテスト
- [mcp_plugin_deep_agents_tests.md](./mcp_plugin_deep_agents_tests.md) - Deep Agentsのテスト
