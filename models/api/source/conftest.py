"""
models/api.py テスト設定ファイル

pytest設定とフック関数:
  - テスト環境のセットアップ
  - テスト結果の収集
  - テストレポートの生成(Markdown + JSON)
"""

import os
import re
import pytest
import json
import sys
from pathlib import Path
from datetime import datetime

def _load_source_root() -> str:
    """プロジェクトルートの .env から SourceCodeRoot を読み込む。"""
    # 優先度1: ルート conftest.py が os.environ に設定済みの場合
    from_env = os.environ.get("SourceCodeRoot", "").strip().strip("'\"")
    if from_env:
        return from_env
    # 優先度2: ディレクトリツリーを遡って .env ファイルを検索する
    current = Path(__file__).resolve()
    for directory in [current, *current.parents]:
        env_file = (directory if directory.is_dir() else directory.parent) / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                m = re.match(r"^\s*SourceCodeRoot\s*=\s*['\"]?(.+?)['\"]?\s*$", line)
                if m:
                    return m.group(1).strip()
    return ""

PROJECT_ROOT = _load_source_root()
if PROJECT_ROOT and PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class TestResultCollector:
    """テスト結果を収集してレポート生成に使用する。"""

    def __init__(self):
        self.results = {
            "normal": [],    # 正常系テスト
            "error": [],     # 異常系テスト
            "security": []   # セキュリティテスト
        }
        self.start_time = datetime.now()

    def add_result(self, nodeid: str, outcome: str, duration: float):
        """テスト結果を追加する。

        分類ルール:
        - "Security" を含む → security
        - "Error" または "_e0" を含む → error
        - その他 → normal
        """
        test_name = nodeid.split("::")[-1]
        class_name = nodeid.split("::")[-2] if len(nodeid.split("::")) > 2 else ""

        result = {
            "id": self._extract_test_id(test_name),
            "name": self._get_readable_name(test_name),
            "outcome": outcome,
            "duration": f"{duration:.3f}s"
        }

        # 分类
        if "Security" in class_name:
            self.results["security"].append(result)
        elif "Error" in class_name or "_e0" in test_name:
            self.results["error"].append(result)
        else:
            self.results["normal"].append(result)

    def _extract_test_id(self, test_name: str) -> str:
        """テストメソッド名からテストIDを抽出する。"""
        if "api_" in test_name.lower():
            parts = test_name.split("_")
            for i, part in enumerate(parts):
                if part.lower() == "api" and i + 1 < len(parts):
                    num = parts[i+1]
                    if num.isdigit():
                        return f"API-{num.zfill(3)}"
        return test_name

    def _get_readable_name(self, test_name: str) -> str:
        """テストメソッド名を読みやすい名称に変換する。"""
        name_map = {
            # ProcessTextFileResponse 正常系
            "test_process_text_file_response_minimal": "ProcessTextFileResponse 最小構成",
            "test_process_text_file_response_single_item": "単一ComplianceItem",
            "test_process_text_file_response_multiple_items": "複数ComplianceItem",
            "test_process_text_file_response_full_compliance_item": "完全構成ComplianceItem",
            "test_process_text_file_response_japanese_message": "日本語メッセージ",
            "test_process_text_file_response_nested_compliance": "ネストしたComplianceItem",

            # Base64TextRequest 通常系
            "test_base64_text_request_minimal": "Base64TextRequest 最小構成",
            "test_base64_text_request_with_session_id": "session_id付き",
            "test_base64_text_request_empty_session_id": "空session_id",
            "test_base64_text_request_large_content": "大きなBase64コンテンツ",
            "test_base64_text_request_japanese_filename": "日本語ファイル名",

            # モデル操作
            "test_model_dump_dict_conversion": "model_dump 辞書変換",
            "test_model_validate_from_dict": "model_validate 辞書から生成",
            "test_json_round_trip": "JSON往復変換",
            "test_model_dump_by_alias": "by_aliasパラメータ検証",

            # 異常系
            "test_process_text_file_response_missing_required": "必須フィールド欠落",
            "test_process_text_file_response_invalid_type": "無効な型",
            "test_base64_text_request_missing_filename": "filename欠落",
            "test_base64_text_request_missing_content": "file_content欠落",
            "test_base64_text_request_invalid_type": "無効な型",

            # セキュリティ
            "test_base64_request_path_traversal_warning": "Path Traversal警告",
            "test_base64_request_command_injection_warning": "Command Injection警告",
            "test_base64_request_crlf_injection_warning": "CRLF Injection警告",
        }
        return name_map.get(test_name, test_name.replace("_", " ").title())

    def generate_reports(self):
        """MarkdownとJSONレポートを生成する。"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        # 統計情報
        total = sum(len(v) for v in self.results.values())
        passed = sum(1 for category in self.results.values()
                    for r in category if r["outcome"] == "passed")
        failed = sum(1 for category in self.results.values()
                    for r in category if r["outcome"] == "failed")
        xfailed = sum(1 for category in self.results.values()
                     for r in category if r["outcome"] == "xfailed")

        # Markdown レポート生成
        md_report = self._generate_markdown_report(total, passed, failed, xfailed, duration)

        # JSON レポート生成
        json_report = self._generate_json_report(total, passed, failed, xfailed)

        # レポート保存
        report_dir = Path(__file__).parent.parent / "reports"
        report_dir.mkdir(exist_ok=True)

        md_path = report_dir / "TestReport_api.md"
        json_path = report_dir / "TestReport_api.json"

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_report)

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, ensure_ascii=False, indent=2)

    def _generate_markdown_report(self, total, passed, failed, xfailed, duration):
        """Markdown形式のレポートを生成する。"""
        pass_rate = (passed / total * 100) if total > 0 else 0
        effective_total = total - xfailed
        effective_pass_rate = (passed / effective_total * 100) if effective_total > 0 else 0

        report = f"""# models/api.py テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| テスト対象 | `app/models/api.py` |
