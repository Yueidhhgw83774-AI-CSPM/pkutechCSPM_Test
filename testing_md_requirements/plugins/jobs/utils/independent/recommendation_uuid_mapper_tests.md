# jobs/utils UUID マッピング + AWSリソースカウント テストケース (#17h-3)

## 1. 概要

ポリシーと推奨事項UUIDの関連付け機能。メタデータファイルからUUID抽出→フォールバックUUID生成の2段階戦略でポリシーごとに一意なUUIDを付与する。`aws_resource_counter.py` はAWS API呼び出し機能がコメントアウトされ、スタブ関数2個のみがアクティブ。

### 1.1 主要機能

| 機能 | モジュール | 説明 |
|------|-----------|------|
| `extract_recommendation_uuid_from_policy` | mapper | ポリシーからUUID抽出（フォールバック付き） |
| `extract_recommendation_uuids_batch` | mapper | 全ポリシーUUID一括抽出 |
| `normalize_recommendation_uuid` | mapper | UUID正規化 |
| `get_uuid_mapping_summary` | mapper | UUIDマッピング統計 |
| `_extract_uuid_from_metadata` | mapper | メタデータファイルからUUID抽出 |
| `_generate_fallback_uuid` | mapper | ハッシュベースのフォールバックUUID生成 |
| `_is_valid_uuid_format` | mapper | UUID形式検証 |
| `get_total_resources_from_metadata_api_stats` | counter | スタブ（固定値返却） |
| `get_total_resources_for_policy` | counter | スタブ（固定値返却） |

### 1.2 カバレッジ目標: 95%

> **注記**: `recommendation_uuid_mapper.py` は外部サービス接続なし（ファイルI/Oのみ）で `tmp_path` による実ファイルテストが可能。`aws_resource_counter.py` はスタブのみのため100%カバレッジが自明。

### 1.3 主要ファイル

| ファイル | パス | 行数 |
|---------|------|------|
| テスト対象1 | `app/jobs/utils/recommendation_uuid_mapper.py` | 252行 |
| テスト対象2 | `app/jobs/utils/aws_resource_counter.py` | 136行（アクティブ48行） |
| テストコード | `test/unit/jobs/utils/test_recommendation_uuid_mapper.py` | 新規作成 |
| conftest | `test/unit/jobs/utils/conftest.py`（#17aと共有） |

### 1.4 依存関係

| 依存 | 種類 | パッチ対象 |
|------|------|-----------|
| `TaskLogger` | `app.jobs.common.logging` | `app.jobs.utils.recommendation_uuid_mapper.TaskLogger` |
| `json` | 標準ライブラリ | パッチ不要（`tmp_path` で実ファイル使用） |
| `os` | 標準ライブラリ | 異常系のみ `patch.object(os, "listdir")` |
| `hashlib` | 標準ライブラリ | パッチ不要 |

> **注記**: 正常系テストでは `tmp_path` で実ディレクトリ・ファイルを作成し、ファイルI/Oをモックしない方針。異常系の特定条件（`os.listdir` 例外等）のみモックを使用する。`TaskLogger` は全テストで autouse モックを適用する（`normalize_recommendation_uuid`, `_generate_fallback_uuid`, `_is_valid_uuid_format`, `get_uuid_mapping_summary` は内部で `TaskLogger` を呼び出さないが、autouse のため自動適用される。副作用なし）。

### 1.5 主要分岐マップ

| メソッド | 分岐数 | 主要分岐 |
|---------|--------|---------|
| `extract_recommendation_uuid_from_policy` | 3 | L39 UUID有効→返却, L39 UUID無効→フォールバック, L48 Exception→フォールバック |
| `extract_recommendation_uuids_batch` | 5 | L71 output_dir空/None, L71 存在しない, L78 非ディレクトリskip, L82 正常処理, L88 Exception |
| `normalize_recommendation_uuid` | 5 | L103 None/空, L103 空白のみ, L108 有効UUID, L112 "unknown-"プレフィックス, L116 その他 |
| `_extract_uuid_from_metadata` | 6 | L137 ファイル不在, L150-154 policy_metadata内発見, L153 無効値skip, L157-162 custom内発見, L164 未発見, L166 Exception |
| `_generate_fallback_uuid` | 4 | L181 None, L181 空文字, L188 "policy-"プレフィックス, L192 ハッシュ生成 |
| `_is_valid_uuid_format` | 6 | L208 falsy, L208 非文字列, L212-217 標準UUID有効, L217 非英数字→False, L220 有効プレフィックス, L225 不一致→False |
| `get_uuid_mapping_summary` | 3 | L246 "unknown", L248 "unknown-"/"generated-", L250 その他 |

> **合計**: 32分岐（全分岐をテストで直接カバー）

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| RUM-001 | メタデータからUUID取得成功 | metadata.json に uuid フィールド | 抽出されたUUID文字列 |
| RUM-002 | メタデータ "unknown" でフォールバック | uuid="unknown" | フォールバックUUID |
| RUM-003 | メタデータ None でフォールバック | uuid=None | フォールバックUUID |
| RUM-004 | 一括抽出: 複数ポリシー | 3ポリシーディレクトリ | 3件のUUIDマッピング |
| RUM-005 | 一括抽出: 非ディレクトリをスキップ | dir + file | dirのみマッピング |
| RUM-006 | 一括抽出: 空ディレクトリ | 空dir | 空dict |
| RUM-007 | UUID正規化: 標準UUID通過 | "550e8400-e29b-41d4-a716-446655440000" | そのまま返却 |
| RUM-008 | UUID正規化: "unknown-"プレフィックス通過 | "unknown-abc" | そのまま返却 |
| RUM-009 | UUID正規化: その他形式 | "custom-uuid" | "normalized-custom-uuid" |
| RUM-010 | UUID正規化: 空白トリム | " abc-uuid " | "normalized-abc-uuid" |
| RUM-011 | メタデータ抽出: "uuid"フィールド | {"policy":{"metadata":{"uuid":"abc"}}} | "abc" |
| RUM-012 | メタデータ抽出: "recommendation_uuid"フィールド | {"policy":{"metadata":{"recommendation_uuid":"def"}}} | "def" |
| RUM-013 | メタデータ抽出: customメタデータ内 | {"policy":{"metadata":{"custom":{"uuid":"ghi"}}}} | "ghi" |
| RUM-014 | メタデータ抽出: ファイル不在 | 存在しないパス | None |
| RUM-015 | メタデータ抽出: UUIDフィールド空値 | {"policy":{"metadata":{"uuid":""}}} | None |
| RUM-016 | フォールバック: "policy-"プレフィックス | "policy-test" | "recommendation-policy-test" |
| RUM-017 | フォールバック: ハッシュ生成 | "my-custom-policy" | "generated-my-custom-policy-{hash}" |
| RUM-018 | フォールバック: 決定性検証 | 同一名2回 | 同一結果 |
| RUM-019 | UUID形式: 標準UUID有効 | "550e8400-e29b-41d4-a716-446655440000" | True |
| RUM-020 | UUID形式: 有効プレフィックス (parametrize) | "recommendation-xxx" 等4種 | True |
| RUM-021 | UUID形式: 不一致 | "random-string" | False |
| RUM-022 | マッピング統計: 混合データ | valid+fallback+unknown | 正確なカウント |
| RUM-023 | マッピング統計: 空dict | {} | 全カウント0 |
| ARC-001 | API統計スタブ返却値 | 任意引数 | {"before_filter":0,"after_filter":0} |
| ARC-002 | ポリシーリソースカウントスタブ返却値 | 任意引数 | {"before_filter":0,"after_filter":0} |

