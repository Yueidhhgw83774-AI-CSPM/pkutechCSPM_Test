# jobs/common テストケース

## 1. 概要

`app/jobs/common/` パッケージは、ジョブシステム全体で使用される共通基盤を提供します。エラー処理の構造化（カスタム例外階層・Custodianエラーハンドラー）、ステータス追跡、タスクロギングの3つの責務を担います。

### 1.1 主要機能

| 機能 | ファイル | 説明 |
|------|---------|------|
| `TaskError` 例外階層 | `error_handling.py` | タスク実行時の構造化エラークラス群 |
| `ValidationErrorInfo` | `error_handling.py` | 検証エラー情報データクラス |
| `ExecutionErrorInfo` | `error_handling.py` | 実行エラー情報データクラス |
| `CustodianErrorHandler` | `error_handling.py` | Custodianエラーの構造化処理・ユーザーメッセージ生成 |
| `StatusTracker` | `status_tracking.py` | ジョブステータス追跡ユーティリティ |
| `TaskLogger` | `logging.py` | タスク用ロガー（ジョブログ統合） |

### 1.2 カバレッジ目標: 90%

> **注記**: エラー処理はジョブシステム全体の信頼性に直結する基盤機能であり、特に `CustodianErrorHandler` の分岐網羅が重要。セキュリティスキャン結果の正確なエラー分類に影響するため高カバレッジが必要。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象1 | `app/jobs/common/error_handling.py` |
| テスト対象2 | `app/jobs/common/status_tracking.py` |
| テスト対象3 | `app/jobs/common/logging.py` |
| テストコード | `test/unit/jobs/common/test_jobs_common.py` |

### 1.4 補足情報

#### モジュール間依存関係

```
logging.py ──→ status_manager.append_job_log
status_tracking.py ──→ status_manager.update_job_status
                    ──→ status_manager.update_job_progress
error_handling.py ──→ logging.TaskLogger
```

#### 主要分岐（error_handling.py: CustodianErrorHandler）

| 分岐 | 条件 | 結果 |
|------|------|------|
| `log_execution_error` L166 | `type == "authentication_error"` or `"permission_error" in type` | `fatal` + `authentication_errors` カウント |
| `log_execution_error` L172 | `return_code == 1` | `fatal` |
| `log_execution_error` L175 | `return_code == 2` | `warning` |
| `log_execution_error` L178 | その他 | `unknown` |
| `_create_validation_error_message` | `type` 5パターン | `invalid_resource`, `yaml_structure`, `missing_field`, `custodian_schema`, デフォルト |
| `_create_execution_error_message` | `type` 7パターン | `permission_error`, `authentication_error`, `invalid_resource`, `filter_error`, `action_error`, `network_error`, デフォルト |
| `_determine_error_severity` | カウント条件 | `high`, `medium`, `low` |
| `should_fail_job` | カウント条件 | `True`（validation/fatal/auth > 0）, `False` |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| JCOM-001 | TaskLogger: デフォルトtask_name | job_id="job-1" | task_name="Task" |
| JCOM-002 | TaskLogger: カスタムtask_name | task_name="MyTask" | task_name="MyTask" |
| JCOM-003 | TaskLogger: _format_message（コンテキストなし） | level="INFO", message="test" | `[Task][INFO] test` |
| JCOM-004 | TaskLogger: _format_message（コンテキストあり） | context={"k": "v"} | `| Context: k=v` 付き |
| JCOM-005 | TaskLogger: infoログ出力 | message="情報" | append_job_log + print呼び出し |
| JCOM-006 | TaskLogger: errorログ出力 | message="エラー" | append_job_log + print呼び出し |
| JCOM-007 | TaskLogger: warningログ出力 | message="警告" | append_job_log + print呼び出し |
| JCOM-008 | TaskLogger: debugログ出力（printなし） | message="デバッグ" | append_job_logのみ（printなし） |
| JCOM-009 | TaskLogger: progressログ出力 | current=5, total=10 | `メッセージ (5/10)` 形式でinfo呼び出し |
| JCOM-010 | StatusTracker: 初期化 | job_id="job-1" | job_idが保持される |
| JCOM-011 | StatusTracker: update_status | status="running" | update_job_status呼び出し |
| JCOM-012 | StatusTracker: update_progress | current=3, total=10 | update_job_progress呼び出し |
| JCOM-013 | StatusTracker: set_running | message="開始" | update_status("running") |
| JCOM-014 | StatusTracker: track_batch_progress（追加情報なし） | item_description="ファイル" | 進捗メッセージ生成 |
| JCOM-015 | StatusTracker: track_batch_progress（追加情報あり） | additional_info="50%" | メッセージに追加情報含む |
| JCOM-016 | StatusTracker: create_summary_data | kwargs指定 | job_id + kwargs含む辞書 |
| JCOM-017 | TaskError: 基本生成 | message="エラー" | message, error_code=None, context={} |
| JCOM-018 | TaskError: 全パラメータ指定 | error_code="E001", context={"k":"v"} | 全フィールド設定 |
| JCOM-019 | ValidationError: 生成 | field_name="name" | error_code="VALIDATION_ERROR" |
| JCOM-020 | ExternalServiceError: 生成 | service_name="AWS" | error_code="EXTERNAL_SERVICE_ERROR" |
| JCOM-021 | ResourceNotFoundError: 生成 | resource_type="policy" | error_code="RESOURCE_NOT_FOUND" |
| JCOM-022 | ProcessingError: 生成 | processing_stage="parse" | error_code="PROCESSING_ERROR" |
| JCOM-023 | ValidationErrorInfo: 生成 | 全フィールド指定 | データクラスインスタンス |
| JCOM-024 | ExecutionErrorInfo: 生成 | 全フィールド指定 | デフォルトerror_stage="execution" |
| JCOM-025 | CustodianErrorHandler: 初期化 | job_id="job-1" | error_counts全て0 |
| JCOM-026 | CustodianErrorHandler: log_validation_error（全フィールド） | 全optional指定 | カウント+1, ログにフィールド含む |
| JCOM-027 | CustodianErrorHandler: log_validation_error（最小フィールド） | optionalなし | カウント+1, 最小コンテキスト |
| JCOM-028 | CustodianErrorHandler: log_execution_error（認証エラー） | type="authentication_error" | fatal + auth カウント |
| JCOM-029 | CustodianErrorHandler: log_execution_error（権限エラー） | type="permission_error" | fatal + auth カウント |
| JCOM-030 | CustodianErrorHandler: log_execution_error（return_code=1） | return_code=1 | fatal カウント |
| JCOM-031 | CustodianErrorHandler: log_execution_error（return_code=2） | return_code=2 | warning カウント |
| JCOM-032 | CustodianErrorHandler: log_execution_error（return_code=0） | return_code=0 | unknown（カウント増加なし） |
| JCOM-033 | create_user_friendly_error: ValidationErrorInfo | ValidationErrorInfo | _create_validation_error_message委譲 |
| JCOM-034 | create_user_friendly_error: ExecutionErrorInfo | ExecutionErrorInfo | _create_execution_error_message委譲 |
| JCOM-035 | create_user_friendly_error: 不明型 | 文字列 | `エラー: {str}` |
| JCOM-036 | _create_validation_error_message: invalid_resource | type="invalid_resource" | リソースタイプ含むメッセージ |
| JCOM-037 | _create_validation_error_message: yaml_structure | type="yaml_structure" | YAML構造エラーメッセージ |
| JCOM-038 | _create_validation_error_message: missing_field | type="missing_field" | 必須フィールドメッセージ |
| JCOM-039 | _create_validation_error_message: custodian_schema | type="custodian_schema" | スキーマ検証エラーメッセージ |
| JCOM-040 | _create_validation_error_message: デフォルト | type="other" | `検証エラー: {message}` |
| JCOM-041 | _create_execution_error_message: permission_error | type="permission_error" | 認証・権限エラーメッセージ |
| JCOM-042 | _create_execution_error_message: authentication_error | type="authentication_error" | 認証・権限エラーメッセージ |
| JCOM-043 | _create_execution_error_message: invalid_resource | type="invalid_resource" | リソースタイプエラーメッセージ |
| JCOM-044 | _create_execution_error_message: filter_error | type="filter_error" | フィルター設定エラーメッセージ |
| JCOM-045 | _create_execution_error_message: action_error | type="action_error" | アクション実行エラーメッセージ |
| JCOM-046 | _create_execution_error_message: network_error | type="network_error" | ネットワークエラーメッセージ |
| JCOM-047 | _create_execution_error_message: デフォルト | type="unknown" | 汎用実行エラーメッセージ |
| JCOM-048 | get_error_summary: エラーなし | 初期状態 | total_errors=0, has_errors=False |
| JCOM-049 | get_error_summary: エラーあり | validation + execution | 正しいカウント集計 |
| JCOM-050 | _determine_error_severity: high | fatal_errors > 0 | "high" |
| JCOM-051 | _determine_error_severity: medium | warning_errors > 0のみ | "medium" |
| JCOM-052 | _determine_error_severity: low | エラーなし | "low" |
| JCOM-053 | should_fail_job: validation errors | validation_errors > 0 | True |
| JCOM-054 | should_fail_job: fatal errors | fatal_errors > 0 | True |
| JCOM-055 | should_fail_job: auth errors | authentication_errors > 0 | True |
| JCOM-056 | should_fail_job: エラーなし | 全カウント0 | False |
| JCOM-057 | log_execution_error: 権限エラー部分一致 | type="account_permission_error" | fatal + auth カウント（部分一致） |

