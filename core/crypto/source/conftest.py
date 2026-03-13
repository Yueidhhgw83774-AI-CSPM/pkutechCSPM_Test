# -*- coding: utf-8 -*-
"""
crypto モジュールテスト用 pytest fixtures。

このモジュールは crypto モジュールテスト用の共有 fixtures を提供します。
環境設定、モックオブジェクト、テストデータを含む。
"""

import os
import re
import sys
import base64
import json
import hashlib
import pytest
from pathlib import Path
from unittest.mock import patch
from typing import Generator

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
# 共有シークレット Fixtures | Shared Secret Fixtures
# =============================================================================

@pytest.fixture
def test_shared_secret() -> bytes:
    """
    テスト用の共有シークレットキーを提供する。
    """
    return b"test_shared_secret_for_hmac"


@pytest.fixture
def test_shared_secret_32() -> bytes:
    """
    AES操作用の32バイトのテスト共有シークレットキーを提供する。
    """
    return b"test_shared_secret_key_123456789"


@pytest.fixture
def mock_env_shared_secret():
    """
    環境変数 SHARED_SECRET をモックする。
    """
    with patch.dict(os.environ, {"SHARED_SECRET": "env_secret_key"}):
        yield "env_secret_key"


@pytest.fixture
def mock_secret_file(tmp_path):
    """
    モックのシークレットファイルを作成する。
    """
    secret_file = tmp_path / "shared_secret"
    secret_file.write_bytes(b"file_secret_key_12345")
    return str(secret_file)


# =============================================================================
# 暗号化ペイロード Fixtures | Encrypted Payload Fixtures
# =============================================================================

@pytest.fixture
def encrypted_payload(test_shared_secret_32):
    """
    IV付きテスト暗号化ペイロードを提供する。
    """
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend

    # テスト用平文 JSON
    plaintext = '{"session_id": "test_123", "prompt": "テストメッセージ"}'

    # キーを生成する
    key = hashlib.sha256(test_shared_secret_32).digest()

    # IVを生成する
    iv = os.urandom(16)

    # パディングを追加する
    padder = padding.PKCS7(128).padder()
    padded = padder.update(plaintext.encode('utf-8')) + padder.finalize()

    # 暗号化する
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()

    return {
        "encrypted_data": base64.b64encode(ciphertext).decode(),
        "iv": base64.b64encode(iv).decode(),
        "expected": json.loads(plaintext)
    }


# =============================================================================
# レポート設定 | Report Configuration
# =============================================================================

@pytest.fixture(scope="session")
def report_dir() -> str:
    """
    レポート出力ディレクトリパスを提供する。
    """
    report_path = Path(__file__).parent.parent / "reports"
    os.makedirs(report_path, exist_ok=True)
    return str(report_path)


# =============================================================================
# テストレポート生成 | Test Report Generation
# =============================================================================