### 2.1 extract_recommendation_uuid_from_policy テスト

```python
# test/unit/jobs/utils/test_recommendation_uuid_mapper.py
import pytest
import json
import os
import hashlib
from unittest.mock import patch, MagicMock

from app.jobs.utils.recommendation_uuid_mapper import (
    extract_recommendation_uuid_from_policy,
    extract_recommendation_uuids_batch,
    normalize_recommendation_uuid,
    get_uuid_mapping_summary,
    _extract_uuid_from_metadata,
    _generate_fallback_uuid,
    _is_valid_uuid_format,
)
from app.jobs.utils.aws_resource_counter import (
    get_total_resources_from_metadata_api_stats,
    get_total_resources_for_policy,
)


class TestExtractRecommendationUuidFromPolicy:
    """ポリシーからのUUID抽出テスト"""

    def test_metadata_uuid_found(self, tmp_path, mock_task_logger):
        """RUM-001: メタデータからUUID取得成功

        L39 の uuid and uuid != "unknown" → True 分岐をカバー
        """
        # Arrange
        policy_dir = tmp_path / "test-policy"
        policy_dir.mkdir()
        metadata = {"policy": {"metadata": {"uuid": "abc-123-def"}}}
        (policy_dir / "metadata.json").write_text(json.dumps(metadata))

        # Act
        result = extract_recommendation_uuid_from_policy(
            "test-policy", str(tmp_path), "job-1"
        )

        # Assert
        assert result == "abc-123-def"

    def test_metadata_returns_unknown_triggers_fallback(self, tmp_path, mock_task_logger):
        """RUM-002: メタデータが "unknown" を返す場合フォールバック

        L39 の uuid != "unknown" → False 分岐をカバー
        """
        # Arrange
        policy_dir = tmp_path / "test-policy"
        policy_dir.mkdir()
        metadata = {"policy": {"metadata": {"uuid": "unknown"}}}
        (policy_dir / "metadata.json").write_text(json.dumps(metadata))

        # Act
        result = extract_recommendation_uuid_from_policy(
            "test-policy", str(tmp_path), "job-1"
        )

        # Assert
        # フォールバックUUIDが生成される（"unknown" ではない）
        assert result != "unknown"
        assert "test-policy" in result or result.startswith("generated-")

    def test_metadata_returns_none_triggers_fallback(self, tmp_path, mock_task_logger):
        """RUM-003: メタデータがNoneを返す場合フォールバック

        L39 の uuid が falsy → False 分岐をカバー
        """
        # Arrange
        policy_dir = tmp_path / "test-policy"
        policy_dir.mkdir()
        # UUIDフィールドなしのメタデータ
        metadata = {"policy": {"metadata": {}}}
        (policy_dir / "metadata.json").write_text(json.dumps(metadata))

        # Act
        result = extract_recommendation_uuid_from_policy(
            "test-policy", str(tmp_path), "job-1"
        )

        # Assert
        assert result != "unknown"
        assert isinstance(result, str)
        assert len(result) > 0
```

### 2.2 extract_recommendation_uuids_batch テスト

```python
class TestExtractRecommendationUuidsBatch:
    """一括UUID抽出テスト"""

    def test_multiple_policy_directories(self, tmp_path, mock_task_logger):
        """RUM-004: 複数ポリシーディレクトリの一括抽出

        L76-83 のループ正常処理をカバー
        """
        # Arrange
        for name in ["policy-a", "policy-b", "policy-c"]:
            d = tmp_path / name
            d.mkdir()
            metadata = {"policy": {"metadata": {"uuid": f"uuid-{name}"}}}
            (d / "metadata.json").write_text(json.dumps(metadata))

        # Act
        result = extract_recommendation_uuids_batch(str(tmp_path), "job-1")

        # Assert
        assert len(result) == 3
        assert "policy-a" in result
        assert "policy-b" in result
        assert "policy-c" in result

    def test_skip_non_directory_entries(self, tmp_path, mock_task_logger):
        """RUM-005: 非ディレクトリエントリをスキップ

        L78 の not os.path.isdir → continue をカバー
        """
        # Arrange
        d = tmp_path / "real-policy"
        d.mkdir()
        metadata = {"policy": {"metadata": {"uuid": "uuid-real"}}}
        (d / "metadata.json").write_text(json.dumps(metadata))
        # ファイルエントリ（ディレクトリではない）
        (tmp_path / "not-a-dir.txt").write_text("dummy")

        # Act
        result = extract_recommendation_uuids_batch(str(tmp_path), "job-1")

        # Assert
        assert len(result) == 1
        assert "real-policy" in result
        assert "not-a-dir.txt" not in result

    def test_empty_directory(self, tmp_path, mock_task_logger):
        """RUM-006: 空ディレクトリ → 空dict

        L76 のループが0回実行されるケースをカバー
        """
        # Arrange（tmp_pathは空）

        # Act
        result = extract_recommendation_uuids_batch(str(tmp_path), "job-1")

        # Assert
        assert result == {}
```

