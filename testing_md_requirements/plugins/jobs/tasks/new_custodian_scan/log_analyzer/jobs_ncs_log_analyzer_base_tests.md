# jobs/tasks/new_custodian_scan/log_analyzer 基盤系 テストケース

## 1. 概要

`log_analyzer/` サブディレクトリの基盤系5ファイル（`models.py`, `__init__.py`, `file_reader.py`, `pattern_matcher.py`, `status_determiner.py`）をまとめたテスト仕様書。データモデル・ファイルI/O・パターンマッチ・ステータス判定を担う。

### 1.1 対象クラス

| クラス/モジュール | ファイル | 行数 | 責務 |
|-----------------|---------|------|------|
| `PolicyStatus`, `ErrorType`, `LogAnalysisResult` | `models.py` | 66 | Enum定義・データクラス・グローバルリソース定数 |
| （パッケージ公開API） | `__init__.py` | 42 | エイリアス・後方互換関数・__all__ |
| `LogFileReader` | `file_reader.py` | 261 | ログ/JSON安全読み込み・パス検証・チャンク読み込み |
| `LogPatternMatcher` | `pattern_matcher.py` | 176 | 正規表現パターンマッチ・リソース数/実行時間抽出 |
| `PolicyStatusDeterminer` | `status_determiner.py` | 110 | ステータス判定・コンプライアンス率計算・スコープ判定 |

### 1.2 カバレッジ目標: 90%

> **注記**: `file_reader.py` はセキュリティ機能（パストラバーサル・シンボリックリンク・サイズ制限）を多く含むため高カバレッジを目指す。`models.py` はデータ定義のみのため構造確認に留める。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象1 | `app/jobs/tasks/new_custodian_scan/log_analyzer/models.py` |
| テスト対象2 | `app/jobs/tasks/new_custodian_scan/log_analyzer/__init__.py` |
| テスト対象3 | `app/jobs/tasks/new_custodian_scan/log_analyzer/file_reader.py` |
| テスト対象4 | `app/jobs/tasks/new_custodian_scan/log_analyzer/pattern_matcher.py` |
| テスト対象5 | `app/jobs/tasks/new_custodian_scan/log_analyzer/status_determiner.py` |
| テストコード | `test/unit/jobs/tasks/new_custodian_scan/log_analyzer/test_log_analyzer_base.py` |

### 1.4 補足情報

#### 依存関係

```
models.py
  ──→ なし（標準ライブラリのみ）

__init__.py
  ──→ orchestrator.PolicyAnalysisOrchestrator
  ──→ models.*

file_reader.py (LogFileReader)
  ──→ TaskLogger（ログ）
  ──→ os, json, pathlib（標準ライブラリ）

pattern_matcher.py (LogPatternMatcher)
  ──→ TaskLogger（ログ）
  ──→ models.LogAnalysisResult
  ──→ re（標準ライブラリ）

status_determiner.py (PolicyStatusDeterminer)
  ──→ TaskLogger（ログ）
  ──→ models.PolicyStatus, ErrorType, LogAnalysisResult, GLOBAL_AWS_RESOURCES
```

#### テスト戦略

| テストカテゴリ | 手法 |
|--------------|------|
| models.py | 実クラスで構造確認（Enum値、dataclassフィールド） |
| __init__.py | PolicyAnalysisOrchestratorをモック化し委譲動作を検証 |
| file_reader.py | tmp_pathで実ファイルシステム構築、TaskLoggerはモック化 |
| pattern_matcher.py | 実インスタンスで直接テスト（純粋な文字列処理） |
| status_determiner.py | 実インスタンスで直接テスト、TaskLoggerはモック化 |

#### 主要分岐マップ

| クラス | メソッド | 行番号 | 条件 | 分岐数 |
|--------|---------|--------|------|--------|
| LogFileReader | `read_log_file` | L65, L68, L73 | パス検証、存在、サイズ | 3 |
| LogFileReader | `read_json_file` | L94, L97, L102, L109, L112 | パス検証、存在、サイズ、JSONエラー、汎用例外 | 5 |
| LogFileReader | `_validate_and_resolve_path` | L156, L163, L172, L175 | 危険パターン、resolve例外、is_relative_to、Python3.8互換 | 4 |
| LogFileReader | `_check_file_size` | L200, L213 | サイズ超過、stat例外 | 2 |
| LogFileReader | `_read_file_chunked` | L239, L246, L256, L260 | チャンク終了、truncate判定、Unicode例外、汎用例外 | 4 |
| LogPatternMatcher | `extract_resource_counts` | L70 | メインパターン一致/不一致 | 2 |
| LogPatternMatcher | `_try_alternative_patterns` | L98, L102 | 代替パターン一致、count:判定 | 3 |
| LogPatternMatcher | `extract_execution_time` | L131 | パターン一致/不一致 | 2 |
| PolicyStatusDeterminer | `determine_status` | L25, L39, L44, L49 | error→no_resources→compliant→violation→default | 5 |
| PolicyStatusDeterminer | `calculate_compliance_rate` | L62 | total==0 | 2 |

---

## 2. 正常系テストケース

### models.py (MDL)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| MDL-001 | PolicyStatus Enum値 | 各Enum | 5つの値が正しい |
| MDL-002 | ErrorType Enum値 | 各Enum | 7つの値が正しい |
| MDL-003 | LogAnalysisResult生成 | 各フィールド | dataclass正常生成 |
| MDL-004 | GLOBAL_AWS_RESOURCES定数 | - | 期待するリソースタイプを含む |

### __init__.py (PKG)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| PKG-001 | CustodianLogAnalyzerエイリアス | - | PolicyAnalysisOrchestratorと同一 |
| PKG-002 | analyze_policy_execution委譲 | policy_output_dir, policy_name, job_id | orchestrator.analyze_policy_executionに委譲 |
| PKG-003 | analyze_multi_region_scan委譲 | custodian_output_dir, job_id | orchestrator.analyze_multi_region_scanに委譲 |
| PKG-004 | __all__エクスポート | - | 全公開名が含まれる |

