# jobs/tasks/new_custodian_scan/results 結果フォーマット テストケース

## 1. 概要

`results/` サブディレクトリの結果フォーマットファイル（`result_formatter.py`）のテスト仕様書。v2マッピング仕様準拠のフォーマット・ポリシー結果変換・ステータス判定・エラー結果作成を担う。

### 1.1 対象クラス

| クラス | ファイル | 行数 | 責務 |
|--------|---------|------|------|
| `ResultFormatter` | `result_formatter.py` | 898 | スキャン結果のフォーマット・変換・ステータス判定・エラー構造化 |

### 1.2 カバレッジ目標: 85%

> **注記**: asyncメソッドは `create_v2_policy_results` と `_map_policy_name` の2件のみ。残り14メソッドはすべて同期。外部依存（TaskLogger、PolicyStatusDeterminer）はモック、opensearch_manager は引数として渡されるため AsyncMock で対応。ValidationErrorInfo は L302 で遅延importされる。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/jobs/tasks/new_custodian_scan/results/result_formatter.py` |
| テストコード | `test/unit/results/test_result_formatter.py`（既存ファイルを拡張） |

### 1.4 依存関係

```
result_formatter.py
├── app.jobs.common.logging.TaskLogger          # ログ出力
├── ..log_analyzer.PolicyStatusDeterminer       # リソーススコープ判定
└── ....common.error_handling.ValidationErrorInfo  # 遅延import (L302)
```

### 1.5 主要分岐マップ

| メソッド | 分岐数 | 主要条件 |
|---------|--------|---------|
| `create_v2_policy_results` | 4 | L60 recommendation_uuid有無, L67 version不足, L127 error_details |
| `_map_policy_name` | 4 | L155 uuid+mappings, L157 policy-prefix, L160 empty title |
| `determine_policy_status_japanese` | 5 | L183 error, L187 total=0, L191 適合, L195 違反, L197 検算 |
| `calculate_compliance_rate` | 3 | L222 total=0 + violation判定, L225 通常計算 |
| `generate_resource_overview` | 3 | L257 新規type, L269 global, L276 regional |
| `create_error_result` | 1 | L302 遅延import |
| `create_execution_summary` | 15 | L384 空判定, L399-412 metrics分類, L423-434 実行判定, L442-458 違反集計, L464-486 リージョン判定 |
| `create_policy_executions` | 10 | L590 空, L598 名前なし, L601/613 新規/既存, L621-637 整合性警告, L662-669 全体status |
| `_get_failure_reason_japanese` | 13 | L815-846 stage×condition 3段階ネスト |
| `_generate_error_insights_japanese` | 10 | L869-894 stage×condition + 汎用推奨 |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| RF-001 | __init__ 初期化 | job_id="test-job" | logger, status_determiner 初期化 |
| RF-002 | create_v2_policy_results metadata有り | uuid有りポリシー | v2_policy構造体 |
| RF-003 | create_v2_policy_results version不足警告 | uuid有り+version=None | warning出力 |
| RF-004 | create_v2_policy_results OpenSearchフォールバック | uuid無しポリシー | OpenSearch取得 |
| RF-005 | create_v2_policy_results エラー詳細付与 | error_occurred=True | error_details追加 |
| RF-006 | create_v2_policy_results 空リスト | [] | [] |
| RF-007 | _map_policy_name uuid+mappings一致 | uuid in mappings | mappings title |
| RF-008 | _map_policy_name policy-prefix | policy-で始まるname | OpenSearch title |
| RF-009 | _map_policy_name policy-prefix空title | OpenSearch空title | original_name |
| RF-010 | _map_policy_name マッチなし | uuid無し+prefix無し | original_name |
| RF-011 | status判定 エラー | error_occurred=True | "エラー" |
| RF-012 | status判定 リソースなし | total=0 | "リソースなし" |
| RF-013 | status判定 適合 | total=5, violation=0 | "適合" |
| RF-014 | status判定 違反あり | total=5, violation=2 | "違反あり" |
| RF-015 | status判定 検算エラー | violation>total | "違反あり"+warning |
| RF-016 | compliance_rate total=0 violation=0 | 0, 0 | 100.0 |
| RF-017 | compliance_rate total=0 violation>0 | 5, 0 | 0.0 |
| RF-018 | compliance_rate 通常計算 | 3, 10 | 70.0 |
| RF-019 | resource_overview 空 | [] | 空構造 |
| RF-020 | resource_overview global+regional分類 | global+regionalポリシー | 分類結果 |
| RF-021 | resource_overview type集計 | 同一typeの複数ポリシー | 集計結果 |
| RF-022 | create_error_result 構造 | error_message | エラー構造体 |
| RF-023 | scan_errors_summary 固定値 | なし | 固定構造体 |
| RF-024 | execution_summary 空 | [] | 空summary |
| RF-025 | execution_summary policy_metrics | 複数ポリシー | metrics計算 |
| RF-026 | execution_summary execution_metrics | 違反+エラー+適合 | 各カウント |
| RF-027 | execution_summary violation_metrics | severity別 | by_severity集計 |
| RF-028 | execution_summary regional_metrics | 複数リージョン | region別集計 |
| RF-029 | execution_summary resource_metrics | リソース統計 | coverage計算 |
| RF-030 | policy_executions 空 | [] | [] |
| RF-031 | policy_executions 単一ポリシー | 1ポリシー1リージョン | 1グループ |
| RF-032 | policy_executions マルチリージョン | 同ポリシー2リージョン | regional_results=2 |
| RF-033 | policy_executions 名前なしスキップ | original_name="" | スキップ |
| RF-034 | policy_executions 整合性警告 | 異なるuuid | logger.warning |
| RF-035 | policy_executions 全体status4パターン | エラー/なし/違反/適合 | 各status |
| RF-036 | insights_summary デフォルト | 引数なし | デフォルト構造 |
| RF-037 | insights_summary カスタム | 全引数指定 | カスタム構造 |
| RF-038 | error_execution_summary | error+stage | エラー構造+error_context |
| RF-039 | error_insights_summary | error+stage | エラーinsights |
| RF-040 | failure_reason validation | 各sub-condition | 日本語メッセージ |
| RF-041 | failure_reason credential | 各sub-condition | 日本語メッセージ |
| RF-042 | failure_reason execution | 各sub-condition | 日本語メッセージ |
| RF-043 | failure_reason 未知stage | unknown | デフォルトメッセージ |
| RF-044 | error_insights validation | account_id/region/policy | insightsリスト |
| RF-045 | error_insights credential | assumerole/token | insightsリスト |
| RF-046 | error_insights execution | timeout/network | insightsリスト |
| RF-047 | error_insights 未知stage | unknown | デフォルト+一般推奨 |

### 2.1 初期化テスト

```python
# test/unit/results/test_result_formatter.py（既存ファイルを拡張）
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

RF_MODULE = "app.jobs.tasks.new_custodian_scan.results.result_formatter"
ERROR_HANDLING_MODULE = "app.jobs.common.error_handling"


class TestResultFormatterInit:
    """ResultFormatter初期化テスト"""

    def test_init(self, result_formatter):
        """RF-001: __init__ 基本初期化

        result_formatter.py:L21-30 の初期化をカバー。
        job_id, logger, status_determiner が正しく設定される。
        """
        # Arrange — fixture で生成済み

        # Act — 初期化は fixture 内で完了

        # Assert
        assert result_formatter.job_id == "test-job-id"
        assert result_formatter.logger is not None
        assert result_formatter.status_determiner is not None
