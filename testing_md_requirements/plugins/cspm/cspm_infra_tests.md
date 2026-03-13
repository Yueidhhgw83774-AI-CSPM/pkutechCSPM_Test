# cspm_plugin 基盤コンポーネント テストケース

## 1. 概要

CSPMプラグインの基盤コンポーネント（`llm_manager.py`、`internal_tools.py`）のテストケースを定義します。
LLMインスタンスの初期化・キャッシュ管理と、CSPMツールのMCPクライアントへの内部登録機能を検証します。

> **注記**: cspm_plugin は大規模プラグイン（22ファイル・4,237行）のため、テスト仕様書を機能別に分割しています。
> - [cspm_plugin_tests.md](./cspm_plugin_tests.md): router.py（メインAPIエンドポイント）
> - [cspm_tools_router_tests.md](./cspm_tools_router_tests.md): tools_router.py（MCPツールエンドポイント）
> - [cspm_tools_tests.md](./cspm_tools_tests.md): tools.py（ツール関数）
> - [cspm_utils_tests.md](./cspm_utils_tests.md): ユーティリティ（policy_utils / resource_identification / yaml_converter）
> - **本ファイル**: 基盤コンポーネント（llm_manager / internal_tools）
> - [cspm_nodes_tests.md](./cspm_nodes_tests.md): ノード群（policy_generation / validation / review）

### 1.1 主要機能

| 機能 | ファイル | 説明 |
|------|---------|------|
| `initialize_policy_llm()` | `llm_manager.py` | ポリシー生成/修正用LLMの初期化・キャッシュ |
| `initialize_enhanced_llm()` | `llm_manager.py` | 強化版（軽量）LLMの初期化・キャッシュ |
| `initialize_review_llm()` | `llm_manager.py` | レビュー用LLM（gpt-5.1-codex）の初期化・キャッシュ |
| `_ensure_tools_loaded()` | `internal_tools.py` | CSPMツールの遅延ロード |
| `handle_validate_policy()` | `internal_tools.py` | ポリシー検証ハンドラー |
| `handle_get_schema()` | `internal_tools.py` | スキーマ取得ハンドラー |
| `handle_list_resources()` | `internal_tools.py` | リソース一覧取得ハンドラー |
| `handle_retrieve_reference()` | `internal_tools.py` | RAG検索ハンドラー（非同期） |
| `register_cspm_internal_tools()` | `internal_tools.py` | MCPクライアントへの内部ツール登録（非同期） |

### 1.2 カバレッジ目標: 90%

> **注記**: llm_manager.py はグローバルキャッシュ変数を使用するため、テスト間の状態リセットが重要。
> internal_tools.py は遅延ロードパターンと外部依存（MCPクライアント）のモックが必要。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象1 | `app/cspm_plugin/llm_manager.py` |
| テスト対象2 | `app/cspm_plugin/internal_tools.py` |
| 依存（LLMファクトリー） | `app/core/llm_factory.py` |
| 依存（MCPクライアント） | `app/mcp_plugin/client.py` |
| 依存（MCPモデル） | `app/models/mcp.py` |
| テストコード | `test/unit/cspm_plugin/test_infra.py` |

### 1.4 補足情報

**llm_manager.py のグローバル変数:**

| 変数名 | 型 | 説明 |
|--------|-----|------|
| `CACHED_POLICY_LLM` | `Optional[ChatOpenAI]` | ポリシー生成用LLMキャッシュ |
| `CACHED_ENHANCED_LLM` | `Optional[ChatOpenAI]` | 強化版LLMキャッシュ |
| `CACHED_REVIEW_LLM` | `Optional[ChatOpenAI]` | レビュー用LLMキャッシュ |

**llm_manager.py の主要分岐:**

| 関数 | 行番号 | 分岐条件 |
|------|--------|---------|
| `initialize_policy_llm` | L31 | キャッシュ済みかチェック |
| `initialize_policy_llm` | L41-44 | ファクトリー例外時 → None |
| `initialize_enhanced_llm` | L55 | キャッシュ済みかチェック |
| `initialize_enhanced_llm` | L65-68 | ファクトリー例外時 → None |
| `initialize_review_llm` | L80 | キャッシュ済みかチェック |
| `initialize_review_llm` | L90-93 | ファクトリー例外時 → None |

**internal_tools.py の主要分岐:**

| 関数 | 行番号 | 分岐条件 |
|------|--------|---------|
| `_ensure_tools_loaded` | L29 | 既にロード済みかチェック |
| `_ensure_tools_loaded` | L45-47 | ImportError 時 → False |
| `handle_validate_policy` | L53 | ツールロード確認 |
| `handle_get_schema` | L62 | ツールロード確認 |
| `handle_list_resources` | L71 | ツールロード確認 |
| `handle_retrieve_reference` | L80 | ツールロード確認 |
| `register_cspm_internal_tools` | L230 | ツールロード可能か確認 |
| `register_cspm_internal_tools` | L241-244 | 登録成功/失敗の分岐 |
| `register_cspm_internal_tools` | L248-250 | 例外発生時 → False |

**internal_tools.py の定数データ:**

