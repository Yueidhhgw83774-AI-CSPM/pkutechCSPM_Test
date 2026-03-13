# jobs/utils ヘルパー・正規化基盤 テストケース

## 1. 概要

`app/jobs/utils/` の最下層モジュール群（`helper_functions.py`, `field_normalizers.py`）のテスト仕様書。共通ユーティリティ関数とフィールド正規化ロジックを担い、他のutilsモジュール（document_creators, document_extractors, store_operations, custodian_output）から広く参照される基盤レイヤーである。

### 1.1 主要機能

| 関数 | ファイル | 説明 |
|------|---------|------|
| `_get_custodian_version()` | helper_functions.py | Cloud Custodian (c7n) のバージョン取得 |
| `_extract_resource_id()` | helper_functions.py | リソースからIDフィールドを抽出 |
| `_load_metadata_from_file()` | helper_functions.py | metadata.json ファイルの読み込み |
| `_determine_resource_type()` | helper_functions.py | リソースタイプの決定（メタデータ or 推定） |
| `_generate_policy_fingerprint()` | helper_functions.py | ポリシーセットのフィンガープリント生成 |
| `_sanitize_resource_for_opensearch()` | field_normalizers.py | リソースデータのOpenSearch互換形式変換 |
| `_normalize_resource_fields()` | field_normalizers.py | マッピング競合回避のためのフィールド正規化 |
| `_normalize_numeric_fields()` | field_normalizers.py | 数値型フィールドの統一（int→float） |
| `_sanitize_custodian_metadata()` | field_normalizers.py | Custodianメタデータ内のフィルター値型統一 |
| `_normalize_filter_values()` | field_normalizers.py | フィルター配列内のvalue型統一 |
| `_normalize_nested_filter_object()` | field_normalizers.py | ネストしたフィルターオブジェクトの正規化 |

### 1.2 カバレッジ目標: 90%

> **注記**: 全関数が同期関数であり、外部依存は `os.path.exists`, `open`, `json.load`, `pkg_resources`/`importlib.metadata` のみ。モック構築が容易なため、高カバレッジを目標とする。`os.walk` を使用する `_generate_policy_fingerprint` はファイルシステムモックが必要。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象1 | `app/jobs/utils/helper_functions.py` (138行) |
| テスト対象2 | `app/jobs/utils/field_normalizers.py` (311行) |
| テストコード | `test/unit/jobs/utils/test_helper_normalizer.py` |
| conftest | `test/unit/jobs/utils/conftest.py` |

### 1.4 依存関係

```
field_normalizers.py
└── helper_functions.py (_extract_resource_id)

被依存（他utilsファイルからの参照）:
├── document_creators.py ← helper_functions, field_normalizers
├── document_extractors.py ← helper_functions, field_normalizers
├── store_operations.py ← helper_functions, field_normalizers
└── custodian_output.py ← helper_functions, field_normalizers
```

### 1.5 主要分岐マップ

| 関数 | 分岐数 | 主要条件 |
|------|--------|---------|
| `_get_custodian_version` | 3 | L10 pkg_resources成功, L15 importlib.metadata成功, L18 両方失敗 |
| `_extract_resource_id` | 6 | L26-28 各IDフィールド存在チェック（5フィールド）, L30 フォールバック |
| `_load_metadata_from_file` | 3 | L45 ファイル存在, L49 ファイル不存在, L51 例外 |
| `_determine_resource_type` | 8 | L69 metadata有り, L70 policy_resource未設定（None）, L73 フルフォーマット, L76 短縮形, L80-87 AWS各リソース, L89 unknown |
| `_generate_policy_fingerprint` | 4 | L107 metadata.json有り, L126 例外スキップ, L130 ハッシュ有り, L136 空 |
| `_sanitize_resource_for_opensearch` | 10 | L47 force_stringify dict/list, L51 force_stringify非dict/list, L53 preserve_structure, L54/56 5KB超list/dict, L58-63 preserve小, L65 dict, L68 list, L89 2KB超item, L95/97 200B判定 |
| `_normalize_resource_fields` | 4 | L142 problematic+dict/list, L144 dict, L146 list, L165 例外 |
| `_normalize_numeric_fields` | 3 | L185 dict, L189 Value+数値, L196 list |
| `_sanitize_custodian_metadata` | 3 | L219 policy存在, L221 filters存在, L226 例外 |
| `_normalize_filter_values` | 6 | L252 value+数値/bool, L256 value+list/dict, L260 value+None, L261 or+list, L264 dict, L267 その他 |
| `_normalize_nested_filter_object` | 5 | L293 value+数値, L296 value+list/dict, L299 value+None, L300 dict, L303 list |

### 1.6 実装上の注意点

