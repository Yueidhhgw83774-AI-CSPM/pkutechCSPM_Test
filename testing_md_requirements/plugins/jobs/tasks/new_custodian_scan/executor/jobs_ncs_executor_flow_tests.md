# jobs/tasks/new_custodian_scan/executor 実行フロー系 テストケース

## 1. 概要

`executor/` サブディレクトリの実行フロー系3ファイル（`main.py`, `subprocess_runner.py`, `statistics_analyzer.py`）をまとめたテスト仕様書。Custodianスキャンの実行エンジン・サブプロセス制御・統計抽出を担う。

### 1.1 対象クラス

| クラス | ファイル | 行数 | 責務 |
|--------|---------|------|------|
| `CustodianExecutor` | `main.py` | 191 | 単一リージョンスキャン実行のオーケストレーション |
| `SubprocessRunner` | `subprocess_runner.py` | 168 | 非同期subprocess実行・ドライラン・タイムアウト制御 |
| `StatisticsAnalyzer` | `statistics_analyzer.py` | 215 | ログ正規表現解析・JSONファイル解析・統計計算 |

### 1.2 カバレッジ目標: 85%

> **注記**: `CustodianExecutor.execute_single_region_scan` は多段分岐を持つ複雑なオーケストレーションメソッド。`StatisticsAnalyzer.extract_scan_statistics_from_log` は5種の正規表現パターンを持つ。pytest-asyncio が必要。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象1 | `app/jobs/tasks/new_custodian_scan/executor/main.py` |
| テスト対象2 | `app/jobs/tasks/new_custodian_scan/executor/subprocess_runner.py` |
| テスト対象3 | `app/jobs/tasks/new_custodian_scan/executor/statistics_analyzer.py` |
| テストコード | `test/unit/jobs/tasks/new_custodian_scan/executor/test_executor_flow.py` |

### 1.4 補足情報

#### 依存関係

```
main.py (CustodianExecutor)
  ──→ CustodianCommandBuilder（コマンド構築）
  ──→ ResultProcessor（結果処理）
  ──→ CustodianLogAnalyzer（ログ解析）
  ──→ ErrorDetector（エラー検出）
  ──→ SecuritySanitizer（セキュリティサニタイズ）
  ──→ StatisticsAnalyzer（統計抽出）
  ──→ SubprocessRunner（サブプロセス実行）
  ──→ count_violations_from_custodian_output（従来版違反カウント）
  ──→ TaskLogger（ログ）

subprocess_runner.py (SubprocessRunner)
  ──→ SecuritySanitizer（環境変数サニタイズ）
  ──→ TaskLogger（ログ）
  ──→ asyncio（create_subprocess_exec, wait_for, sleep）

statistics_analyzer.py (StatisticsAnalyzer)
  ──→ TaskLogger（ログ）
  ──→ os, json, re（標準ライブラリ）
```

#### テスト戦略

| テストカテゴリ | 手法 |
|--------------|------|
| CustodianExecutor | 7コンポーネントをpatch、オーケストレーション分岐を検証 |
| SubprocessRunner | 正常系: create_subprocess_execのみAsyncMock化（wait_forは実asyncio）。タイムアウト系: wait_forもAsyncMock化 |
| StatisticsAnalyzer | 正規表現パターンごとにログ行を入力、parse_output_filesはtmp_pathを使用 |

#### 主要分岐マップ

| クラス | メソッド | 行番号 | 条件 | 分岐数 |
|--------|---------|--------|------|--------|
| CustodianExecutor | `execute_single_region_scan` | L103, L122, L144, L151 | バリデーションエラー、実行エラー、違反カウント不一致、total_scanned>0 | 5 |
| SubprocessRunner | `run_custodian_subprocess` | L60, L79, L91 | ドライラン、タイムアウト、例外 | 3 |
| SubprocessRunner | `_log_command_details` | L118, L122 | 安全でないキー、機密パターン | 3 |
| StatisticsAnalyzer | `extract_scan_statistics_from_log` | L66, L77, L88, L99, L106, L115 | 5種の正規表現パターン、コンプライアンス率計算 | 7 |
| StatisticsAnalyzer | `parse_output_files` | L176, L192, L199, L204, L206 | ディレクトリ不存在、リスト/dict(resources)/dict(その他)/不明形式 | 5 |

---

## 2. 正常系テストケース

### CustodianExecutor (CEXE)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CEXE-001 | 初期化時に全コンポーネントが生成される | job_id, dry_run=False | 7コンポーネント初期化、ドライランログなし |
| CEXE-002 | ドライランモードでログ出力 | dry_run_mode=True | ドライランログ出力 |
| CEXE-003 | 正常スキャン実行（エラーなし、違反一致） | 正常コマンド結果 | result含むscan_statistics, execution_duration等 |
| CEXE-004 | バリデーションエラー検出でエラー結果返却 | validation_error.has_error=True | エラー結果にvalidation_error含む |
| CEXE-005 | 実行ステータスエラーで統計初期化 | execution_status.has_error=True | scan_statistics.violations=0, error=True |
| CEXE-006 | 違反カウント不一致でmax採用 | legacy=5, new=3 | violations=5, warningログ出力 |
| CEXE-007 | total_scanned=0でコンプライアンス率再計算スキップ | total_scanned=0 | compliance_rate未変更 |

### SubprocessRunner (SRUN)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| SRUN-001 | 初期化時にSecuritySanitizerが生成される | job_id, dry_run=False | security_sanitizer初期化 |
| SRUN-002 | ドライランモードでシミュレーション分岐 | dry_run_mode=True | _simulate_custodian_execution呼び出し |
| SRUN-003 | 正常subprocess実行 | 正常コマンド | stdout, stderr, return_code=0 |
| SRUN-004 | 機密環境変数のマスク | SECRET, TOKEN等を含むキー | 機密キーはマスク分岐に入りsanitize_env_value未呼出（間接確認） |
| SRUN-005 | 安全でないキーのスキップ | 不正なキー名 | warningログ出力（間接確認） |
| SRUN-006 | 非機密値のサニタイズ | 通常の環境変数 | sanitize_env_value呼び出し |
| SRUN-007 | ドライラン実行シミュレーション | コマンドリスト | シミュレートstdout, return_code=0 |

