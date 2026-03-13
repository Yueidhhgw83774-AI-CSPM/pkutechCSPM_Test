# jobs/tasks/new_custodian_scan/result_processor テストケース

## 1. 概要

`result_processor.py` はスキャン結果の処理・集約を担当するオーケストレーションクラス。8つのサブコンポーネントに処理を委譲しつつ、Phase3エラー分析・統計計算・v2履歴データ生成の統合制御を行う。

### 1.1 主要機能

| メソッド | 説明 |
|---------|------|
| `__init__` | 8つのサブコンポーネント + Phase3エラーハンドラ + GLOBAL_RESOURCE_TYPES を初期化 |
| `aggregate_multi_region_results` | 複数リージョン結果の集約・Phase3エラー判定・認証エラーログ |
| `_analyze_execution_errors` | 実行エラー分析・ExecutionErrorInfo生成・認証エラー特別処理 |
| `process_scan_for_history_v2` | v2マッピング仕様準拠の履歴データ生成（統計計算・インサイト生成含む） |
| `_extract_account_id` | アカウントID取得（3段階フォールバック） |
| `_calculate_basic_statistics` | 基本統計計算（ユニークポリシー集計含む） |
| `_analyze_custodian_logs` | ログ解析ラッパー（例外処理付き） |
| `_get_authentication_status` | 認証ステータス判定（例外時"success"フォールバック） |
| `_create_error_result` | プライベートエラー結果生成（result_formatterへ委譲） |
| `create_scan_summary` | スキャンサマリー生成（認証/致命的エラー対応） |
| `store_multi_region_results_to_opensearch` | OpenSearch保存（opensearch_managerへ委譲） |
| `process_single_region_result` | 単一リージョン結果処理（result_aggregatorへ委譲） |
| `create_error_result` | パブリックエラー結果生成（result_aggregatorへ委譲） |
| `read_detailed_scan_results` | 詳細結果読み込み（file_processorへ委譲） |

### 1.2 カバレッジ目標: 85%

> **注記**: 委譲メソッドが多いため、委譲の正確性検証とオーケストレーションロジック（エラー分析・統計計算・条件分岐）を重点テスト。pytest-asyncio が必要。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/jobs/tasks/new_custodian_scan/result_processor.py` |
| テストコード | `test/unit/jobs/tasks/new_custodian_scan/test_result_processor.py` |

### 1.4 補足情報

#### サブコンポーネント依存関係

```
result_processor.py ──→ ResultAggregator（基本集約）
                     ──→ OpenSearchManager（OpenSearch保存・推奨事項マッピング）
                     ──→ HistoryManager（アカウントID抽出）
                     ──→ InsightGenerator（インサイト・統計生成）
                     ──→ ResultFormatter（v2形式変換・エラー結果）
                     ──→ CustodianErrorAnalyzer（エラー分析）
                     ──→ ReturnCodeAnalyzer（リターンコード判定）
                     ──→ FileProcessor（ファイル読み込み）
                     ──→ CustodianErrorHandler（Phase3構造化エラー）
                     ──→ TaskLogger（ログ）
                     ──→ ExecutionErrorInfo（データクラス: エラー情報格納）
                     ──→ analyze_multi_region_scan（ログ解析関数）
```

#### テスト戦略

| テストカテゴリ | 手法 |
|--------------|------|
| 初期化テスト | サブコンポーネントクラスを patch してインスタンス生成 |
| オーケストレーションテスト | サブコンポーネントのモックメソッドで戻り値制御・呼び出し検証 |
| 委譲テスト | 引数がそのままサブコンポーネントに渡されることを検証 |
| 非同期テスト | AsyncMock + pytest-asyncio で非同期メソッドをテスト |

#### 主要分岐マップ

| メソッド | 行番号 | 条件 | 分岐数 |
|---------|--------|------|--------|
| `aggregate_multi_region_results` | L101, L122-134 | 認証エラー有無、Phase3失敗判定（認証/非認証） | 3 |
| `_analyze_execution_errors` | L151, L169 | 実行エラー有無、認証エラー判定 | 3 |
| `process_scan_for_history_v2` | L197, L228-258, L263-276 | policy_results空、統計計算、successful_regions形式 | 7 |
| `_extract_account_id` | L344-354 | 直接取得/region_results/metadata | 3 |
| `_calculate_basic_statistics` | L378, L381, L385, L395 | ポリシー名有無、違反有無、初回出現、ゼロ除算防止 | 4 |
| `create_scan_summary` | L481-494 | 認証エラー/致命的エラー/正常 | 3 |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| RPROC-001 | 初期化時に全サブコンポーネントが生成される | job_id="test-job" | 8コンポーネント + Phase3ハンドラ + GLOBAL_RESOURCE_TYPES初期化 |
| RPROC-002 | 正常集約（エラーなし） | 正常region_results | return_code, violations_count, phase3_error_summary含む結果 |
| RPROC-003 | 認証エラーありでエラーログ出力 | has_authentication_errors=True | logger.errorが認証情報付きで呼ばれる |
| RPROC-004 | Phase3ジョブ失敗判定（認証エラー） | should_fail_job=True, 認証エラーあり | logger.errorにfailure_reason="authentication_error" |
| RPROC-005 | Phase3ジョブ失敗判定（非認証エラー） | should_fail_job=True, 認証エラーなし | logger.warningにvalidation_errors含む |
| RPROC-006 | 実行エラーなしでスキップ | has_execution_error=False | ExecutionErrorInfo未生成、result変更なし |
| RPROC-007 | 実行エラーあり（構造化ログ記録） | has_execution_error=True | error_analysis, user_friendly_error追加 |
| RPROC-008 | 認証エラー検出で特別処理 | error_type="authentication_error" | authentication_failure=True, logger.error呼び出し |
| RPROC-009 | v2履歴データ正常生成 | 正常custodian_output_dir, scan_metadata | 全フィールド含む結果辞書 |
| RPROC-010 | aggregated_scan_statistics事前提供 | scan_metadataに統計データあり | 計算スキップ、事前値使用 |
| RPROC-011 | policy_resultsから統計計算 | scan_metadataに統計なし、total_scanned>0 | compliance_rate計算あり |
| RPROC-012 | total_scanned=0で統計計算スキップ | 全policy_resultsのtotal_resources_scanned=0 | aggregated_scan_statistics空のまま |
| RPROC-013 | successful_regions dict形式 | [{"region_name": "us-east-1"}] | regions=["us-east-1"] |
| RPROC-014 | successful_regions str形式（旧形式） | ["us-east-1", "us-west-2"] | regions=["us-east-1", "us-west-2"] |
| RPROC-015 | successful_regions 非リスト | successful_regions="invalid" | regions=[] |
| RPROC-016 | dict形式でregion_nameなし・空文字列（混在） | [{"other_key":"val"}, {"region_name":""}, {"region_name":"us-east-1"}] | regions=["us-east-1"]（無効エントリスキップ） |
| RPROC-017 | アカウントID直接取得成功 | scan_metadata.account_id="123" | "123"返却 |
| RPROC-018 | region_resultsからアカウントID取得 | account_id="unknown", region_resultsあり | history_manager.extract_from_region_results呼び出し |
| RPROC-019 | metadataからアカウントID取得 | account_id="unknown", region_resultsなし | history_manager.extract_from_metadata呼び出し |
| RPROC-020 | 基本統計の正常計算 | 違反あり・なし混在policy_results | 正確な統計値 |
| RPROC-021 | ユニークポリシー重複集計 | 同一ポリシー名が複数リージョンに存在 | unique_policiesが正確にカウント |
| RPROC-022 | 空リスト（ゼロ除算防止） | policy_results=[] | compliance_percentage=0 |
| RPROC-023 | 認証ステータス成功 | has_authentication_errors=False | "success" |
| RPROC-024 | 認証ステータス失敗 | has_authentication_errors=True | "failed" |
| RPROC-025 | スキャンサマリー正常生成 | エラーなしaggregated_result | basic_summaryそのまま返却 |
| RPROC-026 | 認証エラーありサマリー | has_authentication_errors=True | message更新、scan_status="failed" |
| RPROC-027 | 致命的エラーありサマリー | fatal_error_detected=True | message更新、scan_status="failed" |
| RPROC-028 | OpenSearch保存委譲 | 正常引数 | opensearch_manager.store_multi_region_results呼び出し |
| RPROC-029 | 単一リージョン結果処理委譲 | region, return_code等 | result_aggregator.process_single_region_result呼び出し |
| RPROC-030 | パブリックエラー結果生成委譲 | region, error_message | result_aggregator.create_error_result呼び出し |
| RPROC-031 | 詳細結果読み込み委譲 | output_dir, region | file_processor.read_detailed_scan_results呼び出し |
| RPROC-032 | プライベートエラー結果生成委譲 | error_message | result_formatter.create_error_result呼び出し |
| RPROC-033 | ログ解析正常実行 | 正常custodian_output_dir | analyze_multi_region_scan呼び出し |
| RPROC-034 | ポリシー名なしエントリのスキップ | original_policy_name/policy_name両方空 | ユニーク集計に含まれない |

### 2.1 初期化テスト

```python
# test/unit/jobs/tasks/new_custodian_scan/test_result_processor.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

