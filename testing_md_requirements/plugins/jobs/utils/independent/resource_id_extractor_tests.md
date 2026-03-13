# jobs/utils リソースID抽出 テストケース (#17h-2)

## 1. 概要

Cloud Custodianスキャン結果からAWSリソースIDを汎用的に抽出するモジュール。5段階フォールバック戦略（優先フィールド → Idサフィックス → Name → ARN → Identifier）でリソースIDを特定し、ARN構築・サニタイズ等の補助機能も提供する。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `extract_resource_id` | 5段階フォールバックでリソースID抽出（公開） |
| `extract_display_name` | 人間可読な表示名抽出（公開） |
| `extract_resource_arn` | ARN文字列からリソースID抽出（公開） |
| `get_resource_summary` | リソース要約情報取得（公開） |
| `build_resource_arn` | ARN構築または抽出（公開） |
| `sanitize_arn_for_document_id` | ARNをOpenSearch安全な形式に変換（公開） |
| `_get_priority_id_fields` | リソースタイプ別優先IDフィールド（プライベート） |
| `_extract_existing_arn` | 既存ARNフィールド検索（プライベート） |
| `_extract_account_id` | アカウントID抽出（プライベート） |
| `_extract_region` | リージョン抽出（プライベート） |
| `_build_arn_by_resource_type` | リソースタイプ別ARN構築（プライベート） |

### 1.2 カバレッジ目標: 90%

> **注記**: 純粋関数のみで構成され、外部依存が `logging` のみのため高カバレッジが達成可能。`_build_arn_by_resource_type` の9サービスタイプ分岐は `pytest.mark.parametrize` で効率的にカバーする。

### 1.3 主要ファイル

| ファイル | パス | 行数 |
|---------|------|------|
| テスト対象 | `app/jobs/utils/resource_id_extractor.py` | 466行 |
| テストコード | `test/unit/jobs/utils/test_resource_id_extractor.py` | 新規作成 |
| conftest | `test/unit/jobs/utils/conftest.py`（#17aと共有） |

### 1.4 依存関係

| 依存 | 種類 | パッチ対象 |
|------|------|-----------|
| `logging` | 標準ライブラリ | `logging.getLogger` または `caplog` フィクスチャ |
| `re` | 標準ライブラリ（インポートのみ、未使用） | パッチ不要 |
| `hashlib` | 標準ライブラリ（`sanitize_arn_for_document_id` L361 で遅延import） | パッチ不要 |

> **注記**: 外部サービス接続なし。全関数が純粋関数（`logging` 出力を除く）のため、モックは最小限。セキュリティテストでのログ検証には `caplog` フィクスチャを使用する。

### 1.5 主要分岐マップ

| メソッド | 分岐数 | 主要分岐 |
|---------|--------|---------|
| `extract_resource_id` | 7 | L36 優先フィールド, L48 Idサフィックス, L63 Name, L75 ARN, L90 Identifier, L99 フォールバック, L107 Exception |
| `extract_display_name` | 8 | L130 Tags存在, L132 isinstance(list), L134 tag.get("Key")=="Name", L136 name_value非空, L154-156 タイプ別, L160 フォールバック, L163 外側Exception, L169 内側Exception |
| `extract_resource_arn` | 5 | L184 無効入力, L192+195 スラッシュ有ARN, L192+198 スラッシュ無ARN, L201 短縮ARN, L203 Exception |
| `_get_priority_id_fields` | 2 | L220 aws.aws.正規化, L241 マッピング取得 |
| `get_resource_summary` | 3 | L261 arn_fields有→値取得, L261 arn_fields空→None, L273 Exception |
| `build_resource_arn` | 5 | L309 既存ARN, L323 情報不足→None, L330 構築成功, L332 構築失敗, L337 Exception |
| `sanitize_arn_for_document_id` | 3 | L352 無効入力, L359 長さ超過→ハッシュ短縮, L359 通常 |
| `_extract_existing_arn` | 3 | L374-376 直接フィールド, L381-383 ネストdict, L386 None |
| `_extract_account_id` | 2 | L395-397 フィールド発見, L400 None |
| `_extract_region` | 3 | L406-408 AZ, L413-417 Placement.AZ, L420 None |
| `_build_arn_by_resource_type` | 9 | L438 ec2, L441 ebs, L444 sg, L447 s3, L451 iam, L456 lambda, L459 rds, L462 vpc, L465 else |