### StatisticsAnalyzer (STAT)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| STAT-001 | 初期化 | job_id | logger初期化 |
| STAT-002 | パターン1: Using cached | "Using cached c7n.resources.ec2.EC2: 100" | total_scanned=100, resource_type="ec2" |
| STAT-003 | パターン2: Filtered from | "Filtered from 100 to 5" | total_scanned=100, violations=5 |
| STAT-004 | パターン3a: matched N resources | "matched 3 resources" | violations=3 |
| STAT-005 | パターン3b: action matched regex | "action mark matched 2 resource" | violations=2 |
| STAT-006 | パターン3c: count:N | "policy:test-policy count:7" | violations=7 |
| STAT-007 | 複合パターン+コンプライアンス率計算 | cached + filtered | total_scanned>0, compliance_rate計算 |
| STAT-008 | マッチなし（total_scanned=0） | パターン不一致行 | total_scanned=0, compliance_rate=0.0 |
| STAT-009 | parse_custodian_output レガシーラッパー | stdout_output | extract_scan_statistics_from_log呼び出し確認+戻り値一致 |
| STAT-010 | parse_output_files ディレクトリ不存在 | 存在しないパス | 0返却 |
| STAT-011 | parse_output_files JSONリスト形式 | [{"id":"r1"}, {"id":"r2"}, {"id":"r3"}, {"id":"r4"}] | violations=4 |
| STAT-012 | parse_output_files JSON dict resources形式 | {"resources": [...]} | resourcesのlen返却 |
| STAT-013 | parse_output_files JSON dict その他 | {"key": "val"} | 0件（ログのみ） |
| STAT-014 | parse_output_files 不明な形式 | "string data" | 0件（ログのみ） |
| STAT-015 | parse_output_files 少数違反ログ出力（境界値: 3件） | リスト形式ちょうど3件 | violations=3, 内容ログ出力 |
| STAT-016 | parse_output_files 非JSONファイルスキップ | .txtファイルのみ | 0返却、JSONのみ処理 |
| STAT-017 | parse_output_files dict+resources非リスト | {"resources": "string"} | 0返却（リスト以外はスキップ） |
| STAT-018 | extract_scan_statistics_from_log matchedの数値パース失敗 | "matched abc resources" | violations加算されない |

### 2.1 CustodianExecutor テスト

