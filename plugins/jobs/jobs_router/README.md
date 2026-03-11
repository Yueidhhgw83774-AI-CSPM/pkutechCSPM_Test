# Jobs Router テストプロジェクト

## 概要

Jobs Router（ジョブ管理API）の完全なテストスイートです。バックグラウンドジョブの開始、ステータス管理、結果取得、暗号化通信など、36個のテストケースを提供します。

## テスト統計

- **総テスト数**: 36
  - 正常系: 10
  - 異常系: 16
  - セキュリティ: 10

## テスト対象

### エンドポイント

| エンドポイント | HTTPメソッド | 説明 |
|---------------|-------------|------|
| `/start_generate_policies_batch_async` | POST | CSPMポリシー一括生成開始 |
| `/start_file_processing_async` | POST | ファイル処理開始 |
| `/start_custodian_scan_async` | POST | 旧Custodianスキャン開始 |
| `/new_start_custodian_scan_async` | POST | 新Custodianスキャン開始（AssumeRole対応） |
| `/jobs/{job_id}/status` | GET | ジョブステータス取得 |
| `/jobs/{job_id}/result` | GET | ジョブ結果取得 |
| `/jobs/{job_id}/scan_files` | GET | スキャンファイル詳細取得 |

### ソースコード

- `app/jobs/router.py` - メインルーター
- `app/jobs/status_manager.py` - ステータス管理
- `app/models/jobs.py` - モデル定義

## テストケース

### 正常系 (JOB-001~010)

| ID | テスト名 | 説明 |
|----|---------|------|
| JOB-001 | test_start_policy_batch | ポリシーバッチ生成開始 |
| JOB-002 | test_start_file_processing | ファイル処理開始 |
| JOB-003 | test_get_job_status | ジョブステータス取得 |
| JOB-004 | test_get_job_result_completed | 完了ジョブの結果取得 |
| JOB-005 | test_get_scan_files_success | スキャンファイル取得 |
| JOB-006 | test_custodian_scan_encrypted_success | 旧Custodianスキャン（暗号化） |
| JOB-007 | test_custodian_scan_plain_success | 旧Custodianスキャン（平文） |
| JOB-008 | test_new_custodian_scan_encrypted_success | 新Custodianスキャン（暗号化） |
| JOB-009 | test_new_custodian_scan_plain_success | 新Custodianスキャン（平文） |
| JOB-010 | test_new_custodian_scan_with_preset | 新Custodianスキャン（プリセット付き） |

### 異常系 (JOB-E01~E16)

| ID | テスト名 | 説明 |
|----|---------|------|
| JOB-E01 | test_job_status_not_found | 存在しないジョブで404 |
| JOB-E02 | test_job_exclusion_conflict | 排他制御エラーで409 |
| JOB-E03 | test_invalid_request_data | 無効なリクエストで400 |
| JOB-E04 | test_job_result_not_found | 存在しないジョブ結果で404 |
| JOB-E05 | test_auth_hash_verification_failure | 認証ハッシュ検証失敗 |
| JOB-E06 | test_decryption_failure | 復号失敗 |
| JOB-E07 | test_scan_files_job_not_found | スキャンファイル取得（存在しないジョブ） |
| JOB-E08 | test_scan_files_non_custodian_job | スキャンファイル取得（非Custodianジョブ） |
| JOB-E09 | test_scan_files_incomplete_job | スキャンファイル取得（未完了ジョブ） |
| JOB-E10 | test_scan_files_no_result | スキャンファイル取得（結果なし） |
| JOB-E11 | test_request_body_parse_failure | リクエストボディ解析失敗 |
| JOB-E12 | test_new_custodian_auth_failure | 新Custodianスキャン認証失敗 |
| JOB-E13 | test_new_custodian_exclusion_conflict | 新Custodianスキャン排他制御エラー |
| JOB-E14 | test_new_custodian_validation_failure | 新Custodianスキャン検証失敗 |
| JOB-E15 | test_status_pydantic_cast_error | ステータスPydanticキャストエラー |
| JOB-E16 | test_old_custodian_exclusion_conflict | 旧Custodianスキャン排他制御エラー |

### セキュリティ (JOB-SEC-01~10)

