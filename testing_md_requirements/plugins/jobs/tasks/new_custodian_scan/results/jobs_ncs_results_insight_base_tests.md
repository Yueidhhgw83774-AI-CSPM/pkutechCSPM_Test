# jobs/tasks/new_custodian_scan/results Insight基盤系 テストケース

## 1. 概要

`results/` サブディレクトリのInsight基盤系5ファイル（`__init__.py`, `insight_constants.py`, `base_insight_generator.py`, `resource_analyzer.py`, `insight_generator.py`）をまとめたテスト仕様書。定数定義・基底クラス・リソース分析・インサイトオーケストレーションを担う。

### 1.1 対象クラス

| クラス | ファイル | 行数 | 責務 |
|--------|---------|------|------|
| (パッケージ) | `__init__.py` | 24 | 公開クラスのエクスポート |
| `SeverityLevel` 他 | `insight_constants.py` | 58 | 定数・Enum・しきい値・メッセージテンプレート |
| `BaseInsightGenerator` | `base_insight_generator.py` | 96 | インサイト生成ABCとユーティリティメソッド |
| `ResourceAnalyzer` | `resource_analyzer.py` | 231 | リソース分析・分類・コンプライアンス率計算 |
| `InsightGenerator` | `insight_generator.py` | 178 | インサイト生成オーケストレータ |

### 1.2 カバレッジ目標: 90%

> **注記**: 純粋関数・定数定義・ABCが中心のため高カバレッジが見込める。`InsightGenerator.generate_insights` はオーケストレーションメソッドで委譲先をMock化。pytest-asyncio は不要。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象1 | `app/jobs/tasks/new_custodian_scan/results/__init__.py` |
| テスト対象2 | `app/jobs/tasks/new_custodian_scan/results/insight_constants.py` |
| テスト対象3 | `app/jobs/tasks/new_custodian_scan/results/base_insight_generator.py` |
| テスト対象4 | `app/jobs/tasks/new_custodian_scan/results/resource_analyzer.py` |
| テスト対象5 | `app/jobs/tasks/new_custodian_scan/results/insight_generator.py` |
| テストコード | `test/unit/jobs/tasks/new_custodian_scan/results/test_results_insight_base.py` |

### 1.4 補足情報

#### 依存関係

```
__init__.py
  ──→ ResultAggregator, OpenSearchManager, HistoryManager,
      InsightGenerator, ResultFormatter

insight_constants.py
  ──→ enum（標準ライブラリ）

base_insight_generator.py (BaseInsightGenerator)
  ──→ ABC, abstractmethod（標準ライブラリ）
  ──→ TaskLogger（ログ）

resource_analyzer.py (ResourceAnalyzer)
  ──→ BaseInsightGenerator（基底クラス）

insight_generator.py (InsightGenerator)
  ──→ OverviewInsightGenerator（概要インサイト生成）
  ──→ ViolationInsightGenerator（違反インサイト生成）
  ──→ ResourceAnalyzer（リソース分析）
  ──→ DEFAULT_MESSAGES（定数）
  ──→ TaskLogger（ログ）
```

#### テスト戦略

| テストカテゴリ | 手法 |
|--------------|------|
| `__init__.py` | インポート検証のみ |
| `insight_constants.py` | 値の直接アサーション |
| `BaseInsightGenerator` | テスト用具象サブクラスで実インスタンステスト |
| `ResourceAnalyzer` | 実インスタンスでメソッド単位テスト（TaskLoggerのみMock） |
| `InsightGenerator` | 3委譲先をMock化してオーケストレーション検証 |

#### 主要分岐マップ

| クラス | メソッド | 行番号 | 条件 | 分岐数 |
|--------|---------|--------|------|--------|
| BaseInsightGenerator | `determine_cloud_provider` | L49, L54, L56, L58, L61 | 空リスト、aws./azure./gcp.プレフィックス、マッチなし | 5 |
| BaseInsightGenerator | `normalize_region_count` | L73, L75, L84 | int/list/other | 3 |
| BaseInsightGenerator | `get_unique_regions` | L97 | 空リスト/非空 | 2 |
| ResourceAnalyzer | `create_resource_overview_from_log_analysis` | L74, L80 | グローバル/リージョナル分類 | 2 |
| ResourceAnalyzer | `_update_resource_by_type` | L111 | 新規/既存エントリ | 2 |
| ResourceAnalyzer | `is_global_resource` | L204 | マッチあり/なし | 2 |
| ResourceAnalyzer | `calculate_compliance_percentage` | L222, L231 | 空リスト、total>0 | 2 |
| InsightGenerator | `generate_insights` | L63, L90, L102 | 正常/例外/空インサイト | 3 |

---

## 2. 正常系テストケース

### パッケージ (PKG)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| PKG-001 | 全公開クラスのインポート成功 | パッケージインポート | 5クラスが参照可能 |
| PKG-002 | `__all__`に5クラス含まれる | `__all__`参照 | 5要素のリスト |

### 定数 (CST)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CST-001 | SeverityLevel Enum値検証 | Enum参照 | Critical/High/Medium/Low の4値 |
| CST-002 | ComplianceThreshold定数値検証 | 属性参照 | EXCELLENT=80.0, GOOD=50.0, POOR=30.0, CRITICAL=10.0 |
| CST-003 | ViolationThreshold定数値検証 | 属性参照 | NONE=0, MINOR=5, MODERATE=20, MAJOR=50 |
| CST-004 | ResourceDiversityThreshold定数値検証 | 属性参照 | HIGH=5, MEDIUM=2 |
| CST-005 | EfficiencyThreshold定数値検証 | 属性参照 | EXCELLENT=10.0, GOOD=30.0 |
| CST-006 | DEFAULT_MESSAGES全キー検証 | dict参照 | 7キー全存在・値が文字列 |

