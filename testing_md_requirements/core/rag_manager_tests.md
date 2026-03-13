# rag_manager テストケース

## 1. 概要

RAGクライアントのグローバル管理システムのテストケースを定義します。
複数ユーザーが同時アクセスしても安全な初期化を提供するシングルトンパターンを実装しています。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `RAGManager` | RAGクライアントの安全な初期化と管理を行うシングルトンクラス |
| `RAGManager.get_instance()` | シングルトンインスタンスを取得（クラスメソッド、非同期） |
| `RAGManager.initialize()` | RAGシステムを安全に初期化（double-checked locking） |
| `RAGManager.get_enhanced_rag_search()` | 初期化済みの強化版RAG検索システムを取得 |
| `RAGManager.is_initialized()` | 初期化状態を確認 |
| `RAGManager.health_check()` | RAGシステムのヘルスチェック |
| `get_global_rag_manager()` | グローバルRAGマネージャーを取得 |
| `initialize_global_rag_system()` | グローバルRAGシステムを初期化 |
| `get_enhanced_rag_search()` | 初期化済みの強化版RAG検索システムを取得（DI用） |

### 1.2 カバレッジ目標: 75%

> **注記**: AI機能の中核モジュールですが、外部依存（EnhancedRAGSearch）が多いため、
> モック中心のテストとなります。実際の接続テストは統合テストで実施します。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/core/rag_manager.py` |
| テストコード | `test/unit/core/test_rag_manager.py` |

### 1.4 補足情報

**グローバル変数:**

| 変数名 | 型 | 説明 |
|--------|------|------|
| `_global_rag_manager` | `Optional[RAGManager]` | グローバルRAGマネージャーインスタンス |

**クラス変数（RAGManager）:**

| 変数名 | 型 | 説明 |
|--------|------|------|
| `_instance` | `Optional[RAGManager]` | シングルトンインスタンス |
| `_lock` | `asyncio.Lock` | シングルトン取得用ロック |

**インスタンス変数（RAGManager）:**

| 変数名 | 型 | 説明 |
|--------|------|------|
| `enhanced_rag_search` | `Optional[object]` | 強化版RAG検索システム |
| `_initialized` | `bool` | 初期化完了フラグ |
| `_initialization_lock` | `asyncio.Lock` | 初期化用ロック |

**モック設計の重要事項:**

| 項目 | 詳細 |
|------|------|
| EnhancedRAGSearchのpatchパス | `app.rag.enhanced_rag_search.EnhancedRAGSearch` |
| 理由 | `rag_manager.py:55` で `from ..rag.enhanced_rag_search import EnhancedRAGSearch` として**動的インポート**されるため、インポート元でpatchする必要がある |
| 誤った例 | `app.core.rag_manager.EnhancedRAGSearch` ← これは動作しない |

**主要分岐:**

| 行番号 | 条件 | 分岐内容 |
|--------|------|----------|
| 33-36 | `cls._instance is None` | シングルトン初回作成（double-checked locking） |
| 43-44 | `self._initialized` | 初期化済みなら即return True |
| 48-49 | `self._initialized`（ロック内） | double-checked locking |
| 60-66 | `success` | EnhancedRAGSearch初期化成功/失敗 |
| 68-70 | `except Exception` | 初期化中の例外処理 |
| 76-79 | `not self._initialized` | 未初期化なら自動初期化試行 |
| 93-98 | `not self._initialized` | ヘルスチェック：未初期化状態 |
| 101-107 | `self.enhanced_rag_search` | ヘルスチェック：RAG有り |
| 108-113 | else | ヘルスチェック：RAG無し |
| 114-120 | `except Exception` | ヘルスチェック例外 |
| 132-133 | `_global_rag_manager is None` | グローバル初回取得 |
| 145-147 | `except Exception` | グローバル初期化例外 |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| RAG-001 | モジュールインポート成功 | モジュールインポート | 例外なし、クラス・関数が存在 |
| RAG-002 | シングルトンインスタンス取得 | `get_instance()` | RAGManagerインスタンス |
| RAG-003 | シングルトン一貫性 | `get_instance()` 2回呼び出し | 同一インスタンス |
| RAG-004 | 初期化成功 | `initialize()` | True、`_initialized=True` |
| RAG-005 | 初期化済みで再度initialize | 初期化済み状態 | 即座にTrue返却 |
| RAG-006 | double-checked locking動作確認 | 並行初期化 | 1回のみ初期化実行 |
| RAG-007 | get_enhanced_rag_search成功 | 初期化済み状態 | EnhancedRAGSearchインスタンス |
| RAG-008 | get_enhanced_rag_search自動初期化 | 未初期化状態 | 自動初期化後にインスタンス返却 |
| RAG-009 | is_initialized確認（未初期化） | 初期状態 | False |
| RAG-010 | is_initialized確認（初期化済み） | 初期化後 | True |
| RAG-011 | ヘルスチェック成功 | 初期化済み状態 | status="healthy" |
| RAG-012 | グローバルマネージャー取得 | `get_global_rag_manager()` | RAGManagerインスタンス |
| RAG-013 | グローバルシステム初期化成功 | `initialize_global_rag_system()` | True |
| RAG-014 | DI用get_enhanced_rag_search成功 | モジュールレベル関数 | EnhancedRAGSearchインスタンス |

### 2.1 モジュールインポートテスト

```python
# test/unit/core/test_rag_manager.py
import pytest
import sys
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock


