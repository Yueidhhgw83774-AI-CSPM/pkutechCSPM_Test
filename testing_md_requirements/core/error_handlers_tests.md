# error_handlers テストケース

## 1. 概要

エラーハンドリングに関する共通関数を提供するモジュールのテストケースを定義します。標準化されたエラーレスポンス作成、OpenSearch/チャット処理の例外変換、リクエストログ出力を担当します。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `create_error_response()` | 標準化されたHTTPExceptionを作成（エラーID付き） |
| `handle_opensearch_exceptions()` | OpenSearch関連例外を適切なHTTPExceptionに変換 |
| `handle_chat_exceptions()` | チャット処理例外を適切なHTTPExceptionに変換 |
| `log_request_start()` | リクエスト開始をログ出力 |
| `log_request_end()` | リクエスト終了をログ出力 |

### 1.2 カバレッジ目標: 90%

> **注記**: エラーハンドリングはシステム全体の信頼性に直結する基盤機能であり、高いカバレッジが必要。全分岐パスのテストが重要。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/core/error_handlers.py` |
| テストコード | `test/unit/core/test_error_handlers.py` |

### 1.4 補足情報

#### グローバル変数

| 変数名 | 型 | 役割 |
|--------|-----|------|
| `logger` | `logging.Logger` | モジュールレベルのロガー |

#### 主要分岐

| 分岐 | 条件 | 結果 |
|------|------|------|
| error_id生成 | `error_id`が`None` | 新規UUID生成 |
| error_id使用 | `error_id`が指定済み | 指定値を使用 |
| details出力 | `details`がfalsyな値 | 空文字列 |
| details出力 | `details`が指定 | `, 詳細: {details}` |
| OpenSearch例外 | `AuthenticationException` | 401エラー |
| OpenSearch例外 | `AuthorizationException` | 403エラー |
| OpenSearch例外 | その他の例外 | 500エラー |
| チャット例外 | OpenSearch関連例外 | `handle_opensearch_exceptions`に委譲 |
| チャット例外 | `HTTPException` | そのまま再発生（raise） |
| チャット例外 | その他の例外 | 500エラー |
| ログレベル | DEBUG有効 | 追加情報出力 |
| ログレベル | DEBUG無効 | INFO出力のみ |
| 終了ログ | `success=True` | 「完了」 |
| 終了ログ | `success=False` | 「失敗」 |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| ERH-001 | create_error_response: 基本パラメータのみ | status_code=400, message="エラー" | HTTPException(400), 自動生成error_id |
| ERH-002 | create_error_response: error_id指定 | error_id="custom-id" | 指定されたerror_idが使用される |
| ERH-003 | create_error_response: details指定 | details={"key": "value"} | ログに詳細が出力される |
| ERH-004 | create_error_response: detailsなし | details=None | ログに詳細が含まれない |
| ERH-005 | create_error_response: 空の辞書details | details={} | ログに詳細が含まれない（falsyな値） |
| ERH-006 | create_error_response: error_idがUUID形式 | error_id未指定 | UUID形式のerror_idが自動生成 |
| ERH-007 | handle_opensearch_exceptions: AuthenticationException | AuthenticationException | 401, 認証エラーメッセージ |
| ERH-008 | handle_opensearch_exceptions: AuthorizationException | AuthorizationException | 403, 認可エラーメッセージ |
| ERH-009 | handle_opensearch_exceptions: その他例外 | RuntimeError | 500, 汎用エラーメッセージ |
| ERH-010 | handle_opensearch_exceptions: カスタムoperation | operation="検索操作" | メッセージにoperation含む |
| ERH-011 | handle_opensearch_exceptions: デフォルトoperation | operationなし | 「OpenSearch操作」がメッセージに含まれる |
| ERH-012 | handle_chat_exceptions: OpenSearch認証例外 | AuthenticationException | handle_opensearch_exceptionsに委譲→401 |
| ERH-013 | handle_chat_exceptions: OpenSearch認可例外 | AuthorizationException | handle_opensearch_exceptionsに委譲→403 |
| ERH-014 | handle_chat_exceptions: HTTPException | HTTPException(404) | そのまま再発生（raise） |
| ERH-015 | handle_chat_exceptions: その他例外 | ValueError | 500, session_id含むログ |
| ERH-016 | handle_chat_exceptions: デフォルトoperation | operationなし | 「チャット処理」がメッセージに含まれる |
| ERH-017 | log_request_start: 基本ログ | operation, session_id | INFO出力 |
| ERH-018 | log_request_start: 追加kwargs（DEBUG有効） | **kwargs | DEBUG有効時に追加出力 |
| ERH-019 | log_request_start: 空kwargs（DEBUG有効） | kwargsなし | DEBUG出力なし（session_id以外のキーがない） |
| ERH-020 | log_request_start: 追加kwargs（DEBUG無効） | **kwargs | DEBUG無効時は追加出力なし |
| ERH-021 | log_request_end: success=True | success=True | 「完了」ログ |
| ERH-022 | log_request_end: success=False | success=False | 「失敗」ログ |
| ERH-023 | log_request_end: デフォルトsuccess | successなし | 「完了」ログ（デフォルトTrue） |

### 2.1 create_error_response テスト

```python
# test/unit/core/test_error_handlers.py
import pytest
import re
import logging
from fastapi import HTTPException
from opensearchpy.exceptions import AuthenticationException, AuthorizationException