```

### 2.2 create_v2_policy_results テスト

```python
@pytest.mark.asyncio
class TestCreateV2PolicyResults:
    """v2ポリシー結果作成テスト"""

    async def test_with_metadata(self, result_formatter, mock_opensearch_manager):
        """RF-002: create_v2_policy_results metadata有り

        result_formatter.py:L60 のif recommendation_uuid成立パスをカバー。
        metadataからuuid/version/severityが直接取得される。
        """
        # Arrange
        policy_results = [{
            "policy_name": "policy-test-1",
            "metadata": {
                "recommendation_uuid": "uuid-abc",
                "recommendation_version": "1.0",
                "policy_version": "2.0",
                "severity": "High"
            },
            "resource_type": "aws.ec2",
            "region": "us-east-1",
            "violation_count": 3,
            "resource_statistics": {"total_resources_scanned": 10, "resources_after_filter": 8},
            "execution_details": {"execution_duration": 1.5},
            "error_details": {"error_occurred": False}
        }]
        mappings = {"uuid-abc": {"title": "テスト推奨事項"}}

        # Act
        results = await result_formatter.create_v2_policy_results(
            policy_results, mappings, mock_opensearch_manager
        )

        # Assert
        assert len(results) == 1
        assert results[0]["recommendation_uuid"] == "uuid-abc"
        assert results[0]["severity"] == "High"
        assert results[0]["recommendation_version"] == "1.0"
        assert results[0]["policy_version"] == "2.0"
        assert results[0]["policy_name"] == "テスト推奨事項"

    async def test_metadata_version_warning(self, result_formatter, mock_opensearch_manager):
        """RF-003: create_v2_policy_results version不足警告

        result_formatter.py:L67 のif recommendation_version is None or policy_version is None
        成立をカバー。logger.warningが出力される。
        """
        # Arrange
        policy_results = [{
            "policy_name": "policy-test-1",
            "metadata": {
                "recommendation_uuid": "uuid-abc",
                # recommendation_version と policy_version が欠落
                "severity": "Medium"
            },
            "resource_type": "aws.s3",
            "region": "us-east-1",
            "violation_count": 0,
            "resource_statistics": {"total_resources_scanned": 5, "resources_after_filter": 5},
            "execution_details": {"execution_duration": 0.5},
            "error_details": {"error_occurred": False}
        }]
        mappings = {"uuid-abc": {"title": "S3推奨"}}

        # Act
        results = await result_formatter.create_v2_policy_results(
            policy_results, mappings, mock_opensearch_manager
        )

        # Assert
        assert len(results) == 1
        assert results[0]["recommendation_version"] is None
        assert results[0]["policy_version"] is None
        result_formatter.logger.warning.assert_called_once()

    async def test_opensearch_fallback(self, result_formatter, mock_opensearch_manager):
        """RF-004: create_v2_policy_results OpenSearchフォールバック

        result_formatter.py:L72 のelse分岐（recommendation_uuid無し）をカバー。
        OpenSearchからuuidとseverityを取得する。
        """
        # Arrange
        policy_results = [{
            "policy_name": "policy-test-1",
            "metadata": {},  # recommendation_uuid なし
            "resource_type": "aws.ec2",
            "region": "us-east-1",
            "violation_count": 1,
            "resource_statistics": {"total_resources_scanned": 10, "resources_after_filter": 8},
            "execution_details": {"execution_duration": 1.0},
            "error_details": {"error_occurred": False}
        }]
        mock_opensearch_manager.extract_recommendation_uuid.return_value = "uuid-from-os"
        mock_opensearch_manager.extract_severity.return_value = "Critical"
        mappings = {}

        # Act
        results = await result_formatter.create_v2_policy_results(
            policy_results, mappings, mock_opensearch_manager
        )

        # Assert
        assert results[0]["recommendation_uuid"] == "uuid-from-os"
        assert results[0]["severity"] == "Critical"
        assert results[0]["recommendation_version"] is None
        assert results[0]["policy_version"] is None
        mock_opensearch_manager.extract_recommendation_uuid.assert_called_once()

    async def test_error_details_appended(self, result_formatter, mock_opensearch_manager):
        """RF-005: create_v2_policy_results エラー詳細付与

        result_formatter.py:L127 のif error_occurred成立パスをカバー。
        v2_policyにerror_detailsが追加される。
        """
        # Arrange
        error_details = {"error_occurred": True, "error_type": "PermissionError"}
        policy_results = [{
            "policy_name": "policy-test-1",
            "metadata": {"recommendation_uuid": "uuid-1", "severity": "Medium",
                         "recommendation_version": "1.0", "policy_version": "1.0"},
            "resource_type": "aws.iam",
            "region": "us-east-1",
            "violation_count": 0,
            "resource_statistics": {"total_resources_scanned": 0, "resources_after_filter": 0},
            "execution_details": {"execution_duration": 0.0},
            "error_details": error_details
        }]
        mappings = {}

        # Act
        results = await result_formatter.create_v2_policy_results(
            policy_results, mappings, mock_opensearch_manager
        )

        # Assert
        assert "error_details" in results[0]
        assert results[0]["error_details"]["error_type"] == "PermissionError"

    async def test_empty_list(self, result_formatter, mock_opensearch_manager):
        """RF-006: create_v2_policy_results 空リスト

        result_formatter.py:L51 のforループが0回実行をカバー。
        """
        # Arrange / Act
        results = await result_formatter.create_v2_policy_results(
            [], {}, mock_opensearch_manager
        )

        # Assert
        assert results == []
```

### 2.3 _map_policy_name テスト

```python
@pytest.mark.asyncio
class TestMapPolicyName:
    """ポリシー名マッピングテスト"""

    async def test_uuid_in_mappings(self, result_formatter, mock_opensearch_manager):
        """RF-007: _map_policy_name uuid+mappings一致

        result_formatter.py:L155 のif成立パスをカバー。
        mappingsからtitleを取得。
        """
        # Arrange
        mappings = {"uuid-abc": {"title": "推奨事項タイトル"}}

        # Act
        name = await result_formatter._map_policy_name(
            "policy-test", "uuid-abc", mappings, mock_opensearch_manager
        )

        # Assert
        assert name == "推奨事項タイトル"

    async def test_policy_prefix_opensearch(self, result_formatter, mock_opensearch_manager):
        """RF-008: _map_policy_name policy-prefix OpenSearch取得

        result_formatter.py:L157-159 のelif成立パスをカバー。
        policy-で始まるがmappingsに無い→OpenSearchから取得。
        """
        # Arrange
        mock_opensearch_manager.get_recommendation_title_from_policy_name.return_value = "OS取得タイトル"

        # Act
        name = await result_formatter._map_policy_name(
            "policy-test-1", None, {}, mock_opensearch_manager
        )

        # Assert
        assert name == "OS取得タイトル"

    async def test_policy_prefix_empty_title(self, result_formatter, mock_opensearch_manager):
        """RF-009: _map_policy_name policy-prefix空titleフォールバック

        result_formatter.py:L160-161 のif not display_policy_name成立をカバー。
        OpenSearchから空文字が返された場合、元のポリシー名にフォールバック。
        """
        # Arrange
        mock_opensearch_manager.get_recommendation_title_from_policy_name.return_value = ""

        # Act
        name = await result_formatter._map_policy_name(
            "policy-test-1", None, {}, mock_opensearch_manager
        )

        # Assert
        assert name == "policy-test-1"

    async def test_no_match(self, result_formatter, mock_opensearch_manager):
        """RF-010: _map_policy_name マッチなし

        result_formatter.py:L155,157 のいずれも不成立パスをカバー。
        uuid無し、policy-で始まらない→元のポリシー名をそのまま返す。
        """
        # Arrange / Act
        name = await result_formatter._map_policy_name(
            "custom-rule-1", None, {}, mock_opensearch_manager
        )

        # Assert
        assert name == "custom-rule-1"