### 2.3 normalize_recommendation_uuid テスト

```python
class TestNormalizeRecommendationUuid:
    """UUID正規化テスト"""

    def test_standard_uuid_passthrough(self):
        """RUM-007: 標準UUID形式はそのまま返却

        L108 の _is_valid_uuid_format → True をカバー
        """
        # Arrange
        uuid = "550e8400-e29b-41d4-a716-446655440000"

        # Act
        result = normalize_recommendation_uuid(uuid)

        # Assert
        assert result == uuid

    def test_unknown_prefix_passthrough(self):
        """RUM-008: "unknown-"プレフィックスはそのまま返却

        L112 の uuid.startswith("unknown-") → True をカバー
        """
        # Arrange
        uuid = "unknown-empty-policy"

        # Act
        result = normalize_recommendation_uuid(uuid)

        # Assert
        assert result == "unknown-empty-policy"

    def test_other_format_normalized(self):
        """RUM-009: その他形式は "normalized-" プレフィックス付与

        L116 の else 分岐をカバー
        """
        # Arrange
        uuid = "custom-uuid-value"

        # Act
        result = normalize_recommendation_uuid(uuid)

        # Assert
        assert result == "normalized-custom-uuid-value"

    def test_whitespace_trimmed(self):
        """RUM-010: 前後の空白がトリムされる

        L107 の uuid.strip() をカバー
        """
        # Arrange
        uuid = "  custom-value  "

        # Act
        result = normalize_recommendation_uuid(uuid)

        # Assert
        assert result == "normalized-custom-value"
```

### 2.4 _extract_uuid_from_metadata テスト

```python
class TestExtractUuidFromMetadata:
    """メタデータファイルからのUUID抽出テスト"""

    def test_uuid_field_in_policy_metadata(self, tmp_path, mock_task_logger):
        """RUM-011: policy_metadata内の "uuid" フィールド

        L150-154 の uuid_fields ループで最初のマッチをカバー
        """
        # Arrange
        policy_dir = tmp_path / "test-policy"
        policy_dir.mkdir()
        metadata = {"policy": {"metadata": {"uuid": "found-uuid-123"}}}
        (policy_dir / "metadata.json").write_text(json.dumps(metadata))
        _, mock_logger = mock_task_logger

        # Act
        result = _extract_uuid_from_metadata(
            "test-policy", str(tmp_path), mock_logger
        )

        # Assert
        assert result == "found-uuid-123"

    def test_recommendation_uuid_field(self, tmp_path, mock_task_logger):
        """RUM-012: "recommendation_uuid" フィールドで取得

        L148 の uuid_fields 順序（"uuid" なし → "recommendation_uuid" で発見）をカバー
        """
        # Arrange
        policy_dir = tmp_path / "test-policy"
        policy_dir.mkdir()
        metadata = {
            "policy": {"metadata": {"recommendation_uuid": "rec-uuid-456"}}
        }
        (policy_dir / "metadata.json").write_text(json.dumps(metadata))
        _, mock_logger = mock_task_logger

        # Act
        result = _extract_uuid_from_metadata(
            "test-policy", str(tmp_path), mock_logger
        )

        # Assert
        assert result == "rec-uuid-456"

    def test_uuid_in_custom_metadata(self, tmp_path, mock_task_logger):
        """RUM-013: custom メタデータ内のUUID

        L157-162 の custom_metadata 検索をカバー
        """
        # Arrange
        policy_dir = tmp_path / "test-policy"
        policy_dir.mkdir()
        metadata = {
            "policy": {"metadata": {"custom": {"uuid": "custom-uuid-789"}}}
        }
        (policy_dir / "metadata.json").write_text(json.dumps(metadata))
        _, mock_logger = mock_task_logger

        # Act
        result = _extract_uuid_from_metadata(
            "test-policy", str(tmp_path), mock_logger
        )

        # Assert
        assert result == "custom-uuid-789"

    def test_metadata_file_not_exists(self, tmp_path, mock_task_logger):
        """RUM-014: メタデータファイル不在 → None

        L137 の not os.path.exists → None をカバー
        """
        # Arrange（ディレクトリなし）
        _, mock_logger = mock_task_logger

        # Act
        result = _extract_uuid_from_metadata(
            "missing-policy", str(tmp_path), mock_logger
        )

        # Assert
        assert result is None

    def test_uuid_field_empty_value_skipped(self, tmp_path, mock_task_logger):
        """RUM-015: UUIDフィールドが空文字/空白のみ → スキップしてNone

        L153 の条件 `uuid and isinstance(uuid, str) and uuid.strip()` で、
        uuid="" は falsy でスキップ、recommendation_uuid="  " は
        uuid.strip() が "" で falsy となりスキップ。
        全 uuid_fields を走査後、L164 return None に到達する。
        """
        # Arrange
        policy_dir = tmp_path / "test-policy"
        policy_dir.mkdir()
        metadata = {
            "policy": {"metadata": {"uuid": "", "recommendation_uuid": "  "}}
        }
        (policy_dir / "metadata.json").write_text(json.dumps(metadata))
        _, mock_logger = mock_task_logger

        # Act
        result = _extract_uuid_from_metadata(
            "test-policy", str(tmp_path), mock_logger
        )

        # Assert
        assert result is None
```

### 2.5 _generate_fallback_uuid テスト