```python
# test/unit/jobs/tasks/new_custodian_scan/executor/test_executor_flow.py
import asyncio
import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock

MODULE_MAIN = "app.jobs.tasks.new_custodian_scan.executor.main"
MODULE_SRUN = "app.jobs.tasks.new_custodian_scan.executor.subprocess_runner"
MODULE_STAT = "app.jobs.tasks.new_custodian_scan.executor.statistics_analyzer"


class TestCustodianExecutorInit:
    """CustodianExecutor初期化テスト"""

    def test_init_creates_all_components(self, mock_executor_components):
        """CEXE-001: 初期化時に全コンポーネントが生成される

        main.py:L32-53 の7コンポーネント初期化をカバー。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.executor.main import CustodianExecutor

        # Act
        executor = CustodianExecutor("test-job-id")

        # Assert
        mock_executor_components["CustodianCommandBuilder"].assert_called_once_with("test-job-id")
        mock_executor_components["ResultProcessor"].assert_called_once_with("test-job-id")
        mock_executor_components["ErrorDetector"].assert_called_once_with("test-job-id")
        mock_executor_components["SecuritySanitizer"].assert_called_once_with("test-job-id")
        mock_executor_components["CustodianLogAnalyzer"].assert_called_once_with("test-job-id")
        mock_executor_components["StatisticsAnalyzer"].assert_called_once_with("test-job-id")
        mock_executor_components["SubprocessRunner"].assert_called_once_with("test-job-id", False)
        assert executor.dry_run_mode is False

    def test_init_dry_run_mode_logs(self, mock_executor_components):
        """CEXE-002: ドライランモードでログ出力

        main.py:L55-56 のドライランモード分岐をカバー。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.executor.main import CustodianExecutor

        # Act
        executor = CustodianExecutor("test-job-id", dry_run_mode=True)

        # Assert
        assert executor.dry_run_mode is True
        executor.logger.info.assert_called()
        log_msg = executor.logger.info.call_args[0][0]
        assert "コマンド確認モード" in log_msg


class TestExecuteSingleRegionScan:
    """単一リージョンスキャン実行テスト"""

    @pytest.mark.asyncio
    async def test_normal_execution(self, executor):
        """CEXE-003: 正常スキャン実行（エラーなし、違反一致）

        main.py:L58-181 の正常フロー全体をカバー。
        バリデーションエラーなし、実行エラーなし、legacy==new の分岐。
        """
        # Arrange
        executor.command_builder.build_command_for_region.return_value = (
            ["run", "--region", "us-east-1"], {"AWS_REGION": "us-east-1"},
            "/tmp/policy.yml", "/tmp/output"
        )
        executor.command_builder.get_custodian_command_path.return_value = "/usr/bin/custodian"
        executor.subprocess_runner.run_custodian_subprocess = AsyncMock(
            return_value=(["stdout line"], [], 0)
        )
        executor.error_detector.detect_validation_error.return_value = {"has_error": False}
        executor.error_detector.check_execution_status.return_value = {
            "has_error": False, "error_type": None,
            "policy_errors": [], "missing_resources": []
        }
        executor.statistics_analyzer.extract_scan_statistics_from_log.return_value = {
            "total_scanned": 50, "violations": 3, "compliance_rate": 94.0
        }
        # 従来版と同じ違反数
        with patch(f"{MODULE_MAIN}.count_violations_from_custodian_output", return_value=3):
            executor.result_processor.process_single_region_result.return_value = {
                "region": "us-east-1", "return_code": 0, "violations_count": 3
            }

            # Act
            result = await executor.execute_single_region_scan(
                "/tmp", "policy: ...", {"AWS_ACCESS_KEY": "xxx"},
                "us-east-1", region_index=0
            )

        # Assert
        assert result["region"] == "us-east-1"
        assert "execution_duration" in result
        assert result["region_index"] == 0
        assert result["output_dir"] == "/tmp/output"
        assert result["scan_statistics"]["violations"] == 3

    @pytest.mark.asyncio
    async def test_validation_error_returns_error_result(self, executor):
        """CEXE-004: バリデーションエラー検出でエラー結果返却

        main.py:L103-116 のバリデーションエラー分岐をカバー。
        """
        # Arrange
        executor.command_builder.build_command_for_region.return_value = (
            ["run"], {}, "/tmp/policy.yml", "/tmp/output"
        )
        executor.command_builder.get_custodian_command_path.return_value = "/usr/bin/custodian"
        executor.subprocess_runner.run_custodian_subprocess = AsyncMock(
            return_value=([], ["error"], 1)
        )
        executor.error_detector.detect_validation_error.return_value = {
            "has_error": True, "error_message": "Invalid resource type"
        }
        executor.result_processor.create_error_result.return_value = {
            "region": "us-east-1", "error": True
        }

        # Act
        result = await executor.execute_single_region_scan(
            "/tmp", "policy: ...", {}, "us-east-1"
        )

        # Assert
        assert result["error"] is True
        assert "validation_error" in result
        assert result["validation_error"]["has_error"] is True
        # check_execution_statusは呼ばれない
        executor.error_detector.check_execution_status.assert_not_called()
        # process_single_region_resultも呼ばれない（バリデーションエラーで早期リターン）
        executor.result_processor.process_single_region_result.assert_not_called()

    @pytest.mark.asyncio
    async def test_execution_status_error_initializes_stats(self, executor):
        """CEXE-005: 実行ステータスエラーで統計初期化

        main.py:L122-134 の実行エラー時の統計初期化分岐をカバー。
        """
        # Arrange
        executor.command_builder.build_command_for_region.return_value = (
            ["run"], {}, "/tmp/policy.yml", "/tmp/output"
        )
        executor.command_builder.get_custodian_command_path.return_value = "/usr/bin/custodian"
        executor.subprocess_runner.run_custodian_subprocess = AsyncMock(
            return_value=([], ["error"], 1)
        )
        executor.error_detector.detect_validation_error.return_value = {"has_error": False}
        executor.error_detector.check_execution_status.return_value = {
            "has_error": True, "error_type": "missing_resources",
            "policy_errors": ["policy-1"], "missing_resources": ["resources.json"]
        }
        executor.result_processor.process_single_region_result.return_value = {
            "region": "us-east-1", "return_code": 1
        }

        # Act
        result = await executor.execute_single_region_scan(
            "/tmp", "policy: ...", {}, "us-east-1"
        )

        # Assert
        assert result["scan_statistics"]["total_scanned"] == 0
        assert result["scan_statistics"]["violations"] == 0
        assert result["scan_statistics"]["scan_details"]["error"] is True
        assert result["has_policy_errors"] is True
        # statistics_analyzerは呼ばれない
        executor.statistics_analyzer.extract_scan_statistics_from_log.assert_not_called()

    @pytest.mark.asyncio
    async def test_violations_count_mismatch_uses_max(self, executor):
        """CEXE-006: 違反カウント不一致でmax採用

        main.py:L144-148 の違反カウント比較分岐をカバー。
        legacy > new の場合、legacy値が採用される。
        """
        # Arrange
        executor.command_builder.build_command_for_region.return_value = (
            ["run"], {}, "/tmp/policy.yml", "/tmp/output"
        )
        executor.command_builder.get_custodian_command_path.return_value = "/usr/bin/custodian"
        executor.subprocess_runner.run_custodian_subprocess = AsyncMock(
            return_value=(["stdout"], [], 0)
        )
        executor.error_detector.detect_validation_error.return_value = {"has_error": False}
        executor.error_detector.check_execution_status.return_value = {
            "has_error": False, "error_type": None,
            "policy_errors": [], "missing_resources": []
        }
        # new=3, legacy=5 → max=5
        executor.statistics_analyzer.extract_scan_statistics_from_log.return_value = {
            "total_scanned": 50, "violations": 3, "compliance_rate": 94.0
        }
        with patch(f"{MODULE_MAIN}.count_violations_from_custodian_output", return_value=5):
            executor.result_processor.process_single_region_result.return_value = {
                "region": "us-east-1", "return_code": 0
            }

            # Act
            result = await executor.execute_single_region_scan(
                "/tmp", "policy: ...", {}, "us-east-1"
            )

        # Assert
        # max(5, 3) = 5 が採用される
        assert result["scan_statistics"]["violations"] == 5
        # warningログが出力される
        warning_calls = [c for c in executor.logger.warning.call_args_list
                         if "差異" in str(c)]
        assert len(warning_calls) > 0

    @pytest.mark.asyncio
    async def test_total_scanned_zero_skips_compliance_recalc(self, executor):
        """CEXE-007: total_scanned=0でコンプライアンス率再計算スキップ

        main.py:L151 の total_scanned > 0 条件がFalseとなり、
        コンプライアンス率の再計算ブロック（L152-153）をスキップするケースをカバー。
        """
        # Arrange
        executor.command_builder.build_command_for_region.return_value = (
            ["run"], {}, "/tmp/policy.yml", "/tmp/output"
        )
        executor.command_builder.get_custodian_command_path.return_value = "/usr/bin/custodian"
        executor.subprocess_runner.run_custodian_subprocess = AsyncMock(
            return_value=(["stdout"], [], 0)
        )
        executor.error_detector.detect_validation_error.return_value = {"has_error": False}
        executor.error_detector.check_execution_status.return_value = {
            "has_error": False, "error_type": None,
            "policy_errors": [], "missing_resources": []
        }
        # total_scanned=0 → コンプライアンス率再計算なし
        # 初期値を100.0に設定し、再計算されないことを確認
        executor.statistics_analyzer.extract_scan_statistics_from_log.return_value = {
            "total_scanned": 0, "violations": 0, "compliance_rate": 100.0
        }
        with patch(f"{MODULE_MAIN}.count_violations_from_custodian_output", return_value=0):
            executor.result_processor.process_single_region_result.return_value = {
                "region": "us-east-1", "return_code": 0
            }

            # Act
            result = await executor.execute_single_region_scan(
                "/tmp", "policy: ...", {}, "us-east-1"
            )

        # Assert
        # total_scanned=0のため、compliance_rateは再計算されず初期値100.0のまま
        assert result["scan_statistics"]["total_scanned"] == 0
        assert result["scan_statistics"]["compliance_rate"] == 100.0
```

### 2.2 SubprocessRunner テスト