### file_reader.py (FRD)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| FRD-001 | 初期化 | job_id | logger初期化、定数値正常 |
| FRD-002 | read_log_file 正常読み込み | 正常なファイル | ファイル内容 |
| FRD-003 | read_log_file ファイル不在 | 存在しないパス | "" |
| FRD-004 | read_log_file サイズ超過 | max_size超のファイル | ValueError |
| FRD-005 | read_json_file 正常読み込み | 正常なJSONファイル | dict |
| FRD-006 | read_json_file ファイル不在 | 存在しないパス | {} |
| FRD-007 | read_json_file サイズ超過 | 大きなJSONファイル | ValueError |
| FRD-008 | _validate_and_resolve_path 安全なパス | /tmp下のパス | 解決済みPath |
| FRD-009 | _validate_and_resolve_path 危険パターン | ".."含むパス | ValueError |
| FRD-010 | _validate_and_resolve_path 許可外ディレクトリ | /tmp外のパス | ValueError |
| FRD-011 | _validate_and_resolve_path resolve例外 | 不正パス | ValueError |
| FRD-012 | _check_file_size 制限内 | 小さなファイル | True |
| FRD-013 | _check_file_size 超過 | 大きなファイル | False |
| FRD-014 | _read_file_chunked 正常読み込み | 正常ファイル | ファイル内容 |
| FRD-015 | _read_file_chunked truncate | max_size超のファイル | truncateメッセージ付与 |

### pattern_matcher.py (PMT)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| PMT-001 | 初期化でパターンコンパイル | job_id | compiled pattern属性 |
| PMT-002 | extract_resource_counts メインパターン | "Filtered from 100 to 5 ec2" | (100, 5) |
| PMT-003 | extract_resource_counts 代替パターンへフォールバック | "count:10" | (10, 10) |
| PMT-004 | _try_alternative_patterns "resources found" | "3 resources found" | (3, 3) |
| PMT-005 | _try_alternative_patterns 全失敗 | パターンなしログ | (0, 0) |
| PMT-006 | extract_execution_time パターン一致 | policy_info含むログ | 実行時間float |
| PMT-007 | extract_execution_time パターン不一致 | 通常ログ | 0.0 |
| PMT-008 | analyze_log_content 包括解析 | 完全なCustodianログ | LogAnalysisResult |

### status_determiner.py (SDT)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| SDT-001 | 初期化 | job_id | logger初期化 |
| SDT-002 | determine_status ERROR | error_occurred=True | PolicyStatus.ERROR |
| SDT-003 | determine_status NO_RESOURCES | before=0 | PolicyStatus.NO_RESOURCES |
| SDT-004 | determine_status COMPLIANT | before>0, after=0, count=0 | PolicyStatus.COMPLIANT |
| SDT-005 | determine_status VIOLATION | count>0 | PolicyStatus.VIOLATION |
| SDT-006 | determine_status デフォルトCOMPLIANT | before>0, after>0, count=0 | PolicyStatus.COMPLIANT |
| SDT-007 | calculate_compliance_rate total=0 | total=0 | 1.0 |
| SDT-008 | calculate_compliance_rate 正常 | total=100, violation=20 | 0.8 |
| SDT-009 | calculate_compliance_rate violation>total | total=5, violation=10 | 0.0 |
| SDT-010 | determine_resource_scope global | "iam" | "global" |
| SDT-011 | determine_resource_scope regional | "ec2" | "regional" |
| SDT-012 | create_error_result 構造確認 | policy_name, error_message | 正しいdict構造 |

### 2.1 models.py テスト

```python
# test/unit/jobs/tasks/new_custodian_scan/log_analyzer/test_log_analyzer_base.py
import pytest
import json
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

MODULE_FRD = "app.jobs.tasks.new_custodian_scan.log_analyzer.file_reader"
MODULE_PMT = "app.jobs.tasks.new_custodian_scan.log_analyzer.pattern_matcher"
MODULE_SDT = "app.jobs.tasks.new_custodian_scan.log_analyzer.status_determiner"
MODULE_PKG = "app.jobs.tasks.new_custodian_scan.log_analyzer"


class TestModels:
    """データモデルテスト"""

    def test_policy_status_enum_values(self):
        """MDL-001: PolicyStatus Enum値

        models.py:L33-39 の5つのEnum値をカバー。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.log_analyzer.models import PolicyStatus

        # Assert
        assert PolicyStatus.VIOLATION.value == "violation"
        assert PolicyStatus.COMPLIANT.value == "compliant"
        assert PolicyStatus.NO_RESOURCES.value == "no_resources"
        assert PolicyStatus.ERROR.value == "error"
        assert PolicyStatus.PARTIAL_FAILURE.value == "partial_failure"
        assert len(PolicyStatus) == 5

    def test_error_type_enum_values(self):
        """MDL-002: ErrorType Enum値

        models.py:L42-50 の7つのEnum値をカバー。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.log_analyzer.models import ErrorType

        # Assert
        assert ErrorType.AUTHENTICATION.value == "authentication"
        assert ErrorType.PERMISSION.value == "permission"
        assert ErrorType.POLICY.value == "policy"
        assert ErrorType.SYNTAX.value == "syntax"
        assert ErrorType.RUNTIME.value == "runtime"
        assert ErrorType.TIMEOUT.value == "timeout"
        assert ErrorType.UNKNOWN.value == "unknown"
        assert len(ErrorType) == 7

    def test_log_analysis_result_creation(self):
        """MDL-003: LogAnalysisResult生成

        models.py:L53-67 のdataclassフィールドをカバー。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.log_analyzer.models import LogAnalysisResult

        # Act
        result = LogAnalysisResult(
            resources_before_filter=100,
            resources_after_filter=5,
            execution_time=1.5,
            error_details={"error_occurred": False}
        )

        # Assert
        assert result.resources_before_filter == 100
        assert result.resources_after_filter == 5
        assert result.execution_time == 1.5
        assert result.error_details["error_occurred"] is False

    def test_global_aws_resources_constant(self):
        """MDL-004: GLOBAL_AWS_RESOURCES定数

        models.py:L17-30 のグローバルリソース定義をカバー。
        15種類のリソースタイプが定義されていることを検証。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.log_analyzer.models import GLOBAL_AWS_RESOURCES

        # Assert
        assert "iam" in GLOBAL_AWS_RESOURCES
        assert "s3" in GLOBAL_AWS_RESOURCES
        assert "cloudfront" in GLOBAL_AWS_RESOURCES
        assert "route53" in GLOBAL_AWS_RESOURCES
        assert isinstance(GLOBAL_AWS_RESOURCES, set)
        assert len(GLOBAL_AWS_RESOURCES) == 15
        # ec2はグローバルではない
        assert "ec2" not in GLOBAL_AWS_RESOURCES
```

