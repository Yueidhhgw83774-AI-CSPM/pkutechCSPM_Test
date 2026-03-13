# jobs/tasks/new_custodian_scan/main_task テストケース

## 1. 概要

`main_task.py` は新しい Custodian スキャンのメイン制御モジュール。`NewCustodianScanTask` クラスがワークフロー全体を調整し、認証情報解析・スキャン実行・結果処理・履歴保存を各コンポーネントに委譲するオーケストレーターである。

### 1.1 主要機能

| メソッド | 説明 |
|---------|------|
| `_get_custodian_version` | c7n バージョン取得（モジュールレベル関数） |
| `__init__` | 6つの機能コンポーネントを初期化 |
| `_execute_task` | メインワークフロー（認証解析→検証→スキャン→結果処理→一時ファイル削除） |
| `_process_scan_results` | 致命的エラー/違反あり/違反なしの3分岐で結果処理 |
| `_handle_fatal_error` | 致命的エラー時のメタデータ設定 |
| `_store_violations_to_opensearch` | 違反リソースを OpenSearch に保存 |
| `_save_scan_history_v2` | cspm-scan-history-v2 に詳細情報を保存 |
| `_handle_error` | エラー時の履歴保存 + 親クラスのエラー処理呼び出し |
| `_generate_and_store_ai_summary` | AI 統計サマリー生成 |
| `_update_scan_history` | cspm-scan-history-v2 の更新/新規作成 |

### 1.2 カバレッジ目標: 85%

> **注記**: オーケストレーションモジュールのため、全コンポーネントをモックする。遅延 import（`store_scan_history_v2`, `generate_scan_summary`）は `patch` で対応。pytest-asyncio が必要。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/jobs/tasks/new_custodian_scan/main_task.py` |
| テストコード | `test/unit/jobs/tasks/new_custodian_scan/test_main_task.py` |

### 1.4 補足情報

#### 依存関係（全モック対象）

```
main_task.py ──→ BaseTask（基底クラス）
             ──→ BackwardCompatMixin（後方互換）
             ──→ TaskLogger / StatusTracker（ログ・ステータス）
             ──→ CredentialProcessor（認証情報解析）
             ──→ ScanCoordinator（スキャン実行）
             ──→ ResultProcessor（結果処理）
             ──→ ErrorHistoryHandler（エラー履歴保存）
             ──→ get_opensearch_client（非同期 OpenSearch）
             ──→ store_scan_history_v2（遅延 import）
             ──→ generate_scan_summary（遅延 import）
             ──→ tempfile.mkdtemp / shutil.rmtree（一時ディレクトリ）
             ──→ datetime.now（タイムスタンプ）
```

#### テスト戦略

| テストカテゴリ | 手法 |
|--------------|------|
| 初期化テスト | コンポーネントクラスを patch してインスタンス生成 |
| ワークフローテスト | 内部メソッドを `patch.object` でモックし、フロー制御を検証 |
| 個別メソッドテスト | 対象メソッドの依存のみ patch して直接呼び出し |
| 遅延 import テスト | `patch` でモジュールレベルの import を差し替え |

#### フィクスチャ方針

`NewCustodianScanTask.__init__` が6つのコンポーネント（TaskLogger, StatusTracker, CredentialProcessor, ScanCoordinator, ResultProcessor, ErrorHistoryHandler）を生成するため、全依存クラスを `patch` してからインスタンスを生成し、`logger` を `MagicMock` に差し替えてアサーションに使用する。

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| NCMT-001 | _get_custodian_version pkg_resources 成功 | c7n インストール済み | バージョン文字列 |
| NCMT-002 | _get_custodian_version 両方失敗 | 両方例外 | `"unknown"` |
| NCMT-003 | __init__ が全コンポーネントを初期化 | job_id | 6属性設定 |
| NCMT-004 | _execute_task 正常フロー | 有効な kwargs | final_results 返却 |
| NCMT-005 | _execute_task ValidationError 再発生 | 無効な入力 | ValidationError 伝播 |
| NCMT-006 | _execute_task 例外発生時も finally で一時ディレクトリ削除 | 例外発生 | shutil.rmtree 呼び出し |
| NCMT-007 | _execute_task 一時ディレクトリ削除失敗→warning | rmtree 例外 | logger.warning |
| NCMT-008 | _process_scan_results 致命的エラー | return_code=1 | _handle_fatal_error 呼び出し |
| NCMT-009 | _process_scan_results 違反あり | violations_count>0 | _store_violations 呼び出し |
| NCMT-010 | _process_scan_results 違反なし | violations_count=0 | OpenSearch スキップ |
| NCMT-011 | _handle_fatal_error メタデータ設定 | scan_metadata | 4つのフラグ設定 |
| NCMT-012 | _store_violations_to_opensearch 成功 | 違反データ | stored_count 設定 |
| NCMT-013 | _store_violations_to_opensearch 例外キャッチ | store 例外 | error メタデータ設定 |
| NCMT-014 | _save_scan_history_v2 成功 | 有効なデータ | history_v2_stored=True |
| NCMT-015 | _save_scan_history_v2 空 dir→スキップ | 空文字列 | history_v2_stored=False |
| NCMT-016 | _save_scan_history_v2 aggregated 統計含む | 統計データ | enhanced_metadata に含む |
| NCMT-017 | _save_scan_history_v2 save 失敗 | history_saved=False | warning ログ |
| NCMT-018 | _save_scan_history_v2 例外キャッチ | store 関数例外 | error ログ |
| NCMT-019 | _handle_error 履歴保存+super 呼び出し | RuntimeError | 両方呼び出し確認 |
| NCMT-020 | _handle_error 履歴保存例外→super 続行 | save 例外 | error ログ + super 呼び出し |
| NCMT-021 | _generate_and_store_ai_summary 成功 | サマリー返却 | has_ai_summary=True |
| NCMT-022 | _generate_and_store_ai_summary None 返却 | None | has_ai_summary=False |
| NCMT-023 | _generate_and_store_ai_summary 例外 | 生成例外 | error ログ |
| NCMT-024 | _update_scan_history 更新成功 | モック client | client.update 呼び出し |
| NCMT-025 | _update_scan_history client None→スキップ | None | warning ログ |
| NCMT-026 | _get_custodian_version importlib.metadata 成功 | pkg_resources 失敗 | importlib 経由でバージョン返却 |
| NCMT-027 | _store_violations_to_opensearch stored_count=0 | 保存結果0件 | opensearch_store_success=False |

### 2.1 _get_custodian_version テスト

```python
# test/unit/jobs/tasks/new_custodian_scan/test_main_task.py
import sys
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