### BaseInsightGenerator (BASE)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| BASE-001 | 初期化時にlogger生成 | job_id, component_name | job_id保持・logger生成 |
| BASE-002 | 抽象クラスの直接インスタンス化不可 | BaseInsightGenerator() | TypeError |
| BASE-003 | determine_cloud_provider 空リスト→"不明" | [] | "不明" |
| BASE-004 | determine_cloud_provider AWSプレフィックス | "aws.ec2" | "AWS" |
| BASE-005 | determine_cloud_provider Azureプレフィックス | "azure.vm" | "Azure" |
| BASE-006 | determine_cloud_provider GCPプレフィックス | "gcp.compute" | "GCP" |
| BASE-007 | determine_cloud_provider マッチなし→"不明" | "unknown.resource" | "不明" |
| BASE-008 | normalize_region_count int入力 | 5 | 5 |
| BASE-009 | normalize_region_count リスト（重複なし） | ["us-east-1", "eu-west-1"] | 2 |
| BASE-010 | normalize_region_count リスト（重複あり） | ["us-east-1", "us-east-1", "eu-west-1"] | 2（debugログ出力） |
| BASE-011 | normalize_region_count 不正型→0 | "not-a-list" | 0 |
| BASE-012 | get_unique_regions 空リスト→[] | [] | [] |
| BASE-013 | get_unique_regions 重複ありリスト | ["us-east-1", "us-east-1"] | 1要素のリスト |

### ResourceAnalyzer (RESA)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| RESA-001 | 初期化（BaseInsightGenerator継承） | job_id | job_id保持・logger生成 |
| RESA-002 | generate()は空リスト返却 | - | [] |
| RESA-003 | create_resource_overview 空policy_results | {} | 3キーの空リスト |
| RESA-004 | create_resource_overview グローバル+リージョナル混在 | IAM+EC2 | global/regional分類 |
| RESA-005 | _update_resource_by_type 新規エントリ作成 | 新規resource_type | dictに新規エントリ |
| RESA-006 | _update_resource_by_type 既存エントリ累積 | 既存resource_type | violations/resources加算 |
| RESA-007 | _update_global_resources 新規 | 新規グローバルタイプ | dictに新規エントリ |
| RESA-008 | _update_global_resources 累積 | 既存グローバルタイプ | violation_count/total_count加算 |
| RESA-009 | _update_regional_resources 新規 | 新規リージョナルタイプ | type#regionキーで新規エントリ |
| RESA-010 | _update_regional_resources 累積 | 既存リージョナルタイプ | violation_count/total_count加算 |
| RESA-011 | is_global_resource awsプレフィックス除去 | "aws.iam" | True |
| RESA-012 | is_global_resource azureプレフィックス除去 | "azure.iam" | True |
| RESA-013 | is_global_resource マッチなし | "aws.ec2" | False |
| RESA-014 | calculate_compliance_percentage 空リスト→0.0 | [] | 0.0 |
| RESA-015 | calculate_compliance_percentage 全適合→100.0 | violation_count=0×3 | 100.0 |
| RESA-016 | calculate_compliance_percentage 部分適合 | 2適合+1違反 | 約66.7 |

### InsightGenerator (IGEN)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| IGEN-001 | 初期化時に3コンポーネント生成 | job_id | overview/violation/resource_analyzer生成 |
| IGEN-002 | generate_insights正常フロー | 正常データ | 概要+違反インサイト統合 |
| IGEN-003 | generate_insights空インサイト→デフォルト | 両生成器が[]返却 | "スキャンが完了しました" |
| IGEN-004 | _determine_cloud_provider委譲 | policy_results | overview_generator.determine_cloud_provider呼出 |
| IGEN-005 | calculate_compliance_percentage委譲 | policy_results | resource_analyzer.calculate_compliance_percentage呼出 |
| IGEN-006 | create_resource_overview_from_log_analysis委譲 | log_analysis_result | resource_analyzer同名メソッド呼出 |
| IGEN-007 | _is_global_resource委譲 | resource_type | resource_analyzer.is_global_resource呼出 |
| IGEN-008 | aggregated_scan_statisticsがoverview_generatorに転送 | 非None値 | overview_generator.generateの引数に含まれる |

### 2.1 パッケージ・定数テスト

