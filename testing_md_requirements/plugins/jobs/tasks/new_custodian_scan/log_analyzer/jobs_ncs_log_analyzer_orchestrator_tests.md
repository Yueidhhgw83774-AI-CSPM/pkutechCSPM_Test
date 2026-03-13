# jobs/tasks/new_custodian_scan/log_analyzer/orchestrator テストケース

## 1. 概要

`log_analyzer/orchestrator.py` のオーケストレーターテスト仕様書。全ログ解析コンポーネント（LogFileReader, LogPatternMatcher, PolicyStatusDeterminer）を統合し、依存性注入パターンで柔軟な設計を提供する `PolicyAnalysisOrchestrator` クラスを検証する。

### 1.1 対象クラス

| クラス | ファイル | 行数 | 責務 |
|--------|---------|------|------|
| `PolicyAnalysisOrchestrator` | `orchestrator.py` | 396 | ログ解析コンポーネント統合・YAML読み込み・結果構築・統計集約 |

### 1.2 カバレッジ目標: 90%

> **注記**: 依存性注入パターンにより、3つのコンポーネント（file_reader, pattern_matcher, status_determiner）をモック注入してテスト。内部メソッド（`_find_and_read_policy_yaml`, `_read_policy_yaml_metadata`, `_merge_metadata`）は複雑な分岐を含むため個別テストで高カバレッジを目指す。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/jobs/tasks/new_custodian_scan/log_analyzer/orchestrator.py` |
| テストコード | `test/unit/jobs/tasks/new_custodian_scan/log_analyzer/test_log_analyzer_orchestrator.py` |

### 1.4 補足情報

#### 依存関係

```
orchestrator.py (PolicyAnalysisOrchestrator)
  ──→ LogFileReader（DI注入 or 自動生成）
  ──→ LogPatternMatcher（DI注入 or 自動生成）
  ──→ PolicyStatusDeterminer（DI注入 or 自動生成）
  ──→ TaskLogger（ログ）
  ──→ os, glob, yaml（標準/外部ライブラリ）
  ──→ models.PolicyStatus, GLOBAL_AWS_RESOURCES
```

#### テスト戦略

| テストカテゴリ | 手法 |
|--------------|------|
| 初期化 | DI注入とデフォルト生成の両方を検証 |
| パブリックメソッド | 内部メソッドをパッチしてオーケストレーション動作を検証 |
| _build_result | モックlog_analysisと実dictを渡して出力構造を検証 |
| _discover_policy_directories | tmp_pathで実ディレクトリ構造を構築 |
| _find_and_read_policy_yaml | glob.globをパッチ、パス操作は実os |
| _read_policy_yaml_metadata | tmp_pathで実YAMLファイルを作成 |
| _merge_metadata | 純粋なdict操作のためモック不要 |

#### 主要分岐マップ

| メソッド | 行番号 | 条件 | 分岐数 |
|---------|--------|------|--------|
| `__init__` | L34-36 | DI注入 or デフォルト生成（3フィールド） | 6 |
| `analyze_policy_execution` | L40,61,72 | try/except、isinstance(resources, list) | 4 |
| `analyze_multi_region_scan` | L78,90,103 | try/except、error_occurred判定 | 4 |
| `_build_result` | L119,134 | yaml_metadata有無、titleフォールバック | 3 |
| `_discover_policy_directories` | L162 | metadata.json+log存在判定 | 2 |
| `_calculate_compliance_rate` | L190 | total==0 | 2 |
| `_find_and_read_policy_yaml` | L233,234,250 | aws.prefix、GLOBAL判定、yaml_files空 | 4 |
| `_read_policy_yaml_metadata` | L278,288,294,297,300 | 不在、非list、名前不一致、metadata空、uuid有無 | 6 |
| `_merge_metadata` | L353-390 | 6フィールド×2-3段階フォールバック | 15 |

---

## 2. 正常系テストケース

### 初期化 (ORC)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| ORC-001 | DI注入初期化 | 3コンポーネント注入 | 注入されたインスタンスが保持される |
| ORC-002 | デフォルト生成 | コンポーネント未指定 | 各クラスがjob_idで自動生成される |

### analyze_policy_execution (ORC)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| ORC-003 | 正常フロー | ファイル読み込み成功 | 完全なresult dict |
| ORC-004 | resourcesがdict | resources={} | resource_count=0 |
| ORC-005 | yaml_metadata取得成功 | YAML有 | _merge_metadata経由のmetadata |

### analyze_multi_region_scan (ORC)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| ORC-006 | 複数ポリシー正常 | 2ポリシー（エラーなし） | policy_results=2件、統計情報 |
| ORC-007 | エラーポリシー含む | 1成功+1エラー | error_summary集約 |
| ORC-008 | 空ディレクトリ | ポリシーなし | policy_results=[], 統計=0 |

### _build_result (ORC)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| ORC-009 | yaml_metadata有り | yaml_metadata提供 | _merge_metadata経由のmetadata |
| ORC-010 | yaml_metadata無し | yaml_metadata=None | custodian metadata直接参照 |
| ORC-011 | titleフォールバック | title未設定 | policy名にフォールバック |

### _discover_policy_directories (ORC)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| ORC-012 | 正常検出 | metadata.json+log有ディレクトリ | [(name, path), ...] |
| ORC-013 | 空ディレクトリ | 条件未達のディレクトリ | [] |

### ヘルパーメソッド (ORC)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| ORC-014 | _aggregate_error_info | エラー結果 | error_summary更新 |
| ORC-015 | _calculate_aggregated_statistics | 混合結果リスト | 各統計値正確 |
| ORC-016 | _calculate_compliance_rate total=0 | total=0 | 100.0 |
| ORC-017 | _calculate_compliance_rate 正常 | total=100, violation=20 | 80.0 |
| ORC-035 | _calculate_compliance_rate 違反>合計 | total=50, violation=100 | 0.0 |
| ORC-018 | _determine_resource_scope global | "iam" | "global" |
| ORC-019 | _determine_resource_scope regional | "ec2" | "regional" |
| ORC-020 | _create_error_result 構造 | policy_name, error_message | エラーdict構造 |

### _find_and_read_policy_yaml (ORC)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| ORC-021 | リージョナルリソース | resource_type="ec2" | 通常パスでYAML検索 |
| ORC-022 | グローバルリソース | resource_type="iam" | us-east-1パスに置換 |
| ORC-023 | aws.プレフィックス除去 | resource_type="aws.iam" | プレフィックス除去後にグローバル判定 |
| ORC-024 | YAMLファイル無し | glob結果空 | {} |

### _read_policy_yaml_metadata (ORC)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| ORC-025 | 正常抽出（uuid→recommendation_uuid） | 有効YAML | metadataにuuidマッピング |
| ORC-026 | ファイル不在 | 存在しないパス | {} |
| ORC-027 | policiesが非リスト | policies: "invalid" | {} |
| ORC-028 | ポリシー名不一致 | 別名のポリシー | {} |
| ORC-029 | metadata空 | metadata: {} | {} |
| ORC-030 | recommendation_uuid既存 | uuid+recommendation_uuid | uuidマッピングスキップ |

### _merge_metadata (ORC)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| ORC-031 | YAML優先 | 全フィールドYAML有 | YAML値で全フィールド設定 |
| ORC-032 | Custodianフォールバック | YAMLフィールド空 | Custodian値で全フィールド設定 |
| ORC-033 | デフォルトseverity | 両方severity無し | "Medium" |
| ORC-034 | titleフォールバック | 両方title無し | policy name |

### 2.1 初期化テスト

```python
# test/unit/jobs/tasks/new_custodian_scan/log_analyzer/test_log_analyzer_orchestrator.py
import pytest
import os
import json
import yaml
from unittest.mock import patch, MagicMock

