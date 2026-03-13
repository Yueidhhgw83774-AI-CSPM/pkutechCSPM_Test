# -*- coding: utf-8 -*-
"""
permission_checker モジュールテストのpytest fixtures。
"""

import os
import sys
import json
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path

import pytest
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
# Module Reset Fixture | 模块重置 Fixture
# =============================================================================

@pytest.fixture(autouse=True)
def reset_permission_checker_module():
    """テスト間でpermission_checkerモジュール状態をリセットする。

    モジュールキャッシュをクリアすることでテストの独立性を保証する。
    """
    yield
    # テスト後にモジュールキャッシュをクリア
    if "app.core.permission_checker" in sys.modules:
        del sys.modules["app.core.permission_checker"]


# =============================================================================
# Mock Fixtures | 模拟 Fixtures
# =============================================================================

@pytest.fixture
def mock_admin_client():
    """
AsyncOpenSearch管理者クライアントのモックを提供する。

    Returns:
        MagicMock: モックされたAsyncOpenSearchクライアント
    """
    client = MagicMock()
    client.transport = MagicMock()
    client.transport.perform_request = AsyncMock()
    return client


@pytest.fixture
def mock_user_info():
    """標準ユーザー情報のモックを提供する。

    Returns:
        Dict: ユーザー情報辞書
    """
    return {
        "backend_roles": ["user_role"],
        "opensearch_security_roles": ["reader"],
        "attributes": {"department": "engineering"}
    }


@pytest.fixture
def mock_role_permissions():
    """標準ロール権限のモックを提供する。

    Returns:
        Dict: ロール権限辞書
    """
    return {
        "index_permissions": [
            {
                "index_patterns": ["logs-*", "metrics-*"],
                "allowed_actions": ["read", "write"]
            }
        ],
        "cluster_permissions": ["cluster:monitor/*"]
    }


@pytest.fixture
def mock_admin_role_permissions():
    """管理者ロール権限のモックを提供する。

    Returns:
        Dict: 管理者ロール権限辞書
    """
    return {
        "index_permissions": [
            {
                "index_patterns": ["*"],
                "allowed_actions": ["*"]
            }
        ],
        "cluster_permissions": ["*"]
    }


# =============================================================================
# テストレポート生成
# =============================================================================

# グローバルテスト結果ストレージ
_test_results = []


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """テスト結果をキャプチャするフック。
    """
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call":
        # xfailマークされたテストをチェック
        is_xfail = hasattr(rep, "wasxfail") or (
            hasattr(item, '_evalxfail') and item._evalxfail.wasvalid() if hasattr(item, '_evalxfail') else False
        )

        result = {
            "nodeid": item.nodeid,
            "outcome": rep.outcome,
            "duration": rep.duration,
            "longrepr": str(rep.longrepr) if rep.longrepr else "",
            "is_xfail": is_xfail
        }
        _test_results.append(result)


