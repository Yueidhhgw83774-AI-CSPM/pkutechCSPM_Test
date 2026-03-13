# TestReport/plugins/custodian_scan/custodian_scan/source/conftest.py
"""
Custodian Scan テストの共通フィクスチャとモック

このconftest.pyは Jobs Router の成功パターンを適用しています：
1. ルーターモジュールの強制リロード（sys.modules削除）
2. 直接ネームスペースへのモック代入
3. 明示的なフィクスチャ依存関係
4. 完全な隔離とクリーンアップ
"""

import pytest
import sys
import os
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

# プロジェクトルート設定（env_loader を使用）
try:
    from env_loader import PROJECT_ROOT
except ImportError:
    _here = Path(__file__).resolve()
    for _p in [_here, *_here.parents]:
        if (_p / "env_loader.py").exists():
            sys.path.insert(0, str(_p))
            from env_loader import PROJECT_ROOT
            break
    else:
        raise ImportError("env_loader.py が見つかりません")

project_root = PROJECT_ROOT / "platform_python_backend-testing"
sys.path.insert(0, str(project_root))




# ============================================================================
# JWT認証モック
# ============================================================================

@pytest.fixture
def mock_jwt_auth():
    """JWT認証をバイパスするモック"""
    with patch('app.core.auth.get_current_active_user') as mock_auth:
        # User オブジェクトを返すように設定
        from app.models.auth import User
        mock_user = User(username="test_user", email="test@example.com", full_name="Test User", disabled=False)
        mock_auth.return_value = mock_user
        yield mock_auth


# ============================================================================
# Status Manager モック
# ============================================================================

@pytest.fixture(scope="function")
def mock_status_manager():
    """status_manager モジュールのモック"""
    from app.jobs import status_manager
    
    # 元の状態を保存
    original_statuses = status_manager.job_statuses.copy()
    status_manager.job_statuses.clear()
    
    # モッククラスの作成
    class StatusManager:
        job_statuses = status_manager.job_statuses
        check_job_exclusion = MagicMock(return_value=None)
        try_initialize_job_exclusive = MagicMock(return_value=("test-job-id", None))
        get_job_status_sync = MagicMock(return_value=None)
        get_job_result_sync = MagicMock(return_value=None)
        initialize_job = MagicMock(return_value="test-job-id")
        update_job_status = MagicMock()
        append_job_log = MagicMock()
        set_job_completed = MagicMock()
        set_job_failed = MagicMock()
        
    manager = StatusManager()
    yield manager
    
    # クリーンアップ
    status_manager.job_statuses.clear()
    status_manager.job_statuses.update(original_statuses)


# ============================================================================
# Crypto モック
# ============================================================================

@pytest.fixture
def mock_crypto():
    """暗号化関連関数のモック"""
    with patch('app.jobs.router.verify_auth_hash') as mock_verify, \
         patch('app.jobs.router.decrypt_opensearch_dashboard_payload') as mock_decrypt, \
         patch('app.jobs.router._get_shared_secret') as mock_secret, \
         patch('app.core.crypto.decrypt_credentials_field') as mock_decrypt_creds:
        
        mock_crypto_obj = MagicMock()
        mock_crypto_obj.verify_auth_hash = mock_verify
        mock_crypto_obj.decrypt_opensearch_dashboard_payload = mock_decrypt
        mock_crypto_obj._get_shared_secret = mock_secret
        mock_crypto_obj.decrypt_credentials_field = mock_decrypt_creds
        
        # デフォルトの動作を設定
        mock_secret.return_value = "test-shared-secret"
        mock_verify.return_value = True
        mock_decrypt.return_value = {}
        mock_decrypt_creds.return_value = '{"accessKey": "AKIAIOSFODNN7EXAMPLE", "secretKey": "test"}'
        
        yield mock_crypto_obj


# ============================================================================
# Task モック
# ============================================================================