> **注記**: 上記50分岐のうち、49分岐はテストで直接カバー（L134 の `tag.get("Key") != "Name"` は RIE-008 内で `{"Key": "Environment"}` タグにより直接経由）。以下の1分岐はテスト対象外として既知制限事項（Section 8 #5）に記録:
> - `extract_display_name` L132: `isinstance(tags, list)` が False のケース（Tags が dict 形式）→ RIE-009/RIE-010 は Tags 非存在のため L132 未到達。専用テスト追加を推奨
>
> `_build_arn_by_resource_type` の9サービスタイプは `pytest.mark.parametrize` で1テスト関数にまとめる。

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| RIE-001 | Step1 優先フィールド抽出 | aws.ec2 + InstanceId | primary_id=InstanceId値, confidence=high |
| RIE-002 | Step2 Idサフィックス（最短選択） | VolumeId + SecurityGroupId | primary_id=VolumeId値（短い方）, confidence=high |
| RIE-003 | Step3 Nameパターン | BucketName | primary_id=BucketName値, confidence=high |
| RIE-004 | Step4 ARN抽出 | ResourceArn | primary_id=ARN末尾, confidence=medium |
| RIE-005 | Step5 Identifierパターン | DBClusterIdentifier | primary_id=Identifier値, confidence=medium |
| RIE-006 | フォールバック（該当なし） | 空dict | primary_id=unknown, confidence=low |
| RIE-007 | c7n:プレフィックス除外 | c7n:MatchedFiltersのみ | c7n:フィールドを無視してフォールバック |
| RIE-008 | Tags Name タグ抽出 | Tags=[{Key:Name, Value:web-server}] | "web-server" |
| RIE-009 | タイプ別表示名フィールド | aws.s3 + Name | Name値 |
| RIE-010 | 表示名フォールバック | 該当フィールドなし | primary_id値 |
| RIE-011 | ARN スラッシュ有 | arn:aws:ec2:...:instance/i-123 | "i-123" |
| RIE-012 | ARN スラッシュ無 | arn:aws:sns:...:my-topic | "my-topic" |
| RIE-013 | 短縮ARN（<6パーツ） | "partial:arn" | そのまま返却 |
| RIE-014 | 無効ARN入力 | None, "", 123 | "unknown" |
| RIE-015 | 既知リソースタイプ | aws.ec2 | ["InstanceId"] |
| RIE-016 | 未知リソースタイプ | aws.unknown | [] |
| RIE-017 | aws.aws.重複プレフィックス | aws.aws.ec2 | ["InstanceId"]（正規化後） |
| RIE-018 | リソース要約（ARNあり） | InstanceId + ResourceArn | 全フィールド揃った辞書 |
| RIE-019 | リソース要約（ARNなし） | InstanceId のみ | arn=None |
| RIE-020 | 既存ARN検出 | Arn="arn:aws:..." | そのまま返却 |
| RIE-021 | ARN構築（ec2） | InstanceId + OwnerId + AZ | arn:aws:ec2:... |
| RIE-022 | ARN構築 情報不足→None | account_id/region不明 | None |
| RIE-023 | ARNサニタイズ 通常 | arn:aws:ec2:us-east-1:123:instance/i-1 | コロン・スラッシュ → _ |
| RIE-024 | ARNサニタイズ 長文（>512） | 513文字ARN | 490文字 + _ + sha256[:16] |
| RIE-025 | _extract_existing_arn 直接フィールド | Arn="arn:aws:..." | ARN文字列 |
| RIE-026 | _extract_existing_arn ネストdict | {"nested": {"Arn": "arn:aws:..."}} | ARN文字列 |
| RIE-027 | _extract_account_id 取得 | OwnerId="123456789012" | "123456789012" |
| RIE-028 | _extract_region AZ直接 | AvailabilityZone="us-east-1a" | "us-east-1" |
| RIE-029 | _extract_region Placement | Placement.AvailabilityZone | リージョン文字列 |
| RIE-030 | _build_arn_by_resource_type 9タイプ | parametrize(9タイプ) | 各サービス固有のARN形式 |
| RIE-031 | _extract_existing_arn フィールドなし | ARNフィールドなしのdict | None |
| RIE-032 | _extract_account_id フィールドなし | 空dict | None |

### 2.1 リソースID抽出テスト

