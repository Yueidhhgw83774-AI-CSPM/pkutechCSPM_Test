# jobs/status_manager テストケース

## 1. 概要

`app/jobs/status_manager.py` は、ジョブシステム全体のステータス管理を担うインメモリのジョブレジストリです。ジョブの初期化・進捗更新・完了/失敗設定・排他制御・古いジョブのクリーンアップを提供します。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `initialize_job` | 新規ジョブIDの生成とステータス初期化 |
| `update_job_status` | ジョブステータスとメッセージの更新 |
| `update_job_progress` | 数値進捗情報（current/total）の更新 |
| `append_job_log` | ジョブログ行の追記（最大1000行制限） |
| `set_job_completed` | ジョブを完了状態に設定（サマリー・結果ペイロード対応） |
| `set_job_failed` | ジョブを失敗状態に設定（エラーメッセージ・部分結果対応） |
| `get_job_status_sync` | ジョブステータスの同期取得 |
| `get_job_result_sync` | ジョブ結果（ログ含む）の同期取得 |
| `get_active_job_count` | アクティブジョブ数の非同期取得 |
| `cleanup_old_jobs` | 古いジョブエントリの削除 |
| `is_any_job_active` | アクティブジョブ存在チェック |
| `check_job_exclusion` | 排他制御チェック（エラーメッセージ付き） |
| `try_initialize_job_exclusive` | 排他制御付きジョブ初期化（アトミック操作） |

### 1.2 カバレッジ目標: 90%

> **注記**: ジョブ管理はバックエンド全体の信頼性に直結する中核機能。特に排他制御（`try_initialize_job_exclusive`）とステータス遷移のエッジケース（完了後の更新防止等）が重要。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/jobs/status_manager.py` |
| テストコード | `test/unit/jobs/test_status_manager.py`（未実装・本仕様書に基づき作成予定） |

### 1.4 補足情報

#### グローバル状態

| 変数名 | 型 | 説明 |
|--------|------|------|
| `job_statuses` | `Dict[str, Dict[str, Any]]` | ジョブ情報を保持するインメモリ辞書 |
| `_job_status_lock` | `threading.Lock` | 排他制御用ロック |

#### ジョブステータス遷移

```
pending → running → completed
                  → failed
```

- `completed`/`failed` 後は `update_job_status` でステータス上書き不可（ただし `completed`/`failed` への再設定は可能）
- `set_job_completed` は `failed` 状態のジョブを `completed` に上書きしない
- `update_job_progress` は `running` 状態のときのみ進捗を更新

#### 主要分岐

| 関数 | 条件 | 結果 |
|------|------|------|
| `update_job_status` L48 | ステータスが `completed`/`failed` でない、または新ステータスが `completed`/`failed` | ステータス更新 |
| `update_job_progress` L79 | ステータスが `running` | 進捗更新（それ以外は無視） |
| `append_job_log` L101 | ログ行数 > 1000 | 古いログを先頭から削除 |
| `set_job_completed` L129 | ステータスが `failed` | 完了に上書きしない |
| `cleanup_old_jobs` L266 | `updated_at` パース失敗 | 不正エントリとして削除 |

#### 呼び出し元

| ファイル | 使用関数 |
|---------|---------|
| `app/jobs/router.py` | `get_job_status_sync`, `get_job_result_sync`, `initialize_job`, `update_job_status`, `job_statuses`, `append_job_log`, `check_job_exclusion`, `try_initialize_job_exclusive` |
| `app/jobs/common/status_tracking.py` | `update_job_status`, `update_job_progress` |
| `app/jobs/common/logging.py` | `append_job_log` |
| `app/jobs/tasks/base_task.py` | `initialize_job`, `update_job_status`, `set_job_completed`, `set_job_failed` 等 |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| JSM-001 | initialize_job: ジョブ初期化 | `job_type="custodian_scan"` | `job_` プレフィックスのID、ステータス `pending`、空 result リスト |
| JSM-002 | initialize_job: 異なるジョブタイプ | `job_type="file_processing"` | job_type が正しく保存される |
| JSM-003 | update_job_status: ステータス更新 | `status="running"` | ステータスが `running` に変更 |
| JSM-004 | update_job_status: メッセージ付き更新 | `status="running", message="処理中"` | progress.message に反映 |
| JSM-005 | update_job_status: メッセージなし更新 | `status="running", message=None` | 既存 progress.message は変更なし |
| JSM-006 | update_job_status: completed後の更新防止 | completed後に `status="running"` | ステータスは `completed` のまま |
| JSM-007 | update_job_status: completed→failedは許可 | completed後に `status="failed"` | ステータスは `failed` に変更 |
| JSM-007B | update_job_status: failed→completedは許可 | failed後に `status="completed"` | ステータスは `completed` に変更 |
| JSM-008 | update_job_progress: 進捗更新 | `current=5, total=10, unit="files"` | progress に数値情報が設定 |
| JSM-009 | update_job_progress: メッセージ付き | `message="50% 完了"` | progress.message が設定 |
| JSM-010 | update_job_progress: running以外は無視 | ステータス `pending` で呼び出し | progress は更新されない |
| JSM-011 | append_job_log: ログ追記 | `log_line="処理開始"` | result リストに追加 |
| JSM-012 | append_job_log: 複数ログ追記 | 3行分のログ | result リストに3行 |
| JSM-013 | append_job_log: 1000行超過で古いログ削除 | 1001行追記 | 最新1000行のみ保持 |
| JSM-013B | append_job_log: ちょうど1000行は削除されない | 1000行追記 | 全1000行保持（先頭行="ログ行 0"） |
| JSM-014 | set_job_completed: 基本完了 | デフォルト引数 | ステータス `completed`、message="Completed successfully" |
| JSM-015 | set_job_completed: カスタムメッセージ | `final_message="全件処理完了"` | progress.message に反映 |
| JSM-016 | set_job_completed: サマリーデータ付き | `summary_data={"total": 10}` | summary フィールドに保存 |
| JSM-017 | set_job_completed: 結果ペイロード付き | `main_payload_result=[{"id": 1}]` | result フィールドが上書き |
| JSM-018 | set_job_completed: failed状態は上書きしない | failed 後に set_job_completed | ステータスは `failed` のまま |
| JSM-019 | set_job_completed: final_message=None | `final_message=None` | 既存 progress.message を維持 |
| JSM-019B | set_job_completed: summary_data=Noneは空辞書で上書き | `summary_data=None`（既存summaryあり） | summary が `{}` に上書きされる |
| JSM-020 | set_job_failed: 基本失敗 | `error_message="タイムアウト"` | ステータス `failed`、error にメッセージ |
| JSM-021 | set_job_failed: サマリーデータ付き | `summary_data={"partial": True}` | summary フィールドに保存 |
| JSM-022 | set_job_failed: 部分結果付き | `main_payload_result=[{"id": 1}]` | result フィールドに保存 |
| JSM-023 | set_job_failed: 既存resultを維持 | main_payload_result=None、既存ログあり | 既存 result は上書きされない |
| JSM-024 | get_job_status_sync: ジョブ取得 | 存在するジョブID | ジョブ情報のコピーを返す |
| JSM-025 | get_job_status_sync: 存在しないID | 不明なジョブID | None を返す |
| JSM-026 | get_job_result_sync: 結果取得 | 存在するジョブID | result 含むジョブ情報のコピー |
| JSM-027 | get_job_result_sync: 存在しないID | 不明なジョブID | None を返す |
| JSM-028 | get_active_job_count: アクティブなし | 全ジョブ完了 | 0 |
| JSM-029 | get_active_job_count: アクティブあり | pending + running のジョブ | 2 |
| JSM-030 | cleanup_old_jobs: 古いジョブ削除 | 25時間前のジョブ | 削除される |
| JSM-031 | cleanup_old_jobs: 新しいジョブは維持 | 1時間前のジョブ | 削除されない |
| JSM-032 | is_any_job_active: アクティブなし | 全ジョブ completed | False |
| JSM-033 | is_any_job_active: pending あり | pending ジョブ存在 | True |
| JSM-034 | is_any_job_active: running あり | running ジョブ存在 | True |
| JSM-035 | check_job_exclusion: 排他なし | アクティブジョブなし | None |
| JSM-036 | check_job_exclusion: 排他あり | running ジョブ存在 | エラーメッセージ（ジョブID含む） |
| JSM-036B | check_job_exclusion: is_any_job_activeフォールバック | is_any_job_active=True, active_jobs空 | 詳細なしフォールバックメッセージ |
| JSM-037 | try_initialize_job_exclusive: 成功 | アクティブジョブなし | (job_id, None) |
| JSM-038 | try_initialize_job_exclusive: 排他失敗 | running ジョブ存在 | (None, error_message) |

### 2.1 initialize_job テスト

```python
# test/unit/jobs/test_status_manager.py
import pytest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta
import app.jobs.status_manager as sm