| # | 注意点 | 影響 |
|---|--------|------|
| 1 | `_get_custodian_version` は関数内で `import pkg_resources` を実行（L11） | モジュールレベルのパッチが効かない。`pkg_resources.get_distribution` を直接パッチする必要あり |
| 2 | `_sanitize_resource_for_opensearch` の `copy.deepcopy` は `try` ブロックの外（L20） | deepcopy例外はtry/exceptで捕捉されない。try内の `_convert_complex_fields` で例外を発生させる必要あり |
| 3 | `_normalize_resource_fields` の `copy.deepcopy` は `try` ブロックの外（L125） | 同上。try内の `_convert_problematic_fields` で例外を発生させる必要あり |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| HN-001 | _get_custodian_version pkg_resources成功 | c7nインストール済み | バージョン文字列 |
| HN-002 | _get_custodian_version importlib.metadata成功 | pkg_resources失敗 | バージョン文字列 |
| HN-003 | _get_custodian_version 両方失敗 | c7n未インストール | `"unknown"` |
| HN-004 | _extract_resource_id InstanceId | `{"InstanceId": "i-123"}` | `"i-123"` |
| HN-005 | _extract_resource_id GroupId | `{"GroupId": "sg-456"}` | `"sg-456"` |
| HN-006 | _extract_resource_id VolumeId | `{"VolumeId": "vol-789"}` | `"vol-789"` |
| HN-007 | _extract_resource_id id | `{"id": "abc"}` | `"abc"` |
| HN-008 | _extract_resource_id name | `{"name": "test"}` | `"test"` |
| HN-009 | _extract_resource_id フォールバック | `{"other": "val"}`, index=3 | `"resource_3"` |
| HN-010 | _extract_resource_id 優先順位確認 | `{"InstanceId": "i-1", "id": "x"}` | `"i-1"` |
| HN-011 | _load_metadata_from_file 正常読み込み | 有効なJSONファイル | メタデータ辞書 |
| HN-012 | _load_metadata_from_file ファイル不存在 | 存在しないパス | `{}` + warning |
| HN-013 | _determine_resource_type メタデータ有り（フル） | `metadata.policy.resource="aws.ec2"` | `"aws.ec2"` |
| HN-014 | _determine_resource_type メタデータ有り（短縮） | `metadata.policy.resource="ec2"` | `"aws.ec2"` |
| HN-015 | _determine_resource_type EC2推定 | `{"InstanceId": "i-1"}` | `"aws.ec2"` |
| HN-016 | _determine_resource_type SG推定 | `{"GroupId": "sg-1"}` | `"aws.security-group"` |
| HN-017 | _determine_resource_type EBS推定 | `{"VolumeId": "vol-1"}` | `"aws.ebs"` |
| HN-018 | _determine_resource_type S3推定（BucketName） | `{"BucketName": "b"}` | `"aws.s3"` |
| HN-019 | _determine_resource_type S3推定（Name） | `{"Name": "b"}` | `"aws.s3"` |
| HN-020 | _determine_resource_type unknown | 不明リソース, `"aws"` | `"aws.unknown"` |
| HN-020a | _determine_resource_type policy有りresource無し | `metadata={"policy": {"name": "x"}}` | リソースから推定 |
| HN-021 | _generate_policy_fingerprint 単一ポリシー | 1つのmetadata.json | 32文字ハッシュ |
| HN-022 | _generate_policy_fingerprint 決定論的ハッシュ | 同一入力2回 | 同一ハッシュ値 |
| HN-023 | _generate_policy_fingerprint 空ディレクトリ | metadata.jsonなし | `"no-policies-found"` |
| HN-024 | _sanitize_resource_for_opensearch force_stringify dict | `State={"Name":"running"}` | JSON文字列化 |
| HN-024a | _sanitize_resource_for_opensearch force_stringify 非dict/list | `State=42` | `str()` 変換（`"42"`） |
| HN-025 | _sanitize_resource_for_opensearch preserve_structure小list | `Tags=[小リスト]` | 構造保持 |
| HN-026 | _sanitize_resource_for_opensearch preserve_structure大list | `Tags=5KB超リスト` | JSON文字列化 |
| HN-026a | _sanitize_resource_for_opensearch preserve_structure大dict | `Tags=5KB超dict` | JSON文字列化 |
| HN-026b | _sanitize_resource_for_opensearch preserve_structure 2KB超item | `Tags=[2KB超dict]` | item文字列化 |
| HN-027 | _sanitize_resource_for_opensearch 通常dict | ネストdict | 再帰処理 |
| HN-028 | _sanitize_resource_for_opensearch 通常list大 | 200B超dictリスト | JSON文字列化 |
| HN-029 | _sanitize_resource_for_opensearch 通常list小 | 200B以下dictリスト | 再帰処理 |
| HN-030 | _normalize_resource_fields problematic文字列化 | `State=dict` | JSON文字列 |
| HN-031 | _normalize_resource_fields 非problematicはそのまま | `CustomField=dict` | dict保持 |
| HN-032 | _normalize_numeric_fields int→float | `{"Value": 42}` | `{"Value": 42.0}` |
| HN-033 | _normalize_numeric_fields ネストされた数値 | ネスト構造 | 再帰的にfloat変換 |
| HN-034 | _normalize_numeric_fields 非Valueキー | `{"Count": 5}` | `{"Count": 5}` |
| HN-035 | _sanitize_custodian_metadata policy.filters正規化 | `filters=[{value:10}]` | `filters=[{value:"10"}]` |
| HN-036 | _sanitize_custodian_metadata policy無し | `{}` | `{}` |
| HN-037 | _normalize_filter_values 数値value | `[{value: 42}]` | `[{value: "42"}]` |
| HN-038 | _normalize_filter_values bool value | `[{value: True}]` | `[{value: "True"}]` |
| HN-039 | _normalize_filter_values list value | `[{value: [1,2]}]` | `[{value: "[1, 2]"}]` |
| HN-040 | _normalize_filter_values None value | `[{value: None}]` | `[{value: ""}]` |
| HN-041 | _normalize_filter_values or再帰 | `[{or: [{value:1}]}]` | `[{or: [{value:"1"}]}]` |
| HN-042 | _normalize_filter_values 非dictアイテム | `["string_filter"]` | `["string_filter"]` |
| HN-043 | _normalize_nested_filter_object value正規化 | `{value: 3.14}` | `{value: "3.14"}` |
| HN-044 | _normalize_nested_filter_object ネストdict | `{inner: {value: 5}}` | `{inner: {value: "5"}}` |
| HN-045 | _normalize_nested_filter_object ネストlist | `{items: [{value:1}]}` | `{items: [{value:"1"}]}` |
| HN-046 | _normalize_nested_filter_object value=list/dict | `{value: [1, {"a": 2}]}` | `{value: JSON文字列}` |
| HN-047 | _normalize_nested_filter_object value=None | `{value: None}` | `{value: ""}` |

### 2.1 _get_custodian_version テスト

```python
# test/unit/jobs/utils/test_helper_normalizer.py
import pytest
import json
import os
import hashlib
from unittest.mock import patch, MagicMock, mock_open


class TestGetCustodianVersion:
    """_get_custodian_version のテスト"""

    def test_pkg_resources_success(self):
        """HN-001: pkg_resourcesでバージョン取得成功

        helper_functions.py:11 の関数内importをカバー。
        pkg_resourcesは関数内でimportされるため、
        pkg_resources.get_distribution を直接パッチする。
        """
        # Arrange
        mock_dist = MagicMock()
        mock_dist.version = "0.9.35"

        # Act
        with patch("pkg_resources.get_distribution", return_value=mock_dist):
            from app.jobs.utils.helper_functions import _get_custodian_version
            result = _get_custodian_version()

        # Assert
        assert result == "0.9.35"

    def test_importlib_metadata_fallback(self):
        """HN-002: pkg_resources失敗時にimportlib.metadataへフォールバック

        helper_functions.py:10-16 の例外フォールバック分岐をカバー。
        pkg_resourcesが失敗した場合にimportlib.metadataへ切り替わる。
        """
        # Arrange & Act
        with patch("pkg_resources.get_distribution", side_effect=Exception("not found")):
            with patch("importlib.metadata.version", return_value="0.9.36"):
                from app.jobs.utils.helper_functions import _get_custodian_version
                result = _get_custodian_version()

        # Assert
        assert result == "0.9.36"

    def test_both_fail_returns_unknown(self):
        """HN-003: 両方のインポート方法が失敗した場合に'unknown'を返す

        helper_functions.py:17-19 のフォールバック分岐をカバー
        """
        # Arrange & Act
        with patch("pkg_resources.get_distribution", side_effect=Exception("not found")):
            with patch("importlib.metadata.version", side_effect=Exception("not found")):
                from app.jobs.utils.helper_functions import _get_custodian_version
                result = _get_custodian_version()

        # Assert
        assert result == "unknown"
```

