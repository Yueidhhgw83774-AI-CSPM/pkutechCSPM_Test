# jobs/tasks/new_custodian_scan/parallel_executor テストケース

## 1. 概要

`parallel_executor.py` はマルチリージョン Custodian スキャンの並列実行エンジン。セマフォによる並列数制御、リトライ付き subprocess 実行、出力解析、結果統合を担うモジュールである。

### 1.1 主要機能

| メソッド | 説明 |
|---------|------|
| `__init__` | 3つのコンポーネント（TaskLogger, CustodianCommandBuilder, ResultProcessor）を初期化。dry_run_mode 対応 |
| `execute_regions_parallel` | メインエントリポイント。セマフォ制御 + asyncio.gather で並列実行 |
| `_execute_region_with_semaphore` | セマフォ制御下で単一リージョン実行。try/except/finally |
| `execute_single_region` | 単一リージョンスキャンの完全フロー（認証→コマンド構築→実行→解析→結果作成） |
| `_prepare_region_credentials` | クラウドプロバイダー別の認証情報準備（3分岐: azure/role_assumption/accessKey） |
| `_run_custodian_subprocess_with_retry` | リトライ付き subprocess 実行。dry_run/成功/タイムアウト/例外の各パス |
| `_simulate_custodian_execution` | ドライランモード用シミュレーション |
| `_parse_custodian_output` | stdout + JSON ファイルから違反件数を解析 |
| `_process_parallel_results` | 並列結果の分類（成功/失敗/例外/不正型）と統計計算 |

### 1.2 カバレッジ目標: 85%

> **注記**: `_run_custodian_subprocess_with_retry` はリトライループ・タイムアウト・指数バックオフを含む複雑なメソッド。`_parse_custodian_output` は os/json のローカル import を使用。pytest-asyncio が必要。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/jobs/tasks/new_custodian_scan/parallel_executor.py` |
| テストコード | `test/unit/jobs/tasks/new_custodian_scan/test_parallel_executor.py` |

### 1.4 補足情報

#### 依存関係（全モック対象）

```
parallel_executor.py ──→ TaskLogger（ログ）
                      ──→ CustodianCommandBuilder（コマンド構築）
                      ──→ ResultProcessor（結果処理）
                      ──→ asyncio（Semaphore, gather, create_subprocess_exec, wait_for, sleep）
                      ──→ os, json（ローカル import: _parse_custodian_output 内）
```

#### テスト戦略

| テストカテゴリ | 手法 |
|--------------|------|
| 初期化テスト | コンポーネントクラスを patch してインスタンス生成 |
| ワークフローテスト | 内部メソッドを `patch.object` でモック |
| subprocess テスト | `asyncio.create_subprocess_exec` を AsyncMock でモック |
| 出力解析テスト | `os.path.exists`, `os.walk`, `builtins.open` をモック |
| 結果統合テスト | 分類済みデータを直接入力 |

#### リトライロジック（_run_custodian_subprocess_with_retry）

```
dry_run_mode?
  └─ Yes → _simulate_custodian_execution
  └─ No → リトライループ (max_retries + 1 回)
      ├─ 成功 → return (stdout, stderr, return_code)
      ├─ TimeoutError
      │   ├─ 最終試行 → return ([], [timeout msg], -1)
      │   └─ 途中 → sleep(2^attempt) → 次の試行
      ├─ Exception
      │   ├─ 最終試行 → return ([], [error msg], -1)
      │   └─ 途中 → sleep(2^attempt) → 次の試行
      └─ フォールバック → return ([], [unexpected msg], -1)
```

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| PEXE-001 | __init__ 通常モード | job_id, dry_run=False | 3コンポーネント初期化 |
| PEXE-002 | __init__ ドライランモード | dry_run=True | info ログ出力 |
| PEXE-003 | execute_regions_parallel オーケストレーション | 2リージョン | gather + _process_parallel_results |
| PEXE-004 | _execute_region_with_semaphore 成功 | 正常データ | execute_single_region 結果を返す |
| PEXE-005 | execute_single_region 成功 | 正常データ | result に execution_duration 付き |
| PEXE-006 | _prepare_region_credentials Azure | azure | AZURE_* 環境変数 |
| PEXE-007 | _prepare_region_credentials role_assumption | role_assumption | 空辞書 |
| PEXE-008 | _prepare_region_credentials accessKey | accessKey | AWS_* 環境変数 + リージョン |
| PEXE-009 | _run_custodian_subprocess_with_retry ドライラン | dry_run=True | _simulate 呼び出し |
| PEXE-010 | _run_custodian_subprocess_with_retry 初回成功 | 正常実行 | stdout/stderr/return_code |
| PEXE-011 | _run_custodian_subprocess_with_retry タイムアウト後リトライ成功 | 1回目timeout→2回目成功 | 2回目の結果 |
| PEXE-012 | _run_custodian_subprocess_with_retry エラー後リトライ成功 | 1回目例外→2回目成功 | 2回目の結果 |
| PEXE-013 | _simulate_custodian_execution | region名 | シミュレート出力 |
| PEXE-014 | _parse_custodian_output stdout matched | "matched 3 resources" | 3 |
| PEXE-015 | _parse_custodian_output JSON list ファイル | [item1, item2] | 2 |
| PEXE-016 | _parse_custodian_output JSON dict resources | {"resources": [...]} | len |
| PEXE-017 | _parse_custodian_output ディレクトリなし | 存在しないパス | 0 |
| PEXE-018 | _parse_custodian_output invalid count | "matched abc resources" | 0（スキップ） |
| PEXE-019 | _process_parallel_results 全成功 | 成功結果のみ | successful_regions=N |
| PEXE-020 | _process_parallel_results Exception オブジェクト | Exception 入り | exception_results に分類 |
| PEXE-021 | _process_parallel_results 予期しない型 | 文字列 | UnexpectedResultType |
| PEXE-022 | _process_parallel_results 失敗（return_code≠0） | return_code=1 | failed_results に分類 |
| PEXE-023 | _process_parallel_results 実行時間統計 | duration 付き結果 | avg_execution_time 計算 |
| PEXE-024 | _process_parallel_results リージョン数超過 | results > regions | unknown_N ラベル |
| PEXE-025 | _simulate_custodian_execution 長いコマンド | len(command) > 3 | command_preview が切り詰め |
| PEXE-026 | _parse_custodian_output 非JSON ファイル混在 | .txt + .json | .json のみ解析 |
| PEXE-027 | _parse_custodian_output resources が非リスト | {"resources": "str"} | スキップ（0件） |

### 2.1 初期化テスト

```python
# test/unit/jobs/tasks/new_custodian_scan/test_parallel_executor.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

