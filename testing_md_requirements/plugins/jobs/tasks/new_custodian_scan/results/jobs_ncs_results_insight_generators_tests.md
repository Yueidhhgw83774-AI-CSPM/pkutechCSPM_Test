# jobs/tasks/new_custodian_scan/results Insight生成器系 テストケース

## 1. 概要

`results/` サブディレクトリのInsight生成器2ファイル（`overview_insight_generator.py`, `violation_insight_generator.py`）をまとめたテスト仕様書。スキャン概要・コンプライアンス評価・違反分析・動的インサイト生成を担う。

### 1.1 対象クラス

| クラス | ファイル | 行数 | 責務 |
|--------|---------|------|------|
| `OverviewInsightGenerator` | `overview_insight_generator.py` | 346 | スキャン概要・コンプライアンス評価・リージョン分析のインサイト生成 |
| `ViolationInsightGenerator` | `violation_insight_generator.py` | 422 | 違反分析・重要度別分析・動的インサイト生成 |

### 1.2 カバレッジ目標: 90%

> **注記**: 両クラスともBaseInsightGeneratorを継承し、ルールベースのメッセージ生成がメイン。外部API呼び出しなし。pytest-asyncio不要。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象1 | `app/jobs/tasks/new_custodian_scan/results/overview_insight_generator.py` |
| テスト対象2 | `app/jobs/tasks/new_custodian_scan/results/violation_insight_generator.py` |
| テストコード | `test/unit/jobs/tasks/new_custodian_scan/results/test_results_insight_generators.py` |

### 1.4 補足情報

#### 依存関係

```
overview_insight_generator.py (OverviewInsightGenerator)
  ──→ BaseInsightGenerator（基底クラス、#16aでテスト済み）
  ──→ ComplianceThreshold, DEFAULT_MESSAGES（定数、#16aでテスト済み）

violation_insight_generator.py (ViolationInsightGenerator)
  ──→ BaseInsightGenerator（基底クラス、#16aでテスト済み）
  ──→ SeverityLevel, ViolationThreshold, ResourceDiversityThreshold,
      EfficiencyThreshold, DEFAULT_MESSAGES（定数、#16aでテスト済み）
```

#### テスト戦略

| テストカテゴリ | 手法 |
|--------------|------|
| `OverviewInsightGenerator` | 実インスタンスでメソッド単位テスト（TaskLoggerのみMock） |
| `ViolationInsightGenerator` | 実インスタンスでメソッド単位テスト（TaskLoggerのみMock） |

#### 主要分岐マップ

| クラス | メソッド | 行番号 | 条件 | 分岐数 |
|--------|---------|--------|------|--------|
| OIG | `_create_scan_overview_insight` | L96, L113 | regions_count==0, aggregated_scan_statistics有無 | 3 |
| OIG | `_format_overview` | L171 | total_resources_scanned > 0 | 2 |
| OIG | `_create_compliance_insight` | L275, L280, L287, L292, L294 | unique/fallback, 閾値3段 | 5 |
| OIG | `_create_region_insights` | L322, L327, L328, L334, L340 | successful >1/==1(list)/==1(other)/0, failed >0 | 5 |
| VIG | `generate` | L51 | total_violations > 0 | 2 |
| VIG | `_create_top_policy_insight` | L167 | total_violations > 0 | 2 |
| VIG | `_create_top_resource_insight` | L192, L202 | 空リスト、violations有無 | 3 |
| VIG | `_create_severity_insights` | L236, L247 | Critical>0 / elif High>0 | 3 |
| VIG | `_create_dynamic_insights` | L331 | try/except | 2 |
| VIG | `_create_trend_insight` | L341-L348 | NONE/MINOR/MODERATE/MAJOR | 4 |
| VIG | `_create_diversity_insight` | L358, L363 | HIGH/MEDIUM/未満 | 3 |
| VIG | `_create_efficiency_insight` | L373, L383, L385 | 空/EXCELLENT/GOOD/超過 | 4 |
| VIG | `_create_priority_insights` | L407, L412 | Critical/elif High/なし | 3 |

---

## 2. 正常系テストケース

### OverviewInsightGenerator (OIG)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| OIG-001 | 初期化 | job_id | job_id保持・logger生成 |
| OIG-002 | generate正常フロー（3インサイト統合） | 正常データ | scan+compliance+regionインサイト統合 |
| OIG-003 | generate scan_insightが空→スキップ | regions=[] | compliance+regionのみ |
| OIG-004 | _create_scan_overview_insight regions_count==0→空文字 | regions=[] | "" |
| OIG-005 | _create_scan_overview_insight aggregated_stats有り→詳細形式 | agg_stats非None | 詳細情報含む文字列 |
| OIG-006 | _create_scan_overview_insight aggregated_stats無し→基本形式 | agg_stats=None | ポリシー情報含む文字列 |
| OIG-007 | _format_overview 詳細形式（resources>0） | total_resources_scanned=100 | リソース数・違反数含む |
| OIG-008 | _format_overview 基本形式（resources==0） | total_resources_scanned=0 | ポリシー数含む |
| OIG-009 | _build_base_info フォーマット確認 | cloud_provider, account_id, regions_count | 定型文字列 |
| OIG-010 | _build_detailed_info フォーマット確認 | policies, resources, violations, rate | 定型文字列 |
| OIG-011 | _build_policy_info フォーマット確認 | policies, with_violations, compliant | 定型文字列 |
| OIG-012 | _create_compliance_insight ユニーク統計EXCELLENT | compliance_rate=85.0 | "セキュリティ体制が整っています" |
| OIG-013 | _create_compliance_insight ユニーク統計GOOD | compliance_rate=60.0 | "改善の余地があります" |
| OIG-014 | _create_compliance_insight ユニーク統計GOOD未満 | compliance_rate=30.0 | "早急な対策が必要です" |
| OIG-015 | _create_compliance_insight フォールバック（unique==0） | total_unique_policies=0 | 実行ベース統計使用 |
| OIG-016 | _create_compliance_insight ポリシーなし→デフォルト | total_policies=0 | DEFAULT_MESSAGES["no_policies"] |
| OIG-017 | _create_region_insights successful>1 | successful_regions=3リスト | "3個のリージョンで...完了" |
| OIG-018 | _create_region_insights successful==1（リスト） | successful_regions=["us-east-1"] | "リージョン「us-east-1」で...完了" |
| OIG-019 | _create_region_insights successful==1（非リスト） | successful_regions=1 | "1個のリージョンで...完了" |
| OIG-020 | _create_region_insights failed>0 | failed_regions=2リスト | "2個のリージョンで...失敗" |
| OIG-021 | _create_region_insights 成功+失敗混在 | successful=2, failed=1 | 2件のインサイト |

