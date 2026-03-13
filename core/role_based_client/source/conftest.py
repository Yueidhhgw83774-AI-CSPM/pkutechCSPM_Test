# -*- coding: utf-8 -*-
"""
role_based_client モジュールテストのpytest fixtures。

このモジュールはrole_based_clientモジュールのテスト用共有フィクスチャを提供し、
環境設定、モックオブジェクト、テストデータを含みます。
"""

import os
import pprint
import sys
import pytest
from unittest.mock import patch, AsyncMock
from typing import Generator
from pathlib import Path
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

# .env ファイルから環境変数を読み込む
ENV_FILE = Path(__file__).parent.parent.parent / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)


# =============================================================================
# テスト環境設定
# =============================================================================

# テスト用環境変数（.envファイルから読み込み）
MOCK_SETTINGS_ENV = {
    # LLM APIキー - .envから読み込み
    "GPT5_1_CHAT_API_KEY": os.getenv("GPT5_1_CHAT_API_KEY", "test-key"),
    "GPT5_1_CODEX_API_KEY": os.getenv("GPT5_1_CODEX_API_KEY", "test-key"),
    "GPT5_2_API_KEY": os.getenv("GPT5_2_API_KEY", "test-key"),
    "GPT5_MINI_API_KEY": os.getenv("GPT5_MINI_API_KEY", "test-key"),
    "GPT5_NANO_API_KEY": os.getenv("GPT5_NANO_API_KEY", "test-key"),
    "CLAUDE_HAIKU_4_5_KEY": os.getenv("CLAUDE_HAIKU_4_5_KEY", "test-key"),
    "CLAUDE_SONNET_4_5_KEY": os.getenv("CLAUDE_SONNET_4_5_KEY", "test-key"),
    "GEMINI_API": os.getenv("GEMINI_API", "test-key"),
    "DOCKER_BASE_URL": os.getenv("DOCKER_BASE_URL", "http://localhost:11434"),
    "EMBEDDING_3_LARGE_API_KEY": os.getenv("EMBEDDING_3_LARGE_API_KEY", "test-embedding-key"),
    "MODEL_NAME": os.getenv("MODEL_NAME", "gpt-5.1-chat"),
    # OpenSearch Admin 認証情報 - .env から読み込み
    "OPENSEARCH_URL": os.getenv("OPENSEARCH_URL", "https://localhost:9200"),
    "OPENSEARCH_USER": os.getenv("OPENSEARCH_USER", "admin"),
    "OPENSEARCH_PASSWORD": os.getenv("OPENSEARCH_PASSWORD", "admin"),
    "OPENSEARCH_CA_CERTS_PATH": os.getenv("OPENSEARCH_CA_CERTS_PATH", ""),
    # Role-Based Credentials - テスト用固定値（.envファイルで未定義）
    "CSPM_DASHBOARD_READ_USER": os.getenv("CSPM_DASHBOARD_READ_USER", "cspm-read-user"),
    "CSPM_DASHBOARD_READ_PASSWORD": os.getenv("CSPM_DASHBOARD_READ_PASSWORD", "cspm-read-pass"),
    "RAG_SEARCH_READ_USER": os.getenv("RAG_SEARCH_READ_USER", "rag-read-user"),
    "RAG_SEARCH_READ_PASSWORD": os.getenv("RAG_SEARCH_READ_PASSWORD", "rag-read-pass"),
    "DOCUMENT_WRITE_USER": os.getenv("DOCUMENT_WRITE_USER", "doc-write-user"),
    "DOCUMENT_WRITE_PASSWORD": os.getenv("DOCUMENT_WRITE_PASSWORD", "doc-write-pass"),
    "CSPM_JOB_EXEC_USER": os.getenv("CSPM_JOB_EXEC_USER", "cspm-job-user"),
    "CSPM_JOB_EXEC_PASSWORD": os.getenv("CSPM_JOB_EXEC_PASSWORD", "cspm-job-pass"),
}

# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def reset_role_based_client_module():
    """テストごとにモジュールのグローバル変数をリセットする。

    role_based_client.pyのグローバル変数（_role_based_client_instance）は
    モジュールレベルで管理されているため、テスト間の独立性を保つために
    sys.modulesからapp.coreモジュールを削除して再読み込みを強制します。
    """
    yield
    # テスト後にモジュールキャッシュをクリア
    modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
    for mod in modules_to_remove:
        del sys.modules[mod]

@pytest.fixture
def mock_settings_env():
    """テスト用環境変数設定＋モジュールリセット
    """
    with patch.dict("os.environ", MOCK_SETTINGS_ENV, clear=False):
        # モジュールをリセット
        modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
        for mod in modules_to_remove:
            del sys.modules[mod]
        yield


@pytest.fixture
def mock_async_opensearch():
    """
AsyncOpenSearchモック（外部接続防止）

    全テストで実際のOpenSearch接続を防止するために使用。
    pingはデフォルトでTrueを返す。
    """
    with patch("app.core.role_based_client.AsyncOpenSearch") as mock_cls:
        mock_instance = AsyncMock()
        mock_instance.ping = AsyncMock(return_value=True)
        mock_cls.return_value = mock_instance
        yield mock_cls, mock_instance


# =============================================================================
# レポート設定
# =============================================================================