MODULE_ORC = "app.jobs.tasks.new_custodian_scan.log_analyzer.orchestrator"


class TestOrchestratorInit:
    """オーケストレーター初期化テスト"""

    def test_di_injection(self, orchestrator, mock_file_reader, mock_pattern_matcher, mock_status_determiner):
        """ORC-001: DI注入初期化

        orchestrator.py:L24-36 のDI注入パスをカバー。
        3コンポーネント全てが注入されたインスタンスで保持される。
        """
        # Assert
        assert orchestrator.file_reader is mock_file_reader
        assert orchestrator.pattern_matcher is mock_pattern_matcher
        assert orchestrator.status_determiner is mock_status_determiner
        assert orchestrator.job_id == "test-job-id"

    def test_default_creation(self):
        """ORC-002: デフォルト生成

        orchestrator.py:L34-36 のデフォルト生成パスをカバー。
        コンポーネント未指定時にjob_idで自動生成される。
        """
        # Arrange
        with patch(f"{MODULE_ORC}.TaskLogger"), \
             patch(f"{MODULE_ORC}.LogFileReader") as MockFR, \
             patch(f"{MODULE_ORC}.LogPatternMatcher") as MockPM, \
             patch(f"{MODULE_ORC}.PolicyStatusDeterminer") as MockSD:
            from app.jobs.tasks.new_custodian_scan.log_analyzer.orchestrator import PolicyAnalysisOrchestrator

            # Act
            orc = PolicyAnalysisOrchestrator("job-default")

        # Assert
        MockFR.assert_called_once_with("job-default")
        MockPM.assert_called_once_with("job-default")
        MockSD.assert_called_once_with("job-default")
