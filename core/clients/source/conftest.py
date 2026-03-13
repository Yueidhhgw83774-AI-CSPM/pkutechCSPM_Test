# -*- coding: utf-8 -*-
"""
clients モジュールテスト用 pytest 設定ファイル。
テスト対象: app/core/clients.py
テスト仕様: clients_tests.md
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
    # 優先度2: ディレク トリツリーを遡って .env ファイルを検索する
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
    """テスト結果コレクター - テストレポート生成用。"""

    def __init__(self):
        self.results = {
            "normal": [],    # 正常系テスト
            "error": [],     # 異常系テスト
            "security": []   # セキュリティテスト
        }
        self.start_time = datetime.now()

    def add_result(self, nodeid: str, outcome: str, duration: float):
        """
        テスト結果を追加する。

        分類ルール:
        - "Security" または "_sec_" を含む → security
        - "Error" または "_e0" を含む → error
        - その他 → normal
        """
        category = "normal"

        if "Security" in nodeid or "_sec_" in nodeid.lower():
            category = "security"
        elif "Error" in nodeid or "_e0" in nodeid:
            category = "error"

        result = {
            "nodeid": nodeid,
            "status": outcome,
            "duration": duration
        }

        self.results[category].append(result)


# グローバルコレクターインスタンス
collector = TestResultCollector()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """各テストの実行結果をキャプチャする。"""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        nodeid = item.nodeid
        test_outcome = report.outcome  # passed, failed, skipped
        duration = report.duration

        collector.add_result(nodeid, test_outcome, duration)


def pytest_sessionfinish(session, exitstatus):
    """
    テストセッション終了時にレポートを生成する。

    2種類の形式を生成:
    1. Markdown レポート (人間可読)
    2. JSON レポート (機械可読)
    """
    results = collector.results

    # 統計データを計算する
    normal_tests = results["normal"]
    error_tests = results["error"]
    security_tests = results["security"]

    total = len(normal_tests) + len(error_tests) + len(security_tests)
    passed = sum(1 for t in normal_tests + error_tests + security_tests if t["status"] == "passed")
    failed = sum(1 for t in normal_tests + error_tests + security_tests if t["status"] == "failed")
    xfailed = sum(1 for t in normal_tests + error_tests + security_tests if t["status"] == "xfailed")

    pass_rate = (passed / total * 100) if total > 0 else 0
    effective_pass_rate = (passed / (total - xfailed) * 100) if (total - xfailed) > 0 else 0

    # レポートディレクトリを動的に計算する
    report_dir = Path(__file__).parent.parent / "reports"
    report_dir.mkdir(exist_ok=True)

    md_report_path = report_dir / "TestReport_clients.md"
    json_report_path = report_dir / "TestReport_clients.json"

    # Markdown レポート内容
    md_content = f"""# clients.py テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| テスト対象 | `app/core/clients.py` |
| テスト仕様 | `clients_tests.md` |
| 実行日時 | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} |
| カバレッジ目標 | 90% |

## テスト結果集計

| カテゴリ | 総数 | 成功 | 失敗 | 予期失敗 |
|---------|------|------|------|----------|
| 正常系 | {len(normal_tests)} | {sum(1 for t in normal_tests if t['status']=='passed')} | {sum(1 for t in normal_tests if t['status']=='failed')} | {sum(1 for t in normal_tests if t['status']=='xfailed')} |
| 異常系 | {len(error_tests)} | {sum(1 for t in error_tests if t['status']=='passed')} | {sum(1 for t in error_tests if t['status']=='failed')} | {sum(1 for t in error_tests if t['status']=='xfailed')} |
| セキュリティ | {len(security_tests)} | {sum(1 for t in security_tests if t['status']=='passed')} | {sum(1 for t in security_tests if t['status']=='failed')} | {sum(1 for t in security_tests if t['status']=='xfailed')} |
| **合計** | **{total}** | **{passed}** | **{failed}** | **{xfailed}** |

## 合格率

- **実際の合格率**: {pass_rate:.1f}%
- **有効合格率** (予期失敗を除く): {effective_pass_rate:.1f}%

---

## 正常系テスト詳細

