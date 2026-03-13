# jobs/tasks/base_task テストケース

## 1. 概要

`app/jobs/tasks/base_task.py` は、全ジョブタスクの基底クラス `BaseTask` を定義します。テンプレートメソッドパターンにより、タスクの実行フロー（開始→実行→成功/エラー処理）を統一し、ログ出力・ステータス管理の共通処理を提供します。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `BaseTask.__init__` | job_id設定とUTC開始時刻の記録 |
| `BaseTask.execute` | テンプレートメソッド：_execute_task → _handle_success / _handle_error |
| `BaseTask._execute_task` | 抽象メソッド（サブクラスで実装必須） |
| `BaseTask._handle_success` | 成功時のジョブ完了処理（main_payload分岐あり） |
| `BaseTask._handle_error` | エラー時のジョブ失敗処理（エラーサマリー生成） |
| `BaseTask.log_info` | 情報ログ（append_job_log + print） |
| `BaseTask.log_error` | エラーログ（append_job_logのみ） |
| `BaseTask.log_warning` | 警告ログ（append_job_logのみ） |
| `BaseTask.log_debug` | デバッグログ（append_job_logのみ） |

### 1.2 カバレッジ目標: 95%

> **注記**: 基底クラスとして全タスクが依存する基盤。分岐数が少なく網羅しやすいため高カバレッジを目標とする。抽象メソッド `_execute_task` のbodyは除外。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/jobs/tasks/base_task.py` |
| テストコード | `test/unit/jobs/tasks/test_base_task.py` |

### 1.4 補足情報

#### 依存関係（モック対象）

```
base_task.py ──→ status_manager.update_job_status
             ──→ status_manager.set_job_completed
             ──→ status_manager.set_job_failed
             ──→ status_manager.append_job_log
```

#### 主要分岐

| メソッド | 行 | 条件 | 結果 |
|---------|-----|------|------|
| `_handle_success` | L51 | `isinstance(result, dict) and "main_payload" in result` | set_job_completed(message, main_payload, summary_data) |
| `_handle_success` | L58-62 | else | set_job_completed(completion_message, summary_data={"result": result} or None) |
| `_handle_success` | L62 | `result is not None` | summary_data={"result": result} |
| `_handle_success` | L62 | `result is None` | summary_data=None |
| `execute` | L24-31 | try成功 | _handle_success呼び出し |
| `execute` | L34-36 | except | _handle_error呼び出し |

#### テスト用具象サブクラス

BaseTaskは抽象クラスのため、テスト用の具象サブクラスを使用する:

```python
class ConcreteTask(BaseTask):
    """テスト用の具象タスクサブクラス"""
    def __init__(self, job_id: str, return_value=None, raise_error=None):
        super().__init__(job_id)
        self._return_value = return_value
        self._raise_error = raise_error

    async def _execute_task(self, **kwargs) -> Any:
        if self._raise_error:
            raise self._raise_error
        return self._return_value
```

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| JBTASK-001 | BaseTask: 初期化 | job_id="job-1" | job_id設定、start_time記録 |
| JBTASK-002 | execute: 成功フロー | _execute_task正常 | update_job_status→_execute_task→_handle_success |
| JBTASK-003 | execute: エラーフロー | _execute_taskが例外 | _handle_error呼び出し |
| JBTASK-004 | _handle_success: main_payload付きdict | {"main_payload": [...]} | set_job_completed(message, main_payload, summary_data) |
| JBTASK-005 | _handle_success: main_payloadなしdict | {"key": "value"} | set_job_completed(completion_message, summary_data={"result": dict}) |
| JBTASK-006 | _handle_success: None結果 | None | set_job_completed(completion_message, summary_data=None) |
| JBTASK-007 | _handle_success: 文字列結果 | "done" | set_job_completed(completion_message, summary_data={"result": "done"}) |
| JBTASK-008 | _handle_success: message上書き | result["message"]指定 | result["message"]が使用される |
| JBTASK-009 | _handle_error: エラーサマリー生成 | ValueError("test") | set_job_failedにerror_summary付き |
| JBTASK-010 | log_info: 出力 | message="情報" | append_job_log + print |
| JBTASK-011 | log_error: 出力 | message="エラー" | append_job_logのみ |
| JBTASK-012 | log_warning: 出力 | message="警告" | append_job_logのみ |
| JBTASK-013 | log_debug: 出力 | message="デバッグ" | append_job_logのみ |
| JBTASK-014 | _handle_success: 実行時間計算 | 正常完了 | 実行時間が含まれる |
| JBTASK-015 | _handle_error: 実行時間計算 | エラー発生 | 実行時間がエラーメッセージに含まれる |

### 2.1 初期化テスト

```python
# test/unit/jobs/tasks/test_base_task.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Any
from datetime import datetime, timezone

