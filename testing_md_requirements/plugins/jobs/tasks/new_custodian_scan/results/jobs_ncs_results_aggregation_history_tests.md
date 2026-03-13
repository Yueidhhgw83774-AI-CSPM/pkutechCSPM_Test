# jobs/tasks/new_custodian_scan/results 結果集約+履歴系 テストケース

## 1. 概要

`results/` サブディレクトリの結果集約+履歴管理2ファイル（`history_manager.py`, `result_aggregator.py`）をまとめたテスト仕様書。アカウントID抽出・マルチリージョン結果集約・スキャンサマリー生成を担う。

### 1.1 対象クラス

| クラス | ファイル | 行数 | 責務 |
|--------|---------|------|------|
| `HistoryManager` | `history_manager.py` | 139 | アカウントID抽出（メタデータ/リージョン結果/AIサマリーから） |
| `ResultAggregator` | `result_aggregator.py` | 370 | マルチリージョン結果集約・グローバルリソース判定・スキャンサマリー生成 |

### 1.2 カバレッジ目標: 85%

> **注記**: HistoryManagerは外部依存（metadata_extractor, account_id_extractor, os, glob）が多く、遅延importパターンを使用。sys.modulesモック注入で対応。ResultAggregatorはデータ処理中心で高カバレッジが見込める。pytest-asyncio不要。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象1 | `app/jobs/tasks/new_custodian_scan/results/history_manager.py` |
| テスト対象2 | `app/jobs/tasks/new_custodian_scan/results/result_aggregator.py` |
| テストコード | `test/unit/jobs/tasks/new_custodian_scan/results/test_results_aggregation_history.py` |

### 1.4 補足情報

#### 依存関係

```
history_manager.py (HistoryManager)
  ──→ TaskLogger（ログ）
  ──→ app.jobs.utils.metadata_extractor（遅延import、メタデータ抽出）
  ──→ app.jobs.utils.account_id_extractor（遅延import、アカウントID抽出）
  ──→ os, glob（遅延import、ファイル探索）

result_aggregator.py (ResultAggregator)
  ──→ TaskLogger（ログ）
  ──→ datetime（UTC時刻取得）
```

#### テスト戦略

| テストカテゴリ | 手法 |
|--------------|------|
| `HistoryManager` | 遅延importの外部依存はsys.modulesモック注入 + patch.objectで内部メソッドモック |
| `ResultAggregator` | 実インスタンスでメソッド単位テスト（TaskLoggerのみMock） |

#### 主要分岐マップ

| クラス | メソッド | 行番号 | 条件 | 分岐数 |
|--------|---------|--------|------|--------|
| HM | `extract_account_id_from_metadata` | L54, L61, L69, L75 | metadata_files有無, config有無, account_id=="unknown"&&config, except | 5 |
| HM | `extract_account_id_from_region_results` | L92, L97, L101, L104 | error無し&&output_dir, account_id!="unknown", ループ終了, except | 4 |
| HM | `extract_accurate_account_id` | L127, L132, L137 | account_id有効, fallback成功, except | 3 |
| RA | `is_global_resource` | L47-50 | プレフィックス除去→any()マッチ | 2 |
| RA | `_process_individual_region_results` | L113, L127, L137, L152, L159, L161, L166 | error有無, scan_statistics有無, resource_type!="unknown", region重複, stdout有無, stderr有無, total_scanned>0 | 8 |
| RA | `_update_scan_metadata` | L210 | failed_regions非空 | 2 |
| RA | `create_scan_summary` | L337, L355 | failed_regions==0, scan_status判定 | 3 |

---

## 2. 正常系テストケース

### HistoryManager (HM)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| HM-001 | 初期化 | job_id | job_id保持・logger生成 |
| HM-002 | extract_account_id_from_metadata 正常取得 | scan_info有効 | account_id返却 |
| HM-003 | extract_account_id_from_metadata configフォールバック | scan_info="unknown", config有り | config.account_id |
| HM-004 | extract_account_id_from_metadata 両方unknown | scan_info/config両方unknown | "unknown" |
| HM-005 | extract_account_id_from_region_results 最初の成功 | 1つ目成功 | account_id |
| HM-006 | extract_account_id_from_region_results エラースキップ | error有り→2つ目成功 | account_id |
| HM-007 | extract_account_id_from_region_results 全失敗→unknown | 全てerror/unknown | "unknown" |
| HM-008 | extract_account_id_from_region_results 空リスト | [] | "unknown" |
| HM-009 | extract_accurate_account_id AIサマリー有効 | target_account_id有り | account_id |
| HM-010 | extract_accurate_account_id フォールバック成功 | target_account_id無し | extractor結果 |