### 2.2 _extract_resource_id テスト

```python
class TestExtractResourceId:
    """_extract_resource_id のテスト"""

    def test_instance_id(self):
        """HN-004: InstanceIdフィールドからID抽出"""
        # Arrange
        from app.jobs.utils.helper_functions import _extract_resource_id
        resource = {"InstanceId": "i-1234567890abcdef0"}

        # Act
        result = _extract_resource_id(resource, 0)

        # Assert
        assert result == "i-1234567890abcdef0"

    def test_group_id(self):
        """HN-005: GroupIdフィールドからID抽出"""
        # Arrange
        from app.jobs.utils.helper_functions import _extract_resource_id
        resource = {"GroupId": "sg-456def"}

        # Act
        result = _extract_resource_id(resource, 0)

        # Assert
        assert result == "sg-456def"

    def test_volume_id(self):
        """HN-006: VolumeIdフィールドからID抽出"""
        # Arrange
        from app.jobs.utils.helper_functions import _extract_resource_id
        resource = {"VolumeId": "vol-789abc"}

        # Act
        result = _extract_resource_id(resource, 0)

        # Assert
        assert result == "vol-789abc"

    def test_generic_id(self):
        """HN-007: idフィールドからID抽出"""
        # Arrange
        from app.jobs.utils.helper_functions import _extract_resource_id
        resource = {"id": "abc-123"}

        # Act
        result = _extract_resource_id(resource, 0)

        # Assert
        assert result == "abc-123"

    def test_name_field(self):
        """HN-008: nameフィールドからID抽出"""
        # Arrange
        from app.jobs.utils.helper_functions import _extract_resource_id
        resource = {"name": "my-resource"}

        # Act
        result = _extract_resource_id(resource, 0)

        # Assert
        assert result == "my-resource"

    def test_fallback_to_index(self):
        """HN-009: 既知のIDフィールドがない場合はインデックスベースのフォールバック

        helper_functions.py:30 のフォールバック分岐をカバー
        """
        # Arrange
        from app.jobs.utils.helper_functions import _extract_resource_id
        resource = {"OtherField": "value"}

        # Act
        result = _extract_resource_id(resource, 3)

        # Assert
        assert result == "resource_3"

    def test_priority_order(self):
        """HN-010: IDフィールドの優先順位確認（InstanceId > id）

        helper_functions.py:24-28 のループ順序をカバー
        """
        # Arrange
        from app.jobs.utils.helper_functions import _extract_resource_id
        resource = {"InstanceId": "i-first", "id": "generic-id", "name": "my-name"}

        # Act
        result = _extract_resource_id(resource, 0)

        # Assert
        assert result == "i-first"
```

### 2.3 _load_metadata_from_file テスト

```python
class TestLoadMetadataFromFile:
    """_load_metadata_from_file のテスト"""

    def test_load_valid_file(self, tmp_path):
        """HN-011: 有効なmetadata.jsonファイルの正常読み込み"""
        # Arrange
        from app.jobs.utils.helper_functions import _load_metadata_from_file
        metadata = {"policy": {"name": "test-policy", "resource": "ec2"}}
        metadata_file = tmp_path / "metadata.json"
        metadata_file.write_text(json.dumps(metadata), encoding="utf-8")
        logger = MagicMock()

        # Act
        result = _load_metadata_from_file(str(metadata_file), logger)

        # Assert
        assert result == metadata
        logger.warning.assert_not_called()
        logger.error.assert_not_called()

    def test_file_not_exists(self):
        """HN-012: ファイルが存在しない場合は空辞書を返しwarning出力

        helper_functions.py:48-50 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.helper_functions import _load_metadata_from_file
        logger = MagicMock()

        # Act
        result = _load_metadata_from_file("/nonexistent/path/metadata.json", logger)

        # Assert
        assert result == {}
        logger.warning.assert_called_once()
        assert "metadata.jsonが存在しません" in logger.warning.call_args[0][0]
```

### 2.4 _determine_resource_type テスト

```python
class TestDetermineResourceType:
    """_determine_resource_type のテスト"""

    def test_metadata_full_format(self):
        """HN-013: メタデータにフルフォーマットのリソースタイプがある場合

        helper_functions.py:73-74 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.helper_functions import _determine_resource_type
        resource = {}
        metadata = {"policy": {"resource": "aws.ec2"}}

        # Act
        result = _determine_resource_type(resource, metadata, "aws")

        # Assert
        assert result == "aws.ec2"

    def test_metadata_short_format(self):
        """HN-014: メタデータに短縮形リソースタイプがある場合

        helper_functions.py:75-76 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.helper_functions import _determine_resource_type
        resource = {}
        metadata = {"policy": {"resource": "ec2"}}

        # Act
        result = _determine_resource_type(resource, metadata, "aws")

        # Assert
        assert result == "aws.ec2"

    def test_infer_ec2(self):
        """HN-015: InstanceIdからEC2を推定"""
        # Arrange
        from app.jobs.utils.helper_functions import _determine_resource_type
        resource = {"InstanceId": "i-123"}

        # Act
        result = _determine_resource_type(resource, {}, "aws")

        # Assert
        assert result == "aws.ec2"

    def test_infer_security_group(self):
        """HN-016: GroupIdからセキュリティグループを推定"""
        # Arrange
        from app.jobs.utils.helper_functions import _determine_resource_type
        resource = {"GroupId": "sg-123"}

        # Act
        result = _determine_resource_type(resource, {}, "aws")

        # Assert
        assert result == "aws.security-group"

    def test_infer_ebs(self):
        """HN-017: VolumeIdからEBSを推定"""
        # Arrange
        from app.jobs.utils.helper_functions import _determine_resource_type
        resource = {"VolumeId": "vol-123"}

        # Act
        result = _determine_resource_type(resource, {}, "aws")

        # Assert
        assert result == "aws.ebs"

    def test_infer_s3_bucket_name(self):
        """HN-018: BucketNameからS3を推定"""
        # Arrange
        from app.jobs.utils.helper_functions import _determine_resource_type
        resource = {"BucketName": "my-bucket"}

        # Act
        result = _determine_resource_type(resource, {}, "aws")

        # Assert
        assert result == "aws.s3"

    def test_infer_s3_name(self):
        """HN-019: NameからS3を推定"""
        # Arrange
        from app.jobs.utils.helper_functions import _determine_resource_type
        resource = {"Name": "my-bucket"}

        # Act
        result = _determine_resource_type(resource, {}, "aws")

        # Assert
        assert result == "aws.s3"

    def test_unknown_resource(self):
        """HN-020: 推定できないリソースは'unknown'

        helper_functions.py:89 のフォールバック分岐をカバー
        """
        # Arrange
        from app.jobs.utils.helper_functions import _determine_resource_type
        resource = {"SomeOtherField": "value"}

        # Act
        result = _determine_resource_type(resource, {}, "aws")

        # Assert
        assert result == "aws.unknown"

    def test_metadata_policy_without_resource_key(self):
        """HN-020a: metadataにpolicyはあるがresourceキーが無い場合はリソースから推定

        helper_functions.py:70-71 の分岐をカバー。
        policy.get("resource") が None を返すため、リソースデータからの推定にフォールバック。
        """
        # Arrange
        from app.jobs.utils.helper_functions import _determine_resource_type
        resource = {"InstanceId": "i-123"}
        metadata = {"policy": {"name": "test-policy"}}

        # Act
        result = _determine_resource_type(resource, metadata, "aws")

        # Assert
        assert result == "aws.ec2"
```