```python
class TestSubprocessRunnerInit:
    """SubprocessRunner初期化テスト"""

    def test_init_creates_security_sanitizer(self, mock_srun_components):
        """SRUN-001: 初期化時にSecuritySanitizerが生成される

        subprocess_runner.py:L22-33 の初期化をカバー。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.executor.subprocess_runner import SubprocessRunner

        # Act
        runner = SubprocessRunner("test-job-id")

        # Assert
        mock_srun_components["SecuritySanitizer"].assert_called_once_with("test-job-id")
        assert runner.dry_run_mode is False


class TestRunCustodianSubprocess:
    """Custodianサブプロセス実行テスト"""

    @pytest.mark.asyncio
    async def test_dry_run_delegates_to_simulate(self, subprocess_runner):
        """SRUN-002: ドライランモードでシミュレーション分岐

        subprocess_runner.py:L60-61 のドライラン分岐をカバー。
        """
        # Arrange
        subprocess_runner.dry_run_mode = True
        subprocess_runner._simulate_custodian_execution = AsyncMock(
            return_value=(["simulated"], [], 0)
        )

        # Act
        stdout, stderr, rc = await subprocess_runner.run_custodian_subprocess(
            ["custodian", "run"], {"ENV": "val"}, "/tmp/output", "us-east-1"
        )

        # Assert
        assert stdout == ["simulated"]
        assert rc == 0
        subprocess_runner._simulate_custodian_execution.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_normal_subprocess_execution(self, subprocess_runner):
        """SRUN-003: 正常subprocess実行

        subprocess_runner.py:L63-89 の正常実行フローをカバー。
        create_subprocess_execをモックし、communicate()が即座に完了するため
        wait_for（実際のasyncio.wait_for）はタイムアウトせず正常に完了する。
        """
        # Arrange
        mock_process = MagicMock()
        mock_process.communicate = AsyncMock(
            return_value=(b"output line1\noutput line2", b"")
        )
        mock_process.returncode = 0

        with patch(f"{MODULE_SRUN}.asyncio.create_subprocess_exec",
                   new_callable=AsyncMock, return_value=mock_process):
            # Act
            # wait_forは実際のasyncio.wait_forがcommunicate()を待機する
            stdout, stderr, rc = await subprocess_runner.run_custodian_subprocess(
                ["custodian", "run"], {"ENV": "val"}, "/tmp/output", "us-east-1"
            )

        # Assert
        assert rc == 0
        assert len(stdout) == 2
        assert stdout[0] == "output line1"
        mock_process.communicate.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_simulate_execution(self, subprocess_runner):
        """SRUN-007: ドライラン実行シミュレーション

        subprocess_runner.py:L131-168 のシミュレーションをカバー。
        asyncio.sleepをモックして実行時間をスキップ。
        """
        # Arrange
        with patch(f"{MODULE_SRUN}.asyncio.sleep", new_callable=AsyncMock):
            # Act
            stdout, stderr, rc = await subprocess_runner._simulate_custodian_execution(
                ["custodian", "run", "--region", "us-east-1"], "us-east-1"
            )

        # Assert
        assert rc == 0
        assert len(stdout) > 0
        assert any("us-east-1" in line for line in stdout)
        assert stderr == []


class TestLogCommandDetails:
    """コマンド詳細ログテスト"""

    def test_sensitive_env_vars_masked(self, subprocess_runner):
        """SRUN-004: 機密環境変数のマスク

        subprocess_runner.py:L122-123 のSENSITIVE_PATTERNSマッチ分岐をカバー。
        """
        # Arrange
        env = {
            "AWS_SECRET_ACCESS_KEY": "actual-secret-value",
            "AWS_ACCESS_KEY_ID": "AKIAXXXXXXXX",
            "AWS_SESSION_TOKEN": "token123",
            "AWS_REGION": "us-east-1"
        }
        subprocess_runner.security_sanitizer.is_safe_env_key.return_value = True
        subprocess_runner.security_sanitizer.sanitize_env_value.return_value = "us-east-1"

        # Act
        subprocess_runner._log_command_details(
            ["custodian", "run"], env, "/tmp/output", "us-east-1", 600
        )

        # Assert
        # 機密キーはsanitize_env_valueが呼ばれない（マスクされる）
        # 非機密キーのみsanitize_env_valueが呼ばれる
        sanitize_calls = subprocess_runner.security_sanitizer.sanitize_env_value.call_args_list
        sanitized_values = [c[0][0] for c in sanitize_calls]
        assert "actual-secret-value" not in sanitized_values
        assert "AKIAXXXXXXXX" not in sanitized_values

    def test_unsafe_env_key_skipped(self, subprocess_runner):
        """SRUN-005: 安全でないキーのスキップ

        subprocess_runner.py:L118-120 のis_safe_env_key=False分岐をカバー。
        """
        # Arrange
        env = {"NORMAL_KEY": "val", "DANGEROUS\nKEY": "injected"}
        # 最初の呼び出しはTrue、2番目はFalse
        subprocess_runner.security_sanitizer.is_safe_env_key.side_effect = [True, False]
        subprocess_runner.security_sanitizer.sanitize_env_value.return_value = "val"

        # Act
        subprocess_runner._log_command_details(
            ["cmd"], env, "/tmp", "us-east-1", 600
        )

        # Assert
        # 危険なキーに対してwarningログが出力される
        subprocess_runner.logger.warning.assert_called()

    def test_non_sensitive_value_sanitized(self, subprocess_runner):
        """SRUN-006: 非機密値のサニタイズ

        subprocess_runner.py:L126 のsanitize_env_value呼び出しをカバー。
        """
        # Arrange
        env = {"PATH": "/usr/bin", "HOME": "/home/user"}
        subprocess_runner.security_sanitizer.is_safe_env_key.return_value = True
        subprocess_runner.security_sanitizer.sanitize_env_value.return_value = "sanitized"

        # Act
        subprocess_runner._log_command_details(
            ["cmd"], env, "/tmp", "us-east-1", 600
        )

        # Assert
        # 非機密キーの値はsanitize_env_valueで処理される
        assert subprocess_runner.security_sanitizer.sanitize_env_value.call_count == 2
        # 実際の値でsanitize_env_valueが呼ばれていることを確認
        subprocess_runner.security_sanitizer.sanitize_env_value.assert_any_call("/usr/bin")
        subprocess_runner.security_sanitizer.sanitize_env_value.assert_any_call("/home/user")
```

### 2.3 StatisticsAnalyzer テスト