from app.core.error_handlers import (
    create_error_response,
    handle_opensearch_exceptions,
    handle_chat_exceptions,
    log_request_start,
    log_request_end
)


class TestCreateErrorResponse:
    """create_error_response関数のテスト"""

    def test_basic_error_response(self):
        """ERH-001: create_error_response: 基本パラメータのみ"""
        # Arrange
        status_code = 400
        message = "入力が不正です"

        # Act
        result = create_error_response(status_code=status_code, message=message)

        # Assert
        assert isinstance(result, HTTPException)
        assert result.status_code == 400
        assert "入力が不正です" in result.detail
        assert "サポートにID「" in result.detail
        assert "」を伝えてお問い合わせください" in result.detail

    def test_with_custom_error_id(self):
        """ERH-002: create_error_response: error_id指定"""
        # Arrange
        custom_id = "custom-error-id-12345"

        # Act
        result = create_error_response(
            status_code=500,
            message="サーバーエラー",
            error_id=custom_id
        )

        # Assert
        assert custom_id in result.detail

    def test_with_details(self, caplog):
        """ERH-003: create_error_response: details指定"""
        # Arrange
        details = {"user_id": "user123", "action": "delete"}

        # Act
        with caplog.at_level(logging.ERROR, logger="app.core.error_handlers"):
            result = create_error_response(
                status_code=403,
                message="アクセス拒否",
                details=details
            )

        # Assert
        assert "詳細:" in caplog.text
        assert "user_id" in caplog.text or "user123" in caplog.text

    def test_without_details(self, caplog):
        """ERH-004: create_error_response: detailsなし"""
        # Arrange & Act
        with caplog.at_level(logging.ERROR, logger="app.core.error_handlers"):
            result = create_error_response(
                status_code=400,
                message="エラー",
                details=None
            )

        # Assert
        assert "詳細:" not in caplog.text

    def test_with_empty_dict_details(self, caplog):
        """ERH-005: create_error_response: 空の辞書details

        error_handlers.py:36 の分岐をカバー:
        `if details` は空の辞書 `{}` に対して False を返す
        """
        # Arrange
        details = {}

        # Act
        with caplog.at_level(logging.ERROR, logger="app.core.error_handlers"):
            result = create_error_response(
                status_code=400,
                message="エラー",
                details=details
            )

        # Assert
        # 空の辞書はfalsyな値として扱われるため、詳細は出力されない
        assert "詳細:" not in caplog.text

    def test_auto_generated_error_id_is_uuid(self):
        """ERH-006: create_error_response: error_idがUUID形式"""
        # Arrange
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'

        # Act
        result = create_error_response(status_code=500, message="エラー")

        # Assert
        match = re.search(uuid_pattern, result.detail)
        assert match is not None, "error_idがUUID形式ではありません"
