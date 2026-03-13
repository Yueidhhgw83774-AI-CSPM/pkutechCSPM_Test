# chat_dashboard 補足テストケース

## 1. 概要

既存 `chat_dashboard_tests.md`（55件）では未カバーだった公開インターフェース・エッジケースを補完するテスト仕様書です。

### 1.1 本仕様書のスコープ

| 対象ファイル | 未カバー関数/分岐 | 件数 |
|-------------|------------------|------|
| `simple_chat_handler.py` | `ChatMessage.to_langchain_message()`, `_get_system_prompt()`, `get_session_info()`, `clear_session()`, `get_simple_session_info()`, `clear_simple_session()` | 6関数 |
| `basic_auth_logic.py` | `clear_basic_client_cache()`, `decode_basic_auth` エッジケース, `create_opensearch_client_with_basic_auth` ポート/CA証明書分岐 | 1関数+エッジケース |

### 1.2 既存仕様書との関係

- 既存: `chat_dashboard_tests.md`（CHAT-001〜024, CHAT-E01〜E15, CHAT-SEC-01〜SEC-16）
- 本仕様書: **CHAT-S001〜S018**（正常系）/ **CHAT-SE01〜SE04**（異常系）/ **CHAT-SSEC-01〜SSEC-02**（セキュリティ）
- ID衝突なし（接頭辞 `S`, `SE`, `SSEC` で分離）

### 1.3 主要機能（未カバー関数一覧）

| 機能 | 説明 |
|------|------|
| `ChatMessage.to_langchain_message()` | ChatMessageをLangChainメッセージ形式に変換 |
| `SimpleChatBot._get_system_prompt()` | CSPMダッシュボード用システムプロンプトを返却 |
| `SimpleChatBot.get_session_info()` | セッションのメッセージ数を取得 |
| `SimpleChatBot.clear_session()` | セッションの履歴をクリア |
| `get_simple_session_info()` | シングルトン経由でセッション情報を取得 |
| `clear_simple_session()` | シングルトン経由でセッションをクリア |
| `clear_basic_client_cache()` | Basic認証クライアントキャッシュをクリア |
| `decode_basic_auth` エッジケース | 複数コロン・UTF-8不可・空文字列 |
| `create_opensearch_client_with_basic_auth` 分岐 | ポート/CA証明書分岐 |

### 1.4 カバレッジ目標: 95%

> **注記**: 既存仕様書（85%目標）と合わせて95%を目指す。本仕様書はユニットレベルの関数テストが中心。

### 1.5 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象（チャットハンドラー） | `app/chat_dashboard/simple_chat_handler.py` |
| テスト対象（Basic認証ロジック） | `app/chat_dashboard/basic_auth_logic.py` |
| テストコード | `test/unit/chat_dashboard/test_chat_dashboard_supplement.py` |
| conftest | `test/unit/chat_dashboard/conftest.py` |

### 1.6 補足情報

**テスト対象の依存関係:**
- `ChatMessage.to_langchain_message()` → `langchain_core.messages.HumanMessage`, `AIMessage`
- `SimpleChatBot.get_session_info()` / `clear_session()` → `ChatHistory` への委譲
- `get_simple_session_info()` / `clear_simple_session()` → `get_simple_chatbot()` シングルトン経由
- `clear_basic_client_cache()` → モジュールレベル `_basic_client_cache` dict
- `create_opensearch_client_with_basic_auth()` → `settings.OPENSEARCH_URL`, `is_aws_opensearch_service()`, `settings.OPENSEARCH_CA_CERTS_PATH`

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CHAT-S001 | to_langchain_message role="user" | ChatMessage(role="user") | HumanMessage インスタンス |
| CHAT-S002 | to_langchain_message role="assistant" | ChatMessage(role="assistant") | AIMessage インスタンス |
| CHAT-S003 | _get_system_prompt 戻り値がstrであること | SimpleChatBot インスタンス | str型を返却 |
| CHAT-S004 | _get_system_prompt 必須キーワード含有 | SimpleChatBot インスタンス | "CSPM", "セキュリティ", "ツール" の3語すべてを含む |
| CHAT-S005 | get_session_info 正常ケース | 既存セッションID | {"message_count": N} |
| CHAT-S006 | get_session_info 存在しないセッション | 未登録セッションID | {"message_count": 0} |
| CHAT-S007 | clear_session 正常ケース | メッセージ追加済みセッションID | 履歴クリア・カウント0 |
| CHAT-S008 | clear_session 存在しないセッションID（冪等性） | 未登録セッションID | 例外なし |
| CHAT-S009 | get_simple_session_info ユーティリティ経由 | セッションID | get_session_info の結果と同一 |
| CHAT-S010 | clear_simple_session ユーティリティ経由 | セッションID | セッションがクリアされる |
| CHAT-S011 | clear_basic_client_cache 正常動作 | キャッシュにエントリあり | キャッシュが空になる |
| CHAT-S012 | clear_basic_client_cache 空キャッシュ冪等性 | 空キャッシュ | 例外なし・キャッシュは空のまま |
| CHAT-S013 | decode_basic_auth 複数コロン含むトークン | "user:pass:word:extra" | ("user", "pass:word:extra") |
| CHAT-S014 | create_opensearch_client AWS+ポートなし→443 | AWS URL（ポートなし） | port=443 |
| CHAT-S015 | create_opensearch_client 非AWS+ポートなし→9200 | 非AWS URL（ポートなし） | port=9200 |
| CHAT-S016 | create_opensearch_client URL明示ポート使用 | URL にポート指定 | 指定ポートが使用される |
| CHAT-S017 | create_opensearch_client CA証明書パス設定 | 非AWS+CAパスあり | ca_certs が設定される |
| CHAT-S018 | キャッシュクリア後の再作成で新インスタンス | クリア→再作成 | 新しいクライアントインスタンス |