class TestRAGManagerImport:
    """RAGマネージャーモジュールインポートテスト"""

    def test_import_rag_manager_module(self):
        """RAG-001: モジュールのインポート成功"""
        # Arrange
        # （インポートテストのため、事前準備なし）

        # Act
        from app.core import rag_manager

        # Assert
        # クラスが存在することを確認
        assert hasattr(rag_manager, "RAGManager")
        # 関数が存在することを確認
        assert hasattr(rag_manager, "get_global_rag_manager")
        assert hasattr(rag_manager, "initialize_global_rag_system")
        assert hasattr(rag_manager, "get_enhanced_rag_search")
        # グローバル変数が存在することを確認
        assert hasattr(rag_manager, "_global_rag_manager")
```

### 2.2 RAGManager.get_instance テスト

```python
class TestRAGManagerGetInstance:
    """シングルトンインスタンス取得テスト"""

    @pytest.mark.asyncio
    async def test_get_instance_returns_rag_manager(self):
        """RAG-002: シングルトンインスタンス取得成功"""
        # Arrange
        from app.core.rag_manager import RAGManager

        # Act
        instance = await RAGManager.get_instance()

        # Assert
        assert instance is not None
        assert isinstance(instance, RAGManager)

    @pytest.mark.asyncio
    async def test_get_instance_returns_same_instance(self):
        """RAG-003: シングルトン一貫性（同一インスタンス返却）"""
        # Arrange
        from app.core.rag_manager import RAGManager

        # Act
        first_instance = await RAGManager.get_instance()
        second_instance = await RAGManager.get_instance()

        # Assert
        assert first_instance is second_instance