| 定数名 | 説明 |
|--------|------|
| `CSPM_INTERNAL_TOOLS` | MCPToolリスト（4ツール定義） |
| `CSPM_TOOL_HANDLERS` | ツール名→ハンドラー関数マッピング |
| `CSPM_INTERNAL_SERVER_NAME` | 内部サーバー名 "cspm-internal" |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CSPM-IF-001 | ポリシーLLM初期化成功 | ファクトリー正常 | ChatOpenAIインスタンス返却 |
| CSPM-IF-002 | ポリシーLLMキャッシュ返却 | 2回目の呼び出し | 同一インスタンス返却 |
| CSPM-IF-003 | 強化版LLM初期化成功 | ファクトリー正常 | ChatOpenAIインスタンス返却 |
| CSPM-IF-004 | 強化版LLMキャッシュ返却 | 2回目の呼び出し | 同一インスタンス返却 |
| CSPM-IF-005 | レビューLLM初期化成功 | ファクトリー正常 | ChatOpenAIインスタンス返却 |
| CSPM-IF-006 | レビューLLMキャッシュ返却 | 2回目の呼び出し | 同一インスタンス返却 |
| CSPM-IF-007 | ツール遅延ロード成功 | tools.pyインポート成功 | True |
| CSPM-IF-008 | ツール遅延ロード（キャッシュ） | 2回目呼び出し | True（再インポートなし） |
| CSPM-IF-009 | ポリシー検証ハンドラー正常実行 | 有効なpolicy_content | 検証結果文字列 |
| CSPM-IF-010 | スキーマ取得ハンドラー正常実行 | target="aws.s3" | スキーマ文字列 |
| CSPM-IF-011 | リソース一覧ハンドラー正常実行 | cloud="aws" | リソースリスト文字列 |
| CSPM-IF-012 | RAG検索ハンドラー正常実行 | query + cloud | 検索結果文字列 |
| CSPM-IF-013 | 内部ツール登録成功 | 全条件正常 | True |
| CSPM-IF-014 | CSPM_INTERNAL_TOOLSの定義数 | 定数参照 | 4ツール定義 |
| CSPM-IF-015 | CSPM_TOOL_HANDLERSのマッピング数 | 定数参照 | 4ハンドラー |

### 2.1 LLM初期化・キャッシュテスト

```python
# test/unit/cspm_plugin/test_infra.py
import pytest
import sys
from unittest.mock import patch, MagicMock, AsyncMock


class TestInitializePolicyLlm:
    """ポリシー生成用LLMの初期化・キャッシュテスト"""

    @pytest.fixture(autouse=True)
    def reset_llm_cache(self):
        """テストごとにLLMキャッシュをリセット"""
        import app.cspm_plugin.llm_manager as lm
        lm.CACHED_POLICY_LLM = None
        lm.CACHED_ENHANCED_LLM = None
        lm.CACHED_REVIEW_LLM = None
        yield
        lm.CACHED_POLICY_LLM = None
        lm.CACHED_ENHANCED_LLM = None
        lm.CACHED_REVIEW_LLM = None

    @patch("app.cspm_plugin.llm_manager.get_policy_llm")
    def test_initialize_policy_llm_success(self, mock_factory):
        """CSPM-IF-001: ポリシーLLMが正常に初期化されること"""
        # Arrange
        mock_llm = MagicMock()
        mock_factory.return_value = mock_llm

        # Act
        from app.cspm_plugin.llm_manager import initialize_policy_llm
        result = initialize_policy_llm()

        # Assert
        assert result is mock_llm
        mock_factory.assert_called_once()

    @patch("app.cspm_plugin.llm_manager.get_policy_llm")
    def test_policy_llm_cached(self, mock_factory):
        """CSPM-IF-002: 2回目の呼び出しでキャッシュが返されること

        llm_manager.py:31 のキャッシュ分岐をカバーする。
        """
        # Arrange
        mock_llm = MagicMock()
        mock_factory.return_value = mock_llm

        # Act
        from app.cspm_plugin.llm_manager import initialize_policy_llm
        result1 = initialize_policy_llm()
        result2 = initialize_policy_llm()

        # Assert
        assert result1 is result2
        mock_factory.assert_called_once()  # 1回しか呼ばれない


class TestInitializeEnhancedLlm:
    """強化版LLMの初期化・キャッシュテスト"""

    @pytest.fixture(autouse=True)
    def reset_llm_cache(self):
        """テストごとにLLMキャッシュをリセット"""
        import app.cspm_plugin.llm_manager as lm
        lm.CACHED_ENHANCED_LLM = None
        yield
        lm.CACHED_ENHANCED_LLM = None

    @patch("app.cspm_plugin.llm_manager.get_chat_llm")
    def test_initialize_enhanced_llm_success(self, mock_factory):
        """CSPM-IF-003: 強化版LLMが正常に初期化されること"""
        # Arrange
        mock_llm = MagicMock()
        mock_factory.return_value = mock_llm

        # Act
        from app.cspm_plugin.llm_manager import initialize_enhanced_llm
        result = initialize_enhanced_llm()

        # Assert
        assert result is mock_llm
        mock_factory.assert_called_once()

    @patch("app.cspm_plugin.llm_manager.get_chat_llm")
    def test_enhanced_llm_cached(self, mock_factory):
        """CSPM-IF-004: 強化版LLMの2回目呼び出しでキャッシュが返されること

        llm_manager.py:55 のキャッシュ分岐をカバーする。
        """
        # Arrange
        mock_llm = MagicMock()
        mock_factory.return_value = mock_llm

        # Act
        from app.cspm_plugin.llm_manager import initialize_enhanced_llm
        result1 = initialize_enhanced_llm()
        result2 = initialize_enhanced_llm()

        # Assert
        assert result1 is result2
        mock_factory.assert_called_once()


class TestInitializeReviewLlm:
    """レビュー用LLMの初期化・キャッシュテスト"""

    @pytest.fixture(autouse=True)
    def reset_llm_cache(self):
        """テストごとにLLMキャッシュをリセット"""
        import app.cspm_plugin.llm_manager as lm
        lm.CACHED_REVIEW_LLM = None
        yield
        lm.CACHED_REVIEW_LLM = None

    @patch("app.cspm_plugin.llm_manager.get_review_llm")
    def test_initialize_review_llm_success(self, mock_factory):
        """CSPM-IF-005: レビューLLMが正常に初期化されること"""
        # Arrange
        mock_llm = MagicMock()
        mock_factory.return_value = mock_llm

        # Act
        from app.cspm_plugin.llm_manager import initialize_review_llm
        result = initialize_review_llm()

        # Assert
        assert result is mock_llm
        mock_factory.assert_called_once()

    @patch("app.cspm_plugin.llm_manager.get_review_llm")
    def test_review_llm_cached(self, mock_factory):
        """CSPM-IF-006: レビューLLMの2回目呼び出しでキャッシュが返されること

        llm_manager.py:80 のキャッシュ分岐をカバーする。
        """
        # Arrange
        mock_llm = MagicMock()
        mock_factory.return_value = mock_llm

        # Act
        from app.cspm_plugin.llm_manager import initialize_review_llm
        result1 = initialize_review_llm()
        result2 = initialize_review_llm()

        # Assert
        assert result1 is result2
        mock_factory.assert_called_once()
```