### ResultAggregator (RA)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| RA-001 | 初期化 | job_id | GLOBAL_RESOURCE_TYPES定義済み |
| RA-002 | is_global_resource aws.iam→True | "aws.iam" | True |
| RA-003 | is_global_resource aws.ec2→False | "aws.ec2" | False |
| RA-004 | is_global_resource gcpプレフィックス除去 | "gcp.s3" | True |
| RA-004A | is_global_resource 部分一致によるマッチ | "aws.iam-analyzer" | True（"iam"部分一致） |
| RA-005 | aggregate_multi_region_results 統合フロー | 正常データ | 全キー含む結果 |
| RA-006 | _process_individual_region_results 成功のみ | 全成功 | violations集計 |
| RA-007 | _process_individual_region_results エラーのみ | 全エラー | failed_regions |
| RA-008 | _process_individual_region_results 成功+エラー混在 | 混在 | 両方集計 |
| RA-009 | _process_individual_region_results scan_statistics有り | stats付き | 詳細統計 |
| RA-010 | _process_individual_region_results scan_statistics無し | stats無し | 基本集計のみ |
| RA-011 | _process_individual_region_results 重複リージョンdedup | 同一リージョン2回 | 1回だけ記録 |
| RA-012 | _process_individual_region_results stdout/stderr収集 | 出力有り | extend集約 |
| RA-013 | _process_individual_region_results total_scanned==0 | 0 | compliance_rate=0.0 |
| RA-014 | _process_individual_region_results resource_type unknown除外 | unknown | setに追加されない |
| RA-015 | _update_scan_metadata failed有り | 失敗リージョン有り | failed_region_details追加 |
| RA-016 | _update_scan_metadata failed無し | 失敗なし | failed_region_details無し |
| RA-017 | _build_aggregated_result 構造確認 | 正常データ | 全キー含む辞書 |
| RA-018 | process_single_region_result 正常 | region,return_code等 | 結果辞書 |
| RA-019 | create_error_result 正常 | region,error_message | エラー辞書 |
| RA-020 | create_scan_summary 全成功 | failed_regions=0 | "完了"メッセージ |
| RA-021 | create_scan_summary 部分失敗 | failed_regions>0 | "部分完了"メッセージ |

### 2.1 HistoryManager テスト

```python
# test/unit/jobs/tasks/new_custodian_scan/results/test_results_aggregation_history.py
import sys
import pytest
from unittest.mock import patch, MagicMock

HM_MODULE = "app.jobs.tasks.new_custodian_scan.results.history_manager"
RA_MODULE = "app.jobs.tasks.new_custodian_scan.results.result_aggregator"


class TestHistoryManagerInit:
    """HistoryManager初期化テスト"""

    def test_init(self, history_manager):
        """HM-001: 初期化

        history_manager.py:L20-28 をカバー。
        """
        # Assert
        assert history_manager.job_id == "test-job-id"
        assert history_manager.logger is not None


class TestExtractAccountIdFromMetadata:
    """メタデータからのアカウントID抽出テスト"""

    def test_normal_extraction(self, history_manager, mock_metadata_extractor):
        """HM-002: extract_account_id_from_metadata 正常取得

        history_manager.py:L57-72 のscan_info経由取得をカバー。
        """
        # Arrange
        mock_metadata_extractor.extract_metadata_from_output_dir.return_value = {
            "config": {"account_id": "123456"}
        }
        mock_metadata_extractor.extract_scan_info_from_metadata.return_value = {
            "account_id": "123456"
        }

        # Act
        result = history_manager.extract_account_id_from_metadata("/output/dir")

        # Assert
        assert result == "123456"

    def test_config_fallback(self, history_manager, mock_metadata_extractor):
        """HM-003: extract_account_id_from_metadata configフォールバック

        history_manager.py:L69-70 のaccount_id=="unknown"&&config分岐をカバー。
        scan_infoが"unknown"の場合、config.account_idにフォールバック。
        """
        # Arrange
        mock_metadata_extractor.extract_metadata_from_output_dir.return_value = {
            "config": {"account_id": "789012"}
        }
        mock_metadata_extractor.extract_scan_info_from_metadata.return_value = {
            "account_id": "unknown"
        }

        # Act
        result = history_manager.extract_account_id_from_metadata("/output/dir")

        # Assert
        assert result == "789012"

    def test_both_unknown(self, history_manager, mock_metadata_extractor):
        """HM-004: extract_account_id_from_metadata 両方unknown

        history_manager.py:L69 の条件分岐不成立（config無し）→L66-67で取得した"unknown"がそのまま返却される経路をカバー。
        """
        # Arrange
        mock_metadata_extractor.extract_metadata_from_output_dir.return_value = {}
        mock_metadata_extractor.extract_scan_info_from_metadata.return_value = {
            "account_id": "unknown"
        }

        # Act
        result = history_manager.extract_account_id_from_metadata("/output/dir")

        # Assert
        assert result == "unknown"


class TestExtractAccountIdFromRegionResults:
    """リージョン結果からのアカウントID抽出テスト"""

    def test_first_successful_region(self, history_manager):
        """HM-005: extract_account_id_from_region_results 最初の成功

        history_manager.py:L91-99 の成功リージョンからaccount_id取得をカバー。
        """
        # Arrange
        region_results = [
            {"region": "us-east-1", "output_dir": "/output/us-east-1"}
        ]
        with patch.object(
            history_manager, "extract_account_id_from_metadata",
            return_value="123456"
        ):
            # Act
            result = history_manager.extract_account_id_from_region_results(
                region_results
            )

        # Assert
        assert result == "123456"

    def test_skip_error_regions(self, history_manager):
        """HM-006: extract_account_id_from_region_results エラースキップ

        history_manager.py:L92 の"error"チェックでエラーリージョンをスキップし、
        次の成功リージョンからaccount_idを取得。
        """
        # Arrange
        region_results = [
            {"region": "us-east-1", "error": "timeout"},
            {"region": "eu-west-1", "output_dir": "/output/eu-west-1"}
        ]
        with patch.object(
            history_manager, "extract_account_id_from_metadata",
            return_value="789012"
        ):
            # Act
            result = history_manager.extract_account_id_from_region_results(
                region_results
            )

        # Assert
        assert result == "789012"

    def test_all_fail_returns_unknown(self, history_manager):
        """HM-007: extract_account_id_from_region_results 全失敗→unknown

        history_manager.py:L101-102 のループ終了→"unknown"をカバー。
        """
        # Arrange
        region_results = [
            {"region": "us-east-1", "error": "timeout"},
            {"region": "eu-west-1", "error": "denied"}
        ]

        # Act
        result = history_manager.extract_account_id_from_region_results(
            region_results
        )

        # Assert
        assert result == "unknown"

    def test_empty_list_returns_unknown(self, history_manager):
        """HM-008: extract_account_id_from_region_results 空リスト

        history_manager.py:L91 のforループ未実行→L101で"unknown"をカバー。
        """
        # Act
        result = history_manager.extract_account_id_from_region_results([])

        # Assert
        assert result == "unknown"


class TestExtractAccurateAccountId:
    """正確なアカウントID取得テスト"""

    def test_ai_summary_valid(self, history_manager):
        """HM-009: extract_accurate_account_id AIサマリー有効

        history_manager.py:L124-129 のAIサマリー優先取得をカバー。
        """
        # Arrange
        ai_summary = {
            "basic_statistics": {"target_account_id": "123456"}
        }

        # Act
        result = history_manager.extract_accurate_account_id(
            ai_summary, "/output/dir"
        )

        # Assert
        assert result == "123456"

    def test_fallback_to_extractor(
        self, history_manager, mock_account_extractor
    ):
        """HM-010: extract_accurate_account_id フォールバック成功

        history_manager.py:L132-136 のCustodian出力フォールバック成功をカバー。
        AIサマリーにtarget_account_idがない場合（例外パスはHM-E03で検証）。
        """
        # Arrange
        ai_summary = {"basic_statistics": {}}
        mock_account_extractor.extract_account_id_with_fallback.return_value = "789012"

        # Act
        result = history_manager.extract_accurate_account_id(
            ai_summary, "/output/dir"
        )

        # Assert
        assert result == "789012"
```