### 2.5 _generate_policy_fingerprint テスト

```python
class TestGeneratePolicyFingerprint:
    """_generate_policy_fingerprint のテスト"""

    def test_single_policy(self, tmp_path):
        """HN-021: 単一ポリシーのフィンガープリント生成"""
        # Arrange
        from app.jobs.utils.helper_functions import _generate_policy_fingerprint
        policy_dir = tmp_path / "policy1"
        policy_dir.mkdir()
        metadata = {
            "policy": {
                "name": "test-policy",
                "resource": "ec2",
                "filters": [{"type": "value"}],
                "actions": [{"type": "stop"}]
            }
        }
        (policy_dir / "metadata.json").write_text(
            json.dumps(metadata), encoding="utf-8"
        )

        # Act
        result = _generate_policy_fingerprint(str(tmp_path))

        # Assert
        assert isinstance(result, str)
        assert len(result) == 32

    def test_deterministic_hash(self, tmp_path):
        """HN-022: 同一入力に対して決定論的（同一）なハッシュを返す

        helper_functions.py:131 のsort()により順序が統一され、
        同一入力からは常に同一のフィンガープリントが生成されることを確認。
        """
        # Arrange
        from app.jobs.utils.helper_functions import _generate_policy_fingerprint
        for i in range(3):
            policy_dir = tmp_path / f"policy{i}"
            policy_dir.mkdir()
            metadata = {
                "policy": {
                    "name": f"policy-{i}",
                    "resource": "ec2",
                    "filters": [],
                    "actions": []
                }
            }
            (policy_dir / "metadata.json").write_text(
                json.dumps(metadata), encoding="utf-8"
            )

        # Act
        result1 = _generate_policy_fingerprint(str(tmp_path))
        result2 = _generate_policy_fingerprint(str(tmp_path))

        # Assert
        assert isinstance(result1, str)
        assert len(result1) == 32
        assert result1 == result2

    def test_empty_directory(self, tmp_path):
        """HN-023: metadata.jsonがないディレクトリの場合

        helper_functions.py:135-136 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.helper_functions import _generate_policy_fingerprint

        # Act
        result = _generate_policy_fingerprint(str(tmp_path))

        # Assert
        assert result == "no-policies-found"
```

### 2.6 _sanitize_resource_for_opensearch テスト

```python
class TestSanitizeResourceForOpensearch:
    """_sanitize_resource_for_opensearch のテスト"""

    def test_force_stringify_dict(self):
        """HN-024: force_stringifyフィールド（State等）のdict値はJSON文字列化

        field_normalizers.py:48-49 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _sanitize_resource_for_opensearch
        resource = {
            "InstanceId": "i-123",
            "State": {"Name": "running", "Code": 16}
        }

        # Act
        result = _sanitize_resource_for_opensearch(resource)

        # Assert
        assert isinstance(result["State"], str)
        parsed = json.loads(result["State"])
        assert parsed["Name"] == "running"

    def test_force_stringify_non_dict_non_list(self):
        """HN-024a: force_stringifyフィールドの非dict/list値はstr()で変換

        field_normalizers.py:50-51 の分岐をカバー。
        Stateが文字列・数値等の場合はstr()で変換される。
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _sanitize_resource_for_opensearch
        resource = {"State": 42}

        # Act
        result = _sanitize_resource_for_opensearch(resource)

        # Assert
        assert result["State"] == "42"
        assert isinstance(result["State"], str)

    def test_preserve_structure_small_list(self):
        """HN-025: preserve_structureフィールドの小さなリストは構造保持

        field_normalizers.py:58-59 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _sanitize_resource_for_opensearch
        resource = {
            "Tags": [{"Key": "Name", "Value": "test"}]
        }

        # Act
        result = _sanitize_resource_for_opensearch(resource)

        # Assert
        assert isinstance(result["Tags"], list)
        assert result["Tags"][0]["Key"] == "Name"

    def test_preserve_structure_large_list(self):
        """HN-026: preserve_structureフィールドの5KB超リストはJSON文字列化

        field_normalizers.py:54-55 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _sanitize_resource_for_opensearch
        large_tags = [{"Key": f"tag-{i}", "Value": "x" * 100} for i in range(100)]
        resource = {"Tags": large_tags}

        # Act
        result = _sanitize_resource_for_opensearch(resource)

        # Assert
        assert isinstance(result["Tags"], str)

    def test_preserve_structure_large_dict(self):
        """HN-026a: preserve_structureフィールドの5KB超dictはJSON文字列化

        field_normalizers.py:56-57 の分岐をカバー。
        Tagsがdict型で5KB超の場合もJSON文字列化される。
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _sanitize_resource_for_opensearch
        large_dict = {f"key-{i}": "x" * 100 for i in range(100)}
        resource = {"Tags": large_dict}

        # Act
        result = _sanitize_resource_for_opensearch(resource)

        # Assert
        assert isinstance(result["Tags"], str)

    def test_preserve_structure_large_item_in_list(self):
        """HN-026b: preserve_structureリスト内の2KB超itemはJSON文字列化

        field_normalizers.py:89-90 の分岐をカバー。
        preserve_structure=True のリスト内で、個別アイテムが2KBを超える場合。
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _sanitize_resource_for_opensearch
        large_item = {"Key": "Name", "Value": "x" * 2500}
        resource = {"Tags": [large_item]}

        # Act
        result = _sanitize_resource_for_opensearch(resource)

        # Assert
        assert isinstance(result["Tags"], list)
        assert isinstance(result["Tags"][0], str)

    def test_nested_dict_recursive(self):
        """HN-027: 通常のネストdictは再帰的に処理

        field_normalizers.py:65-66 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _sanitize_resource_for_opensearch
        resource = {
            "CustomField": {
                "Inner": {"Key": "val"},
                "State": {"Name": "active"}
            }
        }

        # Act
        result = _sanitize_resource_for_opensearch(resource)

        # Assert
        assert isinstance(result["CustomField"]["Inner"], dict)
        assert isinstance(result["CustomField"]["State"], str)

    def test_list_large_items_stringified(self):
        """HN-028: リスト内の200B超dictアイテムはJSON文字列化

        field_normalizers.py:95-96 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _sanitize_resource_for_opensearch
        large_item = {"key": "v" * 250}
        resource = {"Items": [large_item]}

        # Act
        result = _sanitize_resource_for_opensearch(resource)

        # Assert
        assert isinstance(result["Items"][0], str)

    def test_list_small_items_preserved(self):
        """HN-029: リスト内の200B以下dictアイテムは構造保持

        field_normalizers.py:97-98 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _sanitize_resource_for_opensearch
        resource = {"Items": [{"key": "val"}]}

        # Act
        result = _sanitize_resource_for_opensearch(resource)

        # Assert
        assert isinstance(result["Items"][0], dict)
        assert result["Items"][0]["key"] == "val"
```

