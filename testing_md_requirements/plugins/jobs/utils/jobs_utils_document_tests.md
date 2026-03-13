# jobs/utils ドキュメント生成・抽出 テストケース

## 1. 概要

`app/jobs/utils/` のドキュメント生成モジュール（`document_creators.py`）とドキュメント抽出モジュール（`document_extractors.py`）のテスト仕様書。OpenSearchへ保存するドキュメント構造の生成と、Custodian出力ディレクトリからの違反ドキュメント抽出を担う。

### 1.1 主要機能

| 関数 | ファイル | 説明 |
|------|---------|------|
| `_create_opensearch_document()` | document_creators.py | 単一リソースからOpenSearchドキュメントを作成 |
| `_create_raw_opensearch_document()` | document_creators.py | metadata.json/resource.jsonの生データを使用してドキュメント作成 |
| `_create_policy_grouped_document()` | document_creators.py | ポリシーグループ化されたドキュメントを作成 |
| `_extract_violation_documents_from_output()` | document_extractors.py | Custodian出力からポリシーグループドキュメントを抽出 |
| `_extract_v2_documents_from_output()` | document_extractors.py | Custodian出力から階層構造v2ドキュメントを抽出 |
| `_analyze_logs_for_statistics()` | document_extractors.py | Custodianログからポリシー統計情報を取得 |

### 1.2 カバレッジ目標: 90%

> **注記**: document_creators は純粋な変換関数でモック不要。document_extractors はファイルシステム・外部モジュール依存が多いが、全て標準的なモックで対応可能。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象1 | `app/jobs/utils/document_creators.py` (212行) |
| テスト対象2 | `app/jobs/utils/document_extractors.py` (222行) |
| テストコード | `test/unit/jobs/utils/test_document.py` |
| conftest | `test/unit/jobs/utils/conftest.py` |

### 1.4 依存関係

```
document_creators.py
├── field_normalizers._normalize_numeric_fields
├── field_normalizers._sanitize_custodian_metadata
└── helper_functions._extract_resource_id

document_extractors.py
├── document_creators._create_policy_grouped_document
├── helper_functions._extract_resource_id, _load_metadata_from_file, _determine_resource_type
├── field_normalizers._normalize_resource_fields
├── v2_format_converter.convert_custodian_output_to_v2_hierarchical
└── app.jobs.tasks.new_custodian_scan.log_analyzer.PolicyAnalysisOrchestrator（関数内import）
```

### 1.5 主要分岐マップ

| 関数 | 分岐数 | 主要条件 |
|------|--------|---------|
| `_create_opensearch_document` | 15 | L46 metadata有無, L48 config.account_id, L52 config.region, L56 policy, L60-63 aws AZ/Region fallback, L66-68 azure location, L72-84 resource_type推定 |
| `_create_raw_opensearch_document` | 4 | L135 metadata&config, L141 metadata有無, L142 resource有無 |
| `_create_policy_grouped_document` | 3 | L190 metadata&config, L196 metadata有無 |
| `_extract_violation_documents_from_output` | 6 | L60 list&非空, L62 新規policy, L71 resource有無, L80 ファイル例外, L98 外部例外 |
| `_extract_v2_documents_from_output` | 4 | L134 statistics有無, L149 scan_metadata未設定, L153 doc_type=error, L160 例外 |
| `_analyze_logs_for_statistics` | 5 | L190 results空, L198 policy_name無, L207 既存エントリ集約, L211 新規エントリ, L220 例外 |

### 1.6 実装上の注意点

| # | 注意点 | 影響 |
|---|--------|------|
| 1 | `_create_raw_opensearch_document` は関数内で `_normalize_resource_fields` をimport（L126） | 関数内importは呼び出しごとにソースモジュールから取得するため、パッチ先は**元モジュール** `app.jobs.utils.field_normalizers._normalize_resource_fields`（インポート先モジュールにはモジュール属性として存在しない） |
| 2 | `_analyze_logs_for_statistics` は関数内で `PolicyAnalysisOrchestrator` をimport（L184） | 同上。パッチ先は元モジュール `app.jobs.tasks.new_custodian_scan.log_analyzer.PolicyAnalysisOrchestrator` |
| 3 | `_extract_violation_documents_from_output` は `datetime.now(timezone.utc)` を呼ぶ（L36） | タイムスタンプ検証にはdatetimeモックが必要 |