from app.jobs.tasks.base_task import BaseTask


class ConcreteTask(BaseTask):
    """テスト用の具象タスクサブクラス"""

    def __init__(self, job_id: str, return_value=None, raise_error=None):
        super().__init__(job_id)
        self._return_value = return_value
        self._raise_error = raise_error

    async def _execute_task(self, **kwargs) -> Any:
        if self._raise_error:
            raise self._raise_error
        return self._return_value


class TestBaseTaskInit:
    """BaseTask初期化のテスト"""

    @patch("app.jobs.tasks.base_task.append_job_log")
    @patch("app.jobs.tasks.base_task.update_job_status")
    def test_init(self, mock_update, mock_append):
        """JBTASK-001: BaseTask: 初期化"""
        # Arrange & Act
        task = ConcreteTask(job_id="job-1")

        # Assert
        assert task.job_id == "job-1"
        assert isinstance(task.start_time, datetime)
        assert task.start_time.tzinfo == timezone.utc
```

### 2.2 executeテンプレートメソッドテスト

```python
class TestBaseTaskExecute:
    """BaseTask.executeメソッドのテスト"""

    @patch("app.jobs.tasks.base_task.set_job_completed")
    @patch("app.jobs.tasks.base_task.append_job_log")
    @patch("app.jobs.tasks.base_task.update_job_status")
    @pytest.mark.asyncio
    async def test_execute_success_flow(self, mock_update, mock_append, mock_completed):
        """JBTASK-002: execute: 成功フロー

        base_task.py:24-32 try成功パスをカバー
        """
        # Arrange
        task = ConcreteTask(job_id="job-1", return_value={"key": "value"})

        # Act
        await task.execute()

        # Assert
        # update_job_statusが"running"で呼ばれる
        mock_update.assert_called_once()
        args = mock_update.call_args[0]
        assert args[0] == "job-1"
        assert args[1] == "running"
        # log_info("タスク開始: ...")がappend_job_logで記録される
        first_log = mock_append.call_args_list[0][0][1]
        assert "タスク開始: ConcreteTask" in first_log
        # set_job_completedが呼ばれる
        mock_completed.assert_called_once()

    @patch("app.jobs.tasks.base_task.set_job_failed")
    @patch("app.jobs.tasks.base_task.append_job_log")
    @patch("app.jobs.tasks.base_task.update_job_status")
    @pytest.mark.asyncio
    async def test_execute_error_flow(self, mock_update, mock_append, mock_failed):
        """JBTASK-003: execute: エラーフロー

        base_task.py:34-36 except分岐をカバー
        """
        # Arrange
        task = ConcreteTask(
            job_id="job-1",
            raise_error=ValueError("テストエラー")
        )

        # Act
        await task.execute()

        # Assert
        # エラーパスでもupdate_job_statusが最初に呼ばれる（L26）
        mock_update.assert_called_once()
        assert mock_update.call_args[0][1] == "running"
        # set_job_failedが呼ばれる
        mock_failed.assert_called_once()
        call_args = mock_failed.call_args
        assert call_args[0][0] == "job-1"
        assert "テストエラー" in call_args[0][1]
