# conftest.py
"""
auth テスト設定とフックファンクション

テスト対象:
  - app/core/auth.py
  - app/auth/router.py
  - app/models/auth.py

テスト仕様: docs/testing/plugins/auth_tests.md
"""

import pytest
import pytest_asyncio
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any

# プロジェクトルート設定（env_loader を使用）
try:
    from env_loader import PROJECT_ROOT
except ImportError:
    _here = Path(__file__).resolve()
    for _p in [_here, *_here.parents]:
        if (_p / "env_loader.py").exists():
            sys.path.insert(0, str(_p))
            from env_loader import PROJECT_ROOT
            break
    else:
        raise ImportError("env_loader.py が見つかりません")

project_root = PROJECT_ROOT / "platform_python_backend-testing" if not str(PROJECT_ROOT).endswith("platform_python_backend-testing") else PROJECT_ROOT
if not project_root.exists():
    raise RuntimeError(f"プロジェクトルートディレクトリが存在しません: {project_root}")
sys.path.insert(0, str(project_root))

# JWT秘密鍵を環境変数に設定（shared_secretの鍵を使用）
os.environ["JWT_SECRET_KEY"] = "f4fae6a6c089204d69efdc35438312a81005e1c3825a40cfc706cbe5ec0f50b1"


class TestResultCollector:
    """テスト結果を収集してレポートを生成する"""

    def __init__(self):
        self.results: Dict[str, List[Dict[str, Any]]] = {
            "normal": [],    # 正常系テスト
            "error": [],     # 異常系テスト
            "security": []   # セキュリティテスト
        }
        self.start_time = datetime.now()
        self.end_time = None

    def add_result(self, nodeid: str, outcome: str, duration: float):
        """テスト結果を追加する

        分類ルール:
        - "Security" を含むまたはテスト名に "SEC" を含む → security
        - "Error" を含むまたはテスト名に "_e0" または "_E" を含む → error
        - その他 → normal
        """
        test_name = nodeid.split("::")[-1] if "::" in nodeid else nodeid
        class_name = nodeid.split("::")[-2] if nodeid.count("::") >= 2 else ""

        # 可読名を取得する
        readable_name = self._get_readable_name(test_name)

        # テストIDを抽出する
        test_id = self._extract_test_id(test_name)

        result = {
            "nodeid": nodeid,
            "test_name": test_name,
            "readable_name": readable_name,
            "test_id": test_id,
            "class_name": class_name,
            "outcome": outcome,
            "duration": duration,
            "duration_ms": round(duration * 1000, 2)
        }

        # 分類する
        if "Security" in class_name or "SEC" in test_name.upper() or "security" in test_name.lower():
            self.results["security"].append(result)
        elif "Error" in class_name or "_e0" in test_name.lower() or "_E" in test_name:
            self.results["error"].append(result)
        else:
            self.results["normal"].append(result)

    def _get_readable_name(self, test_name: str) -> str:
        """テストメソッド名を可読名に変換する"""
        name_map = {
            # 正常系テスト (AUTH-001 ~ AUTH-012)
            "test_login_success": "AUTH-001: 有効な認証情報でToken取得",
            "test_get_current_user": "AUTH-002: 認証後にユーザー情報取得",
            "test_protected_route": "AUTH-003: 保護されたルートへのアクセス",
            "test_verify_password_success": "AUTH-004: パスワード検証成功",
            "test_get_password_hash": "AUTH-005: パスワードハッシュ化",
            "test_get_user_found": "AUTH-006: ユーザークエリ成功",
            "test_get_user_with_roles_found": "AUTH-007: ロール付きユーザークエリ成功",
            "test_authenticate_user_with_roles_success": "AUTH-008: ロール付き認証成功",
            "test_create_access_token_with_expiry": "AUTH-009: 有効期限指定Token生成",
            "test_create_access_token_default_expiry": "AUTH-010: デフォルト有効期限Token生成",
            "test_create_access_token_with_roles_and_expiry": "AUTH-011: ロール付きToken生成(期限指定)",
            "test_create_access_token_with_roles_default_expiry": "AUTH-012: ロール付きToken生成(デフォルト期限)",

            # 異常系テスト (AUTH-E01 ~ AUTH-E18)
            "test_login_invalid_password": "AUTH-E01: 無効なパスワードで401返す",
            "test_login_unknown_user": "AUTH-E02: 存在しないユーザーで401返す",
            "test_expired_token": "AUTH-E03: 期限切れTokenで401返す",
            "test_malformed_token": "AUTH-E04: 無効なToken形式で401返す",
            "test_no_auth_header": "AUTH-E05: 認証ヘッダーなしで401返す",
            "test_disabled_user": "AUTH-E06: 無効化されたユーザーで400返す",
            "test_insufficient_roles": "AUTH-E07: 権限不足で403返す",
            "test_verify_password_failure": "AUTH-E08: パスワード検証失敗",
            "test_get_user_not_found": "AUTH-E09: 存在しないユーザーでNone返す",
            "test_authenticate_user_with_roles_unknown": "AUTH-E10: ロール付き認証-ユーザー不存在",
            "test_authenticate_user_with_roles_wrong_password": "AUTH-E11: ロール付き認証-パスワード誤り",
            "test_get_current_user_no_sub": "AUTH-E12: subフィールドなしTokenで401返す",
            "test_get_current_user_unknown_sub": "AUTH-E13: subがDBに存在せず401返す",
            "test_require_all_roles_partial_match": "AUTH-E14: require_all_roles部分一致で403返す",
            "test_get_current_user_with_roles_no_sub": "AUTH-E15: ロール付きユーザー取得-subなしで401返す",
            "test_get_current_user_with_roles_jwt_error": "AUTH-E16: ロール付きユーザー取得-無効Token",
            "test_get_current_user_with_roles_unknown_user": "AUTH-E17: ロール付きユーザー取得-ユーザー不存在",
            "test_disabled_user_with_roles": "AUTH-E18: ロール付き無効化ユーザーで400返す",

            # セキュリティテスト (AUTH-SEC-01 ~ AUTH-SEC-08)
            "test_password_is_hashed": "AUTH-SEC-01: パスワードbcryptハッシュ検証",
            "test_token_modified_rejected": "AUTH-SEC-02: 改ざんされたTokenは拒否される",
            "test_password_not_in_response": "AUTH-SEC-03: レスポンスにパスワード情報を含まない",
            "test_token_expiry_enforced": "AUTH-SEC-04: Token有効期限が強制される",
            "test_default_secret_key_warning": "AUTH-SEC-05: デフォルトSECRET_KEYで警告",
            "test_jwt_alg_none_attack_rejected": "AUTH-SEC-06: JWT alg=none攻撃を防御",
            "test_jwt_role_tampering_rejected": "AUTH-SEC-07: JWTロール改ざんを検出",
            "test_role_escalation_prevented": "AUTH-SEC-08: ロール昇格を防止",
        }
        return name_map.get(test_name, test_name)

    def _extract_test_id(self, test_name: str) -> str:
        """テスト名からテストIDを抽出する"""
        readable = self._get_readable_name(test_name)
        if ":" in readable:
            return readable.split(":")[0].strip()
        return ""

    def get_summary(self) -> Dict[str, Any]:
        """テストサマリーを取得する"""
        total = sum(len(v) for v in self.results.values())
        passed = sum(
            1 for cat in self.results.values()
            for r in cat if r["outcome"] == "passed"
        )
        failed = sum(
            1 for cat in self.results.values()
            for r in cat if r["outcome"] == "failed"
        )
        xfailed = sum(
            1 for cat in self.results.values()
            for r in cat if r["outcome"] == "xfailed"
        )
        skipped = sum(
            1 for cat in self.results.values()
            for r in cat if r["outcome"] == "skipped"
        )

        pass_rate = (passed / total * 100) if total > 0 else 0
        effective_total = total - xfailed - skipped
        effective_pass_rate = (passed / effective_total * 100) if effective_total > 0 else 0

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "xfailed": xfailed,
            "skipped": skipped,
            "pass_rate": f"{pass_rate:.1f}%",
            "effective_pass_rate": f"{effective_pass_rate:.1f}%"
        }

    def generate_markdown_report(self) -> str:
        """Markdown形式のレポートを生成する"""
        summary = self.get_summary()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = f"""# auth テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| テスト対象 | `app/core/auth.py`, `app/auth/router.py`, `app/models/auth.py` |
| テスト仕様 | `docs/testing/plugins/auth_tests.md` |
| 実行時刻 | {timestamp} |
| カバレッジ目標 | 90% |

## テスト結果統計

| カテゴリ | 総数 | 通過 | 失敗 | 予想失敗 | スキップ |
|------|------|------|------|----------|------|
| 正常系 | {len(self.results['normal'])} | {sum(1 for r in self.results['normal'] if r['outcome']=='passed')} | {sum(1 for r in self.results['normal'] if r['outcome']=='failed')} | {sum(1 for r in self.results['normal'] if r['outcome']=='xfailed')} | {sum(1 for r in self.results['normal'] if r['outcome']=='skipped')} |
| 異常系 | {len(self.results['error'])} | {sum(1 for r in self.results['error'] if r['outcome']=='passed')} | {sum(1 for r in self.results['error'] if r['outcome']=='failed')} | {sum(1 for r in self.results['error'] if r['outcome']=='xfailed')} | {sum(1 for r in self.results['error'] if r['outcome']=='skipped')} |
| セキュリティテスト | {len(self.results['security'])} | {sum(1 for r in self.results['security'] if r['outcome']=='passed')} | {sum(1 for r in self.results['security'] if r['outcome']=='failed')} | {sum(1 for r in self.results['security'] if r['outcome']=='xfailed')} | {sum(1 for r in self.results['security'] if r['outcome']=='skipped')} |
| **合計** | **{summary['total']}** | **{summary['passed']}** | **{summary['failed']}** | **{summary['xfailed']}** | **{summary['skipped']}** |

## テスト通過率

- **実際の通過率**: {summary['pass_rate']}
- **有効通過率** (予想失敗を除外): {summary['effective_pass_rate']}

---

## 正常系テスト詳細

| ID | テスト名 | 結果 | 実行時間 |
|----|---------|------|----------|
"""
        for r in self.results['normal']:
            icon = "✅" if r['outcome'] == 'passed' else "❌" if r['outcome'] == 'failed' else "⏭️"
            report += f"| {r['test_id']} | {r['readable_name']} | {icon} | {r['duration_ms']}ms |\n"

        report += """
## 異常系テスト詳細

| ID | テスト名 | 結果 | 実行時間 |
|----|---------|------|----------|
"""
        for r in self.results['error']:
            icon = "✅" if r['outcome'] == 'passed' else "❌" if r['outcome'] == 'failed' else "⏭️"
            report += f"| {r['test_id']} | {r['readable_name']} | {icon} | {r['duration_ms']}ms |\n"

        report += """
## セキュリティテスト詳細

| ID | テスト名 | 結果 | 実行時間 |
|----|---------|------|----------|
"""
        for r in self.results['security']:
            icon = "✅" if r['outcome'] == 'passed' else "❌" if r['outcome'] == 'failed' else "⏭️"
            report += f"| {r['test_id']} | {r['readable_name']} | {icon} | {r['duration_ms']}ms |\n"

        # 結論
        if summary['failed'] == 0:
            conclusion = "✅ 全テスト通過！認証モジュールは正常に動作しています。"
        else:
            conclusion = f"⚠️ {summary['failed']} 個のテストが失敗しました。確認と修正が必要です。"

        report += f"""
---

## 結論

{conclusion}

---

*レポート生成時刻: {timestamp}*
"""
        return report

    def generate_json_report(self) -> str:
        """JSON形式のレポートを生成する"""
        summary = self.get_summary()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report_data = {
            "summary": summary,
            "categories": {
                "normal": {
                    "count": len(self.results['normal']),
                    "results": self.results['normal']
                },
                "error": {
                    "count": len(self.results['error']),
                    "results": self.results['error']
                },
                "security": {
                    "count": len(self.results['security']),
                    "results": self.results['security']
                }
            },
            "execution_time": timestamp,
            "test_target": {
                "files": [
                    "app/core/auth.py",
                    "app/auth/router.py",
                    "app/models/auth.py"
                ],
                "spec": "docs/testing/plugins/auth_tests.md"
            }
        }

        return json.dumps(report_data, indent=2, ensure_ascii=False)