> **関数内import vs モジュールレベルimport のモック戦略**:
> - **関数内import** (`from X import Y` が関数本体内): 呼び出しごとにソースモジュールから取得 → **元モジュール `X.Y` をパッチ**
> - **モジュールレベルimport** (`from X import Y` がファイル先頭): import時に1回だけバインド → **インポート先モジュール `this_module.Y` をパッチ**

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| DC-001 | _create_opensearch_document 基本動作 | metadata有りEC2リソース | 全フィールド設定済みドキュメント |
| DC-002 | _create_opensearch_document metadata無し | `metadata=None` | デフォルト値で構成 |
| DC-003 | _create_opensearch_document config.account_id上書き | metadata.config.account_id有り | 引数account_idより優先 |
| DC-004 | _create_opensearch_document config.region設定 | metadata.config.region有り | regionがconfigから取得 |
| DC-005 | _create_opensearch_document policy情報抽出 | metadata.policy有り | actions/filters/description設定 |
| DC-006 | _create_opensearch_document AWSリージョンAZフォールバック | Placement.AvailabilityZone有り | AZからリージョン推定 |
| DC-007 | _create_opensearch_document AWSリージョンRegionフィールド | resource.Region有り | Regionフィールド使用 |
| DC-008 | _create_opensearch_document Azureリージョンフォールバック | resource.location有り | locationフィールド使用 |
| DC-009 | _create_opensearch_document resource_typeがpolicy_infoから取得 | policy.resource="ec2" | resource_type推定をスキップ |
| DC-010 | _create_opensearch_document EC2推定 | `InstanceId`有り | resource_type="ec2" |
| DC-011 | _create_opensearch_document SG推定 | `GroupId`有り | resource_type="security-group" |
| DC-012 | _create_opensearch_document EBS推定 | `VolumeId`有り | resource_type="ebs" |
| DC-013 | _create_opensearch_document S3推定 | `BucketName`有り | resource_type="s3" |
| DC-014 | _create_opensearch_document Azure type推定 | azure + `type`有り | resource_type=typeの小文字 |
| DC-015 | _create_opensearch_document AZ空文字列 | AZ="" | region="unknown" |
| DC-016 | _create_raw_opensearch_document 正常 | metadata/resource有り | 全フィールド設定 |
| DC-017 | _create_raw_opensearch_document metadata無し | `metadata=None` | デフォルト値 |
| DC-018 | _create_raw_opensearch_document config無し | metadata={"policy":...} | account_id/region="unknown" |
| DC-019 | _create_raw_opensearch_document resource空 | `resource={}` | custodian_resource={} |
| DC-020 | _create_policy_grouped_document 正常 | metadata/resources有り | 全フィールド設定 |
| DC-021 | _create_policy_grouped_document metadata無し | group_data={} | デフォルト値 |
| DC-022 | _create_policy_grouped_document config無し | metadata={"policy":...} | region="unknown" |
| DC-023 | _create_policy_grouped_document resources空 | resources=[] | resource_count=0 |
| DC-024 | _extract_violation_documents 単一ポリシー | 1ポリシー3リソース | 1ドキュメント |
| DC-025 | _extract_violation_documents 複数ポリシー | 2ポリシー | 2ドキュメント |
| DC-026 | _extract_violation_documents resources空リスト | `[]` | スキップ |
| DC-026a | _extract_violation_documents 空dictリソース | `[{}, {"id":"r1"}]` | L71 else分岐（`{}` はfalsy） |
| DC-027 | _extract_violation_documents ファイル無し | glob結果空 | 空リスト |
| DC-028 | _extract_v2_documents 正常 | 階層ドキュメント | 1件のリスト |
| DC-029 | _extract_v2_documents statistics空 | 統計無し | warning出力、処理続行 |
| DC-030 | _extract_v2_documents scan_metadata既存 | scan_metadata設定済み | 上書きしない |
| DC-031 | _extract_v2_documents doc_type=error | doc_type="xxx_error" | 空リスト |
| DC-032 | _analyze_logs 単一ポリシー | 1ポリシー結果 | 統計辞書 |
| DC-033 | _analyze_logs 複数リージョン集約 | 同名ポリシー2件 | 数値が加算 |
| DC-034 | _analyze_logs results空 | policy_results=[] | 空辞書 |
| DC-035 | _analyze_logs policy_name無し | policy_name欠落 | スキップ |

### 2.1 _create_opensearch_document テスト