### 2.1 ChatMessage 変換テスト（CHAT-S001〜S002）

```python
# test/unit/chat_dashboard/test_chat_dashboard_supplement.py
import pytest
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage


class TestChatMessageConversion:
    """ChatMessage.to_langchain_message() の変換テスト"""

    def test_to_langchain_message_user_role(self):
        """CHAT-S001: role='user' → HumanMessage に変換されること

        simple_chat_handler.py:72-73 の分岐をカバーする。
        """
        # Arrange
        from app.chat_dashboard.simple_chat_handler import ChatMessage
        msg = ChatMessage(role="user", content="テスト質問", timestamp=datetime.now())

        # Act
        result = msg.to_langchain_message()

        # Assert
        assert isinstance(result, HumanMessage)
        assert result.content == "テスト質問"

    def test_to_langchain_message_assistant_role(self):
        """CHAT-S002: role='assistant' → AIMessage に変換されること

        simple_chat_handler.py:74-75 の分岐をカバーする。
        """
        # Arrange
        from app.chat_dashboard.simple_chat_handler import ChatMessage
        msg = ChatMessage(role="assistant", content="テスト回答", timestamp=datetime.now())

        # Act
        result = msg.to_langchain_message()

        # Assert
        assert isinstance(result, AIMessage)
        assert result.content == "テスト回答"
```

### 2.2 システムプロンプトテスト（CHAT-S003〜S004）

```python
class TestSystemPrompt:
    """SimpleChatBot._get_system_prompt() のテスト"""

    @pytest.fixture
    def chatbot(self, mock_llm_factory, mock_chat_tools):
        """SimpleChatBot インスタンスを生成

        注意: SimpleChatBot は @dataclass ではなく通常クラスのため、
        _initialize_components 内の動的インポートをモック化する必要がある。
        mock_llm_factory は app.core.llm_factory.get_chat_llm をパッチする。
        """
        from app.chat_dashboard.simple_chat_handler import SimpleChatBot
        return SimpleChatBot()

    def test_get_system_prompt_returns_str(self, chatbot):
        """CHAT-S003: _get_system_prompt が文字列を返すこと

        simple_chat_handler.py:156-194 をカバーする。
        """
        # Act
        result = chatbot._get_system_prompt()

        # Assert
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_system_prompt_contains_required_keywords(self, chatbot):
        """CHAT-S004: _get_system_prompt が必須キーワード3語すべてを含むこと

        simple_chat_handler.py:156-194 の内容妥当性を検証する。
        ツール名の直接検証ではなく、機能的なキーワードで検証する。
        3語すべてが AND 条件で必須（1つでも欠けたら失敗）。
        """
        # Act
        result = chatbot._get_system_prompt()

        # Assert — CSPMダッシュボードのコンテキストに必要なキーワード（すべて必須）
        assert "CSPM" in result, "システムプロンプトに 'CSPM' が含まれていない"
        assert "セキュリティ" in result, "システムプロンプトに 'セキュリティ' が含まれていない"
        assert "ツール" in result or "tool" in result.lower(), \
            "システムプロンプトに 'ツール' または 'tool' が含まれていない"
        # スキャン関連機能の言及を検証（ツール関数名ではなく機能の存在確認）
        assert "スキャン" in result, "システムプロンプトに 'スキャン' が含まれていない"
```

### 2.3 セッション管理テスト（CHAT-S005〜S010）