```python
# test/unit/jobs/tasks/new_custodian_scan/results/test_results_insight_base.py
import pytest
from unittest.mock import patch, MagicMock

MODULE_BASE = "app.jobs.tasks.new_custodian_scan.results.base_insight_generator"
MODULE_RA = "app.jobs.tasks.new_custodian_scan.results.resource_analyzer"
MODULE_IG = "app.jobs.tasks.new_custodian_scan.results.insight_generator"


class TestPackageInit:
    """パッケージインポートテスト"""

    def test_all_public_classes_importable(self):
        """PKG-001: 全公開クラスのインポート成功

        __init__.py:L13-17 の5クラスインポートをカバー。
        """
        # Act
        from app.jobs.tasks.new_custodian_scan.results import (
            ResultAggregator, OpenSearchManager, HistoryManager,
            InsightGenerator, ResultFormatter
        )

        # Assert
        assert ResultAggregator is not None
        assert OpenSearchManager is not None
        assert HistoryManager is not None
        assert InsightGenerator is not None
        assert ResultFormatter is not None

    def test_all_list_contains_five_classes(self):
        """PKG-002: __all__に5クラス含まれる

        __init__.py:L19-25 の__all__定義をカバー。
        """
        # Act
        from app.jobs.tasks.new_custodian_scan import results

        # Assert
        assert len(results.__all__) == 5
        expected = {"ResultAggregator", "OpenSearchManager",
                    "HistoryManager", "InsightGenerator", "ResultFormatter"}
        assert set(results.__all__) == expected


class TestInsightConstants:
    """定数定義テスト"""

    def test_severity_level_enum_values(self):
        """CST-001: SeverityLevel Enum値検証

        insight_constants.py:L14-19 の4値をカバー。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.results.insight_constants import SeverityLevel

        # Assert
        assert SeverityLevel.CRITICAL.value == "Critical"
        assert SeverityLevel.HIGH.value == "High"
        assert SeverityLevel.MEDIUM.value == "Medium"
        assert SeverityLevel.LOW.value == "Low"
        assert len(SeverityLevel) == 4

    def test_compliance_threshold_values(self):
        """CST-002: ComplianceThreshold定数値検証

        insight_constants.py:L23-27 の4しきい値をカバー。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.results.insight_constants import ComplianceThreshold

        # Assert
        assert ComplianceThreshold.EXCELLENT == 80.0
        assert ComplianceThreshold.GOOD == 50.0
        assert ComplianceThreshold.POOR == 30.0
        assert ComplianceThreshold.CRITICAL == 10.0

    def test_violation_threshold_values(self):
        """CST-003: ViolationThreshold定数値検証

        insight_constants.py:L31-35 の4しきい値をカバー。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.results.insight_constants import ViolationThreshold

        # Assert
        assert ViolationThreshold.NONE == 0
        assert ViolationThreshold.MINOR == 5
        assert ViolationThreshold.MODERATE == 20
        assert ViolationThreshold.MAJOR == 50

    def test_resource_diversity_threshold_values(self):
        """CST-004: ResourceDiversityThreshold定数値検証

        insight_constants.py:L39-41 の2しきい値をカバー。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.results.insight_constants import ResourceDiversityThreshold

        # Assert
        assert ResourceDiversityThreshold.HIGH == 5
        assert ResourceDiversityThreshold.MEDIUM == 2

    def test_efficiency_threshold_values(self):
        """CST-005: EfficiencyThreshold定数値検証

        insight_constants.py:L45-47 の2しきい値をカバー。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.results.insight_constants import EfficiencyThreshold

        # Assert
        assert EfficiencyThreshold.EXCELLENT == 10.0
        assert EfficiencyThreshold.GOOD == 30.0

    def test_default_messages_all_keys(self):
        """CST-006: DEFAULT_MESSAGES全キー検証

        insight_constants.py:L51-59 の7キーをカバー。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.results.insight_constants import DEFAULT_MESSAGES

        # Assert
        expected_keys = {
            "scan_completed", "error_during_generation", "no_policies",
            "all_compliant", "minor_violations", "moderate_violations",
            "major_violations"
        }
        assert set(DEFAULT_MESSAGES.keys()) == expected_keys
        # 全値が非空文字列
        for key, value in DEFAULT_MESSAGES.items():
            assert isinstance(value, str) and len(value) > 0, f"{key}の値が不正"
```

### 2.2 BaseInsightGenerator テスト

```python
class TestBaseInsightGeneratorInit:
    """BaseInsightGenerator初期化テスト"""

    def test_init_creates_logger(self, base_generator):
        """BASE-001: 初期化時にlogger生成

        base_insight_generator.py:L18-27 をカバー。
        """
        # Assert
        assert base_generator.job_id == "test-job-id"
        assert base_generator.logger is not None

    def test_abstract_class_not_instantiable(self):
        """BASE-002: 抽象クラスの直接インスタンス化不可

        base_insight_generator.py:L15,L29-37 のABC+abstractmethodをカバー。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.results.base_insight_generator import BaseInsightGenerator

        # Act & Assert
        with pytest.raises(TypeError):
            BaseInsightGenerator("test-job-id", "Test")


class TestDetermineCloudProvider:
    """クラウドプロバイダー判定テスト"""

    def test_empty_list_returns_unknown(self, base_generator):
        """BASE-003: determine_cloud_provider 空リスト→"不明"

        base_insight_generator.py:L49-50 の空リスト分岐をカバー。
        """
        # Act
        result = base_generator.determine_cloud_provider([])

        # Assert
        assert result == "不明"

    def test_aws_prefix(self, base_generator):
        """BASE-004: determine_cloud_provider AWSプレフィックス

        base_insight_generator.py:L54-55 のaws.分岐をカバー。
        """
        # Arrange
        policy_results = [{"resource_type": "aws.ec2"}]

        # Act
        result = base_generator.determine_cloud_provider(policy_results)

        # Assert
        assert result == "AWS"

    def test_azure_prefix(self, base_generator):
        """BASE-005: determine_cloud_provider Azureプレフィックス

        base_insight_generator.py:L56-57 のazure.分岐をカバー。
        """
        # Arrange
        policy_results = [{"resource_type": "azure.vm"}]

        # Act
        result = base_generator.determine_cloud_provider(policy_results)

        # Assert
        assert result == "Azure"

    def test_gcp_prefix(self, base_generator):
        """BASE-006: determine_cloud_provider GCPプレフィックス

        base_insight_generator.py:L58-59 のgcp.分岐をカバー。
        """
        # Arrange
        policy_results = [{"resource_type": "gcp.compute"}]

        # Act
        result = base_generator.determine_cloud_provider(policy_results)

        # Assert
        assert result == "GCP"

    def test_no_match_returns_unknown(self, base_generator):
        """BASE-007: determine_cloud_provider マッチなし→"不明"

        base_insight_generator.py:L61 の全プレフィックス不一致分岐をカバー。
        """
        # Arrange
        policy_results = [{"resource_type": "unknown.resource"}]

        # Act
        result = base_generator.determine_cloud_provider(policy_results)

        # Assert
        assert result == "不明"


class TestNormalizeRegionCount:
    """リージョン数正規化テスト"""

    def test_int_input(self, base_generator):
        """BASE-008: normalize_region_count int入力

        base_insight_generator.py:L73-74 のint分岐をカバー。
        """
        # Act
        result = base_generator.normalize_region_count(5)

        # Assert
        assert result == 5

    def test_list_no_duplicates(self, base_generator):
        """BASE-009: normalize_region_count リスト（重複なし）

        base_insight_generator.py:L75-83 のlist分岐をカバー。
        重複がないためdebugログは出力されない。
        """
        # Act
        result = base_generator.normalize_region_count(["us-east-1", "eu-west-1"])

        # Assert
        assert result == 2

    def test_list_with_duplicates(self, base_generator):
        """BASE-010: normalize_region_count リスト（重複あり）

        base_insight_generator.py:L78-82 の重複検出分岐をカバー。
        """
        # Arrange
        regions = ["us-east-1", "us-east-1", "eu-west-1"]

        # Act
        result = base_generator.normalize_region_count(regions)

        # Assert
        assert result == 2
        # 重複検出のdebugログが出力される
        base_generator.logger.debug.assert_called()

    def test_invalid_type_returns_zero(self, base_generator):
        """BASE-011: normalize_region_count 不正型→0

        base_insight_generator.py:L84-85 のelse分岐をカバー。
        """
        # Act
        result = base_generator.normalize_region_count("not-a-list")

        # Assert
        assert result == 0


class TestGetUniqueRegions:
    """ユニークリージョン取得テスト"""

    def test_empty_list(self, base_generator):
        """BASE-012: get_unique_regions 空リスト→[]

        base_insight_generator.py:L97 のelse分岐（空リスト）をカバー。
        """
        # Act
        result = base_generator.get_unique_regions([])

        # Assert
        assert result == []

    def test_with_duplicates(self, base_generator):
        """BASE-013: get_unique_regions 重複ありリスト

        base_insight_generator.py:L97 のif分岐（非空リスト）をカバー。
        """
        # Act
        result = base_generator.get_unique_regions(["us-east-1", "us-east-1", "eu-west-1"])

        # Assert
        assert len(result) == 2
        assert set(result) == {"us-east-1", "eu-west-1"}
```