### 2.2 __init__.py テスト

```python
class TestPackageInit:
    """パッケージ公開APIテスト"""

    def test_custodian_log_analyzer_alias(self):
        """PKG-001: CustodianLogAnalyzerエイリアス

        __init__.py:L20 のエイリアス定義をカバー。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.log_analyzer import (
            CustodianLogAnalyzer, PolicyAnalysisOrchestrator
        )

        # Assert
        assert CustodianLogAnalyzer is PolicyAnalysisOrchestrator

    def test_analyze_policy_execution_delegates(self):
        """PKG-002: analyze_policy_execution委譲

        __init__.py:L23-26 の後方互換ラッパー関数をカバー。
        job_idでPolicyAnalysisOrchestratorをインスタンス化し、
        analyze_policy_executionへ(policy_output_dir, policy_name)を委譲する動作を確認。
        """
        # Arrange
        mock_result = {"status": "compliant"}
        with patch(f"{MODULE_PKG}.PolicyAnalysisOrchestrator") as MockOrch:
            MockOrch.return_value.analyze_policy_execution.return_value = mock_result

            # Act
            from app.jobs.tasks.new_custodian_scan.log_analyzer import analyze_policy_execution
            result = analyze_policy_execution("/output/dir", "test-policy", "job-123")

        # Assert
        MockOrch.assert_called_once_with("job-123")
        MockOrch.return_value.analyze_policy_execution.assert_called_once_with(
            "/output/dir", "test-policy"
        )
        assert result == mock_result

    def test_analyze_multi_region_scan_delegates(self):
        """PKG-003: analyze_multi_region_scan委譲

        __init__.py:L28-31 の後方互換ラッパー関数をカバー。
        job_idでPolicyAnalysisOrchestratorをインスタンス化し、
        analyze_multi_region_scanへ(custodian_output_dir)を委譲する動作を確認。
        """
        # Arrange
        mock_result = {"policy_results": []}
        with patch(f"{MODULE_PKG}.PolicyAnalysisOrchestrator") as MockOrch:
            MockOrch.return_value.analyze_multi_region_scan.return_value = mock_result

            # Act
            from app.jobs.tasks.new_custodian_scan.log_analyzer import analyze_multi_region_scan
            result = analyze_multi_region_scan("/custodian/output", "job-456")

        # Assert
        MockOrch.assert_called_once_with("job-456")
        MockOrch.return_value.analyze_multi_region_scan.assert_called_once_with(
            "/custodian/output"
        )
        assert result == mock_result

    def test_all_exports(self):
        """PKG-004: __all__エクスポート

        __init__.py:L33-43 の__all__が全公開名を含むことをカバー。
        """
        # Arrange
        import app.jobs.tasks.new_custodian_scan.log_analyzer as pkg

        # Assert
        expected = [
            "PolicyAnalysisOrchestrator",
            "CustodianLogAnalyzer",
            "PolicyStatus",
            "ErrorType",
            "LogAnalysisResult",
            "GLOBAL_AWS_RESOURCES",
            "PolicyStatusDeterminer",
            "analyze_policy_execution",
            "analyze_multi_region_scan"
        ]
        for name in expected:
            assert name in pkg.__all__, f"{name} が __all__ に含まれていない"
```

### 2.3 file_reader.py テスト