```python
# test/unit/jobs/utils/test_resource_id_extractor.py
import pytest
from app.jobs.utils.resource_id_extractor import (
    extract_resource_id,
    extract_display_name,
    extract_resource_arn,
    get_resource_summary,
    build_resource_arn,
    sanitize_arn_for_document_id,
    _get_priority_id_fields,
    _extract_existing_arn,
    _extract_account_id,
    _extract_region,
    _build_arn_by_resource_type,
)


class TestResourceIdExtraction:
    """extract_resource_id の5段階フォールバック戦略テスト"""

    def test_step1_priority_field(self):
        """RIE-001: リソースタイプ別優先フィールドでID抽出（confidence=high）"""
        # Arrange
        resource_data = {"InstanceId": "i-1234567890abcdef0", "Name": "web-server"}
        resource_type = "aws.ec2"

        # Act
        result = extract_resource_id(resource_data, resource_type)

        # Assert
        assert result["primary_id"] == "i-1234567890abcdef0"
        assert result["method"] == "priority_field_pattern"
        assert result["field_used"] == "InstanceId"
        assert result["confidence"] == "high"

    def test_step2_id_suffix_shortest(self):
        """RIE-002: Idサフィックスパターン（最短フィールド名を選択）"""
        # Arrange
        # 優先フィールドに該当しないリソースタイプで、Id末尾フィールドが複数ある
        resource_data = {
            "VolumeId": "vol-abc",
            "SecurityGroupId": "sg-def",
        }
        resource_type = "aws.unknown"  # 優先マッピングなし

        # Act
        result = extract_resource_id(resource_data, resource_type)

        # Assert
        assert result["primary_id"] == "vol-abc"  # VolumeId（8文字）< SecurityGroupId（15文字）
        assert result["method"] == "id_suffix_pattern"
        assert result["confidence"] == "high"

    def test_step3_name_pattern(self):
        """RIE-003: Nameフィールドパターンでの抽出"""
        # Arrange
        resource_data = {"BucketName": "my-bucket-2024"}
        resource_type = "aws.unknown"

        # Act
        result = extract_resource_id(resource_data, resource_type)

        # Assert
        assert result["primary_id"] == "my-bucket-2024"
        assert result["method"] == "name_pattern"
        assert result["field_used"] == "BucketName"
        assert result["confidence"] == "high"

    def test_step4_arn_extraction(self):
        """RIE-004: ARNフィールドからのID抽出（confidence=medium）"""
        # Arrange
        resource_data = {"ResourceArn": "arn:aws:ec2:us-east-1:123456789012:instance/i-abc123"}
        resource_type = "aws.unknown"

        # Act
        result = extract_resource_id(resource_data, resource_type)

        # Assert
        assert result["primary_id"] == "i-abc123"
        assert result["method"] == "arn_extraction"
        assert result["confidence"] == "medium"

    def test_step5_identifier_pattern(self):
        """RIE-005: Identifierパターンでの抽出（confidence=medium）"""
        # Arrange
        resource_data = {"DBClusterIdentifier": "my-cluster"}
        resource_type = "aws.unknown"

        # Act
        result = extract_resource_id(resource_data, resource_type)

        # Assert
        assert result["primary_id"] == "my-cluster"
        assert result["method"] == "identifier_pattern"
        assert result["confidence"] == "medium"

    def test_fallback_unknown(self):
        """RIE-006: 全ステップ不一致時のフォールバック（confidence=low）"""
        # Arrange
        resource_data = {"some_random_field": "value"}
        resource_type = "aws.unknown"

        # Act
        result = extract_resource_id(resource_data, resource_type)

        # Assert
        assert result["primary_id"] == "unknown"
        assert result["method"] == "failed"
        assert result["field_used"] is None
        assert result["confidence"] == "low"

    def test_c7n_prefix_excluded(self):
        """RIE-007: c7n:プレフィックス付きIdフィールドはStep2から除外される

        resource_id_extractor.py:L46 の `not k.startswith("c7n:")` フィルタをカバー。
        """
        # Arrange
        resource_data = {"c7n:MatchedFiltersId": "filter-1"}
        resource_type = "aws.unknown"

        # Act
        result = extract_resource_id(resource_data, resource_type)

        # Assert
        # c7n:フィールドはStep2で無視され、フォールバックに到達
        assert result["primary_id"] == "unknown"
        assert result["method"] == "failed"
```

### 2.2 表示名抽出テスト

```python
class TestDisplayNameExtraction:
    """extract_display_name のテスト"""

    def test_tags_name_tag(self):
        """RIE-008: TagsリストからNameタグを優先抽出

        resource_id_extractor.py:L130-137 の Tags → Name タグパスをカバー。
        """
        # Arrange
        resource_data = {
            "InstanceId": "i-123",
            "Tags": [
                {"Key": "Environment", "Value": "prod"},
                {"Key": "Name", "Value": "web-server-01"},
            ],
        }

        # Act
        result = extract_display_name(resource_data, "aws.ec2")

        # Assert
        assert result == "web-server-01"

    def test_type_specific_field(self):
        """RIE-009: リソースタイプ別フィールドから表示名取得

        resource_id_extractor.py:L154-157 のタイプ別フィールドパスをカバー。
        """
        # Arrange
        resource_data = {"Name": "my-bucket", "CreationDate": "2024-01-01"}

        # Act
        result = extract_display_name(resource_data, "aws.s3")

        # Assert
        assert result == "my-bucket"

    def test_fallback_to_primary_id(self):
        """RIE-010: タグ・タイプ別フィールドなし → primary IDにフォールバック

        resource_id_extractor.py:L160-161 のフォールバックパスをカバー。
        """
        # Arrange
        resource_data = {"InstanceId": "i-fallback-123"}

        # Act
        result = extract_display_name(resource_data, "aws.ec2")

        # Assert
        assert result == "i-fallback-123"
```

### 2.3 ARN解析テスト

```python
class TestArnParsing:
    """extract_resource_arn のテスト"""

    def test_arn_with_slash(self):
        """RIE-011: スラッシュ含むARNから末尾リソースIDを抽出

        resource_id_extractor.py:L195-196 のスラッシュ分割パスをカバー。
        """
        # Arrange
        arn = "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0"

        # Act
        result = extract_resource_arn(arn)

        # Assert
        assert result == "i-1234567890abcdef0"

    def test_arn_without_slash(self):
        """RIE-012: スラッシュなしARNからコロン末尾部分を抽出

        resource_id_extractor.py:L198 のスラッシュなしパスをカバー。
        """
        # Arrange
        arn = "arn:aws:sns:us-east-1:123456789012:my-topic"

        # Act
        result = extract_resource_arn(arn)

        # Assert
        assert result == "my-topic"

    def test_short_arn_fallback(self):
        """RIE-013: 6パーツ未満のARN → そのまま返却

        resource_id_extractor.py:L201 のフォールバックパスをカバー。
        """
        # Arrange
        arn = "partial:arn:value"

        # Act
        result = extract_resource_arn(arn)

        # Assert
        assert result == "partial:arn:value"

    @pytest.mark.parametrize("invalid_input", [None, "", 123])
    def test_invalid_arn_input(self, invalid_input):
        """RIE-014: 無効入力（None, 空文字, 非文字列）→ "unknown"

        resource_id_extractor.py:L184 の入力バリデーションをカバー。
        """
        # Arrange / Act
        result = extract_resource_arn(invalid_input)

        # Assert
        assert result == "unknown"
```