```

### 2.3 _handle_success分岐テスト

```python
class TestBaseTaskHandleSuccess:
    """BaseTask._handle_successの分岐テスト"""

    @patch("app.jobs.tasks.base_task.set_job_completed")
    @patch("app.jobs.tasks.base_task.append_job_log")
    @patch("app.jobs.tasks.base_task.update_job_status")
    @pytest.mark.asyncio
    async def test_handle_success_with_main_payload(
        self, mock_update, mock_append, mock_completed
    ):
        """JBTASK-004: _handle_success: main_payload付きdict

        base_task.py:51-57 isinstance(result, dict) and "main_payload" in result == True
        """
        # Arrange
        task = ConcreteTask(job_id="job-1")
        result = {
            "main_payload": [{"item": 1}],
            "message": "処理完了",
            "summary_data": {"count": 1}
        }

        # Act
        await task._handle_success(result)

        # Assert
        mock_completed.assert_called_once_with(
            "job-1",
            final_message="処理完了",
            main_payload_result=[{"item": 1}],
            summary_data={"count": 1}
        )

    @patch("app.jobs.tasks.base_task.set_job_completed")
    @patch("app.jobs.tasks.base_task.append_job_log")
    @patch("app.jobs.tasks.base_task.update_job_status")
    @pytest.mark.asyncio
    async def test_handle_success_dict_without_main_payload(
        self, mock_update, mock_append, mock_completed
    ):
        """JBTASK-005: _handle_success: main_payloadなしdict

        base_task.py:51のif条件False（dictだがmain_payloadキーなし）
        + L62の三項演算子 result is not None → True → summary_data付き
        """
        # Arrange
        task = ConcreteTask(job_id="job-1")
        result = {"key": "value"}

        # Act
        await task._handle_success(result)

        # Assert
        mock_completed.assert_called_once()
        call_kwargs = mock_completed.call_args[1]
        assert call_kwargs["summary_data"] == {"result": {"key": "value"}}

    @patch("app.jobs.tasks.base_task.set_job_completed")
    @patch("app.jobs.tasks.base_task.append_job_log")
    @patch("app.jobs.tasks.base_task.update_job_status")
    @pytest.mark.asyncio
    async def test_handle_success_none_result(
        self, mock_update, mock_append, mock_completed
    ):
        """JBTASK-006: _handle_success: None結果

        base_task.py:62 result is None → summary_data=None
        """
        # Arrange
        task = ConcreteTask(job_id="job-1")

        # Act
        await task._handle_success(None)

        # Assert
        mock_completed.assert_called_once()
        call_kwargs = mock_completed.call_args[1]
        assert call_kwargs["summary_data"] is None

    @patch("app.jobs.tasks.base_task.set_job_completed")
    @patch("app.jobs.tasks.base_task.append_job_log")
    @patch("app.jobs.tasks.base_task.update_job_status")
    @pytest.mark.asyncio
    async def test_handle_success_string_result(
        self, mock_update, mock_append, mock_completed
    ):
        """JBTASK-007: _handle_success: 文字列結果

        base_task.py:58-62 else分岐（非dictだがnot None）
        """
        # Arrange
        task = ConcreteTask(job_id="job-1")

        # Act
        await task._handle_success("done")

        # Assert
        mock_completed.assert_called_once()
        call_kwargs = mock_completed.call_args[1]
        assert call_kwargs["summary_data"] == {"result": "done"}

    @patch("app.jobs.tasks.base_task.set_job_completed")
    @patch("app.jobs.tasks.base_task.append_job_log")
    @patch("app.jobs.tasks.base_task.update_job_status")
    @pytest.mark.asyncio
    async def test_handle_success_message_override(
        self, mock_update, mock_append, mock_completed
    ):
        """JBTASK-008: _handle_success: message上書き

        base_task.py:54 result.get("message", completion_message)で
        resultにmessageが指定されている場合はそれが使われる
        """
        # Arrange
        task = ConcreteTask(job_id="job-1")
        result = {
            "main_payload": [1, 2, 3],
            "message": "カスタムメッセージ",
        }

        # Act
        await task._handle_success(result)

        # Assert
        mock_completed.assert_called_once()
        call_kwargs = mock_completed.call_args[1]
        assert call_kwargs["final_message"] == "カスタムメッセージ"

    @patch("app.jobs.tasks.base_task.set_job_completed")
    @patch("app.jobs.tasks.base_task.append_job_log")
    @patch("app.jobs.tasks.base_task.update_job_status")
    @pytest.mark.asyncio
    async def test_handle_success_duration_in_message(
        self, mock_update, mock_append, mock_completed
    ):
        """JBTASK-014: _handle_success: 実行時間計算

        base_task.py:45-46 duration計算が完了メッセージに含まれる
        """
        # Arrange
        task = ConcreteTask(job_id="job-1")

        # Act
        await task._handle_success("result")

        # Assert
        mock_completed.assert_called_once()
        call_kwargs = mock_completed.call_args[1]
        # 完了メッセージに実行時間が含まれる
        assert "実行時間:" in call_kwargs["final_message"]
        assert "秒" in call_kwargs["final_message"]
