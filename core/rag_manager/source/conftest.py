# -*- coding: utf-8 -*-
"""
rag_manager モジュールテストのpytest fixtures。

このモジュールはrag_managerモジュールのテスト用共有フィクスチャを提供し、
環境設定、モックオブジェクト、テスト結果収集を含みます。
"""

import os
import sys
import json
import pytest
from datetime import datetime
from pathlib import Path
from typing import Generator
from unittest.mock import patch, MagicMock, AsyncMock
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
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# =============================================================================
# モジュールリセット fixture | モジュールリセットFixture
# =============================================================================

@pytest.fixture(autouse=True)
def reset_rag_manager_module():
    """テスト間でrag_managerモジュールのグローバル状態をリセットする。

    rag_manager.pyはシングルトンパターンとグローバル変数を使用しているため、
    テストの独立性を保証するためにテスト間でリセットする必要があります。
    """
    # テスト前にモジュールキャッシュをクリア
    modules_to_remove = [
        key for key in list(sys.modules.keys())
        if key.startswith("app.core.rag_manager") or key.startswith("app.rag")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]

    yield

    # テスト後のクリーンアップ
    try:
        import app.core.rag_manager as rag_module
        # グローバル変数をリセット
        rag_module._global_rag_manager = None
        # クラス変数をリセット
        rag_module.RAGManager._instance = None
    except (ImportError, AttributeError):
        pass

    # モジュールキャッシュを再度クリア
    modules_to_remove = [
        key for key in list(sys.modules.keys())
        if key.startswith("app.core.rag_manager") or key.startswith("app.rag")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


# =============================================================================
# Mock Fixtures | モックオブジェクト フィクチャーズ
# =============================================================================

@pytest.fixture
def mock_enhanced_rag_search():
    """モックEnhancedRAGSearchオブジェクトを提供する。

    テスト中の外部依存関係を防ぎます。
    """
    mock_rag = MagicMock()
    mock_rag.initialize = AsyncMock(return_value=True)
    mock_rag.get_health = AsyncMock(return_value={"status": "healthy"})
    return mock_rag


# =============================================================================
# テスト結果収集
# =============================================================================

# グローバルテスト結果ストレージ
_test_results = []


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """テスト結果をキャプチャするフック。

    このフックは各テストの結果（成功、失敗、予期された失敗）を
    キャプチャし、レポート生成のために保存します。
    """
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call":
        # xfailマークされたテストをチェック
        is_xfail = hasattr(rep, "wasxfail") or (
            hasattr(item, '_evalxfail') and item._evalxfail.wasvalid()
        )

        result = {
            "nodeid": item.nodeid,
            "outcome": rep.outcome,
            "duration": rep.duration,
            "longrepr": str(rep.longrepr) if rep.longrepr else "",
            "is_xfail": is_xfail
        }
        _test_results.append(result)


def pytest_sessionfinish(session, exitstatus):
    """すべてのテスト完了後に詳細レポートを生成する。

    pytestがすべてのテストを実行した後にこの関数を呼び出します。
MarkdownとJSONの両方の形式でレポートを生成します。
    """
    report_dir = Path(__file__).parent.parent / "reports"
    os.makedirs(report_dir, exist_ok=True)

    # テスト結果を解析
    normal_tests = []
    error_tests = []
    security_tests = []

    passed = 0
    failed = 0
    xfailed = 0

    for result in _test_results:
        nodeid = result["nodeid"]
        outcome = result["outcome"]
        duration = result["duration"]
        is_xfail = result.get("is_xfail", False)

        # xfailテストの結果を上書き
        if is_xfail:
            outcome = "xfailed"

        # テストを分類
        test_info = _parse_test_info(nodeid, outcome, duration)

        if "Security" in nodeid:
            security_tests.append(test_info)
        elif "Error" in nodeid:
            error_tests.append(test_info)
        else:
            normal_tests.append(test_info)

        # 結果をカウント
        if outcome == "passed":
            passed += 1
        elif outcome == "xfailed":
            xfailed += 1
        else:
            failed += 1

    # レポートを生成
    _generate_markdown_report(report_dir, normal_tests, error_tests, security_tests, passed, failed, xfailed)
    _generate_json_report(report_dir, normal_tests, error_tests, security_tests, passed, failed, xfailed)


def _parse_test_info(nodeid: str, outcome: str, duration: float) -> dict:
    """
nodeidからテスト情報を解析する。
    """
    # テストIDと名前を抽出
    test_id, test_name = _get_test_id_and_name(nodeid)

    # ステータス絵文字をフォーマット
    if outcome == "passed":
        status = "✅ 成功"
    elif outcome == "xfailed":
        status = "⚠️ 予期された失敗"
    else:
        status = "❌ 失敗"

    return {
        "id": test_id,
        "name": test_name,
        "status": status,
        "outcome": outcome,
        "duration": f"{duration*1000:.2f}ms"
    }


def _get_test_id_and_name(nodeid: str) -> tuple:
    """
nodeidからテストIDと読みやすい名前を取得する。
    """
    # テストIDから名前へのマッピング
    name_map = {
        "test_import_rag_manager_module": ("RAG-001", "モジュールインポート成功"),
        "test_get_instance_returns_rag_manager": ("RAG-002", "シングルトンインスタンス取得"),
        "test_get_instance_returns_same_instance": ("RAG-003", "シングルトン一貫性"),
        "test_initialize_success": ("RAG-004", "初期化成功"),
        "test_initialize_already_initialized_returns_true": ("RAG-005", "初期化済みで再度initialize"),
        "test_initialize_double_checked_locking": ("RAG-006", "double-checked locking動作確認"),
        "test_get_enhanced_rag_search_success": ("RAG-007", "get_enhanced_rag_search成功"),
        "test_get_enhanced_rag_search_auto_initialize": ("RAG-008", "get_enhanced_rag_search自動初期化"),
        "test_is_initialized_false_initially": ("RAG-009", "is_initialized確認（未初期化）"),
        "test_is_initialized_true_after_init": ("RAG-010", "is_initialized確認（初期化済み）"),
        "test_health_check_success": ("RAG-011", "ヘルスチェック成功"),
        "test_get_global_rag_manager": ("RAG-012", "グローバルマネージャー取得"),
        "test_initialize_global_rag_system_success": ("RAG-013", "グローバルシステム初期化成功"),
        "test_module_level_get_enhanced_rag_search": ("RAG-014", "DI用get_enhanced_rag_search成功"),
        "test_initialize_rag_returns_false": ("RAG-E01", "EnhancedRAGSearch初期化失敗"),
        "test_initialize_exception": ("RAG-E02", "初期化中の例外"),
        "test_get_enhanced_rag_search_init_failure": ("RAG-E03", "get_enhanced_rag_search初期化失敗"),
        "test_health_check_uninitialized": ("RAG-E04", "ヘルスチェック未初期化"),
        "test_health_check_no_rag_search": ("RAG-E05", "ヘルスチェックRAG無し"),
        "test_health_check_exception": ("RAG-E06", "ヘルスチェック例外"),
        "test_initialize_global_rag_system_exception": ("RAG-E07", "グローバル初期化例外"),
        "test_error_log_no_sensitive_info": ("RAG-SEC-01", "エラーログに機密情報が含まれない"),
        "test_health_check_no_stack_trace_leak": ("RAG-SEC-02", "ヘルスチェックに内部エラー詳細が漏洩しない"),
        "test_singleton_thread_safety": ("RAG-SEC-03", "シングルトンのスレッドセーフ性"),
    }

    # テストメソッド名を抽出
    for method_name, (test_id, test_name) in name_map.items():
        if method_name in nodeid:
            return test_id, test_name

    return "UNKNOWN", nodeid.split("::")[-1]


def _generate_markdown_report(report_dir: str, normal_tests: list, error_tests: list,
                              security_tests: list, passed: int, failed: int, xfailed: int):
    """
Markdown形式のテストレポートを生成する。
    """
    total = passed + failed + xfailed
    pass_rate = (passed / total * 100) if total > 0 else 0
    effective_pass_rate = (passed / (passed + failed) * 100) if (passed + failed) > 0 else 0

    md_content = f"""# rag_manager.py テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| テスト対象 | `app/core/rag_manager.py` |
| テスト仕様 | `docs/testing/core/rag_manager_tests.md` |
| 実行時刻 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
| カバレッジ目標 | 75% |

## テスト結果統計

| カテゴリ | 総数 | 成功 | 失敗 | 予期された失敗 |
|------|------|------|------|----------|
| 正常系 | {len(normal_tests)} | {sum(1 for t in normal_tests if t['outcome']=='passed')} | {sum(1 for t in normal_tests if t['outcome']=='failed')} | {sum(1 for t in normal_tests if t['outcome']=='xfailed')} |
| 異常系 | {len(error_tests)} | {sum(1 for t in error_tests if t['outcome']=='passed')} | {sum(1 for t in error_tests if t['outcome']=='failed')} | {sum(1 for t in error_tests if t['outcome']=='xfailed')} |
| セキュリティ | {len(security_tests)} | {sum(1 for t in security_tests if t['outcome']=='passed')} | {sum(1 for t in security_tests if t['outcome']=='failed')} | {sum(1 for t in security_tests if t['outcome']=='xfailed')} |
| **合計** | **{total}** | **{passed}** | **{failed}** | **{xfailed}** |

## テスト成功率

- **実際の成功率**: {pass_rate:.1f}%
- **有効成功率** (予期された失敗を除外): {effective_pass_rate:.1f}%

---

## 正常系テスト詳細

| ID | テスト名 | 結果 | 実行時間 |
|----|---------|------|----------|
"""

    for test in normal_tests:
        md_content += f"| {test['id']} | {test['name']} | {test['status']} | {test['duration']} |\n"

    md_content += "\n## 異常系テスト詳細\n\n"
    md_content += "| ID | テスト名 | 結果 | 実行時間 |\n"
    md_content += "|----|---------|------|----------|\n"

    for test in error_tests:
        md_content += f"| {test['id']} | {test['name']} | {test['status']} | {test['duration']} |\n"

    md_content += "\n## セキュリティテスト詳細\n\n"
    md_content += "| ID | テスト名 | 結果 | 実行時間 |\n"
    md_content += "|----|---------|------|----------|\n"

    for test in security_tests:
        md_content += f"| {test['id']} | {test['name']} | {test['status']} | {test['duration']} |\n"

    md_content += "\n---\n\n## 結論\n\n"

    if failed == 0:
        md_content += "✅ **すべてのテストが成功しました！** RAGマネージャーモジュールは予分通りに動作しています。\n"
    else:
        md_content += f"⚠️ **{failed}件のテストが失敗しました。** 詳細を確認して修正してください。\n"

    if xfailed > 0:
        md_content += f"\n📌 **{xfailed}件のテストは予期された失敗です** (実装側の修正が必要)。\n"

    md_content += "\n---\n\n"
    md_content += f"*レポート生成時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"

    # ファイルに書き込み
    report_path = os.path.join(report_dir, "TestReport_rag_manager.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md_content)


def _generate_json_report(report_dir: str, normal_tests: list, error_tests: list,
                         security_tests: list, passed: int, failed: int, xfailed: int):
    """
JSON形式のテストレポートを生成する。
    """
    total = passed + failed + xfailed
    pass_rate = (passed / total * 100) if total > 0 else 0
    effective_pass_rate = (passed / (passed + failed) * 100) if (passed + failed) > 0 else 0

    json_data = {
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
                "total": len(normal_tests),
                "results": normal_tests
            },
            "error": {
                "total": len(error_tests),
                "results": error_tests
            },
            "security": {
                "total": len(security_tests),
                "results": security_tests
            }
        },
        "execution_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # ファイルに書き込み
    report_path = os.path.join(report_dir, "TestReport_rag_manager.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