### ViolationInsightGenerator (VIG)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| VIG-001 | 初期化 | job_id | job_id保持・logger生成 |
| VIG-002 | generate violations有り→3セクション統合 | total_violations=5 | violation+severity+dynamic |
| VIG-003 | generate violations==0→violation_insightsスキップ | total_violations=0 | severity+dynamicのみ |
| VIG-004 | _get_violating_policies ソート確認 | 違反数バラバラ | 降順ソート |
| VIG-005 | _get_violating_policies violationsキーフォールバック | violations=3（violation_countなし） | violations_normalized=3 |
| VIG-006 | _get_violating_policies 空入力→[] | [] | [] |
| VIG-007 | _create_top_policy_insight 正常 | policy_name, violations | "最も多い違反は..." |
| VIG-008 | _create_top_policy_insight total==0→空文字 | total_violations=0 | "" |
| VIG-009 | _create_top_resource_insight 正常 | resource_by_type有り | "最も違反の多いリソース..." |
| VIG-010 | _create_top_resource_insight 空リスト→空文字 | resource_by_type=[] | "" |
| VIG-011 | _create_top_resource_insight violations==0→空文字 | top violations=0 | "" |
| VIG-012 | _create_severity_insights Critical有り | Critical=3 | "緊急対応が必要" |
| VIG-013 | _create_severity_insights High有り（Criticalなし） | High=5, Critical=0 | "優先的な対応が推奨" |
| VIG-014 | _create_severity_insights Critical/Highなし→[] | Medium=3のみ | [] |
| VIG-015 | _count_violations_by_severity 正常カウント | 複数重要度のポリシー | 4キーの辞書 |
| VIG-016 | _count_violations_by_severity 未知severity無視 | severity="Unknown" | カウント0のまま |
| VIG-017 | _create_trend_insight NONE→all_compliant | 0 | DEFAULT_MESSAGES["all_compliant"] |
| VIG-018 | _create_trend_insight MINOR | 3 | DEFAULT_MESSAGES["minor_violations"] |
| VIG-019 | _create_trend_insight MODERATE | 15 | DEFAULT_MESSAGES["moderate_violations"] |
| VIG-020 | _create_trend_insight MAJOR | 51 | DEFAULT_MESSAGES["major_violations"] |
| VIG-021 | _create_diversity_insight HIGH（5種類以上） | 6種類 | "幅広いセキュリティカバレッジ" |
| VIG-022 | _create_diversity_insight MEDIUM（2-4種類） | 3種類 | "カバーしています" |
| VIG-023 | _create_diversity_insight 未満→空文字 | 1種類 | "" |
| VIG-024 | _create_efficiency_insight 空ポリシー→空文字 | [] | "" |
| VIG-025 | _create_efficiency_insight EXCELLENT（≤10%） | 1/20=5% | "非常に良好" |
| VIG-026 | _create_efficiency_insight GOOD（≤30%） | 5/20=25% | "概ね良好" |
| VIG-027 | _create_efficiency_insight 超過→空文字 | 10/20=50% | "" |
| VIG-028 | _create_priority_insights Critical有り | Critical違反ポリシー | "緊急対応が必要" |
| VIG-029 | _create_priority_insights High有り（Criticalなし） | High違反ポリシー | "優先対応が推奨" |
| VIG-030 | _create_priority_insights なし→[] | Mediumのみ | [] |
| VIG-031 | _calculate_percentage 正常計算 | value=25, total=100 | 25.0 |
| VIG-032 | _calculate_percentage total==0→0 | value=5, total=0 | 0.0 |

### 2.1 OverviewInsightGenerator テスト