```

### 2.4 _handle_errorテスト

```python
class TestBaseTaskHandleError:
    """BaseTask._handle_errorのテスト"""

    @patch("app.jobs.tasks.base_task.set_job_failed")
    @patch("app.jobs.tasks.base_task.append_job_log")
    @patch("app.jobs.tasks.base_task.update_job_status")
    @pytest.mark.asyncio
    async def test_handle_error_creates_summary(
        self, mock_update, mock_append, mock_failed, capsys
    ):
        """JBTASK-009: _handle_error: エラーサマリー生成

        base_task.py:65-83 エラーサマリーデータ生成と set_job_failed呼び出し
        """
        # Arrange
        task = ConcreteTask(job_id="job-1")
        error = ValueError("テストエラー")

        # Act
        await task._handle_error(error)

        # Assert
        mock_failed.assert_called_once()
        call_args = mock_failed.call_args
        assert call_args[0][0] == "job-1"
        # エラーメッセージにクラス名と実行時間が含まれる
        assert "ConcreteTask" in call_args[0][1]
        assert "テストエラー" in call_args[0][1]
        assert "実行時間:" in call_args[0][1]
        # summary_dataにエラー情報が含まれる
        summary = call_args[1]["summary_data"]
        assert summary["error_type"] == "ValueError"
        assert summary["error_message"] == "テストエラー"
        assert summary["task_class"] == "ConcreteTask"
        assert "execution_duration_seconds" in summary
        assert "failed_at" in summary
        # print出力の確認（L71: print(f"Job {self.job_id}: {error_message}")）
        captured = capsys.readouterr()
        assert "Job job-1:" in captured.out
        assert "テストエラー" in captured.out

    @patch("app.jobs.tasks.base_task.set_job_failed")
    @patch("app.jobs.tasks.base_task.append_job_log")
    @patch("app.jobs.tasks.base_task.update_job_status")
    @pytest.mark.asyncio
    async def test_handle_error_duration_calculation(
        self, mock_update, mock_append, mock_failed
    ):
        """JBTASK-015: _handle_error: 実行時間計算

        base_task.py:67 duration計算がエラーメッセージに含まれる
        """
        # Arrange
        task = ConcreteTask(job_id="job-1")
        error = RuntimeError("タイムアウト")

        # Act
        await task._handle_error(error)

        # Assert
        error_msg = mock_failed.call_args[0][1]
        assert "実行時間:" in error_msg
        assert "秒" in error_msg
