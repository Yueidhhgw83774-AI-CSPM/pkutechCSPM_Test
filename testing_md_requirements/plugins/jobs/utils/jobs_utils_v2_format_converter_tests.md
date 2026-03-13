# jobs/utils v2フォーマットコンバーター テストケース (#17d)

## 1. 概要

`app/jobs/utils/v2_format_converter.py` のテスト仕様書。Custodianスキャン結果をcspm-scan-result-v2フォーマットに変換するメインロジックをテストする。ヘルパー群（#17c）の上位レイヤーとして、変換のオーケストレーションと入力検証を検証する。

### 1.1 主要機能

| 関数 | 行 | 説明 |
|------|-----|------|
| `convert_to_v2_format()` | L47-129 | 単一リソースのv2フォーマット変換 |
| `convert_custodian_output_to_v2_hierarchical()` | L132-224 | Custodian出力全体を階層化v2フォーマットに変換 |
| `_collect_policies_data()` | L227-281 | 出力ディレクトリから全ポリシーデータを収集 |
| `_build_hierarchical_policy()` | L284-339 | 単一ポリシーの階層構造構築 |
| `_extract_policy_metadata_fields()` | L342-414 | メタデータフィールド抽出 |
| `_build_policy_definition()` | L417-448 | ポリシー定義構築 |
| `_get_default_metadata_fields()` | L451-466 | デフォルトメタデータフィールド |
| `_organize_resources_by_region()` | L469-521 | リージョン別リソース整理 |

### 1.2 カバレッジ目標: 90%

> **注記**: 本モジュールは #17c で検証済みのヘルパー群に依存する。ヘルパー関数はモックし、本モジュール固有のオーケストレーションロジックと入力検証に集中する。ファイルI/O（`os.path.exists`, `glob.glob`）と `datetime.now` はモック対象。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/jobs/utils/v2_format_converter.py` (525行) |
| テストコード | `test/unit/jobs/utils/test_v2_format_converter.py` |
| conftest | `test/unit/jobs/utils/conftest.py` |

### 1.4 依存関係

```
v2_format_converter.py（本仕様書の対象）
├── resource_id_extractor.py → build_resource_arn（L30）
├── v2_format_helpers.py → extract_account_id, extract_region, build_error_response（L31-33）
├── v2_hierarchical_helpers.py → 11関数（L34-39）
├── v2_format_legacy_functions.py → 3関数（L40-42）
└── 標準ライブラリ: os, glob, datetime, collections.defaultdict, logging
```

> **モック方針**: ヘルパー関数はモジュールレベルimport済み（L30-42）のため、`app.jobs.utils.v2_format_converter.関数名` でパッチする。

### 1.5 主要分岐マップ

| 関数 | 分岐 | 行 |
|------|------|-----|
| `convert_to_v2_format` | 必須パラメータ不足 | L79 |
| `convert_to_v2_format` | account_id 自動抽出 | L90-91 |
| `convert_to_v2_format` | region 自動抽出 | L92-93 |
| `convert_to_v2_format` | 例外キャッチ | L127-129 |
| `convert_custodian_output_to_v2_hierarchical` | 必須パラメータ不足 | L161 |
| `convert_custodian_output_to_v2_hierarchical` | ディレクトリ不存在 | L166-169 |
| `convert_custodian_output_to_v2_hierarchical` | ポリシーデータ空 | L174-176 |
| `convert_custodian_output_to_v2_hierarchical` | policy_status集計 | L194 |
| `convert_custodian_output_to_v2_hierarchical` | 例外キャッチ | L221-224 |
| `_collect_policies_data` | 同名ポリシーマージ | L263-266 |
| `_collect_policies_data` | 新規ポリシー登録 | L267-273 |
| `_collect_policies_data` | 例外キャッチ | L279-281 |
| `_build_hierarchical_policy` | 例外キャッチ | L337-339 |
| `_extract_policy_metadata_fields` | 例外キャッチ | L412-414 |
| `_build_policy_definition` | description 有無 | L430-432 |
| `_build_policy_definition` | filters 有無 | L435-436 |
| `_build_policy_definition` | actions 有無 | L440-442 |
| `_build_policy_definition` | 空定義 | L445-446 |
| `_organize_resources_by_region` | unknown-region フォールバック | L497-498 |
| `_organize_resources_by_region` | 例外キャッチ | L519-521 |

---

## 2. 正常系テストケース

| ID | テスト名 | 検証内容 | 期待結果 |
|----|---------|---------|---------|
| VC-001 | convert_to_v2_format 正常変換 | 全パラメータ指定での変換 | 5キー構造（resource_identity, violation_context, resource_snapshot, metadata, raw_resource） |
| VC-002 | convert_to_v2_format account_id自動抽出 | account_id=None時 | extract_account_id が呼ばれる |
| VC-003 | convert_to_v2_format region自動抽出 | region=None時 | extract_region が呼ばれる |
| VC-004 | convert_to_v2_format account_id/region明示指定 | 両方指定時 | 自動抽出関数が呼ばれない |
| VC-005 | convert_to_v2_format metadata構造 | timestampとcustodian_version | ISO8601形式のtimestamp、version="0.9.42" |
| VC-006 | convert_to_v2_format raw_resource保持 | raw_resourceフィールド | 入力resource_dataがそのまま保持 |
| VC-007 | convert_custodian_output 正常変換 | 1ポリシー・1リソース | 階層構造ドキュメント（scan_id, account_id, policies, scan_summary） |
| VC-008 | convert_custodian_output 複数ポリシー | 3ポリシー | total_policies=3、policy_summary集計が正しい |
| VC-009 | convert_custodian_output policy_statistics連携 | statistics指定 | statsが_build_hierarchical_policyに渡される |
| VC-010 | convert_custodian_output policy_statistics未指定 | None時 | stats=Noneで_build_hierarchical_policyが呼ばれる |
| VC-011 | convert_custodian_output policy_summary集計 | success/partial_success/failed混在 | 各カウントが正しい |
| VC-012 | convert_custodian_output total_resources集計 | 複数リージョン・複数リソース | resource_countの合計 |
| VC-013 | convert_custodian_output doc_type | ドキュメントタイプフィールド | "hierarchical_scan_result_v2" |
| VC-014 | _collect_policies_data 正常収集 | 複数resources.json | ポリシー名→データのDict |
| VC-015 | _collect_policies_data 同名ポリシーマージ | 同一ポリシー名が複数回出現 | resources配列がextendされる |
| VC-016 | _collect_policies_data ポリシーなし | resources.jsonなし | 空Dict |
| VC-017 | _build_hierarchical_policy 正常構築 | リソース・メタデータ・統計情報あり | 7キー構造（policy_name, policy_status, resource_type等） |
| VC-018 | _build_hierarchical_policy statistics=None | 統計情報なし | _build_execution_detailsにNoneが渡される |
| VC-019 | _build_hierarchical_policy メタデータフィールドマージ | policy_metadata_fieldsの統合 | hierarchical_policyにseverity等が含まれる |
| VC-020 | _extract_policy_metadata_fields 全フィールド | metadata完備 | 7フィールド（uuid, id, versions, severity, title, definition） |
| VC-020b | _extract_policy_metadata_fields 仕様キー名乖離 | recommendation_uuidキー使用 | None（実装はuuidキーを読む）— 仕様乖離記録 |
| VC-021 | _extract_policy_metadata_fields severity デフォルト | severityキーなし | "Medium" |
| VC-022 | _extract_policy_metadata_fields title フォールバック | metadata.titleなし | policy.nameが使用される |
| VC-023 | _extract_policy_metadata_fields title優先 | metadata.titleとpolicy.name両方 | metadata.titleが優先 |
| VC-024 | _extract_policy_metadata_fields 空メタデータ | 空Dict | uuid等はNone、severity="Medium"、policy_title="" |
| VC-025 | _build_policy_definition 全フィールド | description, filters, actions全て存在 | 3キーのDict |
| VC-026 | _build_policy_definition 部分フィールド | descriptionのみ | descriptionのみのDict |
| VC-027 | _build_policy_definition 空ポリシー | 全フィールドなし | 空Dict |
| VC-028 | _build_policy_definition 型チェック | description=123, filters="abc" | 不正な型は除外 |
| VC-029 | _get_default_metadata_fields デフォルト値 | 引数なし | 7キー（全てNone/Medium/空Dict） |
| VC-030 | _organize_resources_by_region 正常整理 | 2リージョン・各2リソース | リージョン名ソート済みリスト |
| VC-031 | _organize_resources_by_region unknown-regionフォールバック | リソースにリージョン情報なし | metadata.config.regionが使用される |
| VC-032 | _organize_resources_by_region metadata_regionもunknown | 両方unknown | "unknown-region"のまま |
| VC-033 | _organize_resources_by_region リージョンソート | us-west-2, ap-northeast-1, eu-west-1 | アルファベット順 |