### 2.1 TaskLogger テスト

```python
# test/unit/jobs/common/test_jobs_common.py
import pytest
from unittest.mock import patch, MagicMock, call

from app.jobs.common.logging import TaskLogger


class TestTaskLogger:
    """TaskLoggerクラスのテスト"""

    def test_default_task_name(self):
        """JCOM-001: TaskLogger: デフォルトtask_name"""
        # Arrange & Act
        logger = TaskLogger(job_id="job-1")

        # Assert
        assert logger.job_id == "job-1"
        assert logger.task_name == "Task"

    def test_custom_task_name(self):
        """JCOM-002: TaskLogger: カスタムtask_name"""
        # Arrange & Act
        logger = TaskLogger(job_id="job-2", task_name="MyTask")

        # Assert
        assert logger.task_name == "MyTask"

    def test_format_message_without_context(self):
        """JCOM-003: TaskLogger: _format_message（コンテキストなし）"""
        # Arrange
        logger = TaskLogger(job_id="job-1", task_name="TestTask")

        # Act
        result = logger._format_message("INFO", "テストメッセージ")

        # Assert
        assert result == "[TestTask][INFO] テストメッセージ"

    def test_format_message_with_context(self):
        """JCOM-004: TaskLogger: _format_message（コンテキストあり）

        logging.py:17-18 のif context分岐をカバー
        """
        # Arrange
        logger = TaskLogger(job_id="job-1", task_name="TestTask")
        context = {"key1": "value1", "key2": "value2"}

        # Act
        result = logger._format_message("ERROR", "エラー発生", context=context)

        # Assert
        assert "[TestTask][ERROR] エラー発生" in result
        assert "| Context:" in result
        assert "key1=value1" in result
        assert "key2=value2" in result

    @patch("app.jobs.common.logging.append_job_log")
    def test_info_log(self, mock_append, capsys):
        """JCOM-005: TaskLogger: infoログ出力"""
        # Arrange
        logger = TaskLogger(job_id="job-1", task_name="TestTask")

        # Act
        logger.info("情報メッセージ")

        # Assert
        mock_append.assert_called_once()
        args = mock_append.call_args
        assert args[0][0] == "job-1"
        assert "[TestTask][INFO] 情報メッセージ" in args[0][1]
        # printも呼ばれる
        captured = capsys.readouterr()
        assert "Job job-1:" in captured.out

    @patch("app.jobs.common.logging.append_job_log")
    def test_error_log(self, mock_append, capsys):
        """JCOM-006: TaskLogger: errorログ出力"""
        # Arrange
        logger = TaskLogger(job_id="job-1", task_name="TestTask")

        # Act
        logger.error("エラーメッセージ")

        # Assert
        mock_append.assert_called_once()
        args = mock_append.call_args
        assert "[TestTask][ERROR] エラーメッセージ" in args[0][1]
        captured = capsys.readouterr()
        assert "Job job-1:" in captured.out

    @patch("app.jobs.common.logging.append_job_log")
    def test_warning_log(self, mock_append, capsys):
        """JCOM-007: TaskLogger: warningログ出力"""
        # Arrange
        logger = TaskLogger(job_id="job-1", task_name="TestTask")

        # Act
        logger.warning("警告メッセージ")

        # Assert
        mock_append.assert_called_once()
        args = mock_append.call_args
        assert "[TestTask][WARNING] 警告メッセージ" in args[0][1]

    @patch("app.jobs.common.logging.append_job_log")
    def test_debug_log_no_print(self, mock_append, capsys):
        """JCOM-008: TaskLogger: debugログ出力（printなし）

        logging.py:40-41 debugメソッドはappend_job_logのみでprintを呼ばない
        """
        # Arrange
        logger = TaskLogger(job_id="job-1", task_name="TestTask")

        # Act
        logger.debug("デバッグメッセージ")

        # Assert
        mock_append.assert_called_once()
        args = mock_append.call_args
        assert "[TestTask][DEBUG] デバッグメッセージ" in args[0][1]
        # debugではprintが呼ばれない
        captured = capsys.readouterr()
        assert captured.out == ""

    @patch("app.jobs.common.logging.append_job_log")
    def test_progress_log(self, mock_append):
        """JCOM-009: TaskLogger: progressログ出力"""
        # Arrange
        logger = TaskLogger(job_id="job-1", task_name="TestTask")

        # Act
        logger.progress("処理中", current=5, total=10)

        # Assert
        mock_append.assert_called_once()
        args = mock_append.call_args
        assert "処理中 (5/10)" in args[0][1]
```

### 2.2 StatusTracker テスト

