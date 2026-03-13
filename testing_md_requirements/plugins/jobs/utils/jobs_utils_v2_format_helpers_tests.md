# jobs/utils v2フォーマットヘルパー群 テストケース

## 1. 概要

`app/jobs/utils/` のv2フォーマット変換ヘルパー群（`v2_format_helpers.py`, `v2_hierarchical_helpers.py`, `v2_format_legacy_functions.py`, `resource_id_extractor.py`）のテスト仕様書。v2フォーマットコンバーター（#17d `jobs_utils_v2_format_converter_tests.md`）の内部構成要素であり、リソース属性抽出・階層構造構築・ID抽出・レガシー変換を担う。

### 1.1 主要機能

| 関数 | ファイル | 説明 |
|------|---------|------|
| `extract_ec2_attributes()` | v2_format_helpers.py | EC2インスタンス属性抽出 |
| `extract_s3_attributes()` | v2_format_helpers.py | S3バケット属性抽出 |
| `extract_ebs_attributes()` | v2_format_helpers.py | EBSボリューム属性抽出 |
| `extract_security_group_attributes()` | v2_format_helpers.py | セキュリティグループ属性抽出 |
| `extract_generic_attributes()` | v2_format_helpers.py | 汎用属性抽出 |
| `add_common_attributes()` | v2_format_helpers.py | 共通属性（タグ等）追加 |
| `check_encryption_status()` | v2_format_helpers.py | 暗号化状態チェック |
| `check_public_access()` | v2_format_helpers.py | 公開アクセスチェック |
| `extract_security_groups()` | v2_format_helpers.py | SG ID抽出 |
| `extract_iam_role()` | v2_format_helpers.py | IAMロール抽出 |
| `extract_s3_security_context()` | v2_format_helpers.py | S3セキュリティコンテキスト |
| `extract_ec2_security_context()` | v2_format_helpers.py | EC2セキュリティコンテキスト |
| `extract_account_id()` | v2_format_helpers.py | アカウントID抽出 |
| `extract_region()` | v2_format_helpers.py | リージョン抽出 |
| `build_simple_arn()` | v2_format_helpers.py | 簡易ARN構築 |
| `determine_resource_state()` | v2_format_helpers.py | リソース状態判定 |
| `determine_severity()` | v2_format_helpers.py | 重要度判定 |
| `build_error_response()` | v2_format_helpers.py | エラーレスポンス構築 |
| `_structure_resource_data()` | v2_hierarchical_helpers.py | リソースデータ構造化 |
| `_build_error_document()` | v2_hierarchical_helpers.py | エラードキュメント構築 |
| `_build_empty_document()` | v2_hierarchical_helpers.py | 空ドキュメント構築 |
| `_load_metadata_safely()` | v2_hierarchical_helpers.py | メタデータ安全読み込み |
| `_load_resources_safely()` | v2_hierarchical_helpers.py | リソース安全読み込み |
| `_load_error_info_safely()` | v2_hierarchical_helpers.py | エラー情報安全読み込み |
| `_extract_resource_type_from_metadata()` | v2_hierarchical_helpers.py | メタデータからリソースタイプ抽出 |
| `_determine_policy_status()` | v2_hierarchical_helpers.py | ポリシーステータス判定 |
| `_build_execution_details()` | v2_hierarchical_helpers.py | 実行詳細構築 |
| `_classify_error_type()` | v2_hierarchical_helpers.py | エラータイプ分類 |
| `_extract_region_from_resource()` | v2_hierarchical_helpers.py | リソースからリージョン抽出 |
| `_extract_primary_resource_id()` | v2_hierarchical_helpers.py | プライマリリソースID抽出 |
| `_build_resource_arn_safely()` | v2_hierarchical_helpers.py | ARN安全構築 |
| `_extract_resource_state()` | v2_hierarchical_helpers.py | リソース状態抽出 |
| `_structure_tags()` | v2_hierarchical_helpers.py | タグ構造化 |
| `_build_error_policy()` | v2_hierarchical_helpers.py | エラーポリシー構築 |
| `extract_resource_context()` | v2_format_legacy_functions.py | リソースコンテキスト抽出 |
| `extract_security_context()` | v2_format_legacy_functions.py | セキュリティコンテキスト抽出 |
| `_build_resource_identity()` | v2_format_legacy_functions.py | リソース識別情報構築 |
| `_build_violation_context_v2()` | v2_format_legacy_functions.py | 違反コンテキスト構築 |
| `_create_resource_snapshot()` | v2_format_legacy_functions.py | リソーススナップショット作成 |
| `extract_resource_id()` | resource_id_extractor.py | 5段階フォールバックID抽出 |
| `extract_display_name()` | resource_id_extractor.py | 表示名抽出 |
| `extract_resource_arn()` | resource_id_extractor.py | ARN解析 |
| `_get_priority_id_fields()` | resource_id_extractor.py | 優先IDフィールド取得 |
| `get_resource_summary()` | resource_id_extractor.py | リソース要約取得 |
| `build_resource_arn()` | resource_id_extractor.py | ARN構築・抽出 |
| `sanitize_arn_for_document_id()` | resource_id_extractor.py | ARNサニタイズ |
| `_build_arn_by_resource_type()` | resource_id_extractor.py | タイプ別ARN構築 |

### 1.2 カバレッジ目標: 90%

> **注記**: v2_format_helpers.py と resource_id_extractor.py は純粋な変換関数が中心でモック不要。v2_hierarchical_helpers.py はファイルI/O（`os.path.exists`, `open`, `json.load`）のモックが必要。v2_format_legacy_functions.py はモジュールレベルで他2ファイルをimportするが、同一仕様書スコープ内のため実装を直接利用しモック不要。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象1 | `app/jobs/utils/v2_format_helpers.py` (374行) |
| テスト対象2 | `app/jobs/utils/v2_hierarchical_helpers.py` (461行) |
| テスト対象3 | `app/jobs/utils/v2_format_legacy_functions.py` (356行) |
| テスト対象4 | `app/jobs/utils/resource_id_extractor.py` (466行) |
| テストコード | `test/unit/jobs/utils/test_v2_format_helpers.py` |
| conftest | `test/unit/jobs/utils/conftest.py` |

### 1.4 依存関係

```
v2_format_legacy_functions.py
├── resource_id_extractor.py (extract_resource_id, extract_display_name, build_resource_arn)
└── v2_format_helpers.py (18関数: extract_*_attributes, check_*, extract_*, build_*, determine_*)

v2_format_helpers.py (独立: 標準ライブラリのみ)
v2_hierarchical_helpers.py (独立: 標準ライブラリのみ)
resource_id_extractor.py (独立: 標準ライブラリのみ)

被依存（他utilsファイルからの参照）:
└── v2_format_converter.py ← v2_format_helpers, v2_hierarchical_helpers, v2_format_legacy_functions, resource_id_extractor
```

### 1.5 主要分岐マップ

| 関数 | 分岐数 | 主要条件 |
|------|--------|---------|
| `extract_ec2_attributes` | 7 | L27-36 各フィールド存在チェック（VpcId, Placement.AZ, InstanceType, LaunchTime, State, PrivateIp, PublicIp） |
| `extract_s3_attributes` | 4 | L51-58 CreationDate, Location, Versioning, Website（is not Noneチェック） |
| `extract_generic_attributes` | 2 | L112 フィールド存在 + None除外 |
| `add_common_attributes` | 3 | L121 Tags存在, L122 list型, L124 dict型 |
| `check_encryption_status` | 4 | L135 ebs, L137 s3, L140 ec2(ループ), L148 other |
| `check_public_access` | 4 | L153 ec2, L156 s3(Policy文字列チェック), L164 other |
| `extract_account_id` | 3 | L235 ARNフィールド, L241 NetworkInterfaces, L246 fallback |
| `extract_region` | 4 | L253 ARN, L259 AZ直接, L264 Placement.AZ, L269 fallback |
| `build_simple_arn` | 5 | L278 unknown account/region, L290 unknown service, L302 S3, L304 other, L307 exception |
| `determine_severity` | 4 | L333 security/critical, L335 test/dev, L339 stopped状態, L341 running状態 |
| `_load_metadata_safely` | 3 | L115 ファイル存在, L118 不存在, L119 例外 |
| `_load_resources_safely` | 4 | L127 ファイル存在, L130 list判定, L131 不存在, L132 例外 |
| `_load_error_info_safely` | 4 | L142 ループ3ファイル, L144 存在, L147 内容有無, L151 例外 |
| `_determine_policy_status` | 4 | L175 error有+resources有, L177 error有+resources無, L179 resources有, L182 resources無 |
| `_build_execution_details` | 6 | L219 error, L221 scanned=0, L224 violations>0, L227 scanned>0, L231 else, L235 error_info有 |
| `_classify_error_type` | 5 | L276 permission, L278 config, L280 timeout, L282 network, L284 unknown |
| `_extract_region_from_resource` | 4 | L297 ドット付きキー, L308-310 AZからリージョン, L314 直接フィールド, L320 fallback |
| `_build_resource_arn_safely` | 5 | L357 既存Arnフィールド, L361 EC2, L370 S3, L375 EBS, L383 SG→None |
| `extract_resource_id` | 6 | L33 priority_field, L48 id_suffix, L62 name, L75 arn, L90 identifier, L99 failed |
| `extract_display_name` | 4 | L130 Tags Name, L154 タイプ別フィールド, L160 ID fallback, L166 例外fallback |
| `build_resource_arn` | 4 | L308 existing_arn, L314-317 account/region抽出, L323 情報不足, L328 タイプ別構築 |
| `sanitize_arn_for_document_id` | 3 | L352 invalid入力, L356 特殊文字変換, L359 512文字超(hashlib) |
| `_build_arn_by_resource_type` | 9 | L438 ec2, L441 ebs, L444 sg, L447 s3, L451 iam, L456 lambda, L459 rds, L462 vpc, L465 else |
| `extract_resource_context` | 6 | L47 入力検証, L54-64 5タイプ分岐, L72 例外 |
| `_build_violation_context_v2` | 3 | L211 ドット付きフィルター, L224 state判定, L227 severity判定 |
| `_create_resource_snapshot` | 6 | L273 ec2, L275 s3, L277 ebs, L279 sg, L282 generic, L285 例外 |