MODULE = "app.jobs.tasks.new_custodian_scan.parallel_executor"


class TestParallelExecutorInit:
    """__init__ のコンポーネント初期化テスト"""

    def test_init_normal_mode(self):
        """PEXE-001: 通常モードで3コンポーネントを初期化

        parallel_executor.py:26-31 の全属性設定をカバー。
        """
        # Arrange & Act
        with patch(f"{MODULE}.TaskLogger") as mock_tl, \
             patch(f"{MODULE}.CustodianCommandBuilder") as mock_cb, \
             patch(f"{MODULE}.ResultProcessor") as mock_rp:
            from app.jobs.tasks.new_custodian_scan.parallel_executor import ParallelCustodianExecutor
            executor = ParallelCustodianExecutor("test-job", dry_run_mode=False)

        # Assert
        assert executor.job_id == "test-job"
        assert executor.dry_run_mode is False
        mock_tl.assert_called_once_with("test-job", "ParallelCustodianExecutor")
        mock_cb.assert_called_once_with("test-job")
        mock_rp.assert_called_once_with("test-job")

    def test_init_dry_run_mode(self):
        """PEXE-002: ドライランモードで info ログが出力される

        parallel_executor.py:33-34 の dry_run_mode 分岐をカバー。
        """
        # Arrange & Act
        with patch(f"{MODULE}.TaskLogger") as mock_tl, \
             patch(f"{MODULE}.CustodianCommandBuilder"), \
             patch(f"{MODULE}.ResultProcessor"):
            from app.jobs.tasks.new_custodian_scan.parallel_executor import ParallelCustodianExecutor
            executor = ParallelCustodianExecutor("test-job", dry_run_mode=True)

        # Assert
        assert executor.dry_run_mode is True
        mock_tl.return_value.info.assert_called()