```python
class TestStatisticsAnalyzerInit:
    """StatisticsAnalyzer初期化テスト"""

    def test_init(self, statistics_analyzer):
        """STAT-001: 初期化

        statistics_analyzer.py:L23-31 をカバー。
        """
        assert statistics_analyzer.job_id == "test-job-id"


class TestExtractScanStatisticsFromLog:
    """ログからスキャン統計抽出テスト"""

    def test_pattern1_using_cached(self, statistics_analyzer):
        """STAT-002: パターン1: Using cached

        statistics_analyzer.py:L64-71 の "Using cached" パターンをカバー。
        """
        # Arrange
        stdout = ["Using cached c7n.resources.ec2.EC2: 100"]

        # Act
        result = statistics_analyzer.extract_scan_statistics_from_log(stdout)

        # Assert
        assert result["total_scanned"] == 100
        assert result["resource_type"] == "ec2"

    def test_pattern2_filtered_from(self, statistics_analyzer):
        """STAT-003: パターン2: Filtered from

        statistics_analyzer.py:L75-82 の "Filtered from" パターンをカバー。
        """
        # Arrange
        stdout = ["Filtered from 100 to 5"]

        # Act
        result = statistics_analyzer.extract_scan_statistics_from_log(stdout)

        # Assert
        assert result["total_scanned"] == 100
        assert result["violations"] == 5

    def test_pattern3a_matched_resources(self, statistics_analyzer):
        """STAT-004: パターン3a: matched N resources

        statistics_analyzer.py:L88-96 の "matched N resources" パターンをカバー。
        """
        # Arrange
        stdout = ["INFO - policy-1 - action: mark matched 3 resources"]

        # Act
        result = statistics_analyzer.extract_scan_statistics_from_log(stdout)

        # Assert
        assert result["violations"] == 3

    def test_pattern3b_action_matched_regex(self, statistics_analyzer):
        """STAT-005: パターン3b: action matched regex

        statistics_analyzer.py:L99-103 の正規表現パターンをカバー。
        パターン3aで解析できない形式のfallback。
        """
        # Arrange
        # "matched"と"resources"の間にスペースがある形式（3aの分割では取得できない）
        stdout = ["action mark-for-op matched 2 resource items"]

        # Act
        result = statistics_analyzer.extract_scan_statistics_from_log(stdout)

        # Assert
        assert result["violations"] == 2

    def test_pattern3c_count_pattern(self, statistics_analyzer):
        """STAT-006: パターン3c: count:N

        statistics_analyzer.py:L106-110 の "policy:...count:N" パターンをカバー。
        """
        # Arrange
        stdout = ["policy: test-policy region:us-east-1 count:7 time:1.23"]

        # Act
        result = statistics_analyzer.extract_scan_statistics_from_log(stdout)

        # Assert
        assert result["violations"] == 7

    def test_combined_patterns_compliance_rate(self, statistics_analyzer):
        """STAT-007: 複合パターン+コンプライアンス率計算

        statistics_analyzer.py:L115-117 のtotal_scanned > 0分岐をカバー。
        複数パターンが混在するログからの統計計算。
        """
        # Arrange
        stdout = [
            "Using cached c7n.resources.s3.S3: 200",
            "Filtered from 200 to 10",
            "INFO - policy-1 - action: matched 10 resources"
        ]

        # Act
        result = statistics_analyzer.extract_scan_statistics_from_log(stdout)

        # Assert
        assert result["total_scanned"] == 200
        assert result["violations"] == 10
        # compliance_rate = (200 - 10) / 200 * 100 = 95.0
        assert result["compliance_rate"] == 95.0
        assert result["scan_details"]["compliant_resources"] == 190

    def test_no_match_returns_defaults(self, statistics_analyzer):
        """STAT-008: マッチなし（total_scanned=0）

        statistics_analyzer.py:L118-119 のtotal_scanned == 0分岐をカバー。
        """
        # Arrange
        stdout = ["INFO - Starting scan", "DEBUG - No resources found"]

        # Act
        result = statistics_analyzer.extract_scan_statistics_from_log(stdout)

        # Assert
        assert result["total_scanned"] == 0
        assert result["violations"] == 0
        assert result["compliance_rate"] == 0.0
        assert result["resource_type"] == "unknown"

    def test_matched_non_numeric_not_counted(self, statistics_analyzer):
        """STAT-018: extract_scan_statistics_from_log matchedの数値パース失敗

        statistics_analyzer.py:L88-96 のmatchedパターンで数値部分が非数値の場合。
        正規表現がマッチしないため violations に加算されない。
        """
        # Arrange
        stdout = ["action mark matched abc resources"]

        # Act
        result = statistics_analyzer.extract_scan_statistics_from_log(stdout)

        # Assert
        # "abc"は正規表現 \d+ にマッチしないため加算されない
        assert result["violations"] == 0


class TestParseCustodianOutput:
    """レガシー出力解析テスト"""

    def test_legacy_wrapper_delegates(self, statistics_analyzer):
        """STAT-009: parse_custodian_output レガシーラッパー

        statistics_analyzer.py:L139-161 のレガシーメソッドが
        extract_scan_statistics_from_logに委譲することをカバー。
        wrapsパターンで委譲呼び出しと戻り値の両方を検証する。
        """
        # Arrange
        stdout = ["Filtered from 50 to 3"]

        # Act - wrapsで実メソッドを保持しつつ呼び出しを記録
        with patch.object(statistics_analyzer, 'extract_scan_statistics_from_log',
                          wraps=statistics_analyzer.extract_scan_statistics_from_log) as mock_extract:
            result = statistics_analyzer.parse_custodian_output(stdout, [], "/tmp/output")

        # Assert
        # 委譲呼び出しを明示的に検証
        mock_extract.assert_called_once_with(stdout)
        # 戻り値がextract_scan_statistics_from_logの結果から導出されていることを検証
        assert result == 3


class TestParseOutputFiles:
    """出力ファイル解析テスト"""

    def test_nonexistent_directory(self, statistics_analyzer):
        """STAT-010: parse_output_files ディレクトリ不存在

        statistics_analyzer.py:L176-177 のos.path.exists=False分岐をカバー。
        """
        # Act
        result = statistics_analyzer.parse_output_files("/nonexistent/path")

        # Assert
        assert result == 0

    def test_json_list_format(self, statistics_analyzer, tmp_path):
        """STAT-011: parse_output_files JSONリスト形式

        statistics_analyzer.py:L192-195 のリスト形式JSONをカバー。
        """
        # Arrange
        policy_dir = tmp_path / "policy-1"
        policy_dir.mkdir()
        resources = [{"id": "r1"}, {"id": "r2"}, {"id": "r3"}, {"id": "r4"}]
        (policy_dir / "resources.json").write_text(json.dumps(resources))

        # Act
        result = statistics_analyzer.parse_output_files(str(tmp_path))

        # Assert
        assert result == 4

    def test_json_dict_resources_format(self, statistics_analyzer, tmp_path):
        """STAT-012: parse_output_files JSON dict resources形式

        statistics_analyzer.py:L199-203 のdict + resourcesキー形式をカバー。
        """
        # Arrange
        policy_dir = tmp_path / "policy-1"
        policy_dir.mkdir()
        data = {"resources": [{"id": "r1"}, {"id": "r2"}]}
        (policy_dir / "output.json").write_text(json.dumps(data))

        # Act
        result = statistics_analyzer.parse_output_files(str(tmp_path))

        # Assert
        assert result == 2

    def test_json_dict_other_format(self, statistics_analyzer, tmp_path):
        """STAT-013: parse_output_files JSON dict その他

        statistics_analyzer.py:L204-205 のresourcesキーなしdict形式をカバー。
        """
        # Arrange
        policy_dir = tmp_path / "policy-1"
        policy_dir.mkdir()
        data = {"status": "complete", "metadata": {}}
        (policy_dir / "metadata.json").write_text(json.dumps(data))

        # Act
        result = statistics_analyzer.parse_output_files(str(tmp_path))

        # Assert
        assert result == 0  # 違反件数には加算されない

    def test_json_unknown_format(self, statistics_analyzer, tmp_path):
        """STAT-014: parse_output_files 不明な形式

        statistics_analyzer.py:L206-207 のlist/dict以外の形式をカバー。
        """
        # Arrange
        policy_dir = tmp_path / "policy-1"
        policy_dir.mkdir()
        # JSON文字列はstr型としてロードされる
        (policy_dir / "data.json").write_text('"just a string"')

        # Act
        result = statistics_analyzer.parse_output_files(str(tmp_path))

        # Assert
        assert result == 0

    def test_json_list_few_items_logs_content(self, statistics_analyzer, tmp_path):
        """STAT-015: parse_output_files 少数違反ログ出力（境界値: ちょうど3件）

        statistics_analyzer.py:L196-198 のlen(data) <= 3条件でコンテンツログをカバー。
        境界値テスト: ちょうど3件（閾値上限）で内容ログが出力される。
        """
        # Arrange
        policy_dir = tmp_path / "policy-1"
        policy_dir.mkdir()
        resources = [{"id": "r1"}, {"id": "r2"}, {"id": "r3"}]
        (policy_dir / "resources.json").write_text(json.dumps(resources))

        # Act
        result = statistics_analyzer.parse_output_files(str(tmp_path))

        # Assert
        assert result == 3
        # 3件以下なので内容ログが出力される
        info_calls = [c for c in statistics_analyzer.logger.info.call_args_list
                      if "内容" in str(c)]
        assert len(info_calls) > 0

    def test_non_json_files_skipped(self, statistics_analyzer, tmp_path):
        """STAT-016: parse_output_files 非JSONファイルスキップ

        statistics_analyzer.py:L182 のendswith('.json')条件でフィルタされることをカバー。
        .txt等のファイルは処理対象外。
        """
        # Arrange
        policy_dir = tmp_path / "policy-1"
        policy_dir.mkdir()
        (policy_dir / "output.txt").write_text("not json")
        (policy_dir / "log.csv").write_text("a,b,c")

        # Act
        result = statistics_analyzer.parse_output_files(str(tmp_path))

        # Assert
        assert result == 0

    def test_json_dict_resources_not_list(self, statistics_analyzer, tmp_path):
        """STAT-017: parse_output_files dict+resources非リスト

        statistics_analyzer.py:L200 のisinstance(data['resources'], list)がFalseの場合。
        resourcesキーが存在するがリストでない場合、L202-203の処理がスキップされ
        違反カウントに加算されない。
        """
        # Arrange
        policy_dir = tmp_path / "policy-1"
        policy_dir.mkdir()
        data = {"resources": "not a list"}
        (policy_dir / "resources.json").write_text(json.dumps(data))

        # Act
        result = statistics_analyzer.parse_output_files(str(tmp_path))

        # Assert
        # resourcesがリストでないため違反カウントに加算されない
        assert result == 0
        # warningログは出力されない（正常なフロー）
        statistics_analyzer.logger.warning.assert_not_called()
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CEXE-E01 | 実行時例外でエラー結果返却 | build_command_for_regionが例外 | エラー結果にexecution_duration含む |
| SRUN-E01 | タイムアウトでプロセスkill | asyncio.TimeoutError発生 | return_code=-1, タイムアウトメッセージ |
| SRUN-E02 | subprocess例外 | create_subprocess_execが例外 | return_code=-1, エラーメッセージ |
| STAT-E01 | ログ統計抽出で例外 | 不正なログ行 | デフォルト統計値返却 |
| STAT-E02 | JSONファイル解析エラー | 不正なJSONファイル | 該当ファイルスキップ、他は継続 |
| STAT-E03 | parse_output_files全体例外 | os.walkが例外 | 0返却 |

### 3.1 異常系テスト

```python
class TestExecutorFlowErrors:
    """実行フロー系異常系テスト"""

    @pytest.mark.asyncio
    async def test_execute_scan_exception(self, executor):
        """CEXE-E01: 実行時例外でエラー結果返却

        main.py:L183-191 のexceptブロックをカバー。
        """
        # Arrange
        executor.command_builder.build_command_for_region.side_effect = RuntimeError("構築失敗")
        executor.result_processor.create_error_result.return_value = {
            "region": "us-east-1", "error": True
        }

        # Act
        result = await executor.execute_single_region_scan(
            "/tmp", "policy: ...", {}, "us-east-1", region_index=2
        )

        # Assert
        assert result["error"] is True
        assert "execution_duration" in result
        assert result["execution_duration"] >= 0
        assert result["region_index"] == 2
        executor.logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_subprocess_timeout(self, subprocess_runner):
        """SRUN-E01: タイムアウトでプロセスkill

        subprocess_runner.py:L79-83 のTimeoutError分岐をカバー。
        """
        # Arrange
        mock_process = MagicMock()
        mock_process.kill = MagicMock()
        mock_process.wait = AsyncMock()

        with patch(f"{MODULE_SRUN}.asyncio.create_subprocess_exec",
                   new_callable=AsyncMock, return_value=mock_process):
            with patch(f"{MODULE_SRUN}.asyncio.wait_for",
                       new_callable=AsyncMock,
                       side_effect=asyncio.TimeoutError):
                # Act
                stdout, stderr, rc = await subprocess_runner.run_custodian_subprocess(
                    ["custodian", "run"], {}, "/tmp/output", "us-east-1", timeout=10
                )

        # Assert
        assert rc == -1
        assert any("タイムアウト" in line for line in stderr)
        mock_process.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_subprocess_exception(self, subprocess_runner):
        """SRUN-E02: subprocess例外

        subprocess_runner.py:L91-93 のexceptブロックをカバー。
        """
        # Arrange
        with patch(f"{MODULE_SRUN}.asyncio.create_subprocess_exec",
                   new_callable=AsyncMock,
                   side_effect=OSError("コマンドが見つかりません")):
            # Act
            stdout, stderr, rc = await subprocess_runner.run_custodian_subprocess(
                ["/invalid/custodian", "run"], {}, "/tmp/output", "us-east-1"
            )

        # Assert
        assert rc == -1
        assert any("subprocess実行エラー" in line for line in stderr)
        subprocess_runner.logger.error.assert_called()

    def test_extract_statistics_exception(self, statistics_analyzer):
        """STAT-E01: ログ統計抽出で例外

        statistics_analyzer.py:L134-135 のexceptブロックをカバー。
        """
        # Arrange
        # re.searchが例外を投げるようにモック
        with patch(f"{MODULE_STAT}.re.search", side_effect=Exception("regex error")):
            # Act
            result = statistics_analyzer.extract_scan_statistics_from_log(["test line"])

        # Assert
        # デフォルト値が返される
        assert result["total_scanned"] == 0
        assert result["violations"] == 0
        statistics_analyzer.logger.warning.assert_called()

    def test_json_file_parse_error_continues(self, statistics_analyzer, tmp_path):
        """STAT-E02: JSONファイル解析エラー

        statistics_analyzer.py:L208-210 のファイル単位例外ハンドリングをカバー。
        不正なJSONファイルをスキップし、他のファイルの解析を継続する。
        """
        # Arrange
        policy_dir = tmp_path / "policy-1"
        policy_dir.mkdir()
        # 不正なJSONファイル
        (policy_dir / "bad.json").write_text("not json {{{")
        # 正常なJSONファイル
        (policy_dir / "good.json").write_text(json.dumps([{"id": "r1"}]))

        # Act
        result = statistics_analyzer.parse_output_files(str(tmp_path))

        # Assert
        # 不正ファイルをスキップし、正常ファイルの結果のみ
        assert result == 1
        statistics_analyzer.logger.warning.assert_called()

    def test_parse_output_files_walk_exception(self, statistics_analyzer):
        """STAT-E03: parse_output_files全体例外

        statistics_analyzer.py:L212-213 の全体例外ハンドリングをカバー。
        """
        # Arrange
        with patch(f"{MODULE_STAT}.os.path.exists", return_value=True), \
             patch(f"{MODULE_STAT}.os.walk", side_effect=PermissionError("アクセス拒否")):
            # Act
            result = statistics_analyzer.parse_output_files("/restricted/path")

        # Assert
        assert result == 0
        statistics_analyzer.logger.debug.assert_called()
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| SRUN-SEC-01 | SENSITIVE_PATTERNS全パターンのマスク | 全7パターンを含むキー | 全キーが機密判定されsanitize_env_value未呼出（制限事項#5参照） |
| SRUN-SEC-02 | 環境変数インジェクション対策の委譲確認 | 環境変数 | is_safe_env_key + sanitize_env_value呼び出し |
| STAT-SEC-01 | JSONファイル解析エラーでスタックトレース非露出 | 不正JSONファイル | warningログにstr(e)のみ、トレースバック非含 |