```

### 2.5 ログメソッドテスト

```python
class TestBaseTaskLogging:
    """BaseTaskログメソッドのテスト"""

    @patch("app.jobs.tasks.base_task.append_job_log")
    def test_log_info(self, mock_append, capsys):
        """JBTASK-010: log_info: 出力

        base_task.py:85-89 append_job_log + print
        """
        # Arrange
        task = ConcreteTask(job_id="job-1")

        # Act
        task.log_info("情報メッセージ")

        # Assert
        mock_append.assert_called_once()
        log_msg = mock_append.call_args[0][1]
        assert "[ConcreteTask][INFO] 情報メッセージ" == log_msg
        assert mock_append.call_args[0][0] == "job-1"
        # printも呼ばれる
        captured = capsys.readouterr()
        assert "Job job-1:" in captured.out
        assert "[ConcreteTask][INFO] 情報メッセージ" in captured.out

    @patch("app.jobs.tasks.base_task.append_job_log")
    def test_log_error(self, mock_append, capsys):
        """JBTASK-011: log_error: 出力

        base_task.py:91-94 append_job_logのみ（printなし）
        """
        # Arrange
        task = ConcreteTask(job_id="job-1")

        # Act
        task.log_error("エラーメッセージ")

        # Assert
        mock_append.assert_called_once()
        log_msg = mock_append.call_args[0][1]
        assert "[ConcreteTask][ERROR] エラーメッセージ" == log_msg
        # printは呼ばれない
        captured = capsys.readouterr()
        assert captured.out == ""

    @patch("app.jobs.tasks.base_task.append_job_log")
    def test_log_warning(self, mock_append, capsys):
        """JBTASK-012: log_warning: 出力

        base_task.py:96-99 append_job_logのみ（printなし）
        """
        # Arrange
        task = ConcreteTask(job_id="job-1")

        # Act
        task.log_warning("警告メッセージ")

        # Assert
        mock_append.assert_called_once()
        log_msg = mock_append.call_args[0][1]
        assert "[ConcreteTask][WARNING] 警告メッセージ" == log_msg
        captured = capsys.readouterr()
        assert captured.out == ""

    @patch("app.jobs.tasks.base_task.append_job_log")
    def test_log_debug(self, mock_append, capsys):
        """JBTASK-013: log_debug: 出力

        base_task.py:101-104 append_job_logのみ（printなし）
        """
        # Arrange
        task = ConcreteTask(job_id="job-1")

        # Act
        task.log_debug("デバッグメッセージ")

        # Assert
        mock_append.assert_called_once()
        log_msg = mock_append.call_args[0][1]
        assert "[ConcreteTask][DEBUG] デバッグメッセージ" == log_msg
        captured = capsys.readouterr()
        assert captured.out == ""
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| JBTASK-E01 | execute: 例外がexecuteで捕捉される | RuntimeError | _handle_errorで処理、例外は再送出されない |
| JBTASK-E02 | _handle_error: カスタム例外クラス | カスタム例外 | error_typeにクラス名が記録される |
| JBTASK-E03 | _handle_success: main_payload付きだがmessageなし | {"main_payload": []} | デフォルト完了メッセージ使用 |

### 3.1 異常系テスト