| テストID | テスト名 | 結果 | 実行時間 |
|--------|---------|------|----------|
"""

    # 正常系テスト詳細を追加する
    for idx, test in enumerate(normal_tests, 1):
        test_name = _get_readable_name(test["nodeid"])
        status_icon = "✅" if test["status"] == "passed" else "❌" if test["status"] == "failed" else "⚠️"
        md_content += f"| CLT-{idx:03d} | {test_name} | {status_icon} | {test['duration']:.3f}s |\n"

    md_content += "\n---\n\n## 異常系テスト詳細\n\n"
    md_content += "| テストID | テスト名 | 結果 | 実行時間 |\n"
    md_content += "|--------|---------|------|----------|\n"

    # 異常系テスト詳細を追加する
    for idx, test in enumerate(error_tests, 1):
        test_name = _get_readable_name(test["nodeid"])
        status_icon = "✅" if test["status"] == "passed" else "❌" if test["status"] == "failed" else "⚠️"
        md_content += f"| CLT-E{idx:02d} | {test_name} | {status_icon} | {test['duration']:.3f}s |\n"

    md_content += "\n---\n\n## セキュリティテスト詳細\n\n"
    md_content += "| テストID | テスト名 | 結果 | 実行時間 |\n"
    md_content += "|--------|---------|------|----------|\n"

    # セキュリティテスト詳細を追加する
    for idx, test in enumerate(security_tests, 1):
        test_name = _get_readable_name(test["nodeid"])
        status_icon = "✅" if test["status"] == "passed" else "❌" if test["status"] == "failed" else "⚠️"
        md_content += f"| CLT-SEC-{idx:02d} | {test_name} | {status_icon} | {test['duration']:.3f}s |\n"

    # 結論を追加する
    if failed == 0:
        conclusion = "✅ **すべてのテストが成功!** clients.py モジュールテストが完全に成功し、コード品質が優秀です。"
    else:
        conclusion = f"❌ **{failed} 件の失敗テストがあります**。関連する問題を確認して修正してください。"

    md_content += f"\n---\n\n## 結論\n\n{conclusion}\n\n---\n\n*レポート生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"

    # Markdown レポートを書き込む
    with open(md_report_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    # JSON レポート内容
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
                "passed": sum(1 for t in normal_tests if t["status"] == "passed"),
                "failed": sum(1 for t in normal_tests if t["status"] == "failed"),
                "results": normal_tests
            },
            "error": {
                "total": len(error_tests),
                "passed": sum(1 for t in error_tests if t["status"] == "passed"),
                "failed": sum(1 for t in error_tests if t["status"] == "failed"),
                "results": error_tests
            },
            "security": {
                "total": len(security_tests),
                "passed": sum(1 for t in security_tests if t["status"] == "passed"),
                "failed": sum(1 for t in security_tests if t["status"] == "failed"),
                "results": security_tests
            }
        },
        "execution_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # JSON レポートを書き込む
    with open(json_report_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ テストレポートを生成しました:")
    print(f"  JSON : {md_report_path}")
    print(f"  Markdown: {json_report_path}\n")


def _get_readable_name(test_name: str) -> str:
    """テストメソッド名を読みやすい日本語名に変換する。"""

    name_map = {
        # 正常系テスト (CLT-001 ~ CLT-014)
        "test_extract_aws_region_from_url_standard": "標準AWSドメインからリージョン抽出",
        "test_extract_aws_region_from_url_serverless": "Serverlessドメインからリージョン抽出",
        "test_extract_aws_region_from_url_fallback": "無効URL時のデフォルトリージョンフォールバック",
        "test_initialize_opensearch_success": "OpenSearchクライアント初期化成功",
        "test_initialize_opensearch_with_basic_auth": "Basic認証OpenSearch初期化",
        "test_initialize_opensearch_aws_service": "AWSサービスOpenSearch初期化",
        "test_initialize_opensearch_retry_success": "接続リトライ後成功",
        "test_get_opensearch_client_success": "初期化済みクライアント取得",
        "test_get_opensearch_client_with_auth_success": "カスタム認証クライアント作成",
        "test_initialize_embedding_function_success": "Embedding関数初期化成功",
        "test_initialize_embedding_openai_model": "OpenAI Embeddingモデル初期化",
        "test_initialize_embedding_with_dimensions": "次元指定Embedding初期化",
        "test_get_embedding_function_success": "初期化済みEmbedding関数取得",
        "test_module_import": "モジュールインポートテスト",

        # 異常系テスト (CLT-E01 ~ CLT-E16)
        "test_initialize_opensearch_e01_missing_url": "OPENSEARCH_URL未設定",
        "test_initialize_opensearch_e02_invalid_url": "無効なOPENSEARCH_URL形式",
        "test_initialize_opensearch_e03_missing_credentials": "認証情報未設定",
        "test_initialize_opensearch_e04_connection_timeout": "接続タイムアウト失敗",
        "test_initialize_opensearch_e05_max_retries_exceeded": "最大リトライ回数超過",
        "test_initialize_opensearch_e06_ping_failure": "Ping操作失敗",
        "test_initialize_opensearch_e07_ssl_cert_error": "SSL証明書検証エラー",
        "test_get_opensearch_client_e08_not_initialized": "クライアント未初期化時の取得",
        "test_get_opensearch_client_e09_init_error_state": "初期化エラー状態での取得",
        "test_get_opensearch_client_with_auth_e10_invalid_format": "無効な認証形式",
        "test_get_opensearch_client_with_auth_e11_missing_url": "URL設定未存在",
        "test_get_opensearch_client_with_auth_e12_ping_failure": "カスタム認証Ping失敗",
        "test_initialize_embedding_e13_missing_api_key": "Embedding APIキー未設定",
        "test_initialize_embedding_e14_missing_model_name": "Embeddingモデル名未設定",
        "test_get_embedding_function_e15_not_initialized": "Embedding未初期化時の取得",
        "test_get_embedding_function_e16_init_error_state": "Embeddingエラー状態での取得",

        # セキュリティテスト (CLT-SEC-01 ~ CLT-SEC-06)
        "test_sec_01_credentials_not_logged": "認証情報がログに記録されないこと",
        "test_sec_02_api_key_not_exposed": "APIキーがエラーメッセージに露出しないこと",
        "test_sec_03_ssl_verification_enabled": "SSL証明書検証が強制有効化されること",
        "test_sec_04_connection_timeout_reasonable": "接続タイムアウト設定が適切であること",
        "test_sec_05_error_messages_sanitized": "エラーメッセージから機密情報が除去されること",
        "test_sec_06_auth_header_not_exposed": "認証ヘッダー情報が露出しないこと",
    }

    # nodeid からテストメソッド名を抽出する
    if "::" in test_name:
        test_name = test_name.split("::")[-1]

    return name_map.get(test_name, test_name)


# Pytest fixtures
@pytest.fixture
def mock_settings():
    """settings 設定オブジェクトをモックする。"""
    from unittest.mock import MagicMock
    settings = MagicMock()
    settings.OPENSEARCH_URL = "https://test.us-east-1.es.amazonaws.com:443"
    settings.OPENSEARCH_USER = "admin"
    settings.OPENSEARCH_PASSWORD = "admin123"
    settings.OPENSEARCH_CA_CERTS_PATH = None
    settings.EMBEDDING_API_KEY = "sk-test123"
    settings.EMBEDDING_MODEL_NAME = "text-embedding-3-large"
    settings.EMBEDDING_MODEL_BASE_URL = "http://litellm:4000"
    return settings


@pytest.fixture
def reset_global_state():
    """グローバル状態をリセットする。"""
    import app.core.clients as clients_module

    # グローバル変数をリセットする
    clients_module.os_client = None
    clients_module.OS_CLIENT_INIT_ERROR = None
    clients_module.OS_CLIENT_INITIALIZED = False
    clients_module.embedding_function = None
    clients_module.EMBEDDING_INIT_ERROR = None
    clients_module.EMBEDDING_INITIALIZED = False

    yield

    # テスト後にクリーンアップする
    clients_module.os_client = None
    clients_module.OS_CLIENT_INIT_ERROR = None
    clients_module.OS_CLIENT_INITIALIZED = False
    clients_module.embedding_function = None
    clients_module.EMBEDDING_INIT_ERROR = None
    clients_module.EMBEDDING_INITIALIZED = False