```

### 2.4 determine_policy_status_japanese テスト

```python
class TestDeterminePolicyStatusJapanese:
    """ポリシーステータス判定テスト"""

    def test_error(self, result_formatter):
        """RF-011: status判定 エラー

        result_formatter.py:L183 のif error_occurred成立→"エラー"をカバー。
        """
        # Arrange / Act
        status = result_formatter.determine_policy_status_japanese(10, 0, True)

        # Assert
        assert status == "エラー"

    def test_no_resources(self, result_formatter):
        """RF-012: status判定 リソースなし

        result_formatter.py:L187 のif total_resources_scanned==0→"リソースなし"をカバー。
        """
        # Arrange / Act
        status = result_formatter.determine_policy_status_japanese(0, 0, False)

        # Assert
        assert status == "リソースなし"

    def test_compliant(self, result_formatter):
        """RF-013: status判定 適合

        result_formatter.py:L191 のif total>0 and violation==0→"適合"をカバー。
        """
        # Arrange / Act
        status = result_formatter.determine_policy_status_japanese(5, 0, False)

        # Assert
        assert status == "適合"

    def test_violation(self, result_formatter):
        """RF-014: status判定 違反あり

        result_formatter.py:L195 のif violation_count>0→"違反あり"をカバー。
        """
        # Arrange / Act
        status = result_formatter.determine_policy_status_japanese(5, 2, False)

        # Assert
        assert status == "違反あり"

    def test_violation_exceeds_total_warning(self, result_formatter):
        """RF-015: status判定 検算エラー警告

        result_formatter.py:L197 のif violation_count>total成立→warning+「違反あり」をカバー。
        """
        # Arrange / Act
        status = result_formatter.determine_policy_status_japanese(5, 10, False)

        # Assert
        assert status == "違反あり"
        result_formatter.logger.warning.assert_called_once()
```

### 2.5 calculate_compliance_rate テスト

```python
class TestCalculateComplianceRate:
    """コンプライアンス率計算テスト"""

    def test_zero_total_zero_violation(self, result_formatter):
        """RF-016: compliance_rate total=0, violation=0→100.0

        result_formatter.py:L222-223 のif total==0 and violation==0→100.0をカバー。
        """
        # Arrange / Act
        rate = result_formatter.calculate_compliance_rate(0, 0)

        # Assert
        assert rate == 100.0

    def test_zero_total_with_violation(self, result_formatter):
        """RF-017: compliance_rate total=0, violation>0→0.0

        result_formatter.py:L223 のelse→0.0をカバー。
        引数順: calculate_compliance_rate(violation_count, total_resources)
        """
        # Arrange / Act
        rate = result_formatter.calculate_compliance_rate(5, 0)  # violation=5, total=0

        # Assert
        assert rate == 0.0

    def test_normal_calculation(self, result_formatter):
        """RF-018: compliance_rate 通常計算

        result_formatter.py:L225-226 の通常計算をカバー。
        (10 - 3) / 10 * 100 = 70.0
        """
        # Arrange / Act
        rate = result_formatter.calculate_compliance_rate(3, 10)

        # Assert
        assert rate == 70.0
```

### 2.6 generate_resource_overview テスト

```python
class TestGenerateResourceOverview:
    """リソース概要生成テスト"""

    def test_empty(self, result_formatter):
        """RF-019: resource_overview 空リスト

        result_formatter.py:L248 のforループ0回実行をカバー。
        """
        # Arrange / Act
        overview = result_formatter.generate_resource_overview([])

        # Assert
        assert overview["global_resources"] == []
        assert overview["regional_resources"] == []
        assert overview["resource_by_type"] == []

    def test_global_and_regional(self, result_formatter):
        """RF-020: resource_overview global+regional分類

        result_formatter.py:L269 のscope=="global"とL276 のelse分岐をカバー。
        """
        # Arrange
        policies = [
            {
                "resource_type": "aws.iam",
                "execution_details": {"resource_scope": "global"},
                "resource_statistics": {"total_resources_scanned": 10, "violation_count": 2},
                "region": "us-east-1"
            },
            {
                "resource_type": "aws.ec2",
                "execution_details": {"resource_scope": "regional"},
                "resource_statistics": {"total_resources_scanned": 5, "violation_count": 1},
                "region": "us-east-1"
            }
        ]

        # Act
        overview = result_formatter.generate_resource_overview(policies)

        # Assert
        assert len(overview["global_resources"]) == 1
        assert overview["global_resources"][0]["resource_type"] == "aws.iam"
        assert len(overview["regional_resources"]) == 1
        assert overview["regional_resources"][0]["resource_type"] == "aws.ec2"

    def test_resource_by_type_aggregation(self, result_formatter):
        """RF-021: resource_overview type集計

        result_formatter.py:L257-266 のresource_by_type集計ロジックをカバー。
        同一resource_typeの複数ポリシーが合算される。
        """
        # Arrange
        policies = [
            {
                "resource_type": "aws.ec2",
                "execution_details": {"resource_scope": "regional"},
                "resource_statistics": {"total_resources_scanned": 5, "violation_count": 1},
                "region": "us-east-1"
            },
            {
                "resource_type": "aws.ec2",
                "execution_details": {"resource_scope": "regional"},
                "resource_statistics": {"total_resources_scanned": 3, "violation_count": 2},
                "region": "eu-west-1"
            }
        ]

        # Act
        overview = result_formatter.generate_resource_overview(policies)

        # Assert
        assert len(overview["resource_by_type"]) == 1
        assert overview["resource_by_type"][0]["total_resources"] == 8
        assert overview["resource_by_type"][0]["total_violations"] == 3
```

### 2.7 create_error_result テスト

```python
class TestCreateErrorResult:
    """エラー結果作成テスト"""

    def test_basic_structure(self, result_formatter, mock_error_handler):
        """RF-022: create_error_result 基本構造

        result_formatter.py:L290-352 の構造化エラー結果作成をカバー。
        ValidationErrorInfo遅延import (L302) を含む。
        """
        # Arrange — mock_error_handler fixture で対応

        # Act — ValidationErrorInfoは遅延import (L302) のためソースモジュールをパッチ
        with patch(f"{ERROR_HANDLING_MODULE}.ValidationErrorInfo") as mock_vei:
            result = result_formatter.create_error_result("テストエラー", mock_error_handler)

        # Assert
        assert result["job_id"] == "test-job-id"
        assert result["account_id"] == "unknown"
        assert result["basic_statistics"]["total_violations"] == 0
        assert result["policy_results"] == []
        assert result["execution_summary"]["error"] == "テストエラー"
        assert result["scan_errors_summary"]["total_errors"] == 1
        mock_error_handler.log_validation_error.assert_called_once()
        mock_error_handler.create_user_friendly_error.assert_called_once()
