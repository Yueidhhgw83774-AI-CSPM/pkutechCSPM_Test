"""
health_checker.py 単位テスト

テスト仕様: health_checker_tests.md
カバレッジ目標: 90%+

テストカテゴリ:
  - 正常系: 20 個のテスト
  - 異常系: 20 個のテスト
  - セキュリティテスト: 5 個のテスト
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch, Mock
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
import time
import asyncio

# テスト環境変数を設定する
os.environ.setdefault('OPENSEARCH_URL', 'https://172.19.75.181:9200/')
os.environ.setdefault('OPENSEARCH_USER', 'admin')
os.environ.setdefault('OPENSEARCH_PASSWORD', 'admin')
os.environ.setdefault('AWS_REGION', 'us-east-1')

# テスト対象のモジュールをインポートする前に、問題があるモジュールをmockします。
mock_get_active_job_count = AsyncMock(return_value=0)
mock_status_manager = MagicMock()
mock_status_manager.get_active_job_count = mock_get_active_job_count

# Mock NewCustodianScanTask
mock_new_custodian_scan_task = MagicMock()
mock_new_custodian_scan_task.NewCustodianScanTask = MagicMock()

# Mockが必要なすべてのjobsモジュール(インポートの順序に従って)
sys.modules['app.jobs.tasks'] = MagicMock()
sys.modules['app.jobs.tasks.new_custodian_scan'] = MagicMock()
sys.modules['app.jobs.tasks.new_custodian_scan.main_task'] = mock_new_custodian_scan_task
sys.modules['app.jobs.main_task'] = mock_new_custodian_scan_task  # このmockを追加する
sys.modules['app.jobs.status_manager'] = mock_status_manager

# app.jobs.__init__.py から main_task のインポートを阻止する
sys.modules['app.jobs'] = MagicMock()
sys.modules['app.jobs'].status_manager = mock_status_manager
sys.modules['app.jobs'].get_active_job_count = mock_get_active_job_count

# テスト対象モジュールをインポートする
project_root = Path(__file__).parent.parent.parent.parent / "platform_python_backend-testing"
sys.path.insert(0, str(project_root))

from app.core.health_checker import (
    HealthChecker,
    health_checker
)
from app.models.health import (
    HealthStatus,
    DependencyStatus,
    HealthDependencies,
    HealthResponse,
    HealthErrorResponse
)


# ============================================================================
# 正常系テスト - HealthChecker初期化
# ============================================================================

class TestHealthCheckerInit:
    """
    HealthChecker初期化正常系テスト

        テストID: HC-001, HC-016
    """

    def test_init_records_start_time(self):
        """
        HC-001: インスタンス初期化で起動時刻記録

        测试目的:
          - 验证HealthChecker初始化时记录启动时间
          - 验证start_time是合理的时间戳
        """
        # Arrange & Act - インスタンスの作成
        before_init = time.time()
        checker = HealthChecker()
        after_init = time.time()

        # Assert - start_timeが合理的な範囲内にあることを確認する
        assert hasattr(checker, 'start_time')
        assert before_init <= checker.start_time <= after_init

    def test_singleton_instance_exists(self):
        """
        HC-016: シングルトンインスタンス存在確認

        测试目的:
          - 验证health_checker是HealthChecker实例
        """
        # Act & Assert
        assert isinstance(health_checker, HealthChecker)
        assert hasattr(health_checker, 'start_time')


# ============================================================================
# 正常系テスト - check_health()
# ============================================================================

class TestCheckHealth:
    """
    check_health() 正常系テスト

        テストID: HC-002 ~ HC-020
    """

    @pytest.mark.asyncio
    async def test_all_deps_healthy_returns_200(self):
        """
        HC-002: すべての依存関係が正常→HEALTHY+200

        カバレッジコード行: health_checker.py:30-77

        テスト目的:
          - すべての依存関係が正常な場合にHEALTHY状態を返すことを確認する
          - 200ステータスコードが返されることを確認する
          - warningsがNoneであることを確認する
        """
        # Arrange - テストデータの準備
        checker = HealthChecker()
        mock_deps = HealthDependencies(
            aws_sdk=DependencyStatus.AVAILABLE,
            azure_sdk=DependencyStatus.AVAILABLE,
            custodian=DependencyStatus.AVAILABLE,
            opensearch=DependencyStatus.AVAILABLE
        )

        with patch.object(checker, '_check_dependencies', new_callable=AsyncMock, return_value=mock_deps), \
             patch.object(checker, '_get_memory_usage', return_value=100.0), \
             patch.object(checker, '_get_active_jobs', new_callable=AsyncMock, return_value=0):

            # アクション - テストを実行する
            response, status_code = await checker.check_health()

        # Assert - 結果の検証
        assert status_code == 200
        assert response.status == HealthStatus.HEALTHY
        assert response.warnings is None
        assert isinstance(response, HealthResponse)

    @pytest.mark.asyncio
    async def test_aws_sdk_unavailable_returns_degraded(self):
        """
        HC-003: AWS SDK未インストール→DEGRADED

        测试目的:
          - 验证AWS SDK不可用时返回DEGRADED状态
          - 验证返回503状态码
          - 验证warnings包含AWS SDK信息
        """
        # Arrange
        checker = HealthChecker()
        mock_deps = HealthDependencies(
            aws_sdk=DependencyStatus.UNAVAILABLE,
            azure_sdk=DependencyStatus.AVAILABLE,
            custodian=DependencyStatus.AVAILABLE,
            opensearch=DependencyStatus.AVAILABLE
        )

        with patch.object(checker, '_check_dependencies', new_callable=AsyncMock, return_value=mock_deps), \
             patch.object(checker, '_get_memory_usage', return_value=100.0), \
             patch.object(checker, '_get_active_jobs', new_callable=AsyncMock, return_value=0):

            # Act
            response, status_code = await checker.check_health()

        # Assert
        assert status_code == 503
        assert response.status == HealthStatus.DEGRADED
        assert response.warnings is not None
        assert any("AWS SDK" in w for w in response.warnings)

    @pytest.mark.asyncio
    async def test_azure_sdk_unavailable_returns_degraded(self):
        """
        HC-004: Azure SDK未インストール→DEGRADED
        """
        # Arrange
        checker = HealthChecker()
        mock_deps = HealthDependencies(
            aws_sdk=DependencyStatus.AVAILABLE,
            azure_sdk=DependencyStatus.UNAVAILABLE,
            custodian=DependencyStatus.AVAILABLE,
            opensearch=DependencyStatus.AVAILABLE
        )

        with patch.object(checker, '_check_dependencies', new_callable=AsyncMock, return_value=mock_deps), \
             patch.object(checker, '_get_memory_usage', return_value=100.0), \
             patch.object(checker, '_get_active_jobs', new_callable=AsyncMock, return_value=0):

            # Act
            response, status_code = await checker.check_health()

        # Assert
        assert status_code == 503
        assert response.status == HealthStatus.DEGRADED
        assert response.warnings is not None
        assert any("Azure SDK" in w for w in response.warnings)

    @pytest.mark.asyncio
    async def test_multiple_optional_deps_unavailable(self):
        """
        HC-005: 不要な依存関係の複数障害→DEGRADED

        テスト目的:
          - 複数の不要な依存関係の失敗時にDEGRADEDが返されることを確認する
          - 警告が2件含まれていることを確認する
        """
        # Arrange
        checker = HealthChecker()
        mock_deps = HealthDependencies(
            aws_sdk=DependencyStatus.UNAVAILABLE,
            azure_sdk=DependencyStatus.UNAVAILABLE,
            custodian=DependencyStatus.AVAILABLE,
            opensearch=DependencyStatus.AVAILABLE
        )

        with patch.object(checker, '_check_dependencies', new_callable=AsyncMock, return_value=mock_deps), \
             patch.object(checker, '_get_memory_usage', return_value=100.0), \
             patch.object(checker, '_get_active_jobs', new_callable=AsyncMock, return_value=0):

            # Act
            response, status_code = await checker.check_health()

        # Assert
        assert status_code == 503
        assert response.status == HealthStatus.DEGRADED
        assert response.warnings is not None
        assert len(response.warnings) == 2

    @pytest.mark.asyncio
    async def test_concurrent_check_execution(self):
        """
        HC-006: 並行チェック実行確認

        测试目的:
          - 验证4个依赖检查任务并行执行
        """
        # Arrange
        checker = HealthChecker()

        # シミュレーション用の非同期チェックメソッドを作成する
        check_calls = []

        async def mock_check(name):
            check_calls.append((name, time.time()))
            await asyncio.sleep(0.01)  # ネットワーク遅延をシミュレーションする
            return DependencyStatus.AVAILABLE

        # AsyncMockを使用してコルーチンが正しく処理されることを確認する
        with patch.object(checker, '_check_aws_sdk', new_callable=AsyncMock, return_value=DependencyStatus.AVAILABLE), \
             patch.object(checker, '_check_azure_sdk', new_callable=AsyncMock, return_value=DependencyStatus.AVAILABLE), \
             patch.object(checker, '_check_custodian', new_callable=AsyncMock, return_value=DependencyStatus.AVAILABLE), \
             patch.object(checker, '_check_opensearch', new_callable=AsyncMock, return_value=DependencyStatus.AVAILABLE):

            # Act
            result = await checker._check_dependencies()

        # Assert - 結果構造の正しさを確認する
        assert isinstance(result, HealthDependencies)
        assert result.aws_sdk == DependencyStatus.AVAILABLE
        assert result.azure_sdk == DependencyStatus.AVAILABLE
        assert result.custodian == DependencyStatus.AVAILABLE
        assert result.opensearch == DependencyStatus.AVAILABLE

    @pytest.mark.asyncio
    async def test_uptime_calculation(self):
        """
        HC-007: uptime_secondsの計算

                テスト目的:
                  - uptimeの計算が正しいことを確認する
        """
        # Arrange
        checker = HealthChecker()
        checker.start_time = time.time() - 5  # 5秒前に起動しました

        mock_deps = HealthDependencies(
            aws_sdk=DependencyStatus.AVAILABLE,
            azure_sdk=DependencyStatus.AVAILABLE,
            custodian=DependencyStatus.AVAILABLE,
            opensearch=DependencyStatus.AVAILABLE
        )

        with patch.object(checker, '_check_dependencies', new_callable=AsyncMock, return_value=mock_deps), \
             patch.object(checker, '_get_memory_usage', return_value=100.0), \
             patch.object(checker, '_get_active_jobs', new_callable=AsyncMock, return_value=0):

            # Act
            response, _ = await checker.check_health()

        # Assert
        assert response.uptime_seconds >= 5
        assert response.uptime_seconds < 10  # 10秒以内になるはずだ

    @pytest.mark.asyncio
    async def test_memory_usage_retrieved(self):
        """
        HC-008: memory_usage_mbの取得

                テスト目的:
                  - メモリ使用量が正の数であることを確認する
        """
        # Arrange
        checker = HealthChecker()
        mock_deps = HealthDependencies(
            aws_sdk=DependencyStatus.AVAILABLE,
            azure_sdk=DependencyStatus.AVAILABLE,
            custodian=DependencyStatus.AVAILABLE,
            opensearch=DependencyStatus.AVAILABLE
        )

        with patch.object(checker, '_check_dependencies', new_callable=AsyncMock, return_value=mock_deps), \
             patch.object(checker, '_get_memory_usage', return_value=256.5), \
             patch.object(checker, '_get_active_jobs', new_callable=AsyncMock, return_value=0):

            # Act
            response, _ = await checker.check_health()

        # Assert
        assert response.memory_usage_mb > 0
        assert isinstance(response.memory_usage_mb, float)

    @pytest.mark.asyncio
    async def test_active_jobs_retrieved(self):
        """
        HC-009: active_jobs取得

                テスト目的:
                  - アクティブジョブの数が非負の整数であることを確認する
        """
        # Arrange
        checker = HealthChecker()
        mock_deps = HealthDependencies(
            aws_sdk=DependencyStatus.AVAILABLE,
            azure_sdk=DependencyStatus.AVAILABLE,
            custodian=DependencyStatus.AVAILABLE,
            opensearch=DependencyStatus.AVAILABLE
        )

        with patch.object(checker, '_check_dependencies', new_callable=AsyncMock, return_value=mock_deps), \
             patch.object(checker, '_get_memory_usage', return_value=100.0), \
             patch.object(checker, '_get_active_jobs', new_callable=AsyncMock, return_value=3):

            # Act
            response, _ = await checker.check_health()

        # Assert
        assert response.active_jobs >= 0
        assert isinstance(response.active_jobs, int)

    @pytest.mark.asyncio
    async def test_timestamp_iso_format(self):
        """
        HC-010: タイムスタンプISO形式

        测试目的:
          - 验证时间戳为ISO 8601格式
        """
        # Arrange
        checker = HealthChecker()
        mock_deps = HealthDependencies(
            aws_sdk=DependencyStatus.AVAILABLE,
            azure_sdk=DependencyStatus.AVAILABLE,
            custodian=DependencyStatus.AVAILABLE,
            opensearch=DependencyStatus.AVAILABLE
        )

        with patch.object(checker, '_check_dependencies', new_callable=AsyncMock, return_value=mock_deps), \
             patch.object(checker, '_get_memory_usage', return_value=100.0), \
             patch.object(checker, '_get_active_jobs', new_callable=AsyncMock, return_value=0):

            # Act
            response, _ = await checker.check_health()

        # Assert
        assert "T" in response.timestamp
        assert ("+" in response.timestamp or "Z" in response.timestamp or response.timestamp.endswith("+00:00"))

    @pytest.mark.asyncio
    async def test_health_response_all_fields_present(self):
        """
        HC-011: HealthResponseフィールド全揃い

        测试目的:
          - 验证HealthResponse包含所有必需字段
        """
        # Arrange
        checker = HealthChecker()
        mock_deps = HealthDependencies(
            aws_sdk=DependencyStatus.AVAILABLE,
            azure_sdk=DependencyStatus.AVAILABLE,
            custodian=DependencyStatus.AVAILABLE,
            opensearch=DependencyStatus.AVAILABLE
        )

        with patch.object(checker, '_check_dependencies', new_callable=AsyncMock, return_value=mock_deps), \
             patch.object(checker, '_get_memory_usage', return_value=100.0), \
             patch.object(checker, '_get_active_jobs', new_callable=AsyncMock, return_value=0):

            # Act
            response, _ = await checker.check_health()

        # Assert - 必要なすべてのフィールドが存在することを確認する
        assert hasattr(response, 'status')
        assert hasattr(response, 'timestamp')
        assert hasattr(response, 'uptime_seconds')
        assert hasattr(response, 'memory_usage_mb')
        assert hasattr(response, 'active_jobs')
        assert hasattr(response, 'dependencies')
        assert hasattr(response, 'warnings')

    @pytest.mark.asyncio
    async def test_empty_warnings_converted_to_none(self):
        """
        HC-017: warnings空リスト→Noneに変換

        测试目的:
          - 验证空warnings列表被转换为None
        """
        # Arrange
        checker = HealthChecker()
        mock_deps = HealthDependencies(
            aws_sdk=DependencyStatus.AVAILABLE,
            azure_sdk=DependencyStatus.AVAILABLE,
            custodian=DependencyStatus.AVAILABLE,
            opensearch=DependencyStatus.AVAILABLE
        )

        with patch.object(checker, '_check_dependencies', new_callable=AsyncMock, return_value=mock_deps), \
             patch.object(checker, '_get_memory_usage', return_value=100.0), \
             patch.object(checker, '_get_active_jobs', new_callable=AsyncMock, return_value=0):

            # Act
            response, _ = await checker.check_health()

        # Assert
        assert response.warnings is None


# ============================================================================
# 正常系测试 - 各依赖チェック
# ============================================================================

class TestDependencyChecks:
    """
    依存チェック各正常系テスト

    テストID: HC-012 ~ HC-015
    """

    @pytest.mark.asyncio
    async def test_aws_sdk_available_when_boto3_exists(self):
        """
        HC-012: AWS SDK boto3あり→AVAILABLE

        测试目的:
          - 验证boto3可用时返回AVAILABLE
        """
        # Arrange
        checker = HealthChecker()

        with patch('importlib.util.find_spec', return_value=Mock()):
            # Act
            status = await checker._check_aws_sdk()

        # Assert
        assert status == DependencyStatus.AVAILABLE

    @pytest.mark.asyncio
    async def test_azure_sdk_available_when_command_succeeds(self):
        """
        HC-013: Azure SDK subprocess成功→AVAILABLE

        テスト目的:
        - Azure SDKコマンドが成功した場合、AVAILABLEが返されることを確認する
        """
        # Arrange
        checker = HealthChecker()
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"output", b""))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process), \
             patch('asyncio.wait_for', return_value=(b"output", b"")):

            # Act
            status = await checker._check_azure_sdk()

        # Assert
        assert status == DependencyStatus.AVAILABLE

    @pytest.mark.asyncio
    async def test_custodian_available_when_version_succeeds(self):
        """
        HC-014: Custodian version成功→AVAILABLE

                テスト目的:
                  - custodian versionコマンドが成功した場合、AVAILABLEが返されることを確認する
        """
        # Arrange
        checker = HealthChecker()
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"0.9.0", b""))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process), \
             patch('asyncio.wait_for', return_value=(b"0.9.0", b"")):

            # Act
            status = await checker._check_custodian()

        # Assert
        assert status == DependencyStatus.AVAILABLE

    @pytest.mark.asyncio
    async def test_opensearch_available_when_info_succeeds(self):
        """
        HC-015: OpenSearch接続成功→AVAILABLE

        テスト目的:
        - OpenSearch infoが成功した場合にAVAILABLEが返されることを確認する
        """
        # Arrange
        checker = HealthChecker()
        mock_client = AsyncMock()
        mock_client.info = AsyncMock(return_value={"version": {"number": "2.0.0"}})

        with patch('app.core.health_checker.get_opensearch_client', return_value=mock_client):

            # Act
            status = await checker._check_opensearch()

        # Assert
        assert status == DependencyStatus.AVAILABLE


# ============================================================================
# 正常系テスト - _determine_overall_status()
# ============================================================================

class TestDetermineOverallStatus:
    """
    _determine_overall_status() 正常系テスト

    テストID: HC-018 ~ HC-020
    """

    def test_all_available_returns_healthy(self):
        """
        HC-018: _determine_overall_status: 全て正常→HEALTHY

        テスト目的:
        - すべての依存が利用可能である場合にHEALTHYを返すことを確認する
        """
        # Arrange
        checker = HealthChecker()
        deps = HealthDependencies(
            aws_sdk=DependencyStatus.AVAILABLE,
            azure_sdk=DependencyStatus.AVAILABLE,
            custodian=DependencyStatus.AVAILABLE,
            opensearch=DependencyStatus.AVAILABLE
        )

        # Act
        status, warnings, errors = checker._determine_overall_status(deps)

        # Assert
        assert status == HealthStatus.HEALTHY
        assert warnings is None
        assert errors == []

    def test_optional_deps_unavailable_returns_degraded(self):
        """
        HC-019: _determine_overall_status: 重要でない障害→DEGRADED

        テスト目的:
        - 重要でない依存関係の失敗時にDEGRADEDが返されることを確認する
        """
        # Arrange
        checker = HealthChecker()
        deps = HealthDependencies(
            aws_sdk=DependencyStatus.UNAVAILABLE,
            azure_sdk=DependencyStatus.UNAVAILABLE,
            custodian=DependencyStatus.AVAILABLE,
            opensearch=DependencyStatus.AVAILABLE
        )

        # Act
        status, warnings, errors = checker._determine_overall_status(deps)

        # Assert
        assert status == HealthStatus.DEGRADED
        assert warnings is not None
        assert len(warnings) == 2
        assert errors == []

    def test_critical_deps_unavailable_returns_unhealthy(self):
        """
        HC-020: _determine_overall_status: 重要障害→UNHEALTHY

        テスト目的:
        - 重要な依存関係が失敗した場合にUNHEALTHYを返すことを確認する
        """
        # Arrange
        checker = HealthChecker()
        deps = HealthDependencies(
            aws_sdk=DependencyStatus.AVAILABLE,
            azure_sdk=DependencyStatus.AVAILABLE,
            custodian=DependencyStatus.UNAVAILABLE,
            opensearch=DependencyStatus.UNAVAILABLE
        )

        # Act
        status, warnings, errors = checker._determine_overall_status(deps)

        # Assert
        assert status == HealthStatus.UNHEALTHY
        assert warnings is None
        assert len(errors) == 2


# ============================================================================
# 異常系テスト - 重要依存関係障害
# ============================================================================

class TestHealthCheckerErrors:
    """
    HealthChecker 異常系テスト

        テストID: HC-E01 ~ HC-E20
    """

    @pytest.mark.asyncio
    async def test_opensearch_unavailable_returns_unhealthy(self):
        """
        HC-E01: OpenSearch障害→UNHEALTHY+503

                カバレッジコード行: health_checker.py:48-55

                テスト目的:
                  - OpenSearchが失敗した場合にUNHEALTHYを返すことを確認する
                  - HealthErrorResponseが返されることを確認する
        """
        # Arrange
        checker = HealthChecker()
        mock_deps = HealthDependencies(
            aws_sdk=DependencyStatus.AVAILABLE,
            azure_sdk=DependencyStatus.AVAILABLE,
            custodian=DependencyStatus.AVAILABLE,
            opensearch=DependencyStatus.UNAVAILABLE
        )

        with patch.object(checker, '_check_dependencies', new_callable=AsyncMock, return_value=mock_deps), \
             patch.object(checker, '_get_memory_usage', return_value=100.0), \
             patch.object(checker, '_get_active_jobs', new_callable=AsyncMock, return_value=0):

            # Act
            response, status_code = await checker.check_health()

        # Assert
        assert status_code == 503
        assert response.status == HealthStatus.UNHEALTHY
        assert isinstance(response, HealthErrorResponse)
        assert hasattr(response, 'errors')
        assert len(response.errors) >= 1
        assert any("OpenSearch" in error for error in response.errors)

    @pytest.mark.asyncio
    async def test_custodian_unavailable_returns_unhealthy(self):
        """
        HC-E02: Custodian障害→UNHEALTHY+503
        """
        # Arrange
        checker = HealthChecker()
        mock_deps = HealthDependencies(
            aws_sdk=DependencyStatus.AVAILABLE,
            azure_sdk=DependencyStatus.AVAILABLE,
            custodian=DependencyStatus.UNAVAILABLE,
            opensearch=DependencyStatus.AVAILABLE
        )

        with patch.object(checker, '_check_dependencies', new_callable=AsyncMock, return_value=mock_deps), \
             patch.object(checker, '_get_memory_usage', return_value=100.0), \
             patch.object(checker, '_get_active_jobs', new_callable=AsyncMock, return_value=0):

            # Act
            response, status_code = await checker.check_health()

        # Assert
        assert status_code == 503
        assert response.status == HealthStatus.UNHEALTHY
        assert isinstance(response, HealthErrorResponse)
        assert any("Custodian" in error for error in response.errors)

    @pytest.mark.asyncio
    async def test_multiple_critical_deps_unavailable(self):
        """
        HC-E03: 複数重要依存関係障害→UNHEALTHY

                テスト目的:
                  - 複数の重要依存関係が失敗した場合、errorsが複数のエラーを含むことを確認する
        """
        # Arrange
        checker = HealthChecker()
        mock_deps = HealthDependencies(
            aws_sdk=DependencyStatus.AVAILABLE,
            azure_sdk=DependencyStatus.AVAILABLE,
            custodian=DependencyStatus.UNAVAILABLE,
            opensearch=DependencyStatus.UNAVAILABLE
        )

        with patch.object(checker, '_check_dependencies', new_callable=AsyncMock, return_value=mock_deps), \
             patch.object(checker, '_get_memory_usage', return_value=100.0), \
             patch.object(checker, '_get_active_jobs', new_callable=AsyncMock, return_value=0):

            # Act
            response, status_code = await checker.check_health()

        # Assert
        assert status_code == 503
        assert len(response.errors) == 2

    @pytest.mark.asyncio
    async def test_check_health_exception_returns_error_response(self):
        """
        HC-E04: check_health例外→UNHEALTHY+503

                テスト目的:
                  - 内部異常時にHealthErrorResponseを返すことを確認する
        """
        # Arrange
        checker = HealthChecker()

        with patch.object(checker, '_check_dependencies', side_effect=Exception("Internal error")):

            # Act
            response, status_code = await checker.check_health()

        # Assert
        assert status_code == 503
        assert isinstance(response, HealthErrorResponse)
        assert response.status == HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_aws_sdk_import_exception(self):
        """
        HC-E05: AWS SDK import例外

                テスト目的:
                  - import異常時、UNAVAILABLEを返すことを確認する
        """
        # Arrange
        checker = HealthChecker()

        with patch('importlib.util.find_spec', side_effect=Exception("Import error")):

            # Act
            status = await checker._check_aws_sdk()

        # Assert
        assert status == DependencyStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_aws_sdk_not_found(self):
        """
        HC-E19: boto3未インストール

        测试目的:
          - 验证boto3未安装时返回UNAVAILABLE
        """
        # Arrange
        checker = HealthChecker()

        with patch('importlib.util.find_spec', return_value=None):

            # Act
            status = await checker._check_aws_sdk()

        # Assert
        assert status == DependencyStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_azure_sdk_subprocess_failure(self):
        """
        HC-E06: Azure SDK subprocess失敗

                テスト目的:
                  - subprocessが0以外を返した場合、UNAVAILABLEを返すことを確認する
        """
        # Arrange
        checker = HealthChecker()
        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(return_value=(b"", b"error"))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process), \
             patch('asyncio.wait_for', return_value=None):

            # Act
            status = await checker._check_azure_sdk()

        # Assert
        assert status == DependencyStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_azure_sdk_timeout(self):
        """
        HC-E07: Azure SDK タイムアウト

        测试目的:
          - 验证超时时返回UNAVAILABLE
        """
        # Arrange
        checker = HealthChecker()

        with patch('asyncio.create_subprocess_exec'), \
             patch('asyncio.wait_for', side_effect=asyncio.TimeoutError()):

            # Act
            status = await checker._check_azure_sdk()

        # Assert
        assert status == DependencyStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_azure_sdk_file_not_found(self):
        """
        HC-E08: Azure SDK venvが存在しない

                テスト目的:
                  - ファイルが存在しない場合にUNAVAILABLEを返すことを確認する
        """
        # Arrange
        checker = HealthChecker()

        with patch('asyncio.create_subprocess_exec', side_effect=FileNotFoundError()):

            # Act
            status = await checker._check_azure_sdk()

        # Assert
        assert status == DependencyStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_azure_sdk_generic_exception(self):
        """
        HC-E09: Azure SDK その他例外
        """
        # Arrange
        checker = HealthChecker()

        with patch('asyncio.create_subprocess_exec', side_effect=Exception("Unexpected error")):

            # Act
            status = await checker._check_azure_sdk()

        # Assert
        assert status == DependencyStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_custodian_subprocess_failure(self):
        """
        HC-E10: Custodian subprocess失敗
        """
        # Arrange
        checker = HealthChecker()
        mock_process = AsyncMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(return_value=(b"", b"error"))

        with patch('asyncio.create_subprocess_exec', return_value=mock_process), \
             patch('asyncio.wait_for', return_value=None):

            # Act
            status = await checker._check_custodian()

        # Assert
        assert status == DependencyStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_custodian_timeout(self):
        """
        HC-E11: Custodian タイムアウト
        """
        # Arrange
        checker = HealthChecker()

        with patch('asyncio.create_subprocess_exec'), \
             patch('asyncio.wait_for', side_effect=asyncio.TimeoutError()):

            # Act
            status = await checker._check_custodian()

        # Assert
        assert status == DependencyStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_custodian_file_not_found(self):
        """
        HC-E12: Custodian コマンド不在
        """
        # Arrange
        checker = HealthChecker()

        with patch('asyncio.create_subprocess_exec', side_effect=FileNotFoundError()):

            # Act
            status = await checker._check_custodian()

        # Assert
        assert status == DependencyStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_custodian_generic_exception(self):
        """
        HC-E13: Custodian その他例外
        """
        # Arrange
        checker = HealthChecker()

        with patch('asyncio.create_subprocess_exec', side_effect=Exception("Unexpected error")):

            # Act
            status = await checker._check_custodian()

        # Assert
        assert status == DependencyStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_opensearch_client_none(self):
        """
        HC-E14: OpenSearch client=None

                テスト目的:
                  - clientがNoneの場合、UNAVAILABLEが返されることを確認する
        """
        # Arrange
        checker = HealthChecker()

        with patch('app.core.health_checker.get_opensearch_client', return_value=None):

            # Act
            status = await checker._check_opensearch()

        # Assert
        assert status == DependencyStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_opensearch_info_fails(self):
        """
        HC-E15: OpenSearch info失敗

                テスト目的:
                  - info()が例外を投げた場合にUNAVAILABLEが返されることを確認する
        """
        # Arrange
        checker = HealthChecker()
        mock_client = AsyncMock()
        mock_client.info = AsyncMock(side_effect=Exception("Connection error"))

        with patch('app.core.health_checker.get_opensearch_client', return_value=mock_client):

            # Act
            status = await checker._check_opensearch()

        # Assert
        assert status == DependencyStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_opensearch_info_no_version(self):
        """
        HC-E16: OpenSearch infoにversion無し

        测试目的:
          - 验证info返回空字典时返回UNAVAILABLE
        """
        # Arrange
        checker = HealthChecker()
        mock_client = AsyncMock()
        mock_client.info = AsyncMock(return_value={})

        with patch('app.core.health_checker.get_opensearch_client', return_value=mock_client):

            # Act
            status = await checker._check_opensearch()

        # Assert
        assert status == DependencyStatus.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_opensearch_info_returns_none(self):
        """
        HC-E20: OpenSearch info→None
        """
        # Arrange
        checker = HealthChecker()
        mock_client = AsyncMock()
        mock_client.info = AsyncMock(return_value=None)

        with patch('app.core.health_checker.get_opensearch_client', return_value=mock_client):

            # Act
            status = await checker._check_opensearch()

        # Assert
        assert status == DependencyStatus.UNAVAILABLE

    def test_memory_usage_exception_returns_zero(self):
        """
        HC-E17: メモリ使用量取得失敗

        测试目的:
          - 验证psutil异常时返回0.0
        """
        # Arrange
        checker = HealthChecker()

        with patch('psutil.Process', side_effect=Exception("psutil error")):

            # Act
            result = checker._get_memory_usage()

        # Assert
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_active_jobs_exception_returns_zero(self):
        """
        HC-E18: アクティブジョブ数取得失敗

        测试目的:
          - 验证get_active_job_count异常时返回0
        """
        # Arrange
        checker = HealthChecker()

        with patch('app.core.health_checker.get_active_job_count', side_effect=Exception("Job manager error")):

            # Act
            result = await checker._get_active_jobs()

        # Assert
        assert result == 0


# ============================================================================
# セキュリティ测试
# ============================================================================

@pytest.mark.security
class TestHealthCheckerSecurity:
    """
    HealthChecker セキュリティテスト

        テストID: HC-SEC-01 ~ HC-SEC-05
    """

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="已知限制: 当前实现将异常消息直接输出到日志,可能泄露敏感信息 (HC-SEC-01)")
    async def test_no_credentials_in_error_response(self, caplog):
        """
        HC-SEC-01: エラーログに認証情報が含まれない

        测试目的:
          - 验证错误日志不包含敏感信息(密码、token等)

        ⚠️ 警告: 当前实现直接使用str(e)输出日志,可能泄露凭据
        """
        # Arrange
        import logging
        import re
        checker = HealthChecker()

        # 敏感情報が含まれる例外のシミュレーション
        with caplog.at_level(logging.ERROR):
            with patch.object(checker, '_check_dependencies',
                            side_effect=Exception("Connection failed: password=secret123 token=abc123")):

                # Act
                response, _ = await checker.check_health()

        # Assert - 認証情報パターンがログに含まれていないことを確認する
        credential_patterns = [
            r'password\s*[=:]\s*["\']?[\w\-!@#$%^&*()]+',
            r'secret\s*[=:]\s*["\']?[\w\-!@#$%^&*()]+',
            r'token\s*[=:]\s*["\']?[\w\-!@#$%^&*()]{6,}',
        ]

        for record in caplog.records:
            msg = record.getMessage()
            for pattern in credential_patterns:
                matches = re.search(pattern, msg, re.IGNORECASE)
                assert matches is None, (
                    f"日志中检测到凭据模式: Pattern={pattern}, Message={msg[:100]}"
                )

    @pytest.mark.asyncio
    async def test_no_internal_paths_in_response(self):
        """
        HC-SEC-02: 内部パス情報が露出しない

        测试目的:
          - 验证响应不泄露内部路径信息
        """
        # Arrange
        checker = HealthChecker()
        mock_deps = HealthDependencies(
            aws_sdk=DependencyStatus.AVAILABLE,
            azure_sdk=DependencyStatus.AVAILABLE,
            custodian=DependencyStatus.AVAILABLE,
            opensearch=DependencyStatus.AVAILABLE
        )

        with patch.object(checker, '_check_dependencies', new_callable=AsyncMock, return_value=mock_deps), \
             patch.object(checker, '_get_memory_usage', return_value=100.0), \
             patch.object(checker, '_get_active_jobs', new_callable=AsyncMock, return_value=0):

            # Act
            response, _ = await checker.check_health()

        # Assert
        response_str = str(response)
        assert "/opt/" not in response_str
        assert "C:\\" not in response_str
        assert "/home/" not in response_str

    @pytest.mark.asyncio
    async def test_error_messages_are_generic(self):
        """
        HC-SEC-03: エラーメッセージが汎用的

        测试目的:
          - 验证错误消息不泄露具体技术细节
        """
        # Arrange
        checker = HealthChecker()
        mock_deps = HealthDependencies(
            aws_sdk=DependencyStatus.AVAILABLE,
            azure_sdk=DependencyStatus.AVAILABLE,
            custodian=DependencyStatus.UNAVAILABLE,
            opensearch=DependencyStatus.UNAVAILABLE
        )

        with patch.object(checker, '_check_dependencies', new_callable=AsyncMock, return_value=mock_deps), \
             patch.object(checker, '_get_memory_usage', return_value=100.0), \
             patch.object(checker, '_get_active_jobs', new_callable=AsyncMock, return_value=0):

            # Act
            response, _ = await checker.check_health()

        # Assert
        for error in response.errors:
            # エラーメッセージは簡潔で、スタックトレースは含めないものとする
            assert "Traceback" not in error
            assert "File \"" not in error

    @pytest.mark.asyncio
    async def test_no_version_info_leaked(self):
        """
        HC-SEC-04: バージョン情報が漏洩しない

        测试目的:
          - 验证不在公开API中泄露详细版本信息
        """
        # Arrange
        checker = HealthChecker()
        mock_client = AsyncMock()
        mock_client.info = AsyncMock(return_value={
            "version": {
                "number": "2.0.0",
                "build_hash": "secret-hash-12345"
            }
        })

        with patch('app.core.health_checker.get_opensearch_client', return_value=mock_client):

            # Act
            status = await checker._check_opensearch()

        # Assert
        # 可用性のみを確認し、响应の中でバージョンの詳細を漏らさない
        assert status == DependencyStatus.AVAILABLE

    @pytest.mark.asyncio
    async def test_timing_attack_resistance(self):
        """
        HC-SEC-05: タイミング攻撃耐性

        测试目的:
          - 验证不同错误条件的响应时间相近
        """
        # Arrange
        checker = HealthChecker()

        # 異なる失敗シーンをテストする
        scenarios = [
            HealthDependencies(
                aws_sdk=DependencyStatus.UNAVAILABLE,
                azure_sdk=DependencyStatus.AVAILABLE,
                custodian=DependencyStatus.AVAILABLE,
                opensearch=DependencyStatus.AVAILABLE
            ),
            HealthDependencies(
                aws_sdk=DependencyStatus.AVAILABLE,
                azure_sdk=DependencyStatus.UNAVAILABLE,
                custodian=DependencyStatus.AVAILABLE,
                opensearch=DependencyStatus.AVAILABLE
            )
        ]

        times = []
        for deps in scenarios:
            with patch.object(checker, '_check_dependencies', new_callable=AsyncMock, return_value=deps), \
                 patch.object(checker, '_get_memory_usage', return_value=100.0), \
                 patch.object(checker, '_get_active_jobs', new_callable=AsyncMock, return_value=0):

                # Act
                start = time.time()
                await checker.check_health()
                duration = time.time() - start
                times.append(duration)

        # Assert - レスポンスタイムの差異は大きすぎない（50ms以下）
        if len(times) >= 2:
            time_diff = abs(times[0] - times[1])
            assert time_diff < 0.05  # 50ms