```

### 2.2 handle_opensearch_exceptions テスト

```python
class TestHandleOpenSearchExceptions:
    """handle_opensearch_exceptions関数のテスト"""

    def test_authentication_exception(self):
        """ERH-007: handle_opensearch_exceptions: AuthenticationException"""
        # Arrange
        exc = AuthenticationException(401, "Unauthorized", {})

        # Act
        result = handle_opensearch_exceptions(exc, "インデックス検索")

        # Assert
        assert isinstance(result, HTTPException)
        assert result.status_code == 401
        assert "認証に失敗" in result.detail

    def test_authorization_exception(self):
        """ERH-008: handle_opensearch_exceptions: AuthorizationException"""
        # Arrange
        exc = AuthorizationException(403, "Forbidden", {})

        # Act
        result = handle_opensearch_exceptions(exc, "ドキュメント削除")

        # Assert
        assert isinstance(result, HTTPException)
        assert result.status_code == 403
        assert "アクセス権限がありません" in result.detail

    def test_generic_exception(self):
        """ERH-009: handle_opensearch_exceptions: その他例外"""
        # Arrange
        exc = RuntimeError("Connection timeout")

        # Act
        result = handle_opensearch_exceptions(exc, "接続確認")

        # Assert
        assert isinstance(result, HTTPException)
        assert result.status_code == 500
        assert "エラーが発生しました" in result.detail

    def test_custom_operation_in_message(self):
        """ERH-010: handle_opensearch_exceptions: カスタムoperation"""
        # Arrange
        exc = RuntimeError("Unknown error")
        operation = "カスタム検索操作"

        # Act
        result = handle_opensearch_exceptions(exc, operation)

        # Assert
        assert operation in result.detail

    def test_default_operation(self):
        """ERH-011: handle_opensearch_exceptions: デフォルトoperation"""
        # Arrange
        exc = RuntimeError("Error")

        # Act
        result = handle_opensearch_exceptions(exc)

        # Assert
        assert "OpenSearch操作" in result.detail
```

### 2.3 handle_chat_exceptions テスト

```python
class TestHandleChatExceptions:
    """handle_chat_exceptions関数のテスト"""

    def test_opensearch_authentication_exception(self):
        """ERH-012: handle_chat_exceptions: OpenSearch認証例外

        error_handlers.py:99-100 の分岐をカバー:
        AuthenticationException → handle_opensearch_exceptionsに委譲
        """
        # Arrange
        exc = AuthenticationException(401, "Unauthorized", {})
        session_id = "session-123"

        # Act
        result = handle_chat_exceptions(exc, session_id, "チャット検索")

        # Assert
        assert isinstance(result, HTTPException)
        assert result.status_code == 401

    def test_opensearch_authorization_exception(self):
        """ERH-013: handle_chat_exceptions: OpenSearch認可例外"""
        # Arrange
        exc = AuthorizationException(403, "Forbidden", {})
        session_id = "session-456"

        # Act
        result = handle_chat_exceptions(exc, session_id, "履歴取得")

        # Assert
        assert isinstance(result, HTTPException)
        assert result.status_code == 403

    def test_http_exception_reraise(self):
        """ERH-014: handle_chat_exceptions: HTTPException

        error_handlers.py:103-105 の分岐をカバー:
        HTTPExceptionの場合は新しいエラーレスポンスを作成せず、
        元の例外をそのまま再発生させる（raise）
        """
        # Arrange
        original_exc = HTTPException(status_code=404, detail="Not found")
        session_id = "session-789"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            handle_chat_exceptions(original_exc, session_id, "リソース取得")

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Not found"

    def test_generic_exception(self, caplog):
        """ERH-015: handle_chat_exceptions: その他例外"""
        # Arrange
        exc = ValueError("Invalid value")
        session_id = "session-abc"
        operation = "データ処理"

        # Act
        with caplog.at_level(logging.ERROR, logger="app.core.error_handlers"):
            result = handle_chat_exceptions(exc, session_id, operation)

        # Assert
        assert isinstance(result, HTTPException)
        assert result.status_code == 500
        assert "エラーが発生しました" in result.detail
        assert session_id in caplog.text

    def test_chat_default_operation(self):
        """ERH-016: handle_chat_exceptions: デフォルトoperation"""
        # Arrange
        exc = RuntimeError("Unknown error")
        session_id = "session-def"

        # Act
        result = handle_chat_exceptions(exc, session_id)

        # Assert
        assert "チャット処理" in result.detail