### 2.2 ツール遅延ロードテスト

```python
class TestEnsureToolsLoaded:
    """CSPMツールの遅延ロードテスト"""

    @pytest.fixture(autouse=True)
    def reset_tools_state(self):
        """テストごとにツールロード状態をリセット"""
        import app.cspm_plugin.internal_tools as it
        it._tools_loaded = False
        it._validate_policy = None
        it._get_custodian_schema = None
        it._list_available_resources = None
        it._retrieve_reference = None
        yield
        it._tools_loaded = False
        it._validate_policy = None
        it._get_custodian_schema = None
        it._list_available_resources = None
        it._retrieve_reference = None

    def test_ensure_tools_loaded_success(self):
        """CSPM-IF-007: ツールが正常にロードされること

        internal_tools.py の from .tools import ... は相対インポートのため、
        sys.modules にモックモジュールを差し込んで成功パスを再現する。
        types.ModuleType を使用して明示属性のみを持つモジュールモックとし、
        シンボル名の typo を検出可能にする（MagicMock は存在しない属性も
        自動生成してしまうため不適切）。
        """
        # Arrange
        import types
        import app.cspm_plugin.internal_tools as it
        it._tools_loaded = False
        mock_validate = MagicMock()
        mock_schema = MagicMock()
        mock_list = MagicMock()
        mock_retrieve = MagicMock()
        # types.ModuleType で明示属性のみを持つモジュールを作成
        mock_tools_module = types.ModuleType("app.cspm_plugin.tools")
        mock_tools_module.validate_policy = mock_validate
        mock_tools_module.get_custodian_schema = mock_schema
        mock_tools_module.list_available_resources = mock_list
        mock_tools_module.retrieve_reference = mock_retrieve

        # Act
        with patch.dict("sys.modules", {"app.cspm_plugin.tools": mock_tools_module}):
            result = it._ensure_tools_loaded()

        # Assert - ロード成功かつ関数参照が正しく束縛されていること
        assert result is True
        assert it._tools_loaded is True
        assert it._validate_policy is mock_validate
        assert it._get_custodian_schema is mock_schema
        assert it._list_available_resources is mock_list
        assert it._retrieve_reference is mock_retrieve

    def test_ensure_tools_loaded_cached(self):
        """CSPM-IF-008: ロード済みの場合、再インポートなしでTrueを返すこと

        internal_tools.py:29-30 の分岐をカバーする。
        既存の関数参照が維持され、再インポートが行われないことを
        関数参照の同一性で検証する。
        """
        # Arrange
        import app.cspm_plugin.internal_tools as it
        it._tools_loaded = True
        sentinel_validate = MagicMock(name="sentinel_validate")
        sentinel_schema = MagicMock(name="sentinel_schema")
        sentinel_list = MagicMock(name="sentinel_list")
        sentinel_retrieve = MagicMock(name="sentinel_retrieve")
        it._validate_policy = sentinel_validate
        it._get_custodian_schema = sentinel_schema
        it._list_available_resources = sentinel_list
        it._retrieve_reference = sentinel_retrieve

        # Act
        result = it._ensure_tools_loaded()

        # Assert - 再インポートされず、既存の関数参照が変更されていないこと
        assert result is True
        assert it._validate_policy is sentinel_validate
        assert it._get_custodian_schema is sentinel_schema
        assert it._list_available_resources is sentinel_list
        assert it._retrieve_reference is sentinel_retrieve
```

### 2.3 ハンドラー正常系テスト

```python
class TestToolHandlers:
    """CSPMツールハンドラーの正常系テスト"""

    @pytest.fixture(autouse=True)
    def setup_tools(self):
        """ツールのロード状態をセットアップ"""
        import app.cspm_plugin.internal_tools as it
        self.mock_validate = MagicMock(return_value="Validation successful.")
        self.mock_schema = MagicMock(return_value='{"type": "object"}')
        self.mock_list = MagicMock(return_value="resources:\n- aws.s3")
        self.mock_retrieve = AsyncMock(return_value="Reference data")

        it._tools_loaded = True
        it._validate_policy = MagicMock()
        it._validate_policy.invoke = self.mock_validate
        it._get_custodian_schema = MagicMock()
        it._get_custodian_schema.invoke = self.mock_schema
        it._list_available_resources = MagicMock()
        it._list_available_resources.invoke = self.mock_list
        it._retrieve_reference = MagicMock()
        it._retrieve_reference.ainvoke = self.mock_retrieve
        yield
        it._tools_loaded = False
        it._validate_policy = None
        it._get_custodian_schema = None
        it._list_available_resources = None
        it._retrieve_reference = None

    def test_handle_validate_policy(self):
        """CSPM-IF-009: ポリシー検証ハンドラーが正常に実行されること"""
        # Arrange
        params = {"policy_content": "name: test\nresource: aws.s3"}

        # Act
        from app.cspm_plugin.internal_tools import handle_validate_policy
        result = handle_validate_policy(params)

        # Assert
        assert result == "Validation successful."
        self.mock_validate.assert_called_once_with(
            {"policy_content": "name: test\nresource: aws.s3"}
        )

    def test_handle_get_schema(self):
        """CSPM-IF-010: スキーマ取得ハンドラーが正常に実行されること"""
        # Arrange
        params = {"target": "aws.s3"}

        # Act
        from app.cspm_plugin.internal_tools import handle_get_schema
        result = handle_get_schema(params)

        # Assert
        assert result == '{"type": "object"}'
        self.mock_schema.assert_called_once_with({"target": "aws.s3"})

    def test_handle_list_resources(self):
        """CSPM-IF-011: リソース一覧ハンドラーが正常に実行されること"""
        # Arrange
        params = {"cloud": "aws"}

        # Act
        from app.cspm_plugin.internal_tools import handle_list_resources
        result = handle_list_resources(params)

        # Assert
        assert "aws.s3" in result
        self.mock_list.assert_called_once_with({"cloud": "aws"})

    @pytest.mark.asyncio
    async def test_handle_retrieve_reference(self):
        """CSPM-IF-012: RAG検索ハンドラーが正常に実行されること（非同期）"""
        # Arrange
        params = {"query": "aws s3 encryption", "cloud": "aws"}

        # Act
        from app.cspm_plugin.internal_tools import handle_retrieve_reference
        result = await handle_retrieve_reference(params)

        # Assert
        assert result == "Reference data"
        self.mock_retrieve.assert_called_once_with(
            {"query": "aws s3 encryption", "cloud": "aws"}
        )
```