### 共通import

```python
import pytest
import sys
import os
import json
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, timezone
from collections import defaultdict

# テスト対象
from app.jobs.utils.v2_format_converter import (
    convert_to_v2_format,
    convert_custodian_output_to_v2_hierarchical,
    _collect_policies_data,
    _build_hierarchical_policy,
    _extract_policy_metadata_fields,
    _build_policy_definition,
    _get_default_metadata_fields,
    _organize_resources_by_region,
)
```

### 2.1 convert_to_v2_format テスト

```python
class TestConvertToV2Format:
    """convert_to_v2_format のテスト"""

    class TestNormalConversion:
        """正常変換テスト"""

        @patch("app.jobs.utils.v2_format_converter._create_resource_snapshot")
        @patch("app.jobs.utils.v2_format_converter._build_violation_context_v2")
        @patch("app.jobs.utils.v2_format_converter._build_resource_identity")
        @patch("app.jobs.utils.v2_format_converter.build_resource_arn")
        @patch("app.jobs.utils.v2_format_converter.datetime")
        def test_convert_normal_all_params(
            self, mock_dt, mock_build_arn, mock_identity, mock_violation, mock_snapshot
        ):
            """VC-001: 全パラメータ指定での正常変換"""
            # Arrange
            mock_dt.now.return_value.isoformat.return_value = "2024-01-01T00:00:00+00:00"
            mock_build_arn.return_value = "arn:aws:ec2:us-east-1:123456:instance/i-abc"
            mock_identity.return_value = {"resource_id": "i-abc"}
            mock_violation.return_value = {"policy_name": "test-policy"}
            mock_snapshot.return_value = {"type": "ec2"}
            resource_data = {"InstanceId": "i-abc"}

            # Act
            result = convert_to_v2_format(
                scan_id="scan-001",
                policy_name="test-policy",
                resource_data=resource_data,
                resource_type="aws.ec2",
                account_id="123456",
                region="us-east-1",
                policy_description="テスト"
            )

            # Assert
            assert "resource_identity" in result
            assert "violation_context" in result
            assert "resource_snapshot" in result
            assert "metadata" in result
            assert "raw_resource" in result
            assert result["raw_resource"] == resource_data

        @patch("app.jobs.utils.v2_format_converter._create_resource_snapshot")
        @patch("app.jobs.utils.v2_format_converter._build_violation_context_v2")
        @patch("app.jobs.utils.v2_format_converter._build_resource_identity")
        @patch("app.jobs.utils.v2_format_converter.build_resource_arn")
        @patch("app.jobs.utils.v2_format_converter.extract_account_id")
        @patch("app.jobs.utils.v2_format_converter.datetime")
        def test_convert_auto_extract_account_id(
            self, mock_dt, mock_extract_acct, mock_build_arn,
            mock_identity, mock_violation, mock_snapshot
        ):
            """VC-002: account_id未指定時に自動抽出"""
            # Arrange
            mock_dt.now.return_value.isoformat.return_value = "2024-01-01T00:00:00+00:00"
            mock_extract_acct.return_value = "auto-acct-123"
            mock_build_arn.return_value = "arn:aws:ec2:us-east-1:auto-acct-123:instance/i-abc"
            mock_identity.return_value = {"resource_id": "i-abc"}
            mock_violation.return_value = {}
            mock_snapshot.return_value = {}

            # Act
            result = convert_to_v2_format(
                scan_id="scan-001",
                policy_name="test-policy",
                resource_data={"InstanceId": "i-abc"},
                resource_type="aws.ec2",
                account_id=None,
                region="us-east-1"
            )

            # Assert
            mock_extract_acct.assert_called_once()
            assert "resource_identity" in result

        @patch("app.jobs.utils.v2_format_converter._create_resource_snapshot")
        @patch("app.jobs.utils.v2_format_converter._build_violation_context_v2")
        @patch("app.jobs.utils.v2_format_converter._build_resource_identity")
        @patch("app.jobs.utils.v2_format_converter.build_resource_arn")
        @patch("app.jobs.utils.v2_format_converter.extract_region")
        @patch("app.jobs.utils.v2_format_converter.datetime")
        def test_convert_auto_extract_region(
            self, mock_dt, mock_extract_region, mock_build_arn,
            mock_identity, mock_violation, mock_snapshot
        ):
            """VC-003: region未指定時に自動抽出"""
            # Arrange
            mock_dt.now.return_value.isoformat.return_value = "2024-01-01T00:00:00+00:00"
            mock_extract_region.return_value = "us-west-2"
            mock_build_arn.return_value = "arn:aws:ec2:us-west-2:123456:instance/i-abc"
            mock_identity.return_value = {"resource_id": "i-abc"}
            mock_violation.return_value = {}
            mock_snapshot.return_value = {}

            # Act
            result = convert_to_v2_format(
                scan_id="scan-001",
                policy_name="test-policy",
                resource_data={"InstanceId": "i-abc"},
                resource_type="aws.ec2",
                account_id="123456",
                region=None
            )

            # Assert
            mock_extract_region.assert_called_once()
            assert "resource_identity" in result

        @patch("app.jobs.utils.v2_format_converter._create_resource_snapshot")
        @patch("app.jobs.utils.v2_format_converter._build_violation_context_v2")
        @patch("app.jobs.utils.v2_format_converter._build_resource_identity")
        @patch("app.jobs.utils.v2_format_converter.build_resource_arn")
        @patch("app.jobs.utils.v2_format_converter.extract_region")
        @patch("app.jobs.utils.v2_format_converter.extract_account_id")
        @patch("app.jobs.utils.v2_format_converter.datetime")
        def test_convert_explicit_params_skip_extraction(
            self, mock_dt, mock_extract_acct, mock_extract_region,
            mock_build_arn, mock_identity, mock_violation, mock_snapshot
        ):
            """VC-004: account_id/region明示指定時は自動抽出しない"""
            # Arrange
            mock_dt.now.return_value.isoformat.return_value = "2024-01-01T00:00:00+00:00"
            mock_build_arn.return_value = "arn:aws:ec2:us-east-1:123456:instance/i-abc"
            mock_identity.return_value = {"resource_id": "i-abc"}
            mock_violation.return_value = {}
            mock_snapshot.return_value = {}

            # Act
            convert_to_v2_format(
                scan_id="scan-001",
                policy_name="test-policy",
                resource_data={"InstanceId": "i-abc"},
                resource_type="aws.ec2",
                account_id="123456",
                region="us-east-1"
            )

            # Assert — 自動抽出関数が呼ばれないことを確認
            mock_extract_acct.assert_not_called()
            mock_extract_region.assert_not_called()

        @patch("app.jobs.utils.v2_format_converter._create_resource_snapshot")
        @patch("app.jobs.utils.v2_format_converter._build_violation_context_v2")
        @patch("app.jobs.utils.v2_format_converter._build_resource_identity")
        @patch("app.jobs.utils.v2_format_converter.build_resource_arn")
        @patch("app.jobs.utils.v2_format_converter.datetime")
        def test_convert_metadata_structure(
            self, mock_dt, mock_build_arn, mock_identity, mock_violation, mock_snapshot
        ):
            """VC-005: metadataにtimestampとcustodian_versionが含まれる"""
            # Arrange
            mock_dt.now.return_value.isoformat.return_value = "2024-01-01T00:00:00+00:00"
            mock_build_arn.return_value = "arn:aws:ec2:us-east-1:123456:instance/i-abc"
            mock_identity.return_value = {}
            mock_violation.return_value = {}
            mock_snapshot.return_value = {}

            # Act
            result = convert_to_v2_format(
                scan_id="scan-001",
                policy_name="test-policy",
                resource_data={"InstanceId": "i-abc"},
                resource_type="aws.ec2",
                account_id="123456",
                region="us-east-1"
            )

            # Assert
            mock_dt.now.assert_called_once_with(timezone.utc)
            assert result["metadata"]["scan_timestamp"] == "2024-01-01T00:00:00+00:00"
            assert result["metadata"]["custodian_version"] == "0.9.42"

        @patch("app.jobs.utils.v2_format_converter._create_resource_snapshot")
        @patch("app.jobs.utils.v2_format_converter._build_violation_context_v2")
        @patch("app.jobs.utils.v2_format_converter._build_resource_identity")
        @patch("app.jobs.utils.v2_format_converter.build_resource_arn")
        @patch("app.jobs.utils.v2_format_converter.datetime")
        def test_convert_raw_resource_preserved(
            self, mock_dt, mock_build_arn, mock_identity, mock_violation, mock_snapshot
        ):
            """VC-006: raw_resourceに入力データがそのまま保持される"""
            # Arrange
            mock_dt.now.return_value.isoformat.return_value = "2024-01-01T00:00:00+00:00"
            mock_build_arn.return_value = "arn:aws:ec2:us-east-1:123456:instance/i-abc"
            mock_identity.return_value = {}
            mock_violation.return_value = {}
            mock_snapshot.return_value = {}
            original_data = {"InstanceId": "i-abc", "Tags": [{"Key": "Name", "Value": "test"}]}

            # Act
            result = convert_to_v2_format(
                scan_id="scan-001",
                policy_name="test-policy",
                resource_data=original_data,
                resource_type="aws.ec2",
                account_id="123456",
                region="us-east-1"
            )

            # Assert
            assert result["raw_resource"] is original_data
```