```python
# test/unit/jobs/utils/test_document.py
import pytest
import json
from unittest.mock import patch, MagicMock, mock_open


class TestCreateOpensearchDocument:
    """_create_opensearch_document のテスト"""

    def test_basic_with_full_metadata(self):
        """DC-001: metadata有りで全フィールドが正しく設定される

        document_creators.py:46-57 のmetadata分岐をカバー
        """
        # Arrange
        from app.jobs.utils.document_creators import _create_opensearch_document
        resource = {"InstanceId": "i-123"}
        metadata = {
            "config": {"account_id": "111222333444", "region": "us-east-1"},
            "policy": {
                "name": "test",
                "resource": "ec2",
                "actions": [{"type": "stop"}],
                "filters": [{"type": "value"}],
                "description": "test policy"
            }
        }

        # Act
        result = _create_opensearch_document(
            resource, "test-policy", "job-1", "aws", "default-account",
            "2024-01-01T00:00:00Z", {}, 0, metadata
        )

        # Assert
        assert result["account_id"] == "111222333444"
        assert result["region"] == "us-east-1"
        assert result["policy"]["resource"] == "ec2"
        assert result["policy"]["actions"] == [{"type": "stop"}]
        assert result["scan_id"] == "job-1"

    def test_metadata_none(self):
        """DC-002: metadata=Noneの場合はデフォルト値で構成

        document_creators.py:46 のelse分岐をカバー
        """
        # Arrange
        from app.jobs.utils.document_creators import _create_opensearch_document
        resource = {"InstanceId": "i-123"}

        # Act
        result = _create_opensearch_document(
            resource, "policy-1", "job-1", "aws", "acct-1",
            "2024-01-01T00:00:00Z", {}, 0, None
        )

        # Assert
        assert result["account_id"] == "acct-1"
        assert result["policy"]["resource"] == "ec2"
        assert result["policy"]["actions"] == []

    def test_config_account_id_override(self):
        """DC-003: metadata.config.account_idが引数account_idを上書き

        document_creators.py:48-49 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.document_creators import _create_opensearch_document
        metadata = {"config": {"account_id": "from-metadata"}}

        # Act
        result = _create_opensearch_document(
            {}, "p", "j", "aws", "from-arg", "ts", {}, 0, metadata
        )

        # Assert
        assert result["account_id"] == "from-metadata"

    def test_config_region(self):
        """DC-004: metadata.config.regionからリージョン取得

        document_creators.py:52-53 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.document_creators import _create_opensearch_document
        metadata = {"config": {"region": "ap-northeast-1"}}

        # Act
        result = _create_opensearch_document(
            {}, "p", "j", "aws", "a", "ts", {}, 0, metadata
        )

        # Assert
        assert result["region"] == "ap-northeast-1"

    def test_policy_info_extraction(self):
        """DC-005: metadata.policyからpolicy情報を抽出

        document_creators.py:56-57 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.document_creators import _create_opensearch_document
        metadata = {
            "policy": {
                "resource": "s3",
                "description": "S3 bucket check",
                "filters": [{"type": "global-grants"}],
                "actions": [{"type": "notify"}]
            }
        }

        # Act
        result = _create_opensearch_document(
            {}, "p", "j", "aws", "a", "ts", {}, 0, metadata
        )

        # Assert
        assert result["policy"]["description"] == "S3 bucket check"
        assert result["policy"]["filters"] == [{"type": "global-grants"}]
        assert result["policy"]["resource"] == "s3"

    def test_aws_region_fallback_from_az(self):
        """DC-006: AWSリソースのAvailabilityZoneからリージョン推定

        document_creators.py:60-63 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.document_creators import _create_opensearch_document
        resource = {"Placement": {"AvailabilityZone": "us-west-2a"}}

        # Act
        result = _create_opensearch_document(
            resource, "p", "j", "aws", "a", "ts", {}, 0, None
        )

        # Assert
        assert result["region"] == "us-west-2"

    def test_aws_region_fallback_from_region_field(self):
        """DC-007: AWSリソースのRegionフィールドからリージョン取得

        document_creators.py:64-65 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.document_creators import _create_opensearch_document
        resource = {"Region": "eu-west-1"}

        # Act
        result = _create_opensearch_document(
            resource, "p", "j", "aws", "a", "ts", {}, 0, None
        )

        # Assert
        assert result["region"] == "eu-west-1"

    def test_azure_region_fallback_from_location(self):
        """DC-008: Azureリソースのlocationからリージョン取得

        document_creators.py:66-68 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.document_creators import _create_opensearch_document
        resource = {"location": "japaneast"}

        # Act
        result = _create_opensearch_document(
            resource, "p", "j", "azure", "a", "ts", {}, 0, None
        )

        # Assert
        assert result["region"] == "japaneast"

    def test_resource_type_from_policy_info(self):
        """DC-009: policy_info.resourceが設定済みなら推定をスキップ

        document_creators.py:71-72 の条件分岐をカバー。
        resource_type != "unknown" かつ truthyなら推定ブロックに入らない。
        """
        # Arrange
        from app.jobs.utils.document_creators import _create_opensearch_document
        metadata = {"policy": {"resource": "lambda"}}

        # Act
        result = _create_opensearch_document(
            {}, "p", "j", "aws", "a", "ts", {}, 0, metadata
        )

        # Assert
        assert result["policy"]["resource"] == "lambda"

    def test_infer_ec2(self):
        """DC-010: InstanceIdからEC2を推定

        document_creators.py:74-75 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.document_creators import _create_opensearch_document

        # Act
        result = _create_opensearch_document(
            {"InstanceId": "i-1"}, "p", "j", "aws", "a", "ts", {}, 0, None
        )

        # Assert
        assert result["policy"]["resource"] == "ec2"

    def test_infer_security_group(self):
        """DC-011: GroupIdからsecurity-groupを推定

        document_creators.py:76-77 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.document_creators import _create_opensearch_document

        # Act
        result = _create_opensearch_document(
            {"GroupId": "sg-1"}, "p", "j", "aws", "a", "ts", {}, 0, None
        )

        # Assert
        assert result["policy"]["resource"] == "security-group"

    def test_infer_ebs(self):
        """DC-012: VolumeIdからebsを推定

        document_creators.py:78-79 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.document_creators import _create_opensearch_document

        # Act
        result = _create_opensearch_document(
            {"VolumeId": "vol-1"}, "p", "j", "aws", "a", "ts", {}, 0, None
        )

        # Assert
        assert result["policy"]["resource"] == "ebs"

    def test_infer_s3(self):
        """DC-013: BucketNameからs3を推定

        document_creators.py:80-81 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.document_creators import _create_opensearch_document

        # Act
        result = _create_opensearch_document(
            {"BucketName": "b"}, "p", "j", "aws", "a", "ts", {}, 0, None
        )

        # Assert
        assert result["policy"]["resource"] == "s3"

    def test_infer_azure_type(self):
        """DC-014: Azureリソースのtypeフィールドから推定

        document_creators.py:82-84 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.document_creators import _create_opensearch_document

        # Act
        result = _create_opensearch_document(
            {"type": "Microsoft.Compute/virtualMachines"}, "p", "j",
            "azure", "a", "ts", {}, 0, None
        )

        # Assert
        assert result["policy"]["resource"] == "microsoft.compute/virtualmachines"

    def test_empty_availability_zone(self):
        """DC-015: AvailabilityZoneが空文字列の場合はregion="unknown"

        document_creators.py:63 の三項演算子 `az[:-1] if az else "unknown"` をカバー
        """
        # Arrange
        from app.jobs.utils.document_creators import _create_opensearch_document
        resource = {"Placement": {"AvailabilityZone": ""}}

        # Act
        result = _create_opensearch_document(
            resource, "p", "j", "aws", "a", "ts", {}, 0, None
        )

        # Assert
        assert result["region"] == "unknown"
```

### 2.2 _create_raw_opensearch_document テスト