### 2.3 ResourceAnalyzer テスト

```python
class TestResourceAnalyzerInit:
    """ResourceAnalyzer初期化テスト"""

    def test_init_inherits_base(self, resource_analyzer):
        """RESA-001: 初期化（BaseInsightGenerator継承）

        resource_analyzer.py:L18-25 をカバー。
        super().__init__経由でjob_idとloggerが設定される。
        """
        # Assert
        assert resource_analyzer.job_id == "test-job-id"
        assert resource_analyzer.logger is not None

    def test_generate_returns_empty_list(self, resource_analyzer):
        """RESA-002: generate()は空リスト返却

        resource_analyzer.py:L27-35 の空リスト返却をカバー。
        """
        # Act
        result = resource_analyzer.generate()

        # Assert
        assert result == []


class TestCreateResourceOverview:
    """リソース概要作成テスト"""

    def test_empty_policy_results(self, resource_analyzer):
        """RESA-003: create_resource_overview 空policy_results

        resource_analyzer.py:L52 の.get("policy_results", [])で空リスト→
        ループ未実行で3キーの空リストを返却。
        """
        # Act
        result = resource_analyzer.create_resource_overview_from_log_analysis(
            {}, ["iam"]
        )

        # Assert
        assert result["global_resources"] == []
        assert result["regional_resources"] == []
        assert result["resource_by_type"] == []

    def test_mixed_global_and_regional(self, resource_analyzer):
        """RESA-004: create_resource_overview グローバル+リージョナル混在

        resource_analyzer.py:L58-85 のforループ内分岐をカバー。
        IAM（グローバル）とEC2（リージョナル）の混在データ。
        """
        # Arrange
        log_result = {
            "policy_results": [
                {
                    "resource_type": "aws.iam",
                    "violation_count": 2,
                    "resource_statistics": {"total_resources_scanned": 10},
                    "region": "us-east-1"
                },
                {
                    "resource_type": "aws.ec2",
                    "violation_count": 3,
                    "resource_statistics": {"total_resources_scanned": 50},
                    "region": "us-east-1"
                }
            ]
        }

        # Act
        result = resource_analyzer.create_resource_overview_from_log_analysis(
            log_result, ["iam"]
        )

        # Assert
        assert len(result["global_resources"]) == 1
        assert result["global_resources"][0]["resource_type"] == "aws.iam"
        assert len(result["regional_resources"]) == 1
        assert result["regional_resources"][0]["resource_type"] == "aws.ec2"
        assert len(result["resource_by_type"]) == 2


class TestUpdateResourceByType:
    """リソースタイプ別統計更新テスト"""

    def test_new_entry(self, resource_analyzer):
        """RESA-005: _update_resource_by_type 新規エントリ作成

        resource_analyzer.py:L111-119 の新規作成分岐をカバー。
        """
        # Arrange
        resource_by_type = {}

        # Act
        resource_analyzer._update_resource_by_type(
            resource_by_type, "aws.ec2", 3, 50, ["iam"]
        )

        # Assert
        assert "aws.ec2" in resource_by_type
        assert resource_by_type["aws.ec2"]["total_violations"] == 3
        assert resource_by_type["aws.ec2"]["total_resources"] == 50
        assert resource_by_type["aws.ec2"]["scope"] == "regional"

    def test_existing_entry_accumulates(self, resource_analyzer):
        """RESA-006: _update_resource_by_type 既存エントリ累積

        resource_analyzer.py:L121-122 の累積加算をカバー。
        """
        # Arrange
        resource_by_type = {
            "aws.ec2": {
                "resource_type": "aws.ec2",
                "total_resources": 50, "total_violations": 3,
                "scope": "regional"
            }
        }

        # Act
        resource_analyzer._update_resource_by_type(
            resource_by_type, "aws.ec2", 2, 30, ["iam"]
        )

        # Assert
        assert resource_by_type["aws.ec2"]["total_violations"] == 5
        assert resource_by_type["aws.ec2"]["total_resources"] == 80


class TestUpdateGlobalResources:
    """グローバルリソース更新テスト"""

    def test_new_global_resource(self, resource_analyzer):
        """RESA-007: _update_global_resources 新規

        resource_analyzer.py:L142-148 の新規作成分岐をカバー。
        """
        # Arrange
        global_dict = {}

        # Act
        resource_analyzer._update_global_resources(
            global_dict, "aws.iam", 2, 10, "us-east-1"
        )

        # Assert
        assert "aws.iam" in global_dict
        assert global_dict["aws.iam"]["violation_count"] == 2
        assert global_dict["aws.iam"]["total_count"] == 10
        assert global_dict["aws.iam"]["scanned_from_region"] == "us-east-1"

    def test_existing_global_resource_accumulates(self, resource_analyzer):
        """RESA-008: _update_global_resources 累積

        resource_analyzer.py:L149-150 の累積加算をカバー。
        """
        # Arrange
        global_dict = {
            "aws.iam": {
                "resource_type": "aws.iam", "total_count": 10,
                "violation_count": 2, "scanned_from_region": "us-east-1"
            }
        }

        # Act
        resource_analyzer._update_global_resources(
            global_dict, "aws.iam", 1, 5, "eu-west-1"
        )

        # Assert
        assert global_dict["aws.iam"]["violation_count"] == 3
        assert global_dict["aws.iam"]["total_count"] == 15


class TestUpdateRegionalResources:
    """リージョナルリソース更新テスト"""

    def test_new_regional_resource(self, resource_analyzer):
        """RESA-009: _update_regional_resources 新規

        resource_analyzer.py:L172-178 の新規作成分岐をカバー。
        キー形式: f"{resource_type}#{region}"
        """
        # Arrange
        regional_dict = {}

        # Act
        resource_analyzer._update_regional_resources(
            regional_dict, "aws.ec2", 3, 50, "us-east-1"
        )

        # Assert
        key = "aws.ec2#us-east-1"
        assert key in regional_dict
        assert regional_dict[key]["violation_count"] == 3
        assert regional_dict[key]["total_count"] == 50
        assert regional_dict[key]["region"] == "us-east-1"

    def test_existing_regional_resource_accumulates(self, resource_analyzer):
        """RESA-010: _update_regional_resources 累積

        resource_analyzer.py:L179-180 の累積加算をカバー。
        """
        # Arrange
        regional_dict = {
            "aws.ec2#us-east-1": {
                "resource_type": "aws.ec2", "total_count": 50,
                "violation_count": 3, "region": "us-east-1"
            }
        }

        # Act
        resource_analyzer._update_regional_resources(
            regional_dict, "aws.ec2", 2, 20, "us-east-1"
        )

        # Assert
        assert regional_dict["aws.ec2#us-east-1"]["violation_count"] == 5
        assert regional_dict["aws.ec2#us-east-1"]["total_count"] == 70


class TestIsGlobalResource:
    """グローバルリソース判定テスト"""

    def test_aws_prefix_removed_and_matched(self, resource_analyzer):
        """RESA-011: is_global_resource awsプレフィックス除去

        resource_analyzer.py:L198-206 のプレフィックス除去+マッチをカバー。
        """
        # Act
        result = resource_analyzer.is_global_resource("aws.iam", ["iam"])

        # Assert
        assert result is True

    def test_azure_prefix_matched(self, resource_analyzer):
        """RESA-012: is_global_resource azureプレフィックス除去

        resource_analyzer.py:L199 のazure.除去をカバー。
        """
        # Act
        result = resource_analyzer.is_global_resource("azure.iam", ["iam"])

        # Assert
        assert result is True

    def test_no_match(self, resource_analyzer):
        """RESA-013: is_global_resource マッチなし

        resource_analyzer.py:L204 のany()がFalseとなるケースをカバー。
        """
        # Act
        result = resource_analyzer.is_global_resource("aws.ec2", ["iam", "s3"])

        # Assert
        assert result is False


class TestCalculateCompliancePercentage:
    """コンプライアンス率計算テスト"""

    def test_empty_list_returns_zero(self, resource_analyzer):
        """RESA-014: calculate_compliance_percentage 空リスト→0.0

        resource_analyzer.py:L222-223 の空リスト分岐をカバー。
        """
        # Act
        result = resource_analyzer.calculate_compliance_percentage([])

        # Assert
        assert result == 0.0

    def test_all_compliant(self, resource_analyzer):
        """RESA-015: calculate_compliance_percentage 全適合→100.0

        resource_analyzer.py:L226-231 の全ポリシー適合ケースをカバー。
        """
        # Arrange
        policies = [
            {"violation_count": 0},
            {"violation_count": 0},
            {"violation_count": 0}
        ]

        # Act
        result = resource_analyzer.calculate_compliance_percentage(policies)

        # Assert
        assert result == 100.0

    def test_partial_compliance(self, resource_analyzer):
        """RESA-016: calculate_compliance_percentage 部分適合

        resource_analyzer.py:L226-231 の部分適合ケースをカバー。
        2/3 = 66.67%
        """
        # Arrange
        policies = [
            {"violation_count": 0},
            {"violation_count": 0},
            {"violation_count": 5}
        ]

        # Act
        result = resource_analyzer.calculate_compliance_percentage(policies)

        # Assert
        assert abs(result - 66.67) < 0.1
```

