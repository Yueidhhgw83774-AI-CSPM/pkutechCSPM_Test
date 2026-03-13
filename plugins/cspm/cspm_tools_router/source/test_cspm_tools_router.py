"""
CSPM Tools Router 単元テスト (29 tests)

テスト規格: cspm_tools_router_tests.md
正常系:10, 異常系:12, セキュリティ:7

注意: sys.path と weasyprint mock は conftest.py で設定済み
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


# ==================== 正常系 (CSPM-TR-001~010) ====================
class TestToolsValidateEndpoint:
    @pytest.mark.asyncio
    async def test_validate_success(self, async_client, mock_tools_available):
        """CSPM-TR-001: ポリシー検証成功"""
        r = await async_client.post("/cspm-tools/validate", json={"policy_content": '[{"name":"t","resource":"s3"}]'})
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert "successful" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_validate_failure(self, async_client, mock_tools_available):
        """CSPM-TR-002: ポリシー検証失敗"""
        mock_tools_available["validate"].invoke.return_value = "Validation failed"
        r = await async_client.post("/cspm-tools/validate", json={"policy_content": '[{"invalid"}]'})
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is False
        assert "failed" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_validate_empty_policy(self, async_client, mock_tools_available):
        """CSPM-TR-003: 空ポリシー検証"""
        # 空文字列は ValidatePolicyRequest の min_length=1 で 422 エラー
        r = await async_client.post("/cspm-tools/validate", json={"policy_content": ""})
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_validate_json_response_structure(self, async_client, mock_tools_available):
        """CSPM-TR-010: JSONレスポンス構造検証"""
        r = await async_client.post("/cspm-tools/validate", json={"policy_content": "[]"})
        data = r.json()
        assert "success" in data
        assert "message" in data


class TestToolsSchemaEndpoint:
    @pytest.mark.asyncio
    async def test_schema_success(self, async_client, mock_tools_available):
        """CSPM-TR-004: スキーマ取得成功"""
        r = await async_client.post("/cspm-tools/schema", json={"target": "aws.ec2"})
        assert r.status_code == 200
        data = r.json()
        assert "resources" in data["schema_content"]

    @pytest.mark.asyncio
    async def test_schema_empty_target(self, async_client, mock_tools_available):
        """CSPM-TR-005: 空ターゲット (target は Optional)"""
        # target は Optional なので省略可能
        r = await async_client.post("/cspm-tools/schema", json={})
        assert r.status_code == 200


class TestToolsResourcesEndpoint:
    @pytest.mark.asyncio
    async def test_resources_success(self, async_client, mock_tools_available):
        """CSPM-TR-006: リソース一覧取得成功"""
        r = await async_client.post("/cspm-tools/resources", json={"cloud": "aws"})
        assert r.status_code == 200
        data = r.json()
        assert "resources" in data
        assert data["cloud"] == "aws"

    @pytest.mark.asyncio
    async def test_resources_invalid_cloud(self, async_client, mock_tools_available):
        """CSPM-TR-007: 無効なクラウド指定"""
        # cloud は Literal["aws", "azure", "gcp"] なので "invalid" は 422 エラー
        r = await async_client.post("/cspm-tools/resources", json={"cloud": "invalid"})
        assert r.status_code == 422


class TestToolsReferenceEndpoint:
    @pytest.mark.asyncio
    async def test_reference_success(self, async_client, mock_tools_available):
        """CSPM-TR-008: RAG検索成功"""
        r = await async_client.post("/cspm-tools/reference", json={"query": "S3 encryption", "cloud": "aws"})
        assert r.status_code == 200
        data = r.json()
        assert "references" in data
        assert data["query"] == "S3 encryption"

    @pytest.mark.asyncio
    async def test_reference_no_results(self, async_client, mock_tools_available):
        """CSPM-TR-009: RAG検索結果なし"""
        mock_tools_available["reference"].ainvoke.return_value = "No results found"
        r = await async_client.post("/cspm-tools/reference", json={"query": "nonexistent", "cloud": "aws"})
        assert r.status_code == 200


# ==================== 異常系 (CSPM-TR-E01~E12) ====================
class TestToolsUnavailable:
    @pytest.mark.asyncio
    async def test_validate_tool_unavailable(self, async_client):
        """CSPM-TR-E01: validate_policy の利用不可"""
        with patch("app.cspm_plugin.tools_router.TOOLS_AVAILABLE", False):
            r = await async_client.post("/cspm-tools/validate", json={"policy_content": "[]"})
            assert r.status_code == 503

    @pytest.mark.asyncio
    async def test_schema_tool_unavailable(self, async_client):
        """CSPM-TR-E02: get_custodian_schema の利用は不可です"""
        with patch("app.cspm_plugin.tools_router.TOOLS_AVAILABLE", False):
            r = await async_client.post("/cspm-tools/schema", json={"target": "aws"})
            assert r.status_code == 503

    @pytest.mark.asyncio
    async def test_resources_tool_unavailable(self, async_client):
        """CSPM-TR-E03: list_available_resources の利用不可"""
        with patch("app.cspm_plugin.tools_router.TOOLS_AVAILABLE", False):
            r = await async_client.post("/cspm-tools/resources", json={"cloud": "aws"})
            assert r.status_code == 503

    @pytest.mark.asyncio
    async def test_reference_tool_unavailable(self, async_client):
        """CSPM-TR-E04: retrieve_reference の利用は不可です"""
        with patch("app.cspm_plugin.tools_router.TOOLS_AVAILABLE", False):
            r = await async_client.post("/cspm-tools/reference", json={"query": "test", "cloud": "aws"})
            assert r.status_code == 503


class TestToolsEndpointExceptions:
    @pytest.mark.asyncio
    async def test_validate_exception(self, async_client, mock_tools_available):
        """CSPM-TR-E05: validate 実行例外"""
        mock_tools_available["validate"].invoke.side_effect = RuntimeError("Tool error")
        r = await async_client.post("/cspm-tools/validate", json={"policy_content": "[]"})
        assert r.status_code == 500

    @pytest.mark.asyncio
    async def test_schema_exception(self, async_client, mock_tools_available):
        """CSPM-TR-E06: schema 実行例外"""
        mock_tools_available["schema"].invoke.side_effect = RuntimeError("Schema error")
        r = await async_client.post("/cspm-tools/schema", json={"target": "aws"})
        assert r.status_code == 500

    @pytest.mark.asyncio
    async def test_resources_exception(self, async_client, mock_tools_available):
        """CSPM-TR-E07: resources 実行例外"""
        mock_tools_available["resources"].invoke.side_effect = RuntimeError("Resources error")
        r = await async_client.post("/cspm-tools/resources", json={"cloud": "aws"})
        assert r.status_code == 500

    @pytest.mark.asyncio
    async def test_reference_exception(self, async_client, mock_tools_available):
        """CSPM-TR-E08: reference 実行例外"""
        mock_tools_available["reference"].ainvoke.side_effect = RuntimeError("Reference error")
        r = await async_client.post("/cspm-tools/reference", json={"query": "test", "cloud": "aws"})
        assert r.status_code == 500


class TestToolsValidationErrors:
    @pytest.mark.asyncio
    async def test_validate_missing_policy_content(self, async_client):
        """CSPM-TR-E09: policy_content 謎落"""
        r = await async_client.post("/cspm-tools/validate", json={})
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_schema_missing_target(self, async_client):
        """CSPM-TR-E10: target 欠落 (Optional なので 200)"""
        # target は Optional[str] なので省略可能
        r = await async_client.post("/cspm-tools/schema", json={})
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_resources_missing_cloud(self, async_client):
        """CSPM-TR-E11: cloud 脱落"""
        r = await async_client.post("/cspm-tools/resources", json={})
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_reference_missing_query(self, async_client):
        """CSPM-TR-E12: query 欠落"""
        r = await async_client.post("/cspm-tools/reference", json={"cloud": "aws"})
        assert r.status_code == 422


# ==================== セキュリティテスト (CSPM-TR-SEC-01~07) ====================
@pytest.mark.security
class TestToolsRouterSecurity:
    @pytest.mark.xfail(reason="tools_router.py の全4エンドポイントで str(e) が detail に含まれる既知の脆弱性", strict=True)
    @pytest.mark.asyncio
    async def test_validate_error_no_internal_details(self, async_client, mock_tools_available):
        """CSPM-TR-SEC-01: validate エラー時に内部詳細非露出"""
        mock_tools_available["validate"].invoke.side_effect = ConnectionError("Failed to connect to 192.168.1.100:5432")
        r = await async_client.post("/cspm-tools/validate", json={"policy_content": "[]"})
        assert r.status_code == 500
        assert "192.168.1.100" not in r.json()["detail"]

    @pytest.mark.asyncio
    async def test_validate_xss_in_policy_content(self, async_client, mock_tools_available):
        """CSPM-TR-SEC-02: XSS攻撃文字列の安全処理"""
        r = await async_client.post("/cspm-tools/validate", json={"policy_content": "<script>alert('XSS')</script>"})
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_schema_command_injection(self, async_client, mock_tools_available):
        """CSPM-TR-SEC-03: コマンドインジェクション防止"""
        r = await async_client.post("/cspm-tools/schema", json={"target": "aws; rm -rf /"})
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_resources_sql_injection(self, async_client, mock_tools_available):
        """CSPM-TR-SEC-04: SQLインジェクション風入力"""
        # cloud は Literal["aws", "azure", "gcp"] で検証されるため、
        # 不正な値は 422 エラーになる（これはセキュリティ機能として正しい）
        r = await async_client.post("/cspm-tools/resources", json={"cloud": "aws'; DROP TABLE resources; --"})
        assert r.status_code == 422  # Pydantic バリデーションで拒否される

    @pytest.mark.asyncio
    async def test_reference_query_injection(self, async_client, mock_tools_available):
        """CSPM-TR-SEC-05: RAG検索クエリインジェクション"""
        r = await async_client.post("/cspm-tools/reference", json={"query": '"; DROP TABLE docs; --', "cloud": "aws"})
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_validate_log_injection(self, async_client, mock_tools_available, caplog):
        """CSPM-TR-SEC-06: ログインジェクション（改行文字）"""
        import logging
        with caplog.at_level(logging.DEBUG):
            r = await async_client.post("/cspm-tools/validate", json={"policy_content": "test\n[CRITICAL] Fake log"})
            assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_schema_unicode_normalization(self, async_client, mock_tools_available):
        """CSPM-TR-SEC-07: Unicode正規化攻撃"""
        r = await async_client.post("/cspm-tools/schema", json={"target": "ａｗｓ"})  # 全角文字
        assert r.status_code == 200