```python
# test/unit/jobs/tasks/new_custodian_scan/results/test_results_insight_generators.py
import pytest
from unittest.mock import patch, MagicMock

MODULE_BASE = "app.jobs.tasks.new_custodian_scan.results.base_insight_generator"


class TestOverviewInsightGeneratorInit:
    """OverviewInsightGenerator初期化テスト"""

    def test_init(self, overview_generator):
        """OIG-001: 初期化

        overview_insight_generator.py:L19-26 をカバー。
        """
        # Assert
        assert overview_generator.job_id == "test-job-id"
        assert overview_generator.logger is not None


class TestOverviewGenerate:
    """OverviewInsightGenerator.generate テスト"""

    def test_normal_flow_three_insights(self, overview_generator):
        """OIG-002: generate正常フロー（3インサイト統合）

        overview_insight_generator.py:L28-69 の3段階生成をカバー。
        scan_insight + compliance_insight + region_insightsが統合される。
        """
        # Arrange
        scan_metadata = {
            "regions": ["us-east-1", "eu-west-1"],
            "successful_regions": ["us-east-1", "eu-west-1"],
            "failed_regions": []
        }
        basic_statistics = {
            "total_violations": 5,
            "total_unique_policies": 10,
            "unique_policies_compliant": 9,
            "unique_policy_compliance_percentage": 90.0,
        }

        # Act
        result = overview_generator.generate(
            cloud_provider="AWS", account_id="123456",
            scan_metadata=scan_metadata,
            basic_statistics=basic_statistics,
            aggregated_scan_statistics=None
        )

        # Assert
        assert len(result) == 3  # scan概要 + compliance + region(>1)
        assert any("アカウント" in r for r in result)  # scan概要
        assert any("セキュリティ体制" in r for r in result)  # compliance
        assert any("リージョン" in r and "完了" in r for r in result)  # region

    def test_empty_regions_skips_scan_insight(self, overview_generator):
        """OIG-003: generate scan_insightが空→スキップ

        overview_insight_generator.py:L57-58 のif scan_insightをカバー。
        regions空でscan_insightが""になるケース。
        """
        # Arrange
        scan_metadata = {"regions": [], "successful_regions": [], "failed_regions": []}
        basic_statistics = {
            "total_unique_policies": 10,
            "unique_policies_compliant": 10,
            "unique_policy_compliance_percentage": 100.0,
        }

        # Act
        result = overview_generator.generate(
            cloud_provider="AWS", account_id="123456",
            scan_metadata=scan_metadata,
            basic_statistics=basic_statistics
        )

        # Assert
        # scan概要はregions空で""→スキップされる
        assert not any("アカウント" in r and "リージョンに対して" in r for r in result)
        # compliance_insightは含まれる
        assert any("セキュリティ体制" in r or "適合率" in r for r in result)


class TestCreateScanOverviewInsight:
    """スキャン概要インサイト作成テスト"""

    def test_regions_count_zero_returns_empty(self, overview_generator):
        """OIG-004: _create_scan_overview_insight regions_count==0→空文字

        overview_insight_generator.py:L96-97 の空リージョン分岐をカバー。
        """
        # Arrange
        scan_metadata = {"regions": []}

        # Act
        result = overview_generator._create_scan_overview_insight(
            "AWS", "123456", scan_metadata, {}, None
        )

        # Assert
        assert result == ""

    def test_with_aggregated_stats_detailed(self, overview_generator):
        """OIG-005: _create_scan_overview_insight aggregated_stats有り→詳細形式

        overview_insight_generator.py:L113-119 のagg_stats有り分岐をカバー。
        total_resources_scanned > 0 で詳細形式になる。
        """
        # Arrange
        scan_metadata = {"regions": ["us-east-1"]}
        basic_stats = {"total_violations": 3, "total_policies": 5,
                       "total_unique_policies": 5}
        agg_stats = {"total_scanned": 100, "overall_compliance_rate": 80.0}

        # Act
        result = overview_generator._create_scan_overview_insight(
            "AWS", "123456", scan_metadata, basic_stats, agg_stats
        )

        # Assert
        assert "100" in result  # リソース数
        assert "80.0%" in result  # コンプライアンス率

    def test_without_aggregated_stats_basic(self, overview_generator):
        """OIG-006: _create_scan_overview_insight aggregated_stats無し→基本形式

        overview_insight_generator.py:L113 のagg_stats=None→L111-112のデフォルト値使用。
        total_resources_scanned==0 で基本形式になる。
        """
        # Arrange
        scan_metadata = {"regions": ["us-east-1"]}
        basic_stats = {"total_violations": 3, "total_policies": 5,
                       "total_unique_policies": 5,
                       "policies_with_violations": 2,
                       "policies_compliant": 3}

        # Act
        result = overview_generator._create_scan_overview_insight(
            "AWS", "123456", scan_metadata, basic_stats, None
        )

        # Assert
        assert "ポリシー" in result
        assert "適合" in result


class TestFormatOverview:
    """概要フォーマットテスト"""

    def test_detailed_format_with_resources(self, overview_generator):
        """OIG-007: _format_overview 詳細形式（resources>0）

        overview_insight_generator.py:L171-176 のtotal_resources_scanned>0分岐をカバー。
        """
        # Act
        result = overview_generator._format_overview(
            cloud_provider="AWS", account_id="123456",
            regions_count=2, total_unique_policies=10,
            total_resources_scanned=500, total_violations=5,
            overall_compliance_rate=90.0
        )

        # Assert
        assert "500" in result
        assert "90.0%" in result
        assert "AWS" in result

    def test_basic_format_without_resources(self, overview_generator):
        """OIG-008: _format_overview 基本形式（resources==0）

        overview_insight_generator.py:L177-182 のelse分岐をカバー。
        """
        # Act
        result = overview_generator._format_overview(
            cloud_provider="Azure", account_id="sub-123",
            regions_count=1, total_unique_policies=5,
            policies_with_violations=2, policies_compliant=3
        )

        # Assert
        assert "Azure" in result
        assert "5個のポリシー" in result


class TestBuildInfoMethods:
    """情報構築メソッドテスト"""

    def test_build_base_info(self, overview_generator):
        """OIG-009: _build_base_info フォーマット確認

        overview_insight_generator.py:L201-204 の基本情報文字列生成をカバー。
        """
        # Act
        result = overview_generator._build_base_info("AWS", "123456", 3)

        # Assert
        assert "AWS" in result
        assert "123456" in result
        assert "3個のリージョン" in result

    def test_build_detailed_info(self, overview_generator):
        """OIG-010: _build_detailed_info フォーマット確認

        overview_insight_generator.py:L225-231 の詳細情報文字列生成をカバー。
        """
        # Act
        result = overview_generator._build_detailed_info(10, 500, 5, 90.0)

        # Assert
        assert "500" in result
        assert "10個のポリシー" in result
        assert "5" in result
        assert "90.0%" in result

    def test_build_policy_info(self, overview_generator):
        """OIG-011: _build_policy_info フォーマット確認

        overview_insight_generator.py:L250-254 のポリシー情報文字列生成をカバー。
        """
        # Act
        result = overview_generator._build_policy_info(10, 3, 7)

        # Assert
        assert "10個のポリシー" in result
        assert "3個の違反" in result
        assert "7個が適合" in result


class TestCreateComplianceInsight:
    """コンプライアンス評価インサイトテスト"""

    def test_unique_stats_excellent(self, overview_generator):
        """OIG-012: _create_compliance_insight ユニーク統計EXCELLENT

        overview_insight_generator.py:L287-291 の>=80.0分岐をカバー。
        """
        # Arrange
        stats = {
            "total_unique_policies": 10,
            "unique_policies_compliant": 9,
            "unique_policy_compliance_percentage": 90.0,
        }

        # Act
        result = overview_generator._create_compliance_insight(stats)

        # Assert
        assert "セキュリティ体制が整っています" in result

    def test_unique_stats_good(self, overview_generator):
        """OIG-013: _create_compliance_insight ユニーク統計GOOD

        overview_insight_generator.py:L292-293 の>=50.0分岐をカバー。
        """
        # Arrange
        stats = {
            "total_unique_policies": 10,
            "unique_policies_compliant": 6,
            "unique_policy_compliance_percentage": 60.0,
        }

        # Act
        result = overview_generator._create_compliance_insight(stats)

        # Assert
        assert "改善の余地があります" in result

    def test_unique_stats_below_good(self, overview_generator):
        """OIG-014: _create_compliance_insight ユニーク統計GOOD未満

        overview_insight_generator.py:L294-295 のelse分岐をカバー。
        """
        # Arrange
        stats = {
            "total_unique_policies": 10,
            "unique_policies_compliant": 2,
            "unique_policy_compliance_percentage": 20.0,
        }

        # Act
        result = overview_generator._create_compliance_insight(stats)

        # Assert
        assert "早急な対策が必要です" in result

    def test_fallback_to_execution_stats(self, overview_generator):
        """OIG-015: _create_compliance_insight フォールバック（unique==0）

        overview_insight_generator.py:L275-278 のフォールバック分岐をカバー。
        total_unique_policies==0 で実行ベース統計を使用。
        """
        # Arrange
        stats = {
            "total_unique_policies": 0,
            "total_policies": 10,
            "policies_compliant": 9,
            "compliance_percentage": 90.0,
        }

        # Act
        result = overview_generator._create_compliance_insight(stats)

        # Assert
        assert "セキュリティ体制が整っています" in result

    def test_no_policies_returns_default(self, overview_generator):
        """OIG-016: _create_compliance_insight ポリシーなし→デフォルト

        overview_insight_generator.py:L280-281 のtotal_policies==0分岐をカバー。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.results.insight_constants import DEFAULT_MESSAGES
        stats = {"total_unique_policies": 0, "total_policies": 0}

        # Act
        result = overview_generator._create_compliance_insight(stats)

        # Assert
        assert result == DEFAULT_MESSAGES["no_policies"]


class TestCreateRegionInsights:
    """リージョン分析インサイトテスト"""

    def test_successful_regions_multiple(self, overview_generator):
        """OIG-017: _create_region_insights successful>1

        overview_insight_generator.py:L322-326 のsuccessful>1分岐をカバー。
        """
        # Arrange
        metadata = {
            "successful_regions": ["us-east-1", "eu-west-1", "ap-northeast-1"],
            "failed_regions": []
        }

        # Act
        result = overview_generator._create_region_insights(metadata)

        # Assert
        assert any("3個のリージョン" in r and "正常に完了" in r for r in result)

    def test_successful_regions_single_list(self, overview_generator):
        """OIG-018: _create_region_insights successful==1（リスト）

        overview_insight_generator.py:L327-333 のsuccessful==1+list分岐をカバー。
        """
        # Arrange
        metadata = {"successful_regions": ["us-east-1"], "failed_regions": []}

        # Act
        result = overview_generator._create_region_insights(metadata)

        # Assert
        assert any("us-east-1" in r and "正常に完了" in r for r in result)

    def test_successful_regions_single_non_list(self, overview_generator):
        """OIG-019: _create_region_insights successful==1（非リスト）

        overview_insight_generator.py:L334-337 のelse分岐をカバー。
        successful_regionsがintの場合、isinstance(1, list)はFalse。
        """
        # Arrange
        metadata = {"successful_regions": 1, "failed_regions": []}

        # Act
        result = overview_generator._create_region_insights(metadata)

        # Assert
        assert any("1個のリージョン" in r and "正常に完了" in r for r in result)

    def test_failed_regions(self, overview_generator):
        """OIG-020: _create_region_insights failed>0

        overview_insight_generator.py:L340-344 のfailed>0分岐をカバー。
        """
        # Arrange
        metadata = {"successful_regions": [], "failed_regions": ["us-east-1", "eu-west-1"]}

        # Act
        result = overview_generator._create_region_insights(metadata)

        # Assert
        assert any("2個のリージョンでスキャンが失敗" in r for r in result)

    def test_successful_and_failed_combined(self, overview_generator):
        """OIG-021: _create_region_insights 成功+失敗混在

        overview_insight_generator.py:L322-344 の成功+失敗の両方が存在するケース。
        """
        # Arrange
        metadata = {
            "successful_regions": ["us-east-1", "eu-west-1"],
            "failed_regions": ["ap-northeast-1"]
        }

        # Act
        result = overview_generator._create_region_insights(metadata)

        # Assert
        assert len(result) == 2
        assert any("正常に完了" in r for r in result)
        assert any("失敗" in r for r in result)
```

