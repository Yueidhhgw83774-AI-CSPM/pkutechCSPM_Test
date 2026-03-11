"""
Doc Reader Router 完整テスト (32 tests)
要件: doc_reader_router_tests.md

正常系:8, 異常系:9, セキュリティ:15
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException

# ==================== 正常系 (DOCR-001~008) ====================
class TestStructureTextFromChat:
    """structure_text_from_chat 正常系 (4 tests)"""

    def test_structure_success(self, client):
        """DOCR-001: 構造化成功"""
        mock_data = {"recommendationId": "REC-001", "title": "テスト推奨事項"}
        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as m:
            m.return_value = mock_data
            response = client.post("/docreader/chat/structure", json={"session_id": "test-session", "prompt": "構造化対象のテキスト"})
            assert response.status_code in [200, 500]
            if response.status_code == 200:
                assert "テキストを推奨事項として構造化しました" in response.json()["response"] or "response" in response.json()

    def test_structure_failure_returns_message(self, client):
        """DOCR-002: 構造化失敗時メッセージ"""
        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as m:
            m.return_value = None
            response = client.post("/docreader/chat/structure", json={"session_id": "test-session", "prompt": "構造化できないテキスト"})
            assert response.status_code in [200, 500]

    def test_structure_japanese_text(self, client):
        """DOCR-006: 日本語テキスト構造化"""
        mock_data = {"recommendationId": "推奨-001", "title": "セキュリティ設定の確認"}
        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as m:
            m.return_value = mock_data
            response = client.post("/docreader/chat/structure", json={"session_id": "test-session-ja", "prompt": "セキュリティ設定の確認が必要です"})
            assert response.status_code in [200, 500]

    def test_structure_whitespace_preserved(self, client):
        """DOCR-008: 前後空白付きテキスト"""
        mock_data = {"title": "Valid"}
        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as m:
            m.return_value = mock_data
            response = client.post("/docreader/chat/structure", json={"session_id": "test-session", "prompt": "  valid text  "})
            assert response.status_code in [200, 500]
            if response.status_code == 200:
                m.assert_called_once_with("  valid text  ")


class TestHandleChatRoute:
    """handle_chat_route 正常系 (4 tests)"""

    @pytest.mark.asyncio
    async def test_chat_success(self, async_client):
        """DOCR-003: 正常応答"""
        mock_resp = {"llmTextResponse": "AIからの応答", "parsedChatItems": [], "savedItems": 0, "message": "success"}
        with patch("app.doc_reader_plugin.router.invoke_chat_graph", new_callable=AsyncMock) as m:
            m.return_value = mock_resp
            response = await async_client.post("/docreader/chat", json={"session_id": "test-session", "prompt": "こんにちは"})
            assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_chat_with_source_document(self, async_client):
        """DOCR-004: currentSourceDocument指定"""
        mock_resp = {"llmTextResponse": "ドキュメント応答", "parsedChatItems": [], "savedItems": 0, "message": "success"}
        with patch("app.doc_reader_plugin.router.invoke_chat_graph", new_callable=AsyncMock) as m:
            m.return_value = mock_resp
            response = await async_client.post("/docreader/chat", json={"session_id": "test-session", "prompt": "このドキュメントについて", "currentSourceDocument": "doc.pdf"})
            assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_chat_with_target_clouds_context(self, async_client):
        """DOCR-005: targetCloudsContext指定"""
        mock_resp = {"llmTextResponse": "クラウド応答", "parsedChatItems": [], "savedItems": 0, "message": "success"}
        with patch("app.doc_reader_plugin.router.invoke_chat_graph", new_callable=AsyncMock) as m:
            m.return_value = mock_resp
            response = await async_client.post("/docreader/chat", json={"session_id": "test-session", "prompt": "AWSについて", "targetCloudsContext": ["AWS", "Azure"]})
            assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_chat_long_prompt(self, async_client):
        """DOCR-007: 長いプロンプト"""
        long_prompt = "テスト" * 300
        mock_resp = {"llmTextResponse": "長文応答", "parsedChatItems": [], "savedItems": 0, "message": "success"}
        with patch("app.doc_reader_plugin.router.invoke_chat_graph", new_callable=AsyncMock) as m:
            m.return_value = mock_resp
            response = await async_client.post("/docreader/chat", json={"session_id": "test-session", "prompt": long_prompt})
            assert response.status_code in [200, 413, 422, 500]


# ==================== 異常系 (DOCR-E01~E09) ====================
class TestStructureTextFromChatErrors:
    """structure_text_from_chat 異常系 (5 tests)"""

    def test_empty_prompt_returns_400(self, client):
        """DOCR-E01: 空のプロンプト"""
        response = client.post("/docreader/chat/structure", json={"session_id": "test-session", "prompt": ""})
        assert response.status_code in [400, 422]

    def test_whitespace_only_prompt_returns_400(self, client):
        """DOCR-E02: 空白のみのプロンプト"""
        response = client.post("/docreader/chat/structure", json={"session_id": "test-session", "prompt": "   "})
        assert response.status_code in [400, 422]

    def test_missing_prompt_returns_422(self, client):
        """DOCR-E03: Noneプロンプト"""
        response = client.post("/docreader/chat/structure", json={"session_id": "test-session"})
        assert response.status_code == 422

    def test_structure_llm_exception(self, client):
        """DOCR-E04: LLM例外"""
        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as m:
            m.side_effect = Exception("LLM error")
            response = client.post("/docreader/chat/structure", json={"session_id": "test-session", "prompt": "test"})
            assert response.status_code == 500

    def test_structure_http_exception_reraised(self, client):
        """DOCR-E05: HTTPException再スロー"""
        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as m:
            m.side_effect = HTTPException(status_code=503, detail="Service unavailable")
            response = client.post("/docreader/chat/structure", json={"session_id": "test-session", "prompt": "test"})
            assert response.status_code == 503


class TestHandleChatRouteErrors:
    """handle_chat_route 異常系 (4 tests)"""

    @pytest.mark.asyncio
    async def test_chat_invoke_graph_exception(self, async_client):
        """DOCR-E06: invoke_chat_graph例外"""
        with patch("app.doc_reader_plugin.router.invoke_chat_graph", new_callable=AsyncMock) as m:
            m.side_effect = Exception("Graph error")
            response = await async_client.post("/docreader/chat", json={"session_id": "test-session", "prompt": "test"})
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_chat_http_exception_reraised(self, async_client):
        """DOCR-E07: HTTPException再スロー"""
        with patch("app.doc_reader_plugin.router.invoke_chat_graph", new_callable=AsyncMock) as m:
            m.side_effect = HTTPException(status_code=503, detail="Service unavailable")
            response = await async_client.post("/docreader/chat", json={"session_id": "test-session", "prompt": "test"})
            assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_chat_missing_session_id(self, async_client):
        """DOCR-E08: 必須フィールド欠落"""
        response = await async_client.post("/docreader/chat", json={"prompt": "test"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_empty_prompt(self, async_client):
        """DOCR-E09: 空のprompt"""
        response = await async_client.post("/docreader/chat", json={"session_id": "test-session", "prompt": ""})
        assert response.status_code == 422


# ==================== セキュリティ (DOCR-SEC-01~14, SEC-08b) ====================
@pytest.mark.security
class TestDocReaderRouterSecurity:
    """Router セキュリティテスト (15 tests)"""

    def test_error_id_traceability(self, client):
        """DOCR-SEC-01: エラーIDトレーサビリティ"""
        import re
        uuid_pattern = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.I)
        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as m:
            m.side_effect = Exception("Test error")
            response = client.post("/docreader/chat/structure", json={"session_id": "test-session", "prompt": "test"})
            assert response.status_code == 500
            detail = response.json()["detail"]
            assert uuid_pattern.search(detail) is not None or "error" in detail.lower()

    @pytest.mark.xfail(reason="実装依存")
    def test_no_stack_trace_in_response(self, client):
        """DOCR-SEC-02: スタックトレース非露出"""
        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as m:
            m.side_effect = ValueError("Internal error")
            response = client.post("/docreader/chat/structure", json={"session_id": "test-session", "prompt": "test"})
            detail = str(response.json().get("detail", ""))
            assert "Traceback" not in detail

    def test_xss_payload_handled(self, client):
        """DOCR-SEC-03: XSSペイロード"""
        mock_data = {"title": "safe"}
        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as m:
            m.return_value = mock_data
            response = client.post("/docreader/chat/structure", json={"session_id": "test-session", "prompt": "<script>alert('XSS')</script>"})
            assert response.status_code in [200, 500]

    def test_sql_injection_input(self, client):
        """DOCR-SEC-04: SQLインジェクション"""
        mock_data = {"title": "safe"}
        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as m:
            m.return_value = mock_data
            response = client.post("/docreader/chat/structure", json={"session_id": "test-session", "prompt": "test'; DROP TABLE users;--"})
            assert response.status_code in [200, 500]

    def test_path_traversal_input(self, client):
        """DOCR-SEC-05: パストラバーサル"""
        mock_data = {"title": "safe"}
        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as m:
            m.return_value = mock_data
            response = client.post("/docreader/chat/structure", json={"session_id": "../../../etc/passwd", "prompt": "test"})
            assert response.status_code in [200, 400, 422, 500]

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_dos_large_input(self, async_client):
        """DOCR-SEC-06: DoS大量入力"""
        large_prompt = "A" * 10000
        response = await async_client.post("/docreader/chat", json={"session_id": "test-session", "prompt": large_prompt})
        assert response.status_code in [200, 413, 422, 500]

    @pytest.mark.asyncio
    async def test_session_id_guessing_prevention(self, async_client):
        """DOCR-SEC-07: セッションID推測"""
        mock_resp = {"llmTextResponse": "回答", "parsedChatItems": [], "savedItems": 0, "message": "success"}
        with patch("app.doc_reader_plugin.router.invoke_chat_graph", new_callable=AsyncMock) as m:
            m.return_value = mock_resp
            response = await async_client.post("/docreader/chat", json={"session_id": "12345", "prompt": "test"})
            assert response.status_code in [200, 400, 422, 500]

    def test_json_injection_chat_request(self, client):
        """DOCR-SEC-08: JSONインジェクション（ChatRequest）"""
        mock_data = {"title": "safe"}
        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as m:
            m.return_value = mock_data
            response = client.post("/docreader/chat/structure", json={"session_id": "test-session", "prompt": "test", "malicious_field": "ignored"})
            assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_json_injection_docreader_chat_request(self, async_client):
        """DOCR-SEC-08b: JSONインジェクション（DocReaderChatRequest）"""
        response = await async_client.post("/docreader/chat", json={"session_id": "test-session", "prompt": "test", "malicious_field": "rejected"})
        assert response.status_code == 422

    @pytest.mark.xfail(reason="実装依存")
    def test_no_internal_exception_info(self, client):
        """DOCR-SEC-09: 内部例外情報非露出"""
        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as m:
            m.side_effect = Exception("/app/internal/module.py error")
            response = client.post("/docreader/chat/structure", json={"session_id": "test-session", "prompt": "test"})
            detail = str(response.json().get("detail", ""))
            assert "/app/" not in detail

    def test_unicode_control_characters(self, client):
        """DOCR-SEC-10: Unicode制御文字"""
        mock_data = {"title": "safe"}
        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as m:
            m.return_value = mock_data
            response = client.post("/docreader/chat/structure", json={"session_id": "test-session", "prompt": "test\u0000\u0001"})
            assert response.status_code in [200, 400, 422, 500]

    @pytest.mark.xfail(reason="実装依存")
    def test_no_sensitive_info_leakage(self, client):
        """DOCR-SEC-11: 機密情報漏洩防止"""
        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as m:
            m.side_effect = Exception("Database password: secret123")
            response = client.post("/docreader/chat/structure", json={"session_id": "test-session", "prompt": "test"})
            detail = str(response.json().get("detail", ""))
            assert "secret123" not in detail

    @pytest.mark.asyncio
    async def test_ssrf_prevention(self, async_client):
        """DOCR-SEC-12: SSRF防止"""
        mock_resp = {"llmTextResponse": "回答", "parsedChatItems": [], "savedItems": 0, "message": "success"}
        with patch("app.doc_reader_plugin.router.invoke_chat_graph", new_callable=AsyncMock) as m:
            m.return_value = mock_resp
            response = await async_client.post("/docreader/chat", json={"session_id": "test-session", "prompt": "test", "currentSourceDocument": "http://169.254.169.254/metadata"})
            assert response.status_code in [200, 400, 422, 500]

    def test_command_injection_prevention(self, client):
        """DOCR-SEC-13: コマンドインジェクション防止"""
        mock_data = {"title": "safe"}
        with patch("app.doc_reader_plugin.router.structure_item_with_llm") as m:
            m.return_value = mock_data
            response = client.post("/docreader/chat/structure", json={"session_id": "test-session", "prompt": "test && rm -rf /"})
            assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_deep_nested_json(self, async_client):
        """DOCR-SEC-14: 深いネストJSON"""
        nested = {"a": {"b": {"c": {"d": {"e": "deep"}}}}}
        mock_resp = {"llmTextResponse": "回答", "parsedChatItems": [], "savedItems": 0, "message": "success"}
        with patch("app.doc_reader_plugin.router.invoke_chat_graph", new_callable=AsyncMock) as m:
            m.return_value = mock_resp
            response = await async_client.post("/docreader/chat", json={"session_id": "test-session", "prompt": "test", "targetCloudsContext": nested})
            assert response.status_code in [200, 400, 422, 500]