```

### 2.4 log_request_start テスト

```python
class TestLogRequestStart:
    """log_request_start関数のテスト"""

    def test_basic_log(self, caplog):
        """ERH-017: log_request_start: 基本ログ"""
        # Arrange
        operation = "チャット開始"
        session_id = "session-xyz"

        # Act
        with caplog.at_level(logging.INFO, logger="app.core.error_handlers"):
            log_request_start(operation, session_id)

        # Assert
        assert "チャット開始" in caplog.text
        assert session_id in caplog.text
        assert "開始" in caplog.text

    def test_with_kwargs_debug_enabled(self, caplog):
        """ERH-018: log_request_start: 追加kwargs（DEBUG有効時）"""
        # Arrange
        operation = "ドキュメント処理"
        session_id = "session-debug"
        kwargs = {"user_id": "user123", "document_id": "doc456"}

        # Act
        with caplog.at_level(logging.DEBUG, logger="app.core.error_handlers"):
            log_request_start(operation, session_id, **kwargs)

        # Assert
        assert "ドキュメント処理" in caplog.text
        assert session_id in caplog.text
        # DEBUG有効時は追加情報が出力される
        assert "user_id" in caplog.text or "user123" in caplog.text

    def test_with_empty_kwargs_debug_enabled(self, caplog):
        """ERH-019: log_request_start: 空kwargs（DEBUG有効時）

        error_handlers.py:134-137 の分岐をカバー:
        kwargsが空の場合、log_dataにはsession_idのみ含まれる。
        DEBUG出力ループは実行されるが、session_id以外のキーがないため
        追加のDEBUGログは出力されない。
        """
        # Arrange
        operation = "テスト操作"
        session_id = "session-empty"

        # Act
        with caplog.at_level(logging.DEBUG, logger="app.core.error_handlers"):
            log_request_start(operation, session_id)  # kwargsなし

        # Assert
        assert "テスト操作" in caplog.text
        assert session_id in caplog.text
        # DEBUGレコードはsession_id以外のキーがないため出力されない
        debug_records = [r for r in caplog.records if r.levelno == logging.DEBUG]
        assert len(debug_records) == 0

    def test_with_kwargs_debug_disabled(self, caplog):
        """ERH-020: log_request_start: 追加kwargs（DEBUG無効時）"""
        # Arrange
        operation = "クエリ実行"
        session_id = "session-info"
        kwargs = {"query": "test query"}

        # Act - INFOレベルのみ（DEBUGは無効）
        with caplog.at_level(logging.INFO, logger="app.core.error_handlers"):
            log_request_start(operation, session_id, **kwargs)

        # Assert - INFOレベルの基本情報のみ（DEBUGは出力されない）
        assert "クエリ実行" in caplog.text
        assert session_id in caplog.text
        # DEBUGレコードがないことを確認
        debug_records = [r for r in caplog.records if r.levelno == logging.DEBUG]
        assert len(debug_records) == 0
```

### 2.5 log_request_end テスト

```python
class TestLogRequestEnd:
    """log_request_end関数のテスト"""

    def test_success_true(self, caplog):
        """ERH-021: log_request_end: success=True"""
        # Arrange
        operation = "データ保存"
        session_id = "session-success"

        # Act
        with caplog.at_level(logging.INFO, logger="app.core.error_handlers"):
            log_request_end(operation, session_id, success=True)

        # Assert
        assert "データ保存" in caplog.text
        assert "完了" in caplog.text
        assert session_id in caplog.text

    def test_success_false(self, caplog):
        """ERH-022: log_request_end: success=False"""
        # Arrange
        operation = "データ削除"
        session_id = "session-fail"

        # Act
        with caplog.at_level(logging.INFO, logger="app.core.error_handlers"):
            log_request_end(operation, session_id, success=False)

        # Assert
        assert "データ削除" in caplog.text
        assert "失敗" in caplog.text
        assert session_id in caplog.text

    def test_default_success(self, caplog):
        """ERH-023: log_request_end: デフォルトsuccess"""
        # Arrange
        operation = "更新処理"
        session_id = "session-default"

        # Act
        with caplog.at_level(logging.INFO, logger="app.core.error_handlers"):
            log_request_end(operation, session_id)  # successを指定しない

        # Assert
        assert "完了" in caplog.text  # デフォルトはTrue→「完了」
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| ERH-E01 | create_error_response: 空メッセージ | message="" | 空メッセージでもHTTPException生成 |
| ERH-E02 | create_error_response: 不正ステータスコード | status_code=999 | そのまま使用（FastAPI側で検証） |
| ERH-E03 | handle_opensearch_exceptions: None例外 | e=None | 500エラー（Noneはどの例外タイプにも該当しない） |
| ERH-E04 | handle_chat_exceptions: None session_id | session_id=None | ログに"None"出力、HTTPException返却 |
| ERH-E05 | handle_chat_exceptions: 空session_id | session_id="" | ログに空文字出力、HTTPException返却 |
| ERH-E06 | log_request_start: None operation | operation=None | ログに"None"出力 |
| ERH-E07 | log_request_end: None session_id | session_id=None | ログに"None"出力 |

