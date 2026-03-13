# jobs/utils メタデータ・アカウント抽出 テストケース (#17e)

## 1. 概要

`app/jobs/utils/` のメタデータ抽出モジュール群（`metadata_extractor.py`, `account_id_extractor.py`）のテスト仕様書。Custodianスキャン結果からのメタデータ統合・正規化、およびAWSアカウントIDの多段フォールバック抽出を担う。他のutilsファイルへの依存はなく、独立して動作する。

### 1.1 主要機能

| 関数 | ファイル | 説明 |
|------|---------|------|
| `extract_metadata_from_output_dir()` | metadata_extractor.py | 出力ディレクトリからメタデータを抽出・統合 |
| `extract_scan_info_from_metadata()` | metadata_extractor.py | メタデータからスキャン情報を抽出 |
| `extract_policy_details_from_metadata()` | metadata_extractor.py | メタデータからポリシー詳細を抽出 |
| `_load_metadata_from_file()` | metadata_extractor.py | metadata.jsonファイルの読み込み |
| `_collect_additional_metadata()` | metadata_extractor.py | 追加メタデータファイルからの情報収集 |
| `_integrate_metadata()` | metadata_extractor.py | 代表メタデータと追加情報の統合 |
| `_sanitize_custodian_metadata()` | metadata_extractor.py | メタデータのサニタイズ（数値→文字列変換） |
| `_normalize_filter_values()` | metadata_extractor.py | フィルター値の正規化 |
| `_normalize_nested_filter_object()` | metadata_extractor.py | ネストオブジェクトの正規化 |
| `_normalize_numeric_fields()` | metadata_extractor.py | 数値フィールドの文字列変換 |
| `_create_default_metadata()` | metadata_extractor.py | デフォルトメタデータ生成 |
| `extract_account_id_from_output_dir()` | account_id_extractor.py | メタデータからアカウントID抽出 |
| `extract_account_id_from_resources()` | account_id_extractor.py | リソースファイルからアカウントID抽出 |
| `extract_account_id_with_fallback()` | account_id_extractor.py | 多段フォールバック付きアカウントID抽出 |
| `_extract_account_id_from_metadata_file()` | account_id_extractor.py | メタデータファイルからアカウントID抽出 |
| `_extract_account_id_from_resources_file()` | account_id_extractor.py | リソースファイルからアカウントID抽出 |
| `_extract_account_id_from_environment()` | account_id_extractor.py | 環境変数からアカウントID抽出 |

### 1.2 カバレッジ目標: 90%

> **注記**: 全関数が同期関数であり、外部依存は `glob.glob`, `os.path.exists`, `os.listdir`, `open`, `json.load`, `os.environ.get`, `datetime` のみ。モック構築が容易なため高カバレッジを目標とする。`metadata_extractor.py` と `field_normalizers.py` には同名の内部関数（`_normalize_numeric_fields` 等）が存在するが、**ロジックが異なる**（metadata_extractor版は `int/float→str` 変換、field_normalizers版は `Value` キーの `int→float` 変換）。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象1 | `app/jobs/utils/metadata_extractor.py` (423行) |
| テスト対象2 | `app/jobs/utils/account_id_extractor.py` (226行) |
| テストコード | `test/unit/jobs/utils/test_metadata_account.py` |
| conftest | `test/unit/jobs/utils/conftest.py`（#17aと共有） |

### 1.4 依存関係

```
metadata_extractor.py
├── json, glob, os (標準ライブラリ)
├── datetime (標準ライブラリ)
└── TaskLogger (app.jobs.common.logging)

account_id_extractor.py
├── json, os (標準ライブラリ)
└── TaskLogger (app.jobs.common.logging)

被依存:
  metadata_extractor → store_operations.py, custodian_output.py,
                       custodian_scan.py, history_manager.py,
                       scan_coordinator.py
  account_id_extractor → history_manager.py, opensearch_manager.py
外部依存: なし（他utilsファイルへの依存なし）
```

### 1.5 主要分岐マップ

| 関数 | 分岐数 | 主要条件 |
|------|--------|---------|
| `extract_metadata_from_output_dir` | 3 | L40 ファイルなし, L45-52 正常フロー, L57 例外 |
| `extract_scan_info_from_metadata` | 8 | L83 config存在, L90 profile存在, L94 version, L98 execution, L103 start, L106 isinstance, L110 内部例外, L115 外部例外 |
| `extract_policy_details_from_metadata` | 3 | L146 policy存在, L154-158 filters/actions, L166 例外 |
| `_load_metadata_from_file` | 2 | L189 読み込み成功, L195 例外 |
| `_collect_additional_metadata` | 4 | L222 policy存在, L234 config存在, L239 set→list変換, L244 例外 |
| `_sanitize_custodian_metadata` | 5 | L290 basic_fields, L296 sys-stats, L300 api-stats, L305 metrics(list), L312 例外 |
| `_normalize_filter_values` | 3 | L330 dict→正規化, L334 非dict→value変換, L339 例外 |
| `_normalize_nested_filter_object` | 4 | L357 dict再帰, L359 list再帰, L363 数値変換, L367 例外 |
| `_normalize_numeric_fields` | 4 | L381 dict再帰, L383 list再帰, L385 int/float→str, L388 パススルー |
| `extract_account_id_from_output_dir` | 5 | L31 無効パス, L38 非ディレクトリ, L42 metadata.json存在, L44 有効ID, L51 例外 |
| `extract_account_id_from_resources` | 5 | L70 無効パス, L77 非ディレクトリ, L80 resources.json存在, L82 有効ID, L88 例外 |
| `extract_account_id_with_fallback` | 4 | L106 メタデータ成功, L111 リソース成功, L116 環境変数成功, L119 全失敗 |
| `_extract_account_id_from_metadata_file` | 5 | L141 config.account_id, L146 execution.account, L148 isinstance, L151 見つからず, L153 例外 |
| `_extract_account_id_from_resources_file` | 7 | L173 非list/空, L180 OwnerId, L184 NetworkInterfaces, L194 Arn(::), L196 parts>=5, L199 見つからず, L201 例外 |
| `_extract_account_id_from_environment` | 4 | L215 AWS_ACCOUNT_ID, L220 ACCOUNT_ID, L224 なし, L226 例外 |

### 1.6 実装上の注意点

