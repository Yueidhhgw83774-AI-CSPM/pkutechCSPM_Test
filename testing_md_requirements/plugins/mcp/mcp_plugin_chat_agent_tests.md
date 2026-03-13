# mcp_plugin/chat_agent テストケース

## 1. 概要

MCPチャットエージェント（`chat_agent.py`）のテストケースを定義します。階層的エージェントとDeep Agentsの両モードを統合するエントリーポイントとして機能します。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `invoke_mcp_chat` | MCPチャットエージェント実行（モード選択） |
| `_invoke_hierarchical_mcp_chat` | 階層的MCPエージェント実行 |

### 1.2 カバレッジ目標: 90%

> **注記**: シンプルなルーティングモジュールのため、高カバレッジが期待できる

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/mcp_plugin/chat_agent.py` |
| テストコード | `test/unit/mcp_plugin/test_chat_agent.py` |
| conftest | `test/unit/mcp_plugin/conftest.py` |

### 1.4 補足情報

**モード切り替え:**
- `use_hierarchical=True`（デフォルト）: 階層的エージェント（コスト92%削減）
- `use_hierarchical=False`: Deep Agents（レガシー）

**エクスポート:**
- `invoke_mcp_chat`: メインエントリーポイント
- `stream_deep_agents_mcp_chat`: ストリーミング（deep_agentsからの再エクスポート）
- `clear_session_cache`: キャッシュクリア（deep_agentsからの再エクスポート）

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| MCPCA-001 | 階層的エージェントモードで実行 | use_hierarchical=True | response, progress |
| MCPCA-002 | Deep Agentsモードで実行 | use_hierarchical=False | response, None |
| MCPCA-003 | サーバー指定なしで全サーバー対象 | server_name=None | 正常応答 |
| MCPCA-004 | 特定サーバー指定で実行 | server_name="aws-docs" | 正常応答 |
| MCPCA-005 | エラー応答の適切なフォーマット | error in state | エラーメッセージ応答 |
| MCPCA-006 | progressの構築 | valid state | MCPProgress object |
| MCPCA-007 | 引数の正しい伝播（階層的モード） | all args | 全引数が下層に伝播 |
| MCPCA-008 | 引数の正しい伝播（Deep Agentsモード） | all args | 全引数が下層に伝播 |
| MCPCA-009 | モジュールエクスポートの検証 | module import | __all__の関数がエクスポート |

### 2.1 モード切り替えテスト

```python
# test/unit/mcp_plugin/test_chat_agent.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestInvokeMCPChat:
    """invoke_mcp_chatのテスト"""

    @pytest.mark.asyncio
    async def test_hierarchical_mode(
        self, mock_run_hierarchical
    ):
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
        mock_run_hierarchical.assert_called_once()

    @pytest.mark.asyncio
    async def test_deep_agents_mode(
        self, mock_invoke_deep_agents
    ):
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
        call_kwargs = mock_run_hierarchical.call_args.kwargs
        assert call_kwargs.get("server_name") == "aws-docs"

    @pytest.mark.asyncio
    async def test_args_propagation_hierarchical(
        self, mock_run_hierarchical, mock_build_progress
    ):
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
```

### 2.2 エラーレスポンステスト

```python
class TestHierarchicalErrorHandling:
    """階層的エージェントのエラーハンドリングテスト"""

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
    async def test_progress_building(self, mock_run_hierarchical):
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
        # progress構造の検証（build_progress_from_stateの実装に依存）
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| MCPCA-E01 | 階層的エージェント例外発生 | run_hierarchical raises | エラーID付きメッセージ, None |
| MCPCA-E02 | Deep Agents例外発生 | invoke_deep_agents raises | 例外が伝播 |
| MCPCA-E03 | 応答なしの状態 | final_response=None, error=None | デフォルトエラーメッセージ |

### 3.1 例外ハンドリングテスト