@pytest.fixture
def mock_custodian_tasks():
    """Custodianスキャンタスクのモック"""
    with patch('app.custodian_scan.router.run_custodian_scan_task') as mock_old_scan, \
         patch('app.jobs.tasks.new_custodian_scan.main_task.NewCustodianScanTask') as mock_new_scan, \
         patch('app.custodian_scan.router.CustodianCommandPreview') as mock_preview:
        
        # NewCustodianScanTask のモック設定
        mock_new_scan_instance = AsyncMock()
        mock_new_scan_instance._execute_task = AsyncMock(return_value={
            "message": "スキャン完了",
            "summary_data": {"violations_found": 0}
        })
        mock_new_scan.return_value = mock_new_scan_instance
        
        # CustodianCommandPreview のモック設定
        mock_preview_instance = AsyncMock()
        mock_preview_instance.generate_command_preview = AsyncMock(return_value={
            "command": "custodian run policy.yaml",
            "regions": ["ap-northeast-1"],
            "policy_count": 1
        })
        mock_preview.return_value = mock_preview_instance
        
        mock_tasks_obj = MagicMock()
        mock_tasks_obj.run_custodian_scan_task = mock_old_scan
        mock_tasks_obj.NewCustodianScanTask = mock_new_scan
        mock_tasks_obj.CustodianCommandPreview = mock_preview
        
        yield mock_tasks_obj


# ============================================================================
# OpenSearch モック
# ============================================================================

@pytest.fixture
def mock_opensearch():
    """OpenSearchクライアントのモック"""
    with patch('app.core.clients.get_opensearch_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.index = AsyncMock(return_value={"result": "created", "_id": "test-id"})
        mock_client.update = AsyncMock(return_value={"result": "updated"})
        mock_client.search = AsyncMock(return_value={"hits": {"hits": []}})
        mock_client.bulk = AsyncMock(return_value={"errors": False})
        mock_get_client.return_value = mock_client
        
        yield mock_client


# ============================================================================
# Test App フィクスチャ（Jobs Router の成功パターンを適用）
# ============================================================================

@pytest.fixture
async def test_app(mock_status_manager, mock_custodian_tasks, mock_crypto, mock_opensearch):
    """テスト用FastAPIアプリケーション
    
    Jobs Router の成功パターンを適用：
    1. sys.modules からルーターを削除して強制リロード
    2. モジュールネームスペースに直接モックを代入
    3. プレフィックスの重複を避ける
    """
    from fastapi import FastAPI
    import sys
    
    app = FastAPI()
    
    # ルーターモジュールを強制リロード
    modules_to_reload = [
        'app.custodian_scan.router',
        'app.jobs.router',
    ]
    for module_name in modules_to_reload:
        if module_name in sys.modules:
            del sys.modules[module_name]
    
    # weasyprint をモック（依存関係がある場合）
    with patch.dict('sys.modules', {'weasyprint': MagicMock()}):
        # Import routers
        from app.custodian_scan import router as custodian_router_module
        from app.jobs import router as jobs_router_module
        
        # Custodian Router のモック適用
        custodian_router_module.run_custodian_scan_task = mock_custodian_tasks.run_custodian_scan_task
        custodian_router_module.CustodianCommandPreview = mock_custodian_tasks.CustodianCommandPreview
        
        # Jobs Router のモック適用（status_manager関数）
        jobs_router_module.check_job_exclusion = mock_status_manager.check_job_exclusion
        jobs_router_module.try_initialize_job_exclusive = mock_status_manager.try_initialize_job_exclusive
        jobs_router_module.get_job_status_sync = mock_status_manager.get_job_status_sync
        jobs_router_module.get_job_result_sync = mock_status_manager.get_job_result_sync
        
        # Crypto関数のモック適用
        jobs_router_module.verify_auth_hash = mock_crypto.verify_auth_hash
        jobs_router_module.decrypt_opensearch_dashboard_payload = mock_crypto.decrypt_opensearch_dashboard_payload
        jobs_router_module._get_shared_secret = mock_crypto._get_shared_secret
        
        # Get routers
        custodian_router = custodian_router_module.router
        jobs_router = jobs_router_module.router
        jobs_start_router = jobs_router_module.start_router
        
        # Mount routers（注: main.pyでは /api/custodian プレフィックスで登録されている）
        # しかし、router.py内でprefixが定義されていない場合は、ここで追加
        app.include_router(custodian_router, prefix="/api/custodian", tags=["Custodian Scan"])
        app.include_router(jobs_router)  # 既にprefix="/jobs"を持つ
        app.include_router(jobs_start_router)
        
        yield app


@pytest.fixture
async def authenticated_client(test_app, mock_jwt_auth):
    """認証済みHTTPクライアント"""
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
        headers={"Authorization": "Bearer test_token"}
    ) as client:
        yield client