```

### 2.3 RAGManager.initialize テスト

```python
class TestRAGManagerInitialize:
    """RAGシステム初期化テスト"""

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """RAG-004: 初期化成功"""
        # Arrange
        mock_enhanced_rag = MagicMock()
        mock_enhanced_rag.initialize = AsyncMock(return_value=True)

        with patch(
            "app.rag.enhanced_rag_search.EnhancedRAGSearch",
            return_value=mock_enhanced_rag
        ):
            from app.core.rag_manager import RAGManager
            manager = RAGManager()

            # Act
            result = await manager.initialize()

            # Assert
            assert result is True
            assert manager._initialized is True
            assert manager.enhanced_rag_search is mock_enhanced_rag

    @pytest.mark.asyncio
    async def test_initialize_already_initialized_returns_true(self):
        """RAG-005: 初期化済み状態で再度initializeはTrue即返却

        rag_manager.py:43-44 の分岐をカバーする。
        """
        # Arrange
        from app.core.rag_manager import RAGManager
        manager = RAGManager()
        manager._initialized = True

        # Act
        result = await manager.initialize()

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_initialize_double_checked_locking(self):
        """RAG-006: double-checked locking動作確認

        rag_manager.py:48-49 の分岐をカバーする。
        並行して初期化が試行されても1回のみ実行されることを確認。
        """
        # Arrange
        init_call_count = 0
        instance_count = 0

        class MockEnhancedRAGSearch:
            """initializeの呼び出し回数とインスタンス化回数をカウントするモッククラス"""

            def __init__(self):
                nonlocal instance_count
                instance_count += 1

            async def initialize(self):
                nonlocal init_call_count
                init_call_count += 1
                await asyncio.sleep(0.1)  # 遅延をシミュレート
                return True

        with patch(
            "app.rag.enhanced_rag_search.EnhancedRAGSearch",
            MockEnhancedRAGSearch
        ):
            from app.core.rag_manager import RAGManager
            manager = RAGManager()

            # Act - 並行して初期化を試行
            results = await asyncio.gather(
                manager.initialize(),
                manager.initialize(),
                manager.initialize()
            )

            # Assert
            # すべてTrueを返す
            assert all(results)
            # インスタンス化は1回のみ（double-checked lockingにより）
            assert instance_count == 1, "EnhancedRAGSearchインスタンスは1回のみ作成されるべき"
            # 初期化メソッドも1回のみ実行される
            assert init_call_count == 1, "initialize()は1回のみ実行されるべき"
```

### 2.4 RAGManager.get_enhanced_rag_search テスト

```python
class TestRAGManagerGetEnhancedRAGSearch:
    """強化版RAG検索システム取得テスト"""

    @pytest.mark.asyncio
    async def test_get_enhanced_rag_search_success(self):
        """RAG-007: 初期化済み状態でRAG検索システム取得成功"""
        # Arrange
        mock_enhanced_rag = MagicMock()

        from app.core.rag_manager import RAGManager
        manager = RAGManager()
        manager._initialized = True
        manager.enhanced_rag_search = mock_enhanced_rag

        # Act
        result = await manager.get_enhanced_rag_search()

        # Assert
        assert result is mock_enhanced_rag

    @pytest.mark.asyncio
    async def test_get_enhanced_rag_search_auto_initialize(self):
        """RAG-008: 未初期化状態で自動初期化後にインスタンス返却

        rag_manager.py:76-79 の分岐をカバーする。
        """
        # Arrange
        mock_enhanced_rag = MagicMock()
        mock_enhanced_rag.initialize = AsyncMock(return_value=True)

        with patch(
            "app.rag.enhanced_rag_search.EnhancedRAGSearch",
            return_value=mock_enhanced_rag
        ):
            from app.core.rag_manager import RAGManager
            manager = RAGManager()
            assert manager._initialized is False

            # Act
            result = await manager.get_enhanced_rag_search()

            # Assert
            assert result is mock_enhanced_rag
            assert manager._initialized is True
```

### 2.5 RAGManager.is_initialized テスト

```python
class TestRAGManagerIsInitialized:
    """初期化状態確認テスト"""

    def test_is_initialized_false_initially(self):
        """RAG-009: 初期状態でFalse"""
        # Arrange
        from app.core.rag_manager import RAGManager
        manager = RAGManager()

        # Act
        result = manager.is_initialized()

        # Assert
        assert result is False

    def test_is_initialized_true_after_init(self):
        """RAG-010: 初期化後でTrue"""
        # Arrange
        from app.core.rag_manager import RAGManager
        manager = RAGManager()
        manager._initialized = True

        # Act
        result = manager.is_initialized()

        # Assert
        assert result is True
```

### 2.6 RAGManager.health_check テスト

```python
class TestRAGManagerHealthCheck:
    """ヘルスチェックテスト"""

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """RAG-011: 初期化済み状態でヘルスチェック成功

        rag_manager.py:101-107 の分岐をカバーする。
        """
        # Arrange
        mock_health_info = {"opensearch": "healthy", "embedding": "healthy"}
        mock_enhanced_rag = MagicMock()
        mock_enhanced_rag.get_health = AsyncMock(return_value=mock_health_info)

        from app.core.rag_manager import RAGManager
        manager = RAGManager()
        manager._initialized = True
        manager.enhanced_rag_search = mock_enhanced_rag

        # Act
        result = await manager.health_check()

        # Assert
        assert result["status"] == "healthy"
        assert result["initialized"] is True
        assert result["rag_health"] == mock_health_info