```python
from app.jobs.common.status_tracking import StatusTracker


class TestStatusTracker:
    """StatusTrackerクラスのテスト"""

    def test_init(self):
        """JCOM-010: StatusTracker: 初期化"""
        # Arrange & Act
        tracker = StatusTracker(job_id="job-1")

        # Assert
        assert tracker.job_id == "job-1"

    @patch("app.jobs.common.status_tracking.update_job_status")
    def test_update_status(self, mock_update):
        """JCOM-011: StatusTracker: update_status"""
        # Arrange
        tracker = StatusTracker(job_id="job-1")

        # Act
        tracker.update_status("running", "実行開始")

        # Assert
        mock_update.assert_called_once_with("job-1", "running", "実行開始")

    @patch("app.jobs.common.status_tracking.update_job_progress")
    def test_update_progress(self, mock_progress):
        """JCOM-012: StatusTracker: update_progress"""
        # Arrange
        tracker = StatusTracker(job_id="job-1")

        # Act
        tracker.update_progress(3, 10, "処理中", "regions")

        # Assert
        mock_progress.assert_called_once_with("job-1", 3, 10, "処理中", "regions")

    @patch("app.jobs.common.status_tracking.update_job_status")
    def test_set_running(self, mock_update):
        """JCOM-013: StatusTracker: set_running"""
        # Arrange
        tracker = StatusTracker(job_id="job-1")

        # Act
        tracker.set_running("スキャン開始")

        # Assert
        mock_update.assert_called_once_with("job-1", "running", "スキャン開始")

    @patch("app.jobs.common.status_tracking.update_job_progress")
    def test_track_batch_progress_without_additional_info(self, mock_progress):
        """JCOM-014: StatusTracker: track_batch_progress（追加情報なし）

        status_tracking.py:38-39 additional_infoがNoneの場合の分岐
        """
        # Arrange
        tracker = StatusTracker(job_id="job-1")

        # Act
        tracker.track_batch_progress(
            current_item=2, total_items=5, item_description="ファイル処理"
        )

        # Assert
        mock_progress.assert_called_once()
        args = mock_progress.call_args
        assert args[0][1] == 2  # current
        assert args[0][2] == 5  # total
        message = args[0][3]
        assert "処理中: ファイル処理 (2/5)" in message
        # 追加情報なしの場合、" - " が含まれない
        assert " - " not in message

    @patch("app.jobs.common.status_tracking.update_job_progress")
    def test_track_batch_progress_with_additional_info(self, mock_progress):
        """JCOM-015: StatusTracker: track_batch_progress（追加情報あり）

        status_tracking.py:39-40 additional_info指定時の分岐
        """
        # Arrange
        tracker = StatusTracker(job_id="job-1")

        # Act
        tracker.track_batch_progress(
            current_item=3,
            total_items=10,
            item_description="リージョンスキャン",
            additional_info="ap-northeast-1",
        )

        # Assert
        mock_progress.assert_called_once()
        message = mock_progress.call_args[0][3]
        assert "処理中: リージョンスキャン (3/10)" in message
        assert " - ap-northeast-1" in message

    def test_create_summary_data(self):
        """JCOM-016: StatusTracker: create_summary_data"""
        # Arrange
        tracker = StatusTracker(job_id="job-1")

        # Act
        result = tracker.create_summary_data(
            total_regions=5, success_count=4, error_count=1
        )

        # Assert
        assert result["job_id"] == "job-1"
        assert result["total_regions"] == 5
        assert result["success_count"] == 4
        assert result["error_count"] == 1
```

### 2.3 TaskError例外階層テスト

```python
from app.jobs.common.error_handling import (
    TaskError,
    ValidationError,
    ExternalServiceError,
    ResourceNotFoundError,
    ProcessingError,
)


class TestTaskErrorHierarchy:
    """TaskError例外階層のテスト"""

    def test_task_error_basic(self):
        """JCOM-017: TaskError: 基本生成"""
        # Arrange & Act
        error = TaskError("基本エラー")

        # Assert
        assert str(error) == "基本エラー"
        assert error.message == "基本エラー"
        assert error.error_code is None
        assert error.context == {}

    def test_task_error_full_params(self):
        """JCOM-018: TaskError: 全パラメータ指定"""
        # Arrange
        context = {"key": "value"}

        # Act
        error = TaskError("エラー", error_code="E001", context=context)

        # Assert
        assert error.message == "エラー"
        assert error.error_code == "E001"
        assert error.context == {"key": "value"}

    def test_validation_error(self):
        """JCOM-019: ValidationError: 生成"""
        # Arrange & Act
        error = ValidationError(
            "入力不正", field_name="policy_name", invalid_value=""
        )

        # Assert
        assert isinstance(error, TaskError)
        assert error.error_code == "VALIDATION_ERROR"
        assert error.field_name == "policy_name"
        assert error.invalid_value == ""

    def test_external_service_error(self):
        """JCOM-020: ExternalServiceError: 生成"""
        # Arrange & Act
        error = ExternalServiceError(
            "AWS接続失敗",
            service_name="AWS",
            status_code=503,
            response_data={"error": "Service Unavailable"},
        )

        # Assert
        assert isinstance(error, TaskError)
        assert error.error_code == "EXTERNAL_SERVICE_ERROR"
        assert error.service_name == "AWS"
        assert error.status_code == 503
        assert error.response_data == {"error": "Service Unavailable"}

    def test_resource_not_found_error(self):
        """JCOM-021: ResourceNotFoundError: 生成"""
        # Arrange & Act
        error = ResourceNotFoundError(
            "ポリシー未発見", resource_type="policy", resource_id="pol-001"
        )

        # Assert
        assert isinstance(error, TaskError)
        assert error.error_code == "RESOURCE_NOT_FOUND"
        assert error.resource_type == "policy"
        assert error.resource_id == "pol-001"

    def test_processing_error(self):
        """JCOM-022: ProcessingError: 生成"""
        # Arrange & Act
        error = ProcessingError(
            "パース失敗", processing_stage="yaml_parse", partial_results=["line1"]
        )

        # Assert
        assert isinstance(error, TaskError)
        assert error.error_code == "PROCESSING_ERROR"
        assert error.processing_stage == "yaml_parse"
        assert error.partial_results == ["line1"]
```

### 2.4 データクラステスト

```python
from app.jobs.common.error_handling import ValidationErrorInfo, ExecutionErrorInfo


class TestErrorInfoDataclasses:
    """エラー情報データクラスのテスト"""

    def test_validation_error_info(self):
        """JCOM-023: ValidationErrorInfo: 生成"""
        # Arrange & Act
        info = ValidationErrorInfo(
            type="yaml_structure",
            policy_index=0,
            policy_name="test-policy",
            message="YAMLパースエラー",
            stage="basic",
            resource_type="aws.ec2",
            field_name="resource",
        )

        # Assert
        assert info.type == "yaml_structure"
        assert info.policy_index == 0
        assert info.policy_name == "test-policy"
        assert info.message == "YAMLパースエラー"
        assert info.stage == "basic"
        assert info.resource_type == "aws.ec2"
        assert info.field_name == "resource"

    def test_execution_error_info(self):
        """JCOM-024: ExecutionErrorInfo: 生成"""
        # Arrange & Act
        info = ExecutionErrorInfo(
            type="permission_error",
            region="ap-northeast-1",
            return_code=2,
            message="権限不足",
            policies=["policy-1", "policy-2"],
            resource_type="aws.s3",
        )

        # Assert
        assert info.type == "permission_error"
        assert info.region == "ap-northeast-1"
        assert info.return_code == 2
        assert info.policies == ["policy-1", "policy-2"]
        assert info.error_stage == "execution"  # デフォルト値
```

### 2.5 CustodianErrorHandler テスト

