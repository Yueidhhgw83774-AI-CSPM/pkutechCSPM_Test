"""
error_handlers.py テスト用 pytest 設定ファイル

このファイルはテスト実行を管理し、自動的にレポートを生成します。
"""
import pytest
import json
import sys
import re
from pathlib import Path
from datetime import datetime


# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent.parent / "platform_python_backend-testing"
sys.path.insert(0, str(project_root))


class TestResultCollector:
    """テスト結果を収集してレポートを生成するクラス"""

    def __init__(self):
        self.results = {
            "normal": [],
            "error": [],
            "security": []
        }
        self.start_time = datetime.now()

    def add_result(self, nodeid: str, outcome: str, duration: float):
        """テスト結果を追加"""
        test_name = nodeid.split("::")[-1]

        # テストIDの抽出を試みる
        test_id = self._extract_test_id(test_name)

        # 分類
        if "Security" in nodeid or "_SEC" in test_name or "SEC-" in test_id:
            category = "security"
        elif "Errors" in nodeid or "_E0" in test_name or test_id.startswith("ERH-E"):
            category = "error"
        else:
            category = "normal"

        self.results[category].append({
            "id": test_id,
            "name": self._get_readable_name(test_name),
            "outcome": outcome,
            "duration": round(duration * 1000, 2)  # msに変換
        })

    def _extract_test_id(self, test_name: str) -> str:
        """テスト名からテストIDを抽出"""
        # ドキュメント文字列からERH-XXXパターンを抽出する
        # 実際にはpytestのreportから取得できないため、テスト名からマッピング
        id_map = self._get_test_id_map()
        return id_map.get(test_name, "")

    def _get_test_id_map(self) -> dict:
        """テスト名とテストIDのマッピング"""
        return {
            # TestCreateErrorResponse
            "test_basic_error_response": "ERH-001",
            "test_with_custom_error_id": "ERH-002",
            "test_with_details": "ERH-003",
            "test_without_details": "ERH-004",
            "test_with_empty_dict_details": "ERH-005",
            "test_auto_generated_error_id_is_uuid": "ERH-006",

            # TestHandleOpenSearchExceptions
            "test_authentication_exception": "ERH-007",
            "test_authorization_exception": "ERH-008",
            "test_generic_exception": "ERH-009",
            "test_custom_operation_in_message": "ERH-010",
            "test_default_operation": "ERH-011",

            # TestHandleChatExceptions
            "test_opensearch_authentication_exception": "ERH-012",
            "test_opensearch_authorization_exception": "ERH-013",
            "test_http_exception_reraise": "ERH-014",
            "test_generic_exception": "ERH-015",
            "test_chat_default_operation": "ERH-016",

            # TestLogRequestStart
            "test_basic_log": "ERH-017",
            "test_with_kwargs_debug_enabled": "ERH-018",
            "test_with_empty_kwargs_debug_enabled": "ERH-019",
            "test_with_kwargs_debug_disabled": "ERH-020",

            # TestLogRequestEnd
            "test_success_true": "ERH-021",
            "test_success_false": "ERH-022",
            "test_default_success": "ERH-023",

            # TestCreateErrorResponseErrors
            "test_empty_message": "ERH-E01",
            "test_unusual_status_code": "ERH-E02",

            # TestHandleOpenSearchExceptionsErrors
            "test_none_exception": "ERH-E03",

            # TestHandleChatExceptionsErrors
            "test_none_session_id": "ERH-E04",
            "test_empty_session_id": "ERH-E05",

            # TestLogFunctionsErrors
            "test_log_request_start_none_operation": "ERH-E06",
            "test_log_request_end_none_session_id": "ERH-E07",

            # TestErrorHandlersSecurity
            "test_no_internal_paths_in_response": "ERH-SEC-01",
            "test_no_stacktrace_in_response": "ERH-SEC-02",
            "test_error_id_unpredictable": "ERH-SEC-03",
            "test_no_credentials_in_error_message": "ERH-SEC-04",
            "test_details_not_in_http_response": "ERH-SEC-05",
            "test_session_id_not_in_http_response": "ERH-SEC-06",
            "test_error_id_length_appropriate": "ERH-SEC-07",
            "test_log_injection_newline_handling": "ERH-SEC-08",
            "test_crlf_injection_json_safe": "ERH-SEC-09",
        }

    def _get_readable_name(self, test_name: str) -> str:
        """テスト名を読みやすい名前に変換"""
        name_map = {
            "test_basic_error_response": "基本パラメータのみでエラーレスポンスを作成",
            "test_with_custom_error_id": "カスタムerror_id指定",
            "test_with_details": "details指定でログ出力",
            "test_without_details": "detailsなしでログ出力",
            "test_with_empty_dict_details": "空の辞書detailsでログ出力なし",
            "test_auto_generated_error_id_is_uuid": "自動生成error_idがUUID形式",
            "test_authentication_exception": "AuthenticationException処理",
            "test_authorization_exception": "AuthorizationException処理",
            "test_generic_exception": "その他例外処理",
            "test_custom_operation_in_message": "カスタムoperation指定",
            "test_default_operation": "デフォルトoperation使用",
            "test_opensearch_authentication_exception": "OpenSearch認証例外の委譲",
            "test_opensearch_authorization_exception": "OpenSearch認可例外の委譲",
            "test_http_exception_reraise": "HTTPExceptionの再発生",
            "test_generic_exception": "その他例外の500エラー",
            "test_chat_default_operation": "デフォルトoperation使用",
            "test_basic_log": "基本ログ出力",
            "test_with_kwargs_debug_enabled": "追加kwargs（DEBUG有効）",
            "test_with_empty_kwargs_debug_enabled": "空kwargs（DEBUG有効）",
            "test_with_kwargs_debug_disabled": "追加kwargs（DEBUG無効）",
            "test_success_true": "success=True時のログ",
            "test_success_false": "success=False時のログ",
            "test_default_success": "デフォルトsuccess時のログ",
            "test_empty_message": "空メッセージ処理",
            "test_unusual_status_code": "不正ステータスコード処理",
            "test_none_exception": "None例外処理",
            "test_none_session_id": "None session_id処理",
            "test_empty_session_id": "空session_id処理",
            "test_log_request_start_none_operation": "None operation処理",
            "test_log_request_end_none_session_id": "None session_id処理",
            "test_no_internal_paths_in_response": "内部パス未露出",
            "test_no_stacktrace_in_response": "スタックトレース未露出",
            "test_error_id_unpredictable": "予測不可能なUUID",
            "test_no_credentials_in_error_message": "認証情報未露出",
            "test_details_not_in_http_response": "detailsパラメータ未露出",
            "test_session_id_not_in_http_response": "セッションID未露出",
            "test_error_id_length_appropriate": "error_id長さ検証",
            "test_log_injection_newline_handling": "ログインジェクション対策",
            "test_crlf_injection_json_safe": "CRLFインジェクション対策",
        }
        return name_map.get(test_name, test_name)

    def generate_reports(self, session):
        """Markdownおよび JSONレポートを生成"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        # 統計情報を計算
        total = sum(len(v) for v in self.results.values())
        passed = sum(1 for cat in self.results.values() for r in cat if r["outcome"] == "passed")
        failed = sum(1 for cat in self.results.values() for r in cat if r["outcome"] == "failed")
        xfailed = sum(1 for cat in self.results.values() for r in cat if r["outcome"] == "xfailed")

        pass_rate = (passed / total * 100) if total > 0 else 0
        effective_pass_rate = ((passed + xfailed) / total * 100) if total > 0 else 0

        # レポート出力先
        report_dir = Path(__file__).parent.parent / "reports"
        report_dir.mkdir(exist_ok=True)

        # Markdownレポート生成
        md_path = report_dir / "TestReport_error_handlers.md"
        self._generate_markdown_report(md_path, total, passed, failed, xfailed, pass_rate, effective_pass_rate, end_time)

        # JSONレポート生成
        json_path = report_dir / "TestReport_error_handlers.json"
        self._generate_json_report(json_path, total, passed, failed, xfailed, pass_rate, effective_pass_rate, end_time)

        print(f"\n✅ 测试报告已生成:")
        print(f"  - {md_path}")
        print(f"  - {json_path}\n")

    def _generate_markdown_report(self, path, total, passed, failed, xfailed, pass_rate, effective_pass_rate, end_time):
        """Markdownレポートを生成"""
        content = f"""# error_handlers.py 测试报告