### 2.2 convert_custodian_output_to_v2_hierarchical テスト

```python
class TestConvertCustodianOutputToV2Hierarchical:
    """convert_custodian_output_to_v2_hierarchical のテスト"""

    class TestNormalConversion:
        """正常変換テスト"""

        @patch("app.jobs.utils.v2_format_converter._organize_resources_by_region")
        @patch("app.jobs.utils.v2_format_converter._extract_policy_metadata_fields")
        @patch("app.jobs.utils.v2_format_converter._build_execution_details")
        @patch("app.jobs.utils.v2_format_converter._determine_policy_status")
        @patch("app.jobs.utils.v2_format_converter._extract_resource_type_from_metadata")
        @patch("app.jobs.utils.v2_format_converter._collect_policies_data")
        @patch("app.jobs.utils.v2_format_converter.os.path.exists", return_value=True)
        @patch("app.jobs.utils.v2_format_converter.datetime")
        def test_hierarchical_single_policy(
            self, mock_dt, mock_exists, mock_collect,
            mock_res_type, mock_status, mock_exec, mock_meta, mock_organize
        ):
            """VC-007: 1ポリシー・1リソースの正常変換"""
            # Arrange
            mock_dt.now.return_value.isoformat.return_value = "2024-01-01T00:00:00+00:00"
            mock_collect.return_value = {
                "policy-a": {"resources": [{"id": "r1"}], "metadata": {}, "error_info": None, "policy_dir": "/tmp/policy-a"}
            }
            mock_res_type.return_value = "aws.ec2"
            mock_status.return_value = "success"
            mock_exec.return_value = {"resources_found": 1}
            mock_meta.return_value = {"severity": "High"}
            mock_organize.return_value = [{"region": "us-east-1", "resource_count": 1, "resources": [{}]}]

            # Act
            result = convert_custodian_output_to_v2_hierarchical(
                custodian_output_dir="/tmp/output",
                scan_id="scan-001",
                account_id="123456"
            )

            # Assert
            assert result["scan_id"] == "scan-001"
            assert result["account_id"] == "123456"
            assert result["cloud_provider"] == "aws"
            assert result["doc_type"] == "hierarchical_scan_result_v2"
            assert len(result["policies"]) == 1
            assert result["scan_summary"]["total_policies"] == 1

        @patch("app.jobs.utils.v2_format_converter._build_hierarchical_policy")
        @patch("app.jobs.utils.v2_format_converter._collect_policies_data")
        @patch("app.jobs.utils.v2_format_converter.os.path.exists", return_value=True)
        @patch("app.jobs.utils.v2_format_converter.datetime")
        def test_hierarchical_multiple_policies(
            self, mock_dt, mock_exists, mock_collect, mock_build_hp
        ):
            """VC-008: 複数ポリシーの変換"""
            # Arrange
            mock_dt.now.return_value.isoformat.return_value = "2024-01-01T00:00:00+00:00"
            mock_collect.return_value = {
                "policy-a": {"resources": [], "metadata": {}, "error_info": None, "policy_dir": "/tmp/a"},
                "policy-b": {"resources": [], "metadata": {}, "error_info": None, "policy_dir": "/tmp/b"},
                "policy-c": {"resources": [], "metadata": {}, "error_info": None, "policy_dir": "/tmp/c"},
            }
            mock_build_hp.side_effect = [
                {"policy_name": "policy-a", "policy_status": "success", "resources_by_region": [{"resource_count": 2}]},
                {"policy_name": "policy-b", "policy_status": "failed", "resources_by_region": [{"resource_count": 1}]},
                {"policy_name": "policy-c", "policy_status": "success", "resources_by_region": [{"resource_count": 3}]},
            ]

            # Act
            result = convert_custodian_output_to_v2_hierarchical(
                custodian_output_dir="/tmp/output",
                scan_id="scan-001",
                account_id="123456"
            )

            # Assert
            assert result["scan_summary"]["total_policies"] == 3
            summary = result["scan_summary"]["policy_summary"]
            assert summary["success"] == 2
            assert summary["failed"] == 1

        @patch("app.jobs.utils.v2_format_converter._build_hierarchical_policy")
        @patch("app.jobs.utils.v2_format_converter._collect_policies_data")
        @patch("app.jobs.utils.v2_format_converter.os.path.exists", return_value=True)
        @patch("app.jobs.utils.v2_format_converter.datetime")
        def test_hierarchical_with_statistics(
            self, mock_dt, mock_exists, mock_collect, mock_build_hp
        ):
            """VC-009: policy_statistics指定時にstatsが渡される"""
            # Arrange
            mock_dt.now.return_value.isoformat.return_value = "2024-01-01T00:00:00+00:00"
            mock_collect.return_value = {
                "policy-a": {"resources": [], "metadata": {}, "error_info": None, "policy_dir": "/tmp/a"}
            }
            mock_build_hp.return_value = {
                "policy_name": "policy-a", "policy_status": "success",
                "resources_by_region": []
            }
            stats = {"policy-a": {"resources_scanned": 10, "violation_count": 3}}

            # Act
            convert_custodian_output_to_v2_hierarchical(
                custodian_output_dir="/tmp/output",
                scan_id="scan-001",
                account_id="123456",
                policy_statistics=stats
            )

            # Assert — statsが渡されたことを確認
            call_args = mock_build_hp.call_args
            assert call_args[0][3] == {"resources_scanned": 10, "violation_count": 3}

        @patch("app.jobs.utils.v2_format_converter._build_hierarchical_policy")
        @patch("app.jobs.utils.v2_format_converter._collect_policies_data")
        @patch("app.jobs.utils.v2_format_converter.os.path.exists", return_value=True)
        @patch("app.jobs.utils.v2_format_converter.datetime")
        def test_hierarchical_without_statistics(
            self, mock_dt, mock_exists, mock_collect, mock_build_hp
        ):
            """VC-010: policy_statistics=None時"""
            # Arrange
            mock_dt.now.return_value.isoformat.return_value = "2024-01-01T00:00:00+00:00"
            mock_collect.return_value = {
                "policy-a": {"resources": [], "metadata": {}, "error_info": None, "policy_dir": "/tmp/a"}
            }
            mock_build_hp.return_value = {
                "policy_name": "policy-a", "policy_status": "success",
                "resources_by_region": []
            }

            # Act
            convert_custodian_output_to_v2_hierarchical(
                custodian_output_dir="/tmp/output",
                scan_id="scan-001",
                account_id="123456",
                policy_statistics=None
            )

            # Assert — stats=Noneが渡されたことを確認
            call_args = mock_build_hp.call_args
            assert call_args[0][3] is None

        @patch("app.jobs.utils.v2_format_converter._build_hierarchical_policy")
        @patch("app.jobs.utils.v2_format_converter._collect_policies_data")
        @patch("app.jobs.utils.v2_format_converter.os.path.exists", return_value=True)
        @patch("app.jobs.utils.v2_format_converter.datetime")
        def test_hierarchical_policy_summary_counts(
            self, mock_dt, mock_exists, mock_collect, mock_build_hp
        ):
            """VC-011: policy_summary の success/partial_success/failed 集計"""
            # Arrange
            mock_dt.now.return_value.isoformat.return_value = "2024-01-01T00:00:00+00:00"
            mock_collect.return_value = {
                "p1": {}, "p2": {}, "p3": {}, "p4": {}
            }
            mock_build_hp.side_effect = [
                {"policy_name": "p1", "policy_status": "success", "resources_by_region": []},
                {"policy_name": "p2", "policy_status": "failed", "resources_by_region": []},
                {"policy_name": "p3", "policy_status": "success", "resources_by_region": []},
                {"policy_name": "p4", "policy_status": "partial_success", "resources_by_region": []},
            ]

            # Act
            result = convert_custodian_output_to_v2_hierarchical(
                custodian_output_dir="/tmp/output",
                scan_id="scan-001",
                account_id="123456"
            )

            # Assert
            summary = result["scan_summary"]["policy_summary"]
            assert summary["success"] == 2
            assert summary["failed"] == 1
            assert summary["partial_success"] == 1

        @patch("app.jobs.utils.v2_format_converter._build_hierarchical_policy")
        @patch("app.jobs.utils.v2_format_converter._collect_policies_data")
        @patch("app.jobs.utils.v2_format_converter.os.path.exists", return_value=True)
        @patch("app.jobs.utils.v2_format_converter.datetime")
        def test_hierarchical_total_resources_count(
            self, mock_dt, mock_exists, mock_collect, mock_build_hp
        ):
            """VC-012: total_resources の正しい集計"""
            # Arrange
            mock_dt.now.return_value.isoformat.return_value = "2024-01-01T00:00:00+00:00"
            mock_collect.return_value = {"p1": {}, "p2": {}}
            mock_build_hp.side_effect = [
                {
                    "policy_name": "p1", "policy_status": "success",
                    "resources_by_region": [
                        {"resource_count": 5}, {"resource_count": 3}
                    ]
                },
                {
                    "policy_name": "p2", "policy_status": "success",
                    "resources_by_region": [{"resource_count": 2}]
                },
            ]

            # Act
            result = convert_custodian_output_to_v2_hierarchical(
                custodian_output_dir="/tmp/output",
                scan_id="scan-001",
                account_id="123456"
            )

            # Assert
            assert result["scan_summary"]["total_resources"] == 10

        @patch("app.jobs.utils.v2_format_converter._build_hierarchical_policy")
        @patch("app.jobs.utils.v2_format_converter._collect_policies_data")
        @patch("app.jobs.utils.v2_format_converter.os.path.exists", return_value=True)
        @patch("app.jobs.utils.v2_format_converter.datetime")
        def test_hierarchical_doc_type(
            self, mock_dt, mock_exists, mock_collect, mock_build_hp
        ):
            """VC-013: doc_typeが正しい値"""
            # Arrange
            mock_dt.now.return_value.isoformat.return_value = "2024-01-01T00:00:00+00:00"
            mock_collect.return_value = {"p1": {}}
            mock_build_hp.return_value = {
                "policy_name": "p1", "policy_status": "success",
                "resources_by_region": []
            }

            # Act
            result = convert_custodian_output_to_v2_hierarchical(
                custodian_output_dir="/tmp/output",
                scan_id="scan-001",
                account_id="123456"
            )

            # Assert
            assert result["doc_type"] == "hierarchical_scan_result_v2"
```

