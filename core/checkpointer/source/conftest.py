# -*- coding: utf-8 -*-
"""
checkpointer モジュールテスト用 pytest 設定ファイル。
テスト対象: app/core/checkpointer.py
テスト仕様: checkpointer_tests.md
"""

import os
import re
import sys

# インポート前に必須の環境変数を設定する（設定検証エラーを防ぐ）
os.environ.setdefault("GPT5_1_CHAT_API_KEY", "sk-h6zKpdRQoYKEcj6vhTHMPg")
os.environ.setdefault("GPT5_1_CODEX_API_KEY", "sk-h6zKpdRQoYKEcj6vhTHMPg")
os.environ.setdefault("GPT5_2_API_KEY", "sk-h6zKpdRQoYKEcj6vhTHMPg")
os.environ.setdefault("GPT5_MINI_API_KEY", "sk-EAt8QXSUBIdDJnXV4ROHrA")
os.environ.setdefault("GPT5_NANO_API_KEY", "sk-KbU6B0qXqUc2bru0rQ49vg")
os.environ.setdefault("CLAUDE_HAIKU_4_5_KEY", "sk-AZ2Y4zi06RkkiQ9IVnrw-g")
os.environ.setdefault("CLAUDE_SONNET_4_5_KEY", "sk-ddGysRLuQbS68TPNdBnZDQ")
os.environ.setdefault("GEMINI_API", "sk-6voS6352n0aLHWV3k_jFew")
os.environ.setdefault("DOCKER_BASE_URL", "http://litellm:4000")
os.environ.setdefault("EMBEDDING_3_LARGE_API_KEY", "sk-CVqmdwNwI9y0nHSVeDwwpA")
os.environ.setdefault("OPENSEARCH_URL", "https://opensearch-node:9200")
os.environ.setdefault("LANGGRAPH_STORAGE_TYPE", "memory")
os.environ.setdefault("LANGGRAPH_POSTGRES_URL", "")

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
def reset_checkpointer_module():
    """テストごとに checkpointer モジュールのグローバル状態をリセットする。"""
    # テスト前にモジュールキャッシュをクリアする
    modules_to_remove = [
        key for key in list(sys.modules.keys())
        if key.startswith("app.core.checkpointer")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]

    yield

    # テスト後にグローバル変数をリセットする
    try:
        import app.core.checkpointer as ckp_module
        ckp_module._checkpointer = None
        ckp_module._checkpointer_initialized = False
        ckp_module._connection_pool = None
        ckp_module._current_storage_mode = "unknown"
    except (ImportError, AttributeError):
        pass

    # 再度モジュールキャッシュをクリアする
    modules_to_remove = [
        key for key in list(sys.modules.keys())
        if key.startswith("app.core.checkpointer")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


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
    module_dir = current_file.parent.parent  # source/ の親 = checkpointer/
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
        if "test_checkpointer.py" in nodeid:
            # セキュリティテストの分岐
            if "TestCheckpointerSecurity" in nodeid or "Security" in nodeid:
                if "postgres_url_not_logged" in nodeid:
                    test_id, test_name = "CKP-SEC-01", "PostgreSQL URLがログに出力されないこと"
                elif "credentials_not_exposed" in nodeid:
                    test_id, test_name = "CKP-SEC-02", "認証情報が漏洩しないこと"
                elif "connection_pool_max_size" in nodeid:
                    test_id, test_name = "CKP-SEC-03", "接続プールサイズ制限"
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
                if "postgres_url_not_set" in nodeid:
                    test_id, test_name = "CKP-E01", "PostgreSQL URL未設定時のフォールバック"
                elif "psycopg_not_installed" in nodeid:
                    test_id, test_name = "CKP-E02", "psycopg未インストール時のフォールバック"
                elif "postgres_connection_error" in nodeid:
                    test_id, test_name = "CKP-E03", "PostgreSQL接続エラー時のフォールバック"
                elif "close_pool_error" in nodeid:
                    test_id, test_name = "CKP-E04", "接続プール閉じるエラー処理"
                elif "setup_fails" in nodeid:
                    test_id, test_name = "CKP-E05", "setup失敗時のフォールバック"
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
                if "import_checkpointer_module" in nodeid:
                    test_id, test_name = "CKP-INIT", "モジュールインポート成功"
                elif "initial_storage_mode" in nodeid:
                    test_id, test_name = "CKP-001", "初期ストレージモード確認"
                elif "memory_saver_init_with_memory_type" in nodeid:
                    test_id, test_name = "CKP-002", "MemorySaver初期化(memory指定)"
                elif "memory_saver_fallback_unset" in nodeid:
                    test_id, test_name = "CKP-003", "MemorySaverフォールバック(未設定)"
                elif "cached_checkpointer_returned" in nodeid:
                    test_id, test_name = "CKP-004", "キャッシュされたCheckpointer返却"
                elif "postgres_checkpointer_init" in nodeid:
                    test_id, test_name = "CKP-005", "PostgreSQL Checkpointer初期化"
                elif "sync_checkpointer_memory" in nodeid:
                    test_id, test_name = "CKP-006", "同期Checkpointer取得(memory)"
                elif "sync_checkpointer_postgres_warning" in nodeid:
                    test_id, test_name = "CKP-007", "同期Checkpointer警告(postgres)"
                elif "close_checkpointer_memory" in nodeid:
                    test_id, test_name = "CKP-008", "Checkpointer閉じる(memory)"
                elif "reset_checkpointer_clears_cache" in nodeid:
                    test_id, test_name = "CKP-009", "キャッシュリセット"
                elif "opensearch_fallback_to_memory" in nodeid:
                    test_id, test_name = "CKP-010", "OpenSearchフォールバック"
                elif "unknown_storage_fallback" in nodeid:
                    test_id, test_name = "CKP-011", "未知ストレージフォールバック"
                elif "close_with_postgres_pool" in nodeid:
                    test_id, test_name = "CKP-012", "PostgreSQL接続プール閉じる"
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

    report_md = f"""# checkpointer.py テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| テスト対象 | `app/core/checkpointer.py` |
| テスト仕様 | `checkpointer_tests.md` |
| 実行日時 | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} |
| カバレッジ目標 | 75% |

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
    md_path = os.path.join(report_dir, "TestReport_checkpointer.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    # ─── JSON レポート生成（★ 必須出力物） ───
    json_report = {
        "metadata": {
            "test_target":    "app/core/checkpointer.py",
            "test_spec":      "checkpointer_tests.md",
            "execution_time": datetime.now().isoformat(),
            "coverage_target": "75%",
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
    json_path = os.path.join(report_dir, "TestReport_checkpointer.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_report, f, ensure_ascii=False, indent=2)

    print(f"\n✅ テストレポートを生成しました:")
    print(f"  JSON : {json_path}")
    print(f"  Markdown: {md_path}")