## 测试概要

| 项目 | 值 |
|------|-----|
| 测试对象 | `app/core/error_handlers.py` |
| 测试规格 | `error_handlers_tests.md` |
| 执行时间 | {end_time.strftime('%Y-%m-%d %H:%M:%S')} |
| 覆盖率目标 | 90% |

## 测试结果统计

| 类别 | 总数 | 通过 | 失败 | 预期失败 |
|------|------|------|------|----------|
| 正常系 | {len(self.results['normal'])} | {sum(1 for r in self.results['normal'] if r['outcome'] == 'passed')} | {sum(1 for r in self.results['normal'] if r['outcome'] == 'failed')} | {sum(1 for r in self.results['normal'] if r['outcome'] == 'xfailed')} |
| 异常系 | {len(self.results['error'])} | {sum(1 for r in self.results['error'] if r['outcome'] == 'passed')} | {sum(1 for r in self.results['error'] if r['outcome'] == 'failed')} | {sum(1 for r in self.results['error'] if r['outcome'] == 'xfailed')} |
| 安全测试 | {len(self.results['security'])} | {sum(1 for r in self.results['security'] if r['outcome'] == 'passed')} | {sum(1 for r in self.results['security'] if r['outcome'] == 'failed')} | {sum(1 for r in self.results['security'] if r['outcome'] == 'xfailed')} |
| **合计** | **{total}** | **{passed}** | **{failed}** | **{xfailed}** |