```python
class TestGenerateFallbackUuid:
    """フォールバックUUID生成テスト"""

    def test_policy_prefix(self):
        """RUM-016: "policy-" プレフィックスで "recommendation-" 形式生成

        L185 で normalized_name = policy_name.strip().lower() により小文字化後、
        L188 の startswith("policy-") → True をカバー。
        入力が既に小文字のため変換なし。
        """
        # Arrange
        policy_name = "policy-ec2-check"

        # Act
        result = _generate_fallback_uuid(policy_name)

        # Assert
        assert result == "recommendation-policy-ec2-check"

    def test_hash_based_generation(self):
        """RUM-017: 通常ポリシー名でハッシュベースUUID生成

        L192-195 の hashlib.md5 ベース生成をカバー。
        L185 で小文字化されるため、期待値も小文字で計算する。
        """
        # Arrange
        policy_name = "my-custom-policy"
        expected_hash = hashlib.md5("my-custom-policy".encode()).hexdigest()[:8]

        # Act
        result = _generate_fallback_uuid(policy_name)

        # Assert
        assert result == f"generated-my-custom-policy-{expected_hash}"

    def test_deterministic_output(self):
        """RUM-018: 同一入力で同一結果（決定性検証）

        L192 の hashlib.md5 の決定性をカバー
        """
        # Arrange
        policy_name = "deterministic-test"

        # Act
        result1 = _generate_fallback_uuid(policy_name)
        result2 = _generate_fallback_uuid(policy_name)

        # Assert
        assert result1 == result2
```

### 2.6 _is_valid_uuid_format テスト

```python
class TestIsValidUuidFormat:
    """UUID形式検証テスト"""

    def test_standard_uuid_valid(self):
        """RUM-019: 標準UUID形式 → True

        L212-217 の全条件（長さ36、ダッシュ4、パート長正、英数字）をカバー
        """
        # Arrange
        uuid = "550e8400-e29b-41d4-a716-446655440000"

        # Act
        result = _is_valid_uuid_format(uuid)

        # Assert
        assert result is True

    @pytest.mark.parametrize("prefix,value", [
        ("recommendation-", "recommendation-test-uuid"),
        ("policy-", "policy-ec2-check"),
        ("generated-", "generated-name-abc12345"),
        ("normalized-", "normalized-custom"),
    ])
    def test_valid_prefixes(self, prefix, value):
        """RUM-020: 有効プレフィックス → True

        L220-223 の valid_prefixes ループをカバー
        """
        # Arrange / Act
        result = _is_valid_uuid_format(value)

        # Assert
        assert result is True

    def test_invalid_format_returns_false(self):
        """RUM-021: 無効な形式 → False

        L225 の最終 return False をカバー
        """
        # Arrange
        uuid = "random-string-not-uuid"

        # Act
        result = _is_valid_uuid_format(uuid)

        # Assert
        assert result is False
```

### 2.7 get_uuid_mapping_summary テスト

```python
class TestGetUuidMappingSummary:
    """UUIDマッピング統計テスト"""

    def test_mixed_mapping(self):
        """RUM-022: 混合データで正確なカウント

        get_uuid_mapping_summary は _is_valid_uuid_format を呼ばず、
        単純な文字列比較のみで分類する:
        - L246: uuid == "unknown" → unknown_uuids
        - L248: uuid.startswith(("unknown-", "generated-")) → fallback_uuids
        - L250: else → valid_uuids
        """
        # Arrange
        mapping = {
            "policy-a": "550e8400-e29b-41d4-a716-446655440000",
            "policy-b": "recommendation-policy-b",
            "policy-c": "unknown",
            "policy-d": "unknown-empty-policy",
            "policy-e": "generated-test-abc12345",
        }

        # Act
        result = get_uuid_mapping_summary(mapping)

        # Assert
        assert result["total_policies"] == 5
        # L250 else: "unknown"でも"unknown-"/"generated-"でもない
        assert result["valid_uuids"] == 2      # policy-a (UUID形式), policy-b (recommendation-)
        # L248: "unknown-"または"generated-"プレフィックス
        assert result["fallback_uuids"] == 2    # policy-d (unknown-), policy-e (generated-)
        # L246: 完全一致 "unknown"
        assert result["unknown_uuids"] == 1     # policy-c

    def test_empty_mapping(self):
        """RUM-023: 空dictで全カウント0

        uuid_mapping.values() ループが0回実行されるケースをカバー
        """
        # Arrange / Act
        result = get_uuid_mapping_summary({})

        # Assert
        assert result == {
            "total_policies": 0,
            "valid_uuids": 0,
            "fallback_uuids": 0,
            "unknown_uuids": 0,
        }
```

### 2.8 aws_resource_counter スタブテスト

```python
class TestAwsResourceCounter:
    """AWSリソースカウンター スタブテスト"""

    def test_get_total_resources_from_metadata_api_stats(self):
        """ARC-001: メタデータAPI統計スタブが固定値を返す

        get_total_resources_from_metadata_api_stats の固定値返却をカバー
        """
        # Arrange / Act
        result = get_total_resources_from_metadata_api_stats(
            custodian_output_dir="/tmp/test",
            policy_name="test-policy",
            job_id="job-1",
            region="ap-northeast-1",
            profile=None,
        )

        # Assert
        assert result == {"before_filter": 0, "after_filter": 0}

    def test_get_total_resources_for_policy(self):
        """ARC-002: ポリシーリソースカウントスタブが固定値を返す

        get_total_resources_for_policy の固定値返却をカバー
        """
        # Arrange / Act
        result = get_total_resources_for_policy(
            custodian_output_dir="/tmp/test",
            policy_name="test-policy",
            job_id="job-1",
            region="us-east-1",
            profile="test-profile",
        )

        # Assert
        assert result == {"before_filter": 0, "after_filter": 0}
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| RUM-E01 | UUID抽出で例外 → フォールバック | _extract_uuid_from_metadata が例外 | フォールバックUUID + エラーログ |
| RUM-E02 | 一括抽出: 無効な出力ディレクトリ (parametrize) | output_dir=None / "" | 空dict |
| RUM-E03 | 一括抽出: 存在しないディレクトリ | 不在パス | 空dict |
| RUM-E04 | 一括抽出: os.listdir例外 | os.listdir が PermissionError | 空dict + エラーログ |
| RUM-E05 | UUID正規化: None入力 | uuid=None | "unknown" |
| RUM-E06 | UUID正規化: 空白のみ | uuid="   " | "unknown" |
| RUM-E07 | メタデータ抽出: JSONデコードエラー | 不正JSON | None + 警告ログ |
| RUM-E08 | メタデータ抽出: ファイル読み込み権限エラー | PermissionError | None + 警告ログ |
| RUM-E09 | フォールバック: 空文字 | policy_name="" | "unknown-empty-policy" |
| RUM-E10 | フォールバック: None | policy_name=None | "unknown-empty-policy" |
| RUM-E11 | UUID形式検証: None | uuid_string=None | False |
| RUM-E12 | UUID形式検証: 非文字列 | uuid_string=12345 | False |
| RUM-E13 | UUID形式検証: UUID構造に非英数字 | "550e840!-e29b-..." | False |
| RUM-E14 | UUID形式検証: パート長不正 | 36文字4ダッシュだがパート長不一致 | False |

### 3.1 extract_recommendation_uuid_from_policy 異常系

```python
class TestExtractRecommendationUuidFromPolicyErrors:
    """ポリシーUUID抽出 異常系テスト"""

    def test_exception_triggers_fallback(self, mock_task_logger):
        """RUM-E01: _extract_uuid_from_metadata 内部例外 → フォールバック

        L48-50 の except Exception 分岐をカバー。
        str(e) がエラーログに出力される（SEC-01関連）。
        """
        # Arrange
        with patch(
            "app.jobs.utils.recommendation_uuid_mapper._extract_uuid_from_metadata",
            side_effect=RuntimeError("test error"),
        ):
            # Act
            result = extract_recommendation_uuid_from_policy(
                "test-policy", "/nonexistent", "job-1"
            )

        # Assert
        assert isinstance(result, str)
        assert len(result) > 0
        # フォールバックUUIDが生成されている
        assert "test-policy" in result or result.startswith("generated-")