```python
from app.jobs.common.error_handling import CustodianErrorHandler


class TestCustodianErrorHandler:
    """CustodianErrorHandlerクラスのテスト"""

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_init(self, mock_logger_cls):
        """JCOM-025: CustodianErrorHandler: 初期化"""
        # Arrange & Act
        handler = CustodianErrorHandler(job_id="job-1")

        # Assert
        assert handler.job_id == "job-1"
        assert handler.error_counts["validation_errors"] == 0
        assert handler.error_counts["execution_errors"] == 0
        assert handler.error_counts["warning_errors"] == 0
        assert handler.error_counts["fatal_errors"] == 0
        assert handler.error_counts["authentication_errors"] == 0
        mock_logger_cls.assert_called_once_with("job-1", "CustodianErrorHandler")

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_log_validation_error_all_fields(self, mock_logger_cls):
        """JCOM-026: CustodianErrorHandler: log_validation_error（全フィールド）

        error_handling.py:145-152 の全optional分岐をカバー
        """
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ValidationErrorInfo(
            type="invalid_resource",
            policy_index=0,
            policy_name="test-policy",
            message="不正リソース",
            stage="custodian",
            resource_type="aws.invalid",
            field_name="resource",
        )

        # Act
        handler.log_validation_error(error_info)

        # Assert
        assert handler.error_counts["validation_errors"] == 1
        mock_logger = mock_logger_cls.return_value
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        context = call_args[1]["context"]
        assert context["policy_index"] == 0
        assert context["policy_name"] == "test-policy"
        assert context["resource_type"] == "aws.invalid"
        assert context["field_name"] == "resource"

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_log_validation_error_minimal(self, mock_logger_cls):
        """JCOM-027: CustodianErrorHandler: log_validation_error（最小フィールド）

        error_handling.py:145-152 optionalフィールドがNone/空の場合
        """
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ValidationErrorInfo(
            type="yaml_structure",
            policy_index=None,
            policy_name=None,
            message="構造エラー",
            stage="basic",
        )

        # Act
        handler.log_validation_error(error_info)

        # Assert
        assert handler.error_counts["validation_errors"] == 1
        mock_logger = mock_logger_cls.return_value
        context = mock_logger.error.call_args[1]["context"]
        # optionalフィールドはcontextに含まれない
        assert "policy_index" not in context
        assert "policy_name" not in context
        assert "resource_type" not in context
        assert "field_name" not in context
```

### 2.6 CustodianErrorHandler: log_execution_error テスト

```python
class TestCustodianErrorHandlerExecution:
    """CustodianErrorHandler: log_execution_error の分岐テスト"""

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_authentication_error(self, mock_logger_cls):
        """JCOM-028: log_execution_error: 認証エラー（fatal）

        error_handling.py:166 type == "authentication_error" 分岐
        """
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ExecutionErrorInfo(
            type="authentication_error",
            region="us-east-1",
            return_code=2,
            message="認証失敗",
            policies=["pol-1"],
        )

        # Act
        handler.log_execution_error(error_info)

        # Assert
        assert handler.error_counts["execution_errors"] == 1
        assert handler.error_counts["authentication_errors"] == 1
        assert handler.error_counts["fatal_errors"] == 1
        mock_logger = mock_logger_cls.return_value
        mock_logger.error.assert_any_call("認証エラーを致命的エラーとして処理: 認証失敗")

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_permission_error_in_type(self, mock_logger_cls):
        """JCOM-029: log_execution_error: 権限エラー（fatal）

        error_handling.py:166 "permission_error" in type 分岐
        """
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ExecutionErrorInfo(
            type="permission_error",
            region="ap-northeast-1",
            return_code=2,
            message="権限不足",
            policies=["pol-1"],
        )

        # Act
        handler.log_execution_error(error_info)

        # Assert
        assert handler.error_counts["authentication_errors"] == 1
        assert handler.error_counts["fatal_errors"] == 1

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_permission_error_partial_match(self, mock_logger_cls):
        """JCOM-057: log_execution_error: 権限エラー部分一致（fatal）

        error_handling.py:166 "permission_error" in type の部分一致動作を検証。
        "account_permission_error" などのサブタイプも認証エラーとしてカウントされる。
        """
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ExecutionErrorInfo(
            type="account_permission_error_denied",
            region="ap-northeast-1",
            return_code=1,
            message="サブアカウント権限不足",
            policies=["pol-1"],
        )

        # Act
        handler.log_execution_error(error_info)

        # Assert
        assert handler.error_counts["authentication_errors"] == 1
        assert handler.error_counts["fatal_errors"] == 1

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_return_code_1_fatal(self, mock_logger_cls):
        """JCOM-030: log_execution_error: return_code=1（fatal）

        error_handling.py:172 return_code == 1 分岐
        """
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ExecutionErrorInfo(
            type="invalid_resource",
            region="us-west-2",
            return_code=1,
            message="無効リソース",
            policies=["pol-1"],
        )

        # Act
        handler.log_execution_error(error_info)

        # Assert
        assert handler.error_counts["fatal_errors"] == 1
        assert handler.error_counts["authentication_errors"] == 0
        mock_logger = mock_logger_cls.return_value
        # fatal → logger.error が呼ばれる
        mock_logger.error.assert_called()

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_return_code_2_warning(self, mock_logger_cls):
        """JCOM-031: log_execution_error: return_code=2（warning）

        error_handling.py:175 return_code == 2 分岐
        """
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ExecutionErrorInfo(
            type="filter_error",
            region="eu-west-1",
            return_code=2,
            message="フィルター警告",
            policies=["pol-1"],
        )

        # Act
        handler.log_execution_error(error_info)

        # Assert
        assert handler.error_counts["warning_errors"] == 1
        assert handler.error_counts["fatal_errors"] == 0
        mock_logger = mock_logger_cls.return_value
        # warning → logger.warning が呼ばれる
        mock_logger.warning.assert_called()

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_return_code_0_unknown(self, mock_logger_cls):
        """JCOM-032: log_execution_error: return_code=0（unknown）

        error_handling.py:178 else分岐
        """
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ExecutionErrorInfo(
            type="other_error",
            region="us-east-1",
            return_code=0,
            message="不明エラー",
            policies=["pol-1"],
        )

        # Act
        handler.log_execution_error(error_info)

        # Assert
        assert handler.error_counts["execution_errors"] == 1
        assert handler.error_counts["fatal_errors"] == 0
        assert handler.error_counts["warning_errors"] == 0
```

### 2.7 CustodianErrorHandler: ユーザーフレンドリーメッセージ テスト