```

### 2.8 create_scan_errors_summary テスト

```python
class TestCreateScanErrorsSummary:
    """スキャンエラーサマリーテスト"""

    def test_static_return(self, result_formatter):
        """RF-023: scan_errors_summary 固定値返却

        result_formatter.py:L354-365 の固定構造体をカバー。
        """
        # Arrange / Act
        summary = result_formatter.create_scan_errors_summary()

        # Assert
        assert summary["total_errors"] == 0
        assert summary["errors_by_type"] == {}
        assert summary["failed_policies"] == []
```

### 2.9 create_execution_summary テスト

```python
class TestCreateExecutionSummary:
    """実行サマリー生成テスト"""

    def test_empty_returns_empty_summary(self, result_formatter):
        """RF-024: execution_summary 空→空summary

        result_formatter.py:L384 のif not policy_results→_create_empty_execution_summaryをカバー。
        """
        # Arrange / Act
        summary = result_formatter.create_execution_summary({}, [])

        # Assert
        assert summary["policy_metrics"]["unique_policies_count"] == 0
        assert summary["execution_metrics"]["total_executions"] == 0
        assert summary["resource_metrics"]["total_resources_scanned"] == 0

    def test_policy_metrics(self, result_formatter):
        """RF-025: execution_summary policy_metrics計算

        result_formatter.py:L395-412 のLoop1をカバー。
        unique_policies, global/regional分類, ステータス分類。
        """
        # Arrange
        policies = [
            {
                "original_policy_name": "policy-a",
                "execution_details": {"resource_scope": "global", "has_resources": True},
                "violation_count": 0,
                "error_details": {"error_occurred": False},
                "resource_statistics": {"total_resources_scanned": 5, "resources_after_filter": 5},
                "severity": "Medium", "resource_type": "", "region": ""
            },
            {
                "original_policy_name": "policy-b",
                "execution_details": {"resource_scope": "regional", "has_resources": True},
                "violation_count": 2,
                "error_details": {"error_occurred": False},
                "resource_statistics": {"total_resources_scanned": 10, "resources_after_filter": 8},
                "severity": "High", "resource_type": "aws.ec2", "region": "us-east-1"
            }
        ]

        # Act
        summary = result_formatter.create_execution_summary(
            {"total_violations": 2}, policies
        )

        # Assert
        pm = summary["policy_metrics"]
        assert pm["unique_policies_count"] == 2
        assert pm["global_policies"] == 1
        assert pm["regional_policies"] == 1
        assert pm["policies_compliant"] == 1
        assert pm["policies_with_violations"] == 1

    def test_execution_metrics(self, result_formatter):
        """RF-026: execution_summary execution_metrics計算

        result_formatter.py:L421-434 のLoop2をカバー。
        エラー/適合/違反/リソースなしの各カウント。
        """
        # Arrange
        policies = [
            {  # 成功+適合
                "original_policy_name": "p1",
                "execution_details": {"resource_scope": "regional", "has_resources": True},
                "violation_count": 0,
                "error_details": {"error_occurred": False},
                "resource_statistics": {"total_resources_scanned": 5, "resources_after_filter": 5},
                "severity": "Medium", "resource_type": "", "region": ""
            },
            {  # 成功+違反
                "original_policy_name": "p2",
                "execution_details": {"resource_scope": "regional", "has_resources": True},
                "violation_count": 3,
                "error_details": {"error_occurred": False},
                "resource_statistics": {"total_resources_scanned": 10, "resources_after_filter": 8},
                "severity": "High", "resource_type": "", "region": ""
            },
            {  # エラー
                "original_policy_name": "p3",
                "execution_details": {"resource_scope": "regional", "has_resources": False},
                "violation_count": 0,
                "error_details": {"error_occurred": True},
                "resource_statistics": {"total_resources_scanned": 0, "resources_after_filter": 0},
                "severity": "Medium", "resource_type": "", "region": ""
            },
            {  # 成功+リソースなし
                "original_policy_name": "p4",
                "execution_details": {"resource_scope": "regional", "has_resources": False},
                "violation_count": 0,
                "error_details": {"error_occurred": False},
                "resource_statistics": {"total_resources_scanned": 0, "resources_after_filter": 0},
                "severity": "Medium", "resource_type": "", "region": ""
            }
        ]

        # Act
        summary = result_formatter.create_execution_summary(
            {"total_violations": 3}, policies
        )

        # Assert
        em = summary["execution_metrics"]
        assert em["total_executions"] == 4
        assert em["successful_executions"] == 3
        assert em["failed_executions"] == 1
        assert em["compliant_executions"] == 1
        assert em["violation_executions"] == 1
        assert em["no_resource_executions"] == 1
        assert em["success_rate"] == 75.0

    def test_violation_metrics(self, result_formatter):
        """RF-027: execution_summary violation_metrics計算

        result_formatter.py:L441-458 のLoop3をカバー。
        severity別・resource_type別の集計。
        """
        # Arrange
        policies = [
            {
                "original_policy_name": "p1", "violation_count": 3, "severity": "High",
                "resource_type": "aws.ec2", "region": "",
                "execution_details": {"resource_scope": "regional", "has_resources": True},
                "error_details": {"error_occurred": False},
                "resource_statistics": {"total_resources_scanned": 10, "resources_after_filter": 8}
            },
            {
                "original_policy_name": "p2", "violation_count": 1, "severity": "Critical",
                "resource_type": "aws.s3", "region": "",
                "execution_details": {"resource_scope": "regional", "has_resources": True},
                "error_details": {"error_occurred": False},
                "resource_statistics": {"total_resources_scanned": 5, "resources_after_filter": 5}
            }
        ]

        # Act
        summary = result_formatter.create_execution_summary(
            {"total_violations": 4}, policies
        )

        # Assert
        vm = summary["violation_metrics"]
        assert vm["total_violation_count"] == 4
        assert vm["unique_violating_policies"] == 2
        assert vm["by_severity"]["high"] == 3
        assert vm["by_severity"]["critical"] == 1
        assert len(vm["by_resource_type"]) == 2

    def test_regional_metrics(self, result_formatter):
        """RF-028: execution_summary regional_metrics計算

        result_formatter.py:L462-486 のLoop4をカバー。
        リージョン別の実行/違反/適合/エラー集計。
        """
        # Arrange
        policies = [
            {
                "original_policy_name": "p1", "region": "us-east-1",
                "violation_count": 2,
                "execution_details": {"resource_scope": "regional", "has_resources": True},
                "error_details": {"error_occurred": False},
                "resource_statistics": {"total_resources_scanned": 10, "resources_after_filter": 8},
                "severity": "High", "resource_type": "aws.ec2"
            },
            {
                "original_policy_name": "p2", "region": "us-east-1",
                "violation_count": 0,
                "execution_details": {"resource_scope": "regional", "has_resources": True},
                "error_details": {"error_occurred": False},
                "resource_statistics": {"total_resources_scanned": 5, "resources_after_filter": 5},
                "severity": "Medium", "resource_type": "aws.s3"
            }
        ]

        # Act
        summary = result_formatter.create_execution_summary(
            {"total_violations": 2}, policies
        )

        # Assert
        rm = summary["regional_metrics"]
        assert len(rm) == 1
        assert rm[0]["region"] == "us-east-1"
        assert rm[0]["executions"] == 2
        assert rm[0]["violations"] == 1
        assert rm[0]["compliant"] == 1

    def test_resource_metrics(self, result_formatter):
        """RF-029: execution_summary resource_metrics計算

        result_formatter.py:L489-530 のresource_metricsとcoverage_percentageをカバー。
        """
        # Arrange
        policies = [
            {
                "original_policy_name": "p1", "region": "",
                "violation_count": 0,
                "execution_details": {"resource_scope": "regional", "has_resources": True},
                "error_details": {"error_occurred": False},
                "resource_statistics": {"total_resources_scanned": 100, "resources_after_filter": 80},
                "severity": "Medium", "resource_type": ""
            }
        ]

        # Act
        summary = result_formatter.create_execution_summary(
            {"total_violations": 0}, policies
        )

        # Assert
        rsm = summary["resource_metrics"]
        assert rsm["total_resources_scanned"] == 100
        assert rsm["total_resources_evaluated"] == 80
        assert rsm["coverage_percentage"] == 80.0