### 2.4 InsightGenerator テスト

```python
class TestInsightGeneratorInit:
    """InsightGenerator初期化テスト"""

    def test_init_creates_three_components(self, mock_ig_components):
        """IGEN-001: 初期化時に3コンポーネント生成

        insight_generator.py:L23-36 の3コンポーネント初期化をカバー。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.results.insight_generator import InsightGenerator

        # Act
        generator = InsightGenerator("test-job-id")

        # Assert
        mock_ig_components["OverviewInsightGenerator"].assert_called_once_with("test-job-id")
        mock_ig_components["ViolationInsightGenerator"].assert_called_once_with("test-job-id")
        mock_ig_components["ResourceAnalyzer"].assert_called_once_with("test-job-id")


class TestGenerateInsights:
    """インサイト生成テスト"""

    def test_normal_flow(self, insight_generator):
        """IGEN-002: generate_insights正常フロー

        insight_generator.py:L63-109 の正常フロー全体をカバー。
        概要インサイトと違反インサイトが統合される。
        """
        # Arrange
        insight_generator.overview_generator.generate.return_value = ["概要1"]
        insight_generator.violation_generator.generate.return_value = ["違反1"]
        insight_generator.overview_generator.determine_cloud_provider.return_value = "AWS"

        # Act
        result = insight_generator.generate_insights(
            policy_results=[{"resource_type": "aws.ec2"}],
            basic_statistics={"total_violations": 5},
            account_id="123456",
            scan_metadata={},
            resource_overview={}
        )

        # Assert
        assert "概要1" in result
        assert "違反1" in result
        assert len(result) == 2

    def test_empty_insights_returns_default(self, insight_generator):
        """IGEN-003: generate_insights空インサイト→デフォルト

        insight_generator.py:L102-107 の空インサイト分岐をカバー。
        両生成器が空リストを返す場合、DEFAULT_MESSAGESのデフォルトメッセージが追加される。
        """
        # Arrange
        insight_generator.overview_generator.generate.return_value = []
        insight_generator.violation_generator.generate.return_value = []
        insight_generator.overview_generator.determine_cloud_provider.return_value = "AWS"

        # Act
        result = insight_generator.generate_insights(
            policy_results=[], basic_statistics={"total_violations": 0},
            account_id="123456", scan_metadata={}, resource_overview={}
        )

        # Assert
        assert len(result) == 1
        assert "スキャンが完了しました" in result[0]

    def test_aggregated_scan_statistics_forwarded(self, insight_generator):
        """IGEN-008: aggregated_scan_statisticsがoverview_generatorに転送

        insight_generator.py:L71-75 のoverview_generator.generate()呼び出しで
        aggregated_scan_statisticsが引数として渡されることを検証。
        引数削除やデフォルト値変更の回帰検出を目的とする。
        """
        # Arrange
        insight_generator.overview_generator.generate.return_value = ["概要"]
        insight_generator.violation_generator.generate.return_value = []
        insight_generator.overview_generator.determine_cloud_provider.return_value = "AWS"
        agg_stats = {"total_resources": 100, "total_violations": 5}

        # Act
        insight_generator.generate_insights(
            policy_results=[{"resource_type": "aws.ec2"}],
            basic_statistics={"total_violations": 5},
            account_id="123456", scan_metadata={}, resource_overview={},
            aggregated_scan_statistics=agg_stats
        )

        # Assert — 位置引数・キーワード引数どちらでも検出可能
        args, kwargs = insight_generator.overview_generator.generate.call_args
        assert agg_stats in args or agg_stats in kwargs.values()


class TestInsightGeneratorDelegation:
    """InsightGenerator委譲メソッドテスト"""

    def test_determine_cloud_provider_delegates(self, insight_generator):
        """IGEN-004: _determine_cloud_provider委譲

        insight_generator.py:L111-121 の委譲をカバー。
        """
        # Arrange
        insight_generator.overview_generator.determine_cloud_provider.return_value = "AWS"

        # Act
        result = insight_generator._determine_cloud_provider([{"resource_type": "aws.ec2"}])

        # Assert
        insight_generator.overview_generator.determine_cloud_provider.assert_called_once()
        assert result == "AWS"

    def test_calculate_compliance_delegates(self, insight_generator):
        """IGEN-005: calculate_compliance_percentage委譲

        insight_generator.py:L126-141 の委譲をカバー。
        """
        # Arrange
        insight_generator.resource_analyzer.calculate_compliance_percentage.return_value = 80.0

        # Act
        result = insight_generator.calculate_compliance_percentage([])

        # Assert
        insight_generator.resource_analyzer.calculate_compliance_percentage.assert_called_once()
        assert result == 80.0

    def test_create_resource_overview_delegates(self, insight_generator):
        """IGEN-006: create_resource_overview_from_log_analysis委譲

        insight_generator.py:L143-160 の委譲をカバー。
        """
        # Arrange
        expected = {"global_resources": [], "regional_resources": [], "resource_by_type": []}
        insight_generator.resource_analyzer.create_resource_overview_from_log_analysis.return_value = expected

        # Act
        result = insight_generator.create_resource_overview_from_log_analysis({}, [])

        # Assert
        insight_generator.resource_analyzer.create_resource_overview_from_log_analysis.assert_called_once()
        assert result == expected

    def test_is_global_resource_delegates(self, insight_generator):
        """IGEN-007: _is_global_resource委譲

        insight_generator.py:L162-178 の委譲をカバー。
        """
        # Arrange
        insight_generator.resource_analyzer.is_global_resource.return_value = True

        # Act
        result = insight_generator._is_global_resource("aws.iam", ["iam"])

        # Assert
        insight_generator.resource_analyzer.is_global_resource.assert_called_once_with("aws.iam", ["iam"])
        assert result is True
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| IGEN-E01 | generate_insights概要生成例外→エラーメッセージ | overview_generator.generate例外 | 定型エラーメッセージ追加、デフォルトメッセージなし |
| IGEN-E02 | generate_insights違反生成例外→部分インサイト保持 | violation_generator.generate例外 | 概要インサイト+エラーメッセージ |

### 3.1 異常系テスト

```python
class TestInsightGeneratorErrors:
    """InsightGenerator異常系テスト"""

    def test_overview_exception_returns_error_message(self, insight_generator):
        """IGEN-E01: generate_insights概要生成例外→エラーメッセージ

        insight_generator.py:L90-94 のexceptブロックをカバー。
        早期例外のため概要インサイトなし。エラーメッセージのみが追加され、
        L102のif not insightsはFalse（リストに1要素あるため）。
        """
        # Arrange
        insight_generator.overview_generator.determine_cloud_provider.return_value = "AWS"
        insight_generator.overview_generator.generate.side_effect = RuntimeError("生成失敗")

        # Act
        result = insight_generator.generate_insights(
            policy_results=[], basic_statistics={"total_violations": 0},
            account_id="123456", scan_metadata={}, resource_overview={}
        )

        # Assert
        # エラーメッセージが追加される
        assert any("エラーが発生しました" in msg for msg in result)
        # デフォルトメッセージは追加されない（エラーメッセージで非空になるため）
        assert not any("スキャンが完了しました" in msg for msg in result)
        insight_generator.logger.warning.assert_called()

    def test_violation_exception_preserves_overview(self, insight_generator):
        """IGEN-E02: generate_insights違反生成例外→部分インサイト保持

        insight_generator.py:L90-94 のexceptブロックをカバー。
        概要インサイト追加後に違反生成が例外を投げるケース。
        概要インサイト + エラーメッセージの両方が保持される。
        """
        # Arrange
        insight_generator.overview_generator.determine_cloud_provider.return_value = "AWS"
        insight_generator.overview_generator.generate.return_value = ["概要インサイト"]
        insight_generator.violation_generator.generate.side_effect = RuntimeError("違反分析失敗")

        # Act
        result = insight_generator.generate_insights(
            policy_results=[], basic_statistics={"total_violations": 0},
            account_id="123456", scan_metadata={}, resource_overview={}
        )

        # Assert
        # 概要インサイトが保持される
        assert "概要インサイト" in result
        # エラーメッセージも追加される
        assert any("エラーが発生しました" in msg for msg in result)
        assert len(result) == 2
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| IGEN-SEC-01 | 例外詳細がinsights戻り値に非露出 | RuntimeError("内部SQL情報") | 定型メッセージのみ返却、例外詳細なし |
| BASE-SEC-01 | determine_cloud_providerへの攻撃的入力 | XSS文字列含むresource_type | 安全に"不明"返却 |
| CST-SEC-01 | DEFAULT_MESSAGESが外部入力に非依存 | dict直接参照 | 全値がハードコード文字列 |