```

### 3.2 extract_recommendation_uuids_batch 異常系

```python
class TestExtractRecommendationUuidsBatchErrors:
    """一括UUID抽出 異常系テスト"""

    @pytest.mark.parametrize("invalid_dir", [None, ""])
    def test_invalid_output_dir(self, invalid_dir, mock_task_logger):
        """RUM-E02: None/空文字の出力ディレクトリ → 空dict

        L71 の `not output_dir` → True をカバー。
        None と空文字 "" はいずれも falsy のため同じ分岐に入る。
        """
        # Arrange / Act
        result = extract_recommendation_uuids_batch(invalid_dir, "job-1")

        # Assert
        assert result == {}

    def test_nonexistent_directory(self, mock_task_logger):
        """RUM-E03: 存在しないディレクトリ → 空dict

        L71 の not os.path.exists → True をカバー
        """
        # Arrange / Act
        result = extract_recommendation_uuids_batch("/nonexistent/path", "job-1")

        # Assert
        assert result == {}

    def test_os_listdir_exception(self, tmp_path, mock_task_logger):
        """RUM-E04: os.listdir 例外 → 空dict + エラーログ

        L88-90 の except Exception 分岐をカバー。
        patch.object で os モジュールの listdir を直接パッチする。
        """
        # Arrange
        with patch.object(os, "listdir", side_effect=PermissionError("access denied")):
            # Act
            result = extract_recommendation_uuids_batch(str(tmp_path), "job-1")

        # Assert
        assert result == {}
```

### 3.3 normalize_recommendation_uuid 異常系

```python
class TestNormalizeRecommendationUuidErrors:
    """UUID正規化 異常系テスト"""

    def test_none_input(self):
        """RUM-E05: None入力 → "unknown"

        L103 の not uuid → True をカバー
        """
        # Arrange / Act
        result = normalize_recommendation_uuid(None)

        # Assert
        assert result == "unknown"

    def test_whitespace_only(self):
        """RUM-E06: 空白のみ → "unknown"

        L103 の uuid.strip() == "" → True をカバー
        """
        # Arrange / Act
        result = normalize_recommendation_uuid("   ")

        # Assert
        assert result == "unknown"
```

### 3.4 _extract_uuid_from_metadata 異常系

```python
class TestExtractUuidFromMetadataErrors:
    """メタデータUUID抽出 異常系テスト"""

    def test_json_decode_error(self, tmp_path, mock_task_logger):
        """RUM-E07: 不正JSON → None + 警告ログ

        L166-168 の except Exception（json.JSONDecodeError）をカバー
        """
        # Arrange
        policy_dir = tmp_path / "bad-json"
        policy_dir.mkdir()
        (policy_dir / "metadata.json").write_text("{invalid json content")
        _, mock_logger = mock_task_logger

        # Act
        result = _extract_uuid_from_metadata(
            "bad-json", str(tmp_path), mock_logger
        )

        # Assert
        assert result is None
        mock_logger.warning.assert_called_once()

    def test_permission_error(self, tmp_path, mock_task_logger):
        """RUM-E08: ファイル読み込み権限エラー → None + 警告ログ

        L166-168 の except Exception（PermissionError）をカバー
        """
        # Arrange
        policy_dir = tmp_path / "perm-error"
        policy_dir.mkdir()
        (policy_dir / "metadata.json").write_text("{}")
        _, mock_logger = mock_task_logger

        with patch("builtins.open", side_effect=PermissionError("access denied")):
            # Act
            result = _extract_uuid_from_metadata(
                "perm-error", str(tmp_path), mock_logger
            )

        # Assert
        assert result is None
        mock_logger.warning.assert_called_once()
```

### 3.5 _generate_fallback_uuid 異常系

```python
class TestGenerateFallbackUuidErrors:
    """フォールバックUUID生成 異常系テスト"""

    def test_empty_string(self):
        """RUM-E09: 空文字 → "unknown-empty-policy"

        L181 の policy_name.strip() == "" → True をカバー
        """
        # Arrange / Act
        result = _generate_fallback_uuid("")

        # Assert
        assert result == "unknown-empty-policy"

    def test_none_input(self):
        """RUM-E10: None → "unknown-empty-policy"

        L181 の not policy_name → True をカバー
        """
        # Arrange / Act
        result = _generate_fallback_uuid(None)

        # Assert
        assert result == "unknown-empty-policy"