```python
class TestBaseTaskErrors:
    """BaseTask異常系テスト"""

    @patch("app.jobs.tasks.base_task.set_job_failed")
    @patch("app.jobs.tasks.base_task.append_job_log")
    @patch("app.jobs.tasks.base_task.update_job_status")
    @pytest.mark.asyncio
    async def test_execute_catches_exception(
        self, mock_update, mock_append, mock_failed
    ):
        """JBTASK-E01: execute: 例外がexecuteで捕捉される

        base_task.py:34-36 except Exception分岐。
        executeは例外を再送出せず、_handle_errorで処理を完結する。
        """
        # Arrange
        task = ConcreteTask(
            job_id="job-1",
            raise_error=RuntimeError("致命的エラー")
        )

        # Act（例外が発生しないことを確認）
        await task.execute()

        # Assert
        mock_failed.assert_called_once()
        error_msg = mock_failed.call_args[0][1]
        assert "致命的エラー" in error_msg

    @patch("app.jobs.tasks.base_task.set_job_failed")
    @patch("app.jobs.tasks.base_task.append_job_log")
    @patch("app.jobs.tasks.base_task.update_job_status")
    @pytest.mark.asyncio
    async def test_handle_error_custom_exception(
        self, mock_update, mock_append, mock_failed
    ):
        """JBTASK-E02: _handle_error: カスタム例外クラス

        base_task.py:77 type(error).__name__ でカスタム例外クラス名が記録される
        """
        # Arrange
        class CustomTaskError(Exception):
            pass

        task = ConcreteTask(job_id="job-1")
        error = CustomTaskError("カスタムエラー")

        # Act
        await task._handle_error(error)

        # Assert
        summary = mock_failed.call_args[1]["summary_data"]
        assert summary["error_type"] == "CustomTaskError"
        assert summary["error_message"] == "カスタムエラー"

    @patch("app.jobs.tasks.base_task.set_job_completed")
    @patch("app.jobs.tasks.base_task.append_job_log")
    @patch("app.jobs.tasks.base_task.update_job_status")
    @pytest.mark.asyncio
    async def test_handle_success_main_payload_without_message(
        self, mock_update, mock_append, mock_completed
    ):
        """JBTASK-E03: _handle_success: main_payload付きだがmessageなし

        base_task.py:54 result.get("message", completion_message) で
        messageキーがない場合はデフォルトの完了メッセージが使われる
        """
        # Arrange
        task = ConcreteTask(job_id="job-1")
        result = {
            "main_payload": [{"data": 1}],
            # messageキーなし
        }

        # Act
        await task._handle_success(result)

        # Assert
        mock_completed.assert_called_once()
        call_kwargs = mock_completed.call_args[1]
        # デフォルトの完了メッセージが使われる
        assert "ConcreteTask" in call_kwargs["final_message"]
        assert "正常完了" in call_kwargs["final_message"]
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| JBTASK-SEC-01 | _handle_error: エラーサマリーの認証情報サニタイズ未実装 | password含むエラー | str(error)がそのまま含まれる（既知の制限事項#1） |
| JBTASK-SEC-02 | log_info: ログフォーマット維持 | 改行含むメッセージ | [ClassName][LEVEL]形式維持 |
| JBTASK-SEC-03 | _handle_error: エラーサマリーの構造化 | 例外情報 | 構造化データのみ（スタックトレースなし） |

```python
@pytest.mark.security
class TestBaseTaskSecurity:
    """BaseTaskセキュリティテスト"""

    @patch("app.jobs.tasks.base_task.set_job_failed")
    @patch("app.jobs.tasks.base_task.append_job_log")
    @patch("app.jobs.tasks.base_task.update_job_status")
    @pytest.mark.asyncio
    async def test_error_summary_credential_exposure(
        self, mock_update, mock_append, mock_failed
    ):
        """JBTASK-SEC-01: _handle_error: エラーサマリーに認証情報

        CWE-209: Information Exposure Through an Error Message
        error_summaryにはstr(error)がそのまま含まれるため、
        認証情報入りの例外メッセージはそのまま記録される（既知の制限事項#1）。
        """
        # Arrange
        task = ConcreteTask(job_id="job-1")
        error = ValueError("password=secret123 token=abc-xyz")

        # Act
        await task._handle_error(error)

        # Assert
        summary = mock_failed.call_args[1]["summary_data"]
        # error_messageにはstr(error)が含まれる（サニタイズなし）
        assert summary["error_message"] == "password=secret123 token=abc-xyz"
        # 構造化されたフィールドのみ（スタックトレースは含まれない）
        assert "traceback" not in summary
        assert set(summary.keys()) == {
            "error_type", "error_message", "task_class",
            "execution_duration_seconds", "failed_at"
        }

    @patch("app.jobs.tasks.base_task.append_job_log")
    def test_log_format_integrity(self, mock_append):
        """JBTASK-SEC-02: log_info: ログフォーマット維持

        CWE-117: Improper Output Neutralization for Logs
        改行を含むメッセージでも[ClassName][LEVEL]形式が維持される
        """
        # Arrange
        task = ConcreteTask(job_id="job-1")
        malicious_msg = "正常メッセージ\n[CRITICAL] 偽ログ"

        # Act
        task.log_info(malicious_msg)

        # Assert
        log_msg = mock_append.call_args[0][1]
        assert log_msg.startswith("[ConcreteTask][INFO]")

    @patch("app.jobs.tasks.base_task.set_job_failed")
    @patch("app.jobs.tasks.base_task.append_job_log")
    @patch("app.jobs.tasks.base_task.update_job_status")
    @pytest.mark.asyncio
    async def test_error_summary_no_stacktrace(
        self, mock_update, mock_append, mock_failed
    ):
        """JBTASK-SEC-03: _handle_error: エラーサマリーの構造化

        CWE-209: error_summaryは構造化データのみで構成され、
        traceback情報はprint_exc()で標準エラー出力のみに出力される（サマリーには含まれない）。
        """
        # Arrange
        task = ConcreteTask(job_id="job-1")

        # ネストした例外を発生
        try:
            try:
                raise FileNotFoundError("/secret/path/config.json")
            except FileNotFoundError:
                raise RuntimeError("設定ファイル読み込み失敗") from None
        except RuntimeError as e:
            error = e

        # Act
        await task._handle_error(error)

        # Assert
        summary = mock_failed.call_args[1]["summary_data"]
        # サマリーにはスタックトレースが含まれない
        summary_str = str(summary)
        assert "Traceback" not in summary_str
        assert "/secret/path/" not in summary_str
        # error_messageはstr(error)のみ
        assert summary["error_message"] == "設定ファイル読み込み失敗"
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_base_task_module` | テスト間のモジュール状態リセット | function | Yes |

### 共通フィクスチャ定義

```python
# test/unit/jobs/tasks/conftest.py
import pytest