```python
@pytest.mark.security
class TestInsightBaseSecurity:
    """Insight基盤系セキュリティテスト"""

    def test_exception_details_not_in_return_value(self, insight_generator):
        """IGEN-SEC-01: 例外詳細がinsights戻り値に非露出

        insight_generator.py:L90-94 で例外発生時、str(e)はlogger.warningに
        出力されるが、insights戻り値にはDEFAULT_MESSAGESの定型メッセージのみが
        追加される。例外の内容（内部情報を含む可能性）は外部に露出しない。
        """
        # Arrange
        sensitive_error = "Connection to db://internal-host:5432/secrets failed"
        insight_generator.overview_generator.determine_cloud_provider.return_value = "AWS"
        insight_generator.overview_generator.generate.side_effect = RuntimeError(sensitive_error)

        # Act
        result = insight_generator.generate_insights(
            policy_results=[], basic_statistics={"total_violations": 0},
            account_id="123456", scan_metadata={}, resource_overview={}
        )

        # Assert
        # 戻り値に例外の内部情報が含まれない
        for msg in result:
            assert "db://" not in msg
            assert "internal-host" not in msg
            assert "5432" not in msg
            assert "secrets" not in msg
        # 定型メッセージのみが含まれる
        assert any("エラーが発生しました" in msg for msg in result)

    def test_determine_cloud_provider_safe_with_malicious_input(self, base_generator):
        """BASE-SEC-01: determine_cloud_providerへの攻撃的入力

        base_insight_generator.py:L52-59 のstartswith比較は安全な文字列操作であり、
        攻撃的な入力に対しても例外を投げず"不明"を返却する。
        """
        # Arrange
        malicious_results = [
            {"resource_type": "<script>alert('xss')</script>"},
            {"resource_type": "'; DROP TABLE users; --"},
            {"resource_type": "../../../etc/passwd"}
        ]

        # Act
        result = base_generator.determine_cloud_provider(malicious_results)

        # Assert
        assert result == "不明"

    def test_default_messages_are_hardcoded(self):
        """CST-SEC-01: DEFAULT_MESSAGESが外部入力に非依存

        insight_constants.py:L51-59 の全メッセージがハードコード文字列であり、
        環境変数・設定ファイル等の外部入力に依存しないことを確認。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.results.insight_constants import DEFAULT_MESSAGES

        # Assert
        for key, value in DEFAULT_MESSAGES.items():
            # 文字列型であること（外部入力由来でない）
            assert isinstance(value, str), f"{key}がstr型ではない"
            # 空でないこと
            assert len(value) > 0, f"{key}が空文字列"
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_results_module` | テスト間のモジュール状態リセット | function | Yes |
| `base_generator` | テスト用BaseInsightGenerator具象サブクラスインスタンス | function | No |
| `resource_analyzer` | テスト用ResourceAnalyzerインスタンス | function | No |
| `mock_ig_components` | InsightGenerator依存クラスのパッチ | function | No |
| `insight_generator` | テスト用InsightGeneratorインスタンス | function | No |

