"""
Jobs Router テスト用 conftest.py
pytest フィクスチャとテスト結果収集を提供
"""
import pytest
import sys
import os
import importlib
from pathlib import Path
from dotenv import load_dotenv
import json
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch

# .envファイルから環境変数を読み込む
env_path = Path(__file__).parents[3] / '.env'
load_dotenv(env_path)

# source_root を環境変数から取得
source_root = os.getenv('soure_root', 'C:\\pythonProject\\python_ai_cspm\\platform_python_backend-testing\\')
if source_root not in sys.path:
    sys.path.insert(0, source_root)

from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient


# ==================== テスト結果収集 ====================
class TestResultCollector:
    """テスト結果を収集するクラス"""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.stats = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "error": 0
        }
    
    def add_result(self, test_name: str, outcome: str, duration: float, error_msg: str = None):
        """テスト結果を追加"""
        self.results.append({
            "test_name": test_name,
            "outcome": outcome,
            "duration": duration,
            "error_message": error_msg,
            "timestamp": datetime.now().isoformat()
        })
        self.stats["total"] += 1
        if outcome in self.stats:
            self.stats[outcome] += 1


@pytest.fixture(scope="session")
def test_result_collector():
    """テスト結果コレクターのフィクスチャ"""
    return TestResultCollector()


# ==================== テストフィクスチャ ====================
@pytest.fixture(scope="function")
def mock_status_manager():
    """status_manager モジュールのモック - 每个测试自动使用"""
    # 导入真实的status_manager
    from app.jobs import status_manager
    
    # 清空job_statuses以确保测试隔离
    original_statuses = status_manager.job_statuses.copy()
    status_manager.job_statuses.clear()
    
    # 创建一个简单的对象来访问job_statuses和mock函数
    class StatusManager:
        job_statuses = status_manager.job_statuses
        check_job_exclusion = MagicMock(return_value=None)
        try_initialize_job_exclusive = MagicMock(return_value=("test-job-id", None))
        get_job_status_sync = MagicMock(return_value=None)
        get_job_result_sync = MagicMock(return_value=None)
        
    manager = StatusManager()
    yield manager
    
    # 测试后恢复
    status_manager.job_statuses.clear()
    status_manager.job_statuses.update(original_statuses)


@pytest.fixture
def mock_crypto():
    """暗号化関連関数のモック"""
    with patch('app.jobs.router.decrypt_opensearch_dashboard_payload') as mock_decrypt, \
         patch('app.jobs.router.verify_auth_hash') as mock_verify, \
         patch('app.jobs.router._get_shared_secret') as mock_secret:
        
        mock_crypto_obj = MagicMock()
        mock_crypto_obj.decrypt_opensearch_dashboard_payload = mock_decrypt
        mock_crypto_obj.verify_auth_hash = mock_verify
        mock_crypto_obj._get_shared_secret = mock_secret
        
        # デフォルトの動作を設定
        mock_secret.return_value = "test-shared-secret"
        mock_verify.return_value = True
        mock_decrypt.return_value = {}
        
        yield mock_crypto_obj


@pytest.fixture
def mock_tasks():
    """バックグラウンドタスクのモック"""
    with patch('app.jobs.router.run_file_processing_task') as mock_file, \
         patch('app.jobs.router.run_policy_batch_generation_task') as mock_policy, \
         patch('app.jobs.router.run_custodian_scan_task') as mock_scan, \
         patch('app.jobs.router.new_run_custodian_scan_task') as mock_new_scan:
        
        mock_tasks_obj = MagicMock()
        mock_tasks_obj.file_processing = mock_file
        mock_tasks_obj.policy_batch = mock_policy
        mock_tasks_obj.custodian_scan = mock_scan
        mock_tasks_obj.new_custodian_scan = mock_new_scan
        
        yield mock_tasks_obj