```

### 2.2 analyze_policy_execution テスト

```python
class TestAnalyzePolicyExecution:
    """個別ポリシー解析テスト"""

    def test_normal_flow(self, orchestrator, mock_file_reader, mock_pattern_matcher, mock_status_determiner, mock_log_analysis):
        """ORC-003: analyze_policy_execution 正常フロー

        orchestrator.py:L38-71 の正常フロー全体をカバー。
        ファイル読み込み→解析→ステータス判定→結果構築の一連の流れ。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.log_analyzer.models import PolicyStatus

        mock_file_reader.read_log_file.return_value = "log content"
        mock_file_reader.read_json_file.side_effect = [
            {"policy": {"resource": "ec2"}, "config": {"region": "ap-northeast-1"}},  # metadata
            [{"id": "i-123"}, {"id": "i-456"}]  # resources（list）
        ]
        mock_pattern_matcher.analyze_log_content.return_value = mock_log_analysis
        mock_status_determiner.determine_status.return_value = PolicyStatus.VIOLATION

        # _find_and_read_policy_yamlをモック化（個別テストで検証済み）
        orchestrator._find_and_read_policy_yaml = MagicMock(return_value={})

        # Act
        result = orchestrator.analyze_policy_execution("/output/policy-a", "policy-a")

        # Assert
        assert result["policy_name"] == "policy-a"
        assert result["status"] == "violation"
        assert result["violation_count"] == 2
        assert result["resource_type"] == "ec2"
        assert result["region"] == "ap-northeast-1"
        mock_pattern_matcher.analyze_log_content.assert_called_once_with("log content")

    def test_resources_is_dict(self, orchestrator, mock_file_reader, mock_pattern_matcher, mock_status_determiner, mock_log_analysis):
        """ORC-004: analyze_policy_execution resourcesがdict

        orchestrator.py:L61 のisinstance(resources, list)がFalseの場合をカバー。
        resources.jsonがdictの場合、resource_count=0となる。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.log_analyzer.models import PolicyStatus

        mock_file_reader.read_log_file.return_value = "log"
        mock_file_reader.read_json_file.side_effect = [
            {"policy": {"resource": "ec2"}, "config": {"region": "us-east-1"}},
            {"key": "value"}  # dictはlistではない
        ]
        mock_pattern_matcher.analyze_log_content.return_value = mock_log_analysis
        mock_status_determiner.determine_status.return_value = PolicyStatus.COMPLIANT
        orchestrator._find_and_read_policy_yaml = MagicMock(return_value={})

        # Act
        result = orchestrator.analyze_policy_execution("/output/policy-b", "policy-b")

        # Assert
        assert result["violation_count"] == 0

    def test_with_yaml_metadata(self, orchestrator, mock_file_reader, mock_pattern_matcher, mock_status_determiner, mock_log_analysis):
        """ORC-005: analyze_policy_execution yaml_metadata取得成功

        orchestrator.py:L57,65 のyaml_metadataが存在するフローをカバー。
        _find_and_read_policy_yamlが非空dictを返し、_build_resultに渡される。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.log_analyzer.models import PolicyStatus

        yaml_meta = {"severity": "Critical", "uuid": "yaml-uuid"}
        mock_file_reader.read_log_file.return_value = "log"
        mock_file_reader.read_json_file.side_effect = [
            {"policy": {"resource": "ec2", "metadata": {}}, "config": {"region": "us-east-1"}},
            []
        ]
        mock_pattern_matcher.analyze_log_content.return_value = mock_log_analysis
        mock_status_determiner.determine_status.return_value = PolicyStatus.COMPLIANT
        orchestrator._find_and_read_policy_yaml = MagicMock(return_value=yaml_meta)

        # Act
        result = orchestrator.analyze_policy_execution("/output/policy-c", "policy-c")

        # Assert - yaml_metadataが_merge_metadata経由で反映される
        assert result["metadata"]["severity"] == "Critical"
```

### 2.3 analyze_multi_region_scan テスト

```python
class TestAnalyzeMultiRegionScan:
    """複数リージョンスキャン解析テスト"""

    def test_normal_multi_region(self, orchestrator):
        """ORC-006: 複数ポリシー正常

        orchestrator.py:L76-102 の正常フローをカバー。
        2ポリシーを解析し、統計情報を集約する。
        """
        # Arrange
        result_a = {"status": "compliant", "violation_count": 0,
                     "error_details": {"error_occurred": False}}
        result_b = {"status": "violation", "violation_count": 3,
                     "error_details": {"error_occurred": False}}
        orchestrator._discover_policy_directories = MagicMock(
            return_value=[("policy-a", "/out/a"), ("policy-b", "/out/b")]
        )
        orchestrator.analyze_policy_execution = MagicMock(
            side_effect=[result_a, result_b]
        )

        # Act
        result = orchestrator.analyze_multi_region_scan("/custodian/output")

        # Assert
        assert len(result["policy_results"]) == 2
        assert result["aggregated_statistics"]["total_policies"] == 2
        assert result["aggregated_statistics"]["policies_with_violations"] == 1
        assert result["aggregated_statistics"]["total_violations"] == 3
        assert "analysis_timestamp" in result

    def test_with_error_policy(self, orchestrator):
        """ORC-007: エラーポリシー含む

        orchestrator.py:L90-91 のerror_occurred判定をカバー。
        エラーポリシーがerror_summaryに集約される。
        """
        # Arrange
        result_ok = {"status": "compliant", "violation_count": 0,
                      "error_details": {"error_occurred": False}}
        result_err = {"status": "error", "violation_count": 0,
                       "error_details": {"error_occurred": True, "error_type": "permission",
                                         "error_message": "Access denied"}}
        orchestrator._discover_policy_directories = MagicMock(
            return_value=[("ok-policy", "/out/ok"), ("err-policy", "/out/err")]
        )
        orchestrator.analyze_policy_execution = MagicMock(
            side_effect=[result_ok, result_err]
        )

        # Act
        result = orchestrator.analyze_multi_region_scan("/custodian/output")

        # Assert
        assert result["scan_errors_summary"]["total_errors"] == 1
        assert "permission" in result["scan_errors_summary"]["errors_by_type"]
        assert len(result["scan_errors_summary"]["failed_policies"]) == 1
        assert result["scan_errors_summary"]["failed_policies"][0]["policy_name"] == "err-policy"

    def test_empty_directory(self, orchestrator):
        """ORC-008: 空ディレクトリ

        orchestrator.py:L80-84 のポリシーディレクトリ0件をカバー。
        """
        # Arrange
        orchestrator._discover_policy_directories = MagicMock(return_value=[])

        # Act
        result = orchestrator.analyze_multi_region_scan("/empty/output")

        # Assert
        assert result["policy_results"] == []
        assert result["aggregated_statistics"]["total_policies"] == 0
        assert result["scan_errors_summary"]["total_errors"] == 0
```

### 2.4 _build_result テスト

```python
class TestBuildResult:
    """結果構築テスト"""

    def test_with_yaml_metadata(self, orchestrator, mock_log_analysis):
        """ORC-009: _build_result yaml_metadata有り

        orchestrator.py:L119-124 のyaml_metadata分岐（truthy）をカバー。
        _merge_metadataが呼ばれ、YAMLのmetadataが反映される。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.log_analyzer.models import PolicyStatus

        metadata = {"policy": {"resource": "ec2", "metadata": {"severity": "Low"}},
                     "config": {"region": "us-east-1"}}
        yaml_meta = {"severity": "Critical", "uuid": "yaml-uuid-123"}

        # Act
        result = orchestrator._build_result(
            "test-policy", metadata, mock_log_analysis, 5,
            PolicyStatus.VIOLATION, yaml_meta
        )

        # Assert
        assert result["metadata"]["severity"] == "Critical"
        assert result["metadata"]["recommendation_uuid"] == "yaml-uuid-123"

    def test_without_yaml_metadata(self, orchestrator, mock_log_analysis):
        """ORC-010: _build_result yaml_metadata無し

        orchestrator.py:L125-135 のyaml_metadata=None分岐をカバー。
        Custodianのmetadata.jsonから直接metadataを構築。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.log_analyzer.models import PolicyStatus

        metadata = {"policy": {"resource": "ec2", "metadata": {
            "uuid": "cust-uuid", "recommendation_id": "REC-001",
            "recommendation_version": "1.0", "policy_version": "2.0",
            "severity": "High", "title": "Test Title"
        }}, "config": {"region": "us-east-1"}}

        # Act
        result = orchestrator._build_result(
            "test-policy", metadata, mock_log_analysis, 0,
            PolicyStatus.COMPLIANT, None
        )

        # Assert
        assert result["metadata"]["recommendation_uuid"] == "cust-uuid"
        assert result["metadata"]["recommendation_id"] == "REC-001"
        assert result["metadata"]["severity"] == "High"
        assert result["metadata"]["title"] == "Test Title"

    def test_title_fallback(self, orchestrator, mock_log_analysis):
        """ORC-011: _build_result titleフォールバック

        orchestrator.py:L134 のtitle未設定時のフォールバックをカバー。
        policy_metadata.titleがNoneの場合、metadata.policy.nameにフォールバック。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.log_analyzer.models import PolicyStatus

        metadata = {"policy": {"resource": "ec2", "name": "fallback-name",
                     "metadata": {}}, "config": {"region": "us-east-1"}}

        # Act
        result = orchestrator._build_result(
            "test-policy", metadata, mock_log_analysis, 0,
            PolicyStatus.COMPLIANT, None
        )

        # Assert - policy_metadata.titleがないので、policy.nameにフォールバック
        assert result["metadata"]["title"] == "fallback-name"