### 1.6 実装上の注意点

| # | 注意点 | 影響 |
|---|--------|------|
| 1 | `sanitize_arn_for_document_id` は関数内で `import hashlib`（L361） | 関数内importだがhashlibは標準ライブラリのため、512文字超の実ARNで実際のハッシュ動作をテスト可能。モック不要 |
| 2 | `v2_format_legacy_functions.py` はモジュールレベルで `resource_id_extractor` と `v2_format_helpers` をimport（L18-26） | 同一仕様書スコープ内の4ファイルのため、モックせず実装を直接利用。テストは薄い結合テストとして動作する |
| 3 | `v2_hierarchical_helpers.py` のファイルI/O関数は `os.path.exists`, `open`, `json.load` を使用 | `@patch` で標準ライブラリをモックする必要あり |
| 4 | `build_error_response` と `_build_error_document` は `datetime.now(timezone.utc)` を呼ぶ | タイムスタンプは存在チェックのみ（値の一致は検証しない） |
| 5 | `_build_execution_details` L227 の `resources_scanned > 0` は statistics=None 時に `None > 0` で TypeError を起こす | statistics=None かつ resources=[] の場合、L213 で `resources_scanned=None` → L221 `None is not None` は False → L224 `0 > 0` は False → L227 `None > 0` で TypeError。ただしL205の `try` ブロック内で発生するため L259 `except Exception` でキャッチされ、`processing_error` として返却される（TypeErrorは呼び出し元に伝播しない） |

> **v2_format_legacy_functions.py のモック戦略**:
> 同一仕様書内の4ファイルは相互依存があるが、v2_format_helpers.py と resource_id_extractor.py は純粋関数のためモック不要。v2_format_legacy_functions.py のテストでは実装を直接呼び出し、入力データの違いで分岐をカバーする。

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| VH-001 | extract_ec2_attributes 全属性抽出 | EC2リソース全フィールド | 7属性マッピング |
| VH-002 | extract_s3_attributes Website判定 | S3 Website有り/無し | website_hosting: True/False |
| VH-003 | extract_ebs/sg_attributes 全属性 | EBS+SGリソース | 正しい属性マッピング |
| VH-004 | extract_generic_attributes None除外 | State有+Size=None | Size除外 |
| VH-005 | add_common_attributes タグ変換 | list/dict/空タグ | list保持/dict→list変換 |
| VH-006 | check_encryption_status 3タイプ | ebs/s3/ec2 | True/False/True |
| VH-007 | check_public_access EC2/S3 | PublicIP/Policy | True/True |
| VH-008 | extract_security_groups + iam_role | dict/str混在SG + IAMプロファイル | ID一覧 + ロール名 |
| VH-009 | s3/ec2_security_context 全項目 | S3 Acl/Logging + EC2 Metadata | コンテキスト辞書 |
| VH-010 | extract_account_id + region フォールバック | ARN/AZ/Placement | ID + リージョン |
| VH-011 | build_simple_arn EC2/S3/unknown | 3タイプ | ARN/S3 ARN/None |
| VH-012 | determine_state + severity + error_response | State dict/str + policy名 | 状態/重要度/レスポンス構造 |
| VH-013 | _structure_resource_data 正常系 | EC2データ | 構造化辞書 |
| VH-014 | _structure_resource_data 例外フォールバック | 不正データ | unknown値辞書 |
| VH-015 | _build_error/empty/error_policy_document 構造 | scan_id等 | doc_type/error_message/policy_status |
| VH-016 | _load_metadata_safely 正常/不存在 | ファイル有無 | 辞書/{} |
| VH-017 | _load_resources_safely 正常/非list | list/dictデータ | list/[] |
| VH-018 | _load_error_info_safely ログ検出/空 | custodian.log有無 | ログ情報/None |
| VH-019 | _extract_resource_type + _determine_policy_status | metadata + error/resources | タイプ + ステータス |
| VH-020 | _build_execution_details statistics有り | 統計データ | has_violations |
| VH-021 | _build_execution_details 4状態 | error/no_resources/violations/no_match | 各compliance_status |
| VH-022 | _classify_error_type 5分類 | 5種キーワード | 5種エラータイプ |
| VH-023 | _extract_region + _primary_resource_id | Region/AZ + InstanceId/VolumeId/未知キー | リージョン + ID |
| VH-024 | _build_resource_arn_safely + _extract_state + _structure_tags | EC2/S3/EBS + State + Tags | ARN + 状態 + タグ |
| VH-025 | extract_resource_id ステップ1 priority_field | InstanceId有り | method=priority_field_pattern |
| VH-026 | extract_resource_id ステップ2 id_suffix | CustomId有り | method=id_suffix_pattern |
| VH-027 | extract_resource_id ステップ3-4 name/arn | Name/ResourceArn | method=name/arn_extraction |
| VH-028 | extract_resource_id ステップ5+fallback | Identifier/空 | method=identifier/failed |
| VH-029 | extract_display_name Tags Name優先 | Name タグ有り | タグ値 |
| VH-030 | extract_display_name タイプ別フィールド | SG GroupName | GroupName値 |
| VH-031 | extract_resource_arn ARN解析 | EC2 ARN文字列 | リソースID部分 |
| VH-032 | _get_priority_id_fields タイプ正規化 | aws.ec2/aws.aws.ec2 | InstanceId |
| VH-033 | get_resource_summary 要約情報 | EC2データ | 全要約フィールド |
| VH-034 | build_resource_arn 既存ARN/構築 | Arn有り/無し | 既存ARN/構築ARN |
| VH-035 | sanitize_arn_for_document_id 変換 | 特殊文字ARN/長大ARN | サニタイズ済/ハッシュ短縮 |
| VH-036 | _extract_existing_arn + _account_id + _region | ARNフィールド/OwnerId/AZ | ARN/account/region |
| VH-037 | _build_arn_by_resource_type 全タイプ | ec2/s3/iam/lambda/else | 各ARNフォーマット |
| VH-038 | extract_resource_context EC2タイプ | EC2リソース | EC2属性+共通属性 |
| VH-039 | extract_resource_context 入力検証+汎用 | 空入力/unknownタイプ | エラー/汎用属性 |
| VH-040 | extract_security_context S3/EC2 | S3/EC2リソース | セキュリティ項目 |
| VH-041 | _build_resource_identity 正常 | EC2データ | 識別情報辞書 |
| VH-042 | _build_violation_context_v2 フィルター値 | MatchedFilters有り | filter_values+severity |
| VH-043 | _create_resource_snapshot 5タイプ | ec2/s3/ebs/sg/generic | タイプ別スナップショット |
| VH-044 | _create_ec2/s3_snapshot 詳細 | Tags+SG+全フィールド | 完全スナップショット |

### 共通import

```python
# test/unit/jobs/utils/test_v2_format_helpers.py
import pytest
from unittest.mock import patch, mock_open, MagicMock

# v2_format_helpers.py
from app.jobs.utils.v2_format_helpers import (
    extract_ec2_attributes, extract_s3_attributes, extract_ebs_attributes,
    extract_security_group_attributes, extract_generic_attributes, add_common_attributes,
    check_encryption_status, check_public_access, extract_security_groups,
    extract_iam_role, extract_s3_security_context, extract_ec2_security_context,
    extract_account_id, extract_region, build_simple_arn,
    determine_resource_state, determine_severity, build_error_response
)
# v2_hierarchical_helpers.py
from app.jobs.utils.v2_hierarchical_helpers import (
    _structure_resource_data, _build_error_document, _build_empty_document,
    _load_metadata_safely, _load_resources_safely, _load_error_info_safely,
    _extract_resource_type_from_metadata, _determine_policy_status,
    _build_execution_details, _classify_error_type,
    _extract_region_from_resource, _extract_primary_resource_id,
    _build_resource_arn_safely, _extract_resource_state, _structure_tags,
    _build_error_policy
)
# resource_id_extractor.py
from app.jobs.utils.resource_id_extractor import (
    extract_resource_id, extract_display_name, extract_resource_arn,
    _get_priority_id_fields, get_resource_summary, build_resource_arn,
    sanitize_arn_for_document_id, _extract_existing_arn,
    _extract_account_id, _extract_region, _build_arn_by_resource_type
)
# v2_format_legacy_functions.py
from app.jobs.utils.v2_format_legacy_functions import (
    extract_resource_context, extract_security_context,
    _build_resource_identity, _build_violation_context_v2,
    _create_resource_snapshot
)
```

