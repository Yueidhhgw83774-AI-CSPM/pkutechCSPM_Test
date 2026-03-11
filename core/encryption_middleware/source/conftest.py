"""
encryption_middleware テスト用 pytest 設定ファイル

このファイルは以下の機能を提供:
1. テストモジュールのインポートパス設定
2. テスト結果の収集と分類
3. テスト完了後の自動レポート生成（Markdown/JSON）

レポート出力先:
  - Markdown: ../reports/TestReport_encryption_middleware.md
  - JSON:     ../reports/TestReport_encryption_middleware.json
"""

import pytest
import json
import sys
from pathlib import Path
from datetime import datetime

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent.parent.parent / "platform_python_backend-testing"
sys.path.insert(0, str(project_root))


class TestResultCollector:
    """テスト結果を収集してレポート生成用に保存するクラス"""

    def __init__(self):
        """初期化: 結果を格納する辞書を作成"""
        self.results = {
            "normal": [],    # 正常系テスト
            "error": [],     # 異常系テスト
            "security": []   # セキュリティテスト
        }
        self.start_time = datetime.now()

    def add_result(self, nodeid: str, outcome: str, duration: float):
        """テスト結果を追加

        Args:
            nodeid: テストのノードID（例: test_file.py::TestClass::test_method）
            outcome: テスト結果（passed/failed/skipped/xfailed）
            duration: テスト実行時間（秒）
        """
        # テスト名とクラス名を抽出
        parts = nodeid.split("::")
        if len(parts) >= 3:
            test_class = parts[1]
            test_name = parts[2]
        elif len(parts) == 2:
            test_class = ""
            test_name = parts[1]
        else:
            test_class = ""
            test_name = nodeid

        # テスト結果をカテゴリに分類
        if "Security" in test_class or "_sec_" in test_name.lower():
            category = "security"
        elif "Error" in test_class or "_e0" in test_name or "error" in test_name.lower():
            category = "error"
        else:
            category = "normal"

        # 結果を記録
        result_entry = {
            "name": test_name,
            "class": test_class,
            "outcome": outcome,
            "duration": round(duration * 1000, 2)  # ミリ秒に変換
        }
        self.results[category].append(result_entry)


# グローバルコレクターインスタンス
collector = TestResultCollector()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """各テストの実行結果をキャプチャ

    pytest のフックを使用して、各テストケースの実行結果を収集します。
    """
    outcome = yield
    report = outcome.get_result()

    # テスト本体（call フェーズ）の結果のみを記録
    if report.when == "call":
        collector.add_result(
            nodeid=item.nodeid,
            outcome=report.outcome,
            duration=report.duration
        )


def pytest_sessionfinish(session, exitstatus):
    """全テスト終了時にレポートを生成

    Markdown形式とJSON形式の2種類のレポートを生成します。
    """
    # レポート出力ディレクトリ
    report_dir = Path(__file__).parent.parent / "reports"
    report_dir.mkdir(exist_ok=True)

    # 統計情報を計算
    total_tests = sum(len(collector.results[cat]) for cat in collector.results)

    stats = {}
    for category in ["normal", "error", "security"]:
        results = collector.results[category]
        passed = sum(1 for r in results if r["outcome"] == "passed")
        failed = sum(1 for r in results if r["outcome"] == "failed")
        xfailed = sum(1 for r in results if r["outcome"] in ["xfailed", "xpassed"])
        skipped = sum(1 for r in results if r["outcome"] == "skipped")

        stats[category] = {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "xfailed": xfailed,
            "skipped": skipped
        }

    # 全体統計
    total_passed = sum(s["passed"] for s in stats.values())
    total_failed = sum(s["failed"] for s in stats.values())
    total_xfailed = sum(s["xfailed"] for s in stats.values())
    total_skipped = sum(s["skipped"] for s in stats.values())

    # 通過率計算
    if total_tests > 0:
        pass_rate = (total_passed / total_tests) * 100
        # xfailedを除外した有効通過率
        effective_total = total_tests - total_xfailed
        effective_pass_rate = (total_passed / effective_total * 100) if effective_total > 0 else 0
    else:
        pass_rate = 0
        effective_pass_rate = 0

    execution_time = datetime.now()

    # Markdownレポート生成
    _generate_markdown_report(
        report_dir / "TestReport_encryption_middleware.md",
        stats,
        collector.results,
        total_tests,
        total_passed,
        total_failed,
        total_xfailed,
        total_skipped,
        pass_rate,
        effective_pass_rate,
        execution_time
    )

    # JSONレポート生成
    _generate_json_report(
        report_dir / "TestReport_encryption_middleware.json",
        stats,
        collector.results,
        total_tests,
        total_passed,
        total_failed,
        total_xfailed,
        total_skipped,
        pass_rate,
        effective_pass_rate,
        execution_time
    )

    print(f"\n✅ 测试报告已生成:")
    print(f"  - {report_dir / 'TestReport_encryption_middleware.md'}")
    print(f"  - {report_dir / 'TestReport_encryption_middleware.json'}")