MODULE = "app.jobs.tasks.new_custodian_scan.main_task"


class TestGetCustodianVersion:
    """_get_custodian_version のフォールバック分岐テスト"""

    def test_pkg_resources_success(self):
        """NCMT-001: pkg_resources でバージョン取得成功

        main_task.py:31-33 の try 正常パスをカバー。
        """
        # Arrange
        mock_pkg = MagicMock()
        mock_dist = MagicMock()
        mock_dist.version = "0.9.35"
        mock_pkg.get_distribution.return_value = mock_dist

        with patch.dict(sys.modules, {"pkg_resources": mock_pkg}):
            # Act
            from app.jobs.tasks.new_custodian_scan.main_task import _get_custodian_version
            result = _get_custodian_version()

        # Assert
        assert result == "0.9.35"

    def test_both_fail_returns_unknown(self):
        """NCMT-002: pkg_resources・importlib.metadata 両方失敗で "unknown" を返す

        main_task.py:34 の外側 except → L35 importlib.metadata → L38-40 の最終 except をカバー。
        """
        # Arrange
        mock_pkg = MagicMock()
        mock_pkg.get_distribution.side_effect = Exception("not found")

        with patch.dict(sys.modules, {"pkg_resources": mock_pkg}):
            with patch("importlib.metadata.version", side_effect=Exception("not found")):
                # Act
                from app.jobs.tasks.new_custodian_scan.main_task import _get_custodian_version
                result = _get_custodian_version()

        # Assert
        assert result == "unknown"

    def test_importlib_metadata_fallback_success(self):
        """NCMT-026: pkg_resources 失敗→importlib.metadata で成功

        main_task.py:34 の外側 except → L35-37 の importlib.metadata 成功パスをカバー。
        """
        # Arrange
        mock_pkg = MagicMock()
        mock_pkg.get_distribution.side_effect = Exception("not found")

        with patch.dict(sys.modules, {"pkg_resources": mock_pkg}):
            with patch("importlib.metadata.version", return_value="0.9.36"):
                # Act
                from app.jobs.tasks.new_custodian_scan.main_task import _get_custodian_version
                result = _get_custodian_version()

        # Assert
        assert result == "0.9.36"
```

### 2.2 初期化テスト

```python
class TestNewCustodianScanTaskInit:
    """__init__ のコンポーネント初期化テスト"""

    def test_init_sets_all_components(self):
        """NCMT-003: __init__ が全コンポーネントと dry_run_mode を初期化

        main_task.py:46-58 の全属性設定をカバー。
        """
        # Arrange & Act
        with patch(f"{MODULE}.TaskLogger") as mock_tl, \
             patch(f"{MODULE}.StatusTracker") as mock_st, \
             patch(f"{MODULE}.CredentialProcessor") as mock_cp, \
             patch(f"{MODULE}.ScanCoordinator") as mock_sc, \
             patch(f"{MODULE}.ResultProcessor") as mock_rp, \
             patch(f"{MODULE}.ErrorHistoryHandler") as mock_ehh:
            from app.jobs.tasks.new_custodian_scan.main_task import NewCustodianScanTask
            task = NewCustodianScanTask("test-job-123")

        # Assert
        assert task.job_id == "test-job-123"
        assert task.dry_run_mode is False
        mock_tl.assert_called_once_with("test-job-123", "NewCustodianScan")
        mock_st.assert_called_once_with("test-job-123")
        mock_cp.assert_called_once_with("test-job-123")
        mock_sc.assert_called_once_with("test-job-123", False)
        mock_rp.assert_called_once_with("test-job-123")
        mock_ehh.assert_called_once()  # ErrorHistoryHandler(job_id, self.logger)