```python
@pytest.mark.security
class TestExecutorFlowSecurity:
    """実行フロー系セキュリティテスト"""

    def test_all_sensitive_patterns_masked(self, subprocess_runner):
        """SRUN-SEC-01: SENSITIVE_PATTERNS全パターンのマスク

        subprocess_runner.py:L114 の7パターンすべてがマスク分岐に入ることを確認。
        SENSITIVE_PATTERNS = ["SECRET", "TOKEN", "KEY", "PASSWORD", "CREDENTIAL", "ACCESS", "AUTH"]

        注: _log_command_detailsはsafe_envを返却もログ出力もしないため、
        "***MASKED***"の直接検証は不可能。sanitize_env_value未呼出で
        全キーがマスク分岐（L122-123）に入ったことを間接的に検証する（制限事項#5）。
        """
        # Arrange
        env = {
            "MY_SECRET": "s1",
            "API_TOKEN": "t1",
            "ENCRYPTION_KEY": "k1",
            "DB_PASSWORD": "p1",
            "AWS_CREDENTIAL": "c1",
            "ACCESS_ID": "a1",
            "AUTH_HEADER": "h1",
        }
        subprocess_runner.security_sanitizer.is_safe_env_key.return_value = True

        # Act
        subprocess_runner._log_command_details(
            ["cmd"], env, "/tmp", "us-east-1", 600
        )

        # Assert
        # 全7キーが機密判定されるため、sanitize_env_valueは一度も呼ばれない
        # （L122-123のSENSITIVE_PATTERNS分岐に入り、L126のsanitize_env_valueに到達しない）
        subprocess_runner.security_sanitizer.sanitize_env_value.assert_not_called()
        # is_safe_env_keyは全7キーに対して呼ばれる（L118の安全性チェック通過）
        assert subprocess_runner.security_sanitizer.is_safe_env_key.call_count == 7

    def test_env_injection_prevention_delegates(self, subprocess_runner):
        """SRUN-SEC-02: 環境変数インジェクション対策の委譲確認

        subprocess_runner.py:L118, L126 の安全性チェックが
        SecuritySanitizerに委譲されていることを確認。
        インジェクション対策の実装はSecuritySanitizer側（#14bで検証）。
        """
        # Arrange
        env = {"NORMAL": "value"}
        subprocess_runner.security_sanitizer.is_safe_env_key.return_value = True
        subprocess_runner.security_sanitizer.sanitize_env_value.return_value = "value"

        # Act
        subprocess_runner._log_command_details(
            ["cmd"], env, "/tmp", "us-east-1", 600
        )

        # Assert
        subprocess_runner.security_sanitizer.is_safe_env_key.assert_called_once_with("NORMAL")
        subprocess_runner.security_sanitizer.sanitize_env_value.assert_called_once_with("value")

    def test_json_error_no_stacktrace_in_log(self, statistics_analyzer, tmp_path):
        """STAT-SEC-01: JSONファイル解析エラーでスタックトレース非露出

        statistics_analyzer.py:L209 のwarningログにstr(e)のみが含まれ、
        完全なスタックトレースが露出しないことを確認（代表検証）。
        """
        # Arrange
        policy_dir = tmp_path / "policy-1"
        policy_dir.mkdir()
        (policy_dir / "bad.json").write_text("{invalid json")

        # Act
        statistics_analyzer.parse_output_files(str(tmp_path))

        # Assert
        # warningログが出力されたことを確認（空リスト通過防止）
        warning_calls = statistics_analyzer.logger.warning.call_args_list
        assert len(warning_calls) > 0, "JSONエラーに対するwarningログが出力されていません"
        for call in warning_calls:
            log_msg = str(call)
            # Traceback文字列やFile行が含まれないことを確認
            assert "Traceback" not in log_msg
            assert "File \"" not in log_msg
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_executor_module` | テスト間のモジュール状態リセット | function | Yes |
| `mock_executor_components` | CustodianExecutor全依存クラスのパッチ | function | No |
| `executor` | テスト用CustodianExecutorインスタンス | function | No |
| `mock_srun_components` | SubprocessRunner依存クラスのパッチ | function | No |
| `subprocess_runner` | テスト用SubprocessRunnerインスタンス | function | No |
| `statistics_analyzer` | テスト用StatisticsAnalyzerインスタンス | function | No |