```python
class TestChatAgentExceptions:
    """チャットエージェント例外のテスト"""

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
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| MCPCA-SEC-01 | エラーIDの一意性 | exception occurs | 一意のUUIDが生成 |
| MCPCA-SEC-02 | 内部エラー詳細の非公開（例外経路） | internal exception | 詳細がユーザーに露出しない |
| MCPCA-SEC-03 | セッションIDのログ記録 | valid session_id | session_idがログに記録 |
| MCPCA-SEC-04 | state["error"]の機密情報露出防止 | error with credentials | 機密情報がユーザーに露出しない【実装失敗予定】 |
| MCPCA-SEC-05 | セッションIDのログインジェクション耐性 | malicious session_id | ログインジェクションが発生しない |
| MCPCA-SEC-06 | server_nameの安全性検証 | malicious server_name | パストラバーサル等が発生しない |

```python
@pytest.mark.security
class TestChatAgentSecurity:
    """チャットエージェントセキュリティテスト"""

    @pytest.mark.asyncio
    async def test_error_id_uniqueness(self, mock_run_hierarchical):
        """MCPCA-SEC-01: エラーIDの一意性"""
        # Arrange
        from app.mcp_plugin.chat_agent import invoke_mcp_chat
        import re

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
    async def test_session_id_logged(
        self, mock_run_hierarchical, caplog
    ):
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
    async def test_state_error_credential_exposure(self, mock_run_hierarchical):
        """MCPCA-SEC-04: state["error"]の機密情報露出防止【実装失敗予定】

        注意: 現在の実装(Line 102)では state["error"] が直接ユーザーに返される。
        このテストは、機密情報を含むエラーがユーザーに露出する脆弱性を検出する。
        実装修正後にこのテストがパスするようになる。
        """
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
        # 注: 現在の実装では失敗する（脆弱性の検出）
        assert "password" not in response.lower()
        assert "P@ssw0rd123" not in response
        assert "admin" not in response
        # エラーIDのみ表示されるべき
        assert "エラーID" in response

    @pytest.mark.asyncio
    async def test_session_id_log_injection(
        self, mock_run_hierarchical, caplog
    ):
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
        # 改行後の偽ログエントリが独立したログ行として出力されていないこと
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

        # パストラバーサル/SSRF攻撃パターン
        malicious_server_names = [
            "../../../etc/passwd",
            "http://evil.com/malicious",
            "file:///etc/passwd",
            "server-name; rm -rf /",
        ]

        # Act & Assert
        for server_name in malicious_server_names:
            # このモジュールはルーティング層なので、入力をそのまま渡す
            # 下層での検証を確認するためのテスト
            await invoke_mcp_chat(
                session_id="test-session",
                prompt="テスト",
                server_name=server_name,
                use_hierarchical=True
            )

            # server_nameが下層にそのまま渡されることを確認
            # （検証は下層モジュールの責任だが、この層で変更されていないことを確認）
            call_kwargs = mock_run_hierarchical.call_args.kwargs
            assert call_kwargs.get("server_name") == server_name

            mock_run_hierarchical.reset_mock()
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `mock_run_hierarchical` | run_hierarchical_mcp_agentモック | function | No |
| `mock_invoke_deep_agents` | invoke_deep_agents_mcp_chatモック | function | No |
| `mock_build_progress` | build_progress_from_stateモック | function | No |
| `reset_module_state` | モジュール状態のリセット | function | Yes |

### 共通フィクスチャ定義

```python
# test/unit/mcp_plugin/conftest.py に追加
import sys
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.fixture(autouse=True)
def reset_module_state():
    """モジュール状態のリセット（autouse）"""
    # テスト前の状態を保存
    modules_to_reset = [
        "app.mcp_plugin.chat_agent",
        "app.mcp_plugin.deep_agents",
        "app.mcp_plugin.hierarchical",
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
def mock_run_hierarchical():
    """run_hierarchical_mcp_agentモック（非同期関数）

    注: new_callable=AsyncMockを使用することで、awaitされた時に
    return_valueの値が返される。
    """
    with patch(
        "app.mcp_plugin.chat_agent.run_hierarchical_mcp_agent",
        new_callable=AsyncMock
    ) as mock:
        mock.return_value = {"final_response": "OK"}
        yield mock


@pytest.fixture
def mock_invoke_deep_agents():
    """invoke_deep_agents_mcp_chatモック（非同期関数）

    注: new_callable=AsyncMockを使用することで、awaitされた時に
    return_valueの値が返される。
    """
    with patch(
        "app.mcp_plugin.chat_agent.invoke_deep_agents_mcp_chat",
        new_callable=AsyncMock
    ) as mock:
        mock.return_value = "OK"
        yield mock


@pytest.fixture
def mock_build_progress():
    """build_progress_from_stateモック

    階層的エージェントで使用されるprogress構築関数のモック。
    MCPProgressオブジェクトを返す。
    """
    with patch("app.mcp_plugin.chat_agent.build_progress_from_state") as mock:
        mock_progress = MagicMock()
        mock_progress.llm_calls = 5
        mock_progress.llm_calls_by_model = {"gpt-5-mini": 1, "gpt-5-nano": 3, "gpt-5.1-codex": 1}
        mock_progress.tool_calls = ["search_documentation", "get_details"]
        mock.return_value = mock_progress
        yield mock
```