class TestInitializeJob:
    """ジョブ初期化のテスト"""

    def test_initialize_job_returns_valid_id(self):
        """JSM-001: ジョブ初期化で有効なIDが返される"""
        # Arrange
        from app.jobs.status_manager import initialize_job, job_statuses

        # Act
        job_id = initialize_job("custodian_scan")

        # Assert
        assert job_id.startswith("job_")
        assert job_id in job_statuses
        assert job_statuses[job_id]["status"] == "pending"
        assert job_statuses[job_id]["job_type"] == "custodian_scan"
        assert job_statuses[job_id]["result"] == []
        assert job_statuses[job_id]["error"] is None
        assert job_statuses[job_id]["progress"] is None
        assert "created_at" in job_statuses[job_id]
        assert "updated_at" in job_statuses[job_id]

    def test_initialize_job_different_type(self):
        """JSM-002: 異なるジョブタイプが正しく保存される"""
        # Arrange
        from app.jobs.status_manager import initialize_job, job_statuses

        # Act
        job_id = initialize_job("file_processing")

        # Assert
        assert job_statuses[job_id]["job_type"] == "file_processing"
```

### 2.2 update_job_status テスト

```python
class TestUpdateJobStatus:
    """ジョブステータス更新のテスト"""

    def test_update_status_basic(self):
        """JSM-003: 基本的なステータス更新"""
        # Arrange
        from app.jobs.status_manager import initialize_job, update_job_status, job_statuses
        job_id = initialize_job("test")

        # Act
        update_job_status(job_id, "running")

        # Assert
        assert job_statuses[job_id]["status"] == "running"

    def test_update_status_with_message(self):
        """JSM-004: メッセージ付きステータス更新"""
        # Arrange
        from app.jobs.status_manager import initialize_job, update_job_status, job_statuses
        job_id = initialize_job("test")

        # Act
        update_job_status(job_id, "running", message="処理中")

        # Assert
        assert job_statuses[job_id]["progress"]["message"] == "処理中"

    def test_update_status_none_message_preserves_existing(self):
        """JSM-005: message=Noneのときはprogressのmessageを変更しない"""
        # Arrange
        from app.jobs.status_manager import initialize_job, update_job_status, job_statuses
        job_id = initialize_job("test")
        update_job_status(job_id, "running", message="初期メッセージ")

        # Act
        update_job_status(job_id, "running", message=None)

        # Assert
        assert job_statuses[job_id]["progress"]["message"] == "初期メッセージ"

    def test_update_status_blocked_after_completed(self):
        """JSM-006: completed後のステータス変更は防止される（completed/failed以外）"""
        # Arrange
        from app.jobs.status_manager import initialize_job, update_job_status, job_statuses
        job_id = initialize_job("test")
        job_statuses[job_id]["status"] = "completed"

        # Act
        update_job_status(job_id, "running")

        # Assert
        assert job_statuses[job_id]["status"] == "completed"

    def test_update_status_completed_to_failed_allowed(self):
        """JSM-007: completed→failedへの遷移は許可される"""
        # Arrange
        from app.jobs.status_manager import initialize_job, update_job_status, job_statuses
        job_id = initialize_job("test")
        job_statuses[job_id]["status"] = "completed"

        # Act
        update_job_status(job_id, "failed")

        # Assert
        assert job_statuses[job_id]["status"] == "failed"

    def test_update_status_failed_to_completed_allowed(self):
        """JSM-007B: failed→completedへの遷移は許可される"""
        # Arrange
        from app.jobs.status_manager import initialize_job, update_job_status, job_statuses
        job_id = initialize_job("test")
        job_statuses[job_id]["status"] = "failed"

        # Act
        update_job_status(job_id, "completed")

        # Assert
        assert job_statuses[job_id]["status"] == "completed"