| テスト仕様 | `docs/testing/models/api_tests.md` |
| 実行時刻 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
| 総実行時間 | {duration:.2f}s |
| カバレッジ目標 | 90% |

## テスト結果統計

| カテゴリ | 総数 | 合格 | 失敗 | 予期された失敗 |
|------|------|------|------|----------|
| 正常系 | {len(self.results['normal'])} | {sum(1 for r in self.results['normal'] if r['outcome']=='passed')} | {sum(1 for r in self.results['normal'] if r['outcome']=='failed')} | {sum(1 for r in self.results['normal'] if r['outcome']=='xfailed')} |
| 異常系 | {len(self.results['error'])} | {sum(1 for r in self.results['error'] if r['outcome']=='passed')} | {sum(1 for r in self.results['error'] if r['outcome']=='failed')} | {sum(1 for r in self.results['error'] if r['outcome']=='xfailed')} |
| セキュリティ | {len(self.results['security'])} | {sum(1 for r in self.results['security'] if r['outcome']=='passed')} | {sum(1 for r in self.results['security'] if r['outcome']=='failed')} | {sum(1 for r in self.results['security'] if r['outcome']=='xfailed')} |
| **合計** | **{total}** | **{passed}** | **{failed}** | **{xfailed}** |

## テスト合格率

- **実際の合格率**: {pass_rate:.1f}%
- **有効合格率** (予期された失敗を除く): {effective_pass_rate:.1f}%

---

## 正常系テスト詳細

| ID | テスト名 | 結果 | 実行時間 |
|----|---------|------|----------|
"""
        for r in self.results['normal']:
            status = "✅" if r['outcome'] == 'passed' else "❌" if r['outcome'] == 'failed' else "⏭️"
            report += f"| {r['id']} | {r['name']} | {status} | {r['duration']} |\n"

        report += "\n## 異常系テスト詳細\n\n"
        report += "| ID | テスト名 | 結果 | 実行時間 |\n"
        report += "|----|---------|------|----------|\n"

        for r in self.results['error']:
            status = "✅" if r['outcome'] == 'passed' else "❌" if r['outcome'] == 'failed' else "⏭️"
            report += f"| {r['id']} | {r['name']} | {status} | {r['duration']} |\n"

        if self.results['security']:
            report += "\n## セキュリティテスト詳細\n\n"
            report += "| ID | テスト名 | 結果 | 実行時間 |\n"
            report += "|----|---------|------|----------|\n"

            for r in self.results['security']:
                status = "✅" if r['outcome'] == 'passed' else "❌" if r['outcome'] == 'failed' else "⏭️"
                report += f"| {r['id']} | {r['name']} | {status} | {r['duration']} |\n"

        report += f"""

---

## 結論

{"✅ すべてのテストに合格しました！" if failed == 0 else f"❌ {failed} 件のテストが失敗しました"}

---

*レポート生成時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return report

    def _generate_json_report(self, total, passed, failed, xfailed):
        """JSON形式のレポートを生成する。"""
        pass_rate = (passed / total * 100) if total > 0 else 0
        effective_total = total - xfailed
        effective_pass_rate = (passed / effective_total * 100) if effective_total > 0 else 0

        return {
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "xfailed": xfailed,
                "pass_rate": f"{pass_rate:.1f}%",
                "effective_pass_rate": f"{effective_pass_rate:.1f}%"
            },
            "categories": {
                "normal": {"results": self.results["normal"]},
                "error": {"results": self.results["error"]},
                "security": {"results": self.results["security"]}
            },
            "execution_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }


# Pytest フック
collector = TestResultCollector()

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """各テストの結果をキャプチャする。"""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        collector.add_result(
            nodeid=item.nodeid,
            outcome=report.outcome,
            duration=report.duration
        )

def pytest_sessionfinish(session, exitstatus):
    """すべてのテスト完了後に詳細レポートを生成するpytestフック。"""
    collector.generate_reports()
    print(f"\n✅ テストレポートを生成しました:")
    print(f"  - TestReport_api.md")
    print(f"  - TestReport_api.json")