### 2.4 優先IDフィールドテスト

```python
class TestPriorityIdFields:
    """_get_priority_id_fields のテスト"""

    def test_known_resource_type(self):
        """RIE-015: 既知リソースタイプ → 優先フィールドリスト返却"""
        # Act
        result = _get_priority_id_fields("aws.ec2")

        # Assert
        assert result == ["InstanceId"]

    def test_unknown_resource_type(self):
        """RIE-016: 未知リソースタイプ → 空リスト返却"""
        # Act
        result = _get_priority_id_fields("aws.unknown-service")

        # Assert
        assert result == []

    def test_double_aws_prefix_normalization(self):
        """RIE-017: aws.aws.重複プレフィックスの正規化

        resource_id_extractor.py:L220-221 の正規化ロジックをカバー。
        """
        # Act
        result = _get_priority_id_fields("aws.aws.ec2")

        # Assert
        assert result == ["InstanceId"]
```

### 2.5 リソース要約テスト

```python
class TestResourceSummary:
    """get_resource_summary のテスト"""

    def test_summary_with_arn(self):
        """RIE-018: ARNフィールドあり → 全情報揃った要約辞書"""
        # Arrange
        resource_data = {
            "InstanceId": "i-123",
            "ResourceArn": "arn:aws:ec2:us-east-1:123:instance/i-123",
            "Tags": [{"Key": "Name", "Value": "web"}],
        }

        # Act
        result = get_resource_summary(resource_data, "aws.ec2")

        # Assert
        assert result["primary_id"] == "i-123"
        assert result["display_name"] == "web"
        assert result["arn"] == "arn:aws:ec2:us-east-1:123:instance/i-123"
        assert result["resource_type"] == "aws.ec2"

    def test_summary_without_arn(self):
        """RIE-019: ARNフィールドなし → arn=None"""
        # Arrange
        resource_data = {"InstanceId": "i-456"}

        # Act
        result = get_resource_summary(resource_data, "aws.ec2")

        # Assert
        assert result["primary_id"] == "i-456"
        assert result["arn"] is None
```

### 2.6 ARN構築テスト

```python
from unittest.mock import patch


class TestBuildResourceArn:
    """build_resource_arn のテスト"""

    def test_existing_arn_found(self):
        """RIE-020: 既存ARNフィールド検出 → そのまま返却

        resource_id_extractor.py:L309 の早期リターンをカバー。
        """
        # Arrange
        resource_data = {"Arn": "arn:aws:ec2:us-east-1:123:instance/i-123"}

        # Act
        result = build_resource_arn(resource_data, "aws.ec2")

        # Assert
        assert result == "arn:aws:ec2:us-east-1:123:instance/i-123"

    def test_build_ec2_arn(self):
        """RIE-021: ec2 ARN構築（account_id, region明示）

        resource_id_extractor.py:L320-328 のARN構築パスをカバー。
        """
        # Arrange
        resource_data = {"InstanceId": "i-abc123"}

        # Act
        result = build_resource_arn(
            resource_data, "aws.ec2",
            account_id="123456789012", region="us-east-1",
        )

        # Assert
        assert result == "arn:aws:ec2:us-east-1:123456789012:instance/i-abc123"

    def test_missing_info_returns_none(self):
        """RIE-022: 必要情報不足 → None返却

        resource_id_extractor.py:L323 の情報不足チェックをカバー。
        """
        # Arrange
        # account_id, region ともに取得不可、引数にも未指定
        resource_data = {"some_field": "value"}

        # Act
        result = build_resource_arn(resource_data, "aws.unknown")

        # Assert
        assert result is None
```

### 2.7 ARNサニタイズテスト

```python
class TestSanitizeArn:
    """sanitize_arn_for_document_id のテスト"""

    def test_normal_sanitize(self):
        """RIE-023: 特殊文字（: / * ?）をアンダースコアに置換"""
        # Arrange
        arn = "arn:aws:ec2:us-east-1:123456789012:instance/i-123"

        # Act
        result = sanitize_arn_for_document_id(arn)

        # Assert
        assert ":" not in result
        assert "/" not in result
        assert result == "arn_aws_ec2_us-east-1_123456789012_instance_i-123"

    def test_long_arn_truncation(self):
        """RIE-024: 512文字超のARN → 490文字 + _ + sha256[:16]

        resource_id_extractor.py:L359-363 のハッシュ短縮パスをカバー。
        """
        # Arrange
        # 513文字以上のサニタイズ済み文字列を生成
        long_arn = "arn:aws:ec2:us-east-1:123456789012:" + "a" * 500

        # Act
        result = sanitize_arn_for_document_id(long_arn)

        # Assert
        # sanitized[:490] + "_" + hash_suffix[:16] = 507文字
        assert len(result) == 507
        assert result[490] == "_"  # ハッシュ区切り文字
```

### 2.8 プライベートヘルパーテスト