```python
class TestSessionManagement:
    """SimpleChatBot.get_session_info() / clear_session() のテスト

    注意: CHAT-S005〜S008 は chatbot フィクスチャで SimpleChatBot インスタンスを使用し、
    CHAT-S009〜S010 はシングルトン経由のユーティリティ関数テストのため
    mock_llm_factory / mock_chat_tools を直接受け取る。
    ChatHistory.add_message の直接呼び出しは、get_session_info/clear_session の
    委譲テストとして意図的に内部APIを使用している。
    """

    @pytest.fixture
    def chatbot(self, mock_llm_factory, mock_chat_tools):
        """SimpleChatBot インスタンスを生成"""
        from app.chat_dashboard.simple_chat_handler import SimpleChatBot
        return SimpleChatBot()

    def test_get_session_info_with_messages(self, chatbot):
        """CHAT-S005: メッセージ追加済みセッションの情報を取得

        simple_chat_handler.py:471-475 をカバーする。
        ChatHistory.get_message_count への委譲を確認する。
        """
        # Arrange
        session_id = "test-session-001"
        chatbot.chat_history.add_message(session_id, "user", "質問1")
        chatbot.chat_history.add_message(session_id, "assistant", "回答1")

        # Act
        result = chatbot.get_session_info(session_id)

        # Assert
        assert result == {"message_count": 2}

    def test_get_session_info_nonexistent_session(self, chatbot):
        """CHAT-S006: 存在しないセッションIDでメッセージ数0を返すこと

        simple_chat_handler.py:471-475 をカバーする。
        """
        # Act
        result = chatbot.get_session_info("nonexistent-session")

        # Assert
        assert result == {"message_count": 0}

    def test_clear_session_removes_history(self, chatbot):
        """CHAT-S007: clear_session でセッション履歴が削除されること

        simple_chat_handler.py:477-479 をカバーする。
        ChatHistory.clear_session への委譲を確認する。
        """
        # Arrange
        session_id = "test-session-clear"
        chatbot.chat_history.add_message(session_id, "user", "質問")
        chatbot.chat_history.add_message(session_id, "assistant", "回答")
        assert chatbot.get_session_info(session_id)["message_count"] == 2

        # Act
        chatbot.clear_session(session_id)

        # Assert
        assert chatbot.get_session_info(session_id)["message_count"] == 0

    def test_clear_session_idempotent(self, chatbot):
        """CHAT-S008: 存在しないセッションIDのクリアが例外を発生させないこと（冪等性）

        simple_chat_handler.py:477-479 をカバーする。
        ChatHistory.clear_session は存在しないキーの場合何もしない。
        """
        # Act & Assert — 例外が発生しないことを確認
        chatbot.clear_session("nonexistent-session-id")

    @pytest.mark.asyncio
    async def test_get_simple_session_info_via_utility(self, mock_llm_factory, mock_chat_tools):
        """CHAT-S009: get_simple_session_info がシングルトン経由で正常動作すること

        simple_chat_handler.py:564-567 をカバーする。
        """
        # Arrange
        import app.chat_dashboard.simple_chat_handler as handler
        handler._simple_chatbot = None  # シングルトンリセット
        from app.chat_dashboard.simple_chat_handler import get_simple_session_info, get_simple_chatbot

        chatbot = get_simple_chatbot()
        session_id = "test-utility-session"
        chatbot.chat_history.add_message(session_id, "user", "テスト")

        # Act
        result = await get_simple_session_info(session_id)

        # Assert
        assert result == {"message_count": 1}

    @pytest.mark.asyncio
    async def test_clear_simple_session_via_utility(self, mock_llm_factory, mock_chat_tools):
        """CHAT-S010: clear_simple_session がシングルトン経由でセッションをクリアすること

        simple_chat_handler.py:570-573 をカバーする。
        """
        # Arrange
        import app.chat_dashboard.simple_chat_handler as handler
        handler._simple_chatbot = None  # シングルトンリセット
        from app.chat_dashboard.simple_chat_handler import (
            clear_simple_session, get_simple_chatbot, get_simple_session_info
        )

        chatbot = get_simple_chatbot()
        session_id = "test-clear-utility"
        chatbot.chat_history.add_message(session_id, "user", "テスト")
        chatbot.chat_history.add_message(session_id, "assistant", "回答")

        # Act
        await clear_simple_session(session_id)

        # Assert
        result = await get_simple_session_info(session_id)
        assert result == {"message_count": 0}
```

### 2.4 Basic認証ロジック補足テスト（CHAT-S011〜S018）