```

### 3.6 _is_valid_uuid_format 異常系

```python
class TestIsValidUuidFormatErrors:
    """UUID形式検証 異常系テスト"""

    def test_none_input(self):
        """RUM-E11: None → False

        L208 の not uuid_string → True をカバー
        """
        # Arrange / Act
        result = _is_valid_uuid_format(None)

        # Assert
        assert result is False

    def test_non_string_input(self):
        """RUM-E12: 非文字列（int） → False

        L208 の not isinstance(uuid_string, str) → True をカバー
        """
        # Arrange / Act
        result = _is_valid_uuid_format(12345)

        # Assert
        assert result is False

    def test_non_alnum_in_uuid_structure(self):
        """RUM-E13: UUID構造だが非英数字文字 → False

        L217 の all(c.isalnum() ...) → False をカバー。
        パート長は 8-4-4-4-12 で正しいが '!' が含まれる。
        """
        # Arrange
        uuid = "550e840!-e29b-41d4-a716-446655440000"

        # Act
        result = _is_valid_uuid_format(uuid)

        # Assert
        assert result is False

    def test_wrong_part_lengths(self):
        """RUM-E14: 36文字4ダッシュだがパート長不正 → False

        入力 "5508e400-e29b41d4-a716-4466-55440000" は:
        - len=36, count('-')=4 → L212 条件 True
        - split('-') → ["5508e400","e29b41d4","a716","4466","55440000"]
        - パート長 [8,8,4,4,8] ≠ 標準 [8,4,4,4,12] → L214 条件 False
        - L220 プレフィックス不一致 → L225 return False
        """
        # Arrange
        uuid = "5508e400-e29b41d4-a716-4466-55440000"

        # Act
        result = _is_valid_uuid_format(uuid)

        # Assert
        assert result is False
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| RUM-SEC-01 | str(e) によるエラー情報のログ露出 | 例外発生 | 例外メッセージがログに含まれないこと |
| RUM-SEC-02 | ポリシー名・UUID のログ露出 | ポリシー名・UUID | ポリシー名・UUIDがinfo/warningログに含まれないこと |
| RUM-SEC-03 | MD5ハッシュ使用のセキュリティ影響 | ポリシー名 | MD5出力が8文字に切り詰められることを確認 |
| RUM-SEC-04 | パストラバーサルによる任意ファイル読み込み | policy_name="../../../etc/passwd" | output_dir 外のファイルが読まれないこと |
| RUM-SEC-05 | ログ注入による偽ログエントリ | policy_name に改行文字 | ログメッセージが単一行であること |

```python
@pytest.mark.security
class TestRecommendationUuidMapperSecurity:
    """UUID マッパー セキュリティテスト"""

    @pytest.mark.xfail(
        strict=True,
        raises=AssertionError,
        reason="L49,L89,L167 で str(e) がログに露出。sanitize_error_message 等の導入が必要"
    )
    def test_str_e_log_exposure(self, mock_task_logger):
        """RUM-SEC-01: str(e) によるエラー情報のログ露出

        L49: logger.error(f"UUID抽出でエラー: {str(e)}")
        L89: logger.error(f"UUID一括抽出でエラー: {str(e)}")
        L167: logger.warning(f"メタデータからUUID抽出失敗 {policy_name}: {str(e)}")

        本テストは L49 経路を代表して検証する。L89/L167 も同一パターン
        （str(e) のログ直接出力）のため、修正時は3箇所すべてを対象とする。

        【実装失敗予定】recommendation_uuid_mapper.py:49,89,167 で
        str(e) がログに直接出力される。
        str(e) 内のパス情報がログに含まれるため、以下のアサートは失敗する。
        """
        # Arrange
        sensitive_error = RuntimeError("/secret/path/metadata.json: permission denied")
        _, mock_logger = mock_task_logger

        with patch(
            "app.jobs.utils.recommendation_uuid_mapper._extract_uuid_from_metadata",
            side_effect=sensitive_error,
        ):
            # Act
            extract_recommendation_uuid_from_policy("test", "/tmp", "job-1")

        # Assert - エラーメッセージにパス情報が含まれないこと
        error_call_args = str(mock_logger.error.call_args)
        assert "/secret/path" not in error_call_args

    @pytest.mark.xfail(
        strict=True,
        raises=AssertionError,
        reason="L40,L45,L72,L85 でポリシー名・UUIDがログに出力される"
    )
    def test_sensitive_data_in_logs(self, tmp_path, mock_task_logger):
        """RUM-SEC-02: ポリシー名・UUID のログ露出

        L40: logger.info(f"ポリシー '{policy_name}' のUUID: {uuid}")
        L45: logger.warning(f"ポリシー '{policy_name}' でフォールバックUUID生成: ...")
        L72: logger.warning(f"出力ディレクトリが存在しません: {output_dir}")
        L85: logger.info(f"{len(uuid_mapping)}個のポリシーUUIDを取得")

        本テストは L40 経路（UUID発見時のinfo）を検証する。
        L45/L72/L85 も同一パターン（機密情報のログ直接出力）。

        【実装失敗予定】recommendation_uuid_mapper.py:40,45 で
        ポリシー名とUUIDがログに直接出力される。
        """
        # Arrange
        policy_dir = tmp_path / "confidential-policy"
        policy_dir.mkdir()
        metadata = {"policy": {"metadata": {"uuid": "secret-uuid-value"}}}
        (policy_dir / "metadata.json").write_text(json.dumps(metadata))
        _, mock_logger = mock_task_logger

        # Act
        extract_recommendation_uuid_from_policy(
            "confidential-policy", str(tmp_path), "job-1"
        )

        # Assert - ポリシー名・UUIDがログに含まれないこと
        all_log_calls = (
            str(mock_logger.info.call_args_list)
            + str(mock_logger.warning.call_args_list)
        )
        assert "confidential-policy" not in all_log_calls
        assert "secret-uuid-value" not in all_log_calls

    def test_md5_truncation_limits_collision_surface(self):
        """RUM-SEC-03: MD5ハッシュが8文字に切り詰められることの確認

        L192-193 で hashlib.md5 を使用し hexdigest()[:8] で切り詰め。
        MD5は暗号学的に安全ではないが、本用途ではフォールバックUUIDの
        一意性担保が目的であり、暗号目的ではない。
        8文字（32bit）への切り詰めで衝突確率が上昇する点を確認。

        注記: この検証は衝突が「起きにくい」ことの確認であり、
        衝突が「起きない」ことの暗号的保証ではない。
        """
        # Arrange - "policy-" で始まらない名前を使用（ハッシュ生成パスを通す）
        name1 = "alpha-check"
        name2 = "beta-check"

        # Act
        uuid1 = _generate_fallback_uuid(name1)
        uuid2 = _generate_fallback_uuid(name2)

        # Assert
        # 異なる入力で異なるUUIDが生成される（衝突しない）
        assert uuid1 != uuid2
        # "generated-{name}-{hash}" 形式のハッシュ部分が8文字であること
        hash_part1 = uuid1.split("-")[-1]
        assert len(hash_part1) == 8
        # 16進数文字のみ
        assert all(c in "0123456789abcdef" for c in hash_part1)

    @pytest.mark.xfail(
        strict=True,
        raises=AssertionError,
        reason="L136 で policy_name をサニタイズせずに os.path.join に渡している"
    )
    def test_path_traversal_via_policy_name(self, tmp_path, mock_task_logger):
        """RUM-SEC-04: パストラバーサルによる任意ファイル読み込み

        L136: metadata_file = os.path.join(output_dir, policy_name, "metadata.json")
        policy_name に "../" を含めると output_dir の外にあるファイルを
        読み込む可能性がある。

        【実装失敗予定】recommendation_uuid_mapper.py:136 で
        os.path.join に policy_name を直接渡しており、
        パストラバーサル対策（os.path.realpath + 境界チェック）がない。
        """
        # Arrange
        # output_dir の外にメタデータファイルを配置
        outer_dir = tmp_path / "outer"
        outer_dir.mkdir()
        traversal_target = outer_dir / "metadata.json"
        traversal_target.write_text(json.dumps({
            "policy": {"metadata": {"uuid": "traversed-uuid"}}
        }))

        inner_dir = tmp_path / "inner" / "policies"
        inner_dir.mkdir(parents=True)
        _, mock_logger = mock_task_logger

        # Act - "../outer" でディレクトリトラバーサル
        result = _extract_uuid_from_metadata(
            "../../outer", str(inner_dir), mock_logger
        )

        # Assert - output_dir 外のファイルが読まれないこと
        assert result != "traversed-uuid"

    @pytest.mark.xfail(
        strict=True,
        raises=AssertionError,
        reason="L40,L45 で policy_name をサニタイズせずにログに出力している"
    )
    def test_log_injection_via_policy_name(self, tmp_path, mock_task_logger):
        """RUM-SEC-05: ログ注入による偽ログエントリ

        L40: logger.info(f"ポリシー '{policy_name}' のUUID: {uuid}")
        policy_name に改行文字を含めると、ログに偽エントリが挿入される
        可能性がある。

        【実装失敗予定】recommendation_uuid_mapper.py:40,45 で
        policy_name の改行・制御文字がサニタイズされていない。
        """
        # Arrange
        malicious_name = "legit-policy\nFAKE_LOG: admin login successful"
        # ディレクトリ名に改行文字は使用不可のため、ディレクトリは作成せずモックで対応
        _, mock_logger = mock_task_logger

        with patch(
            "app.jobs.utils.recommendation_uuid_mapper._extract_uuid_from_metadata",
            return_value="test-uuid",
        ):
            # Act
            extract_recommendation_uuid_from_policy(
                malicious_name, str(tmp_path), "job-1"
            )

        # Assert - ログメッセージに改行が含まれないこと
        # str(call_args) は repr() で \n がエスケープされるため、
        # .args[0] で実際の文字列を直接検証する
        actual_log_message = mock_logger.info.call_args.args[0]
        assert "\n" not in actual_log_message
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_uuid_mapper_module` | テスト間のモジュール状態リセット | function | Yes |
| `mock_task_logger` | TaskLogger モック化 | function | Yes |

