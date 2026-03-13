# -*- coding: utf-8 -*-
"""
auth_utils モジュールテスト用 pytest 設定ファイル。

テスト対象: app/core/auth_utils.py
テスト仕様: auth_utils_tests.md
"""

import os
import re
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

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


# =============================================================================
# モジュールリセット Fixture
# =============================================================================

@pytest.fixture(autouse=True)
def reset_auth_utils_module():
    """テストごとに auth_utils モジュールの状態をリセットする。"""
    yield
    # テスト後にモジュールキャッシュをクリアする
    if "app.core.auth_utils" in sys.modules:
        del sys.modules["app.core.auth_utils"]


# =============================================================================
# モック Request Fixtures
# =============================================================================

@pytest.fixture
def mock_request_with_auth():
    """認証ヘッダー付きのモックリクエストを提供する。"""
    mock_headers = MagicMock()
    mock_headers.get = lambda key: (
        "Basic dXNlcjpwYXNz" if key.lower() == "authorization" else None
    )

    mock_request = MagicMock()
    mock_request.headers = mock_headers
    return mock_request


@pytest.fixture
def mock_request_without_auth():
    """認証ヘッダーなしのモックリクエストを提供する。"""
    mock_headers = MagicMock()
    mock_headers.get = lambda key: None

    mock_request = MagicMock()
    mock_request.headers = mock_headers
    return mock_request


# =============================================================================
# テスト結果収集
# =============================================================================