### 2.3 _collect_policies_data テスト

```python
class TestCollectPoliciesData:
    """_collect_policies_data のテスト"""

    @patch("app.jobs.utils.v2_format_converter._load_error_info_safely")
    @patch("app.jobs.utils.v2_format_converter._load_resources_safely")
    @patch("app.jobs.utils.v2_format_converter._load_metadata_safely")
    @patch("app.jobs.utils.v2_format_converter.glob.glob")
    def test_collect_multiple_policies(
        self, mock_glob, mock_meta, mock_resources, mock_error
    ):
        """VC-014: 複数ポリシーの正常収集"""
        # Arrange
        mock_glob.return_value = [
            "/tmp/output/policy-a/resources.json",
            "/tmp/output/policy-b/resources.json",
        ]
        mock_meta.return_value = {"policy": {"name": "test"}}
        mock_resources.side_effect = [[{"id": "r1"}], [{"id": "r2"}, {"id": "r3"}]]
        mock_error.return_value = None

        # Act
        result = _collect_policies_data("/tmp/output")

        # Assert
        assert len(result) == 2
        assert "policy-a" in result
        assert "policy-b" in result
        assert len(result["policy-a"]["resources"]) == 1
        assert len(result["policy-b"]["resources"]) == 2

    @patch("app.jobs.utils.v2_format_converter._load_error_info_safely")
    @patch("app.jobs.utils.v2_format_converter._load_resources_safely")
    @patch("app.jobs.utils.v2_format_converter._load_metadata_safely")
    @patch("app.jobs.utils.v2_format_converter.glob.glob")
    def test_collect_same_policy_merge(
        self, mock_glob, mock_meta, mock_resources, mock_error
    ):
        """VC-015: 同名ポリシーのリソースマージ"""
        # Arrange — 同じポリシー名が2つのリージョンに存在
        mock_glob.return_value = [
            "/tmp/output/us-east-1/my-policy/resources.json",
            "/tmp/output/us-west-2/my-policy/resources.json",
        ]
        mock_meta.return_value = {}
        mock_resources.side_effect = [[{"id": "r1"}], [{"id": "r2"}]]
        mock_error.return_value = None

        # Act
        result = _collect_policies_data("/tmp/output")

        # Assert — リソースがextendされる
        assert len(result) == 1
        assert "my-policy" in result
        assert len(result["my-policy"]["resources"]) == 2

    @patch("app.jobs.utils.v2_format_converter.glob.glob")
    def test_collect_no_resources_files(self, mock_glob):
        """VC-016: resources.jsonが存在しない場合"""
        # Arrange
        mock_glob.return_value = []

        # Act
        result = _collect_policies_data("/tmp/output")

        # Assert
        assert result == {}
```

### 2.4 _build_hierarchical_policy テスト