@pytest.fixture(scope="session")
def report_dir() -> str:
    """レポート出力ディレクトリパスを提供する。
    """
    report_path = Path(__file__).parent.parent / "reports"
    os.makedirs(report_path, exist_ok=True)
    return str(report_path)


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
        is_xfail = hasattr(rep, "wasxfail") or (hasattr(item, '_evalxfail') and item._evalxfail.wasvalid())

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
    """
    import json
    from datetime import datetime

    report_dir = Path(__file__).parent.parent / "reports"
    os.makedirs(report_dir, exist_ok=True)

    # テスト結果を解析
    normal_tests = []
    error_tests = []
    security_tests = []

    passed = 0
    failed = 0
    xfailed = 0

    # テストIDから名前へのマッピング
    test_name_map = {
        # 正常系テスト
        "test_roles_constants_defined": ("RBC-001", "ロール定数が正しく定義されている"),
        "test_role_env_mapping_complete": ("RBC-002", "ROLE_ENV_MAPPINGが全ロールを含む"),
        "test_get_client_for_valid_role": ("RBC-003", "有効なロールでクライアント取得成功"),
        "test_cached_client_returned": ("RBC-004", "初期化済みロールはキャッシュ返却"),
        "test_aws_opensearch_port_443": ("RBC-005", "AWS OpenSearch→ポート443"),
        "test_standard_opensearch_port_9200": ("RBC-006", "標準OpenSearch→ポート9200"),
        "test_url_specified_port": ("RBC-007", "URL指定ポート→そのポート使用"),
        "test_aws_opensearch_ca_certs_none": ("RBC-008", "AWS OpenSearch→ca_certs=None"),
        "test_ca_certs_path_configured": ("RBC-009", "CA_CERTS_PATH設定あり→指定パス使用"),
        "test_no_ca_certs_path_ssl_verification_disabled": ("RBC-010", "CA_CERTS_PATH未設定→SSL検証無効"),
        "test_retry_success_on_second_attempt": ("RBC-011", "リトライ成功（1回目失敗、2回目成功）"),
        "test_get_available_roles": ("RBC-012", "使用可能ロール一覧取得"),
        "test_health_check_success": ("RBC-013", "ヘルスチェック成功"),
        "test_singleton_instance": ("RBC-014", "シングルトンインスタンス取得"),
        "test_convenience_function": ("RBC-015", "便利関数でクライアント取得"),
        "test_localhost_hostname_verification_disabled": ("RBC-016", "localhostでホスト名検証無効"),
        "test_non_localhost_hostname_verification_enabled": ("RBC-017", "non-localhostでホスト名検証有効"),
        "test_ca_certs_path_file_not_exists": ("RBC-018", "CA_CERTS_PATH設定あるがファイル不存在→SSL検証無効化"),
        
        # 異常系テスト
        "test_unknown_role_returns_none": ("RBC-E01", "未知のロール名→None"),
        "test_missing_username": ("RBC-E02", "認証情報未設定（USERNAME）"),
        "test_missing_password": ("RBC-E03", "認証情報未設定（PASSWORD）"),
        "test_opensearch_url_empty": ("RBC-E04", "OPENSEARCH_URL未設定"),
        "test_opensearch_url_invalid_format": ("RBC-E05", "OPENSEARCH_URL不正形式"),
        "test_ping_all_failures": ("RBC-E06", "ping全失敗（max_retries回）"),
        "test_connection_exception_all_retries": ("RBC-E07", "接続例外（max_retries回）"),
        "test_skip_on_previous_error": ("RBC-E08", "過去の初期化エラー→スキップ"),
        "test_health_check_unknown_role": ("RBC-E09", "ヘルスチェック: 未知のロール"),
        "test_health_check_initialization_error": ("RBC-E10", "ヘルスチェック: 初期化エラー状態"),
        "test_health_check_initialization_error_after_ping_failures": ("RBC-E11", "ヘルスチェック: ping全失敗後の初期化エラー状態"),
        "test_health_check_ping_failed": ("RBC-E12", "ヘルスチェック: ping失敗"),
        "test_health_check_exception": ("RBC-E13", "ヘルスチェック: 例外発生"),
        
        # セキュリティテスト
        "test_password_not_in_logs": ("RBC-SEC-01", "パスワードがログに出力されない"),
        "test_ssl_always_enabled": ("RBC-SEC-02", "SSL常時有効"),
        "test_credential_error_message_only_contains_env_var_names": ("RBC-SEC-03", "認証情報エラーメッセージに環境変数名のみ含む"),
        "test_health_check_error_no_password": ("RBC-SEC-04", "ヘルスチェックエラーにパスワードが含まれない"),
        "test_traceback_no_credentials": ("RBC-SEC-05", "traceback出力に認証情報が含まれない"),
        "test_role_credentials_isolation": ("RBC-SEC-06", "各ロールの認証情報が分離されている"),
    }

    for result in _test_results:
        nodeid = result["nodeid"]
        outcome = result["outcome"]
        duration = result["duration"]
        is_xfail = result.get("is_xfail", False)

        # 予期された失敗テストの結果の上書き | Override outcome for xfail tests
        if is_xfail:
            outcome = "xfailed"

        # ノードIDからテスト関数名を抽出する | nodeidからテスト関数名を抽出する
        test_func_name = nodeid.split("::")[-1] if "::" in nodeid else ""
        
        # テストカテゴリを決定し、ID/名称を取得する | 確定テストカテゴリおよびID/名称を取得する
        if test_func_name in test_name_map:
            test_id, test_name = test_name_map[test_func_name]
            
            test_entry = {
                "id": test_id,
                "name": test_name,
                "status": outcome,
                "duration": duration
            }
            
            # テストを分类する | 分类测试
            if test_id.startswith("RBC-SEC"):
                security_tests.append(test_entry)
            elif test_id.startswith("RBC-E"):
                error_tests.append(test_entry)
            else:
                normal_tests.append(test_entry)

        # アウトカムの統計 | 統計結果
        if outcome == "passed":
            passed += 1
        elif outcome == "failed":
            failed += 1
        elif outcome == "xfailed":
            xfailed += 1

    total = len(_test_results)

    # 詳細なMarkdownレポートを生成する | 詳細なMarkdownレポートを生成する
    report_md = f"""# role_based_client.py 测试报告

## 测试概要

| 项目 | 值 |
|------|-----|
| 测试对象 | `app/core/role_based_client.py` |
| 测试规格 | `docs/testing/core/role_based_client_tests.md` |
| 执行时间 | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} |
| 覆盖率目标 | 75% |

## 测试结果统计