```python
class TestPrivateHelpers:
    """プライベート関数のテスト"""

    def test_extract_existing_arn_direct_field(self):
        """RIE-025: 直接ARNフィールドから抽出

        resource_id_extractor.py:L374-377 の直接フィールドパスをカバー。
        """
        # Arrange
        resource_data = {"Arn": "arn:aws:ec2:us-east-1:123:instance/i-123"}

        # Act
        result = _extract_existing_arn(resource_data)

        # Assert
        assert result == "arn:aws:ec2:us-east-1:123:instance/i-123"

    def test_extract_existing_arn_nested_dict(self):
        """RIE-026: ネストdictのArnフィールドから抽出

        resource_id_extractor.py:L380-384 のネスト検索パスをカバー。
        """
        # Arrange
        resource_data = {
            "Configuration": {"Arn": "arn:aws:lambda:us-east-1:123:function:my-func"},
        }

        # Act
        result = _extract_existing_arn(resource_data)

        # Assert
        assert result == "arn:aws:lambda:us-east-1:123:function:my-func"

    def test_extract_account_id_found(self):
        """RIE-027: アカウントIDフィールド検出"""
        # Arrange
        resource_data = {"OwnerId": "123456789012"}

        # Act
        result = _extract_account_id(resource_data)

        # Assert
        assert result == "123456789012"

    def test_extract_region_from_az(self):
        """RIE-028: AvailabilityZoneからリージョン推定

        resource_id_extractor.py:L406-410 のAZパスをカバー。
        """
        # Arrange
        resource_data = {"AvailabilityZone": "us-east-1a"}

        # Act
        result = _extract_region(resource_data)

        # Assert
        assert result == "us-east-1"

    def test_extract_region_from_placement(self):
        """RIE-029: Placement.AvailabilityZoneからリージョン推定

        resource_id_extractor.py:L413-418 のPlacementパスをカバー。
        """
        # Arrange
        resource_data = {
            "Placement": {"AvailabilityZone": "ap-northeast-1c"},
        }

        # Act
        result = _extract_region(resource_data)

        # Assert
        assert result == "ap-northeast-1"

    def test_extract_existing_arn_not_found(self):
        """RIE-031: ARNフィールドなし → None

        resource_id_extractor.py:L386 のNone返却をカバー。
        """
        # Arrange
        resource_data = {"InstanceId": "i-123", "Name": "web-server"}

        # Act
        result = _extract_existing_arn(resource_data)

        # Assert
        assert result is None

    def test_extract_account_id_not_found(self):
        """RIE-032: アカウントIDフィールドなし → None

        resource_id_extractor.py:L400 のNone返却をカバー。
        """
        # Act
        result = _extract_account_id({})

        # Assert
        assert result is None

    @pytest.mark.parametrize("resource_type, resource_id, expected", [
        ("aws.ec2", "i-123", "arn:aws:ec2:us-east-1:123456789012:instance/i-123"),
        ("aws.ebs", "vol-123", "arn:aws:ec2:us-east-1:123456789012:volume/vol-123"),
        ("aws.security-group", "sg-123", "arn:aws:ec2:us-east-1:123456789012:security-group/sg-123"),
        ("aws.s3", "my-bucket", "arn:aws:s3:::my-bucket"),
        ("aws.iam", "my-role", "arn:aws:iam::123456789012:role/my-role"),
        ("aws.lambda", "my-func", "arn:aws:lambda:us-east-1:123456789012:function:my-func"),
        ("aws.rds", "my-db", "arn:aws:rds:us-east-1:123456789012:db:my-db"),
        ("aws.vpc", "vpc-123", "arn:aws:ec2:us-east-1:123456789012:vpc/vpc-123"),
        ("aws.custom", "res-1", "arn:aws:custom:us-east-1:123456789012:res-1"),
    ])
    def test_build_arn_by_resource_type(self, resource_type, resource_id, expected):
        """RIE-030: リソースタイプ別ARN構築（9タイプ + else）

        resource_id_extractor.py:L438-467 の各サービスタイプ分岐をカバー。
        """
        # Arrange
        resource_data = {"RoleName": "my-role"} if resource_type == "aws.iam" else {}

        # Act
        result = _build_arn_by_resource_type(
            resource_type, "us-east-1", "123456789012", resource_id, resource_data,
        )

        # Assert
        assert result == expected
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| RIE-E01 | extract_resource_id 例外 | _get_priority_id_fields が例外発生 | primary_id=error, method=exception_occurred |
| RIE-E02 | extract_display_name 外側例外（ID復旧） | extract_resource_id 初回例外→2回目正常 | primary_id値 |
| RIE-E03 | extract_display_name 内側例外 | extract_resource_id 常に例外 | "unknown" |
| RIE-E04 | extract_resource_arn 例外 | split()で例外発生 | "unknown" |
| RIE-E05 | get_resource_summary 例外 | extract_resource_id が例外発生 | error辞書 |
| RIE-E06 | build_resource_arn 例外 | _extract_existing_arn が例外発生 | None |
| RIE-E07 | build_resource_arn resource_id="unknown" | 全フィールド不一致 | None |
| RIE-E08 | _extract_existing_arn 非awsプレフィックス | Arn="arn:gcp:..." | None（無視） |
| RIE-E09 | sanitize_arn_for_document_id 無効入力 | None, "", 123 | "invalid_arn" |
| RIE-E10 | _extract_region 情報なし | 空dict | None |
| RIE-E11 | build_resource_arn 構築失敗 | _build_arn_by_resource_type→None | None |

### 3.1 異常系テスト

```python
class TestResourceIdExtractorErrors:
    """異常系テスト"""

    def test_extract_resource_id_exception(self):
        """RIE-E01: 内部例外発生時のグレースフルデグラデーション

        resource_id_extractor.py:L107-114 のExceptionハンドラをカバー。
        """
        # Arrange
        with patch(
            "app.jobs.utils.resource_id_extractor._get_priority_id_fields",
            side_effect=RuntimeError("test error"),
        ):
            # Act
            result = extract_resource_id({}, "aws.ec2")

        # Assert
        assert result["primary_id"] == "error"
        assert result["method"] == "exception_occurred"
        assert result["confidence"] == "low"

    def test_display_name_outer_exception_with_id_fallback(self):
        """RIE-E02: 外側Exception発生 → extract_resource_id で復旧

        resource_id_extractor.py:L163-168 の外側except + ID復旧パスをカバー。
        """
        # Arrange
        with patch(
            "app.jobs.utils.resource_id_extractor.extract_resource_id",
        ) as mock_extract:
            # 1回目: L160 で例外（外側exceptへ）
            # 2回目: L167 で正常復旧
            mock_extract.side_effect = [
                RuntimeError("first call fails"),
                {"primary_id": "fallback-id"},
            ]

            # Act
            result = extract_display_name({}, "aws.ec2")

        # Assert
        assert result == "fallback-id"

    def test_display_name_inner_exception_returns_unknown(self):
        """RIE-E03: 内側Exception（復旧も失敗）→ "unknown"

        resource_id_extractor.py:L169-170 の内側exceptパスをカバー。
        """
        # Arrange
        with patch(
            "app.jobs.utils.resource_id_extractor.extract_resource_id",
            side_effect=RuntimeError("always fails"),
        ):
            # Act
            result = extract_display_name({}, "aws.ec2")

        # Assert
        assert result == "unknown"

    def test_extract_resource_arn_exception(self):
        """RIE-E04: ARN解析中の例外 → "unknown"

        resource_id_extractor.py:L203-205 のExceptionハンドラをカバー。
        str を継承したサブクラスで split を override し、isinstance(x, str) = True
        かつ split で例外を発生させることで L203 の except に到達する。
        """
        # Arrange
        class BrokenStr(str):
            """split() で例外を発生させる str サブクラス"""
            def split(self, *args, **kwargs):
                raise RuntimeError("broken split")

        broken_arn = BrokenStr("arn:aws:ec2:us-east-1:123:instance/i-1")

        # Act
        result = extract_resource_arn(broken_arn)

        # Assert
        assert result == "unknown"

    def test_get_resource_summary_exception(self):
        """RIE-E05: リソース要約作成中の例外

        resource_id_extractor.py:L273-283 のExceptionハンドラをカバー。
        """
        # Arrange
        with patch(
            "app.jobs.utils.resource_id_extractor.extract_resource_id",
            side_effect=RuntimeError("test error"),
        ):
            # Act
            result = get_resource_summary({}, "aws.ec2")

        # Assert
        assert result["primary_id"] == "error"
        assert result["display_name"] == "error"
        assert result["extraction_method"] == "failed"
        assert result["resource_type"] == "aws.ec2"

    def test_build_resource_arn_exception(self):
        """RIE-E06: ARN構築中の例外 → None

        resource_id_extractor.py:L337-339 のExceptionハンドラをカバー。
        """
        # Arrange
        with patch(
            "app.jobs.utils.resource_id_extractor._extract_existing_arn",
            side_effect=RuntimeError("test error"),
        ):
            # Act
            result = build_resource_arn({}, "aws.ec2")

        # Assert
        assert result is None

    def test_build_resource_arn_unknown_resource_id(self):
        """RIE-E07: resource_id が "unknown" → None

        resource_id_extractor.py:L323 の `resource_id == "unknown"` 条件をカバー。
        """
        # Arrange
        resource_data = {"some_field": "value"}

        # Act
        result = build_resource_arn(
            resource_data, "aws.unknown",
            account_id="123456789012", region="us-east-1",
        )

        # Assert
        assert result is None

    def test_extract_existing_arn_non_aws_prefix_ignored(self):
        """RIE-E08: arn:aws: 以外のプレフィックスは無視

        resource_id_extractor.py:L376 の `arn.startswith("arn:aws:")` 条件をカバー。
        """
        # Arrange
        resource_data = {"Arn": "arn:gcp:compute:us-central1:123:instance/i-123"}

        # Act
        result = _extract_existing_arn(resource_data)

        # Assert
        assert result is None

    @pytest.mark.parametrize("invalid_input", [None, "", 123])
    def test_sanitize_arn_invalid_input(self, invalid_input):
        """RIE-E09: sanitize_arn_for_document_id 無効入力 → "invalid_arn"

        resource_id_extractor.py:L352-353 の入力バリデーションをカバー。
        """
        # Act
        result = sanitize_arn_for_document_id(invalid_input)

        # Assert
        assert result == "invalid_arn"

    def test_build_resource_arn_construction_failure(self):
        """RIE-E11: _build_arn_by_resource_type が None 返却 → None

        resource_id_extractor.py:L330-334 の `if arn:` else 分岐をカバー。
        """
        # Arrange
        resource_data = {"InstanceId": "i-123"}

        with patch(
            "app.jobs.utils.resource_id_extractor._build_arn_by_resource_type",
            return_value=None,
        ):
            # Act
            result = build_resource_arn(
                resource_data, "aws.ec2",
                account_id="123456789012", region="us-east-1",
            )

        # Assert
        assert result is None

    def test_extract_region_no_info(self):
        """RIE-E10: リージョン情報なし → None

        resource_id_extractor.py:L420 のNone返却をカバー。
        """
        # Act
        result = _extract_region({})

        # Assert
        assert result is None
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| RIE-SEC-01 | str(e) ログ露出 | 機密情報含む例外 | ログに機密情報が含まれない [EXPECTED_TO_FAIL] |
| RIE-SEC-02 | メタデータ ログ露出 | account_id/resource_id | warning ログに生値が含まれない [EXPECTED_TO_FAIL] |
| RIE-SEC-03 | ARNサニタイズ 特殊文字 | XSS風・パストラバーサル文字 | 全て置換される |