@pytest.fixture(autouse=True)
def reset_base_task_module():
    """テストごとにstatus_managerのグローバル状態をリセット

    status_managerのグローバル辞書(job_statuses)がテスト間で
    共有されないようにクリアする。
    注意: app.jobs.tasks.base_taskのモジュールキャッシュ削除は行わない。
    テストクラスが参照中のモジュールを削除するとpatchが効かなくなるため。
    """
    yield
    # status_managerのグローバル辞書をクリア
    try:
        from app.jobs.status_manager import job_statuses
        job_statuses.clear()
    except ImportError:
        pass
```

---

## 6. テスト実行例

```bash
# base_task関連テストのみ実行
pytest test/unit/jobs/tasks/test_base_task.py -v

# 特定のテストクラスのみ実行
pytest test/unit/jobs/tasks/test_base_task.py::TestBaseTaskExecute -v
pytest test/unit/jobs/tasks/test_base_task.py::TestBaseTaskHandleSuccess -v

# カバレッジ付きで実行（95%閾値強制）
pytest test/unit/jobs/tasks/test_base_task.py \
    --cov=app.jobs.tasks.base_task \
    --cov-report=term-missing \
    --cov-fail-under=95 -v

# セキュリティマーカーで実行
pytest test/unit/jobs/tasks/test_base_task.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 15 | JBTASK-001 〜 JBTASK-015 |
| 異常系 | 3 | JBTASK-E01 〜 JBTASK-E03 |
| セキュリティ | 3 | JBTASK-SEC-01 〜 JBTASK-SEC-03 |
| **合計** | **21** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestBaseTaskInit` | JBTASK-001 | 1 |
| `TestBaseTaskExecute` | JBTASK-002〜JBTASK-003 | 2 |
| `TestBaseTaskHandleSuccess` | JBTASK-004〜JBTASK-008, JBTASK-014 | 6 |
| `TestBaseTaskHandleError` | JBTASK-009, JBTASK-015 | 2 |
| `TestBaseTaskLogging` | JBTASK-010〜JBTASK-013 | 4 |
| `TestBaseTaskErrors` | JBTASK-E01〜JBTASK-E03 | 3 |
| `TestBaseTaskSecurity` | JBTASK-SEC-01〜JBTASK-SEC-03 | 3 |

### 実装失敗が予想されるテスト

現時点で失敗が予想されるテストはありません。

### 注意事項

- テスト実行に `pytest`, `pytest-asyncio`, `pytest-cov` が必要
- `@pytest.mark.security` マーカーの使用には `pyproject.toml` への登録が必要
- BaseTaskは抽象クラスのため、テスト用具象サブクラス `ConcreteTask` を使用
- `status_manager` の4関数（update_job_status, set_job_completed, set_job_failed, append_job_log）はすべてモック化必須
- `traceback.print_exc()` は標準エラー出力に出力される。`capsys.readouterr().err` で検証可能
- `@pytest.mark.security` の登録例:
  ```toml
  # pyproject.toml
  [tool.pytest.ini_options]
  markers = ["security: セキュリティ関連テスト"]
  ```

---

## 8. 既知の制限事項と改善推奨

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `_handle_error` がstr(error)をサニタイズせずにerror_summaryに含める | 認証情報入りの例外メッセージがsummary_dataに記録される（CWE-209） | エラーメッセージからパスワード/トークンをマスキングする処理追加を推奨 |
| 2 | `traceback.print_exc()` が標準エラー出力に出力 | 本番環境でスタックトレースが出力される | structured logging（logger.exception等）への移行を推奨 |
| 3 | `log_info` のみprint出力があり、他のログメソッドにはない | ログレベル間で出力先が一貫していない | 全メソッドでprint有無を統一するか、printを除去してlogger統合を推奨 |
| 4 | `start_time` がインスタンス変数で公開されている | テストで直接操作可能だが意図しない変更のリスク | propertyでの読み取り専用化を推奨 |
| 5 | `_handle_error` でtraceback.print_exc()を呼んでいるが、logメソッドとの二重出力 | エラー情報が複数箇所に分散する | 一元化されたエラーログ機構への統合を推奨 |