# グローバルコレクターインスタンス
_collector = TestResultCollector()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """各テストの結果をキャプチャする"""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        _collector.add_result(
            nodeid=report.nodeid,
            outcome=report.outcome,
            duration=report.duration
        )


def pytest_sessionfinish(session, exitstatus):
    """テストセッション終了時にレポートを生成する"""
    _collector.end_time = datetime.now()

    # レポート出力ディレクトリを確定する
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Markdownレポートを生成する
    md_report = _collector.generate_markdown_report()
    md_path = reports_dir / "TestReport_auth.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_report)

    # JSONレポートを生成する
    json_report = _collector.generate_json_report()
    json_path = reports_dir / "TestReport_auth.json"
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json_report)

    print(f"\n{'='*60}")
    print(f"📊 テストレポートを生成しました:")
    print(f"   - Markdown: {md_path}")
    print(f"   - JSON: {json_path}")
    print(f"{'='*60}")


# ============================================================================
# Fixtures（テストフィクスチャ）
# ============================================================================

@pytest.fixture(scope="session")
def app():
    """FastAPIアプリケーションインスタンス（最小化テスト版）

    認証ルートのみを含む最小限のFastAPIアプリを作成し、
    他の依存関係が不足する可能性のあるモジュールのインポートを回避する。
    """
    from fastapi import FastAPI
    from app.auth.router import router as auth_router

    test_app = FastAPI()
    test_app.include_router(auth_router)

    return test_app