```python
import logging


@pytest.mark.security
class TestResourceIdExtractorSecurity:
    """セキュリティテスト"""

    @pytest.mark.xfail(strict=True, raises=AssertionError,
                       reason="str(e) がログに直接含まれ、機密情報が露出する")
    def test_str_e_log_exposure(self, caplog):
        """RIE-SEC-01: logger.error に str(e) が直接含まれ機密情報が露出する

        [EXPECTED_TO_FAIL] resource_id_extractor.py:L108 で `str(e)` を
        そのままログに含めるため、例外メッセージにAPIキーが含まれる場合に
        ログに露出する。同一パターンが L164, L204, L274, L338 にも存在。
        """
        # Arrange
        secret_key = "AKIAIOSFODNN7EXAMPLE"
        with patch(
            "app.jobs.utils.resource_id_extractor._get_priority_id_fields",
            side_effect=RuntimeError(f"connection failed: key={secret_key}"),
        ):
            # Act
            with caplog.at_level(logging.ERROR):
                extract_resource_id({}, "aws.ec2")

        # Assert — 機密情報がログに含まれないことを検証
        for record in caplog.records:
            assert secret_key not in record.getMessage(), \
                f"機密情報がログに露出: {record.getMessage()}"

    @pytest.mark.xfail(strict=True, raises=AssertionError,
                       reason="logger.warning にリソースメタデータが直接含まれる")
    def test_metadata_log_exposure(self, caplog):
        """RIE-SEC-02: logger.warning にaccount_id/resource_idが直接露出する

        [EXPECTED_TO_FAIL] resource_id_extractor.py:L324 で
        `account_id={account_id}, region={region}, resource_id={resource_id}`
        をそのまま warning ログに含めるため、メタデータが露出する。
        """
        # Arrange
        resource_data = {"some_field": "value"}

        # Act
        with caplog.at_level(logging.WARNING):
            build_resource_arn(
                resource_data, "aws.unknown",
                account_id="123456789012", region="us-east-1",
            )

        # Assert — account_idがログに含まれないことを検証
        for record in caplog.records:
            assert "123456789012" not in record.getMessage(), \
                f"account_idがログに露出: {record.getMessage()}"

    def test_sanitize_special_characters(self):
        """RIE-SEC-03: ARNサニタイズが危険な特殊文字を適切に処理する"""
        # Arrange
        # パストラバーサル・ワイルドカード・XSS風文字を含むARN
        dangerous_arn = "arn:aws:s3:::../../../etc/passwd?query=*"

        # Act
        result = sanitize_arn_for_document_id(dangerous_arn)

        # Assert
        assert "../" not in result  # パストラバーサルの / が _ に置換される
        assert "*" not in result    # ワイルドカードが _ に置換される
        assert "?" not in result    # クエリ文字が _ に置換される
        assert ":" not in result    # コロンが _ に置換される
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_resource_id_module` | テスト間のモジュール状態リセット | function | Yes |

