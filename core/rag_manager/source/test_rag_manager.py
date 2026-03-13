# -*- coding: utf-8 -*-
"""
rag_manager.py 単元測試

テスト規格: docs/testing/core/rag_manager_tests.md
カバレッジ目標: 75%+

テスト類別:
  - 正常系: 14 個測試
  - 異常系: 7 個測試
  - 安全測試: 3 個測試

RAGクライアントのグローバル管理システムの単元テストです。
シングルトンパターンとdouble-checked lockingの動作を検証します。
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# プロジェクトルートを Python パスに追加
# プロジェクトのルートディレクトリを Python パスに追加する
project_root = Path(__file__).parent.parent.parent.parent / "platform_python_backend-testing"
sys.path.insert(0, str(project_root))


# =============================================================================
# 正常系テスト | Normal Case Tests
# =============================================================================

class TestRAGManagerImport:
    """
    RAGマネージャーモジュールインポートテスト

    テストID: RAG-001
    """

    def test_import_rag_manager_module(self):
        """
        RAG-001: モジュールのインポート成功

        テスト目的:
          - rag_manager モジュールが正常にインポートできることを確認
          - 必要なクラスと関数が存在することを確認
          - グローバル変数が定義されていることを確認
        """
        # Arrange - インポートテストのため事前準備なし
        # Act - モジュールをインポート
        from app.core import rag_manager

        # Assert - クラスが存在することを確認
        assert hasattr(rag_manager, "RAGManager"), "RAGManagerクラスが存在しない"

        # Assert - 関数が存在することを確認
        assert hasattr(rag_manager, "get_global_rag_manager"), "get_global_rag_manager関数が存在しない"
        assert hasattr(rag_manager, "initialize_global_rag_system"), "initialize_global_rag_system関数が存在しない"
        assert hasattr(rag_manager, "get_enhanced_rag_search"), "get_enhanced_rag_search関数が存在しない"

        # Assert - グローバル変数が存在することを確認
        assert hasattr(rag_manager, "_global_rag_manager"), "_global_rag_manager変数が存在しない"


class TestRAGManagerGetInstance:
    """
    シングルトンインスタンス取得テスト

    テストID: RAG-002 ~ RAG-003
    """

    @pytest.mark.asyncio
    async def test_get_instance_returns_rag_manager(self):
        """
        RAG-002: シングルトンインスタンス取得成功

        覆盖代码行: rag_manager.py:29-36

        テスト目的:
          - get_instance()がRAGManagerインスタンスを返すことを確認
          - インスタンスがNoneでないことを確認
        """
        # Arrange - RAGManagerクラスをインポート
        from app.core.rag_manager import RAGManager

        # Act - インスタンスを取得
        instance = await RAGManager.get_instance()

        # Assert - インスタンスが正しく取得できる
        assert instance is not None, "インスタンスがNoneです"
        assert isinstance(instance, RAGManager), "インスタンスがRAGManager型ではない"

    @pytest.mark.asyncio
    async def test_get_instance_returns_same_instance(self):
        """
        RAG-003: シングルトン一貫性（同一インスタンス返却）

        覆盖代码行: rag_manager.py:33-36

        テスト目的:
          - 複数回呼び出しても同じインスタンスが返されることを確認
          - シングルトンパターンが正しく実装されていることを確認
        """
        # Arrange - RAGManagerクラスをインポート
        from app.core.rag_manager import RAGManager

        # Act - インスタンスを2回取得
        first_instance = await RAGManager.get_instance()
        second_instance = await RAGManager.get_instance()

        # Assert - 同一インスタンスであることを確認
        assert first_instance is second_instance, "インスタンスが一致しません（シングルトン違反）"


class TestRAGManagerInitialize:
    """
    RAGシステム初期化テスト

    テストID: RAG-004 ~ RAG-006
    """

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """
        RAG-004: 初期化成功

        覆盖代码行: rag_manager.py:38-70

        テスト目的:
          - EnhancedRAGSearchの初期化が成功することを確認
          - _initializedフラグがTrueになることを確認
          - enhanced_rag_searchがセットされることを確認
        """
        # Arrange - EnhancedRAGSearchのモックを準備
        mock_enhanced_rag = MagicMock()
        mock_enhanced_rag.initialize = AsyncMock(return_value=True)

        with patch(
            "app.rag.enhanced_rag_search.EnhancedRAGSearch",
            return_value=mock_enhanced_rag
        ):
            from app.core.rag_manager import RAGManager
            manager = RAGManager()

            # Act - 初期化を実行
            result = await manager.initialize()

            # Assert - 初期化が成功している
            assert result is True, "初期化がTrueを返さない"
            assert manager._initialized is True, "_initializedフラグがTrueになっていない"
            assert manager.enhanced_rag_search is mock_enhanced_rag, "enhanced_rag_searchがセットされていない"

    @pytest.mark.asyncio
    async def test_initialize_already_initialized_returns_true(self):
        """
        RAG-005: 初期化済み状態で再度initializeはTrue即返却

        覆盖代码行: rag_manager.py:43-44

        テスト目的:
          - 既に初期化済みの場合、即座にTrueを返すことを確認
          - 二重初期化を防ぐロジックが機能することを確認
        """
        # Arrange - 初期化済みのマネージャーを準備
        from app.core.rag_manager import RAGManager
        manager = RAGManager()
        manager._initialized = True

        # Act - 再度初期化を試行
        result = await manager.initialize()

        # Assert - 即座にTrueを返す
        assert result is True, "初期化済み状態でTrueを返さない"

    @pytest.mark.asyncio
    async def test_initialize_double_checked_locking(self):
        """
        RAG-006: double-checked locking動作確認

        覆盖代码行: rag_manager.py:48-49

        テスト目的:
          - 並行して初期化が試行されても1回のみ実行されることを確認
          - double-checked lockingパターンが正しく機能することを確認
        """
        # Arrange - 初期化回数とインスタンス数をカウントするモック
        init_call_count = 0
        instance_count = 0

        class MockEnhancedRAGSearch:
            """初期化回数をカウントするモッククラス"""

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

            # Assert - すべてTrueを返す
            assert all(results), "並行初期化で全てTrueを返さない"
            # Assert - インスタンス化は1回のみ
            assert instance_count == 1, f"EnhancedRAGSearchインスタンスは1回のみ作成されるべき（実際: {instance_count}回）"
            # Assert - 初期化メソッドも1回のみ実行
            assert init_call_count == 1, f"initialize()は1回のみ実行されるべき（実際: {init_call_count}回）"


class TestRAGManagerGetEnhancedRAGSearch:
    """
    強化版RAG検索システム取得テスト

    テストID: RAG-007 ~ RAG-008
    """

    @pytest.mark.asyncio
    async def test_get_enhanced_rag_search_success(self):
        """
        RAG-007: 初期化済み状態でRAG検索システム取得成功

        覆盖代码行: rag_manager.py:72-81

        テスト目的:
          - 初期化済み状態でenhanced_rag_searchが取得できることを確認
        """
        # Arrange - 初期化済みのマネージャーを準備
        mock_enhanced_rag = MagicMock()

        from app.core.rag_manager import RAGManager
        manager = RAGManager()
        manager._initialized = True
        manager.enhanced_rag_search = mock_enhanced_rag

        # Act - RAG検索システムを取得
        result = await manager.get_enhanced_rag_search()

        # Assert - モックが返される
        assert result is mock_enhanced_rag, "enhanced_rag_searchが正しく返されない"

    @pytest.mark.asyncio
    async def test_get_enhanced_rag_search_auto_initialize(self):
        """
        RAG-008: 未初期化状態で自動初期化後にインスタンス返却

        覆盖代码行: rag_manager.py:76-79

        テスト目的:
          - 未初期化状態でも自動的に初期化が実行されることを確認
          - 初期化後にenhanced_rag_searchが返されることを確認
        """
        # Arrange - EnhancedRAGSearchのモックを準備
        mock_enhanced_rag = MagicMock()
        mock_enhanced_rag.initialize = AsyncMock(return_value=True)

        with patch(
            "app.rag.enhanced_rag_search.EnhancedRAGSearch",
            return_value=mock_enhanced_rag
        ):
            from app.core.rag_manager import RAGManager
            manager = RAGManager()
            assert manager._initialized is False, "初期状態で既に初期化されている"

            # Act - RAG検索システムを取得（自動初期化）
            result = await manager.get_enhanced_rag_search()

            # Assert - モックが返される
            assert result is mock_enhanced_rag, "自動初期化後にenhanced_rag_searchが返されない"
            # Assert - 初期化フラグが立っている
            assert manager._initialized is True, "自動初期化後に_initializedがTrueになっていない"


class TestRAGManagerIsInitialized:
    """
    初期化状態確認テスト

    テストID: RAG-009 ~ RAG-010
    """

    def test_is_initialized_false_initially(self):
        """
        RAG-009: 初期状態でFalse

        覆盖代码行: rag_manager.py:83-87

        テスト目的:
          - 初期状態でis_initialized()がFalseを返すことを確認
        """
        # Arrange - 新しいマネージャーを作成
        from app.core.rag_manager import RAGManager
        manager = RAGManager()

        # Act - 初期化状態を確認
        result = manager.is_initialized()

        # Assert - Falseを返す
        assert result is False, "初期状態でis_initialized()がFalseを返さない"

    def test_is_initialized_true_after_init(self):
        """
        RAG-010: 初期化後でTrue

        覆盖代码行: rag_manager.py:83-87

        テスト目的:
          - 初期化後にis_initialized()がTrueを返すことを確認
        """
        # Arrange - 初期化済みのマネージャーを準備
        from app.core.rag_manager import RAGManager
        manager = RAGManager()
        manager._initialized = True

        # Act - 初期化状態を確認
        result = manager.is_initialized()

        # Assert - Trueを返す
        assert result is True, "初期化後にis_initialized()がTrueを返さない"


class TestRAGManagerHealthCheck:
    """
    ヘルスチェックテスト

    テストID: RAG-011
    """

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """
        RAG-011: 初期化済み状態でヘルスチェック成功

        覆盖代码行: rag_manager.py:101-107

        テスト目的:
          - 初期化済み状態でヘルスチェックが成功することを確認
          - RAGシステムのヘルス情報が正しく返されることを確認
        """
        # Arrange - ヘルス情報を返すモックを準備
        mock_health_info = {"opensearch": "healthy", "embedding": "healthy"}
        mock_enhanced_rag = MagicMock()
        mock_enhanced_rag.get_health = AsyncMock(return_value=mock_health_info)

        from app.core.rag_manager import RAGManager
        manager = RAGManager()
        manager._initialized = True
        manager.enhanced_rag_search = mock_enhanced_rag

        # Act - ヘルスチェックを実行
        result = await manager.health_check()

        # Assert - ヘルスチェック結果が正しい
        assert result["status"] == "healthy", "ステータスが'healthy'ではない"
        assert result["initialized"] is True, "initializedがTrueではない"
        assert result["rag_health"] == mock_health_info, "rag_healthが期待値と一致しない"


class TestGlobalFunctions:
    """
    グローバル関数テスト

    テストID: RAG-012 ~ RAG-014
    """

    @pytest.mark.asyncio
    async def test_get_global_rag_manager(self):
        """
        RAG-012: グローバルマネージャー取得成功

        覆盖代码行: rag_manager.py:128-134

        テスト目的:
          - get_global_rag_manager()がRAGManagerインスタンスを返すことを確認
        """
        # Arrange - 関数をインポート
        from app.core.rag_manager import get_global_rag_manager, RAGManager

        # Act - グローバルマネージャーを取得
        manager = await get_global_rag_manager()

        # Assert - RAGManagerインスタンスが返される
        assert manager is not None, "マネージャーがNoneです"
        assert isinstance(manager, RAGManager), "マネージャーがRAGManager型ではない"

    @pytest.mark.asyncio
    async def test_initialize_global_rag_system_success(self):
        """
        RAG-013: グローバルシステム初期化成功

        覆盖代码行: rag_manager.py:137-148

        テスト目的:
          - initialize_global_rag_system()が成功することを確認
        """
        # Arrange - EnhancedRAGSearchのモックを準備
        mock_enhanced_rag = MagicMock()
        mock_enhanced_rag.initialize = AsyncMock(return_value=True)

        with patch(
            "app.rag.enhanced_rag_search.EnhancedRAGSearch",
            return_value=mock_enhanced_rag
        ):
            from app.core.rag_manager import initialize_global_rag_system

            # Act - グローバルシステムを初期化
            result = await initialize_global_rag_system()

            # Assert - 初期化が成功している
            assert result is True, "グローバルシステム初期化がTrueを返さない"

    @pytest.mark.asyncio
    async def test_module_level_get_enhanced_rag_search(self):
        """
        RAG-014: DI用get_enhanced_rag_search成功

        覆盖代码行: rag_manager.py:151-156

        テスト目的:
          - モジュールレベルのget_enhanced_rag_search()が機能することを確認
          - FastAPI依存性注入で使用できることを確認
        """
        # Arrange - EnhancedRAGSearchのモックを準備
        mock_enhanced_rag = MagicMock()
        mock_enhanced_rag.initialize = AsyncMock(return_value=True)

        with patch(
            "app.rag.enhanced_rag_search.EnhancedRAGSearch",
            return_value=mock_enhanced_rag
        ):
            from app.core.rag_manager import get_enhanced_rag_search

            # Act - RAG検索システムを取得
            result = await get_enhanced_rag_search()

            # Assert - モックが返される
            assert result is mock_enhanced_rag, "DI用関数がenhanced_rag_searchを返さない"


# =============================================================================
# 異常系テスト | Error Case Tests
# =============================================================================

class TestRAGManagerInitializeErrors:
    """
    RAGシステム初期化エラーテスト

    テストID: RAG-E01 ~ RAG-E03
    """

    @pytest.mark.asyncio
    async def test_initialize_rag_returns_false(self, caplog):
        """
        RAG-E01: EnhancedRAGSearch初期化がFalseを返す

        覆盖代码行: rag_manager.py:64-66

        テスト目的:
          - EnhancedRAGSearchの初期化がFalseを返した場合の処理を確認
          - エラーログが出力されることを確認
        """
        # Arrange - 初期化失敗を返すモックを準備
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

            # Act - 初期化を試行
            result = await manager.initialize()

            # Assert - 初期化が失敗している
            assert result is False, "初期化失敗時にFalseを返さない"
            assert manager._initialized is False, "初期化失敗後に_initializedがTrueになっている"
            # Assert - エラーログが出力されている
            assert "初期化に失敗" in caplog.text, "エラーログに'初期化に失敗'が含まれていない"

    @pytest.mark.asyncio
    async def test_initialize_exception(self, caplog):
        """
        RAG-E02: 初期化中に例外が発生

        覆盖代码行: rag_manager.py:68-70

        テスト目的:
          - 初期化中に例外が発生した場合の処理を確認
          - 例外がキャッチされてFalseが返されることを確認
        """
        # Arrange - 例外を発生させるモックを準備
        with patch(
            "app.rag.enhanced_rag_search.EnhancedRAGSearch",
            side_effect=ImportError("Module not found")
        ):
            import logging
            caplog.set_level(logging.ERROR)
            from app.core.rag_manager import RAGManager
            manager = RAGManager()

            # Act - 初期化を試行
            result = await manager.initialize()

            # Assert - 例外がキャッチされてFalseを返す
            assert result is False, "例外発生時にFalseを返さない"
            assert manager._initialized is False, "例外発生後に_initializedがTrueになっている"
            # Assert - エラーログが出力されている
            assert "初期化エラー" in caplog.text, "エラーログに'初期化エラー'が含まれていない"

    @pytest.mark.asyncio
    async def test_get_enhanced_rag_search_init_failure(self):
        """
        RAG-E03: get_enhanced_rag_search自動初期化失敗でRuntimeError

        覆盖代码行: rag_manager.py:78-79

        テスト目的:
          - 自動初期化が失敗した場合にRuntimeErrorが発生することを確認
        """
        # Arrange - 初期化失敗を返すモックを準備
        mock_enhanced_rag = MagicMock()
        mock_enhanced_rag.initialize = AsyncMock(return_value=False)

        with patch(
            "app.rag.enhanced_rag_search.EnhancedRAGSearch",
            return_value=mock_enhanced_rag
        ):
            from app.core.rag_manager import RAGManager
            manager = RAGManager()

            # Act & Assert - RuntimeErrorが発生する
            with pytest.raises(RuntimeError, match="初期化されていません"):
                await manager.get_enhanced_rag_search()


class TestRAGManagerHealthCheckErrors:
    """
    ヘルスチェックエラーテスト

    テストID: RAG-E04 ~ RAG-E06
    """

    @pytest.mark.asyncio
    async def test_health_check_uninitialized(self):
        """
        RAG-E04: 未初期化状態でヘルスチェック

        覆盖代码行: rag_manager.py:93-98

        テスト目的:
          - 未初期化状態でのヘルスチェック結果を確認
        """
        # Arrange - 未初期化のマネージャーを準備
        from app.core.rag_manager import RAGManager
        manager = RAGManager()
        assert manager._initialized is False, "初期状態で既に初期化されている"

        # Act - ヘルスチェックを実行
        result = await manager.health_check()

        # Assert - 未初期化エラーを返す
        assert result["status"] == "uninitialized", "ステータスが'uninitialized'ではない"
        assert result["initialized"] is False, "initializedがFalseではない"
        assert "初期化されていません" in result["error"], "エラーメッセージに'初期化されていません'が含まれていない"

    @pytest.mark.asyncio
    async def test_health_check_no_rag_search(self):
        """
        RAG-E05: enhanced_rag_searchがNoneの状態でヘルスチェック

        覆盖代码行: rag_manager.py:108-113

        テスト目的:
          - enhanced_rag_searchがNoneの場合のエラーハンドリングを確認
        """
        # Arrange - enhanced_rag_searchがNoneのマネージャーを準備
        from app.core.rag_manager import RAGManager
        manager = RAGManager()
        manager._initialized = True
        manager.enhanced_rag_search = None

        # Act - ヘルスチェックを実行
        result = await manager.health_check()

        # Assert - エラーを返す
        assert result["status"] == "error", "ステータスが'error'ではない"
        assert result["initialized"] is False, "initializedがFalseではない"
        assert "利用できません" in result["error"], "エラーメッセージに'利用できません'が含まれていない"

    @pytest.mark.asyncio
    async def test_health_check_exception(self, caplog):
        """
        RAG-E06: ヘルスチェック中に例外が発生

        覆盖代码行: rag_manager.py:114-120

        テスト目的:
          - ヘルスチェック中に例外が発生した場合のエラーハンドリングを確認
        """
        # Arrange - 例外を発生させるモックを準備
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

        # Act - ヘルスチェックを実行
        result = await manager.health_check()

        # Assert - 例外情報を含むエラーを返す
        assert result["status"] == "error", "ステータスが'error'ではない"
        assert result["initialized"] is True, "initializedがTrueではない"
        assert "Connection refused" in result["error"], "エラーメッセージに例外内容が含まれていない"
        # Assert - エラーログが出力されている
        assert "ヘルスチェックエラー" in caplog.text, "エラーログに'ヘルスチェックエラー'が含まれていない"


class TestGlobalFunctionsErrors:
    """
    グローバル関数エラーテスト

    テストID: RAG-E07
    """

    @pytest.mark.asyncio
    async def test_initialize_global_rag_system_exception(self, caplog):
        """
        RAG-E07: グローバル初期化中に例外が発生

        覆盖代码行: rag_manager.py:145-147

        テスト目的:
          - グローバル初期化中の例外がキャッチされることを確認
          - エラーログが出力されることを確認
        """
        # Arrange - 例外を発生させるモックを準備
        with patch(
            "app.core.rag_manager.get_global_rag_manager",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Manager creation failed")
        ):
            import logging
            caplog.set_level(logging.ERROR)
            from app.core.rag_manager import initialize_global_rag_system

            # Act - グローバル初期化を試行
            result = await initialize_global_rag_system()

            # Assert - 例外がキャッチされてFalseを返す
            assert result is False, "例外発生時にFalseを返さない"
            # Assert - エラーログが出力されている
            assert "グローバルRAGシステム初期化エラー" in caplog.text, "エラーログに期待される内容が含まれていない"


# =============================================================================
# セキュリティテスト | Security Tests
# =============================================================================

@pytest.mark.security
class TestRAGManagerSecurity:
    """
    RAGマネージャーセキュリティテスト

    テストID: RAG-SEC-01 ~ RAG-SEC-03
    """

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="実装側でログのサニタイズ処理が未実装のため、機密情報が漏洩する", strict=True)
    async def test_error_log_no_sensitive_info(self, caplog):
        """
        RAG-SEC-01: エラーログに機密情報が含まれない

        覆盖代码行: rag_manager.py:69

        【実装失敗予定】

        テスト目的:
          - 初期化エラー時のログに認証情報やAPIキーが含まれないことを検証
          - 現在の実装では例外メッセージがそのままログに出力されるため失敗する

        推奨事項:
          - ログ出力時のサニタイズ処理を追加すること
        """
        # Arrange - 認証情報を含む例外をシミュレート
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

            # Act - 初期化を試行（エラー発生）
            await manager.initialize()

            # Assert - エラーログが出力されている
            log_text = caplog.text.lower()
            assert "初期化エラー" in caplog.text, "エラーログが出力されていない"

            # Assert - 機密情報がログに含まれていない（現在の実装では失敗）
            assert "sk-secret-key" not in log_text, "❌ APIキーがログに漏洩しています"
            assert "super_secret" not in log_text, "❌ パスワードがログに漏洩しています"

    @pytest.mark.asyncio
    async def test_health_check_no_stack_trace_leak(self):
        """
        RAG-SEC-02: ヘルスチェック結果に内部エラー詳細が漏洩しない

        覆盖代码行: rag_manager.py:114-120

        テスト目的:
          - ヘルスチェック結果にスタックトレースや内部実装の詳細が含まれないことを検証
          - 例外メッセージは含まれても良いが、スタックトレースは含まれるべきでない
        """
        # Arrange - 詳細なエラーを発生させるモックを準備
        detailed_error = ValueError(
            "Internal error at line 123: database connection pool exhausted"
        )
        mock_enhanced_rag = MagicMock()
        mock_enhanced_rag.get_health = AsyncMock(side_effect=detailed_error)

        from app.core.rag_manager import RAGManager
        manager = RAGManager()
        manager._initialized = True
        manager.enhanced_rag_search = mock_enhanced_rag

        # Act - ヘルスチェックを実行
        result = await manager.health_check()

        # Assert - エラーステータスを返す
        error_message = result.get("error", "")
        assert result["status"] == "error", "ステータスが'error'ではない"

        # Assert - スタックトレースが含まれていない
        assert "Traceback" not in error_message, "❌ スタックトレースが漏洩しています"
        assert "File " not in error_message, "❌ ファイルパス情報が漏洩しています"

    @pytest.mark.asyncio
    async def test_singleton_thread_safety(self):
        """
        RAG-SEC-03: シングルトンのスレッドセーフ性

        覆盖代码行: rag_manager.py:29-36

        テスト目的:
          - 並行アクセス時に競合状態が発生しないことを確認
          - 全てのアクセスで同一インスタンスが返されることを確認
        """
        # Arrange - RAGManagerクラスをインポート
        from app.core.rag_manager import RAGManager

        # Act - 多数の並行アクセスを実行
        tasks = [RAGManager.get_instance() for _ in range(100)]
        instances = await asyncio.gather(*tasks)

        # Assert - すべて同一インスタンス
        first_instance = instances[0]
        for i, instance in enumerate(instances[1:], start=1):
            assert instance is first_instance, f"インスタンス{i}が一致しません（競合状態発生）"
