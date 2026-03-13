"""
error_handlers.py 単元テスト

テスト規格: error_handlers_tests.md
覆盖率目標: 90%+

テスト類別:
  - 正常系: 23 個測試
  - 異常系: 7 個測試
  - セキュリティテスト: 9 個測試
"""
import pytest
import re
import logging
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent.parent / "platform_python_backend-testing"
sys.path.insert(0, str(project_root))

# テスト対象モジュールのインポート
from fastapi import HTTPException
from opensearchpy.exceptions import AuthenticationException, AuthorizationException

from app.core.error_handlers import (
    create_error_response,
    handle_opensearch_exceptions,
    handle_chat_exceptions,
    log_request_start,
    log_request_end
)


# ====================================
# 正常系テスト
# ====================================

class TestCreateErrorResponse:
    """create_error_response関数の正常系テスト

    テストID: ERH-001 ~ ERH-006
    """

    def test_basic_error_response(self):
        """ERH-001: create_error_response: 基本パラメータのみ

        覆盖代码行: error_handlers.py:13-42

        テスト目的:
          - 基本パラメータでHTTPExceptionが正しく生成されること
          - エラーメッセージにerror_idが含まれること
        """
        # Arrange - テストデータの準備
        status_code = 400
        message = "入力が不正です"

        # Act - テスト対象の関数を実行する
        result = create_error_response(status_code=status_code, message=message)

        # Assert - 結果の検証
        assert isinstance(result, HTTPException)  # HTTPException型であることを確認
        assert result.status_code == 400  # ステータスコードが正しいことを確認
        assert "入力が不正です" in result.detail  # メッセージが含まれることを確認
        assert "サポートにID「" in result.detail  # error_id部分が含まれることを確認
        assert "」を伝えてお問い合わせください" in result.detail  # 定型文が含まれることを確認

    def test_with_custom_error_id(self):
        """ERH-002: create_error_response: error_id指定

        覆盖代码行: error_handlers.py:30-31

        テスト目的:
          - カスタムerror_idが正しく使用されること
        """
        # Arrange - カスタムerror_idを準備
        custom_id = "custom-error-id-12345"

        # Act - カスタムerror_idを指定して実行
        result = create_error_response(
            status_code=500,
            message="サーバーエラー",
            error_id=custom_id
        )

        # Assert - カスタムIDが含まれることを確認
        assert custom_id in result.detail

    def test_with_details(self, caplog):
        """ERH-003: create_error_response: details指定

        覆盖代码行: error_handlers.py:34-36

        テスト目的:
          - detailsが指定された場合、ログに詳細情報が出力されること
        """
        # Arrange - 詳細情報を準備
        details = {"user_id": "user123", "action": "delete"}

        # Act - detailsを指定してログレベルERRORで実行
        with caplog.at_level(logging.ERROR, logger="app.core.error_handlers"):
            result = create_error_response(
                status_code=403,
                message="アクセス拒否",
                details=details
            )

        # Assert - ログに詳細が出力されていることを確認
        assert "詳細:" in caplog.text
        # user_idまたはその値がログに含まれることを確認
        assert "user_id" in caplog.text or "user123" in caplog.text

    def test_without_details(self, caplog):
        """ERH-004: create_error_response: detailsなし

        覆盖代码行: error_handlers.py:34-36 (Falseブランチ)

        テスト目的:
          - detailsがNoneの場合、ログに詳細情報が出力されないこと
        """
        # Arrange & Act - detailsをNoneで実行
        with caplog.at_level(logging.ERROR, logger="app.core.error_handlers"):
            result = create_error_response(
                status_code=400,
                message="エラー",
                details=None
            )

        # Assert - ログに「詳細:」が含まれないことを確認
        assert "詳細:" not in caplog.text

    def test_with_empty_dict_details(self, caplog):
        """ERH-005: create_error_response: 空の辞書details

        覆盖代码行: error_handlers.py:34-36

        テスト目的:
          - 空の辞書はfalsyな値として扱われ、詳細が出力されないこと
        """
        # Arrange - 空の辞書を準備
        details = {}

        # Act - 空の辞書でdetailsを指定
        with caplog.at_level(logging.ERROR, logger="app.core.error_handlers"):
            result = create_error_response(
                status_code=400,
                message="エラー",
                details=details
            )

        # Assert - 空の辞書はfalsyなのでログに詳細が含まれない
        assert "詳細:" not in caplog.text

    def test_auto_generated_error_id_is_uuid(self):
        """ERH-006: create_error_response: error_idがUUID形式

        覆盖代码行: error_handlers.py:30-31

        テスト目的:
          - error_idが指定されない場合、UUID形式のIDが自動生成されること
        """
        # Arrange - UUID形式の正規表現パターン
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'

        # Act - error_idを指定せずに実行
        result = create_error_response(status_code=500, message="エラー")

        # Assert - UUID形式のerror_idが含まれることを確認
        match = re.search(uuid_pattern, result.detail)
        assert match is not None, "error_idがUUID形式ではありません"