### TestV2FormatHelpers

```python
class TestV2FormatHelpers:
    """v2_format_helpers.py のテスト"""

    class TestAttributeExtractors:
        """リソースタイプ別属性抽出"""

        def test_extract_ec2_attributes_all_fields(self):
            """VH-001: EC2全属性が正しくマッピングされる"""
            # Arrange
            resource = {
                "VpcId": "vpc-123",
                "Placement": {"AvailabilityZone": "us-east-1a"},
                "InstanceType": "t3.micro",
                "LaunchTime": "2024-01-01T00:00:00Z",
                "State": {"Name": "running"},
                "PrivateIpAddress": "10.0.0.1",
                "PublicIpAddress": "54.1.2.3"
            }

            # Act
            result = extract_ec2_attributes(resource)

            # Assert
            assert result["vpc_id"] == "vpc-123"
            assert result["availability_zone"] == "us-east-1a"
            assert result["instance_type"] == "t3.micro"
            assert result["creation_time"] == "2024-01-01T00:00:00Z"
            assert result["state"] == {"Name": "running"}
            assert result["private_ip"] == "10.0.0.1"
            assert result["public_ip"] == "54.1.2.3"

        def test_extract_s3_attributes_website_check(self):
            """VH-002: S3 Website属性のis not None判定を検証"""
            # Arrange
            resource_with_website = {
                "CreationDate": "2024-01-01",
                "Location": "us-east-1",
                "Versioning": {"Status": "Enabled"},
                "Website": {"RedirectAllRequestsTo": {"HostName": "example.com"}}
            }
            resource_without_website = {
                "CreationDate": "2024-01-01",
                "Website": None
            }

            # Act
            result_with = extract_s3_attributes(resource_with_website)
            result_without = extract_s3_attributes(resource_without_website)

            # Assert
            assert result_with["website_hosting"] is True
            assert result_without["website_hosting"] is False

        def test_extract_ebs_sg_attributes(self):
            """VH-003: EBS/SGの属性マッピングを検証"""
            # Arrange
            ebs_resource = {
                "Size": 100, "VolumeType": "gp3",
                "AvailabilityZone": "us-east-1a",
                "CreateTime": "2024-01-01", "State": "available",
                "Attachments": [{"InstanceId": "i-123"}]
            }
            sg_resource = {
                "GroupName": "my-sg", "Description": "Test SG",
                "VpcId": "vpc-123",
                "IpPermissions": [{"FromPort": 80}],
                "IpPermissionsEgress": [{"FromPort": 0}, {"FromPort": 443}]
            }

            # Act
            ebs_result = extract_ebs_attributes(ebs_resource)
            sg_result = extract_security_group_attributes(sg_resource)

            # Assert
            assert ebs_result["size_gb"] == 100
            assert ebs_result["volume_type"] == "gp3"
            assert ebs_result["attachments"] == [{"InstanceId": "i-123"}]
            assert sg_result["group_name"] == "my-sg"
            assert sg_result["inbound_rules_count"] == 1
            assert sg_result["outbound_rules_count"] == 2

        def test_extract_generic_attributes_none_filtering(self):
            """VH-004: 汎用属性抽出でNone値が除外される"""
            # Arrange
            resource = {"State": "running", "Size": None, "Region": "us-east-1", "Other": "ignored"}

            # Act
            result = extract_generic_attributes(resource)

            # Assert
            assert result["state"] == "running"
            assert result["region"] == "us-east-1"
            assert "size" not in result  # None値は除外
            assert "other" not in result  # common_fieldsに含まれないフィールドは除外

        def test_add_common_attributes_tag_formats(self):
            """VH-005: タグのリスト形式保持・辞書形式変換・空タグを検証"""
            # Arrange
            attrs_list = {}
            resource_list = {"Tags": [{"Key": "env", "Value": "prod"}]}
            attrs_dict = {}
            resource_dict = {"Tags": {"env": "prod", "team": "dev"}}
            attrs_empty = {}
            resource_empty_tags = {"Tags": []}
            attrs_no_tags = {}
            resource_no_tags = {"Other": "value"}

            # Act
            add_common_attributes(attrs_list, resource_list)
            add_common_attributes(attrs_dict, resource_dict)
            add_common_attributes(attrs_empty, resource_empty_tags)
            add_common_attributes(attrs_no_tags, resource_no_tags)

            # Assert
            assert attrs_list["tags"] == [{"Key": "env", "Value": "prod"}]
            assert {"key": "env", "value": "prod"} in attrs_dict["tags"]
            assert {"key": "team", "value": "dev"} in attrs_dict["tags"]
            # 空タグ/タグ無し → tagsキーが追加されない（L121 Falsy判定）
            assert "tags" not in attrs_empty
            assert "tags" not in attrs_no_tags

    class TestSecurityFunctions:
        """セキュリティ関連関数"""

        def test_check_encryption_status_three_types(self):
            """VH-006: EBS/S3/EC2の暗号化判定分岐を検証"""
            # Arrange
            ebs_data = {"Encrypted": True}
            s3_data = {}
            ec2_data = {"BlockDeviceMappings": [
                {"Ebs": {"Encrypted": True}},
                {"Ebs": {"Encrypted": False}}
            ]}
            ec2_no_encryption = {"BlockDeviceMappings": [
                {"Ebs": {"Encrypted": False}}
            ]}

            # Act & Assert
            assert check_encryption_status(ebs_data, "aws.ebs") is True
            assert check_encryption_status(s3_data, "aws.s3") is False
            assert check_encryption_status(ec2_data, "aws.ec2") is True
            assert check_encryption_status(ec2_no_encryption, "aws.ec2") is False
            assert check_encryption_status({}, "aws.unknown") is False

        def test_check_public_access_ec2_s3(self):
            """VH-007: EC2パブリックIP/S3ポリシーによる公開アクセス判定"""
            # Arrange
            ec2_public = {"PublicIpAddress": "54.1.2.3"}
            ec2_private = {}
            s3_public = {"Policy": '{"Statement":[{"Principal":"*"}]}'}  # "Principal":"*" 含む
            s3_private = {"Policy": '{"Statement":[{"Principal":{"AWS":"arn:aws:iam::123:root"}}]}'}

            # Act & Assert
            assert check_public_access(ec2_public, "aws.ec2") is True
            assert check_public_access(ec2_private, "aws.ec2") is False
            # S3: '"Principal":"*"' の文字列一致チェック（L161）
            assert check_public_access(s3_public, "aws.s3") is True
            assert check_public_access(s3_private, "aws.s3") is False
            assert check_public_access({}, "aws.rds") is False

        def test_extract_security_groups_and_iam_role(self):
            """VH-008: SG ID抽出（dict/str混在）とIAMロール抽出"""
            # Arrange
            sg_resource = {"SecurityGroups": [
                {"GroupId": "sg-111"},
                "sg-222",
                {"NoGroupId": "skip"}  # GroupIdなしは無視
            ]}
            iam_resource = {
                "IamInstanceProfile": {"Arn": "arn:aws:iam::123:instance-profile/my-role"}
            }
            iam_no_slash = {
                "IamInstanceProfile": {"Arn": "arn-without-slash"}
            }

            # Act
            sg_result = extract_security_groups(sg_resource)
            iam_result = extract_iam_role(iam_resource)
            iam_no_slash_result = extract_iam_role(iam_no_slash)

            # Assert
            assert sg_result == ["sg-111", "sg-222"]
            assert iam_result == "my-role"
            assert iam_no_slash_result == "arn-without-slash"  # スラッシュ無し → ARN全体

        def test_s3_ec2_security_context(self):
            """VH-009: S3/EC2固有セキュリティコンテキストの全フィールド"""
            # Arrange
            s3_data = {
                "Acl": {"Owner": {"DisplayName": "admin"}},
                "Logging": {"TargetBucket": "log-bucket"},
                "Versioning": {"Status": "Enabled"}
            }
            ec2_data = {
                "MetadataOptions": {"HttpTokens": "required", "HttpEndpoint": "enabled"},
                "Monitoring": {"State": "enabled"}
            }

            # Act
            s3_ctx = extract_s3_security_context(s3_data)
            ec2_ctx = extract_ec2_security_context(ec2_data)

            # Assert
            assert s3_ctx["bucket_owner"] == "admin"
            assert s3_ctx["access_logging"] is True
            assert s3_ctx["versioning_enabled"] is True
            assert ec2_ctx["imds_v2_required"] is True
            assert ec2_ctx["metadata_endpoint"] is True
            assert ec2_ctx["detailed_monitoring"] is True

    class TestUtilityFunctions:
        """ユーティリティ関数"""

        def test_extract_account_id_and_region_fallbacks(self):
            """VH-010: アカウントID/リージョンの多段フォールバック"""
            # Arrange
            resource_arn = {"InstanceArn": "arn:aws:ec2:us-east-1:123456789012:instance/i-123"}
            resource_network = {
                "NetworkInterfaces": [{"OwnerId": "987654321098"}]
            }
            resource_az = {"AvailabilityZone": "ap-northeast-1a"}
            resource_placement = {"Placement": {"AvailabilityZone": "eu-west-1b"}}
            resource_empty = {}

            # Act & Assert — account_id
            assert extract_account_id(resource_arn) == "123456789012"
            assert extract_account_id(resource_network) == "987654321098"
            assert extract_account_id(resource_empty) == "unknown"

            # Act & Assert — region
            assert extract_region(resource_arn) == "us-east-1"
            assert extract_region(resource_az) == "ap-northeast-1"
            assert extract_region(resource_placement) == "eu-west-1"
            assert extract_region(resource_empty) == "unknown"

        def test_build_simple_arn_ec2_s3_unknown(self):
            """VH-011: EC2/S3/未知タイプのARN構築"""
            # Arrange
            ec2_resource = {"InstanceArn": "arn:aws:ec2:us-east-1:123:instance/i-1"}
            s3_resource = {"BucketArn": "arn:aws:s3:::my-bucket"}

            # Act
            ec2_arn = build_simple_arn(ec2_resource, "aws.ec2", "i-123")
            s3_arn = build_simple_arn(s3_resource, "aws.s3", "my-bucket")
            unknown_arn = build_simple_arn(ec2_resource, "aws.unknown-type", "res-1")

            # Assert
            assert ec2_arn == "arn:aws:ec2:us-east-1:123:instance/i-123"
            assert s3_arn == "arn:aws:s3:::my-bucket"  # S3はリージョンレス
            assert unknown_arn is None  # unknownサービスはNone

        def test_determine_state_severity_error_response(self):
            """VH-012: リソース状態/重要度判定とエラーレスポンス構造"""
            # Arrange & Act — state
            state_dict = determine_resource_state({"State": {"Name": "running"}}, [])
            state_str = determine_resource_state({"State": "available"}, [])
            state_filter = determine_resource_state({}, ["State.Name"])
            state_unknown = determine_resource_state({}, [])

            # Assert — state
            assert state_dict == "running"
            assert state_str == "available"
            assert state_filter == "filtered_by_state"
            assert state_unknown == "unknown"

            # Arrange & Act — severity
            assert determine_severity("security-check", "running", []) == "high"
            assert determine_severity("critical-policy", "running", []) == "high"
            assert determine_severity("test-policy", "running", []) == "low"
            assert determine_severity("normal", "stopped", []) == "low"
            assert determine_severity("normal", "running", []) == "medium"
            assert determine_severity("normal", "unknown", []) == "medium"

            # Act — error_response
            resp = build_error_response("scan-1", "policy-1", "test error")

            # Assert — error_response
            assert resp["scan_id"] == "scan-1"
            assert resp["policy_name"] == "policy-1"
            assert resp["account_id"] == "error"
            assert resp["resource_identity"]["primary_id"] == "error"
            assert resp["resource_attributes"]["error"] == "test error"
            assert "timestamp" in resp
```