### 共通フィクスチャ定義

```python
# test/unit/jobs/utils/conftest.py（#17a 仕様書で定義予定・共有）
import sys
import pytest

# 対象モジュールのプレフィックス
_TARGET_MODULES = (
    "app.jobs.utils.resource_id_extractor",
)


@pytest.fixture(autouse=True)
def reset_resource_id_module():
    """テストごとにモジュールのグローバル状態をリセット

    resource_id_extractor.py は純粋関数モジュール（可変グローバル状態は logger のみ）
    のため sys.modules 削除は過剰だが、#17a〜#17h 共有 conftest との統一性のため保持する。
    """
    yield
    # テスト後にクリーンアップ
    modules_to_remove = [
        key for key in sys.modules
        if any(key.startswith(prefix) for prefix in _TARGET_MODULES)
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]
```

> **注記**: conftest.py は #17a〜#17h と共有予定。実装時には既存の `_TARGET_MODULES` タプルに `"app.jobs.utils.resource_id_extractor"` を追加する形で統合する。

---

## 6. テスト実行例

```bash
# リソースID抽出テストのみ実行
pytest test/unit/jobs/utils/test_resource_id_extractor.py -v

# 特定のテストクラスのみ実行
pytest test/unit/jobs/utils/test_resource_id_extractor.py::TestResourceIdExtraction -v

# カバレッジ付きで実行
pytest test/unit/jobs/utils/test_resource_id_extractor.py \
    --cov=app.jobs.utils.resource_id_extractor \
    --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/jobs/utils/test_resource_id_extractor.py -m "security" -v

# パラメータ化テスト（ARN構築 9タイプ）の個別実行
pytest test/unit/jobs/utils/test_resource_id_extractor.py::TestPrivateHelpers::test_build_arn_by_resource_type -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 32 | RIE-001 〜 RIE-032 |
| 異常系 | 11 | RIE-E01 〜 RIE-E11 |
| セキュリティ | 3 | RIE-SEC-01 〜 RIE-SEC-03 |
| **合計** | **46** | - |

> **注記**: RIE-014（3パターン）、RIE-E09（3パターン）は `pytest.mark.parametrize` を使用。RIE-030 は9サービスタイプの parametrize。pytest 上のテスト関数数は実質58件（parametrize展開後）。

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestResourceIdExtraction` | RIE-001〜RIE-007 | 7 |
| `TestDisplayNameExtraction` | RIE-008〜RIE-010 | 3 |
| `TestArnParsing` | RIE-011〜RIE-014 | 4 |
| `TestPriorityIdFields` | RIE-015〜RIE-017 | 3 |
| `TestResourceSummary` | RIE-018〜RIE-019 | 2 |
| `TestBuildResourceArn` | RIE-020〜RIE-022 | 3 |
| `TestSanitizeArn` | RIE-023〜RIE-024 | 2 |
| `TestPrivateHelpers` | RIE-025〜RIE-032 | 8 |
| `TestResourceIdExtractorErrors` | RIE-E01〜RIE-E11 | 11 |
| `TestResourceIdExtractorSecurity` | RIE-SEC-01〜RIE-SEC-03 | 3 |