```python
class TestBuildHierarchicalPolicy:
    """_build_hierarchical_policy のテスト"""

    @patch("app.jobs.utils.v2_format_converter._extract_policy_metadata_fields")
    @patch("app.jobs.utils.v2_format_converter._organize_resources_by_region")
    @patch("app.jobs.utils.v2_format_converter._build_execution_details")
    @patch("app.jobs.utils.v2_format_converter._determine_policy_status")
    @patch("app.jobs.utils.v2_format_converter._extract_resource_type_from_metadata")
    def test_build_hierarchical_normal(
        self, mock_res_type, mock_status, mock_exec, mock_organize, mock_meta_fields
    ):
        """VC-017: 正常なポリシー階層構造構築"""
        # Arrange
        mock_res_type.return_value = "aws.ec2"
        mock_status.return_value = "success"
        mock_exec.return_value = {"resources_found": 5}
        mock_organize.return_value = [{"region": "us-east-1", "resource_count": 5, "resources": []}]
        mock_meta_fields.return_value = {"severity": "High", "policy_title": "テストポリシー"}
        policy_data = {
            "resources": [{"id": "r1"}],
            "metadata": {"policy": {"name": "test"}},
            "error_info": None
        }
        stats = {"resources_scanned": 10}

        # Act
        result = _build_hierarchical_policy("test-policy", policy_data, "123456", stats)

        # Assert
        assert result["policy_name"] == "test-policy"
        assert result["policy_status"] == "success"
        assert result["resource_type"] == "aws.ec2"
        assert result["severity"] == "High"
        assert result["policy_title"] == "テストポリシー"

    @patch("app.jobs.utils.v2_format_converter._extract_policy_metadata_fields")
    @patch("app.jobs.utils.v2_format_converter._organize_resources_by_region")
    @patch("app.jobs.utils.v2_format_converter._build_execution_details")
    @patch("app.jobs.utils.v2_format_converter._determine_policy_status")
    @patch("app.jobs.utils.v2_format_converter._extract_resource_type_from_metadata")
    def test_build_hierarchical_no_statistics(
        self, mock_res_type, mock_status, mock_exec, mock_organize, mock_meta_fields
    ):
        """VC-018: statistics=None時"""
        # Arrange
        mock_res_type.return_value = "aws.s3"
        mock_status.return_value = "success"
        mock_exec.return_value = {}
        mock_organize.return_value = []
        mock_meta_fields.return_value = {}
        policy_data = {"resources": [], "metadata": {}, "error_info": None}

        # Act
        _build_hierarchical_policy("test-policy", policy_data, "123456", None)

        # Assert — _build_execution_detailsにNoneが渡される
        mock_exec.assert_called_once_with([], None, None)

    @patch("app.jobs.utils.v2_format_converter._extract_policy_metadata_fields")
    @patch("app.jobs.utils.v2_format_converter._organize_resources_by_region")
    @patch("app.jobs.utils.v2_format_converter._build_execution_details")
    @patch("app.jobs.utils.v2_format_converter._determine_policy_status")
    @patch("app.jobs.utils.v2_format_converter._extract_resource_type_from_metadata")
    def test_build_hierarchical_metadata_merge(
        self, mock_res_type, mock_status, mock_exec, mock_organize, mock_meta_fields
    ):
        """VC-019: メタデータフィールドがポリシー構造にマージされる"""
        # Arrange
        mock_res_type.return_value = "aws.ec2"
        mock_status.return_value = "success"
        mock_exec.return_value = {}
        mock_organize.return_value = []
        mock_meta_fields.return_value = {
            "recommendation_uuid": "uuid-001",
            "severity": "Critical",
            "policy_version": 2
        }
        policy_data = {"resources": [], "metadata": {}, "error_info": None}

        # Act
        result = _build_hierarchical_policy("test-policy", policy_data, "123456", None)

        # Assert — updateによるマージを確認
        assert result["recommendation_uuid"] == "uuid-001"
        assert result["severity"] == "Critical"
        assert result["policy_version"] == 2
```

### 2.5 _extract_policy_metadata_fields テスト

```python
class TestExtractPolicyMetadataFields:
    """_extract_policy_metadata_fields のテスト"""

    def test_full_metadata(self):
        """VC-020: 全フィールド完備のメタデータ"""
        # Arrange
        # 注意: 実装(L378)は policy_metadata.get("uuid") でキー"uuid"を読む。
        # 上位仕様(cspm_scan_result_v2_README.md L48)とテストポリシー
        # (metadata_test_policy.yaml L6)はキー"recommendation_uuid"を使用。
        # → 制約事項 #6 参照
        metadata = {
            "policy": {
                "name": "test-policy",
                "description": "テスト説明",
                "filters": [{"type": "value"}],
                "actions": [{"type": "notify"}],
                "metadata": {
                    "uuid": "uuid-001",
                    "recommendation_id": "A.1",
                    "recommendation_version": 2,
                    "policy_version": 3,
                    "severity": "High",
                    "title": "テストタイトル"
                }
            }
        }

        # Act
        result = _extract_policy_metadata_fields(metadata)

        # Assert — 現在の実装動作（"uuid"キーから取得）
        assert result["recommendation_uuid"] == "uuid-001"
        assert result["recommendation_id"] == "A.1"
        assert result["recommendation_version"] == 2
        assert result["policy_version"] == 3
        assert result["severity"] == "High"
        assert result["policy_title"] == "テストタイトル"

    def test_recommendation_uuid_key_mismatch(self):
        """VC-020b: 上位仕様のキー名(recommendation_uuid)で渡すとNoneになる（仕様乖離記録）"""
        # Arrange — 上位仕様(cspm_scan_result_v2_README.md L48)準拠のキー名
        metadata = {
            "policy": {
                "name": "test-policy",
                "metadata": {
                    "recommendation_uuid": "uuid-spec-001",
                    "severity": "High"
                }
            }
        }

        # Act
        result = _extract_policy_metadata_fields(metadata)

        # Assert — 実装(L378)は .get("uuid") のため None が返る
        # 上位仕様準拠なら "uuid-spec-001" を期待するが、現実装では取得できない
        assert result["recommendation_uuid"] is None  # 実装の制限（制約事項 #6）
        assert result["policy_definition"] == {}  # 入力に description/filters/actions がないため空

    def test_severity_default(self):
        """VC-021: severityキーなし時のデフォルト"""
        # Arrange
        metadata = {"policy": {"name": "test", "metadata": {}}}

        # Act
        result = _extract_policy_metadata_fields(metadata)

        # Assert
        assert result["severity"] == "Medium"

    def test_title_fallback_to_policy_name(self):
        """VC-022: metadata.titleなし時にpolicy.nameフォールバック"""
        # Arrange
        metadata = {"policy": {"name": "fallback-name", "metadata": {}}}

        # Act
        result = _extract_policy_metadata_fields(metadata)

        # Assert
        assert result["policy_title"] == "fallback-name"

    def test_title_priority(self):
        """VC-023: metadata.titleがpolicy.nameより優先"""
        # Arrange
        metadata = {
            "policy": {
                "name": "policy-name",
                "metadata": {"title": "メタデータタイトル"}
            }
        }

        # Act
        result = _extract_policy_metadata_fields(metadata)

        # Assert
        assert result["policy_title"] == "メタデータタイトル"

    def test_empty_metadata(self):
        """VC-024: 空メタデータ"""
        # Arrange
        metadata = {}

        # Act
        result = _extract_policy_metadata_fields(metadata)

        # Assert
        assert result["recommendation_uuid"] is None
        assert result["severity"] == "Medium"
        assert result["policy_title"] == ""
        assert result["policy_definition"] == {}
```

### 2.6 _build_policy_definition テスト

```python
class TestBuildPolicyDefinition:
    """_build_policy_definition のテスト"""

    def test_full_definition(self):
        """VC-025: description, filters, actions 全て存在"""
        # Arrange
        policy = {
            "description": "テスト説明",
            "filters": [{"type": "value", "key": "State"}],
            "actions": [{"type": "notify"}]
        }

        # Act
        result = _build_policy_definition(policy)

        # Assert
        assert result["description"] == "テスト説明"
        assert len(result["filters"]) == 1
        assert len(result["actions"]) == 1

    def test_partial_definition(self):
        """VC-026: descriptionのみ"""
        # Arrange
        policy = {"description": "説明のみ"}

        # Act
        result = _build_policy_definition(policy)

        # Assert
        assert result["description"] == "説明のみ"
        assert "filters" not in result
        assert "actions" not in result

    def test_empty_policy(self):
        """VC-027: 全フィールドなし → 空Dict"""
        # Arrange
        policy = {}

        # Act
        result = _build_policy_definition(policy)

        # Assert
        assert result == {}

    def test_invalid_types_excluded(self):
        """VC-028: 不正な型は除外される"""
        # Arrange — description=int, filters=str はisinstanceチェックで除外
        policy = {
            "description": 123,
            "filters": "not-a-list",
            "actions": [{"type": "notify"}]
        }

        # Act
        result = _build_policy_definition(policy)

        # Assert
        assert "description" not in result
        assert "filters" not in result
        assert "actions" in result
```

### 2.7 _get_default_metadata_fields / _organize_resources_by_region テスト