### 2.4 内部ツール登録テスト

```python
class TestRegisterCspmInternalTools:
    """MCPクライアントへの内部ツール登録テスト"""

    @pytest.fixture(autouse=True)
    def reset_tools_state(self):
        """テストごとにツールロード状態をリセット"""
        import app.cspm_plugin.internal_tools as it
        it._tools_loaded = False
        yield
        it._tools_loaded = False

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.internal_tools.mcp_client")
    @patch("app.cspm_plugin.internal_tools._ensure_tools_loaded", return_value=True)
    async def test_register_success(self, mock_ensure, mock_mcp):
        """CSPM-IF-013: 内部ツール登録が成功すること"""
        # Arrange
        mock_mcp.register_internal_tools = AsyncMock(return_value=True)

        # Act
        from app.cspm_plugin.internal_tools import register_cspm_internal_tools
        result = await register_cspm_internal_tools()

        # Assert
        assert result is True
        mock_mcp.register_internal_tools.assert_called_once()
        # 正しい引数（server_name, tools, tool_handlers）が渡されていること
        call_kwargs = mock_mcp.register_internal_tools.call_args
        assert call_kwargs.kwargs["server_name"] == "cspm-internal"
        assert len(call_kwargs.kwargs["tools"]) == 4
        assert len(call_kwargs.kwargs["tool_handlers"]) == 4
```

### 2.5 定数データ検証テスト

```python
class TestInternalToolsConstants:
    """内部ツール定数の検証テスト"""

    def test_cspm_internal_tools_count(self):
        """CSPM-IF-014: CSPM_INTERNAL_TOOLSに4ツールが定義されていること"""
        # Act
        from app.cspm_plugin.internal_tools import CSPM_INTERNAL_TOOLS

        # Assert
        assert len(CSPM_INTERNAL_TOOLS) == 4
        tool_names = [t.name for t in CSPM_INTERNAL_TOOLS]
        assert "cspm_validate_policy" in tool_names
        assert "cspm_get_schema" in tool_names
        assert "cspm_list_resources" in tool_names
        assert "cspm_retrieve_reference" in tool_names

    def test_cspm_tool_handlers_count(self):
        """CSPM-IF-015: CSPM_TOOL_HANDLERSに4ハンドラーがマッピングされていること"""
        # Act
        from app.cspm_plugin.internal_tools import CSPM_TOOL_HANDLERS

        # Assert
        assert len(CSPM_TOOL_HANDLERS) == 4
        assert "cspm_validate_policy" in CSPM_TOOL_HANDLERS
        assert "cspm_get_schema" in CSPM_TOOL_HANDLERS
        assert "cspm_list_resources" in CSPM_TOOL_HANDLERS
        assert "cspm_retrieve_reference" in CSPM_TOOL_HANDLERS
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CSPM-IF-E01 | ポリシーLLMファクトリー例外 | get_policy_llm() が例外 | None 返却 |
| CSPM-IF-E02 | 強化版LLMファクトリー例外 | get_chat_llm() が例外 | None 返却 |
| CSPM-IF-E03 | レビューLLMファクトリー例外 | get_review_llm() が例外 | None 返却 |
| CSPM-IF-E04 | ツールインポート失敗 | tools.py インポートエラー | False 返却 |
| CSPM-IF-E05 | ハンドラー: ツール未ロード（検証） | _tools_loaded=False, インポート失敗 | "Error: CSPMツールが利用できません" |
| CSPM-IF-E06 | ハンドラー: ツール未ロード（スキーマ） | _tools_loaded=False, インポート失敗 | "Error: CSPMツールが利用できません" |
| CSPM-IF-E07 | ハンドラー: ツール未ロード（リソース） | _tools_loaded=False, インポート失敗 | "Error: CSPMツールが利用できません" |
| CSPM-IF-E08 | ハンドラー: ツール未ロード（RAG） | _tools_loaded=False, インポート失敗 | "Error: CSPMツールが利用できません" |
| CSPM-IF-E09 | 内部ツール登録: ロード失敗 | _ensure_tools_loaded → False | False 返却 |
| CSPM-IF-E10 | 内部ツール登録: MCP登録失敗 | register_internal_tools → False | False 返却 |
| CSPM-IF-E11 | 内部ツール登録: 例外発生 | register_internal_tools で例外 | False 返却 |
| CSPM-IF-E12 | リソースハンドラー: cloudパラメータ未指定 | params={} | デフォルト "aws" で実行 |
| CSPM-IF-E13 | RAGハンドラー: cloudパラメータ未指定 | params={"query": "test"} | デフォルト "aws" で実行 |
| CSPM-IF-E14 | スキーマハンドラー: targetパラメータ未指定 | params={} | target=None で実行 |
| CSPM-IF-E15 | 検証ハンドラー: policy_contentパラメータ未指定 | params={} | 空文字列で実行 |

### 3.1 LLM初期化 異常系

```python
class TestLlmManagerErrors:
    """LLM初期化のエラーテスト"""

    @pytest.fixture(autouse=True)
    def reset_llm_cache(self):
        """テストごとにLLMキャッシュをリセット"""
        import app.cspm_plugin.llm_manager as lm
        lm.CACHED_POLICY_LLM = None
        lm.CACHED_ENHANCED_LLM = None
        lm.CACHED_REVIEW_LLM = None
        yield
        lm.CACHED_POLICY_LLM = None
        lm.CACHED_ENHANCED_LLM = None
        lm.CACHED_REVIEW_LLM = None

    @patch("app.cspm_plugin.llm_manager.get_policy_llm", side_effect=RuntimeError("Config error"))
    def test_policy_llm_factory_exception(self, mock_factory):
        """CSPM-IF-E01: ファクトリー例外時にNoneが返されること

        llm_manager.py:41-44 の例外処理をカバーする。
        """
        # Act
        from app.cspm_plugin.llm_manager import initialize_policy_llm
        result = initialize_policy_llm()

        # Assert
        assert result is None

    @patch("app.cspm_plugin.llm_manager.get_chat_llm", side_effect=RuntimeError("Config error"))
    def test_enhanced_llm_factory_exception(self, mock_factory):
        """CSPM-IF-E02: 強化版LLMファクトリー例外時にNoneが返されること

        llm_manager.py:65-68 の例外処理をカバーする。
        """
        # Act
        from app.cspm_plugin.llm_manager import initialize_enhanced_llm
        result = initialize_enhanced_llm()

        # Assert
        assert result is None

    @patch("app.cspm_plugin.llm_manager.get_review_llm", side_effect=RuntimeError("Config error"))
    def test_review_llm_factory_exception(self, mock_factory):
        """CSPM-IF-E03: レビューLLMファクトリー例外時にNoneが返されること

        llm_manager.py:90-93 の例外処理をカバーする。
        """
        # Act
        from app.cspm_plugin.llm_manager import initialize_review_llm
        result = initialize_review_llm()

        # Assert
        assert result is None