### 2.2 ViolationInsightGenerator テスト

```python
class TestViolationInsightGeneratorInit:
    """ViolationInsightGenerator初期化テスト"""

    def test_init(self, violation_generator):
        """VIG-001: 初期化

        violation_insight_generator.py:L22-29 をカバー。
        """
        # Assert
        assert violation_generator.job_id == "test-job-id"
        assert violation_generator.logger is not None


class TestViolationGenerate:
    """ViolationInsightGenerator.generate テスト"""

    def test_with_violations(self, violation_generator):
        """VIG-002: generate violations有り→3セクション統合

        violation_insight_generator.py:L31-69 のtotal_violations>0分岐をカバー。
        violation_insights + severity_insights + dynamic_insightsが統合される。
        """
        # Arrange
        policy_results = [
            {"policy_name": "test-policy", "violation_count": 5,
             "severity": "Critical", "resource_type": "aws.ec2"}
        ]
        resource_overview = {
            "resource_by_type": [
                {"resource_type": "aws.ec2", "total_violations": 5}
            ]
        }

        # Act
        result = violation_generator.generate(policy_results, 5, resource_overview)

        # Assert — violation + severity + dynamicの各セクションから生成
        assert len(result) >= 3

    def test_without_violations_skips_violation_insights(self, violation_generator):
        """VIG-003: generate violations==0→violation_insightsスキップ

        violation_insight_generator.py:L51 のtotal_violations==0分岐をカバー。
        severity_insightsとdynamic_insightsのみ生成。
        """
        # Arrange
        policy_results = [
            {"policy_name": "test-policy", "violation_count": 0, "severity": "Low"}
        ]

        # Act
        result = violation_generator.generate(policy_results, 0, {})

        # Assert
        # total_violations==0なのでtrend_insightで"all_compliant"が返る
        from app.jobs.tasks.new_custodian_scan.results.insight_constants import DEFAULT_MESSAGES
        assert any(DEFAULT_MESSAGES["all_compliant"] in r for r in result)


class TestGetViolatingPolicies:
    """違反ポリシー取得テスト"""

    def test_sort_by_violations_descending(self, violation_generator):
        """VIG-004: _get_violating_policies ソート確認

        violation_insight_generator.py:L142-146 の降順ソートをカバー。
        """
        # Arrange
        policies = [
            {"policy_name": "a", "violation_count": 3},
            {"policy_name": "b", "violation_count": 10},
            {"policy_name": "c", "violation_count": 1}
        ]

        # Act
        result = violation_generator._get_violating_policies(policies)

        # Assert
        assert result[0]["policy_name"] == "b"
        assert result[1]["policy_name"] == "a"
        assert result[2]["policy_name"] == "c"

    def test_uses_violations_fallback_key(self, violation_generator):
        """VIG-005: _get_violating_policies violationsキーフォールバック

        violation_insight_generator.py:L131-134 のviolationsフォールバックをカバー。
        violation_countがない場合、violationsキーを使用。
        """
        # Arrange
        policies = [{"policy_name": "a", "violations": 5}]

        # Act
        result = violation_generator._get_violating_policies(policies)

        # Assert
        assert len(result) == 1
        assert result[0]["violations_normalized"] == 5

    def test_empty_input(self, violation_generator):
        """VIG-006: _get_violating_policies 空入力→[]

        violation_insight_generator.py:L128-146 のforループ未実行をカバー。
        """
        # Act
        result = violation_generator._get_violating_policies([])

        # Assert
        assert result == []


class TestCreateTopPolicyInsight:
    """トップポリシーインサイト作成テスト"""

    def test_normal_case(self, violation_generator):
        """VIG-007: _create_top_policy_insight 正常

        violation_insight_generator.py:L167-172 のtotal_violations>0分岐をカバー。
        """
        # Arrange
        top_policy = {
            "policy_name": "s3-encryption",
            "violations_normalized": 10,
            "severity": "High"
        }

        # Act
        result = violation_generator._create_top_policy_insight(top_policy, 20)

        # Assert
        assert "s3-encryption" in result
        assert "50.0%" in result

    def test_total_zero_returns_empty(self, violation_generator):
        """VIG-008: _create_top_policy_insight total==0→空文字

        violation_insight_generator.py:L173 のreturn ""をカバー。
        """
        # Arrange
        top_policy = {"policy_name": "test", "violations_normalized": 5,
                      "severity": "Medium"}

        # Act
        result = violation_generator._create_top_policy_insight(top_policy, 0)

        # Assert
        assert result == ""


class TestCreateTopResourceInsight:
    """トップリソースインサイト作成テスト"""

    def test_normal_case(self, violation_generator):
        """VIG-009: _create_top_resource_insight 正常

        violation_insight_generator.py:L196-214 の正常フローをカバー。
        """
        # Arrange
        resource_overview = {
            "resource_by_type": [
                {"resource_type": "aws.ec2", "total_violations": 10},
                {"resource_type": "aws.s3", "total_violations": 3}
            ]
        }

        # Act
        result = violation_generator._create_top_resource_insight(
            resource_overview, 13
        )

        # Assert
        assert "aws.ec2" in result
        assert "76.9%" in result

    def test_empty_resource_by_type(self, violation_generator):
        """VIG-010: _create_top_resource_insight 空リスト→空文字

        violation_insight_generator.py:L192-193 の空リスト分岐をカバー。
        """
        # Act
        result = violation_generator._create_top_resource_insight(
            {"resource_by_type": []}, 5
        )

        # Assert
        assert result == ""

    def test_zero_violations_returns_empty(self, violation_generator):
        """VIG-011: _create_top_resource_insight violations==0→空文字

        violation_insight_generator.py:L202-203 のviolations==0分岐をカバー。
        """
        # Arrange
        resource_overview = {
            "resource_by_type": [
                {"resource_type": "aws.ec2", "total_violations": 0}
            ]
        }

        # Act
        result = violation_generator._create_top_resource_insight(
            resource_overview, 0
        )

        # Assert
        assert result == ""


class TestCreateSeverityInsights:
    """重要度別分析テスト"""

    def test_critical_violations(self, violation_generator):
        """VIG-012: _create_severity_insights Critical有り

        violation_insight_generator.py:L236-245 のCritical>0分岐をカバー。
        """
        # Arrange
        policies = [
            {"violation_count": 3, "severity": "Critical"},
            {"violation_count": 2, "severity": "High"}
        ]

        # Act
        result = violation_generator._create_severity_insights(policies, 5)

        # Assert
        assert len(result) == 1
        assert "Critical" in result[0]
        assert "緊急対応" in result[0]

    def test_high_violations_no_critical(self, violation_generator):
        """VIG-013: _create_severity_insights High有り（Criticalなし）

        violation_insight_generator.py:L247-256 のelif High>0分岐をカバー。
        """
        # Arrange
        policies = [{"violation_count": 5, "severity": "High"}]

        # Act
        result = violation_generator._create_severity_insights(policies, 5)

        # Assert
        assert len(result) == 1
        assert "High" in result[0]
        assert "優先的な対応" in result[0]

    def test_no_critical_or_high(self, violation_generator):
        """VIG-014: _create_severity_insights Critical/Highなし→[]

        violation_insight_generator.py:L236,L247 の両分岐ともFalseのケース。
        """
        # Arrange
        policies = [{"violation_count": 3, "severity": "Medium"}]

        # Act
        result = violation_generator._create_severity_insights(policies, 3)

        # Assert
        assert result == []


class TestCountViolationsBySeverity:
    """重要度別カウントテスト"""

    def test_normal_count(self, violation_generator):
        """VIG-015: _count_violations_by_severity 正常カウント

        violation_insight_generator.py:L260-290 の正常カウントをカバー。
        """
        # Arrange
        policies = [
            {"violation_count": 3, "severity": "Critical"},
            {"violation_count": 5, "severity": "High"},
            {"violation_count": 2, "severity": "Medium"},
        ]

        # Act
        result = violation_generator._count_violations_by_severity(policies)

        # Assert
        assert result["Critical"] == 3
        assert result["High"] == 5
        assert result["Medium"] == 2
        assert result["Low"] == 0

    def test_unknown_severity_ignored(self, violation_generator):
        """VIG-016: _count_violations_by_severity 未知severity無視

        violation_insight_generator.py:L287 のif severity in severity_counts分岐をカバー。
        未知のseverityはカウントに含まれない。
        """
        # Arrange
        policies = [{"violation_count": 5, "severity": "Unknown"}]

        # Act
        result = violation_generator._count_violations_by_severity(policies)

        # Assert
        assert all(v == 0 for v in result.values())


class TestCreateTrendInsight:
    """トレンド分析テスト"""

    def test_none(self, violation_generator):
        """VIG-017: _create_trend_insight NONE→all_compliant

        violation_insight_generator.py:L341-342 のNONE分岐をカバー。
        """
        # Act
        from app.jobs.tasks.new_custodian_scan.results.insight_constants import DEFAULT_MESSAGES
        result = violation_generator._create_trend_insight(0)

        # Assert
        assert result == DEFAULT_MESSAGES["all_compliant"]

    def test_minor(self, violation_generator):
        """VIG-018: _create_trend_insight MINOR

        violation_insight_generator.py:L343-344 の<=5分岐をカバー。
        """
        # Act
        from app.jobs.tasks.new_custodian_scan.results.insight_constants import DEFAULT_MESSAGES
        result = violation_generator._create_trend_insight(3)

        # Assert
        assert result == DEFAULT_MESSAGES["minor_violations"]

    def test_moderate(self, violation_generator):
        """VIG-019: _create_trend_insight MODERATE

        violation_insight_generator.py:L345-346 の<=20分岐をカバー。
        """
        # Act
        from app.jobs.tasks.new_custodian_scan.results.insight_constants import DEFAULT_MESSAGES
        result = violation_generator._create_trend_insight(15)

        # Assert
        assert result == DEFAULT_MESSAGES["moderate_violations"]

    def test_major(self, violation_generator):
        """VIG-020: _create_trend_insight MAJOR

        violation_insight_generator.py:L347-348 のelse分岐をカバー。
        """
        # Act
        from app.jobs.tasks.new_custodian_scan.results.insight_constants import DEFAULT_MESSAGES
        result = violation_generator._create_trend_insight(51)

        # Assert
        assert result == DEFAULT_MESSAGES["major_violations"]


class TestCreateDiversityInsight:
    """リソース多様性分析テスト"""

    def test_high_diversity(self, violation_generator):
        """VIG-021: _create_diversity_insight HIGH（5種類以上）

        violation_insight_generator.py:L358-362 の>=5分岐をカバー。
        """
        # Arrange
        overview = {
            "resource_by_type": [{"resource_type": f"type{i}"} for i in range(6)]
        }

        # Act
        result = violation_generator._create_diversity_insight(overview)

        # Assert
        assert "6種類" in result
        assert "幅広いセキュリティカバレッジ" in result

    def test_medium_diversity(self, violation_generator):
        """VIG-022: _create_diversity_insight MEDIUM（2-4種類）

        violation_insight_generator.py:L363-364 の>=2分岐をカバー。
        """
        # Arrange
        overview = {
            "resource_by_type": [{"resource_type": f"type{i}"} for i in range(3)]
        }

        # Act
        result = violation_generator._create_diversity_insight(overview)

        # Assert
        assert "3種類" in result
        assert "カバーしています" in result

    def test_below_medium(self, violation_generator):
        """VIG-023: _create_diversity_insight 未満→空文字

        violation_insight_generator.py:L365 の<2分岐をカバー。
        """
        # Arrange
        overview = {"resource_by_type": [{"resource_type": "type0"}]}

        # Act
        result = violation_generator._create_diversity_insight(overview)

        # Assert
        assert result == ""


class TestCreateEfficiencyInsight:
    """効率性分析テスト"""

    def test_empty_policies(self, violation_generator):
        """VIG-024: _create_efficiency_insight 空ポリシー→空文字

        violation_insight_generator.py:L373-374 の空リスト分岐をカバー。
        """
        # Act
        result = violation_generator._create_efficiency_insight([])

        # Assert
        assert result == ""

    def test_excellent_rate(self, violation_generator):
        """VIG-025: _create_efficiency_insight EXCELLENT（≤10%）

        violation_insight_generator.py:L383-384 の<=10%分岐をカバー。
        1/20=5%の違反率。
        """
        # Arrange
        policies = [{"violation_count": 1}] + [{"violation_count": 0}] * 19

        # Act
        result = violation_generator._create_efficiency_insight(policies)

        # Assert
        assert "非常に良好" in result

    def test_good_rate(self, violation_generator):
        """VIG-026: _create_efficiency_insight GOOD（≤30%）

        violation_insight_generator.py:L385-386 の<=30%分岐をカバー。
        5/20=25%の違反率。
        """
        # Arrange
        policies = [{"violation_count": 1}] * 5 + [{"violation_count": 0}] * 15

        # Act
        result = violation_generator._create_efficiency_insight(policies)

        # Assert
        assert "概ね良好" in result

    def test_above_good(self, violation_generator):
        """VIG-027: _create_efficiency_insight 超過→空文字

        violation_insight_generator.py:L387 の>30%分岐をカバー。
        10/20=50%の違反率。
        """
        # Arrange
        policies = [{"violation_count": 1}] * 10 + [{"violation_count": 0}] * 10

        # Act
        result = violation_generator._create_efficiency_insight(policies)

        # Assert
        assert result == ""


class TestCreatePriorityInsights:
    """アクション優先度テスト"""

    def test_critical_policies(self, violation_generator):
        """VIG-028: _create_priority_insights Critical有り

        violation_insight_generator.py:L407-411 のcritical分岐をカバー。
        """
        # Arrange
        policies = [
            {"severity": "Critical", "violation_count": 3},
            {"severity": "High", "violation_count": 2}
        ]

        # Act
        result = violation_generator._create_priority_insights(policies)

        # Assert
        assert len(result) == 1
        assert "緊急対応" in result[0]
        assert "Critical" in result[0]

    def test_high_policies_no_critical(self, violation_generator):
        """VIG-029: _create_priority_insights High有り（Criticalなし）

        violation_insight_generator.py:L412-416 のelif high分岐をカバー。
        """
        # Arrange
        policies = [{"severity": "High", "violation_count": 5}]

        # Act
        result = violation_generator._create_priority_insights(policies)

        # Assert
        assert len(result) == 1
        assert "優先対応" in result[0]

    def test_no_critical_or_high(self, violation_generator):
        """VIG-030: _create_priority_insights なし→[]

        violation_insight_generator.py:L407,L412 の両分岐ともFalse。
        """
        # Arrange
        policies = [{"severity": "Medium", "violation_count": 3}]

        # Act
        result = violation_generator._create_priority_insights(policies)

        # Assert
        assert result == []


class TestCalculatePercentage:
    """パーセンテージ計算テスト"""

    def test_normal_calculation(self, violation_generator):
        """VIG-031: _calculate_percentage 正常計算

        violation_insight_generator.py:L421-422 の正常計算をカバー。
        """
        # Act
        result = violation_generator._calculate_percentage(25, 100)

        # Assert
        assert result == 25.0

    def test_total_zero(self, violation_generator):
        """VIG-032: _calculate_percentage total==0→0

        violation_insight_generator.py:L422 のtotal==0ガード句をカバー。
        """
        # Act
        result = violation_generator._calculate_percentage(5, 0)

        # Assert
        assert result == 0.0
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| VIG-E01 | _create_dynamic_insights例外→エラーメッセージ | 内部メソッドが例外 | 定型エラーメッセージ追加 |

### 3.1 異常系テスト

```python
class TestViolationInsightGeneratorErrors:
    """ViolationInsightGenerator異常系テスト"""

    def test_dynamic_insights_exception(self, violation_generator):
        """VIG-E01: _create_dynamic_insights例外→エラーメッセージ

        violation_insight_generator.py:L331-335 のexceptブロックをカバー。
        内部メソッドが例外を投げた場合、定型エラーメッセージが追加される。
        """
        # Arrange
        with patch.object(
            violation_generator, "_create_trend_insight",
            side_effect=RuntimeError("分析失敗")
        ):
            # Act
            result = violation_generator._create_dynamic_insights([], 0, {})

        # Assert
        assert any("エラーが発生しました" in r for r in result)
        violation_generator.logger.warning.assert_called()
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| OIG-SEC-01 | _build_base_infoへの攻撃的account_id | XSS/SQLi文字列 | 安全にフォーマット |
| VIG-SEC-01 | _create_top_policy_insightへの攻撃的policy_name | XSS文字列 | 安全にフォーマット |
| VIG-SEC-02 | _create_dynamic_insights例外詳細が戻り値に非露出 | 機密情報含む例外 | 定型メッセージのみ返却 |