### 3.1 create_error_response 異常系

```python
class TestCreateErrorResponseErrors:
    """create_error_responseエラーテスト"""

    def test_empty_message(self):
        """ERH-E01: create_error_response: 空メッセージ

        error_handlers.py:40 の分岐をカバー:
        空メッセージでもHTTPExceptionは生成される
        """
        # Arrange
        status_code = 400
        message = ""

        # Act
        result = create_error_response(status_code=status_code, message=message)

        # Assert
        assert isinstance(result, HTTPException)
        assert result.status_code == 400
        # 空メッセージでもerror_idは含まれる
        assert "サポートにID「" in result.detail

    def test_unusual_status_code(self):
        """ERH-E02: create_error_response: 不正ステータスコード

        FastAPI/Starletteが最終的に検証するため、
        この関数では任意の整数を受け入れる
        """
        # Arrange
        status_code = 999

        # Act
        result = create_error_response(status_code=status_code, message="エラー")

        # Assert
        assert result.status_code == 999
```

### 3.2 handle_opensearch_exceptions 異常系

```python
class TestHandleOpenSearchExceptionsErrors:
    """handle_opensearch_exceptionsエラーテスト"""

    def test_none_exception(self):
        """ERH-E03: handle_opensearch_exceptions: None例外

        error_handlers.py:58, 66 の isinstance チェックで
        Noneはどの例外タイプにも該当しないため、
        else分岐（汎用エラー、500）として処理される
        """
        # Arrange
        exc = None

        # Act
        result = handle_opensearch_exceptions(exc, "テスト操作")

        # Assert
        # Noneはどの例外タイプにも該当しないため、汎用エラーとして処理
        assert isinstance(result, HTTPException)
        assert result.status_code == 500
        assert "エラーが発生しました" in result.detail
```

### 3.3 handle_chat_exceptions 異常系

```python
class TestHandleChatExceptionsErrors:
    """handle_chat_exceptionsエラーテスト"""

    def test_none_session_id(self, caplog):
        """ERH-E04: handle_chat_exceptions: None session_id

        error_handlers.py:108 でsession_idをログ出力するため、
        Noneは文字列"None"としてログ出力される
        """
        # Arrange
        exc = RuntimeError("Error")
        session_id = None

        # Act
        with caplog.at_level(logging.ERROR, logger="app.core.error_handlers"):
            result = handle_chat_exceptions(exc, session_id, "テスト")

        # Assert
        assert isinstance(result, HTTPException)
        assert result.status_code == 500
        assert "None" in caplog.text

    def test_empty_session_id(self, caplog):
        """ERH-E05: handle_chat_exceptions: 空session_id"""
        # Arrange
        exc = ValueError("Error")
        session_id = ""

        # Act
        with caplog.at_level(logging.ERROR, logger="app.core.error_handlers"):
            result = handle_chat_exceptions(exc, session_id, "テスト")

        # Assert
        assert isinstance(result, HTTPException)
        assert result.status_code == 500
```

### 3.4 log_request_start/end 異常系