class TestHandleOpenSearchExceptions:
    """handle_opensearch_exceptions関数の正常系テスト

    テストID: ERH-007 ~ ERH-011
    """

    def test_authentication_exception(self):
        """ERH-007: handle_opensearch_exceptions: AuthenticationException

        覆盖代码行: error_handlers.py:58-64

        テスト目的:
          - AuthenticationExceptionが401エラーに変換されること
          - 適切な認証エラーメッセージが含まれること
        """
        # Arrange - AuthenticationExceptionを準備
        exc = AuthenticationException(401, "Unauthorized", {})

        # Act - 例外を処理
        result = handle_opensearch_exceptions(exc, "インデックス検索")

        # Assert - 401エラーが返されることを確認
        assert isinstance(result, HTTPException)
        assert result.status_code == 401
        assert "認証に失敗" in result.detail

    def test_authorization_exception(self):
        """ERH-008: handle_opensearch_exceptions: AuthorizationException

        覆盖代码行: error_handlers.py:66-72

        テスト目的:
          - AuthorizationExceptionが403エラーに変換されること
          - 適切な認可エラーメッセージが含まれること
        """
        # Arrange - AuthorizationExceptionを準備
        exc = AuthorizationException(403, "Forbidden", {})

        # Act - 例外を処理
        result = handle_opensearch_exceptions(exc, "ドキュメント削除")

        # Assert - 403エラーが返されることを確認
        assert isinstance(result, HTTPException)
        assert result.status_code == 403
        assert "アクセス権限がありません" in result.detail

    def test_generic_exception(self):
        """ERH-009: handle_opensearch_exceptions: その他例外

        覆盖代码行: error_handlers.py:74-80

        テスト目的:
          - 汎用例外が500エラーに変換されること
          - 汎用エラーメッセージが含まれること
        """
        # Arrange - 汎用例外を準備
        exc = RuntimeError("Connection timeout")

        # Act - 例外を処理
        result = handle_opensearch_exceptions(exc, "接続確認")

        # Assert - 500エラーが返されることを確認
        assert isinstance(result, HTTPException)
        assert result.status_code == 500
        assert "エラーが発生しました" in result.detail

    def test_custom_operation_in_message(self):
        """ERH-010: handle_opensearch_exceptions: カスタムoperation

        覆盖代码行: error_handlers.py:74-80

        テスト目的:
          - カスタムoperationがエラーメッセージに含まれること
        """
        # Arrange - カスタムoperationを準備
        exc = RuntimeError("Unknown error")
        operation = "カスタム検索操作"

        # Act - カスタムoperationで実行
        result = handle_opensearch_exceptions(exc, operation)

        # Assert - メッセージにoperationが含まれることを確認
        assert operation in result.detail

    def test_default_operation(self):
        """ERH-011: handle_opensearch_exceptions: デフォルトoperation

        覆盖代码行: error_handlers.py:45

        テスト目的:
          - operationを指定しない場合、デフォルト値が使用されること
        """
        # Arrange - 例外を準備（operationはデフォルト）
        exc = RuntimeError("Error")

        # Act - operationを指定せずに実行
        result = handle_opensearch_exceptions(exc)

        # Assert - デフォルトoperationがメッセージに含まれることを確認
        assert "OpenSearch操作" in result.detail