| # | 注意点 | 影響 |
|---|--------|------|
| 1 | `metadata_extractor._normalize_numeric_fields` は `int/float→str` 変換（L385-387）。`field_normalizers._normalize_numeric_fields` の `int→float` 変換とは**異なるロジック** | テスト対象の関数を正確に区別する必要あり |
| 2 | `_collect_additional_metadata` が `set` を使用（L215-216）し、最後に `list` 変換（L239-240） | 返却値の `resource_types`, `regions` の順序は不定 |
| 3 | `_extract_account_id_from_resources_file` の ARN 解析は `"::" in arn` 条件（L194） | リージョン付きARN（`arn:aws:ec2:us-east-1:123:...`）は `::` を含まないため一致しない |
| 4 | `extract_scan_info_from_metadata` の `scan_timestamp` は `datetime.now()` で生成（L79） | テストでは値の型（ISO文字列）を検証し、厳密な値比較は避ける |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| MA-001 | extract_metadata_from_output_dir 正常フロー | 複数metadata.json | 統合・サニタイズ済みメタデータ |
| MA-002 | extract_metadata_from_output_dir メタデータなし | 空ディレクトリ | デフォルトメタデータ |
| MA-003 | extract_scan_info_from_metadata 完全抽出 | config+version+execution | 全フィールド抽出済み |
| MA-004 | extract_scan_info_from_metadata 空メタデータ | `{}` | デフォルト値 |
| MA-005 | extract_scan_info_from_metadata start_time非数値 | `start="2024-01-01"` | タイムスタンプ変換スキップ |
| MA-006 | extract_policy_details_from_metadata 完全ポリシー | policy+filters+actions | 正規化済みポリシー詳細 |
| MA-007 | extract_policy_details_from_metadata policyなし | `{}` | デフォルト値 |
| MA-008 | _load_metadata_from_file 正常読み込み | 有効JSON | メタデータ辞書 |
| MA-009 | _collect_additional_metadata 複数ファイル | 3ファイル | ポリシー名・リソースタイプ・リージョン収集 |
| MA-010 | _integrate_metadata 統合 | 代表+追加情報 | scan_statistics追加済み |
| MA-011 | _sanitize_custodian_metadata 全フィールド | basic+sys-stats+api-stats+metrics | 数値→文字列変換・不要フィールド除外 |
| MA-012 | _normalize_filter_values dict正規化 | `[{type: value, value: 10}]` | `[{type: value, value: "10"}]` |
| MA-013 | _normalize_filter_values 非dict | `["string_filter"]` | `[{"value": "string_filter"}]` |
| MA-014 | _normalize_nested_filter_object 再帰処理 | ネストdict/list | 再帰的に数値→文字列変換 |
| MA-015 | _normalize_numeric_fields 数値→文字列 | `42`, `3.14` | `"42"`, `"3.14"` |
| MA-016 | _normalize_numeric_fields dict/list再帰 | ネスト構造 | 全数値を再帰的に文字列変換 |
| MA-017 | _create_default_metadata 構造確認 | なし | 必須フィールド全て含む辞書 |
| MA-018 | extract_account_id_from_output_dir 成功 | metadata.json有り | アカウントID |
| MA-019 | extract_account_id_from_output_dir 非ディレクトリスキップ | ファイルエントリ混在 | ディレクトリのみ探索 |
| MA-020 | extract_account_id_from_resources OwnerId | `{"OwnerId": "123"}` | `"123"` |
| MA-021 | extract_account_id_from_resources NetworkInterfaces | ネストOwnerId | `"456"` |
| MA-022 | extract_account_id_from_resources ARN解析 | IAM ARN | アカウントID部分 |
| MA-023 | extract_account_id_with_fallback メタデータ成功 | メタデータに有効ID | 第1手段で返却 |
| MA-024 | extract_account_id_with_fallback リソース | メタデータ失敗 | 第2手段で返却 |
| MA-025 | extract_account_id_with_fallback 環境変数 | メタデータ+リソース失敗 | 第3手段で返却 |
| MA-026 | extract_account_id_with_fallback 全失敗 | 全手段失敗 | `"unknown"` |
| MA-027 | _extract_account_id_from_metadata_file config | config.account_id有り | アカウントID |
| MA-028 | _extract_account_id_from_metadata_file execution | config無し、execution.account有り | アカウントID |
| MA-029 | _extract_account_id_from_resources_file 非リスト | 非リスト/空リスト | `"unknown"` |
| MA-030 | _extract_account_id_from_environment AWS_ACCOUNT_ID | 環境変数設定 | アカウントID |
| MA-031 | _extract_account_id_from_environment ACCOUNT_ID | AWS_ACCOUNT_IDなし | フォールバック値 |
| MA-032 | _extract_account_id_from_environment 環境変数なし | 環境変数未設定 | `"unknown"` |
| MA-033 | extract_scan_info_from_metadata config有・version無 | config有、version/execution無 | configのみ抽出 |
| MA-034 | _extract_account_id_from_resources_file リージョン付ARN | `arn:aws:ec2:us-east-1:123:...` | `"unknown"` (`::`不在) |
| MA-035 | _collect_additional_metadata configのみ（policyなし） | config有り・policy無し | リージョンのみ収集 |

### 2.1 extract_metadata_from_output_dir テスト

```python
# test/unit/jobs/utils/test_metadata_account.py
import pytest
import json
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


class TestExtractMetadataFromOutputDir:
    """extract_metadata_from_output_dir のテスト"""

    def test_normal_flow_with_multiple_files(self, tmp_path):
        """MA-001: 複数メタデータファイルの統合・サニタイズ

        metadata_extractor.py:L45-52 の正常フローをカバー。
        glob.globで発見された複数のmetadata.jsonを統合し、
        _sanitize_custodian_metadataでサニタイズした結果を返す。
        """
        # Arrange
        from app.jobs.utils.metadata_extractor import extract_metadata_from_output_dir

        # ポリシー1: 代表メタデータ
        policy1_dir = tmp_path / "policy1"
        policy1_dir.mkdir()
        metadata1 = {
            "policy": {"name": "check-ec2", "resource": "aws.ec2"},
            "version": "0.9.35",
            "config": {"account_id": "123456789012", "region": "us-east-1"},
            "execution": {"id": "exec-001", "start": 1700000000}
        }
        (policy1_dir / "metadata.json").write_text(
            json.dumps(metadata1), encoding="utf-8"
        )

        # ポリシー2: 追加メタデータ
        policy2_dir = tmp_path / "policy2"
        policy2_dir.mkdir()
        metadata2 = {
            "policy": {"name": "check-s3", "resource": "aws.s3"},
            "config": {"region": "ap-northeast-1"}
        }
        (policy2_dir / "metadata.json").write_text(
            json.dumps(metadata2), encoding="utf-8"
        )

        # Act
        with patch("app.jobs.utils.metadata_extractor.TaskLogger"):
            result = extract_metadata_from_output_dir(str(tmp_path), "job-001")

        # Assert
        assert isinstance(result, dict)
        # scan_statisticsが追加されている
        assert "scan_statistics" in result
        assert result["scan_statistics"]["total_policies"] == 2

    def test_no_metadata_files_returns_default(self, tmp_path):
        """MA-002: メタデータファイルなし → デフォルトメタデータ返却

        metadata_extractor.py:L40-42 の分岐をカバー。
        glob.globが空リストを返した場合、_create_default_metadataを呼ぶ。
        """
        # Arrange
        from app.jobs.utils.metadata_extractor import extract_metadata_from_output_dir

        # Act
        with patch("app.jobs.utils.metadata_extractor.TaskLogger"):
            result = extract_metadata_from_output_dir(str(tmp_path), "job-002")

        # Assert
        assert result["policy"]["name"] == "unknown"
        assert result["version"] == "unknown"
        assert result["scan_statistics"]["total_policies"] == 0
```

### 2.2 extract_scan_info_from_metadata テスト

```python
class TestExtractScanInfo:
    """extract_scan_info_from_metadata のテスト"""

    def test_full_extraction(self):
        """MA-003: config+profile+version+executionの完全抽出

        metadata_extractor.py:L83-111 の全分岐をカバー。
        config（account_id, region, profile）、version、
        execution（id, start）の全フィールドを抽出する。
        """
        # Arrange
        from app.jobs.utils.metadata_extractor import extract_scan_info_from_metadata
        metadata = {
            "config": {
                "account_id": "123456789012",
                "region": "us-east-1",
                "profile": "production"
            },
            "version": "0.9.35",
            "execution": {
                "id": "exec-001",
                "start": 1700000000  # int型タイムスタンプ
            }
        }

        # Act
        result = extract_scan_info_from_metadata(metadata)

        # Assert
        assert result["account_id"] == "123456789012"
        assert result["region"] == "us-east-1"
        assert result["profile"] == "production"
        assert result["custodian_version"] == "0.9.35"
        assert result["execution_id"] == "exec-001"
        assert result["cloud_provider"] == "aws"
        # タイムスタンプがISO形式に変換されている
        assert "2023-11-14" in result["scan_timestamp"]

    def test_empty_metadata_returns_defaults(self):
        """MA-004: 空メタデータ → 全フィールドがデフォルト値

        metadata_extractor.py:L83 の条件がFalse（configなし）、
        L94, L98 もFalse（version, executionなし）の分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.metadata_extractor import extract_scan_info_from_metadata

        # Act
        result = extract_scan_info_from_metadata({})

        # Assert
        assert result["account_id"] == "unknown"
        assert result["region"] == "unknown"
        assert result["cloud_provider"] == "aws"
        assert result["custodian_version"] == "unknown"
        assert result["execution_id"] == "unknown"
        assert "profile" not in result
        # scan_timestampはISO形式の文字列
        assert isinstance(result["scan_timestamp"], str)

    def test_config_present_version_absent(self):
        """MA-033: config有・version/execution無のメタデータ

        metadata_extractor.py:L83-91 の config 分岐のみ到達し、
        L94（version）, L98（execution）はスキップされる分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.metadata_extractor import extract_scan_info_from_metadata
        metadata = {
            "config": {
                "account_id": "123456789012",
                "region": "ap-northeast-1"
            }
        }

        # Act
        result = extract_scan_info_from_metadata(metadata)

        # Assert
        assert result["account_id"] == "123456789012"
        assert result["region"] == "ap-northeast-1"
        assert result["custodian_version"] == "unknown"  # version未設定
        assert result["execution_id"] == "unknown"  # execution未設定
        assert result["cloud_provider"] == "aws"

    def test_non_numeric_start_time_skips_conversion(self):
        """MA-005: start_timeが文字列の場合はタイムスタンプ変換をスキップ

        metadata_extractor.py:L106 の isinstance(start_time, (int, float))
        がFalseになる分岐をカバー。scan_timestampはデフォルト値のまま。
        """
        # Arrange
        from app.jobs.utils.metadata_extractor import extract_scan_info_from_metadata
        metadata = {
            "execution": {
                "id": "exec-002",
                "start": "2024-01-01T00:00:00Z"  # 文字列型
            }
        }

        # Act
        result = extract_scan_info_from_metadata(metadata)

        # Assert
        assert result["execution_id"] == "exec-002"
        # start_timeが文字列のため変換されず、デフォルトのdatetime.now()が使われる
        assert isinstance(result["scan_timestamp"], str)
        # 文字列の"2024-01-01"ではなく、現在時刻のISO文字列
        assert "T" in result["scan_timestamp"]
```