def _get_readable_name(test_name: str) -> str:
    """テストメソッド名を読みやすい名前に変換する。

    Args:
        test_name: テストメソッド名

    Returns:
        str: 読みやすいテスト名
    """
    # テストIDから読みやすい名前へのマッピング
    name_map = {
        # 正常系テスト
        "test_init_with_admin_client": "管理者クライアント初期化",
        "test_get_user_info_success": "ユーザー情報取得成功",
        "test_get_user_roles_success": "ユーザーロール取得成功",
        "test_get_user_roles_deduplicate": "ロール統合（重複除去）",
        "test_get_role_permissions_success": "ロール権限取得成功",
        "test_index_access_granted": "インデックスアクセス権限許可",
        "test_index_access_denied": "インデックスアクセス権限拒否",
        "test_wildcard_index_pattern_match": "ワイルドカードインデックスパターンマッチ",
        "test_expand_read_action": "汎用アクション展開（read）",
        "test_expand_write_action": "汎用アクション展開（write）",
        "test_expand_wildcard_action": "汎用アクション展開（ワイルドカード）",
        "test_expand_crud_action": "複数アクション許可（crud）",
        "test_expand_manage_action": "汎用アクション展開（manage）",
        "test_expand_index_action": "汎用アクション展開（index）",
        "test_expand_delete_action": "汎用アクション展開（delete）",
        "test_expand_indices_all_action": "汎用アクション展開（indices_all）",
        "test_expand_create_index_action": "汎用アクション展開（create_index）",
        "test_fnmatch_wildcard_pattern": "fnmatchワイルドカードパターンマッチ",
        "test_no_match_action": "不一致アクション",
        "test_multiple_index_access_check": "複数インデックス一括チェック",
        "test_get_accessible_indices": "アクセス可能インデックス取得",
        "test_check_user_index_access_function": "便利関数チェック",

        # 異常系テスト
        "test_get_user_info_not_found": "不存在ユーザー情報取得でNone返却",
        "test_get_user_info_api_error": "ユーザー情報取得APIエラー",
        "test_get_roles_user_not_found": "不存在ユーザーのロール取得",
        "test_get_permissions_role_not_found": "不存在ロールの権限取得",
        "test_get_permissions_api_error": "ロール権限取得APIエラー",
        "test_role_check_error_skip_continue": "ロールチェックエラー時スキップ継続",
        "test_all_roles_check_failed": "全ロールチェック失敗",
        "test_user_roles_fetch_failed": "ユーザーロール取得失敗",
        "test_batch_check_partial_role_error": "バッチチェック中部分ロールエラー",
        "test_batch_check_user_error": "バッチチェック中ユーザー取得失敗",
        "test_accessible_indices_user_error": "アクセス可能インデックス取得ユーザーエラー",
        "test_accessible_indices_partial_role_error": "部分ロールエラー時スキップ継続",

        # セキュリティテスト
        "test_no_permission_user_denied": "権限なしユーザーアクセス拒否",
        "test_wildcard_pattern_safety": "ワイルドカードパターン安全性",
        "test_minimum_privilege_principle": "最小権限原則検証",
        "test_injection_attack_resistance": "インジェクション攻撃耐性",
        "test_role_escalation_prevention": "ロール昇格攻撃防止",
        "test_timing_attack_resistance": "タイミング攻撃耐性",
    }

    # テスト関数名を抽出
    if "::" in test_name:
        test_name = test_name.split("::")[-1]

    return name_map.get(test_name, test_name)


def pytest_sessionfinish(session, exitstatus):
    """すべてのテスト完了後に詳細レポートを生成する。
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

        # 結果をカウント
        if outcome == "passed":
            passed += 1
        elif outcome == "failed":
            failed += 1
        elif outcome == "xfailed":
            xfailed += 1

        # テストIDを解析して分類
        if "test_permission_checker.py" in nodeid:
            test_name = nodeid.split("::")[-1] if "::" in nodeid else nodeid
            readable_name = _get_readable_name(test_name)

            test_entry = {
                "name": readable_name,
                "status": "✅ 成功" if outcome == "passed" else ("❌ 失敗" if outcome == "failed" else "⚠️ 予期された失敗"),
                "duration": f"{duration*1000:.2f}ms"
            }

            # Categorize by test class
            # 按测试类分类
            if "Security" in nodeid:
                # Assign security test IDs
                # 分配安全测试 ID
                security_id_map = {
                    "test_no_permission_user_denied": "PERM-SEC-01",
                    "test_wildcard_pattern_safety": "PERM-SEC-02",
                    "test_minimum_privilege_principle": "PERM-SEC-05",
                    "test_injection_attack_resistance": "PERM-SEC-04",
                    "test_role_escalation_prevention": "PERM-SEC-03",
                    "test_timing_attack_resistance": "PERM-SEC-06",
                }
                test_entry["id"] = security_id_map.get(test_name, "PERM-SEC-XX")
                security_tests.append(test_entry)
            elif "Error" in nodeid:
                # Assign error test IDs
                # 分配异常系测试 ID
                error_id_map = {
                    "test_get_user_info_not_found": "PERM-E01",
                    "test_get_user_info_api_error": "PERM-E02",
                    "test_get_roles_user_not_found": "PERM-E03",
                    "test_get_permissions_role_not_found": "PERM-E04",
                    "test_get_permissions_api_error": "PERM-E05",
                    "test_role_check_error_skip_continue": "PERM-E06",
                    "test_all_roles_check_failed": "PERM-E07",
                    "test_user_roles_fetch_failed": "PERM-E09",
                    "test_batch_check_partial_role_error": "PERM-E08",
                    "test_batch_check_user_error": "PERM-E08-B",
                    "test_accessible_indices_user_error": "PERM-E10",
                    "test_accessible_indices_partial_role_error": "PERM-E10-B",
                }
                test_entry["id"] = error_id_map.get(test_name, "PERM-EXX")
                error_tests.append(test_entry)
            else:
                # Assign normal test IDs
                # 分配正常系测试 ID
                normal_id_map = {
                    "test_init_with_admin_client": "PERM-INIT",
                    "test_get_user_info_success": "PERM-001",
                    "test_get_user_roles_success": "PERM-002",
                    "test_get_user_roles_deduplicate": "PERM-012",
                    "test_get_role_permissions_success": "PERM-003",
                    "test_index_access_granted": "PERM-004",
                    "test_index_access_denied": "PERM-005",
                    "test_wildcard_index_pattern_match": "PERM-013",
                    "test_expand_read_action": "PERM-006",
                    "test_expand_write_action": "PERM-007",
                    "test_expand_wildcard_action": "PERM-008",
                    "test_expand_crud_action": "PERM-014",
                    "test_expand_manage_action": "PERM-006-B",
                    "test_expand_index_action": "PERM-006-C",
                    "test_expand_delete_action": "PERM-006-D",
                    "test_expand_indices_all_action": "PERM-006-E",
                    "test_expand_create_index_action": "PERM-006-F",
                    "test_fnmatch_wildcard_pattern": "PERM-006-G",
                    "test_no_match_action": "PERM-006-H",
                    "test_multiple_index_access_check": "PERM-009",
                    "test_get_accessible_indices": "PERM-010",
                    "test_check_user_index_access_function": "PERM-011",
                }
                test_entry["id"] = normal_id_map.get(test_name, "PERM-XXX")
                normal_tests.append(test_entry)

    # Calculate totals
    # 计算总数
    total = passed + failed + xfailed
    pass_rate = (passed / total * 100) if total > 0 else 0
    effective_pass_rate = (passed / (passed + failed) * 100) if (passed + failed) > 0 else 0

    # Markdownレポートを生成
    md_report = f"""# permission_checker.py テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| テスト対象 | `app/core/permission_checker.py` |