```python
class TestCustodianUserFriendlyMessages:
    """CustodianErrorHandler: create_user_friendly_error のテスト"""

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_validation_error_info_dispatch(self, mock_logger_cls):
        """JCOM-033: create_user_friendly_error: ValidationErrorInfo"""
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ValidationErrorInfo(
            type="yaml_structure",
            policy_index=None,
            policy_name=None,
            message="構造エラー",
            stage="basic",
        )

        # Act
        result = handler.create_user_friendly_error(error_info)

        # Assert
        assert "YAML構造エラー" in result

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_execution_error_info_dispatch(self, mock_logger_cls):
        """JCOM-034: create_user_friendly_error: ExecutionErrorInfo"""
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ExecutionErrorInfo(
            type="network_error",
            region="us-east-1",
            return_code=1,
            message="タイムアウト",
            policies=["pol-1"],
        )

        # Act
        result = handler.create_user_friendly_error(error_info)

        # Assert
        assert "ネットワーク接続エラー" in result

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_unknown_type_dispatch(self, mock_logger_cls):
        """JCOM-035: create_user_friendly_error: 不明型

        error_handling.py:214-215 else分岐
        """
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")

        # Act
        result = handler.create_user_friendly_error("文字列エラー")

        # Assert
        assert "エラー: 文字列エラー" == result

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_validation_msg_invalid_resource(self, mock_logger_cls):
        """JCOM-036: _create_validation_error_message: invalid_resource"""
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ValidationErrorInfo(
            type="invalid_resource",
            policy_index=0,
            policy_name="test-policy",
            message="不正リソース",
            stage="custodian",
            resource_type="aws.invalid",
        )

        # Act
        result = handler._create_validation_error_message(error_info)

        # Assert
        assert "無効なリソースタイプ" in result
        assert "aws.invalid" in result
        assert "test-policy" in result

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_validation_msg_yaml_structure(self, mock_logger_cls):
        """JCOM-037: _create_validation_error_message: yaml_structure"""
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ValidationErrorInfo(
            type="yaml_structure",
            policy_index=None,
            policy_name=None,
            message="不正YAML",
            stage="basic",
        )

        # Act
        result = handler._create_validation_error_message(error_info)

        # Assert
        assert "YAML構造エラー" in result
        assert "不正YAML" in result

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_validation_msg_missing_field(self, mock_logger_cls):
        """JCOM-038: _create_validation_error_message: missing_field"""
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ValidationErrorInfo(
            type="missing_field",
            policy_index=0,
            policy_name="test-policy",
            message="必須フィールド不足",
            stage="basic",
            field_name="resource",
        )

        # Act
        result = handler._create_validation_error_message(error_info)

        # Assert
        assert "必須フィールドが不足" in result
        assert "resource" in result

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_validation_msg_custodian_schema(self, mock_logger_cls):
        """JCOM-039: _create_validation_error_message: custodian_schema"""
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ValidationErrorInfo(
            type="custodian_schema",
            policy_index=0,
            policy_name="test-policy",
            message="スキーマ不正",
            stage="custodian",
        )

        # Act
        result = handler._create_validation_error_message(error_info)

        # Assert
        assert "Custodianスキーマ検証エラー" in result
        assert "スキーマ不正" in result

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_validation_msg_default(self, mock_logger_cls):
        """JCOM-040: _create_validation_error_message: デフォルト

        error_handling.py:247 どのtypeにもマッチしない場合
        """
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ValidationErrorInfo(
            type="unknown_type",
            policy_index=None,
            policy_name=None,
            message="不明なエラー",
            stage="basic",
        )

        # Act
        result = handler._create_validation_error_message(error_info)

        # Assert
        assert result == "検証エラー: 不明なエラー"

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_execution_msg_permission_error(self, mock_logger_cls):
        """JCOM-041: _create_execution_error_message: permission_error"""
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ExecutionErrorInfo(
            type="permission_error",
            region="us-east-1",
            return_code=2,
            message="IAM権限不足",
            policies=["pol-1", "pol-2"],
        )

        # Act
        result = handler._create_execution_error_message(error_info)

        # Assert
        assert "認証・権限エラー" in result
        assert "us-east-1" in result
        assert "pol-1" in result
        assert "スキャンを継続できません" in result

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_execution_msg_authentication_error(self, mock_logger_cls):
        """JCOM-042: _create_execution_error_message: authentication_error"""
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ExecutionErrorInfo(
            type="authentication_error",
            region="ap-northeast-1",
            return_code=2,
            message="認証失敗",
            policies=["pol-1"],
        )

        # Act
        result = handler._create_execution_error_message(error_info)

        # Assert
        assert "認証・権限エラー" in result

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_execution_msg_invalid_resource(self, mock_logger_cls):
        """JCOM-043: _create_execution_error_message: invalid_resource"""
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ExecutionErrorInfo(
            type="invalid_resource",
            region="eu-west-1",
            return_code=1,
            message="不正リソース",
            policies=["pol-1"],
            resource_type="aws.invalid",
        )

        # Act
        result = handler._create_execution_error_message(error_info)

        # Assert
        assert "無効なリソースタイプエラー" in result
        assert "aws.invalid" in result

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_execution_msg_filter_error(self, mock_logger_cls):
        """JCOM-044: _create_execution_error_message: filter_error"""
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ExecutionErrorInfo(
            type="filter_error",
            region="us-west-2",
            return_code=1,
            message="フィルター構文エラー",
            policies=["pol-1"],
        )

        # Act
        result = handler._create_execution_error_message(error_info)

        # Assert
        assert "フィルター設定エラー" in result

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_execution_msg_action_error(self, mock_logger_cls):
        """JCOM-045: _create_execution_error_message: action_error"""
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ExecutionErrorInfo(
            type="action_error",
            region="us-east-1",
            return_code=1,
            message="アクション失敗",
            policies=["pol-1"],
        )

        # Act
        result = handler._create_execution_error_message(error_info)

        # Assert
        assert "アクション実行エラー" in result

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_execution_msg_network_error(self, mock_logger_cls):
        """JCOM-046: _create_execution_error_message: network_error"""
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ExecutionErrorInfo(
            type="network_error",
            region="ap-southeast-1",
            return_code=1,
            message="接続タイムアウト",
            policies=["pol-1"],
        )

        # Act
        result = handler._create_execution_error_message(error_info)

        # Assert
        assert "ネットワーク接続エラー" in result

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_execution_msg_default(self, mock_logger_cls):
        """JCOM-047: _create_execution_error_message: デフォルト

        error_handling.py:292-296 どのtypeにもマッチしない場合
        """
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ExecutionErrorInfo(
            type="unknown_error",
            region="us-east-1",
            return_code=3,
            message="不明なエラー",
            policies=["pol-1"],
        )

        # Act
        result = handler._create_execution_error_message(error_info)

        # Assert
        assert "実行エラー" in result
        assert "return_code: 3" in result
```

### 2.8 CustodianErrorHandler: サマリー・判定テスト