```

### 3.2 ツールロード・ハンドラー 異常系

```python
class TestEnsureToolsLoadedErrors:
    """ツール遅延ロードのエラーテスト"""

    @pytest.fixture(autouse=True)
    def reset_tools_state(self):
        """テストごとにツールロード状態をリセット"""
        import app.cspm_plugin.internal_tools as it
        it._tools_loaded = False
        it._validate_policy = None
        it._get_custodian_schema = None
        it._list_available_resources = None
        it._retrieve_reference = None
        yield
        it._tools_loaded = False
        it._validate_policy = None
        it._get_custodian_schema = None
        it._list_available_resources = None
        it._retrieve_reference = None

    def test_import_error(self):
        """CSPM-IF-E04: ツールインポート失敗時にFalseが返されること

        internal_tools.py:45-47 の ImportError 分岐をカバーする。
        builtins.__import__ のパッチはpytest内部に干渉するため、
        sys.modules を操作してインポートエラーを再現する。
        """
        # Arrange
        import app.cspm_plugin.internal_tools as it
        it._tools_loaded = False

        # Act - tools モジュールを None に設定してインポートエラーを発生させる
        with patch.dict("sys.modules", {"app.cspm_plugin.tools": None}):
            result = it._ensure_tools_loaded()

        # Assert
        assert result is False


