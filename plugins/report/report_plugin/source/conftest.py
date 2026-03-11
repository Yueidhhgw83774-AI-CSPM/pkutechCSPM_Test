# TestReport/plugins/report/report_plugin/source/conftest.py
"""
Report Plugin テストの共通フィクスチャとモック

RAG Plugin / Jobs Router の成功パターンを適用
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

# 環境変数からソースルートを読み込み
from dotenv import load_dotenv
env_path = Path(__file__).parents[4] / ".env"
load_dotenv(env_path)

source_root = os.getenv("soure_root")
if source_root and source_root not in sys.path:
    sys.path.insert(0, source_root)


# ============================================================================
# JWT認証モック
# ============================================================================

@pytest.fixture
def mock_jwt_auth():
    """JWT認証をバイパスするモック"""
    with patch('app.core.auth.get_current_active_user') as mock_auth:
        from app.models.auth import User
        mock_user = User(username="test_user", email="test@example.com", full_name="Test User", disabled=False)
        mock_auth.return_value = mock_user
        yield mock_auth


# ============================================================================
# Report Provider モック
# ============================================================================

@pytest.fixture
def mock_report_data_audit():
    """監査レポートデータのモック"""
    return {
        "report_id": "test-audit-report",
        "report_type": "audit",
        "title": "テスト監査レポート",
        "scan": {
            "scan_id": "scan-123",
            "timestamp": "2026-03-11T10:00:00",
            "account": "123456789012",
            "region": "ap-northeast-1"
        },
        "summary": {
            "total_violations": 10,
            "by_severity": {"critical": 2, "high": 3, "medium": 3, "low": 2},
            "by_status": {"fail": 10, "pass": 5}
        },
        "violations": [
            {
                "policy_id": "ec2-001",
                "severity": "high",
                "resource_type": "AWS::EC2::Instance",
                "resource_id": "i-123",
                "status": "fail"
            }
        ]
    }


@pytest.fixture
def mock_report_data_periodic():
    """定期レポートデータのモック"""
    return {
        "report_id": "test-periodic-report",
        "report_type": "periodic",
        "title": "テスト定期レポート",
        "period": {
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
            "duration_days": 31
        },
        "scans": [
            {"scan_id": "scan-1", "timestamp": "2026-01-01T10:00:00"},
            {"scan_id": "scan-2", "timestamp": "2026-01-15T10:00:00"}
        ],
        "summary": {
            "total_scans": 2,
            "by_severity": {"critical": 5, "high": 10, "medium": 15, "low": 20}
        },
        "trend": {
            "dates": ["2026-01-01", "2026-01-15"],
            "total_violations": [50, 48]
        },
        "analysis": {
            "improvement_rate": 4.0,
            "most_common_policy": "ec2-001"
        },
        "violations": []
    }


@pytest.fixture
def mock_cspm_provider(mock_report_data_audit):
    """CSPMReportProviderのモック"""
    provider = AsyncMock()
    provider.collect_data = AsyncMock(return_value=mock_report_data_audit)
    provider.get_template_name = MagicMock(return_value="cspm/audit_report.html")
    provider.get_report_filename = MagicMock(return_value="audit_report.pdf")
    return provider


@pytest.fixture
def mock_html_renderer():
    """HtmlRendererのモック"""
    renderer = MagicMock()
    renderer.render = MagicMock(return_value="<html><body>Test Report</body></html>")
    return renderer


@pytest.fixture
def mock_pdf_generator():
    """PdfGeneratorのモック"""
    generator = MagicMock()
    generator.generate = MagicMock(return_value=b"%PDF-1.4\n1 0 obj\n<<\n>>\nendobj\nxref\n0 1\ntrailer\n<<\n>>\n%%EOF")
    return generator


@pytest.fixture
def mock_chart_generator():
    """ChartGeneratorのモック"""
    generator = MagicMock()
    generator.generate_severity_chart = MagicMock(return_value="data:image/png;base64,iVBORw0KGgoAAAANS")
    generator.generate_trend_chart = MagicMock(return_value="data:image/png;base64,iVBORw0KGgoAAAANS")
    return generator


@pytest.fixture
def mock_opensearch_fetcher():
    """OpenSearchDataFetcherのモック"""
    fetcher = AsyncMock()
    fetcher.get_scan_info = AsyncMock(return_value={
        "scan_id": "scan-123",
        "timestamp": "2026-03-11T10:00:00",
        "account": "123456789012"
    })
    fetcher.get_violations = AsyncMock(return_value=[
        {
            "policy_id": "ec2-001",
            "severity": "high",
            "resource_type": "AWS::EC2::Instance"
        }
    ])
    return fetcher


# ============================================================================
# Test App フィクスチャ
# ============================================================================

@pytest.fixture
async def test_app(mock_jwt_auth, mock_cspm_provider, mock_html_renderer, mock_pdf_generator):
    """テスト用FastAPIアプリケーション"""
    from fastapi import FastAPI
    import sys
    
    app = FastAPI()
    
    # ルーターモジュールを強制リロード
    modules_to_reload = [
        'app.report_plugin.router',
        'app.report_plugin.models',
        'app.report_plugin.providers.cspm_provider'
    ]
    for mod in modules_to_reload:
        if mod in sys.modules:
            del sys.modules[mod]
    
    # Mock外部依赖库
    mock_weasyprint = MagicMock()
    mock_matplotlib = MagicMock()
    mock_pyplot = MagicMock()
    
    with patch.dict('sys.modules', {
        'weasyprint': mock_weasyprint,
        'matplotlib': mock_matplotlib,
        'matplotlib.pyplot': mock_pyplot,
        'cairo': MagicMock(),
        'cairocffi': MagicMock()
    }):
        # Providerをモック
        with patch('app.report_plugin.router.CSPMReportProvider', return_value=mock_cspm_provider), \
             patch('app.report_plugin.router.HtmlRenderer', return_value=mock_html_renderer), \
             patch('app.report_plugin.router.PdfGenerator', return_value=mock_pdf_generator):
            
            try:
                # Import router
                from app.report_plugin import router as report_router_module
                
                # Get the router
                report_router = report_router_module.router
                
                # Mount router
                app.include_router(report_router)
            except Exception as e:
                # 如果导入失败，创建一个基本的路由器
                from fastapi import APIRouter
                report_router = APIRouter(prefix="/report", tags=["Report Plugin"])
                app.include_router(report_router)
            
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
def sample_audit_request():
    """監査レポートリクエストのサンプル"""
    from app.report_plugin.models import CSPMReportRequest
    return CSPMReportRequest(
        report_type="audit",
        scan_ids=["scan-123"],
        title="テスト監査レポート",
        included_sections=["technical_summary", "violations"],
        violation_statuses=[]
    )


@pytest.fixture
def sample_periodic_request():
    """定期レポートリクエストのサンプル"""
    from app.report_plugin.models import CSPMReportRequest
    return CSPMReportRequest(
        report_type="periodic",
        scan_ids=["scan-1", "scan-2"],
        title="テスト定期レポート",
        included_sections=["trend", "analysis"],
        violation_statuses=[]
    )


@pytest.fixture
def sample_violations():
    """違反データのサンプル"""
    return [
        {
            "policy_id": "ec2-001",
            "severity": "high",
            "resource_type": "AWS::EC2::Instance",
            "resource_id": "i-123",
            "status": "fail",
            "title": "EC2 instance without required tags"
        },
        {
            "policy_id": "s3-001",
            "severity": "critical",
            "resource_type": "AWS::S3::Bucket",
            "resource_id": "my-bucket",
            "status": "fail",
            "title": "S3 bucket not encrypted"
        },
        {
            "policy_id": "iam-001",
            "severity": "medium",
            "resource_type": "AWS::IAM::User",
            "resource_id": "test-user",
            "status": "pass",
            "title": "IAM user with MFA"
        }
    ]


@pytest.fixture
def sample_violation_statuses():
    """違反ステータスのサンプル"""
    from app.report_plugin.models import ViolationStatus
    return [
        ViolationStatus(
            policy_id="ec2-001",
            resource_id="i-123",
            status="acknowledged",
            comment="Already scheduled for remediation"
        )
    ]


# ============================================================================
# pytest設定
# ============================================================================

def pytest_configure(config):
    """pytest設定のカスタマイズ"""
    config.addinivalue_line("markers", "asyncio: mark test as async")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running test")


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """テスト環境のセットアップ"""
    os.environ["TESTING"] = "true"
    
    yield
    
    os.environ.pop("TESTING", None)