```

### 2.3 _execute_task テスト

```python
class TestExecuteTask:
    """_execute_task のワークフローテスト"""

    @pytest.fixture
    def task(self):
        """全依存をモック化した NewCustodianScanTask"""
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.StatusTracker"), \
             patch(f"{MODULE}.CredentialProcessor"), \
             patch(f"{MODULE}.ScanCoordinator"), \
             patch(f"{MODULE}.ResultProcessor"), \
             patch(f"{MODULE}.ErrorHistoryHandler"):
            from app.jobs.tasks.new_custodian_scan.main_task import NewCustodianScanTask
            instance = NewCustodianScanTask("test-job")
        instance.logger = MagicMock()
        return instance

    @pytest.mark.asyncio
    async def test_successful_flow(self, task):
        """NCMT-004: 正常フローで認証解析→検証→スキャン→結果処理を実行

        main_task.py:60-114 の正常パス全体をカバー。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.authType = "accessKey"
        mock_creds.scanRegions = ["us-east-1"]
        task.credential_processor.parse_credentials_payload = AsyncMock(return_value=mock_creds)
        task.scan_coordinator.execute_multi_region_custodian_scan = AsyncMock(
            return_value={"violations_count": 0}
        )

        with patch.object(task, '_process_scan_results', new_callable=AsyncMock,
                          return_value={"message": "完了"}) as mock_process:
            with patch(f"{MODULE}.tempfile.mkdtemp", return_value="/tmp/test"):
                with patch("shutil.rmtree"):
                    # Act
                    result = await task._execute_task(
                        policy_yaml_content="policies: []",
                        credentials_data={"authType": "accessKey"},
                        cloud_provider="aws"
                    )

        # Assert
        assert result == {"message": "完了"}
        task.credential_processor.parse_credentials_payload.assert_awaited_once()
        mock_process.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_validation_error_re_raised(self, task):
        """NCMT-005: ValidationError がそのまま再発生する

        main_task.py:91-95 の ValidationError キャッチ→raise をカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        mock_creds = MagicMock()
        task.credential_processor.parse_credentials_payload = AsyncMock(return_value=mock_creds)
        task.credential_processor.validate_inputs.side_effect = ValidationError(
            "ポリシーが空です", field_name="policy_yaml_content"
        )

        with patch(f"{MODULE}.tempfile.mkdtemp", return_value="/tmp/test"):
            with patch("shutil.rmtree"):
                # Act & Assert
                with pytest.raises(ValidationError, match="ポリシーが空です"):
                    await task._execute_task(
                        policy_yaml_content="",
                        credentials_data={},
                        cloud_provider="aws"
                    )

    @pytest.mark.asyncio
    async def test_temp_dir_cleaned_in_finally(self, task):
        """NCMT-006: 例外発生時も finally で一時ディレクトリが削除される

        main_task.py:116-123 の finally ブロックをカバー。
        """
        # Arrange
        mock_creds = MagicMock()
        task.credential_processor.parse_credentials_payload = AsyncMock(return_value=mock_creds)
        task.scan_coordinator.execute_multi_region_custodian_scan = AsyncMock(
            side_effect=RuntimeError("スキャン失敗")
        )

        with patch(f"{MODULE}.tempfile.mkdtemp", return_value="/tmp/test-dir"):
            with patch("shutil.rmtree") as mock_rmtree:
                # Act
                with pytest.raises(RuntimeError):
                    await task._execute_task(
                        policy_yaml_content="policies: []",
                        credentials_data={},
                        cloud_provider="aws"
                    )

        # Assert
        mock_rmtree.assert_called_once_with("/tmp/test-dir")

    @pytest.mark.asyncio
    async def test_temp_dir_cleanup_failure_logs_warning(self, task):
        """NCMT-007: 一時ディレクトリ削除失敗時に warning ログ

        main_task.py:122-123 の rmtree 例外キャッチをカバー。
        """
        # Arrange
        mock_creds = MagicMock()
        task.credential_processor.parse_credentials_payload = AsyncMock(return_value=mock_creds)
        task.scan_coordinator.execute_multi_region_custodian_scan = AsyncMock(return_value={})

        with patch.object(task, '_process_scan_results', new_callable=AsyncMock, return_value={}):
            with patch(f"{MODULE}.tempfile.mkdtemp", return_value="/tmp/test"):
                with patch("shutil.rmtree", side_effect=OSError("権限不足")):
                    # Act
                    await task._execute_task(
                        policy_yaml_content="x", credentials_data={}, cloud_provider="aws"
                    )

        # Assert
        task.logger.warning.assert_called()
        assert "一時ディレクトリ削除に失敗" in task.logger.warning.call_args[0][0]