### 共通フィクスチャ定義

```python
# test/unit/jobs/tasks/new_custodian_scan/executor/conftest.py
import sys
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

MODULE_MAIN = "app.jobs.tasks.new_custodian_scan.executor.main"
MODULE_SRUN = "app.jobs.tasks.new_custodian_scan.executor.subprocess_runner"
MODULE_STAT = "app.jobs.tasks.new_custodian_scan.executor.statistics_analyzer"


@pytest.fixture(autouse=True)
def reset_executor_module():
    """テストごとにモジュールのグローバル状態をリセット"""
    yield
    modules_to_remove = [key for key in sys.modules
                         if key.startswith("app.jobs.tasks.new_custodian_scan.executor")]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def mock_executor_components():
    """CustodianExecutor全依存クラスのモックパッチ

    main.py の __init__ が参照する全クラスをMagicMockに置き換える。
    """
    component_names = [
        "TaskLogger", "CustodianCommandBuilder", "ResultProcessor",
        "CustodianLogAnalyzer", "ErrorDetector", "SecuritySanitizer",
        "StatisticsAnalyzer", "SubprocessRunner"
    ]
    patches = {}
    mocks = {}
    for name in component_names:
        p = patch(f"{MODULE_MAIN}.{name}")
        mocks[name] = p.start()
        patches[name] = p

    yield mocks

    for p in patches.values():
        p.stop()


@pytest.fixture
def executor(mock_executor_components):
    """テスト用CustodianExecutorインスタンス

    全コンポーネントがモック化された状態でインスタンスを生成。
    executor.command_builder, executor.subprocess_runner 等は
    MagicMockインスタンスとしてアクセス可能。
    """
    from app.jobs.tasks.new_custodian_scan.executor.main import CustodianExecutor
    return CustodianExecutor("test-job-id")


@pytest.fixture
def mock_srun_components():
    """SubprocessRunner依存クラスのモックパッチ"""
    patches = {}
    mocks = {}
    for name in ["TaskLogger", "SecuritySanitizer"]:
        p = patch(f"{MODULE_SRUN}.{name}")
        mocks[name] = p.start()
        patches[name] = p

    yield mocks

    for p in patches.values():
        p.stop()


@pytest.fixture
def subprocess_runner(mock_srun_components):
    """テスト用SubprocessRunnerインスタンス"""
    from app.jobs.tasks.new_custodian_scan.executor.subprocess_runner import SubprocessRunner
    return SubprocessRunner("test-job-id")


@pytest.fixture
def statistics_analyzer():
    """テスト用StatisticsAnalyzerインスタンス

    StatisticsAnalyzerはTaskLoggerのみ依存するため、
    TaskLoggerのみパッチしてインスタンス生成。
    """
    with patch(f"{MODULE_STAT}.TaskLogger"):
        from app.jobs.tasks.new_custodian_scan.executor.statistics_analyzer import StatisticsAnalyzer
        return StatisticsAnalyzer("test-job-id")
```

