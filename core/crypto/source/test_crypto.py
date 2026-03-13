# -*- coding: utf-8 -*-
"""
crypto.py のテスト。
テスト対象: app/core/crypto.py
テスト仕様: crypto_tests.md
カバレッジ目標: 90%
このテストファイルは crypto_tests.md 仕様書に従って記述されており、
正常系テスト、異常系テスト、セキュリティテストの3カテゴリを含む。
テスト命名規則:
- 正常系: test_crypto_XXX_<description>  (CRYPTO-001 ~ CRYPTO-010)
- 異常系: test_crypto_eXX_<description>  (CRYPTO-E01 ~ CRYPTO-E13)
- セキュリティテスト: test_crypto_sec_XX_<description>  (CRYPTO-SEC-01 ~ CRYPTO-SEC-06)
"""
import os
import re
import sys
import json
import time
import base64
import hashlib
import hmac
import inspect
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import patch
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
# Import the module under test
from app.core.crypto import (
    _get_shared_secret,
    verify_auth_hash,
    decrypt_opensearch_dashboard_payload,
    decrypt_credentials_field,
    test_decryption_with_known_data,
)
# =============================================================================
# Test Result Collector
# =============================================================================
class TestResultCollector:
    """テスト結果を収集してレポートを生成するユーティリティクラス"""
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    def start(self):
        """テスト計測を開始する"""
        self.start_time = datetime.now()
    def end(self):
        """テスト計測を終了する"""
        self.end_time = datetime.now()
    def add_result(self, test_id: str, test_name: str, category: str, 
                   passed: bool, message: str = "", expected_fail: bool = False, 
                   duration: float = 0.0):
        """テスト結果を追加する"""
        self.results.append({
            "test_id": test_id,
            "test_name": test_name,
            "category": category,
            "passed": passed,
            "message": message,
            "expected_fail": expected_fail,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        })
    def generate_markdown_report(self, output_path: str):
        """Markdownフォーマットのレポートを生成する"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = sum(1 for r in self.results if not r["passed"] and not r["expected_fail"])
        xfail = sum(1 for r in self.results if r["expected_fail"])
        normal_tests = [r for r in self.results if r["category"] == "normal"]
        error_tests = [r for r in self.results if r["category"] == "error"]
        security_tests = [r for r in self.results if r["category"] == "security"]
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
        else:
            duration = sum(r["duration"] for r in self.results)
        report = f"""# crypto.py テストレポート
## テスト概要
| 項目 | 値 |
|------|-----|
| テスト対象 | app/core/crypto.py |
| テスト仕様 | crypto_tests.md |
| 実行日時 | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} |
| 総実行時間 | {duration:.2f} 秒 |
| カバレッジ目標 | 90% |
## テスト結果集計
| カテゴリ | 総数 | 成功 | 失敗 | 予期失敗 |
|------|------|------|------|---------|
| 正常系 | {len(normal_tests)} | {sum(1 for r in normal_tests if r["passed"])} | {sum(1 for r in normal_tests if not r["passed"] and not r["expected_fail"])} | {sum(1 for r in normal_tests if r["expected_fail"])} |
| 異常系 | {len(error_tests)} | {sum(1 for r in error_tests if r["passed"])} | {sum(1 for r in error_tests if not r["passed"] and not r["expected_fail"])} | {sum(1 for r in error_tests if r["expected_fail"])} |
| セキュリティ | {len(security_tests)} | {sum(1 for r in security_tests if r["passed"])} | {sum(1 for r in security_tests if not r["passed"] and not r["expected_fail"])} | {sum(1 for r in security_tests if r["expected_fail"])} |
| **合計** | **{total}** | **{passed}** | **{failed}** | **{xfail}** |
## 合格率
- **実際の合格率**: {(passed / total * 100) if total > 0 else 0:.1f}%
- **有効合格率**（予期失敗を除く）: {(passed / (total - xfail) * 100) if (total - xfail) > 0 else 0:.1f}%
---
## 正常系テスト詳細
| ID | テスト名 | 結果 | 実行時間 | 備考 |
|----|---------|------|---------|------|
"""
        for r in normal_tests:
            status = "✅ 成功" if r["passed"] else ("⚠️ 予期失敗" if r["expected_fail"] else "❌ 失敗")
            report += f"| {r['test_id']} | {r['test_name']} | {status} | {r['duration']*1000:.2f}ms | {r['message']} |\n"
        report += """
---
## 異常系テスト詳細
| ID | テスト名 | 結果 | 実行時間 | 備考 |
|----|---------|------|---------|------|
"""
        for r in error_tests:
            status = "✅ 成功" if r["passed"] else ("⚠️ 予期失敗" if r["expected_fail"] else "❌ 失敗")
            report += f"| {r['test_id']} | {r['test_name']} | {status} | {r['duration']*1000:.2f}ms | {r['message']} |\n"
        report += """
