"""
health_checker.py テスト設定ファイル

pytest fixtureとテストレポート生成ロジックを含む
"""

import pytest
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv


def _load_source_root():
    """.env ファイルから SourceCodeRoot を読み込む

    Returns:
        str: SourceCodeRoot の絶対パス

    Raises:
        FileNotFoundError: .env ファイルが見つからない場合
        KeyError: SourceCodeRoot キーが .env に存在しない場合
    """
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if not env_path.exists():
        raise FileNotFoundError(f".env ファイルが見つかりません: {env_path}")

    load_dotenv(env_path)
    source_root = os.getenv("SourceCodeRoot")

    if not source_root:
        raise KeyError(".env ファイルに SourceCodeRoot キーが存在しません")

    return source_root


# ★★★ 重要: プロジェクトルートを動的に取得（絶対にハードコードしない） ★★★
PROJECT_ROOT = _load_source_root()
sys.path.insert(0, PROJECT_ROOT)


class TestResultCollector:
    """テスト結果を収集してレポートを生成する"""

    def __init__(self):
        self.results = {
            "normal": [],    # 正常系テスト
            "error": [],     # 異常系テスト
            "security": []   # セキュリティテスト
        }
        self.start_time = datetime.now()

    def add_result(self, nodeid: str, outcome: str, duration: float):
        """テスト結果を追加する

        分類規則:
        - "Security" または "SEC" を含む → security
        - "Error" または "_e0" を含む → error
        - その他 → normal
        """
        test_name = nodeid.split("::")[-1]

        # テストの種類を決定する
        if "Security" in nodeid or "_sec_" in test_name.lower():
            category = "security"
        elif "Error" in nodeid or "_e0" in test_name:
            category = "error"
        else:
            category = "normal"

        # 結果を追加
        self.results[category].append({
            "id": nodeid,
            "name": test_name,
            "outcome": outcome,
            "duration": round(duration * 1000, 2)  # ミリ秒に変換
        })


# グローバルコレクターインスタンス
collector = TestResultCollector()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """各テストの結果をキャプチャする"""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        collector.add_result(
            nodeid=item.nodeid,
            outcome=report.outcome,
            duration=report.duration
        )


def pytest_sessionfinish(session, exitstatus):
    """テストセッション終了時にレポートを生成する"""

    # 統計情報を計算
    total_tests = sum(len(results) for results in collector.results.values())
    passed_tests = sum(
        1 for category in collector.results.values()
        for result in category
        if result["outcome"] == "passed"
    )
    failed_tests = sum(
        1 for category in collector.results.values()
        for result in category
        if result["outcome"] == "failed"
    )
    xfailed_tests = sum(
        1 for category in collector.results.values()
        for result in category
        if result["outcome"] == "xfailed"
    )

    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    effective_pass_rate = (passed_tests / (total_tests - xfailed_tests) * 100) if (total_tests - xfailed_tests) > 0 else 0

    execution_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # JSONレポートを生成
    json_report = {
        "summary": {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "xfailed": xfailed_tests,
            "pass_rate": f"{pass_rate:.1f}%",
            "effective_pass_rate": f"{effective_pass_rate:.1f}%"
        },
        "categories": {
            "normal": {
                "total": len(collector.results["normal"]),
                "passed": sum(1 for r in collector.results["normal"] if r["outcome"] == "passed"),
                "failed": sum(1 for r in collector.results["normal"] if r["outcome"] == "failed"),
                "xfailed": sum(1 for r in collector.results["normal"] if r["outcome"] == "xfailed"),
                "results": collector.results["normal"]
            },
            "error": {
                "total": len(collector.results["error"]),
                "passed": sum(1 for r in collector.results["error"] if r["outcome"] == "passed"),
                "failed": sum(1 for r in collector.results["error"] if r["outcome"] == "failed"),
                "xfailed": sum(1 for r in collector.results["error"] if r["outcome"] == "xfailed"),
                "results": collector.results["error"]
            },
            "security": {
                "total": len(collector.results["security"]),
                "passed": sum(1 for r in collector.results["security"] if r["outcome"] == "passed"),
                "failed": sum(1 for r in collector.results["security"] if r["outcome"] == "failed"),
                "xfailed": sum(1 for r in collector.results["security"] if r["outcome"] == "xfailed"),
                "results": collector.results["security"]
            }
        },
        "execution_time": execution_time
    }

    # JSONレポートを保存
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    json_path = reports_dir / "TestReport_health_checker.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_report, f, ensure_ascii=False, indent=2)

    print(f"\n✅ JSONレポートを生成しました: {json_path}")

    # Markdownレポートを生成
    md_report = _generate_markdown_report(json_report)
    md_path = reports_dir / "TestReport_health_checker.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_report)

    print(f"✅ Markdownレポートを生成しました: {md_path}")

    print(f"\n✅ テストレポートを生成しました:")
    print(f"  - {md_path}")
    print(f"  - {json_path}")