```python
@pytest.mark.security
class TestInsightGeneratorsSecurity:
    """Insight生成器セキュリティテスト"""

    def test_base_info_safe_with_malicious_account_id(self, overview_generator):
        """OIG-SEC-01: _build_base_infoへの攻撃的account_id

        overview_insight_generator.py:L201-204 のf-string結合は安全な文字列操作。
        攻撃的入力でも例外なくフォーマットされる。
        """
        # Arrange
        malicious_id = "<script>alert('xss')</script>"

        # Act
        result = overview_generator._build_base_info("AWS", malicious_id, 1)

        # Assert — この層はプレーンテキスト生成のためエスケープ不要。
        # HTML表示時は表示層でエスケープが必要。
        assert malicious_id in result
        assert isinstance(result, str)

    def test_top_policy_safe_with_malicious_name(self, violation_generator):
        """VIG-SEC-01: _create_top_policy_insightへの攻撃的policy_name

        violation_insight_generator.py:L163-172 のf-stringフォーマットは安全。
        """
        # Arrange
        top_policy = {
            "policy_name": "'; DROP TABLE policies; --",
            "violations_normalized": 5,
            "severity": "High"
        }

        # Act
        result = violation_generator._create_top_policy_insight(top_policy, 10)

        # Assert
        # プレーンテキスト生成層のためそのまま含まれる。HTML表示時は表示層でエスケープが必要。
        assert isinstance(result, str)
        assert "DROP TABLE" in result

    def test_dynamic_insights_exception_details_not_leaked(
        self, violation_generator
    ):
        """VIG-SEC-02: _create_dynamic_insights例外詳細が戻り値に非露出

        violation_insight_generator.py:L331-335 で例外時、str(e)はlogger.warningに
        出力されるが、戻り値には定型メッセージのみが追加される。
        """
        # Arrange
        sensitive_error = "Connection to db://secret-host:5432/admin failed"
        with patch.object(
            violation_generator, "_create_trend_insight",
            side_effect=RuntimeError(sensitive_error)
        ):
            # Act
            result = violation_generator._create_dynamic_insights([], 0, {})

        # Assert
        for msg in result:
            assert "db://" not in msg
            assert "secret-host" not in msg
            assert "5432" not in msg
        assert any("エラーが発生しました" in r for r in result)
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_results_module` | テスト間のモジュール状態リセット（#16a conftest.pyで定義済み） | function | Yes |
| `overview_generator` | テスト用OverviewInsightGeneratorインスタンス | function | No |
| `violation_generator` | テスト用ViolationInsightGeneratorインスタンス | function | No |