### 7.1 予想失敗テスト

| テストID | 失敗理由 | 修正方針 |
|---------|---------|---------|
| RIE-SEC-01 | resource_id_extractor.py:L108 で `str(e)` をそのままログに含めるため、例外メッセージにAPIキーが含まれる場合にログに露出する。同一パターンが L164, L204, L274, L338 にも存在 | ログ出力から `str(e)` を除去するか、マスク処理を導入する |
| RIE-SEC-02 | resource_id_extractor.py:L324 で `account_id={account_id}, region={region}, resource_id={resource_id}` をそのまま warning ログに含める | ログメッセージからメタデータを除去するか、マスク処理を導入する |

### xfail 解除手順

1. `resource_id_extractor.py` の `logger.error(... str(e) ...)` パターンで例外メッセージをマスクまたは汎用メッセージに置換 → RIE-SEC-01 解除
   - L108: `extract_resource_id`
   - L164: `extract_display_name`
   - L204: `extract_resource_arn`
   - L274: `get_resource_summary`
   - L338: `build_resource_arn`
2. `resource_id_extractor.py` L324 の `logger.warning(...)` からメタデータ変数を除去 → RIE-SEC-02 解除
3. 上記修正後、対応する `@pytest.mark.xfail(...)` デコレータを削除
4. テスト実行で PASS を確認

### 注意事項

- `pytest-asyncio` 不要（全関数が同期）
- 外部接続なし。モックは内部関数の例外注入テスト（E01〜E06）でのみ使用
- `logging` の検証には `caplog` フィクスチャ（pytest 組み込み）を使用
- `_build_arn_by_resource_type` のパラメータ化テスト（RIE-030）は IAM の場合に `resource_data` に `RoleName` を設定（L453 の `resource_data.get("RoleName", resource_id)` をカバー）
- モジュールレベル import（L8-10）は標準ライブラリのみのため、パッチ不要

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `re` モジュールが L10 でインポートされているが、コード内で未使用（デッドインポート） | テスト影響なし | 実装側でデッドインポート削除を推奨 |
| 2 | `build_resource_arn` L304 でモジュールレベル logger と同一の `logger = logging.getLogger(__name__)` をローカル再定義 | 動作に影響なし（同一ロガーを参照） | 実装側でローカル再定義を削除し、モジュールレベル logger を使用することを推奨 |
| 3 | `str(e)` がログメッセージに直接含まれる（5箇所: L108, L164, L204, L274, L338） | 機密情報がログに露出するリスク | RIE-SEC-01 が L108 の代表経路を xfail として記録。他4箇所も同一パターンのため省略 |
| 4 | `logger.warning` L324 に account_id, region, resource_id が生値で含まれる | リソースメタデータがログに露出 | RIE-SEC-02 で xfail として記録 |
| 5 | `extract_display_name` L132 で Tags が list でない場合（dict 形式等）のスキップパスが未カバー | RIE-009/RIE-010 は Tags 非存在のため L132 に未到達。Tags が dict 形式（一部 AWS API で返却）の場合の専用テストなし | `resource_data = {"Tags": {"Name": "web"}}` のような Tags dict 形式の専用テスト追加を推奨 |
| 6 | `str(e)` 露出箇所のうち L338（`build_resource_arn`）は ARN構築コンテキストであり、例外メッセージに account_id 等が含まれるリスクが他経路より高い | RIE-SEC-01 は L108 の代表経路のみカバー | 将来的に L338 の独立テスト（RIE-SEC-01b）追加を推奨 |