```python
class TestCreateRawOpensearchDocument:
    """_create_raw_opensearch_document のテスト"""

    def test_normal_with_metadata(self):
        """DC-016: metadata/resource有りで全フィールド設定

        document_creators.py:135-138 のmetadata&config分岐をカバー。
        _normalize_resource_fields は関数内import（L126）のため元モジュールをパッチ。
        """
        # Arrange
        from app.jobs.utils.document_creators import _create_raw_opensearch_document
        resource = {"InstanceId": "i-123", "State": {"Name": "running"}}
        metadata = {
            "config": {"account_id": "111", "region": "us-east-1"},
            "policy": {"name": "test", "filters": []}
        }

        # Act
        with patch(
            "app.jobs.utils.field_normalizers._normalize_resource_fields",
            side_effect=lambda r: r
        ):
            result = _create_raw_opensearch_document(
                resource, "policy-1", "job-1", metadata, 0, "2024-01-01T00:00:00Z"
            )

        # Assert
        assert result["resource_id"] == "i-123"
        assert result["account_id"] == "111"
        assert result["region"] == "us-east-1"
        assert result["scan_id"] == "job-1"
        assert "custodian_metadata" in result
        assert "custodian_resource" in result

    def test_metadata_none(self):
        """DC-017: metadata=Noneの場合はデフォルト値

        document_creators.py:135 のelse分岐 + L141 の三項演算子 `else {}` をカバー
        """
        # Arrange
        from app.jobs.utils.document_creators import _create_raw_opensearch_document
        resource = {"id": "res-1"}

        # Act
        result = _create_raw_opensearch_document(
            resource, "p", "j", None, 0, "ts"
        )

        # Assert
        assert result["account_id"] == "unknown"
        assert result["region"] == "unknown"
        assert result["custodian_metadata"] == {}

    def test_metadata_without_config(self):
        """DC-018: metadataにconfigキーが無い場合

        document_creators.py:135 の `"config" in metadata` が False になる分岐をカバー
        """
        # Arrange
        from app.jobs.utils.document_creators import _create_raw_opensearch_document
        metadata = {"policy": {"name": "test"}}

        # Act
        result = _create_raw_opensearch_document(
            {"id": "r"}, "p", "j", metadata, 0, "ts"
        )

        # Assert
        assert result["account_id"] == "unknown"
        assert result["region"] == "unknown"

    def test_resource_empty(self):
        """DC-019: resourceが空dictの場合

        document_creators.py:142 の三項演算子で `resource` がfalsyの分岐をカバー。
        空dictはPythonでfalsyなので `else {}` 分岐に入り、`_normalize_resource_fields` は呼ばれない。
        """
        # Arrange
        from app.jobs.utils.document_creators import _create_raw_opensearch_document

        # Act
        result = _create_raw_opensearch_document(
            {}, "p", "j", None, 0, "ts"
        )

        # Assert
        assert result["resource_id"] == "resource_0"
        assert result["custodian_resource"] == {}
```

### 2.3 _create_policy_grouped_document テスト

```python
class TestCreatePolicyGroupedDocument:
    """_create_policy_grouped_document のテスト"""

    def test_normal(self):
        """DC-020: metadata/resources有りで全フィールド設定

        document_creators.py:190-193 のmetadata&config分岐をカバー
        """
        # Arrange
        from app.jobs.utils.document_creators import _create_policy_grouped_document
        group_data = {
            "metadata": {
                "config": {"account_id": "111", "region": "us-east-1"},
                "policy": {"name": "test"}
            },
            "resources": [{"id": "r1"}, {"id": "r2"}]
        }

        # Act
        result = _create_policy_grouped_document(
            "test-policy", group_data, "job-1", "aws", "default-acct", {}, "ts"
        )

        # Assert
        assert result["account_id"] == "111"
        assert result["region"] == "us-east-1"
        assert result["resource_count"] == 2
        assert result["doc_type"] == "policy_group"

    def test_metadata_none(self):
        """DC-021: group_dataにmetadataが無い場合

        document_creators.py:183 の `get("metadata", {})` + L190 のelse分岐をカバー
        """
        # Arrange
        from app.jobs.utils.document_creators import _create_policy_grouped_document

        # Act
        result = _create_policy_grouped_document(
            "p", {}, "j", "aws", "acct-1", {}, "ts"
        )

        # Assert
        assert result["account_id"] == "acct-1"
        assert result["region"] == "unknown"
        assert result["resource_count"] == 0

    def test_metadata_without_config(self):
        """DC-022: metadataにconfigが無い場合

        document_creators.py:190 の `"config" in metadata` が False になる分岐をカバー
        """
        # Arrange
        from app.jobs.utils.document_creators import _create_policy_grouped_document
        group_data = {"metadata": {"policy": {"name": "x"}}, "resources": []}

        # Act
        result = _create_policy_grouped_document(
            "p", group_data, "j", "aws", "acct-1", {}, "ts"
        )

        # Assert
        assert result["account_id"] == "acct-1"
        assert result["region"] == "unknown"

    def test_empty_resources(self):
        """DC-023: resourcesが空リストの場合

        document_creators.py:208 の `len(resources)` が0になるケース
        """
        # Arrange
        from app.jobs.utils.document_creators import _create_policy_grouped_document
        group_data = {"metadata": {}, "resources": []}

        # Act
        result = _create_policy_grouped_document(
            "p", group_data, "j", "aws", "a", {}, "ts"
        )

        # Assert
        assert result["resource_count"] == 0
        assert result["resources"] == []
```

### 2.4 _extract_violation_documents_from_output テスト