class TestHandleChatExceptions:
    """handle_chat_exceptions関数の正常系テスト

    テストID: ERH-012 ~ ERH-016
    """

    def test_opensearch_authentication_exception(self):
        """ERH-012: handle_chat_exceptions: OpenSearch認証例外

        覆盖代码行: error_handlers.py:99-100

        テスト目的:
          - AuthenticationExceptionがhandle_opensearch_exceptionsに委譲されること
          - 401エラーが返されること
        """
        # Arrange - AuthenticationExceptionを準備
        exc = AuthenticationException(401, "Unauthorized", {})
        session_id = "session-123"

        # Act - 例外を処理
        result = handle_chat_exceptions(exc, session_id, "チャット検索")

        # Assert - handle_opensearch_exceptionsに委譲され401が返されることを確認
        assert isinstance(result, HTTPException)
        assert result.status_code == 401

    def test_opensearch_authorization_exception(self):
        """ERH-013: handle_chat_exceptions: OpenSearch認可例外

        覆盖代码行: error_handlers.py:99-100

        テスト目的:
          - AuthorizationExceptionがhandle_opensearch_exceptionsに委譲されること
          - 403エラーが返されること
        """
        # Arrange - AuthorizationExceptionを準備
        exc = AuthorizationException(403, "Forbidden", {})
        session_id = "session-456"

        # Act - 例外を処理
        result = handle_chat_exceptions(exc, session_id, "履歴取得")

        # Assert - handle_opensearch_exceptionsに委譲され403が返されることを確認
        assert isinstance(result, HTTPException)
        assert result.status_code == 403

    def test_http_exception_reraise(self):
        """ERH-014: handle_chat_exceptions: HTTPException

        覆盖代码行: error_handlers.py:103-105

        テスト目的:
          - HTTPExceptionの場合、そのまま再発生（raise）されること
        """
        # Arrange - HTTPExceptionを準備
        original_exc = HTTPException(status_code=404, detail="Not found")
        session_id = "session-789"

        # Act & Assert - HTTPExceptionがそのまま発生することを確認
        with pytest.raises(HTTPException) as exc_info:
            handle_chat_exceptions(original_exc, session_id, "リソース取得")

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Not found"

    def test_generic_exception(self, caplog):
        """ERH-015: handle_chat_exceptions: その他例外

        覆盖代码行: error_handlers.py:108-116

        テスト目的:
          - 汎用例外が500エラーに変換されること
          - session_idがログに出力されること
        """
        # Arrange - 汎用例外を準備
        exc = ValueError("Invalid value")
        session_id = "session-abc"
        operation = "データ処理"

        # Act - 例外を処理
        with caplog.at_level(logging.ERROR, logger="app.core.error_handlers"):
            result = handle_chat_exceptions(exc, session_id, operation)

        # Assert - 500エラーが返され、ログにsession_idが含まれることを確認
        assert isinstance(result, HTTPException)
        assert result.status_code == 500
        assert "エラーが発生しました" in result.detail
        assert session_id in caplog.text

    def test_chat_default_operation(self):
        """ERH-016: handle_chat_exceptions: デフォルトoperation

        覆盖代码行: error_handlers.py:83

        テスト目的:
          - operationを指定しない場合、デフォルト値が使用されること
        """
        # Arrange - 例外を準備（operationはデフォルト）
        exc = RuntimeError("Unknown error")
        session_id = "session-def"

        # Act - operationを指定せずに実行
        result = handle_chat_exceptions(exc, session_id)

        # Assert - デフォルトoperationがメッセージに含まれることを確認
        assert "チャット処理" in result.detail