```

### 2.2 execute_regions_parallel テスト

```python
class TestExecuteRegionsParallel:
    """execute_regions_parallel のオーケストレーションテスト"""

    @pytest.fixture
    def executor(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.CustodianCommandBuilder"), \
             patch(f"{MODULE}.ResultProcessor"):
            from app.jobs.tasks.new_custodian_scan.parallel_executor import ParallelCustodianExecutor
            instance = ParallelCustodianExecutor("test-job")
        instance.logger = MagicMock()
        return instance

    @pytest.mark.asyncio
    async def test_orchestration_flow(self, executor):
        """PEXE-003: セマフォ + gather + _process_parallel_results の統合フロー

        parallel_executor.py:59-92 のメインフローをカバー。
        """
        # Arrange
        credentials = MagicMock()
        credentials.scanRegions = ["us-east-1", "ap-northeast-1"]
        region_result = {"violations_count": 0, "return_code": 0}

        with patch.object(executor, '_execute_region_with_semaphore',
                          new_callable=AsyncMock, return_value=region_result), \
             patch.object(executor, '_process_parallel_results',
                          new_callable=AsyncMock, return_value={"total": 0}) as mock_process:
            # Act
            result = await executor.execute_regions_parallel(
                "/tmp", "yaml", credentials, "aws", max_concurrent=3, timeout_per_region=600
            )

        # Assert
        mock_process.assert_awaited_once()
        # _process_parallel_results の第2引数がリージョンリスト
        call_args = mock_process.call_args[0]
        assert call_args[1] == ["us-east-1", "ap-northeast-1"]
```

### 2.3 _execute_region_with_semaphore テスト

```python
class TestExecuteRegionWithSemaphore:
    """_execute_region_with_semaphore のセマフォ制御テスト"""

    @pytest.fixture
    def executor(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.CustodianCommandBuilder"), \
             patch(f"{MODULE}.ResultProcessor"):
            from app.jobs.tasks.new_custodian_scan.parallel_executor import ParallelCustodianExecutor
            instance = ParallelCustodianExecutor("test-job")
        instance.logger = MagicMock()
        return instance

    @pytest.mark.asyncio
    async def test_success(self, executor):
        """PEXE-004: セマフォ制御下で正常に結果を返す

        parallel_executor.py:106-113 の正常パスをカバー。
        """
        # Arrange
        import asyncio
        semaphore = asyncio.Semaphore(1)
        expected = {"violations_count": 2}

        with patch.object(executor, 'execute_single_region',
                          new_callable=AsyncMock, return_value=expected):
            # Act
            result = await executor._execute_region_with_semaphore(
                semaphore, "/tmp", "yaml", MagicMock(), "us-east-1", 0, "aws", 600
            )

        # Assert
        assert result == expected
```

### 2.4 execute_single_region テスト

```python
class TestExecuteSingleRegion:
    """execute_single_region の単一リージョンスキャンテスト"""

    @pytest.fixture
    def executor(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.CustodianCommandBuilder"), \
             patch(f"{MODULE}.ResultProcessor"):
            from app.jobs.tasks.new_custodian_scan.parallel_executor import ParallelCustodianExecutor
            instance = ParallelCustodianExecutor("test-job")
        instance.logger = MagicMock()
        return instance

    @pytest.mark.asyncio
    async def test_success_flow(self, executor):
        """PEXE-005: 単一リージョンスキャンの完全成功フロー

        parallel_executor.py:153-200 の正常パスをカバー。
        """
        # Arrange
        credentials = MagicMock()

        with patch.object(executor, '_prepare_region_credentials',
                          new_callable=AsyncMock, return_value={"key": "val"}), \
             patch.object(executor, '_run_custodian_subprocess_with_retry',
                          new_callable=AsyncMock, return_value=(["stdout"], ["stderr"], 0)):
            executor.command_builder.build_command_for_region.return_value = (
                ["run"], {"ENV": "val"}, "policy.yml", "/tmp/output"
            )
            executor.command_builder.get_custodian_command_path.return_value = "/usr/bin/custodian"
            executor._parse_custodian_output = MagicMock(return_value=5)
            executor.result_processor.process_single_region_result.return_value = {
                "violations_count": 5, "return_code": 0
            }

            # Act
            result = await executor.execute_single_region(
                "/tmp", "yaml", credentials, "us-east-1", 0, "aws", 600
            )

        # Assert
        assert result["violations_count"] == 5
        assert "execution_duration" in result
        assert result["region_index"] == 0
```

### 2.5 _prepare_region_credentials テスト

```python
class TestPrepareRegionCredentials:
    """_prepare_region_credentials の3分岐テスト"""

    @pytest.fixture
    def executor(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.CustodianCommandBuilder"), \
             patch(f"{MODULE}.ResultProcessor"):
            from app.jobs.tasks.new_custodian_scan.parallel_executor import ParallelCustodianExecutor
            instance = ParallelCustodianExecutor("test-job")
        instance.logger = MagicMock()
        return instance

    @pytest.mark.asyncio
    async def test_azure_credentials(self, executor):
        """PEXE-006: Azure の場合は AZURE_* 環境変数を返す

        parallel_executor.py:219-226 の azure 分岐をカバー。
        """
        # Arrange
        credentials = MagicMock()
        credentials.tenantId = "tenant-123"
        credentials.clientId = "client-456"
        credentials.clientSecret = "secret-789"
        credentials.subscriptionId = "sub-012"

        # Act
        result = await executor._prepare_region_credentials(credentials, "us-east-1", "azure")

        # Assert
        assert result["AZURE_TENANT_ID"] == "tenant-123"
        assert result["AZURE_CLIENT_ID"] == "client-456"
        assert result["AZURE_CLIENT_SECRET"] == "secret-789"
        assert result["AZURE_SUBSCRIPTION_ID"] == "sub-012"

    @pytest.mark.asyncio
    async def test_role_assumption(self, executor):
        """PEXE-007: role_assumption の場合は空辞書を返す

        parallel_executor.py:227-232 の role_assumption 分岐をカバー。
        TODO 実装のため空辞書が返る。
        """
        # Arrange
        credentials = MagicMock()
        credentials.authType = "role_assumption"

        # Act
        result = await executor._prepare_region_credentials(credentials, "us-east-1", "aws")

        # Assert
        assert result == {}

    @pytest.mark.asyncio
    async def test_access_key(self, executor):
        """PEXE-008: accessKey の場合は AWS_* 環境変数 + リージョンを返す

        parallel_executor.py:233-240 の else 分岐をカバー。
        """
        # Arrange
        credentials = MagicMock()
        credentials.authType = "accessKey"
        credentials.accessKey = "AKIATEST"
        credentials.secretKey = "secret"
        credentials.sessionToken = "token"

        # Act
        result = await executor._prepare_region_credentials(credentials, "ap-northeast-1", "aws")

        # Assert
        assert result["AWS_ACCESS_KEY_ID"] == "AKIATEST"
        assert result["AWS_SECRET_ACCESS_KEY"] == "secret"
        assert result["AWS_SESSION_TOKEN"] == "token"
        assert result["AWS_DEFAULT_REGION"] == "ap-northeast-1"
```

### 2.6 _run_custodian_subprocess_with_retry テスト

```python
class TestRunCustodianSubprocessWithRetry:
    """_run_custodian_subprocess_with_retry のリトライロジックテスト"""

    @pytest.fixture
    def executor(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.CustodianCommandBuilder"), \
             patch(f"{MODULE}.ResultProcessor"):
            from app.jobs.tasks.new_custodian_scan.parallel_executor import ParallelCustodianExecutor
            instance = ParallelCustodianExecutor("test-job")
        instance.logger = MagicMock()
        return instance

    @pytest.mark.asyncio
    async def test_dry_run_delegates_to_simulate(self, executor):
        """PEXE-009: ドライランモードで _simulate_custodian_execution を呼ぶ

        parallel_executor.py:254-255 の dry_run_mode 分岐をカバー。
        """
        # Arrange
        executor.dry_run_mode = True
        expected = (["simulated"], [], 0)

        with patch.object(executor, '_simulate_custodian_execution',
                          new_callable=AsyncMock, return_value=expected) as mock_sim:
            # Act
            result = await executor._run_custodian_subprocess_with_retry(
                ["cmd"], {}, "/tmp", "us-east-1", 600
            )

        # Assert
        assert result == expected
        mock_sim.assert_awaited_once_with(["cmd"], "us-east-1")

    @pytest.mark.asyncio
    async def test_success_first_attempt(self, executor):
        """PEXE-010: 初回成功で stdout/stderr/return_code を返す

        parallel_executor.py:262-283 の成功パスをカバー。
        注: wait_for は communicate() コルーチンをラップするため、
        テスト時は wait_for をモックして直接戻り値を返す方式を使用。
        communicate() のコルーチン未 await 警告が出る場合は
        wait_for の side_effect 内で受け取った coro を await する形に調整する。
        """
        # Arrange
        mock_process = AsyncMock()
        mock_process.returncode = 0

        with patch(f"{MODULE}.asyncio.create_subprocess_exec",
                   new_callable=AsyncMock, return_value=mock_process), \
             patch(f"{MODULE}.asyncio.wait_for",
                   new_callable=AsyncMock, return_value=(b"output line\n", b"")):
            # Act
            stdout, stderr, rc = await executor._run_custodian_subprocess_with_retry(
                ["custodian", "run"], {}, "/tmp", "us-east-1", 600
            )

        # Assert
        assert rc == 0
        assert "output line" in stdout

    @pytest.mark.asyncio
    async def test_timeout_then_success_on_retry(self, executor):
        """PEXE-011: 1回目タイムアウト→2回目成功

        parallel_executor.py:285-295 のタイムアウトリトライ + L262-283 の成功パスをカバー。
        """
        # Arrange
        import asyncio as aio
        mock_process_timeout = AsyncMock()
        mock_process_timeout.kill = MagicMock()
        mock_process_timeout.wait = AsyncMock()

        mock_process_success = AsyncMock()
        mock_process_success.returncode = 0

        call_count = 0

        async def mock_create_subprocess(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_process_timeout
            return mock_process_success

        async def mock_wait_for(coro, timeout):
            nonlocal call_count
            if call_count == 1:
                raise aio.TimeoutError()
            return (b"success\n", b"")

        with patch(f"{MODULE}.asyncio.create_subprocess_exec", side_effect=mock_create_subprocess), \
             patch(f"{MODULE}.asyncio.wait_for", side_effect=mock_wait_for), \
             patch(f"{MODULE}.asyncio.sleep", new_callable=AsyncMock):
            # Act
            stdout, stderr, rc = await executor._run_custodian_subprocess_with_retry(
                ["cmd"], {}, "/tmp", "us-east-1", 600, max_retries=1
            )

        # Assert
        assert rc == 0
        mock_process_timeout.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_then_success_on_retry(self, executor):
        """PEXE-012: 1回目例外→2回目成功

        parallel_executor.py:297-305 の例外リトライ + L262-283 の成功パスをカバー。
        """
        # Arrange
        mock_process = AsyncMock()
        mock_process.returncode = 0

        call_count = 0

        async def mock_create_subprocess(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise OSError("接続失敗")
            return mock_process

        with patch(f"{MODULE}.asyncio.create_subprocess_exec", side_effect=mock_create_subprocess), \
             patch(f"{MODULE}.asyncio.wait_for",
                   new_callable=AsyncMock, return_value=(b"ok\n", b"")), \
             patch(f"{MODULE}.asyncio.sleep", new_callable=AsyncMock):
            # Act
            stdout, stderr, rc = await executor._run_custodian_subprocess_with_retry(
                ["cmd"], {}, "/tmp", "us-east-1", 600, max_retries=1
            )

        # Assert
        assert rc == 0
```

### 2.7 _simulate_custodian_execution テスト

```python
class TestSimulateCustodianExecution:
    """_simulate_custodian_execution のシミュレーションテスト"""

    @pytest.fixture
    def executor(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.CustodianCommandBuilder"), \
             patch(f"{MODULE}.ResultProcessor"):
            from app.jobs.tasks.new_custodian_scan.parallel_executor import ParallelCustodianExecutor
            instance = ParallelCustodianExecutor("test-job")
        instance.logger = MagicMock()
        return instance

    @pytest.mark.asyncio
    async def test_returns_simulated_output(self, executor):
        """PEXE-013: シミュレーション出力を返す

        parallel_executor.py:316-347 のシミュレーション全体をカバー。
        """
        # Arrange
        with patch(f"{MODULE}.asyncio.sleep", new_callable=AsyncMock):
            # Act
            stdout, stderr, rc = await executor._simulate_custodian_execution(
                ["custodian", "run"], "us-east-1"
            )

        # Assert
        assert rc == 0
        assert len(stdout) > 0
        assert stderr == []
        assert any("us-east-1" in line for line in stdout)

    @pytest.mark.asyncio
    async def test_long_command_preview_truncated(self, executor):
        """PEXE-025: 長いコマンド（4要素以上）で command_preview が切り詰められる

        parallel_executor.py:317 の len(command) > 3 分岐をカバー。
        """
        # Arrange
        long_command = ["custodian", "run", "--region", "us-east-1", "--output-dir", "/tmp"]

        with patch(f"{MODULE}.asyncio.sleep", new_callable=AsyncMock):
            # Act
            await executor._simulate_custodian_execution(long_command, "us-east-1")

        # Assert
        # ログの context に切り詰めされた command_preview が含まれる
        first_info_call = executor.logger.info.call_args_list[0]
        context = first_info_call[1]["context"]
        assert context["command_preview"].endswith("...")
```

### 2.8 _parse_custodian_output テスト

```python
class TestParseCustodianOutput:
    """_parse_custodian_output の出力解析テスト"""

    @pytest.fixture
    def executor(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.CustodianCommandBuilder"), \
             patch(f"{MODULE}.ResultProcessor"):
            from app.jobs.tasks.new_custodian_scan.parallel_executor import ParallelCustodianExecutor
            instance = ParallelCustodianExecutor("test-job")
        instance.logger = MagicMock()
        return instance

    def test_parse_stdout_matched(self, executor):
        """PEXE-014: stdout から "matched N resources" を解析

        parallel_executor.py:363-371 の stdout 解析パスをカバー。
        """
        # Arrange
        stdout = [
            "INFO - policy-1 - action: matched 3 resources",
            "INFO - policy-2 - action: matched 1 resources",
            "INFO - other log line"
        ]

        with patch("os.path.exists", return_value=False):
            # Act
            result = executor._parse_custodian_output(stdout, [], "/tmp/output")

        # Assert
        assert result == 4

    def test_parse_json_list_file(self, executor):
        """PEXE-015: JSON リストファイルから件数を解析

        parallel_executor.py:382-383 の isinstance(data, list) 分岐をカバー。
        """
        # Arrange
        import json
        json_data = [{"id": "1"}, {"id": "2"}]

        with patch("os.path.exists", return_value=True), \
             patch("os.walk", return_value=[("/tmp", [], ["results.json"])]), \
             patch("os.path.join", return_value="/tmp/results.json"), \
             patch("builtins.open", MagicMock()), \
             patch("json.load", return_value=json_data):
            # Act
            result = executor._parse_custodian_output([], [], "/tmp")

        # Assert
        assert result == 2

    def test_parse_json_dict_resources(self, executor):
        """PEXE-016: JSON dict の resources キーから件数を解析

        parallel_executor.py:384-386 の dict + resources 分岐をカバー。
        """
        # Arrange
        json_data = {"resources": [{"id": "1"}, {"id": "2"}, {"id": "3"}]}

        with patch("os.path.exists", return_value=True), \
             patch("os.walk", return_value=[("/tmp", [], ["results.json"])]), \
             patch("os.path.join", return_value="/tmp/results.json"), \
             patch("builtins.open", MagicMock()), \
             patch("json.load", return_value=json_data):
            # Act
            result = executor._parse_custodian_output([], [], "/tmp")

        # Assert
        assert result == 3

    def test_no_output_dir(self, executor):
        """PEXE-017: 出力ディレクトリが存在しない場合は 0

        parallel_executor.py:374 の os.path.exists == False パスをカバー。
        """
        # Arrange
        with patch("os.path.exists", return_value=False):
            # Act
            result = executor._parse_custodian_output([], [], "/nonexistent")

        # Assert
        assert result == 0

    def test_invalid_count_in_stdout(self, executor):
        """PEXE-018: stdout の count が数値でない場合はスキップ

        parallel_executor.py:370 の ValueError/IndexError 分岐をカバー。
        """
        # Arrange
        stdout = ["INFO - action: matched abc resources"]

        with patch("os.path.exists", return_value=False):
            # Act
            result = executor._parse_custodian_output(stdout, [], "/tmp")

        # Assert
        assert result == 0

    def test_non_json_files_skipped(self, executor):
        """PEXE-026: 非JSON ファイルはスキップされ .json のみ解析

        parallel_executor.py:377 の file.endswith('.json') == False パスをカバー。
        """
        # Arrange
        json_data = [{"id": "1"}]

        with patch("os.path.exists", return_value=True), \
             patch("os.walk", return_value=[("/tmp", [], ["log.txt", "results.json"])]), \
             patch("os.path.join", return_value="/tmp/results.json"), \
             patch("builtins.open", MagicMock()), \
             patch("json.load", return_value=json_data):
            # Act
            result = executor._parse_custodian_output([], [], "/tmp")

        # Assert
        # .txt はスキップされ .json の1ファイルのみ解析 → 1件
        assert result == 1

    def test_resources_not_list_skipped(self, executor):
        """PEXE-027: resources が非リスト型の場合はスキップ

        parallel_executor.py:385 の isinstance(data['resources'], list) == False パスをカバー。
        """
        # Arrange
        json_data = {"resources": "not-a-list"}

        with patch("os.path.exists", return_value=True), \
             patch("os.walk", return_value=[("/tmp", [], ["results.json"])]), \
             patch("os.path.join", return_value="/tmp/results.json"), \
             patch("builtins.open", MagicMock()), \
             patch("json.load", return_value=json_data):
            # Act
            result = executor._parse_custodian_output([], [], "/tmp")

        # Assert
        assert result == 0
```

### 2.9 _process_parallel_results テスト

```python
class TestProcessParallelResults:
    """_process_parallel_results の結果統合テスト"""

    @pytest.fixture
    def executor(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.CustodianCommandBuilder"), \
             patch(f"{MODULE}.ResultProcessor"):
            from app.jobs.tasks.new_custodian_scan.parallel_executor import ParallelCustodianExecutor
            instance = ParallelCustodianExecutor("test-job")
        instance.logger = MagicMock()
        return instance

    @pytest.mark.asyncio
    async def test_all_success(self, executor):
        """PEXE-019: 全リージョン成功時の統計

        parallel_executor.py:421-422 の return_code == 0 分岐をカバー。
        """
        # Arrange
        results = [
            {"return_code": 0, "violations_count": 3, "execution_duration": 10.0},
            {"return_code": 0, "violations_count": 2, "execution_duration": 8.0}
        ]
        regions = ["us-east-1", "ap-northeast-1"]
        executor.result_processor.aggregate_multi_region_results.return_value = {"total": 5}

        # Act
        result = await executor._process_parallel_results(results, regions, "aws", 15.0)

        # Assert
        call_args = executor.result_processor.aggregate_multi_region_results.call_args
        metadata = call_args[0][1]
        assert metadata["completed_regions"] == 2
        assert metadata["failed_regions"] == 0
        assert metadata["parallel_execution"] is True

    @pytest.mark.asyncio
    async def test_exception_object(self, executor):
        """PEXE-020: Exception オブジェクトの分類

        parallel_executor.py:412-418 の isinstance(result, Exception) 分岐をカバー。
        """
        # Arrange
        results = [RuntimeError("接続失敗")]
        regions = ["us-east-1"]
        executor.result_processor.aggregate_multi_region_results.return_value = {}

        # Act
        await executor._process_parallel_results(results, regions, "aws", 5.0)

        # Assert
        call_args = executor.result_processor.aggregate_multi_region_results.call_args
        all_results = call_args[0][0]
        metadata = call_args[0][1]
        # exception_results に分類される
        assert any("error_type" in r and r["error_type"] == "RuntimeError" for r in all_results)
        assert metadata["failed_regions"] == 1

    @pytest.mark.asyncio
    async def test_unexpected_result_type(self, executor):
        """PEXE-021: 予期しない結果型の分類

        parallel_executor.py:426-431 の else（予期しない型）分岐をカバー。
        """
        # Arrange
        results = ["unexpected_string"]
        regions = ["us-east-1"]
        executor.result_processor.aggregate_multi_region_results.return_value = {}

        # Act
        await executor._process_parallel_results(results, regions, "aws", 5.0)

        # Assert
        call_args = executor.result_processor.aggregate_multi_region_results.call_args
        all_results = call_args[0][0]
        assert any("UnexpectedResultType" in str(r.get("error_type", "")) for r in all_results)

    @pytest.mark.asyncio
    async def test_failed_result(self, executor):
        """PEXE-022: return_code != 0 の結果が failed に分類

        parallel_executor.py:423-424 の else（failed）分岐をカバー。
        """
        # Arrange
        results = [{"return_code": 1, "violations_count": 0}]
        regions = ["us-east-1"]
        executor.result_processor.aggregate_multi_region_results.return_value = {}

        # Act
        await executor._process_parallel_results(results, regions, "aws", 5.0)

        # Assert
        call_args = executor.result_processor.aggregate_multi_region_results.call_args
        metadata = call_args[0][1]
        assert metadata["failed_regions"] == 1
        assert metadata["completed_regions"] == 0

    @pytest.mark.asyncio
    async def test_avg_execution_time(self, executor):
        """PEXE-023: 実行時間の平均値計算

        parallel_executor.py:440-441 の avg_execution_time 計算をカバー。
        """
        # Arrange
        results = [
            {"return_code": 0, "violations_count": 0, "execution_duration": 10.0},
            {"return_code": 0, "violations_count": 0, "execution_duration": 20.0}
        ]
        regions = ["us-east-1", "ap-northeast-1"]
        executor.result_processor.aggregate_multi_region_results.return_value = {}

        # Act
        await executor._process_parallel_results(results, regions, "aws", 25.0)

        # Assert
        call_args = executor.result_processor.aggregate_multi_region_results.call_args
        metadata = call_args[0][1]
        assert metadata["avg_execution_time"] == 15.0

    @pytest.mark.asyncio
    async def test_regions_out_of_bounds(self, executor):
        """PEXE-024: results が regions より多い場合 unknown_N ラベル

        parallel_executor.py:410 の i < len(regions) else 分岐をカバー。
        """
        # Arrange
        results = [
            {"return_code": 0, "violations_count": 0},
            {"return_code": 0, "violations_count": 0}
        ]
        regions = ["us-east-1"]  # 1つしかない
        executor.result_processor.aggregate_multi_region_results.return_value = {}

        # Act
        await executor._process_parallel_results(results, regions, "aws", 5.0)

        # Assert（例外なく完了すること）
        executor.result_processor.aggregate_multi_region_results.assert_called_once()
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| PEXE-E01 | _execute_region_with_semaphore 例外 | 実行例外 | error_result + error ログ |
| PEXE-E02 | execute_single_region 例外 | 実行例外 | error_result + execution_duration |
| PEXE-E03 | _run_custodian_subprocess_with_retry 最終タイムアウト | 全試行 timeout | ([], [msg], -1) |
| PEXE-E04 | _run_custodian_subprocess_with_retry 最終例外 | 全試行例外 | ([], [msg], -1) |
| PEXE-E05 | _parse_custodian_output JSON ファイル解析エラー | 不正JSON | debug ログ + スキップ |
| PEXE-E06 | _parse_custodian_output 全体例外 | os.path.exists 例外 | warning ログ + 0 |
| PEXE-E07 | _run_custodian_subprocess_with_retry フォールバック | 理論上到達不可 | ([], [msg], -1) |

### 3.1 異常系テスト

```python
class TestParallelExecutorErrors:
    """異常入力・エラー回復のテスト"""

    @pytest.fixture
    def executor(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.CustodianCommandBuilder"), \
             patch(f"{MODULE}.ResultProcessor"):
            from app.jobs.tasks.new_custodian_scan.parallel_executor import ParallelCustodianExecutor
            instance = ParallelCustodianExecutor("test-job")
        instance.logger = MagicMock()
        return instance

    @pytest.mark.asyncio
    async def test_semaphore_execution_exception(self, executor):
        """PEXE-E01: セマフォ制御下で例外発生時に error_result を返す

        parallel_executor.py:114-116 の except 分岐をカバー。
        """
        # Arrange
        import asyncio
        semaphore = asyncio.Semaphore(1)

        with patch.object(executor, 'execute_single_region',
                          new_callable=AsyncMock, side_effect=RuntimeError("実行失敗")):
            executor.result_processor.create_error_result.return_value = {"error": "失敗"}

            # Act
            result = await executor._execute_region_with_semaphore(
                semaphore, "/tmp", "yaml", MagicMock(), "us-east-1", 0, "aws", 600
            )

        # Assert
        executor.result_processor.create_error_result.assert_called_once()
        executor.logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_single_region_exception(self, executor):
        """PEXE-E02: execute_single_region で例外発生時に error_result を返す

        parallel_executor.py:202-210 の except 分岐をカバー。
        """
        # Arrange
        credentials = MagicMock()

        with patch.object(executor, '_prepare_region_credentials',
                          new_callable=AsyncMock, side_effect=RuntimeError("認証失敗")):
            executor.result_processor.create_error_result.return_value = {
                "error": "認証失敗"
            }

            # Act
            result = await executor.execute_single_region(
                "/tmp", "yaml", credentials, "us-east-1", 0, "aws", 600
            )

        # Assert
        assert "execution_duration" in result
        assert result["region_index"] == 0
        executor.result_processor.create_error_result.assert_called_once()

    @pytest.mark.asyncio
    async def test_final_timeout(self, executor):
        """PEXE-E03: 全試行タイムアウトでエラータプルを返す

        parallel_executor.py:291-292 の最終タイムアウト分岐をカバー。
        """
        # Arrange
        import asyncio as aio
        mock_process = AsyncMock()
        mock_process.kill = MagicMock()
        mock_process.wait = AsyncMock()

        with patch(f"{MODULE}.asyncio.create_subprocess_exec",
                   new_callable=AsyncMock, return_value=mock_process), \
             patch(f"{MODULE}.asyncio.wait_for",
                   new_callable=AsyncMock, side_effect=aio.TimeoutError()), \
             patch(f"{MODULE}.asyncio.sleep", new_callable=AsyncMock):
            # Act（max_retries=0 で即最終試行）
            stdout, stderr, rc = await executor._run_custodian_subprocess_with_retry(
                ["cmd"], {}, "/tmp", "us-east-1", 60, max_retries=0
            )

        # Assert
        assert rc == -1
        assert any("タイムアウト" in line for line in stderr)

    @pytest.mark.asyncio
    async def test_final_subprocess_error(self, executor):
        """PEXE-E04: 全試行例外でエラータプルを返す

        parallel_executor.py:301-302 の最終例外分岐をカバー。
        """
        # Arrange
        with patch(f"{MODULE}.asyncio.create_subprocess_exec",
                   new_callable=AsyncMock, side_effect=OSError("プロセス起動失敗")), \
             patch(f"{MODULE}.asyncio.sleep", new_callable=AsyncMock):
            # Act（max_retries=0）
            stdout, stderr, rc = await executor._run_custodian_subprocess_with_retry(
                ["cmd"], {}, "/tmp", "us-east-1", 60, max_retries=0
            )

        # Assert
        assert rc == -1
        assert any("subprocess実行エラー" in line for line in stderr)

    def test_json_file_parse_error(self, executor):
        """PEXE-E05: JSON ファイル解析エラーで debug ログ + スキップ

        parallel_executor.py:387-389 の JSON 解析 except 分岐をカバー。
        """
        # Arrange
        with patch("os.path.exists", return_value=True), \
             patch("os.walk", return_value=[("/tmp", [], ["bad.json"])]), \
             patch("os.path.join", return_value="/tmp/bad.json"), \
             patch("builtins.open", MagicMock()), \
             patch("json.load", side_effect=ValueError("不正JSON")):
            # Act
            result = executor._parse_custodian_output([], [], "/tmp")

        # Assert
        assert result == 0
        executor.logger.debug.assert_called()

    def test_overall_parse_exception(self, executor):
        """PEXE-E06: 出力解析全体で例外発生時に warning ログ + 0

        parallel_executor.py:391-392 の外側 except 分岐をカバー。
        """
        # Arrange
        with patch("os.path.exists", side_effect=Exception("予期しないエラー")):
            # Act
            result = executor._parse_custodian_output([], [], "/tmp")

        # Assert
        assert result == 0
        executor.logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_subprocess_fallback(self, executor):
        """PEXE-E07: フォールバックパス（理論上到達不可の安全ガード）

        parallel_executor.py:307-308 のフォールバックをカバー。
        max_retries=-1 は非現実的な入力だが、防衛的プログラミングの
        安全ガードが機能することを確認する目的で使用。
        通常の呼び出しでは max_retries >= 0 が前提。
        """
        # Arrange & Act
        stdout, stderr, rc = await executor._run_custodian_subprocess_with_retry(
            ["cmd"], {}, "/tmp", "us-east-1", 60, max_retries=-1
        )

        # Assert
        assert rc == -1
        assert any("予期しないエラー" in line for line in stderr)
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| PEXE-SEC-01 | エラーログが str(e) プレフィックス形式 | 例外発生 | フォーマット化された出力 |
| PEXE-SEC-02 | Azure 認証情報が AWS パスに混入しない | azure / aws | 各パス固有の環境変数のみ |
| PEXE-SEC-03 | _prepare_region_credentials の None 防止 | None 属性 | `or ""` で空文字に変換 |

### 4.1 セキュリティテスト

> **注記**: コマンドインジェクション防止は `CustodianCommandBuilder` 側の責務であり、
> `parallel_executor` は `create_subprocess_exec` にリスト形式でコマンドを渡す安全な方式を使用。
> コマンド引数のサニタイゼーションは `command_builder` のテスト仕様書で検証する。

```python
@pytest.mark.security
class TestParallelExecutorSecurity:
    """セキュリティ関連テスト"""

    @pytest.fixture
    def executor(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.CustodianCommandBuilder"), \
             patch(f"{MODULE}.ResultProcessor"):
            from app.jobs.tasks.new_custodian_scan.parallel_executor import ParallelCustodianExecutor
            instance = ParallelCustodianExecutor("test-job")
        instance.logger = MagicMock()
        return instance

    @pytest.mark.asyncio
    async def test_error_log_format(self, executor):
        """PEXE-SEC-01: エラーログがプレフィックス + str(e) 形式で出力

        parallel_executor.py:115 の logger.error を代表検証。
        他の except ブロック（L204, L298 等）でも同様のパターンを使用。
        """
        # Arrange
        import asyncio
        semaphore = asyncio.Semaphore(1)

        with patch.object(executor, 'execute_single_region',
                          new_callable=AsyncMock, side_effect=RuntimeError("test-error")):
            executor.result_processor.create_error_result.return_value = {}

            # Act
            await executor._execute_region_with_semaphore(
                semaphore, "/tmp", "yaml", MagicMock(), "us-east-1", 0, "aws", 600
            )

        # Assert
        error_log = executor.logger.error.call_args[0][0]
        assert "test-error" in error_log
        assert "リージョン us-east-1" in error_log

    @pytest.mark.asyncio
    async def test_azure_aws_credential_isolation(self, executor):
        """PEXE-SEC-02: Azure/AWS 認証パスが相互に混入しない

        parallel_executor.py:219-240 の各分岐で返す環境変数キーが
        それぞれのプロバイダー固有であることを検証。
        """
        # Arrange
        credentials = MagicMock()
        credentials.tenantId = "t"
        credentials.clientId = "c"
        credentials.clientSecret = "s"
        credentials.subscriptionId = "sub"
        credentials.authType = "accessKey"
        credentials.accessKey = "AK"
        credentials.secretKey = "SK"
        credentials.sessionToken = "ST"

        # Act
        azure_result = await executor._prepare_region_credentials(credentials, "r", "azure")
        aws_result = await executor._prepare_region_credentials(credentials, "r", "aws")

        # Assert
        # Azure 結果に AWS キーが含まれないこと
        assert "AWS_ACCESS_KEY_ID" not in azure_result
        # AWS 結果に Azure キーが含まれないこと
        assert "AZURE_TENANT_ID" not in aws_result

    @pytest.mark.asyncio
    async def test_none_credentials_replaced_with_empty_string(self, executor):
        """PEXE-SEC-03: None 属性が空文字に変換される

        parallel_executor.py:222-225, 236-239 の `or ""` パターンを検証。
        None がそのまま環境変数に渡されると subprocess が失敗するため。
        """
        # Arrange
        credentials = MagicMock()
        credentials.tenantId = None
        credentials.clientId = None
        credentials.clientSecret = None
        credentials.subscriptionId = None

        # Act
        result = await executor._prepare_region_credentials(credentials, "r", "azure")

        # Assert
        assert result["AZURE_TENANT_ID"] == ""
        assert result["AZURE_CLIENT_ID"] == ""
        assert result["AZURE_CLIENT_SECRET"] == ""
        assert result["AZURE_SUBSCRIPTION_ID"] == ""
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `executor` | 全依存をモック化した ParallelCustodianExecutor（各テストクラス内で定義） | function | No |

### 共通フィクスチャ定義

```python
# test/unit/jobs/tasks/new_custodian_scan/conftest.py に追加（必要に応じて）
#
# executor フィクスチャの共通パターン:
#   MODULE = "app.jobs.tasks.new_custodian_scan.parallel_executor"
#   with patch(f"{MODULE}.TaskLogger"), \
#        patch(f"{MODULE}.CustodianCommandBuilder"), \
#        patch(f"{MODULE}.ResultProcessor"):
#       instance = ParallelCustodianExecutor("test-job")
#   instance.logger = MagicMock()  # アサーション用に差し替え
#
# 注: asyncio のモックは各テストケース内で個別に設定する。
#     create_subprocess_exec, wait_for, sleep 等は
#     f"{MODULE}.asyncio.XXX" でパッチする。
```

---

## 6. テスト実行例

```bash
# parallel_executor テストのみ実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_parallel_executor.py -v

# 特定のテストクラスのみ実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_parallel_executor.py::TestRunCustodianSubprocessWithRetry -v

# カバレッジ付きで実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_parallel_executor.py \
  --cov=app.jobs.tasks.new_custodian_scan.parallel_executor \
  --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_parallel_executor.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 27 | PEXE-001〜PEXE-027 |
| 異常系 | 7 | PEXE-E01〜PEXE-E07 |
| セキュリティ | 3 | PEXE-SEC-01〜PEXE-SEC-03 |
| **合計** | **37** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestParallelExecutorInit` | PEXE-001〜002 | 2 |
| `TestExecuteRegionsParallel` | PEXE-003 | 1 |
| `TestExecuteRegionWithSemaphore` | PEXE-004 | 1 |
| `TestExecuteSingleRegion` | PEXE-005 | 1 |
| `TestPrepareRegionCredentials` | PEXE-006〜008 | 3 |
| `TestRunCustodianSubprocessWithRetry` | PEXE-009〜012 | 4 |
| `TestSimulateCustodianExecution` | PEXE-013, 025 | 2 |
| `TestParseCustodianOutput` | PEXE-014〜018, 026〜027 | 7 |
| `TestProcessParallelResults` | PEXE-019〜024 | 6 |
| `TestParallelExecutorErrors` | PEXE-E01〜PEXE-E07 | 7 |
| `TestParallelExecutorSecurity` | PEXE-SEC-01〜PEXE-SEC-03 | 3 |

### 実装失敗が予想されるテスト

現時点で失敗が予想されるテストはありません。

> 全メソッドの依存をモックするため、実装の内部ロジックのみを検証。外部サービスの状態に依存しない安定したテスト設計。

### 注意事項

- 全 async メソッドのテストに `pytest-asyncio` パッケージが必要
- `--strict-markers` 運用時は `@pytest.mark.security` を `pyproject.toml` に登録
- `asyncio.create_subprocess_exec`, `asyncio.wait_for`, `asyncio.sleep` は `f"{MODULE}.asyncio.XXX"` でパッチ
- `_parse_custodian_output` は `os`, `json` をローカル import するため、`os.path.exists`, `os.walk`, `json.load` 等はモジュールレベルでパッチ
- `_simulate_custodian_execution` は実際に `asyncio.sleep(10)` を呼ぶため、テスト時は必ずモック化

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `_run_custodian_subprocess_with_retry` のリトライテストは `asyncio.create_subprocess_exec` のモックが複雑（呼び出し回数で動作を変える）| テストコードの可読性が低下 | `side_effect` でリストまたはコールバックを使い、呼び出し順を制御 |
| 2 | `_prepare_region_credentials` の role_assumption 分岐は TODO 未実装で空辞書を返す | 将来の実装変更でテスト修正が必要 | TODO が実装された時点でテストケースを拡張 |
| 3 | `_parse_custodian_output` は `os`, `json` をローカル import するため、パッチ先がモジュールレベル（`os.path.exists` 等）になる | 他テストとの干渉リスク | テストクラスまたはメソッド単位でパッチを適用し、スコープを限定 |
| 4 | `_prepare_region_credentials` の `role_assumption` 分岐は TODO 未実装で空辞書を返す | 認証なしの状態で subprocess 実行を試行するため、AWS SDK 側で認証失敗する想定 | STS AssumeRole が実装された時点でテストケースを拡張。現状は空辞書返却の動作を PEXE-007 で検証 |