```

### 2.10 create_policy_executions テスト

```python
class TestCreatePolicyExecutions:
    """ポリシー実行グループ化テスト"""

    def test_empty(self, result_formatter):
        """RF-030: policy_executions 空→[]

        result_formatter.py:L590 のif not policy_results→[]をカバー。
        """
        # Arrange / Act
        executions = result_formatter.create_policy_executions([])

        # Assert
        assert executions == []

    def test_single_policy_single_region(self, result_formatter):
        """RF-031: policy_executions 単一ポリシー

        result_formatter.py:L601 のif original_name not in policy_groups→新規作成をカバー。
        """
        # Arrange
        policies = [{
            "original_policy_name": "policy-a",
            "policy_name": "ポリシーA",
            "recommendation_uuid": "uuid-1",
            "recommendation_version": "1.0",
            "policy_version": "2.0",
            "severity": "High",
            "resource_type": "aws.ec2",
            "region": "us-east-1",
            "status": "適合",
            "violation_count": 0,
            "resource_statistics": {"total_resources_scanned": 5, "resources_after_filter": 5, "compliance_rate": 100.0},
            "execution_details": {"execution_duration": 1.0, "has_resources": True, "is_compliant": True, "resource_scope": "regional"}
        }]

        # Act
        executions = result_formatter.create_policy_executions(policies)

        # Assert
        assert len(executions) == 1
        assert executions[0]["policy_name"] == "ポリシーA"
        assert executions[0]["overall_status"] == "適合"
        assert len(executions[0]["regional_results"]) == 1

    def test_multi_region_grouping(self, result_formatter):
        """RF-032: policy_executions マルチリージョングループ化

        result_formatter.py:L613 のelse分岐（既存グループに追加）をカバー。
        同じoriginal_policy_nameが1つのグループにまとめられる。
        """
        # Arrange
        base = {
            "original_policy_name": "policy-a",
            "policy_name": "ポリシーA",
            "recommendation_uuid": "uuid-1",
            "recommendation_version": "1.0",
            "policy_version": "2.0",
            "severity": "High",
            "resource_type": "aws.ec2",
            "status": "適合",
            "violation_count": 0,
            "resource_statistics": {"total_resources_scanned": 5, "resources_after_filter": 5, "compliance_rate": 100.0},
            "execution_details": {"execution_duration": 1.0, "has_resources": True, "is_compliant": True, "resource_scope": "regional"}
        }
        policies = [
            {**base, "region": "us-east-1"},
            {**base, "region": "eu-west-1", "violation_count": 2}
        ]

        # Act
        executions = result_formatter.create_policy_executions(policies)

        # Assert
        assert len(executions) == 1
        assert len(executions[0]["regional_results"]) == 2
        assert executions[0]["total_violations"] == 2

    def test_empty_name_skip(self, result_formatter):
        """RF-033: policy_executions 空名前スキップ

        result_formatter.py:L598 のif not original_name→continueをカバー。
        """
        # Arrange
        policies = [{"original_policy_name": "", "policy_name": "", "region": "us-east-1"}]

        # Act
        executions = result_formatter.create_policy_executions(policies)

        # Assert
        assert executions == []

    def test_consistency_warning(self, result_formatter):
        """RF-034: policy_executions 整合性警告

        result_formatter.py:L621 のif current_uuid != existing→warning出力をカバー。
        """
        # Arrange
        base = {
            "original_policy_name": "policy-a", "policy_name": "A",
            "severity": "Medium", "resource_type": "aws.ec2",
            "status": "適合", "violation_count": 0,
            "resource_statistics": {"total_resources_scanned": 5, "resources_after_filter": 5, "compliance_rate": 100.0},
            "execution_details": {"execution_duration": 1.0, "has_resources": True, "is_compliant": True, "resource_scope": "regional"}
        }
        policies = [
            {**base, "region": "us-east-1", "recommendation_uuid": "uuid-1",
             "recommendation_version": "1.0", "policy_version": "1.0"},
            {**base, "region": "eu-west-1", "recommendation_uuid": "uuid-2",
             "recommendation_version": "2.0", "policy_version": "2.0"}
        ]

        # Act
        result_formatter.create_policy_executions(policies)

        # Assert — uuid, rec_version, policy_version の3回warning
        assert result_formatter.logger.warning.call_count == 3

    def test_overall_status_all_patterns(self, result_formatter):
        """RF-035: policy_executions 全体status4パターン

        result_formatter.py:L662-669 の4分岐（エラー/リソースなし/違反/適合）をカバー。
        """
        # Arrange
        def make_policy(name, status, violation, has_resources):
            return {
                "original_policy_name": name, "policy_name": name,
                "recommendation_uuid": None, "recommendation_version": None,
                "policy_version": None, "severity": "Medium",
                "resource_type": "aws.ec2", "region": "us-east-1",
                "status": status, "violation_count": violation,
                "resource_statistics": {"total_resources_scanned": 5 if has_resources else 0,
                                        "resources_after_filter": 5 if has_resources else 0,
                                        "compliance_rate": 100.0},
                "execution_details": {"execution_duration": 1.0, "has_resources": has_resources,
                                      "is_compliant": violation == 0, "resource_scope": "regional"}
            }

        policies = [
            make_policy("p-err", "エラー", 0, False),
            make_policy("p-none", "リソースなし", 0, False),
            make_policy("p-viol", "適合", 3, True),
            make_policy("p-ok", "適合", 0, True)
        ]

        # Act
        executions = result_formatter.create_policy_executions(policies)
        status_map = {e["policy_name"]: e["overall_status"] for e in executions}

        # Assert
        assert status_map["p-err"] == "エラー"
        assert status_map["p-none"] == "リソースなし"
        assert status_map["p-viol"] == "違反あり"
        assert status_map["p-ok"] == "適合"