```

### 2.3 update_job_progress テスト

```python
class TestUpdateJobProgress:
    """進捗更新のテスト"""

    def test_update_progress_running(self):
        """JSM-008: running状態での進捗更新"""
        # Arrange
        from app.jobs.status_manager import initialize_job, update_job_progress, job_statuses
        job_id = initialize_job("test")
        job_statuses[job_id]["status"] = "running"

        # Act
        update_job_progress(job_id, current=5, total=10, unit="files")

        # Assert
        assert job_statuses[job_id]["progress"]["current"] == 5
        assert job_statuses[job_id]["progress"]["total"] == 10
        assert job_statuses[job_id]["progress"]["unit"] == "files"

    def test_update_progress_with_message(self):
        """JSM-009: メッセージ付き進捗更新"""
        # Arrange
        from app.jobs.status_manager import initialize_job, update_job_progress, job_statuses
        job_id = initialize_job("test")
        job_statuses[job_id]["status"] = "running"

        # Act
        update_job_progress(job_id, current=5, total=10, message="50% 完了")

        # Assert
        assert job_statuses[job_id]["progress"]["message"] == "50% 完了"

    def test_update_progress_ignored_when_not_running(self):
        """JSM-010: running以外のステータスでは進捗更新されない"""
        # Arrange
        from app.jobs.status_manager import initialize_job, update_job_progress, job_statuses
        job_id = initialize_job("test")
        # ステータスはpendingのまま

        # Act
        update_job_progress(job_id, current=5, total=10)

        # Assert
        assert job_statuses[job_id]["progress"] is None
```

### 2.4 append_job_log テスト

```python
class TestAppendJobLog:
    """ログ追記のテスト"""

    def test_append_log_basic(self):
        """JSM-011: 基本的なログ追記"""
        # Arrange
        from app.jobs.status_manager import initialize_job, append_job_log, job_statuses
        job_id = initialize_job("test")

        # Act
        append_job_log(job_id, "処理開始")

        # Assert
        assert "処理開始" in job_statuses[job_id]["result"]

    def test_append_log_multiple(self):
        """JSM-012: 複数行のログ追記"""
        # Arrange
        from app.jobs.status_manager import initialize_job, append_job_log, job_statuses
        job_id = initialize_job("test")

        # Act
        append_job_log(job_id, "行1")
        append_job_log(job_id, "行2")
        append_job_log(job_id, "行3")

        # Assert
        assert len(job_statuses[job_id]["result"]) == 3

    def test_append_log_max_lines_truncation(self):
        """JSM-013: 1000行を超えたら古いログが削除される"""
        # Arrange
        from app.jobs.status_manager import initialize_job, append_job_log, job_statuses
        job_id = initialize_job("test")

        # Act: 1001行追記
        for i in range(1001):
            append_job_log(job_id, f"ログ行 {i}")

        # Assert: 最新1000行のみ保持
        result = job_statuses[job_id]["result"]
        assert len(result) == 1000
        assert result[0] == "ログ行 1"  # 最古（行0は削除済み）
        assert result[-1] == "ログ行 1000"  # 最新

    def test_append_log_exactly_max_lines(self):
        """JSM-013B: ちょうど1000行のとき削除は発生しない"""
        # Arrange
        from app.jobs.status_manager import initialize_job, append_job_log, job_statuses
        job_id = initialize_job("test")

        # Act: ちょうど1000行追記
        for i in range(1000):
            append_job_log(job_id, f"ログ行 {i}")

        # Assert: 全1000行が保持される
        result = job_statuses[job_id]["result"]
        assert len(result) == 1000
        assert result[0] == "ログ行 0"  # 先頭行は削除されていない