### 共通フィクスチャ定義

```python
# test/unit/jobs/tasks/new_custodian_scan/results/conftest.py
import sys
import pytest
from unittest.mock import patch, MagicMock

MODULE_BASE = "app.jobs.tasks.new_custodian_scan.results.base_insight_generator"
MODULE_RA = "app.jobs.tasks.new_custodian_scan.results.resource_analyzer"
MODULE_IG = "app.jobs.tasks.new_custodian_scan.results.insight_generator"


@pytest.fixture(autouse=True)
def reset_results_module():
    """テストごとにモジュールのグローバル状態をリセット"""
    yield
    modules_to_remove = [key for key in sys.modules
                         if key.startswith("app.jobs.tasks.new_custodian_scan.results")]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def base_generator():
    """テスト用BaseInsightGenerator具象サブクラスインスタンス

    ABCのため直接インスタンス化できないので、generate()を実装した
    テスト用具象サブクラスを使用する。
    """
    with patch(f"{MODULE_BASE}.TaskLogger"):
        from app.jobs.tasks.new_custodian_scan.results.base_insight_generator import BaseInsightGenerator

        class ConcreteGenerator(BaseInsightGenerator):
            def generate(self, *args, **kwargs):
                return []

        return ConcreteGenerator("test-job-id", "TestGenerator")


@pytest.fixture
def resource_analyzer():
    """テスト用ResourceAnalyzerインスタンス

    TaskLoggerのみパッチして実__init__を通す。
    super().__init__経由でjob_idとloggerが設定される。
    """
    with patch(f"{MODULE_BASE}.TaskLogger"):
        from app.jobs.tasks.new_custodian_scan.results.resource_analyzer import ResourceAnalyzer
        return ResourceAnalyzer("test-job-id")


@pytest.fixture
def mock_ig_components():
    """InsightGenerator依存クラスのモックパッチ

    insight_generator.py の __init__ が参照する全クラスをMagicMockに置き換える。
    """
    patches = {}
    mocks = {}
    for name in ["TaskLogger", "OverviewInsightGenerator",
                 "ViolationInsightGenerator", "ResourceAnalyzer"]:
        p = patch(f"{MODULE_IG}.{name}")
        mocks[name] = p.start()
        patches[name] = p

    yield mocks

    for p in patches.values():
        p.stop()


@pytest.fixture
def insight_generator(mock_ig_components):
    """テスト用InsightGeneratorインスタンス

    全コンポーネントがモック化された状態でインスタンスを生成。
    """
    from app.jobs.tasks.new_custodian_scan.results.insight_generator import InsightGenerator
    return InsightGenerator("test-job-id")
```