```python
class TestExtractViolationDocuments:
    """_extract_violation_documents_from_output のテスト"""

    @pytest.fixture
    def mock_deps(self):
        """共通モック群"""
        with patch("app.jobs.utils.document_extractors.TaskLogger") as mock_logger_cls, \
             patch("app.jobs.utils.document_extractors.glob.glob") as mock_glob, \
             patch("app.jobs.utils.document_extractors._load_metadata_from_file") as mock_load, \
             patch("app.jobs.utils.document_extractors._extract_resource_id") as mock_rid, \
             patch("app.jobs.utils.document_extractors._normalize_resource_fields") as mock_norm, \
             patch("app.jobs.utils.document_extractors._create_policy_grouped_document") as mock_create:
            mock_logger = MagicMock()
            mock_logger_cls.return_value = mock_logger
            mock_rid.side_effect = lambda r, i: f"res-{i}"
            mock_norm.side_effect = lambda r: r if r else {}
            yield {
                "logger": mock_logger,
                "glob": mock_glob,
                "load_metadata": mock_load,
                "extract_id": mock_rid,
                "normalize": mock_norm,
                "create_doc": mock_create,
            }

    def test_single_policy(self, mock_deps):
        """DC-024: 1ポリシー3リソースで1ドキュメント生成

        document_extractors.py:60-76 のリソース処理ループをカバー
        """
        # Arrange
        from app.jobs.utils.document_extractors import _extract_violation_documents_from_output
        mock_deps["glob"].return_value = ["/out/policy1/resources.json"]
        mock_deps["load_metadata"].return_value = {"policy": {"name": "p1"}}
        mock_deps["create_doc"].return_value = {"doc": "result"}

        resources = [{"id": "r1"}, {"id": "r2"}, {"id": "r3"}]

        # Act
        with patch("builtins.open", mock_open()), \
             patch("app.jobs.utils.document_extractors.json.load", return_value=resources):
            result = _extract_violation_documents_from_output(
                "/out", "job-1", "aws", "acct-1", {}
            )

        # Assert
        assert len(result) == 1
        mock_deps["create_doc"].assert_called_once()

    def test_multiple_policies(self, mock_deps):
        """DC-025: 複数ポリシーで複数ドキュメント生成

        document_extractors.py:62-66 のpolicy_groups新規作成をカバー
        """
        # Arrange
        from app.jobs.utils.document_extractors import _extract_violation_documents_from_output
        mock_deps["glob"].return_value = [
            "/out/policy1/resources.json",
            "/out/policy2/resources.json"
        ]
        mock_deps["load_metadata"].return_value = {}
        mock_deps["create_doc"].side_effect = lambda *a, **kw: {"doc": a[0]}

        resources = [{"id": "r1"}]

        # Act
        with patch("builtins.open", mock_open()), \
             patch("app.jobs.utils.document_extractors.json.load", return_value=resources):
            result = _extract_violation_documents_from_output(
                "/out", "job-1", "aws", "acct-1", {}
            )

        # Assert
        assert len(result) == 2

    def test_empty_resources_list(self, mock_deps):
        """DC-026: resources.jsonが空リストの場合はスキップ

        document_extractors.py:60 の `len(resources_data) > 0` がFalseの分岐をカバー
        """
        # Arrange
        from app.jobs.utils.document_extractors import _extract_violation_documents_from_output
        mock_deps["glob"].return_value = ["/out/p1/resources.json"]
        mock_deps["load_metadata"].return_value = {}

        # Act
        with patch("builtins.open", mock_open()), \
             patch("app.jobs.utils.document_extractors.json.load", return_value=[]):
            result = _extract_violation_documents_from_output(
                "/out", "job-1", "aws", "acct-1", {}
            )

        # Assert
        assert result == []

    def test_empty_dict_resource_in_list(self, mock_deps):
        """DC-026a: resourcesリスト内に空dictが含まれる場合

        document_extractors.py:71 の `if resource else {}` のelse分岐をカバー。
        空dictはPythonでfalsyなので `_normalize_resource_fields` は呼ばれず
        直接 `{}` が設定される。L70 `_extract_resource_id({}, i)` は正常通過
        （該当フィールド無し → "resource_0" を返す）。
        """
        # Arrange
        from app.jobs.utils.document_extractors import _extract_violation_documents_from_output
        mock_deps["glob"].return_value = ["/out/p1/resources.json"]
        mock_deps["load_metadata"].return_value = {}
        mock_deps["create_doc"].return_value = {"doc": "result"}

        resources = [{}, {"id": "r1"}]

        # Act
        with patch("builtins.open", mock_open()), \
             patch("app.jobs.utils.document_extractors.json.load", return_value=resources):
            result = _extract_violation_documents_from_output(
                "/out", "job-1", "aws", "acct-1", {}
            )

        # Assert
        assert len(result) == 1
        call_args = mock_deps["create_doc"].call_args
        group_resources = call_args[0][1]["resources"]
        # 空dictリソースは custodian_resource={} に変換される（L71 else分岐）
        assert group_resources[0]["custodian_resource"] == {}

    def test_no_resources_files(self, mock_deps):
        """DC-027: resources.jsonファイルが見つからない場合

        document_extractors.py:40-43 のglob結果が空の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.document_extractors import _extract_violation_documents_from_output
        mock_deps["glob"].return_value = []

        # Act
        result = _extract_violation_documents_from_output(
            "/out", "job-1", "aws", "acct-1", {}
        )

        # Assert
        assert result == []
```

### 2.5 _extract_v2_documents_from_output テスト

```python
class TestExtractV2Documents:
    """_extract_v2_documents_from_output のテスト"""

    @pytest.fixture
    def mock_v2_deps(self):
        """v2抽出の共通モック群"""
        with patch("app.jobs.utils.document_extractors.TaskLogger") as mock_logger_cls, \
             patch("app.jobs.utils.document_extractors._analyze_logs_for_statistics") as mock_stats, \
             patch("app.jobs.utils.document_extractors.convert_custodian_output_to_v2_hierarchical") as mock_conv:
            mock_logger = MagicMock()
            mock_logger_cls.return_value = mock_logger
            yield {
                "logger": mock_logger,
                "stats": mock_stats,
                "convert": mock_conv,
            }

    def test_normal_extraction(self, mock_v2_deps):
        """DC-028: 正常な階層構造v2ドキュメント抽出

        document_extractors.py:128-158 の正常フローをカバー
        """
        # Arrange
        from app.jobs.utils.document_extractors import _extract_v2_documents_from_output
        mock_v2_deps["stats"].return_value = {"policy1": {"total_resources_scanned": 10}}
        mock_v2_deps["convert"].return_value = {
            "doc_type": "hierarchical_scan_result_v2",
            "scan_summary": {"total_policies": 1, "total_resources": 3}
        }

        # Act
        result = _extract_v2_documents_from_output(
            "/out", "job-1", "aws", "acct-1", {"key": "val"}
        )

        # Assert
        assert len(result) == 1
        assert result[0]["scan_metadata"] == {"key": "val"}

    def test_empty_statistics(self, mock_v2_deps):
        """DC-029: ログ解析結果が空の場合はwarning出力して処理続行

        document_extractors.py:134-137 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.document_extractors import _extract_v2_documents_from_output
        mock_v2_deps["stats"].return_value = {}
        mock_v2_deps["convert"].return_value = {
            "doc_type": "hierarchical_scan_result_v2",
            "scan_summary": {"total_policies": 0, "total_resources": 0}
        }

        # Act
        result = _extract_v2_documents_from_output(
            "/out", "job-1", "aws", "acct-1", {}
        )

        # Assert
        assert len(result) == 1
        mock_v2_deps["logger"].warning.assert_called_once()

    def test_scan_metadata_already_set(self, mock_v2_deps):
        """DC-030: scan_metadataが既に設定済みなら上書きしない

        document_extractors.py:149-150 の条件分岐をカバー
        """
        # Arrange
        from app.jobs.utils.document_extractors import _extract_v2_documents_from_output
        mock_v2_deps["stats"].return_value = {}
        mock_v2_deps["convert"].return_value = {
            "doc_type": "hierarchical_scan_result_v2",
            "scan_metadata": {"existing": "data"},
            "scan_summary": {}
        }

        # Act
        result = _extract_v2_documents_from_output(
            "/out", "job-1", "aws", "acct-1", {"new": "data"}
        )

        # Assert
        assert result[0]["scan_metadata"] == {"existing": "data"}

    def test_doc_type_error(self, mock_v2_deps):
        """DC-031: doc_typeが_errorで終わる場合は空リスト

        document_extractors.py:153-155 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.document_extractors import _extract_v2_documents_from_output
        mock_v2_deps["stats"].return_value = {}
        mock_v2_deps["convert"].return_value = {
            "doc_type": "hierarchical_scan_result_v2_error"
        }

        # Act
        result = _extract_v2_documents_from_output(
            "/out", "job-1", "aws", "acct-1", {}
        )

        # Assert
        assert result == []
        mock_v2_deps["logger"].error.assert_called()
```

