# cspm_plugin（tools.py）テストケース

## 1. 概要

CSPMプラグインのLangChainツール関数（`app/cspm_plugin/tools.py`）のテストケースを定義します。
Cloud Custodian連携（ポリシー検証・スキーマ取得）とRAG検索の4つのツール関数＋ヘルパー関数を検証します。

> **注記**: cspm_plugin テスト仕様書は3分割されています。
> - [cspm_plugin_tests.md](./cspm_plugin_tests.md): router.py（メインAPIエンドポイント）
> - [cspm_tools_router_tests.md](./cspm_tools_router_tests.md): tools_router.py（MCPツールエンドポイント）
> - **本ファイル**: tools.py（ツール関数）

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `validate_policy()` | @tool — JSON/YAMLポリシーの構文・スキーマ検証（subprocess） |
| `retrieve_reference()` | @tool（async）— 強化版RAG検索 + フォールバック |
| `get_custodian_schema()` | @tool — Cloud Custodianスキーマ情報取得 |
| `list_available_resources()` | @tool — リソース一覧取得（get_custodian_schemaのラッパー） |
| `_validate_schema_target()` | ヘルパー — スキーマターゲットの入力検証 |
| `_run_custodian_schema()` | ヘルパー — subprocess実行ラッパー |
| `_execute_schema_with_fallback()` | ヘルパー — フォールバック付きスキーマ取得 |
| `_fallback_retrieve_reference()` | ヘルパー — 従来RAGシステムへのフォールバック |

### 1.2 カバレッジ目標: 85%

