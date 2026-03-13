"""Doc Reader Plugin テスト設定（共通）

全 doc_reader サブモジュール共通の pytest 設定
"""
import pytest
import sys
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock
from typing import Dict, Any

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

# Mock weasyprint
from unittest.mock import MagicMock as _M
for _m in ["weasyprint"]+[f"weasyprint.{x}" for x in ["CSS","HTML","css","text","text.fonts","text.ffi","text.constants"]]:
    sys.modules.setdefault(_m, _M())


# ============================================
# Test Result Collector
# ============================================

class TestResultCollector:
    """テスト結果収集"""

    def __init__(self):
        self.results = {
            "normal": [],
            "error": [],
            "security": []
        }
        self.start_time = datetime.now()

    def add_result(self, nodeid: str, outcome: str, duration: float):
        """テスト結果追加"""
        test_name = nodeid.split("::")[-1]
        test_id = self._extract_test_id(nodeid)

        result = {
            "test_id": test_id,
            "test_name": test_name,
            "outcome": outcome,
            "duration_ms": round(duration * 1000, 2),
            "status": "✅" if outcome == "passed" else "❌" if outcome == "failed" else "⚠️"
        }

        if "Security" in nodeid or "SEC" in test_id:
            self.results["security"].append(result)
        elif "Error" in nodeid or "-E" in test_id:
            self.results["error"].append(result)
        else:
            self.results["normal"].append(result)

    def _extract_test_id(self, nodeid: str) -> str:
        """テストIDを抽出"""
        import re
        match = re.search(r'DOCR[A-Z]*-[A-Z0-9\-]+', nodeid)
        if match:
            return match.group(0)
        return "N/A"

    def generate_markdown_report(self, output_path: Path, module_name: str):
        """Markdownレポート生成"""
        total = sum(len(v) for v in self.results.values())
        passed = sum(1 for cat in self.results.values() for r in cat if r["outcome"] == "passed")
        failed = sum(1 for cat in self.results.values() for r in cat if r["outcome"] == "failed")

        if total == 0:
            output_path.write_text(f"# {module_name} テストレポート\n\n**状態**: テスト未実装\n", encoding="utf-8")
            return

        report = f"""# {module_name} テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| 実行日時 | {self.start_time.strftime("%Y-%m-%d %H:%M:%S")} |
| 総テスト数 | {total} |
| 通過 | {passed} |
| 失敗 | {failed} |
| 通過率 | {(passed/total*100 if total > 0 else 0.0):.1f}% |

## 正常系テスト ({len(self.results["normal"])})

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
"""
        for r in self.results["normal"]:
            report += f"| {r['test_id']} | {r['test_name']} | {r['status']} | {r['duration_ms']}ms |\n"

        report += f"\n## 異常系テスト ({len(self.results['error'])})\n\n"
        report += "| ID | テスト名 | 結果 | 時間 |\n"
        report += "|----|---------|------|------|\n"
        for r in self.results["error"]:
            report += f"| {r['test_id']} | {r['test_name']} | {r['status']} | {r['duration_ms']}ms |\n"

        report += f"\n## セキュリティテスト ({len(self.results['security'])})\n\n"
        report += "| ID | テスト名 | 結果 | 時間 |\n"
        report += "|----|---------|------|------|\n"
        for r in self.results["security"]:
            report += f"| {r['test_id']} | {r['test_name']} | {r['status']} | {r['duration_ms']}ms |\n"

        report += f"\n---\n*生成時刻: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*\n"

        output_path.write_text(report, encoding="utf-8")

    def generate_json_report(self, output_path: Path):
        """JSONレポート生成"""
        import json
        total = sum(len(v) for v in self.results.values())
        if total == 0:
            output_path.write_text(json.dumps({"summary": {"total": 0, "passed": 0, "failed": 0, "status": "未実装"}, "categories": self.results}, indent=2, ensure_ascii=False), encoding="utf-8")
            return

        passed = sum(1 for cat in self.results.values() for r in cat if r["outcome"] == "passed")

        report = {
            "summary": {
                "total": total,
                "passed": passed,
                "failed": total - passed,
                "pass_rate": f"{passed/total*100:.1f}%" if total > 0 else "N/A"
            },
            "categories": self.results,
            "execution_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S")
        }

        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


# ============================================
# Pytest Hooks
# ============================================

collector = TestResultCollector()

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """各テストの結果をキャプチャ"""
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call":
        collector.add_result(item.nodeid, rep.outcome, rep.duration)

def pytest_sessionfinish(session, exitstatus):
    """テスト終了時にレポート生成"""
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)

    # モジュール名を取得
    module_path = Path(__file__).parent
    module_name = module_path.parent.name

    collector.generate_markdown_report(reports_dir / f"TestReport_{module_name}.md", module_name)
    collector.generate_json_report(reports_dir / f"TestReport_{module_name}.json")


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def app():
    """FastAPI app fixture"""
    from app.main import app as fastapi_app
    return fastapi_app

@pytest.fixture
def async_client(app):
    """Async test client"""
    from httpx import AsyncClient, ASGITransport
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

@pytest.fixture
def client(app):
    """Sync test client (for FastAPI TestClient)"""
    from fastapi.testclient import TestClient
    return TestClient(app)