```python
class TestGetDefaultMetadataFields:
    """_get_default_metadata_fields のテスト"""

    def test_default_values(self):
        """VC-029: デフォルト値の確認"""
        # Arrange / Act
        result = _get_default_metadata_fields()

        # Assert — 現在の実装デフォルト値
        # 注意: 上位仕様(cspm_scan_result_v2_README.md L30-33)では
        # recommendation_version=1, policy_version=1, policy_title=policy_name
        # だが、実装(L458-466)ではいずれも None → 制約事項 #7 参照
        assert result["recommendation_uuid"] is None
        assert result["recommendation_id"] is None
        assert result["recommendation_version"] is None  # 仕様: 1
        assert result["policy_version"] is None           # 仕様: 1
        assert result["severity"] == "Medium"             # 仕様と一致
        assert result["policy_title"] is None             # 仕様: policy_name
        assert result["policy_definition"] == {}          # 仕様と一致


class TestOrganizeResourcesByRegion:
    """_organize_resources_by_region のテスト"""

    @patch("app.jobs.utils.v2_format_converter._structure_resource_data")
    @patch("app.jobs.utils.v2_format_converter._extract_region_from_resource")
    def test_organize_two_regions(self, mock_region, mock_structure):
        """VC-030: 2リージョン・各2リソースの正常整理"""
        # Arrange
        resources = [{"id": "r1"}, {"id": "r2"}, {"id": "r3"}, {"id": "r4"}]
        mock_region.side_effect = ["us-east-1", "us-west-2", "us-east-1", "us-west-2"]
        mock_structure.side_effect = [
            {"structured": "r1"}, {"structured": "r2"},
            {"structured": "r3"}, {"structured": "r4"}
        ]

        # Act
        result = _organize_resources_by_region(resources, "123456", {})

        # Assert
        assert len(result) == 2
        assert result[0]["region"] == "us-east-1"
        assert result[0]["resource_count"] == 2
        assert result[1]["region"] == "us-west-2"
        assert result[1]["resource_count"] == 2

    @patch("app.jobs.utils.v2_format_converter._structure_resource_data")
    @patch("app.jobs.utils.v2_format_converter._extract_region_from_resource")
    def test_organize_unknown_region_fallback(self, mock_region, mock_structure):
        """VC-031: unknown-region時にmetadata.config.regionへフォールバック"""
        # Arrange
        resources = [{"id": "r1"}]
        mock_region.return_value = "unknown-region"
        mock_structure.return_value = {"structured": "r1"}
        metadata = {"config": {"region": "ap-northeast-1"}}

        # Act
        result = _organize_resources_by_region(resources, "123456", metadata)

        # Assert
        assert result[0]["region"] == "ap-northeast-1"

    @patch("app.jobs.utils.v2_format_converter._structure_resource_data")
    @patch("app.jobs.utils.v2_format_converter._extract_region_from_resource")
    def test_organize_both_unknown_region(self, mock_region, mock_structure):
        """VC-032: リソース・metadata両方unknown-region"""
        # Arrange
        resources = [{"id": "r1"}]
        mock_region.return_value = "unknown-region"
        mock_structure.return_value = {"structured": "r1"}
        metadata = {}  # config.regionなし → デフォルト "unknown-region"

        # Act
        result = _organize_resources_by_region(resources, "123456", metadata)

        # Assert
        assert result[0]["region"] == "unknown-region"

    @patch("app.jobs.utils.v2_format_converter._structure_resource_data")
    @patch("app.jobs.utils.v2_format_converter._extract_region_from_resource")
    def test_organize_sorted_by_region_name(self, mock_region, mock_structure):
        """VC-033: リージョン名でアルファベット順ソート"""
        # Arrange
        resources = [{"id": "r1"}, {"id": "r2"}, {"id": "r3"}]
        mock_region.side_effect = ["us-west-2", "ap-northeast-1", "eu-west-1"]
        mock_structure.side_effect = [{"s": "r1"}, {"s": "r2"}, {"s": "r3"}]

        # Act
        result = _organize_resources_by_region(resources, "123456", {})

        # Assert
        regions = [r["region"] for r in result]
        assert regions == ["ap-northeast-1", "eu-west-1", "us-west-2"]
```

---

## 3. 異常系テストケース

| ID | テスト名 | 検証内容 | 期待結果 |
|----|---------|---------|---------|
| VC-E01 | convert_to_v2_format 必須パラメータ不足 | scan_id/policy_name/resource_data/resource_type がfalsy | build_error_responseの返却値 |
| VC-E02 | convert_to_v2_format 内部例外 | ヘルパー関数が例外送出 | エラーレスポンス（例外抑制） |
| VC-E03 | convert_custodian_output 必須パラメータ不足 | scan_id/account_id が空 | _build_error_documentの返却値 |
| VC-E04 | convert_custodian_output ディレクトリ不存在 | os.path.exists=False | _build_error_documentの返却値 |
| VC-E05 | convert_custodian_output ポリシーデータ空 | _collect_policies_data=空Dict | _build_empty_documentの返却値 |
| VC-E06 | convert_custodian_output 内部例外 | _collect_policies_dataが例外送出 | _build_error_documentの返却値 |
| VC-E07 | _collect_policies_data 例外 | glob.globが例外送出 | 空Dict |
| VC-E08 | _build_hierarchical_policy 例外 | 内部関数が例外送出 | _build_error_policyの返却値 |
| VC-E09 | _extract_policy_metadata_fields 例外 | metadata構造が不正 | _get_default_metadata_fieldsの返却値 |
| VC-E10 | _organize_resources_by_region 例外 | _extract_region_from_resourceが例外 | 空リスト |