MODULE = "app.jobs.tasks.new_custodian_scan.result_processor"


class TestResultProcessorInit:
    """ResultProcessor初期化テスト"""

    def test_init_creates_all_subcomponents(self, mock_components):
        """RPROC-001: 初期化時に全サブコンポーネントが生成される"""
        # Arrange
        from app.jobs.tasks.new_custodian_scan.result_processor import ResultProcessor

        # Act
        proc = ResultProcessor("test-job-id")

        # Assert
        # 8つのサブコンポーネントが初期化されている
        mock_components["ResultAggregator"].assert_called_once_with("test-job-id")
        mock_components["OpenSearchManager"].assert_called_once_with("test-job-id")
        mock_components["HistoryManager"].assert_called_once_with("test-job-id")
        mock_components["InsightGenerator"].assert_called_once_with("test-job-id")
        mock_components["ResultFormatter"].assert_called_once_with("test-job-id")
        mock_components["CustodianErrorAnalyzer"].assert_called_once_with("test-job-id")
        mock_components["ReturnCodeAnalyzer"].assert_called_once_with("test-job-id")
        mock_components["FileProcessor"].assert_called_once_with("test-job-id")
        mock_components["CustodianErrorHandler"].assert_called_once_with("test-job-id")
        # GLOBAL_RESOURCE_TYPES の確認
        assert "iam" in proc.GLOBAL_RESOURCE_TYPES
        assert "s3" in proc.GLOBAL_RESOURCE_TYPES
        assert len(proc.GLOBAL_RESOURCE_TYPES) == 12
```

### 2.2 aggregate_multi_region_results テスト

```python
class TestAggregateMultiRegionResults:
    """複数リージョン結果集約テスト"""

    def test_aggregate_normal_no_errors(self, processor):
        """RPROC-002: 正常集約（エラーなし）

        result_processor.py:L69-136 の正常フローをカバー。
        """
        # Arrange
        region_results = [{"region": "us-east-1", "return_code": 0, "violations_count": 3}]
        scan_metadata = {"completed_regions": 1}
        processor.result_aggregator.aggregate_multi_region_results.return_value = {
            "total_violations": 3,
            "scan_metadata": scan_metadata,
            "region_results": region_results,
            "stdout_output": [],
            "stderr_output": []
        }
        processor.return_code_analyzer.determine_overall_return_code.return_value = 0
        processor.error_analyzer.analyze_execution_result.return_value = {
            "has_execution_error": False
        }
        processor.phase3_error_handler.get_error_summary.return_value = {
            "has_authentication_errors": False,
            "total_errors": 0
        }
        processor.phase3_error_handler.should_fail_job.return_value = False

        # Act
        result = processor.aggregate_multi_region_results(
            region_results, scan_metadata, "/tmp/output"
        )

        # Assert
        assert result["return_code"] == 0
        assert result["violations_count"] == 3
        assert result["custodian_output_dir"] == "/tmp/output"
        assert "phase3_error_summary" in result

    def test_aggregate_with_authentication_error_log(self, processor):
        """RPROC-003: 認証エラーありでエラーログ出力

        result_processor.py:L101-106 の認証エラーログ分岐をカバー。
        """
        # Arrange
        processor.result_aggregator.aggregate_multi_region_results.return_value = {
            "total_violations": 0, "scan_metadata": {},
            "region_results": [], "stdout_output": [], "stderr_output": []
        }
        processor.return_code_analyzer.determine_overall_return_code.return_value = 1
        processor.error_analyzer.analyze_execution_result.return_value = {
            "has_execution_error": False
        }
        processor.phase3_error_handler.get_error_summary.return_value = {
            "has_authentication_errors": True,
            "authentication_errors": 1,
            "total_errors": 1,
            "error_severity": "critical"
        }
        processor.phase3_error_handler.should_fail_job.return_value = True

        # Act
        processor.aggregate_multi_region_results([], {})

        # Assert
        # L102: 認証エラーログが出力される
        processor.logger.error.assert_called()
        call_args = processor.logger.error.call_args
        assert "認証エラー" in call_args[0][0]

    def test_aggregate_phase3_fail_auth_error(self, processor):
        """RPROC-004: Phase3ジョブ失敗判定（認証エラー）

        result_processor.py:L122-128 の認証エラーによるジョブ失敗分岐をカバー。
        """
        # Arrange
        processor.result_aggregator.aggregate_multi_region_results.return_value = {
            "total_violations": 0, "scan_metadata": {},
            "region_results": [], "stdout_output": [], "stderr_output": []
        }
        processor.return_code_analyzer.determine_overall_return_code.return_value = 1
        processor.error_analyzer.analyze_execution_result.return_value = {
            "has_execution_error": False
        }
        error_summary = {
            "has_authentication_errors": True,
            "authentication_errors": 1,
            "total_errors": 1,
            "error_severity": "critical"
        }
        processor.phase3_error_handler.get_error_summary.return_value = error_summary
        processor.phase3_error_handler.should_fail_job.return_value = True

        # Act
        processor.aggregate_multi_region_results([], {})

        # Assert
        # L124: Phase3認証エラーログが出力される
        error_calls = [c for c in processor.logger.error.call_args_list
                       if "Phase 3" in str(c)]
        assert len(error_calls) > 0

    def test_aggregate_phase3_fail_non_auth_error(self, processor):
        """RPROC-005: Phase3ジョブ失敗判定（非認証エラー）

        result_processor.py:L129-134 の非認証エラーによるジョブ失敗分岐をカバー。
        """
        # Arrange
        processor.result_aggregator.aggregate_multi_region_results.return_value = {
            "total_violations": 0, "scan_metadata": {},
            "region_results": [], "stdout_output": [], "stderr_output": []
        }
        processor.return_code_analyzer.determine_overall_return_code.return_value = 1
        processor.error_analyzer.analyze_execution_result.return_value = {
            "has_execution_error": False
        }
        processor.phase3_error_handler.get_error_summary.return_value = {
            "has_authentication_errors": False,
            "validation_errors": 2,
            "fatal_errors": 1,
            "total_errors": 3
        }
        processor.phase3_error_handler.should_fail_job.return_value = True

        # Act
        processor.aggregate_multi_region_results([], {})

        # Assert
        # L130: Phase3非認証エラーwarningログが出力される
        warning_calls = [c for c in processor.logger.warning.call_args_list
                         if "Phase 3" in str(c)]
        assert len(warning_calls) > 0