### 2.7 _normalize_resource_fields テスト

```python
class TestNormalizeResourceFields:
    """_normalize_resource_fields のテスト"""

    def test_problematic_field_stringified(self):
        """HN-030: problematic_text_fieldsのdict/listはJSON文字列化

        field_normalizers.py:142-143 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _normalize_resource_fields
        resource = {
            "State": {"Name": "running", "Code": 16},
            "SecurityGroups": [{"GroupId": "sg-1"}],
            "Tags": [{"Key": "Name", "Value": "test"}]
        }

        # Act
        result = _normalize_resource_fields(resource)

        # Assert
        assert isinstance(result["State"], str)
        assert isinstance(result["SecurityGroups"], str)
        assert isinstance(result["Tags"], str)

    def test_non_problematic_preserved(self):
        """HN-031: 非problematicフィールドのdictはそのまま保持

        field_normalizers.py:144-145 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _normalize_resource_fields
        resource = {
            "CustomField": {"inner": "value"},
            "SimpleField": "text"
        }

        # Act
        result = _normalize_resource_fields(resource)

        # Assert
        assert isinstance(result["CustomField"], dict)
        assert result["SimpleField"] == "text"
```

### 2.8 _normalize_numeric_fields テスト

```python
class TestNormalizeNumericFields:
    """_normalize_numeric_fields のテスト"""

    def test_int_to_float(self):
        """HN-032: Valueキーの整数値をfloatに変換

        field_normalizers.py:189-190 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _normalize_numeric_fields
        obj = {"Value": 42}

        # Act
        result = _normalize_numeric_fields(obj)

        # Assert
        assert result["Value"] == 42.0
        assert isinstance(result["Value"], float)

    def test_nested_value_conversion(self):
        """HN-033: ネスト構造内のValueも再帰的にfloat変換

        field_normalizers.py:191-192 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _normalize_numeric_fields
        obj = {"metrics": {"Value": 100}, "items": [{"Value": 50}]}

        # Act
        result = _normalize_numeric_fields(obj)

        # Assert
        assert isinstance(result["metrics"]["Value"], float)
        assert result["metrics"]["Value"] == 100.0
        assert isinstance(result["items"][0]["Value"], float)
        assert result["items"][0]["Value"] == 50.0

    def test_non_value_key_unchanged(self):
        """HN-034: Valueキー以外の数値フィールドは変換しない"""
        # Arrange
        from app.jobs.utils.field_normalizers import _normalize_numeric_fields
        obj = {"Count": 5, "Value": 10}

        # Act
        result = _normalize_numeric_fields(obj)

        # Assert
        assert result["Count"] == 5
        assert isinstance(result["Count"], int)
        assert isinstance(result["Value"], float)
```

### 2.9 _sanitize_custodian_metadata テスト

```python
class TestSanitizeCustodianMetadata:
    """_sanitize_custodian_metadata のテスト"""

    def test_normalize_filter_values(self):
        """HN-035: policy.filters内のvalue型を正規化

        field_normalizers.py:219-222 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _sanitize_custodian_metadata
        metadata = {
            "policy": {
                "name": "test",
                "filters": [
                    {"type": "value", "key": "State", "value": 10}
                ]
            }
        }

        # Act
        result = _sanitize_custodian_metadata(metadata)

        # Assert
        assert result["policy"]["filters"][0]["value"] == "10"

    def test_no_policy_key(self):
        """HN-036: policyキーがない場合はそのまま返す"""
        # Arrange
        from app.jobs.utils.field_normalizers import _sanitize_custodian_metadata
        metadata = {"version": "1.0"}

        # Act
        result = _sanitize_custodian_metadata(metadata)

        # Assert
        assert result == {"version": "1.0"}
```

### 2.10 _normalize_filter_values テスト

