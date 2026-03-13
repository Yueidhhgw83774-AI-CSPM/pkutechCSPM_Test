# cspm_plugin（tools_router.py）テストケース

## 1. 概要

CSPMプラグインのMCPツールHTTPエンドポイント（`app/cspm_plugin/tools_router.py`）のテストケースを定義します。
4つのMCPツールエンドポイント（検証・スキーマ取得・リソース一覧・参照検索）を検証します。

> **注記**: cspm_plugin テスト仕様書は3分割されています。
> - [cspm_plugin_tests.md](./cspm_plugin_tests.md): router.py（メインAPIエンドポイント）
> - **本ファイル**: tools_router.py（MCPツールエンドポイント）
> - [cspm_tools_tests.md](./cspm_tools_tests.md): tools.py（ツール関数）

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `validate_policy_endpoint()` | POST /cspm-tools/validate — ポリシー検証（MCP用） |
| `get_schema_endpoint()` | POST /cspm-tools/schema — スキーマ取得 |
| `list_resources_endpoint()` | POST /cspm-tools/resources — リソース一覧取得 |
| `retrieve_reference_endpoint()` | POST /cspm-tools/reference — ドキュメント検索（非同期） |

### 1.2 カバレッジ目標: 90%

> **注記**: MCPツールの公開エンドポイントであり、全分岐を網羅する必要がある。
> 特に TOOLS_AVAILABLE フラグの分岐が全エンドポイントに共通する重要パターン。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/cspm_plugin/tools_router.py` |
| 依存（ツール実装） | `app/cspm_plugin/tools.py` |
| リクエスト/レスポンスモデル | `app/models/cspm_tools.py` |
| テストコード | `test/unit/cspm_plugin/test_tools_router.py` |

### 1.4 補足情報

**エンドポイント一覧:**

| エンドポイント | メソッド | リクエストモデル | レスポンスモデル |
|---------------|---------|-----------------|-----------------|
| `/cspm-tools/validate` | POST | `ValidatePolicyRequest` | `ValidatePolicyResponse` |
| `/cspm-tools/schema` | POST | `GetSchemaRequest` | `GetSchemaResponse` |
| `/cspm-tools/resources` | POST | `ListResourcesRequest` | `ListResourcesResponse` |
| `/cspm-tools/reference` | POST | `RetrieveReferenceRequest` | `RetrieveReferenceResponse` |

**リクエストモデルの制約（cspm_tools.py 参照）:**

| エンドポイント | パラメータ | 制約 |
|---------------|-----------|------|
| `/cspm-tools/validate` | `policy_content` | `min_length=1`（空文字列不可） |
| `/cspm-tools/resources` | `cloud` | `Literal["aws", "azure", "gcp"]`（3種類） |
| `/cspm-tools/reference` | `query` | `min_length=1`（空文字列不可） |
| `/cspm-tools/reference` | `cloud` | `Literal["aws", "azure", "gcp", "oci", "tencentcloud", "kubernetes", "general", "tools"]`（8種類、デフォルト="aws"） |

> **注記**: resources エンドポイントは主要3クラウド（AWS/Azure/GCP）のリソースタイプ取得に特化。
> reference エンドポイントはドキュメント検索対象として、Kubernetes や汎用ツール等も含む広範囲のカテゴリをサポート。

**モジュールレベル初期化:**

```python
# tools_router.py:24-38 — ツールインポートの条件付きロード
try:
    from .tools import validate_policy, get_custodian_schema, ...
    TOOLS_AVAILABLE = True
except ImportError as e:
    TOOLS_AVAILABLE = False
    validate_policy = None
    ...