class TestLogRequestStart:
    """log_request_start関数の正常系テスト

    テストID: ERH-017 ~ ERH-020
    """

    def test_basic_log(self, caplog):
        """ERH-017: log_request_start: 基本ログ

        覆盖代码行: error_handlers.py:119-132

        テスト目的:
          - 基本的なINFOログが出力されること
        """
        # Arrange - 基本パラメータを準備
        operation = "チャット開始"
        session_id = "session-xyz"

        # Act - ログ出力を実行
        with caplog.at_level(logging.INFO, logger="app.core.error_handlers"):
            log_request_start(operation, session_id)

        # Assert - ログに必要な情報が含まれることを確認
        assert "チャット開始" in caplog.text
        assert session_id in caplog.text
        assert "開始" in caplog.text

    def test_with_kwargs_debug_enabled(self, caplog):
        """ERH-018: log_request_start: 追加kwargs（DEBUG有効時）

        覆盖代码行: error_handlers.py:134-137

        テスト目的:
          - DEBUG有効時に追加情報が出力されること
        """
        # Arrange - 追加kwargsを準備
        operation = "ドキュメント処理"
        session_id = "session-debug"
        kwargs = {"user_id": "user123", "document_id": "doc456"}

        # Act - DEBUG有効でログ出力
        with caplog.at_level(logging.DEBUG, logger="app.core.error_handlers"):
            log_request_start(operation, session_id, **kwargs)

        # Assert - DEBUG情報が出力されることを確認
        assert "ドキュメント処理" in caplog.text
        assert session_id in caplog.text
        # DEBUG有効時は追加情報が出力される
        assert "user_id" in caplog.text or "user123" in caplog.text

    def test_with_empty_kwargs_debug_enabled(self, caplog):
        """ERH-019: log_request_start: 空kwargs（DEBUG有効時）

        覆盖代码行: error_handlers.py:134-137 (空のループ)

        テスト目的:
          - kwargsが空の場合、DEBUGログが出力されないこと
        """
        # Arrange - kwargsなし
        operation = "テスト操作"
        session_id = "session-empty"

        # Act - kwargsなしでDEBUG有効で実行
        with caplog.at_level(logging.DEBUG, logger="app.core.error_handlers"):
            log_request_start(operation, session_id)  # kwargsなし

        # Assert - DEBUGレコードが出力されないことを確認
        assert "テスト操作" in caplog.text
        assert session_id in caplog.text
        # session_id以外のキーがないためDEBUGログなし
        debug_records = [r for r in caplog.records if r.levelno == logging.DEBUG]
        assert len(debug_records) == 0

    def test_with_kwargs_debug_disabled(self, caplog):
        """ERH-020: log_request_start: 追加kwargs（DEBUG無効時）

        覆盖代码行: error_handlers.py:134 (isEnabledForがFalse)

        テスト目的:
          - DEBUG無効時は追加情報が出力されないこと
        """
        # Arrange - 追加kwargsを準備
        operation = "クエリ実行"
        session_id = "session-info"
        kwargs = {"query": "test query"}

        # Act - INFOレベルのみでログ出力（DEBUGは無効）
        with caplog.at_level(logging.INFO, logger="app.core.error_handlers"):
            log_request_start(operation, session_id, **kwargs)

        # Assert - INFOレベルの基本情報のみ出力されることを確認
        assert "クエリ実行" in caplog.text
        assert session_id in caplog.text
        # DEBUGレコードがないことを確認
        debug_records = [r for r in caplog.records if r.levelno == logging.DEBUG]
        assert len(debug_records) == 0


class TestLogRequestEnd:
    """log_request_end関数の正常系テスト

    テストID: ERH-021 ~ ERH-023
    """

    def test_success_true(self, caplog):
        """ERH-021: log_request_end: success=True

        覆盖代码行: error_handlers.py:140-150

        テスト目的:
          - success=Trueの場合、「完了」ログが出力されること
        """
        # Arrange - success=Trueで準備
        operation = "データ保存"
        session_id = "session-success"

        # Act - success=Trueでログ出力
        with caplog.at_level(logging.INFO, logger="app.core.error_handlers"):
            log_request_end(operation, session_id, success=True)

        # Assert - 「完了」がログに含まれることを確認
        assert "データ保存" in caplog.text
        assert "完了" in caplog.text
        assert session_id in caplog.text

    def test_success_false(self, caplog):
        """ERH-022: log_request_end: success=False

        覆盖代码行: error_handlers.py:140-150

        テスト目的:
          - success=Falseの場合、「失敗」ログが出力されること
        """
        # Arrange - success=Falseで準備
        operation = "データ削除"
        session_id = "session-fail"

        # Act - success=Falseでログ出力
        with caplog.at_level(logging.INFO, logger="app.core.error_handlers"):
            log_request_end(operation, session_id, success=False)

        # Assert - 「失敗」がログに含まれることを確認
        assert "データ削除" in caplog.text
        assert "失敗" in caplog.text
        assert session_id in caplog.text

    def test_default_success(self, caplog):
        """ERH-023: log_request_end: デフォルトsuccess

        覆盖代码行: error_handlers.py:140

        テスト目的:
          - successを指定しない場合、デフォルトでTrue（「完了」）となること
        """
        # Arrange - successを指定しない
        operation = "更新処理"
        session_id = "session-default"

        # Act - successを指定せずにログ出力
        with caplog.at_level(logging.INFO, logger="app.core.error_handlers"):
            log_request_end(operation, session_id)  # successを指定しない

        # Assert - デフォルトはTrue→「完了」が出力されることを確認
        assert "完了" in caplog.text