### 2.6 _analyze_logs_for_statistics テスト

```python
class TestAnalyzeLogsForStatistics:
    """_analyze_logs_for_statistics のテスト"""

    @pytest.fixture
    def mock_orchestrator(self):
        """PolicyAnalysisOrchestratorモック"""
        with patch("app.jobs.utils.document_extractors.TaskLogger") as mock_logger_cls:
            mock_logger = MagicMock()
            mock_logger_cls.return_value = mock_logger
            yield mock_logger

    def test_single_policy(self, mock_orchestrator):
        """DC-032: 単一ポリシーの統計取得

        document_extractors.py:196-216 のループ処理をカバー
        """
        # Arrange
        from app.jobs.utils.document_extractors import _analyze_logs_for_statistics
        mock_result = {
            "policy_results": [{
                "policy_name": "p1",
                "resource_statistics": {
                    "total_resources_scanned": 10,
                    "resources_after_filter": 3
                },
                "violation_count": 3
            }]
        }

        # Act
        with patch(
            "app.jobs.tasks.new_custodian_scan.log_analyzer.PolicyAnalysisOrchestrator"
        ) as mock_cls:
            mock_cls.return_value.analyze_multi_region_scan.return_value = mock_result
            result = _analyze_logs_for_statistics("/out", "job-1")

        # Assert
        assert "p1" in result
        assert result["p1"]["total_resources_scanned"] == 10
        assert result["p1"]["violation_count"] == 3

    def test_multiple_regions_aggregation(self, mock_orchestrator):
        """DC-033: 同名ポリシーの複数リージョン結果を集約

        document_extractors.py:207-210 の既存エントリ加算分岐をカバー
        """
        # Arrange
        from app.jobs.utils.document_extractors import _analyze_logs_for_statistics
        mock_result = {
            "policy_results": [
                {
                    "policy_name": "p1",
                    "resource_statistics": {"total_resources_scanned": 5, "resources_after_filter": 2},
                    "violation_count": 2
                },
                {
                    "policy_name": "p1",
                    "resource_statistics": {"total_resources_scanned": 8, "resources_after_filter": 3},
                    "violation_count": 3
                }
            ]
        }

        # Act
        with patch(
            "app.jobs.tasks.new_custodian_scan.log_analyzer.PolicyAnalysisOrchestrator"
        ) as mock_cls:
            mock_cls.return_value.analyze_multi_region_scan.return_value = mock_result
            result = _analyze_logs_for_statistics("/out", "job-1")

        # Assert
        assert result["p1"]["total_resources_scanned"] == 13
        assert result["p1"]["violation_count"] == 5

    def test_empty_policy_results(self, mock_orchestrator):
        """DC-034: policy_resultsが空の場合は空辞書

        document_extractors.py:190-191 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.document_extractors import _analyze_logs_for_statistics

        # Act
        with patch(
            "app.jobs.tasks.new_custodian_scan.log_analyzer.PolicyAnalysisOrchestrator"
        ) as mock_cls:
            mock_cls.return_value.analyze_multi_region_scan.return_value = {"policy_results": []}
            result = _analyze_logs_for_statistics("/out", "job-1")

        # Assert
        assert result == {}

    def test_policy_name_missing(self, mock_orchestrator):
        """DC-035: policy_nameが欠落しているエントリはスキップ

        document_extractors.py:198-199 の `if not policy_name: continue` をカバー
        """
        # Arrange
        from app.jobs.utils.document_extractors import _analyze_logs_for_statistics
        mock_result = {
            "policy_results": [
                {"resource_statistics": {}, "violation_count": 0},
                {"policy_name": "p1", "resource_statistics": {"total_resources_scanned": 1, "resources_after_filter": 0}, "violation_count": 0}
            ]
        }

        # Act
        with patch(
            "app.jobs.tasks.new_custodian_scan.log_analyzer.PolicyAnalysisOrchestrator"
        ) as mock_cls:
            mock_cls.return_value.analyze_multi_region_scan.return_value = mock_result
            result = _analyze_logs_for_statistics("/out", "job-1")

        # Assert
        assert len(result) == 1
        assert "p1" in result
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| DC-E01 | _extract_violation_documents ファイル読み込みエラー | resources.json読み込み失敗 | エラーログ出力、そのファイルをスキップ |
| DC-E02 | _extract_violation_documents 外部例外 | glob.glob例外 | 空リスト |
| DC-E03 | _extract_v2_documents 統計解析例外 | _analyze_logs_for_statistics例外 | 空リスト |
| DC-E03a | _extract_v2_documents 変換関数例外 | convert関数例外 | 空リスト |
| DC-E04 | _analyze_logs 例外 | Orchestrator例外 | 空辞書 |

### 3.1 抽出処理 異常系

```python
class TestDocumentExtractorErrors:
    """document_extractors エラーテスト"""

    def test_violation_file_read_error(self):
        """DC-E01: resources.json読み込みエラー時はスキップして続行

        document_extractors.py:80-82 のexcept分岐をカバー
        """
        # Arrange
        from app.jobs.utils.document_extractors import _extract_violation_documents_from_output

        # Act
        with patch("app.jobs.utils.document_extractors.TaskLogger") as mock_lc, \
             patch("app.jobs.utils.document_extractors.glob.glob", return_value=["/out/p1/resources.json"]), \
             patch("app.jobs.utils.document_extractors._load_metadata_from_file", return_value={}), \
             patch("builtins.open", side_effect=IOError("read error")):
            mock_lc.return_value = MagicMock()
            result = _extract_violation_documents_from_output(
                "/out", "job-1", "aws", "acct-1", {}
            )

        # Assert
        assert result == []
        mock_lc.return_value.error.assert_called()

    def test_violation_outer_exception(self):
        """DC-E02: glob.glob等の外部例外時は空リスト

        document_extractors.py:98-100 の最外try/except分岐をカバー
        """
        # Arrange
        from app.jobs.utils.document_extractors import _extract_violation_documents_from_output

        # Act
        with patch("app.jobs.utils.document_extractors.TaskLogger") as mock_lc, \
             patch("app.jobs.utils.document_extractors.glob.glob", side_effect=PermissionError("denied")):
            mock_lc.return_value = MagicMock()
            result = _extract_violation_documents_from_output(
                "/out", "job-1", "aws", "acct-1", {}
            )

        # Assert
        assert result == []

    def test_v2_extraction_stats_exception(self):
        """DC-E03: _analyze_logs_for_statistics例外時は空リスト

        document_extractors.py:160-162 の例外分岐をカバー
        （_analyze_logs_for_statisticsの例外がtry/exceptで捕捉される）
        """
        # Arrange
        from app.jobs.utils.document_extractors import _extract_v2_documents_from_output

        # Act
        with patch("app.jobs.utils.document_extractors.TaskLogger") as mock_lc, \
             patch("app.jobs.utils.document_extractors._analyze_logs_for_statistics", side_effect=RuntimeError("fail")):
            mock_lc.return_value = MagicMock()
            result = _extract_v2_documents_from_output(
                "/out", "job-1", "aws", "acct-1", {}
            )

        # Assert
        assert result == []

    def test_v2_convert_exception(self):
        """DC-E03a: convert_custodian_output_to_v2_hierarchical例外時は空リスト

        document_extractors.py:160-162 の例外分岐をカバー
        （_analyze_logs_for_statisticsは成功するがconvert関数で例外）
        """
        # Arrange
        from app.jobs.utils.document_extractors import _extract_v2_documents_from_output

        # Act
        with patch("app.jobs.utils.document_extractors.TaskLogger") as mock_lc, \
             patch("app.jobs.utils.document_extractors._analyze_logs_for_statistics", return_value={}), \
             patch("app.jobs.utils.document_extractors.convert_custodian_output_to_v2_hierarchical",
                   side_effect=RuntimeError("convert fail")):
            mock_lc.return_value = MagicMock()
            result = _extract_v2_documents_from_output(
                "/out", "job-1", "aws", "acct-1", {}
            )

        # Assert
        assert result == []
        mock_lc.return_value.error.assert_called()

    def test_analyze_logs_exception(self):
        """DC-E04: PolicyAnalysisOrchestrator例外時は空辞書

        document_extractors.py:220-223 の例外分岐をカバー
        """
        # Arrange
        from app.jobs.utils.document_extractors import _analyze_logs_for_statistics

        # Act
        with patch("app.jobs.utils.document_extractors.TaskLogger") as mock_lc, \
             patch(
                "app.jobs.tasks.new_custodian_scan.log_analyzer.PolicyAnalysisOrchestrator",
                side_effect=ImportError("module not found")
             ):
            mock_lc.return_value = MagicMock()
            result = _analyze_logs_for_statistics("/out", "job-1")

        # Assert
        assert result == {}
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| DC-SEC-01 | 大量リソースデータの処理 | 1000件のリソース | クラッシュせず正常完了 |
| DC-SEC-02 | ポリシー名にパストラバーサル文字 | `"../../etc"` | 文字列としてそのまま使用 |
| DC-SEC-03 | Azure typeフィールドの注入耐性確認 | 悪意ある文字列 | lower()のみ、HTMLタグは残る |
| DC-SEC-04 | 出力ディレクトリのパストラバーサル | `"../../../etc"` | glob.globにそのまま渡される |