### 2.3 extract_policy_details_from_metadata テスト

```python
class TestExtractPolicyDetails:
    """extract_policy_details_from_metadata のテスト"""

    def test_full_policy_extraction(self):
        """MA-006: 完全なポリシー詳細の抽出（filters/actions含む）

        metadata_extractor.py:L146-162 の正常フローをカバー。
        filters/actionsは _normalize_filter_values で正規化される。
        """
        # Arrange
        from app.jobs.utils.metadata_extractor import extract_policy_details_from_metadata
        metadata = {
            "policy": {
                "name": "check-ec2-stopped",
                "resource": "aws.ec2",
                "description": "停止中のEC2インスタンスを検出",
                "filters": [
                    {"type": "value", "key": "State.Name", "value": "stopped"}
                ],
                "actions": [
                    {"type": "notify", "to": ["admin@example.com"]}
                ],
                "metadata": {"severity": "high"}
            }
        }

        # Act
        result = extract_policy_details_from_metadata(metadata)

        # Assert
        assert result["name"] == "check-ec2-stopped"
        assert result["resource_type"] == "aws.ec2"
        assert result["description"] == "停止中のEC2インスタンスを検出"
        assert len(result["filters"]) == 1
        assert len(result["actions"]) == 1
        assert result["metadata"] == {"severity": "high"}

    def test_no_policy_key_returns_defaults(self):
        """MA-007: policyキーなし → デフォルト値

        metadata_extractor.py:L146 の条件がFalseになる分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.metadata_extractor import extract_policy_details_from_metadata

        # Act
        result = extract_policy_details_from_metadata({})

        # Assert
        assert result["name"] == "unknown"
        assert result["resource_type"] == "unknown"
        assert result["description"] == ""
        assert result["filters"] == []
        assert result["actions"] == []
        assert result["metadata"] == {}
```

### 2.4 メタデータ処理テスト

```python
class TestMetadataProcessing:
    """_load_metadata_from_file, _collect_additional_metadata,
    _integrate_metadata のテスト"""

    def test_load_metadata_from_file_success(self, tmp_path):
        """MA-008: 有効なmetadata.jsonの正常読み込み

        metadata_extractor.py:L189-193 の正常分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.metadata_extractor import _load_metadata_from_file
        metadata = {"policy": {"name": "test", "resource": "ec2"}}
        metadata_file = tmp_path / "metadata.json"
        metadata_file.write_text(json.dumps(metadata), encoding="utf-8")
        logger = MagicMock()

        # Act
        result = _load_metadata_from_file(str(metadata_file), logger)

        # Assert
        assert result == metadata
        logger.warning.assert_not_called()

    def test_collect_additional_metadata_multiple_files(self, tmp_path):
        """MA-009: 複数メタデータファイルからの情報収集

        metadata_extractor.py:L219-240 のループ処理をカバー。
        ポリシー名、リソースタイプ、リージョンがそれぞれ収集される。
        set→list変換（L239-240）も検証する。
        """
        # Arrange
        from app.jobs.utils.metadata_extractor import _collect_additional_metadata
        logger = MagicMock()

        files = []
        for i, (name, resource, region) in enumerate([
            ("policy-a", "aws.ec2", "us-east-1"),
            ("policy-b", "aws.s3", "ap-northeast-1"),
            ("policy-c", "aws.ec2", "us-east-1"),  # 重複リソースタイプ/リージョン
        ]):
            f = tmp_path / f"policy{i}" / "metadata.json"
            f.parent.mkdir()
            f.write_text(json.dumps({
                "policy": {"name": name, "resource": resource},
                "config": {"region": region}
            }), encoding="utf-8")
            files.append(str(f))

        # Act
        result = _collect_additional_metadata(files, logger)

        # Assert
        # total_policies = len(渡されたファイル数) + 1（代表メタデータ分）= 3 + 1 = 4
        assert result["total_policies"] == 4
        assert len(result["policy_names"]) == 3
        assert "policy-a" in result["policy_names"]
        # setからlistへの変換で重複は除去される
        assert set(result["resource_types"]) == {"aws.ec2", "aws.s3"}
        assert set(result["regions"]) == {"us-east-1", "ap-northeast-1"}

    def test_collect_additional_metadata_config_only(self, tmp_path):
        """MA-035: configのみ（policyなし）のメタデータファイル

        metadata_extractor.py:L222 の `if metadata and "policy" in metadata`
        がFalse、L234 の `if metadata and "config" in metadata` がTrue
        となるパスをカバー。policy_names は空のまま、regions のみ収集される。
        """
        # Arrange
        from app.jobs.utils.metadata_extractor import _collect_additional_metadata
        logger = MagicMock()

        f = tmp_path / "config_only" / "metadata.json"
        f.parent.mkdir()
        f.write_text(json.dumps({
            "config": {"region": "eu-west-1"}
            # policy キーなし
        }), encoding="utf-8")

        # Act
        result = _collect_additional_metadata([str(f)], logger)

        # Assert
        # total_policies = len([1ファイル]) + 1（代表分）= 2
        assert result["total_policies"] == 2
        # policyが無いため policy_names は空
        assert result["policy_names"] == []
        # configからリージョンは収集される
        assert "eu-west-1" in result["regions"]

    def test_integrate_metadata_adds_scan_statistics(self):
        """MA-010: 代表メタデータに scan_statistics を追加

        metadata_extractor.py:L263-273 のコピー＋統計追加をカバー。
        """
        # Arrange
        from app.jobs.utils.metadata_extractor import _integrate_metadata
        representative = {
            "policy": {"name": "main-policy"},
            "version": "0.9.35"
        }
        additional = {
            "total_policies": 3,
            "policy_names": ["p1", "p2"],
            "resource_types": ["aws.ec2"],
            "regions": ["us-east-1"]
        }

        # Act
        result = _integrate_metadata(representative, additional)

        # Assert
        assert result["policy"]["name"] == "main-policy"
        assert result["version"] == "0.9.35"
        assert result["scan_statistics"]["total_policies"] == 3
        assert result["scan_statistics"]["policy_names"] == ["p1", "p2"]
        # 元の辞書が変更されていないことを確認
        assert "scan_statistics" not in representative
```

### 2.5 メタデータ正規化テスト