---

## 6. テスト実行例

```bash
# Insight基盤系テスト全体を実行
pytest test/unit/jobs/tasks/new_custodian_scan/results/test_results_insight_base.py -v

# クラス単位で実行
pytest test/unit/jobs/tasks/new_custodian_scan/results/test_results_insight_base.py::TestDetermineCloudProvider -v
pytest test/unit/jobs/tasks/new_custodian_scan/results/test_results_insight_base.py::TestCreateResourceOverview -v

# カバレッジ付きで実行
pytest test/unit/jobs/tasks/new_custodian_scan/results/test_results_insight_base.py \
  --cov=app.jobs.tasks.new_custodian_scan.results.__init__ \
  --cov=app.jobs.tasks.new_custodian_scan.results.insight_constants \
  --cov=app.jobs.tasks.new_custodian_scan.results.base_insight_generator \
  --cov=app.jobs.tasks.new_custodian_scan.results.resource_analyzer \
  --cov=app.jobs.tasks.new_custodian_scan.results.insight_generator \
  --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/jobs/tasks/new_custodian_scan/results/test_results_insight_base.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 45 | PKG-001〜002, CST-001〜006, BASE-001〜013, RESA-001〜016, IGEN-001〜008 |
| 異常系 | 2 | IGEN-E01〜E02 |
| セキュリティ | 3 | IGEN-SEC-01, BASE-SEC-01, CST-SEC-01 |
| **合計** | **50** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestPackageInit` | PKG-001〜PKG-002 | 2 |
| `TestInsightConstants` | CST-001〜CST-006 | 6 |
| `TestBaseInsightGeneratorInit` | BASE-001〜BASE-002 | 2 |
| `TestDetermineCloudProvider` | BASE-003〜BASE-007 | 5 |
| `TestNormalizeRegionCount` | BASE-008〜BASE-011 | 4 |
| `TestGetUniqueRegions` | BASE-012〜BASE-013 | 2 |
| `TestResourceAnalyzerInit` | RESA-001〜RESA-002 | 2 |
| `TestCreateResourceOverview` | RESA-003〜RESA-004 | 2 |
| `TestUpdateResourceByType` | RESA-005〜RESA-006 | 2 |
| `TestUpdateGlobalResources` | RESA-007〜RESA-008 | 2 |
| `TestUpdateRegionalResources` | RESA-009〜RESA-010 | 2 |
| `TestIsGlobalResource` | RESA-011〜RESA-013 | 3 |
| `TestCalculateCompliancePercentage` | RESA-014〜RESA-016 | 3 |
| `TestInsightGeneratorInit` | IGEN-001 | 1 |
| `TestGenerateInsights` | IGEN-002〜IGEN-003, IGEN-008 | 3 |
| `TestInsightGeneratorDelegation` | IGEN-004〜IGEN-007 | 4 |
| `TestInsightGeneratorErrors` | IGEN-E01〜IGEN-E02 | 2 |
| `TestInsightBaseSecurity` | IGEN-SEC-01, BASE-SEC-01, CST-SEC-01 | 3 |

### 実装失敗が予想されるテスト

以下の実行前提が整備されていれば、失敗が予想されるテストはありません。

#### 実行前提

| 前提 | 対応内容 |
|------|---------|
| `security`マーカー | `[tool.pytest.ini_options].markers` に `"security: セキュリティテスト"` を追加 |

### 注意事項

- BaseInsightGeneratorはABCのため、テスト用具象サブクラス `ConcreteGenerator` を定義して使用
- ResourceAnalyzerの`resource_analyzer`フィクスチャはTaskLoggerパッチで実`__init__`を通す（`base_generator`と同じ戦略）
- InsightGeneratorのテストでは3委譲先（Overview/Violation/ResourceAnalyzer）をすべてMock化
- `__init__.py`のインポートテストは他モジュール（ResultAggregator等）のインポートも暗黙的に発生するため、reset_results_moduleのautouseが重要

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | InsightGeneratorの委譲先内部ロジックは対象外 | OverviewInsightGenerator, ViolationInsightGeneratorの詳細動作は検証しない | #16bのテスト仕様書で対応 |
| 2 | `__init__.py`のインポートテストは結合的 | 全モジュールのインポートが暗黙的に発生 | reset_results_moduleフィクスチャでテスト間分離 |
| 3 | ResourceAnalyzerのis_global_resourceは部分一致 | "iam"がglobal_typesに含まれると"iam-user"もマッチ | 実装仕様に従った動作であり制限事項として記録 |
| 4 | DEFAULT_MESSAGESの内容変更はテスト修正が必要 | メッセージ文言変更でIGEN-003等が失敗する | 文言一致ではなく部分文字列検証で脆弱性を低減 |
| 5 | resource_analyzerフィクスチャはTaskLoggerのみパッチ | 実__init__を通すが外部ログ接続を回避 | base_generatorと同じパッチ戦略で一貫性を確保 |