```

**主要分岐:**

| 関数 | 行番号 | 分岐条件 |
|------|--------|---------|
| `validate_policy_endpoint` | L58 | TOOLS_AVAILABLE チェック → 503 |
| `validate_policy_endpoint` | L71 | "Validation successful" 判定 |
| `validate_policy_endpoint` | L74 | Details 分離ロジック |
| `validate_policy_endpoint` | L88-94 | Exception → 500 + Error ID |
| `get_schema_endpoint` | L110 | TOOLS_AVAILABLE チェック → 503 |
| `get_schema_endpoint` | L128-134 | Exception → 500 + Error ID |
| `list_resources_endpoint` | L150 | TOOLS_AVAILABLE チェック → 503 |
| `list_resources_endpoint` | L167-173 | Exception → 500 + Error ID |
| `retrieve_reference_endpoint` | L189 | TOOLS_AVAILABLE チェック → 503 |
| `retrieve_reference_endpoint` | L210-216 | Exception → 500 + Error ID |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CSPM-TR-001 | 有効ポリシー検証成功 | 有効な policy_content | 200, success=true, message 含む |
| CSPM-TR-002 | 検証失敗の正常応答 | 無効ポリシー | 200, success=false |
| CSPM-TR-003 | 検証成功＋Details分離 | "Validation successful.\nDetails..." | 200, success=true, details 有り |
| CSPM-TR-004 | スキーマ取得（ターゲット指定） | target="aws.ec2" | 200, schema_content 有り, target="aws.ec2" |
| CSPM-TR-005 | スキーマ取得（ターゲットなし） | target=None | 200, schema_content 有り, target=null |
| CSPM-TR-006 | リソース一覧取得（AWS） | cloud="aws" | 200, cloud="aws", resources 有り |
| CSPM-TR-007 | リソース一覧取得（Azure） | cloud="azure" | 200, cloud="azure" |
| CSPM-TR-008 | 参照検索成功 | query="s3 encryption", cloud="aws" | 200, references 有り |
| CSPM-TR-009 | 参照検索（デフォルトcloud） | query="ec2 tags" のみ | 200, cloud="aws"（デフォルト） |
| CSPM-TR-010 | 検証失敗時のDetails非分離 | "Validation failed...\nDetails..." | 200, success=false, details=null |

### 2.1 ポリシー検証エンドポイントテスト

```python
# test/unit/cspm_plugin/test_tools_router.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestToolsValidateEndpoint:
    """POST /cspm-tools/validate の正常系テスト"""

    @pytest.mark.asyncio
    async def test_validate_success(self, async_client, mock_tools_available):
        """CSPM-TR-001: 有効ポリシーの検証が成功する

        tools_router.py:64-86 の正常パスをカバー。
        validate_policy.invoke() が "Validation successful." を返すケース。
        L71 の success=True 分岐。
        """
        # Arrange
        mock_tools_available["validate_policy"].invoke.return_value = (
            "Validation successful."
        )
        request_data = {"policy_content": '{"policies": [{"name": "test", "resource": "s3"}]}'}

        # Act
        response = await async_client.post("/cspm-tools/validate", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "successful" in data["message"].lower()
        assert data["details"] is None

    @pytest.mark.asyncio
    async def test_validate_failure(self, async_client, mock_tools_available):
        """CSPM-TR-002: 無効ポリシーの検証結果がsuccess=falseで返る

        L71 の success=False 分岐（"Validation successful" を含まない結果）。
        """
        # Arrange
        mock_tools_available["validate_policy"].invoke.return_value = (
            "Validation failed (Code: 1):\ninvalid resource type 'fake'"
        )
        request_data = {"policy_content": '{"policies": [{"name": "test", "resource": "fake"}]}'}

        # Act
        response = await async_client.post("/cspm-tools/validate", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "failed" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_validate_success_with_details(self, async_client, mock_tools_available):
        """CSPM-TR-003: 検証成功時にDetailsが分離される

        tools_router.py:74-78 の Details 分離ロジックをカバー。
        結果に "Validation successful" と "\nDetails" の両方を含むケース。
        """
        # Arrange
        mock_tools_available["validate_policy"].invoke.return_value = (
            "Validation successful.\nDetails (stderr):\nWarning: deprecated filter"
        )
        request_data = {"policy_content": '{"policies": [{"name": "test", "resource": "s3"}]}'}

        # Act
        response = await async_client.post("/cspm-tools/validate", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "successful" in data["message"].lower()
        assert data["details"] is not None
        assert "deprecated filter" in data["details"]

    @pytest.mark.asyncio
    async def test_validate_failure_no_details_split(self, async_client, mock_tools_available):
        """CSPM-TR-010: 検証失敗時にはDetails分離が発生しない

        tools_router.py:74 の条件は `success and "\nDetails" in result` であるため、
        success=False の場合は Details 分離ロジックを通らず、
        結果文字列がそのまま message に格納される。
        """
        # Arrange
        mock_tools_available["validate_policy"].invoke.return_value = (
            "Validation failed (Code: 1):\nSyntax error at line 5"
            "\nDetails (stderr):\nWarning: deprecated syntax used"
        )
        request_data = {"policy_content": '{"policies": [{"name": "test"}]}'}

        # Act
        response = await async_client.post("/cspm-tools/validate", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        # 失敗時は Details 分離されず、全文が message に入る
        assert "Details" in data["message"]
        assert data["details"] is None
```

### 2.2 スキーマ取得エンドポイントテスト

```python
class TestToolsSchemaEndpoint:
    """POST /cspm-tools/schema の正常系テスト"""

    @pytest.mark.asyncio
    async def test_schema_with_target(self, async_client, mock_tools_available):
        """CSPM-TR-004: ターゲット指定でスキーマ取得成功

        tools_router.py:116-126 の正常パスをカバー。
        """
        # Arrange
        mock_tools_available["get_custodian_schema"].invoke.return_value = (
            "ec2:\n  filters:\n    - tag-count\n    - instance-age"
        )
        request_data = {"target": "aws.ec2"}

        # Act
        response = await async_client.post("/cspm-tools/schema", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["schema_content"] is not None
        assert data["target"] == "aws.ec2"

    @pytest.mark.asyncio
    async def test_schema_without_target(self, async_client, mock_tools_available):
        """CSPM-TR-005: ターゲットなしで全リソース一覧取得

        tools_router.py:117 の target=None ケース。
        """
        # Arrange
        mock_tools_available["get_custodian_schema"].invoke.return_value = (
            "aws:\n  ec2\n  s3\n  iam-user"
        )
        request_data = {}  # target はオプション

        # Act
        response = await async_client.post("/cspm-tools/schema", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["schema_content"] is not None
        assert data["target"] is None
```

### 2.3 リソース一覧エンドポイントテスト

```python
class TestToolsResourcesEndpoint:
    """POST /cspm-tools/resources の正常系テスト"""

    @pytest.mark.asyncio
    async def test_resources_aws(self, async_client, mock_tools_available):
        """CSPM-TR-006: AWSリソース一覧取得成功

        tools_router.py:156-165 の正常パスをカバー。
        """
        # Arrange
        mock_tools_available["list_available_resources"].invoke.return_value = (
            "ec2\ns3\niam-user\nlambda"
        )
        request_data = {"cloud": "aws"}

        # Act
        response = await async_client.post("/cspm-tools/resources", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["cloud"] == "aws"
        assert "ec2" in data["resources"]

    @pytest.mark.asyncio
    async def test_resources_azure(self, async_client, mock_tools_available):
        """CSPM-TR-007: Azureリソース一覧取得成功"""
        # Arrange
        mock_tools_available["list_available_resources"].invoke.return_value = (
            "vm\nstorage-account\nkeyvault"
        )
        request_data = {"cloud": "azure"}

        # Act
        response = await async_client.post("/cspm-tools/resources", json=request_data)

        # Assert
        assert response.status_code == 200
        assert response.json()["cloud"] == "azure"
```

### 2.4 参照検索エンドポイントテスト

```python
class TestToolsReferenceEndpoint:
    """POST /cspm-tools/reference の正常系テスト"""

    @pytest.mark.asyncio
    async def test_reference_success(self, async_client, mock_tools_available):
        """CSPM-TR-008: 参照検索成功

        tools_router.py:195-208 の正常パスをカバー。
        retrieve_reference.ainvoke() を使用（非同期ツール）。
        """
        # Arrange
        mock_tools_available["retrieve_reference"].ainvoke.return_value = (
            "Reference Source: docs/s3.md\nContent:\nS3 encryption policy example..."
        )
        request_data = {"query": "s3 encryption filter", "cloud": "aws"}

        # Act
        response = await async_client.post("/cspm-tools/reference", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "s3 encryption filter"
        assert data["cloud"] == "aws"
        assert "encryption" in data["references"]

    @pytest.mark.asyncio
    async def test_reference_default_cloud(self, async_client, mock_tools_available):
        """CSPM-TR-009: cloud未指定でデフォルト値(aws)が適用

        RetrieveReferenceRequest.cloud のデフォルト値 "aws" の検証。
        """
        # Arrange
        mock_tools_available["retrieve_reference"].ainvoke.return_value = (
            "Reference Source: docs/ec2.md\nContent:\nEC2 tag filtering..."
        )
        request_data = {"query": "ec2 tag filter"}  # cloud 未指定

        # Act
        response = await async_client.post("/cspm-tools/reference", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["cloud"] == "aws"
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CSPM-TR-E01 | validate TOOLS_AVAILABLE=False | モジュール未ロード | 503, "利用できません" |
| CSPM-TR-E02 | schema TOOLS_AVAILABLE=False | モジュール未ロード | 503, "利用できません" |
| CSPM-TR-E03 | resources TOOLS_AVAILABLE=False | モジュール未ロード | 503, "利用できません" |
| CSPM-TR-E04 | reference TOOLS_AVAILABLE=False | モジュール未ロード | 503, "利用できません" |
| CSPM-TR-E05 | validate 例外で500 | invoke が例外送出 | 500 + Error ID |
| CSPM-TR-E06 | schema 例外で500 | invoke が例外送出 | 500 + Error ID |
| CSPM-TR-E07 | resources 例外で500 | invoke が例外送出 | 500 + Error ID |
| CSPM-TR-E08 | reference 例外で500 | ainvoke が例外送出 | 500 + Error ID |
| CSPM-TR-E09 | validate 空文字列 | policy_content="" | 422 (min_length=1) |
| CSPM-TR-E10 | resources 無効クラウド | cloud="invalid" | 422 (Literal) |
| CSPM-TR-E11 | reference 空クエリ | query="" | 422 (min_length=1) |
| CSPM-TR-E12 | reference 無効クラウド | cloud="invalid" | 422 (Literal) |

### 3.1 TOOLS_AVAILABLE=False 系テスト

```python
class TestToolsUnavailable:
    """TOOLS_AVAILABLE=False 時の 503 エラーテスト"""

    @pytest.mark.asyncio
    async def test_validate_tools_unavailable(self, async_client, mock_tools_unavailable):
        """CSPM-TR-E01: validate ツール未ロード時に503

        tools_router.py:58-62 の TOOLS_AVAILABLE チェック分岐。
        """
        # Arrange
        request_data = {"policy_content": '{"policies": []}'}

        # Act
        response = await async_client.post("/cspm-tools/validate", json=request_data)

        # Assert
        assert response.status_code == 503
        assert "利用できません" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_schema_tools_unavailable(self, async_client, mock_tools_unavailable):
        """CSPM-TR-E02: schema ツール未ロード時に503

        tools_router.py:110-114 の TOOLS_AVAILABLE チェック分岐。
        """
        # Arrange
        request_data = {"target": "aws.ec2"}

        # Act
        response = await async_client.post("/cspm-tools/schema", json=request_data)

        # Assert
        assert response.status_code == 503
        assert "利用できません" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_resources_tools_unavailable(self, async_client, mock_tools_unavailable):
        """CSPM-TR-E03: resources ツール未ロード時に503

        tools_router.py:150-154 の TOOLS_AVAILABLE チェック分岐。
        """
        # Arrange
        request_data = {"cloud": "aws"}

        # Act
        response = await async_client.post("/cspm-tools/resources", json=request_data)

        # Assert
        assert response.status_code == 503
        assert "利用できません" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_reference_tools_unavailable(self, async_client, mock_tools_unavailable):
        """CSPM-TR-E04: reference ツール未ロード時に503

        tools_router.py:189-193 の TOOLS_AVAILABLE チェック分岐。
        """
        # Arrange
        request_data = {"query": "test query", "cloud": "aws"}

        # Act
        response = await async_client.post("/cspm-tools/reference", json=request_data)

        # Assert
        assert response.status_code == 503
        assert "利用できません" in response.json()["detail"]
```

### 3.2 Exception ハンドラーテスト

```python
class TestToolsEndpointExceptions:
    """各エンドポイントの Exception ハンドラーテスト"""

    @pytest.mark.asyncio
    async def test_validate_exception(self, async_client, mock_tools_available):
        """CSPM-TR-E05: validate 例外発生で500 + Error ID

        tools_router.py:88-94 の Exception ハンドラーをカバー。
        """
        # Arrange
        mock_tools_available["validate_policy"].invoke.side_effect = RuntimeError(
            "custodian subprocess crashed"
        )
        request_data = {"policy_content": '{"policies": [{"name": "test", "resource": "s3"}]}'}

        # Act
        response = await async_client.post("/cspm-tools/validate", json=request_data)

        # Assert
        assert response.status_code == 500
        detail = response.json()["detail"]
        assert "ID:" in detail
        assert "エラーが発生しました" in detail

    @pytest.mark.asyncio
    async def test_schema_exception(self, async_client, mock_tools_available):
        """CSPM-TR-E06: schema 例外発生で500 + Error ID

        tools_router.py:128-134 の Exception ハンドラーをカバー。
        """
        # Arrange
        mock_tools_available["get_custodian_schema"].invoke.side_effect = RuntimeError(
            "schema command failed"
        )
        request_data = {"target": "aws.ec2"}

        # Act
        response = await async_client.post("/cspm-tools/schema", json=request_data)

        # Assert
        assert response.status_code == 500
        assert "ID:" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_resources_exception(self, async_client, mock_tools_available):
        """CSPM-TR-E07: resources 例外発生で500 + Error ID

        tools_router.py:167-173 の Exception ハンドラーをカバー。
        """
        # Arrange
        mock_tools_available["list_available_resources"].invoke.side_effect = RuntimeError(
            "command not found"
        )
        request_data = {"cloud": "aws"}

        # Act
        response = await async_client.post("/cspm-tools/resources", json=request_data)

        # Assert
        assert response.status_code == 500
        assert "ID:" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_reference_exception(self, async_client, mock_tools_available):
        """CSPM-TR-E08: reference 例外発生で500 + Error ID

        tools_router.py:210-216 の Exception ハンドラーをカバー。
        ainvoke() が例外送出するケース。
        """
        # Arrange
        mock_tools_available["retrieve_reference"].ainvoke.side_effect = RuntimeError(
            "RAG system connection error"
        )
        request_data = {"query": "s3 encryption", "cloud": "aws"}

        # Act
        response = await async_client.post("/cspm-tools/reference", json=request_data)

        # Assert
        assert response.status_code == 500
        assert "ID:" in response.json()["detail"]
```

### 3.3 Pydantic バリデーションエラーテスト

```python
class TestToolsValidationErrors:
    """Pydantic モデルバリデーションによる422エラーテスト"""

    @pytest.mark.asyncio
    async def test_validate_empty_content(self, async_client):
        """CSPM-TR-E09: 空のpolicy_contentで422

        ValidatePolicyRequest.policy_content の min_length=1 バリデーション。
        """
        # Arrange
        request_data = {"policy_content": ""}

        # Act
        response = await async_client.post("/cspm-tools/validate", json=request_data)

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_resources_invalid_cloud(self, async_client):
        """CSPM-TR-E10: 無効なクラウド名で422

        ListResourcesRequest.cloud の Literal["aws", "azure", "gcp"] バリデーション。
        """
        # Arrange
        request_data = {"cloud": "invalid_cloud"}

        # Act
        response = await async_client.post("/cspm-tools/resources", json=request_data)

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_reference_empty_query(self, async_client):
        """CSPM-TR-E11: 空クエリで422

        RetrieveReferenceRequest.query の min_length=1 バリデーション。
        """
        # Arrange
        request_data = {"query": "", "cloud": "aws"}

        # Act
        response = await async_client.post("/cspm-tools/reference", json=request_data)

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_reference_invalid_cloud(self, async_client):
        """CSPM-TR-E12: reference 無効クラウド名で422

        RetrieveReferenceRequest.cloud の Literal バリデーション。
        """
        # Arrange
        request_data = {"query": "test", "cloud": "invalid"}

        # Act
        response = await async_client.post("/cspm-tools/reference", json=request_data)

        # Assert
        assert response.status_code == 422
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CSPM-TR-SEC-01 | 500エラー時に内部情報露出チェック | invoke 例外 | Error ID のみ含む（str(e) を含まない） |
| CSPM-TR-SEC-02 | ポリシー内容インジェクション防止 | コマンドインジェクション文字列 | ツールに安全に渡される |
| CSPM-TR-SEC-03 | YAML爆弾攻撃の防止 | 再帰参照YAML | タイムアウトまたはエラーで安全に処理 |
| CSPM-TR-SEC-04 | パストラバーサル攻撃の防止（schema target） | `../../../etc/passwd` | 安全に処理される |
| CSPM-TR-SEC-05 | 大容量リクエストの制限確認 | 1MBポリシー | 200（処理される）または 413/422 |
| CSPM-TR-SEC-06 | ログインジェクション防止（policy_content） | 改行文字含むcontent | 正常処理（ログは別責務） |
| CSPM-TR-SEC-07 | ログインジェクション防止（query） | 改行文字含むquery | 正常処理（ログは別責務） |

> **注記 CSPM-TR-SEC-01**: 現在の実装では `str(e)` が detail に含まれるため xfail でマーク。
> 修正後は Error ID のみを返し、エラー詳細はサーバーログにのみ記録する想定。

```python
@pytest.mark.security
class TestToolsRouterSecurity:
    """MCPツールルーターのセキュリティテスト"""

    @pytest.mark.xfail(
        reason="tools_router.py:93 で str(e) が露出する既知の問題。修正後にxfailを除去",
        strict=True,
    )
    @pytest.mark.asyncio
    async def test_error_response_contains_str_e(self, async_client, mock_tools_available):
        """CSPM-TR-SEC-01: 500エラー時に内部情報が露出しない

        tools_router.py:93 で `str(e)` が HTTPException.detail に含まれる。
        全4エンドポイントに共通する実装パターン（L93, L133, L172, L215）。
        本テストは validate エンドポイントを代表例として検証する。
        他の3エンドポイント（schema, resources, reference）も同一パターンのため、
        修正時は4箇所すべてを対応すること。
        現在の実装では xfail（修正待ち）。
        """
        # Arrange
        mock_tools_available["validate_policy"].invoke.side_effect = ConnectionError(
            "Internal DB at 10.0.0.5:9200 connection refused"
        )
        request_data = {"policy_content": '{"policies": []}'}

        # Act
        response = await async_client.post("/cspm-tools/validate", json=request_data)

        # Assert
        assert response.status_code == 500
        detail = response.json()["detail"]
        assert "ID:" in detail
        # 修正後に期待される動作（現在は str(e) が含まれるため失敗）
        assert "10.0.0.5" not in detail
        assert "9200" not in detail

    @pytest.mark.asyncio
    async def test_policy_injection_safe(self, async_client, mock_tools_available):
        """CSPM-TR-SEC-02: コマンドインジェクション文字列が安全に処理される

        ツールにそのまま渡されるが、HTTP層では問題なし。
        実際のインジェクション防止はtools.py側の責務。
        """
        # Arrange
        malicious = '; rm -rf / ; echo "pwned"'
        mock_tools_available["validate_policy"].invoke.return_value = (
            "Error: Failed to parse JSON content"
        )
        request_data = {"policy_content": malicious}

        # Act
        response = await async_client.post("/cspm-tools/validate", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_yaml_bomb_protection(self, async_client, mock_tools_available):
        """CSPM-TR-SEC-03: YAML爆弾攻撃が安全に処理される

        YAML爆弾: 再帰的なアンカー参照により、パース時に指数関数的にメモリを消費させる攻撃。
        HTTP層では問題なし、tools.py側でyaml.safe_loadにより安全に処理される。
        """
        # Arrange
        yaml_bomb = """
a: &a ["lol","lol","lol","lol","lol","lol","lol","lol","lol"]
b: &b [*a,*a,*a,*a,*a,*a,*a,*a,*a]
c: &c [*b,*b,*b,*b,*b,*b,*b,*b,*b]
"""
        mock_tools_available["validate_policy"].invoke.return_value = "Error: Failed to parse"
        request_data = {"policy_content": yaml_bomb}

        # Act
        response = await async_client.post("/cspm-tools/validate", json=request_data)

        # Assert - タイムアウトまたはエラーで正常に処理される（ハングしない）
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_schema_path_traversal_protection(self, async_client, mock_tools_available):
        """CSPM-TR-SEC-04: target パラメータにパストラバーサル文字列が含まれても安全に処理される

        tools.py側の _validate_schema_target() でクラウド名検証が行われるため、
        無効なターゲットとしてエラーを返す。
        """
        # Arrange
        path_traversal = "../../../etc/passwd"
        mock_tools_available["get_custodian_schema"].invoke.return_value = (
            "エラー: 無効なクラウド名 '..'. aws, azure, gcp のいずれかを指定してください"
        )
        request_data = {"target": path_traversal}

        # Act
        response = await async_client.post("/cspm-tools/schema", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        # パストラバーサルは無効なクラウド名として拒否される
        assert "無効" in data["schema_content"] or "Error" in data["schema_content"]

    @pytest.mark.asyncio
    async def test_large_request_handling(self, async_client, mock_tools_available):
        """CSPM-TR-SEC-05: 大容量リクエスト（1MB）の処理確認

        FastAPIのデフォルト設定ではリクエストサイズ制限がないため、
        1MBポリシーが処理されるかを確認。
        本番環境ではnginx/リバースプロキシで適切なサイズ制限を設定推奨。
        """
        # Arrange - 1MBポリシー
        large_policy = "x" * (1 * 1024 * 1024)
        mock_tools_available["validate_policy"].invoke.return_value = (
            "Error: Failed to parse JSON content"
        )
        request_data = {"policy_content": large_policy}

        # Act
        response = await async_client.post("/cspm-tools/validate", json=request_data)

        # Assert - 処理される（FastAPIデフォルトではサイズ制限なし）
        # 本番環境でnginx等でサイズ制限設定時は 413 が返る
        assert response.status_code in [200, 413, 422]

    @pytest.mark.asyncio
    async def test_log_injection_in_policy_content(self, async_client, mock_tools_available):
        """CSPM-TR-SEC-06: policy_content内の改行文字が正常に処理される

        tools_router.py:65 で content length をログ出力。
        改行文字を含む入力でもHTTP層では正常に処理される。
        ログ出力時のサニタイズはロギング設定の責務。
        """
        # Arrange - 改行文字とフェイクログメッセージを含むコンテンツ
        malicious_content = 'policies:\n  - name: "test\\n[FAKE] Unauthorized access"'
        mock_tools_available["validate_policy"].invoke.return_value = (
            "Validation successful."
        )
        request_data = {"policy_content": malicious_content}

        # Act
        response = await async_client.post("/cspm-tools/validate", json=request_data)

        # Assert - HTTP層では正常に処理される
        assert response.status_code == 200
        assert response.json()["success"] is True

    @pytest.mark.asyncio
    async def test_log_injection_in_query(self, async_client, mock_tools_available):
        """CSPM-TR-SEC-07: retrieve_reference のクエリ内改行文字が正常に処理される

        tools_router.py:196 で query[:50] をログ出力。
        改行文字を含む入力でもHTTP層では正常に処理される。
        """
        # Arrange - 改行文字を含むクエリ
        malicious_query = "s3 encryption\n[ERROR] Database connection failed"
        mock_tools_available["retrieve_reference"].ainvoke.return_value = (
            "Reference content..."
        )
        request_data = {"query": malicious_query, "cloud": "aws"}

        # Act
        response = await async_client.post("/cspm-tools/reference", json=request_data)

        # Assert - HTTP層では正常に処理される
        assert response.status_code == 200
        assert response.json()["query"] == malicious_query
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_tools_router_module` | テスト間のモジュール状態リセット | function | Yes |
| `mock_tools_available` | TOOLS_AVAILABLE=True + 各ツールモック | function | No |
| `mock_tools_unavailable` | TOOLS_AVAILABLE=False 状態のモック | function | No |
| `async_client` | FastAPI 非同期テストクライアント | function | No |

### 共通フィクスチャ定義

```python
# test/unit/cspm_plugin/conftest.py（既存ファイルに追記）
import sys
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient, ASGITransport


@pytest.fixture(autouse=True)
def reset_tools_router_module():
    """テストごとにモジュールのグローバル状態をリセット

    tools_router.py のモジュールレベル TOOLS_AVAILABLE フラグや
    ツール関数参照をテスト間で独立させる。
    """
    yield
    modules_to_remove = [
        key for key in sys.modules if key.startswith("app.cspm_plugin")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def mock_tools_available():
    """TOOLS_AVAILABLE=True かつ各ツールをモック化

    4つのツール関数すべてをMagicMock/AsyncMockに置換し、
    外部依存（subprocess, OpenSearch, RAG）を完全に遮断する。
    """
    mock_validate = MagicMock()
    mock_validate.invoke = MagicMock(return_value="Validation successful.")

    mock_schema = MagicMock()
    mock_schema.invoke = MagicMock(return_value="schema content")

    mock_resources = MagicMock()
    mock_resources.invoke = MagicMock(return_value="ec2\ns3")

    mock_reference = MagicMock()
    mock_reference.ainvoke = AsyncMock(return_value="Reference content")

    patches = {
        "tools_available": patch(
            "app.cspm_plugin.tools_router.TOOLS_AVAILABLE", True
        ),
        "validate": patch(
            "app.cspm_plugin.tools_router.validate_policy", mock_validate
        ),
        "schema": patch(
            "app.cspm_plugin.tools_router.get_custodian_schema", mock_schema
        ),
        "resources": patch(
            "app.cspm_plugin.tools_router.list_available_resources", mock_resources
        ),
        "reference": patch(
            "app.cspm_plugin.tools_router.retrieve_reference", mock_reference
        ),
    }

    for p in patches.values():
        p.start()

    yield {
        "validate_policy": mock_validate,
        "get_custodian_schema": mock_schema,
        "list_available_resources": mock_resources,
        "retrieve_reference": mock_reference,
    }

    for p in patches.values():
        p.stop()


@pytest.fixture
def mock_tools_unavailable():
    """TOOLS_AVAILABLE=False 状態のモック

    ツールインポート失敗時の状態を再現。
    全エンドポイントで 503 を返すことを検証する。
    """
    patches = {
        "tools_available": patch(
            "app.cspm_plugin.tools_router.TOOLS_AVAILABLE", False
        ),
        "validate": patch(
            "app.cspm_plugin.tools_router.validate_policy", None
        ),
        "schema": patch(
            "app.cspm_plugin.tools_router.get_custodian_schema", None
        ),
        "resources": patch(
            "app.cspm_plugin.tools_router.list_available_resources", None
        ),
        "reference": patch(
            "app.cspm_plugin.tools_router.retrieve_reference", None
        ),
    }

    for p in patches.values():
        p.start()

    yield

    for p in patches.values():
        p.stop()


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
# tools_router.py 関連テストのみ実行
pytest test/unit/cspm_plugin/test_tools_router.py -v

# TOOLS_AVAILABLE テストのみ実行
pytest test/unit/cspm_plugin/test_tools_router.py::TestToolsUnavailable -v

# カバレッジ付きで実行
pytest test/unit/cspm_plugin/test_tools_router.py --cov=app.cspm_plugin.tools_router --cov-report=term-missing -v

# セキュリティテストのみ実行
pytest test/unit/cspm_plugin/test_tools_router.py -m "security" -v

# cspm_plugin 全テスト
pytest test/unit/cspm_plugin/ -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 10 | CSPM-TR-001 〜 CSPM-TR-010 |
| 異常系 | 12 | CSPM-TR-E01 〜 CSPM-TR-E12 |
| セキュリティ | 7 | CSPM-TR-SEC-01 〜 CSPM-TR-SEC-07 |
| **合計** | **29** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestToolsValidateEndpoint` | CSPM-TR-001〜003, 010 | 4 |
| `TestToolsSchemaEndpoint` | CSPM-TR-004〜005 | 2 |
| `TestToolsResourcesEndpoint` | CSPM-TR-006〜007 | 2 |
| `TestToolsReferenceEndpoint` | CSPM-TR-008〜009 | 2 |
| `TestToolsUnavailable` | CSPM-TR-E01〜E04 | 4 |
| `TestToolsEndpointExceptions` | CSPM-TR-E05〜E08 | 4 |
| `TestToolsValidationErrors` | CSPM-TR-E09〜E12 | 4 |
| `TestToolsRouterSecurity` | CSPM-TR-SEC-01〜SEC-07 | 7 |

### 実装失敗が予想されるテスト

| テストID | 失敗理由 | 修正方針 |
|---------|---------|---------|
| CSPM-TR-SEC-01 | 全4エンドポイントの Exception ハンドラー（L93, L133, L172, L215）で `str(e)` が detail に含まれ、内部エラー情報が露出 | Error ID のみを返し、エラー詳細はサーバーログにのみ記録するように修正 |

### 注意事項

- テスト実行に `pytest-asyncio` が必要
- `@pytest.mark.security` マーカーの登録が必要（`pyproject.toml`）
- `mock_tools_available` は 5 つの patch を管理するため、テスト後の cleanup が重要
- `retrieve_reference` のみ非同期（`ainvoke`）であり、他のツールは同期（`invoke`）

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | 全4エンドポイントの Exception ハンドラーで `str(e)` が HTTPException.detail に含まれる（L93, L133, L172, L215） | 内部エラー情報（IPアドレス、接続文字列等）がクライアントに露出するリスク | Error ID のみを返すように実装修正を推奨。CSPM-TR-SEC-01 で xfail マーク済み |
| 2 | TOOLS_AVAILABLE はモジュールレベルで決定され、実行時変更不可 | ツールの動的ロード・アンロードに非対応 | テストでは patch で切り替えるが、本番ではコンテナ再起動が必要 |
| 3 | `retrieve_reference` のみ非同期（`ainvoke`）、他3つは同期（`invoke`） | テストのモック方式が異なる | フィクスチャで `MagicMock`/`AsyncMock` を適切に使い分ける |
| 4 | 本仕様書は tools_router.py のみをカバー | ツール関数の内部ロジック（JSON/YAML解析、subprocess実行等）は別仕様書 | [cspm_tools_tests.md](./cspm_tools_tests.md) を参照 |
| 5 | 認証・認可テストが含まれていない | MCPツールエンドポイントが認証保護されているか未検証 | 認証が必要な場合は別途テスト追加を検討（router.py の Depends 設定確認） |
| 6 | レート制限テストが含まれていない | DoS攻撃への耐性が未検証 | 本番環境ではリバースプロキシ（nginx等）でレート制限設定を推奨 |
| 7 | リクエストサイズ制限がFastAPIデフォルト（無制限） | 大容量リクエストによるリソース枯渇リスク | nginx等で1MB程度の制限設定を推奨 |
| 8 | ログ出力時のサニタイズはアプリケーション層では未実施 | ログインジェクションのリスクは低いが存在 | ロギング設定でフォーマッターによるエスケープを推奨（本仕様書ではHTTP層の正常処理のみ検証） |

### セキュリティテストに関する注記

本仕様書に含まれるセキュリティテスト（CSPM-TR-SEC-01〜07）は、HTTPエンドポイント層での基本的なセキュリティ検証をカバーしています。以下の高度なセキュリティテストは将来的な追加を推奨:

- **認証・認可テスト**: JWT未認証/無効トークンでのアクセス拒否（制限事項#5）
- **レート制限テスト**: 短時間での大量リクエストの制限（制限事項#6、nginx等で対応推奨）
- **SSRF攻撃防止テスト**: retrieve_reference のクエリに内部URLを含むケース（tools.py の責務として分離）
- **CORS設定検証テスト**: 不正なOriginからのアクセス制限（MCPエンドポイントの用途による）

> **ログインジェクション**: CSPM-TR-SEC-06〜07 でHTTP層での正常処理を検証済み。
> 実際のログサニタイズはロギング設定の責務として分離（制限事項#8）。
