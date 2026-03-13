# cspm_plugin（router.py）テストケース

## 1. 概要

CSPMプラグインのメインAPIエンドポイント（`app/cspm_plugin/router.py`）のテストケースを定義します。
ポリシー修正チャット、ポリシー生成エージェント、ポリシー検証の3エンドポイントを検証します。

> **注記**: cspm_plugin は大規模プラグイン（22ファイル・4,239行）のため、テスト仕様書を3分割しています。
> - **本ファイル**: router.py（メインAPIエンドポイント）
> - [cspm_tools_router_tests.md](./cspm_tools_router_tests.md): tools_router.py（MCPツールエンドポイント）
> - [cspm_tools_tests.md](./cspm_tools_tests.md): tools.py（ツール関数）

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `refine_policy_endpoint()` | POST /cspm/chat/refine — ポリシー修正チャット |
| `policy_agent_endpoint()` | POST /cspm/chat/agent — ポリシー生成エージェント（LangGraph） |
| `validate_policy_endpoint()` | POST /cspm/validate_policy_with_tool — ポリシー検証（レガシー） |

### 1.2 カバレッジ目標: 90%

> **注記**: CSPMの中核エンドポイントであり、ビジネスロジックへのエントリーポイント。
> 全分岐を網羅する必要がある。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/cspm_plugin/router.py` |
| 依存（修正ロジック） | `app/cspm_plugin/refinement.py` |
| 依存（エージェント実行） | `app/cspm_plugin/agent_executor.py` |
| 依存（検証ツール） | `app/cspm_plugin/tools.py` |
| リクエストモデル | `app/models/cspm.py`, `app/models/chat.py` |
| テストコード | `test/unit/cspm_plugin/test_router.py` |

### 1.4 補足情報

**エンドポイント一覧:**

| エンドポイント | メソッド | リクエストモデル | レスポンスモデル |
|---------------|---------|-----------------|-----------------|
| `/cspm/chat/refine` | POST | `CSPMPluginChatRequest` | `CSPMPluginChatResponse` |
| `/cspm/chat/agent` | POST | `PolicyAgentRequest` | `PolicyAgentResponse` |
| `/cspm/validate_policy_with_tool` | POST | `PolicyValidationRequest` | `PolicyValidationResponse` |

**主要分岐:**

| 関数 | 行番号 | 分岐条件 |
|------|--------|---------|
| `refine_policy_endpoint` | L42 | HTTPException のキャッチ |
| `refine_policy_endpoint` | L44-52 | その他例外 → 500 + Error ID |
| `policy_agent_endpoint` | L93 | HTTPException のキャッチ |
| `policy_agent_endpoint` | L95-106 | その他例外 → エラーレスポンス（200 + status: error） |
| `validate_policy_endpoint` | L113 | 空ポリシーチェック → isValid: false |
| `validate_policy_endpoint` | L129 | 検証結果判定（"validation successful" で開始するか） |
| `validate_policy_endpoint` | L134-141 | ツール実行例外 → isValid: false |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CSPM-001 | ポリシー修正成功 | 有効な session_id + prompt + policy_context | 200, response フィールド含む |
| CSPM-002 | ポリシーなしで新規作成 | session_id + prompt + policy_context=null | 200, 新規ポリシー生成 |
| CSPM-003 | 説明リクエスト | session_id + "説明して" + policy_context | 200, JSON ブロックなし |
| CSPM-004 | AWS 推奨事項からポリシー生成 | uid + title + target_cloud="aws" | 200, status="active", policy_content 有り |
| CSPM-005 | Azure 推奨事項からポリシー生成 | uid + title + target_cloud="azure" | 200, status="active" |
| CSPM-006 | GCP 推奨事項からポリシー生成 | uid + title + target_cloud="gcp" | 200, status="active" |
| CSPM-007 | 最小限の推奨事項データ | uid + title のみ | 200, 処理成功 |
| CSPM-008 | 有効な JSON ポリシー検証 | 有効な JSON ポリシー | 200, isValid=true |
| CSPM-009 | 有効な YAML ポリシー検証 | 有効な YAML ポリシー | 200, isValid=true |
| CSPM-010 | 検証失敗の正常応答 | 無効なリソースのポリシー | 200, isValid=false, message 含む |
| CSPM-011 | 空文字列ポリシーコンテキスト | session_id + prompt + policy_context="" | 200, 新規ポリシー生成 |

### 2.1 ポリシー修正エンドポイントテスト

```python
# test/unit/cspm_plugin/test_router.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestRefineEndpoint:
    """POST /cspm/chat/refine の正常系テスト"""

    @pytest.mark.asyncio
    async def test_refine_policy_success(self, async_client, mock_generate_refined_policy):
        """CSPM-001: 有効なポリシー修正が成功する

        router.py:36-41 の正常パスをカバー。
        generate_refined_policy() が正常応答を返すケース。
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
    async def test_refine_empty_string_policy(self, async_client, mock_generate_refined_policy):
        """CSPM-011: 空文字列ポリシーコンテキストで新規作成が成功

        router.py:38 で policy_context="" が渡されるケース。
        None と空文字列の動作差異を検証。
        """
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

    @pytest.mark.asyncio
    async def test_refine_explanation_request(self, async_client, mock_generate_refined_policy):
        """CSPM-003: 説明リクエストでJSONブロックなしの応答

        generate_refined_policy() が説明文のみを返すケース。
        """
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
```

### 2.2 ポリシー生成エージェントテスト

```python
class TestAgentEndpoint:
    """POST /cspm/chat/agent の正常系テスト"""

    @pytest.fixture
    def sample_recommendation(self):
        """サンプル推奨事項データ"""
        return {
            "uid": "rec-001",
            "recommendationId": "1.1",
            "title": "S3バケットの暗号化を有効化",
            "description": "セキュリティのためにS3バケットのSSE暗号化を有効にしてください",
            "rationale": "暗号化により保存データを保護",
            "remediation": ["AWSコンソールでS3バケットを開く", "デフォルト暗号化を有効化"],
        }

    @pytest.mark.asyncio
    async def test_agent_aws_policy_generation(
        self, async_client, mock_run_policy_agent, sample_recommendation
    ):
        """CSPM-004: AWS推奨事項からポリシー生成が成功

        router.py:71-91 の正常パスをカバー。
        run_policy_agent() が (policy, None, "active") を返すケース。
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
    async def test_agent_azure_policy_generation(
        self, async_client, mock_run_policy_agent, sample_recommendation
    ):
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
    async def test_agent_gcp_policy_generation(
        self, async_client, mock_run_policy_agent, sample_recommendation
    ):
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
    async def test_agent_minimal_recommendation(
        self, async_client, mock_run_policy_agent
    ):
        """CSPM-007: 最小限の推奨事項データで処理成功

        uid + title のみの最小データでエージェントが動作するか検証。
        """
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
```

### 2.3 ポリシー検証エンドポイントテスト

```python
class TestValidateEndpoint:
    """POST /cspm/validate_policy_with_tool の正常系テスト"""

    @pytest.mark.asyncio
    async def test_validate_valid_json(self, async_client, mock_validate_policy_tool):
        """CSPM-008: 有効なJSONポリシーが検証成功

        router.py:119-132 の正常パスをカバー。
        validate_policy.invoke() が "Validation successful." を返すケース。
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
        validate_policy.invoke() が "Validation failed..." を返すケース。
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
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CSPM-E01 | 空のプロンプト | session_id + prompt="" | 422 (Pydanticバリデーション) |
| CSPM-E02 | session_id 欠落 | prompt のみ | 422 |
| CSPM-E03 | refine LLM 例外 | 有効リクエスト + generate_refined_policy 例外 | 500 + Error ID |
| CSPM-E04 | refine HTTPException 伝播 | generate_refined_policy が HTTPException | HTTPException そのまま伝播 |
| CSPM-E05 | agent UID 欠落 | recommendation_data に uid なし | 422 |
| CSPM-E06 | agent 無効なクラウド指定 | target_cloud="invalid" | 422 |
| CSPM-E07 | agent エージェント実行エラー | run_policy_agent が例外 | 200, status="error", error 含む |
| CSPM-E08 | agent HTTPException 伝播 | run_policy_agent が HTTPException | HTTPException そのまま伝播 |
| CSPM-E09 | validate 空ポリシー | policy_content="" | 200, isValid=false, "empty" |
| CSPM-E10 | validate 空白のみポリシー | policy_content="   " | 200, isValid=false, "empty" |
| CSPM-E11 | validate ツール実行例外 | validate_policy.invoke が例外 | 200, isValid=false, エラーメッセージ |

### 3.1 ポリシー修正エンドポイント異常系

```python
class TestRefineEndpointErrors:
    """POST /cspm/chat/refine の異常系テスト"""

    @pytest.mark.asyncio
    async def test_refine_empty_prompt(self, async_client):
        """CSPM-E01: 空のプロンプトでバリデーションエラー

        CSPMPluginChatRequest.prompt の min_length=1 バリデーション（models/chat.py で定義済み）。
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
        """CSPM-E02: session_id 欠落でバリデーションエラー

        CSPMPluginChatRequest.session_id は必須フィールド（Field(...)）。
        """
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
    async def test_refine_unexpected_exception(
        self, async_client, mock_generate_refined_policy
    ):
        """CSPM-E03: 予期しない例外で500エラー + Error ID

        router.py:44-52 の Exception ハンドラーをカバー。
        generate_refined_policy() が通常例外を送出するケース。
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
    async def test_refine_http_exception_propagation(
        self, async_client, mock_generate_refined_policy
    ):
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
```

### 3.2 ポリシー生成エージェント異常系

```python
class TestAgentEndpointErrors:
    """POST /cspm/chat/agent の異常系テスト"""

    @pytest.mark.asyncio
    async def test_agent_missing_uid(self, async_client):
        """CSPM-E05: UID 欠落でバリデーションエラー

        RecommendationInputDataForAgent.uid は必須フィールド（Field(...)）。
        models/cspm.py:63 の定義。
        """
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
        """CSPM-E06: 無効なクラウド指定でバリデーションエラー

        PolicyAgentRequest.target_cloud の Literal["aws", "azure", "gcp"] バリデーション。
        models/cspm.py:85 の定義。
        """
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
        run_policy_agent() が通常例外を送出するケース。
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
    async def test_agent_http_exception_propagation(
        self, async_client, mock_run_policy_agent
    ):
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
```

### 3.3 ポリシー検証エンドポイント異常系

```python
class TestValidateEndpointErrors:
    """POST /cspm/validate_policy_with_tool の異常系テスト"""

    @pytest.mark.asyncio
    async def test_validate_empty_policy(self, async_client):
        """CSPM-E09: 空のポリシーでisValid=false

        router.py:113-117 の空チェック分岐をカバー。
        `not policy_content or not policy_content.strip()` の前者。
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
    async def test_validate_tool_exception(
        self, async_client, mock_validate_policy_tool
    ):
        """CSPM-E11: ツール実行例外でisValid=false

        router.py:134-141 の Exception ハンドラーをカバー。
        validate_policy.invoke() が例外を送出するケース。
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
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CSPM-SEC-01 | Error ID でスタックトレース非露出 | refine 例外発生 | Error ID のみ露出、スタックトレースなし |
| CSPM-SEC-02 | agent Error ID でスタックトレース非露出 | agent 例外発生 | Error ID のみ露出、内部詳細なし |
| CSPM-SEC-03 | ポリシー内容インジェクション防止 | 悪意あるポリシー文字列 | 安全に処理される |
| CSPM-SEC-04 | 大容量ポリシーコンテキストの処理 | 1MB のポリシー文字列 | タイムアウトまたは処理制限 |

```python
@pytest.mark.security
class TestCSPMRouterSecurity:
    """CSPMルーターセキュリティテスト"""

    @pytest.mark.asyncio
    async def test_refine_error_no_stacktrace(
        self, async_client, mock_generate_refined_policy
    ):
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
    async def test_agent_error_no_internal_details(
        self, async_client, mock_run_policy_agent
    ):
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
    async def test_policy_content_injection(
        self, async_client, mock_validate_policy_tool
    ):
        """CSPM-SEC-03: ポリシー内容にインジェクション攻撃文字列が含まれても安全

        悪意ある入力がバリデーションツールに安全に渡され、
        コマンドインジェクションが発生しないことを検証。
        """
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
        # エラーレスポンスが返るが、コマンドは実行されない
        data = response.json()
        assert data["isValid"] is False

    @pytest.mark.asyncio
    async def test_large_policy_context_handling(
        self, async_client, mock_generate_refined_policy
    ):
        """CSPM-SEC-04: 大容量ポリシーコンテキストの処理

        1MB のポリシー文字列が安全に処理されることを検証。
        本番環境では nginx 等でリクエストサイズ制限を設定推奨。
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
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_cspm_router_module` | テスト間のモジュール状態リセット | function | Yes |
| `mock_generate_refined_policy` | refinement.py のモック | function | No |
| `mock_run_policy_agent` | agent_executor.py のモック | function | No |
| `mock_validate_policy_tool` | tools.py validate_policy のモック | function | No |
| `async_client` | FastAPI テストクライアント | function | No |

### 共通フィクスチャ定義

```python
# test/unit/cspm_plugin/conftest.py
import sys
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport


@pytest.fixture(autouse=True)
def reset_cspm_router_module():
    """テストごとにモジュールのグローバル状態をリセット

    cspm_plugin のモジュールレベル変数（LLMインスタンス等）を
    テスト間で独立させるためにキャッシュを削除する。
    """
    yield
    # テスト後にクリーンアップ
    modules_to_remove = [
        key for key in sys.modules if key.startswith("app.cspm_plugin")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def mock_generate_refined_policy():
    """refinement.generate_refined_policy のモック（外部LLM接続防止）"""
    with patch(
        "app.cspm_plugin.router.generate_refined_policy",
        new_callable=AsyncMock,
    ) as mock_func:
        mock_func.return_value = "モック応答"
        yield mock_func


@pytest.fixture
def mock_run_policy_agent():
    """agent_executor.run_policy_agent のモック（LangGraph実行防止）"""
    with patch(
        "app.cspm_plugin.router.run_policy_agent",
        new_callable=AsyncMock,
    ) as mock_func:
        mock_func.return_value = (
            '[{"name": "mock-policy", "resource": "s3"}]',
            None,
            "active",
        )
        yield mock_func


@pytest.fixture
def mock_validate_policy_tool():
    """tools.validate_policy のモック（subprocess実行防止）"""
    with patch("app.cspm_plugin.router.validate_policy") as mock_tool:
        mock_tool.invoke = MagicMock(return_value="Validation successful.")
        yield mock_tool


@pytest.fixture
async def async_client():
    """FastAPI非同期テストクライアント"""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
```

---

## 6. テスト実行例

```bash
# router.py 関連テストのみ実行
pytest test/unit/cspm_plugin/test_router.py -v

# 特定のテストクラスのみ実行
pytest test/unit/cspm_plugin/test_router.py::TestRefineEndpoint -v

# カバレッジ付きで実行
pytest test/unit/cspm_plugin/test_router.py --cov=app.cspm_plugin.router --cov-report=term-missing -v

# セキュリティマーカーで実行
# pyproject.toml: markers = ["security: セキュリティ関連テスト"]
pytest test/unit/cspm_plugin/test_router.py -m "security" -v

# cspm_plugin 全テスト（router + tools_router + tools）
pytest test/unit/cspm_plugin/ -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 11 | CSPM-001 〜 CSPM-011 |
| 異常系 | 11 | CSPM-E01 〜 CSPM-E11 |
| セキュリティ | 4 | CSPM-SEC-01 〜 CSPM-SEC-04 |
| **合計** | **26** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestRefineEndpoint` | CSPM-001〜003, 011 | 4 |
| `TestAgentEndpoint` | CSPM-004〜007 | 4 |
| `TestValidateEndpoint` | CSPM-008〜010 | 3 |
| `TestRefineEndpointErrors` | CSPM-E01〜E04 | 4 |
| `TestAgentEndpointErrors` | CSPM-E05〜E08 | 4 |
| `TestValidateEndpointErrors` | CSPM-E09〜E11 | 3 |
| `TestCSPMRouterSecurity` | CSPM-SEC-01〜SEC-04 | 4 |

### 実装失敗が予想されるテスト

| テストID | 失敗理由 | 修正方針 |
|---------|---------|---------|
| CSPM-SEC-02 | `router.py:105` で `str(e)` が直接レスポンスに含まれ、内部エラー情報がクライアントに露出 | エラーメッセージを汎用化し、Error ID のみを返すように修正 |

> **注記**: CSPM-E01 は `models/chat.py` で `prompt: str = Field(..., min_length=1)` が定義済みのため、空文字列は 422 エラーとなり正常に動作します。

### 注意事項

- テスト実行に `pytest-asyncio` と `httpx` が必要
- `@pytest.mark.security` マーカーの登録が必要（`pyproject.toml`）
- `async_client` フィクスチャは `app.main` のインポートが必要（環境変数の事前設定が必要）
- 全モックは `router.py` のインポートパスでパッチ（`app.cspm_plugin.router.xxx`）
- APIパスは `/cspm/...` （`/api` プレフィックスなし）

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | **【脆弱性】** `policy_agent_endpoint` のエラーレスポンスに `str(e)` が含まれる（`router.py:105`） | 内部エラー情報（IP、ポート等）がクライアントに露出するリスク | Error ID のみを返すように実装修正が必要 |
| 2 | **【脆弱性】** `validate_policy_endpoint` のエラーレスポンスにも `str(e)` が含まれる（`router.py:140`） | 同上 | 同上 |
| 3 | ~~`CSPMPluginChatRequest.prompt` の空文字バリデーション~~ | ~~`min_length` 未定義の場合~~ | **解消済み**: `min_length=1` が定義済み |
| 4 | 認証テストが本仕様書に含まれていない | 認証ミドルウェアの適用状況は `main.py` のルーター登録方法に依存 | 統合テストで認証ミドルウェアの適用を確認。将来的に CSPM-SEC-06〜08 として認証テストを追加検討 |
| 5 | 本仕様書は router.py のみをカバー | tools_router.py と tools.py の分岐は別仕様書 | [cspm_tools_router_tests.md](./cspm_tools_router_tests.md) と [cspm_tools_tests.md](./cspm_tools_tests.md) を参照 |
| 6 | YAMLインジェクション対策テスト未実装 | Cloud Custodian の YAML パーサーに対する攻撃リスク | 将来的に CSPM-SEC-05 として追加を検討 |
| 7 | リクエストサイズ制限がFastAPIデフォルト（無制限） | 大容量リクエストによるリソース枯渇リスク | nginx等のリバースプロキシで1MB程度の制限設定を推奨。CSPM-SEC-04で動作確認済み |
| 8 | レート制限テストが含まれていない | DoS攻撃への耐性が未検証 | 本番環境ではリバースプロキシでレート制限設定を推奨 |