```

### 2.4 _process_scan_results テスト

```python
class TestProcessScanResults:
    """_process_scan_results の3分岐テスト"""

    @pytest.fixture
    def task(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.StatusTracker"), \
             patch(f"{MODULE}.CredentialProcessor"), \
             patch(f"{MODULE}.ScanCoordinator"), \
             patch(f"{MODULE}.ResultProcessor"), \
             patch(f"{MODULE}.ErrorHistoryHandler"):
            from app.jobs.tasks.new_custodian_scan.main_task import NewCustodianScanTask
            instance = NewCustodianScanTask("test-job")
        instance.logger = MagicMock()
        return instance

    @pytest.mark.asyncio
    async def test_fatal_error_path(self, task):
        """NCMT-008: return_code=1 で _handle_fatal_error が呼ばれる

        main_task.py:138-139 の has_fatal_error 分岐をカバー。
        """
        # Arrange
        scan_results = {"return_code": 1, "violations_count": 0, "scan_metadata": {}}
        task.result_processor.create_scan_summary.return_value = {"status": "failed"}

        with patch.object(task, '_handle_fatal_error') as mock_fatal, \
             patch.object(task, '_save_scan_history_v2', new_callable=AsyncMock):
            # Act
            await task._process_scan_results(scan_results, "aws")

        # Assert
        mock_fatal.assert_called_once()

    @pytest.mark.asyncio
    async def test_violations_path(self, task):
        """NCMT-009: violations_count > 0 で _store_violations が呼ばれる

        main_task.py:140-141 の elif 分岐をカバー。
        """
        # Arrange
        scan_results = {"return_code": 0, "violations_count": 5, "scan_metadata": {}}
        task.result_processor.create_scan_summary.return_value = {}

        with patch.object(task, '_store_violations_to_opensearch',
                          new_callable=AsyncMock) as mock_store, \
             patch.object(task, '_save_scan_history_v2', new_callable=AsyncMock):
            # Act
            await task._process_scan_results(scan_results, "aws")

        # Assert
        mock_store.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_no_violations_path(self, task):
        """NCMT-010: 違反なしで OpenSearch 保存スキップ

        main_task.py:142-145 の else 分岐をカバー。
        """
        # Arrange
        scan_results = {"return_code": 0, "violations_count": 0, "scan_metadata": {}}
        task.result_processor.create_scan_summary.return_value = {}

        with patch.object(task, '_save_scan_history_v2', new_callable=AsyncMock):
            # Act
            await task._process_scan_results(scan_results, "aws")

        # Assert
        scan_metadata = scan_results["scan_metadata"]
        assert scan_metadata["has_ai_summary"] is False
        assert scan_metadata["no_violations_detected"] is True
```

### 2.5 _handle_fatal_error テスト

```python
class TestHandleFatalError:
    """_handle_fatal_error のメタデータ設定テスト"""

    @pytest.fixture
    def task(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.StatusTracker"), \
             patch(f"{MODULE}.CredentialProcessor"), \
             patch(f"{MODULE}.ScanCoordinator"), \
             patch(f"{MODULE}.ResultProcessor"), \
             patch(f"{MODULE}.ErrorHistoryHandler"):
            from app.jobs.tasks.new_custodian_scan.main_task import NewCustodianScanTask
            instance = NewCustodianScanTask("test-job")
        instance.logger = MagicMock()
        return instance

    def test_sets_metadata_flags(self, task):
        """NCMT-011: 致命的エラー時に4つのメタデータフラグを設定

        main_task.py:160-166 の全フラグ設定をカバー。
        """
        # Arrange
        scan_metadata = {}

        # Act
        task._handle_fatal_error(scan_metadata)

        # Assert
        assert scan_metadata["opensearch_store_success"] is False
        assert scan_metadata["opensearch_store_skipped_reason"] == "fatal_error_detected"
        assert scan_metadata["has_ai_summary"] is False
        assert scan_metadata["fatal_error_detected"] is True
```

### 2.6 _store_violations_to_opensearch テスト

```python
class TestStoreViolationsToOpensearch:
    """_store_violations_to_opensearch のテスト"""

    @pytest.fixture
    def task(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.StatusTracker"), \
             patch(f"{MODULE}.CredentialProcessor"), \
             patch(f"{MODULE}.ScanCoordinator"), \
             patch(f"{MODULE}.ResultProcessor"), \
             patch(f"{MODULE}.ErrorHistoryHandler"):
            from app.jobs.tasks.new_custodian_scan.main_task import NewCustodianScanTask
            instance = NewCustodianScanTask("test-job")
        instance.logger = MagicMock()
        return instance

    @pytest.mark.asyncio
    async def test_success_flow(self, task):
        """NCMT-012: 正常時に stored_count をメタデータに設定

        main_task.py:182-196 の成功パスをカバー。
        """
        # Arrange
        task.result_processor.store_multi_region_results_to_opensearch = AsyncMock(return_value=3)
        scan_results = {"violations_count": 5, "region_results": [], "custodian_output_dir": "/tmp"}
        scan_metadata = {}

        with patch.object(task, '_generate_and_store_ai_summary', new_callable=AsyncMock):
            # Act
            await task._store_violations_to_opensearch(scan_results, scan_metadata, "aws")

        # Assert
        assert scan_metadata["opensearch_stored_count"] == 3
        assert scan_metadata["opensearch_store_success"] is True

    @pytest.mark.asyncio
    async def test_exception_caught(self, task):
        """NCMT-013: 例外キャッチでメタデータにエラー情報設定

        main_task.py:198-201 の except 分岐をカバー。
        """
        # Arrange
        task.result_processor.store_multi_region_results_to_opensearch = AsyncMock(
            side_effect=RuntimeError("保存失敗")
        )
        scan_results = {"violations_count": 5, "region_results": [], "custodian_output_dir": "/tmp"}
        scan_metadata = {}

        # Act
        await task._store_violations_to_opensearch(scan_results, scan_metadata, "aws")

        # Assert
        assert scan_metadata["opensearch_store_success"] is False
        assert "保存失敗" in scan_metadata["opensearch_store_error"]

    @pytest.mark.asyncio
    async def test_stored_count_zero(self, task):
        """NCMT-027: stored_count=0 で opensearch_store_success=False

        main_task.py:191 の stored_count > 0 が False になる分岐をカバー。
        """
        # Arrange
        task.result_processor.store_multi_region_results_to_opensearch = AsyncMock(return_value=0)
        scan_results = {"violations_count": 5, "region_results": [], "custodian_output_dir": "/tmp"}
        scan_metadata = {}

        with patch.object(task, '_generate_and_store_ai_summary', new_callable=AsyncMock):
            # Act
            await task._store_violations_to_opensearch(scan_results, scan_metadata, "aws")

        # Assert
        assert scan_metadata["opensearch_stored_count"] == 0
        assert scan_metadata["opensearch_store_success"] is False
```

### 2.7 _save_scan_history_v2 テスト

```python
class TestSaveScanHistoryV2:
    """_save_scan_history_v2 の分岐テスト"""

    @pytest.fixture
    def task(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.StatusTracker"), \
             patch(f"{MODULE}.CredentialProcessor"), \
             patch(f"{MODULE}.ScanCoordinator"), \
             patch(f"{MODULE}.ResultProcessor"), \
             patch(f"{MODULE}.ErrorHistoryHandler"):
            from app.jobs.tasks.new_custodian_scan.main_task import NewCustodianScanTask
            instance = NewCustodianScanTask("test-job")
        instance.logger = MagicMock()
        return instance

    @pytest.mark.asyncio
    async def test_success_path(self, task):
        """NCMT-014: 保存成功で history_v2_stored=True

        main_task.py:238-240 の history_saved=True 分岐をカバー。
        """
        # Arrange
        scan_results = {"custodian_output_dir": "/tmp/output", "region_results": []}
        scan_metadata = {}

        with patch("app.jobs.utils.custodian_output.store_scan_history_v2",
                   new_callable=AsyncMock, return_value=True):
            # Act
            await task._save_scan_history_v2(scan_results, scan_metadata, "aws")

        # Assert
        assert scan_metadata["history_v2_stored"] is True

    @pytest.mark.asyncio
    async def test_empty_dir_skips(self, task):
        """NCMT-015: custodian_output_dir 空文字列でスキップ

        main_task.py:215-218 の not custodian_output_dir 分岐をカバー。
        """
        # Arrange
        scan_results = {"custodian_output_dir": ""}
        scan_metadata = {}

        # Act
        await task._save_scan_history_v2(scan_results, scan_metadata, "aws")

        # Assert
        assert scan_metadata["history_v2_stored"] is False
        task.logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_includes_aggregated_statistics(self, task):
        """NCMT-016: aggregated_scan_statistics を enhanced_metadata に含む

        main_task.py:227-229 の aggregated_scan_statistics 条件をカバー。
        """
        # Arrange
        scan_results = {
            "custodian_output_dir": "/tmp/output",
            "region_results": [],
            "aggregated_scan_statistics": {"total_resources": 100}
        }
        scan_metadata = {}

        with patch("app.jobs.utils.custodian_output.store_scan_history_v2",
                   new_callable=AsyncMock, return_value=True) as mock_store:
            # Act
            await task._save_scan_history_v2(scan_results, scan_metadata, "aws")

        # Assert
        call_kwargs = mock_store.call_args[1]
        assert "aggregated_scan_statistics" in call_kwargs["scan_metadata"]

    @pytest.mark.asyncio
    async def test_save_returns_false(self, task):
        """NCMT-017: store_scan_history_v2 が False を返す場合

        main_task.py:241-243 の else 分岐をカバー。
        """
        # Arrange
        scan_results = {"custodian_output_dir": "/tmp/output", "region_results": []}
        scan_metadata = {}

        with patch("app.jobs.utils.custodian_output.store_scan_history_v2",
                   new_callable=AsyncMock, return_value=False):
            # Act
            await task._save_scan_history_v2(scan_results, scan_metadata, "aws")

        # Assert
        assert scan_metadata["history_v2_stored"] is False
        task.logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_exception_caught(self, task):
        """NCMT-018: 例外キャッチで error ログ

        main_task.py:245-247 の except 分岐をカバー。
        """
        # Arrange
        scan_results = {"custodian_output_dir": "/tmp/output", "region_results": []}
        scan_metadata = {}

        with patch("app.jobs.utils.custodian_output.store_scan_history_v2",
                   new_callable=AsyncMock, side_effect=RuntimeError("DB接続エラー")):
            # Act
            await task._save_scan_history_v2(scan_results, scan_metadata, "aws")

        # Assert
        assert scan_metadata["history_v2_stored"] is False
        task.logger.error.assert_called()
```

### 2.8 _handle_error テスト

```python
class TestHandleError:
    """_handle_error の委譲テスト"""

    @pytest.fixture
    def task(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.StatusTracker"), \
             patch(f"{MODULE}.CredentialProcessor"), \
             patch(f"{MODULE}.ScanCoordinator"), \
             patch(f"{MODULE}.ResultProcessor"), \
             patch(f"{MODULE}.ErrorHistoryHandler"):
            from app.jobs.tasks.new_custodian_scan.main_task import NewCustodianScanTask
            instance = NewCustodianScanTask("test-job")
        instance.logger = MagicMock()
        return instance

    @pytest.mark.asyncio
    async def test_delegates_to_handler_and_super(self, task):
        """NCMT-019: error_history_handler に委譲し、super()._handle_error を呼ぶ

        main_task.py:249-268 の正常パスをカバー。
        """
        # Arrange
        error = RuntimeError("テストエラー")
        task.error_history_handler.save_error_to_history = AsyncMock()

        from app.jobs.tasks.base_task import BaseTask
        with patch.object(BaseTask, '_handle_error', new_callable=AsyncMock) as mock_super:
            # Act
            await task._handle_error(error, cloud_provider="aws", initiated_by_user="admin")

        # Assert
        task.error_history_handler.save_error_to_history.assert_awaited_once()
        mock_super.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_history_save_exception_still_calls_super(self, task):
        """NCMT-020: 履歴保存例外でも super()._handle_error は呼ばれる

        main_task.py:264-265 の except 分岐をカバー。
        """
        # Arrange
        error = RuntimeError("テストエラー")
        task.error_history_handler.save_error_to_history = AsyncMock(
            side_effect=Exception("保存失敗")
        )

        from app.jobs.tasks.base_task import BaseTask
        with patch.object(BaseTask, '_handle_error', new_callable=AsyncMock) as mock_super:
            # Act
            await task._handle_error(error, cloud_provider="aws")

        # Assert
        task.logger.error.assert_called()
        assert "エラー履歴保存に失敗" in task.logger.error.call_args[0][0]
        mock_super.assert_awaited_once()
```

### 2.9 _generate_and_store_ai_summary テスト

```python
class TestGenerateAndStoreAiSummary:
    """_generate_and_store_ai_summary の3分岐テスト"""

    @pytest.fixture
    def task(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.StatusTracker"), \
             patch(f"{MODULE}.CredentialProcessor"), \
             patch(f"{MODULE}.ScanCoordinator"), \
             patch(f"{MODULE}.ResultProcessor"), \
             patch(f"{MODULE}.ErrorHistoryHandler"):
            from app.jobs.tasks.new_custodian_scan.main_task import NewCustodianScanTask
            instance = NewCustodianScanTask("test-job")
        instance.logger = MagicMock()
        return instance

    @pytest.mark.asyncio
    async def test_success(self, task):
        """NCMT-021: サマリー生成成功で has_ai_summary=True

        main_task.py:280-284 の成功分岐をカバー。
        """
        # Arrange
        scan_metadata = {}
        mock_summary = {"total_violations": 10}

        with patch("app.jobs.utils.summary_generation.generate_scan_summary",
                   new_callable=AsyncMock, return_value=mock_summary):
            # Act
            await task._generate_and_store_ai_summary(scan_metadata)

        # Assert
        assert scan_metadata["has_ai_summary"] is True
        assert scan_metadata["ai_scan_summary"] == mock_summary
        assert scan_metadata["ai_summary_type"] == "multi_region_scan"

    @pytest.mark.asyncio
    async def test_returns_none(self, task):
        """NCMT-022: サマリー生成が None を返す場合

        main_task.py:285-288 の else 分岐をカバー。
        """
        # Arrange
        scan_metadata = {}

        with patch("app.jobs.utils.summary_generation.generate_scan_summary",
                   new_callable=AsyncMock, return_value=None):
            # Act
            await task._generate_and_store_ai_summary(scan_metadata)

        # Assert
        assert scan_metadata["has_ai_summary"] is False
        assert "失敗" in scan_metadata["ai_summary_error"]

    @pytest.mark.asyncio
    async def test_exception_caught(self, task):
        """NCMT-023: 例外キャッチで error ログ

        main_task.py:290-293 の except 分岐をカバー。
        """
        # Arrange
        scan_metadata = {}

        with patch("app.jobs.utils.summary_generation.generate_scan_summary",
                   new_callable=AsyncMock, side_effect=RuntimeError("LLM接続エラー")):
            # Act
            await task._generate_and_store_ai_summary(scan_metadata)

        # Assert
        assert scan_metadata["has_ai_summary"] is False
        assert "LLM接続エラー" in scan_metadata["ai_summary_error"]
```

### 2.10 _update_scan_history テスト

```python
class TestUpdateScanHistory:
    """_update_scan_history のテスト"""

    @pytest.fixture
    def task(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.StatusTracker"), \
             patch(f"{MODULE}.CredentialProcessor"), \
             patch(f"{MODULE}.ScanCoordinator"), \
             patch(f"{MODULE}.ResultProcessor"), \
             patch(f"{MODULE}.ErrorHistoryHandler"):
            from app.jobs.tasks.new_custodian_scan.main_task import NewCustodianScanTask
            instance = NewCustodianScanTask("test-job")
        instance.logger = MagicMock()
        return instance

    @pytest.mark.asyncio
    async def test_update_success(self, task):
        """NCMT-024: 更新成功で client.update が呼ばれる

        main_task.py:317-323 の正常パスをカバー。
        """
        # Arrange
        mock_client = AsyncMock()
        summary_data = {"message": "テスト", "summary_data": {}}

        with patch(f"{MODULE}.get_opensearch_client", new_callable=AsyncMock,
                   return_value=mock_client):
            with patch(f"{MODULE}.datetime") as mock_dt:
                mock_dt.now.return_value.isoformat.return_value = "2025-01-01T00:00:00+00:00"
                # Act
                await task._update_scan_history(summary_data)

        # Assert
        mock_client.update.assert_awaited_once()
        call_kwargs = mock_client.update.call_args[1]
        assert call_kwargs["index"] == "cspm-scan-history-v2"
        assert call_kwargs["id"] == "test-job"

    @pytest.mark.asyncio
    async def test_client_none_skips(self, task):
        """NCMT-025: クライアント None で早期 return

        main_task.py:300-302 の not os_client 分岐をカバー。
        """
        # Arrange
        with patch(f"{MODULE}.get_opensearch_client", new_callable=AsyncMock,
                   return_value=None):
            # Act
            await task._update_scan_history({"message": "テスト"})

        # Assert
        task.logger.warning.assert_called()
        assert "OpenSearchクライアント" in task.logger.warning.call_args[0][0]
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| NCMT-E01 | _update_scan_history document_missing → 新規作成 | update 例外 | client.index で新規作成 |
| NCMT-E02 | _update_scan_history 非 document_missing → 外側 catch | update 例外 | warning ログ |
| NCMT-E03 | _execute_task kwargs 欠損でデフォルト値使用 | 空の kwargs | "undefined" 等のデフォルト |

### 3.1 異常系テスト

```python
class TestMainTaskErrors:
    """異常入力・エラー回復のテスト"""

    @pytest.fixture
    def task(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.StatusTracker"), \
             patch(f"{MODULE}.CredentialProcessor"), \
             patch(f"{MODULE}.ScanCoordinator"), \
             patch(f"{MODULE}.ResultProcessor"), \
             patch(f"{MODULE}.ErrorHistoryHandler"):
            from app.jobs.tasks.new_custodian_scan.main_task import NewCustodianScanTask
            instance = NewCustodianScanTask("test-job")
        instance.logger = MagicMock()
        return instance

    @pytest.mark.asyncio
    async def test_update_document_missing_creates_new(self, task):
        """NCMT-E01: document_missing_exception で新規ドキュメント作成

        main_task.py:324-341 の document_missing_exception 分岐をカバー。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_client.update.side_effect = Exception("document_missing_exception")

        with patch(f"{MODULE}.get_opensearch_client", new_callable=AsyncMock,
                   return_value=mock_client):
            with patch(f"{MODULE}.datetime") as mock_dt:
                mock_dt.now.return_value.isoformat.return_value = "2025-01-01T00:00:00+00:00"
                # Act
                await task._update_scan_history({"message": "テスト"})

        # Assert
        mock_client.index.assert_awaited_once()
        call_kwargs = mock_client.index.call_args[1]
        assert call_kwargs["body"]["job_id"] == "test-job"

    @pytest.mark.asyncio
    async def test_update_non_document_missing_caught(self, task):
        """NCMT-E02: document_missing 以外のエラーは外側 catch で warning

        main_task.py:342-344 の else → raise → L348-349 の外側 except をカバー。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_client.update.side_effect = Exception("connection_timeout")

        with patch(f"{MODULE}.get_opensearch_client", new_callable=AsyncMock,
                   return_value=mock_client):
            with patch(f"{MODULE}.datetime") as mock_dt:
                mock_dt.now.return_value.isoformat.return_value = "2025-01-01T00:00:00+00:00"
                # Act（例外が伝播しないことを検証）
                await task._update_scan_history({"message": "テスト"})

        # Assert
        task.logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_execute_task_kwargs_defaults(self, task):
        """NCMT-E03: kwargs 欠損時にデフォルト値が使用される

        main_task.py:65-66 の .get() デフォルト値をカバー。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.authType = "accessKey"
        mock_creds.scanRegions = []
        task.credential_processor.parse_credentials_payload = AsyncMock(return_value=mock_creds)
        task.scan_coordinator.execute_multi_region_custodian_scan = AsyncMock(return_value={})

        with patch.object(task, '_process_scan_results', new_callable=AsyncMock, return_value={}):
            with patch(f"{MODULE}.tempfile.mkdtemp", return_value="/tmp/t"):
                with patch("shutil.rmtree"):
                    # Act
                    await task._execute_task(
                        policy_yaml_content="x",
                        credentials_data={},
                        cloud_provider="aws"
                        # initiated_by_user, scan_trigger_type 省略
                    )

        # Assert（デフォルト値が scan_coordinator に渡されたことを検証）
        call_args = task.scan_coordinator.execute_multi_region_custodian_scan.call_args
        # 位置引数: (temp_dir, policy_yaml_content, parsed_creds, cloud_provider,
        #            initiated_by_user, scan_trigger_type, preset_id, preset_name)
        assert call_args[0][4] == "undefined"  # initiated_by_user デフォルト
        assert call_args[0][5] == "undefined"  # scan_trigger_type デフォルト
        assert call_args[0][6] is None  # preset_id デフォルト
        assert call_args[0][7] is None  # preset_name デフォルト
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| NCMT-SEC-01 | エラーログが所定フォーマットで出力 | 各 except ブロック | プレフィックス付き `str(e)` 形式 |
| NCMT-SEC-02 | _handle_error が内部例外を伝播させない | save 例外 | グレースフル失敗 |
| NCMT-SEC-03 | 一時ディレクトリが例外時にも削除される | スキャン例外 | finally で削除 |

### 4.1 セキュリティテスト

```python
@pytest.mark.security
class TestMainTaskSecurity:
    """セキュリティ関連テスト"""

    @pytest.fixture
    def task(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.StatusTracker"), \
             patch(f"{MODULE}.CredentialProcessor"), \
             patch(f"{MODULE}.ScanCoordinator"), \
             patch(f"{MODULE}.ResultProcessor"), \
             patch(f"{MODULE}.ErrorHistoryHandler"):
            from app.jobs.tasks.new_custodian_scan.main_task import NewCustodianScanTask
            instance = NewCustodianScanTask("test-job")
        instance.logger = MagicMock()
        return instance

    @pytest.mark.asyncio
    async def test_error_log_uses_formatted_prefix(self, task):
        """NCMT-SEC-01: エラーログが所定プレフィックス + str(e) 形式で出力される

        main_task.py:246 の logger.error が f"history_v2保存エラー: {str(e)}" 形式で
        出力されることを検証。str(e) の内容自体は実装が制御するため、
        フォーマットの一貫性のみ確認する。
        """
        # Arrange
        scan_results = {"custodian_output_dir": "/tmp/output", "region_results": []}
        scan_metadata = {}
        error_with_traceback = RuntimeError("テストエラー\nFile \"secret.py\", line 1")

        with patch("app.jobs.utils.custodian_output.store_scan_history_v2",
                   new_callable=AsyncMock, side_effect=error_with_traceback):
            # Act
            await task._save_scan_history_v2(scan_results, scan_metadata, "aws")

        # Assert
        error_log = task.logger.error.call_args[0][0]
        # str(e) にはスタックトレースの "File" 行が含まれるが、
        # logger.error の第1引数（メッセージ文字列）内のフォーマットを検証
        assert "history_v2保存エラー:" in error_log

    @pytest.mark.asyncio
    async def test_handle_error_does_not_propagate(self, task):
        """NCMT-SEC-02: _handle_error の内部例外が呼び出し元に伝播しない

        main_task.py:252-265 の try/except で
        履歴保存の失敗がスキャン処理全体を停止させないことを検証。
        """
        # Arrange
        error = RuntimeError("テスト")
        task.error_history_handler.save_error_to_history = AsyncMock(
            side_effect=Exception("致命的保存エラー")
        )

        from app.jobs.tasks.base_task import BaseTask
        with patch.object(BaseTask, '_handle_error', new_callable=AsyncMock):
            # Act（例外が伝播しないことを検証）
            await task._handle_error(error, cloud_provider="aws")

        # Assert
        # ここに到達すること自体が、例外が伝播しなかった証拠
        task.logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_temp_dir_always_cleaned(self, task):
        """NCMT-SEC-03: 一時ディレクトリが例外発生時にも必ず削除される

        main_task.py:116-123 の finally ブロックにより、
        スキャンデータの一時ファイルが残存しないことを検証。
        """
        # Arrange
        mock_creds = MagicMock()
        task.credential_processor.parse_credentials_payload = AsyncMock(return_value=mock_creds)
        task.scan_coordinator.execute_multi_region_custodian_scan = AsyncMock(
            side_effect=Exception("致命的エラー")
        )

        with patch(f"{MODULE}.tempfile.mkdtemp", return_value="/tmp/sensitive-data"):
            with patch("shutil.rmtree") as mock_rmtree:
                # Act
                with pytest.raises(Exception):
                    await task._execute_task(
                        policy_yaml_content="x", credentials_data={}, cloud_provider="aws"
                    )

        # Assert
        mock_rmtree.assert_called_once_with("/tmp/sensitive-data")
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `task` | 全依存をモック化した NewCustodianScanTask（各テストクラス内で定義） | function | No |

### 共通フィクスチャ定義

```python
# test/unit/jobs/tasks/new_custodian_scan/conftest.py に追加（必要に応じて）
#
# main_task はモジュールレベルの状態を持たないため、
# autouse のモジュールリセットフィクスチャは不要。
#
# task フィクスチャの共通パターン:
#   MODULE = "app.jobs.tasks.new_custodian_scan.main_task"
#   with patch(f"{MODULE}.TaskLogger"), \
#        patch(f"{MODULE}.StatusTracker"), \
#        patch(f"{MODULE}.CredentialProcessor"), \
#        patch(f"{MODULE}.ScanCoordinator"), \
#        patch(f"{MODULE}.ResultProcessor"), \
#        patch(f"{MODULE}.ErrorHistoryHandler"):
#       instance = NewCustodianScanTask("test-job")
#   instance.logger = MagicMock()  # アサーション用に差し替え
#
# 注: BaseTask.__init__ は job_id と start_time を設定するのみ。
# パッチ不要だが、config 読み込みが走る場合は REQUIRED_ENV_VARS が必要。
```

---

## 6. テスト実行例

```bash
# main_task テストのみ実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_main_task.py -v

# 特定のテストクラスのみ実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_main_task.py::TestExecuteTask -v

# カバレッジ付きで実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_main_task.py \
  --cov=app.jobs.tasks.new_custodian_scan.main_task \
  --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_main_task.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 27 | NCMT-001 〜 NCMT-027 |
| 異常系 | 3 | NCMT-E01 〜 NCMT-E03 |
| セキュリティ | 3 | NCMT-SEC-01 〜 NCMT-SEC-03 |
| **合計** | **33** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestGetCustodianVersion` | NCMT-001〜002, 026 | 3 |
| `TestNewCustodianScanTaskInit` | NCMT-003 | 1 |
| `TestExecuteTask` | NCMT-004〜007 | 4 |
| `TestProcessScanResults` | NCMT-008〜010 | 3 |
| `TestHandleFatalError` | NCMT-011 | 1 |
| `TestStoreViolationsToOpensearch` | NCMT-012〜013, 027 | 3 |
| `TestSaveScanHistoryV2` | NCMT-014〜018 | 5 |
| `TestHandleError` | NCMT-019〜020 | 2 |
| `TestGenerateAndStoreAiSummary` | NCMT-021〜023 | 3 |
| `TestUpdateScanHistory` | NCMT-024〜025 | 2 |
| `TestMainTaskErrors` | NCMT-E01〜E03 | 3 |
| `TestMainTaskSecurity` | NCMT-SEC-01〜SEC-03 | 3 |

### 実装失敗が予想されるテスト

現時点で失敗が予想されるテストはありません。

> 全メソッドの依存をモックするため、実装の内部ロジックのみを検証。外部サービスの状態に依存しない安定したテスト設計。

### 注意事項

- 全 async メソッドのテストに `pytest-asyncio` パッケージが必要
- `--strict-markers` 運用時は `@pytest.mark.security` を `pyproject.toml` に登録
- `_save_scan_history_v2` と `_generate_and_store_ai_summary` は遅延 import を使用するため、patch 先はモジュールパスではなく実際の定義元を指定
- `BaseTask._handle_error` のモックには `patch.object(BaseTask, '_handle_error')` を使用
- `shutil` は L119 で関数内ローカル import のため `patch("shutil.rmtree")` で patch（`f"{MODULE}.shutil.rmtree"` ではなく）

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `_execute_task` は多数の内部メソッドを呼ぶため、単体テストではフロー全体を通す統合的テストが必要 | テスト準備が複雑になる | `patch.object` で内部メソッドをモックし、フロー制御のみを検証する |
| 2 | 遅延 import（`store_scan_history_v2`, `generate_scan_summary`）の patch 先はモジュール定義元（`app.jobs.utils.*`）を指定する必要がある | patch 先を間違えるとモックが効かない | テストコード内にコメントで正しい patch 先を明記 |
| 4 | `shutil` は L119 で関数内ローカル import されるため、patch 先は `"shutil.rmtree"` を使用する（`f"{MODULE}.shutil.rmtree"` は不可） | patch 先を間違えるとモックが効かない | `patch("shutil.rmtree")` を使用 |
| 3 | `BaseTask` の `execute` メソッド（L22-36）は本テストでは直接テストしない | `_execute_task` → `execute` の統合フローは未検証 | 統合テストで `execute` 経由のフローを検証 |