### TestV2HierarchicalHelpers

```python
class TestV2HierarchicalHelpers:
    """v2_hierarchical_helpers.py のテスト"""

    class TestResourceStructuring:
        """リソースデータ構造化"""

        def test_structure_resource_data_normal(self):
            """VH-013: EC2リソースデータが正しく構造化される"""
            # Arrange
            resource = {
                "InstanceId": "i-123",
                "Placement": {"AvailabilityZone": "us-east-1a"},
                "State": {"Name": "running"},
                "Tags": [{"Key": "Name", "Value": "test-instance"}]
            }

            # Act
            result = _structure_resource_data(resource, "123456789012")

            # Assert
            assert result["resource_id"] == "i-123"
            assert result["availability_zone"] == "us-east-1a"
            assert result["state"] == "running"
            assert result["action_status"] == "executed"
            assert len(result["tags"]) == 1
            assert result["tags"][0]["key"] == "Name"

        def test_structure_resource_data_exception_fallback(self):
            """VH-014: 構造化中の例外時にフォールバック値が返る"""
            # Arrange — Tagsが不正な型でも外側のtry/exceptでcatch
            # _extract_primary_resource_idが例外を起こすデータ
            # 実際にはresource自体がdictなら例外は起きにくいが、
            # _build_resource_arn_safelyで例外が起きるケースを想定
            # → _structure_resource_dataは全体をtry/exceptで囲んでいるため
            #   内部関数の例外は捕捉される

            # _extract_primary_resource_id側で例外を起こすにはresource.items()が失敗する必要があるが
            # dictであれば失敗しない。ここではmockを使用
            from unittest.mock import patch
            with patch(
                "app.jobs.utils.v2_hierarchical_helpers._extract_primary_resource_id",
                side_effect=RuntimeError("test error")
            ):
                # Act
                result = _structure_resource_data({"key": "value"}, "123")

            # Assert
            assert result["resource_id"] == "unknown"
            assert result["action_status"] == "failed"
            assert result["resource_data"] == {"key": "value"}

    class TestDocumentBuilders:
        """ドキュメント構築"""

        def test_build_error_empty_and_error_policy_document(self):
            """VH-015: エラー/空/エラーポリシードキュメントの構造を検証"""
            # Act
            error_doc = _build_error_document("scan-1", "acc-1", "aws", "test error")
            empty_doc = _build_empty_document("scan-1", "acc-1", "aws")
            error_policy = _build_error_policy("test-policy", "parse error")

            # Assert — error_doc
            assert error_doc["doc_type"] == "hierarchical_scan_result_v2_error"
            assert error_doc["scan_summary"]["error_message"] == "test error"
            assert error_doc["scan_summary"]["total_policies"] == 0

            # Assert — empty_doc
            assert empty_doc["doc_type"] == "hierarchical_scan_result_v2"
            assert "error_message" not in empty_doc["scan_summary"]

            # Assert — error_policy
            assert error_policy["policy_name"] == "test-policy"
            assert error_policy["policy_status"] == "failed"
            assert error_policy["resource_type"] == "unknown"
            assert error_policy["execution_details"]["error_type"] == "processing_error"
            assert error_policy["execution_details"]["error_message"] == "parse error"
            assert error_policy["resources_by_region"] == []

    class TestFileLoaders:
        """ファイル読み込み関数"""

        def test_load_metadata_safely_exists_and_not_exists(self):
            """VH-016: メタデータファイルの正常読み込みと不存在"""
            from unittest.mock import patch, mock_open

            # --- 正常読み込み ---
            # Arrange
            with patch("app.jobs.utils.v2_hierarchical_helpers.os.path.exists", return_value=True), \
                 patch("builtins.open", mock_open()), \
                 patch("app.jobs.utils.v2_hierarchical_helpers.json.load",
                        return_value={"policy": {"resource": "aws.ec2"}}):
                # Act
                result = _load_metadata_safely("/path/to/metadata.json")

            # Assert
            assert result == {"policy": {"resource": "aws.ec2"}}

            # --- ファイル不存在 ---
            with patch("app.jobs.utils.v2_hierarchical_helpers.os.path.exists", return_value=False):
                result_missing = _load_metadata_safely("/nonexistent/metadata.json")

            assert result_missing == {}

        def test_load_resources_safely_list_and_non_list(self):
            """VH-017: リソースファイルのlist/非listデータ処理"""
            from unittest.mock import patch, mock_open

            # --- 正常（list） ---
            with patch("app.jobs.utils.v2_hierarchical_helpers.os.path.exists", return_value=True), \
                 patch("builtins.open", mock_open()), \
                 patch("app.jobs.utils.v2_hierarchical_helpers.json.load",
                        return_value=[{"InstanceId": "i-1"}]):
                result_list = _load_resources_safely("/path/to/resources.json")
            assert result_list == [{"InstanceId": "i-1"}]

            # --- 非list（dict） → 空リスト ---
            with patch("app.jobs.utils.v2_hierarchical_helpers.os.path.exists", return_value=True), \
                 patch("builtins.open", mock_open()), \
                 patch("app.jobs.utils.v2_hierarchical_helpers.json.load",
                        return_value={"key": "value"}):
                result_non_list = _load_resources_safely("/path/to/resources.json")
            assert result_non_list == []

        def test_load_error_info_safely_found_and_empty(self):
            """VH-018: エラーログファイルの検出と空ディレクトリ"""
            from unittest.mock import patch, mock_open

            # --- custodian.log検出 ---
            def mock_exists(path):
                return path.endswith("custodian.log")

            with patch("app.jobs.utils.v2_hierarchical_helpers.os.path.exists", side_effect=mock_exists), \
                 patch("app.jobs.utils.v2_hierarchical_helpers.os.path.join",
                        side_effect=lambda d, f: f"{d}/{f}"), \
                 patch("builtins.open", mock_open(read_data="ERROR: Permission denied")):
                result = _load_error_info_safely("/policy/dir")

            assert result["error_log"] == "ERROR: Permission denied"
            assert result["source_file"] == "custodian.log"

            # --- エラーファイルなし ---
            with patch("app.jobs.utils.v2_hierarchical_helpers.os.path.exists", return_value=False), \
                 patch("app.jobs.utils.v2_hierarchical_helpers.os.path.join",
                        side_effect=lambda d, f: f"{d}/{f}"):
                result_none = _load_error_info_safely("/empty/dir")
            assert result_none is None

    class TestStatusAndExecution:
        """ステータス判定・実行詳細"""

        def test_extract_resource_type_and_policy_status(self):
            """VH-019: リソースタイプ抽出とポリシーステータス判定"""
            # Arrange & Act — resource_type
            meta_policy = {"policy": {"resource": "aws.ec2"}}
            meta_type = {"type": "s3"}
            meta_empty = {}

            assert _extract_resource_type_from_metadata(meta_policy) == "aws.ec2"
            assert _extract_resource_type_from_metadata(meta_type) == "s3"
            assert _extract_resource_type_from_metadata(meta_empty) == "unknown"

            # Act — policy_status
            assert _determine_policy_status([{"id": 1}], {"error_log": "err"}) == "partial_success"
            assert _determine_policy_status([], {"error_log": "err"}) == "failed"
            assert _determine_policy_status([{"id": 1}], None) == "success"
            assert _determine_policy_status([], None) == "partial_success"

        def test_build_execution_details_with_statistics(self):
            """VH-020: statistics有り時の実行詳細構築"""
            # Arrange
            resources = [{"InstanceId": "i-1"}, {"InstanceId": "i-2"}]
            statistics = {
                "total_resources_scanned": 10,
                "resources_after_filter": 3,
                "violation_count": 2
            }

            # Act
            result = _build_execution_details(resources, None, statistics)

            # Assert
            assert result["compliance_status"] == "has_violations"
            assert result["resources_scanned"] == 10
            assert result["resources_after_filter"] == 3
            assert result["violation_count"] == 2
            assert result["action_execution"] == "completed"

        def test_build_execution_details_four_compliance_states(self):
            """VH-021: compliance_statusの4状態を検証"""
            # error: error_info有り
            result_error = _build_execution_details(
                [], {"error_log": "test error"}, {"total_resources_scanned": 5, "resources_after_filter": 0, "violation_count": 0}
            )
            assert result_error["compliance_status"] == "error"
            assert result_error["error_type"] == "unknown_error"

            # no_resources: scanned=0
            result_no_res = _build_execution_details(
                [], None, {"total_resources_scanned": 0, "resources_after_filter": 0, "violation_count": 0}
            )
            assert result_no_res["compliance_status"] == "no_resources"

            # has_violations: violation_count > 0
            result_violations = _build_execution_details(
                [{"id": "r1"}], None, {"total_resources_scanned": 10, "resources_after_filter": 1, "violation_count": 1}
            )
            assert result_violations["compliance_status"] == "has_violations"

            # no_match: scanned > 0, violations = 0
            result_no_match = _build_execution_details(
                [], None, {"total_resources_scanned": 10, "resources_after_filter": 0, "violation_count": 0}
            )
            assert result_no_match["compliance_status"] == "no_match"

        def test_classify_error_type_five_categories(self):
            """VH-022: 5種類のエラータイプ分類"""
            # Act & Assert
            assert _classify_error_type("Access Denied: Permission error") == "permission_error"
            assert _classify_error_type("Invalid configuration file") == "config_error"
            assert _classify_error_type("Request timeout after 30s") == "timeout_error"
            assert _classify_error_type("Network connection refused") == "network_error"
            assert _classify_error_type("Something unexpected happened") == "unknown_error"

    class TestResourceExtractors:
        """リソース情報抽出"""

        def test_extract_region_and_primary_id(self):
            """VH-023: リージョン抽出とプライマリID抽出のフォールバック"""
            # region — 直接フィールド
            assert _extract_region_from_resource({"Region": "us-east-1"}) == "us-east-1"
            # region — AZ → リージョン
            assert _extract_region_from_resource({"AvailabilityZone": "eu-west-1a"}) == "eu-west-1"
            # region — Placement.AZ（ネストキー）
            assert _extract_region_from_resource(
                {"Placement": {"AvailabilityZone": "ap-northeast-1c"}}
            ) == "ap-northeast-1"
            # region — fallback
            assert _extract_region_from_resource({}) == "unknown-region"

            # primary_id — InstanceId
            assert _extract_primary_resource_id({"InstanceId": "i-123"}) == "i-123"
            # primary_id — VolumeId
            assert _extract_primary_resource_id({"VolumeId": "vol-456"}) == "vol-456"
            # primary_id — *Id fallback（キー名に"Id"を含む → L341-342で検出）
            assert _extract_primary_resource_id({"CustomId": "custom-1"}) == "custom-1"
            # primary_id — unknown（キー名に"Id"を含まない）
            assert _extract_primary_resource_id({"other": "value"}) == "unknown-id"

        def test_build_arn_extract_state_structure_tags(self):
            """VH-024: ARN構築/状態抽出/タグ構造化"""
            # --- ARN: 既存Arnフィールド ---
            assert _build_resource_arn_safely(
                {"InstanceArn": "arn:aws:ec2:us-east-1:123:instance/i-1"}, "123"
            ) == "arn:aws:ec2:us-east-1:123:instance/i-1"
            # --- ARN: EC2構築 ---
            ec2_arn = _build_resource_arn_safely(
                {"InstanceId": "i-999", "Placement": {"AvailabilityZone": "us-west-2a"}}, "111"
            )
            assert ec2_arn == "arn:aws:ec2:us-west-2:111:instance/i-999"
            # --- ARN: S3構築 ---
            s3_arn = _build_resource_arn_safely(
                {"Name": "my-bucket", "CreationDate": "2024-01-01"}, "111"
            )
            assert s3_arn == "arn:aws:s3:::my-bucket"
            # --- ARN: SG → None ---
            assert _build_resource_arn_safely({"GroupId": "sg-1"}, "111") is None

            # --- state: State.Name ---
            assert _extract_resource_state({"State": {"Name": "running"}}) == "running"
            # --- state: State文字列 ---
            assert _extract_resource_state({"State": "available"}) == "available"
            # --- state: unknown ---
            assert _extract_resource_state({}) == "unknown"

            # --- tags: 正常リスト ---
            tags = _structure_tags({"Tags": [{"Key": "env", "Value": "prod"}]})
            assert tags == [{"key": "env", "value": "prod"}]
            # --- tags: 非リスト → 空 ---
            assert _structure_tags({"Tags": "invalid"}) == []
            # --- tags: Tags無し → 空 ---
            assert _structure_tags({}) == []
```