```python
class TestLogFileReaderInit:
    """LogFileReader初期化テスト"""

    def test_init(self, file_reader):
        """FRD-001: 初期化

        file_reader.py:L38-46 の初期化とクラス定数をカバー。
        """
        # Assert
        assert file_reader.job_id == "test-job-id"
        assert file_reader.MAX_FILE_SIZE == 50 * 1024 * 1024
        assert file_reader.CHUNK_SIZE == 8192
        assert file_reader.DEFAULT_ALLOWED_BASE == "/tmp"


class TestReadLogFile:
    """ログファイル読み込みテスト"""

    def test_normal_read(self, file_reader, tmp_path):
        """FRD-002: read_log_file 正常読み込み

        file_reader.py:L48-77 の正常フローをカバー。
        """
        # Arrange
        log_file = tmp_path / "custodian-run.log"
        log_file.write_text("INFO: Policy execution started\nINFO: Completed")

        # Act
        result = file_reader.read_log_file(str(log_file))

        # Assert
        assert "Policy execution started" in result
        assert "Completed" in result

    def test_file_not_exists(self, file_reader, tmp_path):
        """FRD-003: read_log_file ファイル不在

        file_reader.py:L68-70 のファイル不在分岐をカバー。
        """
        # Act
        result = file_reader.read_log_file(str(tmp_path / "nonexistent.log"))

        # Assert
        assert result == ""

    def test_file_size_exceeded(self, file_reader, tmp_path):
        """FRD-004: read_log_file サイズ超過

        file_reader.py:L73-74 のサイズ超過分岐をカバー。
        """
        # Arrange
        log_file = tmp_path / "large.log"
        log_file.write_text("x" * 1000)

        # Act & Assert
        with pytest.raises(ValueError, match="ファイルサイズが制限を超えています"):
            file_reader.read_log_file(str(log_file), max_size=100)


class TestReadJsonFile:
    """JSONファイル読み込みテスト"""

    def test_normal_read(self, file_reader, tmp_path):
        """FRD-005: read_json_file 正常読み込み

        file_reader.py:L79-114 の正常フローをカバー。
        """
        # Arrange
        json_file = tmp_path / "metadata.json"
        data = {"policy": {"resource": "ec2"}}
        json_file.write_text(json.dumps(data))

        # Act
        result = file_reader.read_json_file(str(json_file))

        # Assert
        assert result["policy"]["resource"] == "ec2"

    def test_file_not_exists(self, file_reader, tmp_path):
        """FRD-006: read_json_file ファイル不在

        file_reader.py:L97-99 のファイル不在分岐をカバー。
        """
        # Act
        result = file_reader.read_json_file(str(tmp_path / "nonexistent.json"))

        # Assert
        assert result == {}

    def test_file_size_exceeded(self, file_reader, tmp_path):
        """FRD-007: read_json_file サイズ超過

        file_reader.py:L102-103 のサイズ超過分岐をカバー。
        MAX_FILE_SIZEを一時的に小さく設定してテスト。
        """
        # Arrange
        json_file = tmp_path / "large.json"
        json_file.write_text(json.dumps({"data": "x" * 1000}))

        # Act & Assert
        original = file_reader.MAX_FILE_SIZE
        file_reader.MAX_FILE_SIZE = 100
        try:
            with pytest.raises(ValueError, match="JSONファイルサイズが制限を超えています"):
                file_reader.read_json_file(str(json_file))
        finally:
            file_reader.MAX_FILE_SIZE = original


class TestValidateAndResolvePath:
    """パス検証テスト"""

    def test_safe_path(self, file_reader, tmp_path):
        """FRD-008: _validate_and_resolve_path 安全なパス

        file_reader.py:L116-184 の正常フロー（安全パス→解決成功）をカバー。
        """
        # Arrange
        test_file = tmp_path / "test.log"
        test_file.write_text("data")

        # Act
        result = file_reader._validate_and_resolve_path(str(test_file), str(tmp_path))

        # Assert
        assert isinstance(result, Path)
        assert result.exists()

    def test_dangerous_patterns_rejected(self, file_reader):
        """FRD-009: _validate_and_resolve_path 危険パターン

        file_reader.py:L142-159 の11個の危険パターン検出をカバー。
        代表的3パターン（.., /etc/, ;）を検証。
        """
        # Act & Assert
        with pytest.raises(ValueError, match="危険なパスパターン"):
            file_reader._validate_and_resolve_path("/tmp/../etc/passwd")

        with pytest.raises(ValueError, match="危険なパスパターン"):
            file_reader._validate_and_resolve_path("/etc/shadow")

        with pytest.raises(ValueError, match="危険なパスパターン"):
            file_reader._validate_and_resolve_path("/tmp/file;rm -rf /")

    def test_outside_allowed_base(self, file_reader):
        """FRD-010: _validate_and_resolve_path 許可外ディレクトリ

        file_reader.py:L172-174 のis_relative_toチェックをカバー。
        /tmp配下でないパスは拒否される。
        """
        # Act & Assert
        with pytest.raises(ValueError, match="許可されていないディレクトリ"):
            file_reader._validate_and_resolve_path("/var/log/test.log", "/tmp")

    def test_resolve_exception(self, file_reader):
        """FRD-011: _validate_and_resolve_path resolve例外

        file_reader.py:L163-167 のPath.resolve例外をカバー。
        """
        # Arrange
        with patch(f"{MODULE_FRD}.Path.resolve", side_effect=OSError("resolve error")):
            # Act & Assert
            with pytest.raises(ValueError, match="パス解決に失敗しました"):
                file_reader._validate_and_resolve_path("/tmp/valid_looking")


class TestCheckFileSize:
    """ファイルサイズチェックテスト"""

    def test_within_limit(self, file_reader, tmp_path):
        """FRD-012: _check_file_size 制限内

        file_reader.py:L211 のTrue分岐をカバー。
        """
        # Arrange
        test_file = tmp_path / "small.log"
        test_file.write_text("small content")

        # Act
        result = file_reader._check_file_size(test_file, 1000)

        # Assert
        assert result is True

    def test_exceeded(self, file_reader, tmp_path):
        """FRD-013: _check_file_size 超過

        file_reader.py:L200-209 のFalse分岐をカバー。
        """
        # Arrange
        test_file = tmp_path / "large.log"
        test_file.write_text("x" * 500)

        # Act
        result = file_reader._check_file_size(test_file, 100)

        # Assert
        assert result is False


class TestReadFileChunked:
    """チャンク読み込みテスト"""

    def test_normal_read(self, file_reader, tmp_path):
        """FRD-014: _read_file_chunked 正常読み込み

        file_reader.py:L230-254 の正常チャンク読み込みをカバー。
        """
        # Arrange
        test_file = tmp_path / "normal.log"
        content = "log data\n" * 10
        test_file.write_text(content)

        # Act
        result = file_reader._read_file_chunked(test_file, 10000)

        # Assert
        assert result == content

    def test_truncation_at_max_size(self, file_reader, tmp_path):
        """FRD-015: _read_file_chunked truncate

        file_reader.py:L246-252 のmax_size到達時のtruncateをカバー。
        read_size >= max_size かつ f.read(1)が真の場合にtruncateメッセージ付与。
        """
        # Arrange
        test_file = tmp_path / "large.log"
        # max_size(100)より大きいファイルを作成
        test_file.write_text("x" * 200)

        # Act
        result = file_reader._read_file_chunked(test_file, 100)

        # Assert
        assert result.endswith("...[truncated for security - file too large]")
```