```

### 2.5 _discover_policy_directories テスト

```python
class TestDiscoverPolicyDirectories:
    """ポリシーディレクトリ検索テスト"""

    def test_normal_discovery(self, orchestrator, tmp_path):
        """ORC-012: _discover_policy_directories 正常検出

        orchestrator.py:L158-164 のos.walk検索をカバー。
        metadata.json + custodian-run.log の両方が存在するディレクトリのみ検出。
        """
        # Arrange
        policy_a = tmp_path / "policy-a"
        policy_a.mkdir()
        (policy_a / "metadata.json").write_text("{}")
        (policy_a / "custodian-run.log").write_text("log")

        policy_b = tmp_path / "policy-b"
        policy_b.mkdir()
        (policy_b / "metadata.json").write_text("{}")
        (policy_b / "custodian-run.log").write_text("log")

        # metadataのみ（logなし）→検出されない
        incomplete = tmp_path / "incomplete"
        incomplete.mkdir()
        (incomplete / "metadata.json").write_text("{}")

        # Act
        result = orchestrator._discover_policy_directories(str(tmp_path))

        # Assert
        assert len(result) == 2
        names = [name for name, _ in result]
        assert "policy-a" in names
        assert "policy-b" in names

    def test_empty_directory(self, orchestrator, tmp_path):
        """ORC-013: _discover_policy_directories 空ディレクトリ

        orchestrator.py:L162 の条件未達ケース。
        """
        # Act
        result = orchestrator._discover_policy_directories(str(tmp_path))

        # Assert
        assert result == []
```

### 2.6 ヘルパーメソッドテスト

```python
class TestAggregateErrorInfo:
    """エラー情報集約テスト"""

    def test_error_aggregation(self, orchestrator):
        """ORC-014: _aggregate_error_info

        orchestrator.py:L166-175 のエラー集約ロジックをカバー。
        """
        # Arrange
        error_summary = {"total_errors": 0, "errors_by_type": {}, "failed_policies": []}
        result = {"error_details": {
            "error_type": "permission", "error_message": "Access denied"
        }}

        # Act
        orchestrator._aggregate_error_info(error_summary, result, "failed-policy")

        # Assert
        assert error_summary["total_errors"] == 1
        assert error_summary["errors_by_type"]["permission"] == 1
        assert error_summary["failed_policies"][0]["policy_name"] == "failed-policy"
        assert error_summary["failed_policies"][0]["error_type"] == "permission"


class TestCalculateAggregatedStatistics:
    """集約統計計算テスト"""

    def test_mixed_results(self, orchestrator):
        """ORC-015: _calculate_aggregated_statistics 混合結果

        orchestrator.py:L177-186 の集約ロジックをカバー。
        違反・準拠・リソースなし・エラーの混合結果で統計を検証。
        """
        # Arrange
        policy_results = [
            {"status": "violation", "violation_count": 3},
            {"status": "compliant", "violation_count": 0},
            {"status": "no_resources", "violation_count": 0},
            {"status": "error", "violation_count": 0},
        ]

        # Act
        stats = orchestrator._calculate_aggregated_statistics(policy_results)

        # Assert
        assert stats["total_policies"] == 4
        assert stats["policies_with_violations"] == 1
        assert stats["policies_compliant"] == 3  # violation_count==0が3件（error含む。L182はviolation_countのみで判定）
        assert stats["policies_with_no_resources"] == 1
        assert stats["policies_with_errors"] == 1
        assert stats["total_violations"] == 3


class TestCalculateComplianceRate:
    """コンプライアンス率計算テスト"""

    def test_zero_total(self, orchestrator):
        """ORC-016: _calculate_compliance_rate total=0

        orchestrator.py:L190-191 のtotal==0分岐をカバー。
        """
        # Act
        result = orchestrator._calculate_compliance_rate(0, 0)

        # Assert
        assert result == 100.0

    def test_normal_calculation(self, orchestrator):
        """ORC-017: _calculate_compliance_rate 正常計算

        orchestrator.py:L192-193 の正常計算をカバー。
        """
        # Act
        result = orchestrator._calculate_compliance_rate(100, 20)

        # Assert
        assert result == 80.0

    def test_violation_exceeds_total(self, orchestrator):
        """ORC-035: _calculate_compliance_rate 違反>合計

        orchestrator.py:L192 のmax(0, ...)負数防御をカバー。
        violation_count > total_resourcesの場合でも0.0が下限。
        """
        # Act
        result = orchestrator._calculate_compliance_rate(50, 100)

        # Assert
        assert result == 0.0


class TestDetermineResourceScope:
    """リソーススコープ判定テスト"""

    def test_global_resource(self, orchestrator):
        """ORC-018: _determine_resource_scope global

        orchestrator.py:L197 のGLOBAL_AWS_RESOURCES一致をカバー。
        """
        # Act & Assert
        assert orchestrator._determine_resource_scope("iam") == "global"
        assert orchestrator._determine_resource_scope("s3") == "global"

    def test_regional_resource(self, orchestrator):
        """ORC-019: _determine_resource_scope regional

        orchestrator.py:L197 のGLOBAL_AWS_RESOURCES不一致をカバー。
        """
        # Act & Assert
        assert orchestrator._determine_resource_scope("ec2") == "regional"
        assert orchestrator._determine_resource_scope("rds") == "regional"


