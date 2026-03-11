# Jobs Router テスト修正サマリー

## 問題の概要

pytest実行時にモックが正しく動作せず、以下の問題が発生していました：

1. **モックが呼ばれない**: `mock_status_manager.get_job_result_sync`がテスト中に呼ばれない
2. **404エラー**: ルートが正しく登録されていない（ダブルプレフィックス問題）
3. **暗号化テスト失敗**: 暗号化関連の関数がモックされていない

## 根本原因

### 1. モックのタイミング問題

```python
# 問題: routerモジュールのインポート時に関数がバインドされる
from .status_manager import get_job_result_sync

# この時点でget_job_result_syncはstatus_manager.get_job_result_syncを参照
# 後でstatus_manager.get_job_result_syncをモックしても、
# routerモジュールは既に古い参照を持っている
```

### 2. ルートプレフィックスの重複

```python
# router.py内
router = APIRouter(prefix="/jobs", ...)

# conftest.py内（修正前）
app.include_router(router, prefix="/jobs")  # → /jobs/jobs/{job_id}/result
```

### 3. 暗号化関数のモック漏れ

`verify_auth_hash`, `decrypt_opensearch_dashboard_payload`, `_get_shared_secret`がモックされていなかった。

## 解決方法

### 1. ルーターモジュールの強制リロード

```python
# sys.modulesから削除して強制リロード
if 'app.jobs.router' in sys.modules:
    del sys.modules['app.jobs.router']
```

### 2. ルーターモジュールのネームスペースに直接パッチ適用

```python
# Import the router
from app.jobs import router as router_module

# Patch the functions in the router module's namespace directly
router_module.check_job_exclusion = mock_status_manager.check_job_exclusion
router_module.try_initialize_job_exclusive = mock_status_manager.try_initialize_job_exclusive
router_module.get_job_status_sync = mock_status_manager.get_job_status_sync
router_module.get_job_result_sync = mock_status_manager.get_job_result_sync

# 暗号化関数も同様にパッチ
router_module.verify_auth_hash = mock_crypto.verify_auth_hash
router_module.decrypt_opensearch_dashboard_payload = mock_crypto.decrypt_opensearch_dashboard_payload
router_module._get_shared_secret = mock_crypto._get_shared_secret
```

### 3. プレフィックスの重複を修正

```python
# 修正後: routerは既にprefix="/jobs"を持っているので追加しない
app.include_router(router)  # → /jobs/{job_id}/result
app.include_router(start_router)
```

## 変更ファイル

### `conftest.py`

#### 変更前の問題

1. `autouse=True`で`mock_status_manager`が自動適用されていた
2. パッチがコンテキストマネージャー内で行われ、タイミングが不適切
3. `mock_crypto`が`test_app`に渡されていなかった
4. ルータープレフィックスが重複していた

#### 変更後の修正

```python
@pytest.fixture(scope="function")  # autouse削除
def mock_status_manager():
    """status_manager モジュールのモック"""
    from app.jobs import status_manager
    
    original_statuses = status_manager.job_statuses.copy()
    status_manager.job_statuses.clear()
    
    class StatusManager:
        job_statuses = status_manager.job_statuses
        check_job_exclusion = MagicMock(return_value=None)
        try_initialize_job_exclusive = MagicMock(return_value=("test-job-id", None))
        get_job_status_sync = MagicMock(return_value=None)
        get_job_result_sync = MagicMock(return_value=None)
        
    manager = StatusManager()
    yield manager
    
    status_manager.job_statuses.clear()
    status_manager.job_statuses.update(original_statuses)


@pytest.fixture
async def test_app(mock_status_manager, mock_tasks, mock_crypto):  # mock_crypto追加
    """テスト用Fastアプリケーション"""
    from fastapi import FastAPI
    import sys
    
    app = FastAPI()
    
    # ルーターモジュールを強制リロード
    if 'app.jobs.router' in sys.modules:
        del sys.modules['app.jobs.router']
    
    with patch.dict('sys.modules', {'weasyprint': MagicMock()}):
        from app.jobs import router as router_module
        
        # status_manager関数をパッチ
        router_module.check_job_exclusion = mock_status_manager.check_job_exclusion
        router_module.try_initialize_job_exclusive = mock_status_manager.try_initialize_job_exclusive
        router_module.get_job_status_sync = mock_status_manager.get_job_status_sync
        router_module.get_job_result_sync = mock_status_manager.get_job_result_sync
        
        # 暗号化関数をパッチ
        router_module.verify_auth_hash = mock_crypto.verify_auth_hash
        router_module.decrypt_opensearch_dashboard_payload = mock_crypto.decrypt_opensearch_dashboard_payload
        router_module._get_shared_secret = mock_crypto._get_shared_secret
        
        router = router_module.router
        start_router = router_module.start_router
        
        # プレフィックスの重複を修正
        app.include_router(router)  # 既にprefix="/jobs"を持つ
        app.include_router(start_router)
        
        yield app
```

## テスト結果

### 修正前
```
FAILED test_jobs_router.py::TestCustodianScanEndpoints::test_custodian_scan_encrypted_success
FAILED test_jobs_router.py::TestNewCustodianScanEndpoints::test_new_custodian_scan_encrypted_success
FAILED test_jobs_router.py::TestJobsSecurityEndpoints::test_replay_attack_prevention
====================== 3 failed, 30 passed, 3 skipped
```

### 修正後
```
=========================== 33 passed, 3 skipped in 4.45s ============================
```

## 学んだ教訓

1. **Pythonのインポートメカニズム**: モジュールインポート時に関数がバインドされるため、後からパッチしても効かない
2. **モックのタイミング**: インポート前にパッチするか、インポート後にモジュールのネームスペースに直接代入する
3. **sys.modules**: モジュールキャッシュを削除することで強制リロードできる
4. **FastAPIのルーター**: プレフィックスの重複に注意
5. **依存フィクスチャ**: `test_app`が`mock_crypto`に依存していることを明示する必要がある

## 今後の注意点

- 新しいエンドポイントを追加する場合、関連する関数のモックも追加する
- ルーターのプレフィックス設定を確認する
- モックが実際に呼ばれているか確認するテストを書く（`mock.called`, `mock.call_count`）

## 参考資料

- [Python Import System](https://docs.python.org/3/reference/import.html)
- [unittest.mock - Mock object library](https://docs.python.org/3/library/unittest.mock.html)
- [pytest fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [FastAPI APIRouter](https://fastapi.tiangolo.com/tutorial/bigger-applications/)

---

**修正日**: 2026-03-11  
**修正者**: GitHub Copilot  
**ステータス**: ✅ 完了 (33/36 tests passed, 3 skipped intentionally)