```python
from unittest.mock import patch, MagicMock
import base64


class TestClearBasicClientCache:
    """clear_basic_client_cache() のテスト"""

    def test_clear_cache_with_entries(self):
        """CHAT-S011: キャッシュにエントリがある状態でクリアが正常動作すること

        basic_auth_logic.py:126-132 をカバーする。
        """
        # Arrange
        import app.chat_dashboard.basic_auth_logic as auth_module
        auth_module._basic_client_cache["user1:pass1"] = MagicMock()
        auth_module._basic_client_cache["user2:pass2"] = MagicMock()
        assert len(auth_module._basic_client_cache) == 2

        # Act
        auth_module.clear_basic_client_cache()

        # Assert
        assert len(auth_module._basic_client_cache) == 0

    def test_clear_cache_idempotent(self):
        """CHAT-S012: 空キャッシュに対するクリアが冪等に動作すること

        basic_auth_logic.py:126-132 をカバーする。
        """
        # Arrange
        import app.chat_dashboard.basic_auth_logic as auth_module
        auth_module._basic_client_cache.clear()
        assert len(auth_module._basic_client_cache) == 0

        # Act & Assert — 例外が発生しないことを確認
        auth_module.clear_basic_client_cache()
        assert len(auth_module._basic_client_cache) == 0


class TestDecodeBasicAuthEdgeCases:
    """decode_basic_auth() のエッジケーステスト"""

    def test_decode_multiple_colons(self):
        """CHAT-S013: コロンを複数含むトークンで split(':', 1) 動作を確認

        basic_auth_logic.py:37 の split(":", 1) をカバーする。
        パスワードにコロンが含まれるケース。
        """
        # Arrange
        from app.chat_dashboard.basic_auth_logic import decode_basic_auth
        raw = "user:pass:word:extra"
        token = base64.b64encode(raw.encode("utf-8")).decode("utf-8")

        # Act
        username, password = decode_basic_auth(token)

        # Assert
        assert username == "user"
        assert password == "pass:word:extra"


class TestCreateOpensearchClientBranches:
    """create_opensearch_client_with_basic_auth() のポート/CA証明書分岐テスト"""

    @pytest.fixture(autouse=True)
    def reset_cache(self):
        """テストごとにキャッシュをクリア"""
        import app.chat_dashboard.basic_auth_logic as auth_module
        auth_module._basic_client_cache.clear()
        yield
        auth_module._basic_client_cache.clear()

    @patch("app.chat_dashboard.basic_auth_logic.OpenSearch")
    @patch("app.chat_dashboard.basic_auth_logic.is_aws_opensearch_service", return_value=True)
    @patch("app.chat_dashboard.basic_auth_logic.settings")
    def test_aws_no_port_defaults_to_443(self, mock_settings, mock_is_aws, mock_opensearch):
        """CHAT-S014: AWS OpenSearch+ポートなしの場合、port=443がデフォルトになること

        basic_auth_logic.py:93-95 の分岐をカバーする。
        """
        # Arrange
        mock_settings.OPENSEARCH_URL = "https://search-example.us-east-1.es.amazonaws.com"
        mock_settings.OPENSEARCH_CA_CERTS_PATH = None

        # Act
        from app.chat_dashboard.basic_auth_logic import create_opensearch_client_with_basic_auth
        create_opensearch_client_with_basic_auth("admin", "password")

        # Assert
        call_kwargs = mock_opensearch.call_args.kwargs
        assert call_kwargs["hosts"][0]["port"] == 443
        # TLS検証設定が厳密であることも確認
        assert call_kwargs["verify_certs"] is True
        assert call_kwargs["ssl_assert_hostname"] is True

    @patch("app.chat_dashboard.basic_auth_logic.OpenSearch")
    @patch("app.chat_dashboard.basic_auth_logic.is_aws_opensearch_service", return_value=False)
    @patch("app.chat_dashboard.basic_auth_logic.settings")
    def test_non_aws_no_port_defaults_to_9200(self, mock_settings, mock_is_aws, mock_opensearch):
        """CHAT-S015: 非AWS+ポートなしの場合、port=9200がデフォルトになること

        basic_auth_logic.py:96-97 の分岐をカバーする。
        """
        # Arrange
        mock_settings.OPENSEARCH_URL = "https://opensearch.local"
        mock_settings.OPENSEARCH_CA_CERTS_PATH = None

        # Act
        from app.chat_dashboard.basic_auth_logic import create_opensearch_client_with_basic_auth
        create_opensearch_client_with_basic_auth("admin", "password")

        # Assert
        call_kwargs = mock_opensearch.call_args.kwargs
        assert call_kwargs["hosts"][0]["port"] == 9200
        # TLS検証設定が厳密であることも確認
        assert call_kwargs["verify_certs"] is True
        assert call_kwargs["ssl_assert_hostname"] is True

    @patch("app.chat_dashboard.basic_auth_logic.OpenSearch")
    @patch("app.chat_dashboard.basic_auth_logic.is_aws_opensearch_service", return_value=False)
    @patch("app.chat_dashboard.basic_auth_logic.settings")
    def test_explicit_port_in_url(self, mock_settings, mock_is_aws, mock_opensearch):
        """CHAT-S016: URL にポートが明示指定されている場合、そのポートが使用されること

        basic_auth_logic.py:93 の parsed_url.port を使用するケースをカバーする。
        """
        # Arrange
        mock_settings.OPENSEARCH_URL = "https://opensearch.local:9201"
        mock_settings.OPENSEARCH_CA_CERTS_PATH = None

        # Act
        from app.chat_dashboard.basic_auth_logic import create_opensearch_client_with_basic_auth
        create_opensearch_client_with_basic_auth("admin", "password")

        # Assert
        call_kwargs = mock_opensearch.call_args.kwargs
        assert call_kwargs["hosts"][0]["port"] == 9201
        # TLS検証設定が厳密であることも確認
        assert call_kwargs["verify_certs"] is True
        assert call_kwargs["ssl_assert_hostname"] is True

    @patch("app.chat_dashboard.basic_auth_logic.OpenSearch")
    @patch("app.chat_dashboard.basic_auth_logic.is_aws_opensearch_service", return_value=False)
    @patch("app.chat_dashboard.basic_auth_logic.settings")
    def test_ca_certs_path_configured(self, mock_settings, mock_is_aws, mock_opensearch):
        """CHAT-S017: 非AWS環境でCA証明書パスが設定されている場合、ca_certsが設定されること

        basic_auth_logic.py:111-113 の分岐をカバーする。
        """
        # Arrange
        mock_settings.OPENSEARCH_URL = "https://opensearch.local:9200"
        mock_settings.OPENSEARCH_CA_CERTS_PATH = "/etc/ssl/certs/ca-bundle.crt"

        # Act
        from app.chat_dashboard.basic_auth_logic import create_opensearch_client_with_basic_auth
        create_opensearch_client_with_basic_auth("admin", "password")

        # Assert
        call_kwargs = mock_opensearch.call_args.kwargs
        assert call_kwargs["ca_certs"] == "/etc/ssl/certs/ca-bundle.crt"

    @patch("app.chat_dashboard.basic_auth_logic.OpenSearch")
    @patch("app.chat_dashboard.basic_auth_logic.is_aws_opensearch_service", return_value=False)
    @patch("app.chat_dashboard.basic_auth_logic.settings")
    def test_cache_clear_then_recreate_new_instance(self, mock_settings, mock_is_aws, mock_opensearch):
        """CHAT-S018: キャッシュクリア後の再作成で新しいインスタンスが返されること

        basic_auth_logic.py:120（キャッシュ保存）→ 126（クリア）→ 120（再保存）をカバーする。
        注意: reset_cache フィクスチャもキャッシュをクリアするが、本テストでは
        clear_basic_client_cache() 関数自体の動作（クリア→再作成の一連の流れ）を
        テスト対象としているため、テスト内で明示的にクリアを呼び出す。
        """
        # Arrange
        mock_settings.OPENSEARCH_URL = "https://opensearch.local:9200"
        mock_settings.OPENSEARCH_CA_CERTS_PATH = None
        first_mock = MagicMock(name="first_client")
        second_mock = MagicMock(name="second_client")
        mock_opensearch.side_effect = [first_mock, second_mock]

        from app.chat_dashboard.basic_auth_logic import (
            create_opensearch_client_with_basic_auth, clear_basic_client_cache
        )

        # Act — 初回作成
        client1 = create_opensearch_client_with_basic_auth("admin", "password")

        # Act — キャッシュクリア
        clear_basic_client_cache()

        # Act — 再作成
        client2 = create_opensearch_client_with_basic_auth("admin", "password")

        # Assert
        assert client1 is not client2
        assert mock_opensearch.call_count == 2
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CHAT-SE01 | to_langchain_message 不正role→ValueError | role="system" | ValueError("不明なロール: system") |
| CHAT-SE02 | get_simple_session_info chatbot未初期化時 | 初期化失敗するモック | HTTPException (500) |
| CHAT-SE03 | decode_basic_auth UTF-8デコード不可 | 非UTF-8バイト列のbase64 | HTTPException (401) |
| CHAT-SE04 | decode_basic_auth 空文字列 | "" | HTTPException (401) |

### 3.1 ChatMessage異常系（CHAT-SE01）

```python
class TestChatMessageErrors:
    """ChatMessage 変換の異常系テスト"""

    def test_to_langchain_message_invalid_role(self):
        """CHAT-SE01: 不正なロールでValueErrorが発生すること

        simple_chat_handler.py:76-77 の else 分岐をカバーする。
        """
        # Arrange
        from app.chat_dashboard.simple_chat_handler import ChatMessage
        msg = ChatMessage(role="system", content="テスト", timestamp=datetime.now())

        # Act & Assert
        with pytest.raises(ValueError, match="不明なロール: system"):
            msg.to_langchain_message()