class TestCreateErrorResult:
    """エラー結果作成テスト"""

    def test_error_result_structure(self, orchestrator):
        """ORC-020: _create_error_result 構造

        orchestrator.py:L199-211 のエラー結果dict構造をカバー。
        """
        # Act
        result = orchestrator._create_error_result("test-policy", "テストエラー")

        # Assert
        assert result["policy_name"] == "test-policy"
        assert result["status"] == "error"
        assert result["violation_count"] == 0
        assert result["resource_type"] == "unknown"
        assert result["error_details"]["error_occurred"] is True
        assert result["error_details"]["error_message"] == "テストエラー"
        assert result["resource_statistics"]["compliance_rate"] == 0.0
        assert result["execution_details"]["has_resources"] is False
```

### 2.7 _find_and_read_policy_yaml テスト

```python
class TestFindAndReadPolicyYaml:
    """YAMLファイル検索テスト"""

    def test_regional_resource(self, orchestrator):
        """ORC-021: リージョナルリソースYAML検索

        orchestrator.py:L234 のGLOBAL判定がFalseの場合をカバー。
        リージョナルリソースは親ディレクトリをそのまま使用。
        """
        # Arrange
        yaml_meta = {"severity": "High"}
        orchestrator._read_policy_yaml_metadata = MagicMock(return_value=yaml_meta)

        with patch(f"{MODULE_ORC}.glob.glob", return_value=["/tmp/x/region_ap/policy_test.yaml"]):
            # Act
            result = orchestrator._find_and_read_policy_yaml(
                "/tmp/x/region_ap/custodian_output/policy-a", "policy-a", "ec2"
            )

        # Assert
        assert result == yaml_meta
        orchestrator._read_policy_yaml_metadata.assert_called_once()

    def test_global_resource_path_replacement(self, orchestrator):
        """ORC-022: グローバルリソースus-east-1パス置換

        orchestrator.py:L234-242 のGLOBAL_AWS_RESOURCES一致時のパス置換をカバー。
        region_XXX → region_us-east-1に置換される。
        """
        # Arrange
        orchestrator._read_policy_yaml_metadata = MagicMock(return_value={"severity": "High"})
        captured_glob_args = []

        def mock_glob(pattern):
            captured_glob_args.append(pattern)
            return ["/tmp/x/region_us-east-1/policy_test.yaml"]

        with patch(f"{MODULE_ORC}.glob.glob", side_effect=mock_glob):
            # Act
            orchestrator._find_and_read_policy_yaml(
                "/tmp/x/region_ap-northeast-1/custodian_output/policy-a", "policy-a", "iam"
            )

        # Assert - glob検索パスがus-east-1に置換されている
        assert "region_us-east-1" in captured_glob_args[0]
        assert "region_ap-northeast-1" not in captured_glob_args[0]

    def test_aws_prefix_removal(self, orchestrator):
        """ORC-023: aws.プレフィックス除去

        orchestrator.py:L233 のremoveprefix("aws.")をカバー。
        "aws.iam"→"iam"に正規化後、GLOBAL判定に使用。
        """
        # Arrange
        orchestrator._read_policy_yaml_metadata = MagicMock(return_value={})
        captured_glob_args = []

        def mock_glob(pattern):
            captured_glob_args.append(pattern)
            return ["/tmp/x/region_us-east-1/policy_test.yaml"]

        with patch(f"{MODULE_ORC}.glob.glob", side_effect=mock_glob):
            # Act
            orchestrator._find_and_read_policy_yaml(
                "/tmp/x/region_ap-northeast-1/custodian_output/policy-a",
                "policy-a", "aws.iam"
            )

        # Assert - aws.iamが正規化されグローバル判定→us-east-1パス
        assert "region_us-east-1" in captured_glob_args[0]

    def test_no_yaml_files(self, orchestrator):
        """ORC-024: YAMLファイル無し

        orchestrator.py:L250-252 のyaml_files空分岐をカバー。
        """
        # Arrange
        with patch(f"{MODULE_ORC}.glob.glob", return_value=[]):
            # Act
            result = orchestrator._find_and_read_policy_yaml(
                "/tmp/x/region_ap/custodian_output/policy-a", "policy-a", "ec2"
            )

        # Assert
        assert result == {}
```

### 2.8 _read_policy_yaml_metadata テスト

```python
class TestReadPolicyYamlMetadata:
    """YAMLメタデータ抽出テスト"""

    def test_normal_extraction_with_uuid_mapping(self, orchestrator, tmp_path):
        """ORC-025: 正常抽出（uuid→recommendation_uuid）

        orchestrator.py:L300-301 のuuid→recommendation_uuidマッピングをカバー。
        YAMLにuuidがありrecommendation_uuidがない場合にマッピングされる。
        """
        # Arrange
        yaml_content = {"policies": [{
            "name": "test-policy",
            "metadata": {"uuid": "abc-123", "severity": "High", "title": "Test"}
        }]}
        yaml_file = tmp_path / "policy_test.yaml"
        yaml_file.write_text(yaml.dump(yaml_content))

        # Act
        result = orchestrator._read_policy_yaml_metadata(str(yaml_file), "test-policy")

        # Assert
        assert result["uuid"] == "abc-123"
        assert result["recommendation_uuid"] == "abc-123"
        assert result["severity"] == "High"

    def test_file_not_exists(self, orchestrator):
        """ORC-026: ファイル不在

        orchestrator.py:L278-280 のファイル不在分岐をカバー。
        """
        # Act
        result = orchestrator._read_policy_yaml_metadata("/nonexistent/file.yaml", "policy")

        # Assert
        assert result == {}

    def test_policies_not_list(self, orchestrator, tmp_path):
        """ORC-027: policiesが非リスト

        orchestrator.py:L288-290 のpoliciesが非リスト分岐をカバー。
        """
        # Arrange
        yaml_file = tmp_path / "policy_invalid.yaml"
        yaml_file.write_text(yaml.dump({"policies": "not_a_list"}))

        # Act
        result = orchestrator._read_policy_yaml_metadata(str(yaml_file), "policy")

        # Assert
        assert result == {}

    def test_policy_name_not_found(self, orchestrator, tmp_path):
        """ORC-028: ポリシー名不一致

        orchestrator.py:L294,320 のポリシー名不一致→ループ終了をカバー。
        """
        # Arrange
        yaml_content = {"policies": [
            {"name": "other-policy", "metadata": {"severity": "Low"}}
        ]}
        yaml_file = tmp_path / "policy_other.yaml"
        yaml_file.write_text(yaml.dump(yaml_content))

        # Act
        result = orchestrator._read_policy_yaml_metadata(str(yaml_file), "target-policy")

        # Assert
        assert result == {}

    def test_policy_no_metadata(self, orchestrator, tmp_path):
        """ORC-029: metadata空

        orchestrator.py:L297,315-317 のmetadataが空の分岐をカバー。
        ポリシーは見つかるがmetadataが空dict。
        """
        # Arrange
        yaml_content = {"policies": [
            {"name": "test-policy", "metadata": {}}
        ]}
        yaml_file = tmp_path / "policy_empty.yaml"
        yaml_file.write_text(yaml.dump(yaml_content))

        # Act
        result = orchestrator._read_policy_yaml_metadata(str(yaml_file), "test-policy")

        # Assert
        assert result == {}

    def test_recommendation_uuid_already_set(self, orchestrator, tmp_path):
        """ORC-030: recommendation_uuid既存（uuidマッピングスキップ）

        orchestrator.py:L300 のrecommendation_uuid既存判定をカバー。
        uuidとrecommendation_uuidの両方が存在する場合、マッピングはスキップ。
        """
        # Arrange
        yaml_content = {"policies": [{
            "name": "test-policy",
            "metadata": {
                "uuid": "original-uuid",
                "recommendation_uuid": "existing-rec-uuid",
                "severity": "Medium"
            }
        }]}
        yaml_file = tmp_path / "policy_uuid.yaml"
        yaml_file.write_text(yaml.dump(yaml_content))

        # Act
        result = orchestrator._read_policy_yaml_metadata(str(yaml_file), "test-policy")

        # Assert - recommendation_uuidは上書きされない
        assert result["recommendation_uuid"] == "existing-rec-uuid"
        assert result["uuid"] == "original-uuid"