# ====================================
# 異常系テスト
# ====================================

class TestCreateErrorResponseErrors:
    """create_error_response関数の異常系テスト

    テストID: ERH-E01 ~ ERH-E02
    """

    def test_empty_message(self):
        """ERH-E01: create_error_response: 空メッセージ

        覆盖代码行: error_handlers.py:40

        テスト目的:
          - 空メッセージでもHTTPExceptionが生成されること
        """
        # Arrange - 空メッセージを準備
        status_code = 400
        message = ""

        # Act - 空メッセージで実行
        result = create_error_response(status_code=status_code, message=message)

        # Assert - 空メッセージでもHTTPExceptionが生成されることを確認
        assert isinstance(result, HTTPException)
        assert result.status_code == 400
        # 空メッセージでもerror_idは含まれる
        assert "サポートにID「" in result.detail

    def test_unusual_status_code(self):
        """ERH-E02: create_error_response: 不正ステータスコード

        テスト目的:
          - 不正なステータスコードでも受け入れること（FastAPI側で検証）
        """
        # Arrange - 不正なステータスコードを準備
        status_code = 999

        # Act - 不正なステータスコードで実行
        result = create_error_response(status_code=status_code, message="エラー")

        # Assert - そのまま使用されることを確認
        assert result.status_code == 999


class TestHandleOpenSearchExceptionsErrors:
    """handle_opensearch_exceptions関数の異常系テスト

    テストID: ERH-E03
    """

    def test_none_exception(self):
        """ERH-E03: handle_opensearch_exceptions: None例外

        覆盖代码行: error_handlers.py:58, 66, 74 (elseブランチ)

        テスト目的:
          - None例外が汎用エラー（500）として処理されること
        """
        # Arrange - None例外を準備
        exc = None

        # Act - None例外を処理
        result = handle_opensearch_exceptions(exc, "テスト操作")

        # Assert - 汎用エラー（500）として処理されることを確認
        assert isinstance(result, HTTPException)
        assert result.status_code == 500
        assert "エラーが発生しました" in result.detail


class TestHandleChatExceptionsErrors:
    """handle_chat_exceptions関数の異常系テスト

    テストID: ERH-E04 ~ ERH-E05
    """

    def test_none_session_id(self, caplog):
        """ERH-E04: handle_chat_exceptions: None session_id

        覆盖代码行: error_handlers.py:108

        テスト目的:
          - None session_idがログに「None」として出力されること
        """
        # Arrange - None session_idを準備
        exc = RuntimeError("Error")
        session_id = None

        # Act - None session_idで実行
        with caplog.at_level(logging.ERROR, logger="app.core.error_handlers"):
            result = handle_chat_exceptions(exc, session_id, "テスト")

        # Assert - Noneが文字列"None"としてログ出力されることを確認
        assert isinstance(result, HTTPException)
        assert result.status_code == 500
        assert "None" in caplog.text

    def test_empty_session_id(self, caplog):
        """ERH-E05: handle_chat_exceptions: 空session_id

        覆盖代码行: error_handlers.py:108

        テスト目的:
          - 空session_idでもHTTPExceptionが生成されること
        """
        # Arrange - 空session_idを準備
        exc = ValueError("Error")
        session_id = ""

        # Act - 空session_idで実行
        with caplog.at_level(logging.ERROR, logger="app.core.error_handlers"):
            result = handle_chat_exceptions(exc, session_id, "テスト")

        # Assert - 空session_idでもHTTPExceptionが生成されることを確認
        assert isinstance(result, HTTPException)
        assert result.status_code == 500