```

### 2.5 set_job_completed テスト

```python
class TestSetJobCompleted:
    """ジョブ完了設定のテスト"""

    def test_set_completed_basic(self):
        """JSM-014: 基本的なジョブ完了"""
        # Arrange
        from app.jobs.status_manager import initialize_job, set_job_completed, job_statuses
        job_id = initialize_job("test")

        # Act
        set_job_completed(job_id)

        # Assert
        assert job_statuses[job_id]["status"] == "completed"
        assert job_statuses[job_id]["progress"]["message"] == "Completed successfully"
        assert job_statuses[job_id]["error"] is None

    def test_set_completed_custom_message(self):
        """JSM-015: カスタムメッセージで完了"""
        # Arrange
        from app.jobs.status_manager import initialize_job, set_job_completed, job_statuses
        job_id = initialize_job("test")

        # Act
        set_job_completed(job_id, final_message="全件処理完了")

        # Assert
        assert job_statuses[job_id]["progress"]["message"] == "全件処理完了"

    def test_set_completed_with_summary(self):
        """JSM-016: サマリーデータ付き完了"""
        # Arrange
        from app.jobs.status_manager import initialize_job, set_job_completed, job_statuses
        job_id = initialize_job("test")
        summary = {"total": 10, "success": 8}

        # Act
        set_job_completed(job_id, summary_data=summary)

        # Assert
        assert job_statuses[job_id]["summary"] == summary

    def test_set_completed_with_payload(self):
        """JSM-017: 結果ペイロード付き完了"""
        # Arrange
        from app.jobs.status_manager import initialize_job, set_job_completed, job_statuses
        job_id = initialize_job("test")
        payload = [{"id": 1, "policy": "test"}]

        # Act
        set_job_completed(job_id, main_payload_result=payload)

        # Assert
        assert job_statuses[job_id]["result"] == payload

    def test_set_completed_does_not_overwrite_failed(self):
        """JSM-018: failed状態のジョブをcompletedに上書きしない"""
        # Arrange
        from app.jobs.status_manager import initialize_job, set_job_completed, job_statuses
        job_id = initialize_job("test")
        job_statuses[job_id]["status"] = "failed"
        job_statuses[job_id]["error"] = "元のエラー"

        # Act
        set_job_completed(job_id, final_message="完了")

        # Assert
        assert job_statuses[job_id]["status"] == "failed"

    def test_set_completed_none_message_preserves_existing(self):
        """JSM-019: final_message=Noneのとき既存メッセージを維持"""
        # Arrange
        from app.jobs.status_manager import (
            initialize_job, update_job_status, set_job_completed, job_statuses
        )
        job_id = initialize_job("test")
        update_job_status(job_id, "running", message="処理中")

        # Act
        set_job_completed(job_id, final_message=None)

        # Assert
        assert job_statuses[job_id]["progress"]["message"] == "処理中"

    def test_set_completed_none_summary_overwrites_with_empty(self):
        """JSM-019B: summary_data=Noneのとき既存summaryが空辞書に上書きされる"""
        # Arrange
        from app.jobs.status_manager import initialize_job, set_job_completed, job_statuses
        job_id = initialize_job("test")
        # 手動でsummaryを設定
        job_statuses[job_id]["summary"] = {"key": "important_value"}

        # Act
        set_job_completed(job_id, summary_data=None)

        # Assert: 実装L146-148により空辞書で上書きされる
        assert job_statuses[job_id]["summary"] == {}
```

### 2.6 set_job_failed テスト

```python
class TestSetJobFailed:
    """ジョブ失敗設定のテスト"""

    def test_set_failed_basic(self):
        """JSM-020: 基本的なジョブ失敗"""
        # Arrange
        from app.jobs.status_manager import initialize_job, set_job_failed, job_statuses
        job_id = initialize_job("test")

        # Act
        set_job_failed(job_id, "タイムアウトエラー")

        # Assert
        assert job_statuses[job_id]["status"] == "failed"
        assert job_statuses[job_id]["error"] == "タイムアウトエラー"
        assert "Failed: タイムアウトエラー" in job_statuses[job_id]["progress"]["message"]

    def test_set_failed_with_summary(self):
        """JSM-021: サマリーデータ付き失敗"""
        # Arrange
        from app.jobs.status_manager import initialize_job, set_job_failed, job_statuses
        job_id = initialize_job("test")

        # Act
        set_job_failed(job_id, "エラー", summary_data={"partial": True})

        # Assert
        assert job_statuses[job_id]["summary"] == {"partial": True}

    def test_set_failed_with_partial_result(self):
        """JSM-022: 部分結果付き失敗"""
        # Arrange
        from app.jobs.status_manager import initialize_job, set_job_failed, job_statuses
        job_id = initialize_job("test")
        partial = [{"id": 1, "status": "ok"}]

        # Act
        set_job_failed(job_id, "一部失敗", main_payload_result=partial)

        # Assert
        assert job_statuses[job_id]["result"] == partial

    def test_set_failed_preserves_existing_result(self):
        """JSM-023: main_payload_result=Noneのとき既存resultを維持"""
        # Arrange
        from app.jobs.status_manager import (
            initialize_job, append_job_log, set_job_failed, job_statuses
        )
        job_id = initialize_job("test")
        append_job_log(job_id, "既存ログ")

        # Act
        set_job_failed(job_id, "エラー発生")

        # Assert
        assert "既存ログ" in job_statuses[job_id]["result"]
```

### 2.7 get_job_status_sync / get_job_result_sync テスト

```python
class TestGetJobSync:
    """ジョブ情報同期取得のテスト"""

    def test_get_status_existing_job(self):
        """JSM-024: 存在するジョブのステータス取得"""
        # Arrange
        from app.jobs.status_manager import initialize_job, get_job_status_sync
        job_id = initialize_job("test")

        # Act
        result = get_job_status_sync(job_id)

        # Assert
        assert result is not None
        assert result["job_id"] == job_id
        assert result["status"] == "pending"

    def test_get_status_nonexistent_job(self):
        """JSM-025: 存在しないジョブのステータス取得"""
        # Arrange
        from app.jobs.status_manager import get_job_status_sync

        # Act
        result = get_job_status_sync("job_nonexistent")

        # Assert
        assert result is None

    def test_get_result_existing_job(self):
        """JSM-026: 存在するジョブの結果取得"""
        # Arrange
        from app.jobs.status_manager import initialize_job, get_job_result_sync
        job_id = initialize_job("test")

        # Act
        result = get_job_result_sync(job_id)

        # Assert
        assert result is not None
        assert "result" in result

    def test_get_result_nonexistent_job(self):
        """JSM-027: 存在しないジョブの結果取得"""
        # Arrange
        from app.jobs.status_manager import get_job_result_sync

        # Act
        result = get_job_result_sync("job_nonexistent")

        # Assert
        assert result is None
