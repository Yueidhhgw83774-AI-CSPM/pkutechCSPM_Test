"""
CSPM Plugin Router テスト設定と Fixtures

テスト仕様: docs/testing/plugins/cspm/cspm_plugin_tests.md
カバレッジ目標: 90%+
"""

import sys
import os
import pytest
import pytest_asyncio
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

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

project_root = PROJECT_ROOT / "platform_python_backend-testing" if not str(PROJECT_ROOT).endswith("platform_python_backend-testing") else PROJECT_ROOT
if not project_root.exists():
    raise RuntimeError(f"プロジェクトルートディレクトリが存在しません: {project_root}")
sys.path.insert(0, str(project_root))

# Mock weasyprint（libpango 依赖を回避）
from unittest.mock import MagicMock as _MagicMock
for _mod in ["weasyprint", "weasyprint.CSS", "weasyprint.HTML", "weasyprint.css",
             "weasyprint.text", "weasyprint.text.fonts", "weasyprint.text.ffi", "weasyprint.text.constants"]:
    sys.modules.setdefault(_mod, _MagicMock())


# ============================================
# モジュール状態リセット（autouse）
# ============================================

@pytest.fixture(autouse=True)
def reset_cspm_router_module():
    """テストごとに cspm_plugin モジュールのグローバル状態をリセット

    グローバル変数（_simple_chatbot 等）をリセットするが、
    router モジュール自体は削除しない（app.main で登録済みのため）。
    """
    yield
    # グローバル変数のみリセット
    try:
        import app.cspm_plugin.refinement as ref
        if hasattr(ref, '_llm'):
            ref._llm = None
    except (ImportError, AttributeError):
        pass


# ============================================
# アプリ・クライアント Fixtures
# ============================================

@pytest.fixture
def app():
    """FastAPI アプリケーションインスタンス

    lifespan を noop に差し替えて OpenSearch/RAG 初期化をスキップ。
    """
    from contextlib import asynccontextmanager
    import importlib

    @asynccontextmanager
    async def _noop_lifespan(app):
        yield

    main_mod = importlib.import_module("app.main")
    outer = main_mod.app
    if hasattr(outer, "app"):
        fastapi_app = outer.app  # DecryptionMiddleware から内部 FastAPI を取り出す
    else:
        fastapi_app = outer

    # lifespan を noop に差し替え
    fastapi_app.router.lifespan_context = _noop_lifespan
    return fastapi_app


@pytest_asyncio.fixture
async def async_client(app):
    """FastAPI 非同期テストクライアント"""
    from httpx import AsyncClient, ASGITransport
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


# ============================================
# モック Fixtures
# ============================================

@pytest.fixture
def mock_generate_refined_policy():
    """refinement.generate_refined_policy のモック（外部 LLM 接続防止）"""
    with patch(
        "app.cspm_plugin.router.generate_refined_policy",
        new_callable=AsyncMock,
    ) as mock_func:
        mock_func.return_value = "モック応答"
        yield mock_func


@pytest.fixture
def mock_run_policy_agent():
    """agent_executor.run_policy_agent のモック（LangGraph 実行防止）"""
    with patch(
        "app.cspm_plugin.router.run_policy_agent",
        new_callable=AsyncMock,
    ) as mock_func:
        mock_func.return_value = (
            '[{"name": "mock-policy", "resource": "s3"}]',
            None,
            "active",
        )
        yield mock_func


@pytest.fixture
def mock_validate_policy_tool():
    """tools.validate_policy のモック（subprocess 実行防止）"""
    with patch("app.cspm_plugin.router.validate_policy") as mock_tool:
        mock_tool.invoke = MagicMock(return_value="Validation successful.")
        yield mock_tool


@pytest.fixture
def sample_recommendation():
    """サンプル推奨事項データ"""
    return {
        "uid": "rec-001",
        "recommendationId": "1.1",
        "title": "S3バケットの暗号化を有効化",
        "description": "セキュリティのためにS3バケットのSSE暗号化を有効にしてください",
        "rationale": "暗号化により保存データを保護",
        "remediation": ["AWSコンソールでS3バケットを開く", "デフォルト暗号化を有効化"],
    }


# ============================================
# テスト結果コレktor
# ============================================

class TestResultCollector:
    def __init__(self):
        self.results = {"normal": [], "error": [], "security": []}
        self.start_time = datetime.now()

    def add_result(self, nodeid: str, outcome: str, duration: float):
        test_name = nodeid.split("::")[-1]
        if "Security" in nodeid or "_sec_" in test_name.lower():
            cat = "security"
        elif "Error" in nodeid or "error" in test_name.lower() or "_E0" in test_name or "Errors" in nodeid:
            cat = "error"
        else:
            cat = "normal"
        self.results[cat].append({"test_id": test_name, "outcome": outcome, "duration": duration})

    def generate_markdown_report(self, output_path: Path):
        total = sum(len(v) for v in self.results.values())
        passed = sum(1 for cat in self.results.values() for r in cat if r["outcome"] == "passed")
        failed = total - passed
        rate = f"{passed/total*100:.1f}%" if total > 0 else "N/A"
        lines = [
            "# CSPM Plugin Router 测试报告\n",
            "| 项目 | 值 |",
            "|------|-----|",
            f"| 测试对象 | `app/cspm_plugin/router.py` |",
            f"| 执行时间 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |",
            f"| 覆盖率目标 | 90% |\n",
            "| 类别 | 总数 | 通过 | 失败 |",
            "|------|------|------|------|",
        ]
        for cat, label in [("normal","正常系"),("error","异常系"),("security","安全测试")]:
            r = self.results[cat]
            p = sum(1 for x in r if x["outcome"] == "passed")
            lines.append(f"| {label} | {len(r)} | {p} | {len(r)-p} |")
        lines.append(f"| **合计** | **{total}** | **{passed}** | **{failed}** |\n")
        lines.append(f"**通过率**: {rate}\n")
        for cat, label in [("normal","正常系"),("error","异常系"),("security","安全测试")]:
            lines.append(f"\n## {label}测试详情\n| 测试名称 | 结果 | 执行时间 |\n|---------|------|----------|")
            for r in self.results[cat]:
                s = "✅" if r["outcome"] == "passed" else "❌"
                lines.append(f"| {r['test_id']} | {s} | {r['duration']:.3f}s |")
        lines.append(f"\n---\n*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        output_path.write_text("\n".join(lines), encoding="utf-8")

    def generate_json_report(self, output_path: Path):
        total = sum(len(v) for v in self.results.values())
        passed = sum(1 for cat in self.results.values() for r in cat if r["outcome"] == "passed")
        report = {
            "summary": {"total": total, "passed": passed, "failed": total-passed,
                        "pass_rate": f"{passed/total*100:.1f}%" if total > 0 else "N/A"},
            "categories": self.results,
            "execution_time": datetime.now().isoformat()
        }
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call":
        collector = getattr(item.session.config, '_test_collector', None)
        if collector:
            collector.add_result(item.nodeid, rep.outcome, rep.duration)


def pytest_sessionstart(session):
    session.config._test_collector = TestResultCollector()


def pytest_sessionfinish(session, exitstatus):
    collector = getattr(session.config, '_test_collector', None)
    if not collector:
        return
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    collector.generate_markdown_report(reports_dir / "TestReport_cspm_plugin_router.md")
    collector.generate_json_report(reports_dir / "TestReport_cspm_plugin_router.json")