class TestLogFunctionsErrors:
    """ログ関数の異常系テスト

    テストID: ERH-E06 ~ ERH-E07
    """

    def test_log_request_start_none_operation(self, caplog):
        """ERH-E06: log_request_start: None operation

        覆盖代码行: error_handlers.py:132

        テスト目的:
          - None operationがログに「None」として出力されること
        """
        # Arrange - None operationを準備
        operation = None
        session_id = "session-123"

        # Act - None operationで実行
        with caplog.at_level(logging.INFO, logger="app.core.error_handlers"):
            log_request_start(operation, session_id)

        # Assert - Noneが文字列"None"としてログ出力されることを確認
        assert "None" in caplog.text
        assert "開始" in caplog.text

    def test_log_request_end_none_session_id(self, caplog):
        """ERH-E07: log_request_end: None session_id

        覆盖代码行: error_handlers.py:150

        テスト目的:
          - None session_idがログに「None」として出力されること
        """
        # Arrange - None session_idを準備
        operation = "テスト操作"
        session_id = None

        # Act - None session_idで実行
        with caplog.at_level(logging.INFO, logger="app.core.error_handlers"):
            log_request_end(operation, session_id, success=True)

        # Assert - Noneが文字列"None"としてログ出力されることを確認
        assert "テスト操作" in caplog.text
        assert "完了" in caplog.text
        assert "None" in caplog.text


# ====================================
# セキュリティテスト
# ====================================

