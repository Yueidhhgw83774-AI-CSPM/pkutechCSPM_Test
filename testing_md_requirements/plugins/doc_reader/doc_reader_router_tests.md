# doc_reader_plugin/router テストケース

## 1. 概要

`router.py`は、Document Reader Plugin のAPIエンドポイントを定義するモジュールです。チャット機能とテキスト構造化機能の2つの主要エンドポイントを提供し、FastAPIルーターとして動作します。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `structure_text_from_chat` | チャット入力からテキストを推奨事項として構造化するエンドポイント（POST /docreader/chat/structure） |
| `handle_chat_route` | ユーザーからのチャットメッセージを受け取り、LangGraphを使用して応答を生成するエンドポイント（POST /docreader/chat） |

### 1.2 カバレッジ目標: 90%

> **注記**: APIルーターモジュールとして、HTTPリクエスト/レスポンスの検証と例外処理が重要です。外部依存（`chat_logic.invoke_chat_graph`、`structuring.structure_item_with_llm`）は全てモック化が必須です。TestClientは非同期エンドポイントを同期的にテストするため、テスト関数は通常の`def`で記述します。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/doc_reader_plugin/router.py` |
| テストコード | `test/unit/doc_reader_plugin/test_router.py` |
| 依存: chat_logic | `app/doc_reader_plugin/chat_logic.py` |
| 依存: structuring | `app/doc_reader_plugin/structuring.py` |
| 依存: models/chat | `app/models/chat.py` |

### 1.4 補足情報

#### グローバル変数・ルーター設定
- `router` (router.py:22): APIRouter インスタンス（prefix="/docreader", tags=["Document Reader Plugin - Chat"]）

#### 主要分岐（テスト対象）
- router.py:39-40: `structure_text_from_chat`でのprompt空チェック → HTTPException(400)
- router.py:46-54: `structure_text_from_chat`での構造化成功/失敗判定
- router.py:58-59: `structure_text_from_chat`でのHTTPException再スロー
- router.py:60-69: `structure_text_from_chat`での予期せぬエラーハンドリング
- router.py:105-107: `handle_chat_route`でのHTTPException再スロー
- router.py:108-117: `handle_chat_route`での予期せぬエラーハンドリング

#### 主要分岐（テスト対象外）
- router.py:15-20: `structure_item_with_llm` のImportError時のフォールバック
  - **理由**: この分岐はモジュール読み込み時に発生するため、通常のユニットテストでは到達困難。
    テストで `structure_item_with_llm` をモックする際、既にimportが完了しているため、
    ImportError分岐はカバーできない。実装改善（フォールバック関数定義やHTTPException(503)）を推奨。

#### リクエスト/レスポンスモデル
- `ChatRequest`: session_id, prompt, context, current_source_document, target_clouds_context（extra未指定）
- `ChatResponse`: response (str)
- `DocReaderChatRequest`: session_id, prompt, currentSourceDocument, targetCloudsContext（extra="forbid"）
- `DocReaderChatResponse`: llmTextResponse, parsedChatItems, savedItems, message

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| DOCR-001 | structure_text_from_chat: 構造化成功 | 有効なテキスト | ChatResponse（構造化データJSON） |
| DOCR-002 | structure_text_from_chat: 構造化失敗時メッセージ | 構造化不可テキスト | ChatResponse（失敗メッセージ） |
| DOCR-003 | handle_chat_route: 正常応答 | 有効なチャットリクエスト | DocReaderChatResponse |
| DOCR-004 | handle_chat_route: オプションパラメータあり | currentSourceDocument指定 | DocReaderChatResponse |
| DOCR-005 | handle_chat_route: targetCloudsContext指定 | クラウドコンテキスト付き | DocReaderChatResponse |
| DOCR-006 | structure_text_from_chat: 日本語テキスト | 日本語の推奨事項テキスト | ChatResponse（日本語構造化データ） |
| DOCR-007 | handle_chat_route: 長いプロンプト | 1000文字以上のプロンプト | DocReaderChatResponse |
| DOCR-008 | structure_text_from_chat: 前後空白付きテキスト | "  valid text  " | ChatResponse（空白保持） |

### 2.1 structure_text_from_chat テスト

```python
# test/unit/doc_reader_plugin/test_router.py
import pytest
from unittest.mock import patch