```

### 3.2 セッション管理異常系（CHAT-SE02）

```python
class TestSessionManagementErrors:
    """セッション管理ユーティリティ関数の異常系テスト"""

    @pytest.mark.asyncio
    async def test_get_simple_session_info_initialization_failure(self):
        """CHAT-SE02: チャットボット未初期化時にget_simple_session_infoが例外を発生すること

        simple_chat_handler.py:564-567 → get_simple_chatbot() → SimpleChatBot.__init__
        が失敗するケースをカバーする。
        _initialize_components が Exception を raise すると、__init__ 内の
        except ブロックが HTTPException(500) に変換して再 raise する。

        注意: 意図的に mock_llm_factory / mock_chat_tools フィクスチャを使用せず、
        _initialize_components 自体のパッチで初期化失敗を再現している。
        """
        # Arrange — インポートはパッチ適用前に行う（モジュールキャッシュ対策）
        from fastapi import HTTPException
        from app.chat_dashboard.simple_chat_handler import get_simple_session_info
        import app.chat_dashboard.simple_chat_handler as handler
        handler._simple_chatbot = None  # シングルトンリセット

        # Act & Assert
        with patch(
            "app.chat_dashboard.simple_chat_handler.SimpleChatBot._initialize_components",
            side_effect=Exception("LLM初期化失敗")
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_simple_session_info("test-session")

            assert exc_info.value.status_code == 500
```

### 3.3 Basic認証デコード異常系（CHAT-SE03〜SE04）

```python
class TestDecodeBasicAuthErrors:
    """decode_basic_auth() の異常系テスト"""

    def test_decode_non_utf8_bytes(self):
        """CHAT-SE03: UTF-8デコード不可能なバイト列でHTTPException(401)が発生すること

        basic_auth_logic.py:31 の decoded_bytes.decode("utf-8") で
        UnicodeDecodeError が発生するケースをカバーする。
        """
        # Arrange
        from app.chat_dashboard.basic_auth_logic import decode_basic_auth
        # 非UTF-8バイト列をbase64エンコード
        non_utf8_bytes = bytes([0xFF, 0xFE, 0x80, 0x81])
        token = base64.b64encode(non_utf8_bytes).decode("ascii")

        # Act & Assert
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            decode_basic_auth(token)

        assert exc_info.value.status_code == 401

    def test_decode_empty_string(self):
        """CHAT-SE04: 空文字列の入力でHTTPException(401)が発生すること

        basic_auth_logic.py:30-36 をカバーする。
        base64.b64decode("") は b"" を返し、decode("utf-8") は "" を返す。
        ":" が含まれないため ValueError("Invalid format: no colon separator found")
        が発生し、except ブロックで HTTPException(401) に変換される。
        """
        # Arrange
        from app.chat_dashboard.basic_auth_logic import decode_basic_auth
        from fastapi import HTTPException

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            decode_basic_auth("")

        assert exc_info.value.status_code == 401
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CHAT-SSEC-01 | キャッシュクリア後にデータ残存しないこと | クリア実行 | キャッシュ参照不可 |
| CHAT-SSEC-02 | to_langchain_message 巨大文字列のサイズ制限検証 | 1MB超の content | ValueError(match="size\|サイズ") で拒否されるべき [EXPECTED_TO_FAIL] |

### 4.1 キャッシュセキュリティ（CHAT-SSEC-01）

```python
@pytest.mark.security
class TestCacheSecuritySupplement:
    """キャッシュクリアのセキュリティ検証（補足）"""

    def test_cache_clear_no_residual_data(self):
        """CHAT-SSEC-01: キャッシュクリア後にデータが残存しないこと

        basic_auth_logic.py:126-132 をカバーする。
        クリア後にキャッシュキーが `not in` で参照不可かつ辞書サイズが0であることを
        確認し、メモリ上の機密情報残存リスクを検証する。
        """
        # Arrange
        import app.chat_dashboard.basic_auth_logic as auth_module
        cache_key = "sensitive_user:sensitive_password"
        auth_module._basic_client_cache[cache_key] = MagicMock()

        # Act
        auth_module.clear_basic_client_cache()

        # Assert — キャッシュキーでアクセスできないことを確認
        assert cache_key not in auth_module._basic_client_cache
        assert len(auth_module._basic_client_cache) == 0
        # dict.clear() は内部ハッシュテーブルをクリアするので参照残存なし
```

### 4.2 入力サイズ制限（CHAT-SSEC-02）

```python
@pytest.mark.security
class TestInputSizeSupplement:
    """入力サイズ制限のセキュリティ検証（補足）"""

    @pytest.mark.xfail(
        reason="ChatMessage.content にサイズ制限が未実装（simple_chat_handler.py:64-68）",
        strict=True
    )
    def test_to_langchain_message_large_content_rejected(self):
        """CHAT-SSEC-02: 巨大文字列（1MB超）のcontentがサイズ制限で拒否されること

        【実装失敗予定】simple_chat_handler.py:64-68 で ChatMessage は
        @dataclass のため content にサイズ制限がない。
        DoS防御の観点から、上流（router.py の Pydantic モデル等）または
        ChatMessage 自体でサイズ上限バリデーションを追加すべき。

        検証対象: ValueError のメッセージに "size" または "サイズ" を含むこと。
        これにより、サイズ制限以外の想定外例外で誤って合格するのを防ぐ。
        """
        # Arrange
        from app.chat_dashboard.simple_chat_handler import ChatMessage
        large_content = "A" * (1024 * 1024 + 1)  # 1MB + 1バイト

        # Act & Assert — サイズ制限に起因する ValueError が発生すべき
        with pytest.raises(ValueError, match=r"(?i)size|サイズ|too large|上限"):
            msg = ChatMessage(role="user", content=large_content, timestamp=datetime.now())
            msg.to_langchain_message()
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_simple_chatbot_module` | テスト間のシングルトン状態リセット | function | Yes |
| `mock_llm_factory` | LLMファクトリーのモック（外部API呼び出し防止） | function | No |
| `mock_chat_tools` | チャットツールのモック | function | No |
| `reset_cache` | Basic認証キャッシュリセット | function | Yes（一部クラス） |

### 共通フィクスチャ定義

```python
# test/unit/chat_dashboard/conftest.py に追加（既存フィクスチャと併用）
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# テスト用定数（config.pyバリデーション通過に必要な最小環境変数セット）
REQUIRED_ENV_VARS = {
    "GPT5_1_CHAT_API_KEY": "test-key",
    "GPT5_1_CODEX_API_KEY": "test-key",
    "GPT5_2_API_KEY": "test-key",
    "GPT5_MINI_API_KEY": "test-key",
    "GPT5_NANO_API_KEY": "test-key",
    "CLAUDE_HAIKU_4_5_KEY": "test-key",
    "CLAUDE_SONNET_4_5_KEY": "test-key",
    "GEMINI_API": "test-key",
    "DOCKER_BASE_URL": "http://localhost:11434",
    "EMBEDDING_3_LARGE_API_KEY": "test-embedding-key",
    "OPENSEARCH_URL": "https://localhost:9200",
}


@pytest.fixture(autouse=True)
def reset_simple_chatbot_module():
    """テストごとにシングルトン状態をリセット

    simple_chat_handler.py の _simple_chatbot グローバル変数と
    basic_auth_logic.py の _basic_client_cache をリセットする。
    setup（yield前）とteardown（yield後）の両方でリセットし、
    テスト間の状態汚染を防止する。
    """
    # setup: 前のテストの状態を確実にクリア
    try:
        import app.chat_dashboard.simple_chat_handler as handler
        handler._simple_chatbot = None
    except (ImportError, AttributeError):
        pass
    try:
        import app.chat_dashboard.basic_auth_logic as auth_module
        auth_module._basic_client_cache.clear()
    except (ImportError, AttributeError):
        pass

    yield
    # teardown: テスト後にクリーンアップ
    try:
        import app.chat_dashboard.simple_chat_handler as handler
        handler._simple_chatbot = None
    except (ImportError, AttributeError):
        pass
    try:
        import app.chat_dashboard.basic_auth_logic as auth_module
        auth_module._basic_client_cache.clear()
    except (ImportError, AttributeError):
        pass


@pytest.fixture
def mock_llm_factory():
    """LLMファクトリーモック（外部API呼び出し防止）

    注意: SimpleChatBot._initialize_components() は動的ローカルインポート
    （from ..core.llm_factory import get_chat_llm）を使用するため、
    パッチ先はソースモジュール（app.core.llm_factory）を指定する。
    動的ローカルインポートは毎回 sys.modules からモジュールを参照し、
    そこから名前を解決するため、ソースモジュールへのパッチが有効。
    """
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = mock_llm

    with patch("app.core.llm_factory.get_chat_llm", return_value=mock_llm) as mock_factory:
        yield mock_factory, mock_llm


@pytest.fixture
def mock_chat_tools():
    """チャットツールモック（外部依存防止）

    注意: _initialize_components() 内の動的ローカルインポート
    （from .chat_tools import ...）に対応するため、
    パッチ先はソースモジュール（app.chat_dashboard.chat_tools）を指定する。
    """
    with patch("app.chat_dashboard.chat_tools.compare_scan_violations") as mock_compare, \
         patch("app.chat_dashboard.chat_tools.get_scan_info") as mock_scan, \
         patch("app.chat_dashboard.chat_tools.get_resource_details") as mock_resource, \
         patch("app.chat_dashboard.chat_tools.get_policy_recommendations") as mock_policy:
        yield {
            "compare_scan_violations": mock_compare,
            "get_scan_info": mock_scan,
            "get_resource_details": mock_resource,
            "get_policy_recommendations": mock_policy,
        }
```

---

## 6. テスト実行例

```bash
# 補足テストのみ実行
pytest test/unit/chat_dashboard/test_chat_dashboard_supplement.py -v

# 特定のテストクラスのみ実行
pytest test/unit/chat_dashboard/test_chat_dashboard_supplement.py::TestChatMessageConversion -v

# カバレッジ付きで実行（既存テスト + 補足テスト）
pytest test/unit/chat_dashboard/ --cov=app.chat_dashboard --cov-report=term-missing -v

# セキュリティマーカーで実行
# pyproject.toml: markers = ["security: セキュリティ関連テスト"]
pytest test/unit/chat_dashboard/test_chat_dashboard_supplement.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 18 | CHAT-S001 〜 CHAT-S018 |
| 異常系 | 4 | CHAT-SE01 〜 CHAT-SE04 |
| セキュリティ | 2 | CHAT-SSEC-01 〜 CHAT-SSEC-02 |
| **合計** | **24** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestChatMessageConversion` | CHAT-S001〜S002 | 2 |
| `TestSystemPrompt` | CHAT-S003〜S004 | 2 |
| `TestSessionManagement` | CHAT-S005〜S010 | 6 |
| `TestClearBasicClientCache` | CHAT-S011〜S012 | 2 |
| `TestDecodeBasicAuthEdgeCases` | CHAT-S013 | 1 |
| `TestCreateOpensearchClientBranches` | CHAT-S014〜S018 | 5 |
| `TestChatMessageErrors` | CHAT-SE01 | 1 |
| `TestSessionManagementErrors` | CHAT-SE02 | 1 |
| `TestDecodeBasicAuthErrors` | CHAT-SE03〜SE04 | 2 |
| `TestCacheSecuritySupplement` | CHAT-SSEC-01 | 1 |
| `TestInputSizeSupplement` | CHAT-SSEC-02 | 1 |

### 実装失敗が予想されるテスト

以下のテストは現在の実装では**意図的に失敗**します。実装側の修正が必要です。

| テストID | 失敗理由 | 修正方針 |
|---------|---------|---------|
| CHAT-SSEC-02 | `ChatMessage.content` にサイズ制限が未実装（`simple_chat_handler.py:64-68`） | `CSPMDashboardChatRequest.prompt` に `Field(max_length=...)` を追加、または `ChatMessage` でバリデーション |

### 注意事項

- `pytest-asyncio` が必要（`CHAT-S009`, `CHAT-S010`, `CHAT-SE02` で使用）
- `@pytest.mark.security` マーカーの登録が必要（`pyproject.toml` に `markers = ["security: セキュリティ関連テスト"]`）
- `mock_llm_factory` / `mock_chat_tools` フィクスチャは `SimpleChatBot.__init__` 内の `import` 文をモック化するため、テストファイル内で遅延インポートを使用
- 既存 `conftest.py` にフィクスチャが定義済みの場合は、名前衝突に注意して統合すること

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `SimpleChatBot._initialize_components` 内で動的インポートを行うため、モック適用タイミングに注意が必要 | フィクスチャの適用順序によってはモック漏れが発生する可能性 | `mock_llm_factory` と `mock_chat_tools` を同時に使用する |
| 2 | `get_simple_chatbot()` のシングルトンパターンによりテスト間で状態が共有される | テスト間の依存関係が生じる可能性 | `reset_simple_chatbot_module` autouse フィクスチャで毎回リセット |
| 3 | `create_opensearch_client_with_basic_auth` のキャッシュがモジュールレベル変数 | テスト間でキャッシュが残る可能性 | `reset_cache` フィクスチャでテストごとにクリア |
| 4 | `decode_basic_auth` の空文字列テスト（CHAT-SE04）は `b""` → `""` → コロンなし → ValueError の経路で HTTPException(401) になる | 例外経路は一意だが、detail に内部例外メッセージが含まれる（CHAT-E13 で既知） | HTTPException(401) の発生のみを検証し、内部例外種別は検証しない |
| 5 | `ChatMessage` は `@dataclass` のため `role` フィールドに型制約がない | 将来 Pydantic モデルに変更された場合、CHAT-SE01 のインスタンス化が失敗する可能性 | `@dataclass` のままならテスト変更不要。Pydantic 化時はバリデーションのタイミングを再確認 |
| 6 | CHAT-S014〜S017 は `OpenSearch` クラスをモック化するため、実際の TLS 接続検証はできない | モックレベルでは `verify_certs=True` の設定値のみ検証 | 統合テストで実際の TLS ハンドシェイクを検証すべき |
| 7 | `_basic_client_cache` のキーが `username:password` の平文文字列 | キャッシュ存在中にメモリダンプや例外トレースでキーが露出するリスク | CHAT-SEC-14（既存仕様書）でカバー済み。本仕様書スコープ外 |