# ============================================================================
# テストデータフィクスチャ
# ============================================================================

@pytest.fixture
def valid_policy_yaml():
    """有効なCustodianポリシーYAML"""
    return """
policies:
  - name: ec2-require-tags
    resource: aws.ec2
    filters:
      - "tag:Environment": absent
    actions:
      - type: mark-for-op
        tag: c7n_cleanup
        op: stop
        days: 7
"""


@pytest.fixture
def valid_policy_yaml_multiregion():
    """マルチリージョン対応の有効なポリシー"""
    return """
policies:
  - name: s3-bucket-encryption
    resource: aws.s3
    filters:
      - type: bucket-encryption
        state: false
    actions:
      - type: set-bucket-encryption
"""


@pytest.fixture
def invalid_policy_yaml_empty():
    """空のポリシーYAML"""
    return ""


@pytest.fixture
def invalid_policy_yaml_malformed():
    """不正な形式のYAML"""
    return "invalid: yaml: content: ["


@pytest.fixture
def dangerous_policy_yaml():
    """危険なキーワードを含むポリシー"""
    return """
policies:
  - name: dangerous-policy
    resource: aws.ec2
    actions:
      - type: exec
        command: rm -rf /
"""


@pytest.fixture
def valid_aws_credentials():
    """有効なAWS認証情報"""
    return {
        "accessKey": "AKIAIOSFODNN7EXAMPLE",
        "secretKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "defaultRegion": "ap-northeast-1"
    }


@pytest.fixture
def valid_aws_credentials_multiregion():
    """マルチリージョン用のAWS認証情報"""
    return {
        "accessKey": "AKIAIOSFODNN7EXAMPLE",
        "secretKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "scanRegions": ["ap-northeast-1", "us-east-1", "us-west-2"]
    }


@pytest.fixture
def invalid_aws_credentials_short_key():
    """無効なAWS認証情報（アクセスキーが短すぎる）"""
    return {
        "accessKey": "SHORT",
        "secretKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "defaultRegion": "ap-northeast-1"
    }


@pytest.fixture
def valid_azure_credentials():
    """有効なAzure認証情報"""
    return {
        "tenantId": "12345678-1234-1234-1234-123456789012",
        "clientId": "12345678-1234-1234-1234-123456789012",
        "clientSecret": "your-client-secret-value",
        "subscriptionId": "12345678-1234-1234-1234-123456789012"
    }


@pytest.fixture
def invalid_azure_credentials_bad_guid():
    """無効なAzure認証情報（GUID形式不正）"""
    return {
        "tenantId": "not-a-valid-guid",
        "clientId": "12345678-1234-1234-1234-123456789012",
        "clientSecret": "test-secret",
        "subscriptionId": "12345678-1234-1234-1234-123456789012"
    }


@pytest.fixture
def assume_role_credentials():
    """AssumeRole認証情報"""
    return {
        "authType": "role_assumption",
        "roleArn": "arn:aws:iam::123456789012:role/CustodianScanRole",
        "externalIdValue": "external-id-123",
        "scanRegions": ["ap-northeast-1", "us-east-1"]
    }


@pytest.fixture
def invalid_assume_role_credentials():
    """無効なAssumeRole認証情報（ARN形式不正）"""
    return {
        "authType": "role_assumption",
        "roleArn": "invalid-arn-format",
        "scanRegions": ["ap-northeast-1"]
    }


@pytest.fixture
def encrypted_credentials():
    """暗号化された認証情報"""
    return {
        "encryptedData": "base64_encoded_encrypted_data",
        "iv": "initialization_vector"
    }


@pytest.fixture
def mock_custodian_output_success():
    """成功したCustodian出力"""
    return {
        "return_code": 0,
        "violations_count": 5,
        "output_dir": "/tmp/custodian-output",
        "stdout_output": [
            "[CUSTODIAN_STDOUT] Scanning AWS resources...",
            "[CUSTODIAN_STDOUT] Found 5 violations"
        ]
    }


# ============================================================================
# テストレポート生成
# ============================================================================