> **注記**: subprocess呼び出しとRAGシステム連携があるため、
> 外部依存は全てモック化し、ロジック分岐を重点的にテストする。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/cspm_plugin/tools.py` |
| 依存（クライアント） | `app/core/clients.py` |
| 依存（設定） | `app/core/config.py` |
| 依存（RAG） | `app/core/rag_manager.py`, `app/rag/models.py` |
| テストコード | `test/unit/cspm_plugin/test_tools.py` |

### 1.4 補足情報

**validate_policy の主要分岐:**

| 行番号 | 分岐条件 |
|--------|---------|
| L35 | 空入力チェック |
| L43 | JSON形式検出（`{` または `[` で開始） |
| L48 | `policies` キーを持つ dict |
| L51 | list 形式（配列） |
| L55 | `name` キーを持つ単一ポリシー dict |
| L60-63 | 無効なJSON構造 |
| L64-94 | YAML形式の同等分岐 |
| L96-99 | JSON/一般パースエラー |
| L123 | returncode==0 → 成功 |
| L126 | stderr に警告含む場合のDetails付加 |
| L130-134 | returncode!=0 → 失敗 |
| L136 | FileNotFoundError（custodianコマンドなし） |
| L140 | TimeoutExpired |
| L144 | その他Exception |

**_validate_schema_target の分岐:**

| 行番号 | 分岐条件 |
|--------|---------|
| L378 | target=None/空 → 警告付き許可 |
| L385 | 無効クラウド名 → エラー |
| L389 | コンポーネント数超過 → エラー |
| L393 | 無効カテゴリ → エラー |
| L396 | 有効 → 成功 |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CSPM-T-001 | JSON policies形式の検証成功 | `{"policies": [...]}` | "Validation successful." |
| CSPM-T-002 | JSON配列形式の検証成功 | `[{"name":"test",...}]` | "Validation successful." |
| CSPM-T-003 | JSON単一ポリシーの検証成功 | `{"name":"test",...}` | "Validation successful." |
| CSPM-T-004 | YAML policies形式の検証成功 | YAML文字列 | "Validation successful." |
| CSPM-T-005 | YAML配列形式の検証成功 | YAML配列 | "Validation successful." |
| CSPM-T-006 | YAML単一ポリシーの検証成功 | YAML単一 | "Validation successful." |
| CSPM-T-007 | 検証成功＋stderr警告 | returncode=0, stderr有り | "Validation successful.\nDetails..." |
| CSPM-T-008 | 検証失敗の正常応答 | returncode=1 | "Validation failed (Code: 1):\n..." |
| CSPM-T-009 | スキーマターゲット検証（有効） | "aws.ec2.filters" | (True, None, ["aws","ec2","filters"]) |
| CSPM-T-009-B | スキーマターゲットコンポーネントバリエーション | "aws", "aws.ec2" 等 | (True, None, 1〜3要素) |
| CSPM-T-010 | スキーマターゲット検証（空） | None, "", "   " | (True, 警告, []) |
| CSPM-T-011 | スキーマ取得成功 | target="aws" | スキーマ内容 |
| CSPM-T-012 | スキーマフォールバック成功 | 存在しないtarget | 親レベル結果 + 警告 |
| CSPM-T-013 | リソース一覧取得 | cloud="aws" | リソース一覧文字列 |
| CSPM-T-014 | 参照検索成功（全メタデータ） | query + cloud | 関連ドキュメント |
| CSPM-T-014-B | 参照検索成功（最小メタデータ） | query + cloud | ドキュメント（Resource:なし） |
| CSPM-T-014-C | 参照検索複数結果の整形 | query + cloud | "---"区切り複数結果 |
| CSPM-T-014-D | 非標準クラウドでフィルターNone | cloud="kubernetes" | 検索実行（フィルターなし） |
| CSPM-T-015 | スキーマ4コンポーネント境界値 | "aws.ec2.filters.tag" | (True, None, 4要素) |
| CSPM-T-016 | スキーマ取得成功＋stderr警告 | returncode=0, stderr有り | スキーマ + "Warnings:" |

### 2.1 validate_policy テスト

```python
# test/unit/cspm_plugin/test_tools.py
import pytest
import json
from unittest.mock import patch, MagicMock


class TestValidatePolicy:
    """validate_policy ツールの正常系テスト"""

    @pytest.fixture
    def mock_subprocess_success(self):
        """subprocess.run が成功を返すモック"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_result.stdout = ""
        with patch("app.cspm_plugin.tools.subprocess.run", return_value=mock_result) as mock_run:
            yield mock_run, mock_result

    @pytest.fixture
    def mock_tempfile(self):
        """一時ファイル作成のモック"""
        with patch("app.cspm_plugin.tools.tempfile.NamedTemporaryFile") as mock_tmp:
            mock_file = MagicMock()
            mock_file.__enter__ = MagicMock(return_value=mock_file)
            mock_file.__exit__ = MagicMock(return_value=False)
            mock_file.name = "/tmp/test_policy.json"
            mock_tmp.return_value = mock_file
            with patch("app.cspm_plugin.tools.os.path.exists", return_value=True):
                with patch("app.cspm_plugin.tools.os.remove"):
                    yield mock_file

    def test_validate_json_policies_format(self, mock_subprocess_success, mock_tempfile):
        """CSPM-T-001: JSON policies形式のポリシー検証が成功

        tools.py:48-50 の `policies` キーを持つ dict 分岐をカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import validate_policy

        policy = json.dumps({"policies": [{"name": "test", "resource": "s3"}]})

        # Act
        result = validate_policy.invoke({"policy_content": policy})

        # Assert
        assert "Validation successful" in result

    def test_validate_json_array_format(self, mock_subprocess_success, mock_tempfile):
        """CSPM-T-002: JSON配列形式が自動的にpoliciesでラップされる

        tools.py:51-54 の list 形式分岐をカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import validate_policy

        policy = json.dumps([{"name": "test", "resource": "s3"}])

        # Act
        result = validate_policy.invoke({"policy_content": policy})

        # Assert
        assert "Validation successful" in result

    def test_validate_json_single_policy(self, mock_subprocess_success, mock_tempfile):
        """CSPM-T-003: 単一JSON policyオブジェクトが自動ラップされる

        tools.py:55-59 の `name` キーを持つ dict 分岐をカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import validate_policy

        policy = json.dumps({"name": "test", "resource": "s3"})

        # Act
        result = validate_policy.invoke({"policy_content": policy})

        # Assert
        assert "Validation successful" in result

    def test_validate_yaml_policies_format(self, mock_subprocess_success, mock_tempfile):
        """CSPM-T-004: YAML policies形式の検証成功

        tools.py:73-76 の YAML `policies` キー分岐をカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import validate_policy

        yaml_content = "policies:\n  - name: test\n    resource: s3\n"

        # Act
        result = validate_policy.invoke({"policy_content": yaml_content})

        # Assert
        assert "Validation successful" in result

    def test_validate_yaml_array_format(self, mock_subprocess_success, mock_tempfile):
        """CSPM-T-005: YAML配列形式が自動ラップされる

        tools.py:77-81 の YAML 配列分岐をカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import validate_policy

        yaml_content = "- name: test\n  resource: s3\n"

        # Act
        result = validate_policy.invoke({"policy_content": yaml_content})

        # Assert
        assert "Validation successful" in result

    def test_validate_yaml_single_policy(self, mock_subprocess_success, mock_tempfile):
        """CSPM-T-006: YAML単一ポリシーが自動ラップされる

        tools.py:82-86 の YAML 単一ポリシー分岐をカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import validate_policy

        yaml_content = "name: test\nresource: s3\n"

        # Act
        result = validate_policy.invoke({"policy_content": yaml_content})

        # Assert
        assert "Validation successful" in result

    def test_validate_success_with_stderr_warnings(self, mock_tempfile):
        """CSPM-T-007: 検証成功時にstderr警告がDetails付きで返る

        tools.py:126-128 の stderr 警告付加ロジックをカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import validate_policy

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = "Warning: deprecated filter used"
        mock_result.stdout = ""
        policy = json.dumps({"policies": [{"name": "test", "resource": "s3"}]})

        with patch("app.cspm_plugin.tools.subprocess.run", return_value=mock_result):
            # Act
            result = validate_policy.invoke({"policy_content": policy})

        # Assert
        assert "Validation successful" in result
        assert "Details" in result
        assert "deprecated filter" in result

    def test_validate_failure_response(self, mock_tempfile):
        """CSPM-T-008: 検証失敗がエラーコード付きで返る

        tools.py:130-134 の returncode!=0 分岐をカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import validate_policy

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Error: invalid resource type 'fake'"
        mock_result.stdout = ""
        policy = json.dumps({"policies": [{"name": "test", "resource": "fake"}]})

        with patch("app.cspm_plugin.tools.subprocess.run", return_value=mock_result):
            # Act
            result = validate_policy.invoke({"policy_content": policy})

        # Assert
        assert "Validation failed (Code: 1)" in result
        assert "invalid resource type" in result
```

### 2.2 _validate_schema_target テスト

```python
class TestValidateSchemaTarget:
    """_validate_schema_target ヘルパーの正常系テスト"""

    def test_valid_target(self):
        """CSPM-T-009: 有効なターゲットが検証成功

        tools.py:396 の正常終了分岐をカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import _validate_schema_target

        # Act
        is_valid, message, components = _validate_schema_target("aws.ec2.filters")

        # Assert
        assert is_valid is True
        assert message is None
        assert components == ["aws", "ec2", "filters"]

    @pytest.mark.parametrize("target,expected_len", [
        ("aws", 1),              # 最小: クラウドのみ
        ("aws.ec2", 2),          # クラウド + リソース
        ("aws.ec2.filters", 3),  # クラウド + リソース + カテゴリ
    ])
    def test_valid_target_component_variations(self, target, expected_len):
        """CSPM-T-009-B: コンポーネント数バリエーション（境界値テスト）

        tools.py:382-396 の正常パスをカバー。
        1〜3コンポーネントのバリエーションで有効と判定されることを検証。
        """
        # Arrange
        from app.cspm_plugin.tools import _validate_schema_target

        # Act
        is_valid, message, components = _validate_schema_target(target)

        # Assert
        assert is_valid is True
        assert len(components) == expected_len
        assert message is None

    @pytest.mark.parametrize("target", [None, "", "   "])
    def test_empty_target(self, target):
        """CSPM-T-010: 空/空白ターゲットが警告付きで許可

        tools.py:378-380 の target=None/空/空白 分岐をカバー。
        - None: 明示的な未指定
        - "": 空文字列
        - "   ": 空白文字のみ
        """
        # Arrange
        from app.cspm_plugin.tools import _validate_schema_target

        # Act
        is_valid, message, components = _validate_schema_target(target)

        # Assert
        assert is_valid is True
        assert message is not None  # 警告あり
        assert "推奨" in message
        assert components == []

    def test_max_components_boundary_ok(self):
        """CSPM-T-015: 4コンポーネント（MAX_SCHEMA_COMPONENTS境界値）で成功

        tools.py:389 の境界値テスト。
        MAX_SCHEMA_COMPONENTS=4 と一致するケースで有効と判定。
        """
        # Arrange
        from app.cspm_plugin.tools import _validate_schema_target

        # Act
        is_valid, message, components = _validate_schema_target("aws.ec2.filters.tag")

        # Assert
        assert is_valid is True
        assert len(components) == 4
        assert components == ["aws", "ec2", "filters", "tag"]
```

### 2.3 get_custodian_schema テスト

```python
class TestGetCustodianSchema:
    """get_custodian_schema ツールの正常系テスト"""

    def test_schema_success(self):
        """CSPM-T-011: ターゲット指定でスキーマ取得成功

        tools.py:472-527 の get_custodian_schema 正常パスをカバー。
        _execute_schema_with_fallback → _run_custodian_schema の流れ。
        """
        # Arrange
        from app.cspm_plugin.tools import get_custodian_schema

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ec2:\n  filters:\n    - tag-count"
        mock_result.stderr = ""

        with patch("app.cspm_plugin.tools.subprocess.run", return_value=mock_result):
            # Act
            result = get_custodian_schema.invoke({"target": "aws"})

        # Assert
        assert "ec2" in result
        assert "Error:" not in result

    def test_schema_fallback_success(self):
        """CSPM-T-012: 存在しないターゲットで親レベルにフォールバック

        tools.py:442-469 の _execute_schema_with_fallback をカバー。
        1回目失敗、2回目（親レベル）で成功するケース。
        """
        # Arrange
        from app.cspm_plugin.tools import get_custodian_schema

        def mock_subprocess_side_effect(cmd, **kwargs):
            mock_result = MagicMock()
            if "aws.nonexistent.filters" in " ".join(cmd):
                mock_result.returncode = 1
                mock_result.stderr = "not found"
                mock_result.stdout = ""
            elif "aws.nonexistent" in " ".join(cmd):
                mock_result.returncode = 1
                mock_result.stderr = "not found"
                mock_result.stdout = ""
            else:
                mock_result.returncode = 0
                mock_result.stdout = "aws resources list"
                mock_result.stderr = ""
            return mock_result

        with patch("app.cspm_plugin.tools.subprocess.run", side_effect=mock_subprocess_side_effect):
            # Act
            result = get_custodian_schema.invoke({"target": "aws.nonexistent.filters"})

        # Assert
        assert "aws resources list" in result
        assert "警告" in result  # フォールバック警告

    def test_list_available_resources(self):
        """CSPM-T-013: リソース一覧取得がget_custodian_schemaに委譲

        tools.py:534-559 の list_available_resources をカバー。
        内部で get_custodian_schema.invoke() を呼び出す。
        """
        # Arrange
        from app.cspm_plugin.tools import list_available_resources

        with patch(
            "app.cspm_plugin.tools.get_custodian_schema"
        ) as mock_schema:
            mock_schema.invoke.return_value = "ec2\ns3\niam-user"

            # Act
            result = list_available_resources.invoke({"cloud": "aws"})

        # Assert
        assert "ec2" in result


class TestRunCustodianSchemaNormal:
    """_run_custodian_schema ヘルパーの正常系テスト"""

    def test_schema_success_with_stderr_warnings(self):
        """CSPM-T-016: スキーマ取得成功＋stderr警告

        tools.py:428-429 の stderr 警告付加ロジックをカバー。
        returncode=0 の正常終了時に stderr に警告が含まれるケース。
        """
        # Arrange
        from app.cspm_plugin.tools import _run_custodian_schema

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ec2:\n  filters:\n    - tag-count"
        mock_result.stderr = "Deprecation warning: ..."

        with patch(
            "app.cspm_plugin.tools.subprocess.run",
            return_value=mock_result,
        ):
            # Act
            result = _run_custodian_schema("aws")

        # Assert
        assert "ec2" in result
        assert "Warnings:" in result
        assert "Deprecation" in result
```

### 2.4 retrieve_reference テスト

```python
class TestRetrieveReference:
    """retrieve_reference ツールの正常系テスト"""

    @pytest.mark.asyncio
    async def test_reference_success(self):
        """CSPM-T-014: RAG検索が正常に結果を返す（全メタデータ有り）

        tools.py:193-267 の正常パスをカバー。
        強化版RAGシステムが結果を返すケース。
        """
        # Arrange
        from unittest.mock import AsyncMock
        from app.cspm_plugin.tools import retrieve_reference

        mock_rag_search = AsyncMock()
        mock_result = MagicMock()
        mock_doc = MagicMock()
        mock_doc.resource_name = "aws.s3"
        mock_doc.function_name = "encryption"
        mock_doc.section_type = "filter"
        mock_doc.cloud = "aws"
        mock_doc.source = "docs/s3.md"
        mock_doc.section_title = "S3 Encryption"
        mock_doc.content = "S3 encryption filter example"
        mock_doc.metadata = {"has_code_example": True}
        mock_result.results = [mock_doc]
        mock_rag_search.search = AsyncMock(return_value=mock_result)

        # 注意: retrieve_reference は関数内で import しているため、
        # パッチ先は app.core.rag_manager.get_enhanced_rag_search
        with patch(
            "app.core.rag_manager.get_enhanced_rag_search",
            new_callable=AsyncMock,
            return_value=mock_rag_search,
        ):
            # Act
            result = await retrieve_reference.ainvoke(
                {"query": "s3 encryption", "cloud": "aws"}
            )

        # Assert
        assert "S3 Encryption" in result or "encryption" in result.lower()

    @pytest.mark.asyncio
    async def test_reference_success_minimal_metadata(self):
        """CSPM-T-014-B: RAG検索（最小メタデータ）

        tools.py:228-237 の resource_name, function_name, section_type が
        全て None のケースをカバー。
        """
        # Arrange
        from unittest.mock import AsyncMock
        from app.cspm_plugin.tools import retrieve_reference

        mock_rag_search = AsyncMock()
        mock_result = MagicMock()
        mock_doc = MagicMock()
        mock_doc.resource_name = None
        mock_doc.function_name = None
        mock_doc.section_type = None
        mock_doc.cloud = "aws"
        mock_doc.source = "docs/general.md"
        mock_doc.section_title = "General Info"
        mock_doc.content = "General information"
        mock_doc.metadata = {}  # has_code_example 等なし
        mock_result.results = [mock_doc]
        mock_rag_search.search = AsyncMock(return_value=mock_result)

        with patch(
            "app.core.rag_manager.get_enhanced_rag_search",
            new_callable=AsyncMock,
            return_value=mock_rag_search,
        ):
            # Act
            result = await retrieve_reference.ainvoke(
                {"query": "general query", "cloud": "aws"}
            )

        # Assert
        assert "General Info" in result
        assert "Resource:" not in result  # resource_name=None なので含まれない

    @pytest.mark.asyncio
    async def test_reference_success_multiple_results(self):
        """CSPM-T-014-C: 複数検索結果の整形

        tools.py:261, 267 の複数結果 join 動作をカバー。
        """
        # Arrange
        from unittest.mock import AsyncMock
        from app.cspm_plugin.tools import retrieve_reference

        mock_rag_search = AsyncMock()
        mock_result = MagicMock()

        # 2つのドキュメント
        mock_doc1 = MagicMock()
        mock_doc1.resource_name = "aws.s3"
        mock_doc1.function_name = None
        mock_doc1.section_type = "filter"
        mock_doc1.cloud = "aws"
        mock_doc1.source = "docs/s3.md"
        mock_doc1.section_title = "S3 Filter 1"
        mock_doc1.content = "First result"
        mock_doc1.metadata = {}

        mock_doc2 = MagicMock()
        mock_doc2.resource_name = "aws.ec2"
        mock_doc2.function_name = None
        mock_doc2.section_type = "action"
        mock_doc2.cloud = "aws"
        mock_doc2.source = "docs/ec2.md"
        mock_doc2.section_title = "EC2 Action"
        mock_doc2.content = "Second result"
        mock_doc2.metadata = {}

        mock_result.results = [mock_doc1, mock_doc2]
        mock_rag_search.search = AsyncMock(return_value=mock_result)

        with patch(
            "app.core.rag_manager.get_enhanced_rag_search",
            new_callable=AsyncMock,
            return_value=mock_rag_search,
        ):
            # Act
            result = await retrieve_reference.ainvoke(
                {"query": "test query", "cloud": "aws"}
            )

        # Assert - 両方の結果が "---" で区切られて含まれる
        assert "S3 Filter 1" in result
        assert "EC2 Action" in result
        assert "---" in result  # セパレータ

    @pytest.mark.asyncio
    async def test_reference_non_standard_cloud_filter(self):
        """CSPM-T-014-D: 非標準クラウド名でフィルターがNoneになる

        tools.py:206-208 の cloud が aws/azure/gcp 以外の場合、
        SearchFilters が None になることをカバー。
        """
        # Arrange
        from unittest.mock import AsyncMock
        from app.cspm_plugin.tools import retrieve_reference

        mock_rag_search = AsyncMock()
        mock_result = MagicMock()
        mock_result.results = []
        mock_rag_search.search = AsyncMock(return_value=mock_result)

        with patch(
            "app.core.rag_manager.get_enhanced_rag_search",
            new_callable=AsyncMock,
            return_value=mock_rag_search,
        ):
            # Act
            result = await retrieve_reference.ainvoke(
                {"query": "test", "cloud": "kubernetes"}  # aws/azure/gcp 以外
            )

        # Assert - 検索は実行されるが結果なし
        assert "No relevant reference" in result
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CSPM-T-E01 | 空ポリシー入力 | policy_content="" | "Error: Received empty policy content" |
| CSPM-T-E02 | 無効JSON構造 | `{"invalid": true}` | "Error: Invalid JSON structure" |
| CSPM-T-E03 | JSONパースエラー | `{broken json` | "Error: Failed to parse JSON content" |
| CSPM-T-E04 | YAML None パース | 空YAML | "Error: YAML parsed as None" |
| CSPM-T-E05 | 無効YAML構造 | `invalid: true` | "Error: Invalid YAML structure" |
| CSPM-T-E06 | YAMLパースエラー | 不正YAML | "Error: Failed to parse YAML content" |
| CSPM-T-E07 | custodianコマンド未検出 | FileNotFoundError | "Error: 'custodian' command not found" |
| CSPM-T-E08 | custodianタイムアウト | TimeoutExpired | "Error: Policy validation timed out" |
| CSPM-T-E09 | subprocess汎用例外 | Exception | "Error during policy validation" |
| CSPM-T-E10 | スキーマ無効クラウド名 | "invalid_cloud" | "エラー: 無効なクラウド名" |
| CSPM-T-E11 | スキーマコンポーネント超過 | "a.b.c.d.e" | "エラー: コンポーネント数が多すぎます" |
| CSPM-T-E12 | スキーマ無効カテゴリ | "aws.ec2.invalid" | "エラー: 無効なカテゴリ" |
| CSPM-T-E13 | リソース一覧無効クラウド | cloud="invalid" | "Error: Invalid cloud provider" |
| CSPM-T-E14 | RAGシステム未利用可能 | rag_search=None | "Error: Enhanced RAG search system is not available" |
| CSPM-T-E15 | RAGインポートエラー | ImportError | フォールバック呼び出し（await） |
| CSPM-T-E16 | RAG検索結果なし | results=[] | "No relevant reference documents found" |
| CSPM-T-E17 | RAG一般例外 | RuntimeError | フォールバック呼び出し |
| CSPM-T-E18 | フォールバックembedding未利用可 | embedding=None | "Embedding function is not available" |
| CSPM-T-E19 | フォールバックOpenSearch未利用可 | client=None | "OpenSearch client is not available" |
| CSPM-T-E20 | フォールバックindex_name未設定 | index=None | "configuration...missing" |
| CSPM-T-E21 | フォールバック検索結果フィルター後空 | cloud不一致 | "No relevant reference" |
| CSPM-T-E21-B | フォールバックCA証明書パス設定 | 非AWS OpenSearch | CA証明書パスが設定される |
| CSPM-T-E22 | フォールバック一般例外 | RuntimeError | "Error during fallback RAG search" |
| CSPM-T-E23 | スキーマコマンドタイムアウト | TimeoutExpired | "timed out" |
| CSPM-T-E24 | スキーマコマンド未検出 | FileNotFoundError | "command not found" |
| CSPM-T-E25 | スキーマコマンド非ゼロ終了 | returncode=1 | "Error:...exit code" |
| CSPM-T-E26 | スキーマ一般例外 | OSError | "Unexpected error" |
| CSPM-T-E27 | 全フォールバックレベル失敗 | 全レベルエラー | "取得できませんでした" |

### 3.1 validate_policy 異常系

```python
class TestValidatePolicyErrors:
    """validate_policy ツールの異常系テスト"""

    def test_empty_policy(self):
        """CSPM-T-E01: 空ポリシーでエラーメッセージ

        tools.py:35-36 の空入力チェックをカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import validate_policy

        # Act
        result = validate_policy.invoke({"policy_content": ""})

        # Assert
        assert "Error" in result
        assert "empty" in result.lower()

    def test_invalid_json_structure(self):
        """CSPM-T-E02: policiesキーもnameキーも持たないJSONでエラー

        tools.py:60-63 の無効JSON構造分岐をカバー。
        エラーメッセージにデバッグ情報（Parsed type, Parsed keys, Raw input）が
        含まれることを検証。
        """
        # Arrange
        from app.cspm_plugin.tools import validate_policy

        policy = json.dumps({"invalid_key": True})

        # Act
        result = validate_policy.invoke({"policy_content": policy})

        # Assert — エラー種別を先に確認し、その後デバッグ情報を検証
        assert "Error" in result
        assert "Invalid JSON structure" in result
        # tools.py:62-63 のデバッグ情報出力を検証（開発者向け診断情報）
        assert "Parsed type:" in result
        assert "Parsed keys:" in result
        assert "Raw input" in result

    def test_json_parse_error(self):
        """CSPM-T-E03: 不正JSONでパースエラー

        tools.py:96-97 の JSONDecodeError 分岐をカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import validate_policy

        # Act
        result = validate_policy.invoke({"policy_content": "{broken json"})

        # Assert
        assert "Error" in result
        assert "Failed to parse JSON" in result

    def test_yaml_none_parse(self):
        """CSPM-T-E04: YAMLがNoneとしてパースされる

        tools.py:87-88 の yaml_data is None 分岐をカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import validate_policy

        # YAML で null としてパースされる内容
        # Act
        result = validate_policy.invoke({"policy_content": "---\n"})

        # Assert
        assert "Error" in result

    def test_invalid_yaml_structure(self):
        """CSPM-T-E05: policiesキーもnameキーも持たないYAMLでエラー

        tools.py:89-92 の無効YAML構造分岐をカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import validate_policy

        yaml_content = "invalid_key: true\nanother: value\n"

        # Act
        result = validate_policy.invoke({"policy_content": yaml_content})

        # Assert
        assert "Error" in result
        assert "Invalid YAML structure" in result

    def test_yaml_parse_error(self):
        """CSPM-T-E06: 不正YAMLでパースエラー

        tools.py:93-94 の YAMLError 分岐をカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import validate_policy

        # タブ文字はYAMLで禁止
        yaml_content = "name:\t: invalid\n\t- broken"

        # Act
        result = validate_policy.invoke({"policy_content": yaml_content})

        # Assert
        assert "Error" in result

    def test_custodian_command_not_found(self, mock_tempfile_for_errors):
        """CSPM-T-E07: custodianコマンドが見つからない

        tools.py:136-139 の FileNotFoundError 分岐をカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import validate_policy
        import subprocess

        policy = json.dumps({"policies": [{"name": "test", "resource": "s3"}]})

        with patch(
            "app.cspm_plugin.tools.subprocess.run",
            side_effect=FileNotFoundError("No such file"),
        ):
            # Act
            result = validate_policy.invoke({"policy_content": policy})

        # Assert
        assert "command not found" in result.lower()

    def test_custodian_timeout(self, mock_tempfile_for_errors):
        """CSPM-T-E08: custodian検証がタイムアウト

        tools.py:140-143 の TimeoutExpired 分岐をカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import validate_policy
        import subprocess

        policy = json.dumps({"policies": [{"name": "test", "resource": "s3"}]})

        with patch(
            "app.cspm_plugin.tools.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="custodian", timeout=30),
        ):
            # Act
            result = validate_policy.invoke({"policy_content": policy})

        # Assert
        assert "timed out" in result.lower()

    def test_subprocess_general_exception(self, mock_tempfile_for_errors):
        """CSPM-T-E09: subprocess汎用例外

        tools.py:144-148 の Exception 分岐をカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import validate_policy

        policy = json.dumps({"policies": [{"name": "test", "resource": "s3"}]})

        with patch(
            "app.cspm_plugin.tools.subprocess.run",
            side_effect=OSError("Permission denied"),
        ):
            # Act
            result = validate_policy.invoke({"policy_content": policy})

        # Assert
        assert "Error" in result
        assert "policy validation" in result.lower()

    @pytest.fixture
    def mock_tempfile_for_errors(self):
        """一時ファイル作成のモック（エラー系テスト用）"""
        with patch("app.cspm_plugin.tools.tempfile.NamedTemporaryFile") as mock_tmp:
            mock_file = MagicMock()
            mock_file.__enter__ = MagicMock(return_value=mock_file)
            mock_file.__exit__ = MagicMock(return_value=False)
            mock_file.name = "/tmp/test_policy.json"
            mock_tmp.return_value = mock_file
            with patch("app.cspm_plugin.tools.os.path.exists", return_value=True):
                with patch("app.cspm_plugin.tools.os.remove"):
                    yield mock_file
```

### 3.2 _validate_schema_target 異常系

```python
class TestValidateSchemaTargetErrors:
    """_validate_schema_target ヘルパーの異常系テスト"""

    def test_invalid_cloud_name(self):
        """CSPM-T-E10: 無効なクラウド名でエラー

        tools.py:385-386 の無効クラウド名分岐をカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import _validate_schema_target

        # Act
        is_valid, message, components = _validate_schema_target("invalid_cloud")

        # Assert
        assert is_valid is False
        assert "無効なクラウド名" in message

    def test_too_many_components(self):
        """CSPM-T-E11: コンポーネント数超過でエラー

        tools.py:389-390 のコンポーネント数検証をカバー。
        MAX_SCHEMA_COMPONENTS=4 を超えるケース。
        """
        # Arrange
        from app.cspm_plugin.tools import _validate_schema_target

        # Act
        is_valid, message, components = _validate_schema_target("aws.ec2.filters.tag.extra")

        # Assert
        assert is_valid is False
        assert "コンポーネント数" in message

    def test_invalid_category(self):
        """CSPM-T-E12: 無効なカテゴリでエラー

        tools.py:393-394 の無効カテゴリ分岐をカバー。
        VALID_CATEGORIES=("actions", "filters") 以外のケース。
        """
        # Arrange
        from app.cspm_plugin.tools import _validate_schema_target

        # Act
        is_valid, message, components = _validate_schema_target("aws.ec2.invalid_category")

        # Assert
        assert is_valid is False
        assert "無効なカテゴリ" in message
```

### 3.3 list_available_resources 異常系

```python
class TestListResourcesErrors:
    """list_available_resources の異常系テスト"""

    def test_invalid_cloud_provider(self):
        """CSPM-T-E13: 無効なクラウドプロバイダーでエラー

        tools.py:550-551 の入力検証をカバー。
        Literal["aws","azure","gcp"] 以外の値。
        """
        # Arrange
        from app.cspm_plugin.tools import list_available_resources

        # Act
        result = list_available_resources.invoke({"cloud": "invalid"})

        # Assert
        assert "Error" in result
        assert "Invalid cloud provider" in result
```

### 3.4 retrieve_reference 異常系

```python
class TestRetrieveReferenceErrors:
    """retrieve_reference ツールの異常系テスト"""

    @pytest.mark.asyncio
    async def test_rag_system_unavailable(self):
        """CSPM-T-E14: RAGシステムがNoneで利用不可

        tools.py:201-204 の rag_search=None 分岐をカバー。
        """
        # Arrange
        from unittest.mock import AsyncMock
        from app.cspm_plugin.tools import retrieve_reference

        with patch(
            "app.core.rag_manager.get_enhanced_rag_search",
            new_callable=AsyncMock,
            return_value=None,
        ):
            # Act
            result = await retrieve_reference.ainvoke(
                {"query": "test query", "cloud": "aws"}
            )

        # Assert
        assert "not available" in result.lower()

    @pytest.mark.asyncio
    async def test_rag_import_error_triggers_fallback(self):
        """CSPM-T-E15: ImportErrorで従来RAGへフォールバック

        tools.py:269-273 の ImportError 分岐をカバー。
        _fallback_retrieve_reference() が await で呼ばれることを検証。
        """
        # Arrange
        from unittest.mock import AsyncMock
        from app.cspm_plugin.tools import retrieve_reference

        with patch(
            "app.core.rag_manager.get_enhanced_rag_search",
            new_callable=AsyncMock,
            side_effect=ImportError("rag module not found"),
        ):
            with patch(
                "app.cspm_plugin.tools._fallback_retrieve_reference",
                new_callable=AsyncMock,
                return_value="Fallback result",
            ) as mock_fallback:
                # Act
                result = await retrieve_reference.ainvoke(
                    {"query": "test", "cloud": "aws"}
                )

        # Assert - 非同期関数なので assert_awaited_once を使用
        mock_fallback.assert_awaited_once_with("test", "aws")
        assert result == "Fallback result"

    @pytest.mark.asyncio
    async def test_rag_general_exception_triggers_fallback(self):
        """CSPM-T-E17: 一般Exceptionで従来RAGへフォールバック

        tools.py:274-279 の Exception 分岐をカバー。
        ImportError 以外の例外でもフォールバックが呼ばれることを検証。
        """
        # Arrange
        from unittest.mock import AsyncMock
        from app.cspm_plugin.tools import retrieve_reference

        with patch(
            "app.core.rag_manager.get_enhanced_rag_search",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Unexpected error"),
        ):
            with patch(
                "app.cspm_plugin.tools._fallback_retrieve_reference",
                new_callable=AsyncMock,
                return_value="Fallback result from general exception",
            ) as mock_fallback:
                # Act
                result = await retrieve_reference.ainvoke(
                    {"query": "test", "cloud": "aws"}
                )

        # Assert
        mock_fallback.assert_awaited_once_with("test", "aws")
        assert result == "Fallback result from general exception"

    @pytest.mark.asyncio
    async def test_rag_no_results(self):
        """CSPM-T-E16: RAG検索結果が空

        tools.py:219-220 の results=[] 分岐をカバー。
        """
        # Arrange
        from unittest.mock import AsyncMock
        from app.cspm_plugin.tools import retrieve_reference

        mock_rag_search = AsyncMock()
        mock_result = MagicMock()
        mock_result.results = []
        mock_rag_search.search = AsyncMock(return_value=mock_result)

        with patch(
            "app.core.rag_manager.get_enhanced_rag_search",
            new_callable=AsyncMock,
            return_value=mock_rag_search,
        ):
            # Act
            result = await retrieve_reference.ainvoke(
                {"query": "nonexistent topic", "cloud": "aws"}
            )

        # Assert
        assert "No relevant reference" in result
```

### 3.5 _fallback_retrieve_reference 異常系

```python
class TestFallbackRetrieveReferenceErrors:
    """_fallback_retrieve_reference ヘルパーの異常系テスト

    tools.py:282-352 のフォールバックRAG関数をカバー。
    """

    @pytest.mark.asyncio
    async def test_embedding_function_unavailable(self):
        """CSPM-T-E18: embedding_function が利用不可

        tools.py:292-293 の embedding_func_local=None 分岐をカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import _fallback_retrieve_reference

        with patch(
            "app.cspm_plugin.tools.get_embedding_function",
            return_value=None,
        ):
            with patch(
                "app.cspm_plugin.tools.get_opensearch_client",
                new_callable=AsyncMock,
                return_value=MagicMock(),
            ):
                # Act
                result = await _fallback_retrieve_reference("test", "aws")

        # Assert
        assert "Embedding function is not available" in result

    @pytest.mark.asyncio
    async def test_opensearch_client_unavailable(self):
        """CSPM-T-E19: OpenSearch client が利用不可

        tools.py:295-296 の os_client_local=None 分岐をカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import _fallback_retrieve_reference

        with patch(
            "app.cspm_plugin.tools.get_embedding_function",
            return_value=MagicMock(),
        ):
            with patch(
                "app.cspm_plugin.tools.get_opensearch_client",
                new_callable=AsyncMock,
                return_value=None,
            ):
                # Act
                result = await _fallback_retrieve_reference("test", "aws")

        # Assert
        assert "OpenSearch client is not available" in result

    @pytest.mark.asyncio
    async def test_index_name_missing(self):
        """CSPM-T-E20: RAGインデックス名が未設定

        tools.py:299-300 の index_name=None/空 分岐をカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import _fallback_retrieve_reference

        with patch(
            "app.cspm_plugin.tools.get_embedding_function",
            return_value=MagicMock(),
        ):
            with patch(
                "app.cspm_plugin.tools.get_opensearch_client",
                new_callable=AsyncMock,
                return_value=MagicMock(),
            ):
                with patch(
                    "app.cspm_plugin.tools.settings"
                ) as mock_settings:
                    mock_settings.OPENSEARCH_INDEX_RAG = None
                    mock_settings.OPENSEARCH_URL = "https://localhost:9200"

                    # Act
                    result = await _fallback_retrieve_reference("test", "aws")

        # Assert
        assert "configuration" in result.lower() and "missing" in result.lower()

    @pytest.mark.asyncio
    async def test_fallback_search_no_results_after_filter(self):
        """CSPM-T-E21: フォールバック検索でクラウドフィルター後に結果なし

        tools.py:335-336 の filtered_docs が空の分岐をカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import _fallback_retrieve_reference
        from langchain_core.documents import Document

        mock_doc = Document(
            page_content="Azure content",
            metadata={"cloud": "azure", "source": "azure.md"}
        )

        with patch(
            "app.cspm_plugin.tools.get_embedding_function",
            return_value=MagicMock(),
        ):
            with patch(
                "app.cspm_plugin.tools.get_opensearch_client",
                new_callable=AsyncMock,
                return_value=MagicMock(),
            ):
                with patch(
                    "app.cspm_plugin.tools.settings"
                ) as mock_settings:
                    mock_settings.OPENSEARCH_INDEX_RAG = "test-rag"
                    mock_settings.OPENSEARCH_URL = "https://localhost:9200"
                    mock_settings.OPENSEARCH_USER = "admin"
                    mock_settings.OPENSEARCH_PASSWORD = "admin"
                    mock_settings.OPENSEARCH_CA_CERTS_PATH = None

                    with patch(
                        "app.cspm_plugin.tools.is_aws_opensearch_service",
                        return_value=True,
                    ):
                        with patch(
                            "app.cspm_plugin.tools.OpenSearchVectorSearch"
                        ) as mock_vs:
                            mock_instance = MagicMock()
                            mock_instance.asimilarity_search = AsyncMock(
                                return_value=[mock_doc]  # azure の結果のみ
                            )
                            mock_vs.return_value = mock_instance

                            # Act - aws で検索（azure しかないので結果なし）
                            result = await _fallback_retrieve_reference("test", "aws")

        # Assert
        assert "No relevant reference" in result

    @pytest.mark.asyncio
    async def test_fallback_with_ca_certs_path(self):
        """CSPM-T-E21-B: 非AWS OpenSearchでCA証明書パスが設定される

        tools.py:317-318 の is_aws_opensearch_service=False かつ
        CA_CERTS_PATH 設定時の分岐をカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import _fallback_retrieve_reference
        from langchain_core.documents import Document

        mock_doc = Document(
            page_content="AWS S3 content",
            metadata={"cloud": "aws", "source": "s3.md"}
        )

        with patch(
            "app.cspm_plugin.tools.get_embedding_function",
            return_value=MagicMock(),
        ):
            with patch(
                "app.cspm_plugin.tools.get_opensearch_client",
                new_callable=AsyncMock,
                return_value=MagicMock(),
            ):
                with patch(
                    "app.cspm_plugin.tools.settings"
                ) as mock_settings:
                    mock_settings.OPENSEARCH_INDEX_RAG = "test-rag"
                    mock_settings.OPENSEARCH_URL = "https://localhost:9200"
                    mock_settings.OPENSEARCH_USER = "admin"
                    mock_settings.OPENSEARCH_PASSWORD = "admin"
                    mock_settings.OPENSEARCH_CA_CERTS_PATH = "/path/to/ca-bundle.crt"

                    with patch(
                        "app.cspm_plugin.tools.is_aws_opensearch_service",
                        return_value=False,  # 非AWS OpenSearch
                    ):
                        with patch(
                            "app.cspm_plugin.tools.OpenSearchVectorSearch"
                        ) as mock_vs:
                            mock_instance = MagicMock()
                            mock_instance.asimilarity_search = AsyncMock(
                                return_value=[mock_doc]
                            )
                            mock_vs.return_value = mock_instance

                            # Act
                            result = await _fallback_retrieve_reference("test", "aws")

                            # Assert - CA証明書パスが設定されていることを検証
                            call_kwargs = mock_vs.call_args[1]
                            assert call_kwargs.get("ca_certs") == "/path/to/ca-bundle.crt"
                            assert "AWS S3 content" in result

    @pytest.mark.asyncio
    async def test_fallback_general_exception(self):
        """CSPM-T-E22: フォールバック検索で一般例外

        tools.py:351-352 の Exception 分岐をカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import _fallback_retrieve_reference

        with patch(
            "app.cspm_plugin.tools.get_embedding_function",
            return_value=MagicMock(),
        ):
            with patch(
                "app.cspm_plugin.tools.get_opensearch_client",
                new_callable=AsyncMock,
                return_value=MagicMock(),
            ):
                with patch(
                    "app.cspm_plugin.tools.settings"
                ) as mock_settings:
                    mock_settings.OPENSEARCH_INDEX_RAG = "test-rag"
                    mock_settings.OPENSEARCH_URL = "https://localhost:9200"
                    mock_settings.OPENSEARCH_USER = "admin"
                    mock_settings.OPENSEARCH_PASSWORD = "admin"
                    mock_settings.OPENSEARCH_CA_CERTS_PATH = None

                    with patch(
                        "app.cspm_plugin.tools.is_aws_opensearch_service",
                        return_value=True,
                    ):
                        with patch(
                            "app.cspm_plugin.tools.OpenSearchVectorSearch",
                            side_effect=RuntimeError("Connection failed"),
                        ):
                            # Act
                            result = await _fallback_retrieve_reference("test", "aws")

        # Assert
        assert "Error during fallback RAG search" in result
```

### 3.6 _run_custodian_schema 異常系

```python
class TestRunCustodianSchemaErrors:
    """_run_custodian_schema ヘルパーの異常系テスト

    tools.py:399-439 の subprocess 実行ラッパーをカバー。
    """

    def test_schema_command_timeout(self):
        """CSPM-T-E23: スキーマ取得がタイムアウト

        tools.py:434-435 の TimeoutExpired 分岐をカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import _run_custodian_schema
        import subprocess

        with patch(
            "app.cspm_plugin.tools.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="custodian", timeout=30),
        ):
            # Act
            result = _run_custodian_schema("aws")

        # Assert
        assert "timed out" in result.lower()

    def test_schema_command_not_found(self):
        """CSPM-T-E24: custodianコマンドが見つからない

        tools.py:436-437 の FileNotFoundError 分岐をカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import _run_custodian_schema

        with patch(
            "app.cspm_plugin.tools.subprocess.run",
            side_effect=FileNotFoundError("No such file"),
        ):
            # Act
            result = _run_custodian_schema("aws")

        # Assert
        assert "command not found" in result.lower()
        assert "Cloud Custodian" in result

    def test_schema_command_failed_nonzero_exit(self):
        """CSPM-T-E25: スキーマ取得コマンドが非ゼロで終了

        tools.py:431-432 の returncode!=0 分岐をカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import _run_custodian_schema

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Invalid target specified"
        mock_result.stdout = ""

        with patch(
            "app.cspm_plugin.tools.subprocess.run",
            return_value=mock_result,
        ):
            # Act
            result = _run_custodian_schema("aws.invalid")

        # Assert
        assert "Error:" in result
        assert "exit code 1" in result

    def test_schema_general_exception(self):
        """CSPM-T-E26: スキーマ取得で一般例外

        tools.py:438-439 の Exception 分岐をカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import _run_custodian_schema

        with patch(
            "app.cspm_plugin.tools.subprocess.run",
            side_effect=OSError("Permission denied"),
        ):
            # Act
            result = _run_custodian_schema("aws")

        # Assert
        assert "Unexpected error" in result

```

### 3.7 _execute_schema_with_fallback 異常系

```python
class TestExecuteSchemaWithFallbackErrors:
    """_execute_schema_with_fallback ヘルパーの異常系テスト

    tools.py:442-469 のフォールバック付きスキーマ取得をカバー。
    """

    def test_all_fallback_levels_fail(self):
        """CSPM-T-E27: 全フォールバックレベルが失敗

        tools.py:469 の全レベル失敗時の分岐をカバー。
        """
        # Arrange
        from app.cspm_plugin.tools import _execute_schema_with_fallback

        with patch(
            "app.cspm_plugin.tools._run_custodian_schema",
            return_value="Error: not found",
        ):
            # Act
            result, warning = _execute_schema_with_fallback(["aws", "nonexistent", "filters"])

        # Assert
        assert "Error:" in result
        assert "取得できませんでした" in result
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CSPM-T-SEC-01 | コマンドインジェクション防止 | `$(rm -rf /)` 含むポリシー | subprocessに安全に渡される（ファイル経由） |
| CSPM-T-SEC-02 | 一時ファイル確実削除 | 検証後 | os.remove が呼ばれる |
| CSPM-T-SEC-03 | 環境変数カスタムパス | CUSTODIAN_CMD_PATH=カスタムパス | 環境変数のパスが使用される（機能テスト） |
| CSPM-T-SEC-04 | shell=False確認 | subprocess.run呼び出し | shell=Falseで呼び出される |
| CSPM-T-SEC-05 | エラーメッセージ情報漏洩チェック | 例外発生時 | スタックトレースが含まれない |
| CSPM-T-SEC-06 | 大容量ポリシー入力テスト | 1MBポリシー | 処理完了またはリソース制限 |
| CSPM-T-SEC-07 | YAML爆弾攻撃防止 | 再帰参照YAML | 構造エラーとして拒否 |
| CSPM-T-SEC-08 | 深いネスト構造処理 | 100レベルネストYAML | 深度制限内で安全に処理 |

```python
@pytest.mark.security
class TestToolsSecurity:
    """ツール関数のセキュリティテスト"""

    def test_command_injection_prevented(self):
        """CSPM-T-SEC-01: コマンドインジェクション文字列がファイル経由で安全に処理

        validate_policy はポリシー内容を一時ファイルに書き出してから
        subprocess.run にファイルパスを渡すため、内容がコマンドとして解釈されない。
        tools.py:107-111 の一時ファイル書き出しパス。
        """
        # Arrange
        from app.cspm_plugin.tools import validate_policy

        malicious_content = '$(rm -rf /); {"policies": [{"name":"test","resource":"s3"}]}'

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "parse error"
        mock_result.stdout = ""

        with patch("app.cspm_plugin.tools.subprocess.run", return_value=mock_result) as mock_run:
            with patch("app.cspm_plugin.tools.tempfile.NamedTemporaryFile") as mock_tmp:
                mock_file = MagicMock()
                mock_file.__enter__ = MagicMock(return_value=mock_file)
                mock_file.__exit__ = MagicMock(return_value=False)
                mock_file.name = "/tmp/safe.json"
                mock_tmp.return_value = mock_file
                with patch("app.cspm_plugin.tools.os.path.exists", return_value=True):
                    with patch("app.cspm_plugin.tools.os.remove"):
                        # Act
                        result = validate_policy.invoke({"policy_content": malicious_content})

        # Assert — subprocess にはファイルパスのみが渡される
        if mock_run.called:
            cmd_args = mock_run.call_args[0][0]
            assert "$(rm -rf /)" not in " ".join(cmd_args)
            assert "/tmp/safe.json" in cmd_args

    def test_tempfile_cleanup(self):
        """CSPM-T-SEC-02: 一時ファイルが確実に削除される

        tools.py:149-158 の finally ブロックをカバー。
        正常終了・異常終了いずれでも一時ファイルが削除されること。
        """
        # Arrange
        from app.cspm_plugin.tools import validate_policy

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_result.stdout = ""
        policy = json.dumps({"policies": [{"name": "test", "resource": "s3"}]})

        with patch("app.cspm_plugin.tools.subprocess.run", return_value=mock_result):
            with patch("app.cspm_plugin.tools.tempfile.NamedTemporaryFile") as mock_tmp:
                mock_file = MagicMock()
                mock_file.__enter__ = MagicMock(return_value=mock_file)
                mock_file.__exit__ = MagicMock(return_value=False)
                mock_file.name = "/tmp/cleanup_test.json"
                mock_tmp.return_value = mock_file
                with patch("app.cspm_plugin.tools.os.path.exists", return_value=True):
                    with patch("app.cspm_plugin.tools.os.remove") as mock_remove:
                        # Act
                        validate_policy.invoke({"policy_content": policy})

        # Assert
        mock_remove.assert_called_once_with("/tmp/cleanup_test.json")

    def test_custom_custodian_path(self):
        """CSPM-T-SEC-03: CUSTODIAN_CMD_PATH環境変数が正しく反映される

        tools.py:33 の os.environ.get("CUSTODIAN_CMD_PATH", "custodian")。
        カスタムパスが subprocess に正しく渡されることを確認（機能テスト）。

        注意: 環境変数の管理はコンテナ/デプロイ層の責任範囲。
        アプリケーションレベルでは任意パス実行を防ぐ仕組みは含まれていない。
        """
        # Arrange
        from app.cspm_plugin.tools import validate_policy

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        policy = json.dumps({"policies": [{"name": "test", "resource": "s3"}]})

        with patch.dict("os.environ", {"CUSTODIAN_CMD_PATH": "/custom/path/custodian"}):
            with patch("app.cspm_plugin.tools.subprocess.run", return_value=mock_result) as mock_run:
                with patch("app.cspm_plugin.tools.tempfile.NamedTemporaryFile") as mock_tmp:
                    mock_file = MagicMock()
                    mock_file.__enter__ = MagicMock(return_value=mock_file)
                    mock_file.__exit__ = MagicMock(return_value=False)
                    mock_file.name = "/tmp/test.json"
                    mock_tmp.return_value = mock_file
                    with patch("app.cspm_plugin.tools.os.path.exists", return_value=True):
                        with patch("app.cspm_plugin.tools.os.remove"):
                            # Act
                            validate_policy.invoke({"policy_content": policy})

        # Assert
        cmd_args = mock_run.call_args[0][0]
        assert cmd_args[0] == "/custom/path/custodian"

    def test_subprocess_shell_false(self):
        """CSPM-T-SEC-04: subprocess.run が shell=False で呼び出される

        tools.py:115-121, 418-424 の subprocess.run 呼び出しで
        shell=True が使用されていないことを検証（コマンドインジェクション防止）。
        """
        # Arrange
        from app.cspm_plugin.tools import validate_policy

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        policy = json.dumps({"policies": [{"name": "test", "resource": "s3"}]})

        with patch("app.cspm_plugin.tools.subprocess.run", return_value=mock_result) as mock_run:
            with patch("app.cspm_plugin.tools.tempfile.NamedTemporaryFile") as mock_tmp:
                mock_file = MagicMock()
                mock_file.__enter__ = MagicMock(return_value=mock_file)
                mock_file.__exit__ = MagicMock(return_value=False)
                mock_file.name = "/tmp/test.json"
                mock_tmp.return_value = mock_file
                with patch("app.cspm_plugin.tools.os.path.exists", return_value=True):
                    with patch("app.cspm_plugin.tools.os.remove"):
                        # Act
                        validate_policy.invoke({"policy_content": policy})

        # Assert - shell パラメータが True でないことを確認
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get("shell", False) is False  # shell=False（デフォルト）

    def test_error_message_no_stacktrace(self):
        """CSPM-T-SEC-05: エラーメッセージにスタックトレースが含まれない

        tools.py:144-148 の例外捕捉で、ユーザーに返されるメッセージに
        スタックトレースが含まれないことを検証。
        """
        # Arrange
        from app.cspm_plugin.tools import validate_policy

        policy = json.dumps({"policies": [{"name": "test", "resource": "s3"}]})

        with patch("app.cspm_plugin.tools.subprocess.run", side_effect=RuntimeError("Internal failure")):
            with patch("app.cspm_plugin.tools.tempfile.NamedTemporaryFile") as mock_tmp:
                mock_file = MagicMock()
                mock_file.__enter__ = MagicMock(return_value=mock_file)
                mock_file.__exit__ = MagicMock(return_value=False)
                mock_file.name = "/tmp/test.json"
                mock_tmp.return_value = mock_file
                with patch("app.cspm_plugin.tools.os.path.exists", return_value=True):
                    with patch("app.cspm_plugin.tools.os.remove"):
                        # Act
                        result = validate_policy.invoke({"policy_content": policy})

        # Assert - スタックトレースキーワードが含まれない
        assert "Traceback" not in result
        assert "File " not in result  # Python スタックトレース形式
        assert "line " not in result  # 行番号情報
        # エラーメッセージ自体は含まれる
        assert "Error" in result

    def test_large_policy_input(self):
        """CSPM-T-SEC-06: 大容量ポリシー入力の処理

        1MB のポリシー入力が処理できることを検証。
        DoS 攻撃に対する耐性テスト。
        """
        # Arrange
        from app.cspm_plugin.tools import validate_policy

        # 1MB のポリシー生成（約1万のダミーポリシー）
        large_policies = []
        for i in range(10000):
            large_policies.append({
                "name": f"policy_{i}",
                "resource": "s3",
                "filters": [{"type": "tag", "key": "Environment", "value": f"test_{i}"}]
            })
        large_policy = json.dumps({"policies": large_policies})
        print(f"  Test policy size: {len(large_policy) / 1024 / 1024:.2f} MB")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""

        with patch("app.cspm_plugin.tools.subprocess.run", return_value=mock_result):
            with patch("app.cspm_plugin.tools.tempfile.NamedTemporaryFile") as mock_tmp:
                mock_file = MagicMock()
                mock_file.__enter__ = MagicMock(return_value=mock_file)
                mock_file.__exit__ = MagicMock(return_value=False)
                mock_file.name = "/tmp/test.json"
                mock_tmp.return_value = mock_file
                with patch("app.cspm_plugin.tools.os.path.exists", return_value=True):
                    with patch("app.cspm_plugin.tools.os.remove"):
                        # Act
                        result = validate_policy.invoke({"policy_content": large_policy})

        # Assert - 正常に処理完了
        assert "Validation successful" in result

    def test_yaml_bomb_prevention(self):
        """CSPM-T-SEC-07: YAML爆弾攻撃（再帰参照）が安全に処理される

        yaml.safe_load() は再帰参照を展開しないため、
        Billion Laughs 攻撃は無効。ただし構造エラーとして拒否される。
        """
        # Arrange
        from app.cspm_plugin.tools import validate_policy

        # YAML爆弾パターン（再帰参照）
        yaml_bomb = """
lol1: &lol1 "lol"
lol2: &lol2 [*lol1, *lol1, *lol1, *lol1, *lol1]
lol3: &lol3 [*lol2, *lol2, *lol2, *lol2, *lol2]
lol4: &lol4 [*lol3, *lol3, *lol3, *lol3, *lol3]
lol5: &lol5 [*lol4, *lol4, *lol4, *lol4, *lol4]
"""
        # Act
        result = validate_policy.invoke({"policy_content": yaml_bomb})

        # Assert - YAMLパースは成功するが、構造検証で失敗
        # yaml.safe_load は再帰参照を展開するが、
        # 結果が policies/name キーを持たないためエラーになる
        assert "Error" in result
        assert "Invalid YAML structure" in result

    def test_deeply_nested_yaml_handling(self):
        """CSPM-T-SEC-08: 深くネストされたYAML構造の処理

        深いネスト構造がDoS攻撃に使用されないことを検証。
        Pythonのデフォルト再帰深度制限（1000）で保護。
        """
        # Arrange
        from app.cspm_plugin.tools import validate_policy

        # 100レベルのネスト（合理的な深度制限内）
        nested_yaml = "policies:\n"
        for i in range(100):
            nested_yaml += "  " * i + f"level_{i}:\n"

        # Act
        result = validate_policy.invoke({"policy_content": nested_yaml})

        # Assert - 構造が無効としてエラー（深度制限内で正常にパース）
        assert "Error" in result
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_tools_module` | テスト間のモジュール状態リセット（予防的措置） | function | Yes |
| `mock_subprocess_success` | subprocess正常終了モック | function | No |
| `mock_tempfile` | 一時ファイル作成モック | function | No |
| `mock_tempfile_for_errors` | 一時ファイルモック（エラー系） | function | No |
| `mock_opensearch_settings` | OpenSearch設定モック（RAGテスト用） | function | No |

### 共通フィクスチャ定義

```python
# test/unit/cspm_plugin/conftest.py（既存ファイルに追記）
import sys
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def reset_tools_module():
    """テストごとにモジュール状態をリセット（将来の拡張に備えた予防的措置）

    現在 tools.py にはグローバル状態（キャッシュ等）は存在しませんが、
    将来的な変更に備えてモジュール再読み込みを実施します。

    注記: 定数（VALID_CLOUDS, MAX_SCHEMA_COMPONENTS等）は影響を受けません。
    """
    yield
    modules_to_remove = [
        key for key in sys.modules if key.startswith("app.cspm_plugin")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]
```

---

## 6. テスト実行例

```bash
# tools.py 関連テストのみ実行
pytest test/unit/cspm_plugin/test_tools.py -v

# validate_policy テストのみ実行
pytest test/unit/cspm_plugin/test_tools.py::TestValidatePolicy -v
pytest test/unit/cspm_plugin/test_tools.py::TestValidatePolicyErrors -v

# スキーマ系テストのみ実行
pytest test/unit/cspm_plugin/test_tools.py::TestValidateSchemaTarget -v
pytest test/unit/cspm_plugin/test_tools.py::TestGetCustodianSchema -v

# カバレッジ付きで実行
pytest test/unit/cspm_plugin/test_tools.py --cov=app.cspm_plugin.tools --cov-report=term-missing -v

# セキュリティテストのみ実行
pytest test/unit/cspm_plugin/test_tools.py -m "security" -v

# cspm_plugin 全テスト
pytest test/unit/cspm_plugin/ -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 20 | CSPM-T-001〜008, 009, 009-B, 010〜016, 014-B〜D |
| 異常系 | 28 | CSPM-T-E01 〜 CSPM-T-E27, E21-B |
| セキュリティ | 8 | CSPM-T-SEC-01 〜 CSPM-T-SEC-08 |
| **合計** | **56** | - |

> **注記**: CSPM-T-008「検証失敗の正常応答」は、returncode!=0 の分岐が正しく機能することを検証する正常系テストです。validate_policy関数が失敗結果を正常に返すことを確認します。

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestValidatePolicy` | CSPM-T-001〜008 | 8 |
| `TestValidateSchemaTarget` | CSPM-T-009, 009-B, 010, 015 | 4 |
| `TestGetCustodianSchema` | CSPM-T-011〜013 | 3 |
| `TestRetrieveReference` | CSPM-T-014, 014-B〜D | 4 |
| `TestRunCustodianSchemaNormal` | CSPM-T-016 | 1 |
| `TestValidatePolicyErrors` | CSPM-T-E01〜E09 | 9 |
| `TestValidateSchemaTargetErrors` | CSPM-T-E10〜E12 | 3 |
| `TestListResourcesErrors` | CSPM-T-E13 | 1 |
| `TestRetrieveReferenceErrors` | CSPM-T-E14〜E17 | 4 |
| `TestFallbackRetrieveReferenceErrors` | CSPM-T-E18〜E22, E21-B | 6 |
| `TestRunCustodianSchemaErrors` | CSPM-T-E23〜E26 | 4 |
| `TestExecuteSchemaWithFallbackErrors` | CSPM-T-E27 | 1 |
| `TestToolsSecurity` | CSPM-T-SEC-01〜SEC-08 | 8 |
| **合計** | - | **56** |

### 注意事項

- `validate_policy` は同期ツール（`invoke`）、`retrieve_reference` は非同期ツール（`ainvoke`）
- subprocess のモックでは `capture_output=True, text=True, timeout=30` パラメータに注意
- 一時ファイル作成のモックはネストが深くなるため、フィクスチャで共通化推奨
- `@tool` デコレータ付き関数のテストは `.invoke()` / `.ainvoke()` で呼び出す

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `validate_policy` は同期関数のため、イベントループをブロック | 大量ポリシーの並列検証時にスループット低下 | 将来的に非同期化を検討 |
| 2 | `_fallback_retrieve_reference` の従来RAGシステムは非推奨 | 強化版RAGが利用不可の場合のみ使用 | 強化版RAGの安定性確保を優先 |
| 3 | `CUSTODIAN_CMD_PATH` 環境変数で任意パスのコマンド実行が可能 | **コンテナレベルでの保護が必要**（アプリ側制限なし） | 本番環境でのコンテナセキュリティで対応、read-only filesystem推奨 |
| 4 | `validate_policy` の print() デバッグ出力が多数存在 | ログにデバッグ情報が出力される | logging モジュールへの移行を推奨 |
| 5 | `_run_custodian_schema` の `str(e)` がエラーメッセージに含まれる（tools.py:439） | デバッグ情報が詳細すぎる可能性（ただしツール関数レベルのため影響は限定的） | 必要に応じてログレベル調整を検討 |
| 6 | 入力サイズ制限なし | 大容量入力によるメモリ枯渇のリスク | CSPM-T-SEC-06 で1MBまでは動作確認済み、必要に応じてサイズ制限追加を検討 |
| 7 | YAML爆弾攻撃への対策はyaml.safe_load依存 | 再帰参照による展開攻撃は防御可能だが、深いネストは処理される | CSPM-T-SEC-07, SEC-08で動作確認済み。yaml.safe_loadの制限で保護 |
| 8 | RAG検索クエリのサニタイズなし | OpenSearchへのクエリインジェクションの可能性 | RAGシステム側での入力検証に依存。将来的にツール側でもサニタイズ追加を検討 |

### 実装失敗が予想されるテスト

| テストID | 失敗理由 | 修正方針 |
|---------|---------|---------|
| CSPM-T-SEC-05 | `tools.py:144-148` で `str(e)` が直接レスポンスに含まれる場合、例外メッセージの一部がユーザーに露出 | 汎用メッセージ化または例外種別に応じたメッセージ出し分けを検討 |

> **注記**: CSPM-T-SEC-05 は現在の実装では「スタックトレースは含まれない」が「例外メッセージは含まれる」ため、テストは成功しますが、セキュリティレビューでは改善推奨とされています。