@pytest_asyncio.fixture
async def async_client(app):
    """非同期HTTPテストクライアント

    ASGITransportを使用してFastAPIアプリに直接接続する。
    実際のHTTPサーバーを起動せずにテストを実行できる。
    """
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def valid_token():
    """有効なJWT Token（testuser用）

    注意: アプリケーションのSECRET_KEYを使用して署名する。
    エンドポイントテストで認証機能が正常に動作することを確認する。
    """
    from jose import jwt
    from app.core.auth import SECRET_KEY, ALGORITHM
    payload = {
        "sub": "testuser",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def admin_token():
    """管理者JWT Token（全ロール付き）"""
    from jose import jwt
    from app.core.auth import SECRET_KEY, ALGORITHM
    payload = {
        "sub": "admin",
        "roles": [
            "cspm_dashboard_read_role",
            "rag_search_read_role",
            "document_write_role",
            "cspm_job_execution_role"
        ],
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def testuser_token():
    """普通用户JWT Token（限定角色）"""
    from jose import jwt
    from app.core.auth import SECRET_KEY, ALGORITHM
    payload = {
        "sub": "testuser",
        "roles": ["rag_search_read_role"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def dashboard_user_token():
    """仪表板用户Token"""
    from jose import jwt
    from app.core.auth import SECRET_KEY, ALGORITHM
    payload = {
        "sub": "dashboard-user",
        "roles": ["cspm_dashboard_read_role"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def expired_token():
    """过期的Token"""
    from jose import jwt
    from app.core.auth import SECRET_KEY, ALGORITHM
    payload = {
        "sub": "testuser",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def disabled_user_in_db():
    """将禁用用户临时添加到fake_users_db的夹具

    测试结束后执行清理。
    """
    from app.core.auth import fake_users_db

    disabled_user_data = {
        "username": "disabled-user",
        "full_name": "禁用用户",
        "email": "disabled@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": True,
        "roles": []
    }

    # 添加用户
    fake_users_db["disabled-user"] = disabled_user_data
    yield disabled_user_data

    # 清理
    if "disabled-user" in fake_users_db:
        del fake_users_db["disabled-user"]


@pytest.fixture
def mock_role_required_endpoint(app):
    """注册需要角色的测试端点的夹具

    在测试期间向FastAPI应用添加一个需要cspm_dashboard_read_role的临时端点。

    注意: FastAPI难以删除路由器，因此使用测试专用路径避免冲突。
    """
    from fastapi import APIRouter, Depends
    from app.core.auth import require_roles

    test_router = APIRouter(tags=["test"])

    @test_router.get("/protected-dashboard")
    async def protected_dashboard_endpoint(
        user=Depends(require_roles(["cspm_dashboard_read_role"]))
    ):
        return {"status": "ok", "user": user.username}

    # 添加路由器
    app.include_router(test_router)
    yield

    # 注意: FastAPI难以删除路由，但由于是测试专用路径，不会影响其他测试


@pytest.fixture(autouse=True)
def mock_password_verification():
    """Mock密码验证以避免bcrypt/passlib兼容性问题

    Python 3.13 + 新版bcrypt与passlib存在兼容性问题。
    此fixture使用mock来绕过实际的bcrypt调用。
    """
    from unittest.mock import patch

    def mock_verify(plain_password, hashed_password):
        """模拟密码验证 - 密码为'secret'时返回True"""
        return plain_password == "secret"

    def mock_hash(password):
        """模拟密码哈希 - 返回固定格式的假哈希"""
        return f"$2b$12$mockhash_{password}"

    with patch('app.core.auth.pwd_context.verify', side_effect=mock_verify):
        with patch('app.core.auth.pwd_context.hash', side_effect=mock_hash):
            yield