### TestResourceIdExtractor

```python
class TestResourceIdExtractor:
    """resource_id_extractor.py のテスト"""

    class TestExtractResourceId:
        """5段階フォールバックID抽出"""

        def test_step1_priority_field_pattern(self):
            """VH-025: ステップ1 リソースタイプ別優先フィールド"""
            # Arrange
            resource = {"InstanceId": "i-abc123", "OtherId": "other"}

            # Act
            result = extract_resource_id(resource, "aws.ec2")

            # Assert
            assert result["primary_id"] == "i-abc123"
            assert result["method"] == "priority_field_pattern"
            assert result["field_used"] == "InstanceId"
            assert result["confidence"] == "high"

        def test_step2_id_suffix_pattern(self):
            """VH-026: ステップ2 "Id"サフィックスパターン"""
            # Arrange — aws.unknown には優先フィールドなし
            resource = {"CustomId": "custom-001", "LongNameId": "long-id"}

            # Act
            result = extract_resource_id(resource, "aws.unknown")

            # Assert
            assert result["primary_id"] == "custom-001"  # 最短名のIdフィールド
            assert result["method"] == "id_suffix_pattern"

        def test_step3_name_and_step4_arn(self):
            """VH-027: ステップ3 Nameパターン + ステップ4 ARN抽出"""
            # --- ステップ3: Name ---
            name_result = extract_resource_id({"Name": "my-bucket"}, "aws.unknown")
            assert name_result["primary_id"] == "my-bucket"
            assert name_result["method"] == "name_pattern"

            # --- ステップ4: ARN ---
            arn_result = extract_resource_id(
                {"ResourceArn": "arn:aws:ec2:us-east-1:123:instance/i-456"}, "aws.unknown"
            )
            assert arn_result["primary_id"] == "i-456"
            assert arn_result["method"] == "arn_extraction"
            assert arn_result["confidence"] == "medium"

        def test_step5_identifier_and_fallback(self):
            """VH-028: ステップ5 Identifierパターン + フォールバック"""
            # --- Identifier ---
            id_result = extract_resource_id(
                {"DBInstanceIdentifier": "mydb-01"}, "aws.unknown"
            )
            assert id_result["primary_id"] == "mydb-01"
            assert id_result["method"] == "identifier_pattern"

            # --- フォールバック: 全ステップ失敗 ---
            fallback = extract_resource_id({}, "aws.unknown")
            assert fallback["primary_id"] == "unknown"
            assert fallback["method"] == "failed"
            assert fallback["confidence"] == "low"

    class TestDisplayNameAndArn:
        """表示名・ARN関連"""

        def test_extract_display_name_tags_priority(self):
            """VH-029: Tags Nameタグが最優先される"""
            # Arrange
            resource = {
                "Tags": [{"Key": "Name", "Value": "my-instance"}, {"Key": "Env", "Value": "prod"}],
                "InstanceType": "t3.micro"
            }

            # Act
            result = extract_display_name(resource, "aws.ec2")

            # Assert
            assert result == "my-instance"

        def test_extract_display_name_type_specific_field(self):
            """VH-030: Nameタグなし時のタイプ別フィールド"""
            # Arrange
            sg_resource = {"GroupName": "my-security-group", "Description": "Test SG"}

            # Act
            result = extract_display_name(sg_resource, "aws.security-group")

            # Assert
            assert result == "my-security-group"

        def test_extract_resource_arn_parsing(self):
            """VH-031: ARN文字列からリソースID部分を抽出"""
            # スラッシュ区切り
            assert extract_resource_arn(
                "arn:aws:ec2:us-east-1:123:instance/i-abc"
            ) == "i-abc"
            # スラッシュなし（コロン区切りの末尾）
            assert extract_resource_arn(
                "arn:aws:s3:::my-bucket"
            ) == "my-bucket"
            # 不正入力
            assert extract_resource_arn(None) == "unknown"
            assert extract_resource_arn("") == "unknown"
            # 短いARN（5パーツ未満）
            assert extract_resource_arn("short:arn") == "short:arn"

        def test_get_priority_id_fields_normalization(self):
            """VH-032: リソースタイプ正規化とフィールドマッピング"""
            # 通常タイプ
            assert _get_priority_id_fields("aws.ec2") == ["InstanceId"]
            assert _get_priority_id_fields("aws.s3") == ["Name"]
            # 重複プレフィックス正規化: aws.aws.ec2 → aws.ec2
            assert _get_priority_id_fields("aws.aws.ec2") == ["InstanceId"]
            # 未知タイプ
            assert _get_priority_id_fields("aws.unknown") == []

        def test_get_resource_summary(self):
            """VH-033: リソース要約情報の全フィールド"""
            # Arrange
            resource = {
                "InstanceId": "i-abc",
                "Tags": [{"Key": "Name", "Value": "test-inst"}],
                "InstanceArn": "arn:aws:ec2:us-east-1:123:instance/i-abc"
            }

            # Act
            result = get_resource_summary(resource, "aws.ec2")

            # Assert
            assert result["primary_id"] == "i-abc"
            assert result["display_name"] == "test-inst"
            assert result["extraction_method"] == "priority_field_pattern"
            assert result["arn"] == "arn:aws:ec2:us-east-1:123:instance/i-abc"

    class TestArnBuilding:
        """ARN構築ロジック"""

        def test_build_resource_arn_existing_and_built(self):
            """VH-034: 既存ARNの優先利用とARN構築"""
            # --- 既存ARN ---
            result_existing = build_resource_arn(
                {"Arn": "arn:aws:ec2:us-east-1:123:instance/i-1"}, "aws.ec2"
            )
            assert result_existing == "arn:aws:ec2:us-east-1:123:instance/i-1"

            # --- 構築（account_id, region提供） ---
            result_built = build_resource_arn(
                {"InstanceId": "i-999"}, "aws.ec2",
                account_id="111222333444", region="us-west-2"
            )
            assert result_built == "arn:aws:ec2:us-west-2:111222333444:instance/i-999"

        def test_sanitize_arn_for_document_id(self):
            """VH-035: ARNサニタイズ（特殊文字変換・長さ制限）"""
            # --- 特殊文字変換 ---
            result = sanitize_arn_for_document_id("arn:aws:ec2:us-east-1:123:instance/i-abc")
            assert ":" not in result
            assert "/" not in result
            assert result == "arn_aws_ec2_us-east-1_123_instance_i-abc"

            # --- 無効入力 ---
            assert sanitize_arn_for_document_id(None) == "invalid_arn"
            assert sanitize_arn_for_document_id("") == "invalid_arn"

            # --- 長大ARN（512文字超）→ ハッシュ短縮 ---
            long_arn = "arn:aws:ec2:us-east-1:123456789012:instance/" + "x" * 500
            result_long = sanitize_arn_for_document_id(long_arn)
            assert len(result_long) <= 512
            # ハッシュサフィックスの存在確認（末尾16文字がhex）
            hash_part = result_long.split("_")[-1]
            assert len(hash_part) == 16

        def test_extract_existing_arn_account_region(self):
            """VH-036: 既存ARN/アカウントID/リージョン抽出"""
            # --- _extract_existing_arn: 直接フィールド ---
            assert _extract_existing_arn(
                {"Arn": "arn:aws:ec2:us-east-1:123:instance/i-1"}
            ) == "arn:aws:ec2:us-east-1:123:instance/i-1"
            # --- _extract_existing_arn: ネストオブジェクト ---
            assert _extract_existing_arn(
                {"Profile": {"Arn": "arn:aws:iam::123:role/test"}}
            ) == "arn:aws:iam::123:role/test"
            # --- _extract_existing_arn: なし ---
            assert _extract_existing_arn({"key": "value"}) is None

            # --- _extract_account_id ---
            assert _extract_account_id({"OwnerId": "123456789012"}) == "123456789012"
            assert _extract_account_id({}) is None

            # --- _extract_region ---
            assert _extract_region({"AvailabilityZone": "us-east-1a"}) == "us-east-1"
            assert _extract_region(
                {"Placement": {"AvailabilityZone": "eu-west-1b"}}
            ) == "eu-west-1"
            assert _extract_region({}) is None

        def test_build_arn_by_resource_type_all_types(self):
            """VH-037: 全リソースタイプのARNフォーマット"""
            # Arrange
            args = ("us-east-1", "123456789012", "res-id", {})

            # Act & Assert
            assert _build_arn_by_resource_type("aws.ec2", *args) == \
                "arn:aws:ec2:us-east-1:123456789012:instance/res-id"
            assert _build_arn_by_resource_type("aws.ebs", *args) == \
                "arn:aws:ec2:us-east-1:123456789012:volume/res-id"
            assert _build_arn_by_resource_type("aws.security-group", *args) == \
                "arn:aws:ec2:us-east-1:123456789012:security-group/res-id"
            # S3: リージョンレス
            assert _build_arn_by_resource_type("aws.s3", *args) == \
                "arn:aws:s3:::res-id"
            # IAM: リージョンレス + RoleName優先
            assert _build_arn_by_resource_type(
                "aws.iam", "us-east-1", "123", "res-id", {"RoleName": "my-role"}
            ) == "arn:aws:iam::123:role/my-role"
            # Lambda
            assert _build_arn_by_resource_type("aws.lambda", *args) == \
                "arn:aws:lambda:us-east-1:123456789012:function:res-id"
            # RDS
            assert _build_arn_by_resource_type("aws.rds", *args) == \
                "arn:aws:rds:us-east-1:123456789012:db:res-id"
            # VPC
            assert _build_arn_by_resource_type("aws.vpc", *args) == \
                "arn:aws:ec2:us-east-1:123456789012:vpc/res-id"
            # aws.aws.ec2 → 正規化
            assert _build_arn_by_resource_type("aws.aws.ec2", *args) == \
                "arn:aws:ec2:us-east-1:123456789012:instance/res-id"
            # 未知タイプ → 汎用フォーマット
            assert _build_arn_by_resource_type("aws.custom", *args) == \
                "arn:aws:custom:us-east-1:123456789012:res-id"
```

