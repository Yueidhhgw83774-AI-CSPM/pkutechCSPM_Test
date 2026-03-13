# -*- coding: utf-8 -*-
"""
categories モジュールテスト用 pytest 設定ファイル。
テスト対象: app/core/categories.py
テスト仕様: categories_tests.md
"""

import os
import re
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

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


# ─── モジュールリセット Fixture ──────────────────────────────────────────
@pytest.fixture(autouse=True)
def reset_categories_module():
    """テストごとにモジュールのグローバル状態をリセットする。"""
    # テスト前にモジュールキャッシュをクリアする
    modules_to_remove = [
        key for key in list(sys.modules.keys())
        if key.startswith("app.core.categories")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]

    yield

    # テスト後にクリーンアップする
    try:
        import app.core.categories as cat_module
        cat_module._categories_data = []
        cat_module._categories_for_prompt_str = ""
    except ImportError:
        pass

    # 再度モジュールキャッシュをクリアする
    modules_to_remove = [
        key for key in list(sys.modules.keys())
        if key.startswith("app.core.categories")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


# ─── テストデータ Fixtures ───────────────────────────────────────────────
@pytest.fixture
def valid_categories_json(tmp_path):
    """テスト用の有効な categories JSON ファイルを作成する。"""
    categories = [
        {
            "name": "Identity and Access Management",
            "description": "IAM related controls"
        },
        {
            "name": "Data Security",
            "description": "Data protection controls"
        },
        {
            "name": "Network Security",
            "description": "Network related controls"
        }
    ]
    json_file = tmp_path / "categories.json"
    json_file.write_text(json.dumps(categories), encoding="utf-8")
    return str(json_file)


# ─── テスト結果収集 ──────────────────────────────────────────────────────
_test_results = []  # テスト結果を格納するグローバルリスト

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
    # ★★★ 重要: レポートパスの動的計算（絶対にハードコードしない） ★★★
    from pathlib import Path
    current_file = Path(__file__).resolve()
    module_dir = current_file.parent.parent  # source/ の親 = categories/
    report_dir = module_dir / "reports"
    os.makedirs(report_dir, exist_ok=True)

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

        # xfail テストのステータスを上書きする
        if is_xfail:
            outcome = "xfailed"

        # nodeid パターンでテストを分類する
        if "test_categories.py" in nodeid:
            # セキュリティテストの分岐
            if "TestCategoriesSecurity" in nodeid or "Security" in nodeid:
                if "path_traversal" in nodeid:
                    test_id, test_name = "CAT-SEC-01", "パストラバーサル攻撃への対応"
                elif "large_categories" in nodeid or "dos_resistance" in nodeid:
                    test_id, test_name = "CAT-SEC-02", "大量データによるDoS耐性"
                elif "malicious_json" in nodeid:
                    test_id, test_name = "CAT-SEC-03", "悪意のあるJSONコンテンツの安全処理"
                else:
                    continue
                security_tests.append({
                    "id": test_id,
                    "name": test_name,
                    "status": outcome,
                    "duration": duration
                })
            # 異常系テストの分岐
            elif "Error" in nodeid or "Errors" in nodeid:
                if "file_not_found" in nodeid:
                    test_id, test_name = "CAT-E01", "ファイル未検出時のフォールバック"
                elif "invalid_json" in nodeid:
                    test_id, test_name = "CAT-E02", "無効なJSON構文時のフォールバック"
                elif "unexpected_exception" in nodeid:
                    test_id, test_name = "CAT-E03", "予期せぬ例外時のフォールバック"
                elif "permission_error" in nodeid:
                    test_id, test_name = "CAT-E04", "権限エラー時のフォールバック"
                else:
                    continue
                error_tests.append({
                    "id": test_id,
                    "name": test_name,
                    "status": outcome,
                    "duration": duration
                })
            # 正常系テストの分岐
            else:
                if "import_categories_module" in nodeid:
                    test_id, test_name = "CAT-001", "モジュールインポート成功"
                elif "load_valid_categories" in nodeid:
                    test_id, test_name = "CAT-002", "有効なJSONファイルからの読み込み"
                elif "prompt_string_format" in nodeid:
                    test_id, test_name = "CAT-003", "プロンプト文字列のフォーマット検証"
                elif "auto_load_when_not_loaded" in nodeid:
                    test_id, test_name = "CAT-004", "未ロード時の自動ロード"
                elif "cached_data_returned" in nodeid:
                    test_id, test_name = "CAT-005", "キャッシュデータの返却"
                elif "empty_categories_list" in nodeid:
                    test_id, test_name = "CAT-006", "空リスト時のフォールバック"
                elif "category_without_description" in nodeid:
                    test_id, test_name = "CAT-007", "説明なしカテゴリの処理"
                elif "category_without_name_skipped" in nodeid:
                    test_id, test_name = "CAT-008", "名前なしカテゴリのスキップ"
                else:
                    continue
                normal_tests.append({
                    "id": test_id,
                    "name": test_name,
                    "status": outcome,
                    "duration": duration
                })

        # 集計
        if outcome == "passed":
            passed += 1
        elif outcome == "failed":
            failed += 1
        elif outcome == "xfailed":
            xfailed += 1

    total = len(_test_results)

    # ─── Markdown レポート生成（全文日本語） ───
    def _icon(status: str) -> str:
        return "✅ 成功" if status == "passed" else ("⚠️ 予期失敗" if status == "xfailed" else "❌ 失敗")

    rows_normal   = "\n".join(f"| {t['id']} | {t['name']} | {_icon(t['status'])} | {t['duration']*1000:.2f}ms |" for t in sorted(normal_tests,   key=lambda x: x["id"]))
    rows_error    = "\n".join(f"| {t['id']} | {t['name']} | {_icon(t['status'])} | {t['duration']*1000:.2f}ms |" for t in sorted(error_tests,    key=lambda x: x["id"]))
    rows_security = "\n".join(f"| {t['id']} | {t['name']} | {_icon(t['status'])} | {t['duration']*1000:.2f}ms |" for t in sorted(security_tests, key=lambda x: x["id"]))

    conclusion = "✅ **予期しない失敗はありません。すべてのテストが正常に完了しました。**" if failed == 0 else f"❌ **{failed} 件のテストが失敗しました。**"

    report_md = f"""# categories.py テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| テスト対象 | `app/core/categories.py` |
| テスト仕様 | `categories_tests.md` |
| 実行日時 | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} |
| カバレッジ目標 | 60% |

## テスト結果集計

| カテゴリ | 総数 | 成功 | 失敗 | 予期失敗 |
|---------|------|------|------|----------|
| 正常系 | {len(normal_tests)} | {sum(1 for t in normal_tests if t['status']=='passed')} | {sum(1 for t in normal_tests if t['status']=='failed')} | {sum(1 for t in normal_tests if t['status']=='xfailed')} |
| 異常系 | {len(error_tests)} | {sum(1 for t in error_tests if t['status']=='passed')} | {sum(1 for t in error_tests if t['status']=='failed')} | {sum(1 for t in error_tests if t['status']=='xfailed')} |
| セキュリティ | {len(security_tests)} | {sum(1 for t in security_tests if t['status']=='passed')} | {sum(1 for t in security_tests if t['status']=='failed')} | {sum(1 for t in security_tests if t['status']=='xfailed')} |
| **合計** | **{total}** | **{passed}** | **{failed}** | **{xfailed}** |

## 合格率

- **実際の合格率**: {round(passed/total*100, 1) if total > 0 else 0.0:.1f}%
- **有効合格率**（予期失敗を除く）: {round(passed/(total-xfailed)*100, 1) if (total-xfailed) > 0 else 0.0:.1f}%

---

## 正常系テスト詳細

| ID | テスト名 | 結果 | 実行時間 |
|----|---------|------|----------|
{rows_normal}

---

## 異常系テスト詳細

| ID | テスト名 | 結果 | 実行時間 |
|----|---------|------|----------|
{rows_error}

---

## セキュリティテスト詳細

| ID | テスト名 | 結果 | 実行時間 |
|----|---------|------|----------|
{rows_security}

---

## 結論

{conclusion}
{"" if xfailed == 0 else f"⚠️ **{xfailed} 件の予期失敗テストがあります（既知の問題）。**"}

---
*レポート生成日時: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

    # Markdown レポートを書き込む
    md_path = os.path.join(report_dir, "TestReport_categories.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report_md)
"""

    # ─── JSON レポート生成（★ 必須出力物） ───
    json_report = {
        "metadata": {
            "test_target":    "app/core/categories.py",
            "test_spec":      "categories_tests.md",
            "execution_time": datetime.now().isoformat(),
            "coverage_target": "60%",
        },
        "summary": {
            "total":     total,
            "passed":    passed,
            "failed":    failed,
            "xfailed":   xfailed,
            "pass_rate": round(passed / total * 100, 1) if total > 0 else 0.0,
        },
        "results": {
            "normal":   normal_tests,
            "error":    error_tests,
            "security": security_tests,
        },
    }
    json_path = os.path.join(report_dir, "TestReport_categories.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_report, f, ensure_ascii=False, indent=2)

    print(f"\n✅ テストレポートを生成しました:")
    print(f"  JSON : {json_path}")
    print(f"  Markdown: {md_path}")
"""