```python
class TestSanitizeAndNormalize:
    """_sanitize_custodian_metadata, _normalize_filter_values,
    _normalize_nested_filter_object, _normalize_numeric_fields のテスト"""

    def test_sanitize_all_fields(self):
        """MA-011: 全フィールド存在時のサニタイズ処理

        metadata_extractor.py:L290-308 の全分岐をカバー。
        basic_fieldsはコピー、sys-statsは数値→文字列変換、
        api-statsはそのまま、metricsはリスト各要素を正規化。
        未知フィールドは除外される。
        """
        # Arrange
        from app.jobs.utils.metadata_extractor import _sanitize_custodian_metadata
        metadata = {
            "policy": {"name": "test"},
            "version": "0.9.35",
            "execution": {"id": "exec-001"},
            "config": {"region": "us-east-1"},
            "scan_statistics": {"total_policies": 1},
            "sys-stats": {"cpu": 45.2, "memory": 1024},
            "api-stats": {"calls": 100},
            "metrics": [{"duration": 5.3, "name": "scan"}],
            "unknown_field": "should_be_dropped"
        }

        # Act
        result = _sanitize_custodian_metadata(metadata)

        # Assert
        # basic_fieldsはコピーされる
        assert result["policy"]["name"] == "test"
        assert result["version"] == "0.9.35"
        # sys-statsの数値は文字列に変換
        assert result["sys-stats"]["cpu"] == "45.2"
        assert result["sys-stats"]["memory"] == "1024"
        # api-statsはそのまま
        assert result["api-stats"]["calls"] == 100
        # metricsの数値は文字列に変換
        assert result["metrics"][0]["duration"] == "5.3"
        assert result["metrics"][0]["name"] == "scan"  # 文字列はそのまま
        # 未知フィールドは除外
        assert "unknown_field" not in result

    def test_normalize_filter_values_dict_items(self):
        """MA-012: dictフィルターの正規化

        metadata_extractor.py:L330-332 の分岐をカバー。
        dict項目は _normalize_nested_filter_object で処理される。
        """
        # Arrange
        from app.jobs.utils.metadata_extractor import _normalize_filter_values
        filters = [
            {"type": "value", "key": "State", "value": 10},
            {"type": "value", "key": "Count", "value": 3.14}
        ]

        # Act
        result = _normalize_filter_values(filters)

        # Assert
        assert len(result) == 2
        assert result[0]["value"] == "10"  # int→str
        assert result[0]["type"] == "value"  # 文字列はそのまま
        assert result[1]["value"] == "3.14"  # float→str

    def test_normalize_filter_values_non_dict_items(self):
        """MA-013: 非dictフィルターは {"value": str(item)} に変換

        metadata_extractor.py:L334-335 の分岐をカバー。
        文字列やプリミティブ値はvalue辞書でラップされる。
        """
        # Arrange
        from app.jobs.utils.metadata_extractor import _normalize_filter_values
        filters = ["string_filter", 42, True]

        # Act
        result = _normalize_filter_values(filters)

        # Assert
        assert result[0] == {"value": "string_filter"}
        assert result[1] == {"value": "42"}
        assert result[2] == {"value": "True"}

    def test_normalize_nested_filter_object_recursive(self):
        """MA-014: ネストオブジェクトの再帰処理（dict/list/数値）

        metadata_extractor.py:L357-363 の3分岐をカバー。
        dict値は再帰、list値は_normalize_filter_values経由、
        プリミティブ値は_normalize_numeric_fieldsで変換。
        """
        # Arrange
        from app.jobs.utils.metadata_extractor import _normalize_nested_filter_object
        obj = {
            "inner_dict": {"value": 5},
            "inner_list": [{"value": 10}],
            "count": 42,
            "name": "test"
        }

        # Act
        result = _normalize_nested_filter_object(obj)

        # Assert
        # dict値は再帰処理
        assert result["inner_dict"]["value"] == "5"
        # list値は_normalize_filter_values経由
        assert result["inner_list"][0]["value"] == "10"
        # 数値は文字列変換
        assert result["count"] == "42"
        # 文字列はそのまま
        assert result["name"] == "test"

    def test_normalize_numeric_fields_converts_numbers(self):
        """MA-015: int/floatを文字列に変換

        metadata_extractor.py:L385-387 の分岐をカバー。
        全ての数値型（int, float）が文字列に変換される。
        """
        # Arrange
        from app.jobs.utils.metadata_extractor import _normalize_numeric_fields

        # Act & Assert
        assert _normalize_numeric_fields(42) == "42"
        assert _normalize_numeric_fields(3.14) == "3.14"
        assert _normalize_numeric_fields(0) == "0"
        assert _normalize_numeric_fields(-1.5) == "-1.5"
        # 非数値はそのまま
        assert _normalize_numeric_fields("text") == "text"
        assert _normalize_numeric_fields(None) is None
        # bool は int のサブクラスのため isinstance(True, int) は True
        # str(True) → "True", str(False) → "False" となる
        assert _normalize_numeric_fields(True) == "True"
        assert _normalize_numeric_fields(False) == "False"

    def test_normalize_numeric_fields_recursive(self):
        """MA-016: dict/listの再帰的な数値→文字列変換

        metadata_extractor.py:L381-384 の再帰分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.metadata_extractor import _normalize_numeric_fields
        obj = {
            "cpu": 45.2,
            "nested": {"memory": 1024},
            "values": [1, 2.5, "text"]
        }

        # Act
        result = _normalize_numeric_fields(obj)

        # Assert
        assert result["cpu"] == "45.2"
        assert result["nested"]["memory"] == "1024"
        assert result["values"] == ["1", "2.5", "text"]
```

### 2.6 _create_default_metadata テスト

```python
class TestCreateDefaultMetadata:
    """_create_default_metadata のテスト"""

    def test_default_structure(self):
        """MA-017: デフォルトメタデータの構造確認

        metadata_extractor.py:L399-419 の返却値構造をカバー。
        全必須フィールドが存在し、適切なデフォルト値を持つこと。
        """
        # Arrange
        from app.jobs.utils.metadata_extractor import _create_default_metadata

        # Act
        result = _create_default_metadata()

        # Assert
        assert result["policy"]["name"] == "unknown"
        assert result["policy"]["resource"] == "unknown"
        assert result["version"] == "unknown"
        assert result["config"]["account_id"] == "unknown"
        assert result["config"]["region"] == "unknown"
        assert result["execution"]["id"] == "unknown"
        assert isinstance(result["execution"]["start"], float)
        assert result["scan_statistics"]["total_policies"] == 0
        assert result["scan_statistics"]["policy_names"] == []
        assert result["scan_statistics"]["resource_types"] == []
        assert result["scan_statistics"]["regions"] == []
```

### 2.7 extract_account_id_from_output_dir テスト

```python
class TestExtractAccountIdFromOutputDir:
    """extract_account_id_from_output_dir のテスト"""

    def test_successful_extraction(self, tmp_path):
        """MA-018: メタデータからアカウントIDを正常取得

        account_id_extractor.py:L36-46 のループ＋成功分岐をカバー。
        最初に見つかった有効なアカウントIDを返す。
        """
        # Arrange
        from app.jobs.utils.account_id_extractor import extract_account_id_from_output_dir
        policy_dir = tmp_path / "check-ec2"
        policy_dir.mkdir()
        metadata = {"config": {"account_id": "123456789012"}}
        (policy_dir / "metadata.json").write_text(
            json.dumps(metadata), encoding="utf-8"
        )

        # Act
        with patch("app.jobs.utils.account_id_extractor.TaskLogger"):
            result = extract_account_id_from_output_dir(str(tmp_path), "job-001")

        # Assert
        assert result == "123456789012"

    def test_non_directory_entries_skipped(self, tmp_path):
        """MA-019: 非ディレクトリエントリはスキップされる

        account_id_extractor.py:L38-39 の continue 分岐をカバー。
        ファイルエントリが混在していてもディレクトリのみ探索する。
        """
        # Arrange
        from app.jobs.utils.account_id_extractor import extract_account_id_from_output_dir

        # ファイルエントリ（スキップされるべき）
        (tmp_path / "not_a_directory.txt").write_text("dummy")
        # ディレクトリエントリ（探索されるべき）
        policy_dir = tmp_path / "check-s3"
        policy_dir.mkdir()
        metadata = {"config": {"account_id": "987654321098"}}
        (policy_dir / "metadata.json").write_text(
            json.dumps(metadata), encoding="utf-8"
        )

        # Act
        with patch("app.jobs.utils.account_id_extractor.TaskLogger"):
            result = extract_account_id_from_output_dir(str(tmp_path), "job-002")

        # Assert
        assert result == "987654321098"
```

### 2.8 extract_account_id_from_resources テスト