### TestV2FormatLegacyFunctions

```python
class TestV2FormatLegacyFunctions:
    """v2_format_legacy_functions.py のテスト

    注記: v2_format_helpers.py と resource_id_extractor.py は同一仕様書
    スコープ内のためモックせず、実装を直接利用する。
    """

    class TestResourceContext:
        """リソース・セキュリティコンテキスト"""

        def test_extract_resource_context_ec2(self):
            """VH-038: EC2タイプのリソースコンテキスト抽出"""
            # Arrange
            resource = {
                "VpcId": "vpc-123",
                "InstanceType": "t3.micro",
                "Tags": [{"Key": "env", "Value": "prod"}]
            }

            # Act
            result = extract_resource_context(resource, "aws.ec2")

            # Assert
            assert result["vpc_id"] == "vpc-123"
            assert result["instance_type"] == "t3.micro"
            assert "tags" in result  # add_common_attributesで追加

        def test_extract_resource_context_validation_and_generic(self):
            """VH-039: 入力検証と汎用タイプの処理"""
            # --- 入力検証: 空データ ---
            result_empty = extract_resource_context({}, "aws.ec2")
            assert "extraction_error" in result_empty

            # --- 入力検証: 空タイプ ---
            result_no_type = extract_resource_context({"key": "val"}, "")
            assert "extraction_error" in result_no_type

            # --- EBSタイプ ---
            ebs_resource = {"Size": 100, "VolumeType": "gp3", "State": "available"}
            result_ebs = extract_resource_context(ebs_resource, "aws.ebs")
            assert result_ebs["size_gb"] == 100
            assert result_ebs["volume_type"] == "gp3"

            # --- SGタイプ ---
            sg_resource = {"GroupName": "test-sg", "VpcId": "vpc-1", "IpPermissions": []}
            result_sg = extract_resource_context(sg_resource, "aws.security-group")
            assert result_sg["group_name"] == "test-sg"

            # --- 汎用タイプ ---
            resource = {"State": "active", "Size": 100}
            result_generic = extract_resource_context(resource, "aws.custom-type")
            assert result_generic["state"] == "active"
            assert result_generic["size"] == 100

        def test_extract_security_context_s3_ec2(self):
            """VH-040: S3/EC2のセキュリティコンテキスト"""
            # --- S3 ---
            s3_resource = {
                "Acl": {"Owner": {"DisplayName": "admin"}},
                "Versioning": {"Status": "Enabled"}
            }
            s3_ctx = extract_security_context(s3_resource, "aws.s3")
            assert s3_ctx["encryption_enabled"] is False  # S3はデフォルトFalse
            assert s3_ctx["bucket_owner"] == "admin"
            assert s3_ctx["versioning_enabled"] is True

            # --- EC2 ---
            ec2_resource = {
                "PublicIpAddress": "54.1.2.3",
                "MetadataOptions": {"HttpTokens": "required", "HttpEndpoint": "enabled"},
                "SecurityGroups": [{"GroupId": "sg-1"}]
            }
            ec2_ctx = extract_security_context(ec2_resource, "aws.ec2")
            assert ec2_ctx["public_access"] is True
            assert ec2_ctx["imds_v2_required"] is True
            assert ec2_ctx["security_groups"] == ["sg-1"]

    class TestResourceIdentity:
        """リソース識別・違反コンテキスト"""

        def test_build_resource_identity_normal(self):
            """VH-041: リソース識別情報の正常構築"""
            # Arrange
            resource = {"InstanceId": "i-abc123"}

            # Act
            result = _build_resource_identity(
                resource, "aws.ec2", "123456789012", "us-east-1"
            )

            # Assert
            assert result["primary_id"] == "i-abc123"
            assert result["resource_type"] == "aws.ec2"
            assert result["extraction_metadata"]["method"] == "priority_field_pattern"
            assert result["extraction_metadata"]["confidence"] == "high"

        def test_build_violation_context_v2_filter_values(self):
            """VH-042: 違反コンテキストのフィルター値抽出"""
            # Arrange
            resource = {
                "c7n:MatchedFilters": ["State.Name"],
                "State": {"Name": "running"}
            }

            # Act
            result = _build_violation_context_v2(
                "scan-1", "security-policy", resource, "Check running instances"
            )

            # Assert
            assert result["scan_id"] == "scan-1"
            assert result["matched_filters"] == ["State.Name"]
            assert result["filter_values"]["State.Name"] == "running"
            assert result["policy_metadata"]["severity"] == "high"  # "security"含む
            assert result["policy_metadata"]["description"] == "Check running instances"

    class TestResourceSnapshot:
        """リソーススナップショット"""

        def test_create_resource_snapshot_five_types(self):
            """VH-043: 5タイプのリソーススナップショット分岐"""
            # EC2
            ec2_snap = _create_resource_snapshot(
                {"State": {"Name": "running"}, "InstanceType": "t3.micro"}, "aws.ec2"
            )
            assert ec2_snap["state"] == "running"
            assert ec2_snap["instance_type"] == "t3.micro"

            # S3
            s3_snap = _create_resource_snapshot({"Name": "bucket-1"}, "aws.s3")
            assert s3_snap["name"] == "bucket-1"

            # EBS
            ebs_snap = _create_resource_snapshot(
                {"State": "available", "Size": 100, "Encrypted": True}, "aws.ebs"
            )
            assert ebs_snap["state"] == "available"
            assert ebs_snap["encrypted"] is True

            # SG
            sg_snap = _create_resource_snapshot(
                {"GroupName": "sg-1", "VpcId": "vpc-1"}, "aws.security-group"
            )
            assert sg_snap["group_name"] == "sg-1"

            # Generic
            generic_snap = _create_resource_snapshot(
                {"Name": "res-1", "Status": "active"}, "aws.custom"
            )
            assert generic_snap["name"] == "res-1"
            assert generic_snap["status"] == "active"

        def test_create_ec2_s3_snapshot_details(self):
            """VH-044: EC2/S3スナップショットの詳細フィールド"""
            # --- EC2 ---
            ec2_data = {
                "State": {"Name": "running"},
                "LaunchTime": "2024-01-01T00:00:00Z",
                "InstanceType": "t3.micro",
                "Tags": [{"Key": "Name", "Value": "test"}],
                "SecurityGroups": [{"GroupId": "sg-1"}, {"GroupId": "sg-2"}],
                "VpcId": "vpc-123",
                "SubnetId": "subnet-456",
                "PublicIpAddress": "54.1.2.3",
                "PrivateIpAddress": "10.0.0.1"
            }
            ec2_snap = _create_resource_snapshot(ec2_data, "aws.ec2")
            assert ec2_snap["state"] == "running"
            assert ec2_snap["tags"] == {"Name": "test"}
            assert ec2_snap["security_groups"] == ["sg-1", "sg-2"]
            assert ec2_snap["public_ip"] == "54.1.2.3"

            # --- S3 ---
            s3_data = {
                "Name": "my-bucket",
                "CreationDate": "2024-01-01",
                "Location": {"LocationConstraint": "us-east-1"},
                "Versioning": {"Status": "Enabled"},
                "Encryption": {"Rules": [{"ApplyServerSideEncryptionByDefault": {}}]}
            }
            s3_snap = _create_resource_snapshot(s3_data, "aws.s3")
            assert s3_snap["name"] == "my-bucket"
            assert s3_snap["location"] == "us-east-1"
            assert s3_snap["versioning"] == "Enabled"
            assert len(s3_snap["encryption"]) == 1
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| VH-E01 | extract_resource_id 例外ハンドリング | 例外発生データ | primary_id="error", method="exception_occurred" |
| VH-E02 | _build_execution_details 例外 | 内部処理例外 | compliance_status="error", error_type="processing_error" |
| VH-E03 | build_resource_arn 情報不足 | account/region/id不明 | None |
| VH-E04 | _load_metadata_safely JSON解析例外 | 不正JSONファイル | {} |
| VH-E05 | _build_execution_details statistics=None フォールバック | resources=[], error_info=None, statistics=None | L227 TypeError → L259 except → compliance_status="error", error_type="processing_error" |

```python
class TestV2HelpersErrors:
    """異常系テスト"""

    def test_extract_resource_id_exception(self):
        """VH-E01: extract_resource_idの例外ハンドリング"""
        from unittest.mock import patch

        # Arrange — _get_priority_id_fieldsが例外を投げるケース
        with patch(
            "app.jobs.utils.resource_id_extractor._get_priority_id_fields",
            side_effect=RuntimeError("unexpected error")
        ):
            # Act
            result = extract_resource_id({"InstanceId": "i-1"}, "aws.ec2")

        # Assert
        assert result["primary_id"] == "error"
        assert result["method"] == "exception_occurred"
        assert result["confidence"] == "low"

    def test_build_execution_details_exception(self):
        """VH-E02: _build_execution_detailsの例外時フォールバック"""
        from unittest.mock import patch

        # Arrange — statistics.getが例外を投げる
        with patch(
            "app.jobs.utils.v2_hierarchical_helpers._classify_error_type",
            side_effect=RuntimeError("classify error")
        ):
            # Act — error_info有りのパスで_classify_error_typeが例外
            result = _build_execution_details(
                [], {"error_log": "test"}, None
            )

        # Assert
        assert result["compliance_status"] == "error"
        assert result["error_type"] == "processing_error"
        assert "classify error" in result["error_message"]

    def test_build_resource_arn_insufficient_info(self):
        """VH-E03: ARN構築に必要な情報が不足"""
        # Arrange — account_id, region, resource_id全て不明
        result = build_resource_arn({}, "aws.ec2")

        # Assert
        assert result is None

    def test_build_execution_details_none_statistics_fallback(self):
        """VH-E05: statistics=None, resources=[], error_info=None → L227 TypeError → except フォールバック"""
        # Arrange — 既知不具合 L227 の再現条件
        # statistics=None → resources_scanned=None (L213)
        # resources=[] → violation_count=0 (L215)
        # error_info=None → L219 スキップ
        # L221: None is not None → False → スキップ
        # L224: 0 > 0 → False → スキップ
        # L227: None > 0 → TypeError!
        # → L259 except Exception でキャッチ → processing_error として返却

        # Act
        result = _build_execution_details([], None, None)

        # Assert — TypeError は L259 except でキャッチされ、エラー辞書が返る
        assert result["compliance_status"] == "error"
        assert result["error_type"] == "processing_error"
        assert result["error_message"]  # エラーメッセージが非空であること

    def test_load_metadata_safely_json_error(self):
        """VH-E04: JSON解析エラー時の安全なフォールバック"""
        from unittest.mock import patch, mock_open

        # Arrange
        with patch("app.jobs.utils.v2_hierarchical_helpers.os.path.exists", return_value=True), \
             patch("builtins.open", mock_open()), \
             patch("app.jobs.utils.v2_hierarchical_helpers.json.load",
                    side_effect=ValueError("Invalid JSON")):
            # Act
            result = _load_metadata_safely("/path/to/invalid.json")

        # Assert
        assert result == {}
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 検証内容 | 期待結果 |
|----|---------|---------|---------|
| VH-SEC-01 | sanitize_arn_for_document_id インジェクション防止 | HTML特殊文字・メタ文字入力 | 置換対象（`:`,`/`,`*`,`?`）のみ置換。`<`,`>`,`&` は非置換 |
| VH-SEC-02 | _build_execution_details エラー長制限 | 1000文字超エラーメッセージ | 500文字で切り詰め |
| VH-SEC-03 | _load_error_info_safely ファイルパス制約 | 固定ファイル名リスト | 任意ファイル読み取り不可 |