```

### 2.3 _analyze_execution_errors テスト

```python
class TestAnalyzeExecutionErrors:
    """実行エラー分析テスト"""

    def test_no_execution_error_skips_processing(self, processor):
        """RPROC-006: 実行エラーなしでスキップ

        result_processor.py:L151 の has_execution_error=False 分岐をカバー。
        """
        # Arrange
        region_results = [{"region": "us-east-1", "return_code": 0}]
        processor.error_analyzer.analyze_execution_result.return_value = {
            "has_execution_error": False
        }

        # Act
        processor._analyze_execution_errors(region_results)

        # Assert
        assert "error_analysis" in region_results[0]
        assert "user_friendly_error" not in region_results[0]
        assert "authentication_failure" not in region_results[0]
        processor.phase3_error_handler.log_execution_error.assert_not_called()

    def test_execution_error_creates_structured_log(self, processor):
        """RPROC-007: 実行エラーあり（構造化ログ記録）

        result_processor.py:L151-166 の実行エラー検出時の処理をカバー。
        """
        # Arrange
        region_results = [{"region": "us-east-1", "return_code": 1}]
        processor.error_analyzer.analyze_execution_result.return_value = {
            "has_execution_error": True,
            "error_type": "filter_error",
            "error_message": "フィルタエラー",
            "affected_policies": ["policy-a"],
            "resource_type": "ec2",
            "error_stage": "filter"
        }
        processor.phase3_error_handler.create_user_friendly_error.return_value = "エラーが発生しました"

        # Act
        processor._analyze_execution_errors(region_results)

        # Assert
        # ExecutionErrorInfoが生成されてlog_execution_errorに渡される
        processor.phase3_error_handler.log_execution_error.assert_called_once()
        error_info = processor.phase3_error_handler.log_execution_error.call_args[0][0]
        assert error_info.type == "filter_error"
        assert error_info.region == "us-east-1"
        assert error_info.return_code == 1
        # user_friendly_errorが追加される
        assert region_results[0]["user_friendly_error"] == "エラーが発生しました"

    def test_authentication_error_sets_failure_flag(self, processor):
        """RPROC-008: 認証エラー検出で特別処理

        result_processor.py:L169-174 の認証エラー特別処理をカバー。
        """
        # Arrange
        region_results = [{"region": "ap-northeast-1", "return_code": 2}]
        processor.error_analyzer.analyze_execution_result.return_value = {
            "has_execution_error": True,
            "error_type": "authentication_error",
            "error_message": "認証失敗",
            "affected_policies": [],
            "error_stage": "execution"
        }
        processor.phase3_error_handler.create_user_friendly_error.return_value = "認証エラー"

        # Act
        processor._analyze_execution_errors(region_results)

        # Assert
        # L170: authentication_failure フラグが設定される
        assert region_results[0]["authentication_failure"] is True
        # L171: 認証エラーログが出力される
        processor.logger.error.assert_called()
        assert "認証エラー" in str(processor.logger.error.call_args)