def _generate_markdown_report(json_report: dict) -> str:
    """Markdown形式のテストレポートを生成する"""

    summary = json_report["summary"]
    categories = json_report["categories"]
    execution_time = json_report["execution_time"]

    # テストが成功したかを判定
    if summary["failed"] == 0:
        conclusion = "✅ **すべてのテストが成功しました！** コード品質は良好です。"
    else:
        conclusion = f"❌ **{summary['failed']}件のテストが失敗しました！** 修正後にコードを提出してください。"

    md = f"""# health_checker.py テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| テスト対象 | `app/core/health_checker.py` |
| テスト仕様 | `health_checker_tests.md` |
| 実行時刻 | {execution_time} |
| カバレッジ目標 | 90% |

## テスト結果統計

| カテゴリ | 総数 | 成功 | 失敗 | 予期された失敗 |
|------|------|------|------|----------|
| 正常系 | {categories['normal']['total']} | {categories['normal']['passed']} | {categories['normal']['failed']} | {categories['normal']['xfailed']} |
| 異常系 | {categories['error']['total']} | {categories['error']['passed']} | {categories['error']['failed']} | {categories['error']['xfailed']} |
| セキュリティ | {categories['security']['total']} | {categories['security']['passed']} | {categories['security']['failed']} | {categories['security']['xfailed']} |
| **合計** | **{summary['total']}** | **{summary['passed']}** | **{summary['failed']}** | **{summary['xfailed']}** |

## テスト成功率

- **実際の成功率**: {summary['pass_rate']}
- **有効成功率** (予期された失敗を除外): {summary['effective_pass_rate']}

---

## 正常系テスト詳細

| ID | テスト名 | 結果 | 実行時間 |
|----|---------|------|----------|
"""

    for result in categories['normal']['results']:
        status_icon = "✅" if result['outcome'] == "passed" else ("⚠️" if result['outcome'] == "xfailed" else "❌")
        test_name = _get_readable_name(result['name'])
        md += f"| - | {test_name} | {status_icon} | {result['duration']}ms |\n"

    md += "\n## 異常系テスト詳細\n\n"
    md += "| ID | テスト名 | 結果 | 実行時間 |\n"
    md += "|----|---------|------|----------|\n"

    for result in categories['error']['results']:
        status_icon = "✅" if result['outcome'] == "passed" else ("⚠️" if result['outcome'] == "xfailed" else "❌")
        test_name = _get_readable_name(result['name'])
        md += f"| - | {test_name} | {status_icon} | {result['duration']}ms |\n"

    md += "\n## セキュリティテスト詳細\n\n"
    md += "| ID | テスト名 | 結果 | 実行時間 |\n"
    md += "|----|---------|------|----------|\n"

    for result in categories['security']['results']:
        status_icon = "✅" if result['outcome'] == "passed" else ("⚠️" if result['outcome'] == "xfailed" else "❌")
        test_name = _get_readable_name(result['name'])
        md += f"| - | {test_name} | {status_icon} | {result['duration']}ms |\n"

    md += f"\n---\n\n## 結論\n\n{conclusion}\n\n---\n\n*レポート生成時刻: {execution_time}*\n"

    return md


def _get_readable_name(test_name: str) -> str:
    """テストメソッド名を読みやすい名前に変換する"""

    name_map = {
        # 正常系テスト
        "test_health_status_init_healthy": "HEALTH-001: HealthStatus初期化(正常状態)",
        "test_health_status_init_unhealthy": "HEALTH-002: HealthStatus初期化(異常状態)",
        "test_health_status_to_dict": "HEALTH-003: HealthStatus辞書形式変換",
        "test_perform_health_check_all_healthy": "HEALTH-004: 完全ヘルスチェック(全サービス正常)",
        "test_perform_health_check_opensearch_unhealthy": "HEALTH-005: 完全ヘルスチェック(OpenSearch異常)",
        "test_perform_health_check_litellm_unhealthy": "HEALTH-006: 完全ヘルスチェック(LiteLLM異常)",
        "test_perform_health_check_all_unhealthy": "HEALTH-007: 完全ヘルスチェック(全サービス異常)",
        "test_check_opensearch_healthy": "HEALTH-008: OpenSearch接続チェック(正常)",
        "test_check_opensearch_unhealthy": "HEALTH-009: OpenSearch接続チェック(異常)",
        "test_check_litellm_healthy": "HEALTH-010: LiteLLM接続チェック(正常)",
        "test_check_litellm_unhealthy": "HEALTH-011: LiteLLM接続チェック(異常)",

        # 異常系テスト
        "test_health_status_none_message": "HEALTH-E01: HealthStatus messageがNone",
        "test_health_status_empty_message": "HEALTH-E02: HealthStatus messageが空文字列",
        "test_health_status_none_details": "HEALTH-E03: HealthStatus detailsがNone",
        "test_perform_health_check_opensearch_exception": "HEALTH-E04: ヘルスチェック時OpenSearch例外",
        "test_perform_health_check_litellm_exception": "HEALTH-E05: ヘルスチェック時LiteLLM例外",
        "test_perform_health_check_both_exception": "HEALTH-E06: ヘルスチェック時全サービス例外",
        "test_check_opensearch_connection_timeout": "HEALTH-E07: OpenSearch接続タイムアウト",
        "test_check_opensearch_authentication_error": "HEALTH-E08: OpenSearch認証失敗",
        "test_check_litellm_connection_timeout": "HEALTH-E09: LiteLLM接続タイムアウト",
        "test_check_litellm_invalid_response": "HEALTH-E10: LiteLLM無効な応答",

        # セキュリティテスト
        "test_sec_01_no_credentials_in_error": "HEALTH-SEC-01: エラー情報に認証情報を含まない",
        "test_sec_02_no_internal_paths_in_response": "HEALTH-SEC-02: 応答に内部パスを含まない",
        "test_sec_03_response_timing_consistent": "HEALTH-SEC-03: 応答時間の一貫性",
        "test_sec_04_details_structure_consistent": "HEALTH-SEC-04: details構造の一貫性",
        "test_sec_05_no_stack_trace_in_details": "HEALTH-SEC-05: detailsにスタックトレースを含まない",
        "test_sec_06_timeout_values_not_exposed": "HEALTH-SEC-06: タイムアウト値を応答に露出しない"
    }

    return name_map.get(test_name, test_name)