class TestToolHandlersErrors:
    """ツールハンドラーのエラーテスト"""

    @pytest.fixture(autouse=True)
    def setup_tools_unavailable(self):
        """ツールがロードできない状態をセットアップ"""
        import app.cspm_plugin.internal_tools as it
        it._tools_loaded = False
        yield
        it._tools_loaded = False

    @patch("app.cspm_plugin.internal_tools._ensure_tools_loaded", return_value=False)
    def test_handle_validate_policy_tools_unavailable(self, mock_ensure):
        """CSPM-IF-E05: ツール未ロード時にエラーメッセージが返されること（検証）

        internal_tools.py:53-54 の分岐をカバーする。
        """
        # Act
        from app.cspm_plugin.internal_tools import handle_validate_policy
        result = handle_validate_policy({"policy_content": "test"})

        # Assert
        assert result == "Error: CSPMツールが利用できません"

    @patch("app.cspm_plugin.internal_tools._ensure_tools_loaded", return_value=False)
    def test_handle_get_schema_tools_unavailable(self, mock_ensure):
        """CSPM-IF-E06: ツール未ロード時にエラーメッセージが返されること（スキーマ）

        internal_tools.py:62-63 の分岐をカバーする。
        """
        # Act
        from app.cspm_plugin.internal_tools import handle_get_schema
        result = handle_get_schema({"target": "aws"})

        # Assert
        assert result == "Error: CSPMツールが利用できません"

    @patch("app.cspm_plugin.internal_tools._ensure_tools_loaded", return_value=False)
    def test_handle_list_resources_tools_unavailable(self, mock_ensure):
        """CSPM-IF-E07: ツール未ロード時にエラーメッセージが返されること（リソース）

        internal_tools.py:71-72 の分岐をカバーする。
        """
        # Act
        from app.cspm_plugin.internal_tools import handle_list_resources
        result = handle_list_resources({"cloud": "aws"})

        # Assert
        assert result == "Error: CSPMツールが利用できません"

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.internal_tools._ensure_tools_loaded", return_value=False)
    async def test_handle_retrieve_reference_tools_unavailable(self, mock_ensure):
        """CSPM-IF-E08: ツール未ロード時にエラーメッセージが返されること（RAG）

        internal_tools.py:80-81 の分岐をカバーする。
        """
        # Act
        from app.cspm_plugin.internal_tools import handle_retrieve_reference
        result = await handle_retrieve_reference({"query": "test"})

        # Assert
        assert result == "Error: CSPMツールが利用できません"

    def test_handle_list_resources_default_cloud(self):
        """CSPM-IF-E12: cloudパラメータ未指定時にデフォルト"aws"が使用されること

        internal_tools.py:74 の params.get("cloud", "aws") をカバーする。
        """
        # Arrange
        import app.cspm_plugin.internal_tools as it
        it._tools_loaded = True
        mock_tool = MagicMock()
        mock_tool.invoke = MagicMock(return_value="resources:\n- aws.s3")
        it._list_available_resources = mock_tool

        # Act
        result = it.handle_list_resources({})

        # Assert
        mock_tool.invoke.assert_called_once_with({"cloud": "aws"})

        # Cleanup
        it._tools_loaded = False
        it._list_available_resources = None

    @pytest.mark.asyncio
    async def test_handle_retrieve_reference_default_cloud(self):
        """CSPM-IF-E13: RAGハンドラーでcloudパラメータ未指定時にデフォルト"aws"が使用されること

        internal_tools.py:84 の params.get("cloud", "aws") をカバーする。
        """
        # Arrange
        import app.cspm_plugin.internal_tools as it
        it._tools_loaded = True
        mock_tool = MagicMock()
        mock_tool.ainvoke = AsyncMock(return_value="Reference data")
        it._retrieve_reference = mock_tool

        # Act
        result = await it.handle_retrieve_reference({"query": "test"})

        # Assert
        mock_tool.ainvoke.assert_called_once_with({"query": "test", "cloud": "aws"})

        # Cleanup
        it._tools_loaded = False
        it._retrieve_reference = None

    def test_handle_get_schema_no_target(self):
        """CSPM-IF-E14: スキーマハンドラーでtargetパラメータ未指定時にNoneが渡されること

        internal_tools.py:65 の params.get("target") をカバーする。
        target 未指定時は None が _get_custodian_schema.invoke に渡される。
        """
        # Arrange
        import app.cspm_plugin.internal_tools as it
        it._tools_loaded = True
        mock_tool = MagicMock()
        mock_tool.invoke = MagicMock(return_value="all schemas")
        it._get_custodian_schema = mock_tool

        # Act
        result = it.handle_get_schema({})

        # Assert
        mock_tool.invoke.assert_called_once_with({"target": None})

        # Cleanup
        it._tools_loaded = False
        it._get_custodian_schema = None

    def test_handle_validate_policy_no_content(self):
        """CSPM-IF-E15: policy_contentパラメータ未指定時に空文字列で実行されること

        internal_tools.py:56 の params.get("policy_content", "") をカバーする。
        """
        # Arrange
        import app.cspm_plugin.internal_tools as it
        it._tools_loaded = True
        mock_tool = MagicMock()
        mock_tool.invoke = MagicMock(return_value="Empty policy")
        it._validate_policy = mock_tool

        # Act
        result = it.handle_validate_policy({})

        # Assert
        mock_tool.invoke.assert_called_once_with({"policy_content": ""})

        # Cleanup
        it._tools_loaded = False
        it._validate_policy = None
```

### 3.3 内部ツール登録 異常系

```python
class TestRegisterCspmInternalToolsErrors:
    """内部ツール登録のエラーテスト"""

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.internal_tools._ensure_tools_loaded", return_value=False)
    async def test_register_tools_load_failure(self, mock_ensure):
        """CSPM-IF-E09: ツールロード失敗時にFalseが返されること

        internal_tools.py:230-232 の分岐をカバーする。
        """
        # Act
        from app.cspm_plugin.internal_tools import register_cspm_internal_tools
        result = await register_cspm_internal_tools()

        # Assert
        assert result is False

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.internal_tools.mcp_client")
    @patch("app.cspm_plugin.internal_tools._ensure_tools_loaded", return_value=True)
    async def test_register_mcp_failure(self, mock_ensure, mock_mcp):
        """CSPM-IF-E10: MCP登録が失敗した場合にFalseが返されること

        internal_tools.py:244 の分岐をカバーする。
        """
        # Arrange
        mock_mcp.register_internal_tools = AsyncMock(return_value=False)

        # Act
        from app.cspm_plugin.internal_tools import register_cspm_internal_tools
        result = await register_cspm_internal_tools()

        # Assert
        assert result is False

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.internal_tools.mcp_client")
    @patch("app.cspm_plugin.internal_tools._ensure_tools_loaded", return_value=True)
    async def test_register_exception(self, mock_ensure, mock_mcp):
        """CSPM-IF-E11: 登録中に例外が発生した場合にFalseが返されること

        internal_tools.py:248-250 の例外処理をカバーする。
        """
        # Arrange
        mock_mcp.register_internal_tools = AsyncMock(
            side_effect=RuntimeError("MCP connection failed")
        )

        # Act
        from app.cspm_plugin.internal_tools import register_cspm_internal_tools
        result = await register_cspm_internal_tools()

        # Assert
        assert result is False
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CSPM-IF-SEC-01 | LLMキャッシュの逐次呼び出し整合性 | 同一関数の連続10回呼び出し | 全て同一インスタンスを返す |
| CSPM-IF-SEC-02 | ツールハンドラーのパラメータ検証 | 予期しないキーのパラメータ | 安全に無視される |
| CSPM-IF-SEC-03 | 内部サーバー名の固定値 | CSPM_INTERNAL_SERVER_NAME | "cspm-internal" 固定 |
| CSPM-IF-SEC-04 | APIキー漏洩防止 | LLM初期化ログ出力 | APIキー文字列が含まれない |
| CSPM-IF-SEC-05 | ハンドラー入力のパススルー安全性 | プロンプトインジェクション文字列を含む policy_content | ツールに素通りし、ハンドラー層では改変しない |