```

### 2.4 process_scan_for_history_v2 テスト

```python
class TestProcessScanForHistoryV2:
    """v2履歴データ生成テスト"""

    @pytest.mark.asyncio
    async def test_normal_v2_processing(self, processor, history_v2_setup):
        """RPROC-009: v2履歴データ正常生成

        result_processor.py:L176-322 の正常フローをカバー。
        """
        # Arrange
        scan_metadata = {
            "scan_timestamp": "2025-01-01T00:00:00Z",
            "regions": ["us-east-1"],
            "scan_type": "cspm",
            "completed_regions": 1,
            "failed_regions": 0,
            "start_time": "2025-01-01T00:00:00Z",
            "end_time": "2025-01-01T00:01:00Z",
            "duration_seconds": 60,
            "successful_regions": [{"region_name": "us-east-1"}],
            "aggregated_scan_statistics": {"total_scanned": 100, "total_violations": 5, "overall_compliance_rate": 95.0}
        }

        # Act
        result = await processor.process_scan_for_history_v2("/tmp/output", scan_metadata)

        # Assert
        assert result["job_id"] == "test-job-id"
        assert result["account_id"] == "123456789012"
        assert "basic_statistics" in result
        assert "policy_results" in result
        assert "resource_overview" in result
        assert "insights" in result
        assert "execution_summary" in result
        assert "authentication_status" in result

    @pytest.mark.asyncio
    async def test_aggregated_stats_from_scan_metadata(self, processor, history_v2_setup):
        """RPROC-010: aggregated_scan_statistics事前提供

        result_processor.py:L226-228 のscan_metadataから直接取得分岐をカバー。
        """
        # Arrange
        pre_stats = {"total_scanned": 200, "total_violations": 10, "overall_compliance_rate": 95.0}
        scan_metadata = {
            "aggregated_scan_statistics": pre_stats,
            "successful_regions": []
        }

        # Act
        result = await processor.process_scan_for_history_v2("/tmp/output", scan_metadata)

        # Assert
        # 事前提供の統計がgenerate_insightsに渡される
        call_kwargs = processor.insight_generator.generate_insights.call_args[1]
        assert call_kwargs["aggregated_scan_statistics"] == pre_stats

    @pytest.mark.asyncio
    async def test_calculate_stats_from_policy_results(self, processor, history_v2_setup):
        """RPROC-011: policy_resultsから統計計算

        result_processor.py:L228-252 のpolicy_resultsからの計算分岐をカバー。
        total_scanned > 0 (L240) の true 分岐。
        """
        # Arrange
        # aggregated_scan_statisticsなし → 計算実行
        processor.result_formatter.create_v2_policy_results = AsyncMock(return_value=[
            {"policy_name": "p1", "violation_count": 2,
             "resource_statistics": {"total_resources_scanned": 50, "resources_after_filter": 10}},
            {"policy_name": "p2", "violation_count": 0,
             "resource_statistics": {"total_resources_scanned": 30, "resources_after_filter": 5}}
        ])
        # _calculate_basic_statisticsは実行値を返す
        history_v2_setup["mock_stats"].return_value = {"total_violations": 2}
        scan_metadata = {"successful_regions": []}

        # Act
        result = await processor.process_scan_for_history_v2("/tmp/output", scan_metadata)

        # Assert
        # 統計計算が実行され、generate_insightsに計算済み統計が渡される
        call_kwargs = processor.insight_generator.generate_insights.call_args[1]
        calc_stats = call_kwargs["aggregated_scan_statistics"]
        assert calc_stats["total_scanned"] == 80  # 50 + 30
        assert calc_stats["total_evaluated"] == 15  # 10 + 5

    @pytest.mark.asyncio
    async def test_total_scanned_zero_skips_calculation(self, processor, history_v2_setup):
        """RPROC-012: total_scanned=0で統計計算スキップ

        result_processor.py:L240 の total_scanned == 0 分岐をカバー。
        """
        # Arrange
        processor.result_formatter.create_v2_policy_results = AsyncMock(return_value=[
            {"policy_name": "p1", "violation_count": 0,
             "resource_statistics": {"total_resources_scanned": 0, "resources_after_filter": 0}}
        ])
        history_v2_setup["mock_stats"].return_value = {"total_violations": 0}
        scan_metadata = {"successful_regions": []}

        # Act
        result = await processor.process_scan_for_history_v2("/tmp/output", scan_metadata)

        # Assert
        # total_scanned=0のためaggregated_scan_statisticsは空 → warningログ
        warning_calls = [c for c in processor.logger.warning.call_args_list
                         if "aggregated_scan_statistics" in str(c)]
        assert len(warning_calls) > 0

    @pytest.mark.asyncio
    async def test_successful_regions_dict_format(self, processor, history_v2_setup):
        """RPROC-013: successful_regions dict形式

        result_processor.py:L267-270 のdict形式region処理をカバー。
        """
        # Arrange
        scan_metadata = {
            "successful_regions": [
                {"region_name": "us-east-1", "status": "ok"},
                {"region_name": "eu-west-1", "status": "ok"}
            ],
            "aggregated_scan_statistics": {"total_scanned": 10}
        }

        # Act
        result = await processor.process_scan_for_history_v2("/tmp/output", scan_metadata)

        # Assert
        assert scan_metadata["regions"] == ["us-east-1", "eu-west-1"]

    @pytest.mark.asyncio
    async def test_successful_regions_str_format(self, processor, history_v2_setup):
        """RPROC-014: successful_regions str形式（旧形式）

        result_processor.py:L271-273 のstr形式region処理をカバー。
        """
        # Arrange
        scan_metadata = {
            "successful_regions": ["us-east-1", "ap-northeast-1"],
            "aggregated_scan_statistics": {"total_scanned": 10}
        }

        # Act
        result = await processor.process_scan_for_history_v2("/tmp/output", scan_metadata)

        # Assert
        assert scan_metadata["regions"] == ["us-east-1", "ap-northeast-1"]

    @pytest.mark.asyncio
    async def test_successful_regions_non_list(self, processor, history_v2_setup):
        """RPROC-015: successful_regions 非リスト

        result_processor.py:L275-276 のisinstance(successful_regions, list)=False分岐をカバー。
        """
        # Arrange
        scan_metadata = {
            "successful_regions": "invalid_format",
            "aggregated_scan_statistics": {"total_scanned": 10}
        }

        # Act
        result = await processor.process_scan_for_history_v2("/tmp/output", scan_metadata)

        # Assert
        assert scan_metadata["regions"] == []

    @pytest.mark.asyncio
    async def test_dict_region_without_region_name(self, processor, history_v2_setup):
        """RPROC-016: dict形式でregion_nameなし・空文字列（混在）

        result_processor.py:L269 のregion_name取得失敗（None/空文字列）でスキップされる分岐をカバー。
        `if region_name:` はNoneと空文字列の両方をFalseとして評価する。
        """
        # Arrange
        scan_metadata = {
            "successful_regions": [
                {"other_key": "value"},     # region_name=None（キーなし）
                {"region_name": ""},         # region_name=""（空文字列）
                {"region_name": "us-east-1"}  # 有効なregion_name
            ],
            "aggregated_scan_statistics": {"total_scanned": 10}
        }

        # Act
        result = await processor.process_scan_for_history_v2("/tmp/output", scan_metadata)

        # Assert
        # region_nameなし・空文字列のエントリはスキップされる
        assert scan_metadata["regions"] == ["us-east-1"]
```

### 2.5 _extract_account_id テスト

```python
class TestExtractAccountId:
    """アカウントID取得テスト"""

    @pytest.mark.asyncio
    async def test_direct_account_id(self, processor):
        """RPROC-017: アカウントID直接取得成功

        result_processor.py:L344-345 のscan_metadataから直接取得をカバー。
        """
        # Arrange
        scan_metadata = {"account_id": "123456789012"}

        # Act
        result = await processor._extract_account_id(scan_metadata, "/tmp/output")

        # Assert
        assert result == "123456789012"
        # region_resultsやmetadataからの取得は呼ばれない
        processor.history_manager.extract_account_id_from_region_results.assert_not_called()
        processor.history_manager.extract_account_id_from_metadata.assert_not_called()

    @pytest.mark.asyncio
    async def test_extract_from_region_results(self, processor):
        """RPROC-018: region_resultsからアカウントID取得

        result_processor.py:L349-350 のregion_resultsフォールバックをカバー。
        """
        # Arrange
        region_results = [{"region": "us-east-1", "account_id": "987654321098"}]
        scan_metadata = {"account_id": "unknown", "region_results": region_results}
        processor.history_manager.extract_account_id_from_region_results.return_value = "987654321098"

        # Act
        result = await processor._extract_account_id(scan_metadata, "/tmp/output")

        # Assert
        assert result == "987654321098"
        processor.history_manager.extract_account_id_from_region_results.assert_called_once_with(region_results)

    @pytest.mark.asyncio
    async def test_extract_from_metadata(self, processor):
        """RPROC-019: metadataからアカウントID取得

        result_processor.py:L352-353 のregion_resultsなしフォールバックをカバー。
        """
        # Arrange
        scan_metadata = {"account_id": "unknown"}
        processor.history_manager.extract_account_id_from_metadata.return_value = "111222333444"

        # Act
        result = await processor._extract_account_id(scan_metadata, "/tmp/output")

        # Assert
        assert result == "111222333444"
        processor.history_manager.extract_account_id_from_metadata.assert_called_once_with("/tmp/output")