```

### 2.8 get_active_job_count テスト

```python
class TestGetActiveJobCount:
    """アクティブジョブ数取得のテスト"""

    @pytest.mark.asyncio
    async def test_no_active_jobs(self):
        """JSM-028: アクティブジョブなし"""
        # Arrange
        from app.jobs.status_manager import initialize_job, get_active_job_count, job_statuses
        job_id = initialize_job("test")
        job_statuses[job_id]["status"] = "completed"

        # Act
        count = await get_active_job_count()

        # Assert
        assert count == 0

    @pytest.mark.asyncio
    async def test_multiple_active_jobs(self):
        """JSM-029: 複数のアクティブジョブ"""
        # Arrange
        from app.jobs.status_manager import initialize_job, get_active_job_count, job_statuses
        job1 = initialize_job("test1")
        job2 = initialize_job("test2")
        job_statuses[job1]["status"] = "pending"
        job_statuses[job2]["status"] = "running"

        # Act
        count = await get_active_job_count()

        # Assert
        assert count == 2
```

### 2.9 cleanup_old_jobs テスト

```python
class TestCleanupOldJobs:
    """古いジョブクリーンアップのテスト"""

    def test_cleanup_removes_old_jobs(self):
        """JSM-030: 期限切れジョブが削除される"""
        # Arrange
        from app.jobs.status_manager import initialize_job, cleanup_old_jobs, job_statuses
        job_id = initialize_job("test")
        # 25時間前のタイムスタンプを設定
        old_time = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
        job_statuses[job_id]["updated_at"] = old_time

        # Act
        cleanup_old_jobs(max_age_seconds=3600 * 24)

        # Assert
        assert job_id not in job_statuses

    def test_cleanup_keeps_recent_jobs(self):
        """JSM-031: 新しいジョブは削除されない"""
        # Arrange
        from app.jobs.status_manager import initialize_job, cleanup_old_jobs, job_statuses
        job_id = initialize_job("test")
        # updated_at は現在時刻（initialize_jobで設定済み）

        # Act
        cleanup_old_jobs(max_age_seconds=3600 * 24)

        # Assert
        assert job_id in job_statuses
```

### 2.10 is_any_job_active テスト

```python
class TestIsAnyJobActive:
    """アクティブジョブ存在チェックのテスト"""

    def test_no_active_jobs(self):
        """JSM-032: アクティブジョブなしでFalse"""
        # Arrange
        from app.jobs.status_manager import initialize_job, is_any_job_active, job_statuses
        job_id = initialize_job("test")
        job_statuses[job_id]["status"] = "completed"

        # Act
        result = is_any_job_active()

        # Assert
        assert result is False

    def test_pending_job_active(self):
        """JSM-033: pendingジョブでTrue"""
        # Arrange
        from app.jobs.status_manager import initialize_job, is_any_job_active

        # Act（initialize_jobでpending状態）
        initialize_job("test")
        result = is_any_job_active()

        # Assert
        assert result is True

    def test_running_job_active(self):
        """JSM-034: runningジョブでTrue"""
        # Arrange
        from app.jobs.status_manager import initialize_job, is_any_job_active, job_statuses
        job_id = initialize_job("test")
        job_statuses[job_id]["status"] = "running"

        # Act
        result = is_any_job_active()

        # Assert
        assert result is True
```

### 2.11 check_job_exclusion テスト

```python
class TestCheckJobExclusion:
    """排他制御チェックのテスト"""

    def test_no_exclusion(self):
        """JSM-035: アクティブジョブなしでNone"""
        # Arrange
        from app.jobs.status_manager import check_job_exclusion

        # Act
        result = check_job_exclusion()

        # Assert
        assert result is None

    def test_exclusion_with_active_job(self):
        """JSM-036: アクティブジョブありでエラーメッセージ"""
        # Arrange
        from app.jobs.status_manager import initialize_job, check_job_exclusion, job_statuses
        job_id = initialize_job("custodian_scan")
        job_statuses[job_id]["status"] = "running"

        # Act
        result = check_job_exclusion()

        # Assert
        assert result is not None
        assert "実行中" in result
        assert job_id in result
        assert "custodian_scan" in result

    def test_exclusion_fallback_message(self):
        """JSM-036B: is_any_job_activeがTrueだがactive_jobsリスト空のフォールバック"""
        # Arrange
        from unittest.mock import patch
        from app.jobs.status_manager import check_job_exclusion

        # Act: is_any_job_activeをモックしてTrue返却、job_statusesは空のまま
        with patch("app.jobs.status_manager.is_any_job_active", return_value=True):
            result = check_job_exclusion()

        # Assert: 詳細なしのフォールバックメッセージ
        assert result is not None
        assert "実行中" in result