```python
class TestConverterErrors:
    """異常系テスト"""

    class TestConvertToV2FormatErrors:
        """convert_to_v2_format の異常系"""

        @patch("app.jobs.utils.v2_format_converter.build_error_response")
        def test_missing_required_params(self, mock_error_resp):
            """VC-E01: 必須パラメータ不足"""
            # Arrange
            mock_error_resp.return_value = {"error": "missing params"}

            # Act — scan_idが空文字
            result = convert_to_v2_format(
                scan_id="",
                policy_name="test",
                resource_data={"id": "1"},
                resource_type="aws.ec2"
            )

            # Assert
            mock_error_resp.assert_called_once()
            assert result == {"error": "missing params"}

        @patch("app.jobs.utils.v2_format_converter.build_error_response")
        @patch("app.jobs.utils.v2_format_converter.build_resource_arn")
        @patch("app.jobs.utils.v2_format_converter.datetime")
        def test_internal_exception(self, mock_dt, mock_build_arn, mock_error_resp):
            """VC-E02: ヘルパー関数例外時のエラーレスポンス"""
            # Arrange
            mock_dt.now.return_value.isoformat.return_value = "2024-01-01T00:00:00+00:00"
            mock_build_arn.side_effect = RuntimeError("ARN構築失敗")
            mock_error_resp.return_value = {"error": "internal"}

            # Act
            result = convert_to_v2_format(
                scan_id="scan-001",
                policy_name="test",
                resource_data={"id": "1"},
                resource_type="aws.ec2",
                account_id="123456",
                region="us-east-1"
            )

            # Assert — 例外が抑制されエラーレスポンスが返る
            mock_error_resp.assert_called_once()
            assert result == {"error": "internal"}

    class TestConvertHierarchicalErrors:
        """convert_custodian_output_to_v2_hierarchical の異常系"""

        @patch("app.jobs.utils.v2_format_converter._build_error_document")
        def test_missing_required_params(self, mock_error_doc):
            """VC-E03: 必須パラメータ不足"""
            # Arrange
            mock_error_doc.return_value = {"error": "missing"}

            # Act — account_id が空文字
            result = convert_custodian_output_to_v2_hierarchical(
                custodian_output_dir="/tmp/output",
                scan_id="scan-001",
                account_id=""
            )

            # Assert
            mock_error_doc.assert_called_once()
            assert result == {"error": "missing"}

        @patch("app.jobs.utils.v2_format_converter._build_error_document")
        @patch("app.jobs.utils.v2_format_converter.os.path.exists", return_value=False)
        def test_directory_not_exists(self, mock_exists, mock_error_doc):
            """VC-E04: ディレクトリ不存在"""
            # Arrange
            mock_error_doc.return_value = {"error": "dir not found"}

            # Act
            result = convert_custodian_output_to_v2_hierarchical(
                custodian_output_dir="/nonexistent",
                scan_id="scan-001",
                account_id="123456"
            )

            # Assert
            mock_error_doc.assert_called_once()
            # エラーメッセージにパスが含まれる
            call_args = mock_error_doc.call_args
            assert "/nonexistent" in call_args[0][3]

        @patch("app.jobs.utils.v2_format_converter._build_empty_document")
        @patch("app.jobs.utils.v2_format_converter._collect_policies_data", return_value={})
        @patch("app.jobs.utils.v2_format_converter.os.path.exists", return_value=True)
        def test_empty_policies_data(self, mock_exists, mock_collect, mock_empty_doc):
            """VC-E05: ポリシーデータ空 → 空ドキュメント"""
            # Arrange
            mock_empty_doc.return_value = {"empty": True}

            # Act
            result = convert_custodian_output_to_v2_hierarchical(
                custodian_output_dir="/tmp/output",
                scan_id="scan-001",
                account_id="123456"
            )

            # Assert
            mock_empty_doc.assert_called_once_with("scan-001", "123456", "aws")
            assert result == {"empty": True}

        @patch("app.jobs.utils.v2_format_converter._build_error_document")
        @patch("app.jobs.utils.v2_format_converter._collect_policies_data")
        @patch("app.jobs.utils.v2_format_converter.os.path.exists", return_value=True)
        def test_internal_exception(self, mock_exists, mock_collect, mock_error_doc):
            """VC-E06: 内部例外 → エラードキュメント"""
            # Arrange
            mock_collect.side_effect = RuntimeError("収集失敗")
            mock_error_doc.return_value = {"error": "internal"}

            # Act
            result = convert_custodian_output_to_v2_hierarchical(
                custodian_output_dir="/tmp/output",
                scan_id="scan-001",
                account_id="123456"
            )

            # Assert
            mock_error_doc.assert_called_once()
            assert result == {"error": "internal"}

    class TestCollectPoliciesDataErrors:
        """_collect_policies_data の異常系"""

        @patch("app.jobs.utils.v2_format_converter.glob.glob")
        def test_glob_exception(self, mock_glob):
            """VC-E07: glob.globが例外送出 → 空Dict"""
            # Arrange
            mock_glob.side_effect = PermissionError("アクセス拒否")

            # Act
            result = _collect_policies_data("/tmp/output")

            # Assert
            assert result == {}

    class TestBuildHierarchicalPolicyErrors:
        """_build_hierarchical_policy の異常系"""

        @patch("app.jobs.utils.v2_format_converter._build_error_policy")
        @patch("app.jobs.utils.v2_format_converter._extract_resource_type_from_metadata")
        def test_internal_exception(self, mock_res_type, mock_error_policy):
            """VC-E08: 内部関数例外 → エラーポリシー"""
            # Arrange
            mock_res_type.side_effect = KeyError("metadata error")
            mock_error_policy.return_value = {"policy_name": "test", "error": True}

            # Act
            result = _build_hierarchical_policy(
                "test-policy", {"resources": [], "metadata": {}, "error_info": None}, "123456"
            )

            # Assert
            mock_error_policy.assert_called_once_with("test-policy", "'metadata error'")

    class TestExtractMetadataFieldsErrors:
        """_extract_policy_metadata_fields の異常系"""

        @patch("app.jobs.utils.v2_format_converter._get_default_metadata_fields")
        def test_exception_returns_defaults(self, mock_defaults):
            """VC-E09: 例外時にデフォルト値返却"""
            # Arrange — Dictでない値を設定してAttributeErrorを発生させる
            mock_defaults.return_value = {"severity": "Medium"}
            bad_metadata = {"policy": "not-a-dict"}

            # Act
            result = _extract_policy_metadata_fields(bad_metadata)

            # Assert — str.get() → AttributeError → except → defaults
            mock_defaults.assert_called_once()
            assert result == {"severity": "Medium"}  # モックの返却値と一致

    class TestOrganizeResourcesErrors:
        """_organize_resources_by_region の異常系"""

        @patch("app.jobs.utils.v2_format_converter._extract_region_from_resource")
        def test_exception_returns_empty_list(self, mock_region):
            """VC-E10: 例外時に空リスト返却"""
            # Arrange
            mock_region.side_effect = TypeError("型エラー")

            # Act
            result = _organize_resources_by_region([{"id": "r1"}], "123456", {})

            # Assert
            assert result == []
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 検証内容 | 期待結果 |
|----|---------|---------|---------|
| VC-SEC-01 | convert_to_v2_format 例外メッセージ非フィルタリング記録 | 機密情報を含む例外発生時 | str(e)がフィルタリングなしでbuild_error_responseに渡される（現状動作記録） |
| VC-SEC-02 | convert_custodian_output パストラバーサル入力の現状動作記録 | パストラバーサル文字列入力 | os.path.exists分岐で処理（パス正規化なし、現状動作記録） |
| VC-SEC-03 | _collect_policies_data ポリシー名インジェクション耐性 | ディレクトリ名に特殊文字 | os.path.basename による安全な抽出 |

```python
@pytest.mark.security
class TestConverterSecurity:
    """セキュリティテスト"""

    @patch("app.jobs.utils.v2_format_converter.build_error_response")
    @patch("app.jobs.utils.v2_format_converter.build_resource_arn")
    @patch("app.jobs.utils.v2_format_converter.datetime")
    def test_error_message_passes_exception_unfiltered(self, mock_dt, mock_build_arn, mock_error_resp):
        """VC-SEC-01: 例外メッセージがフィルタリングなしで渡される現状動作の記録"""
        # Arrange
        mock_dt.now.return_value.isoformat.return_value = "2024-01-01T00:00:00+00:00"
        # 機密情報を含む例外を発生させる
        mock_build_arn.side_effect = RuntimeError("Connection to 10.0.0.1:9200 failed with key=SECRET123")
        mock_error_resp.return_value = {"error": "handled"}

        # Act
        convert_to_v2_format(
            scan_id="scan-001",
            policy_name="test",
            resource_data={"id": "1"},
            resource_type="aws.ec2",
            account_id="123456",
            region="us-east-1"
        )

        # Assert — str(e)がそのまま渡される（フィルタリングなし）
        # L128: build_error_response(scan_id, policy_name, str(e))
        call_args = mock_error_resp.call_args[0]
        assert call_args[0] == "scan-001"
        assert call_args[1] == "test"
        # 注意: 現実装ではstr(e)がそのまま渡される。
        # 本番運用では機密情報フィルタリングの追加検討が必要
        assert "SECRET123" in call_args[2]

    @patch("app.jobs.utils.v2_format_converter._build_error_document")
    @patch("app.jobs.utils.v2_format_converter.os.path.exists")
    def test_directory_traversal_resistance(self, mock_exists, mock_error_doc):
        """VC-SEC-02: パストラバーサル入力のハンドリング"""
        # Arrange
        mock_exists.return_value = False  # トラバーサルパスは存在しないと想定
        mock_error_doc.return_value = {"error": "not found"}

        # Act
        result = convert_custodian_output_to_v2_hierarchical(
            custodian_output_dir="../../../etc/passwd",
            scan_id="scan-001",
            account_id="123456"
        )

        # Assert — os.path.existsチェックで拒否される
        # 注意: 現状は os.path.exists=False による分岐確認のみ（現状動作記録）。
        # パス正規化(os.path.realpath等)による積極的な拒否は未実装のため、
        # 脆弱性検出テストとするには exists=True 時の挙動検証が別途必要
        mock_exists.assert_called_once_with("../../../etc/passwd")
        mock_error_doc.assert_called_once()

    @patch("app.jobs.utils.v2_format_converter._load_error_info_safely")
    @patch("app.jobs.utils.v2_format_converter._load_resources_safely")
    @patch("app.jobs.utils.v2_format_converter._load_metadata_safely")
    @patch("app.jobs.utils.v2_format_converter.glob.glob")
    def test_policy_name_from_basename(
        self, mock_glob, mock_meta, mock_resources, mock_error
    ):
        """VC-SEC-03: ポリシー名はos.path.basenameで安全に抽出される"""
        # Arrange — ディレクトリ名に特殊文字
        mock_glob.return_value = [
            "/tmp/output/../../../etc/passwd/resources.json",
        ]
        mock_meta.return_value = {}
        mock_resources.return_value = [{"id": "r1"}]
        mock_error.return_value = None

        # Act
        result = _collect_policies_data("/tmp/output")

        # Assert — os.path.basename("...passwd") → "passwd"（安全に抽出）
        assert "passwd" in result
        # ディレクトリトラバーサルパスがポリシー名に含まれない
        for key in result:
            assert "../" not in key