```

### 2.7 グローバル関数テスト

```python
class TestGlobalFunctions:
    """グローバル関数テスト"""

    @pytest.mark.asyncio
    async def test_get_global_rag_manager(self):
        """RAG-012: グローバルマネージャー取得成功"""
        # Arrange
        from app.core.rag_manager import get_global_rag_manager, RAGManager

        # Act
        manager = await get_global_rag_manager()

        # Assert
        assert manager is not None
        assert isinstance(manager, RAGManager)

    @pytest.mark.asyncio
    async def test_initialize_global_rag_system_success(self):
        """RAG-013: グローバルシステム初期化成功"""
        # Arrange
        mock_enhanced_rag = MagicMock()
        mock_enhanced_rag.initialize = AsyncMock(return_value=True)

        with patch(
            "app.rag.enhanced_rag_search.EnhancedRAGSearch",
            return_value=mock_enhanced_rag
        ):
            from app.core.rag_manager import initialize_global_rag_system

            # Act
            result = await initialize_global_rag_system()

            # Assert
            assert result is True

    @pytest.mark.asyncio
    async def test_module_level_get_enhanced_rag_search(self):
        """RAG-014: DI用get_enhanced_rag_search成功"""
        # Arrange
        mock_enhanced_rag = MagicMock()
        mock_enhanced_rag.initialize = AsyncMock(return_value=True)

        with patch(
            "app.rag.enhanced_rag_search.EnhancedRAGSearch",
            return_value=mock_enhanced_rag
        ):
            from app.core.rag_manager import get_enhanced_rag_search

            # Act
            result = await get_enhanced_rag_search()

            # Assert
            assert result is mock_enhanced_rag
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| RAG-E01 | EnhancedRAGSearch初期化失敗 | initialize()がFalse返却 | False、_initialized=False |
| RAG-E02 | 初期化中の例外 | EnhancedRAGSearch初期化で例外 | False、エラーログ出力 |
| RAG-E03 | get_enhanced_rag_search初期化失敗 | 自動初期化失敗 | RuntimeError |
| RAG-E04 | ヘルスチェック未初期化 | _initialized=False | status="uninitialized" |
| RAG-E05 | ヘルスチェックRAG無し | enhanced_rag_search=None | status="error" |
| RAG-E06 | ヘルスチェック例外 | get_health()で例外 | status="error"、エラー内容 |
| RAG-E07 | グローバル初期化例外 | initialize()で例外 | False、エラーログ出力 |

### 3.1 初期化エラーテスト

```python
class TestRAGManagerInitializeErrors:
    """RAGシステム初期化エラーテスト"""

    @pytest.mark.asyncio
    async def test_initialize_rag_returns_false(self, caplog):
        """RAG-E01: EnhancedRAGSearch初期化がFalseを返す

        rag_manager.py:64-66 の分岐をカバーする。
        """
        # Arrange
        mock_enhanced_rag = MagicMock()
        mock_enhanced_rag.initialize = AsyncMock(return_value=False)

        with patch(
            "app.rag.enhanced_rag_search.EnhancedRAGSearch",
            return_value=mock_enhanced_rag
        ):
            import logging
            caplog.set_level(logging.ERROR)
            from app.core.rag_manager import RAGManager
            manager = RAGManager()

            # Act
            result = await manager.initialize()

            # Assert
            assert result is False
            assert manager._initialized is False
            assert "初期化に失敗" in caplog.text

    @pytest.mark.asyncio
    async def test_initialize_exception(self, caplog):
        """RAG-E02: 初期化中に例外が発生

        rag_manager.py:68-70 の分岐をカバーする。
        """
        # Arrange
        with patch(
            "app.rag.enhanced_rag_search.EnhancedRAGSearch",
            side_effect=ImportError("Module not found")
        ):
            import logging
            caplog.set_level(logging.ERROR)
            from app.core.rag_manager import RAGManager
            manager = RAGManager()

            # Act
            result = await manager.initialize()

            # Assert
            assert result is False
            assert manager._initialized is False
            assert "初期化エラー" in caplog.text

    @pytest.mark.asyncio
    async def test_get_enhanced_rag_search_init_failure(self):
        """RAG-E03: get_enhanced_rag_search自動初期化失敗でRuntimeError

        rag_manager.py:78-79 の分岐をカバーする。
        """
        # Arrange
        mock_enhanced_rag = MagicMock()
        mock_enhanced_rag.initialize = AsyncMock(return_value=False)

        with patch(
            "app.rag.enhanced_rag_search.EnhancedRAGSearch",
            return_value=mock_enhanced_rag
        ):
            from app.core.rag_manager import RAGManager
            manager = RAGManager()

            # Act & Assert
            with pytest.raises(RuntimeError, match="初期化されていません"):
                await manager.get_enhanced_rag_search()
```