```

### 2.11 create_insights_summary テスト

```python
class TestCreateInsightsSummary:
    """インサイトサマリーテスト"""

    def test_defaults(self, result_formatter):
        """RF-036: insights_summary デフォルト

        result_formatter.py:L673-699 のデフォルト引数パスをカバー。
        """
        # Arrange / Act
        summary = result_formatter.create_insights_summary()

        # Assert
        assert summary["has_summary"] is True
        assert summary["summary_type"] == "detailed"
        assert summary["generation_status"] == "completed"
        assert summary["insights"] == []
        assert summary["trend_analysis"] == {}

    def test_custom_params(self, result_formatter):
        """RF-037: insights_summary カスタムパラメータ

        result_formatter.py:L697-698 のinsights/trend_analysis引数指定をカバー。
        """
        # Arrange
        insights = ["洞察1", "洞察2"]
        trend = {"trend_key": "value"}

        # Act
        summary = result_formatter.create_insights_summary(
            insights=insights, generation_status="partial",
            summary_type="brief", trend_analysis=trend
        )

        # Assert
        assert summary["insights"] == insights
        assert summary["generation_status"] == "partial"
        assert summary["summary_type"] == "brief"
        assert summary["trend_analysis"] == trend
```

### 2.12 エラー系execution_summary/insights_summary テスト

```python
class TestCreateErrorExecutionSummary:
    """エラー時execution_summaryテスト"""

    def test_basic_structure(self, result_formatter):
        """RF-038: error_execution_summary 基本構造

        result_formatter.py:L701-770 のエラー時構造をカバー。
        error_contextに_get_failure_reason_japaneseの結果が含まれる。
        """
        # Arrange
        error = ValueError("テストエラー")

        # Act
        summary = result_formatter.create_error_execution_summary(
            error, "validation", "aws"
        )

        # Assert
        assert summary["execution_metrics"]["failed_executions"] == 1
        assert summary["execution_metrics"]["success_rate"] == 0.0
        assert summary["error_context"]["error_stage"] == "validation"
        assert summary["error_context"]["error_type"] == "ValueError"
        assert summary["error_context"]["error_message"] == "テストエラー"
        assert isinstance(summary["error_context"]["failure_reason"], str)


class TestCreateErrorInsightsSummary:
    """エラー時insights_summaryテスト"""

    def test_basic_structure(self, result_formatter):
        """RF-039: error_insights_summary 基本構造

        result_formatter.py:L772-800 のエラー時インサイト構造をカバー。
        """
        # Arrange
        error = ConnectionError("network error")

        # Act
        summary = result_formatter.create_error_insights_summary(error, "execution")

        # Assert
        assert summary["has_summary"] is True
        assert summary["summary_type"] == "error_analysis"
        assert summary["generation_status"] == "failed"
        assert summary["error_message"] == "network error"
        assert len(summary["insights"]) >= 2  # stage説明 + 一般推奨
```

### 2.13 _get_failure_reason_japanese テスト

```python
class TestGetFailureReasonJapanese:
    """エラー原因日本語変換テスト"""

    def test_validation_stage(self, result_formatter):
        """RF-040: failure_reason validation全sub-condition

        result_formatter.py:L815-823 の4分岐をカバー。
        """
        # Arrange / Act / Assert
        assert "アカウントID" in result_formatter._get_failure_reason_japanese(
            ValueError("invalid account_id"), "validation"
        )
        assert "リージョン" in result_formatter._get_failure_reason_japanese(
            ValueError("bad region"), "validation"
        )
        assert "ポリシー" in result_formatter._get_failure_reason_japanese(
            ValueError("invalid policy"), "validation"
        )
        assert "検証" in result_formatter._get_failure_reason_japanese(
            ValueError("unknown error"), "validation"
        )

    def test_credential_stage(self, result_formatter):
        """RF-041: failure_reason credential全sub-condition

        result_formatter.py:L825-833 の4分岐をカバー。
        """
        # Arrange / Act / Assert
        assert "AssumeRole" in result_formatter._get_failure_reason_japanese(
            PermissionError("AccessDenied"), "credential"
        )
        assert "トークン" in result_formatter._get_failure_reason_japanese(
            ValueError("token expired"), "credential"
        )
        assert "認証情報" in result_formatter._get_failure_reason_japanese(
            ValueError("credential not found"), "credential"
        )
        assert "認証処理" in result_formatter._get_failure_reason_japanese(
            ValueError("unknown auth error"), "credential"
        )

    def test_execution_stage(self, result_formatter):
        """RF-042: failure_reason execution全sub-condition

        result_formatter.py:L835-843 の4分岐をカバー。
        """
        # Arrange / Act / Assert
        assert "タイムアウト" in result_formatter._get_failure_reason_japanese(
            TimeoutError("timeout"), "execution"
        )
        assert "ネットワーク" in result_formatter._get_failure_reason_japanese(
            ConnectionError("network error"), "execution"
        )
        assert "権限" in result_formatter._get_failure_reason_japanese(
            PermissionError("permission denied"), "execution"
        )
        assert "実行中" in result_formatter._get_failure_reason_japanese(
            RuntimeError("unknown"), "execution"
        )

    def test_unknown_stage(self, result_formatter):
        """RF-043: failure_reason 未知stage

        result_formatter.py:L845-846 のelse分岐をカバー。
        """
        # Arrange / Act
        reason = result_formatter._get_failure_reason_japanese(
            RuntimeError("error"), "unknown_stage"
        )

        # Assert
        assert "unknown_stage" in reason
        assert "予期しないエラー" in reason
```

### 2.14 _generate_error_insights_japanese テスト

```python
class TestGenerateErrorInsightsJapanese:
    """エラーインサイト日本語生成テスト"""

    def test_validation_insights(self, result_formatter):
        """RF-044: error_insights validation stage全3分岐

        result_formatter.py:L872-878 のvalidation分岐をカバー。
        account_id (L873), region (L875), policy (L877) の3分岐。
        """
        # Arrange / Act / Assert — account_id分岐 (L873)
        insights_acct = result_formatter._generate_error_insights_japanese(
            ValueError("invalid account_id format"), "validation"
        )
        assert any("アカウントID" in i for i in insights_acct)

        # region分岐 (L875)
        insights_region = result_formatter._generate_error_insights_japanese(
            ValueError("bad region name"), "validation"
        )
        assert any("リージョン" in i for i in insights_region)

        # policy分岐 (L877)
        insights_policy = result_formatter._generate_error_insights_japanese(
            ValueError("invalid policy definition"), "validation"
        )
        assert any("ポリシー" in i for i in insights_policy)

        # 全パターンで検証段階メッセージと一般推奨が含まれる
        for ins in [insights_acct, insights_region, insights_policy]:
            assert any("検証段階" in i for i in ins)
            assert any("問題が解決しない" in i for i in ins)

    def test_credential_insights(self, result_formatter):
        """RF-045: error_insights credential stage全2分岐

        result_formatter.py:L880-885 のcredential分岐をカバー。
        assumerole/accessdenied (L881) → 2件追加, token (L884) → 1件追加。
        """
        # Arrange / Act / Assert — assumerole分岐 (L881)
        insights_role = result_formatter._generate_error_insights_japanese(
            PermissionError("AccessDenied on AssumeRole"), "credential"
        )
        assert any("AssumeRole" in i for i in insights_role)
        assert any("信頼関係" in i for i in insights_role)

        # token分岐 (L884)
        insights_token = result_formatter._generate_error_insights_japanese(
            ValueError("token expired"), "credential"
        )
        assert any("トークン" in i for i in insights_token)

        # 全パターンで認証段階メッセージが含まれる
        for ins in [insights_role, insights_token]:
            assert any("認証段階" in i for i in ins)

    def test_execution_insights(self, result_formatter):
        """RF-046: error_insights execution stage全2分岐

        result_formatter.py:L887-891 のexecution分岐をカバー。
        timeout (L888) と network/connection (L890) の2分岐。
        """
        # Arrange / Act / Assert — timeout分岐 (L888)
        insights_timeout = result_formatter._generate_error_insights_japanese(
            TimeoutError("timeout occurred"), "execution"
        )
        assert any("タイムアウト" in i for i in insights_timeout)

        # network分岐 (L890)
        insights_network = result_formatter._generate_error_insights_japanese(
            ConnectionError("network connection failed"), "execution"
        )
        assert any("ネットワーク" in i for i in insights_network)

        # 全パターンで実行段階メッセージが含まれる
        for ins in [insights_timeout, insights_network]:
            assert any("実行段階" in i for i in ins)

    def test_unknown_stage_with_general(self, result_formatter):
        """RF-047: error_insights 未知stage + 一般推奨

        result_formatter.py:L869 のget()デフォルト + L894 の一般推奨をカバー。
        """
        # Arrange / Act
        insights = result_formatter._generate_error_insights_japanese(
            RuntimeError("unexpected"), "unknown_stage"
        )

        # Assert
        assert any("unknown_stage" in i for i in insights)
        # 一般推奨は必ず最後に追加
        assert "問題が解決しない" in insights[-1]
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| RF-E01 | create_v2 OpenSearch例外伝播 | opensearch_manager.extract raises | 例外がそのまま伝播 |
| RF-E02 | _map_policy_name OpenSearch例外伝播 | get_recommendation_title_from_policy_name raises | 例外がそのまま伝播 |
| RF-E03 | create_error_result import失敗 | ValidationErrorInfo import失敗 | ImportError伝播 |