```python
class TestExtractAccountIdFromResources:
    """extract_account_id_from_resources のテスト"""

    def test_owner_id_extraction(self, tmp_path):
        """MA-020: リソースのOwnerIdからアカウントID抽出

        account_id_extractor.py:L180-181 の分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.account_id_extractor import extract_account_id_from_resources
        policy_dir = tmp_path / "check-ec2"
        policy_dir.mkdir()
        resources = [{"InstanceId": "i-123", "OwnerId": "111222333444"}]
        (policy_dir / "resources.json").write_text(
            json.dumps(resources), encoding="utf-8"
        )

        # Act
        with patch("app.jobs.utils.account_id_extractor.TaskLogger"):
            result = extract_account_id_from_resources(str(tmp_path), "job-003")

        # Assert
        assert result == "111222333444"

    def test_network_interfaces_owner_id(self, tmp_path):
        """MA-021: NetworkInterfaces内のOwnerIdからアカウントID抽出

        account_id_extractor.py:L184-189 のネスト構造分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.account_id_extractor import extract_account_id_from_resources
        policy_dir = tmp_path / "check-ec2"
        policy_dir.mkdir()
        resources = [{
            "InstanceId": "i-456",
            "NetworkInterfaces": [
                {"NetworkInterfaceId": "eni-1", "OwnerId": "555666777888"}
            ]
        }]
        (policy_dir / "resources.json").write_text(
            json.dumps(resources), encoding="utf-8"
        )

        # Act
        with patch("app.jobs.utils.account_id_extractor.TaskLogger"):
            result = extract_account_id_from_resources(str(tmp_path), "job-004")

        # Assert
        assert result == "555666777888"

    def test_regional_arn_no_double_colon(self, tmp_path):
        """MA-034: リージョン付ARN（::不在）→ "unknown"

        account_id_extractor.py:L194 の `"::" in arn` 条件がFalseになる分岐をカバー。
        リージョン付きARN（arn:aws:ec2:us-east-1:123:...）は "::" を含まず、
        ARN解析パスに到達しないため "unknown" を返す。
        """
        # Arrange
        from app.jobs.utils.account_id_extractor import _extract_account_id_from_resources_file
        logger = MagicMock()
        resources_file = tmp_path / "resources.json"
        resources = [{
            "Arn": "arn:aws:ec2:us-east-1:123456789012:instance/i-abc123"
        }]
        resources_file.write_text(json.dumps(resources), encoding="utf-8")

        # Act
        result = _extract_account_id_from_resources_file(str(resources_file), logger)

        # Assert
        assert result == "unknown"

    def test_arn_parsing(self, tmp_path):
        """MA-022: ARNからアカウントIDを解析

        account_id_extractor.py:L192-197 の分岐をカバー。
        "::" を含むARN（リージョンなしのグローバルサービス）から
        アカウントIDを抽出する。
        """
        # Arrange
        from app.jobs.utils.account_id_extractor import extract_account_id_from_resources
        policy_dir = tmp_path / "check-iam"
        policy_dir.mkdir()
        resources = [{
            "Arn": "arn:aws:iam::999888777666:role/MyRole"
        }]
        (policy_dir / "resources.json").write_text(
            json.dumps(resources), encoding="utf-8"
        )

        # Act
        with patch("app.jobs.utils.account_id_extractor.TaskLogger"):
            result = extract_account_id_from_resources(str(tmp_path), "job-005")

        # Assert
        assert result == "999888777666"
```

### 2.9 extract_account_id_with_fallback テスト

```python
class TestExtractAccountIdWithFallback:
    """extract_account_id_with_fallback のテスト"""

    def test_metadata_success(self):
        """MA-023: 第1手段（メタデータ）で成功 → 即座に返却

        account_id_extractor.py:L105-107 の分岐をカバー。
        第1手段で成功した場合、第2・第3手段は呼び出されないことを検証。
        """
        # Arrange
        from app.jobs.utils.account_id_extractor import extract_account_id_with_fallback

        # Act
        with patch(
            "app.jobs.utils.account_id_extractor.extract_account_id_from_output_dir",
            return_value="111111111111"
        ) as mock_metadata, patch(
            "app.jobs.utils.account_id_extractor.extract_account_id_from_resources"
        ) as mock_resources, patch(
            "app.jobs.utils.account_id_extractor._extract_account_id_from_environment"
        ) as mock_env:
            result = extract_account_id_with_fallback("/dummy", "job-006")

        # Assert
        assert result == "111111111111"
        # 順序検証: 第1手段のみ正しい引数で呼ばれ、第2・第3手段は呼ばれない
        mock_metadata.assert_called_once_with("/dummy", "job-006")
        mock_resources.assert_not_called()
        mock_env.assert_not_called()

    def test_resources_fallback(self):
        """MA-024: 第2手段（リソースファイル）へのフォールバック

        account_id_extractor.py:L110-112 の分岐をカバー。
        メタデータ抽出が "unknown" を返した場合にリソースから抽出。
        第3手段は呼び出されないことを検証。
        """
        # Arrange
        from app.jobs.utils.account_id_extractor import extract_account_id_with_fallback

        # Act
        with patch(
            "app.jobs.utils.account_id_extractor.extract_account_id_from_output_dir",
            return_value="unknown"
        ) as mock_metadata, patch(
            "app.jobs.utils.account_id_extractor.extract_account_id_from_resources",
            return_value="222222222222"
        ) as mock_resources, patch(
            "app.jobs.utils.account_id_extractor._extract_account_id_from_environment"
        ) as mock_env:
            result = extract_account_id_with_fallback("/dummy", "job-007")

        # Assert
        assert result == "222222222222"
        # 順序検証: 第1・第2手段が正しい引数で呼ばれ、第3手段は呼ばれない
        mock_metadata.assert_called_once_with("/dummy", "job-007")
        mock_resources.assert_called_once_with("/dummy", "job-007")
        mock_env.assert_not_called()

    def test_environment_fallback(self):
        """MA-025: 第3手段（環境変数）へのフォールバック

        account_id_extractor.py:L115-117 の分岐をカバー。
        メタデータ・リソースが両方 "unknown" の場合に環境変数から抽出。
        全3手段が順序通り呼び出されることを検証。
        """
        # Arrange
        from app.jobs.utils.account_id_extractor import extract_account_id_with_fallback

        # Act
        with patch(
            "app.jobs.utils.account_id_extractor.extract_account_id_from_output_dir",
            return_value="unknown"
        ) as mock_metadata, patch(
            "app.jobs.utils.account_id_extractor.extract_account_id_from_resources",
            return_value="unknown"
        ) as mock_resources, patch(
            "app.jobs.utils.account_id_extractor._extract_account_id_from_environment",
            return_value="333333333333"
        ) as mock_env:
            result = extract_account_id_with_fallback("/dummy", "job-008")

        # Assert
        assert result == "333333333333"
        # 順序検証: 全3手段が正しい引数で1回ずつ呼ばれる
        mock_metadata.assert_called_once_with("/dummy", "job-008")
        mock_resources.assert_called_once_with("/dummy", "job-008")
        mock_env.assert_called_once()

    def test_all_fail_returns_unknown(self):
        """MA-026: 全手段失敗 → "unknown"

        account_id_extractor.py:L119 の最終フォールバックをカバー。
        """
        # Arrange
        from app.jobs.utils.account_id_extractor import extract_account_id_with_fallback

        # Act
        with patch(
            "app.jobs.utils.account_id_extractor.extract_account_id_from_output_dir",
            return_value="unknown"
        ), patch(
            "app.jobs.utils.account_id_extractor.extract_account_id_from_resources",
            return_value="unknown"
        ), patch(
            "app.jobs.utils.account_id_extractor._extract_account_id_from_environment",
            return_value="unknown"
        ):
            result = extract_account_id_with_fallback("/dummy", "job-009")

        # Assert
        assert result == "unknown"
```

### 2.10 アカウントID内部抽出テスト

