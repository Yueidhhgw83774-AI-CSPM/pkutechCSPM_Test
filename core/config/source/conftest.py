# -*- coding: utf-8 -*-
"""
config モジュールテスト用 pytest 設定ファイル。
テスト対象: app/core/config.py
テスト仕様: config_tests.md
"""

import os
import re
import sys
import pytest
import json
from pathlib import Path
from datetime import datetime

# ─── SourceCodeRoot を .env から読み込む ────────────────────────────────
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
            "security": []   # セキュリティテスト（該当する場合）
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
        class_name = nodeid.split("::")[-2] if "::" in nodeid else ""

        result = {
            "id": self._extract_test_id(test_name),
            "name": self._get_readable_name(test_name),
            "outcome": outcome,
            "duration": f"{duration:.3f}s"
        }

        # 分類する
        if "Security" in class_name:
            self.results["security"].append(result)
        elif "Error" in class_name or "_e0" in test_name:
            self.results["error"].append(result)
        else:
            self.results["normal"].append(result)

    def _extract_test_id(self, test_name: str) -> str:
        """テストメソッド名からテストIDを抽出する。"""
        # docstring またはテスト名からIDを抽出する
        if "cfg_" in test_name.lower():
            parts = test_name.split("_")
            for i, part in enumerate(parts):
                if part.lower() == "cfg" and i + 1 < len(parts):
                    return f"CFG-{parts[i+1].upper()}"
        return test_name

    def _get_readable_name(self, test_name: str) -> str:
        """テストメソッド名を読みやすい日本語名に変換する。"""
        name_map = {
            # 正常系テスト
            "test_load_from_env": "環境変数から設定読み込み",
            "test_default_values": "デフォルト値の適用",
            "test_opensearch_url_generation": "OpenSearch URL生成",
            "test_aws_opensearch_url": "AWS OpenSearch判定",
            "test_min_interval_calculation": "MIN_INTERVAL_SECONDS計算",
            "test_settings_instance_exists": "設定インスタンス存在確認",

            # 異常系テスト
            "test_missing_required_fields": "必須設定の欠落",
            "test_invalid_port_type": "無効な型",
            "test_invalid_opensearch_url": "無効なOpenSearch URL",

            # AWS判定テスト
            "test_is_aws_opensearch_service": "AWS OpenSearch Service判定",
        }
        return name_map.get(test_name, test_name.replace("_", " ").title())

    def generate_reports(self):
        """MarkdownとJSONレポートを生成する。"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        # 統計を計算する
        total = sum(len(results) for results in self.results.values())
        passed = sum(1 for cat in self.results.values() for r in cat if r["outcome"] == "passed")
        failed = sum(1 for cat in self.results.values() for r in cat if r["outcome"] == "failed")
        xfailed = sum(1 for cat in self.results.values() for r in cat if r["outcome"] == "xfailed")

        pass_rate = (passed / total * 100) if total > 0 else 0
        effective_pass_rate = (passed / (total - xfailed) * 100) if (total - xfailed) > 0 else 0

        # Markdownレポートを生成する
        self._generate_markdown_report(total, passed, failed, xfailed, pass_rate, effective_pass_rate, end_time)

        # JSONレポートを生成する
        self._generate_json_report(total, passed, failed, xfailed, pass_rate, effective_pass_rate, end_time)

    def _generate_markdown_report(self, total, passed, failed, xfailed, pass_rate, effective_pass_rate, end_time):
        """Markdown形式のテストレポートを生成する。"""
        report_path = Path(__file__).parent.parent / "reports" / "TestReport_config.md"

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# config.py テストレポート\n\n")

            # テスト概要
            f.write("## テスト概要\n\n")
            f.write("| 項目 | 値 |\n")
            f.write("|------|-----|\n")
            f.write("| テスト対象 | `app/core/config.py` |\n")
            f.write("| テスト仕様 | `config_tests.md` |\n")
            f.write(f"| 実行日時 | {end_time.strftime('%Y-%m-%d %H:%M:%S')} |\n")
            f.write("| カバレッジ目標 | 85% |\n\n")

            # テスト結果集計
            f.write("## テスト結果集計\n\n")
            f.write("| カテゴリ | 総数 | 成功 | 失敗 | 予期失敗 |\n")
            f.write("|------|------|------|------|----------|\n")

            normal_count = len(self.results["normal"])
            normal_passed = sum(1 for r in self.results["normal"] if r["outcome"] == "passed")
            normal_failed = sum(1 for r in self.results["normal"] if r["outcome"] == "failed")
            normal_xfailed = sum(1 for r in self.results["normal"] if r["outcome"] == "xfailed")

            error_count = len(self.results["error"])
            error_passed = sum(1 for r in self.results["error"] if r["outcome"] == "passed")
            error_failed = sum(1 for r in self.results["error"] if r["outcome"] == "failed")
            error_xfailed = sum(1 for r in self.results["error"] if r["outcome"] == "xfailed")

            security_count = len(self.results["security"])
            security_passed = sum(1 for r in self.results["security"] if r["outcome"] == "passed")
            security_failed = sum(1 for r in self.results["security"] if r["outcome"] == "failed")
            security_xfailed = sum(1 for r in self.results["security"] if r["outcome"] == "xfailed")

            f.write(f"| 正常系 | {normal_count} | {normal_passed} | {normal_failed} | {normal_xfailed} |\n")
            f.write(f"| 異常系 | {error_count} | {error_passed} | {error_failed} | {error_xfailed} |\n")
            f.write(f"| セキュリティ | {security_count} | {security_passed} | {security_failed} | {security_xfailed} |\n")
            f.write(f"| **合計** | **{total}** | **{passed}** | **{failed}** | **{xfailed}** |\n\n")

            # 合格率（ごうごくりつ）
            f.write("## 合格率\n\n")
            f.write(f"- **実際の合格率**: {pass_rate:.1f}%\n")
            f.write(f"- **有効合格率** (予期失敗を除く): {effective_pass_rate:.1f}%\n\n")

            f.write("---\n\n")

            # 正常系テスト詳細
            if self.results["normal"]:
                f.write("## 正常系テスト詳細\n\n")
                f.write("| ID | テスト名 | 結果 | 実行時間 |\n")
                f.write("|----|---------|------|----------|\n")
                for r in self.results["normal"]:
                    status = "✅" if r["outcome"] == "passed" else "❌" if r["outcome"] == "failed" else "⚠️"
                    f.write(f"| {r['id']} | {r['name']} | {status} | {r['duration']} |\n")
                f.write("\n")

            # 異常系テスト詳細
            if self.results["error"]:
                f.write("## 異常系テスト詳細\n\n")
                f.write("| ID | テスト名 | 結果 | 実行時間 |\n")
                f.write("|----|---------|------|----------|\n")
                for r in self.results["error"]:
                    status = "✅" if r["outcome"] == "passed" else "❌" if r["outcome"] == "failed" else "⚠️"
                    f.write(f"| {r['id']} | {r['name']} | {status} | {r['duration']} |\n")
                f.write("\n")

            # セキュリティテスト詳細
            if self.results["security"]:
                f.write("## セキュリティテスト詳細\n\n")
                f.write("| ID | テスト名 | 結果 | 実行時間 |\n")
                f.write("|----|---------|------|----------|\n")
                for r in self.results["security"]:
                    status = "✅" if r["outcome"] == "passed" else "❌" if r["outcome"] == "failed" else "⚠️"
                    f.write(f"| {r['id']} | {r['name']} | {status} | {r['duration']} |\n")
                f.write("\n")

            f.write("---\n\n")

            # 結論
            f.write("## 結論\n\n")
            if failed == 0:
                f.write("✅ **すべてのテストが成功!** config.pyモジュールが正常に動作しています。\n\n")
            else:
                f.write(f"❌ **{failed}件の失敗テストがあります**。詳細を確認して問題を修正してください。\n\n")

            f.write("---\n\n")
            f.write(f"*レポート生成日時: {end_time.strftime('%Y-%m-%d %H:%M:%S')}*\n")

        print(f"✅ Markdownレポートを生成しました: {report_path}")

    def _generate_json_report(self, total, passed, failed, xfailed, pass_rate, effective_pass_rate, end_time):
        """JSON形式のテストレポートを生成する。"""
        report_path = Path(__file__).parent.parent / "reports" / "TestReport_config.json"

        report_data = {
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "xfailed": xfailed,
                "pass_rate": f"{pass_rate:.1f}%",
                "effective_pass_rate": f"{effective_pass_rate:.1f}%"
            },
            "categories": self.results,
            "execution_time": end_time.strftime("%Y-%m-%d %H:%M:%S")
        }

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSONレポートを生成しました: {report_path}")


# グローバルコレクターインスタンス
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
    """テストセッション終了時にレポートを生成する。"""
    collector.generate_reports()
    # レポートパスを動的に計算する
    report_dir = Path(__file__).parent.parent / "reports"
    print(f"\n✅ テストレポートを生成しました:")
    print(f"  Markdown: {report_dir / 'TestReport_config.md'}")
    print(f"  JSON: {report_dir / 'TestReport_config.json'}")