@pytest.fixture
async def test_app(mock_status_manager, mock_tasks, mock_crypto):
    """テスト用Fastアプリケーション"""
    from fastapi import FastAPI
    import sys
    
    # app.mainを直接importせず、新しいテスト用アプリを作成
    app = FastAPI()
    
    # ルーターモジュールを強制リロードするため、sys.modulesから削除
    if 'app.jobs.router' in sys.modules:
        del sys.modules['app.jobs.router']
    
    # weasyprint をモック
    with patch.dict('sys.modules', {'weasyprint': MagicMock()}):
        # Import the router
        from app.jobs import router as router_module
        
        # Patch the status_manager functions in the router module's namespace directly
        router_module.check_job_exclusion = mock_status_manager.check_job_exclusion
        router_module.try_initialize_job_exclusive = mock_status_manager.try_initialize_job_exclusive
        router_module.get_job_status_sync = mock_status_manager.get_job_status_sync
        router_module.get_job_result_sync = mock_status_manager.get_job_result_sync
        
        # Patch the crypto functions in the router module's namespace directly
        router_module.verify_auth_hash = mock_crypto.verify_auth_hash
        router_module.decrypt_opensearch_dashboard_payload = mock_crypto.decrypt_opensearch_dashboard_payload
        router_module._get_shared_secret = mock_crypto._get_shared_secret
        
        # Get the routers
        router = router_module.router
        start_router = router_module.start_router
        
        # Mount routers without adding extra prefix (router already has prefix="/jobs")
        app.include_router(router)
        app.include_router(start_router)
        
        yield app


@pytest.fixture
async def authenticated_client(test_app):
    """認証済みHTTPクライアント"""
    from httpx import ASGITransport
    
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test"
    ) as client:
        # 必要に応じて認証ヘッダーを追加
        client.headers.update({"Authorization": "Bearer test-token"})
        yield client


# ==================== pytest hooks ====================
def pytest_runtest_makereport(item, call):
    """テスト結果をフックで収集"""
    if call.when == "call":
        collector = item.session.config._test_result_collector
        outcome = "passed" if call.excinfo is None else "failed"
        error_msg = str(call.excinfo.value) if call.excinfo else None
        collector.add_result(
            test_name=item.nodeid,
            outcome=outcome,
            duration=call.duration,
            error_msg=error_msg
        )


def pytest_configure(config):
    """pytest起動時の設定"""
    config._test_result_collector = TestResultCollector()


def pytest_sessionfinish(session, exitstatus):
    """テストセッション終了時にレポート生成"""
    collector = session.config._test_result_collector
    
    # レポートディレクトリのパス
    report_dir = Path(__file__).parent.parent / 'reports'
    report_dir.mkdir(exist_ok=True)
    
    # Markdownレポート生成
    md_report_path = report_dir / f'test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
    with open(md_report_path, 'w', encoding='utf-8') as f:
        f.write("# Jobs Router テストレポート\n\n")
        f.write(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## テスト統計\n\n")
        f.write(f"- 総テスト数: {collector.stats['total']}\n")
        f.write(f"- 成功: {collector.stats['passed']}\n")
        f.write(f"- 失敗: {collector.stats['failed']}\n")
        f.write(f"- スキップ: {collector.stats['skipped']}\n")
        f.write(f"- エラー: {collector.stats['error']}\n\n")
        
        f.write("## テスト結果詳細\n\n")
        for result in collector.results:
            status_icon = "✅" if result["outcome"] == "passed" else "❌"
            f.write(f"### {status_icon} {result['test_name']}\n")
            f.write(f"- 結果: {result['outcome']}\n")
            f.write(f"- 実行時間: {result['duration']:.3f}秒\n")
            if result['error_message']:
                f.write(f"- エラー: `{result['error_message']}`\n")
            f.write("\n")
    
    # JSONレポート生成
    json_report_path = report_dir / f'test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(json_report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": collector.stats,
            "results": collector.results,
            "generated_at": datetime.now().isoformat()
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ テストレポートを生成しました:")
    print(f"  - Markdown: {md_report_path}")
    print(f"  - JSON: {json_report_path}")


# テスト名マッピング（日本語表示用）
TEST_NAME_MAPPING = {
    "test_start_policy_batch": "JOB-001: ポリシーバッチ生成開始",
    "test_start_file_processing": "JOB-002: ファイル処理開始",
    "test_get_job_status": "JOB-003: ジョブステータス取得",
    "test_get_job_result_completed": "JOB-004: ジョブ結果取得（完了）",
    "test_get_scan_files_success": "JOB-005: スキャンファイル取得",
    "test_custodian_scan_encrypted_success": "JOB-006: 旧Custodianスキャン開始（暗号化）",
    "test_custodian_scan_plain_success": "JOB-007: 旧Custodianスキャン開始（平文）",
    "test_new_custodian_scan_encrypted_success": "JOB-008: 新Custodianスキャン開始（暗号化）",
    "test_new_custodian_scan_plain_success": "JOB-009: 新Custodianスキャン開始（平文）",
    "test_new_custodian_scan_with_preset": "JOB-010: 新Custodianスキャン（プリセット付き）",
}