```

### 2.9 _merge_metadata テスト

```python
class TestMergeMetadata:
    """メタデータマージテスト"""

    def test_all_from_yaml(self, orchestrator):
        """ORC-031: YAML優先

        orchestrator.py:L353-390 の全フィールドYAML優先パスをカバー。
        """
        # Arrange
        yaml_meta = {
            "uuid": "yaml-uuid",
            "recommendation_id": "YAML-REC-001",
            "recommendation_version": "2.0",
            "policy_version": "3.0",
            "severity": "Critical",
            "title": "YAML Title"
        }
        custodian_meta = {"policy": {"metadata": {
            "uuid": "cust-uuid", "recommendation_id": "CUST-REC",
            "severity": "Low", "title": "Custodian Title"
        }}}

        # Act
        result = orchestrator._merge_metadata(yaml_meta, custodian_meta)

        # Assert - 全フィールドYAML値
        assert result["recommendation_uuid"] == "yaml-uuid"
        assert result["recommendation_id"] == "YAML-REC-001"
        assert result["recommendation_version"] == "2.0"
        assert result["policy_version"] == "3.0"
        assert result["severity"] == "Critical"
        assert result["title"] == "YAML Title"

    def test_all_from_custodian(self, orchestrator):
        """ORC-032: Custodianフォールバック

        orchestrator.py:L358,364,369,374,380,388 の各フィールドCustodianパスをカバー。
        YAMLフィールドが全て空の場合、Custodianの値が使用される。
        """
        # Arrange
        yaml_meta = {}  # 全フィールド空
        custodian_meta = {"policy": {"metadata": {
            "uuid": "cust-uuid", "recommendation_id": "CUST-REC",
            "recommendation_version": "1.0", "policy_version": "1.0",
            "severity": "High", "title": "Custodian Title"
        }}}

        # Act
        result = orchestrator._merge_metadata(yaml_meta, custodian_meta)

        # Assert - 全フィールドCustodian値
        assert result["recommendation_uuid"] == "cust-uuid"
        assert result["recommendation_id"] == "CUST-REC"
        assert result["severity"] == "High"
        assert result["title"] == "Custodian Title"

    def test_default_severity(self, orchestrator):
        """ORC-033: デフォルトseverity

        orchestrator.py:L382 のYAML・Custodian両方severity無し→"Medium"をカバー。
        """
        # Arrange
        yaml_meta = {}
        custodian_meta = {"policy": {"metadata": {}}}

        # Act
        result = orchestrator._merge_metadata(yaml_meta, custodian_meta)

        # Assert
        assert result["severity"] == "Medium"

    def test_title_fallback_to_policy_name(self, orchestrator):
        """ORC-034: titleフォールバック

        orchestrator.py:L390 のYAML・Custodian両方title無し→policy.nameをカバー。
        """
        # Arrange
        yaml_meta = {}
        custodian_meta = {"policy": {"name": "fallback-policy", "metadata": {}}}

        # Act
        result = orchestrator._merge_metadata(yaml_meta, custodian_meta)

        # Assert
        assert result["title"] == "fallback-policy"
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| ORC-E01 | analyze_policy_execution例外 | 内部処理で例外 | _create_error_result dict |
| ORC-E02 | analyze_multi_region_scan例外 | _discover_policy_directories例外 | エラーレスポンス |
| ORC-E03 | _find_and_read_policy_yaml例外 | glob.glob例外 | {} |
| ORC-E04 | _read_policy_yaml_metadata YAMLError | 不正YAML | {} |
| ORC-E05 | _read_policy_yaml_metadata 汎用例外 | open例外 | {} |

### 3.1 異常系テスト