```python
@pytest.mark.security
class TestV2HelpersSecurity:
    """セキュリティテスト"""

    def test_sanitize_arn_injection_prevention(self):
        """VH-SEC-01: OpenSearchドキュメントIDインジェクション防止"""
        # Arrange — 特殊文字を含むARN
        malicious_arn = "arn:aws:ec2:*:?:instance/<script>alert(1)&amp;</script>"

        # Act
        result = sanitize_arn_for_document_id(malicious_arn)

        # Assert — L356の置換対象（:, /, *, ?）が全て置換されている
        assert ":" not in result
        assert "/" not in result
        assert "*" not in result
        assert "?" not in result
        # Assert — <, >, & はサニタイズ対象外（L356の置換リストに含まれない）
        # OpenSearchドキュメントIDとしては問題ないが、
        # 表示時のXSSリスクは呼び出し元で対応する必要あり
        assert "<script>" in result  # HTMLタグは保持される（残留リスク）
        assert "&" in result  # アンパサンドも保持される（残留リスク）

    def test_build_execution_details_error_truncation(self):
        """VH-SEC-02: エラーメッセージの500文字切り詰め"""
        # Arrange
        long_error = "A" * 1000
        error_info = {"error_log": long_error}

        # Act
        result = _build_execution_details([], error_info, None)

        # Assert — error_message[:500]で切り詰め
        assert len(result["error_message"]) == 500
        assert result["error_message"] == "A" * 500

    def test_load_error_info_safely_fixed_filenames(self):
        """VH-SEC-03: エラーファイル名が固定リストに制限されている"""
        from unittest.mock import patch, call

        # Arrange
        calls_made = []
        def track_exists(path):
            calls_made.append(path)
            return False

        # Act
        with patch("app.jobs.utils.v2_hierarchical_helpers.os.path.exists",
                    side_effect=track_exists), \
             patch("app.jobs.utils.v2_hierarchical_helpers.os.path.join",
                    side_effect=lambda d, f: f"{d}/{f}"):
            _load_error_info_safely("/policy/dir")

        # Assert — 固定3ファイルのみチェックされる
        expected_files = [
            "/policy/dir/custodian.log",
            "/policy/dir/error.log",
            "/policy/dir/stderr.log"
        ]
        assert calls_made == expected_files
        # 任意のファイル名（例: /etc/passwd）は読み取られない
```

