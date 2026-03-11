"""
CSPM Tools 测试配置和 Fixtures

测试规格: docs/testing/plugins/cspm/cspm_tools_tests.md
测试数量: 56 (正常系:20, 异常系:28, 安全:8)
"""

import sys
import os
import pytest
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent.parent.parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

_source_root_env = os.environ.get("soure_root", "").strip().strip('"').strip("'")
if _source_root_env and Path(_source_root_env).exists():
    project_root = Path(_source_root_env)
else:
    project_root = Path(__file__).resolve().parents[5] / "platform_python_backend-testing"

if not project_root.exists():
    raise RuntimeError(f"项目根目录不存在: {project_root}")
sys.path.insert(0, str(project_root))

# Mock weasyprint
from unittest.mock import MagicMock as _MM
for _m in ["weasyprint", "weasyprint.CSS", "weasyprint.HTML", "weasyprint.css",
           "weasyprint.text", "weasyprint.text.fonts", "weasyprint.text.ffi", "weasyprint.text.constants"]:
    sys.modules.setdefault(_m, _MM())


@pytest.fixture
def mock_subprocess_success():
    """subprocess.run が成功を返すモック"""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""
    mock_result.stdout = ""
    with patch("app.cspm_plugin.tools.subprocess.run", return_value=mock_result) as mock_run:
        yield mock_run, mock_result


@pytest.fixture
def mock_tempfile():
    """一時ファイル作成のモック"""
    with patch("app.cspm_plugin.tools.tempfile.NamedTemporaryFile") as mock_tmp:
        mock_file = MagicMock()
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=False)
        mock_file.name = "/tmp/test_policy.json"
        mock_tmp.return_value = mock_file
        with patch("app.cspm_plugin.tools.os.path.exists", return_value=True):
            with patch("app.cspm_plugin.tools.os.remove"):
                yield mock_file


@pytest.fixture
def mock_rag_system_success():
    """強化版RAGシステムのモック（成功）"""
    with patch("app.cspm_plugin.tools.get_enhanced_rag_system") as mock_get:
        mock_rag = AsyncMock()
        mock_rag.search.return_value = [
            MagicMock(
                page_content="Test document content",
                metadata={"Resource": "s3", "Framework": "AWS", "source": "test.md"}
            )
        ]
        mock_get.return_value = mock_rag
        yield mock_rag


@pytest.fixture
def mock_rag_unavailable():
    """RAGシステム利用不可のモック"""
    with patch("app.cspm_plugin.tools.get_enhanced_rag_system", return_value=None):
        yield


class TestResultCollector:
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
        lines = [f"# CSPM Tools 测试报告\n", f"**通过率**: {passed}/{total} ({passed/total*100:.1f}%)\n"]
        for cat, label in [("normal","正常系"),("error","异常系"),("security","安全测试")]:
            r = self.results[cat]
            p = sum(1 for x in r if x["outcome"] == "passed")
            lines.append(f"\n## {label}: {p}/{len(r)}\n")
        output_path.write_text("\n".join(lines), encoding="utf-8")

    def generate_json_report(self, output_path: Path):
        total = sum(len(v) for v in self.results.values())
        passed = sum(1 for cat in self.results.values() for r in cat if r["outcome"] == "passed")
        report = {"summary": {"total": total, "passed": passed}, "categories": self.results}
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call":
        item.session.config._test_collector.add_result(item.nodeid, rep.outcome, rep.duration)


def pytest_sessionstart(session):
    session.config._test_collector = TestResultCollector()


def pytest_sessionfinish(session, exitstatus):
    collector = session.config._test_collector
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    collector.generate_markdown_report(reports_dir / "TestReport_cspm_tools.md")
    collector.generate_json_report(reports_dir / "TestReport_cspm_tools.json")