class TestStructureTextFromChat:
    """structure_text_from_chat エンドポイントの正常系テスト

    NOTE: TestClientは非同期エンドポイントを同期的にテストするため、
    テスト関数は通常の def で記述します（async def は不要）。
    """

    def test_structure_success(self, client):
        """DOCR-001: 構造化成功

        router.py:46-48 の構造化成功分岐をカバー。

        NOTE: レスポンスは以下の形式で返却される（router.py:48）:
        "テキストを推奨事項として構造化しました:\n```json\n{JSONデータ}\n```"
        json.dumps(..., ensure_ascii=False) でエンコードされるため、
        日本語文字はUnicodeエスケープされずそのまま出力される。
        """
        # Arrange
        mock_structured_data = {
            "recommendationId": "REC-001",
            "title": "テスト推奨事項",
            "description": "テスト説明",
            "severity": "medium"
        }

        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as mock_structure:
            mock_structure.return_value = mock_structured_data

            # Act
            response = client.post(
                "/docreader/chat/structure",
                json={"session_id": "test-session", "prompt": "構造化対象のテキスト"}
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        # フォーマット検証: コードフェンス付きJSON形式
        assert "テキストを推奨事項として構造化しました:" in data["response"]
        assert "```json" in data["response"]
        assert "```" in data["response"].split("```json")[1]  # 閉じコードフェンス
        # データ内容検証
        assert "REC-001" in data["response"]
        assert "テスト推奨事項" in data["response"]  # ensure_ascii=False で日本語がそのまま出力

    def test_structure_failure_returns_message(self, client):
        """DOCR-002: 構造化失敗時メッセージ

        router.py:52-54 の構造化失敗分岐をカバー。
        """
        # Arrange
        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as mock_structure:
            mock_structure.return_value = None  # 構造化失敗

            # Act
            response = client.post(
                "/docreader/chat/structure",
                json={"session_id": "test-session", "prompt": "構造化できないテキスト"}
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "テキストの構造化に失敗しました。"

    def test_structure_japanese_text(self, client):
        """DOCR-006: 日本語テキスト構造化

        日本語テキストの構造化処理を検証。
        """
        # Arrange
        mock_structured_data = {
            "recommendationId": "推奨-001",
            "title": "セキュリティ設定の確認",
            "description": "システムのセキュリティ設定を定期的に確認してください。",
            "severity": "high"
        }

        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as mock_structure:
            mock_structure.return_value = mock_structured_data

            # Act
            response = client.post(
                "/docreader/chat/structure",
                json={
                    "session_id": "test-session-ja",
                    "prompt": "セキュリティ設定の確認が必要です。定期的な監査を実施してください。"
                }
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "セキュリティ設定の確認" in data["response"]

    def test_structure_whitespace_preserved(self, client):
        """DOCR-008: 前後空白付きテキスト

        実装は空白をトリミングせずそのまま渡す（router.py:44）。
        空白チェック（router.py:39）はstrip()で判定するが、
        実際の値は未加工で渡される。
        """
        # Arrange
        mock_structured_data = {"title": "Valid"}

        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as mock_structure:
            mock_structure.return_value = mock_structured_data

            # Act
            response = client.post(
                "/docreader/chat/structure",
                json={"session_id": "test-session", "prompt": "  valid text  "}
            )

        # Assert
        assert response.status_code == 200
        # 実装は空白を保持して渡す
        mock_structure.assert_called_once_with("  valid text  ")
```

### 2.2 handle_chat_route テスト

```python
from unittest.mock import AsyncMock


class TestHandleChatRoute:
    """handle_chat_route エンドポイントの正常系テスト

    NOTE: TestClientは非同期エンドポイントを同期的にテストするため、
    テスト関数は通常の def で記述します（async def は不要）。

    IMPORTANT: invoke_chat_graph は async 関数（router.py:91 で await される）なので、
    モックには AsyncMock を使用する必要があります。
    通常の MagicMock.return_value では TypeError が発生します。
    """

    def test_chat_success(self, client):
        """DOCR-003: 正常応答

        router.py:91-104 の正常処理パスをカバー。
        """
        # Arrange
        with patch("app.doc_reader_plugin.router.invoke_chat_graph", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = "AIからの応答テキストです。"

            # Act
            response = client.post(
                "/docreader/chat",
                json={
                    "session_id": "test-session",
                    "prompt": "こんにちは、質問があります。"
                }
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["llmTextResponse"] == "AIからの応答テキストです。"
        assert data["parsedChatItems"] == []
        assert data["savedItems"] == []
        assert data["message"] == "チャット処理が完了しました"

    def test_chat_with_source_document(self, client):
        """DOCR-004: オプションパラメータあり

        currentSourceDocument パラメータ指定時の動作を検証。
        """
        # Arrange
        with patch("app.doc_reader_plugin.router.invoke_chat_graph", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = "ドキュメントに基づく応答"

            # Act
            response = client.post(
                "/docreader/chat",
                json={
                    "session_id": "test-session",
                    "prompt": "このドキュメントについて教えて",
                    "currentSourceDocument": "security-guidelines.pdf"
                }
            )

        # Assert
        assert response.status_code == 200
        # invoke_chat_graphが正しい引数で呼ばれたか確認
        mock_invoke.assert_called_once_with(
            session_id="test-session",
            user_prompt="このドキュメントについて教えて",
            source_document_context="security-guidelines.pdf",
            ui_target_clouds_context=None
        )

    def test_chat_with_target_clouds_context(self, client):
        """DOCR-005: targetCloudsContext指定

        クラウドコンテキスト付きリクエストの動作を検証。
        """
        # Arrange
        with patch("app.doc_reader_plugin.router.invoke_chat_graph", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = "AWS向けの応答"

            # Act
            response = client.post(
                "/docreader/chat",
                json={
                    "session_id": "test-session",
                    "prompt": "AWSのセキュリティについて",
                    "targetCloudsContext": ["AWS", "Azure"]
                }
            )

        # Assert
        assert response.status_code == 200
        mock_invoke.assert_called_once_with(
            session_id="test-session",
            user_prompt="AWSのセキュリティについて",
            source_document_context=None,
            ui_target_clouds_context=["AWS", "Azure"]
        )

    def test_chat_long_prompt(self, client):
        """DOCR-007: 長いプロンプト

        1000文字以上のプロンプトが正常に処理されることを検証。
        """
        # Arrange
        long_prompt = "セキュリティに関する質問です。" * 100  # 約1500文字

        with patch("app.doc_reader_plugin.router.invoke_chat_graph", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = "長い質問への応答"

            # Act
            response = client.post(
                "/docreader/chat",
                json={
                    "session_id": "test-session",
                    "prompt": long_prompt
                }
            )

        # Assert
        assert response.status_code == 200
        assert mock_invoke.call_args[1]["user_prompt"] == long_prompt
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| DOCR-E01 | structure_text_from_chat: 空のプロンプト | prompt="" | HTTPException(400) |
| DOCR-E02 | structure_text_from_chat: 空白のみのプロンプト | prompt="   " | HTTPException(400) |
| DOCR-E03 | structure_text_from_chat: Noneプロンプト | promptなし | HTTPException(422) |
| DOCR-E04 | structure_text_from_chat: LLM例外 | LLMエラー発生 | HTTPException(500) with error_id |
| DOCR-E05 | structure_text_from_chat: HTTPException再スロー | HTTPException発生 | 元のHTTPException |
| DOCR-E06 | handle_chat_route: invoke_chat_graph例外 | グラフ実行エラー | HTTPException(500) with error_id |
| DOCR-E07 | handle_chat_route: HTTPException再スロー | HTTPException発生 | 元のHTTPException |
| DOCR-E08 | handle_chat_route: 必須フィールド欠落 | session_idなし | HTTPException(422) |
| DOCR-E09 | handle_chat_route: 空のprompt | prompt="" | HTTPException(422) |

### 3.1 structure_text_from_chat 異常系

```python
class TestStructureTextFromChatErrors:
    """structure_text_from_chat エンドポイントの異常系テスト"""

    def test_empty_prompt(self, client):
        """DOCR-E01: 空のプロンプト

        router.py:39-40 の空文字列チェック分岐をカバー。
        """
        # Arrange & Act
        response = client.post(
            "/docreader/chat/structure",
            json={"session_id": "test-session", "prompt": ""}
        )

        # Assert
        assert response.status_code == 400
        assert "No text provided to structure" in response.json()["detail"]

    def test_whitespace_only_prompt(self, client):
        """DOCR-E02: 空白のみのプロンプト

        router.py:39 の strip() による空白のみ判定をカバー。
        """
        # Arrange & Act
        response = client.post(
            "/docreader/chat/structure",
            json={"session_id": "test-session", "prompt": "   "}
        )

        # Assert
        assert response.status_code == 400
        assert "No text provided to structure" in response.json()["detail"]

    def test_missing_prompt_field(self, client):
        """DOCR-E03: Noneプロンプト（フィールド欠落）

        Pydantic バリデーションエラーをカバー。
        """
        # Arrange & Act
        response = client.post(
            "/docreader/chat/structure",
            json={"session_id": "test-session"}  # promptなし
        )

        # Assert
        assert response.status_code == 422  # Validation Error

    def test_llm_exception(self, client):
        """DOCR-E04: LLM例外

        router.py:60-69 の予期せぬエラーハンドリングをカバー。
        """
        # Arrange
        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as mock_structure:
            mock_structure.side_effect = Exception("LLM connection failed")

            # Act
            response = client.post(
                "/docreader/chat/structure",
                json={"session_id": "test-session", "prompt": "テスト"}
            )

        # Assert
        assert response.status_code == 500
        detail = response.json()["detail"]
        assert "Error structuring text from chat" in detail
        assert "ID:" in detail  # error_id が含まれる

    def test_http_exception_rethrow(self, client):
        """DOCR-E05: HTTPException再スロー

        router.py:58-59 のHTTPException再スロー分岐をカバー。

        NOTE: 実際のstructure_item_with_llm実装はHTTPExceptionを
        発生させないが、将来の拡張や依存変更に備えた防御的テスト。
        """
        # Arrange
        from fastapi import HTTPException

        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as mock_structure:
            mock_structure.side_effect = HTTPException(status_code=503, detail="Service unavailable")

            # Act
            response = client.post(
                "/docreader/chat/structure",
                json={"session_id": "test-session", "prompt": "テスト"}
            )

        # Assert
        assert response.status_code == 503
        assert response.json()["detail"] == "Service unavailable"
```

### 3.2 handle_chat_route 異常系

```python
from unittest.mock import AsyncMock


class TestHandleChatRouteErrors:
    """handle_chat_route エンドポイントの異常系テスト

    IMPORTANT: invoke_chat_graph は async 関数なので、
    side_effect を使う場合も AsyncMock が必要。
    """

    def test_invoke_chat_graph_exception(self, client):
        """DOCR-E06: invoke_chat_graph例外

        router.py:108-117 の予期せぬエラーハンドリングをカバー。
        """
        # Arrange
        with patch("app.doc_reader_plugin.router.invoke_chat_graph", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.side_effect = Exception("Graph execution failed")

            # Act
            response = client.post(
                "/docreader/chat",
                json={"session_id": "test-session", "prompt": "質問です"}
            )

        # Assert
        assert response.status_code == 500
        detail = response.json()["detail"]
        assert "予期しないエラーが発生しました" in detail
        assert "ID「" in detail  # error_id が含まれる

    def test_http_exception_rethrow(self, client):
        """DOCR-E07: HTTPException再スロー

        router.py:105-107 のHTTPException再スロー分岐をカバー。
        """
        # Arrange
        from fastapi import HTTPException

        with patch("app.doc_reader_plugin.router.invoke_chat_graph", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.side_effect = HTTPException(status_code=429, detail="Rate limit exceeded")

            # Act
            response = client.post(
                "/docreader/chat",
                json={"session_id": "test-session", "prompt": "質問です"}
            )

        # Assert
        assert response.status_code == 429
        assert response.json()["detail"] == "Rate limit exceeded"

    def test_missing_session_id(self, client):
        """DOCR-E08: 必須フィールド欠落

        Pydantic バリデーションエラー（session_idなし）をカバー。
        """
        # Arrange & Act
        response = client.post(
            "/docreader/chat",
            json={"prompt": "質問です"}  # session_idなし
        )

        # Assert
        assert response.status_code == 422

    def test_empty_prompt_validation(self, client):
        """DOCR-E09: 空のprompt

        DocReaderChatRequest の min_length=1 バリデーションをカバー。
        空文字列は長さ0なので min_length=1 制約により422エラーとなる。

        NOTE: 空白のみ（例: " "）は min_length=1 を満たすため422にならない。
        空白のみを拒否したい場合はモデル側でカスタムバリデーション
        （例: @field_validator で strip() 後に検証）が必要。
        現在の実装ではそのような検証は行われていない。
        """
        # Arrange & Act
        response = client.post(
            "/docreader/chat",
            json={"session_id": "test-session", "prompt": ""}
        )

        # Assert
        assert response.status_code == 422  # Pydantic validation error
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| DOCR-SEC-01 | エラーIDによるトレーサビリティ | 例外発生 | UUID形式のエラーID |
| DOCR-SEC-02 | スタックトレース非露出 | 例外発生 | 詳細なスタックトレースがレスポンスに含まれない |
| DOCR-SEC-03 | XSSペイロード入力時のAPI動作確認 | XSSスクリプト入力 | APIがクラッシュせず200（サニタイズはUI側責務） |
| DOCR-SEC-04 | SQLインジェクション風入力 | SQL文字列入力 | 安全に処理 |
| DOCR-SEC-05 | パストラバーサル風入力 | "../"を含む入力 | 安全に処理 |
| DOCR-SEC-06 | 大量入力によるDoS | 非常に長い文字列 | 処理成功（サイズ制限は実装されていない）[slow] |
| DOCR-SEC-07 | セッションID推測防止 | 推測可能なセッションID | 処理される（検証は別レイヤー） |
| DOCR-SEC-08 | JSONインジェクション（ChatRequest） | 不正なJSON構造 | 200（extra未指定で無視） |
| DOCR-SEC-08b | JSONインジェクション（DocReaderChatRequest） | 不正なJSON構造 | 422（extra="forbid"） |
| DOCR-SEC-09 | 内部例外情報の非露出 | 内部エラー発生 | 内部パス・モジュール名が露出しない |
| DOCR-SEC-10 | Unicode制御文字の処理 | 制御文字を含む入力 | 200（制御文字検証は未実装） |
| DOCR-SEC-11 | 機密情報漏洩防止 | 例外メッセージに機密情報含む | 機密情報がレスポンスに露出しない |
| DOCR-SEC-12 | SSRF防止（currentSourceDocument） | 内部URL指定 | 安全に処理（URL検証は未実装） |
| DOCR-SEC-13 | コマンドインジェクション防止 | コマンド文字列含む入力 | 安全に処理 |
| DOCR-SEC-14 | 深いネストJSON | 深いネスト構造 | 適切に処理またはエラー |

```python
from unittest.mock import AsyncMock


@pytest.mark.security
class TestDocReaderRouterSecurity:
    """router.py セキュリティテスト

    IMPORTANT: invoke_chat_graph を使用するテストでは AsyncMock を使用すること。
    """

    def test_error_id_traceability(self, client):
        """DOCR-SEC-01: エラーIDによるトレーサビリティ

        エラー発生時にUUID形式のエラーIDが生成され、
        ログとレスポンスで追跡可能であることを検証。
        """
        # Arrange
        import re
        uuid_pattern = re.compile(
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            re.IGNORECASE
        )

        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as mock_structure:
            mock_structure.side_effect = Exception("Test error")

            # Act
            response = client.post(
                "/docreader/chat/structure",
                json={"session_id": "test-session", "prompt": "テスト"}
            )

        # Assert
        assert response.status_code == 500
        detail = response.json()["detail"]
        assert uuid_pattern.search(detail) is not None

    def test_no_stack_trace_in_response(self, client):
        """DOCR-SEC-02: スタックトレース非露出

        エラーレスポンスに詳細なスタックトレースが含まれないことを検証。
        """
        # Arrange
        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as mock_structure:
            mock_structure.side_effect = ValueError("Internal error with sensitive info")

            # Act
            response = client.post(
                "/docreader/chat/structure",
                json={"session_id": "test-session", "prompt": "テスト"}
            )

        # Assert
        assert response.status_code == 500
        response_text = response.text
        assert "Traceback" not in response_text
        assert "File \"" not in response_text

    def test_xss_payload_handling(self, client):
        """DOCR-SEC-03: XSSペイロード入力時のAPI動作確認

        XSSスクリプトを含む入力が安全に処理されることを検証。

        ■ 検証項目（このテストで確認すること）:
        1. APIがクラッシュせず200を返す
        2. Content-Type が application/json である
        3. レスポンスがJSON形式で返される（response.json()が成功する）

        ■ 説明（このテストの前提・限界）:
        - APIレイヤーではXSSの「実害」（ブラウザでのスクリプト実行）は検証不可
        - Content-Type: application/json であれば、
          ブラウザがHTMLとして解釈することは通常ない
        - 実際のXSS防止検証はUIレイヤー（フロントエンド）で行う必要がある
        - このテストは「入力がそのまま文字列として扱われ、APIが壊れない」ことの確認
        - サニタイズは未実装（フロントエンド側の責務）
        """
        # Arrange
        xss_payload = "<script>alert('XSS')</script>"
        mock_result = {"title": xss_payload}

        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as mock_structure:
            mock_structure.return_value = mock_result

            # Act
            response = client.post(
                "/docreader/chat/structure",
                json={"session_id": "test-session", "prompt": xss_payload}
            )

        # Assert - 検証項目1: APIがクラッシュせず200を返す
        assert response.status_code == 200
        # Assert - 検証項目2: Content-Type が application/json
        assert "application/json" in response.headers.get("content-type", "")
        # Assert - 検証項目3: JSON形式で返される
        data = response.json()
        assert "response" in data

    def test_sql_injection_like_input(self, client):
        """DOCR-SEC-04: SQLインジェクション風入力

        SQL文字列を含む入力が安全に処理されることを検証。
        """
        # Arrange
        sql_payload = "'; DROP TABLE users; --"

        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as mock_structure:
            mock_structure.return_value = {"title": "safe"}

            # Act
            response = client.post(
                "/docreader/chat/structure",
                json={"session_id": "test-session", "prompt": sql_payload}
            )

        # Assert
        assert response.status_code == 200
        mock_structure.assert_called_once_with(sql_payload)

    def test_path_traversal_like_input(self, client):
        """DOCR-SEC-05: パストラバーサル風入力

        パストラバーサル文字列を含む入力が安全に処理されることを検証。
        """
        # Arrange
        traversal_payload = "../../etc/passwd"

        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as mock_structure:
            mock_structure.return_value = {"title": "safe"}

            # Act
            response = client.post(
                "/docreader/chat/structure",
                json={"session_id": "test-session", "prompt": traversal_payload}
            )

        # Assert
        assert response.status_code == 200

    @pytest.mark.slow
    def test_large_input_handling(self, client):
        """DOCR-SEC-06: 大量入力によるDoS

        非常に長い文字列入力が処理されることを検証。

        NOTE: 現在の実装にはリクエストボディサイズ制限がないため、
        200（処理成功）が期待される。DoS対策はインフラレベルで実施推奨。

        PERFORMANCE: このテストは1MBのペイロードを使用するため、
        環境によっては不安定になる可能性あり。
        pytest.mark.slow でマークし、通常の高速テストスイートから除外可能。
        実行例: pytest -m "not slow" で除外
        """
        # Arrange
        large_payload = "A" * 1_000_000  # 1MB

        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as mock_structure:
            mock_structure.return_value = {"title": "processed"}

            # Act
            response = client.post(
                "/docreader/chat/structure",
                json={"session_id": "test-session", "prompt": large_payload}
            )

        # Assert
        # 実装にサイズ制限がないため200が期待される
        assert response.status_code == 200

    def test_predictable_session_id(self, client):
        """DOCR-SEC-07: セッションID推測防止

        推測可能なセッションIDでも処理されることを検証。
        セッションIDの検証は別レイヤー（認証）で行われる想定。
        """
        # Arrange
        predictable_session_id = "1"

        with patch("app.doc_reader_plugin.router.invoke_chat_graph", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = "Response"

            # Act
            response = client.post(
                "/docreader/chat",
                json={"session_id": predictable_session_id, "prompt": "質問"}
            )

        # Assert
        assert response.status_code == 200

    def test_json_injection_chat_request(self, client):
        """DOCR-SEC-08: JSON インジェクション（ChatRequest）

        不正なJSON構造の処理を検証（/docreader/chat/structure エンドポイント）。

        NOTE: ChatRequestはextra未指定（デフォルト: "ignore"）のため、
        追加フィールドは無視されて処理が継続される。
        """
        # Arrange
        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as mock_structure:
            mock_structure.return_value = {"title": "safe"}

            # Act - ChatRequest（extra未指定）
            response = client.post(
                "/docreader/chat/structure",
                content='{"session_id": "test", "prompt": "test", "__proto__": {"admin": true}}',
                headers={"Content-Type": "application/json"}
            )

        # Assert
        # ChatRequestはextra未指定なので追加フィールドは無視され200
        assert response.status_code == 200

    def test_json_injection_docreader_chat_request(self, client):
        """DOCR-SEC-08b: JSON インジェクション（DocReaderChatRequest）

        不正なJSON構造の処理を検証（/docreader/chat エンドポイント）。

        NOTE: DocReaderChatRequestはextra="forbid"のため、
        未定義フィールドが含まれると422エラーになる。
        これはモデル仕様の重要な検証項目。
        """
        # Arrange & Act - DocReaderChatRequest（extra="forbid"）
        response = client.post(
            "/docreader/chat",
            content='{"session_id": "test", "prompt": "test", "__proto__": {"admin": true}}',
            headers={"Content-Type": "application/json"}
        )

        # Assert
        # DocReaderChatRequestはextra="forbid"なので追加フィールドは拒否され422
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert isinstance(detail, list), "Pydantic validation errorはリスト形式"
        assert len(detail) > 0, "少なくとも1つのエラーが含まれる"

        # Pydantic v1/v2 両対応のアサーション
        # - v2: err["type"] == "extra_forbidden"
        # - v1: err["type"] == "value_error.extra"
        # - err["loc"] はリスト/タプル形式（例: ["__proto__"] or ("__proto__",)）
        #   in 演算子で要素として "__proto__" が含まれるかをチェック
        # NOTE: エラー順序が変わっても対応できるよう detail 全体を走査
        found_extra_error = any(
            "type" in err
            and "loc" in err
            and "extra" in err["type"].lower()
            and "__proto__" in err["loc"]  # loc はリスト/タプルなので in で要素チェック
            for err in detail
        )
        assert found_extra_error, (
            f"extra="forbid" による __proto__ 拒否エラーが見つからない: {detail}"
        )

    @pytest.mark.xfail(reason="router.py:68で例外詳細が露出。修正後にxfailを削除")
    def test_internal_path_not_exposed(self, client):
        """DOCR-SEC-09: 内部例外情報の非露出

        内部エラー発生時に、内部パスやモジュール名が
        レスポンスに露出しないことを検証。

        【実装失敗予定】router.py:68 で例外オブジェクトを直接露出している。
        detail=f"Error structuring text from chat [ID: {error_id}]: {e}"
        修正方針: 例外詳細を削除し、エラーIDのみを返す。
        """
        # Arrange
        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as mock_structure:
            mock_structure.side_effect = Exception("Error in /app/doc_reader_plugin/router.py")

            # Act
            response = client.post(
                "/docreader/chat/structure",
                json={"session_id": "test-session", "prompt": "テスト"}
            )

        # Assert
        assert response.status_code == 500
        detail = response.json()["detail"]
        # 実装修正後にこのアサーションが成功するはず
        assert "/app/" not in detail

    def test_unicode_control_characters(self, client):
        """DOCR-SEC-10: Unicode制御文字の処理

        Unicode制御文字を含む入力が安全に処理されることを検証。

        NOTE: 現在の実装では制御文字の検証を行っていないため200が期待される。
        """
        # Arrange
        # NULL文字、改行、タブ、RTL制御文字などを含む
        unicode_payload = "テスト\x00\n\t\u200fテキスト"

        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as mock_structure:
            mock_structure.return_value = {"title": "safe"}

            # Act
            response = client.post(
                "/docreader/chat/structure",
                json={"session_id": "test-session", "prompt": unicode_payload}
            )

        # Assert
        assert response.status_code == 200

    @pytest.mark.xfail(reason="router.py:68で例外詳細が露出。修正後にxfailを削除")
    def test_sensitive_info_not_leaked(self, client):
        """DOCR-SEC-11: 機密情報漏洩防止

        例外メッセージに機密情報（API Key、DB接続文字列）が含まれる場合でも、
        レスポンスに露出しないことを検証。

        【実装失敗予定】router.py:68 で例外オブジェクトを直接露出している。
        """
        # Arrange
        sensitive_error = "Connection failed: password=secret123, api_key=sk-xxx"

        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as mock_structure:
            mock_structure.side_effect = Exception(sensitive_error)

            # Act
            response = client.post(
                "/docreader/chat/structure",
                json={"session_id": "test-session", "prompt": "テスト"}
            )

        # Assert
        assert response.status_code == 500
        detail = response.json()["detail"]
        # 実装修正後にこれらのアサーションが成功するはず
        assert "password=" not in detail
        assert "api_key=" not in detail

    def test_ssrf_prevention_current_source_document(self, client):
        """DOCR-SEC-12: SSRF防止（currentSourceDocument）

        currentSourceDocumentに内部URLを指定した場合の動作を検証。

        NOTE: 現在の実装ではURL検証を行っていないため、
        値はそのまま渡される。SSRF対策は別レイヤーで実施推奨。
        """
        # Arrange
        internal_urls = [
            "http://169.254.169.254/latest/meta-data/",  # AWS metadata
            "http://localhost:8080/admin",
            "file:///etc/passwd"
        ]

        for url in internal_urls:
            with patch("app.doc_reader_plugin.router.invoke_chat_graph", new_callable=AsyncMock) as mock_invoke:
                mock_invoke.return_value = "Response"

                # Act
                response = client.post(
                    "/docreader/chat",
                    json={
                        "session_id": "test-session",
                        "prompt": "質問",
                        "currentSourceDocument": url
                    }
                )

            # Assert
            # URL検証が未実装のため200が返る
            assert response.status_code == 200

    def test_command_injection_prevention(self, client):
        """DOCR-SEC-13: コマンドインジェクション防止

        コマンドインジェクション文字列を含む入力が安全に処理されることを検証。
        """
        # Arrange
        command_payloads = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "$(whoami)",
            "`id`"
        ]

        for payload in command_payloads:
            with patch("app.doc_reader_plugin.router.structure_item_with_llm") as mock_structure:
                mock_structure.return_value = {"title": "safe"}

                # Act
                response = client.post(
                    "/docreader/chat/structure",
                    json={"session_id": "test-session", "prompt": payload}
                )

            # Assert
            assert response.status_code == 200

    def test_deeply_nested_json(self, client):
        """DOCR-SEC-14: 深いネストJSON

        深くネストされたJSON構造が適切に処理されることを検証。
        """
        # Arrange
        # 深いネスト構造を作成
        deep_value = "value"
        for _ in range(50):
            deep_value = {"nested": deep_value}

        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as mock_structure:
            mock_structure.return_value = {"title": "safe"}

            # Act
            response = client.post(
                "/docreader/chat/structure",
                json={
                    "session_id": "test-session",
                    "prompt": "test",
                    "context": deep_value
                }
            )

        # Assert
        # 深いネストでもPydanticが処理するか、バリデーションエラーになる
        assert response.status_code in [200, 422]
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_router_module` | テスト間のモジュール状態リセット | function | Yes |
| `app` | テスト用FastAPIアプリケーション | function | No |
| `client` | テスト用HTTPクライアント | function | No |

### 共通フィクスチャ定義

```python
# test/unit/doc_reader_plugin/conftest.py
import sys
import pytest
from unittest.mock import AsyncMock  # async関数モック用
from fastapi.testclient import TestClient
from fastapi import FastAPI


@pytest.fixture(autouse=True)
def reset_router_module():
    """テストごとにモジュールのグローバル状態をリセット

    router.py はモジュールレベルでAPIRouterを定義しているため、
    テスト間の状態汚染を防ぐためにリセットが必要。

    NOTE: この処理は各テストで実行されるためオーバーヘッドがある。
    テスト間の独立性が確実に必要な場合のみ有効化を検討。
    """
    yield
    # テスト後にクリーンアップ
    modules_to_remove = [
        key for key in sys.modules
        if key.startswith("app.doc_reader_plugin")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def app():
    """テスト用FastAPIアプリケーション

    router.py のルーターを含む最小限のアプリケーションを作成。
    """
    from app.doc_reader_plugin.router import router
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """テスト用HTTPクライアント

    FastAPIのTestClientを使用した同期テスト用クライアント。
    TestClientは非同期エンドポイントを同期的にテストできるため、
    テスト関数は通常のdefで記述する。
    """
    return TestClient(app)
```

---

## 6. テスト実行例

```bash
# router関連テストのみ実行
pytest test/unit/doc_reader_plugin/test_router.py -v

# 特定のテストクラスのみ実行
pytest test/unit/doc_reader_plugin/test_router.py::TestStructureTextFromChat -v
pytest test/unit/doc_reader_plugin/test_router.py::TestHandleChatRoute -v

# カバレッジ付きで実行
pytest test/unit/doc_reader_plugin/test_router.py --cov=app.doc_reader_plugin.router --cov-report=term-missing -v

# セキュリティマーカーで実行
# NOTE: 現在の pyproject.toml には [tool.pytest.ini_options] セクションが存在しないため、
#       テスト実行前に以下を追加する必要があります:
#       [tool.pytest.ini_options]
#       markers = ["security: セキュリティ関連テスト", "slow: 遅いテスト（大量入力など）"]
pytest test/unit/doc_reader_plugin/test_router.py -m "security" -v

# 遅いテスト（1MB入力など）を除外して実行
pytest test/unit/doc_reader_plugin/test_router.py -m "not slow" -v

# 失敗時に詳細表示
pytest test/unit/doc_reader_plugin/test_router.py -v --tb=long
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 8 | DOCR-001 〜 DOCR-008 |
| 異常系 | 9 | DOCR-E01 〜 DOCR-E09 |
| セキュリティ | 15 | DOCR-SEC-01 〜 DOCR-SEC-14, DOCR-SEC-08b |
| **合計** | **32** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestStructureTextFromChat` | DOCR-001, DOCR-002, DOCR-006, DOCR-008 | 4 |
| `TestHandleChatRoute` | DOCR-003, DOCR-004, DOCR-005, DOCR-007 | 4 |
| `TestStructureTextFromChatErrors` | DOCR-E01 〜 DOCR-E05 | 5 |
| `TestHandleChatRouteErrors` | DOCR-E06 〜 DOCR-E09 | 4 |
| `TestDocReaderRouterSecurity` | DOCR-SEC-01 〜 DOCR-SEC-14, DOCR-SEC-08b | 15 |

### 実装失敗が予想されるテスト

以下のテストは現在の実装では**意図的に失敗**する可能性があります。

| テストID | 失敗理由 | 修正方針 | pytest.mark |
|---------|---------|---------|------------|
| DOCR-SEC-09 | `router.py:68` で例外オブジェクトを直接露出（`detail=f"...{e}"`） | 例外詳細を削除し、エラーIDのみを返す | `@pytest.mark.xfail` |
| DOCR-SEC-11 | 同上。機密情報を含む例外メッセージがレスポンスに露出 | 同上 | `@pytest.mark.xfail` |

### OWASP Top 10 カバレッジ

| OWASP 2021 | カバレッジ | 関連テストID |
|------------|-----------|-------------|
| A01: Broken Access Control | 部分的 | DOCR-SEC-07 |
| A02: Cryptographic Failures | N/A | - |
| A03: Injection | ✅ | DOCR-SEC-03, DOCR-SEC-04, DOCR-SEC-05, DOCR-SEC-08, DOCR-SEC-13 |
| A04: Insecure Design | 部分的 | - |
| A05: Security Misconfiguration | ✅ | DOCR-SEC-02, DOCR-SEC-09, DOCR-SEC-11 |
| A06: Vulnerable Components | N/A | - |
| A07: Auth Failures | 部分的 | DOCR-SEC-07 |
| A08: Data Integrity Failures | 部分的 | DOCR-SEC-08 |
| A09: Logging Failures | ✅ | DOCR-SEC-01 |
| A10: SSRF | 部分的 | DOCR-SEC-12 |

### 注意事項

- `@pytest.mark.security` と `@pytest.mark.slow` は未登録だと `PytestUnknownMarkWarning` が発生
  - **現在の `pyproject.toml` には `[tool.pytest.ini_options]` セクションが存在しません**
  - テスト実行前に以下のセクションを `pyproject.toml` に追加する必要があります:
    ```toml
    [tool.pytest.ini_options]
    markers = [
        "security: セキュリティ関連テスト",
        "slow: 遅いテスト（大量入力など）"
    ]
    ```
  - `--strict-markers` オプション使用時はマーカー未登録でテストが失敗します
- TestClient は非同期エンドポイントを同期的にテスト可能（`async def` 不要）
- **CRITICAL**: `invoke_chat_graph` は async 関数のため、モックには `AsyncMock` を使用すること
  - `patch(..., new_callable=AsyncMock)` を使用
  - 通常の `MagicMock.return_value` では `TypeError` が発生する
- 外部LLM接続は全てモック化必須
- ImportError時の動作（router.py:15-20）はモジュール読み込み時に発生するため、
  通常のユニットテストではカバー困難。実装改善を推奨

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | ImportError時のグレースフルデグラデーション未実装 | `structure_item_with_llm` が未定義時に NameError | try-except内でフォールバック関数を定義するか、HTTPException(503)を返す |
| 2 | リクエストボディサイズ制限なし | DoS攻撃の可能性 | FastAPI の body サイズ制限設定、またはインフラレベルで対応 |
| 3 | セッションID検証なし | 任意のセッションIDで処理可能 | 認証レイヤーでの検証（別モジュール責務） |
| 4 | 構造化データの保存未実装 | TODO コメントあり（router.py:49-50） | 将来のインデックス保存機能実装時に対応 |
| 5 | エラーメッセージに例外詳細が露出 | 機密情報漏洩の可能性（router.py:68） | 例外詳細を削除し、エラーIDのみを返す |
| 6 | currentSourceDocumentのURL検証なし | SSRF攻撃の可能性 | URLスキームのホワイトリスト検証を実装 |