---
## セキュリティテスト詳細
| ID | テスト名 | 結果 | 実行時間 | 備考 |
|----|---------|------|---------|------|
"""
        for r in security_tests:
            status = "✅ 成功" if r["passed"] else ("⚠️ 予期失敗" if r["expected_fail"] else "❌ 失敗")
            report += f"| {r['test_id']} | {r['test_name']} | {status} | {r['duration']*1000:.2f}ms | {r['message']} |\n"
        report += """
---
## 予期失敗テスト説明
| ID | 問題説明 | 修正案 |
|----|---------|-------------|
| CRYPTO-SEC-01 | verify_auth_hash で == 比較を使用、タイミング攻撃リスクあり | hmac.compare_digest() を使用する |
| CRYPTO-SEC-03 | 復号エラー時に str(e) が内部詳細を漏洩 | 統一した汎用エラーメッセージを返す |
| CRYPTO-SEC-06 | 異なる種類の復号エラーに異なるメッセージを返す | 全復号エラーメッセージを統一する |
---
## 結論
"""
        if failed == 0:
            report += "✅ **予期しない失敗のテストはすべて通過しました。**\n\n"
        else:
            report += f"❌ **{failed} 件のテストが失敗しました。修正が必要です。**\n\n"
        if xfail > 0:
            report += f"⚠️ **{xfail} 件の予期失敗テストがあります。これらは既知のセキュリティ問題です。早急な修正を推奨します。**\n"
        report += f"""