| テスト仕様 | `docs/testing/core/permission_checker_tests.md` |
| 実行時刻 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
| カバレッジ目標 | 85% |

## テスト結果統計

| カテゴリ | 総数 | 成功 | 失敗 | 予期された失敗 |
|------|------|------|------|----------|
| 正常系 | {len(normal_tests)} | {sum(1 for t in normal_tests if '✅' in t['status'])} | {sum(1 for t in normal_tests if '❌' in t['status'])} | {sum(1 for t in normal_tests if '⚠️' in t['status'])} |
| 異常系 | {len(error_tests)} | {sum(1 for t in error_tests if '✅' in t['status'])} | {sum(1 for t in error_tests if '❌' in t['status'])} | {sum(1 for t in error_tests if '⚠️' in t['status'])} |
| セキュリティ | {len(security_tests)} | {sum(1 for t in security_tests if '✅' in t['status'])} | {sum(1 for t in security_tests if '❌' in t['status'])} | {sum(1 for t in security_tests if '⚠️' in t['status'])} |
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
        md_report += f"| {test['id']} | {test['name']} | {test['status']} | {test['duration']} |\n"

    md_report += f"""
## 異常系テスト詳細

| ID | テスト名 | 結果 | 実行時間 |
|----|---------|------|----------|
"""

    for test in error_tests:
        md_report += f"| {test['id']} | {test['name']} | {test['status']} | {test['duration']} |\n"

    md_report += f"""
## セキュリティテスト詳細

| ID | テスト名 | 結果 | 実行時間 |
|----|---------|------|----------|
"""

    for test in security_tests:
        md_report += f"| {test['id']} | {test['name']} | {test['status']} | {test['duration']} |\n"

    md_report += f"""
---

## 結論

"""

    if failed == 0:
        md_report += "✅ **すべてのテストが成功** - permission_checker モジュールは正常に動作しています\n"
    else:
        md_report += f"⚠️ **{failed}件の失敗テストがあります** - 追加確認が必要です\n"

    if xfailed > 0:
        md_report += f"\n📝 **{xfailed}件の予期された失敗テスト** - これらは既知の制限または実装待ち機能です\n"

    md_report += f"""
---

*レポート生成時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    # Markdownレポートを書き込み
    md_path = os.path.join(report_dir, "TestReport_permission_checker.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_report)

    print(f"\n✅ Markdownレポートを生成しました: {md_path}")

    # JSONレポートを生成
    json_report = {
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

    # JSONレポートを書き込み
    json_path = os.path.join(report_dir, "TestReport_permission_checker.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_report, f, ensure_ascii=False, indent=2)

    print(f"✅ JSONレポートを生成しました: {json_path}\n")