---

## 6. テスト実行例

```bash
# chat_agent関連テストのみ実行
pytest test/unit/mcp_plugin/test_chat_agent.py -v

# カバレッジ付きで実行
pytest test/unit/mcp_plugin/test_chat_agent.py --cov=app.mcp_plugin.chat_agent --cov-report=term-missing -v
```

---

## 7. テストケース一覧（サマリー）

### テストID規則

本仕様書では、他の完成済みテスト仕様書（jobs_tests.md, chat_dashboard_tests.md等）と同様に、**カテゴリ別ID**を採用しています：

- **正常系**: `MCPCA-{3桁連番}` (例: MCPCA-001, MCPCA-002, ...)
- **異常系**: `MCPCA-E{2桁連番}` (例: MCPCA-E01, MCPCA-E02, ...)
- **セキュリティ**: `MCPCA-SEC-{2桁連番}` (例: MCPCA-SEC-01, MCPCA-SEC-02, ...)

> **注記**: プレフィックス`MCPCA`は "MCP Chat Agent" の略称です。

### テストケース数

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 9 | MCPCA-001 〜 MCPCA-009 |
| 異常系 | 3 | MCPCA-E01 〜 MCPCA-E03 |
| セキュリティ | 6 | MCPCA-SEC-01 〜 MCPCA-SEC-06 |
| **合計** | **18** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestInvokeMCPChat` | MCPCA-001〜MCPCA-004, MCPCA-007〜MCPCA-009 | 7 |
| `TestHierarchicalErrorHandling` | MCPCA-005〜MCPCA-006 | 2 |
| `TestChatAgentExceptions` | MCPCA-E01〜MCPCA-E03 | 3 |
| `TestChatAgentSecurity` | MCPCA-SEC-01〜MCPCA-SEC-06 | 6 |

### 実装失敗が予想されるテスト

| テストID | 理由 | 修正方針 |
|---------|------|---------|
| MCPCA-SEC-04 | Line 102でstate["error"]が直接ユーザーに返される脆弱性 | エラーIDを生成し、詳細をログに記録してエラーIDのみ返すよう修正 |

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | 実際のLLM呼び出しテスト不可 | モデル応答品質の検証不可 | 統合テストで別途検証 |
| 2 | state["error"]の直接露出（Line 102） | 機密情報漏洩リスク | 実装修正必須（エラーIDへ変更） |
| 3 | 入力検証なし（session_id, server_name） | インジェクションリスク | 下層モジュールまたはバリデーション層で実装 |

### セキュリティ境界の明確化

このモジュール（`chat_agent.py`）のセキュリティ責任範囲：

| 責任範囲 | 担当 |
|---------|------|
| 例外時のエラーID生成・内部詳細非公開 | chat_agent.py（Line 106-109）✅ 実装済み |
| state["error"]の機密情報マスク | chat_agent.py（Line 102）❌ **要修正** |
| 入力検証（prompt, session_id, server_name） | router層またはバリデーション層 |
| MCP検索の安全性 | hierarchical/ または deep_agents/ |
| 認証・認可 | router層（SHARED-HMAC） |

---

## 関連ドキュメント

- [mcp_plugin_router_tests.md](./mcp_plugin_router_tests.md) - APIルーターのテスト
- [mcp_plugin_deep_agents_tests.md](./mcp_plugin_deep_agents_tests.md) - Deep Agentsのテスト
- [mcp_plugin_hierarchical_tests.md](./mcp_plugin_hierarchical_tests.md) - 階層的エージェントのテスト