### 共通フィクスチャ定義

```python
# test/unit/jobs/utils/conftest.py に追加（既存の場合はマージ）
import sys
import os
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def reset_uuid_mapper_module():
    """テストごとにモジュールのグローバル状態をリセット

    recommendation_uuid_mapper はモジュールレベルのグローバル状態を
    持たないが、TaskLogger インポート経路の影響を排除するためリセットする。
    """
    yield
    # テスト後にクリーンアップ（対象モジュールとその依存に限定）
    prefixes = (
        "app.jobs.utils.recommendation_uuid_mapper",
        "app.jobs.utils.aws_resource_counter",
        "app.jobs.common",
    )
    modules_to_remove = [
        key for key in sys.modules if key.startswith(prefixes)
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture(autouse=True)
def mock_task_logger():
    """TaskLoggerをモック化して外部依存を排除

    recommendation_uuid_mapper.py の公開関数のうち
    extract_recommendation_uuid_from_policy, extract_recommendation_uuids_batch
    は内部で TaskLogger(job_id, "UUIDMapper") を生成する。
    モック化して外部ロギングシステムへの依存を排除する。

    注記: normalize_recommendation_uuid, _generate_fallback_uuid,
    _is_valid_uuid_format, get_uuid_mapping_summary は TaskLogger を
    使用しないが、autouse のため自動適用される（副作用なし）。
    """
    with patch(
        "app.jobs.utils.recommendation_uuid_mapper.TaskLogger"
    ) as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        yield mock_cls, mock_instance
```

---

## 6. テスト実行例