### 共通フィクスチャ定義

```python
# test/unit/jobs/tasks/new_custodian_scan/results/conftest.py
# ※ 以下は #16a の conftest.py に追記する。
# ※ reset_results_module (autouse) と MODULE_BASE, pytest, patch 等の
#    import は既に定義済み。


@pytest.fixture
def overview_generator():
    """テスト用OverviewInsightGeneratorインスタンス

    TaskLoggerのみパッチして実__init__を通す。
    super().__init__経由でjob_idとloggerが設定される。
    """
    with patch(f"{MODULE_BASE}.TaskLogger"):
        from app.jobs.tasks.new_custodian_scan.results.overview_insight_generator import (
            OverviewInsightGenerator
        )
        return OverviewInsightGenerator("test-job-id")


@pytest.fixture
def violation_generator():
    """テスト用ViolationInsightGeneratorインスタンス

    TaskLoggerのみパッチして実__init__を通す。
    super().__init__経由でjob_idとloggerが設定される。
    """
    with patch(f"{MODULE_BASE}.TaskLogger"):
        from app.jobs.tasks.new_custodian_scan.results.violation_insight_generator import (
            ViolationInsightGenerator
        )
        return ViolationInsightGenerator("test-job-id")
```

---

## 6. テスト実行例

```bash
# Insight生成器テスト全体を実行
pytest test/unit/jobs/tasks/new_custodian_scan/results/test_results_insight_generators.py -v

# クラス単位で実行
pytest test/unit/jobs/tasks/new_custodian_scan/results/test_results_insight_generators.py::TestCreateComplianceInsight -v
pytest test/unit/jobs/tasks/new_custodian_scan/results/test_results_insight_generators.py::TestCreateSeverityInsights -v

# カバレッジ付きで実行
pytest test/unit/jobs/tasks/new_custodian_scan/results/test_results_insight_generators.py \
  --cov=app.jobs.tasks.new_custodian_scan.results.overview_insight_generator \
  --cov=app.jobs.tasks.new_custodian_scan.results.violation_insight_generator \
  --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/jobs/tasks/new_custodian_scan/results/test_results_insight_generators.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 53 | OIG-001〜OIG-021, VIG-001〜VIG-032 |
| 異常系 | 1 | VIG-E01 |
| セキュリティ | 3 | OIG-SEC-01, VIG-SEC-01, VIG-SEC-02 |
| **合計** | **57** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestOverviewInsightGeneratorInit` | OIG-001 | 1 |
| `TestOverviewGenerate` | OIG-002〜OIG-003 | 2 |
| `TestCreateScanOverviewInsight` | OIG-004〜OIG-006 | 3 |
| `TestFormatOverview` | OIG-007〜OIG-008 | 2 |
| `TestBuildInfoMethods` | OIG-009〜OIG-011 | 3 |
| `TestCreateComplianceInsight` | OIG-012〜OIG-016 | 5 |
| `TestCreateRegionInsights` | OIG-017〜OIG-021 | 5 |
| `TestViolationInsightGeneratorInit` | VIG-001 | 1 |
| `TestViolationGenerate` | VIG-002〜VIG-003 | 2 |
| `TestGetViolatingPolicies` | VIG-004〜VIG-006 | 3 |
| `TestCreateTopPolicyInsight` | VIG-007〜VIG-008 | 2 |
| `TestCreateTopResourceInsight` | VIG-009〜VIG-011 | 3 |
| `TestCreateSeverityInsights` | VIG-012〜VIG-014 | 3 |
| `TestCountViolationsBySeverity` | VIG-015〜VIG-016 | 2 |
| `TestCreateTrendInsight` | VIG-017〜VIG-020 | 4 |
| `TestCreateDiversityInsight` | VIG-021〜VIG-023 | 3 |
| `TestCreateEfficiencyInsight` | VIG-024〜VIG-027 | 4 |
| `TestCreatePriorityInsights` | VIG-028〜VIG-030 | 3 |
| `TestCalculatePercentage` | VIG-031〜VIG-032 | 2 |
| `TestViolationInsightGeneratorErrors` | VIG-E01 | 1 |
| `TestInsightGeneratorsSecurity` | OIG-SEC-01, VIG-SEC-01, VIG-SEC-02 | 3 |