```python
class TestLogFunctionsErrors:
    """ログ関数エラーテスト"""

    def test_log_request_start_none_operation(self, caplog):
        """ERH-E06: log_request_start: None operation

        f-string内でNoneは"None"文字列に変換される
        """
        # Arrange
        operation = None
        session_id = "session-123"

        # Act
        with caplog.at_level(logging.INFO, logger="app.core.error_handlers"):
            log_request_start(operation, session_id)

        # Assert
        assert "None" in caplog.text
        assert "開始" in caplog.text

    def test_log_request_end_none_session_id(self, caplog):
        """ERH-E07: log_request_end: None session_id"""
        # Arrange
        operation = "テスト操作"
        session_id = None

        # Act
        with caplog.at_level(logging.INFO, logger="app.core.error_handlers"):
            log_request_end(operation, session_id, success=True)

        # Assert
        assert "テスト操作" in caplog.text
        assert "完了" in caplog.text
        assert "None" in caplog.text
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| ERH-SEC-01 | エラーレスポンスに内部パスが含まれない | FileNotFoundError with path | パス情報未露出（汎用メッセージ使用） |
| ERH-SEC-02 | エラーレスポンスにスタックトレースが含まれない | 任意の例外 | Traceback未露出 |
| ERH-SEC-03 | error_idが予測不可能なUUID | 複数回呼び出し | 全て異なるUUID |
| ERH-SEC-04 | 認証情報がエラーメッセージに含まれない | AuthenticationException | パスワード/トークン未露出 |
| ERH-SEC-05 | detailsパラメータがHTTPレスポンスに含まれない | details指定 | detailsはログのみ、レスポンスに未露出 |
| ERH-SEC-06 | セッションIDがHTTPレスポンスに含まれない | handle_chat_exceptions | session_idはログのみ |
| ERH-SEC-07 | error_idの長さが適切（UUID v4形式） | - | 36文字（32hex + 4hyphens） |
| ERH-SEC-08 | ログインジェクション: 改行文字の処理 | 改行を含むエラー | 【既知の制限事項】改行はそのまま出力 |
| ERH-SEC-09 | CRLFインジェクション: HTTPレスポンスへの影響 | CRLF含むメッセージ | FastAPIのJSONシリアライズで安全 |

```python
@pytest.mark.security
class TestErrorHandlersSecurity:
    """error_handlersセキュリティテスト"""

    def test_no_internal_paths_in_response(self):
        """ERH-SEC-01: エラーレスポンスに内部パスが含まれない

        CWE-209: Information Exposure Through an Error Message対策

        handle_opensearch_exceptionsは汎用メッセージを返すため、
        例外メッセージ内の内部パスはHTTPレスポンスに含まれない。
        """
        # Arrange
        exc = FileNotFoundError("/opt/app/secret/config.yaml not found")
        internal_path_patterns = [
            r'/opt/[\w\-/.]+',
            r'/usr/local/[\w\-/.]+',
            r'/home/[\w\-/.]+',
            r'/var/[\w\-/.]+',
            r'[A-Z]:\\[\w\-\\/]+',
        ]

        # Act
        result = handle_opensearch_exceptions(exc, "ファイル読み込み")

        # Assert
        for pattern in internal_path_patterns:
            matches = re.findall(pattern, result.detail)
            assert not matches, f"内部パスが露出: {matches}"

    def test_no_stacktrace_in_response(self):
        """ERH-SEC-02: エラーレスポンスにスタックトレースが含まれない

        CWE-209対策
        """
        # Arrange
        exc = RuntimeError("Internal error at line 42")

        # Act
        result = handle_opensearch_exceptions(exc, "処理")

        # Assert
        assert "Traceback" not in result.detail
        assert "File \"" not in result.detail
        # "line XX" パターンが含まれていないことを確認（日本語の「行」は許容）
        assert not re.search(r'\bline \d+\b', result.detail)

    def test_error_id_unpredictable(self):
        """ERH-SEC-03: error_idが予測不可能なUUID

        CWE-330: Use of Insufficiently Random Values対策
        """
        # Arrange
        error_ids = set()

        # Act
        for _ in range(10):
            result = create_error_response(status_code=500, message="エラー")
            # error_idを抽出
            match = re.search(
                r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
                result.detail
            )
            if match:
                error_ids.add(match.group(0))

        # Assert - 10回呼び出して10個のユニークなIDが生成される
        assert len(error_ids) == 10, "error_idが重複しています（予測可能な可能性）"

    def test_no_credentials_in_error_message(self):
        """ERH-SEC-04: 認証情報がエラーメッセージに含まれない

        OWASP A02:2021 - Cryptographic Failures対策

        handle_opensearch_exceptionsは固定の汎用メッセージを返すため、
        例外メッセージ内の認証情報はHTTPレスポンスに含まれない。
        """
        # Arrange
        exc = AuthenticationException(
            401,
            "Authentication failed for user admin with password=secret123",
            {}
        )

        # Act
        result = handle_opensearch_exceptions(exc, "認証")

        # Assert
        # 固定メッセージが使用されることを確認
        assert "認証に失敗" in result.detail
        # 元の例外メッセージ内容が含まれないことを確認
        assert "password" not in result.detail.lower()
        assert "secret123" not in result.detail
        assert "admin" not in result.detail

    def test_details_not_in_http_response(self):
        """ERH-SEC-05: detailsパラメータがHTTPレスポンスに含まれない

        error_handlers.py:27 のdocstring:
        「details: 追加詳細情報（オプション、ログ出力のみ）」

        detailsはデバッグ用にログ出力されるが、
        HTTPレスポンス（detail文字列）には含まれない。
        """
        # Arrange
        sensitive_details = {
            "internal_user_id": 12345,
            "database_query": "SELECT * FROM users WHERE password='secret'",
            "stack_frame": "/opt/app/sensitive.py:42"
        }

        # Act
        result = create_error_response(
            status_code=500,
            message="処理エラー",
            details=sensitive_details
        )

        # Assert - detailsの内容がHTTPレスポンスに含まれない
        assert "internal_user_id" not in result.detail
        assert "12345" not in result.detail
        assert "database_query" not in result.detail
        assert "SELECT" not in result.detail
        assert "sensitive.py" not in result.detail

    def test_session_id_not_in_http_response(self):
        """ERH-SEC-06: セッションIDがHTTPレスポンスに含まれない

        handle_chat_exceptionsはセッションIDをログ出力するが、
        HTTPレスポンスには含まれない。
        """
        # Arrange
        exc = RuntimeError("Error")
        session_id = "sensitive-session-12345"

        # Act
        result = handle_chat_exceptions(exc, session_id, "処理")

        # Assert
        assert session_id not in result.detail
        # error_idのみ含まれる
        assert re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-', result.detail) is not None

    def test_error_id_length_appropriate(self):
        """ERH-SEC-07: error_idの長さが適切（UUID v4形式）

        UUID v4形式（36文字: 32hex + 4hyphens）であることを確認
        """
        # Arrange & Act
        result = create_error_response(status_code=500, message="エラー")

        # Assert
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
        実装側でサニタイズ処理の追加を推奨。
        """
        # Arrange
        malicious_message = (
            "Normal error\n"
            "[CRITICAL] FAKE - System compromised"
        )
        exc = RuntimeError(malicious_message)
        session_id = "session-test"

        # Act
        with caplog.at_level(logging.ERROR, logger="app.core.error_handlers"):
            handle_chat_exceptions(exc, session_id, "処理")

        # Assert - 改行文字がエスケープまたは除去されることを期待
        for record in caplog.records:
            log_message = record.getMessage()
            # 改行がエスケープされている（\\n）か、除去されていることを確認
            # 現在の実装では失敗する（xfail）
            assert "\n" not in log_message or "\\n" in log_message, \
                f"改行文字が未処理のままログ出力されています: {log_message[:50]}..."

    def test_crlf_injection_json_safe(self):
        """ERH-SEC-09: CRLFインジェクション: HTTPレスポンスへの影響

        HTTP Response Splitting対策

        FastAPIはJSONレスポンスを返すため、CRLFは文字列として
        JSONシリアライズされ、HTTPヘッダーに影響しない。
        """
        # Arrange
        crlf_payload = "error\r\nSet-Cookie: malicious=value"

        # Act
        result = create_error_response(
            status_code=400,
            message=crlf_payload
        )

        # Assert
        # HTTPException.detailは文字列として保持される
        # FastAPIがJSONレスポンスとして返す際に自動エスケープされる
        assert isinstance(result, HTTPException)
        assert result.status_code == 400
        # detailにはCRLFが文字列として含まれる（JSONでエスケープされる）
        assert "error" in result.detail
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_error_handlers_module` | テスト間のモジュール状態リセット | function | Yes |

### 共通フィクスチャ定義

```python
# test/unit/core/conftest.py に追加（または test_error_handlers.py 内に定義）
import sys
import pytest


@pytest.fixture(autouse=True)
def reset_error_handlers_module():
    """テストごとにerror_handlersモジュールの状態をリセット

    loggerの状態やハンドラーが共有されないように、
    テスト間でモジュールをリフレッシュする。
    """
    yield

    # テスト後にクリーンアップ
    modules_to_remove = [
        key for key in sys.modules
        if key.startswith("app.core.error_handlers")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]
```

---

## 6. テスト実行例

```bash
# error_handlers関連テストのみ実行
pytest test/unit/core/test_error_handlers.py -v

# 特定のテストクラスのみ実行
pytest test/unit/core/test_error_handlers.py::TestCreateErrorResponse -v
pytest test/unit/core/test_error_handlers.py::TestHandleOpenSearchExceptions -v
pytest test/unit/core/test_error_handlers.py::TestHandleChatExceptions -v
pytest test/unit/core/test_error_handlers.py::TestLogRequestStart -v
pytest test/unit/core/test_error_handlers.py::TestLogRequestEnd -v
pytest test/unit/core/test_error_handlers.py::TestErrorHandlersSecurity -v

# カバレッジ付きで実行
pytest test/unit/core/test_error_handlers.py --cov=app.core.error_handlers --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/core/test_error_handlers.py -m "security" -v

# xfailを含めた詳細表示
pytest test/unit/core/test_error_handlers.py -v --tb=short
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 23 | ERH-001 〜 ERH-023 |
| 異常系 | 7 | ERH-E01 〜 ERH-E07 |
| セキュリティ | 9 | ERH-SEC-01 〜 ERH-SEC-09 |
| **合計** | **39** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestCreateErrorResponse` | ERH-001〜ERH-006 | 6 |
| `TestHandleOpenSearchExceptions` | ERH-007〜ERH-011 | 5 |
| `TestHandleChatExceptions` | ERH-012〜ERH-016 | 5 |
| `TestLogRequestStart` | ERH-017〜ERH-020 | 4 |
| `TestLogRequestEnd` | ERH-021〜ERH-023 | 3 |
| `TestCreateErrorResponseErrors` | ERH-E01〜ERH-E02 | 2 |
| `TestHandleOpenSearchExceptionsErrors` | ERH-E03 | 1 |
| `TestHandleChatExceptionsErrors` | ERH-E04〜ERH-E05 | 2 |
| `TestLogFunctionsErrors` | ERH-E06〜ERH-E07 | 2 |
| `TestErrorHandlersSecurity` | ERH-SEC-01〜ERH-SEC-09 | 9 |

### 実装失敗が予想されるテスト

以下のテストは現在の実装では**意図的に失敗**します（`@pytest.mark.xfail`）。

| テストID | 失敗理由 | 修正方針 |
|---------|---------|---------|
| ERH-SEC-08 | `str(e)`をそのままログ出力（`error_handlers.py:75, 108`） | エラーメッセージから制御文字を除去するサニタイズ処理を追加 |

### 注意事項

- テスト実行に `pytest` と `pytest-cov` が必要
- `@pytest.mark.security` マーカーの使用には `pyproject.toml` への登録が必要:
  ```toml
  [tool.pytest.ini_options]
  markers = ["security: セキュリティテスト"]
  ```
- `caplog` フィクスチャでログ検証時は `logger="app.core.error_handlers"` を指定して対象ロガーを限定
- OpenSearch例外クラス（`AuthenticationException`, `AuthorizationException`）は `opensearchpy.exceptions` からインポート

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | ログに`exc_info=True`で出力 | スタックトレースがログに出力される | 本番環境ではログレベルをWARNING以上に設定 |
| 2 | `str(e)`をそのままログ出力 | 例外メッセージに機密情報が含まれる場合、ログに露出 | 例外メッセージのサニタイズ処理追加を推奨 |
| 3 | 入力バリデーションなし | `status_code`や`message`の不正値をそのまま使用 | FastAPI側でレスポンス検証されるため影響は限定的 |
| 4 | ログレベル判定 | `logger.isEnabledFor(logging.DEBUG)`でDEBUG出力を制御 | テスト時はロガーレベルを適切に設定 |
| 5 | UUID生成の衝突可能性 | 理論上は衝突可能だが実用上は無視できる | 追跡IDとして十分なユニーク性 |
| 6 | ログインジェクション未対策 | 改行を含むエラーメッセージがログにそのまま出力される | `_sanitize_log_message()`関数の追加を推奨 |
| 7 | HTTPException再発生 | `handle_chat_exceptions`でHTTPExceptionを`raise`する | 呼び出し元でtry-exceptが必要 |