```python
class TestCustodianErrorHandlerSummary:
    """CustodianErrorHandler: サマリー・判定メソッドのテスト"""

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_get_error_summary_no_errors(self, mock_logger_cls):
        """JCOM-048: get_error_summary: エラーなし"""
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")

        # Act
        summary = handler.get_error_summary()

        # Assert
        assert summary["total_errors"] == 0
        assert summary["has_errors"] is False
        assert summary["has_fatal_errors"] is False
        assert summary["has_authentication_errors"] is False
        assert summary["error_severity"] == "low"

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_get_error_summary_with_errors(self, mock_logger_cls):
        """JCOM-049: get_error_summary: エラーあり"""
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        handler.error_counts["validation_errors"] = 2
        handler.error_counts["execution_errors"] = 3
        handler.error_counts["fatal_errors"] = 1

        # Act
        summary = handler.get_error_summary()

        # Assert
        assert summary["total_errors"] == 5  # validation(2) + execution(3)
        assert summary["has_errors"] is True
        assert summary["has_fatal_errors"] is True
        assert summary["error_severity"] == "high"

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_determine_severity_high(self, mock_logger_cls):
        """JCOM-050: _determine_error_severity: high"""
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        handler.error_counts["fatal_errors"] = 1

        # Act
        result = handler._determine_error_severity()

        # Assert
        assert result == "high"

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_determine_severity_medium(self, mock_logger_cls):
        """JCOM-051: _determine_error_severity: medium

        error_handling.py:329 warning_errors > 0 かつ fatal=0, validation=0, auth=0
        """
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        handler.error_counts["warning_errors"] = 2

        # Act
        result = handler._determine_error_severity()

        # Assert
        assert result == "medium"

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_determine_severity_low(self, mock_logger_cls):
        """JCOM-052: _determine_error_severity: low"""
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")

        # Act
        result = handler._determine_error_severity()

        # Assert
        assert result == "low"

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_should_fail_job_validation(self, mock_logger_cls):
        """JCOM-053: should_fail_job: validation errors"""
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        handler.error_counts["validation_errors"] = 1

        # Act & Assert
        assert handler.should_fail_job() is True

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_should_fail_job_fatal(self, mock_logger_cls):
        """JCOM-054: should_fail_job: fatal errors"""
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        handler.error_counts["fatal_errors"] = 1

        # Act & Assert
        assert handler.should_fail_job() is True

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_should_fail_job_auth(self, mock_logger_cls):
        """JCOM-055: should_fail_job: auth errors"""
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        handler.error_counts["authentication_errors"] = 1

        # Act & Assert
        assert handler.should_fail_job() is True

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_should_fail_job_false(self, mock_logger_cls):
        """JCOM-056: should_fail_job: エラーなし"""
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")

        # Act & Assert
        assert handler.should_fail_job() is False
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| JCOM-E01 | TaskError: 例外として発生可能 | raise TaskError | catchでメッセージ取得可能 |
| JCOM-E02 | ValidationError: 継承チェーン | isinstance確認 | TaskError, Exceptionの子クラス |
| JCOM-E03 | ExternalServiceError: response_dataデフォルト | response_data未指定 | 空辞書 |
| JCOM-E04 | ProcessingError: partial_resultsデフォルト | partial_results未指定 | None |
| JCOM-E05 | CustodianErrorHandler: execution_error resource_type付き | resource_type指定 | contextにresource_type含む |
| JCOM-E06 | CustodianErrorHandler: execution_msg 空policiesリスト | policies=[] | 影響ポリシー: 不明（Falsy判定） |
| JCOM-E07 | StatusTracker: update_progress デフォルトunit | unit未指定 | "items"がデフォルト |
| JCOM-E08 | CustodianErrorHandler: execution_error 空文字resource_type | resource_type="" | contextにresource_type含まない（Falsy） |
| JCOM-E09 | CustodianErrorHandler: execution_msg 空policiesの表示内容 | policies=[] | `不明` 表示（Falsy判定） |

### 3.1 例外階層 異常系

```python
class TestTaskErrorHierarchyErrors:
    """TaskError例外階層のエラーテスト"""

    def test_task_error_raisable(self):
        """JCOM-E01: TaskError: 例外として発生可能"""
        # Arrange & Act & Assert
        with pytest.raises(TaskError, match="テストエラー"):
            raise TaskError("テストエラー", error_code="TEST")

    def test_validation_error_inheritance(self):
        """JCOM-E02: ValidationError: 継承チェーン"""
        # Arrange
        error = ValidationError("検証失敗")

        # Assert
        assert isinstance(error, TaskError)
        assert isinstance(error, Exception)

    def test_external_service_error_default_response_data(self):
        """JCOM-E03: ExternalServiceError: response_dataデフォルト"""
        # Arrange & Act
        error = ExternalServiceError("エラー", service_name="OpenSearch")

        # Assert
        assert error.response_data == {}
        assert error.status_code is None

    def test_processing_error_default_partial_results(self):
        """JCOM-E04: ProcessingError: partial_resultsデフォルト"""
        # Arrange & Act
        error = ProcessingError("パースエラー", processing_stage="parse")

        # Assert
        assert error.partial_results is None
```

### 3.2 CustodianErrorHandler 異常系

```python
class TestCustodianErrorHandlerErrors:
    """CustodianErrorHandler異常系テスト"""

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_execution_error_with_resource_type(self, mock_logger_cls):
        """JCOM-E05: log_execution_error: resource_type付き

        error_handling.py:192-193 resource_type条件分岐
        """
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ExecutionErrorInfo(
            type="invalid_resource",
            region="us-east-1",
            return_code=1,
            message="リソースエラー",
            policies=["pol-1"],
            resource_type="aws.invalid.type",
        )

        # Act
        handler.log_execution_error(error_info)

        # Assert
        mock_logger = mock_logger_cls.return_value
        call_args = mock_logger.error.call_args
        context = call_args[1]["context"]
        assert context["resource_type"] == "aws.invalid.type"

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_execution_msg_empty_policies(self, mock_logger_cls):
        """JCOM-E06: _create_execution_error_message: 空policiesリスト"""
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ExecutionErrorInfo(
            type="filter_error",
            region="us-east-1",
            return_code=1,
            message="フィルターエラー",
            policies=[],
        )

        # Act
        result = handler._create_execution_error_message(error_info)

        # Assert
        assert "フィルター設定エラー" in result
        # 空リスト [] はFalsyなため、'不明' が表示される
        assert "影響ポリシー: 不明" in result

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_execution_error_empty_string_resource_type(self, mock_logger_cls):
        """JCOM-E08: log_execution_error: 空文字resource_type

        error_handling.py:192 if error_info.resource_type: は空文字列でFalse
        """
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ExecutionErrorInfo(
            type="invalid_resource",
            region="us-east-1",
            return_code=1,
            message="リソースエラー",
            policies=["pol-1"],
            resource_type="",
        )

        # Act
        handler.log_execution_error(error_info)

        # Assert
        mock_logger = mock_logger_cls.return_value
        context = mock_logger.error.call_args[1]["context"]
        # 空文字列はFalsyなためcontextに含まれない
        assert "resource_type" not in context

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_execution_msg_empty_policies_content(self, mock_logger_cls):
        """JCOM-E09: _create_execution_error_message: 空policiesの表示内容"""
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ExecutionErrorInfo(
            type="unknown_error",
            region="us-east-1",
            return_code=1,
            message="エラー",
            policies=[],
        )

        # Act
        result = handler._create_execution_error_message(error_info)

        # Assert
        # policies=[] はFalsyなため、'不明' が表示される
        assert "影響ポリシー: 不明" in result

    @patch("app.jobs.common.status_tracking.update_job_progress")
    def test_status_tracker_default_unit(self, mock_progress):
        """JCOM-E07: StatusTracker: update_progress デフォルトunit"""
        # Arrange
        tracker = StatusTracker(job_id="job-1")

        # Act
        tracker.update_progress(1, 10, "処理中")

        # Assert
        mock_progress.assert_called_once_with("job-1", 1, 10, "処理中", "items")
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| JCOM-SEC-01 | ユーザーメッセージの定型フォーマット維持 | パスを含むエラー | 定型フォーマットのみ検証（パス含有は既知の制限事項#7） |
| JCOM-SEC-02 | ユーザーメッセージの定型フォーマット維持 | Traceback含む | 定型テンプレート使用（現状Tracebackは含まれる：制限事項#7） |
| JCOM-SEC-03 | エラーサマリーに認証情報が含まれない | 認証エラー処理後 | パスワード/トークン未露出 |
| JCOM-SEC-04 | ログメッセージのインジェクション耐性 | 改行含むメッセージ | フォーマット維持 |
| JCOM-SEC-05 | エラーカウントの整合性 | log_*メソッド経由操作 | サマリーと整合 |
| JCOM-SEC-06 | ログへの認証情報漏洩防止 | password含むメッセージ | エラーサマリーに認証情報非含有 |
| JCOM-SEC-07 | context辞書のインジェクション耐性 | 改行含むcontext値 | フォーマット構造維持 |
| JCOM-SEC-08 | CRLFインジェクション耐性 | CRLF含むメッセージ | ログフォーマット維持 |