### 2.4 pattern_matcher.py テスト

```python
class TestLogPatternMatcherInit:
    """LogPatternMatcher初期化テスト"""

    def test_init_compiles_patterns(self, pattern_matcher):
        """PMT-001: 初期化でパターンコンパイル

        pattern_matcher.py:L29-55 のパターンコンパイルをカバー。
        """
        # Assert
        assert pattern_matcher.resource_count_pattern is not None
        assert pattern_matcher.policy_info_pattern is not None
        assert len(pattern_matcher._alternative_patterns) == 5


class TestExtractResourceCounts:
    """リソース数抽出テスト"""

    def test_main_pattern_match(self, pattern_matcher):
        """PMT-002: extract_resource_counts メインパターン

        pattern_matcher.py:L69-76 の"Filtered from X to Y"パターンをカバー。
        """
        # Arrange
        log_content = "2024-01-01 INFO Filtered from 100 to 5 ec2"

        # Act
        before, after = pattern_matcher.extract_resource_counts(log_content)

        # Assert
        assert before == 100
        assert after == 5

    def test_fallback_to_alternative(self, pattern_matcher):
        """PMT-003: extract_resource_counts 代替パターンへフォールバック

        pattern_matcher.py:L84 の代替パターン呼び出しをカバー。
        """
        # Arrange - メインパターンなし、count:パターンあり
        log_content = "policy:test resource:ec2 region:us-east-1 count:10 time:1.5"

        # Act
        before, after = pattern_matcher.extract_resource_counts(log_content)

        # Assert
        assert before == 10
        assert after == 10

    def test_alternative_resources_found(self, pattern_matcher):
        """PMT-004: _try_alternative_patterns "resources found"

        pattern_matcher.py:L96-114 の"resources found"代替パターンをカバー。
        """
        # Arrange
        log_content = "3 resources found in region"

        # Act
        before, after = pattern_matcher._try_alternative_patterns(log_content)

        # Assert
        assert before == 3
        assert after == 3

    def test_all_patterns_fail(self, pattern_matcher):
        """PMT-005: _try_alternative_patterns 全失敗

        pattern_matcher.py:L117-118 の全パターン失敗→(0,0)をカバー。
        """
        # Arrange
        log_content = "No matching patterns here at all"

        # Act
        before, after = pattern_matcher._try_alternative_patterns(log_content)

        # Assert
        assert before == 0
        assert after == 0


class TestExtractExecutionTime:
    """実行時間抽出テスト"""

    def test_pattern_match(self, pattern_matcher):
        """PMT-006: extract_execution_time パターン一致

        pattern_matcher.py:L130-134 のpolicy_infoパターンをカバー。
        """
        # Arrange
        log_content = "policy:test-policy resource:ec2 region:us-east-1 count:5 time:2.35"

        # Act
        result = pattern_matcher.extract_execution_time(log_content)

        # Assert
        assert result == 2.35

    def test_pattern_no_match(self, pattern_matcher):
        """PMT-007: extract_execution_time パターン不一致

        pattern_matcher.py:L136-137 のパターン不一致→0.0をカバー。
        """
        # Act
        result = pattern_matcher.extract_execution_time("No time info here")

        # Assert
        assert result == 0.0


class TestAnalyzeLogContent:
    """包括ログ解析テスト"""

    def test_full_analysis(self, pattern_matcher):
        """PMT-008: analyze_log_content 包括解析

        pattern_matcher.py:L139-177 の全抽出統合をカバー。
        """
        # Arrange
        log_content = (
            "Filtered from 50 to 3 ec2\n"
            "policy:test resource:ec2 region:us-east-1 count:3 time:1.5"
        )

        # Act
        result = pattern_matcher.analyze_log_content(log_content)

        # Assert
        assert result.resources_before_filter == 50
        assert result.resources_after_filter == 3
        assert result.execution_time == 1.5
        assert result.error_details["error_occurred"] is False
```

### 2.5 status_determiner.py テスト