```

### 2.6 _calculate_basic_statistics テスト

```python
class TestCalculateBasicStatistics:
    """基本統計計算テスト"""

    def test_normal_statistics_calculation(self, processor):
        """RPROC-020: 基本統計の正常計算

        result_processor.py:L357-410 の正常計算フローをカバー。
        """
        # Arrange
        policy_results = [
            {"original_policy_name": "policy-A", "policy_name": "policy-A", "violation_count": 3},
            {"original_policy_name": "policy-B", "policy_name": "policy-B", "violation_count": 0},
        ]
        scan_metadata = {"completed_regions": 1, "failed_regions": 0}
        processor.insight_generator.calculate_compliance_percentage.return_value = 50.0

        # Act
        result = processor._calculate_basic_statistics(policy_results, scan_metadata)

        # Assert
        assert result["total_violations"] == 3
        assert result["total_policies"] == 2
        assert result["total_unique_policies"] == 2
        assert result["policies_with_violations"] == 1
        assert result["policies_compliant"] == 1
        assert result["unique_policies_with_violations"] == 1
        assert result["unique_policies_compliant"] == 1
        assert result["unique_policy_compliance_percentage"] == 50.0
        assert result["total_regions"] == 1
        assert result["compliance_percentage"] == 50.0

    def test_unique_policy_deduplication(self, processor):
        """RPROC-021: ユニークポリシー重複集計

        result_processor.py:L385 の「同一ポリシーが別リージョンで重複」分岐をカバー。
        同一original_policy_nameが複数存在し、一方にのみ違反がある場合、
        unique_policy_violationsはTrueとして記録される。
        """
        # Arrange
        policy_results = [
            # policy-A: us-east-1で違反あり
            {"original_policy_name": "policy-A", "policy_name": "policy-A-us-east-1", "violation_count": 2},
            # policy-A: us-west-2で違反なし（L385: 既に辞書に存在するためFalse設定をスキップ）
            {"original_policy_name": "policy-A", "policy_name": "policy-A-us-west-2", "violation_count": 0},
            # policy-B: 違反なし（L385: 辞書に未登録のため初回False設定）
            {"original_policy_name": "policy-B", "policy_name": "policy-B-us-east-1", "violation_count": 0},
        ]
        scan_metadata = {"completed_regions": 2, "failed_regions": 0}
        processor.insight_generator.calculate_compliance_percentage.return_value = 66.7

        # Act
        result = processor._calculate_basic_statistics(policy_results, scan_metadata)

        # Assert
        assert result["total_unique_policies"] == 2
        assert result["unique_policies_with_violations"] == 1  # policy-Aのみ
        assert result["unique_policies_compliant"] == 1  # policy-Bのみ
        assert result["unique_policy_compliance_percentage"] == 50.0
        # 総実行回数は3（リージョン×ポリシー）
        assert result["total_policy_executions"] == 3

    def test_empty_policy_results_zero_division(self, processor):
        """RPROC-022: 空リスト（ゼロ除算防止）

        result_processor.py:L395 の len(unique_policies) == 0 でゼロ除算を防止する分岐をカバー。
        """
        # Arrange
        policy_results = []
        scan_metadata = {"completed_regions": 0, "failed_regions": 0}
        processor.insight_generator.calculate_compliance_percentage.return_value = 0

        # Act
        result = processor._calculate_basic_statistics(policy_results, scan_metadata)

        # Assert
        assert result["total_violations"] == 0
        assert result["total_unique_policies"] == 0
        assert result["unique_policy_compliance_percentage"] == 0
        assert result["total_regions"] == 0

    def test_empty_policy_name_skipped(self, processor):
        """RPROC-034: ポリシー名なしエントリのスキップ

        result_processor.py:L378 の if original_name: が False になる分岐をカバー。
        original_policy_name と policy_name が両方欠落・空の場合、
        ユニークポリシー集計に含まれない。
        """
        # Arrange
        policy_results = [
            {"original_policy_name": "policy-A", "policy_name": "policy-A", "violation_count": 1},
            {"violation_count": 0},  # original_policy_name/policy_name 両方欠落
            {"original_policy_name": "", "policy_name": "", "violation_count": 0},  # 空文字列
        ]
        scan_metadata = {"completed_regions": 1, "failed_regions": 0}
        processor.insight_generator.calculate_compliance_percentage.return_value = 33.3

        # Act
        result = processor._calculate_basic_statistics(policy_results, scan_metadata)

        # Assert
        # ポリシー名なしエントリはユニーク集計に含まれない
        assert result["total_unique_policies"] == 1  # policy-Aのみ
        assert result["total_policies"] == 3  # 全エントリ数
        assert result["total_violations"] == 1