def _generate_markdown_report(filepath, stats, results, total, passed, failed, xfailed, skipped,
                               pass_rate, effective_pass_rate, execution_time):
    """Markdown形式のテストレポートを生成"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# encryption_middleware.py 测试报告\n\n")

        # テスト概要
        f.write("## 测试概要\n\n")
        f.write("| 项目 | 值 |\n")
        f.write("|------|-----|\n")
        f.write("| 测试对象 | `app/core/encryption_middleware.py` |\n")
        f.write("| 测试规格 | `docs/testing/core/encryption_middleware_tests.md` |\n")
        f.write(f"| 执行时间 | {execution_time.strftime('%Y-%m-%d %H:%M:%S')} |\n")
        f.write("| 覆盖率目标 | 85% |\n\n")

        # テスト結果統計
        f.write("## 测试结果统计\n\n")
        f.write("| 类别 | 总数 | 通过 | 失败 | 预期失败 | 跳过 |\n")
        f.write("|------|------|------|------|----------|------|\n")
        f.write(f"| 正常系 | {stats['normal']['total']} | {stats['normal']['passed']} | "
                f"{stats['normal']['failed']} | {stats['normal']['xfailed']} | {stats['normal']['skipped']} |\n")
        f.write(f"| 异常系 | {stats['error']['total']} | {stats['error']['passed']} | "
                f"{stats['error']['failed']} | {stats['error']['xfailed']} | {stats['error']['skipped']} |\n")
        f.write(f"| 安全测试 | {stats['security']['total']} | {stats['security']['passed']} | "
                f"{stats['security']['failed']} | {stats['security']['xfailed']} | {stats['security']['skipped']} |\n")
        f.write(f"| **合计** | **{total}** | **{passed}** | **{failed}** | **{xfailed}** | **{skipped}** |\n\n")

        # 通過率
        f.write("## 测试通过率\n\n")
        f.write(f"- **实际通过率**: {pass_rate:.1f}%\n")
        f.write(f"- **有效通过率** (排除预期失败): {effective_pass_rate:.1f}%\n\n")

        f.write("---\n\n")

        # 各カテゴリの詳細
        categories = [
            ("normal", "正常系测试详情"),
            ("error", "异常系测试详情"),
            ("security", "安全测试详情")
        ]

        for cat_key, cat_title in categories:
            f.write(f"## {cat_title}\n\n")
            if results[cat_key]:
                f.write("| ID | 测试名称 | 结果 | 执行时间 |\n")
                f.write("|----|---------|------|----------|\n")
                for idx, result in enumerate(results[cat_key], 1):
                    outcome_symbol = {
                        "passed": "✅",
                        "failed": "❌",
                        "xfailed": "⚠️",
                        "xpassed": "✅",
                        "skipped": "⏭️"
                    }.get(result["outcome"], "❓")

                    readable_name = _get_readable_name(result["name"])
                    f.write(f"| {idx} | {readable_name} | {outcome_symbol} | {result['duration']:.2f}ms |\n")
            else:
                f.write("_このカテゴリのテストはありません_\n")
            f.write("\n")

        f.write("---\n\n")

        # 結論
        f.write("## 结论\n\n")
        if failed == 0 and skipped == 0:
            f.write("✅ **所有测试通过!** 加密中间件模块功能正常。\n\n")
        elif failed == 0:
            f.write(f"⚠️ **测试基本通过，但有 {skipped} 个测试被跳过。** 请检查跳过原因。\n\n")
        else:
            f.write(f"❌ **有 {failed} 个测试失败!** 需要修复相关问题。\n\n")

        f.write("---\n\n")
        f.write(f"*报告生成时间: {execution_time.strftime('%Y-%m-%d %H:%M:%S')}*\n")

    print(f"✅ Markdown报告已生成: {filepath}")


def _generate_json_report(filepath, stats, results, total, passed, failed, xfailed, skipped,
                          pass_rate, effective_pass_rate, execution_time):
    """JSON形式のテストレポートを生成"""

    report = {
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "xfailed": xfailed,
            "skipped": skipped,
            "pass_rate": f"{pass_rate:.1f}%",
            "effective_pass_rate": f"{effective_pass_rate:.1f}%"
        },
        "categories": {
            "normal": {
                "total": stats["normal"]["total"],
                "passed": stats["normal"]["passed"],
                "failed": stats["normal"]["failed"],
                "xfailed": stats["normal"]["xfailed"],
                "skipped": stats["normal"]["skipped"],
                "results": results["normal"]
            },
            "error": {
                "total": stats["error"]["total"],
                "passed": stats["error"]["passed"],
                "failed": stats["error"]["failed"],
                "xfailed": stats["error"]["xfailed"],
                "skipped": stats["error"]["skipped"],
                "results": results["error"]
            },
            "security": {
                "total": stats["security"]["total"],
                "passed": stats["security"]["passed"],
                "failed": stats["security"]["failed"],
                "xfailed": stats["security"]["xfailed"],
                "skipped": stats["security"]["skipped"],
                "results": results["security"]
            }
        },
        "execution_time": execution_time.strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"✅ JSON报告已生成: {filepath}")


def _get_readable_name(test_name: str) -> str:
    """测试方法名转换为可读名称

    根据测试要件文档中的测试名称生成映射表
    """
    name_map = {
        # 初期化テスト
        "test_init_with_successful_decryption_test": "ENCMW-001: 初期化時の復号テスト成功",
        "test_init_with_decryption_test_failure": "ENCMW-E01: 初期化時の復号テスト失敗",
        "test_init_with_decryption_test_exception": "ENCMW-E02: 初期化時の復号テスト例外",
        "test_init_with_custom_paths": "ENCMW-013: カスタムパスリストでの初期化",

        # パススルーテスト
        "test_non_http_scope_passthrough": "ENCMW-002: 非HTTPスコープのパススルー",
        "test_non_target_path_passthrough": "ENCMW-003: 復号対象外パスのパススルー",
        "test_get_request_passthrough": "ENCMW-004: GET リクエストのパススルー",
        "test_empty_body_passthrough": "ENCMW-005: 空ボディのパススルー",
        "test_non_json_body_passthrough": "ENCMW-006: 非JSONボディのパススルー",
        "test_non_encrypted_json_passthrough": "ENCMW-007: encryptedフラグなしのパススルー",
        "test_http_disconnect_message": "ENCMW-014: http.disconnect メッセージ処理",

        # 復号成功テスト
        "test_decrypt_encrypted_request_success": "ENCMW-008: 暗号化リクエストの復号成功",
        "test_content_length_header_update": "ENCMW-009: Content-Length ヘッダー更新",
        "test_content_length_header_addition": "ENCMW-010: Content-Length ヘッダー追加",
        "test_decrypt_with_valid_auth_hash": "ENCMW-011: 認証ハッシュ検証成功",
        "test_decrypt_without_auth_hash": "ENCMW-015: 認証ハッシュヘッダーなしで復号成功",

        # ファクトリ関数テスト
        "test_create_decryption_middleware": "ENCMW-012: ファクトリ関数でミドルウェア生成",

        # 異常系テスト
        "test_decrypt_with_invalid_auth_hash": "ENCMW-E03: 無効な認証ハッシュ",
        "test_decrypt_with_missing_iv": "ENCMW-E04: IV欠落エラー",
        "test_decrypt_with_invalid_ciphertext": "ENCMW-E05: 暗号文復号失敗",
        "test_decrypt_with_decryption_exception": "ENCMW-E06: 復号処理中の例外",
        "test_send_error_response_for_decryption_failure": "ENCMW-E07: 復号失敗時の400エラーレスポンス",
        "test_malformed_encrypted_data_structure": "ENCMW-E08: 不正な暗号化データ構造",
        "test_receive_exception_handling": "ENCMW-E09: receive() 関数の例外処理",

        # セキュリティテスト
        "test_sec_01_shared_secret_not_logged": "ENCMW-SEC-01: 共有秘密鍵がログに出力されないこと",
        "test_sec_02_decrypted_data_not_logged": "ENCMW-SEC-02: 復号後のデータがログに出力されないこと",
        "test_sec_03_auth_hash_not_logged": "ENCMW-SEC-03: 認証ハッシュがログに出力されないこと",
        "test_sec_04_error_message_safe": "ENCMW-SEC-04: エラーメッセージに秘密情報が含まれないこと",
        "test_sec_05_timing_attack_resistance": "ENCMW-SEC-05: タイミング攻撃への耐性",
    }

    return name_map.get(test_name, test_name)