```python
class TestOrchestratorErrors:
    """オーケストレーター異常系テスト"""

    def test_analyze_policy_execution_exception(self, orchestrator, mock_file_reader):
        """ORC-E01: analyze_policy_execution 例外

        orchestrator.py:L72-74 の汎用例外→_create_error_resultをカバー。
        """
        # Arrange
        mock_file_reader.read_log_file.side_effect = RuntimeError("読み込みエラー")

        # Act
        result = orchestrator.analyze_policy_execution("/output/policy-fail", "fail-policy")

        # Assert
        assert result["status"] == "error"
        assert result["error_details"]["error_occurred"] is True
        assert "読み込みエラー" in result["error_details"]["error_message"]

    def test_analyze_multi_region_scan_exception(self, orchestrator):
        """ORC-E02: analyze_multi_region_scan 例外

        orchestrator.py:L103-110 の汎用例外→エラーレスポンスをカバー。
        """
        # Arrange
        orchestrator._discover_policy_directories = MagicMock(
            side_effect=OSError("ディレクトリアクセス失敗")
        )

        # Act
        result = orchestrator.analyze_multi_region_scan("/broken/output")

        # Assert
        assert result["policy_results"] == []
        assert result["scan_errors_summary"]["total_errors"] == 1
        assert "ディレクトリアクセス失敗" in result["scan_errors_summary"]["analysis_error"]
        assert "analysis_timestamp" in result

    def test_find_and_read_policy_yaml_exception(self, orchestrator):
        """ORC-E03: _find_and_read_policy_yaml 例外

        orchestrator.py:L261-263 の汎用例外→{}をカバー。
        """
        # Arrange
        with patch(f"{MODULE_ORC}.os.path.dirname", side_effect=TypeError("パスエラー")):
            # Act
            result = orchestrator._find_and_read_policy_yaml("/invalid", "policy", "ec2")

        # Assert
        assert result == {}

    def test_read_policy_yaml_metadata_yaml_error(self, orchestrator, tmp_path):
        """ORC-E04: _read_policy_yaml_metadata YAMLError

        orchestrator.py:L323-325 のyaml.YAMLError→{}をカバー。
        """
        # Arrange
        yaml_file = tmp_path / "invalid.yaml"
        yaml_file.write_text("invalid: yaml: content: [unclosed")

        # Act
        result = orchestrator._read_policy_yaml_metadata(str(yaml_file), "policy")

        # Assert
        assert result == {}

    def test_read_policy_yaml_metadata_generic_exception(self, orchestrator, tmp_path):
        """ORC-E05: _read_policy_yaml_metadata 汎用例外

        orchestrator.py:L326-328 の汎用例外→{}をカバー。
        """
        # Arrange
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("policies: []")

        with patch("builtins.open", side_effect=PermissionError("読み取り拒否")):
            # Act
            result = orchestrator._read_policy_yaml_metadata(str(yaml_file), "policy")

        # Assert
        assert result == {}
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| ORC-SEC-01 | エラー結果構造の一貫性 | 各種エラー | 固定キーセット・固定スキーマ |
| ORC-SEC-02 | YAML安全パーサ使用確認 | 有効YAML | yaml.safe_loadが呼ばれる |
| ORC-SEC-03 | マルチリージョンエラー応答 | 内部例外 | スタックトレース非含有 |

```python
@pytest.mark.security
class TestOrchestratorSecurity:
    """オーケストレーターセキュリティテスト"""

    def test_error_result_fixed_schema(self, orchestrator):
        """ORC-SEC-01: エラー結果の固定スキーマ検証

        orchestrator.py:L199-211 のエラー結果が固定キーセット・固定構造に従うことを検証。
        error_messageの内容サニタイズは別レイヤーの責務（本テストでは対象外）。
        """
        # Arrange
        error_messages = [
            "通常エラー",
            "File /internal/path/secret.py not found",
            "KeyError: 'password'",
        ]

        # Act & Assert
        for msg in error_messages:
            result = orchestrator._create_error_result("policy", msg)
            # 固定キーセットであること
            expected_keys = {"policy_name", "resource_type", "region", "status",
                             "violation_count", "metadata", "resource_statistics",
                             "execution_details", "error_details"}
            assert set(result.keys()) == expected_keys
            # error_detailsの構造が固定であること
            assert set(result["error_details"].keys()) == {"error_occurred", "error_type", "error_message"}

    def test_yaml_safe_load_used(self, orchestrator, tmp_path):
        """ORC-SEC-02: YAML安全パーサ使用確認

        orchestrator.py:L284 でyaml.safe_loadが使用されていることを検証。
        yaml.load（任意コード実行可能）ではなくsafe_loadが呼ばれる。
        """
        # Arrange
        yaml_file = tmp_path / "policy_safe.yaml"
        yaml_file.write_text(yaml.dump({"policies": []}))

        with patch(f"{MODULE_ORC}.yaml.safe_load", wraps=yaml.safe_load) as mock_safe:
            # Act
            orchestrator._read_policy_yaml_metadata(str(yaml_file), "policy")

        # Assert
        mock_safe.assert_called_once()

    def test_multi_region_error_no_stack_trace(self, orchestrator):
        """ORC-SEC-03: マルチリージョンエラー応答

        orchestrator.py:L103-110 のエラーレスポンスにスタックトレースが含まれないことを検証。
        """
        # Arrange
        orchestrator._discover_policy_directories = MagicMock(
            side_effect=RuntimeError("Internal processing error")
        )

        # Act
        result = orchestrator.analyze_multi_region_scan("/output")

        # Assert - analysis_errorにはstr(e)のみ含まれる
        error_str = result["scan_errors_summary"]["analysis_error"]
        assert "Traceback" not in error_str
        assert "File " not in error_str
        assert error_str == "Internal processing error"
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse | 定義元 |
|--------------|------|---------|---------|--------|
| `reset_log_analyzer_module` | モジュール状態リセット | function | Yes | #15a定義を流用 |
| `mock_file_reader` | DI注入用モックLogFileReader | function | No | #15b新規 |
| `mock_pattern_matcher` | DI注入用モックLogPatternMatcher | function | No | #15b新規 |
| `mock_status_determiner` | DI注入用モックPolicyStatusDeterminer | function | No | #15b新規 |
| `orchestrator` | テスト用PolicyAnalysisOrchestrator | function | No | #15b新規 |
| `mock_log_analysis` | モックLogAnalysisResult | function | No | #15b新規 |

> **conftest.py統合方針**: `test/unit/jobs/tasks/new_custodian_scan/log_analyzer/conftest.py` に#15a定義済みフィクスチャ（`reset_log_analyzer_module`, `file_reader`, `pattern_matcher`, `status_determiner`, `make_log_result`）が存在する。#15bでは以下の新規フィクスチャを追記する。名前衝突はなく、`reset_log_analyzer_module`（autouse）は#15bテストにも自動適用される。追記時、#15aのimport行に `MagicMock` を追加すること（`from unittest.mock import patch, MagicMock`）。

### conftest.py追記分