### 3.1 異常系テスト

```python
@pytest.mark.asyncio
class TestResultFormatterErrors:
    """ResultFormatter異常系テスト"""

    async def test_create_v2_opensearch_exception_propagates(
        self, result_formatter, mock_opensearch_manager
    ):
        """RF-E01: create_v2_policy_results OpenSearch例外伝播

        result_formatter.py:L75 のawait opensearch_manager.extract_recommendation_uuid
        が例外を発生した場合、try/exceptが無いため呼び出し元に伝播する。
        """
        # Arrange
        policy_results = [{
            "policy_name": "policy-test",
            "metadata": {},  # uuid無し → OpenSearchフォールバック
            "resource_type": "aws.ec2", "region": "us-east-1",
            "violation_count": 0,
            "resource_statistics": {"total_resources_scanned": 0, "resources_after_filter": 0},
            "execution_details": {"execution_duration": 0.0},
            "error_details": {"error_occurred": False}
        }]
        mock_opensearch_manager.extract_recommendation_uuid.side_effect = ConnectionError("OS down")

        # Act & Assert
        with pytest.raises(ConnectionError, match="OS down"):
            await result_formatter.create_v2_policy_results(
                policy_results, {}, mock_opensearch_manager
            )

    async def test_map_policy_name_exception_propagates(
        self, result_formatter, mock_opensearch_manager
    ):
        """RF-E02: _map_policy_name OpenSearch例外伝播

        result_formatter.py:L159 のawait opensearch_manager.get_recommendation_title_from_policy_name
        が例外を発生した場合の伝播を確認。
        """
        # Arrange
        mock_opensearch_manager.get_recommendation_title_from_policy_name.side_effect = RuntimeError("search failed")

        # Act & Assert
        with pytest.raises(RuntimeError, match="search failed"):
            await result_formatter._map_policy_name(
                "policy-test", None, {}, mock_opensearch_manager
            )

    def test_create_error_result_import_failure(self, result_formatter):
        """RF-E03: create_error_result ValidationErrorInfo import失敗

        result_formatter.py:L302 の遅延import失敗時にImportErrorが伝播する。
        patch.dictでsys.modulesのソースモジュールをNoneに設定し、
        import自体を失敗させる。
        """
        # Arrange
        import sys
        mock_handler = MagicMock()

        # Act & Assert — ソースモジュールをNoneにしてimport失敗を再現
        with patch.dict(sys.modules, {"app.jobs.common.error_handling": None}):
            with pytest.raises(ImportError):
                result_formatter.create_error_result("test error", mock_handler)
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| RF-SEC-01 | エラー結果にクレデンシャル非露出 | password含むerror_message | 構造化フィールドに限定 |
| RF-SEC-02 | failure_reasonは汎用日本語メッセージ | 機密情報含むerror | 生の例外文字列を含まない |
| RF-SEC-03 | error_execution_summary str(error)限定 | 長大error | error_contextに限定出力 |

```python
@pytest.mark.security
class TestResultFormatterSecurity:
    """ResultFormatterセキュリティテスト"""

    def test_error_result_credential_containment(self, result_formatter, mock_error_handler):
        """RF-SEC-01: エラー結果にクレデンシャル非露出

        result_formatter.py:L319-352 のerror_result構造で、
        error_messageは指定フィールドにのみ格納され、
        他のフィールド（account_id等）には漏洩しない。
        """
        # Arrange
        sensitive_message = "Auth failed: password=SuperSecret123, key=AKIA1234"
        mock_error_handler.create_user_friendly_error.return_value = "処理エラーが発生しました"
        mock_error_handler.get_error_summary.return_value = {}

        # Act — ValidationErrorInfoは遅延import (L302) のためソースモジュールをパッチ
        with patch(f"{ERROR_HANDLING_MODULE}.ValidationErrorInfo"):
            result = result_formatter.create_error_result(sensitive_message, mock_error_handler)

        # Assert — error_messageはexecution_summaryとscan_errors_summaryにのみ存在
        assert result["account_id"] == "unknown"
        assert "SuperSecret" not in result["account_id"]
        assert result["basic_statistics"]["total_violations"] == 0
        # error_messageが含まれるフィールドを明示的に確認
        assert result["execution_summary"]["error"] == sensitive_message
        assert result["scan_errors_summary"]["error_message"] == sensitive_message

    def test_failure_reason_generic_japanese(self, result_formatter):
        """RF-SEC-02: failure_reasonは汎用日本語メッセージ

        result_formatter.py:L802-846 の_get_failure_reason_japaneseは
        生の例外文字列をそのまま返さず、汎用的な日本語メッセージを返す。
        """
        # Arrange
        sensitive_error = ValueError("DB connection string: host=secret.db.internal password=dbpass123")

        # Act
        reason = result_formatter._get_failure_reason_japanese(sensitive_error, "execution")

        # Assert — 生の例外文字列が含まれない
        assert "secret.db.internal" not in reason
        assert "dbpass123" not in reason
        assert isinstance(reason, str)
        # 日本語の汎用メッセージが返される
        assert len(reason) > 0

    def test_error_execution_summary_exposure_limited(self, result_formatter):
        """RF-SEC-03: error_execution_summary str(error)限定出力

        result_formatter.py:L755,766 でstr(error)がerror_contextに格納されるが、
        他の統計フィールドには漏洩しない。
        """
        # Arrange
        sensitive_error = RuntimeError("AWS_SECRET_KEY=AKIAIOSFODNN7EXAMPLE leaked")

        # Act
        summary = result_formatter.create_error_execution_summary(
            sensitive_error, "credential", "aws"
        )

        # Assert — str(error)はerror_contextとregional_metricsのerror_messageにのみ
        assert summary["error_context"]["error_message"] == str(sensitive_error)
        assert summary["regional_metrics"][0]["error_message"] == str(sensitive_error)
        # 統計フィールドには漏洩しない
        assert summary["policy_metrics"]["unique_policies_count"] == 0
        assert summary["execution_metrics"]["success_rate"] == 0.0
        # violation_metricsにはerror情報なし
        assert "error" not in str(summary["violation_metrics"])
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_results_module` | モジュール状態リセット | function | Yes |
| `result_formatter` | ResultFormatterインスタンス | function | No |
| `mock_opensearch_manager` | OpenSearchManager AsyncMock | function | No |
| `mock_error_handler` | エラーハンドラモック | function | No |

### 共通フィクスチャ定義

```python
# test/unit/results/conftest.py に追加
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# テスト用定数
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