### 3.2 ヘルスチェックエラーテスト

```python
class TestRAGManagerHealthCheckErrors:
    """ヘルスチェックエラーテスト"""

    @pytest.mark.asyncio
    async def test_health_check_uninitialized(self):
        """RAG-E04: 未初期化状態でヘルスチェック

        rag_manager.py:93-98 の分岐をカバーする。
        """
        # Arrange
        from app.core.rag_manager import RAGManager
        manager = RAGManager()
        assert manager._initialized is False

        # Act
        result = await manager.health_check()

        # Assert
        assert result["status"] == "uninitialized"
        assert result["initialized"] is False
        assert "初期化されていません" in result["error"]

    @pytest.mark.asyncio
    async def test_health_check_no_rag_search(self):
        """RAG-E05: enhanced_rag_searchがNoneの状態でヘルスチェック

        rag_manager.py:108-113 の分岐をカバーする。
        """
        # Arrange
        from app.core.rag_manager import RAGManager
        manager = RAGManager()
        manager._initialized = True
        manager.enhanced_rag_search = None

        # Act
        result = await manager.health_check()

        # Assert
        assert result["status"] == "error"
        assert result["initialized"] is False
        assert "利用できません" in result["error"]

    @pytest.mark.asyncio
    async def test_health_check_exception(self, caplog):
        """RAG-E06: ヘルスチェック中に例外が発生

        rag_manager.py:114-120 の分岐をカバーする。
        """
        # Arrange
        mock_enhanced_rag = MagicMock()
        mock_enhanced_rag.get_health = AsyncMock(
            side_effect=ConnectionError("Connection refused")
        )

        import logging
        caplog.set_level(logging.ERROR)
        from app.core.rag_manager import RAGManager
        manager = RAGManager()
        manager._initialized = True
        manager.enhanced_rag_search = mock_enhanced_rag

        # Act
        result = await manager.health_check()

        # Assert
        assert result["status"] == "error"
        assert result["initialized"] is True
        assert "Connection refused" in result["error"]
        assert "ヘルスチェックエラー" in caplog.text
```

### 3.3 グローバル関数エラーテスト