```python
class TestPolicyStatusDeterminerInit:
    """PolicyStatusDeterminer初期化テスト"""

    def test_init(self, status_determiner):
        """SDT-001: 初期化

        status_determiner.py:L12-15 をカバー。
        """
        # Assert
        assert status_determiner.job_id == "test-job-id"


class TestDetermineStatus:
    """ステータス判定テスト"""

    def test_error_status(self, status_determiner, make_log_result):
        """SDT-002: determine_status ERROR

        status_determiner.py:L25-33 のerror_occurred=True分岐をカバー。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.log_analyzer.models import PolicyStatus
        log_result = make_log_result(error_occurred=True)

        # Act
        status = status_determiner.determine_status(log_result, resource_count=0)

        # Assert
        assert status == PolicyStatus.ERROR

    def test_no_resources(self, status_determiner, make_log_result):
        """SDT-003: determine_status NO_RESOURCES

        status_determiner.py:L39-41 のresources_before==0分岐をカバー。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.log_analyzer.models import PolicyStatus
        log_result = make_log_result(before=0, after=0)

        # Act
        status = status_determiner.determine_status(log_result, resource_count=0)

        # Assert
        assert status == PolicyStatus.NO_RESOURCES

    def test_compliant(self, status_determiner, make_log_result):
        """SDT-004: determine_status COMPLIANT

        status_determiner.py:L44-46 のbefore>0, after==0, count==0分岐をカバー。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.log_analyzer.models import PolicyStatus
        log_result = make_log_result(before=50, after=0)

        # Act
        status = status_determiner.determine_status(log_result, resource_count=0)

        # Assert
        assert status == PolicyStatus.COMPLIANT

    def test_violation(self, status_determiner, make_log_result):
        """SDT-005: determine_status VIOLATION

        status_determiner.py:L49-54 のcount>0分岐をカバー。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.log_analyzer.models import PolicyStatus
        log_result = make_log_result(before=50, after=5)

        # Act
        status = status_determiner.determine_status(log_result, resource_count=5)

        # Assert
        assert status == PolicyStatus.VIOLATION

    def test_default_compliant(self, status_determiner, make_log_result):
        """SDT-006: determine_status デフォルトCOMPLIANT

        status_determiner.py:L57-58 のデフォルト分岐をカバー。
        before>0, after>0だがcount==0のケース。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.log_analyzer.models import PolicyStatus
        log_result = make_log_result(before=50, after=10)

        # Act
        status = status_determiner.determine_status(log_result, resource_count=0)

        # Assert
        assert status == PolicyStatus.COMPLIANT


class TestCalculateComplianceRate:
    """コンプライアンス率計算テスト"""

    def test_zero_total(self, status_determiner):
        """SDT-007: calculate_compliance_rate total=0

        status_determiner.py:L62-63 のtotal==0分岐をカバー。
        """
        # Act
        result = status_determiner.calculate_compliance_rate(0, 0)

        # Assert
        assert result == 1.0

    def test_normal_calculation(self, status_determiner):
        """SDT-008: calculate_compliance_rate 正常

        status_determiner.py:L64-65 の正常計算をカバー。
        """
        # Act
        result = status_determiner.calculate_compliance_rate(100, 20)

        # Assert
        assert result == 0.8

    def test_violation_exceeds_total(self, status_determiner):
        """SDT-009: calculate_compliance_rate violation>total

        status_determiner.py:L65 のmax(0.0, ...)をカバー。
        違反数>合計の場合でも0.0が下限。
        """
        # Act
        result = status_determiner.calculate_compliance_rate(5, 10)

        # Assert
        assert result == 0.0


class TestDetermineResourceScope:
    """リソーススコープ判定テスト"""

    def test_global_resource(self, status_determiner):
        """SDT-010: determine_resource_scope global

        status_determiner.py:L78 のGLOBAL_AWS_RESOURCES一致をカバー。
        """
        # Act & Assert
        assert status_determiner.determine_resource_scope("iam") == "global"
        assert status_determiner.determine_resource_scope("s3") == "global"

    def test_regional_resource(self, status_determiner):
        """SDT-011: determine_resource_scope regional

        status_determiner.py:L78 のGLOBAL_AWS_RESOURCES不一致をカバー。
        """
        # Act & Assert
        assert status_determiner.determine_resource_scope("ec2") == "regional"
        assert status_determiner.determine_resource_scope("rds") == "regional"


class TestCreateErrorResult:
    """エラー結果作成テスト"""

    def test_error_result_structure(self, status_determiner):
        """SDT-012: create_error_result 構造確認

        status_determiner.py:L82-110 の戻り値dict構造をカバー。
        """
        # Act
        result = status_determiner.create_error_result("test-policy", "テストエラー")

        # Assert
        assert result["policy_name"] == "test-policy"
        assert result["status"] == "error"
        assert result["violation_count"] == 0
        assert result["error_details"]["error_occurred"] is True
        assert result["error_details"]["error_message"] == "テストエラー"
        assert result["error_details"]["error_type"] == "unknown"
        assert result["resource_statistics"]["compliance_rate"] == 0.0
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| FRD-E01 | read_json_file JSONDecodeError | 不正なJSON | JSONDecodeError re-raise |
| FRD-E02 | read_json_file 汎用例外 | open例外 | {} |
| FRD-E03 | _check_file_size stat例外 | stat失敗 | False |
| FRD-E04 | _read_file_chunked 汎用例外 | open例外 | エラーメッセージ文字列 |
| FRD-E05 | _validate_and_resolve_path Python3.8互換 | is_relative_to未対応 | AttributeError→relative_to fallback |

### 3.1 異常系テスト

```python
class TestLogAnalyzerBaseErrors:
    """基盤系異常系テスト"""

    def test_json_decode_error(self, file_reader, tmp_path):
        """FRD-E01: read_json_file JSONDecodeError

        file_reader.py:L109-111 のJSONDecodeError re-raiseをカバー。
        """
        # Arrange
        json_file = tmp_path / "invalid.json"
        json_file.write_text("{invalid json content")

        # Act & Assert
        with pytest.raises(json.JSONDecodeError):
            file_reader.read_json_file(str(json_file))

    def test_json_generic_exception(self, file_reader, tmp_path):
        """FRD-E02: read_json_file 汎用例外

        file_reader.py:L112-114 の汎用例外→{}をカバー。
        """
        # Arrange
        json_file = tmp_path / "test.json"
        json_file.write_text('{"key": "value"}')

        with patch("builtins.open", side_effect=PermissionError("読み取り拒否")):
            # Act
            result = file_reader.read_json_file(str(json_file))

        # Assert
        assert result == {}

    def test_check_file_size_stat_exception(self, file_reader, tmp_path):
        """FRD-E03: _check_file_size stat例外

        file_reader.py:L213-215 のstat例外→Falseをカバー。
        """
        # Arrange
        test_file = tmp_path / "test.log"
        test_file.write_text("data")
        mock_path = MagicMock()
        mock_path.stat.side_effect = OSError("stat error")

        # Act
        result = file_reader._check_file_size(mock_path, 1000)

        # Assert
        assert result is False

    def test_read_file_chunked_exception(self, file_reader, tmp_path):
        """FRD-E04: _read_file_chunked 汎用例外

        file_reader.py:L260-262 の汎用例外→エラー文字列をカバー。
        """
        # Arrange
        mock_path = MagicMock()

        with patch("builtins.open", side_effect=IOError("読み込みエラー")):
            # Act
            result = file_reader._read_file_chunked(mock_path, 1000)

        # Assert
        assert "Error reading file" in result

    def test_validate_path_python38_fallback(self, file_reader, tmp_path):
        """FRD-E05: _validate_and_resolve_path Python3.8互換

        file_reader.py:L175-181 のAttributeError→relative_to fallbackをカバー。
        is_relative_toが存在しない環境でrelative_toにより同等の検証を行う。
        """
        # Arrange
        test_file = tmp_path / "test.log"
        test_file.write_text("data")

        # Act - is_relative_toをAttributeErrorにしてfallbackを発動
        with patch.object(Path, 'is_relative_to', side_effect=AttributeError):
            result = file_reader._validate_and_resolve_path(str(test_file), str(tmp_path))

        # Assert
        assert isinstance(result, Path)
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| FRD-SEC-01 | パストラバーサル攻撃ベクター | 複数の攻撃パス | 全てValueError |
| FRD-SEC-02 | 許可外ディレクトリアクセス防止 | /var, /home等 | 全てValueError |
| FRD-SEC-03 | コマンドインジェクション文字拒否 | パイプ、セミコロン等 | 全てValueError |
| FRD-SEC-04 | シンボリックリンク攻撃防止 | /etc/passwdへのシンボリックリンク | ValueError |