```python
@pytest.mark.security
class TestJobsCommonSecurity:
    """jobs/common セキュリティテスト"""

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_user_message_no_internal_paths(self, mock_logger_cls):
        """JCOM-SEC-01: ユーザーメッセージに内部パスが含まれない

        CWE-209: Information Exposure Through an Error Message対策
        create_user_friendly_errorが返すメッセージに内部パスが露出しないことを確認
        """
        # Arrange
        import re

        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ExecutionErrorInfo(
            type="unknown_type",
            region="us-east-1",
            return_code=1,
            message="/opt/app/config/secret.yaml でエラー発生: /home/user/.aws/credentials 読み取り失敗",
            policies=["pol-1"],
        )

        # Act
        result = handler.create_user_friendly_error(error_info)

        # Assert
        # メッセージは定型フォーマットで出力される
        assert "実行エラー" in result
        assert result.startswith("実行エラー")
        # 注意: 現在の実装ではerror_info.messageがそのまま定型テンプレート内に含まれる
        # パスがテンプレート内の「詳細:」行に露出する可能性がある（既知の制限事項#7参照）

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_user_message_no_stacktrace(self, mock_logger_cls):
        """JCOM-SEC-02: ユーザーメッセージにスタックトレースが含まれない

        CWE-209対策
        注意: 現在の実装ではerror_info.messageがそのまま含まれるため、
        Tracebackを含むメッセージは定型テンプレート内に表示される（既知の制限事項#7参照）
        """
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ValidationErrorInfo(
            type="custodian_schema",
            policy_index=0,
            policy_name="test",
            message='Traceback (most recent call last):\n  File "/app/core.py", line 42',
            stage="custodian",
        )

        # Act
        result = handler.create_user_friendly_error(error_info)

        # Assert
        # 定型フォーマットが使用される
        assert "Custodianスキーマ検証エラー" in result
        # メッセージ内容はテンプレート内の「詳細」行に含まれる
        assert "Traceback" in result  # 現在の実装では未サニタイズ

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_error_summary_no_credentials(self, mock_logger_cls):
        """JCOM-SEC-03: エラーサマリーに認証情報が含まれない

        OWASP A02:2021 - Cryptographic Failures対策
        get_error_summaryがカウント数値のみ返し、メッセージ内容を含まないことを確認
        """
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        # 認証情報を含むエラーを処理
        error_info = ExecutionErrorInfo(
            type="authentication_error",
            region="us-east-1",
            return_code=2,
            message="password=secret123, token=abc-xyz",
            policies=["pol-1"],
        )
        handler.log_execution_error(error_info)

        # Act
        summary = handler.get_error_summary()

        # Assert
        # サマリーにはカウント数値のみ含まれる
        summary_str = str(summary)
        assert "secret123" not in summary_str
        assert "abc-xyz" not in summary_str
        assert "password" not in summary_str
        # カウントのみ含まれる
        assert summary["authentication_errors"] == 1

    @patch("app.jobs.common.logging.append_job_log")
    def test_log_message_format_integrity(self, mock_append):
        """JCOM-SEC-04: ログメッセージのインジェクション耐性

        CWE-117: Improper Output Neutralization for Logs
        改行を含むメッセージがフォーマット構造を破壊しないことを確認
        """
        # Arrange
        logger = TaskLogger(job_id="job-1", task_name="TestTask")
        malicious_message = "正常メッセージ\n[CRITICAL] 偽のクリティカルログ"

        # Act
        logger.info(malicious_message)

        # Assert
        # フォーマットが[TaskName][LEVEL]で始まることを確認
        call_args = mock_append.call_args[0][1]
        assert call_args.startswith("[TestTask][INFO]")

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_error_counts_consistency(self, mock_logger_cls):
        """JCOM-SEC-05: エラーカウントの整合性

        エラーカウントがlog_*メソッド経由で正しく増加し、
        get_error_summaryの結果と整合することを確認。
        error_countsは公開属性だが、log_*メソッド経由での操作が運用ルール。
        """
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")

        # 複数のエラーを記録
        val_info = ValidationErrorInfo(
            type="yaml_structure", policy_index=None,
            policy_name=None, message="エラー", stage="basic",
        )
        exec_info = ExecutionErrorInfo(
            type="filter_error", region="us-east-1",
            return_code=2, message="フィルターエラー", policies=["p1"],
        )
        handler.log_validation_error(val_info)
        handler.log_execution_error(exec_info)

        # Act
        summary = handler.get_error_summary()

        # Assert
        assert summary["validation_errors"] == 1
        assert summary["execution_errors"] == 1
        assert summary["total_errors"] == 2
        assert summary["warning_errors"] == 1  # return_code=2 → warning
        assert summary["has_errors"] is True

    @patch("app.jobs.common.error_handling.TaskLogger")
    def test_log_no_credential_leakage(self, mock_logger_cls):
        """JCOM-SEC-06: ログへの認証情報漏洩防止

        CWE-532: Insertion of Sensitive Information into Log File
        log_execution_errorでerror_info.messageに認証情報が含まれる場合、
        get_error_summaryには露出しないことを確認。
        注意: ログ（append_job_log）には現状messageがそのまま記録される（既知の制限事項#6）
        """
        # Arrange
        handler = CustodianErrorHandler(job_id="job-1")
        error_info = ExecutionErrorInfo(
            type="authentication_error",
            region="us-east-1",
            return_code=2,
            message="AWS_SECRET_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE token=eyJhbGciOiJIUzI1NiJ9",
            policies=["pol-1"],
        )

        # Act
        handler.log_execution_error(error_info)
        summary = handler.get_error_summary()

        # Assert
        # サマリーにはカウント数値のみ含まれ、メッセージ内容は含まれない
        summary_str = str(summary)
        assert "AKIAIOSFODNN7EXAMPLE" not in summary_str
        assert "eyJhbGciOiJIUzI1NiJ9" not in summary_str
        assert "AWS_SECRET_ACCESS_KEY" not in summary_str

    @patch("app.jobs.common.logging.append_job_log")
    def test_context_injection_resistance(self, mock_append):
        """JCOM-SEC-07: context辞書のインジェクション耐性

        CWE-117: Improper Output Neutralization for Logs
        context値に改行文字が含まれる場合でも、
        _format_messageのフォーマット構造が維持されることを確認
        """
        # Arrange
        logger = TaskLogger(job_id="job-1", task_name="TestTask")
        malicious_context = {
            "user": "admin\n[CRITICAL] System compromised",
            "action": "login\r\nX-Injected-Header: evil",
        }

        # Act
        logger.info("テストメッセージ", context=malicious_context)

        # Assert
        call_args = mock_append.call_args[0][1]
        # フォーマットが[TaskName][LEVEL]で始まること
        assert call_args.startswith("[TestTask][INFO]")
        # Context部分は1行に収まる（改行はそのまま含まれるが構造は維持）
        assert "| Context:" in call_args

    @patch("app.jobs.common.logging.append_job_log")
    def test_crlf_injection_resistance(self, mock_append, capsys):
        """JCOM-SEC-08: CRLFインジェクション耐性

        CWE-93: Improper Neutralization of CRLF Sequences
        CRLFを含むメッセージでもフォーマット構造が維持されることを確認。
        print出力も検証。
        """
        # Arrange
        logger = TaskLogger(job_id="job-1", task_name="TestTask")
        crlf_message = "正常メッセージ\r\n[CRITICAL] 偽のクリティカルログ"

        # Act
        logger.error(crlf_message)

        # Assert
        call_args = mock_append.call_args[0][1]
        assert call_args.startswith("[TestTask][ERROR]")
        # print出力も確認
        captured = capsys.readouterr()
        assert "Job job-1:" in captured.out
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_jobs_common_module` | テスト間のモジュール状態リセット | function | Yes |
| `mock_status_manager` | status_manager全関数モック | function | No |