# テスト結果を格納するグローバルリスト
_test_results = []


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """テスト結果をキャプチャする pytest フック。"""
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call":
        # xfail マーカーの確認

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
    """全テスト完了後にレポートを生成する pytest フック。"""
    # ★ 重要: 現在のファイル位置から相対的に reports/ ディレクトリを計算する
    # パス構造:
    #   TestReport/
    # └── core/                 ← 分類ategorization
    #         └── auth_utils/       ← モジュール名
    #             ├── source/
    #             │   └── conftest.py  ← このファイル
    # └── reports/      ← レポート出力先
    from pathlib import Path
    current_file = Path(__file__).resolve()
    module_dir = current_file.parent.parent  # source/ の親 = auth_utils/
    report_dir = module_dir / "reports"
    os.makedirs(report_dir, exist_ok=True)

    # テスト結果を解析する
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

        # xfail テストの結果を上書きする
        if is_xfail:
            outcome = "xfailed"

        # テスト ID を解析し、分類する
        if "test_auth_utils.py" in nodeid:
            # セキュリティテスト
            if "TestAuthUtilsSecurity" in nodeid:
                if "auth_header_not_fully_logged" in nodeid:
                    test_id, test_name = "AUTIL-SEC-01", "認証ヘッダーがログに完全出力されない"
                elif "error_message_does_not_expose_credentials" in nodeid:
                    test_id, test_name = "AUTIL-SEC-02", "エラーメッセージに認証情報が含まれない"
                elif "x_auth_hash_header_masked" in nodeid:
                    test_id, test_name = "AUTIL-SEC-03", "x-auth-hashヘッダーがマスクされる"
                elif "empty_header_value_filtering_safe" in nodeid:
                    test_id, test_name = "AUTIL-SEC-04", "空ヘッダー値のフィルタリングが安全"
                elif "short_auth_header_filtering" in nodeid:
                    test_id, test_name = "AUTIL-SEC-05", "短い認証ヘッダー値のフィルタリング"
                else:
                    continue
                security_tests.append({
                    "id": test_id,
                    "name": test_name,
                    "status": outcome,
                    "duration": duration
                })
            # 異常系テスト
            elif "Error" in nodeid:
                if "test_no_auth_header" in nodeid:
                    test_id, test_name = "AUTIL-E01", "認証ヘッダーなしでHTTPException"
                elif "test_invalid_auth_format" in nodeid:
                    test_id, test_name = "AUTIL-E02", "無効な認証形式でHTTPException"
                elif "test_empty_auth_header" in nodeid:
                    test_id, test_name = "AUTIL-E03", "空の認証ヘッダーでHTTPException"
                elif "test_request_without_auth_header" in nodeid:
                    test_id, test_name = "AUTIL-E06", "Requestからの取得失敗でHTTPException"
                elif "test_lowercase_basic_prefix" in nodeid:
                    test_id, test_name = "AUTIL-E07", "小文字basicプレフィックスでHTTPException"
                elif "test_no_endpoint_auth" in nodeid:
                    test_id, test_name = "AUTIL-E04", "エンドポイント認証なしでHTTPException"
                elif "test_empty_endpoint_auth" in nodeid:
                    test_id, test_name = "AUTIL-E05", "空のエンドポイント認証でHTTPException"
                else:
                    continue
                error_tests.append({
                    "id": test_id,
                    "name": test_name,
                    "status": outcome,
                    "duration": duration
                })
            # 正常系テスト
            else:
                if "test_import_module" in nodeid:
                    test_id, test_name = "AUTIL-INIT", "模块导入"
                elif "test_extract_basic_token_with_space" in nodeid:
                    test_id, test_name = "AUTIL-001", "Basic令牌提取（有空格）"
                elif "test_extract_basic_token_without_space" in nodeid:
                    test_id, test_name = "AUTIL-002", "Basic令牌提取（无空格）"
                elif "test_extract_shared_hmac_token" in nodeid:
                    test_id, test_name = "AUTIL-003", "SHARED-HMAC头接受"
                elif "test_extract_from_request_lowercase" in nodeid:
                    test_id, test_name = "AUTIL-004", "从Request获取（小写）"
                elif "test_extract_from_request_uppercase" in nodeid:
                    test_id, test_name = "AUTIL-005", "从Request获取（大写）"
                elif "test_validate_with_opensearch_auth" in nodeid:
                    test_id, test_name = "AUTIL-006", "验证（有OpenSearch）"
                elif "test_validate_without_opensearch_auth" in nodeid:
                    test_id, test_name = "AUTIL-007", "验证（无OpenSearch）"
                elif "test_validate_opensearch_auth_default_none" in nodeid:
                    test_id, test_name = "AUTIL-007-B", "opensearch_auth默认None"
                elif "test_log_with_both_auth" in nodeid:
                    test_id, test_name = "AUTIL-008", "デバッグログ出力（両認証あり）"
                elif "test_log_with_header_filtering" in nodeid:
                    test_id, test_name = "AUTIL-009", "デバッグログ出力（ヘッダーフィルタリング）"
                elif "test_log_without_auth" in nodeid:
                    test_id, test_name = "AUTIL-010", "デバッグログ出力（認証なし）"
                elif "test_log_without_request_headers" in nodeid:
                    test_id, test_name = "AUTIL-010-B", "デバッグログ出力（リクエストヘッダーなし）"
                elif "test_log_without_debug_level" in nodeid:
                    test_id, test_name = "AUTIL-011", "デバッグログ出力（DEBUG無効）"
                else:
                    continue
                normal_tests.append({
                    "id": test_id,
                    "name": test_name,
                    "status": outcome,
                    "duration": duration
                })

        # 結果を集計する
        if outcome == "passed":
            passed += 1
        elif outcome == "failed":
            failed += 1
        elif outcome == "xfailed":
            xfailed += 1

    total = len(_test_results)

    # 詳細な Markdown レポートを生成する
    report_md = f"""# auth_utils.py テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| テスト対象 | `app/core/auth_utils.py` |
| テスト仕様 | `auth_utils_tests.md` |
| 実行日時 | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} |
| カバレッジ目標 | 90% |

## テスト結果集計

| カテゴリ | 総数 | 成功 | 失敗 | 予期失敗 |
|---------|------|------|------|---------|
| 正常系 | {len(normal_tests)} | {sum(1 for t in normal_tests if t['status']=='passed')} | {sum(1 for t in normal_tests if t['status']=='failed')} | {sum(1 for t in normal_tests if t['status']=='xfailed')} |
| 異常系 | {len(error_tests)} | {sum(1 for t in error_tests if t['status']=='passed')} | {sum(1 for t in error_tests if t['status']=='failed')} | {sum(1 for t in error_tests if t['status']=='xfailed')} |
| セキュリティ | {len(security_tests)} | {sum(1 for t in security_tests if t['status']=='passed')} | {sum(1 for t in security_tests if t['status']=='failed')} | {sum(1 for t in security_tests if t['status']=='xfailed')} |
| **合計** | **{total}** | **{passed}** | **{failed}** | **{xfailed}** |

## 合格率

- **実際の合格率**: {(passed/total*100) if total>0 else 0:.1f}%
- **有効合格率**（予期失敗を除く）: {(passed/(total-xfailed)*100) if (total-xfailed)>0 else 0:.1f}%

---

## 正常系テスト詳細

| ID | テスト名 | 結果 | 実行時間 |
|----|---------|------|---------|
"""

    for t in sorted(normal_tests, key=lambda x: x['id']):
        status_icon = "✅ 成功" if t['status'] == "passed" else ("⚠️ 予期失敗" if t['status'] == "xfailed" else "❌ 失敗")
        report_md += f"| {t['id']} | {t['name']} | {status_icon} | {t['duration']*1000:.2f}ms |\n"

    report_md += """
---

## 異常系テスト詳細

| ID | テスト名 | 結果 | 実行時間 |
|----|---------|------|---------|
"""

    for t in sorted(error_tests, key=lambda x: x['id']):
        status_icon = "✅ 成功" if t['status'] == "passed" else ("⚠️ 予期失敗" if t['status'] == "xfailed" else "❌ 失敗")
        report_md += f"| {t['id']} | {t['name']} | {status_icon} | {t['duration']*1000:.2f}ms |\n"

    report_md += """
---

## セキュリティテスト詳細

| ID | テスト名 | 結果 | 実行時間 |
|----|---------|------|---------|
"""

    for t in sorted(security_tests, key=lambda x: x['id']):
        status_icon = "✅ 成功" if t['status'] == "passed" else ("⚠️ 予期失敗" if t['status'] == "xfailed" else "❌ 失敗")
        report_md += f"| {t['id']} | {t['name']} | {status_icon} | {t['duration']*1000:.2f}ms |\n"

    report_md += """
---

## 結論

"""

    if failed == 0:
        report_md += "✅ **予期失敗以外のすべてのテストが成功しました。**\n\n"
    else:
        report_md += f"❌ **{failed} 件のテストが失敗しました。**\n\n"

    if xfailed > 0:
        report_md += f"⚠️ **{xfailed} 件の予期失敗テストがあります（既知の問題）。**\n"

    report_md += f"""
---

*レポート生成日時: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

    # Markdown レポートを書き込む
    md_path = os.path.join(report_dir, "TestReport_auth_utils.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    # JSON レポートを生成する
    json_report = {
        "metadata": {
            "test_target": "app/core/auth_utils.py",
            "test_spec": "auth_utils_tests.md",
            "execution_time": datetime.now().isoformat(),
            "coverage_target": "90%"
        },
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "xfailed": xfailed,
            "pass_rate": (passed/total*100) if total>0 else 0
        },
        "results": {
            "normal": normal_tests,
            "error": error_tests,
            "security": security_tests
        }
    }

    json_path = os.path.join(report_dir, "TestReport_auth_utils.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_report, f, ensure_ascii=False, indent=2)

    print(f"\n✅ テストレポートを生成しました:")
    print(f"  - {md_path}")
    print(f"  - {json_path}")