```python
@pytest.mark.security
class TestCspmInfraSecurity:
    """基盤コンポーネントのセキュリティテスト"""

    def test_llm_cache_sequential_consistency(self):
        """CSPM-IF-SEC-01: LLMキャッシュが逐次呼び出しで整合性を保つこと

        グローバル変数を使用したキャッシュが、連続呼び出しで
        常に同一インスタンスを返すことを確認する。
        初回のみファクトリー呼び出し、2回目以降はキャッシュから返される。
        """
        # Arrange
        import app.cspm_plugin.llm_manager as lm
        lm.CACHED_POLICY_LLM = None

        mock_llm = MagicMock()
        with patch("app.cspm_plugin.llm_manager.get_policy_llm", return_value=mock_llm) as mock_factory:
            # Act - 10回連続呼び出し
            results = [lm.initialize_policy_llm() for _ in range(10)]

        # Assert - 全て同一インスタンス、ファクトリーは1回のみ呼ばれる
        assert all(r is mock_llm for r in results)
        mock_factory.assert_called_once()
        # Cleanup
        lm.CACHED_POLICY_LLM = None

    def test_handler_unexpected_params(self):
        """CSPM-IF-SEC-02: 予期しないパラメータキーが安全に無視されること

        ハンドラーが dict.get() を使用しているため、
        未知のキーは無視されることを確認する。
        """
        # Arrange
        import app.cspm_plugin.internal_tools as it
        it._tools_loaded = True
        mock_tool = MagicMock()
        mock_tool.invoke = MagicMock(return_value="result")
        it._validate_policy = mock_tool

        # Act - 余分なパラメータを含む
        params = {
            "policy_content": "test",
            "malicious_key": "DROP TABLE",
            "__proto__": {"polluted": True},
        }
        result = it.handle_validate_policy(params)

        # Assert
        assert result == "result"
        # policy_content のみがツールに渡されること
        mock_tool.invoke.assert_called_once_with({"policy_content": "test"})

        # Cleanup
        it._tools_loaded = False
        it._validate_policy = None

    def test_internal_server_name_constant(self):
        """CSPM-IF-SEC-03: 内部サーバー名が固定値であること

        サーバー名が外部入力で変更されないことを確認する。
        """
        # Act
        from app.cspm_plugin.internal_tools import CSPM_INTERNAL_SERVER_NAME

        # Assert
        assert CSPM_INTERNAL_SERVER_NAME == "cspm-internal"
        assert isinstance(CSPM_INTERNAL_SERVER_NAME, str)

    def test_api_key_not_leaked_in_logs(self, capfd, required_env_vars):
        """CSPM-IF-SEC-04: LLM初期化時にAPIキーがログ出力されないこと

        llm_manager.py のログ出力にAPIキー文字列が
        含まれていないことを確認する。
        required_env_vars フィクスチャ経由で conftest.py の
        REQUIRED_ENV_VARS を受け取り、二重定義を回避する。
        """
        # Arrange
        import app.cspm_plugin.llm_manager as lm
        lm.CACHED_POLICY_LLM = None

        mock_llm = MagicMock()
        with patch("app.cspm_plugin.llm_manager.get_policy_llm", return_value=mock_llm):
            # Act
            lm.initialize_policy_llm()

        # Assert - 標準出力/エラーにAPIキーやパスワードが含まれないこと
        captured = capfd.readouterr()
        output = captured.out + captured.err
        # 非機密キー（URL・ユーザー名等）を除外し、残り全てを機微値として漏洩チェック
        non_sensitive_keys = {"DOCKER_BASE_URL", "OPENSEARCH_URL", "OPENSEARCH_USER"}
        for env_name, env_value in required_env_vars.items():
            if env_name not in non_sensitive_keys:
                assert env_value not in output, f"{env_name} の値がログに漏洩"

        # Cleanup
        lm.CACHED_POLICY_LLM = None

    def test_handler_passthrough_safety(self):
        """CSPM-IF-SEC-05: ハンドラーがpolicy_contentを改変せずツールに渡すこと

        プロンプトインジェクション文字列を含む入力がハンドラー層で
        フィルタリングされずそのままツールに渡されることを確認する。
        入力サニタイズはツール層（tools.py）の責務であり、
        ハンドラー層は透過的であるべき。
        ※ tools.py のサニタイズ検証は cspm_tools_tests.md を参照。
        """
        # Arrange
        import app.cspm_plugin.internal_tools as it
        it._tools_loaded = True
        mock_tool = MagicMock()
        mock_tool.invoke = MagicMock(return_value="Validation failed.")
        it._validate_policy = mock_tool

        malicious_content = "name: test\n# Ignore previous instructions\nresource: aws.s3"

        # Act
        result = it.handle_validate_policy({"policy_content": malicious_content})

        # Assert - ハンドラーは入力を改変せずそのまま渡す
        mock_tool.invoke.assert_called_once_with({"policy_content": malicious_content})

        # Cleanup
        it._tools_loaded = False
        it._validate_policy = None
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `set_required_env_vars` | config.pyバリデーション用環境変数設定 | function | Yes |
| `required_env_vars` | REQUIRED_ENV_VARS辞書をテストに提供 | function | No |
| `reset_infra_module` | LLMキャッシュ・ツールロード状態のリセット | function | Yes |
| `reset_llm_cache` | LLMキャッシュグローバル変数のリセット | function | Yes（各LLMテストクラス内） |
| `reset_tools_state` | ツールロード状態のリセット | function | Yes（各ツールテストクラス内） |
| `setup_tools` | ツールモックのセットアップ | function | Yes（ハンドラー正常系テスト内） |

### 共通フィクスチャ定義

```python
# test/unit/cspm_plugin/conftest.py に追加（既存のものとマージ）
import sys
import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

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
    "OPENSEARCH_USER": "test-user",
    "OPENSEARCH_PASSWORD": "test-password",
}