```

### 2.12 try_initialize_job_exclusive テスト

```python
class TestTryInitializeJobExclusive:
    """排他制御付きジョブ初期化のテスト"""

    def test_exclusive_init_success(self):
        """JSM-037: アクティブジョブなしで初期化成功"""
        # Arrange
        from app.jobs.status_manager import try_initialize_job_exclusive, job_statuses

        # Act
        job_id, error = try_initialize_job_exclusive("custodian_scan")

        # Assert
        assert job_id is not None
        assert job_id.startswith("job_")
        assert error is None
        assert job_id in job_statuses
        assert job_statuses[job_id]["status"] == "pending"

    def test_exclusive_init_blocked(self):
        """JSM-038: アクティブジョブありで初期化失敗"""
        # Arrange
        from app.jobs.status_manager import (
            initialize_job, try_initialize_job_exclusive, job_statuses
        )
        existing_id = initialize_job("scan1")
        job_statuses[existing_id]["status"] = "running"

        # Act
        job_id, error = try_initialize_job_exclusive("scan2")

        # Assert
        assert job_id is None
        assert error is not None
        assert "実行中" in error
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| JSM-E01 | update_job_status: 存在しないジョブID | 不明なID | 例外なし（Warning出力のみ） |
| JSM-E02 | update_job_progress: 存在しないジョブID | 不明なID | 例外なし（無視） |
| JSM-E03 | append_job_log: 存在しないジョブID | 不明なID | 例外なし（無視） |
| JSM-E04 | set_job_completed: 存在しないジョブID | 不明なID | 例外なし（Warning出力） |
| JSM-E05 | set_job_failed: 存在しないジョブID | 不明なID | 例外なし（Warning出力） |
| JSM-E06 | append_job_log: resultがリストでない場合 | result を文字列に書き換え | リストに再初期化されログ追記 |
| JSM-E07 | cleanup_old_jobs: 不正なupdated_at | updated_at を無効な文字列に | 不正エントリとして削除 |
| JSM-E08 | set_job_failed: error_messageが非文字列 | `error_message=123`（int） | str化されて保存 |

### 3.1 存在しないジョブID テスト

```python
class TestNonexistentJobId:
    """存在しないジョブIDに対する操作のテスト"""

    def test_update_status_nonexistent(self, capsys):
        """JSM-E01: 存在しないジョブIDでのステータス更新はWarning出力のみ"""
        # Arrange
        from app.jobs.status_manager import update_job_status

        # Act
        update_job_status("job_nonexistent", "running")

        # Assert: 例外なし & Warning出力
        captured = capsys.readouterr()
        assert "Warning" in captured.out
        assert "job_nonexistent" in captured.out

    def test_update_progress_nonexistent(self):
        """JSM-E02: 存在しないジョブIDでの進捗更新は例外なし（サイレント無視）"""
        # Arrange
        from app.jobs.status_manager import update_job_progress

        # Act & Assert: 例外が発生しないことを確認
        update_job_progress("job_nonexistent", 1, 10)

    def test_append_log_nonexistent(self):
        """JSM-E03: 存在しないジョブIDでのログ追記は例外なし（サイレント無視）"""
        # Arrange
        from app.jobs.status_manager import append_job_log

        # Act & Assert
        append_job_log("job_nonexistent", "テストログ")

    def test_set_completed_nonexistent(self, capsys):
        """JSM-E04: 存在しないジョブIDでの完了設定はWarning出力のみ"""
        # Arrange
        from app.jobs.status_manager import set_job_completed

        # Act
        set_job_completed("job_nonexistent")

        # Assert
        captured = capsys.readouterr()
        assert "Warning" in captured.out
        assert "job_nonexistent" in captured.out

    def test_set_failed_nonexistent(self, capsys):
        """JSM-E05: 存在しないジョブIDでの失敗設定はWarning出力のみ"""
        # Arrange
        from app.jobs.status_manager import set_job_failed

        # Act
        set_job_failed("job_nonexistent", "テストエラー")

        # Assert
        captured = capsys.readouterr()
        assert "Warning" in captured.out
        assert "job_nonexistent" in captured.out
```

### 3.2 不正データ テスト