```python
@pytest.mark.security
class TestDocumentSecurity:
    """ドキュメント生成・抽出セキュリティテスト"""

    def test_large_resource_data(self):
        """DC-SEC-01: 大量リソースデータの安全な処理

        1000件のリソースを含むgroup_dataでクラッシュしないことを確認。
        """
        # Arrange
        from app.jobs.utils.document_creators import _create_policy_grouped_document
        resources = [{"id": f"r-{i}", "data": f"v-{i}"} for i in range(1000)]
        group_data = {"metadata": {}, "resources": resources}

        # Act
        result = _create_policy_grouped_document(
            "p", group_data, "j", "aws", "a", {}, "ts"
        )

        # Assert
        assert result["resource_count"] == 1000
        assert isinstance(result, dict)

    def test_malicious_policy_name(self):
        """DC-SEC-02: パストラバーサル文字を含むポリシー名の安全な処理

        ポリシー名は内部生成だが、Custodian出力のディレクトリ名に由来するため
        悪意ある文字が含まれる可能性を確認。文字列としてそのまま保存される。
        """
        # Arrange
        from app.jobs.utils.document_creators import _create_opensearch_document
        malicious_name = "../../etc/passwd"

        # Act
        result = _create_opensearch_document(
            {}, malicious_name, "j", "aws", "a", "ts", {}, 0, None
        )

        # Assert
        assert result["policy"]["name"] == malicious_name
        assert isinstance(result["policy"]["name"], str)

    def test_azure_type_injection(self):
        """DC-SEC-03: Azureリソースtypeフィールドの注入耐性確認

        resource["type"]は外部入力由来。lower()変換のみで、HTML除去や
        サニタイズは行われない。現行挙動として `<script>` タグがそのまま
        保存されることを確認。
        """
        # Arrange
        from app.jobs.utils.document_creators import _create_opensearch_document
        malicious_type = '<script>alert("xss")</script>'

        # Act
        result = _create_opensearch_document(
            {"type": malicious_type}, "p", "j", "azure", "a", "ts", {}, 0, None
        )

        # Assert
        # lower()はHTMLタグを除去しない → "<script>" はそのまま残る（現行挙動の確認）
        assert result["policy"]["resource"] == malicious_type.lower()
        assert "<script>" in result["policy"]["resource"]

    def test_output_dir_path_traversal(self):
        """DC-SEC-04: 出力ディレクトリにパストラバーサルが含まれる場合の現行挙動確認

        custodian_output_dirは内部生成値だが、悪意ある入力が渡された場合の
        挙動を確認。glob.globにそのまま渡されるため、パス検証は行われない。
        """
        # Arrange
        from app.jobs.utils.document_extractors import _extract_violation_documents_from_output
        malicious_dir = "/out/../../../etc"

        # Act
        with patch("app.jobs.utils.document_extractors.TaskLogger") as mock_lc, \
             patch("app.jobs.utils.document_extractors.glob.glob", return_value=[]) as mock_glob:
            mock_lc.return_value = MagicMock()
            result = _extract_violation_documents_from_output(
                malicious_dir, "job-1", "aws", "acct-1", {}
            )

        # Assert
        assert result == []
        # パストラバーサル文字列がglob.globにそのまま渡されることを確認
        call_args = mock_glob.call_args[0][0]
        assert "../../../etc" in call_args
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_utils_module` | テスト間のモジュール状態リセット | function | Yes |
| `mock_deps` | _extract_violation_documents共通モック | function | No |
| `mock_v2_deps` | _extract_v2_documents共通モック | function | No |
| `mock_orchestrator` | _analyze_logs共通モック | function | No |