---

## 5. フィクスチャ定義

| フィクスチャ名 | スコープ | 用途 |
|---------------|---------|------|
| `reset_utils_module` | function (autouse) | `sys.modules` から `app.jobs.utils` 配下をクリア |
| `sample_ec2_resource` | function | EC2テストデータ |
| `sample_s3_resource` | function | S3テストデータ |

```python
# test/unit/jobs/utils/conftest.py（追記分）
import sys
import pytest


@pytest.fixture(autouse=True)
def reset_utils_module():
    """テスト間のモジュール状態汚染を防止"""
    yield
    # app.jobs.utils 配下のモジュールキャッシュをクリア
    keys_to_remove = [k for k in sys.modules if k.startswith("app.jobs.utils")]
    for key in keys_to_remove:
        del sys.modules[key]


@pytest.fixture
def sample_ec2_resource():
    """標準的なEC2インスタンスデータ"""
    return {
        "InstanceId": "i-0abc123def456",
        "InstanceType": "t3.micro",
        "VpcId": "vpc-123",
        "SubnetId": "subnet-456",
        "Placement": {"AvailabilityZone": "us-east-1a"},
        "State": {"Name": "running"},
        "PrivateIpAddress": "10.0.0.1",
        "PublicIpAddress": "54.1.2.3",
        "LaunchTime": "2024-01-01T00:00:00Z",
        "Tags": [{"Key": "Name", "Value": "test-instance"}],
        "SecurityGroups": [{"GroupId": "sg-789"}],
        "OwnerId": "123456789012"
    }


@pytest.fixture
def sample_s3_resource():
    """標準的なS3バケットデータ"""
    return {
        "Name": "my-test-bucket",
        "CreationDate": "2024-01-01T00:00:00Z",
        "Location": {"LocationConstraint": "us-east-1"},
        "Versioning": {"Status": "Enabled"},
        "Acl": {"Owner": {"DisplayName": "admin"}}
    }
```

---

## 6. テスト実行コマンド

```bash
# 全テスト実行
pytest test/unit/jobs/utils/test_v2_format_helpers.py -v

# 正常系のみ（注: "error_response"等の名前を含む正常系テストも除外される場合あり）
pytest test/unit/jobs/utils/test_v2_format_helpers.py -v -k "not Error and not Security"

# セキュリティテストのみ
pytest test/unit/jobs/utils/test_v2_format_helpers.py -v -m security

# カバレッジ計測
pytest test/unit/jobs/utils/test_v2_format_helpers.py --cov=app.jobs.utils.v2_format_helpers --cov=app.jobs.utils.v2_hierarchical_helpers --cov=app.jobs.utils.v2_format_legacy_functions --cov=app.jobs.utils.resource_id_extractor --cov-report=term-missing
```

---

## 7. テストケースサマリー

### 7.1 件数

| カテゴリ | 件数 |
|---------|------|
| 正常系 | 44 |
| 異常系 | 5 |
| セキュリティ | 3 |
| **合計** | **52** |

### 7.2 テストクラス構成

```
TestV2FormatHelpers/
├── TestAttributeExtractors (VH-001 ~ VH-005)     # 5件
├── TestSecurityFunctions (VH-006 ~ VH-009)        # 4件
└── TestUtilityFunctions (VH-010 ~ VH-012)         # 3件

TestV2HierarchicalHelpers/
├── TestResourceStructuring (VH-013 ~ VH-014)      # 2件
├── TestDocumentBuilders (VH-015)                   # 1件
├── TestFileLoaders (VH-016 ~ VH-018)              # 3件
├── TestStatusAndExecution (VH-019 ~ VH-022)       # 4件
└── TestResourceExtractors (VH-023 ~ VH-024)       # 2件

TestResourceIdExtractor/
├── TestExtractResourceId (VH-025 ~ VH-028)        # 4件
├── TestDisplayNameAndArn (VH-029 ~ VH-033)        # 5件
└── TestArnBuilding (VH-034 ~ VH-037)             # 4件

TestV2FormatLegacyFunctions/
├── TestResourceContext (VH-038 ~ VH-040)          # 3件
├── TestResourceIdentity (VH-041 ~ VH-042)        # 2件
└── TestResourceSnapshot (VH-043 ~ VH-044)        # 2件

TestV2HelpersErrors (VH-E01 ~ VH-E05)             # 5件
TestV2HelpersSecurity (VH-SEC-01 ~ VH-SEC-03)     # 3件
```

### 7.3 実装失敗が予想されるテスト

| ID | 理由 | 対応方針 |
|----|------|---------|
| VH-021 (no_match) | `_build_execution_details` L227 `resources_scanned > 0` は **statistics=None かつ resources=[] の場合のみ** `None > 0` で TypeError リスクあり。VH-021のテストでは statistics を明示的に提供しているため失敗しない | VH-E05 で TypeError → except フォールバック動作を検証済み。正常系テストでは statistics 引数を提供して回避 |
| VH-011 (S3 ARN) | `build_simple_arn` で S3 リソースの account_id/region 抽出結果が "unknown" の場合、L278 で None を返す | ARN付きS3データで account_id/region を解決可能にする |

### 7.4 残留リスク

| ID | リスク内容 | 管理方針 |
|----|-----------|---------|
| VH-SEC-01 | `sanitize_arn_for_document_id` は `<`, `>`, `&` 等のHTML特殊文字を置換しない（L356の置換対象は `:`, `/`, `*`, `?` のみ） | OpenSearchドキュメントIDとしては問題なし。表示時のXSS対策は呼び出し元の責務 |

---

## 8. 既知の制約事項

| # | 制約 | 回避策 |
|---|------|--------|
| 1 | `v2_format_legacy_functions.py` のテストは同一仕様書内ファイルをモックしないため、厳密な単体テストではなく薄い結合テストとなる | 入力データの変化で各分岐をカバー。個別関数の単体テストは各ファイルのテストクラスで実施済み |
| 2 | `_build_execution_details` の L227 `resources_scanned > 0` は statistics=None 時に `None > 0` で TypeError リスクあり。ただし L205 の try ブロック内で発生するため L259 except でキャッチされ外部に伝播しない | VH-E05 で TypeError → except フォールバック（processing_error）の動作を検証済み。正常系テスト（VH-019〜VH-022）では statistics を明示的に指定して本来のロジックを検証する |
| 3 | `sanitize_arn_for_document_id` の hashlib 関数内import（L361）はテストで実際のハッシュ値を検証 | hashlib.sha256 の戻り値は決定論的のため再現性あり |
| 4 | `_load_error_info_safely` はエラーファイルの内容全体を読み込む（サイズ制限なし） | `_build_execution_details` の error_content[:500] で切り詰められるが、メモリ上には全文が一時的に保持される |
| 5 | `check_public_access` のS3判定は `'"Principal":"*"'` の文字列一致（L161）であり、JSONの空白差異に影響される | 実運用では `"Principal" : "*"` のように空白が入る可能性あり。より堅牢な判定には JSON パースが必要 |