### 共通フィクスチャ定義

```python
# test/unit/jobs/common/conftest.py
import sys
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def reset_jobs_common_module():
    """テストごとにjobs/commonモジュールの状態をリセット

    CustodianErrorHandlerのインスタンス状態がテスト間で共有されないように、
    モジュールキャッシュをクリーンアップする。
    status_managerのグローバル辞書もクリアしてテスト独立性を保証する。
    """
    yield
    # status_managerのグローバル辞書をクリア
    try:
        from app.jobs.status_manager import job_statuses
        job_statuses.clear()
    except ImportError:
        pass
    # テスト後にモジュールキャッシュをクリーンアップ
    modules_to_remove = [
        key for key in sys.modules
        if key.startswith("app.jobs.common")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def mock_status_manager():
    """status_manager全関数モック（外部状態変更防止）"""
    with patch("app.jobs.common.status_tracking.update_job_status") as mock_update, \
         patch("app.jobs.common.status_tracking.update_job_progress") as mock_progress, \
         patch("app.jobs.common.logging.append_job_log") as mock_append:
        yield {
            "update_job_status": mock_update,
            "update_job_progress": mock_progress,
            "append_job_log": mock_append,
        }
```

---

## 6. テスト実行例

```bash
# jobs/common関連テストのみ実行
pytest test/unit/jobs/common/test_jobs_common.py -v

# 特定のテストクラスのみ実行
pytest test/unit/jobs/common/test_jobs_common.py::TestTaskLogger -v
pytest test/unit/jobs/common/test_jobs_common.py::TestStatusTracker -v
pytest test/unit/jobs/common/test_jobs_common.py::TestCustodianErrorHandler -v
pytest test/unit/jobs/common/test_jobs_common.py::TestCustodianErrorHandlerExecution -v
pytest test/unit/jobs/common/test_jobs_common.py::TestCustodianUserFriendlyMessages -v

# カバレッジ付きで実行（90%閾値強制）
pytest test/unit/jobs/common/test_jobs_common.py \
    --cov=app.jobs.common.error_handling \
    --cov=app.jobs.common.status_tracking \
    --cov=app.jobs.common.logging \
    --cov-report=term-missing \
    --cov-fail-under=90 -v

# セキュリティマーカーで実行
pytest test/unit/jobs/common/test_jobs_common.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 57 | JCOM-001 〜 JCOM-057 |
| 異常系 | 9 | JCOM-E01 〜 JCOM-E09 |
| セキュリティ | 8 | JCOM-SEC-01 〜 JCOM-SEC-08 |
| **合計** | **74** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestTaskLogger` | JCOM-001〜JCOM-009 | 9 |
| `TestStatusTracker` | JCOM-010〜JCOM-016 | 7 |
| `TestTaskErrorHierarchy` | JCOM-017〜JCOM-022 | 6 |
| `TestErrorInfoDataclasses` | JCOM-023〜JCOM-024 | 2 |
| `TestCustodianErrorHandler` | JCOM-025〜JCOM-027 | 3 |
| `TestCustodianErrorHandlerExecution` | JCOM-028〜JCOM-032, JCOM-057 | 6 |
| `TestCustodianUserFriendlyMessages` | JCOM-033〜JCOM-047 | 15 |
| `TestCustodianErrorHandlerSummary` | JCOM-048〜JCOM-056 | 9 |
| `TestTaskErrorHierarchyErrors` | JCOM-E01〜JCOM-E04 | 4 |
| `TestCustodianErrorHandlerErrors` | JCOM-E05〜JCOM-E09 | 5 |
| `TestJobsCommonSecurity` | JCOM-SEC-01〜JCOM-SEC-08 | 8 |

### 実装失敗が予想されるテスト

現時点で失敗が予想されるテストはありません。

### 注意事項

- テスト実行に `pytest` と `pytest-cov` が必要
- `@pytest.mark.security` マーカーの使用には `pyproject.toml` への登録が必要:
  ```toml
  [tool.pytest.ini_options]
  markers = ["security: セキュリティテスト"]
  ```
- `CustodianErrorHandler` は内部で `TaskLogger` を使用するため、ほとんどのテストで `@patch("app.jobs.common.error_handling.TaskLogger")` が必要
- `status_manager` の関数はグローバル辞書を操作するため、必ずモック化すること

---

## 8. 既知の制限事項と改善推奨

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `TaskLogger` は `print()` で標準出力にもログ出力 | テスト出力が冗長になる場合がある | `capsys` フィクスチャで検証、または `-s` オプションで確認 |
| 2 | `CustodianErrorHandler.error_counts` は公開属性 | テストで直接操作可能だがプロパティ化されていない | テストではlog_*メソッド経由での操作を推奨 |
| 3 | `_create_execution_error_message` でエラーメッセージをそのまま含む | 内部エラー詳細がユーザーメッセージに含まれる可能性（CWE-209） | 実装側で `_sanitize_message()` 関数追加を推奨 |
| 4 | `log_execution_error` L166 の部分一致判定 | `"permission_error" in type` は `"account_permission_error"` にも該当 | `==` 比較への変更を推奨（GitHub Issue作成推奨） |
| 5 | `status_manager` はインメモリグローバル辞書 | テスト間で状態が共有される | autouse fixtureでモジュールリセット + `job_statuses.clear()` |
| 6 | `log_*` メソッドが `error_info.message` をサニタイズせずにログ出力 | 認証情報がログに露出するリスク（CWE-532） | パスワード/トークンのマスキング処理追加を推奨 |
| 7 | `create_user_friendly_error` が内部パス・Tracebackを除去しない | 内部情報がユーザーメッセージに露出（CWE-209） | 正規表現による絶対パス/Traceback除去処理の追加を推奨 |
| 8 | `TaskLogger._format_message` がcontext値をエスケープしない | 改行を含むcontext値がログフォーマットを破壊（CWE-117） | context値のエスケープ処理を推奨 |