| ID | テスト名 | 説明 |
|----|---------|------|
| JOB-SEC-01 | test_unauthorized_access_prevention | 未認証アクセス防止 |
| JOB-SEC-02 | test_job_id_injection_resistance | ジョブIDインジェクション耐性 |
| JOB-SEC-03 | test_shared_secret_not_in_response | 共有シークレット非露出 |
| JOB-SEC-04 | test_credentials_not_in_logs | 認証情報ログ非出力 |
| JOB-SEC-05 | test_payload_size_limit | ペイロードサイズ制限 |
| JOB-SEC-06 | test_concurrent_job_exclusion | 並行ジョブ排他制御 |
| JOB-SEC-07 | test_error_message_info_leakage_prevention | エラーメッセージ情報漏洩防止 |
| JOB-SEC-08 | test_session_id_format_validation | セッションID形式検証 |
| JOB-SEC-09 | test_job_result_access_control | ジョブ結果アクセス制御 |
| JOB-SEC-10 | test_replay_attack_prevention | リプレイ攻撃防止 |

## 実行方法

### 全テスト実行

```bash
cd C:\pythonProject\python_ai_cspm\TestReport\plugins\jobs\jobs_router\source
pytest test_jobs_router.py -v
```

### カテゴリ別実行

```bash
# 正常系のみ
pytest test_jobs_router.py::TestJobsStartEndpoints -v
pytest test_jobs_router.py::TestJobsStatusEndpoints -v
pytest test_jobs_router.py::TestScanFilesEndpoint -v
pytest test_jobs_router.py::TestCustodianScanEndpoints -v
pytest test_jobs_router.py::TestNewCustodianScanEndpoints -v

# 異常系のみ
pytest test_jobs_router.py::TestJobsErrors -v
pytest test_jobs_router.py::TestEncryptedRequestErrors -v
pytest test_jobs_router.py::TestScanFilesErrors -v
pytest test_jobs_router.py::TestNewCustodianScanErrors -v
pytest test_jobs_router.py::TestMiscErrors -v

# セキュリティテストのみ
pytest test_jobs_router.py::TestJobsSecurityEndpoints -v
pytest -m security test_jobs_router.py -v
```

### カバレッジ付き実行

```bash
pytest test_jobs_router.py --cov=app.jobs.router --cov-report=html -v
```

## 環境設定

### 必要な環境変数

`.env` ファイルに以下を設定：

```env
soure_root=C:\pythonProject\python_ai_cspm\platform_python_backend-testing\
```

### 依存パッケージ

```bash
pip install pytest pytest-asyncio httpx fastapi python-dotenv
```

## テスト設計の特徴

### モック戦略

- **status_manager**: ジョブステータス管理関数をモック
- **crypto**: 暗号化関連関数をモック
- **tasks**: バックグラウンドタスクをモック

### 実装の特性

1. **暗号化エンドポイントの例外処理**
   - 認証失敗（401）を含む全ての例外が広域`except`で捕捉され400に変換
   - router.py:334-336, 464-466

2. **スキャンファイル取得の例外処理**
   - 結果なし（404）を含む例外が500に変換
   - router.py:281-286

3. **排他制御機能**
   - `try_initialize_job_exclusive()`: レースコンディション対策
   - `check_job_exclusion()`: 実行中ジョブのチェック
   - 排他制御エラー時は409 Conflictを返す

### 認証方式

新Custodianスキャンは2つの認証方式をサポート：

- `"role_assumption"`: AssumeRole方式
- `"secret_key"`: アクセスキー方式

## レポート生成

テスト実行後、以下のレポートが自動生成されます：

- `reports/test_report_YYYYMMDD_HHMMSS.md` - Markdownレポート
- `reports/test_report_YYYYMMDD_HHMMSS.json` - JSONレポート

## トラブルシューティング

### ImportError

```bash
# sys.pathに追加されない場合
export PYTHONPATH="${PYTHONPATH}:C:/pythonProject/python_ai_cspm/platform_python_backend-testing"
```

### モックが効かない

conftest.pyのフィクスチャが正しくロードされているか確認：

```bash
pytest --fixtures test_jobs_router.py
```

## 参照

- 要件文書: `docs/testing/plugins/jobs/jobs_router_tests.md`
- ソースコード: `app/jobs/router.py`, `app/jobs/status_manager.py`
- モデル定義: `app/models/jobs.py`

## 変更履歴

- 2024-01-XX: 初版作成（36テストケース）