### 2.2 ResultAggregator テスト

```python
class TestResultAggregatorInit:
    """ResultAggregator初期化テスト"""

    def test_init(self, result_aggregator):
        """RA-001: 初期化

        result_aggregator.py:L20-34 をカバー。
        GLOBAL_RESOURCE_TYPESが定義済みであること。
        """
        # Assert
        assert result_aggregator.job_id == "test-job-id"
        assert result_aggregator.logger is not None
        assert isinstance(result_aggregator.GLOBAL_RESOURCE_TYPES, list)
        assert "iam" in result_aggregator.GLOBAL_RESOURCE_TYPES
        assert "s3" in result_aggregator.GLOBAL_RESOURCE_TYPES


class TestIsGlobalResource:
    """グローバルリソース判定テスト"""

    def test_aws_iam_is_global(self, result_aggregator):
        """RA-002: is_global_resource aws.iam→True

        result_aggregator.py:L47-50 のaws.プレフィックス除去→マッチをカバー。
        """
        # Act & Assert
        assert result_aggregator.is_global_resource("aws.iam") is True

    def test_aws_ec2_is_not_global(self, result_aggregator):
        """RA-003: is_global_resource aws.ec2→False

        result_aggregator.py:L50 のany()マッチ失敗をカバー。
        """
        # Act & Assert
        assert result_aggregator.is_global_resource("aws.ec2") is False

    def test_gcp_prefix_stripped(self, result_aggregator):
        """RA-004: is_global_resource gcpプレフィックス除去

        result_aggregator.py:L47 のgcp.プレフィックス除去をカバー。
        gcp.s3 → "s3" → GLOBAL_RESOURCE_TYPESにマッチ。
        """
        # Act & Assert
        assert result_aggregator.is_global_resource("gcp.s3") is True

    def test_partial_match_iam_analyzer(self, result_aggregator):
        """RA-004A: is_global_resource 部分一致によるマッチ

        result_aggregator.py:L50 のany(global_type in clean_type)は部分一致判定。
        "iam-analyzer"は"iam"をsubstringとして含むためTrueとなる。
        この動作はIAM関連リソースを広くグローバル扱いする意図と整合するが、
        意図しない誤判定の可能性がある（制限事項#6参照）。
        """
        # Act & Assert
        assert result_aggregator.is_global_resource("aws.iam-analyzer") is True


class TestAggregateMultiRegionResults:
    """マルチリージョン結果集約テスト"""

    def test_orchestration(self, result_aggregator):
        """RA-005: aggregate_multi_region_results 統合フロー

        result_aggregator.py:L52-83 の3段階処理をカバー。
        _process → _update_metadata → _build_result のオーケストレーション。
        """
        # Arrange
        region_results = [
            {"region": "us-east-1", "violations_count": 3},
            {"region": "eu-west-1", "violations_count": 2},
        ]
        scan_metadata = {"total_regions": 2}

        # Act
        result = result_aggregator.aggregate_multi_region_results(
            region_results, scan_metadata
        )

        # Assert
        assert result["total_violations"] == 5
        assert len(result["successful_regions"]) == 2
        assert "scan_metadata" in result
        assert "region_results" in result
        assert "aggregated_scan_statistics" in result
        # scan_metadataが更新されている
        assert scan_metadata["completed_regions"] == 2
        assert "scan_end_time" in scan_metadata
        # region_resultsがscan_metadataに追加されている
        assert scan_metadata["region_results"] == region_results


class TestProcessIndividualRegionResults:
    """個別リージョン結果処理テスト"""

    def test_success_only(self, result_aggregator):
        """RA-006: _process_individual_region_results 成功のみ

        result_aggregator.py:L120-163 の成功リージョン処理をカバー。
        """
        # Arrange
        results = [
            {"region": "us-east-1", "violations_count": 3},
            {"region": "eu-west-1", "violations_count": 2},
        ]

        # Act
        data = result_aggregator._process_individual_region_results(results)

        # Assert
        assert data["total_violations"] == 5
        assert data["successful_regions"] == ["us-east-1", "eu-west-1"]
        assert data["failed_regions"] == []

    def test_error_only(self, result_aggregator):
        """RA-007: _process_individual_region_results エラーのみ

        result_aggregator.py:L113-119 のエラーリージョン処理をカバー。
        """
        # Arrange
        results = [
            {"region": "us-east-1", "error": "timeout"},
            {"region": "eu-west-1", "error": "permission denied"},
        ]

        # Act
        data = result_aggregator._process_individual_region_results(results)

        # Assert
        assert data["total_violations"] == 0
        assert data["successful_regions"] == []
        assert len(data["failed_regions"]) == 2
        assert data["failed_regions"][0]["region"] == "us-east-1"

    def test_mixed_success_and_error(self, result_aggregator):
        """RA-008: _process_individual_region_results 成功+エラー混在

        result_aggregator.py:L110-163 の成功/エラー混在をカバー。
        """
        # Arrange
        results = [
            {"region": "us-east-1", "violations_count": 3},
            {"region": "eu-west-1", "error": "timeout"},
        ]

        # Act
        data = result_aggregator._process_individual_region_results(results)

        # Assert
        assert data["total_violations"] == 3
        assert data["successful_regions"] == ["us-east-1"]
        assert len(data["failed_regions"]) == 1

    def test_with_scan_statistics(self, result_aggregator):
        """RA-009: _process_individual_region_results scan_statistics有り

        result_aggregator.py:L126-148 のscan_statistics処理をカバー。
        total_scanned/violations集計、resource_type記録、per_region_stats追加。
        """
        # Arrange
        results = [{
            "region": "us-east-1",
            "violations_count": 3,
            "scan_statistics": {
                "total_scanned": 100,
                "violations": 3,
                "compliance_rate": 97.0,
                "resource_type": "aws.ec2"
            }
        }]

        # Act
        data = result_aggregator._process_individual_region_results(results)

        # Assert
        agg = data["aggregated_scan_statistics"]
        assert agg["total_scanned"] == 100
        assert agg["total_violations"] == 3
        assert agg["total_compliant"] == 97
        assert agg["overall_compliance_rate"] == 97.0
        assert "aws.ec2" in agg["resource_types"]
        assert len(agg["per_region_stats"]) == 1

    def test_without_scan_statistics(self, result_aggregator):
        """RA-010: _process_individual_region_results scan_statistics無し

        result_aggregator.py:L126-127 のscan_statistics無し分岐をカバー。
        """
        # Arrange
        results = [{"region": "us-east-1", "violations_count": 2}]

        # Act
        data = result_aggregator._process_individual_region_results(results)

        # Assert
        agg = data["aggregated_scan_statistics"]
        assert agg["total_scanned"] == 0
        assert agg["resource_types"] == []
        assert agg["per_region_stats"] == []

    def test_duplicate_region_dedup(self, result_aggregator):
        """RA-011: _process_individual_region_results 重複リージョンdedup

        result_aggregator.py:L152-156 の重複チェック（successful_regions_set）をカバー。
        グローバルリソース処理で同一リージョンが複数回現れるケース。
        """
        # Arrange
        results = [
            {"region": "us-east-1", "violations_count": 3},
            {"region": "us-east-1", "violations_count": 2},
        ]

        # Act
        data = result_aggregator._process_individual_region_results(results)

        # Assert
        assert data["successful_regions"] == ["us-east-1"]
        assert data["total_violations"] == 5  # 違反数は重複でも合計
        # L156のデバッグログ出力を確認（重複検出時）
        result_aggregator.logger.debug.assert_called()

    def test_stdout_stderr_collection(self, result_aggregator):
        """RA-012: _process_individual_region_results stdout/stderr収集

        result_aggregator.py:L159-162 のstdout/stderr extend集約をカバー。
        """
        # Arrange
        results = [
            {"region": "us-east-1", "violations_count": 0,
             "stdout_output": ["line1", "line2"],
             "stderr_output": ["err1"]},
            {"region": "eu-west-1", "violations_count": 0,
             "stdout_output": ["line3"], "stderr_output": []},
        ]

        # Act
        data = result_aggregator._process_individual_region_results(results)

        # Assert
        assert data["all_stdout"] == ["line1", "line2", "line3"]
        assert data["all_stderr"] == ["err1"]

    def test_total_scanned_zero_compliance(self, result_aggregator):
        """RA-013: _process_individual_region_results total_scanned==0

        result_aggregator.py:L166 の条件分岐不成立（total_scanned==0）→L165で初期化された0.0が維持される経路をカバー。
        """
        # Arrange
        results = [{"region": "us-east-1", "violations_count": 0}]

        # Act
        data = result_aggregator._process_individual_region_results(results)

        # Assert
        assert data["aggregated_scan_statistics"]["overall_compliance_rate"] == 0.0

    def test_resource_type_unknown_filtered(self, result_aggregator):
        """RA-014: _process_individual_region_results resource_type unknown除外

        result_aggregator.py:L137-138 のresource_type!="unknown"チェックをカバー。
        """
        # Arrange
        results = [{
            "region": "us-east-1",
            "violations_count": 0,
            "scan_statistics": {
                "total_scanned": 10,
                "violations": 0,
                "compliance_rate": 100.0,
                "resource_type": "unknown"
            }
        }]

        # Act
        data = result_aggregator._process_individual_region_results(results)

        # Assert
        assert data["aggregated_scan_statistics"]["resource_types"] == []


class TestUpdateScanMetadata:
    """スキャンメタデータ更新テスト"""

    def test_with_failed_regions(self, result_aggregator):
        """RA-015: _update_scan_metadata failed有り

        result_aggregator.py:L210-211 のfailed_regions非空→failed_region_details追加をカバー。
        """
        # Arrange
        metadata = {"existing_key": "value"}
        successful = ["us-east-1"]
        failed = [{"region": "eu-west-1", "error": "timeout"}]

        # Act
        result_aggregator._update_scan_metadata(metadata, successful, failed)

        # Assert
        assert metadata["completed_regions"] == 1
        assert metadata["failed_regions"] == 1
        assert metadata["successful_regions"] == successful
        assert "scan_end_time" in metadata
        assert metadata["failed_region_details"] == failed

    def test_without_failed_regions(self, result_aggregator):
        """RA-016: _update_scan_metadata failed無し

        result_aggregator.py:L210 のfailed_regions空→failed_region_details追加なしをカバー。
        """
        # Arrange
        metadata = {}
        successful = ["us-east-1", "eu-west-1"]

        # Act
        result_aggregator._update_scan_metadata(metadata, successful, [])

        # Assert
        assert metadata["completed_regions"] == 2
        assert metadata["failed_regions"] == 0
        assert "failed_region_details" not in metadata


class TestBuildAggregatedResult:
    """集約結果構築テスト"""

    def test_structure(self, result_aggregator):
        """RA-017: _build_aggregated_result 構造確認

        result_aggregator.py:L230-253 の結果辞書構築をカバー。
        """
        # Arrange
        processed_data = {
            "total_violations": 5,
            "successful_regions": ["us-east-1"],
            "failed_regions": [],
            "all_stdout": ["line1"],
            "all_stderr": [],
            "aggregated_scan_statistics": {"total_scanned": 100}
        }
        scan_metadata = {"total_regions": 1}
        region_results = [{"region": "us-east-1"}]

        # Act
        result = result_aggregator._build_aggregated_result(
            processed_data, scan_metadata, region_results
        )

        # Assert
        assert result["total_violations"] == 5
        assert result["successful_regions"] == ["us-east-1"]
        assert result["failed_regions"] == []
        assert result["scan_metadata"] == scan_metadata
        assert result["region_results"] == region_results
        assert result["stdout_output"] == ["line1"]
        assert result["aggregated_scan_statistics"]["total_scanned"] == 100


class TestProcessSingleRegionResult:
    """単一リージョン結果処理テスト"""

    def test_normal(self, result_aggregator):
        """RA-018: process_single_region_result 正常

        result_aggregator.py:L255-292 の単一リージョン結果辞書構築をカバー。
        """
        # Act
        result = result_aggregator.process_single_region_result(
            region="us-east-1",
            return_code=0,
            stdout_output=["OK"],
            stderr_output=[],
            violations_count=3
        )

        # Assert
        assert result["region"] == "us-east-1"
        assert result["return_code"] == 0
        assert result["violations_count"] == 3
        assert result["stdout_output"] == ["OK"]
        assert result["stderr_output"] == []


class TestCreateErrorResult:
    """エラー結果作成テスト"""

    def test_normal(self, result_aggregator):
        """RA-019: create_error_result 正常

        result_aggregator.py:L294-312 のエラー結果辞書構築をカバー。
        """
        # Act
        result = result_aggregator.create_error_result(
            "us-east-1", "connection timeout"
        )

        # Assert
        assert result["region"] == "us-east-1"
        assert result["error"] == "connection timeout"
        assert result["violations_count"] == 0


class TestCreateScanSummary:
    """スキャンサマリー生成テスト"""

    def test_all_success(self, result_aggregator):
        """RA-020: create_scan_summary 全成功

        result_aggregator.py:L337-342 のfailed_regions==0分岐をカバー。
        """
        # Arrange
        aggregated_result = {
            "total_violations": 5,
            "scan_metadata": {
                "completed_regions": 3,
                "total_regions": 3,
                "failed_regions": 0
            }
        }

        # Act
        result = result_aggregator.create_scan_summary(
            aggregated_result, "AWS"
        )

        # Assert
        assert "完了" in result["message"]
        assert "部分" not in result["message"]
        assert result["summary_data"]["scan_status"] == "success"
        assert result["summary_data"]["violations_found"] == 5

    def test_partial_failure(self, result_aggregator):
        """RA-021: create_scan_summary 部分失敗

        result_aggregator.py:L343-348 のfailed_regions>0分岐をカバー。
        """
        # Arrange
        aggregated_result = {
            "total_violations": 3,
            "scan_metadata": {
                "completed_regions": 2,
                "total_regions": 3,
                "failed_regions": 1
            }
        }

        # Act
        result = result_aggregator.create_scan_summary(
            aggregated_result, "AWS"
        )

        # Assert
        assert "部分完了" in result["message"]
        assert result["summary_data"]["scan_status"] == "failed"
        assert "成功: 2" in result["message"]
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| HM-E01 | extract_account_id_from_metadata 例外→unknown | metadata抽出例外 | "unknown" |
| HM-E02 | extract_account_id_from_region_results 例外→unknown | イテレーション例外 | "unknown" |
| HM-E03 | extract_accurate_account_id フォールバック例外→unknown | extractor例外 | "unknown" |
| HM-E04 | extract_accurate_account_id ai_summary=None→AttributeError | None | AttributeError発生 |

### 3.1 異常系テスト

```python
class TestHistoryManagerErrors:
    """HistoryManager異常系テスト"""

    def test_metadata_extraction_exception(
        self, history_manager, mock_metadata_extractor
    ):
        """HM-E01: extract_account_id_from_metadata 例外→unknown

        history_manager.py:L75-77 のexceptブロックをカバー。
        """
        # Arrange
        mock_metadata_extractor.extract_metadata_from_output_dir.side_effect = (
            RuntimeError("extraction failed")
        )

        # Act
        result = history_manager.extract_account_id_from_metadata("/output")

        # Assert
        assert result == "unknown"
        history_manager.logger.warning.assert_called()

    def test_region_results_exception(self, history_manager):
        """HM-E02: extract_account_id_from_region_results 例外→unknown

        history_manager.py:L104-106 のexceptブロックをカバー。
        forループのイテレーション開始時の例外を検証。
        個別リージョン処理中の例外はextract_account_id_from_metadata内で
        catchされるため、このexceptブロックには到達しない。
        """
        # Arrange — イテレーション中に例外を発生させる
        bad_results = MagicMock()
        bad_results.__iter__ = MagicMock(
            side_effect=RuntimeError("iteration failed")
        )

        # Act
        result = history_manager.extract_account_id_from_region_results(
            bad_results
        )

        # Assert
        assert result == "unknown"
        history_manager.logger.warning.assert_called()

    def test_accurate_account_id_fallback_exception(
        self, history_manager, mock_account_extractor
    ):
        """HM-E03: extract_accurate_account_id フォールバック例外→unknown

        history_manager.py:L137-139 のexceptブロックをカバー。
        AIサマリー無し→フォールバック→例外のケース。
        """
        # Arrange
        ai_summary = {"basic_statistics": {}}
        mock_account_extractor.extract_account_id_with_fallback.side_effect = (
            RuntimeError("extractor failed")
        )

        # Act
        result = history_manager.extract_accurate_account_id(
            ai_summary, "/output/dir"
        )

        # Assert
        assert result == "unknown"
        history_manager.logger.warning.assert_called()

    def test_ai_summary_none_raises_error(self, history_manager):
        """HM-E04: extract_accurate_account_id ai_summary=None→AttributeError

        history_manager.py:L124 のai_summary.get()はtryブロック外にあるため、
        ai_summary=Noneの場合AttributeErrorが発生し、呼び出し元に伝播する。
        """
        # Act & Assert
        with pytest.raises(AttributeError):
            history_manager.extract_accurate_account_id(None, "/output/dir")
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| HM-SEC-01 | extract_account_id_from_metadata例外でパス非露出 | ファイルパス含む例外 | return値に機密情報なし |
| RA-SEC-01 | create_error_result攻撃的メッセージ安全格納 | XSS/SQLi文字列 | 安全に格納 |
| RA-SEC-02 | process_single_region_result攻撃的リージョン名 | 注入文字列 | 安全に格納 |