```python
@pytest.mark.security
class TestLogAnalyzerBaseSecurity:
    """基盤系セキュリティテスト"""

    def test_path_traversal_attack_vectors(self, file_reader):
        """FRD-SEC-01: パストラバーサル攻撃ベクター

        file_reader.py:L142-159 の危険パターン検出をカバー。
        代表的な攻撃パターン7種を検証（11パターン中の代表）。
        """
        # Arrange
        attack_paths = [
            "/tmp/../../../etc/passwd",   # '..' パストラバーサル
            "/tmp/log/../../etc/shadow",  # '..' + '/etc/' 複合攻撃
            "~/.ssh/id_rsa",              # '~' ホームディレクトリ展開
            "/proc/self/environ",         # '/proc/' プロセス情報
            "/sys/class/net/eth0",        # '/sys/' システム情報
            "/dev/null",                  # '/dev/' デバイスファイル
            "/root/.bashrc",              # '/root/' rootディレクトリ
        ]

        # Act & Assert
        for path in attack_paths:
            with pytest.raises(ValueError, match="危険なパスパターン"):
                file_reader._validate_and_resolve_path(path)

    def test_directory_restriction(self, file_reader):
        """FRD-SEC-02: 許可外ディレクトリアクセス防止

        file_reader.py:L172-181 のis_relative_toチェックをカバー。
        /tmp配下以外のディレクトリアクセスが拒否される。
        """
        # Act & Assert
        with pytest.raises(ValueError, match="許可されていないディレクトリ"):
            file_reader._validate_and_resolve_path("/var/log/syslog", "/tmp")

        with pytest.raises(ValueError, match="許可されていないディレクトリ"):
            file_reader._validate_and_resolve_path("/home/user/data.log", "/tmp")

    def test_command_injection_chars_rejected(self, file_reader):
        """FRD-SEC-03: コマンドインジェクション文字拒否

        file_reader.py:L151-153 のインジェクション文字検出をカバー。
        """
        # Arrange
        injection_paths = [
            "/tmp/file|cat /etc/passwd",
            "/tmp/file;rm -rf /",
            "/tmp/file&echo hack",
            "/tmp/file\\..\\etc\\passwd",
        ]

        # Act & Assert
        for path in injection_paths:
            with pytest.raises(ValueError, match="危険なパスパターン"):
                file_reader._validate_and_resolve_path(path)

    def test_symlink_attack_prevention(self, file_reader, tmp_path):
        """FRD-SEC-04: シンボリックリンク攻撃防止

        file_reader.py:L161-167 のresolve(strict=False)と
        L170-181 のis_relative_toチェックをカバー。
        tmp_path配下のシンボリックリンクが許可外パスを指す場合、
        resolve後のis_relative_toで拒否される。
        """
        # Arrange
        symlink = tmp_path / "evil_link"
        symlink.symlink_to("/etc/passwd")

        # Act & Assert - resolveで/etc/passwdに解決されるがtmp_path外なので拒否
        with pytest.raises(ValueError, match="許可されていないディレクトリ"):
            file_reader._validate_and_resolve_path(str(symlink), str(tmp_path))
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_log_analyzer_module` | テスト間のモジュール状態リセット | function | Yes |
| `file_reader` | テスト用LogFileReaderインスタンス | function | No |
| `pattern_matcher` | テスト用LogPatternMatcherインスタンス | function | No |
| `status_determiner` | テスト用PolicyStatusDeterminerインスタンス | function | No |
| `make_log_result` | LogAnalysisResultファクトリ | function | No |

### 共通フィクスチャ定義

```python
# test/unit/jobs/tasks/new_custodian_scan/log_analyzer/conftest.py
import sys
import pytest
from unittest.mock import patch

MODULE_FRD = "app.jobs.tasks.new_custodian_scan.log_analyzer.file_reader"
MODULE_PMT = "app.jobs.tasks.new_custodian_scan.log_analyzer.pattern_matcher"
MODULE_SDT = "app.jobs.tasks.new_custodian_scan.log_analyzer.status_determiner"


@pytest.fixture(autouse=True)
def reset_log_analyzer_module():
    """テスト間のモジュール状態リセット（autouse）"""
    yield
    modules_to_remove = [k for k in sys.modules
                         if k.startswith("app.jobs.tasks.new_custodian_scan.log_analyzer")]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def file_reader():
    """テスト用LogFileReaderインスタンス

    TaskLoggerをモック化して実インスタンスを生成。
    tmp_pathと組み合わせてファイルシステムテストを行う。
    """
    with patch(f"{MODULE_FRD}.TaskLogger"):
        from app.jobs.tasks.new_custodian_scan.log_analyzer.file_reader import LogFileReader
        return LogFileReader("test-job-id")


@pytest.fixture
def pattern_matcher():
    """テスト用LogPatternMatcherインスタンス

    純粋な文字列処理のためTaskLoggerのみモック化。
    """
    with patch(f"{MODULE_PMT}.TaskLogger"):
        from app.jobs.tasks.new_custodian_scan.log_analyzer.pattern_matcher import LogPatternMatcher
        return LogPatternMatcher("test-job-id")


@pytest.fixture
def status_determiner():
    """テスト用PolicyStatusDeterminerインスタンス

    TaskLoggerをモック化して実インスタンスを生成。
    """
    with patch(f"{MODULE_SDT}.TaskLogger"):
        from app.jobs.tasks.new_custodian_scan.log_analyzer.status_determiner import PolicyStatusDeterminer
        return PolicyStatusDeterminer("test-job-id")


@pytest.fixture
def make_log_result():
    """LogAnalysisResultファクトリフィクスチャ

    テスト用のLogAnalysisResultを簡単に生成するヘルパー。
    """
    from app.jobs.tasks.new_custodian_scan.log_analyzer.models import LogAnalysisResult

    def _factory(before=0, after=0, time=0.0, error_occurred=False,
                 error_type=None, error_message=""):
        error_details = {"error_occurred": error_occurred}
        if error_type:
            error_details["error_type"] = error_type
        if error_message:
            error_details["error_message"] = error_message
        return LogAnalysisResult(
            resources_before_filter=before,
            resources_after_filter=after,
            execution_time=time,
            error_details=error_details
        )

    return _factory
```