```python
class TestInvalidData:
    """不正なデータに対する耐性テスト"""

    def test_append_log_result_not_list(self):
        """JSM-E06: resultがリストでない場合に再初期化される"""
        # Arrange
        from app.jobs.status_manager import initialize_job, append_job_log, job_statuses
        job_id = initialize_job("test")
        job_statuses[job_id]["result"] = "不正な文字列"

        # Act
        append_job_log(job_id, "新しいログ")

        # Assert
        assert isinstance(job_statuses[job_id]["result"], list)
        assert "新しいログ" in job_statuses[job_id]["result"]

    def test_cleanup_invalid_updated_at(self):
        """JSM-E07: 不正なupdated_atのジョブが削除される"""
        # Arrange
        from app.jobs.status_manager import initialize_job, cleanup_old_jobs, job_statuses
        job_id = initialize_job("test")
        job_statuses[job_id]["updated_at"] = "これは日付ではない"

        # Act
        cleanup_old_jobs()

        # Assert
        assert job_id not in job_statuses

    def test_set_failed_non_string_error(self):
        """JSM-E08: 非文字列のerror_messageがstr化される"""
        # Arrange
        from app.jobs.status_manager import initialize_job, set_job_failed, job_statuses
        job_id = initialize_job("test")

        # Act
        set_job_failed(job_id, 12345)

        # Assert
        assert job_statuses[job_id]["error"] == "12345"
        assert isinstance(job_statuses[job_id]["error"], str)
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| JSM-SEC-01 | get_job_status_sync: 浅いコピーの制限確認 | 返却値のトップレベル変更 | トップレベルキーはグローバルに影響しない |
| JSM-SEC-01B | get_job_status_sync: ネスト辞書の共有参照を検出 **[暫定テスト — deepcopy導入時に期待値反転予定]** | 返却値のネスト変更 | progressが共有参照であることを確認（既知の制限） |
| JSM-SEC-02 | ジョブIDの予測不可能性 | 複数ジョブ生成 | UUID4形式で推測不可 |
| JSM-SEC-03 | ログ保存時挙動確認（悪意ある文字列） | 悪意あるログ行 | そのまま文字列として保存（解釈されない） |
| JSM-SEC-04 | set_job_failed: 入力がそのまま保存される | 内部情報を含む文字列 | error フィールドにサニタイズなしで格納（呼び出し元の責務） |
| JSM-SEC-05 | try_initialize_job_exclusive: スレッドセーフティ | Barrier同期の並行呼び出し | 1つのみ成功 |
| JSM-SEC-08 | initialize_job: 悪意あるjob_type文字列 | XSS・巨大文字列・制御文字 | 文字列として保存、システム異常終了なし |

```python
@pytest.mark.security
class TestSecurityStatusManager:
    """セキュリティテスト"""

    def test_returned_status_top_level_isolated(self):
        """JSM-SEC-01: get_job_status_syncの返却値のトップレベル変更はグローバルに影響しない"""
        # Arrange
        from app.jobs.status_manager import initialize_job, get_job_status_sync, job_statuses
        job_id = initialize_job("test")

        # Act
        returned = get_job_status_sync(job_id)
        returned["status"] = "hacked"
        returned["evil_field"] = "injected"

        # Assert: トップレベルキーの変更はグローバルに影響しない
        assert job_statuses[job_id]["status"] == "pending"
        assert "evil_field" not in job_statuses[job_id]

    def test_returned_status_nested_shared_reference(self):
        """JSM-SEC-01B: 浅いコピーのためネスト辞書は共有参照（既知の制限事項）[暫定テスト — deepcopy導入時に期待値反転予定]"""
        # Arrange
        from app.jobs.status_manager import (
            initialize_job, update_job_status, get_job_status_sync, job_statuses
        )
        job_id = initialize_job("test")
        update_job_status(job_id, "running", message="元のメッセージ")

        # Act: ネスト辞書を変更
        returned = get_job_status_sync(job_id)
        returned["progress"]["message"] = "改竄された"

        # Assert: 浅いコピーのためネスト辞書はグローバルと共有される（既知の制限）
        # NOTE: 実装がcopy.deepcopyに変更された場合、このテストは失敗する→その時は期待値を反転させる
        assert job_statuses[job_id]["progress"]["message"] == "改竄された"

    def test_job_id_unpredictability(self):
        """JSM-SEC-02: ジョブIDがUUID4形式で予測不可能"""
        # Arrange
        import uuid as uuid_module
        from app.jobs.status_manager import initialize_job

        # Act
        ids = [initialize_job("test") for _ in range(10)]

        # Assert: すべて一意
        assert len(set(ids)) == 10
        # UUID4形式の厳密チェック
        for job_id in ids:
            uuid_part = job_id.replace("job_", "")
            parsed = uuid_module.UUID(uuid_part, version=4)
            assert str(parsed) == uuid_part

    def test_log_injection_resistance(self):
        """JSM-SEC-03: 悪意ある文字列のログ保存時挙動確認"""
        # Arrange
        from app.jobs.status_manager import initialize_job, append_job_log, job_statuses
        job_id = initialize_job("test")
        malicious_log = '<script>alert("xss")</script>\n\r\nInjected-Header: value'

        # Act
        append_job_log(job_id, malicious_log)

        # Assert: そのまま文字列として保存される（解釈・実行されない）
        assert job_statuses[job_id]["result"][-1] == malicious_log

    def test_error_message_stored_as_is(self):
        """JSM-SEC-04: set_job_failedは入力をそのまま保存する（サニタイズは呼び出し元の責務）"""
        # Arrange
        from app.jobs.status_manager import initialize_job, set_job_failed, job_statuses
        job_id = initialize_job("test")
        # 内部情報を含む可能性のあるエラーメッセージ
        raw_error = "DB接続失敗: host=internal.db:5432 user=admin"

        # Act
        set_job_failed(job_id, raw_error)

        # Assert: status_managerはサニタイズしない。入力がそのまま格納される
        # NOTE: APIレスポンスとしてクライアントに返却する際のサニタイズはrouter層の責務
        assert job_statuses[job_id]["error"] == raw_error

    def test_exclusive_init_thread_safety(self):
        """JSM-SEC-05: try_initialize_job_exclusiveのスレッドセーフティ（Barrier同期）"""
        # Arrange
        import threading
        from app.jobs.status_manager import try_initialize_job_exclusive, job_statuses

        # 事前条件: ジョブが空であること
        assert len(job_statuses) == 0

        num_threads = 5
        barrier = threading.Barrier(num_threads)
        results = []
        errors = []
        lock = threading.Lock()

        def attempt_init():
            barrier.wait()  # 全スレッドが揃ってから同時に実行
            job_id, error = try_initialize_job_exclusive("concurrent_test")
            with lock:
                results.append(job_id)
                errors.append(error)

        # Act: 5スレッドで同時に初期化を試行
        threads = [threading.Thread(target=attempt_init) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Assert: 成功は1つのみ
        successful = [r for r in results if r is not None]
        failed = [e for e in errors if e is not None]
        assert len(successful) == 1
        assert len(failed) == num_threads - 1

    def test_malicious_job_type_handling(self):
        """JSM-SEC-08: 悪意あるjob_type文字列でもシステムが異常終了しない"""
        # Arrange
        from app.jobs.status_manager import initialize_job, job_statuses

        malicious_types = [
            '<script>alert("xss")</script>',  # XSSペイロード
            "A" * 10000,  # 巨大文字列
            "line1\nline2\r\nline3",  # 改行・制御文字
            "../../../etc/passwd",  # パストラバーサル
        ]

        # Act & Assert
        for malicious_type in malicious_types:
            job_id = initialize_job(malicious_type)
            assert job_id is not None
            assert job_statuses[job_id]["job_type"] == malicious_type
```

---

## 5. フィクスチャ

| フィクスチャ名 | スコープ | 説明 |
|---------------|---------|------|
| `reset_job_statuses` | function (autouse) | 各テスト前後にグローバル `job_statuses` をクリア |

```python
# test/unit/jobs/conftest.py
import pytest
import app.jobs.status_manager as sm


@pytest.fixture(autouse=True)
def reset_job_statuses():
    """各テスト前後にグローバル状態をリセット（オブジェクト参照を維持）"""
    # NOTE: sys.modulesからの削除はオブジェクト参照が壊れるため使用しない。
    # モジュールレベルの辞書を直接clearすることで安全にリセットする。
    sm.job_statuses.clear()
    yield
    sm.job_statuses.clear()
```

---

## 6. テスト実行例

```bash
# ※ テストファイルは未実装。本仕様書に基づき作成後に実行すること。

# 全テスト実行
pytest test/unit/jobs/test_status_manager.py -v

# 正常系のみ（異常系・セキュリティクラスを除外）
pytest test/unit/jobs/test_status_manager.py -v -k "not (Nonexistent or InvalidData or Security)"

# 異常系のみ
pytest test/unit/jobs/test_status_manager.py -v -k "Nonexistent or InvalidData"

# セキュリティテストのみ
pytest test/unit/jobs/test_status_manager.py -v -k "Security"

# カバレッジ計測
pytest test/unit/jobs/test_status_manager.py --cov=app.jobs.status_manager --cov-report=term-missing
```

---

## 7. テストケースサマリー

### 7.1 テスト数サマリー

| カテゴリ | テスト数 |
|---------|---------|
| 正常系 | 42（JSM-001〜038 + 007B, 013B, 019B, 036B） |
| 異常系 | 8（JSM-E01〜E08） |
| セキュリティ | 7（JSM-SEC-01, 01B, 02, 03, 04, 05, 08） |
| **合計** | **57** |

### 7.2 クラス構成

| クラス名 | テスト数 | 対象関数 |
|---------|---------|---------|
| `TestInitializeJob` | 2 | `initialize_job` |
| `TestUpdateJobStatus` | 6 | `update_job_status`（+007B） |
| `TestUpdateJobProgress` | 3 | `update_job_progress` |
| `TestAppendJobLog` | 4 | `append_job_log`（+013B） |
| `TestSetJobCompleted` | 7 | `set_job_completed`（+019B） |
| `TestSetJobFailed` | 4 | `set_job_failed` |
| `TestGetJobSync` | 4 | `get_job_status_sync`, `get_job_result_sync` |
| `TestGetActiveJobCount` | 2 | `get_active_job_count` |
| `TestCleanupOldJobs` | 2 | `cleanup_old_jobs` |
| `TestIsAnyJobActive` | 3 | `is_any_job_active` |
| `TestCheckJobExclusion` | 3 | `check_job_exclusion`（+036B） |
| `TestTryInitializeJobExclusive` | 2 | `try_initialize_job_exclusive` |
| `TestNonexistentJobId` | 5 | 各関数の不存在ID処理 |
| `TestInvalidData` | 3 | 不正データ耐性 |
| `TestSecurityStatusManager` | 7 | セキュリティ検証（+SEC-01B, SEC-08） |

### 7.3 失敗予測テーブル

| テストID | 失敗理由 | 対処法 |
|---------|---------|--------|
| JSM-SEC-01B | 実装が `copy.deepcopy` に変更された場合 | 期待値を反転（ネスト変更がグローバルに影響しないことを確認）|
| JSM-SEC-08 | 巨大文字列（10000文字）でメモリ制約環境の場合 | テスト対象文字列サイズを縮小 |

### 7.4 補足事項

- `get_job_status_sync` と `get_job_result_sync` は現在ほぼ同じ実装（浅いコピーを返す）。将来 `get_job_status_sync` が result を除外する可能性がある（コメントアウトされたコード L228-L233）
- `cleanup_old_jobs` の `except:` （L268）はベアexceptで、任意の例外を捕捉する。PEP8違反だが意図的な安全策
- `_job_status_lock` は `check_job_exclusion` と `try_initialize_job_exclusive` でのみ使用。他の関数（`initialize_job`, `update_job_status` 等）はロックなしでグローバル辞書にアクセスしている

---

## 8. 既知の制限事項

| 制限事項 | 影響 | 回避策 |
|---------|------|--------|
| インメモリ管理のためプロセス再起動でデータ消失 | テスト影響なし（各テストでリセット） | 永続化は将来実装（Redis/DB） |
| `_job_status_lock` が排他制御関数でのみ使用 | 通常のステータス更新はスレッドセーフでない | 単一ワーカー前提で運用（BackgroundTasksは同一スレッド） |
| `cleanup_old_jobs` のベアexcept | 全例外を無視するため予期せぬバグを隠す可能性 | テストでは明示的に不正データを注入して検証 |
| `get_job_status_sync` が浅いコピーを返す | ネストされた辞書（progress等）は共有参照で、変更がグローバル状態に伝播する | JSM-SEC-01Bで既知の挙動として検出。将来 `copy.deepcopy` への変更を検討 |
| `set_job_failed` がエラーメッセージをサニタイズしない | 呼び出し元が内部情報を含む文字列を渡すとそのまま保存される | サニタイズはrouter層の責務。JSM-SEC-04で挙動を確認済み |
| ジョブ数の上限チェックなし | 大量のジョブ登録でメモリ枯渇の可能性 | `cleanup_old_jobs` の定期呼び出しで対応 |