```python
@pytest.mark.security
class TestAggregationHistorySecurity:
    """結果集約+履歴セキュリティテスト"""

    def test_metadata_exception_no_path_leak(
        self, history_manager, mock_metadata_extractor
    ):
        """HM-SEC-01: extract_account_id_from_metadata例外でパス非露出

        history_manager.py:L75-77 で例外時、str(e)はlogger.warningに出力されるが
        return値は定型"unknown"のみで機密情報を含まない。
        """
        # Arrange
        sensitive_path = "/etc/secrets/db_credentials.json"
        mock_metadata_extractor.extract_metadata_from_output_dir.side_effect = (
            FileNotFoundError(f"File not found: {sensitive_path}")
        )

        # Act
        result = history_manager.extract_account_id_from_metadata(
            sensitive_path
        )

        # Assert
        assert result == "unknown"
        assert "secrets" not in result
        assert "credentials" not in result

    def test_error_result_malicious_message(self, result_aggregator):
        """RA-SEC-01: create_error_result攻撃的メッセージ安全格納

        result_aggregator.py:L294-312 のf-string格納は安全な文字列操作。
        この層はプレーンテキスト生成のためエスケープ不要。
        HTML表示時は表示層でエスケープが必要。
        """
        # Arrange
        malicious_msg = "<script>alert('xss')</script>; DROP TABLE scans; --"

        # Act
        result = result_aggregator.create_error_result("us-east-1", malicious_msg)

        # Assert
        assert result["error"] == malicious_msg
        assert isinstance(result["error"], str)

    def test_single_region_malicious_region_name(self, result_aggregator):
        """RA-SEC-02: process_single_region_result攻撃的リージョン名

        result_aggregator.py:L276-282 の辞書格納は安全な文字列操作。
        この層はプレーンテキスト生成のためエスケープ不要。
        HTML表示時は表示層でエスケープが必要。
        """
        # Arrange
        malicious_region = "'; DROP TABLE regions; --"

        # Act
        result = result_aggregator.process_single_region_result(
            malicious_region, 0, [], [], 0
        )

        # Assert
        assert result["region"] == malicious_region
        assert isinstance(result["region"], str)
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_results_module` | テスト間のモジュール状態リセット（#16a conftest.pyで定義済み） | function | Yes |
| `history_manager` | テスト用HistoryManagerインスタンス | function | No |
| `result_aggregator` | テスト用ResultAggregatorインスタンス | function | No |
| `mock_metadata_extractor` | metadata_extractorモジュールモック（遅延import対応） | function | No |
| `mock_account_extractor` | account_id_extractorモジュールモック（遅延import対応） | function | No |