### 実装失敗が予想されるテスト

以下の実行前提が整備されていれば、失敗が予想されるテストはありません。

#### 実行前提

| 前提 | 対応内容 |
|------|---------|
| `security`マーカー | `pyproject.toml` に定義済み（#16aで追加） |
| `reset_results_module` | `conftest.py` に #16a で定義済み |

### 注意事項

- 両クラスともBaseInsightGeneratorを継承（#16aでテスト済み）。継承メソッド（determine_cloud_provider, normalize_region_count, get_unique_regions）はここでは直接テストしない
- OIG/VIG共にTaskLoggerパッチ方式で実`__init__`を通す（#16aと同じ戦略）
- VIG-E01のpatch.objectは実インスタンスの内部メソッドをモックし、try/exceptの例外ハンドリングを検証
- VIG-002/VIG-003のgenerate()テストは実装全体のオーケストレーション動作を検証するため、結果の具体的な内容ではなく構造を確認

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | OIG._create_scan_overview_insightの統計取得パスが多岐 | total_unique_policies/total_policiesのフォールバック組合せが多い | 主要パス（unique有り/無し）のみテスト、細かい.get()デフォルトは間接カバー |
| 2 | VIG._create_top_resource_insightのviolations/total_violationsキー二重チェック | 両キーの組合せパターンが多い | 主要パス（total_violationsキー使用）をテスト、violationsキーは間接カバー |
| 3 | DEFAULT_MESSAGESの文言変更でVIG-017〜020等が失敗 | メッセージ定数に依存するアサーション | 定数参照による比較で脆弱性を低減 |
| 4 | _create_region_insightsの入力がnormalize_region_countに依存 | normalize_region_countの動作変更が間接的に影響 | 基底クラスのテスト（#16a）で保証 |
| 5 | VIG._create_violation_insightsはgenerateからのみ呼ばれる | 個別テストなし（generate経由で間接カバー） | VIG-002でgenerate全体のオーケストレーションを検証 |