---

## 6. テスト実行例

```bash
# 基盤系テスト全体を実行
pytest test/unit/jobs/tasks/new_custodian_scan/log_analyzer/test_log_analyzer_base.py -v

# クラス単位で実行
pytest test/unit/jobs/tasks/new_custodian_scan/log_analyzer/test_log_analyzer_base.py::TestReadLogFile -v
pytest test/unit/jobs/tasks/new_custodian_scan/log_analyzer/test_log_analyzer_base.py::TestDetermineStatus -v

# カバレッジ付きで実行（__init__.pyを含むパッケージ全体）
pytest test/unit/jobs/tasks/new_custodian_scan/log_analyzer/test_log_analyzer_base.py \
  --cov=app.jobs.tasks.new_custodian_scan.log_analyzer \
  --cov-report=term-missing -v

# セキュリティマーカーで実行（実行前提のマーカー登録が必要）
pytest test/unit/jobs/tasks/new_custodian_scan/log_analyzer/test_log_analyzer_base.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 43 | MDL-001〜004, PKG-001〜004, FRD-001〜015, PMT-001〜008, SDT-001〜012 |
| 異常系 | 5 | FRD-E01〜E05 |
| セキュリティ | 4 | FRD-SEC-01〜04 |
| **合計** | **52** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestModels` | MDL-001〜004 | 4 |
| `TestPackageInit` | PKG-001〜004 | 4 |
| `TestLogFileReaderInit` | FRD-001 | 1 |
| `TestReadLogFile` | FRD-002〜004 | 3 |
| `TestReadJsonFile` | FRD-005〜007 | 3 |
| `TestValidateAndResolvePath` | FRD-008〜011 | 4 |
| `TestCheckFileSize` | FRD-012〜013 | 2 |
| `TestReadFileChunked` | FRD-014〜015 | 2 |
| `TestLogPatternMatcherInit` | PMT-001 | 1 |
| `TestExtractResourceCounts` | PMT-002〜005 | 4 |
| `TestExtractExecutionTime` | PMT-006〜007 | 2 |
| `TestAnalyzeLogContent` | PMT-008 | 1 |
| `TestPolicyStatusDeterminerInit` | SDT-001 | 1 |
| `TestDetermineStatus` | SDT-002〜006 | 5 |
| `TestCalculateComplianceRate` | SDT-007〜009 | 3 |
| `TestDetermineResourceScope` | SDT-010〜011 | 2 |
| `TestCreateErrorResult` | SDT-012 | 1 |
| `TestLogAnalyzerBaseErrors` | FRD-E01〜E05 | 5 |
| `TestLogAnalyzerBaseSecurity` | FRD-SEC-01〜04 | 4 |

### 実装失敗が予想されるテスト

以下の実行前提が整備されていれば、失敗が予想されるテストはありません。

#### 実行前提（実装タスクとしてpyproject.tomlへの追加が必要）

| 前提 | 対応内容 |
|------|---------|
| `security`マーカー | `[tool.pytest.ini_options].markers` に `"security: セキュリティテスト"` を追加 |

### 注意事項

- `file_reader.py` の `DEFAULT_ALLOWED_BASE = "/tmp"` のため、tmp_pathフィクスチャ（/tmp配下）との組み合わせが必須
- PKG-002/003のテストは`PolicyAnalysisOrchestrator`をモック化するため、orchestrator.pyの実装には依存しない
- `pattern_matcher.py` のテストは実際の正規表現マッチングを検証するため、モック不要
- FRD-E05のPython3.8互換テストは `is_relative_to` をAttributeErrorにしてfallbackを検証

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `__init__.py` のテストはPolicyAnalysisOrchestratorをモック化 | orchestratorとの統合動作は検証しない | #15bのorchestrator仕様書で統合テストとして対応 |
| 2 | `file_reader.py` のシンボリックリンク解決はFRD-SEC-04で直接検証 | /etc/passwdへのシンボリックリンク作成にはOS権限が必要 | tmp_path配下でsymlink_toを使用し実際のシンボリックリンクを作成して検証 |
| 3 | `_read_file_chunked` のUnicodeDecodeError分岐 | `errors='replace'`により到達不能（L258コメント参照） | 実装コメント通り到達しないため、汎用例外テストでカバー |
| 4 | `pattern_matcher.py` の代替パターン5種のうち3種のみ検証 | "resources matched"、"Found resources"パターンは未検証 | 3種で代替パターンロジックの動作は確認済み |
| 5 | `DEFAULT_ALLOWED_BASE="/tmp"` に依存 | テスト環境のtmp_pathが/tmp配下でない場合失敗 | 標準的なLinux/macOS環境ではtmp_pathは/tmp配下 |