### 共通フィクスチャ定義

```python
# test/unit/jobs/tasks/new_custodian_scan/results/conftest.py
# ※ 以下は #16a の conftest.py に追記する。
# ※ reset_results_module (autouse) と MODULE_BASE, pytest, patch 等の
#    import は既に定義済み。

import sys

HM_MODULE = "app.jobs.tasks.new_custodian_scan.results.history_manager"
RA_MODULE = "app.jobs.tasks.new_custodian_scan.results.result_aggregator"
UTILS_META = "app.jobs.utils.metadata_extractor"
UTILS_ACCOUNT = "app.jobs.utils.account_id_extractor"


@pytest.fixture
def history_manager():
    """テスト用HistoryManagerインスタンス

    TaskLoggerのみパッチして実__init__を通す。
    """
    with patch(f"{HM_MODULE}.TaskLogger"):
        from app.jobs.tasks.new_custodian_scan.results.history_manager import (
            HistoryManager
        )
        return HistoryManager("test-job-id")
    # 注記: テスト内で内部メソッドをモックする場合は
    # patch.object(history_manager, "method_name") を使用する。
    # HM-005〜HM-008 でこのパターンを利用。


@pytest.fixture
def result_aggregator():
    """テスト用ResultAggregatorインスタンス

    TaskLoggerのみパッチして実__init__を通す。
    """
    with patch(f"{RA_MODULE}.TaskLogger"):
        from app.jobs.tasks.new_custodian_scan.results.result_aggregator import (
            ResultAggregator
        )
        return ResultAggregator("test-job-id")


@pytest.fixture
def mock_metadata_extractor():
    """metadata_extractorモジュールのモック（遅延import対応）

    HistoryManager.extract_account_id_from_metadata内の遅延importに対応。
    sys.modulesにモックモジュールを注入して、
    from ....utils.metadata_extractor import ... を安全に実行可能にする。
    """
    mock_module = MagicMock()
    with patch.dict(sys.modules, {UTILS_META: mock_module}):
        yield mock_module


@pytest.fixture
def mock_account_extractor():
    """account_id_extractorモジュールのモック（遅延import対応）

    HistoryManager.extract_accurate_account_id内の遅延importに対応。
    """
    mock_module = MagicMock()
    with patch.dict(sys.modules, {UTILS_ACCOUNT: mock_module}):
        yield mock_module
```