---

## 6. テスト実行例

```bash
# 実行フロー系テスト全体を実行
pytest test/unit/jobs/tasks/new_custodian_scan/executor/test_executor_flow.py -v

# クラス単位で実行
pytest test/unit/jobs/tasks/new_custodian_scan/executor/test_executor_flow.py::TestExecuteSingleRegionScan -v
pytest test/unit/jobs/tasks/new_custodian_scan/executor/test_executor_flow.py::TestExtractScanStatisticsFromLog -v

# カバレッジ付きで実行
pytest test/unit/jobs/tasks/new_custodian_scan/executor/test_executor_flow.py \
  --cov=app.jobs.tasks.new_custodian_scan.executor.main \
  --cov=app.jobs.tasks.new_custodian_scan.executor.subprocess_runner \
  --cov=app.jobs.tasks.new_custodian_scan.executor.statistics_analyzer \
  --cov-report=term-missing -v

# セキュリティマーカーで実行（実行前提テーブルのマーカー登録が必要）
pytest test/unit/jobs/tasks/new_custodian_scan/executor/test_executor_flow.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 32 | CEXE-001〜007, SRUN-001〜007, STAT-001〜018 |
| 異常系 | 6 | CEXE-E01, SRUN-E01〜E02, STAT-E01〜E03 |
| セキュリティ | 3 | SRUN-SEC-01〜SEC-02, STAT-SEC-01 |
| **合計** | **41** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestCustodianExecutorInit` | CEXE-001〜CEXE-002 | 2 |
| `TestExecuteSingleRegionScan` | CEXE-003〜CEXE-007 | 5 |
| `TestSubprocessRunnerInit` | SRUN-001 | 1 |
| `TestRunCustodianSubprocess` | SRUN-002〜SRUN-003, SRUN-007 | 3 |
| `TestLogCommandDetails` | SRUN-004〜SRUN-006 | 3 |
| `TestStatisticsAnalyzerInit` | STAT-001 | 1 |
| `TestExtractScanStatisticsFromLog` | STAT-002〜STAT-008, STAT-018 | 8 |
| `TestParseCustodianOutput` | STAT-009 | 1 |
| `TestParseOutputFiles` | STAT-010〜STAT-017 | 8 |
| `TestExecutorFlowErrors` | CEXE-E01, SRUN-E01〜E02, STAT-E01〜E03 | 6 |
| `TestExecutorFlowSecurity` | SRUN-SEC-01〜SEC-02, STAT-SEC-01 | 3 |

### 実装失敗が予想されるテスト

以下の実行前提が整備されていれば、失敗が予想されるテストはありません。

#### 実行前提（実装タスクとしてpyproject.tomlへの追加が必要）

| 前提 | 対応内容 |
|------|---------|
| `pytest-asyncio` | `[dependency-groups].dev` に `"pytest-asyncio>=0.23.0"` を追加 |
| `security`マーカー | `[tool.pytest.ini_options].markers` に `"security: セキュリティテスト"` を追加 |

### 注意事項

- StatisticsAnalyzerのparse_output_filesテストは`tmp_path`フィクスチャを使用（実ファイルI/O）
- SubprocessRunnerのSRUN-003ではcreate_subprocess_execのみモックし、wait_forは実際のasyncioに委譲する
- SRUN-E01（タイムアウト）ではwait_forもモックしてTimeoutErrorを発生させる

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | CustodianExecutorの委譲先内部ロジックは対象外 | ErrorDetector, StatisticsAnalyzer等の詳細動作は検証しない | 各コンポーネントの個別テスト仕様書で対応 |
| 2 | count_violations_from_custodian_outputはモック対象 | 従来版の違反カウントロジックは検証しない | 別途violations_counterのテストで対応 |
| 3 | SubprocessRunnerの実際のプロセス実行は未テスト | asyncio.create_subprocess_execをモックするため | 結合テストで実際のCustodian実行を検証 |
| 4 | StatisticsAnalyzerの正規表現は実際のCustodianログに依存 | Custodianのログフォーマット変更で失敗する可能性 | Custodianバージョンアップ時にログサンプルを更新 |
| 5 | _log_command_detailsの結果（safe_env）は外部から検証できない | メソッドが値を返さず、ログ出力のみ | SecuritySanitizer呼び出し検証で間接的にカバー |