```

### 2.7 認証ステータス・スキャンサマリーテスト

```python
class TestAuthenticationAndSummary:
    """認証ステータスとスキャンサマリーテスト"""

    def test_authentication_status_success(self, processor):
        """RPROC-023: 認証ステータス成功

        result_processor.py:L437 の認証エラーなし分岐をカバー。
        """
        # Arrange
        processor.phase3_error_handler.get_error_summary.return_value = {
            "has_authentication_errors": False
        }

        # Act
        result = processor._get_authentication_status()

        # Assert
        assert result == "success"

    def test_authentication_status_failed(self, processor):
        """RPROC-024: 認証ステータス失敗

        result_processor.py:L437 の認証エラーあり分岐をカバー。
        """
        # Arrange
        processor.phase3_error_handler.get_error_summary.return_value = {
            "has_authentication_errors": True
        }

        # Act
        result = processor._get_authentication_status()

        # Assert
        assert result == "failed"

    def test_create_scan_summary_normal(self, processor):
        """RPROC-025: スキャンサマリー正常生成

        result_processor.py:L454-496 のエラーなし正常パスをカバー。
        """
        # Arrange
        aggregated_result = {
            "phase3_error_summary": {"has_authentication_errors": False},
            "scan_metadata": {"fatal_error_detected": False}
        }
        basic_summary = {
            "message": "スキャン完了",
            "summary_data": {"scan_status": "completed"}
        }
        processor.result_aggregator.create_scan_summary.return_value = basic_summary

        # Act
        result = processor.create_scan_summary(aggregated_result, "aws")

        # Assert
        assert result["message"] == "スキャン完了"
        assert result["summary_data"]["scan_status"] == "completed"

    def test_create_scan_summary_auth_error(self, processor):
        """RPROC-026: 認証エラーありサマリー

        result_processor.py:L481-488 の認証エラーメッセージ更新分岐をカバー。
        """
        # Arrange
        aggregated_result = {
            "phase3_error_summary": {"has_authentication_errors": True},
            "scan_metadata": {"fatal_error_detected": False}
        }
        basic_summary = {
            "message": "元のメッセージ",
            "summary_data": {}
        }
        processor.result_aggregator.create_scan_summary.return_value = basic_summary

        # Act
        result = processor.create_scan_summary(aggregated_result, "aws")

        # Assert
        assert "認証エラー" in result["message"]
        assert result["summary_data"]["has_authentication_errors"] is True
        assert result["summary_data"]["scan_status"] == "failed"

    def test_create_scan_summary_fatal_error(self, processor):
        """RPROC-027: 致命的エラーありサマリー

        result_processor.py:L489-494 の致命的エラーメッセージ更新分岐をカバー。
        """
        # Arrange
        aggregated_result = {
            "phase3_error_summary": {"has_authentication_errors": False},
            "scan_metadata": {"fatal_error_detected": True}
        }
        basic_summary = {
            "message": "元のメッセージ",
            "summary_data": {}
        }
        processor.result_aggregator.create_scan_summary.return_value = basic_summary

        # Act
        result = processor.create_scan_summary(aggregated_result, "aws")

        # Assert
        assert "致命的エラー" in result["message"]
        assert result["summary_data"]["scan_status"] == "failed"
```

### 2.8 委譲メソッドテスト

```python
class TestDelegationMethods:
    """サブコンポーネントへの委譲テスト"""

    @pytest.mark.asyncio
    async def test_store_multi_region_results_delegates(self, processor):
        """RPROC-028: OpenSearch保存委譲

        result_processor.py:L498-519 の委譲をカバー。
        """
        # Arrange
        # 戻り値5 = 保存されたドキュメント数の総計
        processor.opensearch_manager.store_multi_region_results = AsyncMock(return_value=5)

        # Act
        result = await processor.store_multi_region_results_to_opensearch(
            region_results=[{"region": "us-east-1"}],
            scan_metadata={"key": "val"},
            cloud_provider="aws",
            custodian_output_dir="/tmp/output"
        )

        # Assert
        assert result == 5
        processor.opensearch_manager.store_multi_region_results.assert_awaited_once_with(
            [{"region": "us-east-1"}], {"key": "val"}, "aws", "/tmp/output"
        )

    def test_process_single_region_result_delegates(self, processor):
        """RPROC-029: 単一リージョン結果処理委譲

        result_processor.py:L524-547 の委譲をカバー。
        """
        # Arrange
        expected = {"region": "us-east-1", "status": "success"}
        processor.result_aggregator.process_single_region_result.return_value = expected

        # Act
        result = processor.process_single_region_result(
            "us-east-1", 0, ["stdout"], ["stderr"], 3
        )

        # Assert
        assert result == expected
        processor.result_aggregator.process_single_region_result.assert_called_once_with(
            "us-east-1", 0, ["stdout"], ["stderr"], 3
        )

    def test_create_error_result_public_delegates(self, processor):
        """RPROC-030: パブリックエラー結果生成委譲

        result_processor.py:L549-560 の委譲をカバー。
        """
        # Arrange
        expected = {"region": "us-east-1", "error": "timeout"}
        processor.result_aggregator.create_error_result.return_value = expected

        # Act
        result = processor.create_error_result("us-east-1", "timeout")

        # Assert
        assert result == expected
        processor.result_aggregator.create_error_result.assert_called_once_with(
            "us-east-1", "timeout"
        )

    def test_read_detailed_scan_results_delegates(self, processor):
        """RPROC-031: 詳細結果読み込み委譲

        result_processor.py:L562-573 の委譲をカバー。
        """
        # Arrange
        expected = {"policies": []}
        processor.file_processor.read_detailed_scan_results.return_value = expected

        # Act
        result = processor.read_detailed_scan_results("/tmp/output", "us-east-1")

        # Assert
        assert result == expected
        processor.file_processor.read_detailed_scan_results.assert_called_once_with(
            "/tmp/output", "us-east-1"
        )

    def test_create_error_result_private_delegates(self, processor):
        """RPROC-032: プライベートエラー結果生成委譲

        result_processor.py:L442-452 の委譲をカバー。
        result_formatter.create_error_resultにerror_messageとphase3_error_handlerが渡される。
        """
        # Arrange
        expected = {"error": True, "message": "処理失敗"}
        processor.result_formatter.create_error_result.return_value = expected

        # Act
        result = processor._create_error_result("処理失敗")

        # Assert
        assert result == expected
        processor.result_formatter.create_error_result.assert_called_once_with(
            "処理失敗", processor.phase3_error_handler
        )

    @pytest.mark.asyncio
    async def test_analyze_custodian_logs_normal(self, processor):
        """RPROC-033: ログ解析正常実行

        result_processor.py:L412-426 の正常パスをカバー。
        """
        # Arrange
        expected = {"policy_results": [{"name": "p1"}]}
        with patch(f"{MODULE}.analyze_multi_region_scan", return_value=expected) as mock_analyze:
            # Act
            result = await processor._analyze_custodian_logs("/tmp/output")

        # Assert
        assert result == expected
        mock_analyze.assert_called_once_with("/tmp/output", "test-job-id")
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| RPROC-E01 | ログ解析でpolicy_resultsなし | policy_results空/未設定 | エラー結果返却 |
| RPROC-E02 | v2履歴処理で例外発生 | 内部メソッドが例外送出 | エラー結果返却 |
| RPROC-E03 | _analyze_custodian_logs例外 | analyze_multi_region_scanが例外 | 空policy_results返却 |
| RPROC-E04 | _get_authentication_status例外 | get_error_summaryが例外 | "success"返却 |

### 3.1 ResultProcessor異常系テスト