```python
# test/unit/jobs/tasks/new_custodian_scan/log_analyzer/conftest.py
# === #15b追記分（既存の#15aフィクスチャに追記） ===

MODULE_ORC = "app.jobs.tasks.new_custodian_scan.log_analyzer.orchestrator"


@pytest.fixture
def mock_file_reader():
    """DI注入用モックLogFileReader

    PolicyAnalysisOrchestratorにDI注入するためのMagicMock。
    #15aのfile_readerフィクスチャ（実インスタンス）とは別物。
    """
    return MagicMock()


@pytest.fixture
def mock_pattern_matcher():
    """DI注入用モックLogPatternMatcher

    PolicyAnalysisOrchestratorにDI注入するためのMagicMock。
    """
    return MagicMock()


@pytest.fixture
def mock_status_determiner():
    """DI注入用モックPolicyStatusDeterminer

    PolicyAnalysisOrchestratorにDI注入するためのMagicMock。
    """
    return MagicMock()


@pytest.fixture
def orchestrator(mock_file_reader, mock_pattern_matcher, mock_status_determiner):
    """テスト用PolicyAnalysisOrchestrator（全依存モック注入）

    TaskLoggerをモック化し、3コンポーネントをMagicMockで注入。
    オーケストレーション動作のみを検証できる。
    """
    with patch(f"{MODULE_ORC}.TaskLogger"):
        from app.jobs.tasks.new_custodian_scan.log_analyzer.orchestrator import PolicyAnalysisOrchestrator
        return PolicyAnalysisOrchestrator(
            "test-job-id",
            file_reader=mock_file_reader,
            pattern_matcher=mock_pattern_matcher,
            status_determiner=mock_status_determiner
        )


@pytest.fixture
def mock_log_analysis():
    """モックLogAnalysisResult

    _build_resultテスト等で使用するモックログ解析結果。
    """
    mock = MagicMock()
    mock.resources_before_filter = 100
    mock.resources_after_filter = 5
    mock.execution_time = 1.5
    mock.error_details = {"error_occurred": False}
    return mock
```

---

## 6. テスト実行例

```bash
# orchestratorテスト全体を実行
pytest test/unit/jobs/tasks/new_custodian_scan/log_analyzer/test_log_analyzer_orchestrator.py -v

# クラス単位で実行
pytest test/unit/jobs/tasks/new_custodian_scan/log_analyzer/test_log_analyzer_orchestrator.py::TestAnalyzePolicyExecution -v
pytest test/unit/jobs/tasks/new_custodian_scan/log_analyzer/test_log_analyzer_orchestrator.py::TestMergeMetadata -v

# カバレッジ付きで実行
pytest test/unit/jobs/tasks/new_custodian_scan/log_analyzer/test_log_analyzer_orchestrator.py \
  --cov=app.jobs.tasks.new_custodian_scan.log_analyzer.orchestrator \
  --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/jobs/tasks/new_custodian_scan/log_analyzer/test_log_analyzer_orchestrator.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 35 | ORC-001〜035 |
| 異常系 | 5 | ORC-E01〜ORC-E05 |
| セキュリティ | 3 | ORC-SEC-01〜ORC-SEC-03 |
| **合計** | **43** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestOrchestratorInit` | ORC-001〜002 | 2 |
| `TestAnalyzePolicyExecution` | ORC-003〜005 | 3 |
| `TestAnalyzeMultiRegionScan` | ORC-006〜008 | 3 |
| `TestBuildResult` | ORC-009〜011 | 3 |
| `TestDiscoverPolicyDirectories` | ORC-012〜013 | 2 |
| `TestAggregateErrorInfo` | ORC-014 | 1 |
| `TestCalculateAggregatedStatistics` | ORC-015 | 1 |
| `TestCalculateComplianceRate` | ORC-016〜017, ORC-035 | 3 |
| `TestDetermineResourceScope` | ORC-018〜019 | 2 |
| `TestCreateErrorResult` | ORC-020 | 1 |
| `TestFindAndReadPolicyYaml` | ORC-021〜024 | 4 |
| `TestReadPolicyYamlMetadata` | ORC-025〜030 | 6 |
| `TestMergeMetadata` | ORC-031〜034 | 4 |
| `TestOrchestratorErrors` | ORC-E01〜E05 | 5 |
| `TestOrchestratorSecurity` | ORC-SEC-01〜ORC-SEC-03 | 3 |

### 実装失敗が予想されるテスト

以下の実行前提が整備されていれば、失敗が予想されるテストはありません。

#### 実行前提（実装タスクとしてpyproject.tomlへの追加が必要）

| 前提 | 対応内容 |
|------|---------|
| `security`マーカー | `[tool.pytest.ini_options].markers` に `"security: セキュリティテスト"` を追加 |

### 注意事項

- `orchestrator`フィクスチャはDI注入パターンにより、3コンポーネント全てがMagicMockとして注入される
- パブリックメソッド（`analyze_policy_execution`, `analyze_multi_region_scan`）のテストでは内部メソッドをパッチして単体テスト化する
- `_read_policy_yaml_metadata`テストではtmp_pathで実YAMLファイルを作成し、yaml.safe_loadの実動作を検証する
- `_merge_metadata`は純粋なdict操作のためモック不要、実dictで検証する
- #15aの`make_log_result`フィクスチャは#15bでは直接使用しないが、conftest.pyに存在し干渉しない

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `analyze_multi_region_scan`の`analysis_timestamp`は`datetime.now()`使用 | テストでは厳密な値検証不可 | キーの存在確認のみで検証 |
| 2 | `_discover_policy_directories`はos.walkを使用 | 深いネスト構造は未検証 | 1階層のディレクトリ構造で基本動作を確認 |
| 3 | `_find_and_read_policy_yaml`のパス操作はOS依存 | Windowsパスセパレータは未検証 | Linux/macOS環境前提でテスト |
| 4 | `_merge_metadata`の6フィールドフォールバックは代表パターンのみ | 全組み合わせ（2^6=64通り）は未検証 | 4テストで代表的4パターン（全YAML/全Custodian/デフォルト/混合）をカバー |
| 5 | パブリックメソッドテストでは内部メソッドをパッチ | 統合動作の一部は検証対象外 | 各内部メソッドの個別テストで補完 |
