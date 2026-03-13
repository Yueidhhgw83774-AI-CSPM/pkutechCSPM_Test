"""AWS Plugin 測試配置

pytest fixtures および hooks
"""
import pytest
import sys
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock
from typing import Dict, Any, List
import os
from dotenv import load_dotenv

# 環境変数読み込み
_env = Path(__file__).resolve().parents[4] / "TestReport" / ".env"
if _env.exists(): load_dotenv(_env)
_root = os.environ.get("soure_root", "").strip().strip('"').strip("'")
project_root = Path(_root) if _root and Path(_root).exists() else Path(__file__).resolve().parents[5] / "platform_python_backend-testing"
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
            "test_name": self._get_readable_name(test_name),
            "outcome": outcome,
            "duration_ms": round(duration * 1000, 2),
            "status": "✅" if outcome == "passed" else "❌" if outcome == "failed" else "⚠️"
        }

        if "Security" in nodeid or "SEC" in test_id:
            self.results["security"].append(result)
        elif "Error" in nodeid or test_id.startswith("AWS-E"):
            self.results["error"].append(result)
        else:
            self.results["normal"].append(result)

    def _extract_test_id(self, nodeid: str) -> str:
        """テストIDを抽出"""
        if "AWS-" in nodeid:
            import re
            match = re.search(r'AWS-[A-Z0-9\-]+', nodeid)
            if match:
                return match.group(0)
        return "N/A"

    def _get_readable_name(self, test_name: str) -> str:
        """テスト名をわかりやすい名前に変換"""
        name_map = {
            "test_get_regions_success": "AssumeRoleでリージョン一覧取得成功",
            "test_region_name_mapping_us_east_1": "リージョンマッピング（us-east-1）",
            "test_region_name_mapping_tokyo": "リージョンマッピング（Tokyo）",
            "test_execute_success": "AWS操作実行成功",
            "test_list_actions_success": "アクション一覧取得成功",
            "test_get_help_success": "ヘルプ取得成功",
            "test_access_denied_role_not_exist": "AccessDenied（ロール不存在）",
            "test_no_credentials_error": "NoCredentialsError",
        }
        return name_map.get(test_name, test_name.replace("_", " ").title())

    def generate_markdown_report(self, output_path: Path):
        """Markdownレポート生成"""
        total = sum(len(v) for v in self.results.values())
        passed = sum(1 for cat in self.results.values() for r in cat if r["outcome"] == "passed")
        failed = sum(1 for cat in self.results.values() for r in cat if r["outcome"] == "failed")

        report = f"""# AWS Plugin テストレポート

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
        total = sum(len(v) for v in self.results.values())
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

    collector.generate_markdown_report(reports_dir / "TestReport_aws_plugin.md")
    collector.generate_json_report(reports_dir / "TestReport_aws_plugin.json")


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