RF_MODULE = "app.jobs.tasks.new_custodian_scan.results.result_formatter"
ERROR_HANDLING_MODULE = "app.jobs.common.error_handling"


@pytest.fixture(autouse=True)
def reset_results_module():
    """テストごとにresultsモジュール状態をリセット

    削除範囲をresultsサブディレクトリに限定し、
    app.core等の他テストへの副作用を防止する。
    """
    yield
    modules_to_remove = [
        key for key in sys.modules
        if key.startswith("app.jobs.tasks.new_custodian_scan.results")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def result_formatter():
    """ResultFormatterインスタンス（依存モック済み）"""
    with patch(f"{RF_MODULE}.TaskLogger"), \
         patch(f"{RF_MODULE}.PolicyStatusDeterminer") as mock_determiner_cls:
        # PolicyStatusDeterminerのモック設定
        mock_determiner = MagicMock()
        mock_determiner.determine_resource_scope.return_value = "regional"
        mock_determiner_cls.return_value = mock_determiner

        from app.jobs.tasks.new_custodian_scan.results.result_formatter import (
            ResultFormatter
        )
        formatter = ResultFormatter("test-job-id")
        formatter.logger = MagicMock()
        yield formatter


@pytest.fixture
def mock_opensearch_manager():
    """OpenSearchManager AsyncMock"""
    mock = AsyncMock()
    mock.extract_recommendation_uuid.return_value = "uuid-default"
    mock.extract_severity.return_value = "Medium"
    mock.get_recommendation_title_from_policy_name.return_value = "デフォルトタイトル"
    return mock


@pytest.fixture
def mock_error_handler():
    """エラーハンドラモック"""
    mock = MagicMock()
    mock.log_validation_error.return_value = None
    mock.create_user_friendly_error.return_value = "処理中にエラーが発生しました"
    mock.get_error_summary.return_value = {"total_errors": 1}
    return mock
```

---

## 6. テスト実行例

```bash
# ResultFormatter関連テストのみ実行
pytest test/unit/results/test_result_formatter.py -v

# 特定のテストクラスのみ実行
pytest test/unit/results/test_result_formatter.py::TestCreateV2PolicyResults -v

# カバレッジ付きで実行
pytest test/unit/results/test_result_formatter.py \
    --cov=app.jobs.tasks.new_custodian_scan.results.result_formatter \
    --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/results/test_result_formatter.py -m "security" -v

# 非同期テストのみ実行
pytest test/unit/results/test_result_formatter.py \
    -k "TestCreateV2PolicyResults or TestMapPolicyName" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 47 | RF-001 〜 RF-047 |
| 異常系 | 3 | RF-E01 〜 RF-E03 |
| セキュリティ | 3 | RF-SEC-01 〜 RF-SEC-03 |
| **合計** | **53** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestResultFormatterInit` | RF-001 | 1 |
| `TestCreateV2PolicyResults` | RF-002〜RF-006 | 5 |
| `TestMapPolicyName` | RF-007〜RF-010 | 4 |
| `TestDeterminePolicyStatusJapanese` | RF-011〜RF-015 | 5 |
| `TestCalculateComplianceRate` | RF-016〜RF-018 | 3 |
| `TestGenerateResourceOverview` | RF-019〜RF-021 | 3 |
| `TestCreateErrorResult` | RF-022 | 1 |
| `TestCreateScanErrorsSummary` | RF-023 | 1 |
| `TestCreateExecutionSummary` | RF-024〜RF-029 | 6 |
| `TestCreatePolicyExecutions` | RF-030〜RF-035 | 6 |
| `TestCreateInsightsSummary` | RF-036〜RF-037 | 2 |
| `TestCreateErrorExecutionSummary` | RF-038 | 1 |
| `TestCreateErrorInsightsSummary` | RF-039 | 1 |
| `TestGetFailureReasonJapanese` | RF-040〜RF-043 | 4 |
| `TestGenerateErrorInsightsJapanese` | RF-044〜RF-047 | 4 |
| `TestResultFormatterErrors` | RF-E01〜RF-E03 | 3 |
| `TestResultFormatterSecurity` | RF-SEC-01〜RF-SEC-03 | 3 |

### 実装失敗が予想されるテスト

現時点で失敗が予想されるテストはありません。

### 注意事項

- `pytest-asyncio` が必要（`create_v2_policy_results` と `_map_policy_name` のテスト）。現在 `pyproject.toml` の dev 依存に未登録のため、実行前に `uv add --dev pytest-asyncio` で追加が必要
- `@pytest.mark.security` マーカーは `pyproject.toml` に登録済み
- `PolicyStatusDeterminer` はフィクスチャ内でモック化され、`determine_resource_scope` は `"regional"` を返す。テストでglobalスコープが必要な場合は `mock_determiner.determine_resource_scope.return_value = "global"` で上書き
- `ValidationErrorInfo` は L302 で遅延importされるため、`create_error_result` テストでは個別パッチが必要

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `PolicyStatusDeterminer` のモックにより `determine_resource_scope` の実ロジックはテスト対象外 | `generate_resource_overview` 等のスコープ判定がモック依存 | `log_analyzer` モジュールの単体テストで別途カバー |
| 2 | `ValidationErrorInfo` の遅延import (L302) | テスト時に実importを避けるため個別パッチが必要 | `with patch(f"{ERROR_HANDLING_MODULE}.ValidationErrorInfo")` でソースモジュールをパッチ |
| 3 | `create_error_result` 内の `datetime.now(timezone.utc)` | タイムスタンプが実行時刻に依存し厳密比較不可 | ISO形式文字列であることのみ検証、または `freezegun` で固定 |
| 4 | `create_execution_summary` のLoop4箇所 | テストデータが複雑になりやすい | 各Loopのメトリクスを個別テスト(RF-025~029)で分離検証 |
| 5 | `error_handler` 引数は型ヒントなし | 任意のオブジェクトが渡される可能性 | MagicMock で必要メソッド (`log_validation_error`, `create_user_friendly_error`, `get_error_summary`) のみモック |
| 6 | `_get_failure_reason_japanese` / `_generate_error_insights_japanese` はプライベートメソッド | 直接テストはカプセル化違反の可能性 | 分岐が多く間接テストでは網羅困難なため直接テストを採用 |