```python
class TestAccountIdInternalExtractors:
    """_extract_account_id_from_metadata_file,
    _extract_account_id_from_resources_file,
    _extract_account_id_from_environment のテスト"""

    def test_metadata_file_config_account_id(self, tmp_path):
        """MA-027: config.account_idからアカウントID取得

        account_id_extractor.py:L138-142 の分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.account_id_extractor import _extract_account_id_from_metadata_file
        logger = MagicMock()
        metadata_file = tmp_path / "metadata.json"
        metadata_file.write_text(json.dumps({
            "config": {"account_id": "444555666777"}
        }), encoding="utf-8")

        # Act
        result = _extract_account_id_from_metadata_file(str(metadata_file), logger)

        # Assert
        assert result == "444555666777"

    def test_metadata_file_execution_account_fallback(self, tmp_path):
        """MA-028: config.account_idが無い場合にexecution.accountからフォールバック

        account_id_extractor.py:L145-149 の分岐をカバー。
        config.account_idが "unknown" の場合、execution.account を試行する。
        """
        # Arrange
        from app.jobs.utils.account_id_extractor import _extract_account_id_from_metadata_file
        logger = MagicMock()
        metadata_file = tmp_path / "metadata.json"
        metadata_file.write_text(json.dumps({
            "config": {"account_id": "unknown"},
            "execution": {"account": "888999000111"}
        }), encoding="utf-8")

        # Act
        result = _extract_account_id_from_metadata_file(str(metadata_file), logger)

        # Assert
        assert result == "888999000111"

    def test_resources_file_non_list_returns_unknown(self, tmp_path):
        """MA-029: リソースファイルが非リスト/空リストの場合は "unknown"

        account_id_extractor.py:L173-174 の分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.account_id_extractor import _extract_account_id_from_resources_file
        logger = MagicMock()

        # 非リスト
        f1 = tmp_path / "resources_dict.json"
        f1.write_text(json.dumps({"key": "value"}), encoding="utf-8")

        # 空リスト
        f2 = tmp_path / "resources_empty.json"
        f2.write_text(json.dumps([]), encoding="utf-8")

        # Act
        result1 = _extract_account_id_from_resources_file(str(f1), logger)
        result2 = _extract_account_id_from_resources_file(str(f2), logger)

        # Assert
        assert result1 == "unknown"
        assert result2 == "unknown"

    def test_environment_aws_account_id(self):
        """MA-030: AWS_ACCOUNT_ID環境変数からアカウントID取得

        account_id_extractor.py:L215-217 の分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.account_id_extractor import _extract_account_id_from_environment

        # Act
        with patch.dict(os.environ, {"AWS_ACCOUNT_ID": "env-123456"}, clear=False):
            result = _extract_account_id_from_environment()

        # Assert
        assert result == "env-123456"

    def test_environment_account_id_fallback(self):
        """MA-031: ACCOUNT_ID環境変数へのフォールバック

        account_id_extractor.py:L220-221 の分岐をカバー。
        AWS_ACCOUNT_IDが未設定の場合、ACCOUNT_IDを試行する。
        """
        # Arrange
        from app.jobs.utils.account_id_extractor import _extract_account_id_from_environment

        # Act — clear=True で既存環境変数を全除去し、ACCOUNT_IDのみ設定
        with patch.dict(os.environ, {"ACCOUNT_ID": "fallback-789"}, clear=True):
            result = _extract_account_id_from_environment()

        # Assert
        assert result == "fallback-789"

    def test_environment_no_env_vars(self):
        """MA-032: 環境変数未設定 → "unknown"

        account_id_extractor.py:L224 の最終フォールバックをカバー。
        """
        # Arrange
        from app.jobs.utils.account_id_extractor import _extract_account_id_from_environment

        # Act
        with patch.dict(os.environ, {}, clear=True):
            result = _extract_account_id_from_environment()

        # Assert
        assert result == "unknown"
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| MA-E01 | extract_metadata_from_output_dir glob例外 | glob.glob例外 | デフォルトメタデータ |
| MA-E02 | extract_scan_info_from_metadata Noneメタデータ | `None` | デフォルト値（外部except経由） |
| MA-E03 | extract_policy_details_from_metadata None入力 | `None` | デフォルト値（正常パス経由） |
| MA-E04 | _load_metadata_from_file 読み込み失敗 | 不正JSON | `{}` |
| MA-E05 | _collect_additional_metadata 初回例外 | ファイル読み込み例外 | 初期値（list型保証） |
| MA-E05b | _collect_additional_metadata 途中例外 | 2回目で例外 | 部分結果（list型保証） |
| MA-E06 | _sanitize_custodian_metadata 例外 | 内部処理例外 | 元データ返却 |
| MA-E07 | extract_account_id_from_output_dir 不正パス | 空文字/不存在 | `"unknown"` |
| MA-E08 | extract_account_id_from_output_dir os.listdir例外 | 権限エラー | `"unknown"` |
| MA-E09 | _extract_account_id_from_metadata_file JSON解析エラー | 不正JSON | `"unknown"` |
| MA-E10 | extract_account_id_from_resources 不正パス | 空文字/不存在 | `"unknown"` |
| MA-E11 | extract_account_id_from_resources os.listdir例外 | 権限エラー | `"unknown"` |

### 3.1 メタデータ抽出 異常系

```python
class TestMetadataExtractorErrors:
    """metadata_extractor エラーテスト"""

    def test_extract_metadata_glob_exception(self):
        """MA-E01: glob.globで例外発生時にデフォルトメタデータを返す

        metadata_extractor.py:L57-59 の外部例外分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.metadata_extractor import extract_metadata_from_output_dir

        # Act
        with patch("app.jobs.utils.metadata_extractor.TaskLogger"), \
             patch("app.jobs.utils.metadata_extractor.glob.glob",
                   side_effect=PermissionError("access denied")):
            result = extract_metadata_from_output_dir("/dummy", "job-err-01")

        # Assert
        assert result["policy"]["name"] == "unknown"
        assert result["scan_statistics"]["total_policies"] == 0

    def test_scan_info_none_metadata(self):
        """MA-E02: Noneメタデータ → 外部例外でデフォルト値を返す

        metadata_extractor.py:L83 の `if metadata and "config" in metadata`
        で None は短絡評価されFalse。続く L94 の `if "version" in metadata`
        で `"version" in None` が TypeError を発生させ、
        L115 の外部 except で捕捉されてデフォルト値を返す。
        """
        # Arrange
        from app.jobs.utils.metadata_extractor import extract_scan_info_from_metadata

        # Act
        result = extract_scan_info_from_metadata(None)

        # Assert
        assert result["account_id"] == "unknown"
        assert result["region"] == "unknown"
        assert result["cloud_provider"] == "aws"

    def test_policy_details_none_metadata(self):
        """MA-E03: Noneメタデータ → 正常パスでデフォルト値を返す

        metadata_extractor.py:L146 の `metadata and "policy" in metadata` で
        Noneは短絡評価されFalseとなり、except節には到達しない。
        デフォルト値の policy_details がそのまま返される正常系の動作を確認。
        """
        # Arrange
        from app.jobs.utils.metadata_extractor import extract_policy_details_from_metadata

        # Act
        result = extract_policy_details_from_metadata(None)

        # Assert
        assert result["name"] == "unknown"
        assert result["filters"] == []
        assert result["actions"] == []

    def test_load_metadata_invalid_json(self, tmp_path):
        """MA-E04: 不正なJSONファイル → 空辞書を返す

        metadata_extractor.py:L195-197 の例外分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.metadata_extractor import _load_metadata_from_file
        logger = MagicMock()
        invalid_file = tmp_path / "metadata.json"
        invalid_file.write_text("{broken json", encoding="utf-8")

        # Act
        result = _load_metadata_from_file(str(invalid_file), logger)

        # Assert
        assert result == {}
        logger.warning.assert_called_once()

    def test_collect_additional_metadata_exception(self):
        """MA-E05: ファイル読み込み中の例外 → 部分結果を返す（型整合性保証）

        metadata_extractor.py:L244-251 の外部 except 分岐をカバー。
        _load_metadata_from_file が想定外の例外を送出した場合、
        外部 except で捕捉され、additional_info（初期値のまま）を返す。

        **重要**: 例外経路でも resource_types / regions は list 型で返す。
        初期値は set()（L214-215）だが、例外ハンドラ内の set→list 変換
        （L247-250）により list に変換してから返却する。
        これにより、上流が常に list 型を前提にできることを保証する。

        **実装修正**: 本テスト仕様に合わせ、metadata_extractor.py の
        except ブロック（L246-250）に set→list 変換ロジックを追加済み。
        修正前は set のまま返却されていたバグを修正。
        """
        # Arrange
        from app.jobs.utils.metadata_extractor import _collect_additional_metadata
        logger = MagicMock()

        # Act
        # _load_metadata_from_fileが例外を送出するようモック
        with patch(
            "app.jobs.utils.metadata_extractor._load_metadata_from_file",
            side_effect=Exception("unexpected error")
        ):
            result = _collect_additional_metadata(["file1.json", "file2.json"], logger)

        # Assert
        # total_policiesは初期値（len(files) + 1 = 3）
        assert result["total_policies"] == 3
        assert result["policy_names"] == []
        # 例外経路でも resource_types / regions は list 型であること
        assert isinstance(result["resource_types"], list)
        assert isinstance(result["regions"], list)
        assert result["resource_types"] == []
        assert result["regions"] == []
        logger.warning.assert_called_once()

    def test_collect_additional_metadata_partial_exception(self):
        """MA-E05b: ループ途中で例外 → 部分結果をlist型で返す

        metadata_extractor.py:L219-246 のループ途中例外をカバー。
        1回目のファイル読み込みは成功し、2回目で例外が発生した場合、
        1回目の処理結果を含む部分結果が set→list 変換済みで返却される。
        """
        # Arrange
        from app.jobs.utils.metadata_extractor import _collect_additional_metadata
        logger = MagicMock()

        call_count = 0
        def mock_load(path, logger):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {
                    "policy": {"name": "policy-a", "resource": "aws.ec2"},
                    "config": {"region": "us-east-1"}
                }
            raise Exception("2回目で失敗")

        # Act
        with patch(
            "app.jobs.utils.metadata_extractor._load_metadata_from_file",
            side_effect=mock_load
        ):
            result = _collect_additional_metadata(
                ["file1.json", "file2.json"], logger
            )

        # Assert
        # total_policiesは初期値（len(files) + 1 = 3）
        assert result["total_policies"] == 3
        # 1回目の処理結果が含まれる
        assert "policy-a" in result["policy_names"]
        # set→list変換が適用されている
        assert isinstance(result["resource_types"], list)
        assert isinstance(result["regions"], list)
        assert "aws.ec2" in result["resource_types"]
        assert "us-east-1" in result["regions"]
        logger.warning.assert_called_once()

    def test_sanitize_metadata_exception_returns_original(self):
        """MA-E06: 内部処理で例外 → 元のメタデータをそのまま返す

        metadata_extractor.py:L312-313 の例外分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.metadata_extractor import _sanitize_custodian_metadata
        metadata = {"policy": {"name": "test"}, "unknown_key": "value"}

        # Act
        # sys-stats処理（L301-303）で _normalize_numeric_fields が呼ばれTypeErrorを発生させる
        with patch(
            "app.jobs.utils.metadata_extractor._normalize_numeric_fields",
            side_effect=TypeError("type error")
        ):
            # sys-statsキーが存在する場合に _normalize_numeric_fields が呼ばれる
            metadata_with_sys = {**metadata, "sys-stats": {"cpu": 45}}
            result = _sanitize_custodian_metadata(metadata_with_sys)

        # Assert
        # 例外時は元のメタデータをそのまま返す
        assert result == metadata_with_sys
```

### 3.2 アカウントID抽出 異常系

```python
class TestAccountIdExtractorErrors:
    """account_id_extractor エラーテスト"""

    def test_invalid_path(self):
        """MA-E07: 空文字/不存在パス → "unknown"

        account_id_extractor.py:L31 のガード条件をカバー。
        """
        # Arrange
        from app.jobs.utils.account_id_extractor import extract_account_id_from_output_dir

        # Act & Assert
        with patch("app.jobs.utils.account_id_extractor.TaskLogger"):
            # 空文字
            assert extract_account_id_from_output_dir("", "job-err-07a") == "unknown"
            # 存在しないパス
            assert extract_account_id_from_output_dir(
                "/nonexistent/path", "job-err-07b"
            ) == "unknown"

    def test_listdir_exception(self, tmp_path):
        """MA-E08: os.listdirで例外発生時は "unknown"

        account_id_extractor.py:L51-53 の例外分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.account_id_extractor import extract_account_id_from_output_dir

        # Act
        with patch("app.jobs.utils.account_id_extractor.TaskLogger"), \
             patch("app.jobs.utils.account_id_extractor.os.listdir",
                   side_effect=PermissionError("access denied")):
            result = extract_account_id_from_output_dir(str(tmp_path), "job-err-08")

        # Assert
        assert result == "unknown"

    def test_metadata_file_invalid_json(self, tmp_path):
        """MA-E09: メタデータファイルのJSON解析エラー → "unknown"

        account_id_extractor.py:L153-155 の例外分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.account_id_extractor import _extract_account_id_from_metadata_file
        logger = MagicMock()
        invalid_file = tmp_path / "metadata.json"
        invalid_file.write_text("{invalid}", encoding="utf-8")

        # Act
        result = _extract_account_id_from_metadata_file(str(invalid_file), logger)

        # Assert
        assert result == "unknown"
        logger.warning.assert_called_once()

    def test_resources_invalid_path(self):
        """MA-E10: extract_account_id_from_resources に空文字/不存在パス → "unknown"

        account_id_extractor.py:L70-71 のガード条件をカバー。
        extract_account_id_from_output_dir（MA-E07）と対称のテスト。
        """
        # Arrange
        from app.jobs.utils.account_id_extractor import extract_account_id_from_resources

        # Act & Assert
        with patch("app.jobs.utils.account_id_extractor.TaskLogger"):
            # 空文字
            assert extract_account_id_from_resources("", "job-err-10a") == "unknown"
            # 存在しないパス
            assert extract_account_id_from_resources(
                "/nonexistent/path", "job-err-10b"
            ) == "unknown"

    def test_resources_listdir_exception(self, tmp_path):
        """MA-E11: extract_account_id_from_resources で os.listdir 例外 → "unknown"

        account_id_extractor.py:L88-90 の例外分岐をカバー。
        extract_account_id_from_output_dir（MA-E08）と対称のテスト。
        """
        # Arrange
        from app.jobs.utils.account_id_extractor import extract_account_id_from_resources

        # Act
        with patch("app.jobs.utils.account_id_extractor.TaskLogger"), \
             patch("app.jobs.utils.account_id_extractor.os.listdir",
                   side_effect=PermissionError("access denied")):
            result = extract_account_id_from_resources(str(tmp_path), "job-err-11")

        # Assert
        assert result == "unknown"
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| MA-SEC-01 | パストラバーサル入力の現状動作確認 | `"../../etc/passwd"` | `{}` (読み込み失敗) |
| MA-SEC-02 | アカウントID特殊文字のパススルー動作確認 | SQLインジェクション文字列 | 文字列としてそのまま返却 |
| MA-SEC-03 | 大量入力データのDoS耐性 | 1000フィールドのメタデータ | クラッシュせず正常完了 |

```python
@pytest.mark.security
class TestMetadataAccountSecurity:
    """メタデータ・アカウント抽出セキュリティテスト"""

    def test_path_traversal_behavior(self, tmp_path):
        """MA-SEC-01: パストラバーサル入力の現状動作確認

        _load_metadata_from_fileにパストラバーサルを含むパスが渡された場合の
        現行挙動を確認する。実装にはパス検証がないため、本テストは
        防御機構の検証ではなく挙動の記録として位置づける。
        実運用ではパスは glob.glob の結果（内部生成）のため低リスク。
        """
        # Arrange
        from app.jobs.utils.metadata_extractor import _load_metadata_from_file
        logger = MagicMock()
        malicious_path = str(tmp_path / ".." / ".." / "etc" / "passwd")

        # Act
        result = _load_metadata_from_file(malicious_path, logger)

        # Assert
        # ファイル不存在またはJSON解析失敗で空辞書
        assert result == {}
        assert logger.warning.called

    def test_account_id_special_characters(self, tmp_path):
        """MA-SEC-02: 特殊文字を含むアカウントIDのパススルー動作確認

        SQLインジェクション風の文字列がアカウントIDとして
        メタデータに含まれていた場合、そのまま文字列として返却される。
        本モジュールはデータ抽出が責務であり、入力バリデーションは
        下流の利用側が行うため、パススルー動作が正しい挙動である。
        """
        # Arrange
        from app.jobs.utils.account_id_extractor import _extract_account_id_from_metadata_file
        logger = MagicMock()
        malicious_id = "'; DROP TABLE accounts; --"
        metadata_file = tmp_path / "metadata.json"
        metadata_file.write_text(json.dumps({
            "config": {"account_id": malicious_id}
        }), encoding="utf-8")

        # Act
        result = _extract_account_id_from_metadata_file(str(metadata_file), logger)

        # Assert
        # 文字列としてそのまま返却（サニタイズはこのモジュールの責務外）
        assert result == malicious_id
        assert isinstance(result, str)

    @pytest.mark.slow
    def test_large_metadata_dos_resilience(self):
        """MA-SEC-03: 大量入力データの処理安定性（DoS耐性）

        大量フィールド（1000件のsys-stats、100件のmetrics）を持つ
        メタデータを _sanitize_custodian_metadata に渡した場合、
        メモリ枯渇やタイムアウトなくサニタイズが正常完了することを確認する。

        性能基準: 処理時間が30秒以内であること。
        通常は数十ミリ秒で完了するため、30秒超は深刻な性能回帰の兆候。
        閾値はCI環境の負荷変動を考慮し余裕を持たせている。

        @pytest.mark.slow により通常テスト実行から分離可能:
          pytest -m "not slow"  # 通常テスト（本テストを除外）
          pytest -m slow        # 性能テストのみ実行
        """
        import time
        # Arrange
        from app.jobs.utils.metadata_extractor import _sanitize_custodian_metadata
        large_metadata = {
            "policy": {"name": "test"},
            "version": "1.0",
            "sys-stats": {f"metric_{i}": i * 1.5 for i in range(1000)},
            "metrics": [{"value": i} for i in range(100)]
        }

        # Act
        start_time = time.monotonic()
        result = _sanitize_custodian_metadata(large_metadata)
        elapsed = time.monotonic() - start_time

        # Assert
        assert isinstance(result, dict)
        assert "policy" in result
        assert "sys-stats" in result
        # 全数値が文字列に変換されている
        for key, value in result["sys-stats"].items():
            assert isinstance(value, str)
        # 性能基準: 30秒以内に完了すること（通常は数十ms、CI負荷考慮）
        assert elapsed < 30.0, f"処理時間 {elapsed:.2f}秒 が上限30秒を超過"
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_utils_module` | テスト間のモジュール状態リセット | function | Yes |

> **注記**: `reset_utils_module` は #17a の conftest.py（`test/unit/jobs/utils/conftest.py`）で定義予定。#17a のテスト仕様書で仕様化済みだが、テストコード実装が未完了の場合は先に conftest.py を作成する必要がある。`metadata_extractor` および `account_id_extractor` はモジュールレベルの可変状態を持たない（`import` 文のみ）ため、`sys.modules` クリーンアップは安全に動作する。テスト内で関数をインポートする方式（import-inside-method）を使用することで、各テストが新しいモジュールインスタンスから関数を取得する。

### 共通フィクスチャ定義

```python
# test/unit/jobs/utils/conftest.py（#17a 仕様書で定義予定・共有）
import sys
import pytest

# 本テストファイルで使用するモジュールのみを対象とする
# app.jobs.utils 全体を削除すると、トップレベル import を利用する
# 他テストファイルに副作用を及ぼすリスクがあるため、対象を限定する
_TARGET_MODULES = (
    "app.jobs.utils.metadata_extractor",
    "app.jobs.utils.account_id_extractor",
)


@pytest.fixture(autouse=True)
def reset_utils_module():
    """テストごとにモジュールのグローバル状態をリセット

    metadata_extractor / account_id_extractor のモジュールキャッシュのみ
    クリアし、テスト間の独立性を保証する。
    """
    yield
    # テスト後にクリーンアップ（対象モジュールのみ）
    modules_to_remove = [
        key for key in sys.modules
        if key in _TARGET_MODULES
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]
```

---

## 6. テスト実行例

```bash
# メタデータ・アカウント抽出テストのみ実行
pytest test/unit/jobs/utils/test_metadata_account.py -v

# 特定のテストクラスのみ実行
pytest test/unit/jobs/utils/test_metadata_account.py::TestExtractScanInfo -v

# カバレッジ付きで実行
pytest test/unit/jobs/utils/test_metadata_account.py \
  --cov=app.jobs.utils.metadata_extractor \
  --cov=app.jobs.utils.account_id_extractor \
  --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/jobs/utils/test_metadata_account.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 35 | MA-001 〜 MA-035 |
| 異常系 | 12 | MA-E01 〜 MA-E11, MA-E05b |
| セキュリティ | 3 | MA-SEC-01 〜 MA-SEC-03 |
| **合計** | **50** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestExtractMetadataFromOutputDir` | MA-001〜MA-002 | 2 |
| `TestExtractScanInfo` | MA-003〜MA-005, MA-033 | 4 |
| `TestExtractPolicyDetails` | MA-006〜MA-007 | 2 |
| `TestMetadataProcessing` | MA-008〜MA-010, MA-035 | 4 |
| `TestSanitizeAndNormalize` | MA-011〜MA-016 | 6 |
| `TestCreateDefaultMetadata` | MA-017 | 1 |
| `TestExtractAccountIdFromOutputDir` | MA-018〜MA-019 | 2 |
| `TestExtractAccountIdFromResources` | MA-020〜MA-022, MA-034 | 4 |
| `TestExtractAccountIdWithFallback` | MA-023〜MA-026 | 4 |
| `TestAccountIdInternalExtractors` | MA-027〜MA-032 | 6 |
| `TestMetadataExtractorErrors` | MA-E01〜MA-E06, MA-E05b | 7 |
| `TestAccountIdExtractorErrors` | MA-E07〜MA-E11 | 5 |
| `TestMetadataAccountSecurity` | MA-SEC-01〜MA-SEC-03 | 3 |

### 7.3 予想失敗テスト

現時点で失敗が予想されるテストはありません。

> **MA-E05 / MA-E05b 修正履歴**: 元の実装では `_collect_additional_metadata` の例外経路で `resource_types` / `regions` が `set` のまま返却されるバグがあった。`metadata_extractor.py` の except ブロック（L246-250）に set→list 変換ロジックを追加する実装修正を適用済み。修正後の実装では MA-E05 / MA-E05b ともに成功する。

> **MA-E02 について**: `extract_scan_info_from_metadata(None)` は `None` が `Dict[str, Any]` の型ヒントに反するが、実装は外部 `except` で安全に処理する。テストは現在の実装動作を検証するもので、テスト自体は成功する。

### 注意事項

- `@pytest.mark.security` マーカーは `pyproject.toml` に `markers = ["security: セキュリティ関連テスト"]` の登録が必要
- `@pytest.mark.slow` マーカーは `pyproject.toml` に `markers = ["slow: 性能テスト（CI環境での実行時間に注意）"]` の登録が必要
- `tmp_path` フィクスチャはpytest組み込みのため追加パッケージ不要
- テスト内で関数をインポートする方式（import-inside-method）を使用。`reset_utils_module` の `sys.modules` クリーンアップと組み合わせてテスト間の独立性を保証
- `TaskLogger` は公開関数テスト時にモック必要。プライベート関数は `logger` パラメータに `MagicMock()` を直接渡す
- `_extract_account_id_from_environment` のテストでは `patch.dict(os.environ, ...)` で環境変数を制御

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `_collect_additional_metadata` が `set` を使用するため、`resource_types` と `regions` の順序が不定 | テストで順序依存のアサーションを使えない | `set()` で比較するか、`sorted()` を使用 |
| 2 | `_extract_account_id_from_resources_file` の ARN 解析は `"::" in arn` 条件でフィルタ | リージョン付きARN（`arn:aws:ec2:us-east-1:123:...`）からはアカウントIDを抽出できない | 実運用ではOwnerId優先のため低影響。ARN解析はフォールバック手段 |
| 3 | `extract_scan_info_from_metadata` の `scan_timestamp` は `datetime.now()` で生成 | テストで厳密な値比較が困難 | 型（str）と形式（ISO 8601）のみ検証 |
| 4 | `metadata_extractor` と `field_normalizers` に同名の内部関数が存在（`_normalize_numeric_fields` 等） | テスト対象の関数を取り違える可能性 | テスト内のインポートパスを `app.jobs.utils.metadata_extractor` に明示的に指定 |
| 5 | `_extract_account_id_from_environment` は `os.environ` を直接参照 | テスト間で環境変数が漏洩する可能性 | `patch.dict(os.environ, ...)` で各テスト内でスコープを限定 |
| 6 | `_create_default_metadata` 内の `datetime.now(timezone.utc).timestamp()` は実行時刻依存 | テストで厳密な値比較が困難 | `isinstance(value, float)` で型のみ検証 |
| 7 | エラーログにファイルパスが含まれる（metadata_extractor:L196, account_id_extractor:L154） | 本番環境でのログにサーバー内部パスが露出する可能性 | 実運用時のログレベル設定で制御。テストでは現行動作の記録に留める |
| 8 | アカウントIDのフォーマット検証なし（12桁数値かの妥当性チェック未実装） | 不正な値がそのまま返却される | 入力検証は上位モジュールの責務。本モジュールは抽出に特化 |