---
*レポート生成日時: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
    def generate_json_report(self, output_path: str):
        """JSONフォーマットのレポートを生成する"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = sum(1 for r in self.results if not r["passed"] and not r["expected_fail"])
        xfail = sum(1 for r in self.results if r["expected_fail"])
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
        else:
            duration = sum(r["duration"] for r in self.results)
        report = {
            "metadata": {
                "test_target": "app/core/crypto.py",
                "test_spec": "crypto_tests.md",
                "execution_time": datetime.now().isoformat(),
                "total_duration_seconds": duration,
                "coverage_target": "90%"
            },
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "expected_fail": xfail,
                "pass_rate": (passed / total * 100) if total > 0 else 0,
                "effective_pass_rate": (passed / (total - xfail) * 100) if (total - xfail) > 0 else 0
            },
            "results_by_category": {
                "normal": [r for r in self.results if r["category"] == "normal"],
                "error": [r for r in self.results if r["category"] == "error"],
                "security": [r for r in self.results if r["category"] == "security"]
            },
            "all_results": self.results
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
_collector = TestResultCollector()
def pytest_configure(config):
    """pytest設定フック"""
    _collector.start()
def pytest_sessionfinish(session, exitstatus):
    """pytestセッション終了フック"""
    _collector.end()
    report_dir = r"C:\pythonProject\python_ai_cspm\TestReport\crypto\reports"
    os.makedirs(report_dir, exist_ok=True)
    _collector.generate_markdown_report(os.path.join(report_dir, "TestReport_crypto.md"))
    _collector.generate_json_report(os.path.join(report_dir, "TestReport_crypto.json"))
def record_result(test_id: str, test_name: str, category: str, 
                  passed: bool, message: str = "", expected_fail: bool = False, 
                  duration: float = 0.0):
    """テスト結果を記録する"""
    _collector.add_result(test_id, test_name, category, passed, message, expected_fail, duration)
# =============================================================================
# 正常系テスト (CRYPTO-001 ~ CRYPTO-010)
# =============================================================================
@pytest.mark.normal
class TestGetSharedSecret:
    """CRYPTO-001 ～ CRYPTO-004: _get_shared_secret 正常系テスト"""
    def test_crypto_001_get_from_env_variable(self):
        """CRYPTO-001: 环境変数SHARED_SECRETから鍵取得"""
        test_id = "CRYPTO-001"
        test_name = "環境変数から共有キー取得"
        start = time.time()
        try:
            test_secret = "my_test_secret_key"
            with patch.dict(os.environ, {"SHARED_SECRET": test_secret}):
                result = _get_shared_secret()
            assert result == test_secret.encode('utf-8'), f"期待値: {test_secret.encode('utf-8')}, 実際値: {result}"
            duration = time.time() - start
            record_result(test_id, test_name, "normal", True, "環境変数から鍵の取得に成功", False, duration)
        except Exception as e:
            duration = time.time() - start
            record_result(test_id, test_name, "normal", False, str(e), False, duration)
            raise
    def test_crypto_002_get_from_file(self, tmp_path):
        """CRYPTO-002: ファイルから鍵取得"""
        test_id = "CRYPTO-002"
        test_name = "ファイルから共有キー取得"
        start = time.time()
        try:
            secret_file = tmp_path / "shared_secret"
            secret_file.write_bytes(b"file_secret_key_12345")
            env = os.environ.copy()
            env.pop("SHARED_SECRET", None)
            env["SHARED_SECRET_FILE"] = str(secret_file)
            with patch.dict(os.environ, env, clear=True):
                result = _get_shared_secret()
            assert result == b"file_secret_key_12345", f"期待値: b'file_secret_key_12345', 実際値: {result}"
            duration = time.time() - start
            record_result(test_id, test_name, "normal", True, "ファイルから鍵の取得に成功", False, duration)
        except Exception as e:
            duration = time.time() - start
            record_result(test_id, test_name, "normal", False, str(e), False, duration)
            raise
    def test_crypto_003_fallback_to_default_key(self):
        """CRYPTO-003: デフォルト開発用鍵のフォールバック"""
        test_id = "CRYPTO-003"
        test_name = "デフォルトキーへのフォールバック"
        start = time.time()
        try:
            env = os.environ.copy()
            env.pop("SHARED_SECRET", None)
            env.pop("SHARED_SECRET_FILE", None)
            with patch.dict(os.environ, env, clear=True):
                with patch("os.path.exists", return_value=False):
                    result = _get_shared_secret()
            expected = "default_shared_secret_for_development_only".encode('utf-8')
            assert result == expected, f"デフォルトキーを期待, 実際値: {result}"
            duration = time.time() - start
            record_result(test_id, test_name, "normal", True, "デフォルトキーへのフォールバックに成功", False, duration)
        except Exception as e:
            duration = time.time() - start
            record_result(test_id, test_name, "normal", False, str(e), False, duration)
            raise
    def test_crypto_004_strip_whitespace_false(self, tmp_path):
        """CRYPTO-004: strip_whitespace=Falseで空白保持"""
        test_id = "CRYPTO-004"
        test_name = "空白文字の保持"
        start = time.time()
        try:
            secret_with_whitespace = b"  secret_with_spaces  \n"
            secret_file = tmp_path / "shared_secret"
            secret_file.write_bytes(secret_with_whitespace)
            env = os.environ.copy()
            env.pop("SHARED_SECRET", None)
            env["SHARED_SECRET_FILE"] = str(secret_file)
            with patch.dict(os.environ, env, clear=True):
                result = _get_shared_secret(strip_whitespace=False)
            assert result == secret_with_whitespace, "空白文字は保持される必要があります"
            duration = time.time() - start
            record_result(test_id, test_name, "normal", True, "空白文字の保持に成功", False, duration)
        except Exception as e:
            duration = time.time() - start
            record_result(test_id, test_name, "normal", False, str(e), False, duration)
            raise
@pytest.mark.normal
class TestVerifyAuthHash:
    """CRYPTO-005, CRYPTO-010: verify_auth_hash 正常系テスト"""
    def _create_valid_auth_header(self, session_id: str, shared_secret: bytes, 
                                   timestamp: int = None) -> str:
        """有効な認証ヘッダーを作成する"""
        if timestamp is None:
            timestamp = int(time.time())
        message = f"{session_id}:{timestamp}"
        hash_value = hmac.new(shared_secret, message.encode(), hashlib.sha256).hexdigest()
        return f"SHARED-HMAC-{timestamp}-{hash_value}"
    def test_crypto_005_valid_auth_hash(self, test_shared_secret):
        """CRYPTO-005: 有効なHMAC認証ハッシュの検証成功"""
        test_id = "CRYPTO-005"
        test_name = "有効なHMAC認証ハッシュ検証"
        start = time.time()
        try:
            session_id = "test-session-123"
            auth_header = self._create_valid_auth_header(session_id, test_shared_secret)
            result = verify_auth_hash(auth_header, session_id, test_shared_secret)
            assert result is True, "有効な認証ハッシュは検証に成功する必要があります"
            duration = time.time() - start
            record_result(test_id, test_name, "normal", True, "認証ハッシュ検証成功", False, duration)
        except Exception as e:
            duration = time.time() - start
            record_result(test_id, test_name, "normal", False, str(e), False, duration)
            raise
    def test_crypto_010_valid_hash_within_time_drift(self, test_shared_secret):
        """CRYPTO-010: 時刻ずれが許容範囲内での検証成功"""
        test_id = "CRYPTO-010"
        test_name = "時間ドリフト許容検証"
        start = time.time()
        try:
            session_id = "test-session-456"
            past_timestamp = int(time.time()) - 300  # 300秒前
            auth_header = self._create_valid_auth_header(session_id, test_shared_secret, 
                                                         timestamp=past_timestamp)
            result = verify_auth_hash(auth_header, session_id, test_shared_secret, 
                                     allowed_time_drift=600)
            assert result is True, "300秒の時間差は600秒の許容範囲内である必要があります"
            duration = time.time() - start
            record_result(test_id, test_name, "normal", True, "時間ドリフト検証成功", False, duration)
        except Exception as e:
            duration = time.time() - start
            record_result(test_id, test_name, "normal", False, str(e), False, duration)
            raise
@pytest.mark.normal
class TestDecryptOpensearchDashboardPayload:
    """CRYPTO-006, CRYPTO-007: decrypt_opensearch_dashboard_payload 正常系テスト"""
    def test_crypto_006_decrypt_valid_payload(self, test_shared_secret_32, encrypted_payload):
        """CRYPTO-006: 有効なペイロードのAES-CBC復号成功"""
        test_id = "CRYPTO-006"
        test_name = "有効なペイロードのAES-CBC復号"
        start = time.time()
        try:
            result = decrypt_opensearch_dashboard_payload(
                encrypted_payload["encrypted_data"],
                encrypted_payload["iv"],
                test_shared_secret_32
            )
            assert isinstance(result, dict), f"復号結果は辞書型である必要があります, 実際: {type(result)}"
            duration = time.time() - start
            record_result(test_id, test_name, "normal", True, "AES-CBC復号成功", False, duration)
        except Exception as e:
            duration = time.time() - start
            record_result(test_id, test_name, "normal", False, str(e), False, duration)
            raise
    def test_crypto_007_decrypt_returns_valid_json(self, test_shared_secret_32, encrypted_payload):
        """CRYPTO-007: 復号後のJSON正常パース"""
        test_id = "CRYPTO-007"
        test_name = "復号後のJSON解析"
        start = time.time()
        try:
            result = decrypt_opensearch_dashboard_payload(
                encrypted_payload["encrypted_data"],
                encrypted_payload["iv"],
                test_shared_secret_32
            )
            assert result == encrypted_payload["expected"], f"復号結果が一致しません"
            assert result["session_id"] == "test_123", "session_id が一致しません"
            assert result["prompt"] == "テストメッセージ", "prompt が一致しません"
            duration = time.time() - start
            record_result(test_id, test_name, "normal", True, "JSON解析成功", False, duration)
        except Exception as e:
            duration = time.time() - start
            record_result(test_id, test_name, "normal", False, str(e), False, duration)
            raise
@pytest.mark.normal
class TestDecryptCredentialsField:
    """CRYPTO-008: decrypt_credentials_field 正常系テスト"""
    def test_crypto_008_decrypt_base64_encoded_data(self):
        """CRYPTO-008: 認証情報フィールドのBase64復号"""
        test_id = "CRYPTO-008"
        test_name = "Base64から認証情報復号"
        start = time.time()
        try:
            original_data = '{"access_key": "AKIA...", "secret_key": "xxx"}'
            encoded_data = base64.b64encode(original_data.encode('utf-8')).decode()
            result = decrypt_credentials_field(encoded_data)
            assert result == original_data, f"復号結果が一致しません, 期待値: {original_data}, 実際値: {result}"
            duration = time.time() - start
            record_result(test_id, test_name, "normal", True, "Base64復号成功", False, duration)
        except Exception as e:
            duration = time.time() - start
            record_result(test_id, test_name, "normal", False, str(e), False, duration)
            raise
@pytest.mark.normal
class TestDecryptionWithKnownData:
    """CRYPTO-009: test_decryption_with_known_data 正常系テスト"""
    def test_crypto_009_known_data_decryption_success(self):
        """CRYPTO-009: test_decryption_with_known_dataの成功"""
        test_id = "CRYPTO-009"
        test_name = "既知データの復号テスト"
        start = time.time()
        try:
            result = test_decryption_with_known_data()
            assert result is True, "既知データの復号テストはTrueを返す必要があります"
            duration = time.time() - start
            record_result(test_id, test_name, "normal", True, "既知データの復号成功", False, duration)
        except Exception as e:
            duration = time.time() - start
            record_result(test_id, test_name, "normal", False, str(e), False, duration)
            raise
# =============================================================================
# 異常系テスト (CRYPTO-E01 ~ CRYPTO-E13)
# =============================================================================
@pytest.mark.error
class TestGetSharedSecretErrors:
    """CRYPTO-E01: _get_shared_secret 異常系テスト"""
    def test_crypto_e01_empty_secret_file_raises_error(self, tmp_path):
        """CRYPTO-E01: 鍵ファイルが空でValueError"""
        test_id = "CRYPTO-E01"
        test_name = "空の鍵ファイルエラー"
        start = time.time()
        try:
            empty_file = tmp_path / "empty_secret"
            empty_file.write_bytes(b"")
            env = os.environ.copy()
            env.pop("SHARED_SECRET", None)
            env["SHARED_SECRET_FILE"] = str(empty_file)
            with patch.dict(os.environ, env, clear=True):
                with pytest.raises(ValueError, match="共有鍵ファイルが空です"):
                    _get_shared_secret()
            duration = time.time() - start
            record_result(test_id, test_name, "error", True, "空のファイルで正しくValueErrorが発生", False, duration)
        except Exception as e:
            duration = time.time() - start
            record_result(test_id, test_name, "error", False, str(e), False, duration)
            raise
@pytest.mark.error
class TestVerifyAuthHashErrors:
    """CRYPTO-E02 ～ CRYPTO-E04, CRYPTO-E11: verify_auth_hash 異常系テスト"""
    def test_crypto_e02_invalid_format_returns_false(self, test_shared_secret):
        """CRYPTO-E02: 不正なHMAC形式でFalse返却"""
        test_id = "CRYPTO-E02"
        test_name = "無効なHMAC形式"
        start = time.time()
        try:
            invalid_headers = [
                "INVALID-FORMAT",
                "SHARED-HMAC-notanumber-abc123",
                "SHARED-HMAC--abcdef",
                "",
                "Bearer token123",
            ]
            for header in invalid_headers:
                result = verify_auth_hash(header, "session-id", test_shared_secret)
                assert result is False, f"無効ヘッダー '{header}' はFalseを返す必要があります"
            duration = time.time() - start
            record_result(test_id, test_name, "error", True, "無効な形式で正しくFalseを返却", False, duration)
        except Exception as e:
            duration = time.time() - start
            record_result(test_id, test_name, "error", False, str(e), False, duration)
            raise
    def test_crypto_e03_expired_timestamp_returns_false(self, test_shared_secret):
        """CRYPTO-E03: 時刻ずれ超過でFalse返却"""
        test_id = "CRYPTO-E03"
        test_name = "タイムスタンプ期限切れ"
        start = time.time()
        try:
            session_id = "test-session"
            old_timestamp = int(time.time()) - 1200  # 1200秒前
            message = f"{session_id}:{old_timestamp}"
            hash_value = hmac.new(test_shared_secret, message.encode(), hashlib.sha256).hexdigest()
            auth_header = f"SHARED-HMAC-{old_timestamp}-{hash_value}"
            result = verify_auth_hash(auth_header, session_id, test_shared_secret)
            assert result is False, "期限切れのタイムスタンプはFalseを返す必要があります"
            duration = time.time() - start
            record_result(test_id, test_name, "error", True, "期限切れタイムスタンプで正しくFalseを返却", False, duration)
        except Exception as e:
            duration = time.time() - start
            record_result(test_id, test_name, "error", False, str(e), False, duration)
            raise
    def test_crypto_e04_tampered_hash_returns_false(self, test_shared_secret):
        """CRYPTO-E04: 不正なHMACハッシュ値でFalse返却"""
        test_id = "CRYPTO-E04"
        test_name = "篡改的哈希值"
        start = time.time()
        try:
            timestamp = int(time.time())
            tampered_hash = "a" * 64
            auth_header = f"SHARED-HMAC-{timestamp}-{tampered_hash}"
            result = verify_auth_hash(auth_header, "session-id", test_shared_secret)
            assert result is False, "改ざんされたハッシュ値はFalseを返す必要があります"
            duration = time.time() - start
            record_result(test_id, test_name, "error", True, "改ざんハッシュで正しくFalseを返却", False, duration)
        except Exception as e:
            duration = time.time() - start
            record_result(test_id, test_name, "error", False, str(e), False, duration)
            raise
    def test_crypto_e11_none_auth_header_returns_false(self, test_shared_secret):
        """CRYPTO-E11: auth_header=NoneでFalse返却"""
        test_id = "CRYPTO-E11"
        test_name = "None認証ヘッダー"
        start = time.time()
        try:
            result = verify_auth_hash(None, "session-id", test_shared_secret)
            assert result is False, "None認証ヘッダーはFalseを返す必要があります"
            duration = time.time() - start
            record_result(test_id, test_name, "error", True, "None認証ヘッダーで正しくFalseを返却", False, duration)
        except Exception as e:
            duration = time.time() - start
            record_result(test_id, test_name, "error", False, str(e), False, duration)
            raise
@pytest.mark.error
class TestDecryptPayloadErrors:
    """CRYPTO-E05 ～ CRYPTO-E10, CRYPTO-E12, CRYPTO-E13: decrypt_opensearch_dashboard_payload 異常系テスト"""
    def test_crypto_e05_invalid_iv_size_raises_error(self, test_shared_secret_32):
        """CRYPTO-E05: 無効なIVサイズでValueError"""
        test_id = "CRYPTO-E05"
        test_name = "無効なIVサイズ"
        start = time.time()
        try:
            invalid_iv = base64.b64encode(b"short_iv").decode()
            encrypted_data = base64.b64encode(b"dummy_encrypted_data_16").decode()
            with pytest.raises(ValueError):
                decrypt_opensearch_dashboard_payload(encrypted_data, invalid_iv, test_shared_secret_32)
            duration = time.time() - start
            record_result(test_id, test_name, "error", True, "無効なIVサイズで正しくValueErrorが発生", False, duration)
        except Exception as e:
            duration = time.time() - start
            record_result(test_id, test_name, "error", False, str(e), False, duration)
            raise
    def test_crypto_e06_invalid_pkcs7_padding_raises_error(self, test_shared_secret_32):
        """CRYPTO-E06: 無効なPKCS7パディングでValueError"""
        test_id = "CRYPTO-E06"
        test_name = "無効なPKCS7パディング"
        start = time.time()
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            key = hashlib.sha256(test_shared_secret_32).digest()
            iv = os.urandom(16)
            bad_padded = b"invalid_padding!"
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(bad_padded) + encryptor.finalize()
            encrypted_data = base64.b64encode(ciphertext).decode()
            iv_b64 = base64.b64encode(iv).decode()
            with pytest.raises(ValueError):
                decrypt_opensearch_dashboard_payload(encrypted_data, iv_b64, test_shared_secret_32)
            duration = time.time() - start
            record_result(test_id, test_name, "error", True, "無効なパディングで正しくValueErrorが発生", False, duration)
        except Exception as e:
            duration = time.time() - start
            record_result(test_id, test_name, "error", False, str(e), False, duration)
            raise
    def test_crypto_e07_empty_encrypted_input_raises_error(self, test_shared_secret_32):
        """CRYPTO-E07: 空の暗号化入力でValueError"""
        test_id = "CRYPTO-E07"
        test_name = "空の暗号化入力"
        start = time.time()
        try:
            with pytest.raises(ValueError):
                decrypt_opensearch_dashboard_payload("", "", test_shared_secret_32)
            duration = time.time() - start
            record_result(test_id, test_name, "error", True, "空の入力で正しくValueErrorが発生", False, duration)
        except Exception as e:
            duration = time.time() - start
            record_result(test_id, test_name, "error", False, str(e), False, duration)
            raise
    def test_crypto_e08_non_utf8_decrypted_data_raises_error(self, test_shared_secret_32):
        """CRYPTO-E08: UTF-8デコード不可でValueError"""
        test_id = "CRYPTO-E08"
        test_name = "非UTF-8データ"
        start = time.time()
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.primitives import padding as crypto_padding
            from cryptography.hazmat.backends import default_backend
            key = hashlib.sha256(test_shared_secret_32).digest()
            iv = os.urandom(16)
            non_utf8_data = bytes([0xFF, 0xFE, 0x80, 0x81, 0x82, 0x83, 0x84, 0x85])
            padder = crypto_padding.PKCS7(128).padder()
            padded = padder.update(non_utf8_data) + padder.finalize()
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(padded) + encryptor.finalize()
            encrypted_data = base64.b64encode(ciphertext).decode()
            iv_b64 = base64.b64encode(iv).decode()
            with pytest.raises(ValueError):
                decrypt_opensearch_dashboard_payload(encrypted_data, iv_b64, test_shared_secret_32)
            duration = time.time() - start
            record_result(test_id, test_name, "error", True, "非UTF-8データで正しくValueErrorが発生", False, duration)
        except Exception as e:
            duration = time.time() - start
            record_result(test_id, test_name, "error", False, str(e), False, duration)
            raise
    def test_crypto_e09_invalid_json_after_decrypt_raises_error(self, test_shared_secret_32):
        """CRYPTO-E09: JSON解析失敗でValueError"""
        test_id = "CRYPTO-E09"
        test_name = "無効なJSON"
        start = time.time()
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.primitives import padding as crypto_padding
            from cryptography.hazmat.backends import default_backend
            key = hashlib.sha256(test_shared_secret_32).digest()
            iv = os.urandom(16)
            not_json = "this is not json data at all"
            padder = crypto_padding.PKCS7(128).padder()
            padded = padder.update(not_json.encode('utf-8')) + padder.finalize()
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(padded) + encryptor.finalize()
            encrypted_data = base64.b64encode(ciphertext).decode()
            iv_b64 = base64.b64encode(iv).decode()
            with pytest.raises(ValueError):
                decrypt_opensearch_dashboard_payload(encrypted_data, iv_b64, test_shared_secret_32)
            duration = time.time() - start
            record_result(test_id, test_name, "error", True, "無効なJSONで正しくValueErrorが発生", False, duration)
        except Exception as e:
            duration = time.time() - start
            record_result(test_id, test_name, "error", False, str(e), False, duration)
            raise
    def test_crypto_e12_data_shorter_than_padding_length_raises_error(self, test_shared_secret_32):
        """CRYPTO-E12: padded_dataがパディング長より短いでValueError"""
        test_id = "CRYPTO-E12"
        test_name = "パディング長より短いデータ"
        start = time.time()
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            key = hashlib.sha256(test_shared_secret_32).digest()
            iv = os.urandom(16)
            bad_data = b"X" + b"\x0F" * 15
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(bad_data) + encryptor.finalize()
            encrypted_b64 = base64.b64encode(ciphertext).decode()
            iv_b64 = base64.b64encode(iv).decode()
            with pytest.raises(ValueError):
                decrypt_opensearch_dashboard_payload(encrypted_b64, iv_b64, test_shared_secret_32)
            duration = time.time() - start
            record_result(test_id, test_name, "error", True, "データ長エラーで正しくValueErrorが発生", False, duration)
        except Exception as e:
            duration = time.time() - start
            record_result(test_id, test_name, "error", False, str(e), False, duration)
            raise
    def test_crypto_e13_inconsistent_padding_bytes_raises_error(self, test_shared_secret_32):
        """CRYPTO-E13: パディングバイト不一致でValueError"""
        test_id = "CRYPTO-E13"
        test_name = "パディングバイト不一致"
        start = time.time()
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            key = hashlib.sha256(test_shared_secret_32).digest()
            iv = os.urandom(16)
            bad_data = b"A" * 13 + b"\x03\x03\x02"
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(bad_data) + encryptor.finalize()
            encrypted_b64 = base64.b64encode(ciphertext).decode()
            iv_b64 = base64.b64encode(iv).decode()
            with pytest.raises(ValueError):
                decrypt_opensearch_dashboard_payload(encrypted_b64, iv_b64, test_shared_secret_32)
            duration = time.time() - start
            record_result(test_id, test_name, "error", True, "パディング不一致で正しくValueErrorが発生", False, duration)
        except Exception as e:
            duration = time.time() - start
            record_result(test_id, test_name, "error", False, str(e), False, duration)
            raise
@pytest.mark.error
class TestDecryptCredentialsFieldErrors:
    """CRYPTO-E10: decrypt_credentials_field 異常系テスト"""
    def test_crypto_e10_invalid_base64_raises_error(self):
        """CRYPTO-E10: 不正なBase64データでValueError"""
        test_id = "CRYPTO-E10"
        test_name = "無効なBase64データ"
        start = time.time()
        try:
            invalid_base64 = "!!!not-valid-base64!!!"
            with pytest.raises(ValueError):
                decrypt_credentials_field(invalid_base64)
            duration = time.time() - start
            record_result(test_id, test_name, "error", True, "無効なBase64で正しくValueErrorが発生", False, duration)
        except Exception as e:
            duration = time.time() - start
            record_result(test_id, test_name, "error", False, str(e), False, duration)
            raise
# =============================================================================
# セキュリティテスト (CRYPTO-SEC-01 ～ CRYPTO-SEC-06)
# =============================================================================
@pytest.mark.security
class TestCryptoSecurity:
    """セキュリティテスト"""
    @pytest.mark.xfail(reason="現在の実装では == 比較を使用しており、タイミング攻撃リスクがあります", strict=False)
    def test_crypto_sec_01_hmac_uses_compare_digest(self):
        """CRYPTO-SEC-01: HMAC比較にhmac.compare_digest使用を検証（タイミング攻撃耐性）"""
        test_id = "CRYPTO-SEC-01"
        test_name = "HMACタイミング攻撃防御"
        start = time.time()
        try:
            source = inspect.getsource(verify_auth_hash)
            assert "compare_digest" in source, (
                "verify_auth_hash は hmac.compare_digest() を使用する必要があります。"
                "== 比較はタイミング攻撃リスクがあります。"
                "修正: received_hash == expected_hash → hmac.compare_digest(received_hash, expected_hash)"
            )
            duration = time.time() - start
            record_result(test_id, test_name, "security", True, "compare_digestを使用", False, duration)
        except AssertionError as e:
            duration = time.time() - start
            record_result(test_id, test_name, "security", False, str(e), True, duration)
            raise
    def test_crypto_sec_02_timestamp_tampering_detection(self, test_shared_secret):
        """CRYPTO-SEC-02: タイムスタンプ改ざん検出"""
        test_id = "CRYPTO-SEC-02"
        test_name = "タイムスタンプ改ざん検出"
        start = time.time()
        try:
            session_id = "session-sec-02"
            original_timestamp = int(time.time())
            message = f"{session_id}:{original_timestamp}"
            hash_value = hmac.new(test_shared_secret, message.encode(), hashlib.sha256).hexdigest()
            tampered_timestamp = original_timestamp + 1
            auth_header = f"SHARED-HMAC-{tampered_timestamp}-{hash_value}"
            result = verify_auth_hash(auth_header, session_id, test_shared_secret)
            assert result is False, "改ざんされたタイムスタンプは検出される必要があります"
            duration = time.time() - start
            record_result(test_id, test_name, "security", True, "タイムスタンプ改ざん検出成功", False, duration)
        except Exception as e:
            duration = time.time() - start
            record_result(test_id, test_name, "security", False, str(e), False, duration)
            raise
    @pytest.mark.xfail(reason="現在の実装のエラーメッセージが内部詳細を漏洩する可能性があります", strict=False)
    def test_crypto_sec_03_padding_oracle_no_detail_leak(self, test_shared_secret_32):
        """CRYPTO-SEC-03: パディングオラクル攻撃対策 - エラーメッセージに内部詳細が含まれない"""
        test_id = "CRYPTO-SEC-03"
        test_name = "パディングオラクル攻撃防御"
        start = time.time()
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            key = hashlib.sha256(test_shared_secret_32).digest()
            bad_padding_patterns = [
                b"\x00" * 16,
                b"A" * 15 + b"\x11",
                b"A" * 14 + b"\x02\x01",
            ]
            errors = []
            for pattern in bad_padding_patterns:
                iv = os.urandom(16)
                cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
                encryptor = cipher.encryptor()
                ciphertext = encryptor.update(pattern) + encryptor.finalize()
                encrypted_b64 = base64.b64encode(ciphertext).decode()
                iv_b64 = base64.b64encode(iv).decode()
                with pytest.raises(ValueError) as exc_info:
                    decrypt_opensearch_dashboard_payload(encrypted_b64, iv_b64, test_shared_secret_32)
                errors.append(str(exc_info.value))
            unique_messages = set(errors)
            assert len(unique_messages) == 1, (
                f"パディングオラクル情報漏洩: エラーパターンによって異なるメッセージが返却されます。\n"
                f"検出されたメッセージ: {unique_messages}\n"
                f"修正: 復号失敗時は統一したメッセージを返す"
            )
            error_msg = errors[0]
            assert "パディング" not in error_msg, f"エラーメッセージにパディング詳細が含まれています: {error_msg}"
            duration = time.time() - start
            record_result(test_id, test_name, "security", True, "パディングオラクル攻撃防御が有効", False, duration)
        except AssertionError as e:
            duration = time.time() - start
            record_result(test_id, test_name, "security", False, str(e), True, duration)
            raise
    def test_crypto_sec_04_default_key_warning_output(self, capsys):
        """CRYPTO-SEC-04: デフォルト鍵使用時の警告出力確認"""
        test_id = "CRYPTO-SEC-04"
        test_name = "デフォルトキー警告出力"
        start = time.time()
        try:
            env = os.environ.copy()
            env.pop("SHARED_SECRET", None)
            env.pop("SHARED_SECRET_FILE", None)
            with patch.dict(os.environ, env, clear=True):
                with patch("os.path.exists", return_value=False):
                    _get_shared_secret()
            captured = capsys.readouterr()
            assert "WARNING" in captured.out, "WARNINGが出力される必要があります"
            assert "デフォルト開発用共有鍵" in captured.out or "default" in captured.out.lower(), "デフォルトキーについて言及される必要があります"
            duration = time.time() - start
            record_result(test_id, test_name, "security", True, "デフォルトキー警告出力が正常", False, duration)
        except Exception as e:
            duration = time.time() - start
            record_result(test_id, test_name, "security", False, str(e), False, duration)
            raise
    def test_crypto_sec_05_hmac_single_bit_difference(self, test_shared_secret):
        """CRYPTO-SEC-05: 1ビット異なるHMACハッシュでFalse"""
        test_id = "CRYPTO-SEC-05"
        test_name = "HMAC単一ビット差異検出"
        start = time.time()
        try:
            session_id = "session-sec-05"
            timestamp = int(time.time())
            message = f"{session_id}:{timestamp}"
            correct_hash = hmac.new(test_shared_secret, message.encode(), hashlib.sha256).hexdigest()
            tampered_hash = list(correct_hash)
            tampered_hash[-1] = 'a' if tampered_hash[-1] != 'a' else 'b'
            tampered_hash = ''.join(tampered_hash)
            auth_header = f"SHARED-HMAC-{timestamp}-{tampered_hash}"
            result = verify_auth_hash(auth_header, session_id, test_shared_secret)
            assert result is False, "単一ビット差異は検出される必要があります"
            duration = time.time() - start
            record_result(test_id, test_name, "security", True, "単一ビット差異検出成功", False, duration)
        except Exception as e:
            duration = time.time() - start
            record_result(test_id, test_name, "security", False, str(e), False, duration)
            raise
    @pytest.mark.xfail(reason="現在の実装では異なる種類の復号エラーに対して異なるメッセージを返します", strict=False)
    def test_crypto_sec_06_error_message_no_internal_details(self, test_shared_secret_32):
        """CRYPTO-SEC-06: エラーメッセージに内部詳細が含まれない"""
        test_id = "CRYPTO-SEC-06"
        test_name = "エラーメッセージに内部詳細が含まれない"
        start = time.time()
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            key = hashlib.sha256(test_shared_secret_32).digest()
            iv = os.urandom(16)
            bad_data = b"A" * 15 + b"\x11"
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(bad_data) + encryptor.finalize()
            encrypted_b64 = base64.b64encode(ciphertext).decode()
            iv_b64 = base64.b64encode(iv).decode()
            with pytest.raises(ValueError) as exc_info:
                decrypt_opensearch_dashboard_payload(encrypted_b64, iv_b64, test_shared_secret_32)
            error_msg = str(exc_info.value)
            internal_detail_keywords = ["パディング長", "データ長", "バイト"]
            for keyword in internal_detail_keywords:
                assert keyword not in error_msg, (
                    f"エラーメッセージに内部詳細 '{keyword}' が含まれています: {error_msg}\n"
                    f"修正: 復号失敗時は 'OpenSearchダッシュボード復号に失敗しました' のみを返す"
                )
            duration = time.time() - start
            record_result(test_id, test_name, "security", True, "エラーメッセージに内部詳細が含まれない", False, duration)
        except AssertionError as e:
            duration = time.time() - start
            record_result(test_id, test_name, "security", False, str(e), True, duration)
            raise
# =============================================================================
# Main Entry Point
# =============================================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