# グローバルテスト結果ストレージ
_test_results = []

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    テスト結果をキャプチャするフック。
    """
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call":
        # xfailマークがついているか確認する
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
    """すべてのテスト完了後に詳細レポートを生成する pytest フック。"""
    import json
    from datetime import datetime

    # ★★★ 重要: レポートパスの動的計算（絶対にハードコードしない） ★★★
    report_dir = Path(__file__).parent.parent / "reports"
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

        # テスト ID と名前を抽出する
        if "test_crypto_" in nodeid:
            # テスト ID を解析する
            if "test_crypto_sec_" in nodeid:
                # セキュリティテスト
                test_type = "security"
                if "sec_01" in nodeid:
                    test_id = "CRYPTO-SEC-01"
                    test_name = "HMACタイミング攻撃防御"
                elif "sec_02" in nodeid:
                    test_id = "CRYPTO-SEC-02"
                    test_name = "タイムスタンプ改ざん検出"
                elif "sec_03" in nodeid:
                    test_id = "CRYPTO-SEC-03"
                    test_name = "パディングオラクル攻撃防御"
                elif "sec_04" in nodeid:
                    test_id = "CRYPTO-SEC-04"
                    test_name = "デフォルトキー警告出力"
                elif "sec_05" in nodeid:
                    test_id = "CRYPTO-SEC-05"
                    test_name = "HMAC単一ビット差異検出"
                elif "sec_06" in nodeid:
                    test_id = "CRYPTO-SEC-06"
                    test_name = "エラーメッセージから内部詳細を漏洩しないこと"
                else:
                    continue
                security_tests.append({
                    "id": test_id,
                    "name": test_name,
                    "status": outcome,
                    "duration": duration
                })
            elif "test_crypto_e" in nodeid:
                # 異常系テスト
                test_type = "error"
                if "_e01_" in nodeid:
                    test_id, test_name = "CRYPTO-E01", "空キーファイルエラー"
                elif "_e02_" in nodeid:
                    test_id, test_name = "CRYPTO-E02", "無効なHMAC形式"
                elif "_e03_" in nodeid:
                    test_id, test_name = "CRYPTO-E03", "タイムスタンプ期限切れ"
                elif "_e04_" in nodeid:
                    test_id, test_name = "CRYPTO-E04", "改ざんされたハッシュ値"
                elif "_e05_" in nodeid:
                    test_id, test_name = "CRYPTO-E05", "無効なIVサイズ"
                elif "_e06_" in nodeid:
                    test_id, test_name = "CRYPTO-E06", "無効なPKCS7パディング"
                elif "_e07_" in nodeid:
                    test_id, test_name = "CRYPTO-E07", "空の暗号化入力"
                elif "_e08_" in nodeid:
                    test_id, test_name = "CRYPTO-E08", "非UTF-8データ"
                elif "_e09_" in nodeid:
                    test_id, test_name = "CRYPTO-E09", "無効なJSON"
                elif "_e10_" in nodeid:
                    test_id, test_name = "CRYPTO-E10", "無効なBase64データ"
                elif "_e11_" in nodeid:
                    test_id, test_name = "CRYPTO-E11", "None認証ヘッダー"
                elif "_e12_" in nodeid:
                    test_id, test_name = "CRYPTO-E12", "パディング長より短いデータ"
                elif "_e13_" in nodeid:
                    test_id, test_name = "CRYPTO-E13", "パディングバイト不一致"
                else:
                    continue
                error_tests.append({
                    "id": test_id,
                    "name": test_name,
                    "status": outcome,
                    "duration": duration
                })
            elif "_001_" in nodeid:
                normal_tests.append({"id": "CRYPTO-001", "name": "環境変数から共有キー取得", "status": outcome, "duration": duration})
            elif "_002_" in nodeid:
                normal_tests.append({"id": "CRYPTO-002", "name": "ファイルから共有キー取得", "status": outcome, "duration": duration})
            elif "_003_" in nodeid:
                normal_tests.append({"id": "CRYPTO-003", "name": "デフォルトキーへのフォールバック", "status": outcome, "duration": duration})
            elif "_004_" in nodeid:
                normal_tests.append({"id": "CRYPTO-004", "name": "空白文字の保持", "status": outcome, "duration": duration})
            elif "_005_" in nodeid:
                normal_tests.append({"id": "CRYPTO-005", "name": "有効なHMAC認証ハッシュ検証", "status": outcome, "duration": duration})
            elif "_006_" in nodeid:
                normal_tests.append({"id": "CRYPTO-006", "name": "有効なペイロードのAES-CBC復号化", "status": outcome, "duration": duration})
            elif "_007_" in nodeid:
                normal_tests.append({"id": "CRYPTO-007", "name": "復号化後のJSON解析", "status": outcome, "duration": duration})
            elif "_008_" in nodeid:
                normal_tests.append({"id": "CRYPTO-008", "name": "Base64からの認証情報復号化", "status": outcome, "duration": duration})
            elif "_009_" in nodeid:
                normal_tests.append({"id": "CRYPTO-009", "name": "既知データの復号化テスト", "status": outcome, "duration": duration})
            elif "_010_" in nodeid:
                normal_tests.append({"id": "CRYPTO-010", "name": "時間ドリフト許容検証", "status": outcome, "duration": duration})

        # 結果を集計する
        if outcome == "passed":
            passed += 1
        elif outcome == "failed":
            failed += 1
        elif outcome == "xfailed":
            xfailed += 1

    total = len(_test_results)

    # Generate detailed Markdown report
    # 詳細なMarkdownレポートを生成する
    report_md = f"""# crypto.py 测试报告

## 测试概要

| 项目 | 值 |
|------|-----|
| 测试对象 | `app/core/crypto.py` |
| 测试规格 | `crypto_tests.md` |
| 执行时间 | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} |
| 覆盖率目标 | 90% |

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

## 異常系テスト詳細

| ID | テスト名称 | 結果 | 実行時間 |
|----|---------|------|---------|
"""

    for t in error_tests:
        status_icon = "✅ 成功" if t['status'] == "passed" else "❌ 失敗"
        report_md += f"| {t['id']} | {t['name']} | {status_icon} | {t['duration']*1000:.2f}ms |\n"

    report_md += """
---

## セキュリティテスト詳細

| ID | テスト名称 | 結果 | 実行時間 |
|----|---------|------|---------|
"""

    for t in security_tests:
        if t['status'] == "passed":
            status_icon = "✅ 成功"
        elif t['status'] == "xfailed":
            status_icon = "⚠️ 予期される失敗"
        else:
            status_icon = "❌ 失敗"
        report_md += f"| {t['id']} | {t['name']} | {status_icon} | {t['duration']*1000:.2f}ms |\n"

    report_md += """
---

## 予期される失敗テスト説明

| ID | 問題説明 | コード位置 | 推奨修正 |
|----|---------|---------|---------|
| CRYPTO-SEC-01 | ==比較を使用、タイミング攻撃リスクあり | crypto.py:98 | hmac.compare_digest()を使用 |
| CRYPTO-SEC-03 | エラーメッセージがパディング詳細を漏洩 | crypto.py:165 | 統一エラーメッセージを返す |
| CRYPTO-SEC-06 | 異なるエラーが異なるメッセージを返す | crypto.py:165 | すべての復号化エラーメッセージを統一 |

---

## 結論

"""

    if failed == 0:
        report_md += "✅ **予期される失敗以外のすべてのテストが成功しました。**\n\n"
    else:
        report_md += f"❌ **{failed} 件のテストが失敗しました。**\n\n"

    if xfailed > 0:
        report_md += f"⚠️ **{xfailed} 件の予期される失敗テスト（既知のセキュリティ問題）があります。**\n"

    report_md += f"""
---

*レポート生成時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

    # Markdown レポートの書き込み
    md_path = os.path.join(report_dir, "TestReport_crypto.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    # JSON レポートの生成
    json_report = {
        "metadata": {
            "test_target": "app/core/crypto.py",
            "test_spec": "crypto_tests.md",
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

    json_path = os.path.join(report_dir, "TestReport_crypto.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_report, f, ensure_ascii=False, indent=2)

    print(f"\n✅ テストレポートが生成されました:")
    print(f"  - {md_path}")
    print(f"  - {json_path}")