---

## 6. テスト実行例

```bash
# 結果集約+履歴テスト全体を実行
pytest test/unit/jobs/tasks/new_custodian_scan/results/test_results_aggregation_history.py -v

# クラス単位で実行
pytest test/unit/jobs/tasks/new_custodian_scan/results/test_results_aggregation_history.py::TestProcessIndividualRegionResults -v
pytest test/unit/jobs/tasks/new_custodian_scan/results/test_results_aggregation_history.py::TestExtractAccountIdFromMetadata -v

# カバレッジ付きで実行
pytest test/unit/jobs/tasks/new_custodian_scan/results/test_results_aggregation_history.py \
  --cov=app.jobs.tasks.new_custodian_scan.results.history_manager \
  --cov=app.jobs.tasks.new_custodian_scan.results.result_aggregator \
  --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/jobs/tasks/new_custodian_scan/results/test_results_aggregation_history.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 32 | HM-001〜HM-010, RA-001〜RA-004A, RA-005〜RA-021 |
| 異常系 | 4 | HM-E01〜HM-E04 |
| セキュリティ | 3 | HM-SEC-01, RA-SEC-01, RA-SEC-02 |
| **合計** | **39** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestHistoryManagerInit` | HM-001 | 1 |
| `TestExtractAccountIdFromMetadata` | HM-002〜HM-004 | 3 |
| `TestExtractAccountIdFromRegionResults` | HM-005〜HM-008 | 4 |
| `TestExtractAccurateAccountId` | HM-009〜HM-010 | 2 |
| `TestResultAggregatorInit` | RA-001 | 1 |
| `TestIsGlobalResource` | RA-002〜RA-004A | 4 |
| `TestAggregateMultiRegionResults` | RA-005 | 1 |
| `TestProcessIndividualRegionResults` | RA-006〜RA-014 | 9 |
| `TestUpdateScanMetadata` | RA-015〜RA-016 | 2 |
| `TestBuildAggregatedResult` | RA-017 | 1 |
| `TestProcessSingleRegionResult` | RA-018 | 1 |
| `TestCreateErrorResult` | RA-019 | 1 |
| `TestCreateScanSummary` | RA-020〜RA-021 | 2 |
| `TestHistoryManagerErrors` | HM-E01〜HM-E04 | 4 |
| `TestAggregationHistorySecurity` | HM-SEC-01, RA-SEC-01, RA-SEC-02 | 3 |