```python
class TestResultProcessorErrors:
    """ResultProcessorエラーテスト"""

    @pytest.mark.asyncio
    async def test_history_v2_no_policy_results(self, processor, history_v2_setup):
        """RPROC-E01: ログ解析でpolicy_resultsなし

        result_processor.py:L197-199 のpolicy_results空チェック分岐をカバー。
        """
        # Arrange
        history_v2_setup["mock_logs"].return_value = {"policy_results": []}
        processor.result_formatter.create_error_result.return_value = {
            "error": True, "message": "ログ解析からポリシー結果が取得できません"
        }

        # Act
        result = await processor.process_scan_for_history_v2(
            "/tmp/output", {"successful_regions": []}
        )

        # Assert
        assert result["error"] is True
        processor.result_formatter.create_error_result.assert_called_once()

    @pytest.mark.asyncio
    async def test_history_v2_exception(self, processor, history_v2_setup):
        """RPROC-E02: v2履歴処理で例外発生

        result_processor.py:L324-326 のexceptブロックをカバー。
        """
        # Arrange
        history_v2_setup["mock_logs"].side_effect = RuntimeError("予期しないエラー")
        processor.result_formatter.create_error_result.return_value = {
            "error": True, "message": "予期しないエラー"
        }

        # Act
        result = await processor.process_scan_for_history_v2("/tmp/output", {})

        # Assert
        assert result["error"] is True
        processor.logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_analyze_custodian_logs_exception(self, processor):
        """RPROC-E03: _analyze_custodian_logs例外

        result_processor.py:L424-426 のexceptブロックをカバー。
        """
        # Arrange
        with patch(f"{MODULE}.analyze_multi_region_scan",
                   side_effect=Exception("解析失敗")) as mock_analyze:
            # Act
            result = await processor._analyze_custodian_logs("/tmp/output")

        # Assert
        assert result == {"policy_results": []}
        processor.logger.error.assert_called()
        # ログメッセージに例外内容が含まれる（L425: f"ログ解析エラー: {str(e)}"）
        log_msg = processor.logger.error.call_args[0][0]
        assert "ログ解析エラー" in log_msg
        assert "解析失敗" in log_msg

    def test_get_authentication_status_exception(self, processor):
        """RPROC-E04: _get_authentication_status例外

        result_processor.py:L438-440 のexceptブロックをカバー。
        現在の実装は例外時に"success"を返す（Fail-Open設計）。
        セキュリティ的にはFail-Closed（"failed"返却）が望ましいが、
        本テストは現在の実装動作を記録する。
        """
        # Arrange
        processor.phase3_error_handler.get_error_summary.side_effect = Exception("ハンドラエラー")

        # Act
        result = processor._get_authentication_status()

        # Assert
        assert result == "success"
        processor.logger.warning.assert_called()
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| RPROC-SEC-01 | エラー結果に内部情報が露出しない | 内部例外メッセージ | result_formatterに委譲（サニタイズ責務はformatter側） |
| RPROC-SEC-02 | 認証エラー情報の適切なログ記録 | 認証エラー発生 | credentials等の機密情報がログに含まれない（代表検証） |
| RPROC-SEC-03 | アカウントIDフォールバックの安全性 | 全取得ソース失敗 | "unknown"が返却される（内部例外の伝播なし） |

```python
@pytest.mark.security
class TestResultProcessorSecurity:
    """ResultProcessorセキュリティテスト"""

    def test_error_result_delegates_sanitization(self, processor):
        """RPROC-SEC-01: エラー結果に内部情報が露出しない

        _create_error_resultはresult_formatterに委譲する。
        エラーメッセージのサニタイズはresult_formatterの責務であるが、
        本メソッドが内部スタックトレース等を独自に付加しないことを確認（代表検証）。
        """
        # Arrange
        internal_error = "ConnectionError: opensearch:9200 refused (internal-host-abc123)"
        processor.result_formatter.create_error_result.return_value = {"error": True}

        # Act
        result = processor._create_error_result(internal_error)

        # Assert
        # 引数がそのままresult_formatterに渡される（独自加工なし）
        call_args = processor.result_formatter.create_error_result.call_args[0]
        assert call_args[0] == internal_error
        # 戻り値はresult_formatterの結果そのまま（内部情報の追加なし）
        assert result == {"error": True}

    def test_auth_error_log_no_credentials(self, processor):
        """RPROC-SEC-02: 認証エラー情報の適切なログ記録

        _analyze_execution_errorsで認証エラーをログに記録する際、
        credentials等の機密情報がcontextに含まれないことを確認（代表検証）。
        """
        # Arrange
        region_results = [{
            "region": "us-east-1",
            "return_code": 2,
            "credentials": {"access_key": "AKIAXXXXXXXX", "secret_key": "secret123"}
        }]
        processor.error_analyzer.analyze_execution_result.return_value = {
            "has_execution_error": True,
            "error_type": "authentication_error",
            "error_message": "認証失敗",
            "affected_policies": [],
            "error_stage": "execution"
        }
        processor.phase3_error_handler.create_user_friendly_error.return_value = "認証エラー"

        # Act
        processor._analyze_execution_errors(region_results)

        # Assert
        # ログのcontext引数に機密情報が含まれないことを確認
        for call in processor.logger.error.call_args_list:
            call_str = str(call)
            assert "AKIAXXXXXXXX" not in call_str
            assert "secret123" not in call_str

    @pytest.mark.asyncio
    async def test_account_id_fallback_safe(self, processor):
        """RPROC-SEC-03: アカウントIDフォールバックの安全性

        全取得ソースが失敗した場合でも"unknown"が返却され、
        内部例外が伝播しないことを確認。
        """
        # Arrange
        scan_metadata = {}  # account_id キーなし → .get で "unknown"
        # region_resultsも空 → metadataから取得
        processor.history_manager.extract_account_id_from_metadata.return_value = "unknown"

        # Act
        result = await processor._extract_account_id(scan_metadata, "/tmp/output")

        # Assert
        assert result == "unknown"
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_result_processor_module` | テスト間のモジュール状態リセット | function | Yes |
| `mock_components` | 全サブコンポーネントクラスのパッチ | function | No |
| `processor` | テスト用ResultProcessorインスタンス | function | No |
| `history_v2_setup` | process_scan_for_history_v2用モックセットアップ | function | No |

### 共通フィクスチャ定義

```python
# test/unit/jobs/tasks/new_custodian_scan/conftest.py に追加
import sys
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

MODULE = "app.jobs.tasks.new_custodian_scan.result_processor"

# テスト用定数（config.pyバリデーション通過に必要な最小環境変数セット）
REQUIRED_ENV_VARS = {
    "GPT5_1_CHAT_API_KEY": "test-key",
    "GPT5_1_CODEX_API_KEY": "test-key",
    "GPT5_2_API_KEY": "test-key",
    "GPT5_MINI_API_KEY": "test-key",
    "GPT5_NANO_API_KEY": "test-key",
    "CLAUDE_HAIKU_4_5_KEY": "test-key",
    "CLAUDE_SONNET_4_5_KEY": "test-key",
    "GEMINI_API": "test-key",
    "DOCKER_BASE_URL": "http://localhost:11434",
    "EMBEDDING_3_LARGE_API_KEY": "test-embedding-key",
    "OPENSEARCH_URL": "https://localhost:9200",
}