| 类别 | 总数 | 通过 | 失败 | 预期失败 |
|------|------|------|------|---------|
| 正常系 | {len(normal_tests)} | {sum(1 for t in normal_tests if t['status']=='passed')} | {sum(1 for t in normal_tests if t['status']=='failed')} | {sum(1 for t in normal_tests if t['status']=='xfailed')} |
| 异常系 | {len(error_tests)} | {sum(1 for t in error_tests if t['status']=='passed')} | {sum(1 for t in error_tests if t['status']=='failed')} | {sum(1 for t in error_tests if t['status']=='xfailed')} |
| 安全测试 | {len(security_tests)} | {sum(1 for t in security_tests if t['status']=='passed')} | {sum(1 for t in security_tests if t['status']=='failed')} | {sum(1 for t in security_tests if t['status']=='xfailed')} |
| **合计** | **{total}** | **{passed}** | **{failed}** | **{xfailed}** |

## 测试通过率

- **实际通过率**: {(passed/total*100) if total>0 else 0:.1f}%
- **有效通过率** (排除预期失败): {(passed/(total-xfailed)*100) if (total-xfailed)>0 else 0:.1f}%

---

## 正常系测试详情

| ID | 测试名称 | 结果 | 执行时间 |
|----|---------|------|---------|
"""

    for t in normal_tests:
        status_icon = "✅ 通过" if t['status'] == "passed" else "❌ 失败"
        report_md += f"| {t['id']} | {t['name']} | {status_icon} | {t['duration']*1000:.2f}ms |\n"

    report_md += """
---

## 异常系测试详情

| ID | 测试名称 | 结果 | 执行时间 |
|----|---------|------|---------|
"""

    for t in error_tests:
        status_icon = "✅ 通过" if t['status'] == "passed" else "❌ 失败"
        report_md += f"| {t['id']} | {t['name']} | {status_icon} | {t['duration']*1000:.2f}ms |\n"

    report_md += """
---

## 安全测试详情

| ID | 测试名称 | 结果 | 执行时间 |
|----|---------|------|---------|
"""

    for t in security_tests:
        if t['status'] == "passed":
            status_icon = "✅ 通过"
        elif t['status'] == "xfailed":
            status_icon = "⚠️ 预期失败"
        else:
            status_icon = "❌ 失败"
        report_md += f"| {t['id']} | {t['name']} | {status_icon} | {t['duration']*1000:.2f}ms |\n"

    # 予期される失敗がある場合は説明を追加する |
    if xfailed > 0:
        report_md += """
---

## 预期失败测试说明

| ID | 问题描述 | 代码位置 | 建议修复 |
|----|---------|---------|---------|
| RBC-SEC-04 | str(e)をそのままエラーに格納するため漏洩リスク | role_based_client.py:268 | エラーメッセージのサニタイズを実装 |

"""

    report_md += """
---

## 结论

"""

    if failed == 0:
        report_md += "✅ **所有非预期失败的测试均已通过。**\n\n"
    else:
        report_md += f"❌ **有 {failed} 个测试未通过。**\n\n"

    if xfailed > 0:
        report_md += f"⚠️ **有 {xfailed} 个预期失败的测试（已知问题）。**\n"

    report_md += f"""
---

*レポート生成時刻: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

    # Markdownレポートを書き込み
    md_path = os.path.join(report_dir, "TestReport_role_based_client.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    # JSONレポートを生成
    json_report = {
        "metadata": {
            "test_target": "app/core/role_based_client.py",
            "test_spec": "docs/testing/core/role_based_client_tests.md",
            "execution_time": datetime.now().isoformat(),
            "coverage_target": "75%"
        },
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "xfailed": xfailed,
            "pass_rate": (passed/total*100) if total>0 else 0,
            "effective_pass_rate": (passed/(total-xfailed)*100) if (total-xfailed)>0 else 0
        },
        "results": {
            "normal": normal_tests,
            "error": error_tests,
            "security": security_tests
        }
    }

    json_path = os.path.join(report_dir, "TestReport_role_based_client.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_report, f, ensure_ascii=False, indent=2)

    print(f"\n✅ テストレポートを生成しました:")
    print(f"  - {md_path}")
    print(f"  - {json_path}")