```python
class TestNormalizeFilterValues:
    """_normalize_filter_values のテスト"""

    def test_numeric_value(self):
        """HN-037: 数値valueを文字列に変換

        field_normalizers.py:254-255 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _normalize_filter_values
        filters = [{"type": "value", "value": 42}]

        # Act
        result = _normalize_filter_values(filters)

        # Assert
        assert result[0]["value"] == "42"

    def test_bool_value(self):
        """HN-038: booleanのvalueを文字列に変換"""
        # Arrange
        from app.jobs.utils.field_normalizers import _normalize_filter_values
        filters = [{"type": "value", "value": True}]

        # Act
        result = _normalize_filter_values(filters)

        # Assert
        assert result[0]["value"] == "True"

    def test_list_value(self):
        """HN-039: listのvalueをJSON文字列に変換

        field_normalizers.py:256-258 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _normalize_filter_values
        filters = [{"type": "value", "value": [1, 2, 3]}]

        # Act
        result = _normalize_filter_values(filters)

        # Assert
        assert isinstance(result[0]["value"], str)
        parsed = json.loads(result[0]["value"])
        assert parsed == [1, 2, 3]

    def test_none_value(self):
        """HN-040: Noneのvalueを空文字に変換

        field_normalizers.py:260 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _normalize_filter_values
        filters = [{"type": "value", "value": None}]

        # Act
        result = _normalize_filter_values(filters)

        # Assert
        assert result[0]["value"] == ""

    def test_or_recursive(self):
        """HN-041: 'or'キーの再帰的なフィルター正規化

        field_normalizers.py:261-263 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _normalize_filter_values
        filters = [{"or": [{"type": "value", "value": 1}]}]

        # Act
        result = _normalize_filter_values(filters)

        # Assert
        assert result[0]["or"][0]["value"] == "1"

    def test_non_dict_item(self):
        """HN-042: dict以外のフィルターアイテムはそのまま保持

        field_normalizers.py:272-274 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _normalize_filter_values
        filters = ["string_filter", {"type": "value", "value": 5}]

        # Act
        result = _normalize_filter_values(filters)

        # Assert
        assert result[0] == "string_filter"
        assert result[1]["value"] == "5"
```

### 2.11 _normalize_nested_filter_object テスト

```python
class TestNormalizeNestedFilterObject:
    """_normalize_nested_filter_object のテスト"""

    def test_value_numeric(self):
        """HN-043: ネストオブジェクト内の数値valueを文字列に変換

        field_normalizers.py:293-295 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _normalize_nested_filter_object
        obj = {"type": "value", "value": 3.14}

        # Act
        result = _normalize_nested_filter_object(obj)

        # Assert
        assert result["value"] == "3.14"
        assert result["type"] == "value"

    def test_nested_dict(self):
        """HN-044: ネストしたdictオブジェクトを再帰的に正規化

        field_normalizers.py:300-302 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _normalize_nested_filter_object
        obj = {"inner": {"value": 5, "other": "keep"}}

        # Act
        result = _normalize_nested_filter_object(obj)

        # Assert
        assert result["inner"]["value"] == "5"
        assert result["inner"]["other"] == "keep"

    def test_nested_list_with_dicts(self):
        """HN-045: リスト内のdictオブジェクトも再帰的に正規化

        field_normalizers.py:303-307 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _normalize_nested_filter_object
        obj = {"items": [{"value": 1}, "plain_string"]}

        # Act
        result = _normalize_nested_filter_object(obj)

        # Assert
        assert result["items"][0]["value"] == "1"
        assert result["items"][1] == "plain_string"

    def test_value_list_dict(self):
        """HN-046: valueがlist/dict型の場合はJSON文字列に変換

        field_normalizers.py:296-297 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _normalize_nested_filter_object
        obj = {"value": [1, {"a": 2}]}

        # Act
        result = _normalize_nested_filter_object(obj)

        # Assert
        assert isinstance(result["value"], str)
        parsed = json.loads(result["value"])
        assert parsed == [1, {"a": 2}]

    def test_value_none(self):
        """HN-047: valueがNoneの場合は空文字に変換

        field_normalizers.py:299 の分岐をカバー
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _normalize_nested_filter_object
        obj = {"type": "value", "value": None}

        # Act
        result = _normalize_nested_filter_object(obj)

        # Assert
        assert result["value"] == ""
        assert result["type"] == "value"
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| HN-E01 | _load_metadata_from_file JSON解析エラー | 不正JSON | `{}` + error log |
| HN-E02 | _generate_policy_fingerprint 不正JSON | 壊れたmetadata.json | そのポリシーをスキップ |
| HN-E03 | _generate_policy_fingerprint os.walk例外 | `os.walk()` が例外 | `"fingerprint-generation-error"` |
| HN-E04 | _sanitize_resource_for_opensearch 変換例外 | `json.dumps` が例外を送出 | フォールバック構造体 |
| HN-E05 | _normalize_resource_fields 変換例外 | `json.dumps` が例外を送出 | フォールバック構造体 |
| HN-E06 | _sanitize_custodian_metadata 例外 | `copy.deepcopy` が例外 | 最小限メタデータ |
| HN-E07 | _determine_resource_type metadataなし | `metadata=None` | リソースからの推定 |

### 3.1 ファイル操作 異常系

```python
class TestHelperFunctionsErrors:
    """helper_functions エラーテスト"""

    def test_load_metadata_invalid_json(self, tmp_path):
        """HN-E01: 不正なJSONファイルの場合はエラーログを出力し空辞書を返す

        helper_functions.py:51-53 の例外分岐をカバー
        """
        # Arrange
        from app.jobs.utils.helper_functions import _load_metadata_from_file
        invalid_file = tmp_path / "metadata.json"
        invalid_file.write_text("{invalid json content", encoding="utf-8")
        logger = MagicMock()

        # Act
        result = _load_metadata_from_file(str(invalid_file), logger)

        # Assert
        assert result == {}
        logger.error.assert_called_once()
        assert "metadata.jsonの読み込みエラー" in logger.error.call_args[0][0]

    def test_generate_fingerprint_invalid_json(self, tmp_path):
        """HN-E02: 不正なmetadata.jsonはスキップして他のポリシーを処理

        helper_functions.py:126-127 の例外スキップをカバー
        """
        # Arrange
        from app.jobs.utils.helper_functions import _generate_policy_fingerprint

        # 有効なポリシー
        valid_dir = tmp_path / "valid_policy"
        valid_dir.mkdir()
        valid_metadata = {"policy": {"name": "valid", "resource": "ec2", "filters": [], "actions": []}}
        (valid_dir / "metadata.json").write_text(
            json.dumps(valid_metadata), encoding="utf-8"
        )

        # 不正なポリシー
        invalid_dir = tmp_path / "invalid_policy"
        invalid_dir.mkdir()
        (invalid_dir / "metadata.json").write_text("{broken", encoding="utf-8")

        # Act
        result = _generate_policy_fingerprint(str(tmp_path))

        # Assert
        assert isinstance(result, str)
        assert len(result) == 32

    def test_generate_fingerprint_walk_exception(self):
        """HN-E03: os.walkで例外発生時のフォールバック

        helper_functions.py:138-139 の最外try/except分岐をカバー。
        os.walk()が例外を送出した場合、"fingerprint-generation-error"を返す。
        """
        # Arrange
        from app.jobs.utils.helper_functions import _generate_policy_fingerprint

        # Act
        with patch("os.walk", side_effect=PermissionError("access denied")):
            result = _generate_policy_fingerprint("/nonexistent")

        # Assert
        assert result == "fingerprint-generation-error"