```bash
# recommendation_uuid_mapper + aws_resource_counter テストのみ実行
pytest test/unit/jobs/utils/test_recommendation_uuid_mapper.py -v

# 特定テストクラスのみ
pytest test/unit/jobs/utils/test_recommendation_uuid_mapper.py::TestExtractRecommendationUuidFromPolicy -v

# カバレッジ付き（両モジュール）
pytest test/unit/jobs/utils/test_recommendation_uuid_mapper.py \
  --cov=app.jobs.utils.recommendation_uuid_mapper \
  --cov=app.jobs.utils.aws_resource_counter \
  --cov-report=term-missing -v

# セキュリティマーカーで実行
# pyproject.toml に @pytest.mark.security は登録済み
pytest test/unit/jobs/utils/test_recommendation_uuid_mapper.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 25 | RUM-001〜RUM-023, ARC-001〜ARC-002 |
| 異常系 | 14 | RUM-E01〜RUM-E14 |
| セキュリティ | 5 | RUM-SEC-01〜RUM-SEC-05 |
| **合計** | **44** | - |

> **注記**: RUM-020 は `pytest.mark.parametrize` で4プレフィックスを、RUM-E02 は2パターン（None, ""）を展開するため、テスト実行時は48件となる。

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestExtractRecommendationUuidFromPolicy` | RUM-001〜RUM-003 | 3 |
| `TestExtractRecommendationUuidsBatch` | RUM-004〜RUM-006 | 3 |
| `TestNormalizeRecommendationUuid` | RUM-007〜RUM-010 | 4 |
| `TestExtractUuidFromMetadata` | RUM-011〜RUM-015 | 5 |
| `TestGenerateFallbackUuid` | RUM-016〜RUM-018 | 3 |
| `TestIsValidUuidFormat` | RUM-019〜RUM-021 | 3 |
| `TestGetUuidMappingSummary` | RUM-022〜RUM-023 | 2 |
| `TestAwsResourceCounter` | ARC-001〜ARC-002 | 2 |
| `TestExtractRecommendationUuidFromPolicyErrors` | RUM-E01 | 1 |
| `TestExtractRecommendationUuidsBatchErrors` | RUM-E02〜RUM-E04 | 3 |
| `TestNormalizeRecommendationUuidErrors` | RUM-E05〜RUM-E06 | 2 |
| `TestExtractUuidFromMetadataErrors` | RUM-E07〜RUM-E08 | 2 |
| `TestGenerateFallbackUuidErrors` | RUM-E09〜RUM-E10 | 2 |
| `TestIsValidUuidFormatErrors` | RUM-E11〜RUM-E14 | 4 |
| `TestRecommendationUuidMapperSecurity` | RUM-SEC-01〜RUM-SEC-05 | 5 |

### 実装失敗が予想されるテスト

以下のテストは現在の実装では**意図的に失敗**します。実装側の修正が必要です。

| テストID | 失敗理由 | 修正方針 |
|---------|---------|---------|
| RUM-SEC-01 | `str(e)` がエラーログに直接出力される（`recommendation_uuid_mapper.py:49,89,167`） | `sanitize_error_message()` の導入、または `type(e).__name__` のみ出力 |
| RUM-SEC-02 | ポリシー名・UUIDがinfo/warningログに直接出力される（`recommendation_uuid_mapper.py:40,45,72,85`） | ログレベルをDEBUGに変更、または値をマスク処理 |
| RUM-SEC-04 | `policy_name` がサニタイズされずに `os.path.join` に渡される（`recommendation_uuid_mapper.py:136`） | `os.path.realpath()` + `output_dir` 境界チェックの導入 |
| RUM-SEC-05 | `policy_name` の改行・制御文字がサニタイズされずにログに出力される（`recommendation_uuid_mapper.py:40,45`） | ログ出力前に `policy_name.replace('\n', '\\n')` 等のサニタイズ処理を追加 |

#### xfail 解除手順

| テストID | 対象関数 | 修正箇所 | 解除条件 |
|---------|---------|---------|---------|
| RUM-SEC-01 | `extract_recommendation_uuid_from_policy`, `extract_recommendation_uuids_batch`, `_extract_uuid_from_metadata` | L49, L89, L167 | `str(e)` をサニタイズ関数に置換 |
| RUM-SEC-02 | `extract_recommendation_uuid_from_policy`, `extract_recommendation_uuids_batch` | L40, L45, L72, L85 | ポリシー名・UUID値をマスクまたはログレベル変更 |
| RUM-SEC-04 | `_extract_uuid_from_metadata` | L136 | `os.path.realpath()` + startswith 境界チェック追加 |
| RUM-SEC-05 | `extract_recommendation_uuid_from_policy` | L40, L45 | policy_name の改行・制御文字をエスケープ |

> **xfail 運用注記**: `strict=True` が設定されているため、実装修正により xfail テストが PASS した場合は XPASS となり CI が失敗する。修正完了後は `@pytest.mark.xfail` デコレータを削除し、`pytest -v` でテストが PASS（not XPASS）であることを確認する。

### 注意事項

- `@pytest.mark.security` マーカーは `pyproject.toml` に登録済み
- `TaskLogger` は autouse フィクスチャでモック化済み（個別パッチ不要）
- `tmp_path` を使用するテストでは実ファイルI/Oを行う（モックなし）
- `aws_resource_counter.py` のテストは `TaskLogger` に依存しないためモック不要

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `_is_valid_uuid_format` L217 は `isalnum()` チェックのため、`g`〜`z` も有効と判定される（UUID標準は16進数のみ） | UUID検証が緩い（false positive の可能性） | 現状の実装仕様として許容。厳密な検証が必要な場合は `uuid.UUID()` を使用 |
| 2 | `_generate_fallback_uuid` L192 で MD5 を使用（暗号学的に非推奨） | フォールバックUUIDの一意性は暗号的保証なし | 本用途は識別子生成（暗号目的外）のため許容。8文字切り詰めで衝突リスクは2^32分の1 |
| 3 | `extract_recommendation_uuids_batch` L71 は `not output_dir` で空文字も True と判定 | 空文字と None が同一処理 | 実用上問題なし（空文字パスは無効）。RUM-E02 で parametrize 検証済み |
| 4 | `_extract_uuid_from_metadata` L153 で `isinstance(uuid, str)` チェック。非文字列値（int等）のメタデータは無視される | 数値UUIDのメタデータに対応不可 | 実運用で数値UUIDは想定外。必要なら `str(uuid)` 変換を追加 |
| 5 | `aws_resource_counter.py` はアクティブコード48行中46行がdocstring/コメント。スタブテスト2件のみ | テスト価値が低い | コメントアウトされた `AWSResourceCounter` クラスの再有効化時にテスト追加が必要 |
| 6 | RUM-SEC-01 は L49 経路のみ検証。L89（batch）と L167（metadata）は同一パターンのため代表テスト | 3経路中2経路が未テスト | 修正時に3箇所すべてを対象とし、必要に応じて経路別テストを追加 |