```

---

## 5. フィクスチャ

| フィクスチャ名 | スコープ | 用途 |
|-------------|---------|------|
| `reset_converter_module` | function (autouse) | モジュール状態リセット（現在no-op、可変状態なし） |
| `sample_resource_data` | function | EC2リソースデータのサンプル |
| `sample_metadata` | function | metadata.jsonのサンプル |
| `sample_policy_data` | function | ポリシーデータのサンプル |

```python
# conftest.py への追記
import pytest


@pytest.fixture(autouse=True)
def reset_converter_module():
    """テスト間のモジュール状態リセット（現在は no-op）

    v2_format_converter はモジュールレベルの可変状態を持たない
    （logger のみ、かつ idempotent）ため sys.modules 削除は不要。
    テストファイル冒頭で関数を直接 import しているため、
    sys.modules からモジュールを削除すると @patch が再 import した
    新モジュールをパッチする一方、テストが呼ぶ関数は旧モジュールの
    __globals__ を参照し、パッチが効かなくなるリスクがある。
    """
    yield


@pytest.fixture
def sample_resource_data():
    """EC2リソースデータのサンプル"""
    return {
        "InstanceId": "i-0abc123def456789",
        "InstanceType": "t3.medium",
        "State": {"Name": "running"},
        "Tags": [{"Key": "Name", "Value": "test-instance"}],
        "c7n:MatchedFilters": ["filter-1"]
    }


@pytest.fixture
def sample_metadata():
    """metadata.jsonのサンプル"""
    return {
        "policy": {
            "name": "test-policy",
            "resource": "aws.ec2",
            "description": "テストポリシー",
            "filters": [{"type": "value", "key": "State", "value": "running"}],
            "actions": [{"type": "notify"}],
            "metadata": {
                "uuid": "uuid-test-001",  # 実装はこのキー名で読む（制約事項 #6）
                "recommendation_id": "A.1",
                "recommendation_version": 1,
                "policy_version": 1,
                "severity": "High",
                "title": "EC2テストポリシー"
            }
        },
        "config": {"region": "us-east-1"}
    }


@pytest.fixture
def sample_policy_data(sample_resource_data, sample_metadata):
    """ポリシーデータのサンプル"""
    return {
        "resources": [sample_resource_data],
        "metadata": sample_metadata,
        "error_info": None,
        "policy_dir": "/tmp/output/test-policy"
    }
```

---

## 6. テスト実行例

```bash
# 全テスト実行
pytest test/unit/jobs/utils/test_v2_format_converter.py -v

# 正常系のみ
pytest test/unit/jobs/utils/test_v2_format_converter.py -v -k "not Error and not Security"

# 異常系のみ
pytest test/unit/jobs/utils/test_v2_format_converter.py -v -k "Error"

# セキュリティテストのみ
pytest test/unit/jobs/utils/test_v2_format_converter.py -v -m security

# カバレッジ計測
pytest test/unit/jobs/utils/test_v2_format_converter.py --cov=app.jobs.utils.v2_format_converter --cov-report=term-missing
```

---

## 7. テストケースサマリー

### 7.1 件数サマリー

| カテゴリ | 件数 |
|---------|------|
| 正常系 | 34 |
| 異常系 | 10 |
| セキュリティ | 3 |
| **合計** | **47** |

### 7.2 クラス構成

| テストクラス | テストメソッド数 | 対応テストID |
|------------|---------------|-------------|
| `TestConvertToV2Format` | 6 | VC-001〜VC-006 |
| `TestConvertCustodianOutputToV2Hierarchical` | 7 | VC-007〜VC-013 |
| `TestCollectPoliciesData` | 3 | VC-014〜VC-016 |
| `TestBuildHierarchicalPolicy` | 3 | VC-017〜VC-019 |
| `TestExtractPolicyMetadataFields` | 6 | VC-020, VC-020b, VC-021〜VC-024 |
| `TestBuildPolicyDefinition` | 4 | VC-025〜VC-028 |
| `TestGetDefaultMetadataFields` | 1 | VC-029 |
| `TestOrganizeResourcesByRegion` | 4 | VC-030〜VC-033 |
| `TestConverterErrors` | 10 | VC-E01〜VC-E10 |
| `TestConverterSecurity` | 3 | VC-SEC-01〜VC-SEC-03 |

### 7.3 予想失敗テスト

現時点で失敗が予想されるテストはありません。

> **仕様乖離記録テスト**: VC-020b は上位仕様と実装のキー名乖離（`recommendation_uuid` vs `uuid`）を記録するテストであり、現状動作（`result["recommendation_uuid"] is None`）を検証するため**テスト自体は成功**する。仕様準拠に修正する場合は L378 を `.get("recommendation_uuid")` に変更する必要がある（制約事項 #6）。

> **VC-E09 補足**: `{"policy": "not-a-dict"}` → L372 `metadata.get("policy", {})` で `"not-a-dict"` (str) を取得 → L373 `policy.get("metadata", {})` で `str.get()` → `AttributeError` → except で `_get_default_metadata_fields()` が返る。テストは成功する。
> **VC-SEC-01 補足**: 現実装では `str(e)` がフィルタリングなしで渡される。テストは現状動作を記録するものであり、将来的な改善候補。

### 7.4 注意事項

- **モック方針**: 全ヘルパー関数（#17c で検証済み）はモジュールレベルimportのため `app.jobs.utils.v2_format_converter.関数名` でパッチ
- **datetime.now モック**: `datetime` モジュール全体をパッチし、`mock_dt.now.return_value.isoformat.return_value` で ISO8601 文字列を返す。実装は `datetime.now(timezone.utc)` と引数付きで呼ぶが、`MagicMock.return_value` は引数に依存しないため動作する。VC-005 では `mock_dt.now.assert_called_once_with(timezone.utc)` で引数も検証する
- **_collect_policies_data**: `os.path.dirname` と `os.path.basename` でポリシー名を決定するため、ファイルパス構造がテストの前提条件
- **policy_summary 集計**: L194 の `if policy_status in policy_summary` により、未知のステータス（"success"/"partial_success"/"failed"以外）はカウントされない

---

## 8. 既知の制約事項

| # | 制約事項 | 回避策 |
|---|---------|--------|
| 1 | `custodian_version` がハードコード（L112: `"0.9.42"`） | テストではハードコード値を検証。動的取得のTODOが実装内にあり |
| 2 | `convert_to_v2_format` は例外を発生させず常にDictを返す | テストではエラーレスポンスの型・構造を検証 |
| 3 | `_collect_policies_data` の同名ポリシーマージ時、metadataは最初のもののみ保持 | L263-266 の分岐で resources のみ extend される設計を検証 |
| 4 | `str(e)` がフィルタリングなしで `build_error_response` に渡される（L128） | セキュリティテスト VC-SEC-01 で現状動作を記録。将来的な改善候補 |
| 5 | `os.path.exists` チェックのみでディレクトリトラバーサル対策（L166） | パス正規化は実装されていない。本番ではcustodian_output_dirは内部パラメータのため低リスク |
| 6 | `_extract_policy_metadata_fields`(L378) は `policy_metadata.get("uuid")` で `recommendation_uuid` を取得するが、上位仕様（`cspm_scan_result_v2_README.md` L48）とテストポリシー（`metadata_test_policy.yaml` L6）のキー名は `recommendation_uuid` | 上位仕様準拠にするには L378 を `.get("recommendation_uuid")` に変更する必要がある。VC-020b で乖離を検証済み |
| 7 | `_get_default_metadata_fields`(L458-466) のデフォルト値が上位仕様と乖離: `recommendation_version=None`(仕様:1), `policy_version=None`(仕様:1), `policy_title=None`(仕様:policy_name) | 仕様準拠にするには実装側のデフォルト値を変更する必要がある。VC-029 で現状動作を検証済み |
| 8 | テストファイル冒頭で `from ... import` した関数と `sys.modules` 削除による `@patch` 対象の乖離リスク | `reset_converter_module` を no-op に変更済み。v2_format_converter にモジュールレベル可変状態がないため `sys.modules` 削除は不要 |