### 共通フィクスチャ定義

```python
# test/unit/jobs/utils/conftest.py（既存に追加）
# reset_utils_module は #17a（jobs_utils_helper_normalizer_tests.md）で定義済み（app.jobs.utils のみクリア）
```

---

## 6. テスト実行例

```bash
# ドキュメント生成・抽出テストのみ実行
pytest test/unit/jobs/utils/test_document.py -v

# 特定のテストクラスのみ実行
pytest test/unit/jobs/utils/test_document.py::TestCreateOpensearchDocument -v

# カバレッジ付きで実行
pytest test/unit/jobs/utils/test_document.py \
  --cov=app.jobs.utils.document_creators \
  --cov=app.jobs.utils.document_extractors \
  --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/jobs/utils/test_document.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 36 | DC-001 〜 DC-035（DC-026a含む） |
| 異常系 | 5 | DC-E01 〜 DC-E04（DC-E03a含む） |
| セキュリティ | 4 | DC-SEC-01 〜 DC-SEC-04 |
| **合計** | **45** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestCreateOpensearchDocument` | DC-001〜DC-015 | 15 |
| `TestCreateRawOpensearchDocument` | DC-016〜DC-019 | 4 |
| `TestCreatePolicyGroupedDocument` | DC-020〜DC-023 | 4 |
| `TestExtractViolationDocuments` | DC-024〜DC-027, DC-026a | 5 |
| `TestExtractV2Documents` | DC-028〜DC-031 | 4 |
| `TestAnalyzeLogsForStatistics` | DC-032〜DC-035 | 4 |
| `TestDocumentExtractorErrors` | DC-E01〜DC-E04, DC-E03a | 5 |
| `TestDocumentSecurity` | DC-SEC-01〜DC-SEC-04 | 4 |

### 実装失敗が予想されるテスト

現時点で失敗が予想されるテストはありません。

### 残留リスク

| テストID | リスク内容 | 対応方針 |
|---------|-----------|---------|
| DC-SEC-03 | 現行挙動（`lower()` のみでHTMLタグ `<script>` が残る）を固定しているため、将来サニタイズ実装が追加された場合にアサーション `assert "<script>" in` の更新が必要 | サニタイズ追加時に `assert "<script>" not in` へ変更 |

### 注意事項

- `@pytest.mark.security` マーカーは `pyproject.toml` に登録が必要
- `_create_raw_opensearch_document` は関数内import（L126）のため、`_normalize_resource_fields` は元モジュール `app.jobs.utils.field_normalizers._normalize_resource_fields` をパッチする
- `_analyze_logs_for_statistics` は関数内import（L184）のため、`PolicyAnalysisOrchestrator` は元モジュール `app.jobs.tasks.new_custodian_scan.log_analyzer.PolicyAnalysisOrchestrator` をパッチする
- conftest.py の `reset_utils_module` は #17a（`jobs_utils_helper_normalizer_tests.md`）で定義済み（`app.jobs.utils` スコープ）

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `_extract_violation_documents` はファイルシステム依存（glob, open） | モック複雑度が高い | テストではopen/json.load/globを全てモック |
| 2 | `_extract_v2_documents` は `convert_custodian_output_to_v2_hierarchical` に依存 | #17d（`jobs_utils_v2_format_converter_tests.md`）完了前はモックで代替 | 戻り値の構造体をモックで再現 |
| 3 | `_analyze_logs_for_statistics` は `PolicyAnalysisOrchestrator` に依存 | ログ解析モジュールの変更影響を受ける | Orchestratorの戻り値構造をモックで固定 |
| 4 | `_create_opensearch_document` の L38-39 でサニタイズが無効化されている | コメントアウトされたコードが将来復活する可能性 | テストはコメントアウト状態を前提に設計 |
| 5 | `_extract_violation_documents` L71 の `if resource else {}` は `resource=None` では到達不能 | L70 `_extract_resource_id(None, i)` が先に `TypeError` を発生 → ファイル全体がスキップされる（L80 catch） | Noneリソースのエラー処理はDC-E01のパターンでカバー済み。L71ガードは空dict（`{}`）のみに有効 |