@pytest.fixture(autouse=True)
def reset_result_processor_module():
    """テストごとにモジュールのグローバル状態をリセット

    ResultProcessorは複数のサブモジュールに依存するため、
    テスト間の干渉を防ぐためモジュールキャッシュをクリアする。
    """
    yield
    modules_to_remove = [key for key in sys.modules if key.startswith("app.jobs")]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def mock_components():
    """全サブコンポーネントクラスのモックパッチ

    ResultProcessor.__init__が参照する全クラスをMagicMockに置き換える。
    各パッチの戻り値（=モックインスタンス）はprocessorの属性としてアクセス可能。
    """
    component_names = [
        "TaskLogger", "ResultAggregator", "OpenSearchManager",
        "HistoryManager", "InsightGenerator", "ResultFormatter",
        "CustodianErrorAnalyzer", "ReturnCodeAnalyzer",
        "FileProcessor", "CustodianErrorHandler"
    ]
    patches = {}
    mocks = {}
    for name in component_names:
        p = patch(f"{MODULE}.{name}")
        mocks[name] = p.start()
        patches[name] = p

    yield mocks

    for p in patches.values():
        p.stop()


@pytest.fixture
def processor(mock_components):
    """テスト用ResultProcessorインスタンス

    全サブコンポーネントがモック化された状態でインスタンスを生成。
    processor.result_aggregator, processor.opensearch_manager 等は
    MagicMockインスタンスとしてアクセス可能。
    """
    from app.jobs.tasks.new_custodian_scan.result_processor import ResultProcessor
    return ResultProcessor("test-job-id")


@pytest.fixture
def history_v2_setup(processor):
    """process_scan_for_history_v2テスト用モックセットアップ

    v2履歴処理の正常フローに必要な全モックを設定する。
    各テストでは必要なモックのみオーバーライドして使用。
    """
    # _analyze_custodian_logs モック
    mock_logs = AsyncMock(return_value={
        "policy_results": [{"policy_name": "test-policy"}],
        "scan_errors_summary": {"total_errors": 0},
        "aggregated_statistics": {}
    })

    # _extract_account_id モック
    mock_account_id = AsyncMock(return_value="123456789012")

    # 非同期サブコンポーネントモック
    processor.opensearch_manager.get_recommendation_mappings = AsyncMock(return_value={})
    processor.result_formatter.create_v2_policy_results = AsyncMock(return_value=[
        {"policy_name": "test-policy", "violation_count": 1,
         "resource_statistics": {"total_resources_scanned": 10, "resources_after_filter": 5}}
    ])

    # 同期サブコンポーネントモック
    processor.insight_generator.create_resource_overview_from_log_analysis = MagicMock(return_value={})
    processor.insight_generator.generate_insights = MagicMock(return_value=[])
    processor.insight_generator.calculate_compliance_percentage = MagicMock(return_value=90.0)

    # _get_authentication_status モック
    processor.phase3_error_handler.get_error_summary.return_value = {
        "has_authentication_errors": False
    }

    # _calculate_basic_statistics モック
    mock_stats = MagicMock(return_value={"total_violations": 1, "total_policies": 1})

    with patch.object(processor, '_analyze_custodian_logs', mock_logs), \
         patch.object(processor, '_extract_account_id', mock_account_id), \
         patch.object(processor, '_calculate_basic_statistics', mock_stats):
        yield {
            "mock_logs": mock_logs,
            "mock_account_id": mock_account_id,
            "mock_stats": mock_stats
        }
```

---

## 6. テスト実行例

```bash
# ResultProcessor関連テストのみ実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_result_processor.py -v

# 特定のテストクラスのみ実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_result_processor.py::TestProcessScanForHistoryV2 -v

# カバレッジ付きで実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_result_processor.py --cov=app.jobs.tasks.new_custodian_scan.result_processor --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_result_processor.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 34 | RPROC-001〜RPROC-034 |
| 異常系 | 4 | RPROC-E01〜RPROC-E04 |
| セキュリティ | 3 | RPROC-SEC-01〜RPROC-SEC-03 |
| **合計** | **41** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestResultProcessorInit` | RPROC-001 | 1 |
| `TestAggregateMultiRegionResults` | RPROC-002〜RPROC-005 | 4 |
| `TestAnalyzeExecutionErrors` | RPROC-006〜RPROC-008 | 3 |
| `TestProcessScanForHistoryV2` | RPROC-009〜RPROC-016 | 8 |
| `TestExtractAccountId` | RPROC-017〜RPROC-019 | 3 |
| `TestCalculateBasicStatistics` | RPROC-020〜RPROC-022, RPROC-034 | 4 |
| `TestAuthenticationAndSummary` | RPROC-023〜RPROC-027 | 5 |
| `TestDelegationMethods` | RPROC-028〜RPROC-033 | 6 |
| `TestResultProcessorErrors` | RPROC-E01〜RPROC-E04 | 4 |
| `TestResultProcessorSecurity` | RPROC-SEC-01〜RPROC-SEC-03 | 3 |

### 実装失敗が予想されるテスト

現時点で失敗が予想されるテストはありません。

### 注意事項

- `pytest-asyncio` が必要（process_scan_for_history_v2, _extract_account_id, _analyze_custodian_logs, store_multi_region_results_to_opensearch）
- `@pytest.mark.security` マーカーの登録要否（pyproject.toml）
- history_v2_setupフィクスチャは `patch.object` を使用してインスタンスメソッドを直接モックするため、processorフィクスチャと組み合わせて使用
- ExecutionErrorInfoはデータクラスのため、`call_args[0][0].type` 等で属性を直接検証

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | サブコンポーネント内部ロジックは本テスト対象外 | 委譲先の詳細動作は検証しない | 各サブコンポーネントの個別テスト仕様書で対応 |
| 2 | GLOBAL_RESOURCE_TYPESはハードコード定数 | 値の変更時にテスト修正が必要 | RPROC-001でリスト長と代表値を検証 |
| 3 | process_scan_for_history_v2は多数の依存を持つ | モック設定が複雑 | history_v2_setupフィクスチャで共通化 |
| 4 | _analyze_execution_errorsはregion_resultsを破壊的に変更 | 入力辞書が変更される副作用あり | テストで変更後の値を直接検証 |
| 5 | 依存コンポーネントの戻り構造変更を検知できない | モック中心のため、委譲先（例: `result_aggregator.create_scan_summary`）の戻り値構造が変わった場合（`summary_data`キー欠落等）、本テストでは回帰を検出できない | 結合テストまたは各サブコンポーネントのテストで戻り値スキーマを検証する。将来的にはインターフェース型定義（TypedDict等）の導入も検討 |
| 6 | `error_summary`の必須キー欠損時の挙動が未固定 | `phase3_error_handler.get_error_summary()`の戻り辞書から`has_authentication_errors`等を`.get()`で取得しているが、キー自体が欠損した場合のデフォルト値依存がテストで明示されていない。ログ出力時に`error_summary["authentication_errors"]`等の直接参照（L103-105）がKeyErrorを起こす可能性がある | `error_summary`が不完全な辞書の場合の防御テスト追加、または実装側で`.get()`に統一する修正を検討 |