### 実装失敗が予想されるテスト

以下の実行前提が整備されていれば、失敗が予想されるテストはありません。

#### 実行前提

| 前提 | 対応内容 |
|------|---------|
| `security`マーカー | `pyproject.toml` に定義済み（#16aで追加） |
| `reset_results_module` | `conftest.py` に #16a で定義済み |
| `app.jobs.utils` パッケージ | sys.modulesモック注入で対応（mock_metadata_extractor, mock_account_extractor） |

### 注意事項

- HistoryManagerの`extract_account_id_from_metadata`と`extract_account_id_from_region_results`はtry/except付きで、例外時は"unknown"を返却（HM-E01〜E02でカバー）。`extract_accurate_account_id`はtry/except付きだがL124の`ai_summary.get()`がtryブロック外にあり、ai_summary=Noneの場合AttributeErrorが伝播する（HM-E04で検証）。フォールバック例外はHM-E03でカバー
- extract_account_id_from_region_resultsはextract_account_id_from_metadataを内部呼び出しするため、patch.objectで内部メソッドをモックして自身のロジックのみテスト
- ResultAggregator._update_scan_metadataはdatetime.now()を使用するが、テストではscan_end_timeの存在のみ確認（datetime モック不要）
- ResultAggregator._process_individual_region_resultsは複雑なループ処理のため、9テストで各条件分岐を個別にカバー

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | HistoryManagerの遅延importパターン | テスト環境でapp.jobs.utils.*が未インストールの場合、sys.modulesモック注入が必要 | mock_metadata_extractor/mock_account_extractorフィクスチャで対応 |
| 2 | extract_account_id_from_metadata内のos/glob呼び出し | テスト時に実ファイルシステムにアクセスするが、情報ログ（logger.info）のみで結果値に影響なし（例外はL75-77でcatchされる） | モック不要（存在しないパスでもエラーにならない）。テスト速度改善が必要な場合はos/globもモック可能 |
| 3 | _update_scan_metadataのdatetime.now() | テスト実行時刻に依存するが、存在チェックのみで値の正確性は検証不要 | scan_end_timeの存在確認のみ |
| 4 | create_scan_summaryのメッセージ文言依存 | "完了"/"部分完了"等の文言変更でテスト失敗 | 部分一致アサーションで脆弱性を低減 |
| 5 | extract_account_id_from_region_resultsのoutput_dir無しリージョン | L92の条件 `"error" not in result and result.get("output_dir")` でerror無し+output_dir無しのリージョンはスキップされるがテスト未カバー | 実運用で発生しにくいシナリオ（結果dictにoutput_dirが含まれない不正形式）のため未実施 |
| 6 | is_global_resourceの部分一致判定 | L50の `any(global_type in clean_type)` は完全一致ではなくsubstring一致。例: "iam-analyzer"は"iam"を含むためTrueとなる。IAM関連リソースを広くグローバル扱いする意図と整合するが、意図しない誤判定の可能性がある | RA-004Aテストで動作を文書化。修正が必要な場合は完全一致 (`==`) またはプレフィックス一致 (`startswith`) への変更を検討 |