class TestResultCollector:
    """テスト結果を収集してレポートを生成"""
    def __init__(self):
        self.results = {"normal": [], "error": [], "security": []}

    def add_result(self, nodeid: str, outcome: str, duration: float):
        test_name = nodeid.split("::")[-1]
        if "Security" in nodeid:
            cat = "security"
        elif "Error" in nodeid:
            cat = "error"
        else:
            cat = "normal"
        self.results[cat].append({"test_id": test_name, "outcome": outcome, "duration": duration})

    def generate_markdown_report(self, output_path: Path):
        total = sum(len(v) for v in self.results.values())
        passed = sum(1 for cat in self.results.values() for r in cat if r["outcome"] == "passed")
        
        lines = [
            f"# Custodian Scan テストレポート\n",
            f"**生成日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"**通過率**: {passed}/{total} ({(passed/total*100 if total > 0 else 0.0):.1f}%)\n",
            f"\n---\n"
        ]
        
        for cat, label in [("normal", "正常系テスト"), ("error", "異常系テスト"), ("security", "セキュリティテスト")]:
            r = self.results[cat]
            if not r:
                continue
            p = sum(1 for x in r if x["outcome"] == "passed")
            f = len(r) - p
            lines.append(f"\n## {label}: {p}/{len(r)}\n")
            lines.append(f"- ✅ 成功: {p}")
            lines.append(f"- ❌ 失敗: {f}\n")
            
            if f > 0:
                lines.append(f"\n### 失敗したテスト\n")
                for test in r:
                    if test["outcome"] != "passed":
                        lines.append(f"- `{test['test_id']}` ({test['duration']:.3f}s)")
        
        output_path.write_text("\n".join(lines), encoding="utf-8")

    def generate_json_report(self, output_path: Path):
        total = sum(len(v) for v in self.results.values())
        passed = sum(1 for cat in self.results.values() for r in cat if r["outcome"] == "passed")
        report = {
            "summary": {
                "total": total, 
                "passed": passed,
                "failed": total - passed,
                "pass_rate": round(passed/total*100 if total > 0 else 0.0, 2)
            }, 
            "categories": self.results,
            "generated_at": datetime.now().isoformat()
        }
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """各テストの実行結果を収集"""
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call":
        collector = getattr(item.session.config, '_test_collector', None)
        if collector:
            collector.add_result(item.nodeid, rep.outcome, rep.duration)


def pytest_sessionstart(session):
    """テストセッション開始時にコレクターを初期化"""
    session.config._test_collector = TestResultCollector()


def pytest_sessionfinish(session, exitstatus):
    """テストセッション終了時にレポートを生成"""
    collector = getattr(session.config, '_test_collector', None)
    if not collector:
        return

    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    collector.generate_markdown_report(reports_dir / "TestReport_custodian_scan.md")
    collector.generate_json_report(reports_dir / "TestReport_custodian_scan.json")


@pytest.fixture
def mock_custodian_output_no_violations():
    """違反なしのCustodian出力"""
    return {
        "return_code": 0,
        "violations_count": 0,
        "output_dir": "/tmp/custodian-output",
        "stdout_output": ["[CUSTODIAN_STDOUT] No violations found"],
        "stderr_output": [],
        "cloud_provider": "aws"
    }


@pytest.fixture
def mock_custodian_output_error():
    """エラーのあるCustodian出力"""
    return {
        "return_code": 1,
        "violations_count": 0,
        "output_dir": "/tmp/custodian-output",
        "stdout_output": [],
        "stderr_output": ["[CUSTODIAN_STDERR] Authentication failed"],
        "cloud_provider": "aws"
    }


# ============================================================================
# pytest設定
# ============================================================================

def pytest_configure(config):
    """pytest設定のカスタマイズ"""
    config.addinivalue_line(
        "markers",
        "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers",
        "security: mark test as security test"
    )


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """テスト環境のセットアップ"""
    # 環境変数の設定
    os.environ["TESTING"] = "true"
    os.environ["ENABLE_SECURITY_VALIDATION"] = "false"  # テスト中はセキュリティ検証を無効化
    
    yield
    
    # クリーンアップ
    os.environ.pop("TESTING", None)
    os.environ.pop("ENABLE_SECURITY_VALIDATION", None)