```

### 3.2 正規化 異常系

```python
class TestFieldNormalizerErrors:
    """field_normalizers エラーテスト"""

    def test_sanitize_resource_internal_conversion_error(self):
        """HN-E04: _convert_complex_fields内部で例外発生時のフォールバック構造体

        field_normalizers.py:103-112 のtry/except分岐をカバー。

        【注意】copy.deepcopy(L20)はtryブロックの外にあるため、
        deepcopyではなくtry内の処理（json.dumps）で例外を発生させる。
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _sanitize_resource_for_opensearch
        resource = {
            "InstanceId": "i-123",
            "State": {"Name": "running"}  # force_stringifyでjson.dumpsが呼ばれる
        }

        # Act
        # json.dumpsがforce_stringify処理中に例外を送出するようモック
        original_dumps = json.dumps
        call_count = [0]

        def failing_dumps(*args, **kwargs):
            call_count[0] += 1
            # deepcopy後の内部処理中のjson.dumps呼び出しで例外
            if call_count[0] == 1:
                raise TypeError("simulated serialization error")
            return original_dumps(*args, **kwargs)

        with patch("app.jobs.utils.field_normalizers.json.dumps", side_effect=failing_dumps):
            result = _sanitize_resource_for_opensearch(resource)

        # Assert
        assert "original_resource_json" in result
        assert "sanitization_error" in result

    def test_normalize_resource_fields_internal_error(self):
        """HN-E05: _convert_problematic_fields内部で例外発生時のフォールバック構造体

        field_normalizers.py:163-171 のtry/except分岐をカバー。

        【注意】copy.deepcopy(L125)はtryブロックの外にあるため、
        deepcopyではなくtry内の処理（json.dumps）で例外を発生させる。
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _normalize_resource_fields
        resource = {
            "InstanceId": "i-123",
            "State": {"Name": "running"}  # problematicフィールドでjson.dumpsが呼ばれる
        }

        # Act
        original_dumps = json.dumps
        call_count = [0]

        def failing_dumps(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise TypeError("simulated serialization error")
            return original_dumps(*args, **kwargs)

        with patch("app.jobs.utils.field_normalizers.json.dumps", side_effect=failing_dumps):
            result = _normalize_resource_fields(resource)

        # Assert
        assert "original_resource_json" in result
        assert "conversion_error" in result
        assert "resource_id" in result

    def test_sanitize_custodian_metadata_exception(self):
        """HN-E06: deepcopyで例外発生時の最小限メタデータ

        field_normalizers.py:226-231 の例外分岐をカバー。
        _sanitize_custodian_metadata ではdeepcopyがtry内(L216)にあるため、
        deepcopy例外でフォールバックが動作する。
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _sanitize_custodian_metadata
        metadata = {"policy": {"filters": []}}

        # Act
        with patch("app.jobs.utils.field_normalizers.copy.deepcopy", side_effect=Exception("error")):
            result = _sanitize_custodian_metadata(metadata)

        # Assert
        assert "sanitization_error" in result
        assert "original_metadata_keys" in result
        assert "policy" in result["original_metadata_keys"]

    def test_determine_resource_type_none_metadata(self):
        """HN-E07: metadataがNoneの場合はリソースから推定

        helper_functions.py:69 の条件分岐をカバー
        """
        # Arrange
        from app.jobs.utils.helper_functions import _determine_resource_type
        resource = {"InstanceId": "i-123"}

        # Act
        result = _determine_resource_type(resource, None, "aws")

        # Assert
        assert result == "aws.ec2"
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| HN-SEC-01 | 悪意あるパス入力時の現行挙動確認 | `"../../../etc/passwd"` | `{}` (ファイル不存在 or JSON解析失敗) |
| HN-SEC-02 | 大量フィールドリソース処理 | 1000フィールドのdict | クラッシュせず正常完了 |
| HN-SEC-03 | JSON注入耐性（value） | `'"; DROP TABLE users; --'` | 文字列としてそのまま保存 |
| HN-SEC-04 | 深いネスト構造の処理 | 500階層のネストdict | クラッシュせず処理完了 |

```python
@pytest.mark.security
class TestHelperNormalizerSecurity:
    """ヘルパー・正規化基盤セキュリティテスト"""

    def test_malicious_path_input_behavior(self, tmp_path):
        """HN-SEC-01: 悪意あるパス入力時の現行挙動確認

        _load_metadata_from_fileにパストラバーサルを含むパスが渡された場合の
        現行挙動を確認する。実装にはパス検証やベースディレクトリ制限がないため、
        本テストは「防御機構の検証」ではなく「挙動の記録」として位置づける。
        実運用ではパスは内部生成のため低リスク。
        """
        # Arrange
        from app.jobs.utils.helper_functions import _load_metadata_from_file
        logger = MagicMock()
        malicious_path = str(tmp_path / ".." / ".." / "etc" / "passwd")

        # Act
        result = _load_metadata_from_file(malicious_path, logger)

        # Assert
        # ファイル不存在で空辞書、存在してもJSON解析エラーで空辞書
        # 注意: 実装にパス検証がないため、これは防御ではなく挙動確認
        assert result == {}
        # warningかerrorのいずれかが記録される
        assert logger.warning.called or logger.error.called

    def test_large_resource_does_not_crash(self):
        """HN-SEC-02: 大量のフィールドを持つリソースデータの安全な処理

        1000フィールドのリソースでクラッシュせず正常に処理されること、
        force_stringifyフィールドが期待通り文字列化されることを確認。
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _sanitize_resource_for_opensearch
        resource = {f"field_{i}": f"value_{i}" for i in range(1000)}
        resource["State"] = {"Name": "running"}

        # Act
        result = _sanitize_resource_for_opensearch(resource)

        # Assert
        assert isinstance(result, dict)
        assert len(result) >= 1000
        assert isinstance(result["State"], str)

    def test_json_injection_in_filter_value(self):
        """HN-SEC-03: フィルターvalue内のJSON注入文字列が安全に文字列化される

        SQLインジェクション風の文字列がvalueとして渡された場合、
        str()変換によりそのまま文字列として保存されることを確認。
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _normalize_filter_values
        malicious_value = '"; DROP TABLE users; --'
        filters = [{"type": "value", "value": malicious_value}]

        # Act
        result = _normalize_filter_values(filters)

        # Assert
        assert result[0]["value"] == malicious_value
        assert isinstance(result[0]["value"], str)

    def test_deep_nesting_does_not_crash(self):
        """HN-SEC-04: 深くネストしたオブジェクトでのスタックオーバーフロー防止

        _sanitize_resource_for_opensearch の再帰関数が、
        500階層のネスト構造を処理してもクラッシュしないことを確認。
        Pythonのデフォルト再帰深度制限(1000)以内で動作する。
        """
        # Arrange
        from app.jobs.utils.field_normalizers import _sanitize_resource_for_opensearch
        resource = {"level": 0}
        current = resource
        for i in range(1, 500):
            current["nested"] = {"level": i}
            current = current["nested"]

        # Act
        result = _sanitize_resource_for_opensearch(resource)

        # Assert
        assert isinstance(result, dict)
        assert result["level"] == 0
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_utils_module` | テスト間のモジュール状態リセット | function | Yes |

### 共通フィクスチャ定義

```python
# test/unit/jobs/utils/conftest.py
import sys
import pytest


@pytest.fixture(autouse=True)
def reset_utils_module():
    """テストごとにモジュールのグローバル状態をリセット

    helper_functions と field_normalizers はステートレスだが、
    importキャッシュのクリーンアップにより独立したテスト環境を保証する。
    対象は app.jobs.utils 配下のみに限定し、無関係なモジュールへの影響を防ぐ。
    """
    yield
    # テスト後にクリーンアップ（app.jobs.utils のみ）
    modules_to_remove = [
        key for key in sys.modules
        if key.startswith("app.jobs.utils")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]
```

---

## 6. テスト実行例

```bash
# ヘルパー・正規化基盤テストのみ実行
pytest test/unit/jobs/utils/test_helper_normalizer.py -v

# 特定のテストクラスのみ実行
pytest test/unit/jobs/utils/test_helper_normalizer.py::TestExtractResourceId -v

# カバレッジ付きで実行
pytest test/unit/jobs/utils/test_helper_normalizer.py \
  --cov=app.jobs.utils.helper_functions \
  --cov=app.jobs.utils.field_normalizers \
  --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/jobs/utils/test_helper_normalizer.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 51 | HN-001 〜 HN-047（枝番含む） |
| 異常系 | 7 | HN-E01 〜 HN-E07 |
| セキュリティ | 4 | HN-SEC-01 〜 HN-SEC-04 |
| **合計** | **62** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestGetCustodianVersion` | HN-001〜HN-003 | 3 |
| `TestExtractResourceId` | HN-004〜HN-010 | 7 |
| `TestLoadMetadataFromFile` | HN-011〜HN-012 | 2 |
| `TestDetermineResourceType` | HN-013〜HN-020a | 9 |
| `TestGeneratePolicyFingerprint` | HN-021〜HN-023 | 3 |
| `TestSanitizeResourceForOpensearch` | HN-024〜HN-029（枝番含む） | 9 |
| `TestNormalizeResourceFields` | HN-030〜HN-031 | 2 |
| `TestNormalizeNumericFields` | HN-032〜HN-034 | 3 |
| `TestSanitizeCustodianMetadata` | HN-035〜HN-036 | 2 |
| `TestNormalizeFilterValues` | HN-037〜HN-042 | 6 |
| `TestNormalizeNestedFilterObject` | HN-043〜HN-047 | 5 |
| `TestHelperFunctionsErrors` | HN-E01〜HN-E03 | 3 |
| `TestFieldNormalizerErrors` | HN-E04〜HN-E07 | 4 |
| `TestHelperNormalizerSecurity` | HN-SEC-01〜HN-SEC-04 | 4 |

### 実装失敗が予想されるテスト

| テストID | 失敗理由 | 修正方針 |
|---------|---------|---------|
| HN-E04 | `_sanitize_resource_for_opensearch` の `json.dumps` モック方式は呼び出し回数制御が複雑で、意図した箇所以外で例外が発生する可能性あり | テスト実装時に `side_effect` のカウンタ調整、またはカスタムオブジェクトの `__repr__` で例外を発生させる方式に変更 |
| HN-E05 | HN-E04と同様の理由 | 同上 |

### 注意事項

- `@pytest.mark.security` マーカーは `pyproject.toml` に `markers = ["security: セキュリティ関連テスト"]` の登録が必要
- `tmp_path` フィクスチャはpytest組み込みのため追加パッケージ不要
- `_get_custodian_version` は**関数内import**（`helper_functions.py:11`）のため、`pkg_resources.get_distribution` を直接パッチする（モジュールレベルのパッチは無効）
- `_sanitize_resource_for_opensearch` と `_normalize_resource_fields` は **`copy.deepcopy` が `try` ブロックの外** にあるため、deepcopy例外でフォールバックは動作しない。try内の処理で例外を発生させる必要がある
- 環境変数パッチは不要（テスト対象モジュールは `config.py` をimportしない）

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `_generate_policy_fingerprint` はファイルシステム依存 | 実際のディレクトリ構造が必要 | `tmp_path` フィクスチャで一時ディレクトリを生成 |
| 2 | `_sanitize_resource_for_opensearch` の内部関数はサイズ判定に `str()` 変換を使用 | 大きなオブジェクトでのパフォーマンス懸念 | テストでは現実的なサイズのデータで検証 |
| 3 | `pkg_resources` パッケージ自体が存在しない環境では `patch('pkg_resources.get_distribution')` が失敗する可能性あり | テスト結果の不安定性 | `patch.dict(sys.modules, {'pkg_resources': MagicMock()})` で代替するか、`setuptools` を開発依存に含める |
| 4 | `_sanitize_resource_for_opensearch` / `_normalize_resource_fields` の再帰関数は循環参照を検出しない | `RecursionError` で異常終了する可能性 | 実運用ではCloud Custodian出力が循環参照を含まないため低リスク |
| 5 | HN-E04/E05 の `json.dumps` モック方式は呼び出し回数の正確な制御が困難 | テスト実装時に調整が必要 | 代替手段としてカスタム非シリアライズオブジェクトの注入を検討 |