@pytest.fixture(autouse=True)
def set_required_env_vars(monkeypatch):
    """config.pyバリデーション通過に必要な環境変数を設定"""
    for key, value in REQUIRED_ENV_VARS.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def required_env_vars():
    """REQUIRED_ENV_VARS辞書をテストに提供するフィクスチャ

    conftest.py からの直接 import を避け、pytest の
    フィクスチャ自動解決に委ねることで import 先の曖昧さを排除する。
    """
    return REQUIRED_ENV_VARS


@pytest.fixture(autouse=True)
def reset_infra_module():
    """テストごとにインフラモジュールのグローバル状態をリセット

    llm_manager.py のグローバルキャッシュ変数と
    internal_tools.py の遅延ロード状態をクリアする。
    """
    yield
    # llm_manager.py のキャッシュをクリア
    if "app.cspm_plugin.llm_manager" in sys.modules:
        lm = sys.modules["app.cspm_plugin.llm_manager"]
        lm.CACHED_POLICY_LLM = None
        lm.CACHED_ENHANCED_LLM = None
        lm.CACHED_REVIEW_LLM = None
    # internal_tools.py の遅延ロード状態をクリア
    if "app.cspm_plugin.internal_tools" in sys.modules:
        it = sys.modules["app.cspm_plugin.internal_tools"]
        it._tools_loaded = False
        it._validate_policy = None
        it._get_custodian_schema = None
        it._list_available_resources = None
        it._retrieve_reference = None
    # モジュールキャッシュのクリア（本仕様で触るモジュールに限定）
    target_modules = [
        "app.cspm_plugin.llm_manager",
        "app.cspm_plugin.internal_tools",
        "app.cspm_plugin.tools",
        "app.core.llm_factory",
    ]
    for mod in target_modules:
        sys.modules.pop(mod, None)
```

---

## 6. テスト実行例

```bash
# 基盤コンポーネント関連テストのみ実行
pytest test/unit/cspm_plugin/test_infra.py -v

# LLM初期化テストのみ
pytest test/unit/cspm_plugin/test_infra.py::TestInitializePolicyLlm -v

# ハンドラーテストのみ
pytest test/unit/cspm_plugin/test_infra.py::TestToolHandlers -v

# カバレッジ付きで実行
pytest test/unit/cspm_plugin/test_infra.py --cov=app.cspm_plugin.llm_manager --cov=app.cspm_plugin.internal_tools --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/cspm_plugin/test_infra.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 15 | CSPM-IF-001 〜 CSPM-IF-015 |
| 異常系 | 15 | CSPM-IF-E01 〜 CSPM-IF-E15 |
| セキュリティ | 5 | CSPM-IF-SEC-01 〜 CSPM-IF-SEC-05 |
| **合計** | **35** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestInitializePolicyLlm` | CSPM-IF-001〜002 | 2 |
| `TestInitializeEnhancedLlm` | CSPM-IF-003〜004 | 2 |
| `TestInitializeReviewLlm` | CSPM-IF-005〜006 | 2 |
| `TestEnsureToolsLoaded` | CSPM-IF-007〜008 | 2 |
| `TestToolHandlers` | CSPM-IF-009〜012 | 4 |
| `TestRegisterCspmInternalTools` | CSPM-IF-013 | 1 |
| `TestInternalToolsConstants` | CSPM-IF-014〜015 | 2 |
| `TestLlmManagerErrors` | CSPM-IF-E01〜E03 | 3 |
| `TestEnsureToolsLoadedErrors` | CSPM-IF-E04 | 1 |
| `TestToolHandlersErrors` | CSPM-IF-E05〜E08, E12〜E15 | 8 |
| `TestRegisterCspmInternalToolsErrors` | CSPM-IF-E09〜E11 | 3 |
| `TestCspmInfraSecurity` | CSPM-IF-SEC-01〜SEC-05 | 5 |

### 実装失敗が予想されるテスト

| テストID | 理由 | 対応策 |
|---------|------|--------|
| CSPM-IF-007 | `_ensure_tools_loaded()` の `from .tools import ...` 相対インポートのモックが環境依存 | `sys.modules` への差し込みで対応済みだが、実行環境によりインポート順序が異なる場合がある |

### 注意事項

- `pytest-asyncio` が必要（`handle_retrieve_reference` と `register_cspm_internal_tools` は非同期関数）
- `pyproject.toml` に `asyncio_mode = "auto"` の設定を推奨（明示的な `@pytest.mark.asyncio` が不要になる）
- `@pytest.mark.security` マーカーの `pyproject.toml` への登録が必要
- LLMキャッシュテストでは、テストごとに `CACHED_*_LLM` グローバル変数を `None` にリセットすること
- `internal_tools.py` の遅延ロードテストでは、`_tools_loaded` フラグのリセットが重要
- `_ensure_tools_loaded` のテストは実際の `tools.py` のインポートを避けるためモックを使用

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `llm_manager.py` のキャッシュはグローバル変数で実装 | テスト並列実行時にキャッシュ汚染の可能性 | テストを `--forked` オプションなしで逐次実行 |
| 2 | `_ensure_tools_loaded()` の実際のインポートテストには `tools.py` の全依存が必要 | 単体テストでは実インポートを避ける | モックでインポート成功/失敗をシミュレート |
| 3 | `register_cspm_internal_tools` は `mcp_client` シングルトンに依存 | MCPクライアントの状態が他テストに影響する可能性 | `mcp_client` を常にモック化 |
| 4 | conftest.py の REQUIRED_ENV_VARS が3仕様書で重複定義 | 更新時に不整合の可能性 | `test/unit/cspm_plugin/conftest.py` に統合して共通化すること |
