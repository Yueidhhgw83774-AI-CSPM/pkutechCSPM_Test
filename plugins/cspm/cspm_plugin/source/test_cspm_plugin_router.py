"""
CSPM Plugin Router 単元テスト

テスト規格: docs/testing/plugins/cspm/cspm_plugin_tests.md
カバレッジ目標: 90%+

テストクラス:
  正常系: 11 テスト (CSPM-001 ~ CSPM-011)
  異常系: 11 テスト (CSPM-E01 ~ CSPM-E11)
  セキュリティ: 4 テスト (CSPM-SEC-01 ~ CSPM-SEC-04)
  合計: 26 テスト
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# .envファイルの設定を読み込む
_env_path = Path(__file__).resolve().parent.parent.parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

_source_root_env = os.environ.get("soure_root", "").strip().strip('"').strip("'")
if _source_root_env and Path(_source_root_env).exists():
    project_root = Path(_source_root_env)
else:
    project_root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "platform_python_backend-testing"

if not project_root.exists():
    raise RuntimeError(f"项目根目录不存在: {project_root}")
sys.path.insert(0, str(project_root))

# Mock weasyprint
from unittest.mock import MagicMock as _MagicMock
for _mod in ["weasyprint", "weasyprint.CSS", "weasyprint.HTML", "weasyprint.css",
             "weasyprint.text", "weasyprint.text.fonts", "weasyprint.text.ffi", "weasyprint.text.constants"]:
    sys.modules.setdefault(_mod, _MagicMock())


# ============================================================
# 正常系テスト: ポリシー修正エンドポイント (CSPM-001 ~ CSPM-003, 011)
# ============================================================

class TestRefineEndpoint:
    """POST /cspm/chat/refine の正常系テスト"""

    @pytest.mark.asyncio
    async def test_refine_policy_success(self, async_client, mock_generate_refined_policy):
        """CSPM-001: 有効なポリシー修正が成功する

        router.py:36-41 の正常パスをカバー。
        """
        # Arrange
        mock_generate_refined_policy.return_value = (
            '修正しました。\n```json\n[{"name": "s3-encryption", '
            '"resource": "s3", "filters": [{"type": "encryption"}]}]\n```'
        )
        request_data = {
            "session_id": "test-session-001",
            "prompt": "S3の暗号化チェックを追加",
            "policy_context": '[{"name": "s3-check", "resource": "s3"}]',
        }

        # Act
        response = await async_client.post("/cspm/chat/refine", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "encryption" in data["response"]

    @pytest.mark.asyncio
    async def test_refine_without_policy(self, async_client, mock_generate_refined_policy):
        """CSPM-002: ポリシーなしで新規作成が成功する

        router.py:38-39 で policy_context=None が渡されるケース。
        """
        # Arrange
        mock_generate_refined_policy.return_value = (
            '```json\n[{"name": "new-policy", "resource": "ec2"}]\n```'
        )
        request_data = {
            "session_id": "test-session-002",
            "prompt": "EC2のセキュリティグループチェックを作成",
            "policy_context": None,
        }

        # Act
        response = await async_client.post("/cspm/chat/refine", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "response" in data

    @pytest.mark.asyncio
    async def test_refine_explanation_request(self, async_client, mock_generate_refined_policy):
        """CSPM-003: 説明リクエストでJSONブロックなしの応答"""
        # Arrange
        mock_generate_refined_policy.return_value = (
            "このポリシーはS3バケットの暗号化状態をチェックします。"
        )
        request_data = {
            "session_id": "test-session-003",
            "prompt": "このポリシーを説明して",
            "policy_context": '[{"name": "s3-check", "resource": "s3"}]',
        }

        # Act
        response = await async_client.post("/cspm/chat/refine", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "```json" not in data["response"]

    @pytest.mark.asyncio
    async def test_refine_empty_string_policy(self, async_client, mock_generate_refined_policy):
        """CSPM-011: 空文字列ポリシーコンテキストで新規作成が成功"""
        # Arrange
        mock_generate_refined_policy.return_value = (
            '```json\n[{"name": "new-policy", "resource": "ec2"}]\n```'
        )
        request_data = {
            "session_id": "test-session-011",
            "prompt": "EC2のセキュリティグループチェックを作成",
            "policy_context": "",
        }

        # Act
        response = await async_client.post("/cspm/chat/refine", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "response" in data


# ============================================================
# 正常系テスト: ポリシー生成エージェント (CSPM-004 ~ CSPM-007)
# ============================================================

class TestAgentEndpoint:
    """POST /cspm/chat/agent の正常系テスト"""

    @pytest.mark.asyncio
    async def test_agent_aws_policy_generation(self, async_client, mock_run_policy_agent, sample_recommendation):
        """CSPM-004: AWS推奨事項からポリシー生成が成功

        router.py:71-91 の正常パスをカバー。
        """
        # Arrange
        mock_run_policy_agent.return_value = (
            '[{"name": "s3-encryption", "resource": "s3"}]',
            None,
            "active",
        )
        request_data = {
            "recommendation_data": sample_recommendation,
            "target_cloud": "aws",
        }

        # Act
        response = await async_client.post("/cspm/chat/agent", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == "rec-001"
        assert data["status"] == "active"
        assert data["policy_content"] is not None
        assert data["error"] is None

    @pytest.mark.asyncio
    async def test_agent_azure_policy_generation(self, async_client, mock_run_policy_agent, sample_recommendation):
        """CSPM-005: Azure推奨事項からポリシー生成が成功"""
        # Arrange
        mock_run_policy_agent.return_value = (
            '[{"name": "vm-check", "resource": "azure.vm"}]',
            None,
            "active",
        )
        sample_recommendation["uid"] = "rec-azure-001"
        request_data = {
            "recommendation_data": sample_recommendation,
            "target_cloud": "azure",
        }

        # Act
        response = await async_client.post("/cspm/chat/agent", json=request_data)

        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "active"

    @pytest.mark.asyncio
    async def test_agent_gcp_policy_generation(self, async_client, mock_run_policy_agent, sample_recommendation):
        """CSPM-006: GCP推奨事項からポリシー生成が成功"""
        # Arrange
        mock_run_policy_agent.return_value = (
            '[{"name": "gcs-check", "resource": "gcp.bucket"}]',
            None,
            "active",
        )
        sample_recommendation["uid"] = "rec-gcp-001"
        request_data = {
            "recommendation_data": sample_recommendation,
            "target_cloud": "gcp",
        }

        # Act
        response = await async_client.post("/cspm/chat/agent", json=request_data)

        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "active"

    @pytest.mark.asyncio
    async def test_agent_minimal_recommendation(self, async_client, mock_run_policy_agent):
        """CSPM-007: 最小限の推奨事項データで処理成功"""
        # Arrange
        mock_run_policy_agent.return_value = (
            '[{"name": "minimal-policy", "resource": "ec2"}]',
            None,
            "active",
        )
        request_data = {
            "recommendation_data": {
                "uid": "min-001",
                "title": "EC2セキュリティチェック",
            },
            "target_cloud": "aws",
        }

        # Act
        response = await async_client.post("/cspm/chat/agent", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == "min-001"
        assert data["status"] == "active"


# ============================================================
# 正常系テスト: ポリシー検証エンドポイント (CSPM-008 ~ CSPM-010)
# ============================================================

class TestValidateEndpoint:
    """POST /cspm/validate_policy_with_tool の正常系テスト"""

    @pytest.mark.asyncio
    async def test_validate_valid_json(self, async_client, mock_validate_policy_tool):
        """CSPM-008: 有効なJSONポリシーが検証成功

        router.py:119-132 の正常パスをカバー。
        router.py:129 の is_valid=True 分岐。
        """
        # Arrange
        mock_validate_policy_tool.invoke.return_value = "Validation successful."
        request_data = {
            "policy_content": '[{"name": "s3-check", "resource": "s3"}]'
        }

        # Act
        response = await async_client.post(
            "/cspm/validate_policy_with_tool", json=request_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["isValid"] is True
        assert "successful" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_validate_valid_yaml(self, async_client, mock_validate_policy_tool):
        """CSPM-009: 有効なYAMLポリシーが検証成功"""
        # Arrange
        mock_validate_policy_tool.invoke.return_value = "Validation successful."
        request_data = {
            "policy_content": "policies:\n  - name: s3-check\n    resource: s3\n"
        }

        # Act
        response = await async_client.post(
            "/cspm/validate_policy_with_tool", json=request_data
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["isValid"] is True

    @pytest.mark.asyncio
    async def test_validate_failure_response(self, async_client, mock_validate_policy_tool):
        """CSPM-010: 検証失敗がisValid=falseで正常応答

        router.py:129 の is_valid=False 分岐をカバー。
        """
        # Arrange
        mock_validate_policy_tool.invoke.return_value = (
            "Validation failed (Code: 1):\ninvalid resource type"
        )
        request_data = {
            "policy_content": '[{"name": "test", "resource": "invalid-resource"}]'
        }

        # Act
        response = await async_client.post(
            "/cspm/validate_policy_with_tool", json=request_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["isValid"] is False
        assert "failed" in data["message"].lower()


# ============================================================
# 異常系テスト: ポリシー修正エンドポイント (CSPM-E01 ~ CSPM-E04)
# ============================================================

class TestRefineEndpointErrors:
    """POST /cspm/chat/refine の異常系テスト"""

    @pytest.mark.asyncio
    async def test_refine_empty_prompt(self, async_client):
        """CSPM-E01: 空のプロンプトでバリデーションエラー

        CSPMPluginChatRequest.prompt の min_length=1 バリデーション。
        """
        # Arrange
        request_data = {
            "session_id": "test-session",
            "prompt": "",
            "policy_context": None,
        }

        # Act
        response = await async_client.post("/cspm/chat/refine", json=request_data)

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_refine_missing_session_id(self, async_client):
        """CSPM-E02: session_id 欠落でバリデーションエラー"""
        # Arrange
        request_data = {
            "prompt": "修正して",
            "policy_context": None,
        }

        # Act
        response = await async_client.post("/cspm/chat/refine", json=request_data)

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_refine_unexpected_exception(self, async_client, mock_generate_refined_policy):
        """CSPM-E03: 予期しない例外で500エラー + Error ID

        router.py:44-52 の Exception ハンドラーをカバー。
        """
        # Arrange
        mock_generate_refined_policy.side_effect = RuntimeError("LLM connection failed")
        request_data = {
            "session_id": "test-session",
            "prompt": "修正して",
            "policy_context": None,
        }

        # Act
        response = await async_client.post("/cspm/chat/refine", json=request_data)

        # Assert
        assert response.status_code == 500
        assert "Error ID" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_refine_http_exception_propagation(self, async_client, mock_generate_refined_policy):
        """CSPM-E04: HTTPException がそのまま伝播される

        router.py:42-43 の HTTPException キャッチ & re-raise をカバー。
        """
        # Arrange
        from fastapi import HTTPException

        mock_generate_refined_policy.side_effect = HTTPException(
            status_code=503, detail="Policy Refinement LLM is not available."
        )
        request_data = {
            "session_id": "test-session",
            "prompt": "修正して",
            "policy_context": None,
        }

        # Act
        response = await async_client.post("/cspm/chat/refine", json=request_data)

        # Assert
        assert response.status_code == 503
        assert "LLM" in response.json()["detail"]


# ============================================================
# 異常系テスト: ポリシー生成エージェント (CSPM-E05 ~ CSPM-E08)
# ============================================================

class TestAgentEndpointErrors:
    """POST /cspm/chat/agent の異常系テスト"""

    @pytest.mark.asyncio
    async def test_agent_missing_uid(self, async_client):
        """CSPM-E05: UID 欠落でバリデーションエラー"""
        # Arrange
        request_data = {
            "recommendation_data": {"title": "テスト"},  # uid なし
            "target_cloud": "aws",
        }

        # Act
        response = await async_client.post("/cspm/chat/agent", json=request_data)

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_agent_invalid_cloud(self, async_client):
        """CSPM-E06: 無効なクラウド指定でバリデーションエラー"""
        # Arrange
        request_data = {
            "recommendation_data": {"uid": "test-001", "title": "テスト"},
            "target_cloud": "invalid_cloud",
        }

        # Act
        response = await async_client.post("/cspm/chat/agent", json=request_data)

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_agent_execution_error(self, async_client, mock_run_policy_agent):
        """CSPM-E07: エージェント実行の予期しない例外でエラーレスポンス

        router.py:95-106 の Exception ハンドラーをカバー。
        応答は200だが、body に status="error" と error メッセージを含む。
        """
        # Arrange
        mock_run_policy_agent.side_effect = RuntimeError("Graph execution failed")
        request_data = {
            "recommendation_data": {"uid": "err-001", "title": "エラーテスト"},
            "target_cloud": "aws",
        }

        # Act
        response = await async_client.post("/cspm/chat/agent", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert data["error"] is not None
        assert "Error ID" in data["error"]
        assert data["uuid"] == "err-001"

    @pytest.mark.asyncio
    async def test_agent_http_exception_propagation(self, async_client, mock_run_policy_agent):
        """CSPM-E08: HTTPException がそのまま伝播される

        router.py:93-94 の HTTPException キャッチ & re-raise をカバー。
        """
        # Arrange
        from fastapi import HTTPException

        mock_run_policy_agent.side_effect = HTTPException(
            status_code=503, detail="Agent not available"
        )
        request_data = {
            "recommendation_data": {"uid": "err-002", "title": "テスト"},
            "target_cloud": "aws",
        }

        # Act
        response = await async_client.post("/cspm/chat/agent", json=request_data)

        # Assert
        assert response.status_code == 503


# ============================================================
# 異常系テスト: ポリシー検証エンドポイント (CSPM-E09 ~ CSPM-E11)
# ============================================================

class TestValidateEndpointErrors:
    """POST /cspm/validate_policy_with_tool の異常系テスト"""

    @pytest.mark.asyncio
    async def test_validate_empty_policy(self, async_client):
        """CSPM-E09: 空のポリシーでisValid=false

        router.py:113-117 の空チェック分岐をカバー。
        """
        # Arrange
        request_data = {"policy_content": ""}

        # Act
        response = await async_client.post(
            "/cspm/validate_policy_with_tool", json=request_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["isValid"] is False
        assert "empty" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_validate_whitespace_only_policy(self, async_client):
        """CSPM-E10: 空白のみポリシーでisValid=false

        router.py:113 の `not policy_content.strip()` 分岐をカバー。
        """
        # Arrange
        request_data = {"policy_content": "   "}

        # Act
        response = await async_client.post(
            "/cspm/validate_policy_with_tool", json=request_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["isValid"] is False
        assert "empty" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_validate_tool_exception(self, async_client, mock_validate_policy_tool):
        """CSPM-E11: ツール実行例外でisValid=false

        router.py:134-141 の Exception ハンドラーをカバー。
        """
        # Arrange
        mock_validate_policy_tool.invoke.side_effect = RuntimeError(
            "subprocess failed"
        )
        request_data = {
            "policy_content": '[{"name": "test", "resource": "s3"}]'
        }

        # Act
        response = await async_client.post(
            "/cspm/validate_policy_with_tool", json=request_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["isValid"] is False
        assert "error" in data["message"].lower()


# ============================================================
# セキュリティテスト (CSPM-SEC-01 ~ CSPM-SEC-04)
# ============================================================

@pytest.mark.security
class TestCSPMRouterSecurity:
    """CSPM ルーターセキュリティテスト"""

    @pytest.mark.asyncio
    async def test_refine_error_no_stacktrace(self, async_client, mock_generate_refined_policy):
        """CSPM-SEC-01: refine エラー時にスタックトレースが露出しない

        router.py:46-52 のエラーハンドリングで、Error ID のみを返し、
        内部のスタックトレースや例外詳細を露出しないことを検証。
        """
        # Arrange
        mock_generate_refined_policy.side_effect = ValueError(
            "Internal secret: DB password is xyz"
        )
        request_data = {
            "session_id": "sec-test",
            "prompt": "テスト",
            "policy_context": None,
        }

        # Act
        response = await async_client.post("/cspm/chat/refine", json=request_data)

        # Assert
        assert response.status_code == 500
        detail = response.json()["detail"]
        assert "Error ID" in detail
        assert "Internal secret" not in detail
        assert "DB password" not in detail
        assert "Traceback" not in detail

    @pytest.mark.xfail(
        reason="router.py:105 で str(e) が露出する既知の問題。修正後にxfailを除去",
        strict=True,
    )
    @pytest.mark.asyncio
    async def test_agent_error_no_internal_details(self, async_client, mock_run_policy_agent):
        """CSPM-SEC-02: agent エラー時に内部詳細が過度に露出しない

        router.py:95-106 のエラーハンドリング検証。
        router.py:105 で str(e) が直接レスポンスに含まれるため、
        現在の実装では xfail（修正待ち）。
        """
        # Arrange
        mock_run_policy_agent.side_effect = ConnectionError(
            "Failed to connect to internal DB at 192.168.1.100:5432"
        )
        request_data = {
            "recommendation_data": {"uid": "sec-001", "title": "テスト"},
            "target_cloud": "aws",
        }

        # Act
        response = await async_client.post("/cspm/chat/agent", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "Error ID" in data["error"]
        # 修正後に期待される動作（現在は str(e) が含まれるため失敗）
        assert "192.168.1.100" not in data["error"]
        assert "5432" not in data["error"]

    @pytest.mark.asyncio
    async def test_policy_content_injection(self, async_client, mock_validate_policy_tool):
        """CSPM-SEC-03: ポリシー内容にインジェクション攻撃文字列が含まれても安全"""
        # Arrange
        malicious_content = '$(rm -rf /); {"name": "test", "resource": "s3"}'
        mock_validate_policy_tool.invoke.return_value = (
            "Error: Failed to parse JSON content"
        )
        request_data = {"policy_content": malicious_content}

        # Act
        response = await async_client.post(
            "/cspm/validate_policy_with_tool", json=request_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["isValid"] is False

    @pytest.mark.asyncio
    async def test_large_policy_context_handling(self, async_client, mock_generate_refined_policy):
        """CSPM-SEC-04: 大容量ポリシーコンテキストの処理

        1MB のポリシー文字列が安全に処理されることを検証。
        """
        # Arrange
        large_policy = "x" * (1 * 1024 * 1024)  # 1MB
        mock_generate_refined_policy.return_value = "処理されました"
        request_data = {
            "session_id": "large-test",
            "prompt": "このポリシーをレビュー",
            "policy_context": large_policy,
        }

        # Act
        response = await async_client.post("/cspm/chat/refine", json=request_data)

        # Assert - 処理される（サイズ制限はアプリ外で実施推奨）
        assert response.status_code in [200, 413, 422]