## 测试通过率

- **实际通过率**: {pass_rate:.1f}%
- **有效通过率** (排除预期失败): {effective_pass_rate:.1f}%

---

## 正常系测试详情

| ID | 测试名称 | 结果 | 执行时间 |
|----|---------|------|----------|
"""
        for result in self.results['normal']:
            status = "✅" if result['outcome'] == "passed" else "❌" if result['outcome'] == "failed" else "⚠️"
            content += f"| {result['id']} | {result['name']} | {status} | {result['duration']}ms |\n"

        content += """
## 异常系测试详情

| ID | 测试名称 | 结果 | 执行时间 |
|----|---------|------|----------|
"""
        for result in self.results['error']:
            status = "✅" if result['outcome'] == "passed" else "❌" if result['outcome'] == "failed" else "⚠️"
            content += f"| {result['id']} | {result['name']} | {status} | {result['duration']}ms |\n"

        content += """
## 安全测试详情

| ID | 测试名称 | 结果 | 执行时间 |
|----|---------|------|----------|
"""
        for result in self.results['security']:
            status = "✅" if result['outcome'] == "passed" else "❌" if result['outcome'] == "failed" else "⚠️"
            content += f"| {result['id']} | {result['name']} | {status} | {result['duration']}ms |\n"

        # 结论
        if failed == 0:
            conclusion = "✅ **全てのテストが正常に完了しました。** error_handlers モジュールは期待通りに動作しています。"
        else:
            conclusion = f"⚠️ **{failed}件のテストが失敗しました。** 詳細を確認して修正してください。"

        content += f"""
---

## 结论

{conclusion}

---

*报告生成时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}*
"""

        path.write_text(content, encoding='utf-8')
        print(f"✅ Markdown报告已生成: {path}")

    def _generate_json_report(self, path, total, passed, failed, xfailed, pass_rate, effective_pass_rate, end_time):
        """JSONレポートを生成"""
        report = {
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "xfailed": xfailed,
                "pass_rate": f"{pass_rate:.1f}%",
                "effective_pass_rate": f"{effective_pass_rate:.1f}%"
            },
            "categories": {
                "normal": {
                    "total": len(self.results['normal']),
                    "passed": sum(1 for r in self.results['normal'] if r['outcome'] == 'passed'),
                    "failed": sum(1 for r in self.results['normal'] if r['outcome'] == 'failed'),
                    "xfailed": sum(1 for r in self.results['normal'] if r['outcome'] == 'xfailed'),
                    "results": self.results['normal']
                },
                "error": {
                    "total": len(self.results['error']),
                    "passed": sum(1 for r in self.results['error'] if r['outcome'] == 'passed'),
                    "failed": sum(1 for r in self.results['error'] if r['outcome'] == 'failed'),
                    "xfailed": sum(1 for r in self.results['error'] if r['outcome'] == 'xfailed'),
                    "results": self.results['error']
                },
                "security": {
                    "total": len(self.results['security']),
                    "passed": sum(1 for r in self.results['security'] if r['outcome'] == 'passed'),
                    "failed": sum(1 for r in self.results['security'] if r['outcome'] == 'failed'),
                    "xfailed": sum(1 for r in self.results['security'] if r['outcome'] == 'xfailed'),
                    "results": self.results['security']
                }
            },
            "execution_time": end_time.strftime('%Y-%m-%d %H:%M:%S')
        }

        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"✅ JSON报告已生成: {path}")


# グローバルコレクター
collector = TestResultCollector()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """各テストの結果をキャプチャ"""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        collector.add_result(
            nodeid=item.nodeid,
            outcome=report.outcome,
            duration=report.duration
        )


def pytest_sessionfinish(session, exitstatus):
    """テストセッション終了時にレポートを生成"""
    collector.generate_reports(session)


@pytest.fixture(autouse=True)
def reset_error_handlers_module():
    """テストごとにerror_handlersモジュールの状態をリセット"""
    yield

    # テスト後のクリーンアップ
    modules_to_remove = [
        key for key in sys.modules
        if key.startswith("app.core.error_handlers")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]