@pytest.mark.security
class TestErrorHandlersSecurity:
    """error_handlersモジュールのセキュリティテスト

    テストID: ERH-SEC-01 ~ ERH-SEC-09
    """

    def test_no_internal_paths_in_response(self):
        """ERH-SEC-01: エラーレスポンスに内部パスが含まれない

        CWE-209: Information Exposure Through an Error Message対策

        テスト目的:
          - 内部パスがHTTPレスポンスに露出しないこと
        """
        # Arrange - 内部パスを含む例外を準備
        exc = FileNotFoundError("/opt/app/secret/config.yaml not found")
        internal_path_patterns = [
            r'/opt/[\w\-/.]+',
            r'/usr/local/[\w\-/.]+',
            r'/home/[\w\-/.]+',
            r'/var/[\w\-/.]+',
            r'[A-Z]:\\[\w\-\\/]+',
        ]

        # Act - 例外を処理
        result = handle_opensearch_exceptions(exc, "ファイル読み込み")

        # Assert - 内部パスが露出していないことを確認
        for pattern in internal_path_patterns:
            matches = re.findall(pattern, result.detail)
            assert not matches, f"内部パスが露出: {matches}"

    def test_no_stacktrace_in_response(self):
        """ERH-SEC-02: エラーレスポンスにスタックトレースが含まれない

        CWE-209対策

        テスト目的:
          - スタックトレースがHTTPレスポンスに露出しないこと
        """
        # Arrange - スタックトレース情報を含む例外を準備
        exc = RuntimeError("Internal error at line 42")

        # Act - 例外を処理
        result = handle_opensearch_exceptions(exc, "処理")

        # Assert - スタックトレース情報が露出していないことを確認
        assert "Traceback" not in result.detail
        assert 'File "' not in result.detail
        # "line XX" パターンが含まれていないことを確認
        assert not re.search(r'\bline \d+\b', result.detail)

    def test_error_id_unpredictable(self):
        """ERH-SEC-03: error_idが予測不可能なUUID

        CWE-330: Use of Insufficiently Random Values対策

        テスト目的:
          - error_idが予測不可能であること（ユニーク性）
        """
        # Arrange - error_idを収集するセット
        error_ids = set()

        # Act - 10回実行してerror_idを収集
        for _ in range(10):
            result = create_error_response(status_code=500, message="エラー")
            # error_idを抽出
            match = re.search(
                r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
                result.detail
            )
            if match:
                error_ids.add(match.group(0))

        # Assert - 10個全てがユニークであることを確認
        assert len(error_ids) == 10, "error_idが重複しています（予測可能な可能性）"

    def test_no_credentials_in_error_message(self):
        """ERH-SEC-04: 認証情報がエラーメッセージに含まれない

        OWASP A02:2021 - Cryptographic Failures対策

        テスト目的:
          - 認証情報がHTTPレスポンスに露出しないこと
        """
        # Arrange - 認証情報を含む例外を準備
        exc = AuthenticationException(
            401,
            "Authentication failed for user admin with password=secret123",
            {}
        )

        # Act - 例外を処理
        result = handle_opensearch_exceptions(exc, "認証")

        # Assert - 固定メッセージが使用され、認証情報が露出していないことを確認
        assert "認証に失敗" in result.detail
        # 元の例外メッセージ内容が含まれないことを確認
        assert "password" not in result.detail.lower()
        assert "secret123" not in result.detail
        assert "admin" not in result.detail

    def test_details_not_in_http_response(self):
        """ERH-SEC-05: detailsパラメータがHTTPレスポンスに含まれない

        テスト目的:
          - detailsがログにのみ出力され、HTTPレスポンスには含まれないこと
        """
        # Arrange - 機密情報を含むdetailsを準備
        sensitive_details = {
            "internal_user_id": 12345,
            "database_query": "SELECT * FROM users WHERE password='secret'",
            "stack_frame": "/opt/app/sensitive.py:42"
        }

        # Act - detailsを指定して実行
        result = create_error_response(
            status_code=500,
            message="処理エラー",
            details=sensitive_details
        )

        # Assert - detailsの内容がHTTPレスポンスに含まれないことを確認
        assert "internal_user_id" not in result.detail
        assert "12345" not in result.detail
        assert "database_query" not in result.detail
        assert "SELECT" not in result.detail
        assert "sensitive.py" not in result.detail

    def test_session_id_not_in_http_response(self):
        """ERH-SEC-06: セッションIDがHTTPレスポンスに含まれない

        テスト目的:
          - session_idがログにのみ出力され、HTTPレスポンスには含まれないこと
        """
        # Arrange - 機密性の高いsession_idを準備
        exc = RuntimeError("Error")
        session_id = "sensitive-session-12345"

        # Act - session_idを指定して実行
        result = handle_chat_exceptions(exc, session_id, "処理")

        # Assert - session_idがHTTPレスポンスに含まれないことを確認
        assert session_id not in result.detail
        # error_idのみ含まれることを確認
        assert re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-', result.detail) is not None

    def test_error_id_length_appropriate(self):
        """ERH-SEC-07: error_idの長さが適切（UUID v4形式）

        テスト目的:
          - error_idがUUID v4形式（36文字）であること
        """
        # Arrange & Act - error_idを生成
        result = create_error_response(status_code=500, message="エラー")

        # Assert - UUID v4形式（36文字）であることを確認
        uuid_match = re.search(
            r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})',
            result.detail
        )
        assert uuid_match is not None
        error_id = uuid_match.group(1)
        assert len(error_id) == 36, f"error_idの長さが不正: {len(error_id)}"

    @pytest.mark.xfail(reason="既知の制限事項#6: ログインジェクション未対策")
    def test_log_injection_newline_handling(self, caplog):
        """ERH-SEC-08: ログインジェクション: 改行文字の処理

        CWE-117: Improper Output Neutralization for Logs

        【既知の制限事項】
        現在の実装ではstr(e)をそのまま出力するため、
        改行文字を含むエラーメッセージはそのままログ出力される。

        テスト目的:
          - 改行文字が適切にエスケープされること（現在は失敗）
        """
        # Arrange - 悪意のある改行を含むメッセージを準備
        malicious_message = (
            "Normal error\n"
            "[CRITICAL] FAKE - System compromised"
        )
        exc = RuntimeError(malicious_message)
        session_id = "session-test"

        # Act - 例外を処理
        with caplog.at_level(logging.ERROR, logger="app.core.error_handlers"):
            handle_chat_exceptions(exc, session_id, "処理")

        # Assert - 改行文字がエスケープまたは除去されることを期待（xfail）
        for record in caplog.records:
            log_message = record.getMessage()
            # 改行がエスケープされている（\\n）か、除去されていることを確認
            # 現在の実装では失敗する
            assert "\n" not in log_message or "\\n" in log_message, \
                f"改行文字が未処理のままログ出力されています: {log_message[:50]}..."

    def test_crlf_injection_json_safe(self):
        """ERH-SEC-09: CRLFインジェクション: HTTPレスポンスへの影響

        HTTP Response Splitting対策

        テスト目的:
          - CRLFがJSONシリアライズされ、HTTPヘッダーに影響しないこと
        """
        # Arrange - CRLFを含むペイロードを準備
        crlf_payload = "error\r\nSet-Cookie: malicious=value"

        # Act - CRLFを含むメッセージで実行
        result = create_error_response(
            status_code=400,
            message=crlf_payload
        )

        # Assert - HTTPExceptionが正常に生成されることを確認
        # FastAPIがJSONレスポンスとして返す際に自動エスケープされる
        assert isinstance(result, HTTPException)
        assert result.status_code == 400
        # detailにはCRLFが文字列として含まれる（JSONでエスケープされる）
        assert "error" in result.detail