```python
class TestGlobalFunctionsErrors:
    """グローバル関数エラーテスト"""

    @pytest.mark.asyncio
    async def test_initialize_global_rag_system_exception(self, caplog):
        """RAG-E07: グローバル初期化中に例外が発生

        rag_manager.py:145-147 の分岐をカバーする。
        """
        # Arrange
        with patch(
            "app.core.rag_manager.get_global_rag_manager",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Manager creation failed")
        ):
            import logging
            caplog.set_level(logging.ERROR)
            from app.core.rag_manager import initialize_global_rag_system

            # Act
            result = await initialize_global_rag_system()

            # Assert
            assert result is False
            assert "グローバルRAGシステム初期化エラー" in caplog.text
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| RAG-SEC-01 | エラーログに機密情報が含まれない | 例外発生時 | 【実装失敗予定】認証情報がログに出力されない（現状は漏洩する） |
| RAG-SEC-02 | ヘルスチェックに内部エラー詳細が漏洩しない | 例外発生時 | 例外メッセージは含まれるが、スタックトレースは含まれない |
| RAG-SEC-03 | シングルトンのスレッドセーフ性 | 並行アクセス | 競合状態なし |

```python
@pytest.mark.security
class TestRAGManagerSecurity:
    """RAGマネージャーセキュリティテスト"""

    @pytest.mark.asyncio
    async def test_error_log_no_sensitive_info(self, caplog):
        """RAG-SEC-01: エラーログに機密情報が含まれない

        初期化エラー時のログに認証情報やAPIキーが含まれないことを検証。

        【実装失敗予定】rag_manager.py:69 で例外メッセージがそのままログに出力されるため、
        機密情報を含む例外が発生した場合、ログに漏洩する。
        実装側でサニタイズ処理を追加することを推奨。
        """
        # Arrange
        # 認証情報を含む例外をシミュレート
        sensitive_error = Exception(
            "Connection failed: api_key=sk-secret-key-12345, password=super_secret"
        )

        with patch(
            "app.rag.enhanced_rag_search.EnhancedRAGSearch",
            side_effect=sensitive_error
        ):
            import logging
            caplog.set_level(logging.ERROR)
            from app.core.rag_manager import RAGManager
            manager = RAGManager()

            # Act
            await manager.initialize()

            # Assert
            log_text = caplog.text.lower()
            assert "初期化エラー" in caplog.text
            # 以下は現在の実装では失敗する（機密情報がログに含まれる）
            # 実装修正後に有効化すること
            assert "sk-secret-key" not in log_text, "APIキーがログに漏洩しています"
            assert "super_secret" not in log_text, "パスワードがログに漏洩しています"

    @pytest.mark.asyncio
    async def test_health_check_no_stack_trace_leak(self):
        """RAG-SEC-02: ヘルスチェック結果に内部エラー詳細が漏洩しない

        ヘルスチェック結果にスタックトレースや内部実装の詳細が含まれないことを検証。
        """
        # Arrange
        detailed_error = ValueError(
            "Internal error at line 123: database connection pool exhausted"
        )
        mock_enhanced_rag = MagicMock()
        mock_enhanced_rag.get_health = AsyncMock(side_effect=detailed_error)

        from app.core.rag_manager import RAGManager
        manager = RAGManager()
        manager._initialized = True
        manager.enhanced_rag_search = mock_enhanced_rag

        # Act
        result = await manager.health_check()

        # Assert
        error_message = result.get("error", "")
        # 例外メッセージは含まれるが、スタックトレースは含まれない
        assert "Traceback" not in error_message
        assert "File " not in error_message
        # 例外型名は漏洩しても問題ない（デバッグに有用）
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_singleton_thread_safety(self):
        """RAG-SEC-03: シングルトンのスレッドセーフ性

        並行アクセス時に競合状態が発生せず、同一インスタンスが返されることを検証。
        """
        # Arrange
        from app.core.rag_manager import RAGManager

        # Act - 多数の並行アクセス
        tasks = [RAGManager.get_instance() for _ in range(100)]
        instances = await asyncio.gather(*tasks)

        # Assert
        # すべて同一インスタンス
        first_instance = instances[0]
        for instance in instances[1:]:
            assert instance is first_instance
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_rag_manager_module` | テスト間のモジュール・シングルトン状態リセット | function | Yes |
| `mock_enhanced_rag_search` | EnhancedRAGSearchモック | function | No |

### 共通フィクスチャ定義

```python
# test/unit/core/conftest.py に追加
import sys
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.fixture(autouse=True)
def reset_rag_manager_module():
    """テストごとにrag_managerモジュールのグローバル状態をリセット

    rag_manager.pyはシングルトンパターンを使用しており、
    テスト間の独立性を保証するためリセットが必要。
    テスト前後両方でクリアすることで、並列実行時の競合を防止する。
    """
    # テスト前にモジュールキャッシュをクリア
    modules_to_remove = [
        key for key in list(sys.modules.keys())
        if key.startswith("app.core.rag_manager") or key.startswith("app.rag")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]

    yield

    # テスト後にクリーンアップ
    try:
        import app.core.rag_manager as rag_module
        # グローバル変数をリセット
        rag_module._global_rag_manager = None
        # クラス変数をリセット
        rag_module.RAGManager._instance = None
    except (ImportError, AttributeError):
        pass
    # モジュールキャッシュもクリア
    modules_to_remove = [
        key for key in list(sys.modules.keys())
        if key.startswith("app.core.rag_manager") or key.startswith("app.rag")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def mock_enhanced_rag_search():
    """EnhancedRAGSearchモック（外部依存防止）"""
    mock_rag = MagicMock()
    mock_rag.initialize = AsyncMock(return_value=True)
    mock_rag.get_health = AsyncMock(return_value={"status": "healthy"})
    return mock_rag
```

---

## 6. テスト実行例

```bash
# rag_manager関連テストのみ実行
pytest test/unit/core/test_rag_manager.py -v

# 特定のテストクラスのみ実行
pytest test/unit/core/test_rag_manager.py::TestRAGManagerInitialize -v
pytest test/unit/core/test_rag_manager.py::TestRAGManagerHealthCheck -v
pytest test/unit/core/test_rag_manager.py::TestRAGManagerSecurity -v

# カバレッジ付きで実行
pytest test/unit/core/test_rag_manager.py --cov=app.core.rag_manager --cov-report=term-missing -v

# セキュリティマーカーで実行
# pyproject.toml: markers = ["security: セキュリティ関連テスト"]
pytest test/unit/core/test_rag_manager.py -m "security" -v

# 非同期テストのみ実行
pytest test/unit/core/test_rag_manager.py -k "async" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 14 | RAG-001 〜 RAG-014 |
| 異常系 | 7 | RAG-E01 〜 RAG-E07 |
| セキュリティ | 3 | RAG-SEC-01 〜 RAG-SEC-03 |
| **合計** | **24** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestRAGManagerImport` | RAG-001 | 1 |
| `TestRAGManagerGetInstance` | RAG-002〜RAG-003 | 2 |
| `TestRAGManagerInitialize` | RAG-004〜RAG-006 | 3 |
| `TestRAGManagerGetEnhancedRAGSearch` | RAG-007〜RAG-008 | 2 |
| `TestRAGManagerIsInitialized` | RAG-009〜RAG-010 | 2 |
| `TestRAGManagerHealthCheck` | RAG-011 | 1 |
| `TestGlobalFunctions` | RAG-012〜RAG-014 | 3 |
| `TestRAGManagerInitializeErrors` | RAG-E01〜RAG-E03 | 3 |
| `TestRAGManagerHealthCheckErrors` | RAG-E04〜RAG-E06 | 3 |
| `TestGlobalFunctionsErrors` | RAG-E07 | 1 |
| `TestRAGManagerSecurity` | RAG-SEC-01〜RAG-SEC-03 | 3 |

### 実装失敗が予想されるテスト

以下のテストは現在の実装では**意図的に失敗**します。実装側の修正が必要です。

| テストID | 失敗理由 | 修正方針 |
|---------|---------|---------|
| RAG-SEC-01 | `rag_manager.py:69` で例外メッセージがそのままログに出力される | ログ出力時のサニタイズ処理を追加 |

> **推奨事項**: 認証情報やAPIキーが例外メッセージに含まれる可能性があるため、
> ログ出力時のサニタイズ処理の追加を検討してください。

### 注意事項

- `pytest-asyncio` パッケージが必要です
- `@pytest.mark.security` マーカーを `pyproject.toml` に登録してください
- `EnhancedRAGSearch` クラスは `app.rag.enhanced_rag_search` モジュールに存在します
- シングルトンパターンのため、テスト間の独立性確保にはモジュールキャッシュのクリアが必須です

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | EnhancedRAGSearch実接続テストはモックのみ | 実際の接続動作は未検証 | 統合テストで補完 |
| 2 | シングルトンパターンによるテスト分離の困難さ | 並列テスト実行時に競合の可能性 | autouseフィクスチャでリセット |
| 3 | ログへの例外メッセージ出力 | 機密情報漏洩のリスク | サニタイズ処理の追加を推奨 |
